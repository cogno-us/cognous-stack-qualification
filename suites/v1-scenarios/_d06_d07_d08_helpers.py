"""Shared bootstrap for scenarios D06 (ingress pressure), D07 (restore boundary), D08 (audit and export).

SPDX-License-Identifier: Apache-2.0

Everything here runs against the FROZEN F5b-repaired seven-component bounded synthetic reference.
It never changes product code, pins, profiles or defaults: the seven component checkouts are verified
pristine at their exact pinned commits before any of their code is imported and again at session end.
No network, payment, model or production effect is used. Linux only (owner decision D2).

Reference layout (the same one ``tools/run_security_runtime.py --prepare-work`` builds)::

    $SCN_COMPONENTS_DIR/{control_plane,runtime,replay,evidence_pack,odes,exchange,manifest}

Optional: ``SCN_HUB_DIR`` = checkout of hub 8517818f (read only, used to quote declared residual risks),
``SCN_EVIDENCE_DIR`` = directory that receives one JSON evidence file per test.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import platform
import resource
import sqlite3
import statistics
import sys
import threading
import time
from pathlib import Path

import pytest

sys.dont_write_bytecode = True  # a bytecode file inside a pinned checkout would make it non-pristine

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402  (the one source of pinned identities: freeze manifest + refreeze overlay)
import _contract_matrix as _matrix  # noqa: E402  (compatibility gate for contract-governed boundaries; the pins stay the tested revisions)
PROFILE_PATH = _pins.PROFILE_PATH
from pristine_checkout import require_pristine  # noqa: E402

FROZEN_HUB = _pins.FROZEN_HUB
FROZEN_RUNTIME = _pins.FROZEN_RUNTIME
FROZEN_CONTROL_PLANE = _pins.FROZEN_CONTROL_PLANE
COMPONENT_NAMES = ('control_plane', 'runtime', 'replay', 'evidence_pack', 'odes', 'exchange', 'manifest')
SCENARIO_VERSION = '1.0.0'


class _Reference:
    pass


_REF: _Reference | None = None


def _git(path, *args):
    import subprocess
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=60).strip()



def lost_ack_status():
    """Strict, per-runtime-row expectation of the first-delivery status after a lost acknowledgement.

    A runtime that declares ``execution-attempt-lifecycle`` conformance (the N-1 rule) reports ``reconciled`` once the destination
    is observed applied; an undeclared (older) runtime reports ``unknown``. One value per row, never "either".
    """
    declared = _matrix.declares(reference().paths['runtime'], 'execution-attempt-lifecycle')
    return 'reconciled' if declared else 'unknown'


def reference() -> _Reference:
    """Verify pins and put the reference on sys.path (idempotent)."""
    global _REF
    if _REF is not None:
        return _REF
    base = os.environ.get('SCN_COMPONENTS_DIR')
    if not base:
        pytest.fail('SCN_COMPONENTS_DIR is not set; the scenarios cannot run against the pinned reference '
                    '(see suites/v1-scenarios/README note in the report; build with tools/run_security_runtime.py --prepare-work)')
    base = Path(base).resolve()
    profile = json.loads(PROFILE_PATH.read_text())
    assert profile['components']['runtime']['revision'] == FROZEN_RUNTIME
    assert profile['components']['control_plane']['revision'] == FROZEN_CONTROL_PLANE
    # Compatibility gate: the contract-version matrix for components on a declared-contract boundary (their sha pin is the
    # recorded *tested revision*), the sha pin for every other component. Every checkout must be pristine either way.
    gates, matrix_rows = _matrix.admit_components(base, profile['components'], COMPONENT_NAMES, require_pristine,
                                                  lambda p: _git(p, 'rev-parse', 'HEAD'))
    paths, pins = {}, {}
    for name in COMPONENT_NAMES:
        spec = profile['components'][name]
        path = base / name
        paths[name] = path
        pins[name] = {'repository': spec['repository'], 'commit': gates[name]['revision'], 'tree': _git(path, 'rev-parse', 'HEAD^{tree}'),
                      'gate': gates[name]['gate'], 'tested_revision': gates[name]['tested_revision'],
                      'tested_revision_match': gates[name]['tested_revision_match']}
    hub = os.environ.get('SCN_HUB_DIR')
    hub_identity = None
    if hub:
        require_pristine(hub, FROZEN_HUB, 'hub')
        hub_identity = {'repository': 'cogno-us/cognous-open-control-stack', 'commit': FROZEN_HUB}
    env = os.environ
    env['COGNOUS_SECURITY_RUNTIME_GENERATION'] = profile.get('suite_generation', 'f5b')  # the profile selects the generation (f5b through r2, p4 from r3)
    env['GAX_RUNTIME_COMPATIBILITY_PROFILE'] = profile['exchange_compatibility_profile']
    env['MOLTBOT_SAFE_CONTROL_PLANE_ROOT'] = str(paths['control_plane'])
    env['MOLTBOT_SAFE_ROOT'] = str(paths['runtime'])
    env['UPSTREAM_MANIFEST_EXAMPLE'] = str(paths['manifest'] / 'examples/refund_integration_v1_1.manifest.json')
    order = [paths['control_plane'], paths['control_plane'] / 'src', paths['runtime'], paths['replay'] / 'src',
             paths['evidence_pack'] / 'src', paths['odes'] / 'src', paths['exchange']]
    for entry in reversed(order):
        sys.path.insert(0, str(entry))
    # The qualification repository has its own ``tests`` directory; the control-plane fixtures need theirs.
    loaded = sys.modules.get('tests')
    if loaded is not None and not str(getattr(loaded, '__file__', '') or '').startswith(str(paths['control_plane'])):
        for key in [k for k in sys.modules if k == 'tests' or k.startswith('tests.')]:
            del sys.modules[key]
    chain_spec = importlib.util.spec_from_file_location('scn_security_runtime_chain', ROOT / 'suites/security-runtime/test_security_runtime_chain.py')
    chain = importlib.util.module_from_spec(chain_spec)
    sys.modules['scn_security_runtime_chain'] = chain
    chain_spec.loader.exec_module(chain)  # the frozen harness: integrated(), produce(), exchange_setup()
    ref = _Reference()
    ref.paths, ref.pins, ref.hub = paths, pins, hub_identity
    ref.matrix_rows = matrix_rows
    ref.profile = profile
    ref.chain = chain
    ref.base = base
    _REF = ref
    return ref


def assert_pins_still_pristine():
    ref = reference()
    for name, path in ref.paths.items():
        require_pristine(path, ref.pins[name]['commit'], name)
    if ref.hub:
        require_pristine(os.environ['SCN_HUB_DIR'], FROZEN_HUB, 'hub')


@pytest.fixture(scope='module')
def pinned_reference():
    """Module fixture: pins verified pristine before use and again after the module's tests."""
    ref = reference()
    yield ref
    assert_pins_still_pristine()


# ----------------------------------------------------------------------------------------------
# determinism: execute twice under unchanged conditions and compare (owner decision D3)
# ----------------------------------------------------------------------------------------------

def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False, default=str).encode()


def digest(value) -> str:
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def compare_runs(run1, run2):
    d1, d2 = digest(run1['outcome']), digest(run2['outcome'])
    return {'assertion': 'outcome digest of run 1 equals run 2 under unchanged conditions',
            'run1_outcome_digest': d1, 'run2_outcome_digest': d2, 'verdict': 'MATCH' if d1 == d2 else 'MISMATCH'}


def environment_identity():
    ref = reference()
    return {'scenario_version': SCENARIO_VERSION, 'python': sys.version.split()[0], 'platform': platform.platform(),
            'sqlite': sqlite3.sqlite_version, 'cpu_count': os.cpu_count(), 'components': ref.pins, 'contract_matrix': ref.matrix_rows,
            'hub': ref.hub or {'repository': 'cogno-us/cognous-open-control-stack', 'commit': FROZEN_HUB, 'verified_in_this_run': False},
            'frozen_pins_asserted': {'hub': FROZEN_HUB, 'runtime': FROZEN_RUNTIME, 'control_plane': FROZEN_CONTROL_PLANE},
            'network': 'none', 'paid_model_calls': 0, 'live_effects': 0}


def record(request, record_property, name, payload):
    """Attach evidence to the JUnit record and, when SCN_EVIDENCE_DIR is set, to a JSON file."""
    payload = {'test': request.node.name, 'environment': environment_identity(), **payload}
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    record_property(name, text)
    target = os.environ.get('SCN_EVIDENCE_DIR')
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        (Path(target) / (request.node.name + '.json')).write_text(text + '\n')
    return payload


# ----------------------------------------------------------------------------------------------
# D06 measurement (report-only; no pass/fail thresholds are applied to any number here)
# ----------------------------------------------------------------------------------------------

def _status_kb(field):
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith(field + ':'):
            return int(line.split()[1])
    return None


def _reset_peak_rss():
    try:
        Path('/proc/self/clear_refs').write_text('5')
        return True
    except OSError:
        return False


def dir_bytes(path):
    total = 0
    for p in Path(path).rglob('*'):
        if p.is_file():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
    return total


def percentiles(samples):
    if not samples:
        return {'n': 0}
    s = sorted(samples)
    pick = lambda q: s[min(len(s) - 1, int(q * len(s)))]
    return {'n': len(s), 'p50_ms': round(pick(0.50) * 1000, 3), 'p95_ms': round(pick(0.95) * 1000, 3),
            'p99_ms': round(pick(0.99) * 1000, 3), 'max_ms': round(s[-1] * 1000, 3), 'mean_ms': round(statistics.fmean(s) * 1000, 3)}


class Meter:
    """Measure wall time, CPU, memory, concurrency, storage and per-class latency of a block."""

    def __init__(self, label, watch_dirs=()):
        self.label = label
        self.watch_dirs = [Path(p) for p in watch_dirs]
        self.lat = {}
        self._lock = threading.Lock()
        self.inflight = 0
        self.max_inflight = 0
        self.threads_peak = 0
        self.requests = 0

    def __enter__(self):
        self.peak_reset = _reset_peak_rss()
        self.rss_before_kb = _status_kb('VmRSS')
        self.storage_before = sum(dir_bytes(p) for p in self.watch_dirs)
        self.cpu0 = time.process_time()
        self.ru0 = resource.getrusage(resource.RUSAGE_SELF)
        self.t0 = time.perf_counter()
        return self

    def timed(self, klass, fn, *args, **kwargs):
        with self._lock:
            self.inflight += 1
            self.max_inflight = max(self.max_inflight, self.inflight)
            self.threads_peak = max(self.threads_peak, threading.active_count())
            self.requests += 1
        t = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            dt = time.perf_counter() - t
            with self._lock:
                self.inflight -= 1
                self.lat.setdefault(klass, []).append(dt)

    def __exit__(self, *exc):
        self.wall = time.perf_counter() - self.t0
        self.cpu = time.process_time() - self.cpu0
        ru1 = resource.getrusage(resource.RUSAGE_SELF)
        self.ctx_switches_voluntary = ru1.ru_nvcsw - self.ru0.ru_nvcsw
        self.ctx_switches_involuntary = ru1.ru_nivcsw - self.ru0.ru_nivcsw
        self.rss_after_kb = _status_kb('VmRSS')
        self.rss_peak_kb = _status_kb('VmHWM')
        self.storage_after = sum(dir_bytes(p) for p in self.watch_dirs)
        return False

    def report(self):
        all_samples = [x for v in self.lat.values() for x in v]
        return {'label': self.label, 'report_only': True, 'thresholds_applied': None,
                'requests': self.requests, 'wall_seconds': round(self.wall, 4),
                'request_rate_per_second': round(self.requests / self.wall, 2) if self.wall else None,
                'cpu_seconds_process_all_threads': round(self.cpu, 4),
                'cpu_utilisation_of_one_core': round(self.cpu / self.wall, 3) if self.wall else None,
                'memory_kb': {'rss_before': self.rss_before_kb, 'rss_after': self.rss_after_kb, 'peak_rss_during_block': self.rss_peak_kb,
                              'peak_counter_reset_at_start': self.peak_reset},
                'concurrency': {'max_in_flight_requests': self.max_inflight, 'peak_python_threads': self.threads_peak},
                'storage_bytes': {'before': self.storage_before, 'after': self.storage_after, 'growth': self.storage_after - self.storage_before,
                                  'growth_per_request': round((self.storage_after - self.storage_before) / self.requests, 1) if self.requests else None},
                'context_switches': {'voluntary': self.ctx_switches_voluntary, 'involuntary': self.ctx_switches_involuntary},
                'latency': {'all': percentiles(all_samples), **{k: percentiles(v) for k, v in sorted(self.lat.items())}}}


# ----------------------------------------------------------------------------------------------
# D08: export the reference's own artifacts, plant defects in COPIES, and evaluate with its consumers
# ----------------------------------------------------------------------------------------------

D08_CASES = ('valid', 'lost_ack', 'revoked', 'unreadable')
from _reason_norm import normalise_reason  # noqa: E402,F401  (shared normaliser; re-exported for existing callers)


def build_exports(case, root):
    """Produce one case with the frozen harness and write every exported artifact to ``root/case``.

    Returns {'dir': Path, 'objects': {...JSON-able artifacts...}, 'sha256': {file: digest}}.
    """
    ref = reference()
    out = Path(root) / case
    out.mkdir(parents=True)
    with pytest.MonkeyPatch.context() as mp:
        p, r, f, d, dest, result, export, bundle = ref.chain.produce(out / 'producer', mp, case)
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    from odes import export_cognous_stack_package
    bundle_dict = bundle.model_dump(mode='json')
    pack = import_manifest_reconstruction(f.manifest, bundle_dict)
    objects = {
        'journal': f.records.load().model_dump(mode='json'),
        'proposal': p.model_dump(mode='json'),
        'executor_export': export,
        'bundle': bundle_dict,
        'pack': pack.model_dump(mode='json'),
        'odes': export_cognous_stack_package(f.manifest, bundle_dict),
        'manifest': f.manifest,
        'destination_observation': dest.observe(d.effect_id),
    }
    sums = {}
    for name, value in objects.items():
        path = out / f'{name}.json'
        path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + '\n')
        sums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'dir': out, 'sha256': sums, 'objects_on_disk': {n: out / f'{n}.json' for n in objects},
            'status': result.status, 'effect_id': d.effect_id,
            'destination_effects': dest.effect_count(d.binding.grant_id)}


def load_copy(exports, name):
    """A fresh deep copy of an exported artifact, read back from the exported file (never the pinned source)."""
    return json.loads(exports['objects_on_disk'][name].read_text())


def _flag_replay(bundle):
    flags = []
    if not all(x.complete for x in bundle.import_reports):
        flags.append('import_incomplete')
    if bundle.status != 'reconstruction_complete':
        flags.append('status=' + bundle.status)
    if any(fi.severity == 'error' for x in bundle.import_reports for fi in x.findings):
        flags.append('error_finding')
    return flags


def eval_replay(journal, proposal, executor_export):
    from agent_replay_bundle.importers import import_bounded_workflow
    cp_rev = reference().chain.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION
    try:
        bundle = import_bounded_workflow(journal, proposal=proposal, moltbot_export=executor_export, control_plane_revision=cp_rev)
    except Exception as exc:  # the importer's typed refusal is the detection
        return {'stage': 'replay_import', 'verdict': 'rejected', 'why': type(exc).__name__ + ': ' + normalise_reason(exc)}, None
    flags = _flag_replay(bundle)
    return {'stage': 'replay_import', 'verdict': 'flagged' if flags else 'accepted', 'why': ','.join(flags)}, bundle.model_dump(mode='json')


def eval_pack_from_bundle(manifest, bundle_dict):
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    from agent_governance_evidence_pack import validate_evidence_pack
    try:
        pack = import_manifest_reconstruction(manifest, bundle_dict)
        report = validate_evidence_pack(pack)
    except Exception as exc:
        return {'stage': 'evidence_pack_import', 'verdict': 'rejected', 'why': type(exc).__name__ + ': ' + normalise_reason(exc)}
    errors = sorted(i.code for i in report.issues if str(i.severity).endswith('error'))
    return {'stage': 'evidence_pack_import', 'verdict': 'accepted' if report.valid else 'flagged', 'why': ','.join(errors)}


_ODES_BASELINE_FAIL = {'consumption_conditions', 'recipient_reliance_decision'}  # fail on every clean export with an empty recipient policy


def eval_odes_package(package):
    from odes import evaluate_recipient_package
    from odes.recipient_validator import _evaluate_replay_semantics
    try:
        semantic = _evaluate_replay_semantics(package)
        result = evaluate_recipient_package(package, {})
    except Exception as exc:
        return {'stage': 'odes_recipient', 'verdict': 'rejected', 'why': type(exc).__name__ + ': ' + normalise_reason(exc)}
    failing = sorted(k for k, v in result.items() if isinstance(v, dict) and v.get('status') == 'fail') 
    new_failing = [k for k in failing if k not in _ODES_BASELINE_FAIL]
    flags = (['replay_semantic=' + semantic['status']] if semantic['status'] != 'pass' else []) + ['fail:' + k for k in new_failing]
    return {'stage': 'odes_recipient', 'verdict': 'flagged' if flags else 'accepted', 'why': ','.join(flags)}


def eval_odes_from_bundle(manifest, bundle_dict):
    from odes import export_cognous_stack_package
    try:
        package = export_cognous_stack_package(manifest, bundle_dict)
    except Exception as exc:
        return {'stage': 'odes_export', 'verdict': 'rejected', 'why': type(exc).__name__ + ': ' + normalise_reason(exc)}
    return eval_odes_package(package)


def eval_pack_artifact(pack_dict):
    from agent_governance_evidence_pack.loader import load_evidence_pack_json
    from agent_governance_evidence_pack import validate_evidence_pack
    try:
        report = validate_evidence_pack(load_evidence_pack_json(pack_dict))
    except Exception as exc:
        return {'stage': 'evidence_pack_validate', 'verdict': 'rejected', 'why': type(exc).__name__ + ': ' + normalise_reason(exc)}
    errors = sorted(i.code for i in report.issues if str(i.severity).endswith('error'))
    return {'stage': 'evidence_pack_validate', 'verdict': 'accepted' if report.valid else 'flagged', 'why': ','.join(errors)}


def evaluate_producer_exports(manifest, journal, proposal, executor_export):
    """Replay import -> Evidence Pack import/validate -> ODES export/recipient evaluation, from producer artifacts."""
    stages = []
    verdict, bundle = eval_replay(journal, proposal, executor_export)
    stages.append(verdict)
    if bundle is not None:
        stages.append(eval_pack_from_bundle(manifest, bundle))
        stages.append(eval_odes_from_bundle(manifest, bundle))
    return stages


def evaluate_bundle(manifest, bundle_dict):
    return [eval_pack_from_bundle(manifest, bundle_dict), eval_odes_from_bundle(manifest, bundle_dict)]


def summarise(stages):
    """Collapse stage verdicts: detected when any stage rejects or flags."""
    first = next((s for s in stages if s['verdict'] in ('rejected', 'flagged')), None)
    return {'detected': first is not None, 'first_detecting_stage': first['stage'] if first else None,
            'verdict': first['verdict'] if first else 'accepted', 'why': first['why'] if first else ''}


# ---- planted-defect catalogue --------------------------------------------------------------------
# Each mutation edits a deep copy loaded from an exported file. Classes follow the scenario stimulus:
# drop, reorder, duplicate, corrupt, remove_observation. ``fn(obj)`` edits in place; a mutation that leaves the
# artifact unchanged for a case is not applicable to that case (nothing to plant) and is listed, not run.

def _swap(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]


def _list_mutations(prefix, target, getter, klass_names=('drop', 'reorder', 'duplicate')):
    """drop / reorder / duplicate mutations over one list inside the artifact."""
    def drop(obj, which):
        lst = getter(obj)
        lst.pop({'first': 0, 'last': -1, 'middle': len(lst) // 2}[which])
    out = [(f'{prefix}.drop_first', 'drop', target, lambda o: drop(o, 'first')),
           (f'{prefix}.drop_middle', 'drop', target, lambda o: drop(o, 'middle')),
           (f'{prefix}.drop_last', 'drop', target, lambda o: drop(o, 'last')),
           (f'{prefix}.drop_all', 'remove_observation' if 'observ' in prefix else 'drop', target, lambda o: getter(o).clear()),
           (f'{prefix}.reorder_swap_first_two', 'reorder', target, lambda o: _swap(getter(o), 0, 1)),
           (f'{prefix}.reorder_reverse', 'reorder', target, lambda o: getter(o).reverse()),
           (f'{prefix}.duplicate_first', 'duplicate', target, lambda o: getter(o).insert(1, copy.deepcopy(getter(o)[0]))),
           (f'{prefix}.duplicate_last_appended', 'duplicate', target, lambda o: getter(o).append(copy.deepcopy(getter(o)[-1])))]
    return out


def producer_mutations():
    t = 'producer'
    J = lambda key: (lambda o: o['journal'][key])
    X = lambda key: (lambda o: o['executor_export'][key])
    m = []
    for key in ('check_events', 'decisions', 'resolution_checks', 'refusals', 'attempts', 'observations', 'reconciliations', 'closeouts'):
        m += _list_mutations('journal.' + key, t, J(key))
    for key in ('effects', 'attempts', 'attempt_events', 'observations', 'control_plane_attempts'):
        m += _list_mutations('export.' + key, t, X(key))

    def setitem(path, value_fn):
        def fn(o):
            cur = o
            for k in path[:-1]:
                cur = cur[k]
            cur[path[-1]] = value_fn(cur[path[-1]])
        return fn
    flip_status = lambda v: 'executed' if v != 'executed' else 'unknown'
    m += [
        ('journal.check_events.corrupt_commitment', 'corrupt', t, lambda o: o['journal']['check_events'][6].__setitem__('proposal_commitment', 'sha256:' + '1' * 64)),
        ('journal.decisions.corrupt_result', 'corrupt', t, lambda o: o['journal']['decisions'][0].__setitem__('result', 'hold' if o['journal']['decisions'][0]['result'] == 'authorized' else 'authorized')),
        ('journal.decisions.corrupt_effect_id', 'corrupt', t, lambda o: o['journal']['decisions'][0].__setitem__('effect_id', 'sha256:' + '2' * 64)),
        ('journal.refusals.corrupt_reason', 'corrupt', t, lambda o: o['journal']['refusals'][0].__setitem__('reasons', ['grant_active'])),
        ('journal.attempts.corrupt_status', 'corrupt', t, lambda o: o['journal']['attempts'][0].__setitem__('status', 'acknowledged' if o['journal']['attempts'][0].get('status') != 'acknowledged' else 'failed')),
        ('journal.observations.corrupt_state', 'corrupt', t, lambda o: o['journal']['observations'][-1].__setitem__('state', 'absent')),
        ('journal.reconciliations.corrupt_observed_state', 'corrupt', t, lambda o: o['journal']['reconciliations'][-1].__setitem__('observed_state', 'absent')),
        ('journal.closeouts.corrupt', 'corrupt', t, lambda o: o['journal']['closeouts'][0].__setitem__('reasons', ['forged'])),
        ('export.effects.corrupt_amount', 'corrupt', t, lambda o: o['executor_export']['effects'][0].__setitem__('amount', 99.0)),
        ('export.effects.corrupt_state', 'corrupt', t, lambda o: o['executor_export']['effects'][0].__setitem__('state', 'partial')),
        ('export.attempt_events.corrupt_status', 'corrupt', t, lambda o: o['executor_export']['attempt_events'][-1].__setitem__('status', 'executed')),
        ('export.result.corrupt_status', 'corrupt', t, setitem(['executor_export', 'execution_result', 'status'], flip_status)),
        ('export.result.corrupt_acknowledged', 'corrupt', t, setitem(['executor_export', 'execution_result', 'acknowledged'], lambda v: not v)),
        ('export.result.corrupt_newly_executed', 'corrupt', t, setitem(['executor_export', 'execution_result', 'newly_executed'], lambda v: not v)),
        ('export.result.corrupt_observed_state', 'corrupt', t, setitem(['executor_export', 'execution_result', 'observed_state'], lambda v: 'absent' if v != 'absent' else 'applied')),
        ('export.result.remove_observation', 'remove_observation', t, setitem(['executor_export', 'execution_result', 'observation'], lambda v: None if v else (_ for _ in ()).throw(KeyError('no observation present')))),
        ('export.control_plane_evidence.remove', 'drop', t, lambda o: o['executor_export'].__setitem__('control_plane_evidence', {})),
    ]
    return m


def bundle_mutations(bundle):
    """Mutations of the exported Replay reconstruction bundle, generated from the record types it holds."""
    t = 'bundle'
    types = sorted({r['record_type'] for r in bundle['records']})
    B = lambda o: o['records']

    def by_type(rt):
        return lambda o: [i for i, r in enumerate(o['records']) if r['record_type'] == rt]
    m = []
    for rt in types:
        idx = by_type(rt)
        klass = 'remove_observation' if 'observation' in rt else 'drop'
        m.append((f'bundle.record[{rt}].drop_first', klass, t, lambda o, idx=idx: o['records'].pop(idx(o)[0])))
        m.append((f'bundle.record[{rt}].drop_all', klass, t, lambda o, rt=rt: o.__setitem__('records', [r for r in o['records'] if r['record_type'] != rt])))
        m.append((f'bundle.record[{rt}].reorder_swap_first_two', 'reorder', t, lambda o, idx=idx: _swap(o['records'], idx(o)[0], idx(o)[1])))
        m.append((f'bundle.record[{rt}].duplicate', 'duplicate', t, lambda o, idx=idx: o['records'].append(copy.deepcopy(o['records'][idx(o)[0]]))))

        def corrupt(o, rt=rt, idx=idx):
            data = o['records'][idx(o)[0]]['data']
            for key in sorted(data):  # alter one existing scalar value (never merely add an extension field)
                if isinstance(data[key], str) and data[key]:
                    data[key] = data[key] + '~tampered'
                    return
                if isinstance(data[key], (int, float)) and not isinstance(data[key], bool):
                    data[key] = data[key] + 1
                    return
            raise KeyError('no scalar to corrupt')
        m.append((f'bundle.record[{rt}].corrupt_existing_value', 'corrupt', t, corrupt))
    m += [
        ('bundle.records.reorder_reverse', 'reorder', t, lambda o: o['records'].reverse()),
        ('bundle.links.drop_all', 'drop', t, lambda o: o['links'].clear()),
        ('bundle.commitments.drop_all', 'drop', t, lambda o: o['commitments'].clear()),
        ('bundle.import_reports.drop_all', 'remove_observation', t, lambda o: o['import_reports'].clear()),
        ('bundle.import_reports.drop_findings', 'remove_observation', t, lambda o: [x['findings'].clear() for x in o['import_reports']]),
        ('bundle.status.corrupt', 'corrupt', t, lambda o: o.__setitem__('status', 'incomplete')),
        ('bundle.semantics.promote_independent_verification', 'corrupt', t, lambda o: o['semantics'].__setitem__('independent_effect_verification', True)),
        ('bundle.semantics.promote_destination_observation', 'corrupt', t, lambda o: o['semantics'].__setitem__('destination_observation', 'not_performed' if o['semantics']['destination_observation'] != 'not_performed' else 'producer_reported')),
    ]
    return m


def pack_mutations(pack):
    t = 'pack'
    ti = lambda o: o['metadata']['traceable_import']
    m = []
    for key in ('lifecycle_records', 'source_record_refs', 'conversion_losses', 'import_findings', 'unresolved_issues', 'replay_import_reports'):
        if isinstance(pack['metadata']['traceable_import'].get(key), list) and pack['metadata']['traceable_import'][key]:
            klass_all = 'remove_observation' if key in ('conversion_losses', 'import_findings', 'unresolved_issues', 'replay_import_reports') else 'drop'
            m += [(f'pack.{key}.drop_first', 'drop', t, lambda o, key=key: ti(o)[key].pop(0)),
                  (f'pack.{key}.drop_all', klass_all, t, lambda o, key=key: ti(o)[key].clear())]
            if len(pack['metadata']['traceable_import'][key]) > 1:
                m += [(f'pack.{key}.reorder_swap_first_two', 'reorder', t, lambda o, key=key: _swap(ti(o)[key], 0, 1))]
            m += [(f'pack.{key}.duplicate_first', 'duplicate', t, lambda o, key=key: ti(o)[key].insert(1, copy.deepcopy(ti(o)[key][0])))]
    rb = lambda o: ti(o)['retained_sources']['reconstruction_bundle']
    m += [
        ('pack.retained_bundle.records.drop_first', 'drop', t, lambda o: rb(o)['records'].pop(0)),
        ('pack.retained_bundle.records.reorder_reverse', 'reorder', t, lambda o: rb(o)['records'].reverse()),
        ('pack.retained_bundle.records.duplicate_first', 'duplicate', t, lambda o: rb(o)['records'].append(copy.deepcopy(rb(o)['records'][0]))),
        ('pack.retained_bundle.records.corrupt', 'corrupt', t, lambda o: rb(o)['records'][0]['data'].__setitem__('__planted__', 'tampered')),
        ('pack.retained_bundle.import_reports.drop_all', 'remove_observation', t, lambda o: rb(o)['import_reports'].clear()),
        ('pack.derived_counts.corrupt', 'corrupt', t, lambda o: ti(o)['derived_counts'].__setitem__(next(iter(ti(o)['derived_counts'])), 12345)),
        ('pack.replay_semantic_validation.corrupt_status', 'corrupt', t, lambda o: ti(o)['replay_semantic_validation'].__setitem__('status', 'not_validated')),
        ('pack.replay_semantics.promote_independent_verification', 'corrupt', t, lambda o: ti(o)['replay_semantics'].__setitem__('independent_effect_verification', True)),
        ('pack.reconstruction_completeness.corrupt', 'corrupt', t, lambda o: ti(o).__setitem__('reconstruction_completeness', 'reconstruction_partial')),
        ('pack.refusal_vocabulary_summary.relabel_total', 'corrupt', t, lambda o: ti(o)['refusal_vocabulary_summary'].__setitem__('total_refusals', 7)),
    ]
    return m


def odes_mutations(package, rehash):
    """Mutations of the exported ODES package. ``rehash`` recomputes the package digests afterwards."""
    t = 'odes_rehashed' if rehash else 'odes'
    EF = lambda o: o['provenance']['execution_facts']
    RB = lambda o: o['provenance']['retained_sources']['reconstruction_bundle']
    m = []
    for key in ('resolution_check_event', 'resolution_check', 'effect_time_refusal', 'attempt_closeout', 'effect_observation_history',
                'control_plane_attempt_transitions', 'destination_effects', 'accepted_control_plane_observations', 'executor_observations', 'reconciliations'):
        if isinstance(package['provenance']['execution_facts'].get(key), list) and package['provenance']['execution_facts'][key]:
            klass_all = 'remove_observation' if 'observ' in key else 'drop'
            m += [(f'odes.execution_facts.{key}.drop_first', 'drop', t, lambda o, key=key: EF(o)[key].pop(0)),
                  (f'odes.execution_facts.{key}.drop_all', klass_all, t, lambda o, key=key: EF(o)[key].clear())]
            if len(package['provenance']['execution_facts'][key]) > 1:
                m.append((f'odes.execution_facts.{key}.reorder_swap_first_two', 'reorder', t, lambda o, key=key: _swap(EF(o)[key], 0, 1)))
            m.append((f'odes.execution_facts.{key}.duplicate_first', 'duplicate', t, lambda o, key=key: EF(o)[key].insert(1, copy.deepcopy(EF(o)[key][0]))))
    m += [
        ('odes.retained_bundle.records.drop_first', 'drop', t, lambda o: RB(o)['records'].pop(0)),
        ('odes.retained_bundle.records.reorder_reverse', 'reorder', t, lambda o: RB(o)['records'].reverse()),
        ('odes.retained_bundle.records.duplicate_first', 'duplicate', t, lambda o: RB(o)['records'].append(copy.deepcopy(RB(o)['records'][0]))),
        ('odes.retained_bundle.records.corrupt', 'corrupt', t, lambda o: RB(o)['records'][0]['data'].__setitem__('__planted__', 'tampered')),
        ('odes.retained_bundle.import_reports.drop_all', 'remove_observation', t, lambda o: RB(o)['import_reports'].clear()),
        ('odes.execution_facts.promote_independent_delivery_verification', 'corrupt', t, lambda o: EF(o).__setitem__('independent_delivery_verification', 'verified')),
        ('odes.execution_facts.promote_retry_permission', 'corrupt', t, lambda o: EF(o).__setitem__('retry_permission', 'permitted')),
        ('odes.execution_facts.corrupt_acknowledgement_summary', 'corrupt', t, lambda o: EF(o).__setitem__('acknowledgement_summary', 'acknowledged' if EF(o)['acknowledgement_summary'] != 'acknowledged' else 'unknown')),
        ('odes.execution_facts.corrupt_destination_observed', 'corrupt', t, lambda o: EF(o).__setitem__('destination_observed', 'absent' if EF(o)['destination_observed'] != 'absent' else 'applied')),
        ('odes.execution_facts.remove_destination_observation_scope', 'remove_observation', t, lambda o: EF(o).pop('destination_observation_scope')),
    ]
    return m


def odes_rehash(package):
    """Recompute the ODES content digests after an edit (the documented content-self-consistency forgery)."""
    from odes.recipient_validator import _material_package_content, _package_core
    from odes.common import sha256 as odes_sha256
    package['integrity']['value'] = odes_sha256(_package_core(package))
    package['package_digest'] = odes_sha256(_material_package_content(package))
    return package


def apply_mutation(base, fn, rehash=False):
    """Deep-copy ``base`` (already loaded from the exported file), apply ``fn``; returns (copy, changed)."""
    work = copy.deepcopy(base)
    try:
        fn(work)
    except (KeyError, IndexError, TypeError, StopIteration):
        return work, False  # nothing to plant for this case
    changed = work != base
    if rehash and changed:
        odes_rehash(work)
    return work, changed


# ----------------------------------------------------------------------------------------------
# D07: restore boundary worlds (frozen F5b chain + frozen C1 atomic claim profile)
# ----------------------------------------------------------------------------------------------


def sqlite_backup(source, target):
    """Explicit consistent SQLite backup/restore primitive (no live callers during restore, as in the reference tests)."""
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    return hashlib.sha256(Path(target).read_bytes()).hexdigest()


def sqlite_rows(path, tables=None):
    """Whole-table state of a SQLite file via a read-only connection (an observer that cannot write)."""
    with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True) as db:
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        out = {}
        for name in names:
            if tables is not None and name not in tables:
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            out[name] = [list(r) for r in db.execute('SELECT * FROM ' + quoted + ' ORDER BY rowid')]
    return out


class Witness:
    """Append-only commit witness OUTSIDE the restore set. It is a test observer, never an admission input, NOT an anchor.

    It records every effect row that appears in the destination during a call, by diffing read-only observations
    around the call (independent of the executor's own success/ack claims).
    """

    def __init__(self, path, db_path):
        self.path, self.db_path = Path(path), Path(db_path)
        self.entries = []

    def _effects(self):
        try:
            with sqlite3.connect(self.db_path.resolve().as_uri() + '?mode=ro', uri=True) as db:
                return {(r[0], r[1]) for r in db.execute('SELECT effect_id, rowid FROM effects')}
        except sqlite3.OperationalError:
            return set()

    def around(self, fn):
        before = self._effects()
        try:
            return fn()
        finally:
            for effect_id, _ in sorted(self._effects() - before):
                entry = {'synthetic_commit_observed': effect_id, 'sequence': len(self.entries) + 1}
                self.entries.append(entry)
                with self.path.open('a') as f:
                    f.write(json.dumps(entry) + '\n')

    def commits(self, effect_id=None):
        return len([e for e in self.entries if effect_id in (None, e['synthetic_commit_observed'])])


class ChainWorld:
    """One integrated F5b flow (Control Plane + runtime + EffectiveGrantDestination) with snapshot/restore of each side."""

    def __init__(self, root, monkeypatch):
        ref = reference()
        self.root = Path(root)
        self.chain = ref.chain
        (self.p, self.r, self.f, self.c, self.d, self.dest, self.executor, self.env) = ref.chain.integrated(self.root, monkeypatch)
        self.now = ref.chain.NOW
        self.witness = Witness(self.root / 'outside-restore-witness.jsonl', self.dest.path)
        self.grant_id = self.d.binding.grant_id

    # --- actions
    def execute(self, simulate=None):
        def run():
            try:
                res = self.executor.execute(envelope=self.env, proposal=self.p, decision=self.d, now=self.now, simulate=simulate)
                return {'status': res.status, 'newly_executed': res.newly_executed, 'attempted': res.attempted, 'acknowledged': res.acknowledged,
                        'observed_state': res.observed_state, 'error': res.error}
            except Exception as exc:  # a raised refusal is still an observed outcome
                return {'status': 'raised:' + type(exc).__name__, 'newly_executed': False, 'error': normalise_reason(exc)}
        return self.witness.around(run)

    def revoke_resolver(self):
        next(iter(self.r.statuses.values())).status = 'revoked'

    def revoke_destination(self):
        self.dest.set_effective_grant(principal=self.p.principal, grant_id=self.grant_id, revision=self.d.binding.grant_revision,
                                      permissions=self.p.requested_permissions, status='revoked')

    # --- state
    def effects(self):
        return self.dest.effect_count(self.grant_id)

    def journal_counts(self):
        rec = self.f.records.load()
        return {k: len(getattr(rec, k)) for k in ('decisions', 'refusals', 'attempts', 'observations', 'reconciliations', 'closeouts', 'check_events')}

    # --- authority-side snapshot/restore: resolver statuses + Control Plane journal file
    def authority_snapshot(self):
        return {'statuses': copy.deepcopy(self.r.statuses), 'journal': self.f.records.path.read_bytes()}

    def authority_restore(self, snap):
        self.r.statuses.clear()
        self.r.statuses.update(copy.deepcopy(snap['statuses']))
        self.f.records.path.write_bytes(snap['journal'])

    # --- destination-side snapshot/restore: complete SQLite store (effects, attempts, failures, effective grants)
    def destination_snapshot(self, name):
        snap = self.root / name
        sqlite_backup(self.dest.path, snap)
        return snap

    def destination_restore(self, snap):
        sqlite_backup(snap, self.dest.path)


C1_AUTHORITY_TABLES = ('authority_grants_v1', 'authority_approvals_v1', 'authority_policies_v1', 'authority_evidence_v1',
                       'execution_claims_v1', 'effect_budgets_v1')
# The runtime keeps revocations of destination grants in a separate table (authority_grant_revocations_v1). C1_AUTHORITY_TABLES does
# not include it, so a restore of C1_AUTHORITY_TABLES leaves the revocation memory in place; this set adds it for the case that
# rolls the revocation memory back as well (SCN-D07 'c1_authority_tables_and_revocations_after_revoke').
C1_AUTHORITY_TABLES_WITH_REVOCATIONS = C1_AUTHORITY_TABLES + ('authority_grant_revocations_v1',)
C1_DESTINATION_TABLES = ('effects', 'attempts', 'attempt_events', 'authority_effect_receipts_v1', 'failure_records_v1')


def restore_tables(snapshot, live, tables):
    """Table-granular restore: replace only ``tables`` of ``live`` with their rows from ``snapshot`` (a table absent from the snapshot becomes empty)."""
    with sqlite3.connect(live) as db:
        db.execute('ATTACH DATABASE ? AS snap', (str(snapshot),))
        for t in tables:
            db.execute(f'DELETE FROM main."{t}"')
            # a table the snapshot does not have yet (the revocation table is created at the first revocation) is restored to empty
            if db.execute('SELECT 1 FROM snap.sqlite_master WHERE type = ? AND name = ?', ('table', t)).fetchone():
                db.execute(f'INSERT INTO main."{t}" SELECT * FROM snap."{t}"')
        db.commit()
        db.execute('DETACH DATABASE snap')


class C1World:
    """Frozen C1 atomic authority/effect profile (the one the matched-refund job drives): authority tables and effect
    tables live in ONE SQLite file, so 'authority alone' is a table-granular restore and 'destination' a whole-file restore."""

    def __init__(self, root):
        ref = reference()
        spec = importlib.util.spec_from_file_location('scn_c1_helpers', ROOT / 'suites/cognous-execution-runtime/tests/test_local_authority_effect.py')
        self.h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.h)
        from engine.safe_executor import LocalExecutionPolicy
        from engine.local_authority_effect import AtomicAuthorityEffectDestination, AtomicLocalControlPlaneExecutor
        self._Dest, self._Exec = AtomicAuthorityEffectDestination, AtomicLocalControlPlaneExecutor
        self.root = Path(root)
        self.clock = self.h.MutableClock(self.h.BASE)
        self.env = self.h.envelope()
        self.claim = self.h.make_claim(self.env)
        op = self.env.operation
        self.policy = LocalExecutionPolicy(frozenset({op.institution_id}), frozenset({op.authority_domain}), frozenset({op.adapter_id}),
                                           frozenset({op.action_id}), ('urn:cognous:synthetic-account:',), frozenset({'USD'}), 100.0, 1)
        self.reopen()
        self.dest.provision_claim(self.claim)
        self.witness = Witness(self.root / 'outside-restore-witness.jsonl', self.dest.path)
        self.n = 0

    def reopen(self):
        self.dest = self._Dest(self.root / 'state', clock=self.clock)
        self.executor = self._Exec(workflow=object(), destination=self.dest, policy=self.policy)

    def execute(self, simulate=None):
        self.n += 1

        def run():
            try:
                res = self.executor.execute(envelope=self.env, claim_id=self.claim.claim_id, attempt_id=f'attempt:d07:{self.n:03d}', simulate=simulate)
                return {'status': res.status, 'newly_executed': res.newly_executed, 'error': normalise_reason(res.error) if res.error else None}
            except Exception as exc:
                return {'status': 'raised:' + type(exc).__name__, 'newly_executed': False, 'error': normalise_reason(exc)}
        return self.witness.around(run)

    def revoke(self):
        self.dest.set_grant_status(self.claim.grant_id, status='revoked')

    def snapshot(self, name):
        snap = self.root / name
        sqlite_backup(self.dest.path, snap)
        return snap

    def restore_full(self, snap):
        sqlite_backup(snap, self.dest.path)
        self.reopen()

    def restore_tables(self, snap, tables):
        restore_tables(snap, self.dest.path, tables)
        self.reopen()

    def state(self):
        rows = sqlite_rows(self.dest.path)
        with sqlite3.connect(self.dest.path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            grant = db.execute('SELECT status FROM authority_grants_v1 WHERE grant_id=?', (self.claim.grant_id,)).fetchone()
        return {'effects': len(rows['effects']), 'claim': self.dest.claim_state(self.claim.claim_id), 'budget': self.dest.budget_state('budget-1'),
                'grant_status': grant[0] if grant else None, 'attempts': len(rows['attempts']),
                'receipts': len(rows['authority_effect_receipts_v1']), 'failure_records': len(rows['failure_records_v1'])}


# ----------------------------------------------------------------------------------------------
# D06: ingress pressure worlds and request generators (all report-only measurement; hard gates are
# zero unauthorized effects and zero excess duplicate effects, owner decision D5)
# ----------------------------------------------------------------------------------------------
import dataclasses  # noqa: E402
import subprocess  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402

_OBSERVER_CODE = r'''
import json, sqlite3, sys
db = sqlite3.connect("file:" + sys.argv[1] + "?mode=ro", uri=True)
def q(sql):
    try:
        return [list(r) for r in db.execute(sql).fetchall()]
    except sqlite3.OperationalError:
        return None
print(json.dumps({"effects": q("SELECT effect_id, grant_id, target, amount, unit, state FROM effects ORDER BY rowid"),
                  "attempts": q("SELECT COUNT(*) FROM attempts"), "admission_rejections": q("SELECT COUNT(*) FROM admission_rejections_v1"),
                  "failure_records": q("SELECT failure_class, reason_code, COUNT(*) FROM failure_records_v1 GROUP BY 1, 2 ORDER BY 1, 2")}))
'''


def observe_destination(path):
    """Independent observation: a separate Python process opening the destination read-only (it cannot write)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return json.loads(subprocess.check_output([sys.executable, '-I', '-c', _OBSERVER_CODE, str(Path(path).resolve())], env=env, text=True, timeout=60))


def capture(fn):
    """Observed outcome of one request: what it returned or the exact exception class and (normalised) message."""
    try:
        return {'returned': fn()}
    except Exception as exc:
        return {'raised': type(exc).__name__, 'message': normalise_reason(exc)}


def run_pool(tasks, workers, meter):
    """Run (klass, fn) tasks, ``workers`` at a time, in submission order; returns [(klass, outcome)] in submission order."""
    def run(task):
        klass, fn = task
        return klass, meter.timed(klass, capture, fn)
    if workers <= 1:
        return [run(t) for t in tasks]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run, tasks))


def malformed_envelope_cases(env):
    """Bounded malformed execution envelopes: (class, envelope, expected typed refusal message)."""
    op = env.operation
    exact = 'exact execution envelope and operation required'
    deep = {}
    cur = deep
    for _ in range(40):
        cur['n'] = {}
        cur = cur['n']
    rep = lambda **kw: dataclasses.replace(env, operation=dataclasses.replace(op, **kw))
    return [
        ('not_an_envelope', {'a': 1}, exact),
        ('none_envelope', None, exact),
        ('operation_wrong_type', dataclasses.replace(env, operation=object()), exact),
        ('string_over_1MiB', rep(payload={'x': 'y' * (1048576 + 1)}), 'execution string exceeds byte budget'),
        ('nesting_over_32', rep(payload=deep), 'execution input exceeds structural budget'),
        ('object_over_10000_keys', rep(payload={str(i): i for i in range(10001)}), 'execution object exceeds budget'),
        ('array_over_10000_items', rep(payload={'a': list(range(10001))}), 'execution array exceeds budget'),
        ('non_finite_amount', rep(amount=float('nan')), 'execution number must be finite'),
        ('non_plain_value', rep(payload={'a': {1, 2}}), 'execution input requires plain builtin values'),
        ('non_string_key', rep(payload={1: 2}), 'execution object keys must be exact strings'),
        ('integer_over_256_bits', rep(payload={'a': 1 << 300}), 'execution integer exceeds budget'),
    ]


# unauthenticated Control Plane proposals: the claimed identity/binding cannot be authenticated by the resolver
UNAUTH_PROPOSALS = [
    ('actor_spoof', lambda i: {'actor': f'intruder-{i}'}, 'proposal_identity_binding_mismatch'),
    ('principal_swap', lambda i: {'principal': f'other-principal-{i}'}, 'proposal_identity_binding_mismatch'),
    ('unknown_action', lambda i: {'action_id': f'unknown.action.{i}'}, 'action_class_unknown'),
    ('authority_context_missing', lambda i: {'authority_context_ref': f'nope-{i}'}, 'authority_context_missing'),
    ('manifest_digest_forged', lambda i: {'manifest_digest': 'sha256:' + format(i, '064x')}, 'manifest_digest_mismatch'),
    ('adapter_mismatch', lambda i: {'adapter_id': f'evil-adapter-{i}'}, 'adapter_mismatch'),
    ('target_out_of_scope', lambda i: {'target': f'urn:evil:{i}'}, 'target_out_of_scope'),
]


def malformed_proposal_cases():
    """Malformed Control Plane proposals rejected at the model boundary (pydantic ValidationError)."""
    good = dict(manifest_id='m', manifest_version='1', manifest_digest='sha256:' + '0' * 64, actor='a', principal='p', action_id='x',
                adapter_id='ad', target='t', payload={}, payload_commitment='sha256:' + '0' * 64)
    drop = lambda k: {kk: v for kk, v in good.items() if kk != k}
    return [('missing_actor', drop('actor')), ('missing_payload', drop('payload')), ('payload_not_object', {**good, 'payload': [1, 2]}),
            ('negative_amount', {**good, 'amount': -1}), ('nan_amount', {**good, 'amount': float('nan')}), ('inf_amount', {**good, 'amount': float('inf')}),
            ('amount_wrong_type', {**good, 'amount': 'lots'}), ('negative_effects', {**good, 'effects': -3}),
            ('requested_permissions_not_list', {**good, 'requested_permissions': 'admin'}), ('actor_wrong_type', {**good, 'actor': 12345})]


class ExchangeWorld:
    """Frozen exchange ingress (GAX assessment + run_exchange) in front of the F5b chain, one valid message prepared."""

    def __init__(self, root, monkeypatch):
        ref = reference()
        (self.gax, self.p, self.r, self.f, self.d, self.dest, self.bundle, self.message, self.registry, self.kwargs) = ref.chain.exchange_setup(Path(root), monkeypatch)
        self.root = Path(root)
        self.now = ref.chain.NOW
        self.grant_id = self.d.binding.grant_id

    def _base(self, **kw):
        return self.gax.make_message(self.bundle, created_at=self.now.isoformat(), expires_at=self.now.replace(year=self.now.year + 1).isoformat(), **kw)

    def _rehash(self, m):
        m['content_digest'] = self.gax.digest(m['content'])
        m['message_digest'] = self.gax.digest({k: v for k, v in m.items() if k != 'message_digest'})
        return m

    def deliver(self, message):
        out = self.gax.run_exchange(message, self.bundle, self.registry, self.dest, **self.kwargs)
        return {'handling': out['assessment']['permitted_handling'], 'errors': list(out['assessment']['errors']),
                'attempted': bool(out['execution'].get('attempted')), 'newly_executed': bool(out['execution'].get('newly_executed')),
                'attempt_status': out['execution'].get('attempt_status') or out['execution'].get('reason')}, out

    def typed_attack_messages(self):
        """(class, builder(i) -> message, expected typed error code)."""
        b, rh = self._base, self._rehash

        def tamper(i):
            m = b(message_id=f'att-tamper-{i}')
            m['content']['summary'] = 'tampered'
            return m

        def missing(i):
            m = b(message_id=f'att-missing-{i}')
            del m['sender']
            return m

        def downgrade(i):
            m = b(message_id=f'att-profile-{i}')
            m['profile'] = 'urn:attacker:profile'
            return rh(m)

        def purpose(i):
            m = b(message_id=f'att-purpose-{i}')
            m['purpose'] = 'transfer_all_funds'
            return rh(m)

        def binding(i):
            m = b(message_id=f'att-binding-{i}')
            m['requested_action']['amount'] = 999999.0 + i
            return rh(m)

        unsafe_ids = ['../escape-{i}', 'a/b-{i}', '.hidden-{i}', 'x' * 200, 'a..b-{i}']
        return [
            ('untrusted_sender', lambda i: b(message_id=f'att-sender-{i}', sender=f'mallory-{i}'), 'GAX-IDENTITY-SENDER-UNTRUSTED'),
            ('wrong_recipient', lambda i: b(message_id=f'att-rcpt-{i}', recipient=f'other-{i}'), 'GAX-IDENTITY-WRONG-RECIPIENT'),
            ('digest_tamper', tamper, 'GAX-INTEGRITY-DIGEST'),
            ('missing_required_field', missing, 'GAX-SCHEMA-MISSING-REQUIRED'),
            ('unsafe_message_id', lambda i: b(message_id=unsafe_ids[i % len(unsafe_ids)].format(i=i)), 'GAX-SCHEMA-MESSAGE-ID-UNSAFE'),
            ('expired', lambda i: self.gax.make_message(self.bundle, message_id=f'att-exp-{i}', created_at='2020-01-01T00:00:00+00:00', expires_at='2020-01-02T00:00:00+00:00'), 'GAX-FRESHNESS-EXPIRED'),
            ('profile_downgrade_rehashed', downgrade, 'GAX-PROFILE-UNSUPPORTED-OR-DOWNGRADE'),
            ('unsupported_purpose_rehashed', purpose, 'GAX-PURPOSE-UNSUPPORTED'),
            ('operation_binding_mismatch_rehashed', binding, 'GAX-REFERENCE-OPERATION-BINDING-MISMATCH'),
        ]

    def type_confusion_messages(self):
        """Malformed ingress that is NOT a well-formed-but-wrong message: wrong JSON types (class, builder(i))."""
        b, rh = self._base, self._rehash

        def mod(i, **changes):
            m = b(message_id=f'att-type-{i}')
            m.update(changes)
            return rh(m)
        return [
            ('message_id_is_list', lambda i: {**b(message_id=f'att-id-{i}'), 'message_id': ['a']}),
            ('message_id_is_object', lambda i: {**b(message_id=f'att-id-{i}'), 'message_id': {'a': i}}),
            ('sender_is_list', lambda i: mod(i, sender=['a'])),
            ('authority_refs_is_string', lambda i: mod(i, authority_refs='nope')),
            ('expires_at_not_a_time', lambda i: mod(i, expires_at='not-a-time')),
            ('content_has_nan', lambda i: {**b(message_id=f'att-nan-{i}'), 'content': {'v': float('nan')}}),
            ('message_is_string', lambda i: 'garbage'),
            ('message_is_none', lambda i: None),
        ]


def chain_evidence(w, result):
    """Replay -> Evidence Pack -> ODES evaluation of the flow a ChainWorld just executed (evidence obligations)."""
    from engine.producer_contract import export_execution_artifacts
    ref = reference()
    export = export_execution_artifacts(w.env, result, w.dest, repository_revision=ref.chain.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
    journal = w.f.records.load().model_dump(mode='json')
    stages = evaluate_producer_exports(w.f.manifest, journal, w.p.model_dump(mode='json'), export)
    return [(s['stage'], s['verdict'], s['why']) for s in stages]


_UNSET = object()


def raw_execute(w, envelope=_UNSET):
    """Execute and return the raw result object (not the normalised dict)."""
    return w.executor.execute(envelope=w.env if envelope is _UNSET else envelope, proposal=w.p, decision=w.d, now=w.now)


def kinds(outcomes):
    """Histogram of outcome kinds for report-only recording."""
    hist = {}
    for _klass, o in outcomes:
        key = o.get('raised') and (o['raised'] + ': ' + o['message']) or 'returned'
        hist[key] = hist.get(key, 0) + 1
    return dict(sorted(hist.items()))
