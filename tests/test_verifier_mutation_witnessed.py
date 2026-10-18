"""Proof of the witnessed population of the mutation harness (catalogue version 3, family H) with stub verifiers.

The stubs are not verifiers. They show that the harness counts family H the way the ODES verification-report contract says (decision
28): H1 to H6 expected reject, H7 and H8 expected abstain, B and F expected accept; the witnessed population is its own corpus with its
own clean corpus, never pooled with the unwitnessed one; a stub that accepts everything shows no family H detection and is flagged; one
that rejects everything shows witnessed clean false rejection and is flagged. Also: the witness operators are deterministic and break
what they claim (checked with the harness's own re-derivation of the witness profile), catalogue version 3 leaves every version 2 mutant
byte-identical, and the witnessed clean corpus is the committed output of `acp witness publish`. No verifier or network is needed.
SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import functools
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'suites' / 'verifier-mutation'
sys.path.insert(0, str(SUITE))
sys.path.insert(0, str(ROOT / 'tests'))
from verifier_mutation import cli, contract, corpus, jsonio, operators, report, runner  # noqa: E402
from verifier_mutation import witness_operators as wo  # noqa: E402
from verifier_mutation.trace import ABSENT_FILE, FILENAMES, load_clean_corpus  # noqa: E402
import test_verifier_mutation_harness as base  # noqa: E402

ODES = contract.load()
V3_OPERATOR_SET_DIGEST = 'sha256:86e4b43449acdf7976aaf3d091d33c2d5b4636f5e64fe3a4d22c4d8f23b9d00c'  # operators.json of catalogue 3 (qualification ce684ec6), the set run 4 used
RUN4_ODES = '296e6bce26d5d68bae402eebca188a3f362b2963'  # run 4's own ODES revision (the vendored validator has moved on)
WMANIFEST, WTRACES = load_clean_corpus(SUITE / 'corpus' / 'witnessed')
WBY = {t.trace_id: t for t in WTRACES}
OPERATOR_SET = json.loads((SUITE / 'operators.json').read_text(encoding='utf-8'))
WMAP = json.loads((SUITE / 'witness-seed-map.json').read_text(encoding='utf-8'))
TINY_W = [WBY[i] for i in ('acp-run-authorized', 'holder-inventory-applied', 'journal-applied', 'journal-lost-ack-closeout')]
OPS = {o.operator_id: o for o in wo.WITNESS_OPERATORS}


def records(data):
    return [json.loads(x) for x in data.decode('utf-8').splitlines() if x.strip()]


def chain_ok(rs):
    prev = None
    for i, r in enumerate(rs):
        if r['sequence'] != i or r['previous_digest'] != prev or r['digest'] != jsonio.commitment({k: v for k, v in r.items() if k != 'digest'}):
            return False
        prev = r['digest']
    return True


def mutate(trace_id, operator_id, seed=5, draw=0):
    t = WBY[trace_id]
    ctx = operators.Ctx(trace=t, rng=operators.rng_for(seed, t.trace_id, operator_id, draw), peers=[p for p in WTRACES if p.trace_id != trace_id])
    OPS[operator_id].fn(ctx)
    return operators.build_files(t, ctx)


class FakeRunner(base.FakeRunner):
    """The unwitnessed fake runner plus the witness and inventory roles (an absent witness file is passed as a missing path)."""

    def verify(self, files):
        self.calls += 1
        with tempfile.TemporaryDirectory() as tmp:
            argv = ['--mode', self.mode]
            for role, flag in (('run_record', '--run-record'), ('proposal_export', '--proposal'), ('destination_ledger', '--ledger'),
                               ('witness', '--witness'), ('holder_inventory', '--holder-inventory')):
                if role in files:
                    p = Path(tmp) / FILENAMES[role]
                    if files[role] != ABSENT_FILE:
                        p.write_bytes(files[role])
                    argv += [flag, str(p)]
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = base.stub.main(argv)
            if code == 2 and not out.getvalue().strip():  # what the real Runner reports for an input error: exit 2, no report
                return runner.Outcome('error', detail='exit 2, no report: input error')
            if self.mode == 'crash' or code != 0:
                return runner.Outcome('error', detail='crash or input error')
            return runner.reduce_report(out.getvalue().encode(), ODES)


def run_both(mode, wtraces=TINY_W, draws=1, wseeds=None, controls=()):
    r = FakeRunner(mode)
    slots, dropped = corpus.generate(base.TINY, 7, draws)
    run = report.execute(r, base.TINY, slots, None)
    wslots, wdropped = corpus.generate(wtraces, 7, draws, operators=wo.WITNESS_OPERATORS)
    wrun = report.execute(r, wtraces, wslots, wseeds)
    ctl = [(s, o) for s, o in wrun.seed_invalid if s.seed_id in controls]
    data = (SUITE / 'operators.json').read_bytes()
    doc = report.build(run, traces=base.TINY, slots=slots, duplicates_dropped=dropped, seeds=None, clean_manifest=base.MANIFEST, operator_set_bytes=data,
                       operator_set_digest=jsonio.digest(data), seed=7, draws=draws, frozen_revision='test', generated_at='2026-10-18T00:00:00+00:00',
                       command=f'stub --mode {mode}', witnessed=report.Witnessed(wrun, wtraces, wslots, wdropped, WMANIFEST, wseeds, ctl))
    return wrun, doc


def corpus_by_id(doc, cid):
    mr = doc['mutation_report']
    return next(c for c in mr['family_t'] + mr['clean'] if c['corpus_id'] == cid)


def wrow(doc, cat):
    return next(r for r in corpus_by_id(doc, 't-generated-witnessed')['categories'] if r['category'] == cat)


def wflags(doc):
    return {f['id'] for f in doc['mutation_report']['extensions']['x-qualification-harness']['witnessed']['flags']}


@functools.lru_cache(maxsize=None)
def witnessed_slots(seed, draws):
    return corpus.generate(WTRACES, seed, draws, operators=wo.WITNESS_OPERATORS)


class WitnessOperators(unittest.TestCase):
    def test_categories_expected_verdicts_and_intended_codes(self):
        self.assertEqual(wo.witness_categories(), ['B', 'F', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8'])
        ids = [o.operator_id for o in wo.WITNESS_OPERATORS] + [o.operator_id for o in operators.OPERATORS]
        self.assertEqual(len(ids), len(set(ids)))
        names = set(json.loads((SUITE / 'verifier-code-names.json').read_text())['names'])
        for o in wo.WITNESS_OPERATORS:
            with self.subTest(operator=o.operator_id):
                want = {'H7': 'abstain', 'H8': 'abstain', 'B': 'accept', 'F': 'accept'}.get(o.category, 'reject')
                self.assertEqual(o.expected_verdict, want)
                self.assertEqual(bool(o.intended_codes), want == 'reject')
                self.assertTrue(set(o.intended_codes) <= names, sorted(set(o.intended_codes) - names))
        per = {c: sum(1 for o in wo.WITNESS_OPERATORS if o.category == c) for c in wo.witness_categories()}
        self.assertTrue(all(n >= 3 for n in per.values()), per)  # several variants per category

    def test_operator_set_is_catalogue_v3_labelled_post_hoc_and_keeps_v2(self):
        self.assertEqual(OPERATOR_SET['operator_version'], '3.1')
        self.assertEqual(OPERATOR_SET['revises']['operator_set_digest'], V3_OPERATOR_SET_DIGEST)  # catalogue 3 as run 4 measured it
        by = {o['operator_id']: o for o in OPERATOR_SET['witnessed_operators']}
        self.assertEqual({k for k, o in by.items() if o['expected_outcome'] == 'input_error'}, {'H8.witness-file-absent'})  # decision 30-A
        self.assertEqual(by['H8.witness-file-absent']['expected_verdict'], 'abstain')  # the report contract has no row-level input_error
        self.assertEqual(by['H8.witness-empty-file']['expected_outcome'], 'abstain')
        self.assertEqual(len(OPERATOR_SET['operators']), 81)  # the version 2 operators, unchanged
        self.assertEqual(len(OPERATOR_SET['witnessed_operators']), len(wo.WITNESS_OPERATORS))
        self.assertEqual(OPERATOR_SET['expected_abstain_categories'], ['H7', 'H8'])
        self.assertIn("written after the verifier's tier V3 existed", OPERATOR_SET['intended_codes']['status'])
        self.assertIn('not held-out', OPERATOR_SET['intended_codes']['status'])
        self.assertIn('witness_operators.py', OPERATOR_SET['implementation_sha256'])
        self.assertEqual(cli.operator_set_bytes(cli.operator_set_doc(OPERATOR_SET['seed'], OPERATOR_SET['draws_per_variant'])), (SUITE / 'operators.json').read_bytes())

    def test_catalogue_v3_leaves_every_version_2_mutant_byte_identical(self):
        slots, _ = base.full(OPERATOR_SET['seed'], OPERATOR_SET['draws_per_variant'])
        run3 = json.loads((ROOT / 'results' / 'verifier-mutation' / 'run-3-adb8927' / 'mutation-report.json').read_text())
        want = next(i['digest'] for i in run3['subject']['inputs'] if i['name'] == 'generated-mutants')
        self.assertEqual(corpus.mutant_set_digest(slots), want)

    def test_deterministic_under_a_seed(self):
        a, _ = corpus.generate(TINY_W, 11, 2, operators=wo.WITNESS_OPERATORS)
        b, _ = corpus.generate(TINY_W, 11, 2, operators=wo.WITNESS_OPERATORS)
        c, _ = corpus.generate(TINY_W, 12, 2, operators=wo.WITNESS_OPERATORS)
        self.assertEqual(corpus.mutant_set_digest(a), corpus.mutant_set_digest(b))
        self.assertNotEqual(corpus.mutant_set_digest(a), corpus.mutant_set_digest(c))

    def test_every_category_has_effective_mutants_on_the_frozen_corpus(self):
        slots, _ = witnessed_slots(OPERATOR_SET['seed'], OPERATOR_SET['draws_per_variant'])
        eff = {s.category for s in slots if s.status == 'effective'}
        self.assertEqual(eff, set(wo.witness_categories()))

    def test_chain_and_link_operators_break_only_the_chain(self):
        for op in ('H1.previous-digest-relinked', 'H1.sequence-shifted', 'H1.first-record-gains-previous-digest'):
            rs = records(mutate('journal-lost-ack-closeout', op)['witness'])
            self.assertFalse(chain_ok(rs), op)
            for r in rs:  # each record's own digest still recomputes: only the link or the index is wrong
                self.assertEqual(r['digest'], jsonio.commitment({k: v for k, v in r.items() if k != 'digest'}), op)
        dup = records(mutate('journal-applied', 'H1.digest-line-duplicated')['witness'])
        self.assertEqual(len(dup), 3)
        self.assertTrue(any(dup[i] == dup[i + 1] for i in range(2)))

    def test_run_id_operators_keep_a_consistent_chain_for_another_run(self):
        for op in ('H2.run-id-rewritten-rechained', 'H2.run-id-case-changed', 'H2.run-id-trailing-space', 'H2.run-id-lookalike-hyphen'):
            files = mutate('journal-applied', op)
            rs = records(files['witness'])
            self.assertTrue(chain_ok(rs), op)
            self.assertNotEqual({r['run_id'] for r in rs}, {json.loads(files['run_record'])['run_id']}, op)

    def test_shrink_rewrite_and_coverage_operators_against_the_harness_rederivation(self):
        t = WBY['journal-applied']
        latest = records(t.files['witness'])[-1]['ledgers']
        self.assertEqual(wo.head_digest(json.loads(t.files['run_record'])), latest)  # clean: the witness covers every row
        shrunk = json.loads(mutate('journal-applied', 'H4.covered-row-dropped-tail')['run_record'])
        self.assertTrue(any(len(shrunk.get(n, [])) < e['count'] for n, e in latest.items()))
        self.assertEqual(mutate('journal-applied', 'H4.covered-row-dropped-tail')['witness'], t.files['witness'])
        swapped = json.loads(mutate('journal-applied', 'H5.covered-rows-swapped')['run_record'])
        heads = wo.head_digest(swapped, {n: e['count'] for n, e in latest.items()})
        self.assertEqual({n: e['count'] for n, e in heads.items()}, {n: e['count'] for n, e in latest.items()})
        self.assertNotEqual(heads, latest)
        for op in ('H7.witness-remade-over-prefix', 'H7.witness-omits-a-ledger', 'H7.witness-count-lowered-head-recomputed', 'H7.witness-tail-truncated'):
            files = mutate('journal-lost-ack-closeout', op)
            self.assertEqual(files['run_record'], WBY['journal-lost-ack-closeout'].files['run_record'], op)  # the record is untouched
            rs = records(files['witness'])
            self.assertTrue(chain_ok(rs), op)
            doc = json.loads(files['run_record'])
            for r in rs:  # every held head is right for its prefix ...
                self.assertEqual(wo.head_digest(doc, {n: e['count'] for n, e in r['ledgers'].items()}), r['ledgers'], op)
            # ... and some row is not covered by the latest record
            self.assertTrue(any(len(rows) > rs[-1]['ledgers'].get(n, {}).get('count', 0) for n, rows in wo.ledgers(doc).items()), op)

    def test_rolled_back_record_is_the_earlier_snapshot(self):
        files = mutate('journal-applied', 'H4.record-rolled-back')
        self.assertEqual(files['run_record'], WBY['journal-applied'].extra['earlier_run_record'])
        self.assertEqual(files['witness'], WBY['journal-applied'].files['witness'])

    def test_destination_drop_touches_only_the_destination_ledger(self):
        t = WBY['journal-lost-ack-unobserved']
        files = mutate('journal-lost-ack-unobserved', 'H4.destination-row-dropped-uncorroborated')
        self.assertEqual(files['run_record'], t.files['run_record'])
        self.assertEqual(files['witness'], t.files['witness'])
        self.assertEqual(json.loads(files['destination_ledger'])['effects'], {})

    def test_forgery_bound_operators_are_self_consistent(self):
        files = mutate('journal-applied', 'F.reseal-amount-and-rewitness')
        rs = records(files['witness'])
        self.assertTrue(chain_ok(rs))
        self.assertEqual(wo.head_digest(json.loads(files['run_record'])), rs[-1]['ledgers'])
        self.assertNotEqual(files['run_record'], WBY['journal-applied'].files['run_record'])
        extended = mutate('journal-lost-ack-closeout', 'F.witness-history-extended')
        rs = records(extended['witness'])
        self.assertEqual(len(rs), 4)
        self.assertTrue(chain_ok(rs))
        doc = json.loads(extended['run_record'])
        for r in rs:
            self.assertEqual(wo.head_digest(doc, {n: e['count'] for n, e in r['ledgers'].items()}), r['ledgers'])
        collapsed = records(mutate('journal-lost-ack-closeout', 'F.witness-history-collapsed')['witness'])
        self.assertEqual(len(collapsed), 1)
        self.assertTrue(chain_ok(collapsed))

    def test_benign_witness_forms_hold_the_same_records(self):
        clean = records(WBY['journal-applied'].files['witness'])
        for op in ('B.witness-keys-reordered', 'B.witness-spaced-separators', 'B.witness-crlf', 'B.witness-no-final-newline',
                   'B.witness-blank-line-between-records', 'B.witness-escaped-ascii'):
            files = mutate('journal-applied', op)
            self.assertNotEqual(files['witness'], WBY['journal-applied'].files['witness'], op)
            self.assertEqual(records(files['witness']), clean, op)

    def test_controls_and_inventory_operators(self):
        self.assertEqual(mutate('journal-applied', 'H8.witness-empty-file')['witness'], b'')
        self.assertEqual(mutate('journal-applied', 'H8.witness-file-absent')['witness'], ABSENT_FILE)
        slots, _ = witnessed_slots(OPERATOR_SET['seed'], OPERATOR_SET['draws_per_variant'])
        for v in ('duplicated', 'dropped', 'added'):
            mine = [s for s in slots if s.operator_id == f'H6.holder-{v}-against-record-reference']
            self.assertEqual({s.status for s in mine}, {'na'})  # the record never names an inventory (holder-inventory non-claim)
            self.assertTrue(any('names no inventory' in s.reason for s in mine))
        inv = json.loads(mutate('holder-inventory-applied', 'H6.kind-lifecycle-value')['holder_inventory'])
        self.assertTrue(any(h['kind'] in ('expired', 'revoked', 'lapsed') for h in inv['holders']))


class WitnessedCorpus(unittest.TestCase):
    def test_matches_its_manifest_and_pins_the_same_controller(self):
        self.assertEqual(len(WTRACES), 17)
        self.assertEqual(WMANIFEST['kind'], 'verifier-mutation-witnessed-clean-corpus')
        self.assertEqual(WMANIFEST['control_plane_revision'], base.MANIFEST['control_plane_revision'])
        self.assertEqual(WMANIFEST['reason_registry_digest'], base.MANIFEST['reason_registry_digest'])
        self.assertIn('acp witness publish', WMANIFEST['witness_producer'])
        for t in WTRACES:
            self.assertTrue({'run_record', 'witness', 'proposal_export', 'manifest', 'destination_ledger'} <= set(t.files), t.trace_id)
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            shutil.copytree(SUITE / 'corpus' / 'witnessed', Path(tmp) / 'w')
            (Path(tmp) / 'w' / 'journal-applied' / FILENAMES['witness']).write_bytes(b'')
            with self.assertRaises(ValueError):
                load_clean_corpus(Path(tmp) / 'w')

    def test_every_witness_is_producer_output_that_covers_its_record(self):
        multi = 0
        for t in WTRACES:
            with self.subTest(trace=t.trace_id):
                rs = records(t.files['witness'])
                self.assertTrue(chain_ok(rs))
                self.assertEqual(t.files['witness'], b''.join(wo._line(r) for r in rs))  # sorted compact JSON lines, as the producer writes
                self.assertEqual(wo.head_digest(json.loads(t.files['run_record'])), rs[-1]['ledgers'])  # the final publication covers every row
                multi += len(rs) > 1
                meta = json.loads((SUITE / 'corpus' / 'witnessed' / t.trace_id / 'scenario.json').read_text())
                self.assertEqual(len(meta['publications']), len(rs))
        self.assertEqual(multi, 8)  # the staged test-helper flows; the acp run traces are published once
        self.assertEqual(sum(1 for t in WTRACES if 'holder_inventory' in t.files), 2)


class WitnessedHarness(unittest.TestCase):
    def test_report_validates_and_keeps_the_witnessed_population_apart(self):
        _, doc = run_both('partial')
        self.assertEqual(ODES.validate(doc), [])
        mr = doc['mutation_report']
        self.assertEqual([c['corpus_id'] for c in mr['family_t']], ['t-generated', 't-generated-witnessed'])
        self.assertEqual([c['corpus_id'] for c in mr['clean']], ['clean-generated', 'clean-generated-witnessed'])
        w = corpus_by_id(doc, 't-generated-witnessed')
        self.assertTrue({r['category'] for r in w['categories']} <= {'B', 'F', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8'})
        self.assertFalse(any(r['category'].startswith('H') for r in corpus_by_id(doc, 't-generated')['categories']))
        for sc in w['scenarios']:
            self.assertTrue({r['category'] for r in sc['categories']} <= {'B', 'F', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8'})
        self.assertEqual(wrow(doc, 'H7')['expected_verdict'], 'abstain')
        self.assertEqual(wrow(doc, 'H8')['expected_verdict'], 'abstain')
        self.assertIn('witness_is_not_publication', {n['id'] for n in doc['does_not_prove']})
        self.assertIn('V3', doc['scope']['tiers_run'])
        self.assertTrue({'witness', 'holder_inventory'} <= {i['role'] for i in doc['subject']['inputs']})

    def test_no_pooling_is_enforced_by_the_validator(self):
        _, doc = run_both('partial')
        mixed = json.loads(json.dumps(doc))
        w = corpus_by_id(mixed, 't-generated-witnessed')
        w['categories'].append(json.loads(json.dumps(next(r for r in corpus_by_id(mixed, 't-generated')['categories'] if r['category'] == 'W1'))))
        self.assertIn('witnessed_corpus_mixed', {v.code for v in ODES.validate(mixed)})
        missing = json.loads(json.dumps(doc))
        missing['mutation_report']['clean'] = [c for c in missing['mutation_report']['clean'] if c['corpus_id'] != 'clean-generated-witnessed']
        self.assertIn('witnessed_clean_corpus_missing', {v.code for v in ODES.validate(missing)})
        # the unwitnessed and witnessed clean tables never share a denominator
        self.assertEqual(corpus_by_id(doc, 'clean-generated')['rows'][0]['false_rejection']['n'] <= len(base.TINY), True)
        self.assertTrue(all(r['false_rejection']['n'] <= len(TINY_W) for r in corpus_by_id(doc, 'clean-generated-witnessed')['rows'] if r['category'] != 'B'))

    def test_accept_everything_shows_no_family_h_detection_and_is_flagged(self):
        _, doc = run_both('accept')
        self.assertEqual(ODES.validate(doc), [])
        self.assertIn('witnessed_no_family_h_detection', wflags(doc))
        for cat in ('H1', 'H2', 'H3', 'H4', 'H5', 'H6'):
            r = wrow(doc, cat)
            self.assertEqual(r['detection']['any_code']['k'], 0, cat)
            self.assertEqual(r['false_acceptance']['k'], r['n_eff'], cat)
        h7 = wrow(doc, 'H7')
        self.assertEqual(h7['false_acceptance'], {'k': h7['n_eff'], 'n': h7['n_eff']})  # a confirmed control is a false acceptance
        self.assertTrue(all(r['false_rejection']['k'] == 0 for r in corpus_by_id(doc, 'clean-generated-witnessed')['rows']))

    def test_reject_everything_shows_witnessed_clean_false_rejection_and_is_flagged(self):
        _, doc = run_both('reject')
        self.assertEqual(ODES.validate(doc), [])
        self.assertIn('witnessed_rejects_every_clean_trace', wflags(doc))
        rows = corpus_by_id(doc, 'clean-generated-witnessed')['rows']
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r['false_rejection']['k'], r['false_rejection']['n'], r['category'])
        h7 = wrow(doc, 'H7')
        self.assertEqual(h7['verdicts']['reject'], h7['n_eff'])  # a rejected control: shown as reject, not credited as abstain

    def test_abstain_on_the_controls(self):
        _, doc = run_both('abstain')
        self.assertEqual(ODES.validate(doc), [])
        h7, h8 = wrow(doc, 'H7'), wrow(doc, 'H8')
        self.assertEqual(h7['abstained'], {'k': h7['n_eff'], 'n': h7['n_eff']})
        # the absent-file variant is an input error for the stub (exit 2, no report): error, never abstain or detection
        absent = sum(1 for t in TINY_W)  # one effective slot per trace at draws=1
        self.assertEqual((h8['verdicts']['abstain'], h8['verdicts']['error']), (h8['n_eff'] - absent, absent))
        self.assertNotIn('witnessed_errors_present', wflags(doc))  # an expected input error (exit 2, no report) is not a runtime error
        self.assertNotIn('witnessed_controls_never_abstain', wflags(doc))
        ctl = doc['mutation_report']['extensions']['x-qualification-harness']['witnessed']['input_error_controls']
        self.assertEqual(ctl, [{'operator_id': 'H8.witness-file-absent', 'expected_outcome': 'input_error', 'n_eff': absent, 'exit_2_no_report': absent, 'other': []}])

    def test_an_input_error_control_that_crashes_instead_is_still_an_error(self):
        slot = corpus.Slot(mutant_id='t:H8.witness-file-absent:0', trace_id='t', scenario='s', operator_id='H8.witness-file-absent', category='H8', draw=0,
                           status='effective', expected_verdict='abstain', expected_outcome='input_error')
        met = report.Result(slot, runner.Outcome('error', detail='exit 2, no report: x'))
        crashed = report.Result(slot, runner.Outcome('error', detail='timed out after 60s'))
        accepted = report.Result(slot, runner.Outcome('accept'))
        self.assertEqual([report._input_error_met(r) for r in (met, crashed, accepted)], [True, False, False])
        self.assertEqual(report.input_error_controls(report.Run(results=[met, crashed, accepted])),
                         [{'operator_id': 'H8.witness-file-absent', 'expected_outcome': 'input_error', 'n_eff': 3, 'exit_2_no_report': 1,
                           'other': ['t:H8.witness-file-absent:0 -> accept', 't:H8.witness-file-absent:0 -> error']}])

    def test_the_real_runner_reports_an_input_error_with_the_detail_the_control_expects(self):
        import inspect
        self.assertIn('f"exit {done.returncode}, no report: "', inspect.getsource(runner.Runner.verify))
        self.assertEqual(report.INPUT_ERROR_DETAIL, 'exit 2, no report')

    def test_a_narrow_witness_check_separates_controls_from_damage(self):
        _, doc = run_both('witness')
        self.assertEqual(ODES.validate(doc), [])
        self.assertEqual(corpus_by_id(doc, 'clean-generated-witnessed')['rows'][0]['false_rejection']['k'], 0)
        h8 = wrow(doc, 'H8')
        self.assertEqual(h8['verdicts']['abstain'] + h8['verdicts']['error'], h8['n_eff'])
        h2 = wrow(doc, 'H2')
        self.assertGreater(h2['detection']['any_code']['k'], 0)
        self.assertGreater(wrow(doc, 'H2')['detection']['intended_code']['k'], 0)  # the stub's witness_run_mismatch is an intended code
        b = wrow(doc, 'B')
        self.assertEqual(b['verdicts']['reject'], 0)

    def test_report_is_byte_identical_for_a_fixed_seed(self):
        self.assertEqual(json.dumps(run_both('witness')[1]), json.dumps(run_both('witness')[1]))


def mini_witness_odes(directory):
    """A tiny stand-in for the ODES witness-digest and holder-inventory fixtures, built from one witnessed trace."""
    t = WBY['holder-inventory-applied']
    rec, wit, inv = json.loads(t.files['run_record']), records(t.files['witness']), json.loads(t.files['holder_inventory'])

    def put(contract_name, kind, name, document, refusal=None, record=None):
        d = Path(directory) / 'contracts' / contract_name / 'fixtures' / kind
        d.mkdir(parents=True, exist_ok=True)
        fx = {'fixture_id': name, 'synthetic': True, 'expected_outcome': kind, 'reason': 'x', 'expected_refusal': refusal, 'document': document}
        if record is not None:
            fx['record'] = record
        (d / f'{name}.json').write_text(json.dumps(fx), encoding='utf-8')
    put('witness-digest', 'valid', WMAP['carrier']['witness-digest'], wit, record=rec)
    put('witness-digest', 'valid', WMAP['carrier']['holder-inventory'], wit, record=rec)
    bad = json.loads(json.dumps(wit))
    bad[-1]['previous_digest'] = 'sha256:' + '1' * 64
    put('witness-digest', 'invalid', 'previous-digest-does-not-link', bad, 'witness_chain_invalid')
    put('witness-digest', 'invalid', 'empty-witness-file', [], 'witness_holds_no_digest')
    put('witness-digest', 'invalid', 'something-new', wit[:1], 'some_rule_nobody_classified')
    put('holder-inventory', 'valid', 'two-holders', inv)
    put('holder-inventory', 'invalid', 'kind-expired', {**inv, 'holders': [{**inv['holders'][0], 'kind': 'expired'}]}, 'unknown_enum_value')


class WitnessSeeds(unittest.TestCase):
    def test_seeds_are_classified_carried_and_reported_as_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            mini_witness_odes(tmp)
            seeds = corpus.load_witness_seed_corpus(Path(tmp), WMAP, 'abc')
        self.assertEqual(sorted((s.seed_id, s.category) for s in seeds.invalid),
                         [('holder-inventory/kind-expired', 'H6'), ('witness-digest/empty-witness-file', None),
                          ('witness-digest/previous-digest-does-not-link', 'H1'), ('witness-digest/something-new', None)])
        inv_seed = next(s for s in seeds.invalid if s.contract == 'holder-inventory')
        self.assertEqual(set(inv_seed.files), {'run_record', 'witness', 'holder_inventory'})
        self.assertIn('holder_inventory_shape', inv_seed.intended_codes)
        self.assertEqual(seeds.invalid[0].files['witness'].count(b'\n') >= 0, True)
        _, doc = run_both('witness', wseeds=seeds, controls=tuple(WMAP['unclassified_on_purpose']))
        self.assertEqual(ODES.validate(doc), [])
        seed = corpus_by_id(doc, 't-seed-odes-witness')
        self.assertEqual(seed['provenance'], 'seed')
        self.assertEqual(sorted(r['category'] for r in seed['categories']), ['H1', 'H6'])
        for r in seed['categories']:
            self.assertIsNone(r['detection'])
        self.assertEqual(corpus_by_id(doc, 'clean-odes-witness-valid')['provenance'], 'seed_valid_fixtures')
        w = doc['mutation_report']['extensions']['x-qualification-harness']['witnessed']
        self.assertEqual(w['seed_corpus']['unclassified'], 2)
        self.assertEqual([c['seed_id'] for c in w['seed_controls']], ['witness-digest/empty-witness-file'])
        self.assertEqual(w['seed_controls'][0]['observed_verdict'], 'abstain')

    def test_unwitnessed_seed_digests_are_unchanged_by_the_witness_seed_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            base.mini_odes(tmp)
            seeds = corpus.load_seed_corpus(Path(tmp), corpus.load_seed_map(SUITE / 'seed-map.json'), 'abc')
        entries = [{"seed_id": s.seed_id, "category": s.category, "expected_refusal": s.expected_code, "sha256": jsonio.digest(s.files["run_record"])}
                   for s in sorted(seeds.invalid, key=lambda x: x.seed_id)]
        self.assertEqual(seeds.digests()[0][0], jsonio.commitment(entries))


class RetainedRun4(unittest.TestCase):
    """The retained run 4 report (verifier 5974c50, ODES 296e6bce, catalogue v3): it validates, names its pins, keeps the populations apart."""

    DIR = ROOT / 'results' / 'verifier-mutation' / 'run-4-5974c50'

    def test_validates_and_names_its_pins(self):
        doc = json.loads((self.DIR / 'mutation-report.json').read_text())
        self.assertEqual(ODES.validate(doc), [])
        mr = doc['mutation_report']
        h = mr['extensions']['x-qualification-harness']
        contract_doc = json.loads((SUITE / 'contract' / 'verification-report' / 'CONTRACT.json').read_text())
        self.assertEqual(doc['verifier']['source_revision'], '5974c505e8b01b529fe1852c5b5deefe78a1c677')
        self.assertEqual(h['seed_corpus']['odes_revision'], RUN4_ODES)
        self.assertEqual(h['witnessed']['seed_corpus']['odes_revision'], RUN4_ODES)
        self.assertEqual(contract_doc['odes_commit'], '0a37180fb09af596a1d134e38b316307e12fb424')  # re-vendored after run 4; run 4 still validates
        self.assertEqual(mr['operator_set_digest'], V3_OPERATOR_SET_DIGEST)  # catalogue 3, not re-labelled: the current operators.json is 3.1
        self.assertNotEqual(mr['operator_set_digest'], jsonio.digest((SUITE / 'operators.json').read_bytes()))
        self.assertEqual(h['operator_version'], '3')
        self.assertEqual(h['clean_traces'], {'n': 19, 'verdicts': {'reject': 0, 'accept': 19, 'abstain': 0, 'error': 0}})
        self.assertEqual(h['witnessed']['clean_traces'], {'n': 17, 'verdicts': {'reject': 0, 'accept': 17, 'abstain': 0, 'error': 0}})
        self.assertIn('witness_is_not_publication', {n['id'] for n in doc['does_not_prove']})
        clean_w = next(c for c in mr['clean'] if c['corpus_id'] == 'clean-generated-witnessed')
        self.assertTrue(all(r['false_rejection']['k'] == 0 for r in clean_w['rows']))

    def test_unwitnessed_rows_equal_run_3(self):
        a = json.loads((ROOT / 'results' / 'verifier-mutation' / 'run-3-adb8927' / 'mutation-report.json').read_text())['mutation_report']
        b = json.loads((self.DIR / 'mutation-report.json').read_text())['mutation_report']
        pick = lambda m, cid: next(c for c in m['family_t'] + m['clean'] if c['corpus_id'] == cid)
        self.assertEqual(pick(a, 't-generated'), pick(b, 't-generated'))
        self.assertEqual(pick(a, 'clean-generated'), pick(b, 'clean-generated'))

    def test_the_misses_are_the_ones_the_readme_lists(self):
        ops = {o['operator_id']: o for o in json.loads((self.DIR / 'per-operator.json').read_text())['operators'] if o['population'] == 'witnessed'}
        missed = {k: o['verdicts'] for k, o in ops.items() if o['not_rejected']}
        self.assertEqual(missed, {'H4.destination-row-dropped-uncorroborated': {'reject': 0, 'accept': 1, 'abstain': 0, 'error': 0},
                                  'H4.ledger-removed': {'reject': 19, 'accept': 0, 'abstain': 12, 'error': 0}})
        self.assertEqual(ops['H8.witness-file-absent']['verdicts'], {'reject': 0, 'accept': 0, 'abstain': 0, 'error': 17})


if __name__ == '__main__':
    unittest.main()
