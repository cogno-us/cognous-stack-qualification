"""Rebuild the pinned producer environment of a delegated workflow on a local Linux machine.

SPDX-License-Identifier: Apache-2.0

The recipe for each environment already exists, as the workflow YAML under .github/workflows: which repository is checked
out at which exact commit and into which directory, which packages are installed (and from which lock), and which
environment variables the test step receives.  This tool reads that YAML and nothing else for pins.  It holds no revision,
repository name or variable value of its own, so a pin that changes in a workflow changes here with no edit to this file.

    python tools/rc_env.py plan    [--recipe R ...]                 offline: print the recipe read from the workflows
    python tools/rc_env.py prepare --work DIR [--recipe R ...]      clone pins, apply the suite overlay, build the venvs
    python tools/rc_env.py env     --work DIR --recipe R [--stage S] print the variables to export for one test stage
    python tools/rc_env.py check   --work DIR [--recipe R ...]      compare what is on disk with the pins; exit 1 on mismatch

A recipe is ``WORKFLOW`` (file stem) or ``WORKFLOW:JOB``.  With no ``--recipe`` the default set below is used.

What it reproduces: checkouts at the exact pinned commits, the suite overlay (``tools/install_suite.py``, the same script the
workflow runs), one virtual environment per distinct install sequence that precedes a test step (a workflow that swaps the
installed Replay between two test steps gets two environments), and the variables of each test step with every relative path
made absolute.  What it does not reproduce: third-party packages that a workflow installs without a pin or lock resolve
from PyPI on the day of ``prepare``; the exact versions found are recorded (``pip freeze``) and ``check`` reports a change.
Steps it does not model (uploads, example generators, shell checks) are listed in the plan, never silently run.

Network use is limited to the git host (``git init`` + ``git fetch --depth 1 origin <sha>``, one repository at a time) and
the Python package index.  No credential is read or sent; a variable that refers to a secret is dropped and reported.
Candidate or release status is never inferred: this tool prepares inputs and verifies them, it runs no gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'cognous.rc-env/1'
MANIFEST = 'rc-env.json'
MARKER = '.rc-env-building'
GIT_BASE_ENV = 'RC_ENV_GIT_BASE'  # test hook: replaces https://github.com/
DEFAULT_GIT_BASE = 'https://github.com/'
SHA_RE = re.compile(r'^[0-9a-f]{40}$')
EXPR_RE = re.compile(r'\$\{\{(.*?)\}\}')
# Recipes whose workflow runs a test step against pinned producers.  Names only: no pin lives here.
DEFAULT_RECIPES = (
    'cognous-replay-bundle--tests',
    'cognous-governance-evidence-pack--tests',
    'cognous-governed-exchange--tests',
    'open-decision-evidence-standard--tests',
    'cognous-execution-runtime--python-safety',
    'cognous-execution-runtime--worker21-authority-effect',
    'cognous-execution-runtime--durable-refusal',
    'claude-agent-pilot:offline-controls',
    'openai-agent-pilot:offline-controls',
)
# pip options a recipe may use.  Anything else is refused rather than guessed.
PIP_FLAGS_PLAIN = {'--require-hashes', '-q', '--quiet', '--no-deps'}
PIP_FLAGS_VALUE = {'--only-binary', '--no-binary', '-r', '--requirement', '-e', '--editable', '-c', '--constraint'}


class RecipeError(ValueError):
    """The workflow uses something this builder does not model; it refuses instead of guessing."""


# ----------------------------------------------------------------------------------------------------------------------
# reading the recipe from a workflow
# ----------------------------------------------------------------------------------------------------------------------

def _yaml():
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - PyYAML is in tools/requirements-ci.lock and requirements-serial.txt
        raise RecipeError('PyYAML is required to read the workflows (python -m pip install pyyaml)') from error
    return yaml


def split_recipe(name):
    workflow, _, job = name.partition(':')
    return workflow, job


def slug(name):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', name).strip('_')


def load_workflow(workflow, root=None):
    path = Path(root or ROOT) / '.github' / 'workflows' / (workflow + '.yml')
    if not path.is_file():
        raise RecipeError('No workflow file: ' + path.name)
    return path, _yaml().safe_load(path.read_text(encoding='utf-8'))


def expand(value, *, workspace, matrix=None, inputs=None, what='value'):
    """Resolve the only expressions a recipe may carry; any other expression is refused."""
    text = str(value)
    inputs = inputs or {}

    def one(match):
        body = ' '.join(match.group(1).split())
        if body == 'github.workspace':
            return str(workspace)
        m = re.fullmatch(r'matrix\.([\w-]+)', body)
        if m and m.group(1) in (matrix or {}):
            return matrix[m.group(1)]
        m = re.fullmatch(r"inputs\.(\w+) \|\| '([^']*)'", body)
        if m:
            return inputs.get(m.group(1), m.group(2))
        raise RecipeError(f'{what}: expression not modelled: ${{{{ {body} }}}}')

    return EXPR_RE.sub(one, text)


def _logical_lines(script):
    """Shell lines of a ``run`` block: continuations joined, here-documents and comments dropped."""
    out, pending, heredoc = [], '', None
    for raw in script.splitlines():
        if heredoc is not None:
            if raw.strip() == heredoc:
                heredoc = None
            continue
        line = pending + raw.strip()
        pending = ''
        if line.endswith('\\'):
            pending = line[:-1].rstrip() + ' '
            continue
        m = re.search(r"<<-?\s*'?\"?(\w+)'?\"?\s*$", line)
        if m:
            heredoc = m.group(1)
            line = line[:m.start()].strip()
        if line and not line.startswith('#'):
            out.append(line)
    if pending.strip():
        out.append(pending.strip())
    return out


def parse_pip(line):
    """Return the ordered pip arguments of a ``pip install`` line, or None for ``pip install --upgrade pip``."""
    tokens = shlex.split(line)
    if tokens[:1] in (['python'], ['python3']):
        tokens = tokens[1:]
    if tokens[:2] == ['-m', 'pip']:
        tokens = tokens[2:]
    elif tokens[:1] == ['pip']:
        tokens = tokens[1:]
    if tokens[:1] != ['install']:
        raise RecipeError('pip line not modelled: ' + line)
    rest, args, i = tokens[1:], [], 0
    if rest in (['--upgrade', 'pip'], ['-U', 'pip']):
        return None  # upgrading the installer is not part of the pinned environment
    while i < len(rest):
        token = rest[i]
        if token in PIP_FLAGS_PLAIN:
            args.append((token, None))
        elif token.startswith('--only-binary=') or token.startswith('--no-binary='):
            args.append((token.split('=')[0], token.split('=', 1)[1]))
        elif token in PIP_FLAGS_VALUE:
            if i + 1 >= len(rest):
                raise RecipeError('pip option without a value: ' + line)
            args.append((token, rest[i + 1]))
            i += 1
        elif token.startswith('-'):
            raise RecipeError(f'pip option not modelled: {token} in: {line}')
        else:
            args.append(('', token))
        i += 1
    return args


def read_recipe(name, *, root=None, source_rev=None):
    """Read a recipe: checkouts, ordered build events and test stages, all from the workflow file."""
    workflow, job_name = split_recipe(name)
    path, doc = load_workflow(workflow, root)
    jobs = doc.get('jobs') or {}
    if not job_name:
        candidates = [k for k, j in jobs.items() if any('actions/checkout' in str(s.get('uses', '')) for s in j.get('steps', []))]
        if len(candidates) != 1:
            raise RecipeError(f'{workflow}: name one job as WORKFLOW:JOB (jobs with a checkout: {", ".join(candidates) or "none"})')
        job_name = candidates[0]
    if job_name not in jobs:
        raise RecipeError(f'{workflow}: no job {job_name}')
    job = jobs[job_name]
    # a matrix is read as its last entry per axis (the newest interpreter), the one this builder prepares
    matrix = {k: str(v[-1]) for k, v in ((job.get('strategy') or {}).get('matrix') or {}).items() if isinstance(v, list) and v}
    python_version = matrix.get('python-version') or matrix.get('python')
    inputs = {'source_revision': source_rev} if source_rev else {}
    ws = Path('${WORKSPACE}')  # placeholder resolved at prepare time; kept relative in the plan
    job_env = {**(doc.get('env') or {}), **(job.get('env') or {})}
    recipe = {'name': (workflow + ':' + job_name) if ':' in name or len(jobs) > 1 else workflow, 'workflow': path.name,
              'workflow_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'job': job_name,
              'python_version': python_version, 'checkouts': [], 'events': [], 'stages': [], 'verify': [],
              'unmodelled': [], 'skipped_steps': [], 'source_override': bool(source_rev)}
    has_explicit_source = False
    for index, step in enumerate(job.get('steps', [])):
        label = step.get('name') or str(step.get('uses') or ('step %d' % index))
        condition = step.get('if')
        if condition is not None:
            m = re.fullmatch(r"\s*matrix\.([\w-]+) == '([^']*)'\s*", str(condition))
            if not (m and matrix.get(m.group(1)) == m.group(2)):
                recipe['skipped_steps'].append({'step': label, 'if': str(condition)})
                continue
        uses = str(step.get('uses', ''))
        if uses.startswith('actions/checkout@'):
            w = step.get('with') or {}
            repo = w.get('repository')
            where = str(w.get('path') or '.')
            if not repo:
                recipe['checkouts'].append({'role': 'self', 'repository': None, 'sha': None, 'path': where, 'step': label})
                continue
            ref = str(w.get('ref', ''))
            local = re.fullmatch(r'\$\{\{\s*inputs\.qualification_revision \|\| github\.sha\s*\}\}', ref)
            if repo == 'cogno-us/cognous-stack-qualification' or local:
                recipe['checkouts'].append({'role': 'qualification', 'repository': repo, 'sha': None, 'path': where, 'step': label})
                continue
            sha = expand(ref, workspace=ws, inputs=inputs, what=label + ' ref')
            role = 'source' if 'inputs.source_revision' in ref else 'upstream'
            if role == 'source' and source_rev:
                sha = source_rev
            if role == 'source':
                has_explicit_source = True
            if not SHA_RE.match(sha):
                raise RecipeError(f'{label}: ref is not a full commit id: {sha}')
            recipe['checkouts'].append({'role': role, 'repository': repo, 'sha': sha, 'path': where, 'step': label})
        elif uses.startswith('actions/setup-python@'):
            w = step.get('with') or {}
            if w.get('python-version') is not None:
                python_version = expand(w['python-version'], workspace=ws, matrix=matrix, what='python-version')
                recipe['python_version'] = python_version
        elif 'run' in step:
            cwd = str(step.get('working-directory') or '.')
            step_env = {**job_env, **(step.get('env') or {})}
            for line in _logical_lines(str(step['run'])):
                if re.search(r'tools/install_suite\.py', line):
                    tokens = shlex.split(line)
                    opts = {t: tokens[i + 1] for i, t in enumerate(tokens[:-1]) if t.startswith('--')}
                    recipe['events'].append({'kind': 'overlay', 'suite': opts.get('--suite'), 'source_root': opts.get('--source-root'),
                                             'evidence': opts.get('--evidence'), 'cwd': cwd, 'step': label})
                elif re.match(r'^(python3? -m )?pip install\b', line):
                    args = parse_pip(line)
                    if args is not None:
                        recipe['events'].append({'kind': 'install', 'args': args, 'cwd': cwd, 'step': label})
                elif re.match(r'^test "\$\(git -C (\S+) rev-parse HEAD\)" = "([0-9a-f]{40})"$', line):
                    m = re.match(r'^test "\$\(git -C (\S+) rev-parse HEAD\)" = "([0-9a-f]{40})"$', line)
                    recipe['verify'].append({'path': m.group(1), 'sha': m.group(2)})
                elif re.match(r'^set [-+]', line):
                    continue  # shell options
                elif re.match(r'^(python3? -m )?(pytest|unittest)\b|^pytest\b', line):
                    env = {}
                    for key, value in step_env.items():
                        if 'secrets.' in str(value):
                            recipe['skipped_steps'].append({'step': label, 'if': f'variable {key} refers to a secret; dropped'})
                            continue
                        env[key] = expand(value, workspace=ws, what=f'{label} env {key}')
                    recipe['events'].append({'kind': 'test', 'command': line, 'cwd': cwd, 'env': env, 'step': label})
                else:
                    recipe['unmodelled'].append({'step': label, 'line': line[:160]})
    if not any(c['role'] in ('source', 'self') for c in recipe['checkouts']):
        raise RecipeError(f'{workflow}: no source checkout found')
    if source_rev and not has_explicit_source:
        raise RecipeError(f'{workflow}: --source-rev given but the recipe has no source checkout')
    stage_names, installs = set(), []
    for event in recipe['events']:
        if event['kind'] == 'install':
            installs.append(event)
        elif event['kind'] == 'test':
            base = slug(event['step']).lower() or 'test'
            name, n = base, 2
            while name in stage_names:
                name, n = f'{base}-{n}', n + 1
            stage_names.add(name)
            signature = json.dumps([[e['args'], e['cwd']] for e in installs], sort_keys=True)
            venv = hashlib.sha256(signature.encode()).hexdigest()[:10]
            recipe['stages'].append({'name': name, 'step': event['step'], 'command': event['command'], 'cwd': event['cwd'],
                                     'env': event['env'], 'venv': venv, 'installs': len(installs)})
    if not recipe['stages']:
        raise RecipeError(f'{workflow}: no test step found')
    return recipe


# ----------------------------------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------------------------------

def _git_base():
    return os.environ.get(GIT_BASE_ENV, DEFAULT_GIT_BASE)


def _clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ('VIRTUAL_ENV', 'PYTHONPATH', 'PYTHONHOME')}
    env.update(GIT_TERMINAL_PROMPT='0', PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_INPUT='1', PYTHONDONTWRITEBYTECODE='1')
    env.update(extra)
    return env


def run(command, *, cwd=None, timeout=900, capture=False):
    result = subprocess.run([str(c) for c in command], cwd=cwd, env=_clean_env(), timeout=timeout, text=True,
                            stdout=subprocess.PIPE if capture else None, stderr=subprocess.STDOUT if capture else None)
    if result.returncode:
        raise RuntimeError('command failed (%d): %s\n%s' % (result.returncode, ' '.join(map(str, command)), result.stdout or ''))
    return (result.stdout or '').strip()


def git(path, *args, timeout=300):
    return run(['git', '-C', path, *args], timeout=timeout, capture=True)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch_exact(repository, sha, dest, *, full_history=False):
    """Materialise ``repository`` at exactly ``sha`` in a new directory ``dest`` (init, then fetch that commit)."""
    dest = Path(dest)
    dest.mkdir(parents=True)
    run(['git', 'init', '-q', dest])
    git(dest, 'remote', 'add', 'origin', _git_base() + repository + '.git')
    depth = [] if full_history else ['--depth', '1']
    try:
        git(dest, 'fetch', '-q', '--no-tags', *depth, 'origin', sha)
        git(dest, 'checkout', '-q', '--detach', 'FETCH_HEAD')
    except RuntimeError:
        # The host refused a fetch by commit id: fetch the branches and check the commit out from them.
        git(dest, 'fetch', '-q', '--no-tags', 'origin', '+refs/heads/*:refs/remotes/origin/*')
        git(dest, 'checkout', '-q', '--detach', sha)
    head = git(dest, 'rev-parse', 'HEAD')
    if head != sha:
        raise RuntimeError(f'{repository}: fetched {head}, pinned {sha}')
    return head


def store_checkout(store, repository, sha, *, full_history):
    path = Path(store) / (repository.replace('/', '__') + '__' + sha[:12] + ('__full' if full_history else ''))
    if path.is_dir():
        try:
            if git(path, 'rev-parse', 'HEAD') == sha:
                return path
        except RuntimeError:
            pass
        shutil.rmtree(path)
    fetch_exact(repository, sha, path, full_history=full_history)
    return path


def tracked_changes(path):
    """{file: sha256 or None (deleted)} for tracked files that differ from HEAD in ``path``."""
    out = {}
    for name in git(path, 'diff', '--name-only', 'HEAD').splitlines():
        target = Path(path) / name
        out[name] = sha256_file(target) if target.is_file() else None
    return out


def resolve_path(value, base, *, always=False):
    """Absolute form of one path-like value (a ``:``-separated list is resolved element by element).

    Without ``always`` only values that look like paths (contain a slash, or are ``.``) are changed."""
    parts = []
    for part in str(value).split(':'):
        if always or part in ('.', '') or ('/' in part and '://' not in part and not part.startswith('$')):
            p = Path(part or '.')
            parts.append(str(p if p.is_absolute() else Path(os.path.normpath(Path(base) / p))))
        else:
            parts.append(part)
    return ':'.join(parts)


def ws_value(value, workspace):
    return str(value).replace('${WORKSPACE}', str(workspace))


def stage_env(recipe, stage, layout, venv_dir):
    base = layout.cwd(stage['cwd'])
    env = {}
    for key, value in stage['env'].items():
        value = ws_value(value, layout.workspace)
        looks_like_path = ('/' in value or value in ('.',)) and '://' not in value and ' ' not in value
        env[key] = resolve_path(value, base) if looks_like_path else value
    # Several pinned repositories track bytecode and package metadata; keep test runs from rewriting them (not a pin).
    env.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    env['VIRTUAL_ENV'] = str(venv_dir)
    return env


class Layout:
    """Where one recipe lives under --work: ``ws`` stands in for the Actions workspace."""

    def __init__(self, work, recipe):
        self.base = Path(work).resolve() / slug(recipe['name'])
        self.workspace = self.base / 'ws'
        self.self_checkout = any(c['role'] == 'self' for c in recipe['checkouts'])

    def cwd(self, relative):
        root = ROOT if self.self_checkout else self.workspace
        return Path(os.path.normpath(root / relative))

    def dest(self, checkout):
        if checkout['role'] == 'self':
            return ROOT
        return Path(os.path.normpath(self.workspace / checkout['path']))

    def venv(self, key):
        return self.base / 'venvs' / key


def _pip_command(venv_dir, args, base):
    command = [venv_dir / 'bin' / 'python', '-m', 'pip', 'install']
    for flag, value in args:
        if flag in ('-e', '--editable'):
            path, bracket, extras = value.partition('[')
            command += ['-e', resolve_path(path, base) + bracket + extras]
        elif flag in ('-r', '--requirement', '-c', '--constraint'):
            command += [flag, resolve_path(value, base)]
        elif flag == '':
            looks_path = value.startswith(('.', '/')) or ('/' in value and '==' not in value)
            command.append(resolve_path(value, base) if looks_path else value)
        elif value is None:
            command.append(flag)
        else:
            command += [flag, value]
    return command


def pick_python(recipe, explicit):
    if explicit:
        return str(explicit), []
    wanted = recipe.get('python_version')
    if wanted:
        found = shutil.which('python' + wanted)
        if found:
            return found, []
        return sys.executable, [f'python{wanted} not found; using {sys.executable}']
    return sys.executable, []


# ----------------------------------------------------------------------------------------------------------------------
# commands
# ----------------------------------------------------------------------------------------------------------------------

def _recipes(args):
    names = args.recipe or list(DEFAULT_RECIPES)
    overrides = {}
    for item in getattr(args, 'source_rev', None) or []:
        key, _, value = item.partition('=')
        if not value or not SHA_RE.match(value):
            raise RecipeError('--source-rev takes RECIPE=<40-hex commit id>')
        overrides[key] = value
    unknown = set(overrides) - set(names)
    if unknown:
        raise RecipeError('--source-rev names a recipe that is not selected: ' + ', '.join(sorted(unknown)))
    return [read_recipe(n, source_rev=overrides.get(n)) for n in names]


def cmd_plan(args):
    plans = _recipes(args)
    json.dump(plans if len(plans) != 1 else plans[0], sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write('\n')
    return 0


def prepare_one(recipe, work, *, python, full_history, force):
    if not sys.platform.startswith('linux'):
        raise RecipeError('Linux only')
    layout = Layout(work, recipe)
    if layout.base.exists():
        if not force:
            raise RecipeError(f'{layout.base} exists; use --force to rebuild this recipe directory')
        if not ((layout.base / MANIFEST).exists() or (layout.base / MARKER).exists()) and any(layout.base.iterdir()):
            raise RecipeError(f'{layout.base} is not a directory made by prepare; refusing to remove it')
        shutil.rmtree(layout.base)
    layout.workspace.mkdir(parents=True)
    (layout.base / MARKER).write_text('prepare started here\n')  # lets --force clear a directory a failed prepare left behind
    store = Path(work).resolve() / '_store'
    store.mkdir(parents=True, exist_ok=True)
    warnings = []
    # 1. checkouts: the source first (it owns the workspace root), then the others in workflow order, one repository at a time
    ordered = sorted(enumerate(recipe['checkouts']), key=lambda item: (item[1]['role'] != 'source', item[0]))
    done = {}
    for position, checkout in ordered:
        dest = layout.dest(checkout)
        if checkout['role'] == 'self':
            done[position] = {**checkout, 'path_abs': str(ROOT), 'head': git(ROOT, 'rev-parse', 'HEAD'), 'tree': git(ROOT, 'rev-parse', 'HEAD^{tree}')}
            continue
        if checkout['role'] == 'qualification':
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.symlink_to(ROOT, target_is_directory=True)
            done[position] = {**checkout, 'path_abs': str(dest), 'head': git(ROOT, 'rev-parse', 'HEAD'), 'tree': git(ROOT, 'rev-parse', 'HEAD^{tree}'),
                              'note': 'this repository, linked; the workflow ref (workflow input or event commit) is replaced by the local head'}
            continue
        cached = store_checkout(store, checkout['repository'], checkout['sha'], full_history=full_history)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(cached, dest, symlinks=True, dirs_exist_ok=(dest == layout.workspace))
        head = git(dest, 'rev-parse', 'HEAD')
        if head != checkout['sha']:
            raise RuntimeError(f'{checkout["repository"]}: checked out {head}, pinned {checkout["sha"]}')
        done[position] = {**checkout, 'path_abs': str(dest), 'head': head, 'tree': git(dest, 'rev-parse', 'HEAD^{tree}')}
    done = [done[i] for i in sorted(done)]
    # 2. the suite overlay, with the repository's own script
    overlays = []
    for event in recipe['events']:
        if event['kind'] != 'overlay':
            continue
        base = layout.cwd(event['cwd'])
        source_root = Path(resolve_path(ws_value(event['source_root'], layout.workspace), base, always=True))
        evidence = Path(resolve_path(ws_value(event['evidence'], layout.workspace), base, always=True))
        run([sys.executable, '-I', ROOT / 'tools' / 'install_suite.py', '--suite', event['suite'], '--source-root', source_root,
             '--evidence', evidence], capture=True)
        report = json.loads(evidence.read_text())
        overlays.append({'suite': event['suite'], 'source_root': str(source_root), 'evidence': str(evidence),
                         'files': {o['path']: o['sha256'] for o in report['overlay']}})
    # 3. one venv per distinct install sequence in front of a test step
    interpreter, notes = pick_python(recipe, python)
    warnings += notes
    venvs, built = [], {}
    installs = []
    for event in (e for e in recipe['events'] if e['kind'] in ('install', 'test')):
        if event['kind'] == 'install':
            installs.append(event)
            continue
        key = next(s['venv'] for s in recipe['stages'] if s['command'] == event['command'] and s['step'] == event['step'])
        if key in built:
            continue
        venv_dir = layout.venv(key)
        run([interpreter, '-m', 'venv', venv_dir])
        for install in installs:
            base = layout.cwd(install['cwd'])
            run(_pip_command(venv_dir, install['args'], base), cwd=base, timeout=1800, capture=True)
        freeze = run([venv_dir / 'bin' / 'python', '-m', 'pip', 'freeze', '--all'], capture=True).splitlines()
        version = run([venv_dir / 'bin' / 'python', '-c', 'import platform;print(platform.python_version())'], capture=True)
        built[key] = True
        venvs.append({'key': key, 'path': str(venv_dir), 'python': version, 'installs': len(installs), 'freeze': freeze,
                      'freeze_sha256': hashlib.sha256('\n'.join(freeze).encode()).hexdigest()})
    for entry in done:
        if entry['role'] in ('source', 'upstream'):
            entry['tracked_changes'] = tracked_changes(entry['path_abs'])  # overlay files and anything an install rewrote
    stages = []
    for stage in recipe['stages']:
        stages.append({**stage, 'env_resolved': stage_env(recipe, stage, layout, layout.venv(stage['venv'])),
                       'cwd_abs': str(layout.cwd(stage['cwd']))})
    manifest = {'schema': SCHEMA, 'recipe': recipe['name'], 'workflow': recipe['workflow'], 'workflow_sha256': recipe['workflow_sha256'],
                'job': recipe['job'], 'full_history': full_history, 'qualification_head': git(ROOT, 'rev-parse', 'HEAD'),
                'workspace': str(layout.workspace), 'python_requested': recipe['python_version'], 'python_used': interpreter,
                'checkouts': done, 'verify': recipe['verify'], 'overlays': overlays, 'venvs': venvs, 'stages': stages,
                'unmodelled': recipe['unmodelled'], 'skipped_steps': recipe['skipped_steps'], 'warnings': warnings,
                'source_override': recipe['source_override'],
                'claim': 'NONE: preparing an environment is not execution or acceptance'}
    (layout.base / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


def cmd_prepare(args):
    recipes = _recipes(args)
    for recipe in recipes:
        manifest = prepare_one(recipe, args.work, python=args.python, full_history=args.full_history, force=args.force)
        print(f'prepared {manifest["recipe"]}: {len(manifest["checkouts"])} checkouts, {len(manifest["venvs"])} venvs, '
              f'{len(manifest["stages"])} test stages -> {Layout(args.work, recipe).base}')
        for warning in manifest['warnings']:
            print('  warning: ' + warning)
    return 0


def load_manifests(work, names=None):
    found = {}
    for path in sorted(Path(work).resolve().glob('*/' + MANIFEST)):
        manifest = json.loads(path.read_text())
        found[manifest['recipe']] = (path.parent, manifest)
    if names:
        missing = [n for n in names if n not in found]
        if missing:
            raise RecipeError('not prepared under --work: ' + ', '.join(missing))
        found = {n: found[n] for n in names}
    if not found:
        raise RecipeError('nothing prepared under --work (run prepare first)')
    return found


def cmd_env(args):
    name = args.recipe[0] if args.recipe else None
    manifests = load_manifests(args.work, [name] if name else None)
    if len(manifests) != 1:
        raise RecipeError('name one recipe with --recipe (prepared: %s)' % ', '.join(manifests))
    (_, manifest), = manifests.values()
    stages = {s['name']: s for s in manifest['stages']}
    if args.stage and args.stage not in stages:
        raise RecipeError('no stage %s (stages: %s)' % (args.stage, ', '.join(stages)))
    stage = stages[args.stage] if args.stage else manifest['stages'][0]
    env = dict(stage['env_resolved'])
    if args.json:
        json.dump({'recipe': manifest['recipe'], 'stage': stage['name'], 'cwd': stage['cwd_abs'], 'command': stage['command'],
                   'env': env, 'path_prepend': [str(Path(env['VIRTUAL_ENV']) / 'bin')]}, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    print(f'# recipe {manifest["recipe"]}; stage {stage["name"]} (all stages: {", ".join(stages)})')
    print(f'# cd {shlex.quote(stage["cwd_abs"])} && {stage["command"]}')
    for key in sorted(env):
        print(f'export {key}={shlex.quote(env[key])}')
    print(f'export PATH={shlex.quote(str(Path(env["VIRTUAL_ENV"]) / "bin"))}:"$PATH"')
    return 0


def check_one(directory, manifest):
    """Return a list of (status, subject, detail) rows for one prepared recipe."""
    rows = []

    def ok(subject, detail=''):
        rows.append(('ok', subject, detail))

    def bad(subject, detail):
        rows.append(('MISMATCH', subject, detail))

    # the pins as the workflow states them now, against the pins recorded at prepare
    try:
        override = next((c['sha'] for c in manifest['checkouts'] if c['role'] == 'source'), None) if manifest['source_override'] else None
        now = read_recipe(manifest['recipe'], source_rev=override)
    except RecipeError as error:
        bad('workflow', 'cannot be read any more: %s' % error)
        now = None
    if now is not None:
        if now['workflow_sha256'] != manifest['workflow_sha256']:
            bad('workflow ' + manifest['workflow'], 'file changed since prepare (hash differs); pins may have moved')
        else:
            ok('workflow ' + manifest['workflow'], 'unchanged since prepare')
        want = {(c['repository'], c['path']): c['sha'] for c in now['checkouts'] if c['sha']}
        have = {(c['repository'], c['path']): c['sha'] for c in manifest['checkouts'] if c['sha']}
        for key in sorted(set(want) | set(have)):
            if want.get(key) != have.get(key):
                bad('pin %s at %s' % key, 'workflow says %s, prepared %s' % (want.get(key), have.get(key)))
    # the workflow's own verification lines must agree with its checkout pins
    by_path = {c['path'].rstrip('/'): c['sha'] for c in manifest['checkouts'] if c['sha']}
    for item in manifest['verify']:
        pinned = by_path.get(item['path'].rstrip('/'))
        if pinned is not None and pinned != item['sha']:
            bad('verify line ' + item['path'], f'workflow verifies {item["sha"]} but checks out {pinned}')
    overlay_paths = {}
    for overlay in manifest['overlays']:
        overlay_paths.setdefault(overlay['source_root'], {}).update(overlay['files'])
    for checkout in manifest['checkouts']:
        subject = f'{checkout["role"]} {checkout["repository"] or "(this repository)"} at {checkout["path"]}'
        path = Path(checkout['path_abs'])
        if not path.exists():
            bad(subject, 'directory missing')
            continue
        if checkout['role'] == 'qualification':
            head = git(ROOT, 'rev-parse', 'HEAD')
            (ok if head == checkout['head'] else bad)(subject, f'this repository head {head[:12]}, prepared {checkout["head"][:12]}')
            continue
        if checkout['role'] == 'self':
            continue
        head = git(path, 'rev-parse', 'HEAD')
        if head != checkout['sha']:
            bad(subject, f'head {head}, pinned {checkout["sha"]}')
            continue
        now_changed = tracked_changes(path)
        was = checkout.get('tracked_changes', {})
        drift = sorted(f for f in set(now_changed) | set(was) if now_changed.get(f, 'same-as-head') != was.get(f, 'same-as-head'))
        if drift:
            bad(subject, 'tracked files changed after prepare: ' + ', '.join(drift[:5]) + (' ...' if len(drift) > 5 else ''))
        else:
            ok(subject, f'head {head[:12]} as pinned' + (f'; {len(was)} tracked file(s) differ from it as recorded at prepare (overlay, install side effects)' if was else ''))
    for source_root, files in overlay_paths.items():
        missing = [f for f, digest in files.items() if not (Path(source_root) / f).is_file() or sha256_file(Path(source_root) / f) != digest]
        (bad if missing else ok)('overlay in ' + source_root, ('%d file(s) absent or changed: %s' % (len(missing), ', '.join(missing[:3]))) if missing else f'{len(files)} files as installed')
    for venv in manifest['venvs']:
        python = Path(venv['path']) / 'bin' / 'python'
        if not python.exists():
            bad('venv ' + venv['key'], 'missing')
            continue
        try:
            freeze = run([python, '-m', 'pip', 'freeze', '--all'], capture=True).splitlines()
        except RuntimeError as error:
            bad('venv ' + venv['key'], 'pip failed: ' + str(error)[:120])
            continue
        if freeze != venv['freeze']:
            diff = sorted(set(freeze) ^ set(venv['freeze']))
            bad('venv ' + venv['key'], 'installed packages differ from prepare: ' + ', '.join(diff[:5]))
        else:
            ok('venv ' + venv['key'], f'{len(freeze)} packages as at prepare (python {venv["python"]})')
        checkout_dirs = [Path(c['path_abs']).resolve() for c in manifest['checkouts'] if c['role'] in ('source', 'upstream', 'self')]
        try:
            editable = json.loads(run([python, '-m', 'pip', 'list', '--editable', '--format=json'], capture=True))
        except (RuntimeError, ValueError):
            editable = []
        for item in editable:
            location = Path(item.get('editable_project_location') or '.').resolve()
            if not any(location == d or d in location.parents for d in checkout_dirs):
                bad('venv ' + venv['key'], f'editable install {item.get("name")} points outside the checkouts: {location}')
    for stage in manifest['stages']:
        absent = [k for k, v in stage['env_resolved'].items() if v.startswith('/') and ':' not in v and not Path(v).exists()]
        (bad if absent else ok)('stage ' + stage['name'], ('paths missing for ' + ', '.join(absent)) if absent else f'{len(stage["env_resolved"])} variables resolve')
    return rows


def cmd_check(args):
    manifests = load_manifests(args.work, args.recipe or None)
    mismatches = 0
    for name, (directory, manifest) in manifests.items():
        print('recipe ' + name)
        for status, subject, detail in check_one(directory, manifest):
            mismatches += status != 'ok'
            print(f'  {status:8} {subject}: {detail}')
    print('result: %s' % ('%d mismatch(es)' % mismatches if mismatches else 'all pins and hashes match'))
    return 1 if mismatches else 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    for name, fn, text in (('plan', cmd_plan, 'print the recipe read from the workflows (offline)'),
                           ('prepare', cmd_prepare, 'clone the pinned revisions, apply the overlay, build the virtual environments'),
                           ('env', cmd_env, 'print the variables to export for one test stage'),
                           ('check', cmd_check, 'verify what is on disk against the pins')):
        p = sub.add_parser(name, help=text)
        p.set_defaults(fn=fn)
        p.add_argument('--recipe', action='append', metavar='WORKFLOW[:JOB]', help='repeatable; default set: ' + ', '.join(DEFAULT_RECIPES))
        if name != 'plan':
            p.add_argument('--work', type=Path, required=True, help='directory that holds the prepared environments')
        if name in ('plan', 'prepare'):
            p.add_argument('--source-rev', action='append', metavar='RECIPE=SHA', help='replace the owning-source commit of one recipe')
        if name == 'prepare':
            p.add_argument('--python', type=Path, help='interpreter for the virtual environments (default: the version the workflow names)')
            p.add_argument('--full-history', action='store_true', help='fetch full history instead of depth 1')
            p.add_argument('--force', action='store_true', help='rebuild a recipe directory that prepare made earlier')
        if name == 'env':
            p.add_argument('--stage', help='test stage name (default: the first)')
            p.add_argument('--json', action='store_true', help='print JSON instead of export lines')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (RecipeError, RuntimeError) as error:
        print('rc_env: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
