#!/usr/bin/env python3
"""BOUNDED Registry integration probe (Qualification-owned; NOT a Wiki case; separately labelled REGISTRY-PROBE-S3).

SPDX-License-Identifier: Apache-2.0
PREPARED, NOT YET EXECUTED against the final tuple. Non-authorizing. Separate from, and NOT, Registry enforcement qualification. Makes no claims (claims_made = []).

    python tools/registry_integration_probe.py --tuple TUPLE.json --components DIR --out NEWDIR \
        [--registry-builder-dir R_A40FE755] [--site DIR_WITH_PYNACL] [--with-pack-odes] [--dry-check]

Chain probed (one synthetic scenario, one proposal, synthetic Ed25519 keys, patched fixed clock):
  Registry-governed Control Plane decision (existing public classes + the CP repo's own test builders)  -> execute
  -> Runtime export (best effort, recorded) -> Replay CUR import under the Architect-approved E1 registry-governed profile
  -> (optional) Pack/ODES -> assert actual source identity / authority provenance.
Never synthesizes an authenticated source label, never relabels to 7a4bcd40/c5e97e87, never strips effective_configuration to get an
import through. Outcome per stage is PASS | FAIL | BLOCKED (exact reason) | NOT_RUN; the overall outcome is BLOCKED while any required
stage is BLOCKED and nothing FAILed. The Replay stage is BLOCKED unless the installed Replay HEAD == the tuple Replay SHA and it exposes the E1 selector (below).

Registry bytes under test: the CP test builders accept only exact Registry pins (ACCEPTED_PINS in the CP repo). If the tuple Registry
is not one of them (6b96a9a6 is not; it is code-equal to a40fe755 except README), a second pristine checkout at an ACCEPTED pin must be
given as --registry-builder-dir; the probe then proves code-equality (git diff excluding docs/ and README.md) and RECORDS that the
bytes exercised are the accepted pin's, not the tuple SHA's. Without it the probe is BLOCKED before running anything.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA_RE = re.compile(r'[0-9a-f]{40}')
NEEDED = ('control_plane', 'runtime', 'replay', 'registry')
OPTIONAL_TUPLE = ('evidence_pack', 'odes')

# ----------------------------------------------------------------------------------------------------------------------------------
# E1 selector, copied ONCE from Replay E1 PR #81 (head a88a383ee3288b2776d50f4f9ea1dc92ec791df3, UNMERGED when this was written):
#   import_bounded_workflow(..., control_plane_revision=<CP b19c47dd>, control_plane_profile="registry-governed-effective-configuration/0.1")
#   resulting import-report profile id: control-plane-current-stack-registry-governed-effective-configuration-0.1@b19c47dd
# The Replay stage runs ONLY if the installed Replay checkout's HEAD == the tuple's Replay SHA AND its modules expose exactly this selector
# (kwarg in the signature, effective_configuration.REGISTRY_GOVERNED_PROFILE == value, importers.BOUNDED_CUR_REGISTRY_GOVERNED_PROFILE == profile_id).
# On any Replay without E1 the stage is BLOCKED (never relabelled, never stripped). The SHA of the E1 PR head is NOT a gate (the tuple carries the merged SHA).
E1_SELECTOR = {"kwarg": "control_plane_profile", "value": "registry-governed-effective-configuration/0.1",
               "profile_id": "control-plane-current-stack-registry-governed-effective-configuration-0.1@b19c47dd",
               "source": "cogno-us/cognous-replay-bundle PR #81 head a88a383ee3288b2776d50f4f9ea1dc92ec791df3 (unmerged at authoring)"}
PROBE_SCOPE = 'Registry-governed CP decision -> Replay import (E1 profile) ONLY'
GATES = {  # where each negative is refused (static attribution from S0/E1 reports; the exact refusal text is recorded in each check's `observed`)
    'N_forged_signature': 'Registry verification in registry_successor via CP derive_policy (registry_governed_policy); construction refuses before any state write',
    'N_revoked_selection': 'Registry selection check via CP derive_policy (construction)',
    'N_withdrawn_selection': 'Registry selection check via CP derive_policy (construction)',
    'N_stale_expired_selection': 'Registry validity window check via CP derive_policy (construction)',
    'N_substituted_configuration_age61': 'CP effective_configuration_binding.classify via GovernedLifecycle._resolve at execute (EffectTimeRefusal authorization_binding_changed)',
    'N_substituted_configuration_family_dropped': 'CP effective_configuration_binding.classify via GovernedLifecycle._resolve at execute (EffectTimeRefusal authorization_binding_changed)',
    'N_tampered_member_vs_record_digest': 'CP effective_configuration_binding.record_defect (digest recomputation)',
    'N_effective_configuration_under_plain_profile': 'Replay import_bounded_workflow / refusal_evidence closed runtime_authority member set (plain CUR profile admits no effective_configuration)',
    'N_missing_effective_configuration_under_registry_profile': 'Replay effective_configuration check: member required on every authorized decision (E1 profile)',
    'N_tampered_effective_configuration_under_registry_profile': 'Replay effective_configuration check: digest recomputation / exact shape (E1 profile)',
}
NOT_CLAIMED = ['Registry enforcement qualification', 'signature/trust verification', 'live configuration in force', 'Registry revision provenance',
               'continuous ingress-to-Verifier chain']
#: outcome vocabulary (never "qualified"): PASS_IMPORT = the E1-profile Replay import of the CP-only governed record was accepted AND every other required
#: check held; REFUSED_AS_EXPECTED = a negative was refused with the recorded text at the recorded gate; BLOCKED(reason) = a stage could not run honestly.
# ----------------------------------------------------------------------------------------------------------------------------------


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(path, *args, check=True):
    r = subprocess.run(['git', '-C', str(path), *args], capture_output=True, text=True, timeout=120)
    if check and r.returncode:
        raise RuntimeError(f'git {args}: {r.stderr.strip()}')
    return r.stdout.strip(), r.returncode


class Blocked(Exception):
    pass


# ============================================================ parent (preflight, orchestration, evidence)
def accepted_pins(cp):
    src = (Path(cp) / 'tests' / 'test_f5_class_unreadable_governance.py').read_text()
    m = re.search(r'ACCEPTED_PINS\s*=\s*\(([^)]*)\)', src)
    names = [n.strip() for n in m.group(1).split(',') if n.strip()]
    return {n: re.search(rf'^{n}\s*=\s*"([0-9a-f]{{40}})"', src, re.M).group(1) for n in names}


def preflight(a):
    from pristine_checkout import require_pristine
    t = json.loads(Path(a.tuple).read_text())
    for s in json.dumps(t).split('"'):
        if 'PLACEHOLDER' in s or 'TEMPLATE' in s:
            raise SystemExit(f'REFUSED: tuple contains a placeholder/template marker: {s[:60]!r}')
    for k in NEEDED:
        if not SHA_RE.fullmatch(str(t.get(k, ''))):
            raise SystemExit(f'REFUSED: tuple.{k} is not a 40-hex SHA')
    comp = Path(a.components)
    for k in NEEDED + tuple(x for x in OPTIONAL_TUPLE if a.with_pack_odes):
        require_pristine(comp / k, t[k], k)
    if a.out.exists():
        raise SystemExit('REFUSED: --out must be new')
    pins = accepted_pins(comp / 'control_plane')
    reg = t['registry']
    info = {'tuple_registry': reg, 'cp_accepted_registry_pins': pins}
    if reg in pins.values():
        info.update(builder_dir=str(comp / 'registry'), builder_head=reg, bytes_exercised='tuple registry SHA')
    elif a.registry_builder_dir:
        require_pristine(a.registry_builder_dir, git(a.registry_builder_dir, 'rev-parse', 'HEAD')[0], 'registry-builder')
        bh = git(a.registry_builder_dir, 'rev-parse', 'HEAD')[0]
        if bh not in pins.values():
            raise SystemExit(f'REFUSED: --registry-builder-dir HEAD {bh} is not a CP-accepted Registry pin')
        _, rc = git(comp / 'registry', 'diff', '--quiet', bh, reg, '--', '.', ':!docs', ':!README.md', check=False)
        if rc != 0:
            info['blocked'] = f'tuple Registry {reg} is NOT code-equal (outside docs/ and README.md) to the CP-accepted pin {bh}; CP builders cannot run against it'
        info.update(builder_dir=str(Path(a.registry_builder_dir).resolve()), builder_head=bh,
                    bytes_exercised=f'CP-accepted pin {bh} (code-equal to tuple Registry {reg} outside docs/ and README.md: {rc == 0}); NOT the tuple SHA bytes')
    else:
        info['blocked'] = (f'tuple Registry {reg} is not among the CP test-builder accepted pins {sorted(pins.values())}; the builders skip/fail on it. '
                           'Provide --registry-builder-dir at an accepted pin that is code-equal to the tuple Registry.')
    info['code_identity'] = code_identity(comp / 'registry', info.get('builder_head'), reg)
    return t, info


def code_identity(regdir, builder_head, tuple_reg):
    """git diff --stat between the Registry bytes exercised and the tuple Registry; INFERRED when either object is not in the checkout."""
    if not builder_head or builder_head == tuple_reg:
        return {'status': 'IDENTICAL_SHA' if builder_head == tuple_reg else 'NOT_APPLICABLE', 'exercised': builder_head, 'tuple': tuple_reg}
    for sha in (builder_head, tuple_reg):
        if git(regdir, 'cat-file', '-e', f'{sha}^{{commit}}', check=False)[1] != 0:
            return {'status': 'INFERRED', 'exercised': builder_head, 'tuple': tuple_reg,
                    'statement': f'object {sha} not present in {regdir}; code-identity NOT verified here (INFERRED from the S0 report only)'}
    stat, _ = git(regdir, 'diff', '--stat', builder_head, tuple_reg)
    names, _ = git(regdir, 'diff', '--name-only', builder_head, tuple_reg)
    other = [n for n in names.splitlines() if not (n.startswith('docs/') or n == 'README.md')]
    return {'status': 'VERIFIED' if not other else 'DIFFERS', 'exercised': builder_head, 'tuple': tuple_reg, 'diff_stat_tail': stat.splitlines()[-1:] ,
            'files_outside_docs_and_README': other,
            'statement': ('code-identical apart from README/docs (git diff --name-only outside docs/ and README.md is empty)' if not other
                          else f'NOT code-identical: {other[:10]}')}


def child_cfg(a, t, info, work):
    comp = Path(a.components).resolve()
    paths = [str(comp / 'control_plane'), str(comp / 'control_plane' / 'src'), str(comp / 'runtime'), str(comp / 'replay' / 'src')]
    if a.site:
        paths.insert(0, str(Path(a.site).resolve()))
    return {'paths': paths, 'tuple': t, 'info': info, 'work': str(work), 'components': str(comp), 'dry': a.dry_check,
            'with_pack_odes': a.with_pack_odes, 'e1': E1_SELECTOR, 'site': a.site}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tuple', type=Path)
    ap.add_argument('--components', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--registry-builder-dir', type=Path, default=None)
    ap.add_argument('--site', type=Path, default=None, help='directory providing PyNaCl when it is not installed (recorded)')
    ap.add_argument('--with-pack-odes', action='store_true')
    ap.add_argument('--dry-check', action='store_true', help='preflight + import/attribute checks only; no scenario is executed; writes nothing')
    ap.add_argument('--child', type=Path, default=None, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.child:
        return child(json.loads(a.child.read_text()))
    if not (a.tuple and a.components and a.out):
        ap.error('--tuple, --components and --out are required')
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        t, info = preflight(a)
    except ValueError as e:
        raise SystemExit(f'REFUSED: {e}')
    work = (Path(os.devnull) if a.dry_check else a.out / 'work')
    if not a.dry_check:
        (a.out / 'raw').mkdir(parents=True)
        work.mkdir()
    cfg = child_cfg(a, t, info, work)
    cfgf = (a.out / 'raw' / 'child-config.json') if not a.dry_check else Path(os.environ.get('TMPDIR', '/tmp')) / f'rip-{os.getpid()}.json'
    cfgf.write_text(json.dumps(cfg, indent=1, default=str))
    env = {k: v for k, v in os.environ.items() if not k.startswith(('PYTHON', 'OCS_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', OCS_REQUIRE_REGISTRY_PIN='1')
    if 'builder_dir' in info and 'blocked' not in info:
        env['OCS_REGISTRY_PIN_DIR'] = info['builder_dir']
    # -B is required: -I ignores PYTHONDONTWRITEBYTECODE, and __pycache__ in a checkout would make it non-pristine.
    # -I: no script dir, no PYTHONPATH, no user site -> the qualification repository's own `tests` package cannot shadow the CP's.
    cmd = [sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--child', str(cfgf)]
    log = (a.out / 'raw' / 'log.txt') if not a.dry_check else None
    if log:
        with log.open('w') as s:
            rc = subprocess.run(cmd, cwd=a.out / 'work', env=env, stdout=s, stderr=subprocess.STDOUT, timeout=1800).returncode
    else:
        r = subprocess.run(cmd, cwd='/', env=env, capture_output=True, text=True, timeout=600)
        rc = r.returncode
        print(r.stdout[-3000:], r.stderr[-1500:], file=sys.stderr if rc else sys.stdout)
        cfgf.unlink(missing_ok=True)
        return rc
    # evidence: tool versions + pristine-after + hashes of EVERY artifact
    from pristine_checkout import require_pristine
    problems = []
    for k in NEEDED:
        try:
            require_pristine(Path(a.components) / k, t[k], k)
        except ValueError as e:
            problems.append(str(e))
    envrec = {'python': sys.version, 'platform': platform.platform(), 'tool': 'registry_integration_probe.py', 'tool_sha256': sha256(__file__),
              'git': subprocess.check_output(['git', '--version'], text=True).strip(), 'child_returncode': rc, 'checkouts_pristine_after': not problems,
              'problems': problems, 'qualification_head': git(ROOT, 'rev-parse', 'HEAD')[0], 'utc': datetime.now(timezone.utc).isoformat(),
              'registry': info, 'e1_selector': E1_SELECTOR}
    (a.out / 'raw' / 'env.json').write_text(json.dumps(envrec, indent=2, sort_keys=True, default=str) + '\n')
    sums = '\n'.join(f'{sha256(p)}  ./{p.relative_to(a.out).as_posix()}' for p in sorted(a.out.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS')
    (a.out / 'SHA256SUMS').write_text(sums + '\n')
    ev = json.loads((a.out / 'evidence.json').read_text()) if (a.out / 'evidence.json').exists() else {'overall': 'FAIL', 'reason': 'child wrote no evidence.json'}
    print(json.dumps({'overall': ev.get('overall'), 'out': str(a.out)}))
    return {'PASS': 0, 'BLOCKED': 3}.get(ev.get('overall'), 1)


# ============================================================ child (runs under python -I; imports CP builders; executes the scenario)
def child(cfg):
    sys.path[:0] = cfg['paths']
    out = {'label': 'REGISTRY-PROBE-S3 (bounded; NOT a Wiki case; non-authorizing; single scenario; synthetic keys; patched clock)', 'stages': {}, 'checks': {}}
    work = Path(cfg['work'])
    dry = cfg['dry']

    def put(group, key, status, **kw):
        out[group][key] = {'status': status, **kw}
        print(f'[{status}] {group}.{key} {kw.get("reason") or kw.get("observed") or ""}', flush=True)

    def finish():
        req = [v['status'] for v in list(out['stages'].values()) + list(out['checks'].values()) if not v.get('optional')]
        out['overall'] = 'FAIL' if 'FAIL' in req else 'BLOCKED' if ('BLOCKED' in req or 'NOT_RUN' in req) else 'PASS'
        blocked = sorted(k for k, v in list(out['stages'].items()) + list(out['checks'].items()) if v['status'] == 'BLOCKED' and not v.get('optional'))
        out['outcome'] = {'PASS': 'PASS_IMPORT', 'FAIL': 'FAIL'}.get(out['overall']) or 'BLOCKED(' + ','.join(blocked or ['not_run']) + ')'
        # per-item outcome vocabulary: negatives -> REFUSED_AS_EXPECTED, the Replay positive -> PASS_IMPORT, everything else keeps PASS/FAIL/BLOCKED/NOT_RUN
        for k, v in out['checks'].items():
            if k.startswith('N_') and v['status'] == 'PASS':
                v['outcome'] = 'REFUSED_AS_EXPECTED'
            if k in GATES:
                v['gate'] = GATES[k]
        rp = out['stages'].get('replay_e1_import_governed_record')
        if rp and rp['status'] == 'PASS':
            rp['outcome'] = 'PASS_IMPORT'
        info_ = cfg['info']
        ci = info_.get('code_identity', {})
        out['probe_scope'] = PROBE_SCOPE
        out['registry_bytes_exercised'] = {
            'checkout_sha_actually_imported': info_.get('builder_head'),
            'tuple_registry_sha': cfg['tuple']['registry'],
            'statement': ('bytes exercised are the CP-builder pin %s, not the tuple Registry %s; ' % (info_.get('builder_head'), cfg['tuple']['registry'])
                          + (ci.get('statement') or 'code-identity not evaluated')) if info_.get('builder_head') != cfg['tuple']['registry'] else 'bytes exercised are the tuple Registry SHA',
            'code_identity': ci, 'code_identity_epistemic_status': ci.get('status', 'INFERRED')}
        if dry:
            out['outcome'] = 'DRY_CHECK_OK (nothing executed; NOT an import result)' if out['overall'] == 'PASS' else out['outcome']
        out['claims_made'] = []
        out['not_claimed'] = list(NOT_CLAIMED)
        out['verifier_run'] = False
        out['cannot_claim'] = NOT_CLAIMED + ['that Replay authenticates the Registry source (it retains but does not verify effective_configuration)',
                                             'production readiness', 'any statement beyond one scenario and one proposal (synthetic keys, patched clock, host-supplied selection material)']
        if not dry:
            (work.parent / 'evidence.json').write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + '\n')
        else:
            print(json.dumps({'dry_check': out['overall'], 'outcome': out['outcome'], 'stages': {k: v['status'] for k, v in out['stages'].items()}}, indent=1))
        return {'PASS': 0, 'BLOCKED': 3}.get(out['overall'], 1)

    info = cfg['info']
    if 'blocked' in info:
        put('stages', 'registry_builder_pin', 'BLOCKED', reason=info['blocked'])
        return finish()
    put('stages', 'registry_builder_pin', 'PASS', observed=info['bytes_exercised'])
    try:
        import nacl.bindings  # noqa: F401
    except ImportError:
        put('stages', 'pynacl', 'BLOCKED', reason='PyNaCl not importable (pass --site DIR or install Registry requirements-ed25519.lock.txt)')
        return finish()
    import pytest
    try:
        import tests.final3_support as F
        from tests.final3_support import (base, bind_approval, NOW, R_, ANC, AGE, TOL, mat, revoked, withdrawn, Source, FreshnessProfile, v8id, t8)
        from tests import d06_support as D
        from agent_control_plane import effective_configuration_binding as ecb
    except BaseException as e:  # pytest.skip.Exception / Failed raised at import by the builders' pin gate are BaseException
        put('stages', 'cp_builders_import', 'BLOCKED', reason=f'{type(e).__name__}: {str(e)[:300]}')
        return finish()
    put('stages', 'cp_builders_import', 'PASS')

    # ---- Replay import surface (static facts; no scenario)
    from agent_replay_bundle import importers as I
    cur = getattr(I, 'CONTROL_PLANE_CUR_REVISION', None)
    t = cfg['tuple']
    if cur is None:
        put('stages', 'replay_cur_generation', 'BLOCKED', reason='Replay checkout has no CONTROL_PLANE_CUR_REVISION: no honest label exists for the current Control Plane')
    elif cur != t['control_plane']:
        put('stages', 'replay_cur_generation', 'FAIL', observed=cur, expected=t['control_plane'], reason='Replay CUR label != tuple Control Plane SHA')
    else:
        put('stages', 'replay_cur_generation', 'PASS', observed=cur)
    e1 = cfg['e1']
    e1_kw = None
    e1_profile_id = e1['profile_id']
    import inspect
    import subprocess as _sp
    try:
        from agent_replay_bundle import effective_configuration as _EC
    except ImportError:  # a Replay without E1
        _EC = None
    replay_dir = Path(cfg['components']) / 'replay'
    head = _sp.run(['git', '-C', str(replay_dir), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    why = []
    if head != t['replay']:
        why.append(f"Replay installed HEAD {head or '?'} != tuple Replay SHA {t['replay']}")
    if not str(Path(I.__file__).resolve()).startswith(str(replay_dir.resolve())):
        why.append(f'agent_replay_bundle imported from {I.__file__}, not from the tuple Replay checkout')
    if e1['kwarg'] not in inspect.signature(I.import_bounded_workflow).parameters:
        why.append(f"import_bounded_workflow has no kwarg {e1['kwarg']!r}")
    if getattr(_EC, 'REGISTRY_GOVERNED_PROFILE', None) != e1['value']:  # _EC None -> mismatch
        why.append(f"effective_configuration.REGISTRY_GOVERNED_PROFILE != {e1['value']!r}")
    if getattr(I, 'BOUNDED_CUR_REGISTRY_GOVERNED_PROFILE', None) != e1['profile_id']:
        why.append(f"importers.BOUNDED_CUR_REGISTRY_GOVERNED_PROFILE != {e1['profile_id']!r}")
    if why:
        put('stages', 'e1_selector', 'BLOCKED', reason='E1 selector not exposed by the installed Replay: ' + '; '.join(why) +
            '. The probe will NOT synthesize an authenticated source label or strip effective_configuration.')
    else:
        e1_kw = {e1['kwarg']: e1['value']}
        put('stages', 'e1_selector', 'PASS', observed={'replay_head': head, 'selector': e1_kw, 'profile_id': e1['profile_id']})
    if dry:
        put('stages', 'dry_check_scope', 'PASS', observed='imports and attribute checks only; no decision was made, nothing executed')
        return finish()

    mp = pytest.MonkeyPatch()
    D.patch_clock(mp)  # the CP builders' fixed synthetic clock (recorded caveat)
    BASE = {'anc': 'anchor', 'age': 60, 'tol': 2}

    def newdir(n):
        d = work / n
        d.mkdir(parents=True)
        return d

    def stage(conf, name):
        tp = newdir(name)
        p, res, cfgo = base.prepared(tp / 'w', t1=R_, freshness=FreshnessProfile(anchor_deadline_to_inputs=False))
        store = tp / 'store'
        store.mkdir()
        flow = F.make(store, res, cfgo, conf)
        bind_approval(res, flow.runtime_authority_profile)
        return p, res, cfgo, store, flow

    # ---- S1 Registry-governed decision + execute
    record = None
    try:
        p, res, cfgo, store, flow = stage(BASE, 'pos')
        d = flow.decide(p, now=NOW)
        ra = d.binding.runtime_authority
        ec = ra.get('effective_configuration')
        ok = d.result == 'authorized' and ec is not None and flow.configuration_binding_status(d) == 'bound'
        put('stages', 'cp_registry_governed_decision', 'PASS' if ok else 'FAIL', observed={'result': d.result, 'has_effective_configuration': ec is not None,
            'binding_status': flow.configuration_binding_status(d)})
        att, obs = flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=NOW)
        put('stages', 'cp_execute', 'PASS' if (att.status, obs.state) == ('acknowledged', 'applied') else 'FAIL', observed=[att.status, obs.state])
        record = json.loads((store / 'run.json').read_text())
        (work.parent / 'raw' / 'cp-record.json').write_text(json.dumps(record, indent=1, sort_keys=True))
    except Exception as e:
        put('stages', 'cp_registry_governed_decision', 'FAIL', reason=f'{type(e).__name__}: {str(e)[:300]}')
        return finish()

    # ---- S2 provenance assertions at the CP side (independent recomputation; no probe-supplied label)
    try:
        members = ec['members']
        rows = {r['slot']: r for r in members['families']}
        want = {'anchor_deadline': (ANC, {t8.FIELDS[ANC]: 'anchor'}), 'observation_max_age': (AGE, {t8.FIELDS[AGE]: 60}), 'observation_clock_tolerance': (TOL, {t8.FIELDS[TOL]: 2})}
        bad = []
        if ecb.digest_of(ec['version'], members) != ec['digest']:
            bad.append('record digest != digest_of(version, members)')
        if ec['version'] != ecb.VERSION:
            bad.append('version')
        if set(rows) != set(want):
            bad.append(f'slots {sorted(rows)}')
        for slot, (fam, payload) in want.items():
            r = rows.get(slot, {})
            if r.get('family_id') != fam or r.get('contract_version') != 'r08-v8' or r.get('effective_policy_digest') != v8id.effective_policy_digest(fam, payload, 'r08-v8'):
                bad.append(f'row {slot}: {r}')
        blob = json.dumps(record, sort_keys=True)
        for lab in ('7a4bcd40', 'c5e97e87'):
            if lab in blob:
                bad.append(f'historical label {lab} present in the CP record')
        put('checks', 'cp_provenance_recomputed', 'PASS' if not bad else 'FAIL', observed={'families': {k: v['effective_policy_digest'][:23] for k, v in rows.items()}, 'record_digest': ec['digest'][:23]}, reason='; '.join(bad) or None)
        out['source_identity'] = {'registry_bytes_exercised': info['bytes_exercised'], 'registry_tuple_sha': t['registry'], 'cp_sha': t['control_plane'],
                                  'signing_key_sha256': hashlib.sha256(bytes(base.PK) if isinstance(base.PK, (bytes, bytearray)) else str(base.PK).encode()).hexdigest(),
                                  'authenticated_source_label_supplied_by_probe': False}
    except Exception as e:
        put('checks', 'cp_provenance_recomputed', 'FAIL', reason=f'{type(e).__name__}: {str(e)[:300]}')

    # ---- negatives (CP side; executable now)
    def construct(label, **over):
        tp = newdir('n-' + label)
        pp, res_, cfg_ = base.prepared(tp / 'w', t1=R_, freshness=FreshnessProfile(anchor_deadline_to_inputs=False))
        st = tp / 'store'
        st.mkdir()
        try:
            F.build(st, res_, cfg_, F.fams(age=Source(over['age'])))
            return 'CONSTRUCTED'
        except BaseException as e:
            return f'{type(e).__name__}: {e}'
    for label, expect, kw in (('forged_signature', 'signature_invalid', {'age': mat(AGE, 60, sk=base.OTHER_SK)}),
                              ('revoked_selection', 'selection_revoked', {'age': revoked(AGE, 60)}),
                              ('withdrawn_selection', 'selection_withdrawn', {'age': withdrawn(AGE, 60)}),
                              ('stale_expired_selection', 'selection_expired', {'age': mat(AGE, 60, stmt_over={'effective': {'valid_from': '2026-01-01T00:00:00Z', 'valid_until': '2026-01-02T00:00:00Z'}})})):
        obs_ = construct(label, **kw)
        put('checks', 'N_' + label, 'PASS' if (obs_ != 'CONSTRUCTED' and expect in obs_) else 'FAIL', expected=expect, observed=obs_[:240])
    for label, conf in (('substituted_configuration_age61', dict(BASE, age=61)), ('substituted_configuration_family_dropped', {'anc': 'anchor', 'age': 60})):
        try:
            p2, res2, cfg2, store2, flow2 = stage(BASE, 'sub-' + label)
            d2 = flow2.decide(p2, now=NOW)
            wf = F.make(store2, res2, cfg2, conf)
            bind_approval(res2, wf.runtime_authority_profile)
            st = wf.configuration_binding_status(wf.records.decision(d2.decision_id))
            try:
                wf.execute(p2, wf.records.decision(d2.decision_id), adapter_id=p2.adapter_id, now=NOW)
                ex = 'EXECUTED'
            except Exception as e:
                ex = f'{type(e).__name__}: {e}'
            reasons = [r.reasons for r in wf.records.load().refusals][-1:] or None
            eff = wf.destination.snapshot()['effects']
            good = st == 'mismatch' and ex != 'EXECUTED' and not eff and reasons and 'authorization_binding_changed' in json.dumps(reasons)
            put('checks', 'N_' + label, 'PASS' if good else 'FAIL', expected='mismatch / refused / authorization_binding_changed / no effect',
                observed={'status': st, 'execute': ex[:160], 'reasons': reasons, 'effects': eff})
        except Exception as e:
            put('checks', 'N_' + label, 'FAIL', reason=f'{type(e).__name__}: {str(e)[:200]}')
    tam = json.loads(json.dumps(ec))
    tam['members']['families'][0]['effective_policy_digest'] = 'sha256:' + '1' * 64
    put('checks', 'N_tampered_member_vs_record_digest', 'PASS' if ecb.record_defect(tam) else 'FAIL', observed=ecb.record_defect(tam))

    # ---- Runtime export of a GOVERNED decision: investigated (scratch, 2026-10-31), BLOCKED on existing public interfaces; the CP-only record is imported.
    # Finding 1 (RESOLVED): the S0 'denied for tenant_id proposal mismatch' is the Wiki-chain fixture building ExecutionOperation without tenant_id; passing
    #   tenant_id=proposal.tenant_id (field exists on ExecutionOperation) clears control_plane_adapter's tenant check.
    # Finding 2 (NOT resolvable without new production interfaces): PinnedControlPlaneExecutor.execute rebuilds the workflow with
    #   self.workflow.__class__(manifest=..., resolver=..., ...) and cannot reconstruct a GovernedPolicyWorkflow (required keyword-only 'families' and 'verifier') ->
    #   TypeError at control_plane_adapter.py:334; the governed fixture destination is also not an EffectiveGrantDestination (no expected_effective_grant_digest).
    # The probe re-verifies those two preconditions statically and reports BLOCKED; if either changed it says so instead of assuming.
    export = None
    try:
        import inspect as _i
        from engine import control_plane_adapter as _CPA
        from agent_control_plane.registry_governed_policy import GovernedPolicyWorkflow as _GPW
        rebuilt = 'self.workflow.__class__(' in _i.getsource(_CPA.PinnedControlPlaneExecutor.execute)
        need = sorted(n for n, q in _i.signature(_GPW.__init__).parameters.items() if q.kind is q.KEYWORD_ONLY and q.default is q.empty and n in ('families', 'verifier'))
        if rebuilt and need:
            put('stages', 'runtime_export', 'BLOCKED', optional=True, reason=(
                'Runtime export of a governed decision needs a new production interface: PinnedControlPlaneExecutor.execute rebuilds the workflow via '
                f'self.workflow.__class__(...) which cannot construct GovernedPolicyWorkflow (required keyword-only {need}); (the earlier tenant_id proposal mismatch is '
                'resolved by ExecutionOperation(tenant_id=proposal.tenant_id) but is not the remaining blocker). The Replay stage imports the CP-only governed record, '
                'the supported shape of E1 fixtures (no Runtime export captured there either).'))
        else:
            put('stages', 'runtime_export', 'BLOCKED', optional=True, reason='preconditions of the documented blocker changed (rebuilt=%s need=%s); Runtime export NOT wired - investigate, do not assume' % (rebuilt, need))
    except Exception as e:
        put('stages', 'runtime_export', 'BLOCKED', optional=True, reason=f'could not re-verify the documented Runtime blocker: {type(e).__name__}: {str(e)[:160]}')

    # ---- Replay: plain CUR profile must REFUSE effective_configuration (executable once Replay has CUR)
    prop = p.model_dump(mode='json')

    def replay(rec, **kw):
        try:
            b = I.import_bounded_workflow(rec, proposal=prop, control_plane_revision=cur, moltbot_export=export, **kw)
            return 'ACCEPTED', b
        except Exception as e:
            return f'{type(e).__name__}[{getattr(e, "code", None)}]: {str(e)[:200]}', None
    if cur is None or cur != t['control_plane']:
        put('checks', 'N_effective_configuration_under_plain_profile', 'BLOCKED', reason='no honest CUR label in Replay')
    else:
        res_, _ = replay(record)
        put('checks', 'N_effective_configuration_under_plain_profile', 'PASS' if res_ != 'ACCEPTED' else 'FAIL',
            expected='refused (plain CUR profile admits no effective_configuration)', observed=res_)

    # ---- Replay: E1 registry-governed profile
    if e1_kw is None or cur is None or cur != t['control_plane']:
        why = 'E1 selector unavailable or no honest CUR label (see stages.e1_selector / replay_cur_generation); positive import and the Replay-side negatives cannot be run honestly'
        for k in ('replay_e1_import_governed_record', 'N_missing_effective_configuration_under_registry_profile', 'N_tampered_effective_configuration_under_registry_profile'):
            put('stages' if k.startswith('replay') else 'checks', k, 'BLOCKED', reason=why)
    else:
        r_pos, bundle = replay(record, **e1_kw)
        blob = json.dumps(bundle.model_dump(mode='json'), sort_keys=True, default=str) if bundle is not None else ''
        prov_ok = bundle is not None and bundle.import_reports[0].adapter_profile == e1_profile_id and ec['digest'] in blob and all(r['effective_policy_digest'] in blob for r in rows.values()) \
            and cur in blob and '7a4bcd40' not in blob and 'c5e97e87' not in blob
        put('stages', 'replay_e1_import_governed_record', 'PASS' if (r_pos == 'ACCEPTED' and prov_ok) else 'FAIL',
            observed={'import': r_pos, 'retains_digest_and_family_rows_and_cur_label_no_historical_label': bool(prov_ok), 'complete': getattr(bundle, 'complete', None)})
        miss = json.loads(json.dumps(record))
        for dd in miss['decisions']:
            dd['binding']['runtime_authority'].pop('effective_configuration', None)
        r_miss, _ = replay(miss, **e1_kw)
        put('checks', 'N_missing_effective_configuration_under_registry_profile', 'PASS' if r_miss != 'ACCEPTED' else 'FAIL', expected='refused', observed=r_miss)
        bad = json.loads(json.dumps(record))
        for dd in bad['decisions']:
            dd['binding']['runtime_authority']['effective_configuration']['digest'] = 'sha256:' + '2' * 64
        r_bad, _ = replay(bad, **e1_kw)
        put('checks', 'N_tampered_effective_configuration_under_registry_profile', 'PASS' if r_bad != 'ACCEPTED' else 'FAIL', expected='refused (digest/shape)', observed=r_bad)

    # ---- optional Pack / ODES
    put('stages', 'pack_odes', 'NOT_RUN', optional=True, reason='optional; enable with --with-pack-odes only after the Replay E1 stage is PASS; call signatures to be filled from the merged S1 Pack/ODES PRs '
        '(ODES export_cognous_stack_package / Pack importer) - not guessed here')
    return finish()


if __name__ == '__main__':
    raise SystemExit(main())
