import copy
import pytest
from tools.aggregate_full_candidate import validate_reports
from tools.reference_release import BATCHES


def reports():
    result=[]
    for batch,names in BATCHES.items():
        r={'batch':batch,'profile_sha256':'exact','passed':True,'suite_runs':[{'suite':n,'repetition':rep,'returncode':0} for n in names for rep in (1,2)],'extra':[]}
        if batch=='exchange':r.update(representative_repeatable=True,representative_runs=[{'returncode':0},{'returncode':0}])
        if batch=='authority':r['extra']=[{'returncode':0}]
        if batch=='registry':
            r['extra']=[{'returncode':0} for _ in range(3)]
            r['suite_runs'] += [{'suite':'index_local_chain','repetition':rep,'returncode':0} for rep in (1,2)]
        result.append(r)
    return result


def test_complete_reports_pass():validate_reports(reports(),'exact')


@pytest.mark.parametrize('mutation',['missing','duplicate','digest','failed','repetition','transport','mock','registry'])
def test_incomplete_batch_cannot_pass(mutation):
    data=reports()
    if mutation=='missing':data.pop()
    elif mutation=='duplicate':data[-1]=copy.deepcopy(data[0])
    elif mutation=='digest':data[0]['profile_sha256']='different'
    elif mutation=='failed':data[0]['passed']=False
    elif mutation=='repetition':data[0]['suite_runs'].pop()
    elif mutation=='transport':next(r for r in data if r['batch']=='exchange')['representative_repeatable']=False
    elif mutation=='mock':next(r for r in data if r['batch']=='authority')['extra']=[]
    elif mutation=='registry':next(r for r in data if r['batch']=='registry')['suite_runs'].pop()
    with pytest.raises(ValueError):validate_reports(data,'exact')


def test_historical_green_reports_do_not_qualify_refusal_candidate():
    with pytest.raises(ValueError, match="missing suite repetition"):
        validate_reports(reports(), 'exact', {'runtime_profile':'typed-refusal-candidate-20261015'})


@pytest.mark.parametrize('missing', ['executor_refusal','gax_refusal','gax_historical_artifacts','replay_refusal','odes_refusal','evidence_pack_refusal'])
def test_each_current_generation_suite_is_mandatory(missing):
    from tools.reference_release import CANDIDATE_SUITES
    data=reports()
    for report in data:
        report['suite_runs'] += [{'suite':name,'repetition':rep,'returncode':0}
            for name in CANDIDATE_SUITES[report['batch']] for rep in (1,2)]
    profile={'runtime_profile':'typed-refusal-candidate-20261015'}
    validate_reports(data, 'exact', profile)
    for report in data:
        report['suite_runs']=[run for run in report['suite_runs']
            if (run['suite'],run['repetition']) != (missing,2)]
    with pytest.raises(ValueError, match="missing suite repetition"):
        validate_reports(data, 'exact', profile)
