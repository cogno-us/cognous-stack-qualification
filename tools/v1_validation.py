"""Frozen-V1 validation controller helpers.

SPDX-License-Identifier: Apache-2.0

Subcommands
  plan            emit the GitHub Actions job matrix from the freeze manifest
  freeze-verify   verify every identity recorded in the freeze manifest
  check-workflow-pins  compare the sha literals of the controller workflow with manifest + overlay
  component-suite discover and run one component's own tests at its pinned commit
  aggregate       merge job results; refuse to promote missing, failed or skipped
                  mandatory coverage to PASS

This module never modifies product code, component pins or expected outcomes.
Status vocabulary: PASS, FAIL, INCONCLUSIVE, NOT RUN, NOT APPLICABLE.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "suites"))
import _pins  # noqa: E402  (the one source of pins: freeze manifest + refreeze overlay)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import declared_limits as DL  # noqa: E402  (declared known limits, read from the committed pre-registration twin)
STATUSES = ("PASS", "FAIL", "INCONCLUSIVE", "NOT RUN", "NOT APPLICABLE")
MAX_RETAINED_LOG = 5 * 1024 * 1024  # bytes of gzip retained per log
# Per-component pytest timeout. A timeout is INCONCLUSIVE, so it must sit well above the slowest suite: measured on a
# development host, gax_imx_transport takes about 167 s, constitutional_authority about 131 s and ODES runs about 3000
# tests; a shared runner can be several times slower. 900 s leaves a factor of five over the slowest measured suite.
# A freeze-manifest entry may still set its own test_timeout_seconds. The job-level limit of the workflow (40 minutes)
# covers one 900 s attempt plus setup; a timed-out attempt is not retried.
DEFAULT_TEST_TIMEOUT_SECONDS = 900
# Components whose own tests skip unless a pinned sibling component is installed (skips are INCONCLUSIVE rows).
# component key -> ((sibling key, pip targets tried in order, relative to the sibling checkout), ...)
SIBLING_PROVISIONING = {
    "moltbot_safe": (("control_plane", (".[runtime-authority]", ".")),),  # runtime tests need the Control Plane local-authority-effect contract
    "odes": (("replay_bundle", (".",)),),                                  # ODES tests need the accepted Replay revision installed
    # evidence pack tests import the pinned Replay importers and the Control Plane freshness module (33 skips without them)
    "governance_evidence_pack": (("replay_bundle", (".",)), ("control_plane", (".[runtime-authority]", "."))),
    # one Replay pairing test imports the pack importer (1 skip without it)
    "replay_bundle": (("governance_evidence_pack", (".",)),),
}


# Siblings installed editable from their git checkout. ODES identifies the installed Replay revision from the module's own git checkout
# (or pip's VCS commit, which a local-directory install does not record); a plain local install gives neither, so its tests skip.
EDITABLE_SIBLINGS = frozenset({"replay_bundle"})


def sibling_install_command(py, sb, target):
    """The pip command that installs one pinned sibling target (``.`` or ``.[extra]``, relative to the sibling checkout)."""
    spec = f"{sb['dir']}{'' if target == '.' else target[1:]}"
    return [py, "-m", "pip", "install", "-q", *(("-e",) if sb["component"] in EDITABLE_SIBLINGS else ()), spec]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(path, *args, check=True, timeout=300):
    proc = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_resolved(manifest_path, refreeze_log=None):
    """(manifest, applied): the freeze manifest overridden by the APPLIED entries of ``refreeze_log`` (None: no overlay).
    An inconsistent log (from_sha not the pin in force, unknown component) exits with a clear message."""
    manifest = load_manifest(manifest_path)
    if not refreeze_log:
        return manifest, []
    try:
        return _pins.apply_overlay(manifest, _pins.load_json(refreeze_log))
    except _pins.RefreezeError as exc:
        sys.exit(f"refreeze overlay error ({refreeze_log}): {exc}")


def all_components(manifest):
    """Yield (group, key, spec) for every pinned component."""
    for group in ("components_subject", "components_lock_remainder", "components_optional"):
        for key, spec in manifest.get(group, {}).items():
            yield group, key, spec


# ----------------------------------------------------------------- plan
def cmd_plan(args):
    manifest, _ = load_resolved(args.manifest, args.refreeze_log)
    include = []
    for group, key, spec in all_components(manifest):
        oses = ["ubuntu-latest", "windows-latest", "macos-latest"] if group != "components_optional" and not getattr(args, "linux_only", False) else ["ubuntu-latest"]
        for os_name in oses:
            pys = ["3.12"] + (["3.11"] if os_name == "ubuntu-latest" and group != "components_optional" else [])
            for py in pys:
                include.append({"component": key, "group": group, "repository": spec["repository"],
                                "sha": spec["sha"], "os": os_name, "python": py,
                                "timeout": int(spec.get("test_timeout_seconds", DEFAULT_TEST_TIMEOUT_SECONDS))})
    out = {"include": include}
    text = json.dumps(out, separators=(",", ":"))
    if args.out_file:
        Path(args.out_file).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_file).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            fh.write(f"matrix={text}\n")
    else:
        print(text)


# --------------------------------------------------------- freeze verify
def fetch_exact(repo_dir: Path, repository: str, sha: str):
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        subprocess.run(["git", "init", "-q", str(repo_dir)], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "remote", "add", "origin", f"https://github.com/{repository}.git"], check=True)
    git(repo_dir, "fetch", "-q", "--depth", "1", "origin", sha, timeout=600)
    git(repo_dir, "checkout", "-q", "--detach", "FETCH_HEAD")
    return git(repo_dir, "rev-parse", "HEAD")


def ls_remote_tag(repository: str, tag: str):
    proc = subprocess.run(["git", "ls-remote", "--tags", f"https://github.com/{repository}.git",
                           f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"], capture_output=True, text=True, timeout=120)
    peeled = direct = None
    for line in proc.stdout.splitlines():
        sha, ref = line.split("\t")
        if ref.endswith("^{}"):
            peeled = sha
        else:
            direct = sha
    return peeled or direct


def profile_pin_checks(prof, manifest, label, suffix="", require_authority=False):
    """[(check name, ok, expected, actual)] that a profile and a (resolved) manifest agree in BOTH directions (E-3).

    profile -> manifest: every profile component names a manifest repository at the manifest revision (as before).
    manifest -> profile: the profile lists at least one component, and every pinned subject component appears in it (by its profile_key)
    with its repository and the manifest (overlay) revision. A profile ``constitutional_authority`` section must equal the pinned authority
    (repository and revision); with ``require_authority`` the section must be present."""
    comps = prof.get("components")
    if not isinstance(comps, dict) or not comps:
        return [(f"{label} profile lists its components", False, "at least one component", comps)]
    byrepo = {s["repository"]: s["sha"] for _, _, s in all_components(manifest)}
    checks = [(f"{label} profile pin {name} equals manifest{suffix}", byrepo.get(spec.get("repository")) == spec.get("revision"), spec.get("revision"),
               byrepo.get(spec.get("repository"))) for name, spec in comps.items()]
    for key, spec in manifest["components_subject"].items():
        pk = spec.get("profile_key", key)
        entry = comps.get(pk) or {}
        checks.append((f"{label} profile lists pinned subject component {pk} at its manifest revision{suffix}",
                       entry.get("repository") == spec["repository"] and entry.get("revision") == spec["sha"], spec["sha"], entry.get("revision")))
    auth = manifest.get("components_lock_remainder", {}).get("constitutional_authority")
    section = prof.get("constitutional_authority")
    if auth is not None and (section is not None or require_authority):
        section = section if isinstance(section, dict) else {}
        checks.append((f"{label} profile constitutional_authority equals the pinned authority{suffix}",
                       section.get("repository") == auth["repository"] and section.get("revision") == auth["sha"], auth["sha"], section.get("revision")))
    return checks


def cmd_freeze_verify(args):
    m = load_manifest(args.manifest)  # ORIGINAL freeze: hub/profile/lock/tag identities are checked against what was frozen
    resolved, applied = load_resolved(args.manifest, args.refreeze_log)  # components that are fetched and qualified
    checks = []

    def check(name, ok, expected=None, actual=None, detail=None):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "expected": expected, "actual": actual, "detail": detail})

    hub = Path(args.hub_dir)
    qual = Path(args.qual_dir)
    ident = m["identities"]
    hub_head = git(hub, "rev-parse", "HEAD")
    check("hub head equals frozen hub head", hub_head == ident["hub"]["head"], ident["hub"]["head"], hub_head)
    tag_commit = ident["hub"]["tag_commit"]
    check("hub public-reference tag peels to recorded commit",
          ls_remote_tag(ident["hub"]["repository"], ident["hub"]["public_reference_tag"]) == tag_commit, tag_commit)
    anc = subprocess.run(["git", "-C", str(hub), "merge-base", "--is-ancestor", tag_commit, hub_head]).returncode == 0
    check("hub tag commit is an ancestor of hub head", anc)
    changed = sorted(git(hub, "diff", "--name-only", tag_commit, hub_head).splitlines())
    check("hub head differs from tag only by the recorded tag-recording files",
          changed == sorted(ident["hub"]["head_minus_tag_files"]), sorted(ident["hub"]["head_minus_tag_files"]), changed)
    for rel, expected in m["hub_file_hashes"].items():
        p = hub / rel
        actual = sha256_file(p) if p.exists() else None
        check(f"hub file hash {rel}", actual == expected, expected, actual)
    for rel, expected in m["qualification_file_hashes"].items():
        p = qual / rel
        actual = sha256_file(p) if p.exists() else None
        check(f"qualification file hash {rel}", actual == expected, expected, actual)
    q = ident["qualification"]
    anc = subprocess.run(["git", "-C", str(qual), "merge-base", "--is-ancestor", q["closeout"], "HEAD"]).returncode == 0
    check("qualification closeout is an ancestor of the harness checkout", anc, q["closeout"])
    check("qualification public-reference tag peels to closeout",
          ls_remote_tag(q["repository"], q["public_reference_tag"]) == q["tag_commit"] == q["closeout"], q["closeout"])
    rt = ident["runtime"]
    check("runtime public-reference tag peels to recorded sha",
          ls_remote_tag(rt["repository"], rt["public_reference_tag"]) == rt["sha"], rt["sha"])
    check("runtime quarantine tag exists", ls_remote_tag(rt["repository"], rt["quarantine_tag"]) is not None)
    # profile pins agree with manifest
    prof = json.loads((hub / m["profile"]["path"]).read_text())
    for name, ok, exp, act in profile_pin_checks(prof, m, "hub"):
        check(name, ok, exp, act)
    in_force = {}  # pin in force before each entry: the manifest pin, then the previous entry's to_sha (chained re-freezes)
    for eid, group, key, frm, to in applied:
        before = in_force.get((group, key), m[group][key]["sha"])
        check(f"refreeze {eid}: {key} from_sha equals the pin in force (freeze-manifest pin or the previous re-freeze's to_sha) and to_sha is a distinct 40-hex commit",
              before == frm and re.fullmatch(r"[0-9a-f]{40}", to) is not None and to != frm, before, to)
        in_force[(group, key)] = to
    # the qualification profile (the original, or the r1 profile via --qual-profile) must equal manifest + overlay
    qprof_path = qual / (args.qual_profile or m["profile"]["qualification_profile"])
    qprof = json.loads(qprof_path.read_text())
    auth_moved = any(k == "constitutional_authority" for _, _, k, _, _ in applied)
    for name, ok, exp, act in profile_pin_checks(qprof, resolved, "qualification", " + refreeze overlay" if applied else "", require_authority=auth_moved):
        check(name, ok, exp, act)
    lock = json.loads((hub / "component-lock.json").read_text())
    for key, spec in {**m["components_lock_remainder"], **m["components_optional"]}.items():  # hub lock is frozen: original pins
        check(f"hub lock pin {key} equals manifest", lock["components"][key]["sha"] == spec["sha"], spec["sha"], lock["components"][key]["sha"])
    # fetch every pinned component exactly
    work = Path(args.work)
    fetched = {}  # key -> record; never shadows `resolved` (the manifest-plus-overlay pins that are iterated)
    for group, key, spec in all_components(resolved):
        try:
            got = fetch_exact(work / key, spec["repository"], spec["sha"])
            tree = git(work / key, "rev-parse", "HEAD^{tree}")
            fetched[key] = {"repository": spec["repository"], "commit": got, "tree": tree, "group": group}
            check(f"component {key} resolves to pinned commit", got == spec["sha"], spec["sha"], got)
        except Exception as exc:  # noqa: BLE001 - record, never hide
            check(f"component {key} resolves to pinned commit", False, spec["sha"], None, str(exc)[:500])
    out = {"schema": "cognous.v1-validation-freeze-verification/1", "validation_id": m["validation_id"],
           "refreeze_applied": [{"id": e, "component": k, "from_sha": f, "to_sha": t} for e, _, k, f, t in applied],
           "harness_revision": os.environ.get("GITHUB_SHA") or git(qual, "rev-parse", "HEAD"),
           "workflow_run": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
           "python": sys.version, "platform": platform.platform(), "components": fetched,
           "components_expected": sorted(key for _, key, _ in all_components(resolved)), "checks": checks,
           "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for c in checks:
        print(("ok   " if c["status"] == "PASS" else "FAIL ") + c["check"])
    sys.exit(0 if out["status"] == "PASS" else 1)


# ----------------------------------------------------- workflow pin literals
# F-T3-1: the workflow is read as YAML structure (PyYAML, hash-locked in .github/locks/jsonschema-pyyaml-c943d3.txt), not with regular
# expressions over its text, so key order, comments, quoting, CRLF, block or flow style and multi-line matrix entries do not matter.
_HEX40_RE = re.compile(r"(?<![0-9A-Za-z])[0-9A-Fa-f]{40}(?![0-9A-Za-z])")
_REPO_KEYS = ("repository", "repo")
_REF_KEYS = ("ref", "sha")


def _yaml_module():
    try:
        import yaml
    except ImportError as exc:  # fail closed: a check that cannot parse the workflow must not pass it
        raise SystemExit("PyYAML is required to check the workflow pins (python -m pip install --require-hashes -r .github/locks/jsonschema-pyyaml-c943d3.txt)") from exc
    return yaml


def _load_workflow_yaml(text):
    """Parse a workflow as YAML with every plain scalar kept as a string (a 40-digit sha is not an integer) and duplicate mapping keys refused."""
    yaml = _yaml_module()

    class _Loader(yaml.SafeLoader):
        pass

    _Loader.yaml_implicit_resolvers = {k: [(t, r) for t, r in v if t == "tag:yaml.org,2002:null"] for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}

    def construct_mapping(loader, node, deep=False):
        seen = set()
        for k, _ in node.value:
            key = loader.construct_object(k, deep=True)
            if key in seen:
                raise yaml.YAMLError(f"duplicate mapping key {key!r} (line {k.start_mark.line + 1})")
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    _Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        return yaml.load(text, Loader=_Loader)
    except yaml.YAMLError as exc:  # refuse, never skip
        raise SystemExit(f"workflow is not valid YAML for the pin check: {exc}") from exc


def _norm_repo(value):
    """owner/name of a repository reference (lower case; URL prefix, .git suffix and quotes dropped), or None."""
    if not isinstance(value, str):
        return None
    v = value.strip().strip("'\"")
    v = re.sub(r"^(?:https?://|git@)?(?:www\.)?github\.com[/:]", "", v, flags=re.I)
    v = re.sub(r"\.git$", "", v)
    return v.lower() if re.fullmatch(r"[\w.-]+/[\w.-]+", v) else None


def _walk_yaml(node):
    """Yield every mapping and every string (keys included) of a parsed YAML document."""
    if isinstance(node, dict):
        yield node
        for k, v in node.items():
            yield from _walk_yaml(k)
            yield from _walk_yaml(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_yaml(v)
    elif isinstance(node, str):
        yield node


def _name_hits(string, pinned):
    return sorted((m.start(), p) for p in pinned for m in re.finditer(r"(?<![\w.-])" + re.escape(p) + r"(?:\.git)?(?![\w.-])", string, re.I))


def workflow_pin_literals(text, pinned=()):
    """[(repository (lower case), ref literal)] for every pairing in a workflow text, read as YAML structure.

    1. A mapping with a ``repository`` or ``repo`` key naming ``owner/name`` pairs that repository with every ``ref`` and ``sha`` of the same
       mapping (whatever the key order or style: a checkout ``with:`` block, a one-line or multi-line matrix entry) and with every 40-hex
       literal in its other string values.
    2. With ``pinned`` (repository names in force), every 40-hex literal of any string (a ``run`` script, an environment value, a ``git clone``
       command line) is paired with the nearest preceding pinned repository name of the same string, else the nearest following one.
    Raises SystemExit when the text is not valid YAML or repeats a mapping key."""
    doc = _load_workflow_yaml(text)
    pairs, pinned = [], [p.lower() for p in pinned]
    for node in _walk_yaml(doc):
        if isinstance(node, dict):
            repos = {r for r in (_norm_repo(node.get(k)) for k in _REPO_KEYS) if r}
            for r in repos:
                for k in _REF_KEYS:
                    if isinstance(node.get(k), str):
                        pairs.append((r, node[k].strip()))
                for k, v in node.items():
                    if k not in _REF_KEYS and k not in _REPO_KEYS and isinstance(v, str):
                        pairs.extend((r, h) for h in _HEX40_RE.findall(v))
        elif isinstance(node, str) and pinned:
            hits = _name_hits(node, pinned)
            for m in _HEX40_RE.finditer(node):
                before = [h for h in hits if h[0] < m.start()]
                near = before[-1] if before else (hits[0] if hits else None)
                if near:
                    pairs.append((near[1], m.group(0)))
    return pairs


def workflow_pin_mismatches(text, resolved):
    """Messages for every pinned-repository literal of the workflow that differs from the pin in force (E-4, F-T3-1).

    ``resolved`` is the manifest with the refreeze overlay applied (component pins) and the hub head of its identities. A repository that is
    not pinned (third-party actions, other repositories) is not checked. A pinned repository that the workflow names (in any YAML string)
    but for which it carries no sha literal at all is reported too (a literal removed or hidden behind an expression); a pinned repository
    the workflow never names (for example one whose pin is taken from the plan at run time) needs no literal."""
    pins = {s["repository"].lower(): s["sha"] for _, _, s in all_components(resolved)}
    hub = resolved["identities"]["hub"]
    pins[hub["repository"].lower()] = hub["head"]
    lits = workflow_pin_literals(text, pins)
    bad = [f"{repo}: workflow literal {lit!r} is not the pin in force {pins[repo]}" for repo, lit in lits if repo in pins and lit != pins[repo]]
    named = {p for node in _walk_yaml(_load_workflow_yaml(text)) if isinstance(node, str) for _, p in _name_hits(node, pins)}
    have = {repo for repo, _ in lits}
    bad += [f"{repo}: named by the workflow but no sha literal is present for it" for repo in sorted(named - have)]
    return bad


def cmd_check_workflow_pins(args):
    resolved, _ = load_resolved(args.manifest, args.refreeze_log)
    bad = workflow_pin_mismatches(Path(args.workflow).read_text(encoding="utf-8"), resolved)
    for b in bad:
        print("FAIL " + b)
    if bad:
        sys.exit(f"{len(bad)} workflow pin literal(s) differ from the manifest plus overlay")
    print("ok   every pinned-repository literal of the workflow equals the pin in force")


# ------------------------------------------------------- component suite
def run(cmd, cwd, timeout, log):
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, errors="replace")
        log.write(f"$ {' '.join(map(str, cmd))}\n{proc.stdout}\n{proc.stderr}\n[exit {proc.returncode}]\n")
        return proc.returncode, proc.stdout, time.monotonic() - start, False
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"")
        out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        log.write(f"$ {' '.join(map(str, cmd))}\n{out}\n[TIMEOUT after {timeout}s]\n")
        return 124, out, time.monotonic() - start, True


def junit_counts(path: Path):
    if not path.exists():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    t = f = e = s = 0
    for tc in root.iter("testcase"):
        t += 1
        if tc.find("failure") is not None:
            f += 1
        if tc.find("error") is not None:
            e += 1
        if tc.find("skipped") is not None:
            s += 1
    return {"testcases": t, "failures": f, "errors": e, "skipped": s}


def retain_log(text: str, dest: Path):
    data = text.encode("utf-8", "replace")
    gz = gzip.compress(data, 9)
    info = {"sha256_uncompressed": hashlib.sha256(data).hexdigest(), "bytes_uncompressed": len(data), "retained": True}
    if len(gz) > MAX_RETAINED_LOG:
        info["retained"] = False
        info["limitation"] = f"gzip log {len(gz)} bytes exceeds {MAX_RETAINED_LOG}; not retained in Git"
    else:
        dest.write_bytes(gz)
        info["file"] = dest.name
    return info


def _resolve_pin_file(explicit, env_name):
    value = explicit or os.environ.get(env_name)
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise RuntimeError(f"{env_name or 'pins file'} names {value}, which is not a file")
    return path


def provision_siblings(component, siblings_root, manifest_path, refreeze_log, fetch=None):
    """Fetch the exact pinned sibling components a component's tests need and return their records (pins in force: manifest plus overlay).

    Raises RuntimeError when a sibling cannot be resolved or fetched at its pin; nothing is installed here."""
    fetch = fetch or fetch_exact
    wanted = SIBLING_PROVISIONING.get(component, ())
    if not wanted:
        return []
    if manifest_path is None:
        raise RuntimeError("no freeze manifest for the sibling pins (pass --pins-manifest or set MANIFEST)")
    manifest, _ = load_resolved(manifest_path, refreeze_log)
    specs = {key: spec for _, key, spec in all_components(manifest)}
    records = []
    for key, targets in wanted:
        if key not in specs:
            raise RuntimeError(f"sibling {key} is not in the freeze manifest")
        spec = specs[key]
        dest = Path(siblings_root) / key
        actual = fetch(dest, spec["repository"], spec["sha"])
        if actual != spec["sha"]:
            raise RuntimeError(f"sibling {key} resolved to {actual}, not its pin {spec['sha']}")
        records.append({"component": key, "repository": spec["repository"], "pinned_sha": spec["sha"], "actual_sha": actual,
                        "dir": str(dest), "targets": list(targets)})
    return records


def cmd_component_suite(args):
    repo = Path(args.repo_dir).resolve()
    if args.fetch:
        fetch_exact(repo, args.repository, args.sha)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    actual = git(repo, "rev-parse", "HEAD")
    result = {"schema": "cognous.v1-validation-job/1", "component": args.component, "repository": args.repository,
              "pinned_sha": args.sha, "actual_sha": actual, "os": args.os_name, "python": platform.python_version(),
              "platform": platform.platform(), "workflow_run": os.environ.get("GITHUB_RUN_ID"),
              "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "job": os.environ.get("GITHUB_JOB"),
              "attempts": [], "timeout_seconds": args.timeout}
    if actual != args.sha:
        result.update(status="FAIL", classification="setup/harness defect", reason="checked-out commit differs from pin")
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        sys.exit(1)
    siblings = []
    if args.component in SIBLING_PROVISIONING:
        if args.no_siblings:
            result["siblings"] = "disabled by --no-siblings"
        else:
            try:
                manifest_path = _resolve_pin_file(args.pins_manifest, "MANIFEST")
                log_path = _resolve_pin_file(args.refreeze_log, "REFREEZE_LOG")
                siblings = provision_siblings(args.component, repo.parent / (repo.name + "-siblings"), manifest_path, log_path)
                result["siblings"] = [{k: v for k, v in sb.items() if k != "targets"} for sb in siblings]
            except Exception as exc:  # noqa: BLE001 - recorded, never hidden
                result.update(status="FAIL", classification="setup/harness defect", reason=f"sibling provisioning failed: {str(exc)[:500]}")
                (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
                sys.exit(1)
    # inventory (independent of whether tests can run)
    tests_dirs = [str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("test*") if p.is_dir() and ".git" not in p.parts and "node_modules" not in p.parts][:50]
    test_files = sorted(str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("test_*.py") if ".git" not in p.parts and "node_modules" not in p.parts)
    wfs = sorted(p.name for p in (repo / ".github" / "workflows").glob("*.y*ml")) if (repo / ".github" / "workflows").exists() else []
    runs_on = {}
    wf_dir = repo / ".github" / "workflows"
    for wf in (wf_dir.glob("*.y*ml") if wf_dir.exists() else []):
        txt = wf.read_text(encoding="utf-8", errors="replace")
        found = sorted(set(re.findall(r"runs-on:\s*([^\n#]+)", txt)) | set(re.findall(r"^\s*os:\s*\[([^\]]+)\]", txt, re.M)))
        if found:
            runs_on[wf.name] = [x.strip() for x in found]
    result["inventory"] = {"ci_runs_on": runs_on, "test_dirs": tests_dirs, "test_files": test_files, "test_file_count": len(test_files), "ci_workflows": wfs,
                           "has_pyproject": (repo / "pyproject.toml").exists(), "has_requirements": sorted(p.name for p in repo.glob("requirements*.txt"))}
    py = sys.executable
    log = out / "job.log"
    with open(log, "w", encoding="utf-8") as fh:
        for attempt in (1, 2):
            rec = {"attempt": attempt}
            setup_ok = True
            installs = []
            fh.write(f"==== attempt {attempt}\n")
            run([py, "-m", "pip", "install", "-q", "pytest"], repo, 600, fh)
            sibling_installs = []
            for sb in siblings:  # pinned siblings first: the component's own requirements are installed afterwards and keep precedence
                installed = False
                for target in sb["targets"]:
                    rc, _, _, _ = run(sibling_install_command(py, sb, target), repo, 900, fh)
                    sibling_installs.append({"sibling": sb["component"], "target": target, "rc": rc})
                    installed = rc == 0
                    if installed:
                        break
                setup_ok = setup_ok and installed
            if sibling_installs:
                rec["sibling_installs"] = sibling_installs
                rec["sibling_install_ok"] = setup_ok  # visible on its own: the project install below cannot overwrite it
            if (repo / "pyproject.toml").exists() or (repo / "setup.py").exists():
                for extra in (".[dev,test]", ".[dev]", ".[test]", "."):
                    rc, _, _, _ = run([py, "-m", "pip", "install", "-q", "-e", extra], repo, 900, fh)
                    installs.append({"target": extra, "rc": rc})
                    if rc == 0:
                        break
                setup_ok = setup_ok and bool(installs) and installs[-1]["rc"] == 0
            for req in sorted(repo.glob("requirements*.txt")):
                rc, _, _, _ = run([py, "-m", "pip", "install", "-q", "-r", req.name], repo, 900, fh)
                installs.append({"target": req.name, "rc": rc})
                setup_ok = setup_ok and rc == 0
            # dedicated harness requirements that the component's own tests tell us to install (they skip otherwise)
            for req in sorted((repo / "testing" / "harness").glob("requirements*.txt")) if (repo / "testing" / "harness").is_dir() else []:
                rel = str(req.relative_to(repo)).replace("\\", "/")
                rc, _, _, _ = run([py, "-m", "pip", "install", "-q", "-r", rel], repo, 900, fh)
                installs.append({"target": rel, "rc": rc})
                setup_ok = setup_ok and rc == 0
            rec["installs"] = installs
            rc, freeze, _, _ = run([py, "-m", "pip", "freeze"], repo, 120, fh)
            if attempt == 1:
                (out / "pip-freeze.txt").write_text(freeze, encoding="utf-8")
            junit = out.resolve() / f"junit-attempt{attempt}.xml"
            if not test_files:
                rec.update(outcome="NOT RUN", reason="no test_*.py discovered in this component at the pinned commit")
                result["attempts"].append(rec)
                break
            rc, stdout, secs, timed_out = run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"], repo, args.timeout, fh)
            counts = junit_counts(junit)
            rec.update(returncode=rc, execution_seconds=round(secs, 2), timed_out=timed_out, counts=counts, setup_ok=setup_ok)
            if timed_out:
                rec.update(outcome="INCONCLUSIVE", reason=f"timeout after {args.timeout}s")
            elif rc == 0 and counts and counts["testcases"] > 0 and counts["failures"] == counts["errors"] == 0:
                rec.update(outcome="PASS")
            elif rc == 5:
                rec.update(outcome="NOT RUN", reason="pytest collected no tests")
            elif counts and (counts["failures"] or counts["errors"]) and counts["testcases"] > 0:
                rec.update(outcome="FAIL", reason="test failures/errors")
            else:
                rec.update(outcome="INCONCLUSIVE", reason="pytest produced no usable JUnit (collection/setup error)")
            result["attempts"].append(rec)
            # at most one automatic retry, only for a plausible setup/transient cause
            retry = (not setup_ok) or (rec["outcome"] == "INCONCLUSIVE" and not timed_out)
            if attempt == 1 and retry:
                continue
            break
    final = result["attempts"][-1]
    result["status"] = final["outcome"]
    result["reason"] = final.get("reason")
    if len(result["attempts"]) > 1:
        result["retry_note"] = "one automatic retry after a plausible setup/transient cause; both attempts preserved"
        result["attempt_outcomes"] = [a.get("outcome") for a in result["attempts"]]
        if final["outcome"] == "PASS" and result["attempts"][0]["outcome"] != "PASS":
            result["flaky_or_setup"] = True  # reported by the job row, the summary and the markdown; it does not block the verdict
    result["log"] = retain_log(log.read_text(encoding="utf-8", errors="replace"), out / "job.log.gz")
    log.unlink()
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("component", "os", "python", "status", "reason")}))
    sys.exit(0)  # the aggregate decides; a failing suite is evidence, not a workflow error


def pinned_sources(manifest):
    """Every pinned public source of the freeze: subject and lock-remainder components, the hub and the qualification closeout."""
    return _pins.pinned_sources(manifest)


def cmd_probe_suite(args):
    """Run the validation probes (suites/v1-probes) against one exactly pinned component. A failing probe is a finding, not a harness error.

    With --pins-manifest, --repo-dir becomes a directory of exact checkouts of ALL pinned public sources (one subdirectory per
    freeze-manifest key) for multi-repository probes such as the SR-3 provenance scan; --repository/--sha are then not used.
    With --full-history the single pinned checkout is unshallowed (for probes that read git history)."""
    repo = Path(args.repo_dir).resolve()
    pins = None
    if args.pins_manifest:
        manifest, _ = load_resolved(args.pins_manifest, args.refreeze_log)
        pins = pinned_sources(manifest)
        actuals = {k: fetch_exact(repo / k, r, sha) for k, (r, sha) in pins.items()}
        args.repository = "multiple:" + ",".join(sorted(pins))
        args.sha = hashlib.sha256(json.dumps(sorted(pins.items())).encode()).hexdigest()
        actual = args.sha if all(actuals[k] == pins[k][1] for k in pins) else "mismatch:" + json.dumps(
            {k: actuals[k] for k in pins if actuals[k] != pins[k][1]})
    else:
        actual = fetch_exact(repo, args.repository, args.sha)
        if args.full_history and git(repo, "rev-parse", "--is-shallow-repository") == "true":
            git(repo, "fetch", "-q", "--unshallow", "origin", timeout=900)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    result = {"schema": "cognous.v1-validation-job/1", "component": args.component, "repository": args.repository, "pinned_sha": args.sha,
              "actual_sha": actual, "os": args.os_name, "python": platform.python_version(), "workflow_run": os.environ.get("GITHUB_RUN_ID"),
              "kind": "probe-suite", "attempts": []}
    if actual != args.sha:
        result.update(status="FAIL", classification="setup/harness defect", reason="checked-out commit differs from pin")
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n"); sys.exit(1)
    py = sys.executable
    junit = out.resolve() / "junit.xml"
    with open(out / "job.log", "w", encoding="utf-8") as fh:
        run([py, "-m", "pip", "install", "-q", "pytest", "httpx"], repo, 600, fh)
        reqs = [] if pins else [r for r in sorted(repo.glob("requirements*.txt")) if "dev" not in r.name]
        for req in reqs:
            run([py, "-m", "pip", "install", "-q", "-r", req.name], repo, 900, fh)
        if not reqs and not pins and (repo / "pyproject.toml").exists():
            # pyproject-only component: install its declared runtime dependencies, never the project itself
            # (the probes import the pinned source tree directly, so the checkout stays unmodified).
            import tomllib
            deps = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8")).get("project", {}).get("dependencies", [])
            if deps:
                run([py, "-m", "pip", "install", "-q", *deps], repo, 900, fh)
        if args.harness_requirements and not pins:
            # dedicated harness requirements that the component's own checks tell us to install (they skip or fail without them)
            hdir = repo / "testing" / "harness"
            for req in sorted(hdir.glob("requirements*.txt")) if hdir.is_dir() else []:
                run([py, "-m", "pip", "install", "-q", "-r", str(req.relative_to(repo)).replace("\\", "/")], repo, 900, fh)
        if args.extras and not pins and (repo / "pyproject.toml").exists():
            import tomllib
            optional = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8")).get("project", {}).get("optional-dependencies", {})
            extra_deps = [d for name in args.extras.split(",") for d in optional.get(name.strip(), [])]
            if extra_deps:
                run([py, "-m", "pip", "install", "-q", *extra_deps], repo, 900, fh)
        if args.npm_dir:
            run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], repo / args.npm_dir, 900, fh)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **{args.env_var: str(repo)})
        env["PROBE_REPORT_DIR"] = str(out.resolve())  # probes that produce a structured report (SR-3 scan) write it next to junit.xml
        if args.pins_manifest:
            env["PROBE_FREEZE_MANIFEST"] = str(Path(args.pins_manifest).resolve())
            if args.refreeze_log:
                env["PROBE_REFREEZE_LOG"] = str(Path(args.refreeze_log).resolve())  # the probe applies the same overlay
        suite = Path(args.suite).resolve()
        start = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", str(suite)], cwd=suite, env=env,
                                  capture_output=True, text=True, timeout=args.timeout, errors="replace")
            returncode = proc.returncode
            fh.write(proc.stdout + proc.stderr + f"[exit {proc.returncode}]\n")
        except subprocess.TimeoutExpired as exc:
            timed_out, returncode = True, 124
            partial = [x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "") for x in (exc.stdout, exc.stderr)]
            fh.write("".join(partial) + f"[TIMEOUT after {args.timeout}s]\n")
    counts = junit_counts(junit)  # partial junit, if any, is kept and counted; it never turns a timeout into a pass
    ran = bool(counts and counts["testcases"] > 0) and not timed_out
    result["attempts"].append({"attempt": 1, "returncode": returncode, "counts": counts, "execution_seconds": round(time.monotonic() - start, 2),
                               "outcome": "PASS" if ran else "INCONCLUSIVE"})
    result["status"] = "PASS" if ran else "INCONCLUSIVE"
    if timed_out:
        result["reason"] = f"probe suite timed out after {args.timeout} s"
    else:
        result["reason"] = "probe harness executed; individual probe outcomes are in junit.xml" if ran else "no probe results produced"
    result["log"] = retain_log((out / "job.log").read_text(encoding="utf-8", errors="replace"), out / "job.log.gz")
    (out / "job.log").unlink()
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("component", "status", "reason")}))


# -------------------------------------------------------------- aggregate
def freeze_record_problem(freeze, expected_jobs, validation_id=None):
    """Why a freeze-verification record cannot count as PASS proof of the pinned components, or None.

    The record must carry ``components_expected`` (written by freeze-verify), at least one component, a ``components`` map that lists exactly
    those components, no failed check under a PASS status and, when a plan is present, exactly the plan's component set. A record without
    ``components_expected`` (the legacy shape, for example the retained g6-r10 record with 0 components) is a problem: it proves no pinned
    component was fetched. No record at all is not a record problem here; the caller reads it as NOT RUN."""
    if not freeze:
        return None
    if validation_id is not None and freeze.get("validation_id") != validation_id:
        return f"freeze record is for validation id {freeze.get('validation_id')!r}, not {validation_id!r}"
    if "components_expected" not in freeze:
        return "freeze record lacks components_expected (legacy record): it is not proof that the pinned components were fetched"
    exp, got = freeze.get("components_expected"), freeze.get("components")
    if not isinstance(exp, list) or not exp or not isinstance(got, dict):
        return "freeze record lists no expected components"
    if set(exp) != set(got) or len(exp) != len(set(exp)):
        return f"freeze record components {sorted(got)} differ from its expected set {sorted(exp)}"
    bad = [c.get("check") for c in freeze.get("checks") or [] if isinstance(c, dict) and c.get("status") != "PASS"]
    if bad:
        return f"freeze record has failed checks under its status: {bad[:3]}"
    plan_set = {e["component"] for e in expected_jobs}
    if plan_set and plan_set != set(exp):
        return f"freeze record components differ from the plan's component set ({sorted(plan_set ^ set(exp))})"
    return None


def freeze_components_proof(freeze):
    if not freeze:
        return "no freeze record"
    return "verified" if "components_expected" in freeze else "legacy record without components_expected: not proof that pinned components were fetched"


def verdict(requirements):
    """Selected-V1 verdict. Never promotes missing, failed or skipped mandatory coverage."""
    mandatory = [r for r in requirements if r.get("mandatory", True)]
    if any(r["status"] == "FAIL" for r in mandatory):
        return "FAIL"
    for r in mandatory:
        if r["status"] == "NOT APPLICABLE":
            if not r.get("not_applicable_reason"):
                return "INCOMPLETE"
        elif r["status"] != "PASS":
            return "INCOMPLETE"
    return "PASS" if mandatory else "INCOMPLETE"


def full_catalog_status(requirements):
    """Reporting only. Real status of EVERY row (scope-reduced rows included); a scope-reduced row is never counted as PASS.

    unreduced_mandatory_verdict is the verdict rule applied to the rows that were mandatory before any scope reduction
    (currently mandatory rows plus rows carrying a scope_reduction record). It does not feed the selected verdict.
    """
    unreduced = [r for r in requirements if r.get("mandatory", True) or r.get("scope_reduction")]
    return {"note": "computed over ALL rows with their real statuses, including scope-reduced rows; scope reduction never converts a row to PASS",
            "rows": len(requirements),
            "status_counts": {st: sum(1 for r in requirements if r["status"] == st) for st in STATUSES},
            "unreduced_mandatory_rows": len(unreduced),
            "unreduced_mandatory_status_counts": {st: sum(1 for r in unreduced if r["status"] == st) for st in STATUSES},
            "unreduced_mandatory_verdict": verdict([dict(r, mandatory=True) for r in unreduced])}


def scope_reduction_block(requirements):
    """Reporting only. Every row moved out of the mandatory claim by a scope-reduction decision, with its real status."""
    moved = [r for r in requirements if r.get("scope_reduction")]
    return {"note": "rows moved out of the V1 mandatory claim into documented known limitations; their statuses, selectors and results are unchanged",
            "count": len(moved),
            "rows": [{"id": r["id"], "decision": r["scope_reduction"].get("decision"), "category": r["scope_reduction"].get("category"),
                      "final_status": r["status"], "declared_final_status": r["scope_reduction"].get("final_status"), "mandatory": bool(r.get("mandatory", True))} for r in moved]}


def _case_info(tc):
    """The detailed outcome of one JUnit testcase: passed, failed, skipped, or xfailed (a strict or plain expected failure that failed).

    A strict xfail that passes is written by pytest as a failure with an XPASS(strict) message; it is kept as failed and flagged."""
    fail = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
    if fail is not None:
        unexpected = "XPASS(strict)" in (fail.get("message") or "")
        return {"kind": "failed", "unexpected_pass": unexpected}
    sk = tc.find("skipped")
    if sk is not None:
        return {"kind": "xfailed" if sk.get("type") == "pytest.xfail" else "skipped", "unexpected_pass": False}
    return {"kind": "passed", "unexpected_pass": False}


def load_junit_index(inputs: Path, results, detail=False):
    """component -> list of (classname, name, outcome). Only Linux/3.12 component runs plus single-instance jobs count as selector evidence.

    With detail=True each tuple carries a fourth member, the _case_info dict (xfailed vs skipped, unexpected strict pass)."""
    index = {}
    for r in results:
        comp = r.get("component")
        if not comp or (r.get("os") not in (None, "ubuntu-latest")) or str(r.get("python", "3.12"))[:4] not in ("3.12", ""):
            continue
        d = inputs / r["_dir"]
        files = sorted(d.glob("junit-attempt*.xml"))[-1:] or sorted(d.rglob("junit.xml"))
        for f in files:
            try:
                root = ET.parse(f).getroot()
            except ET.ParseError:
                continue
            for tc in root.iter("testcase"):
                out = "failed" if (tc.find("failure") is not None or tc.find("error") is not None) else "skipped" if tc.find("skipped") is not None else "passed"
                row = (tc.get("classname", ""), tc.get("name", ""), out)
                index.setdefault(comp, []).append(row + (_case_info(tc),) if detail else row)
    return index


def _kind(t):
    return t[3]["kind"] if len(t) > 3 else t[2]


# Job records that carry the outcome of a gating audit step: PASS only when the record says the audit step succeeded (E-8). A record without
# the field (written before the field existed) is not PASS proof for these components.
JOB_AUDIT_COMPONENTS = {"native-f5b-suite": "audit_outcome"}


def effective_job_status(record):
    """The status of a job record as the requirement rows read it: PASS is kept only when the record's audit field, where one is required, is
    'success' and, where the record carries the exit code of its pytest session (``pytest_exit``), that code is 0 (F-T2-2)."""
    st = record.get("status")
    field = JOB_AUDIT_COMPONENTS.get(record.get("component"))
    if st == "PASS" and field and record.get(field) != "success":
        return "INCONCLUSIVE"
    if st == "PASS" and record.get("pytest_exit") not in (None, 0):
        return "INCONCLUSIVE"  # F-T2-2: a pytest session that exited non-zero is not PASS whatever its (possibly partial) JUnit says
    return st


# Job-kind rows whose job must have run with zero skipped tests (the same fail-closed rule the native-f5b job applies to itself).
# Component-suite rows keep their own semantics: retained component suites carry skips (control_plane 1, replay_bundle 17), and
# qual-tooling (non-mandatory, 1 skip) and matched-refund are not listed.
JOB_ZERO_SKIP_COMPONENTS = frozenset({"hub-tests"})
# Pytest-session job rows: PASS needs at least `min_cases` executed cases (the row's optional integer field; default 1) when the job's counts are
# known. The retained counts (hub-tests 653) are far above the default; no other number is invented here (F-T2-2).
JOB_MIN_CASES_COMPONENTS = frozenset({"hub-tests", "qual-tooling"})


def validate_requirements(doc):
    """Refuse a malformed requirements document (E-10). Raises ValueError naming the row.

    A `tests` row needs at least one selector; every selector needs a component, a compilable non-empty regular expression and an integer
    min of at least 1 (min defaults to 1), so a row can never be PASS with zero executed cases by construction. Row ids must be unique."""
    seen = set()
    for r in doc.get("requirements", []):
        rid = r.get("id")
        if not rid or rid in seen:
            raise ValueError(f"requirement row id {rid!r} is missing or duplicated")
        seen.add(rid)
        if r.get("kind", "tests") == "job" and "min_cases" in r:
            mc = r["min_cases"]
            if isinstance(mc, bool) or not isinstance(mc, int) or mc < 1:
                raise ValueError(f"requirement {rid}: job min_cases must be an integer of at least 1 (got {mc!r})")
        if r.get("kind", "tests") != "tests":
            continue
        sels = r.get("selectors")
        if not isinstance(sels, list) or not sels:
            raise ValueError(f"requirement {rid}: a tests row needs at least one selector")
        for sel in sels:
            mn = sel.get("min", 1)
            if not sel.get("component") or not isinstance(sel.get("re"), str) or not sel["re"]:
                raise ValueError(f"requirement {rid}: selector needs a component and a non-empty re: {sel}")
            if isinstance(mn, bool) or not isinstance(mn, int) or mn < 1:
                raise ValueError(f"requirement {rid}: selector min must be an integer of at least 1 (got {mn!r})")
            try:
                re.compile(sel["re"])
            except re.error as exc:
                raise ValueError(f"requirement {rid}: selector re does not compile: {exc}") from exc


def evaluate_requirements(doc, index, job_status, declared=None, job_counts_by_component=None):
    """Compute each requirement's status from executed evidence. A requirement is PASS only when adequate evidence executed and passed.

    declared: the record of declared_limits.load() or None. With a record, a `tests` row is computed over the matched cases that are NOT
    declared known limits: an undeclared failure is FAIL, an undeclared skip (a strict xfail counts as skipped) is INCONCLUSIVE.
    The minimum of every selector is still measured over ALL matched cases. Declared cases matched by the row are listed with their
    actual outcome (DECLARED-LIMIT); a declared test the row's selector would match but that was not run is listed as NOT RUN.
    When every case a selector matched is declared (zero undeclared cases remain) the row is INCONCLUSIVE, never PASS.
    A declared strict expected failure that passes (XPASS) makes the row FAIL; a declared test the row would select that was not run makes it INCONCLUSIVE.
    Without a record (declared=None) nothing is declared and the rule is the one in force before declared limits were reported.
    A declared case observed as passed or skipped (not failed or xfailed) is listed as a reportable condition; a skipped one also makes the row INCONCLUSIVE.
    job_counts_by_component: component -> junit counts of the job; when given, a job row of JOB_ZERO_SKIP_COMPONENTS is PASS only with
    testcases > 0 and skipped == 0 (missing counts are not PASS). None leaves job rows as before.
    """
    dmap = DL.by_component(declared) if declared is not None else {}
    evaluated = []
    for r in doc.get("requirements", []):
        r = dict(r)
        kind = r.get("kind", "tests")
        r.setdefault("mandatory", True)
        if kind == "tests":
            hits, fails, skips, undeclared_total, detail = 0, 0, 0, 0, []
            listed, not_run, conditions, zero_undeclared, xpassed, unmet = {}, {}, [], [], [], []
            for sel in r.get("selectors", []):
                rx = re.compile(sel["re"], re.I)
                comp = sel["component"]
                cases = index.get(comp, [])
                declared_here = dmap.get(comp, {})
                m = [t for t in cases if rx.search(f"{t[0]}::{t[1]}")]
                dm = [t for t in m if (t[0], t[1]) in declared_here]
                um = [t for t in m if (t[0], t[1]) not in declared_here]
                f = [t for t in um if t[2] == "failed"]
                k = [t for t in um if t[2] == "skipped"]
                hits += len(m); fails += len(f); skips += len(k); undeclared_total += len(um)
                row_detail = {"component": comp, "re": sel["re"], "matched": len(m), "failed": len(f), "skipped": len(k), "min": sel.get("min", 1),
                              "failed_tests": [f"{t[0]}::{t[1]}" for t in f][:10]}
                if declared is not None:
                    row_detail.update(declared_matched=len(dm), undeclared_matched=len(um))
                detail.append(row_detail)
                if dm and not um:
                    zero_undeclared.append(f"{comp}/{sel['re']}")
                for t in dm:
                    info = t[3] if len(t) > 3 else {"kind": t[2], "unexpected_pass": False}
                    entry = declared_here[(t[0], t[1])]
                    listed[(comp, t[0], t[1])] = {"label": "DECLARED-LIMIT", "component": comp, "test": f"{t[0]}::{t[1]}", "declaration_id": entry["id"],
                                                  "outcome": info["kind"], "unexpected_pass": bool(info.get("unexpected_pass"))}
                    if info.get("unexpected_pass"):
                        xpassed.append(f"{t[0]}::{t[1]}")
                        conditions.append(f"declared test passed unexpectedly (strict expected failure XPASS): {t[0]}::{t[1]}")
                    elif info["kind"] not in ("failed", "xfailed"):
                        # a declared known limit is expected to be observed failing (or xfailing); a pass or a skip is reported, never silent.
                        # A skip is also not coverage (row INCONCLUSIVE). A plain pass only adds the condition: the retained g6-r10 control_plane
                        # known-limit tests document their limit by passing, and turning those rows INCONCLUSIVE would flip the retained verdict.
                        if info["kind"] == "skipped":
                            unmet.append(f"{t[0]}::{t[1]} ({info['kind']})")
                        conditions.append(f"declared test did not fail as declared (observed {info['kind']}): {t[0]}::{t[1]}")
                present = {(t[0], t[1]) for t in cases}
                for key, entry in declared_here.items():
                    if key not in present and rx.search(f"{key[0]}::{key[1]}"):
                        not_run[(comp, key[0], key[1])] = {"label": "DECLARED-LIMIT", "component": comp, "test": f"{key[0]}::{key[1]}",
                                                           "declaration_id": entry["id"], "outcome": "NOT RUN"}
            short = any(d["matched"] < d["min"] for d in detail)
            r["selector_results"] = detail
            r["executed_cases"] = hits
            if declared is not None:
                r["undeclared_cases"] = undeclared_total
                r["declared_limit_cases"] = sorted(listed.values(), key=lambda x: x["test"])
                r["declared_not_run"] = sorted(not_run.values(), key=lambda x: x["test"])
                conditions += [f"declared test not run: {x['test']}" for x in r["declared_not_run"]]
            if fails:
                r["status"] = "FAIL"; r.setdefault("classification", "product defect")
            elif xpassed:
                r["status"] = "FAIL"; r.setdefault("classification", "declared strict expected failure passed")
                r["reason"] = "a declared strict expected failure passed unexpectedly (DR-7): " + ", ".join(xpassed)
            elif short:
                r["status"] = "INCONCLUSIVE"; r["reason"] = "selector matched fewer executed cases than required (job missing or selector defective)"
            elif skips:
                r["status"] = "INCONCLUSIVE"; r["reason"] = "matched cases were skipped"
            elif unmet:
                r["status"] = "INCONCLUSIVE"
                r["reason"] = "a declared known-limit test was skipped instead of failing as declared: " + ", ".join(unmet)
            elif r.get("declared_not_run"):
                r["status"] = "INCONCLUSIVE"
                r["reason"] = "a declared test that a selector of the row would match was not run: " + ", ".join(x["test"] for x in r["declared_not_run"])
            elif zero_undeclared:
                r["status"] = "INCONCLUSIVE"
                r["reason"] = ("every case matched by selector " + ", ".join(zero_undeclared) + " is a declared known limit: zero undeclared cases remain, "
                               "so the row is not reported as PASS")
                conditions.append("zero undeclared cases remain for selector " + ", ".join(zero_undeclared))
            elif hits == 0:
                r["status"] = "INCONCLUSIVE"; r["reason"] = "zero executed cases matched: a tests row is never PASS without executed evidence"
            elif r.get("adequacy", "adequate") == "adequate":
                r["status"] = "PASS"; r["provenance"] = r.get("provenance", "NEW EXECUTION")
            else:
                r["status"] = "INCONCLUSIVE"
                r["reason"] = "matched cases passed but are declared inadequate for the full requirement: " + r.get("adequacy_note", "partial coverage")
            if declared is not None:
                r["reportable_conditions"] = conditions
        elif kind == "job":
            st = job_status.get(r["component"])
            r["status"] = st if st in ("PASS", "FAIL") else "INCONCLUSIVE"
            if r["status"] == "PASS" and job_counts_by_component is not None and r["component"] in JOB_ZERO_SKIP_COMPONENTS:
                c = job_counts_by_component.get(r["component"]) or {}
                if not c.get("testcases") or c.get("skipped") != 0:
                    r["status"] = "INCONCLUSIVE"
                    r["reason"] = f"job passed with skipped tests or without counts (counts: {c or 'none'}); a skip is not coverage for this row"
            if r["status"] == "PASS" and job_counts_by_component is not None and r["component"] in JOB_MIN_CASES_COMPONENTS:
                c = job_counts_by_component.get(r["component"]) or {}
                need = r.get("min_cases", 1)
                if (c.get("testcases") or 0) < need:
                    r["status"] = "INCONCLUSIVE"
                    r["reason"] = f"job executed {c.get('testcases') or 0} case(s), fewer than the minimum {need} (counts: {c or 'none'})"
            if r["status"] != "PASS":
                r.setdefault("reason", f"job status {st}")
        elif kind == "not_applicable":
            r["status"] = "NOT APPLICABLE"
        else:  # gap / manual: status declared with reason; never promoted
            r["status"] = r.get("declared_status", "NOT RUN")
            if r["status"] == "PASS":
                r["status"] = "INCONCLUSIVE"; r["reason"] = "declared PASS without executed evidence is refused"
        evaluated.append(r)
    return evaluated


def requirements_markdown(reqs):
    lines = ["| ID | Source | Status | Mandatory | Provenance | Cases | Note |", "|---|---|---|---|---|---|---|"]
    for r in reqs:
        note = (r.get("reason") or r.get("not_applicable_reason") or r.get("classification") or "")[:160].replace("|", "/")
        lines.append(f"| {r['id']} | {r.get('source','')} | {r['status']} | {'yes' if r['mandatory'] else 'no'} | {r.get('provenance','')} | {r.get('executed_cases','')} | {note} |")
    return "\n".join(lines) + "\n"


def declared_limit_rows(reqs):
    """Rows that carry declared known limits (matched or NOT RUN) or a reportable condition, in matrix order."""
    return [r for r in reqs if r.get("declared_limit_cases") or r.get("declared_not_run") or r.get("reportable_conditions")]


def declared_limits_markdown(reqs):
    lines = []
    for r in declared_limit_rows(reqs):
        lines.append(f"- **{r['id']}** ({r['status']}, mandatory: {'yes' if r['mandatory'] else 'no'}; {r.get('undeclared_cases', 0)} undeclared case(s) counted)")
        for c in r.get("declared_limit_cases", []):
            lines.append(f"  - DECLARED-LIMIT `{c['test']}` ({c['component']}): {c['outcome']}" + (" - UNEXPECTED PASS of a strict expected failure" if c["unexpected_pass"] else ""))
        for c in r.get("declared_not_run", []):
            lines.append(f"  - DECLARED-LIMIT `{c['test']}` ({c['component']}): NOT RUN")
        for cond in r.get("reportable_conditions", []):
            lines.append(f"  - reportable condition: {cond}")
    return "\n".join(lines) + ("\n" if lines else "")


def declared_limits_block(record, reqs, index):
    """Report block: the declared set that was used (with its hash), the state of every declaration the controller can match, and the rows."""
    states = []
    for e in record["entries"]:
        if e["kind"] == "test" and e["component"]:
            cases = [t for t in index.get(e["component"], []) if t[0] == e["classname"] and t[1] == e["name"]]
            outcome = ",".join(sorted({(t[3]["kind"] if len(t) > 3 else t[2]) for t in cases})) if cases else "NOT RUN"
            states.append({"id": e["id"], "component": e["component"], "test": f"{e['classname']}::{e['name']}", "outcome": outcome})
    rows = declared_limit_rows(reqs)
    return {"note": "declared known limits are listed beside the rows they fall in; a tests row is computed over the matched cases that are not declared, "
                    "selector minimums are measured over all matched cases, and a row whose selector matched only declared cases is INCONCLUSIVE",
            "declared_set_sha256": record["declared_set_sha256"], "twin": record["twin"], "match_rule": record["match_rule"], "counts": record["counts"],
            "entries": record["entries"], "matchable_states": states,
            "rows": [{"id": r["id"], "status": r["status"], "mandatory": r["mandatory"], "undeclared_cases": r.get("undeclared_cases"),
                      "declared_limit_cases": r.get("declared_limit_cases", []), "declared_not_run": r.get("declared_not_run", []),
                      "reportable_conditions": r.get("reportable_conditions", [])} for r in rows],
            "reportable_conditions": [{"id": r["id"], "condition": c} for r in rows for c in r.get("reportable_conditions", [])]}


VALIDATION_ID_RE = re.compile(r"^v1-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+$")
_CONTROL_NAMES = ("result.json", "plan.json", "freeze-verification.json")


def _load_control_json(path: Path):
    """Read one control record; refuse symlinks and non-regular files."""
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f"refusing control record that is not a regular file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def collect_control_records(inputs: Path):
    """Read control records only from their fixed locations; refuse anything else.

    plan.json: only collected/v1v-plan/.  freeze-verification.json: only
    collected/v1v-freeze/.  result.json: only at the top level of the other
    collected/v1v-*/ directories.  A control-named file anywhere else (for
    example nested inside another artifact) is refused, as is more than one
    result for one (component, os, python).
    """
    allowed = set()
    plan_path = inputs / "v1v-plan" / "plan.json"
    freeze_path = inputs / "v1v-freeze" / "freeze-verification.json"
    allowed.update({plan_path, freeze_path})
    results = []
    for d in sorted(inputs.glob("v1v-*")):
        if d.is_symlink() or not d.is_dir():
            raise SystemExit(f"refusing artifact entry that is not a plain directory: {d}")
        if d.name in ("v1v-plan", "v1v-freeze"):
            continue
        rp = d / "result.json"
        if rp.exists() or rp.is_symlink():
            allowed.add(rp)
            r = _load_control_json(rp)
            r["_dir"] = d.name
            results.append(r)
    for p in inputs.rglob("*"):
        if p.name in _CONTROL_NAMES and p not in allowed:
            raise SystemExit(f"refusing control record outside its fixed location: {p.relative_to(inputs)}")
    seen = set()
    for r in results:
        key = (r.get("component"), r.get("os"), str(r.get("python")))
        if key in seen:
            raise SystemExit(f"refusing duplicate result for {key}")
        seen.add(key)
    freeze = _load_control_json(freeze_path) if freeze_path.exists() or freeze_path.is_symlink() else None
    expected = []
    if plan_path.exists() or plan_path.is_symlink():
        expected = _load_control_json(plan_path).get("include", [])
        if not isinstance(expected, list) or not all(isinstance(e, dict) and e.get("component") and e.get("os") and e.get("python") for e in expected):
            raise SystemExit("refusing plan record: include must be a list of entries with component, os and python")
    return results, freeze, expected


def job_counts(record, inputs: Path):
    """Test counts of one job record for the summary.

    Component and probe jobs carry them in their last attempt. A single-instance job (for example the scenario suite) writes them at the
    top level of its record and has no attempts; when a record carries neither, they are read from the job's own junit.xml (None when absent).
    Reporting only: no status or verdict is derived from this value.
    """
    att = record["attempts"][-1] if record.get("attempts") else {}
    if att.get("counts") is not None:
        return att["counts"]
    if isinstance(record.get("counts"), dict):
        return record["counts"]
    return junit_counts(inputs / record["_dir"] / "junit.xml")


def _job_junit_failures(record, inputs: Path):
    """(classname, name) of every failed or errored case in the last JUnit report of one job, and whether a report was readable."""
    d = inputs / record["_dir"]
    files = sorted(d.glob("junit-attempt*.xml"))[-1:] or sorted(d.rglob("junit.xml"))[:1]
    failed, readable = [], False
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        readable = True
        for tc in root.iter("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                failed.append((tc.get("classname", ""), tc.get("name", "")))
    return failed, readable


def job_blockers(results, expected, missing, declared, inputs: Path, requirements):
    """Jobs that stop the verdict from being PASS whatever the requirement rows say (E-1).

    The requirement rows see only the cases their selectors match, so an undeclared failure elsewhere in a pinned component's own suite would
    leave the verdict PASS with the job status FAIL. A blocker is, for every collected job record: FAIL (unless every failed case of its JUnit
    report is a declared known limit of that component and at least one is present), INCONCLUSIVE or any other status that is not PASS, NOT RUN
    (unless the plan marks the component optional); and every expected job that produced no result. A job whose component is the subject of a
    non-mandatory job row (scope reduced: qualification tooling, matched-refund rerun) is not a blocker. Returns a list of
    {job, component, os, python, status, kind (FAIL|INCOMPLETE), reason}; FAIL blockers make the verdict FAIL, the others INCOMPLETE.
    """
    dmap = DL.by_component(declared) if declared is not None else {}
    reduced = {r.get("component") for r in requirements if r.get("kind") == "job" and not r.get("mandatory", True)}
    optional = {(e["component"], e["os"], str(e["python"])[:4]) for e in expected if e.get("group") == "components_optional"}
    blockers = []

    def add(rec, kind, reason, job):
        blockers.append({"job": job, "component": rec.get("component"), "os": rec.get("os"), "python": rec.get("python"),
                         "status": rec.get("status"), "kind": kind, "reason": reason})

    for r in results:
        st = effective_job_status(r)
        if st == "PASS" or r.get("component") in reduced:
            continue
        if st == "NOT RUN" and (r.get("component"), r.get("os"), str(r.get("python"))[:4]) in optional:
            continue
        if st == "FAIL":
            failed, _ = _job_junit_failures(r, inputs)
            declared_here = dmap.get(r.get("component"), {})
            undeclared = [f"{c}::{n}" for c, n in failed if (c, n) not in declared_here]
            if failed and not undeclared:
                continue  # every failed case is a declared known limit of this component
            add(r, "FAIL", "job FAIL with undeclared failing case(s): " + ", ".join(undeclared[:5]) if undeclared else
                "job FAIL without a failing case in its JUnit report (setup, collection or harness failure)", r["_dir"])
        else:
            add(r, "INCOMPLETE", f"job status {st}", r["_dir"])
    for m in missing:
        if m["component"] not in reduced:
            add(m, "INCOMPLETE", m["reason"], "(missing)")
    return blockers


PLAN_RECORD_PROBLEM = ("no plan record (v1v-plan/plan.json) or it lists no jobs: missing jobs, the job-to-plan sha/repository binding, the "
                       "freeze-versus-plan component check and the optional-group allowance cannot be evaluated")


def record_binding_problems(results, freeze, expected, run_id=None, require_plan=True):
    """[(job dir, message)] for job records that are not bound to this run, the plan and the freeze record (E-11).

    run_id: the aggregate's own GITHUB_RUN_ID; without it the freeze record's workflow_run is the reference (no reference: no run check).
    require_plan (default True, fail closed): an empty plan (no v1v-plan record or no included jobs) is itself a problem, reported under the job
    name "(plan)" (F-T2-1); the explicit local escape is the aggregate's --no-plan-record.
    Every job record must carry that workflow_run; a component job whose plan entry names a repository and sha must record the same
    repository, pinned_sha and actual_sha; and the commit the freeze record fetched for the component must equal the job's actual_sha."""
    ref = str(run_id) if run_id else (str(freeze["workflow_run"]) if freeze and freeze.get("workflow_run") else None)
    plan = {(e["component"], e["os"], str(e["python"])[:4]): e for e in expected}
    fetched = (freeze or {}).get("components") or {}
    problems = []
    if require_plan and not expected:
        problems.append(("(plan)", PLAN_RECORD_PROBLEM))
    for r in results:
        where = r["_dir"]
        if ref is not None and str(r.get("workflow_run")) != ref:
            problems.append((where, f"workflow_run {r.get('workflow_run')!r} is not the run {ref}"))
        e = plan.get((r.get("component"), r.get("os"), str(r.get("python"))[:4]))
        if e and e.get("sha"):
            for field, want in (("pinned_sha", e["sha"]), ("actual_sha", e["sha"]), ("repository", e.get("repository"))):
                if want and r.get(field) != want:
                    problems.append((where, f"{field} {r.get(field)!r} differs from the plan ({want})"))
        rec = fetched.get(r.get("component"))
        if isinstance(rec, dict) and rec.get("commit") and r.get("actual_sha") and rec["commit"] != r["actual_sha"]:
            problems.append((where, f"actual_sha {r['actual_sha']} differs from the commit the freeze record fetched ({rec['commit']})"))
    return problems


def cmd_aggregate(args):
    if not VALIDATION_ID_RE.fullmatch(str(args.validation_id)):
        raise SystemExit("invalid validation id")
    inputs = Path(args.inputs)
    try:
        declared = DL.load(getattr(args, "declared_twin", None), require_committed=getattr(args, "require_committed_twin", False),
                           declared_set_file=getattr(args, "declared_set", None))
    except (DL.DeclaredSetError, OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"refusing to aggregate: declared known limits cannot be taken from the committed twin: {exc}")
    results, freeze, expected = collect_control_records(inputs)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    counts = {s: 0 for s in STATUSES}
    rows = []
    for r in results:
        counts[r.get("status", "INCONCLUSIVE")] = counts.get(r.get("status", "INCONCLUSIVE"), 0) + 1
        att = r["attempts"][-1] if r.get("attempts") else {}
        rows.append({"job": r["_dir"], "component": r.get("component"), "os": r.get("os"), "python": r.get("python"),
                     "status": r.get("status"), "reason": r.get("reason"), "counts": job_counts(r, inputs),
                     "attempts": len(r.get("attempts", [])), "flaky_or_setup": bool(r.get("flaky_or_setup")),
                     "attempt_outcomes": r.get("attempt_outcomes") or [a.get("outcome") for a in r.get("attempts", [])]})
    seen = {(r.get("component"), r.get("os"), str(r.get("python"))[:4]) for r in results}
    missing = []
    for e in expected:
        if (e["component"], e["os"], e["python"][:4]) not in seen:
            missing.append({"component": e["component"], "os": e["os"], "python": e["python"], "status": "INCONCLUSIVE",
                            "reason": "expected job produced no result (setup failure, cancelled or unavailable runner)"})
            counts["INCONCLUSIVE"] += 1
    rows.extend({"job": "(missing)", **m, "counts": None, "attempts": 0} for m in missing)
    requirements = []
    if args.requirements and Path(args.requirements).exists():
        req_doc = json.loads(Path(args.requirements).read_text(encoding="utf-8"))
        try:
            validate_requirements(req_doc)
        except ValueError as exc:
            raise SystemExit(f"refusing to aggregate: malformed requirements: {exc}")
        job_status = {r.get("component"): effective_job_status(r) for r in results if r.get("os") in (None, "ubuntu-latest") and str(r.get("python", "3.12"))[:4] in ("3.12", "")}
        junit_index = load_junit_index(inputs, results, detail=True)
        job_counts_by_component = {r.get("component"): job_counts(r, inputs) for r in results
                                   if r.get("os") in (None, "ubuntu-latest") and str(r.get("python", "3.12"))[:4] in ("3.12", "")}
        requirements = evaluate_requirements(req_doc, junit_index, job_status, declared, job_counts_by_component)
        (out / "requirements-matrix.json").write_text(json.dumps({"schema": "cognous.v1-validation-matrix/1", "validation_id": args.validation_id,
                                                                  "declared_set_sha256": declared["declared_set_sha256"], "requirements": requirements}, indent=2) + "\n", encoding="utf-8")
        (out / "requirements-matrix.md").write_text(requirements_markdown(requirements) + "\nDeclared set sha256: `" + declared["declared_set_sha256"] + "`\n"
                                                    + ("\n### Declared known limits beside their rows\n\n" + declared_limits_markdown(requirements) if declared_limit_rows(requirements) else ""), encoding="utf-8")
    freeze_problem = freeze_record_problem(freeze, expected, args.validation_id)
    freeze_status = "FAIL" if freeze_problem else (freeze or {}).get("status", "NOT RUN")
    summary = {"schema": "cognous.v1-validation-summary/1", "validation_id": args.validation_id,
               "workflow_run": os.environ.get("GITHUB_RUN_ID"), "freeze_status": freeze_status, "freeze_components_proof": freeze_components_proof(freeze),
               "flaky_or_setup_jobs": [{"job": x["job"], "component": x["component"], "os": x["os"], "python": x["python"], "attempt_outcomes": x["attempt_outcomes"]}
                                       for x in rows if x.get("flaky_or_setup")],
               "job_status_counts": counts, "expected_jobs": len(expected), "missing_jobs": len(missing), "jobs": rows,
               "selected_v1_verdict": "INCOMPLETE" if not requirements else verdict(requirements),
               "verdict_basis": "no requirement matrix supplied: aggregation refuses to promote" if not requirements else "requirement matrix",
               "requirement_status_counts": {st: sum(1 for r in requirements if r["status"] == st) for st in STATUSES},
               "requirement_status_by_source_class": {sc: {st: sum(1 for r in requirements if r.get("source_class", "docx-or-catalog") == sc and r["status"] == st) for st in STATUSES} for sc in sorted({r.get("source_class", "docx-or-catalog") for r in requirements})},
               "mandatory_requirement_status_counts": {st: sum(1 for r in requirements if r["status"] == st and r["mandatory"]) for st in STATUSES}}
    if requirements:
        summary["declared_limits"] = declared_limits_block(declared, requirements, junit_index)
        summary["full_catalog_status"] = full_catalog_status(requirements)
        summary["scope_reduction"] = scope_reduction_block(requirements)
    blockers = job_blockers(results, expected, missing, declared, inputs, requirements) if requirements else []
    no_plan = bool(getattr(args, "no_plan_record", False))
    binding = record_binding_problems(results, freeze, expected, os.environ.get("GITHUB_RUN_ID"), require_plan=not no_plan)
    summary["record_binding_problems"] = [{"job": j, "problem": m} for j, m in binding]
    summary["no_plan_record"] = no_plan
    if requirements:
        blockers += [{"job": j, "component": next((x.get("component") for x in results if x["_dir"] == j), None), "os": None, "python": None,
                      "status": "UNBOUND", "kind": "INCOMPLETE", "reason": m} for j, m in binding]
    summary["blocking_jobs"] = blockers
    if blockers and summary["selected_v1_verdict"] != "FAIL":
        summary["selected_v1_verdict"] = "FAIL" if any(b["kind"] == "FAIL" for b in blockers) else "INCOMPLETE"
        summary["verdict_note"] = "job(s) not covered by a declared known limit: " + "; ".join(
            f"{b['component']} {b['os']} py{b['python']} ({b['job']}): {b['reason']}" for b in blockers)
    if freeze is None or freeze.get("status") != "PASS" or freeze_problem:
        summary["selected_v1_verdict"] = "INCOMPLETE" if summary["selected_v1_verdict"] != "FAIL" else "FAIL"
        summary["verdict_note"] = ((summary["verdict_note"] + " | ") if summary.get("verdict_note") else "") + (
            "freeze verification did not pass; no result may be promoted" + (f" ({freeze_problem})" if freeze_problem else ""))
    if no_plan and not expected:
        # explicit escape (local or retained re-aggregation without a plan record): missing jobs, sha binding and the freeze-vs-plan
        # check were not evaluated, so the verdict is at most INCOMPLETE
        summary["verdict_basis"] += "; run without a plan record (--no-plan-record): at most INCOMPLETE"
        if summary["selected_v1_verdict"] == "PASS":
            summary["selected_v1_verdict"] = "INCOMPLETE"
        summary["verdict_note"] = ((summary["verdict_note"] + " | ") if summary.get("verdict_note") else "") + PLAN_RECORD_PROBLEM + " (--no-plan-record)"
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [f"## V1 validation {args.validation_id}", "", f"Freeze: **{summary['freeze_status']}** · Verdict: **{summary['selected_v1_verdict']}** ({summary['verdict_basis']})", "",
             "| Status | Jobs |", "|---|---|"] + [f"| {k} | {v} |" for k, v in counts.items()] + ["",
             "| Component | OS | Python | Status | Testcases/fail/err/skip | Reason |", "|---|---|---|---|---|---|"]
    for row in rows:
        c = row["counts"] or {}
        note = (row['reason'] or '') + (f" RETRIED: attempts {' -> '.join(map(str, row['attempt_outcomes']))} (first attempt did not pass; reported, not blocking)" if row.get('flaky_or_setup') else '')
        lines.append(f"| {row['component']} | {row['os']} | {row['python']} | {row['status']} | {c.get('testcases','-')}/{c.get('failures','-')}/{c.get('errors','-')}/{c.get('skipped','-')} | {note.strip()} |")
    if requirements:
        fc, sr = summary["full_catalog_status"], summary["scope_reduction"]
        lines += ["", "### Full-catalog status (all rows, real statuses; reporting only, not the verdict basis)", "",
                  "| Status | All rows | Pre-reduction mandatory rows |", "|---|---|---|"]
        lines += [f"| {st} | {fc['status_counts'][st]} | {fc['unreduced_mandatory_status_counts'][st]} |" for st in STATUSES]
        lines += ["", f"Pre-reduction mandatory verdict (verdict rule applied to the rows that were mandatory before scope reduction): **{fc['unreduced_mandatory_verdict']}**"]
        lines += ["", f"### Scope reduction ({sr['count']} rows moved out of the mandatory claim; statuses unchanged, none counted as PASS)", ""]
        if sr["rows"]:
            lines += ["| ID | Decision | Category | Final status |", "|---|---|---|---|"]
            lines += [f"| {x['id']} | {x['decision']} | {x['category']} | {x['final_status']} |" for x in sr["rows"]]
        else:
            lines += ["No rows are scope-reduced."]
    if requirements:
        dl = summary["declared_limits"]
        lines += ["", f"### Declared known limits (declared set sha256 `{dl['declared_set_sha256']}`; twin sha256 `{dl['twin']['sha256']}`, {dl['twin']['source']}; "
                      f"{dl['counts']['entries']} declarations, {dl['counts']['matchable_by_controller']} matchable by the controller)", ""]
        lines += [declared_limits_markdown(requirements).rstrip() or "No row carries a declared known limit.", ""]
        if dl["reportable_conditions"]:
            lines += [f"Reportable conditions: {len(dl['reportable_conditions'])} (listed above per row)."]
    md = "\n".join(lines) + "\n"
    (out / "summary.md").write_text(md, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(md)
    print(md)


def cmd_declared_set(args):
    try:
        record = DL.load(args.declared_twin, require_committed=not args.allow_uncommitted_twin)
    except (DL.DeclaredSetError, OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"declared set cannot be derived: {exc}")
    text = json.dumps(record, indent=2) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--manifest", required=True); p.add_argument("--refreeze-log", default=None, help="overlay: APPLIED entries override the manifest pins"); p.add_argument("--linux-only", action="store_true", help="D2: plan Linux (ubuntu) jobs only; macOS/Windows are unsupported platforms"); p.add_argument("--github-output"); p.add_argument("--out-file")
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("freeze-verify")
    for a in ("--manifest", "--hub-dir", "--qual-dir", "--work", "--out"):
        p.add_argument(a, required=True)
    p.add_argument("--refreeze-log", default=None, help="overlay: APPLIED entries override the manifest pins of the components that are fetched")
    p.add_argument("--qual-profile", default=None, help="qualification profile path (repo-relative) to check against manifest + overlay; default the manifest's")
    p.set_defaults(fn=cmd_freeze_verify)
    p = sub.add_parser("check-workflow-pins", help="fail when a pinned-repository sha literal of the workflow differs from manifest + overlay")
    p.add_argument("--workflow", required=True); p.add_argument("--manifest", required=True); p.add_argument("--refreeze-log", default=None)
    p.set_defaults(fn=cmd_check_workflow_pins)
    p = sub.add_parser("component-suite")
    for a in ("--component", "--repository", "--sha", "--repo-dir", "--out", "--os-name"):
        p.add_argument(a, required=True)
    p.add_argument("--timeout", type=int, default=DEFAULT_TEST_TIMEOUT_SECONDS)
    p.add_argument("--fetch", action="store_true", help="fetch the exact pinned commit into --repo-dir first")
    p.add_argument("--pins-manifest", default=None, help="freeze manifest that names the sibling pins (default: $MANIFEST, relative to the checkout of this tool)")
    p.add_argument("--refreeze-log", default=None, help="overlay for the sibling pins (default: $REFREEZE_LOG; the file must exist when the variable is set)")
    p.add_argument("--no-siblings", action="store_true", help="local use: do not provision pinned sibling components (the row skips they cause stay INCONCLUSIVE)")
    p.set_defaults(fn=cmd_component_suite)
    p = sub.add_parser("probe-suite")
    for a in ("--component", "--repo-dir", "--out", "--os-name", "--suite"):
        p.add_argument(a, required=True)
    p.add_argument("--repository", default=None); p.add_argument("--sha", default=None)
    p.add_argument("--refreeze-log", default=None, help="with --pins-manifest: overlay APPLIED refreeze-log entries onto the manifest pins")
    p.add_argument("--pins-manifest", default=None, help="fetch every pinned public source of this freeze manifest under --repo-dir/<key> (multi-repository probes)")
    p.add_argument("--full-history", action="store_true", help="unshallow the pinned checkout so probes can read git history")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--env-var", default="PROBE_INDEX_DIR", help="env var that points the probes at the pinned checkout (one per component)")
    p.add_argument("--npm-dir", default=None, help="run `npm ci` in this directory of the pinned checkout before the probes")
    p.add_argument("--extras", default=None, help="comma-separated [project.optional-dependencies] groups of the pinned pyproject to install (dependencies only; the project itself is never installed)")
    p.add_argument("--harness-requirements", action="store_true", help="install the pinned checkout's testing/harness/requirements*.txt before the probes")
    p.set_defaults(fn=cmd_probe_suite)
    p = sub.add_parser("aggregate")
    p.add_argument("--inputs", required=True); p.add_argument("--out", required=True)
    p.add_argument("--validation-id", required=True); p.add_argument("--requirements")
    p.add_argument("--declared-twin", default=None, help="pre-registration twin to read declared known limits from (default: the repository twin)")
    p.add_argument("--declared-set", default=None, help="a declared-set record written by the declared-set subcommand; the aggregate refuses to run if it differs from the set derived from the twin")
    p.add_argument("--allow-uncommitted-twin", action="store_true", help="local use only: accept a twin that differs from its copy at git HEAD (the default refuses)")
    p.add_argument("--no-plan-record", action="store_true", help="local use only: aggregate without a v1v-plan record; recorded in the summary (no_plan_record) and the verdict is then at most INCOMPLETE (the default refuses to promote)")
    p.set_defaults(fn=cmd_aggregate)
    p = sub.add_parser("declared-set", help="print the declared-set record (entries and sha256) derived from the committed twin; reads no results")
    p.add_argument("--declared-twin", default=None); p.add_argument("--out", default=None); p.add_argument("--allow-uncommitted-twin", action="store_true")
    p.set_defaults(fn=cmd_declared_set)
    args = ap.parse_args()
    if args.cmd == "aggregate":
        args.require_committed_twin = not args.allow_uncommitted_twin
    args.fn(args)


if __name__ == "__main__":
    main()
