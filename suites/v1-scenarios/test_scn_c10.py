"""SCN-C10 Executor confinement (executed against the frozen F5b seven-component reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C10): attempt path traversal, symlink escape, prohibited filesystem, process and network access through
supported surfaces. Required observation: no access outside the declared test boundary; report exactly which isolation
surfaces were exercised.

Declared boundary (frozen runtime 4a83b175 docs/execution-boundary.md and docs/threat-model.md): the supported adapter has
NO subprocess, network or credential capability; the supported destinations reject path traversal and symlinked database
paths/components before resolution. NOT declared (and so not claimed): OS/container confinement, seccomp/AppArmor, network
namespaces, credential brokers, and the filesystem check/use race. Where the reference itself declares a limit, a separate
``declared_out_of_model`` test records what actually happens (it is a characterisation, labelled as such, and the evidence
JSON says ``required_observation_met`` false when an escape is observed); it is never presented as confinement.

Isolation surfaces exercised (the full list is repeated in each evidence file):
  S1 constructor path surface: database_name traversal / absolute / empty / NUL (3 destination classes)
  S2 constructor symlink surface: root, root parent, database file (existing, dangling), symlinked subdirectory (3 classes)
  S3 envelope surface of route A (Control Plane + PinnedControlPlaneExecutor): requested permissions naming prohibited
     filesystem/process/network capabilities, hostile target and payload strings
  S4 observed behaviour of an authorized run: process, network, SQLite and filesystem-write events from a ``sys.addaudithook``
     observer (an independent witness that can observe but not block)
  S5 static import surface of the supported engine modules (no subprocess/socket/ctypes/http imports)
  S6 declared out-of-model characterisations: symlink swap after construction, hardlinked database file
NOT exercised (listed in the batch report): the optional OpenShell destination (needs a Docker gateway and a pinned CLI),
OS/container isolation (not part of the reference), credential brokers (none exist).
Each case runs twice from fresh directories and the normalised observations are compared (D3). Hard gate (D5): zero
unauthorized effects, zero excess duplicate effects.
"""
from __future__ import annotations

import ast
import dataclasses
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import _c_2b_helpers as C
from _c_2b_helpers import pinned_reference  # noqa: F401

H = C.H
SURFACES = ['S1 constructor path surface', 'S2 constructor symlink surface', 'S3 route-A envelope surface (permissions, target, payload)',
            'S4 observed process/network/sqlite/filesystem events of an authorized run', 'S5 static import surface of supported engine modules',
            'S6 declared out-of-model characterisations']
NOT_EXERCISED = ['OpenShell optional destination (Docker gateway + pinned CLI not available)', 'OS/container isolation (not in the reference)',
                 'credential brokers (none exist in the reference)']
CLASSES = ('durable', 'effective_grant', 'atomic')


def _make(kind, root, database_name=None):
    ref = C.reference()  # puts the runtime on sys.path
    kwargs = {} if database_name is None else {'database_name': database_name}
    if kind == 'durable':
        from engine.safe_executor import DurableRefundDestination
        return DurableRefundDestination(root, **kwargs)
    if kind == 'effective_grant':
        from engine.effective_grant import EffectiveGrantDestination
        return EffectiveGrantDestination(root, **kwargs)
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    return AtomicAuthorityEffectDestination(root, clock=lambda: datetime(2030, 1, 1, tzinfo=timezone.utc), **kwargs)


def _layout(work):
    """work/sandbox is the declared boundary; everything else under work is outside it."""
    sandbox = work / 'sandbox'
    outside = work / 'outside'
    outside.mkdir()
    (outside / 'secret.txt').write_text('SYNTHETIC-OUTSIDE-SECRET\n')
    with sqlite3.connect(outside / 'victim.sqlite3') as conn:
        conn.execute('CREATE TABLE victim(v TEXT)')
        conn.execute("INSERT INTO victim VALUES ('untouched')")
    return sandbox, outside


def _attempt(kind, root, name, work, boundary):
    before = {k: v for k, v in C.tree_snapshot(work).items() if k.split('/')[0] != 'sandbox'}
    err = None
    with C.Observer(boundary) as obs:
        try:
            _make(kind, root, name)
        except Exception as exc:
            err = C.exc_text(exc)
    after = {k: v for k, v in C.tree_snapshot(work).items() if k.split('/')[0] != 'sandbox'}
    rep = obs.report()
    return err, before, after, rep


def _norm(err):
    return None if err is None else err.split(':')[0] + ':' + (err.split(':', 1)[1].strip()[:60] if ':' in err else '')


def _assert_confined(checks, label, err, before, after, rep, *, must_raise=True, expect_type=None):
    if must_raise:
        checks.expect(err is not None, f'{label}: the constructor must refuse (explicit failure), it returned')
    if expect_type and err is not None:
        checks.expect(err.startswith(expect_type), f'{label}: expected {expect_type}, observed {err}')
    checks.equal(after, before, f'{label}: nothing outside the sandbox was created, modified or removed')
    checks.equal(rep['process_events'], [], f'{label}: no process event')
    checks.equal(rep['network_events'], [], f'{label}: no network event')
    checks.equal([p for p in rep['write_class_outside_boundary'] if '/outside' in p or '/sandbox/../' in p], [], f'{label}: no write-class event aimed outside the boundary')


# ---------------------------------------------------------------------------------------------------------
# S1: path traversal at the destination constructor
# ---------------------------------------------------------------------------------------------------------
PATH_VARIANTS = {
    'dotdot_sibling': ('../escape.sqlite3', 'PermissionError'),
    'dotdot_deep': ('a/../../escape.sqlite3', 'PermissionError'),
    'dotdot_into_outside_dir': ('../outside/planted.sqlite3', 'PermissionError'),
    'dotdot_only': ('..', 'PermissionError'),
    'absolute_outside': ('@OUTSIDE@/abs.sqlite3', 'PermissionError'),
    'absolute_etc': ('/etc/cognous-c10-planted.sqlite3', 'PermissionError'),
    'empty_name': ('', None),
    'dot_only': ('.', None),
    'nul_byte': ('x\x00.sqlite3', None),
}


@pytest.mark.parametrize('kind', CLASSES)
@pytest.mark.parametrize('variant', sorted(PATH_VARIANTS))
def test_scn_c10_path_traversal_database_name(request, record_property, tmp_path, pinned_reference, kind, variant):
    raw, expect_type = PATH_VARIANTS[variant]

    def trial(work, mp, checks):
        sandbox, outside = _layout(work)
        name = raw.replace('@OUTSIDE@', str(outside))
        etc_before = Path('/etc/cognous-c10-planted.sqlite3').exists()
        err, before, after, rep = _attempt(kind, sandbox, name, work, sandbox)
        _assert_confined(checks, f'{kind}/{variant}', err, before, after, rep, expect_type=expect_type)
        checks.equal(Path('/etc/cognous-c10-planted.sqlite3').exists(), etc_before, 'nothing was created in /etc')
        return {'surface': 'S1', 'class': kind, 'variant': variant, 'refused': err is not None, 'error': _norm(err), 'outside_unchanged': after == before,
                'process_events': rep['process_events'], 'network_events': rep['network_events'], 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, extra={'isolation_surfaces_exercised': SURFACES[:1], 'not_exercised': NOT_EXERCISED})


# ---------------------------------------------------------------------------------------------------------
# S2: symlink escape at the destination constructor
# ---------------------------------------------------------------------------------------------------------
def _sym_root(work, outside, sandbox):
    link = work / 'link_root'
    link.symlink_to(outside, target_is_directory=True)
    return link, None


def _sym_root_parent(work, outside, sandbox):
    link = work / 'link_parent'
    link.symlink_to(outside, target_is_directory=True)
    return link / 'root', None


def _sym_db_existing(work, outside, sandbox):
    sandbox.mkdir()
    (sandbox / 'refunds.sqlite3').symlink_to(outside / 'victim.sqlite3')
    return sandbox, None


def _sym_db_dangling(work, outside, sandbox):
    sandbox.mkdir()
    (sandbox / 'refunds.sqlite3').symlink_to(outside / 'planted-by-symlink.sqlite3')
    return sandbox, None


def _sym_subdir(work, outside, sandbox):
    sandbox.mkdir()
    (sandbox / 'sub').symlink_to(outside, target_is_directory=True)
    return sandbox, 'sub/planted.sqlite3'


def _sym_db_inside(work, outside, sandbox):
    sandbox.mkdir()
    (sandbox / 'real.sqlite3').write_bytes(b'')
    (sandbox / 'refunds.sqlite3').symlink_to(sandbox / 'real.sqlite3')
    return sandbox, None


def _sym_root_chain(work, outside, sandbox):
    (work / 'hop2').symlink_to(outside, target_is_directory=True)
    (work / 'hop1').symlink_to(work / 'hop2', target_is_directory=True)
    return work / 'hop1' / 'deep', None


SYM_VARIANTS = {'root_is_symlink': _sym_root, 'root_parent_is_symlink': _sym_root_parent, 'db_symlink_to_existing_outside_file': _sym_db_existing,
                'db_dangling_symlink_to_outside': _sym_db_dangling, 'db_in_symlinked_subdir': _sym_subdir, 'db_symlink_inside_root': _sym_db_inside,
                'root_via_symlink_chain': _sym_root_chain}


@pytest.mark.parametrize('kind', CLASSES)
@pytest.mark.parametrize('variant', sorted(SYM_VARIANTS))
def test_scn_c10_symlink_escape(request, record_property, tmp_path, pinned_reference, kind, variant):
    def trial(work, mp, checks):
        sandbox, outside = _layout(work)
        root, name = SYM_VARIANTS[variant](work, outside, sandbox)
        victim_before = (outside / 'victim.sqlite3').read_bytes()
        err, before, after, rep = _attempt(kind, root, name, work, sandbox if root == sandbox else root)
        _assert_confined(checks, f'{kind}/{variant}', err, before, after, rep, expect_type=None)
        checks.equal((outside / 'victim.sqlite3').read_bytes(), victim_before, 'the outside SQLite file is byte-identical')
        checks.equal(sorted(p.name for p in outside.iterdir()), ['secret.txt', 'victim.sqlite3'], 'no file appeared in the outside directory')
        checks.expect(err is not None and err.startswith(('PermissionError', 'OSError', 'ValueError')), f'{variant}: refused with a typed error, observed {err}')
        return {'surface': 'S2', 'class': kind, 'variant': variant, 'refused': err is not None, 'error': _norm(err), 'outside_unchanged': after == before,
                'process_events': rep['process_events'], 'network_events': rep['network_events'], 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, extra={'isolation_surfaces_exercised': SURFACES[1:2], 'not_exercised': NOT_EXERCISED})


def test_scn_c10_legitimate_construction_creates_only_inside_the_boundary(request, record_property, tmp_path, pinned_reference):
    """Control: the same observer sees what a legitimate construction does, so the refusals above are not vacuous."""
    def trial(work, mp, checks):
        out = {}
        for kind in CLASSES:
            sandbox = work / f'sb-{kind}'
            before = C.tree_snapshot(work)
            with C.Observer(sandbox) as obs:
                dest = _make(kind, sandbox)
            rep = obs.report()
            made = sorted(set(C.tree_snapshot(work)) - set(before))
            checks.expect(bool(made) and all(m.startswith(f'sb-{kind}') for m in made), f'{kind}: files created only under the sandbox: {made}')
            checks.equal(rep['write_class_outside_boundary'], [], f'{kind}: no write-class event outside the sandbox')
            checks.equal(rep['process_events'] + rep['network_events'], [], f'{kind}: no process/network event')
            checks.expect(rep['write_class_events'] > 0, f'{kind}: the observer does see writes (it is not blind)')
            out[kind] = {'created_names': sorted(Path(m).name for m in made), 'write_class_events_seen': rep['write_class_events'] > 0}
        return {'surface': 'S1/S2 control', 'classes': out, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial)


# ---------------------------------------------------------------------------------------------------------
# S3: route-A envelope surface
# ---------------------------------------------------------------------------------------------------------
ENVELOPE_VARIANTS = {
    'permission_filesystem_write_added': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=tuple(e.operation.requested_permissions) + ('filesystem.write',)),
    'permission_process_exec_added': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=tuple(e.operation.requested_permissions) + ('process.exec',)),
    'permission_network_connect_added': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=tuple(e.operation.requested_permissions) + ('network.connect',)),
    'permission_replaced_by_process_exec': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=('process.exec',)),
    'permission_wildcard': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=('*',)),
    'permission_path_like': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=('../../etc/shadow',)),
    'permissions_emptied': lambda e, ch: dataclasses.replace(e.operation, requested_permissions=()),
    'target_traversal_inside_prefix': lambda e, ch: dataclasses.replace(e.operation, target='urn:cognous:synthetic-account:../../etc/passwd'),
    'target_file_url': lambda e, ch: dataclasses.replace(e.operation, target='file:///etc/passwd'),
    'target_metadata_url': lambda e, ch: dataclasses.replace(e.operation, target='http://169.254.169.254/latest/meta-data/'),
    'target_absolute_path': lambda e, ch: dataclasses.replace(e.operation, target='/etc/passwd'),
    'payload_path_traversal': lambda e, ch: dataclasses.replace(e.operation, payload={'customer_id': 'customer-001', 'refund_reason': '../../etc/passwd'},
                                                                payload_commitment=ch.commitment({'customer_id': 'customer-001', 'refund_reason': '../../etc/passwd'})),
    'payload_shell_command': lambda e, ch: dataclasses.replace(e.operation, payload={'customer_id': 'customer-001', 'refund_reason': '$(touch /tmp/c10-pwned); rm -rf /'},
                                                               payload_commitment=ch.commitment({'customer_id': 'customer-001', 'refund_reason': '$(touch /tmp/c10-pwned); rm -rf /'})),
    'payload_url_fetch': lambda e, ch: dataclasses.replace(e.operation, payload={'customer_id': 'customer-001', 'refund_reason': 'http://127.0.0.1:9/exfil'},
                                                           payload_commitment=ch.commitment({'customer_id': 'customer-001', 'refund_reason': 'http://127.0.0.1:9/exfil'})),
}


@pytest.mark.parametrize('variant', sorted(ENVELOPE_VARIANTS))
def test_scn_c10_route_a_hostile_envelope_is_refused_without_prohibited_access(request, record_property, tmp_path, pinned_reference, variant):
    def trial(work, mp, checks):
        chain = C.reference().chain
        flow = H.flow_a(work, mp)
        env = dataclasses.replace(flow.env, operation=ENVELOPE_VARIANTS[variant](flow.env, chain))
        checks.expect(env != flow.env, f'{variant}: the plant changed the envelope')
        before = H.db_summary(flow.dest.path)
        marker = Path('/tmp/c10-pwned')
        marker_before = marker.exists()
        with C.Observer(work) as obs:
            res, exc = H.execute_a(flow, envelope=env)
        rep = obs.report()
        after = H.db_summary(flow.dest.path)
        refused = exc is not None or (res is not None and res.status in ('denied', 'failed'))
        checks.expect(refused, f'{variant}: a hostile envelope must be refused, observed {H.result_view(res, exc)}')
        checks.equal(after['effects'], before['effects'], f'{variant}: no destination effect')
        checks.equal(rep['process_events'], [], f'{variant}: no process event')
        checks.equal(rep['network_events'], [], f'{variant}: no network event')
        checks.equal(rep['write_class_outside_boundary'], [], f'{variant}: no write-class event outside the boundary')
        checks.equal(marker.exists(), marker_before, f'{variant}: the shell-command payload left no marker file')
        gate = H.effect_gate(after, authorized_effect_ids=())
        view = H.result_view(res, exc)
        if 'error' in view and view['error']:
            view['error'] = C.H2.normalise_reason(view['error'])
        if 'raised' in view and view['raised']:
            view['raised'] = C.H2.normalise_reason(view['raised'])
        return {'surface': 'S3', 'variant': variant, 'result': view, 'effects_after': len(after['effects']), 'process_events': rep['process_events'],
                'network_events': rep['network_events'], 'write_class_outside_boundary': rep['write_class_outside_boundary'], **gate}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, extra={'isolation_surfaces_exercised': SURFACES[2:3], 'not_exercised': NOT_EXERCISED})


# ---------------------------------------------------------------------------------------------------------
# S4: what an authorized run actually does (independent observer)
# ---------------------------------------------------------------------------------------------------------
def _read_roots(ref, work):
    roots = [work, Path(sys.prefix), Path(sys.base_prefix), Path(sys.exec_prefix), C.HERE.parent.parent, Path('/usr/lib'), Path('/lib'),
             Path('/usr/local/lib'), Path('/proc/self'), Path('/dev'), Path('/sys/devices/system/cpu')] + list(ref.base.iterdir()) + [ref.base]
    return [r.resolve() for r in roots if r.exists()]


def test_scn_c10_authorized_run_has_no_process_network_or_outside_write(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        ref = C.reference()
        flow = H.flow_a(work, mp)
        with C.Observer(work) as obs:
            res, exc = H.execute_a(flow)
        rep = obs.report()
        checks.expect(res is not None and res.status == 'executed', f'the authorized run executed: {H.result_view(res, exc)}')
        summary = H.db_summary(flow.dest.path)
        gate = H.effect_gate(summary, authorized_effect_ids=(flow.env.effect_id,))
        checks.equal(rep['process_events'], [], 'no subprocess/fork/exec during an authorized run')
        checks.equal(rep['network_events'], [], 'no socket/DNS activity during an authorized run')
        checks.equal(rep['write_class_outside_boundary'], [], 'every write-class event is inside the declared boundary')
        sqlite_paths = sorted({Path(p.split(' ')[0]).name for k, p in obs.events if k == 'sqlite3.connect'})
        outside_sqlite = sorted({p.split(' ')[0] for k, p in obs.events if k == 'sqlite3.connect' and not obs._inside(p)})
        checks.equal(outside_sqlite, [], 'no SQLite database outside the boundary was opened')
        roots = _read_roots(ref, work)
        reads_outside = sorted({p for k, p in obs.events if k == 'open-read' and not any(Path(os.path.realpath(p)).is_relative_to(r) for r in roots)})
        sensitive = [p for p in reads_outside if any(s in p for s in ('/.ssh', '/etc/shadow', '/etc/passwd', '.aws', '.netrc', '/proc/self/environ', 'credentials'))]
        checks.equal(sensitive, [], 'no credential-like or host-identity file was read')
        loaded = sorted(m for m in sys.modules if 'openshell' in m)
        checks.equal(loaded, [], 'the OpenShell optional destination was not loaded by the supported path')
        return {'surface': 'S4', 'status': res.status if res else None, 'event_kind_counts_nonread': {k: v for k, v in rep['event_counts'].items() if k != 'open-read'},
                'process_events': rep['process_events'], 'network_events': rep['network_events'], 'sqlite_database_names': sqlite_paths,
                'write_class_outside_boundary': rep['write_class_outside_boundary'], 'reads_outside_known_roots': len(reads_outside),
                'sensitive_reads': sensitive, 'openshell_modules_loaded': loaded, **gate}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, extra={'isolation_surfaces_exercised': SURFACES[3:4], 'not_exercised': NOT_EXERCISED,
                                                                         'observer': 'sys.addaudithook; observes, cannot block'})


def test_scn_c10_denied_run_has_no_process_network_or_outside_write(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        H.revoke_resolver(flow)
        with C.Observer(work) as obs:
            res, exc = H.execute_a(flow)
        rep = obs.report()
        summary = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied', f'a revoked grant is denied: {H.result_view(res, exc)}')
        checks.equal(summary['effects'], [], 'no effect')
        checks.equal(rep['process_events'] + rep['network_events'], [], 'no process/network event')
        checks.equal(rep['write_class_outside_boundary'], [], 'no write outside the boundary')
        return {'surface': 'S4', 'status': res.status if res else None, 'process_events': rep['process_events'], 'network_events': rep['network_events'],
                **H.effect_gate(summary, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial)


# ---------------------------------------------------------------------------------------------------------
# S5: static import surface
# ---------------------------------------------------------------------------------------------------------
PROHIBITED_IMPORTS = {'subprocess', 'socket', 'ctypes', 'http', 'urllib', 'requests', 'ftplib', 'smtplib', 'telnetlib', 'pty', 'multiprocessing', 'asyncio', 'ssl', 'shutil'}
PROHIBITED_CALLS = {'os.system', 'os.popen', 'os.exec', 'os.spawn', 'os.fork', 'os.symlink', 'os.link', 'eval', 'exec', '__import__'}
SUPPORTED_MODULES = ('safe_executor', 'effective_grant', 'control_plane_adapter', 'atomic_local_control_plane_executor', 'local_authority_effect',
                     'local_authority_effect_recovery', 'refund_intent', 'producer_contract', 'operation_admission', 'revocation_closeout', 'recovery_resolution')


def _scan(path):
    tree = ast.parse(path.read_text())
    imports, calls = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {a.name.split('.')[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split('.')[0])
        elif isinstance(node, ast.Call):
            f = node.func
            name = f'{f.value.id}.{f.attr}' if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else f.id if isinstance(f, ast.Name) else None
            if name:
                calls.add(name)
    return sorted(imports & PROHIBITED_IMPORTS), sorted(c for c in calls if c in PROHIBITED_CALLS or any(c.startswith(p) for p in ('os.exec', 'os.spawn')))


def test_scn_c10_supported_engine_modules_have_no_process_or_network_imports(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        ref = C.reference()
        engine = ref.paths['runtime'] / 'engine'
        table = {}
        for name in SUPPORTED_MODULES:
            path = engine / f'{name}.py'
            if not path.exists():
                table[name] = 'missing'
                continue
            imports, calls = _scan(path)
            table[name] = {'prohibited_imports': imports, 'prohibited_calls': calls}
            checks.equal(imports, [], f'{name}: no process/network/ctypes imports')
            checks.equal(calls, [], f'{name}: no process-spawning or dynamic-eval calls')
        optional = {}
        for name in ('openshell_environment', 'openshell_worker', 'c8_source_evidence'):
            path = engine / f'{name}.py'
            if path.exists():
                optional[name] = {'prohibited_imports': _scan(path)[0], 'on_supported_path': False}
        # none of the supported modules imports the optional ones
        for name in SUPPORTED_MODULES:
            path = engine / f'{name}.py'
            if path.exists():
                text = path.read_text()
                checks.expect('openshell' not in text, f'{name}: does not reference the optional OpenShell destination')
        return {'surface': 'S5', 'supported_modules': table, 'optional_modules_not_on_supported_path': optional}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, gate=False, extra={'isolation_surfaces_exercised': SURFACES[4:5]})


def test_scn_c10_declared_boundary_text_matches_what_is_claimed(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        ref = C.reference()
        doc = (ref.paths['runtime'] / 'docs' / 'execution-boundary.md').read_text()
        threat = (ref.paths['runtime'] / 'docs' / 'threat-model.md').read_text()
        for needle in ('no subprocess execution in the supported destination path', 'no destination network calls', 'rejection of symlinked database paths',
                       'These controls do not constitute host confinement'):
            checks.expect(needle in doc, f'execution-boundary.md states: {needle!r}')
        checks.expect('OS/container sandboxing' in threat and 'not implemented' in threat, 'threat-model.md declares OS/container sandboxing out of model')
        return {'declared_in_scope': ['database path traversal rejection', 'symlinked database path/component rejection', 'no subprocess, no destination network call, no credential capability'],
                'declared_out_of_model': ['host confinement', 'filesystem check/use race', 'OS/container sandbox, seccomp, network namespaces, credential brokers']}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# S6: declared out-of-model characterisations (recorded, never presented as confinement)
# ---------------------------------------------------------------------------------------------------------
def test_scn_c10_declared_out_of_model_symlink_swap_after_construction(request, record_property, tmp_path, pinned_reference):
    """The reference declares the filesystem check/use race out of model; this records what happens."""
    def trial(work, mp, checks):
        sandbox, outside = _layout(work)
        dest = _make('effective_grant', sandbox)
        victim = outside / 'victim.sqlite3'
        with sqlite3.connect(victim) as conn:  # an outside database that happens to hold the table the trusted writer targets
            conn.execute('CREATE TABLE effective_grants_v1 (grant_id TEXT PRIMARY KEY,principal TEXT NOT NULL,digest TEXT NOT NULL,'
                         'derivation TEXT NOT NULL,status TEXT NOT NULL)')
        victim_before = victim.read_bytes()
        rows_before = sqlite3.connect(victim).execute('SELECT COUNT(*) FROM effective_grants_v1').fetchone()[0]
        # a host-level actor with write access to the sandbox replaces the database file AFTER the constructor's checks
        dest.path.unlink()
        for suffix in ('-wal', '-shm'):
            (sandbox / f'refunds.sqlite3{suffix}').unlink(missing_ok=True)
        dest.path.symlink_to(victim)
        err = None
        try:
            dest.set_effective_grant(principal='p', grant_id='g', revision='1', permissions=['x'])
        except Exception as exc:
            err = C.exc_text(exc)
        rows_after = sqlite3.connect(victim).execute('SELECT COUNT(*) FROM effective_grants_v1').fetchone()[0]
        changed = rows_after != rows_before
        doc = (C.reference().paths['runtime'] / 'docs' / 'execution-boundary.md').read_text()
        checks.expect('check/use race' in doc, 'the race is declared in execution-boundary.md (so this characterisation is of a documented limit)')
        return {'surface': 'S6', 'declared_out_of_model': True, 'actor': 'host-level filesystem writer', 'access_outside_boundary_observed': changed or err is None,
                'outside_file_modified': changed, 'error': _norm(err), 'required_observation_met': not (changed or err is None),
                'note': 'documented limit: constructor-time checks only; no dirfd/openat confinement', 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, extra={'isolation_surfaces_exercised': SURFACES[5:6], 'classification': 'declared_out_of_model_characterisation'})


def test_scn_c10_declared_out_of_model_hardlinked_database_file(request, record_property, tmp_path, pinned_reference):
    """A hardlink is neither a symlink nor a path escape to the constructor's checks; a host actor can create one."""
    def trial(work, mp, checks):
        sandbox, outside = _layout(work)
        sandbox.mkdir()
        victim = outside / 'victim.sqlite3'
        os.link(victim, sandbox / 'refunds.sqlite3')
        victim_before = victim.read_bytes()
        err = None
        try:
            _make('durable', sandbox)
        except Exception as exc:
            err = C.exc_text(exc)
        changed = victim.read_bytes() != victim_before
        return {'surface': 'S6', 'declared_out_of_model': True, 'actor': 'host-level filesystem writer (needs write access to both directories)',
                'constructor_refused': err is not None, 'error': _norm(err), 'outside_inode_modified': changed,
                'required_observation_met': err is not None and not changed,
                'note': 'the reference checks symlinks and lexical escape only; link count is not examined', 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C10', trial, extra={'isolation_surfaces_exercised': SURFACES[5:6], 'classification': 'declared_out_of_model_characterisation'})
