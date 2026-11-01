"""Unit tests of the graph layer, on a synthetic base (no registered scenario is run). See README for the command."""
import hashlib
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'support'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comparators.wiki.harness import _base
from comparators.wiki.apps import wiki_langgraph_app as app
from synthetic_base import SyntheticBase, SyntheticBaseWithHook
from reference_profiles.assurance_runtime import digest

TMP = tempfile.TemporaryDirectory()
COUNTER = [0]


def fresh(cls, mutation=None):
    COUNTER[0] += 1
    return cls(Path(TMP.name) / ('case-%d' % COUNTER[0]), 'opa-unused', mutation)


Graph = app.make_wiki_langgraph_app(SyntheticBase, 'GraphOverSynthetic')
GraphHook = app.make_wiki_langgraph_app(SyntheticBaseWithHook, 'GraphOverSyntheticHook')


def checkpoint_threads(a):
    with sqlite3.connect(a.root / 'checkpoints.sqlite') as c:
        return {r[0] for r in c.execute('SELECT DISTINCT thread_id FROM checkpoints')}


class ContractTests(unittest.TestCase):
    def test_contract_accepts_complete_base(self):
        app.check_base_contract(SyntheticBase)

    def test_contract_rejects_incomplete_base(self):
        class Bad: apply = lambda self, r: None
        with self.assertRaises(TypeError):
            app.make_wiki_langgraph_app(Bad)

    def test_request_is_the_base_request_unchanged(self):
        self.assertIs(Graph.request, SyntheticBase.request)

    def test_unknown_fault_still_raises(self):
        with self.assertRaises(ValueError):
            fresh(Graph).request(None, 'no_such_fault')

    def test_unknown_graph_mutation_raises(self):
        with self.assertRaises(ValueError):
            fresh(Graph, 'graph_nonsense')

    def test_base_mutation_passes_through(self):
        self.assertEqual(fresh(Graph, 'base_only').mutation, 'base_only')

    def test_lazy_name_is_the_graph_over_the_real_wiki_opa_app(self):
        from comparators.wiki.apps.wiki_opa_app import WikiOpaApp
        self.assertTrue(issubclass(app.WikiLangGraphOPA, WikiOpaApp))
        self.assertIs(app.WikiLangGraphOPA._base_cls, WikiOpaApp)


class AutoModeTests(unittest.TestCase):
    def test_effect_goes_through_interrupt_then_base(self):
        a = fresh(Graph); r = a.request(); out = a.apply(r)
        self.assertEqual((out['status'], out['reason']), ('accepted', None))
        s = a.snapshot()
        self.assertEqual(len(s['effects']), 1)
        self.assertEqual(s['events'][0]['request_digest'], digest(r))
        self.assertIn(r['body']['id'], checkpoint_threads(a))  # the graph really ran

    def test_base_denial_passes_through(self):
        a = fresh(Graph); a.revoke(); out = a.apply(a.request())
        self.assertEqual((out['status'], out['reason']), ('denied', 'POLICY_DENIED'))
        self.assertEqual(a.snapshot()['effects'], [])

    def test_audit_outage_propagates_as_integrity_error(self):
        a = fresh(Graph); a.break_audit()
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            a.apply(a.request())
        self.assertEqual(str(ctx.exception), 'synthetic audit outage')
        self.assertEqual(a.snapshot()['effects'], [])

    def test_two_concurrent_callers_one_budget(self):
        a = fresh(Graph); reqs = [a.request({'effect': 'p%d' % i}) for i in range(2)]
        barrier = threading.Barrier(2); outs = []
        def go(r):
            barrier.wait(timeout=10); outs.append(a.apply(r)['status'])
        ts = [threading.Thread(target=go, args=(r,)) for r in reqs]
        [t.start() for t in ts]; [t.join(60) for t in ts]
        self.assertEqual(sorted(outs), ['accepted', 'denied'])
        self.assertEqual(len(a.snapshot()['effects']), 1)

    def test_fork_safe(self):
        a = fresh(Graph); r = a.request()
        p = multiprocessing.get_context('fork').Process(target=lambda: (a.apply(r), os._exit(0)))
        p.start(); p.join(60)
        self.assertEqual(p.exitcode, 0)
        self.assertEqual(len(a.snapshot()['effects']), 1)


class HoldTests(unittest.TestCase):
    def check_recorded_denial(self, a, r, reason):
        ev = [e for e in a.snapshot()['events'] if e['status'] == 'denied' and e['request_digest'] == digest(r)]
        self.assertTrue(ev and ev[-1]['reason'] == reason and type(ev[-1]['at']) is int)

    def test_hold_denies_and_records_then_approve_executes(self):
        a = fresh(Graph); a.require_approval(); r = a.request(); out = a.apply(r)
        self.assertEqual((out['status'], out['reason']), ('denied', app.REASON_PENDING))
        self.assertEqual(a.snapshot()['effects'], [])
        self.check_recorded_denial(a, r, app.REASON_PENDING)
        self.assertEqual(a.pending_threads(), [r['body']['id']])
        a.approve()
        self.assertEqual(len(a.snapshot()['effects']), 1)
        self.assertEqual(a.last_resolutions[0]['status'], 'accepted')
        self.assertEqual(a.pending_threads(), [])

    def test_reject_is_a_recorded_denial_not_an_exception(self):
        a = fresh(Graph); a.require_approval(); r = a.request(); a.apply(r); a.reject()
        self.assertEqual(a.snapshot()['effects'], [])
        self.assertEqual(a.last_resolutions[0]['reason'], 'APPROVAL_REJECTED')
        self.check_recorded_denial(a, r, 'APPROVAL_REJECTED')

    def test_timeout_is_a_recorded_denial(self):
        a = fresh(Graph); a.require_approval(); r = a.request(); a.apply(r); a.timeout()
        self.assertEqual(a.snapshot()['effects'], [])
        self.check_recorded_denial(a, r, 'APPROVAL_TIMED_OUT')

    def test_resubmission_while_pending_stays_pending(self):
        a = fresh(Graph); a.require_approval(); r = a.request()
        a.apply(r); out = a.apply(r)
        self.assertEqual(out['reason'], app.REASON_PENDING)
        self.assertEqual(a.pending_threads(), [r['body']['id']])
        a.approve()
        self.assertEqual(len(a.snapshot()['effects']), 1)

    def test_approval_is_judged_at_resume_time(self):
        a = fresh(Graph); a.require_approval(); a.apply(a.request()); a.revoke(); a.approve()
        self.assertEqual(a.snapshot()['effects'], [])  # base refuses after revocation

    def test_pending_survives_reopen(self):
        a = fresh(Graph); a.require_approval(); a.apply(a.request()); a.reopen(); a.approve()
        self.assertEqual(len(a.snapshot()['effects']), 1)

    def test_release_returns_to_registered_behaviour(self):
        a = fresh(Graph); a.require_approval(); a.release_approval()
        self.assertEqual(a.apply(a.request())['status'], 'accepted')

    def test_hold_with_audit_outage_fails_loudly_and_leaves_nothing_pending(self):
        a = fresh(Graph); a.require_approval(); a.break_audit()
        with self.assertRaises(sqlite3.IntegrityError):
            a.apply(a.request())
        self.assertEqual(a.pending_threads(), [])
        self.assertEqual(a.snapshot()['effects'], [])

    def test_hook_is_used_when_the_base_has_one(self):
        SyntheticBaseWithHook.hook_calls = 0
        a = fresh(GraphHook); a.require_approval(); a.apply(a.request()); a.reject()
        self.assertEqual(SyntheticBaseWithHook.hook_calls, 2)

    def test_unauthenticated_hold_is_marked_unauthenticated(self):
        a = fresh(Graph); a.require_approval(); r = a.request(); r['signature'] = '00' * 64
        a.apply(r)
        self.assertIs(a.snapshot()['events'][-1]['command_authenticated'], False)


class WiringTests(unittest.TestCase):
    def test_effect_node_calls_the_configured_base(self):
        class Marked(SyntheticBase):
            def apply(self, request):
                return {'status': 'denied', 'reason': 'SENTINEL_BASE', 'result': {'duplicate': False}}
        G = app.make_wiki_langgraph_app(Marked)
        a = fresh(G)
        self.assertEqual(a.apply(a.request())['reason'], 'SENTINEL_BASE')
        a.require_approval(); a.apply(a.request()); a.approve()
        self.assertEqual(a.last_resolutions[0]['reason'], 'SENTINEL_BASE')


class AblationTests(unittest.TestCase):
    """Each graph-layer ablation must be detected by a property check (a pass is not vacuous)."""

    def test_every_ablation_has_a_test(self):
        self.assertEqual(set(app.GRAPH_MUTATIONS), {'graph_bypass_graph', 'graph_skip_hold',
                                                    'graph_reject_as_approve', 'graph_timeout_as_approve'})

    def test_bypass_is_detected_by_missing_graph_run(self):
        a = fresh(Graph, 'graph_bypass_graph'); r = a.request(); a.apply(r)
        self.assertNotIn(r['body']['id'], checkpoint_threads(a)
                         if (a.root / 'checkpoints.sqlite').exists() else set())

    def test_skip_hold_is_detected_by_effect_before_approval(self):
        a = fresh(Graph, 'graph_skip_hold'); a.require_approval(); a.apply(a.request())
        self.assertEqual(len(a.snapshot()['effects']), 1)  # healthy class gives 0 (see HoldTests)

    def test_reject_as_approve_is_detected_by_effect_after_reject(self):
        a = fresh(Graph, 'graph_reject_as_approve'); a.require_approval(); a.apply(a.request()); a.reject()
        self.assertEqual(len(a.snapshot()['effects']), 1)

    def test_timeout_as_approve_is_detected_by_effect_after_timeout(self):
        a = fresh(Graph, 'graph_timeout_as_approve'); a.require_approval(); a.apply(a.request()); a.timeout()
        self.assertEqual(len(a.snapshot()['effects']), 1)


class UnchangedOracleTests(unittest.TestCase):
    """Drive the graph class over the SYNTHETIC base through the unchanged pinned runner functions."""

    @classmethod
    def setUpClass(cls):
        cls.runner = _base.pinned_runner()
        cls.runner.ADAPTERS = {'synthetic-graph': Graph}

    def case(self, steps, statuses, effects):
        return dict(id='synthetic-graph', steps=steps, expected_statuses=statuses, expected_effects=effects,
                    allowed_effect_ids=['effect'], expected_payload='synthetic-graph')

    def run_case(self, case):
        COUNTER[0] += 1
        return self.runner.run_case(Graph, case, Path(TMP.name) / ('oracle-%d' % COUNTER[0]), 'opa-unused')

    def test_accept_case_scores_pass(self):
        row = self.run_case(self.case([{'action': 'execute'}], ['accepted'], 1))
        self.assertTrue(row['pass_case'])

    def test_hold_case_scores_pass_with_durable_denials(self):
        row = self.run_case(self.case([{'action': 'require_approval'}, {'action': 'execute'},
                                       {'action': 'reject'}], ['denied'], 0))
        self.assertTrue(row['pass_case'], row)
        self.assertEqual((row['denied_calls'], row['durably_recorded_denials']), (1, 1))

    def test_hold_then_approve_scores_pass(self):
        row = self.run_case(self.case([{'action': 'require_approval'}, {'action': 'execute'},
                                       {'action': 'approve'}], ['denied'], 1))
        self.assertTrue(row['pass_case'], row)

    def test_audit_outage_maps_to_unavailable(self):
        row = self.run_case(self.case([{'action': 'break_audit'}, {'action': 'execute'}], ['unavailable'], 0))
        self.assertTrue(row['pass_case'], row)

    def test_ablation_changes_the_verdict(self):
        COUNTER[0] += 1
        steps = [{'action': 'require_approval'}, {'action': 'execute'}, {'action': 'reject'}]
        row = self.runner.run_case(Graph, self.case(steps, ['denied'], 0), Path(TMP.name) / ('oracle-%d' % COUNTER[0]),
                                   'opa-unused', 'graph_reject_as_approve')
        self.assertFalse(row['pass_case'])


if __name__ == '__main__':
    unittest.main()
