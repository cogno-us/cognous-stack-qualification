"""ASW core-12, family S (supply chain, wiki layer L16): S01 dependency commit drift from the component lock,
S02 artifact digest mismatch.

SPDX-License-Identifier: Apache-2.0

No network and no package manager is used. S01 drift is produced on private local copies of the pinned checkouts (the
pinned checkouts themselves are never touched and are re-verified pristine by the module fixture) and on the revision
constants the replay importers accept. S02 substitutes/tampers the artifacts the reference binds by digest or commitment
(governed-exchange message and retained bundle, Control Plane manifest digest, atomic execution claim, executor export,
evidence pack).

Executed against the frozen F5b-repaired seven-component bounded synthetic reference (see ``_asw_helpers``); every test
runs twice from fresh stores and the hard gate applies to every run. A genuine violation FAILS; nothing is loosened.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import _asw_helpers as A
import _d02_d05_d09_helpers as H
from _asw_helpers import C, no_network, pinned_reference  # noqa: F401  (fixtures)
from pristine_checkout import require_pristine

pytestmark = pytest.mark.usefixtures('pinned_reference')

NAMES = H.COMPONENT_NAMES
BAD = 'sha256:' + '0' * 64
GIT_ID = ['-c', 'user.name=asw', '-c', 'user.email=asw@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, stderr=subprocess.STDOUT, timeout=60).strip()


def drifted_copy(name, kind, root):
    """Private copy of a pinned checkout, then one kind of drift applied to the copy."""
    ref = H.reference()
    dst = root / name
    shutil.copytree(ref.paths[name], dst, symlinks=True)
    if kind == 'pristine_copy':
        return dst
    if kind == 'extra_commit':
        git(dst, *GIT_ID, 'commit', '--allow-empty', '-q', '-m', 'drift: unaccepted revision')
    elif kind == 'amended_head_same_tree':
        git(dst, *GIT_ID, 'commit', '--amend', '--allow-empty', '-q', '-m', 'same tree, different commit')
    elif kind in ('tracked_modification', 'assume_unchanged'):
        target = git(dst, 'ls-files').splitlines()[0]
        with open(dst / target, 'a') as handle:
            handle.write('\n# drifted\n')
        if kind == 'assume_unchanged':
            git(dst, 'update-index', '--assume-unchanged', target)
    elif kind == 'untracked_file':
        (dst / 'unaccepted_module.py').write_text('SHADOW = True\n')
    elif kind == 'ignored_file':
        (dst / '.git/info/exclude').write_text('shadow_*.py\n')
        (dst / 'shadow_module.py').write_text('SHADOW = True\n')
    else:
        raise ValueError(kind)
    return dst


# =====================================================================================================
# S01  Dependency commit drift from component lock: reject unaccepted revisions
# =====================================================================================================

def test_asw_s01_positive_control_exact_pins_are_accepted_and_the_lock_is_observed(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ref = H.reference()
        profile = ref.profile
        checks.equal(profile['components']['runtime']['revision'], H.FROZEN_RUNTIME, 'profile pins the frozen runtime')
        checks.equal(profile['components']['control_plane']['revision'], H.FROZEN_CONTROL_PLANE, 'profile pins the frozen control plane')
        checks.equal((profile['selected'], profile['reference_release_authorized'], profile['production_deployment_authorized']), (False, False, False),
                     'the profile is a non-selecting, non-authorizing candidate')
        for name in NAMES:
            try:
                got = require_pristine(ref.paths[name], profile['components'][name]['revision'], name)
            except ValueError as exc:
                got = f'REFUSED: {exc}'
            checks.equal(got, profile['components'][name]['revision'], f'{name}: exact pin accepted')
        # copies are accepted too (the drift tests below start from a verified-pristine copy)
        copy_ok = drifted_copy('manifest', 'pristine_copy', work)
        checks.equal(require_pristine(copy_ok, profile['components']['manifest']['revision'], 'manifest-copy'), profile['components']['manifest']['revision'], 'pristine copy accepted')
        lock_observation = None
        if ref.hub:
            lock = json.loads((Path(os.environ['SCN_HUB_DIR']) / 'component-lock.json').read_text())
            locked = {v.get('sha') for v in lock['components'].values()}
            lock_observation = {
                'hub_commit': H.FROZEN_HUB, 'hub_lock_qualification_status': lock.get('qualification_status'), 'hub_lock_runtime_profile': lock.get('runtime_profile'),
                'profile_revisions_listed_in_hub_component_lock': {n: profile['components'][n]['revision'] in locked for n in NAMES},
                'note': 'informational: the hub component-lock.json predates the F5b candidate pins; the qualification profile (not the lock) is the pin source for this reference run'}
        return {'pins_verified': NAMES, 'lock_observation': lock_observation, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S01', trial)


DRIFT_KINDS = ['extra_commit', 'amended_head_same_tree', 'tracked_modification', 'untracked_file', 'assume_unchanged', 'ignored_file']


@pytest.mark.parametrize('kind', DRIFT_KINDS)
@pytest.mark.parametrize('name', NAMES)
def test_asw_s01_drifted_component_checkout_is_refused_before_its_code_runs(request, record_property, tmp_path, name, kind):
    def trial(work, mp, checks):
        ref = H.reference()
        pin = ref.profile['components'][name]['revision']
        clone = drifted_copy(name, kind, work)
        refused = None
        try:
            require_pristine(clone, pin, name)
        except ValueError as exc:
            refused = str(exc)
        checks.expect(refused is not None, f'{name} with {kind} drift must be refused by the pristine-pin check')
        return {'component': name, 'drift': kind, 'refused_with': refused, 'head_after_drift': git(clone, 'rev-parse', 'HEAD') == pin, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S01', trial)


@pytest.mark.parametrize('kind', ['extra_commit', 'untracked_file'])
@pytest.mark.parametrize('name', NAMES)
def test_asw_s01_qualification_runner_refuses_a_drifted_component_set(request, record_property, tmp_path, name, kind):
    """The runner that builds the reference (tools/run_security_runtime.py) refuses a drifted component BEFORE it starts the suite."""
    def trial(work, mp, checks):
        ref = H.reference()
        comps = work / 'components'
        comps.mkdir()
        for other in NAMES:
            if other != name:
                os.symlink(ref.paths[other], comps / other)
        drifted_copy(name, kind, comps)
        out = work / 'out'
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        proc = subprocess.run([sys.executable, '-I', str(A.ROOT / 'tools/run_security_runtime.py'), '--profile', 'process/security-runtime-f5b-20261016.json',
                               '--components', str(comps), '--out', str(out)], cwd=str(A.ROOT), env=env, capture_output=True, text=True, timeout=120)
        checks.expect(proc.returncode != 0, f'the runner must exit non-zero for a drifted {name}; observed exit {proc.returncode}')
        checks.expect(f'Dirty or mismatched source: {name}' in proc.stderr, f'the runner names the drifted component; observed {proc.stderr[-200:]!r}')
        checks.expect(not out.exists(), 'no evidence/run directory was started for a drifted set')
        return {'component': name, 'drift': kind, 'exit_nonzero': proc.returncode != 0, 'named': f'Dirty or mismatched source: {name}' in proc.stderr,
                'run_started': out.exists(), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S01', trial)


def _export_flow(work, mp):
    flow = H.flow_a(work, mp)
    res, exc = H.execute_a(flow)
    ch = H.reference().chain
    export = ch.export_execution_artifacts(flow.env, res, flow.dest, repository_revision=ch.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
    raw = flow.f.records.load().model_dump(mode='json')
    return flow, export, raw


def _set(obj, path, value):
    keys = path.strip('/').split('/')
    for k in keys[:-1]:
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    if isinstance(obj, list):
        obj[int(keys[-1])] = value
    else:
        obj[keys[-1]] = value


def _import(flow, export, raw, control_plane_revision=None):
    ch = H.reference().chain
    try:
        b = ch.import_bounded_workflow(raw, proposal=flow.p.model_dump(mode='json'), moltbot_export=export,
                                       control_plane_revision=control_plane_revision or ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)
        return f'ACCEPTED complete={all(x.complete for x in b.import_reports)}'
    except Exception as exc:
        return A.norm(f'{type(exc).__name__}: {str(exc)[:140]}')


def test_asw_s01_positive_control_accepted_revisions_import_complete(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow, export, raw = _export_flow(work, mp)
        outcome = _import(flow, export, raw)
        checks.equal(outcome, 'ACCEPTED complete=True', 'the accepted F5b producer and Control Plane revisions import completely')
        return {'import': outcome, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S01', trial)


REVISION_DRIFT = {
    'control_plane_revision': ('cp', '0' * 40, 'unsupported Control Plane revision'),
    'runtime_repository_revision': ('/repository/revision', '1' * 40, 'unsupported Moltbot producer repository revision'),
    'runtime_provenance_revision': ('/provenance/source_asserted/repository_revision', '1' * 40, 'contradicts repository assertion'),
}


@pytest.mark.parametrize('drift', sorted(REVISION_DRIFT))
def test_asw_s01_replay_import_rejects_unaccepted_component_revisions(request, record_property, tmp_path, drift):
    path, value, expected = REVISION_DRIFT[drift]

    def trial(work, mp, checks):
        flow, export, raw = _export_flow(work, mp)
        if path == 'cp':
            outcome = _import(flow, export, raw, control_plane_revision=value)
        else:
            e2 = copy.deepcopy(export)
            _set(e2, path, value)
            outcome = _import(flow, e2, raw)
        checks.expect(expected in outcome, f'the import must reject the drifted revision ({expected!r}); observed {outcome!r}')
        return {'drift': drift, 'import': outcome, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S01', trial)


# =====================================================================================================
# S02  Artifact digest mismatch: reject substituted artifact or disclose nonverification
# =====================================================================================================

def test_asw_s02_positive_control_matching_artifacts_execute_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        res = H.exchange_run(flow)
        checks.equal(H.exchange_view(res)['attempt_status'], 'executed', 'matching artifacts execute')
        s = H.db_summary(flow.dest.path)
        A.one_effect_expected(checks, s, 'matching artifacts')
        return {'view': H.exchange_view(res), 'effects': s['effects'], **A.gate_for(s, {res['execution'].get('effect_id')})}
    A.run(request, record_property, tmp_path, 'S02', trial)


MESSAGE_TAMPER = {
    'unsigned_amount': (lambda gax, m: {**m, 'requested_action': {**m['requested_action'], 'amount': 999.0}}, 'GAX-INTEGRITY-DIGEST'),
    'unsigned_content': (lambda gax, m: {**m, 'content': {**m['content'], 'note': 'changed after signing'}}, 'GAX-INTEGRITY-DIGEST'),
    'message_digest_zeroed': (lambda gax, m: {**m, 'message_digest': BAD}, 'GAX-INTEGRITY-DIGEST'),
    'content_digest_zeroed': (lambda gax, m: {**m, 'content_digest': BAD}, 'GAX-INTEGRITY-DIGEST'),
    'resigned_operation_commitment': (lambda gax, m: A.resign_message(gax, m, operation_commitment=BAD), 'GAX-REFERENCE-OPERATION-BINDING-MISMATCH'),
    'resigned_proposal_commitment': (lambda gax, m: A.resign_message(gax, m, proposal_commitment=BAD), 'GAX-REFERENCE-OPERATION-BINDING-MISMATCH'),
}


@pytest.mark.parametrize('tamper', sorted(MESSAGE_TAMPER))
def test_asw_s02_route_c_tampered_exchange_message_is_rejected(request, record_property, tmp_path, tamper):
    mutate, code = MESSAGE_TAMPER[tamper]

    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        res = flow.gax.run_exchange(mutate(flow.gax, flow.message), flow.bundle, flow.registry, flow.dest, **flow.kwargs)
        checks.expect(code in (res['assessment'].get('errors') or []), f'rejected with {code}; observed {res["assessment"]}')
        checks.equal(bool((res.get('execution') or {}).get('attempted')), False, 'nothing dispatched')
        s = A.no_effect(checks, flow, f'tampered message {tamper}')
        return {'tamper': tamper, 'handling': res['assessment']['permitted_handling'], 'errors': res['assessment'].get('errors'), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'S02', trial)


def _bundle_variant(bundle, variant):
    b = json.loads(json.dumps(bundle))
    if variant == 'extra_field':
        b['substituted_marker'] = 'artifact replaced after the digest in evidence_refs was computed'
    elif variant == 'identifier_changed':
        for key in ('bundle_id', 'run_id'):
            if key in b:
                b[key] = str(b[key]) + '-substituted'
                break
    return b


@pytest.mark.parametrize('variant', ['extra_field', 'identifier_changed'])
def test_asw_s02_route_c_substituted_replay_bundle_is_rejected_or_nonverification_disclosed(request, record_property, tmp_path, variant):
    """The message's evidence_refs carry the digest of the retained bundle it points at. A bundle that is NOT that artifact
    (same derived proposal, different bytes) must be rejected, or the assessment must disclose that the digest was not
    verified. The acceptance text of S02 allows no third outcome."""
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        bundle = _bundle_variant(flow.bundle, variant)
        checks.expect(flow.gax.digest(bundle) != flow.message['evidence_refs'][0]['digest'], 'the substituted bundle really differs from the digest the message binds')
        res = flow.gax.run_exchange(flow.message, bundle, flow.registry, flow.dest, **flow.kwargs)
        assessment = res['assessment']
        ex = res.get('execution') or {}
        text = json.dumps(assessment).lower()
        rejected = assessment['permitted_handling'] != 'ACCEPT_FOR_ASSESSMENT' or bool(assessment.get('errors')) or not ex.get('attempted')
        disclosed = 'digest' in text and any(w in text for w in ('unverified', 'not_verified', 'nonverif', 'not verified'))
        checks.expect(rejected or disclosed,
                      'S02 VIOLATION: a bundle whose digest differs from the digest bound in the message was accepted and executed with no rejection '
                      f'and no disclosure of non-verification; assessment={assessment}, execution attempted={ex.get("attempted")} status={ex.get("attempt_status")}')
        s = H.db_summary(flow.dest.path)
        return {'variant': variant, 'assessment': assessment, 'execution': {k: ex.get(k) for k in ('attempted', 'attempt_status', 'newly_executed')},
                'rejected': rejected, 'nonverification_disclosed': disclosed, 'effects': s['effects'],
                'component': 'cognous-governed-exchange experiments/odex_gax_imx_reference/gax_ref.py assess_message (evidence_refs[].digest not compared to the supplied bundle)',
                **A.gate_for(s, {ex.get('effect_id')})}
    A.run(request, record_property, tmp_path, 'S02', trial)


def test_asw_s02_route_c_bundle_yielding_a_different_operation_is_rejected(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        bundle = json.loads(json.dumps(flow.bundle))
        hits = _rewrite_value(bundle, 'customer-001', 'customer-099')
        checks.expect(hits > 0, 'the bundle carried the original subject')
        res = flow.gax.run_exchange(flow.message, bundle, flow.registry, flow.dest, **flow.kwargs)
        checks.expect(res['assessment']['permitted_handling'] != 'ACCEPT_FOR_ASSESSMENT' or not (res.get('execution') or {}).get('attempted'),
                      f'a substituted bundle with a different operation must not execute; observed {res["assessment"]}')
        s = A.no_effect(checks, flow, 'bundle with different operation')
        return {'handling': res['assessment']['permitted_handling'], 'errors': res['assessment'].get('errors'), 'values_rewritten': hits, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'S02', trial)


def _rewrite_value(node, old, new):
    count = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and v == old:
                node[k] = new
                count += 1
            elif isinstance(v, str) and old in v:
                node[k] = v.replace(old, new)
                count += 1
            else:
                count += _rewrite_value(v, old, new)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str) and old in v:
                node[i] = v.replace(old, new)
                count += 1
            else:
                count += _rewrite_value(v, old, new)
    return count


def test_asw_s02_route_a_forged_manifest_digest_is_not_authorized(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp, mutate=lambda p, r, f, d: p.model_copy(update={'manifest_digest': BAD}))
        decision = A.expect_not_authorized(checks, flow.d, 'forged manifest digest')
        checks.expect('manifest_digest_mismatch' in decision['reasons'], f'names manifest_digest_mismatch; observed {decision["reasons"]}')
        res, exc = A.execute_decision(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, 'forged manifest digest')
        return {'decision': decision, 'result': A.view_a(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'S02', trial)


@pytest.mark.parametrize('field', ['amount', 'operation_commitment', 'claim_commitment', 'target', 'approval_state_commitment'])
def test_asw_s02_route_b_tampered_execution_claim_is_rejected_at_provisioning(request, record_property, tmp_path, field):
    def trial(work, mp, checks):
        from agent_control_plane.local_authority_effect import LocalExecutionClaim
        from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
        (work / 'good').mkdir()
        flow = H.flow_b(work / 'good')
        part = flow.parts[0]
        raw = part.claim.model_dump(mode='json')
        raw[field] = {'amount': 999.0, 'target': 'urn:cognous:synthetic-account:attacker'}.get(field, BAD)
        tampered = LocalExecutionClaim.model_validate(raw)
        (work / 'victim').mkdir()
        dest = H.hooked_atomic_class()(work / 'victim', clock=flow.clock)
        rejected = None
        try:
            dest.provision_claim(tampered)
        except Exception as exc:
            rejected = f'{type(exc).__name__}: {exc}'
        checks.expect(rejected is not None, f'tampered claim ({field}) must be rejected at provisioning')
        res, exc = None, None
        try:
            res = AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=flow.policy).execute(envelope=part.env, claim_id=tampered.claim_id)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
        checks.expect(A.refused_before_dispatch(res, exc), f'the tampered claim cannot be used; observed {A.view_b(res, exc)}')
        s = H.db_summary(dest.path)
        checks.equal(s['effects'], [], 'no destination effect')
        return {'field': field, 'provisioning_rejected_with': A.norm(rejected), 'use': A.view_b(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'S02', trial)


EXPORT_TAMPER = {
    'manifest_digest': '/execution_envelope/operation/manifest_digest',
    'payload_commitment': '/execution_envelope/operation/payload_commitment',
    'proposal_commitment': '/execution_envelope/operation/proposal_commitment',
    'effect_identity': '/execution_envelope/effect_id',
    'effect_operation_digest': '/effects/0/operation_digest',
    'attempt_operation_digest': '/attempts/0/operation_digest',
    'observation_operation_digest': '/observations/0/destination_state/operation_digest',
    'result_operation_digest': '/execution_result/observation/destination_state/operation_digest',
}


@pytest.mark.parametrize('artifact', sorted(EXPORT_TAMPER))
def test_asw_s02_executor_export_with_a_substituted_digest_is_rejected_by_the_replay_import(request, record_property, tmp_path, artifact):
    def trial(work, mp, checks):
        flow, export, raw = _export_flow(work, mp)
        checks.equal(_import(flow, export, raw), 'ACCEPTED complete=True', 'untampered export imports')
        e2 = copy.deepcopy(export)
        _set(e2, EXPORT_TAMPER[artifact], BAD)
        outcome = _import(flow, e2, raw)
        checks.expect(outcome.startswith('ImportContractError'), f'a substituted {artifact} must be rejected; observed {outcome!r}')
        return {'artifact': artifact, 'import': outcome, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S02', trial)


PACK_TAMPER = ['/metadata/traceable_import/input_artifacts/0/hash', '/metadata/traceable_import/input_artifacts/1/hash',
               '/metadata/traceable_import/source_record_refs/0/hash', '/metadata/traceable_import/source_record_refs/0/source_content_commitment',
               '/metadata/traceable_import/source_record_refs/1/local_content_commitment']


@pytest.mark.parametrize('index', range(len(PACK_TAMPER)))
def test_asw_s02_evidence_pack_with_a_substituted_digest_is_detected(request, record_property, tmp_path, index):
    path = PACK_TAMPER[index]

    def trial(work, mp, checks):
        from agent_governance_evidence_pack import EvidencePack, validate_evidence_pack
        from agent_governance_evidence_pack.importer import import_manifest_reconstruction
        ch = H.reference().chain
        flow, export, raw = _export_flow(work, mp)
        bundle = ch.import_bounded_workflow(raw, proposal=flow.p.model_dump(mode='json'), moltbot_export=export, control_plane_revision=ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)
        pack = import_manifest_reconstruction(flow.f.manifest, bundle.model_dump(mode='json'))
        checks.expect(validate_evidence_pack(pack).valid, 'the untampered pack validates')
        pj = pack.model_dump(mode='json')
        _set(pj, path, BAD)
        try:
            verdict = 'valid' if validate_evidence_pack(EvidencePack.model_validate(pj)).valid else 'invalid'
        except Exception as exc:
            verdict = f'rejected:{type(exc).__name__}'
        checks.expect(verdict != 'valid', f'tampered pack ({path}) must not validate; observed {verdict}')
        return {'tampered_path': path, 'verdict': verdict, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    A.run(request, record_property, tmp_path, 'S02', trial)
