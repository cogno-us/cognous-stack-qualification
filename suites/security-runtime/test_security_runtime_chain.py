"""Exact repaired-source continuation of the original runtime-authority cases, never selected.

Original synthetic tests derived from supplied Moltbook 101526_A K1–K5.
Apache-2.0. Component-local tests remain with their owning implementations.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import pytest
from tests.test_runtime_authority import setup_flow,bind_approval,NOW,PROFILE,INSTITUTION
from agent_control_plane.bounded import commitment
from engine.effective_grant import EffectiveGrantDestination,DERIVATION
from engine.safe_executor import ExecutionOperation,ExecutionEnvelope,EXECUTION_ENVELOPE_VERSION,LocalExecutionPolicy
from engine.control_plane_adapter import PinnedControlPlaneExecutor
from engine.producer_contract import export_execution_artifacts
from agent_replay_bundle.importers import import_bounded_workflow,CONTROL_PLANE_SECURITY_REVISION as CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION,MOLTBOT_SECURITY_REVISION as MOLTBOT_RUNTIME_AUTHORITY_REVISION


def integrated(tmp_path,monkeypatch,*,purpose=False):
    import agent_control_plane.bounded as cp
    monkeypatch.setattr(cp,'_now',lambda:NOW)
    p,r,f,c=setup_flow(tmp_path/'cp',purpose=purpose)
    grant=r.contexts[PROFILE]['grant'];dest=EffectiveGrantDestination(tmp_path/'sqlite')
    digest=dest.set_effective_grant(principal=p.principal,grant_id=grant['grant_id'],revision=grant['revision'],permissions=p.requested_permissions)
    r.contexts[PROFILE]['runtime_authority'].update(expected_effective_grant_digest=digest,effective_grant_derivation_version=DERIVATION)
    bind_approval(r,c);f.destination=dest
    d=f.decide(p,now=NOW);assert d.result=='authorized',d.reasons
    fields={k:getattr(p,k) for k in ['actor','principal','manifest_id','manifest_version','manifest_digest','action_id','adapter_id','target','payload','payload_commitment','amount','unit','effects','requirement_id']}
    op=ExecutionOperation(**fields,institution_id=INSTITUTION,authority_domain='customer-refunds',
        proposal_commitment=commitment(p.model_dump(mode='json')),requested_permissions=tuple(p.requested_permissions),
        authority_context_id=p.authority_context_ref,grant_id=d.binding.grant_id,grant_revision=d.binding.grant_revision,effective_max_effects=d.binding.effective_max_effects)
    pol=LocalExecutionPolicy(allowed_institutions=frozenset({INSTITUTION}),allowed_authority_domains=frozenset({'customer-refunds'}),
        allowed_adapters=frozenset({p.adapter_id}),allowed_actions=frozenset({p.action_id}),allowed_target_prefixes=('urn:cognous:synthetic-account:',),
        allowed_units=frozenset({'USD'}),max_amount=1000,max_effects=1)
    executor=PinnedControlPlaneExecutor(workflow=f,destination=dest,policy=pol,observation_clock=lambda:NOW)
    env=ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION,d.decision_id,d.effect_id,op)
    return p,r,f,c,d,dest,executor,env


def produce(tmp_path,monkeypatch,case):
    p,r,f,c,d,dest,executor,env=integrated(tmp_path,monkeypatch,purpose=case.startswith('purpose'))
    if case=='unreadable':
        def broken(ref):raise TimeoutError()
        r.grant_status=broken
    elif case=='revoked':next(iter(r.statuses.values())).status='revoked'
    elif case=='purpose_closed':r.purpose.state='closed'
    elif case=='purpose_reopened':r.purpose.epoch='new-epoch'
    elif case=='tampered_evidence':next(iter(r.evidence.values())).validation_record['statement']['values']['validated_count']=999
    elif case=='input_dropped':
        # An approved input remains required but is omitted from the resolver path.
        r.contexts[PROFILE]['requirement']['evidence']=[]
    elif case=='race':
        original=dest.commit
        def race(snapshot,**kwargs):
            dest.set_effective_grant(principal=p.principal,grant_id=d.binding.grant_id,revision='2',permissions=p.requested_permissions+['admin'])
            return original(snapshot,**kwargs)
        dest.commit=race
    result=executor.execute(envelope=env,proposal=p,decision=d,now=NOW,simulate='lost_ack' if case=='lost_ack' else None)
    export=export_execution_artifacts(env,result,dest,repository_revision=MOLTBOT_RUNTIME_AUTHORITY_REVISION)
    raw=f.records.load().model_dump(mode='json')
    bundle=import_bounded_workflow(raw,proposal=p.model_dump(mode='json'),moltbot_export=export,control_plane_revision=CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)
    # Retain native producer/consumer bytes beside the authoritative SQLite state.
    for name,data in [('proposal.json',p.model_dump(mode='json')),('executor.json',export),
                      ('reconstruction.json',bundle.model_dump(mode='json')),
                      ('destination-observation.json',dest.observe(d.effect_id))]:
        (tmp_path/name).write_text(json.dumps(data,indent=2)+'\n')
    return p,r,f,d,dest,result,export,bundle


@pytest.mark.parametrize('case,reason',[('unreadable','status_unreadable'),('revoked','grant_revoked'),
    ('purpose_closed','purpose_closed'),('purpose_reopened','purpose_epoch_changed'),
    ('tampered_evidence','evidence_signature_invalid'),('input_dropped','required_input_not_read')])
def test_denial_preserves_actual_journal_refusal_and_destination(tmp_path,monkeypatch,case,reason):
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,case)
    assert result.status=='denied' and not result.attempted
    assert dest.observe(d.effect_id)['state']=='absent'
    refusal=f.records.load().refusals[-1].model_dump(mode='json')
    assert reason in refusal['reasons']
    assert result.control_plane_evidence['refusal']==export['control_plane_evidence']['refusal']==refusal
    assert any(x.record_type=='effect_time_refusal' and x.data==refusal for x in bundle.records)
    events=[x.data for x in bundle.records if x.record_type=='resolution_check_event']
    assert events==[x.model_dump(mode='json') for x in f.records.load().check_events]
    assert all(x.complete for x in bundle.import_reports)


@pytest.mark.parametrize('case',['valid','lost_ack','race'])
def test_effect_and_commit_boundary(tmp_path,monkeypatch,case):
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,case)
    count=dest.effect_count(d.binding.grant_id)
    if case=='race':
        assert count==0 and 'effective_grant_changed_at_commit' in result.error
    else:
        assert count==1 and dest.observe(d.effect_id)['state']=='applied'
        if case=='lost_ack':assert result.status=='unknown' and not result.acknowledged
    assert all(x.complete for x in bundle.import_reports)


def test_runtime_profile_cannot_drop_executor_refusal(tmp_path,monkeypatch):
    from agent_replay_bundle.importers import ImportContractError
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    export['control_plane_evidence']={};export['execution_result']['control_plane_evidence']={}
    with pytest.raises(ImportContractError):import_bounded_workflow(f.records.load().model_dump(mode='json'),proposal=p.model_dump(mode='json'),moltbot_export=export,control_plane_revision=CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)


def test_journal_substitution_rejected(tmp_path,monkeypatch):
    from agent_replay_bundle.importers import ImportContractError
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    raw=f.records.load().model_dump(mode='json');raw['check_events'][1]['proposal_commitment']='sha256:'+'0'*64
    with pytest.raises(ImportContractError):import_bounded_workflow(raw,proposal=p.model_dump(mode='json'),moltbot_export=export,control_plane_revision=CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)


@pytest.mark.parametrize('case',['valid','lost_ack','revoked','unreadable','purpose_closed','race'])
def test_evidence_pack_preserves_exact_source_and_reason_versions(tmp_path,monkeypatch,case):
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction,RUNTIME_AUTHORITY_TRANSFORMATION_VERSION
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,case)
    raw=bundle.model_dump(mode='json')
    pack=import_manifest_reconstruction(f.manifest,raw)
    from agent_governance_evidence_pack import validate_evidence_pack,render_traceable_markdown
    assert validate_evidence_pack(pack).valid
    text=render_traceable_markdown(pack)
    assert text
    (tmp_path/'evidence-pack.json').write_text(pack.model_dump_json(indent=2)+'\n')
    (tmp_path/'evidence-pack.md').write_text(text)
    trace=pack.model_dump(mode='json')['metadata']['traceable_import']
    assert trace['retained_sources']['reconstruction_bundle']==raw
    summary=trace['refusal_vocabulary_summary']
    if case in {'revoked','unreadable','purpose_closed'}:
        assert summary['total_refusals']==1 and summary['series'][0]['version']=='runtime-authority-reasons/0.1'
    assert not summary['disappearance_assessed']


def test_journal_read_omission_rejected(tmp_path,monkeypatch):
    from agent_replay_bundle.importers import ImportContractError
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    raw=f.records.load().model_dump(mode='json')
    index=next(i for i,x in enumerate(raw['check_events']) if x['phase']=='input')
    del raw['check_events'][index]
    with pytest.raises(ImportContractError):import_bounded_workflow(raw,proposal=p.model_dump(mode='json'),moltbot_export=export,control_plane_revision=CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)


def test_refusal_vocabulary_cannot_disappear(tmp_path,monkeypatch):
    from agent_replay_bundle.importers import ImportContractError
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    raw=f.records.load().model_dump(mode='json');del raw['refusals'][0]['reason_vocabulary_version']
    with pytest.raises(ImportContractError):import_bounded_workflow(raw,proposal=p.model_dump(mode='json'),moltbot_export=export,control_plane_revision=CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)


def test_evidence_pack_cannot_relabel_refusal_counts(tmp_path,monkeypatch):
    from agent_governance_evidence_pack import import_manifest_reconstruction,validate_evidence_pack
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    pack=import_manifest_reconstruction(f.manifest,bundle.model_dump(mode='json'))
    pack.metadata['traceable_import']['refusal_vocabulary_summary']['total_refusals']=0
    assert not validate_evidence_pack(pack).valid


def test_security_pair_rejects_historical_cp(tmp_path, monkeypatch):
    from agent_replay_bundle.importers import ImportContractError, CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION as historical
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    with pytest.raises(ImportContractError, match='revision combination'):
        import_bounded_workflow(f.records.load().model_dump(mode='json'), proposal=p.model_dump(mode='json'),
            moltbot_export=export, control_plane_revision=historical)


def test_failure_reference_is_not_durability_proof(tmp_path, monkeypatch):
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    assert bundle.metadata['executor_failure_reference_verification']=='source_asserted_not_independently_verified'
    assert isinstance(export['control_plane_evidence']['failure_record_id'],str)


def test_failure_reference_type_confusion_rejected(tmp_path, monkeypatch):
    from agent_replay_bundle.importers import ImportContractError
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'revoked')
    export['control_plane_evidence']['failure_record_id']=123
    export['execution_result']['control_plane_evidence']['failure_record_id']=123
    with pytest.raises(ImportContractError, match='failure reference'):
        import_bounded_workflow(f.records.load().model_dump(mode='json'),proposal=p.model_dump(mode='json'),
            moltbot_export=export,control_plane_revision=CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)


@pytest.mark.parametrize('case',['valid','lost_ack','revoked','unreadable','purpose_closed','race'])
def test_odes_preserves_repaired_runtime_semantics(tmp_path,monkeypatch,case):
    from odes import export_cognous_stack_package,evaluate_recipient_package
    from odes.common import SECURITY_REVISIONS,SECURITY_PROFILE_VERSION
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,case)
    package=export_cognous_stack_package(f.manifest,bundle.model_dump(mode='json'))
    assert package['provenance']['pinned_revisions']==SECURITY_REVISIONS
    assert package['profile']['implementation_profile_version']==SECURITY_PROFILE_VERSION
    assert package['provenance']['retained_sources']['reconstruction_bundle']==bundle.model_dump(mode='json')
    events=package['provenance']['execution_facts']['resolution_check_event']
    assert events==[x.model_dump(mode='json') for x in f.records.load().check_events]
    from odes.recipient_validator import _evaluate_replay_semantics
    assert _evaluate_replay_semantics(package)['status']=='pass'
    # Semantic replay success cannot supply missing issuer/status/use authority.
    recipient=evaluate_recipient_package(package,{})
    assert recipient['recipient_reliance_decision']['status']=='fail'
    (tmp_path/'odes-package.json').write_text(json.dumps(package,indent=2)+'\n')


def test_odes_rejects_relabelled_replay_pin(tmp_path,monkeypatch):
    from odes import export_cognous_stack_package
    from odes.recipient_validator import _evaluate_replay_semantics
    p,r,f,d,dest,result,export,bundle=produce(tmp_path,monkeypatch,'valid')
    package=export_cognous_stack_package(f.manifest,bundle.model_dump(mode='json'))
    package['provenance']['pinned_revisions']['replay']='83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a'
    assert _evaluate_replay_semantics(package)['status']=='fail'
