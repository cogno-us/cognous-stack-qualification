import pytest
from refusal_sources import actual, bundle
from agent_governance_evidence_pack import import_manifest_reconstruction, validate_evidence_pack, ImportContractError
from agent_governance_evidence_pack.importer import REFUSAL_REVISIONS, REFUSAL_TRANSFORMATION_VERSION

@pytest.mark.parametrize('change',['grant','approval','policy','evidence','lost-ack','success'])
def test_exact_refusal_evidence_survives_pack_revalidation(actual,change):
    cp,p,e,b,m=bundle(actual,change)
    pack=import_manifest_reconstruction(m,b)
    report=validate_evidence_pack(pack)
    assert report.valid, report.issues
    trace=pack.metadata['traceable_import']
    assert trace['retained_sources']['reconstruction_bundle']==b
    assert trace['selected_revisions']==REFUSAL_REVISIONS
    assert trace['supported_revision_sets']=={k:[v] for k,v in REFUSAL_REVISIONS.items()}
    assert trace['transformation_version']==REFUSAL_TRANSFORMATION_VERSION

@pytest.mark.parametrize('change',['drop-refusal','substitute-effect','erase-floors','promote-status'])
def test_retained_evidence_tampering_is_rejected(actual,change):
    _,_,_,b,m=bundle(actual)
    if change=='drop-refusal':b['records']=[r for r in b['records'] if r['record_type']!='effect_time_refusal']
    elif change=='erase-floors':b['records']=[r for r in b['records'] if r['record_type']!='input_time_floors']
    elif change=='substitute-effect':next(r for r in b['records'] if r['record_type']=='effect_time_refusal')['data']['effect_id']='other'
    else:b['status']='reconstruction_partial'
    with pytest.raises((ImportContractError,ValueError)):import_manifest_reconstruction(m,b)
