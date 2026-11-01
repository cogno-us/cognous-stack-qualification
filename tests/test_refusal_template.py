"""Refusal-test template logic, exercised with an in-memory adapter (no pinned components needed)."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'suites'))
import _refusal_template as T  # noqa: E402


class _Mp:
    def undo(self):
        pass


class FakeAdapter(T.Adapter):
    """A toy route. Flags let a test break exactly one leg."""
    def __init__(self, *, leak=False, no_row=False, row_without_versions=False, control_blocked=False, other_policy=False, survive=False):
        self.f = dict(leak=leak, no_row=no_row, row_without_versions=row_without_versions, control_blocked=control_blocked,
                      other_policy=other_policy, survive=survive)

    def build(self, work, mp):
        return {'changed': False, 'writer': True, 'ledger': [], 'refusals': [], 'checks': []}

    def apply_change(self, flow):
        flow['changed'] = True

    def execute(self, flow):
        policy = '2.0' if (self.f['other_policy'] and not flow['changed']) else '1.0'
        flow['checks'].append({'stage': 'effect', 'policy': policy})
        if flow['changed']:
            if self.f['leak']:
                flow['ledger'].append('E1')
            if flow['writer'] and not self.f['no_row']:
                changed = [{'input_type': 'grant', 'input_id': 'G1'}] if self.f['row_without_versions'] else \
                          [{'input_type': 'grant', 'input_id': 'G1', 'expected_version': 'r1;active', 'observed_version': 'r1;revoked'}]
                flow['refusals'].append({'refusal_id': 'R1', 'effect_id': 'E1', 'stage': 'effect_time_revalidation', 'reasons': ['grant_revoked'],
                                         'changed_inputs': changed,
                                         'resolution_inputs': [{'input_type': 'policy', 'input_id': 'P1', 'observed': {'version': '1.0'}}]})
        elif not self.f['control_blocked']:
            flow['ledger'].append('E1')

    def effect_id(self, flow):
        return 'E1'

    def ledger_effect_ids(self, flow):
        return list(flow['ledger'])

    def refusal_rows(self, flow):
        return list(flow['refusals'])

    def disable_refusal_writer(self, flow):
        flow['writer'] = self.f['survive']  # a surviving mutant keeps writing the row

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {'P1': flow['checks'][-1]['policy']}


def spec(**kw):
    base = dict(name='fake', reasons=('grant_revoked',), changed_inputs=(T.ChangedInput('grant', 'G1'),),
                provenance=T.Provenance('code-reading', 'fake.py:build'), revocation=True, stage='effect_time_revalidation')
    base.update(kw)
    return T.RefusalSpec(**base)


def run(adapter, s=None):
    with tempfile.TemporaryDirectory() as d:
        return T.run_refusal_scenario(adapter, s or spec(), pathlib.Path(d), _Mp)


class RefusalTemplate(unittest.TestCase):
    def test_all_legs_pass(self):
        result = run(FakeAdapter())
        self.assertEqual(result.legs_passed, T.LEGS)
        self.assertTrue(result.mutation['detected'])
        self.assertTrue(result.mutation['effect_still_blocked'])
        self.assertEqual(result.control['bound_policy_versions'], {'P1': '1.0'})
        self.assertEqual(result.evidence()['expected_today_provenance']['kind'], 'code-reading')

    def assertLeg(self, leg, adapter=None, s=None):
        with self.assertRaises(T.RefusalTemplateFailure) as caught:
            run(adapter or FakeAdapter(), s)
        self.assertEqual(caught.exception.leg, leg, str(caught.exception))

    def test_a_effect_in_ledger(self):
        self.assertLeg('a', FakeAdapter(leak=True))

    def test_b_missing_row_reason_or_versions(self):
        self.assertLeg('b', FakeAdapter(no_row=True))
        self.assertLeg('b', FakeAdapter(row_without_versions=True))
        self.assertLeg('b', s=spec(reasons=('grant_expired',)))
        self.assertLeg('b', s=spec(changed_inputs=(T.ChangedInput('grant', 'OTHER'),)))
        self.assertLeg('b', s=spec(stage='decision'))

    def test_c_control_must_reach_destination_and_be_policy_bound(self):
        self.assertLeg('c', FakeAdapter(control_blocked=True))
        self.assertLeg('c', FakeAdapter(other_policy=True))
        self.assertTrue(run(FakeAdapter(other_policy=True), spec(revocation=False)))  # the policy binding is a revocation-probe rule

    def test_d_surviving_mutant_is_a_failure(self):
        self.assertLeg('d', FakeAdapter(survive=True))

    def test_e_provenance_label_required(self):
        self.assertLeg('e', s=spec(provenance=T.Provenance('guess', 'x')))
        self.assertLeg('e', s=spec(provenance=T.Provenance('run', '  ')))
        self.assertTrue(run(FakeAdapter(), spec(provenance=T.Provenance('run', 'pinned run abc'))))

    def test_no_refusal_holder_is_coverage_unknown_never_expired(self):
        rows = [{'refusal_id': 'R1', 'effect_id': 'E1', 'reasons': ['grant_revoked'], 'changed_inputs': [{'input_id': 'G1'}]}]
        out = T.classify_holders([{'holder_id': 'G1', 'kind': 'grant'}, {'holder_id': 'M1', 'kind': 'mandate'},
                                  {'holder_id': 'D1', 'effect_ids': ['E1']}], rows)
        self.assertEqual([h['holder_id'] for h in out['witnessed_refusals']], ['G1', 'D1'])
        self.assertEqual([h['holder_id'] for h in out['unenumerated_authority_needing_containment']], ['M1'])
        unknown = out['unenumerated_authority_needing_containment'][0]
        self.assertEqual(unknown['classification'], 'coverage_unknown')
        self.assertNotIn('expired', str(out).lower())
        self.assertEqual(set(out), {'witnessed_refusals', 'unenumerated_authority_needing_containment'})
        self.assertEqual(T.classify_holders([{'holder_id': 'M1'}], [])['witnessed_refusals'], [])


if __name__ == '__main__':
    unittest.main()
