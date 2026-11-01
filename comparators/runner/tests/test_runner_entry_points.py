"""Entry points: refusals, stale declarations, plan-driven schedule and a masked plumbing run end to end (verdicts discarded)."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from comparators.runner import cells, run_core, run_wiki_subset

REPO = Path(__file__).resolve().parents[3]
WIKI = REPO / 'comparators/runner/run_wiki_subset.py'
TOP = REPO / 'comparators/runner/run_comparison.py'


def run(script, *args):
    return subprocess.run([sys.executable, '-I', str(script), *args], capture_output=True, text=True, timeout=900)


def test_a_real_run_is_refused_without_confirmation(tmp_path, opa):
    for script in (WIKI, TOP):
        p = run(script, '--opa', opa, '--output', str(tmp_path / script.stem))
        assert p.returncode != 0 and 'confirm-real-run' in (p.stdout + p.stderr)
        assert not (tmp_path / script.stem).exists()


def test_stale_declarations_stop_the_run_before_any_trial(tmp_path, opa, plan):
    stale = json.loads((REPO / run_wiki_subset.DECL_REL).read_text())
    stale['records'][0]['scenario_sha256'] = '0' * 64   # the scenario changed since the declaration was written
    f = tmp_path / 'decl.json'
    f.write_text(json.dumps(stale))
    p = run(WIKI, '--opa', opa, '--output', str(tmp_path / 'out'), '--declarations', str(f), '--twins', plan['cases'][0]['id'])
    assert p.returncode == 2 and 'not current' in p.stdout
    assert not (tmp_path / 'out' / 'results.json').exists()


def test_an_existing_output_directory_is_never_reused(tmp_path, opa, plan):
    (tmp_path / 'out').mkdir()
    p = run(WIKI, '--opa', opa, '--output', str(tmp_path / 'out'), '--twins', plan['cases'][0]['id'])
    assert p.returncode != 0


def test_the_schedule_is_deterministic_and_comes_from_the_cases_given():
    cases = [dict(id='a'), dict(id='b'), dict(id='c')]
    one = run_core.schedule(cases, list(run_core.PROFILES), 2, 1701)
    assert one == run_core.schedule(cases, list(run_core.PROFILES), 2, 1701)
    assert one != run_core.schedule(cases, list(run_core.PROFILES), 2, 1702)
    assert len(one) == 2 * 3 * 3
    assert len(run_core.schedule(cases + [dict(id='d')], list(run_core.PROFILES), 2, 1701)) == 2 * 4 * 3


def test_the_table_rows_cover_every_scenario_of_the_plan(plan):
    rows = run_wiki_subset.case_table_rows(plan)
    ids = sorted(x for r in rows for x in r['scenarios'])
    assert ids == sorted([c['id'] for c in plan['cases']] + [c['id'] for c in plan['non_executed']])


def test_twins_carry_no_original_id_and_no_title(plan):
    ids = [c['id'] for c in plan['cases'][:3]]
    twins, rename = run_core.twin_cases(plan['cases'], ids)
    assert [t['id'] for t in twins] == ['twin-1', 'twin-2', 'twin-3']
    blob = json.dumps(twins)
    assert not any(i in blob for i in ids)
    with pytest.raises(SystemExit):
        run_core.twin_cases(plan['cases'], ['no-such-scenario'])


def test_masked_plumbing_end_to_end_through_entry_point_aggregation_and_report(tmp_path, opa, plan, decl):
    states = cells.scenario_states(plan, 'cognous-protected-destination', decl)
    ocs = states['cognous-protected-destination']
    asked = next(c['id'] for c in plan['cases'] if ocs[c['id']]['run'] and ocs[c['id']]['scored'])
    expressed_nc = next((c['id'] for c in plan['cases'] if ocs[c['id']]['run'] and not ocs[c['id']]['scored']), None)
    not_run = next(c['id'] for c in plan['cases'] if not ocs[c['id']]['run'])
    ids = [i for i in (asked, expressed_nc, not_run) if i]
    out = tmp_path / 'wiki'
    p = run(WIKI, '--opa', opa, '--output', str(out), '--twins', ','.join(ids))
    assert p.returncode == 0, p.stdout + p.stderr
    result = json.loads((out / 'results.json').read_text())
    assert result['masked'] is True and result['rows'] and not any(r.get('error') for r in result['rows'])
    blob = json.dumps(result)
    assert not any(i in blob for i in ids) and '"pass_case"' not in blob and '"outcome": "pass"' not in blob and '"outcome": "fail"' not in blob
    # a scenario that is not run for a configuration has no trial of it
    ocs_rows = [r for r in result['rows'] if r['profile'] == 'cognous-protected-destination']
    assert len(ocs_rows) == len(ids) - 1
    summary = (out / 'summary.md').read_text()
    assert 'verdicts discarded' in summary and 'twin-1' in summary and not any(i in summary for i in ids)
