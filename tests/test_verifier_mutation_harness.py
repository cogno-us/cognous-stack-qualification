"""Proof of the trace-mutation harness (design stage S5, family T) with stub verifiers.

The stubs are not verifiers. They exist to show that the harness counts what it should: a stub that accepts everything shows no
detection and is flagged; one that rejects everything shows clean false rejection and is flagged; a crash is an error and never a
detection; the operators are deterministic under a seed; every report the harness emits validates against the ODES
``verification-report`` contract (vendored under suites/verifier-mutation/contract). No verifier, component, controller or network is
needed, and the clean corpus is a committed snapshot of real `acp run` and test-helper output.
SPDX-License-Identifier: Apache-2.0
"""
import ast
import contextlib
import functools
import hashlib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'suites' / 'verifier-mutation'
sys.path.insert(0, str(SUITE))
from verifier_mutation import cli, contract, corpus, jsonio, operators, report, runner  # noqa: E402
from verifier_mutation.trace import FILENAMES, MEASURES, load_clean_corpus, measures  # noqa: E402

STUB_PATH = SUITE / 'stubs' / 'stub_verifier.py'
spec = importlib.util.spec_from_file_location('stub_verifier', STUB_PATH)
stub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stub)
ODES = contract.load()
MANIFEST, TRACES = load_clean_corpus(SUITE / 'corpus' / 'clean')
BY_ID = {t.trace_id: t for t in TRACES}
OPERATOR_SET = json.loads((SUITE / 'operators.json').read_text(encoding='utf-8'))
@functools.lru_cache(maxsize=None)
def full(seed, draws):
    return corpus.generate(TRACES, seed, draws)


UNWITNESSED_ROLES = {'run_record', 'proposal_export', 'manifest', 'destination_ledger'}
V2_OPERATOR_SET_DIGEST = 'sha256:0c2b6730560e53c2f6cb7670bd2ccaf3fab70e33e3e3330a31cb0d226fb65629'
TINY = [BY_ID[i] for i in ('default-applied', 'default-held', 'journal-lost-ack', 'acp-run-authorized')]


class FakeRunner:
    """In-process stand-in for runner.Runner: runs the stub's main() on files in a temp directory (no process is spawned)."""

    def __init__(self, mode):
        self.mode, self.calls = mode, 0

    def verify(self, files):
        self.calls += 1
        with tempfile.TemporaryDirectory() as tmp:
            argv = ['--mode', self.mode]
            for role, flag in (('run_record', '--run-record'), ('proposal_export', '--proposal'), ('destination_ledger', '--ledger')):
                if role in files:
                    p = Path(tmp) / FILENAMES[role]
                    p.write_bytes(files[role])
                    argv += [flag, str(p)]
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = stub.main(argv)
            if self.mode == 'crash' or code != 0:
                return runner.Outcome('error', detail='crash')
            return runner.reduce_report(out.getvalue().encode(), ODES)


def mini_odes(directory):
    """A tiny stand-in for an ODES checkout: two invalid fixtures (one classified, one not) and two valid ones."""
    def put(contract_name, kind, name, document, refusal=None):
        d = Path(directory) / 'contracts' / contract_name / 'fixtures' / kind
        d.mkdir(parents=True, exist_ok=True)
        (d / f'{name}.json').write_text(json.dumps({'fixture_id': name, 'synthetic': True, 'expected_outcome': kind, 'reason': 'x',
                                                    'expected_refusal': refusal, 'document': document}), encoding='utf-8')
    base = json.loads(TRACES[0].files['run_record'])
    put('control-plane-journal', 'invalid', 'with-extra', {**base, 'extra': 1}, 'undeclared_member')
    put('control-plane-journal', 'invalid', 'odd', {**base, 'closeouts': 7}, 'some_rule_nobody_classified')
    put('control-plane-journal', 'valid', 'ok-1', base)
    put('execution-attempt-lifecycle', 'valid', 'ok-2', base)
    put('execution-attempt-lifecycle', 'invalid', 'naive', base, 'timestamp_invalid')


def run_harness(mode, traces=TINY, draws=1, seeds=None, runner_obj=None):
    slots, dropped = corpus.generate(traces, 7, draws)
    r = runner_obj or FakeRunner(mode)
    run = report.execute(r, traces, slots, seeds)
    data = (SUITE / 'operators.json').read_bytes()
    doc = report.build(run, traces=traces, slots=slots, duplicates_dropped=dropped, seeds=seeds, clean_manifest=MANIFEST, operator_set_bytes=data,
                       operator_set_digest=jsonio.digest(data), seed=7, draws=draws, frozen_revision='test', generated_at='2026-10-18T00:00:00+00:00',
                       command=f'stub --mode {mode}')
    return run, doc


def generated(doc):
    return next(c for c in doc['mutation_report']['family_t'] if c['provenance'] == 'generated')


def row(corpus_, cat):
    return next(r for r in corpus_['categories'] if r['category'] == cat)


def flag_ids(doc):
    return {f['id'] for f in doc['mutation_report']['extensions']['x-qualification-harness']['flags']}


class Operators(unittest.TestCase):
    def test_every_operator_is_tagged_with_one_design_category(self):
        schema = json.loads((SUITE / 'contract' / 'verification-report' / 'schema.json').read_text())
        enum = schema['$defs']['category']['enum']
        self.assertEqual(len(enum), 44)  # 36 + family H (ODES decision 28); the unwitnessed operators never use an H category
        self.assertTrue({o.category for o in operators.OPERATORS} <= set(enum))
        self.assertEqual(sorted(set(enum) - {o.category for o in operators.OPERATORS}), ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'L1', 'Q'])
        self.assertEqual(len({o.operator_id for o in operators.OPERATORS}), len(operators.OPERATORS))
        self.assertEqual(report.CATEGORY_ORDER, enum)

    def test_deterministic_under_a_seed_and_different_under_another(self):
        a, _ = corpus.generate(TINY, 11, 2)
        b, _ = corpus.generate(TINY, 11, 2)
        c, _ = corpus.generate(TINY, 12, 2)
        self.assertEqual(corpus.mutant_set_digest(a), corpus.mutant_set_digest(b))
        self.assertNotEqual(corpus.mutant_set_digest(a), corpus.mutant_set_digest(c))
        for x, y in zip(a, b):
            self.assertEqual((x.mutant_id, x.status, x.files), (y.mutant_id, y.status, y.files))

    def test_one_slot_does_not_depend_on_the_others(self):
        everything, _ = corpus.generate(TINY, 11, 2)
        one, _ = corpus.generate([BY_ID['default-applied']] + [BY_ID['default-held']], 11, 2, [o for o in operators.OPERATORS if o.category == 'D1'])
        want = {s.mutant_id: s for s in everything if s.trace_id in ('default-applied', 'default-held') and s.category == 'D1'}
        for s in one:
            self.assertEqual(s.files, want[s.mutant_id].files)

    def test_the_operator_set_file_is_the_code(self):
        self.assertEqual(cli.operator_set_bytes(cli.operator_set_doc(OPERATOR_SET['seed'], OPERATOR_SET['draws_per_variant'])), (SUITE / 'operators.json').read_bytes())

    def test_slots_are_effective_noop_or_na_and_none_is_lost(self):
        slots, dropped = corpus.generate(TINY, 3, 2)
        self.assertEqual({s.status for s in slots}, {'effective', 'na'})
        self.assertGreater(dropped, 0)  # identical mutants of one trace and operator are dropped, not counted twice
        keys = {(s.trace_id, s.operator_id, s.draw) for s in slots}
        self.assertEqual(len(keys), len(slots))
        self.assertTrue(all(s.files is None for s in slots if s.status == 'na'))

    def test_noop_is_decided_on_the_files(self):
        noop = operators.Operator('Z.noop', 'S1', 'noop', (), ('run_record',), '', lambda c: c.doc('run_record'))
        slots, _ = corpus.generate(TINY, 1, 1, [noop])
        self.assertEqual({s.status for s in slots}, {'noop'})  # re-serialized, canonically equal
        dup = operators.Operator('Z.dup', 'W1', 'dup', (), ('run_record',), '', operators.w1_dup_result)
        eff = [s for s in corpus.generate(TINY, 1, 1, [dup])[0] if s.trace_id == 'default-applied']
        self.assertEqual({s.status for s in eff}, {'effective'})  # Python's parser reads the clean document, the text is still damaged

    def test_wire_operators_produce_what_they_claim(self):
        slots, _ = full(5, 1)
        for s in slots:
            if s.status != 'effective' or s.category not in ('W1', 'W2', 'W5'):
                continue
            if s.operator_id == 'W2.nan-proposal-amount':
                data = s.files['proposal_export']
            elif s.operator_id == 'W2.nonfinite-ledger-amount':
                data = s.files['destination_ledger']
            else:
                data = s.files['run_record']
            with self.subTest(slot=s.mutant_id), self.assertRaises(stub.Strict):
                stub.strict_load(data)
        for s in slots:
            if s.status == 'effective' and s.category == 'B':
                with self.subTest(slot=s.mutant_id):
                    for role, data in s.files.items():
                        stub.strict_load(data)
                        if s.operator_id == 'B.resolution-check-id-renamed' and role == 'run_record':
                            continue  # a different (producer-local) id on purpose: checked in test_version_2_reclassifications
                        self.assertEqual(json.loads(data), BY_ID[s.trace_id].doc(role))  # same content, other text

    def test_decision_and_receipt_operators_break_what_they_claim(self):
        slots, _ = full(5, 1)
        seen = set()
        for s in slots:
            if s.status != 'effective' or s.category not in ('D1', 'D2', 'R1', 'R2'):
                continue
            paths = {role: json.loads(data) for role, data in s.files.items()}
            rr = paths['run_record']
            bad = [d for d in rr['decisions'] if (d['result'] == 'authorized') != (not d['reasons']) or (d['result'] == 'authorized') != (d['binding'] is not None)]
            authorized = {d['effect_id'] for d in rr['decisions'] if d['result'] == 'authorized'}
            stray = [r for r in paths.get('destination_ledger', {}).get('effects', {}).values() if r['effect_id'] not in authorized]
            with self.subTest(slot=s.mutant_id):
                self.assertTrue(bad if s.category in ('D1', 'D2') else stray)
            seen.add(s.category)
        self.assertEqual(seen, {'D1', 'D2', 'R1', 'R2'})

    def test_forgery_bound_operator_is_self_consistent(self):
        slots, _ = corpus.generate(TRACES, 5, 1, [o for o in operators.OPERATORS if o.category == 'F'])
        effective = [s for s in slots if s.status == 'effective']
        self.assertGreater(len(effective), 5)
        for s in effective:
            rr, proposal, ledger = (json.loads(s.files[r]) for r in ('run_record', 'proposal_export', 'destination_ledger'))
            d = rr['decisions'][0]
            b = d['binding']
            pc = jsonio.commitment(proposal)
            self.assertEqual(b['proposal_commitment'], pc)
            self.assertEqual(d['effect_id'], jsonio.commitment({'proposal': pc, 'grant_id': b['grant_id'], 'grant_revision': b['grant_revision']}))
            self.assertEqual(b['amount'], proposal['amount'])
            self.assertEqual({r['effect_id'] for r in ledger['effects'].values()}, {d['effect_id']} if ledger['effects'] else set())
            self.assertNotEqual(s.files['run_record'], BY_ID[s.trace_id].files['run_record'])

    def test_measures_are_derived_from_the_files(self):
        clean = measures(BY_ID['default-applied'].files)
        self.assertEqual(clean, {'unauthorized_effects': 0, 'excess_duplicate_effects': 0, 'authorized_count': 1, 'held_count': 0})
        slots, _ = corpus.generate([BY_ID['default-applied']], 5, 1, [o for o in operators.OPERATORS if o.operator_id in ('R1.unauthorized-ledger-effect', 'R4.second-ledger-row')])
        got = {s.operator_id: measures(s.files) for s in slots if s.status == 'effective'}
        self.assertEqual(got['R1.unauthorized-ledger-effect']['unauthorized_effects'], 1)
        self.assertEqual(got['R4.second-ledger-row']['excess_duplicate_effects'], 1)
        self.assertIsNone(measures({'run_record': b'{not json'}))


def canon_roles(files):
    return {role: jsonio.commitment(json.loads(data)) for role, data in files.items()}


class VersionTwo(unittest.TestCase):
    """Catalogue version 2 (V3b, written after run 1 was read): the three evidence-based reclassifications and the post-hoc intended codes."""

    @staticmethod
    def effective(operator_id, draws=2):
        ops = [o for o in operators.OPERATORS if o.operator_id == operator_id]
        assert len(ops) == 1, operator_id
        return [s for s in corpus.generate(TRACES, 5, draws, ops)[0] if s.status == 'effective']

    def test_version_2_reclassifications(self):
        # W3 keeps only the integer spelling: a different canonical byte string, so a different number under the pinned profile
        for oid, role in (('W3.binding-amount-integer-form', 'run_record'), ('W3.proposal-amount-integer-form', 'proposal_export'), ('W3.ledger-amount-integer-form', 'destination_ledger')):
            slots = self.effective(oid)
            self.assertTrue(slots, oid)
            for s in slots:
                self.assertEqual(s.expected_verdict, 'reject')
                self.assertNotEqual(canon_roles(s.files)[role], canon_roles(BY_ID[s.trace_id].files)[role], s.mutant_id)
        # the float spellings are B: textually different, canonically identical, value-equal
        for oid, role in (('B.binding-amount-float-form', 'run_record'), ('B.proposal-amount-float-form', 'proposal_export'), ('B.ledger-amount-float-form', 'destination_ledger')):
            slots = self.effective(oid)
            self.assertTrue(slots, oid)
            for s in slots:
                self.assertEqual(s.expected_verdict, 'accept')
                self.assertEqual(s.intended_codes, ())
                self.assertNotEqual(s.files[role], BY_ID[s.trace_id].files[role])
                self.assertEqual(canon_roles(s.files), canon_roles(BY_ID[s.trace_id].files), s.mutant_id)
                self.assertTrue(re.search(rb'"amount": (?:[0-9]+\.00|[0-9]+e[0-9]+|[0-9]+\.0e0)[,\s}]', s.files[role]), s.mutant_id)  # another spelling
        # J2: only a resolution check id differs, and the operator is benign now; no J2 operator is expected-accept
        self.assertEqual([o.operator_id for o in operators.OPERATORS if o.category == 'J2'], ['J2.resolution-checks-reordered'])
        slots = self.effective('B.resolution-check-id-renamed')
        self.assertTrue(slots)
        for s in slots:
            now, was = json.loads(s.files['run_record']), BY_ID[s.trace_id].doc('run_record')
            self.assertEqual(s.expected_verdict, 'accept')
            self.assertEqual({k: v for k, v in now.items() if k != 'resolution_checks'}, {k: v for k, v in was.items() if k != 'resolution_checks'})
            diffs = [(a, b) for a, b in zip(now['resolution_checks'], was['resolution_checks']) if a != b]
            self.assertEqual(len(diffs), 1)
            self.assertEqual({k for k in diffs[0][0] if diffs[0][0][k] != diffs[0][1][k]}, {'check_id'})

    def test_r6_is_an_uncorroborated_row_and_the_corroborated_drop_is_r5(self):
        r6 = self.effective('R6.truncate-ledger-tail')
        self.assertTrue(r6)
        self.assertEqual({s.trace_id for s in r6}, {'journal-lost-ack-unobserved'})
        for s in r6:
            rr, was = json.loads(s.files['run_record']), BY_ID[s.trace_id]
            self.assertEqual(s.expected_verdict, 'accept')
            self.assertEqual(s.intended_codes, ())
            self.assertIn('unknown', {a['status'] for a in rr['attempts']})
            self.assertFalse([o for o in rr['observations'] if o['state'] in ('applied', 'partial')])  # nothing corroborates the row
            self.assertEqual(len(json.loads(s.files['destination_ledger'])['effects']), len(was.doc('destination_ledger')['effects']) - 1)
        r5 = self.effective('R5.drop-ledger-row-of-lost-ack-observed')
        self.assertTrue(r5)
        self.assertNotIn('journal-lost-ack-unobserved', {s.trace_id for s in r5})
        for s in r5:
            rr = json.loads(s.files['run_record'])
            self.assertEqual(s.expected_verdict, 'reject')
            self.assertTrue([o for o in rr['observations'] if o['state'] == 'applied'])  # the record contradicts the snapshot

    def test_the_added_trace_is_a_real_lost_ack_without_an_applied_observation(self):
        t = BY_ID['journal-lost-ack-unobserved']
        rr = t.doc('run_record')
        self.assertEqual([a['status'] for a in rr['attempts']], ['attempted', 'unknown'])
        self.assertEqual([o['state'] for o in rr['observations']], ['absent'])
        self.assertEqual(rr['closeouts'], [])
        self.assertEqual([(x['result'], x['observation_accepted']) for x in rr['reconciliations']], [('observed_absent', True), ('hold', False)])
        self.assertEqual(len(t.doc('destination_ledger')['effects']), 1)
        entry = next(e for e in MANIFEST['traces'] if e['trace_id'] == 'journal-lost-ack-unobserved')
        self.assertEqual(set(entry['files']), UNWITNESSED_ROLES)
        self.assertEqual(MANIFEST['control_plane_revision'], json.loads((SUITE / 'corpus' / 'clean' / t.trace_id / 'scenario.json').read_text())['control_plane_revision'])

    def test_code_vocabulary_refresh_keeps_every_earlier_name_and_adds_the_witness_and_ledger_codes(self):
        names = set(json.loads((SUITE / 'verifier-code-names.json').read_text())['names'])
        self.assertEqual(len(names), 441)  # 268 at adb8927; 5974c50 adds 14 (witness and holder-inventory report notes, profile member names); 2fcdc3e6 adds 158 (V10's 157 and profile_sidecar_semantics_only); 0a43a7f0 adds reason_label_mismatch; none removed
        self.assertIn('reason_label_mismatch', names)
        self.assertIn('profile_sidecar_semantics_only', names)
        self.assertEqual(sorted(names), json.loads((SUITE / 'verifier-code-names.json').read_text())['names'])
        # the 07c2eb8 file (246 names) is a subset: a refresh adds names, it does not drop any
        self.assertTrue(len(names) >= 246)
        added_since_07c2eb8 = {'attempt_rows_not_in_record', 'destination_state_has_members_outside_ledger_row', 'holder_inventory_missing', 'holder_inventory_shape',
                               'operation_digest_mismatch', 'operation_digest_not_in_destination_state', 'rows_not_covered_by_witness', 'witness_chain_invalid',
                               'witness_ledger_head_mismatch', 'witness_ledger_shrunk', 'witness_record_shape', 'witness_run_mismatch', 'witness_version_unsupported'}
        self.assertTrue(added_since_07c2eb8 <= names)
        # present at 07c2eb8 already, listed for the record
        self.assertTrue({'resolution_check_mismatch', 'resolution_check_without_completion', 'effect_check_before_decision_check', 'ledger_row_without_attempt',
                         'ledger_row_after_definitive_failure'} <= names)

    def test_retained_run_3_report_validates_against_the_vendored_contract_and_names_its_pins(self):
        report_path = ROOT / 'results' / 'verifier-mutation' / 'run-3-adb8927' / 'mutation-report.json'
        doc = json.loads(report_path.read_text())
        contract = json.loads((SUITE / 'contract' / 'verification-report' / 'CONTRACT.json').read_text())
        validator = ODES
        self.assertEqual(validator.validate(doc), [])
        harness = doc['mutation_report']['extensions']['x-qualification-harness']
        self.assertEqual(doc['verifier']['source_revision'], 'adb8927fc13308370ea3b7ad3c899fd69c8fe203')
        self.assertEqual(harness['seed_corpus']['odes_revision'], 'fe705e8703ef4290aa7e6f00c31f1049b75a2bec')  # run 3's own ODES revision
        self.assertEqual(contract['odes_commit'], '304f6cc3d59fa0cac2bfc738d74de5e10c812454')  # re-vendored (README only since 0a37180f); run 3 still validates
        self.assertEqual(doc['mutation_report']['operator_set_digest'], V2_OPERATOR_SET_DIGEST)  # catalogue v2, not re-labelled
        self.assertEqual(OPERATOR_SET['supersedes']['operator_set_digest'], V2_OPERATOR_SET_DIGEST)
        self.assertEqual(harness['clean_traces'], {'n': 19, 'verdicts': {'reject': 0, 'accept': 19, 'abstain': 0, 'error': 0}})
        self.assertEqual(harness['flags'], [])

    def test_code_vocabulary_matches_the_verifier_source_when_a_clone_is_available(self):
        import os
        clone = os.environ.get('VERIFIER_CLONE')
        if not clone or not Path(clone).is_dir():
            self.skipTest('set VERIFIER_CLONE to a verifier clone to regenerate the vocabulary')
        from verifier_mutation import codenames
        vocab = json.loads((SUITE / 'verifier-code-names.json').read_text())
        full, names = codenames.names_at(Path(clone), vocab['verifier_revision'])
        self.assertEqual(full, vocab['verifier_revision'])
        self.assertEqual(names, vocab['names'])

    def test_intended_codes_are_names_the_verifier_has_and_are_labelled_post_hoc(self):
        vocab = json.loads((SUITE / 'verifier-code-names.json').read_text())
        self.assertEqual(vocab['verifier_revision'], '0a43a7f0216cb0300f198e69d1c2f6d3acb19c1a')
        names = set(vocab['names'])
        for o in operators.OPERATORS:
            with self.subTest(operator=o.operator_id):
                self.assertTrue(set(o.intended_codes) <= names, sorted(set(o.intended_codes) - names))
                self.assertEqual(bool(o.intended_codes), o.expected_verdict == 'reject')
        gone = {'wire_number_form_drift', 'transplanted_record', 'ledger_row_mismatch', 'ledger_binding_mismatch', 'ledger_row_missing', 'unauthorized_effect',
                'ledger_effect_for_held_decision', 'excess_duplicate_effect', 'ledger_duplicate_effect', 'expected_observed_mismatch', 'grant_revoked_but_authorized',
                'input_contradicts_result', 'record_commitment_mismatch', 'binding_mismatch', 'unknown_reason_code', 'wire_unicode_normalization'}
        self.assertFalse(gone & {c for o in operators.OPERATORS for c in o.intended_codes})
        by_id = {o.operator_id: set(o.intended_codes) for o in operators.OPERATORS}
        self.assertEqual(by_id['I4.input-commitment-altered'], {'resolution_check_mismatch'})
        self.assertEqual(by_id['J2.resolution-checks-reordered'], {'resolution_checks_out_of_order', 'effect_check_before_decision_check'})
        self.assertEqual(by_id['J3.completed-event-dropped'], by_id['J3.completed-rewritten-as-interrupted'])
        self.assertEqual(by_id['J3.completed-event-dropped'], {'resolution_check_without_completion'})
        self.assertEqual(by_id['X1.ledger-from-another-run'], {'ledger_effect_without_decision', 'ledger_row_without_attempt', 'ledger_row_after_definitive_failure',
                                                               'acknowledged_attempt_without_ledger_row', 'observation_without_ledger_row',
                                                               'acknowledgement_differs_from_ledger_row', 'observation_differs_from_ledger_row'})
        self.assertEqual(by_id['R5.drop-ledger-row-of-lost-ack-observed'], {'observation_without_ledger_row', 'acknowledged_attempt_without_ledger_row'})
        self.assertEqual(OPERATOR_SET['operator_version'], '3.2')  # 3.1: H8.witness-file-absent input-error control; 3.2: H4.destination-row-dropped-uncorroborated known-limit control (ODES decision 30-A)
        self.assertIn('post-hoc', OPERATOR_SET['intended_codes']['status'])
        self.assertIn('703cdde1', OPERATOR_SET['intended_codes']['status'])
        self.assertEqual(OPERATOR_SET['supersedes']['operator_version'], '2')
        self.assertEqual(OPERATOR_SET['supersedes']['operator_set_digest'], V2_OPERATOR_SET_DIGEST)

    def test_the_report_labels_localized_figures_as_post_hoc(self):
        _, doc = run_harness('accept')
        harness = doc['mutation_report']['extensions']['x-qualification-harness']
        self.assertIn('post-hoc', harness['intended_codes_status'])
        self.assertIn('not held-out', harness['definitions']['intended_code'])
        self.assertIn('any_code detection is the primary figure', harness['definitions']['intended_code'])
        self.assertEqual(harness['operator_version'], '3.2')


class Corpora(unittest.TestCase):
    def test_clean_corpus_matches_its_manifest(self):
        self.assertEqual(len(TRACES), 19)
        self.assertEqual(MANIFEST['canonicalization_profile'], jsonio.PROFILE)
        self.assertEqual(set(MANIFEST['contract_versions']), {'control-plane-journal', 'execution-attempt-lifecycle'})
        for t in TRACES:
            self.assertEqual(set(t.files), UNWITNESSED_ROLES)
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            shutil.copytree(SUITE / 'corpus' / 'clean', Path(tmp) / 'c')
            (Path(tmp) / 'c' / 'default-applied' / FILENAMES['run_record']).write_bytes(b'{}')
            with self.assertRaises(ValueError):
                load_clean_corpus(Path(tmp) / 'c')

    def test_clean_corpus_is_real_output_of_both_producers(self):
        producers = {json.loads((SUITE / 'corpus' / 'clean' / t.trace_id / 'scenario.json').read_text())['producer'] for t in TRACES}
        self.assertEqual(len(producers), 2)
        self.assertTrue(any(p.startswith('acp run') for p in producers))
        results = {t.doc('run_record')['decisions'][0]['result'] for t in TRACES}
        self.assertEqual(results, {'authorized', 'hold'})

    def test_seed_corpus_classifies_by_map_and_counts_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            mini_odes(tmp)
            seeds = corpus.load_seed_corpus(Path(tmp), corpus.load_seed_map(SUITE / 'seed-map.json'), 'abc')
        self.assertEqual((len(seeds.invalid), len(seeds.valid)), (3, 2))
        self.assertEqual(sorted(s.category or '-' for s in seeds.invalid), ['-', 'S1', 'T1'])
        self.assertEqual([s.expected_code for s in seeds.unclassified()], ['some_rule_nobody_classified'])

    def test_vendored_contract_is_unmodified(self):
        base = SUITE / 'contract' / 'verification-report'
        manifest = json.loads((base / 'CONTRACT.json').read_text())
        self.assertEqual((manifest['contract'], manifest['contract_version']), ('verification-report', '0.1.0-draft'))
        for name, want in manifest['files'].items():
            self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), want, name)

    def test_package_is_standard_library_only_and_independent_of_the_controller(self):
        stdlib = set(sys.stdlib_module_names)
        for path in sorted((SUITE / 'verifier_mutation').glob('*.py')) + [STUB_PATH]:
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else \
                    [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else []
                for n in names:
                    if path.name == 'capture.py' and n in ('agent_control_plane', 'tests'):
                        continue  # the opt-in capture tool imports the stack's own test helpers, as its docstring says
                    self.assertIn(n, stdlib, f'{path.name} imports {n}')
        for name in ('cli.py', 'report.py', 'runner.py', 'corpus.py', 'operators.py', 'witness_operators.py'):
            self.assertNotIn('v1_validation', (SUITE / 'verifier_mutation' / name).read_text())


class Runner(unittest.TestCase):
    def test_template(self):
        t = runner.parse_template('v --run-record {run_record} [--proposal {proposal_export}] [--ledger {destination_ledger}] --json')
        self.assertEqual(t.expand({'run_record': Path('/a')}), ['v', '--run-record', '/a', '--json'])
        self.assertEqual(t.expand({'run_record': Path('/a'), 'destination_ledger': Path('/l')}), ['v', '--run-record', '/a', '--json', '--ledger', '/l'])
        for bad in ('v --proposal {proposal_export}', 'v {run_record} {destination_ledger}', 'v {run_record} [--x {manifest}'):
            with self.assertRaises(ValueError):
                runner.parse_template(bad)

    def command(self, mode):
        return f'{sys.executable} {STUB_PATH} --mode {mode} --run-record {{run_record}} [--proposal {{proposal_export}}] [--ledger {{destination_ledger}}]'

    def test_external_process_verdicts(self):
        files = BY_ID['default-applied'].files
        want = {'accept': 'accept', 'reject': 'reject', 'abstain': 'abstain', 'crash': 'error', 'garbage': 'error', 'invalid': 'error'}
        for mode, verdict in want.items():
            with self.subTest(mode=mode):
                self.assertEqual(runner.Runner(self.command(mode)).verify(files).verdict, verdict)
        self.assertEqual(runner.Runner(self.command('reject')).verify(files).codes, {'stub_always_reject'})
        slow = runner.Runner(self.command('slow'), timeout=0.5).verify(files)
        self.assertEqual(slow.verdict, 'error')
        self.assertIn('timed out', slow.detail)
        self.assertEqual(runner.Runner('/nonexistent/verifier --run-record {run_record}').verify(files).verdict, 'error')

    def test_a_trace_report_that_carries_a_mutation_report_is_an_error(self):
        _, doc = run_harness('accept')
        self.assertEqual(runner.reduce_report(json.dumps(doc).encode(), ODES).verdict, 'error')


class HarnessWithStubs(unittest.TestCase):
    def test_accept_everything_shows_no_detection_and_is_flagged(self):
        run, doc = run_harness('accept')
        self.assertEqual(ODES.validate(doc), [])
        self.assertEqual(flag_ids(doc), {'no_detection_anywhere', 'accepts_every_mutant'})
        g = generated(doc)
        checked = 0
        for r in g['categories']:
            if r['expected_verdict'] == 'not_applicable':
                continue
            self.assertEqual(r['detection']['any_code']['k'], 0, r['category'])
            self.assertEqual(r['false_acceptance'], {'k': r['n_eff'], 'n': r['n_eff']}, r['category'])
            self.assertEqual(r['verdicts']['accept'], r['n_eff'])
            checked += r['n_eff']
        self.assertGreater(checked, 100)
        self.assertEqual(sum(1 for o in run.clean.values() if o.verdict == 'accept'), len(TINY))
        for c in doc['mutation_report']['clean']:
            self.assertTrue(all(x['false_rejection']['k'] == 0 for x in c['rows']))

    def test_reject_everything_shows_clean_false_rejection_and_is_flagged(self):
        run, doc = run_harness('reject')
        self.assertEqual(ODES.validate(doc), [])
        self.assertIn('rejects_every_clean_trace', flag_ids(doc))
        clean = next(c for c in doc['mutation_report']['clean'] if c['corpus_id'] == 'clean-generated')
        for r in clean['rows']:
            self.assertEqual(r['false_rejection']['k'], r['false_rejection']['n'], r['category'])
        self.assertTrue(any(r['false_rejection']['n'] > 0 for r in clean['rows']))
        benign = next(r for r in clean['rows'] if r['category'] == 'B')
        self.assertEqual(benign['false_rejection'], {'k': row(generated(doc), 'B')['n_eff'], 'n': row(generated(doc), 'B')['n_eff']})
        for r in generated(doc)['categories']:
            if r['expected_verdict'] != 'not_applicable':
                self.assertEqual(r['detection']['any_code'], {'k': r['n_eff'], 'n': r['n_eff']})
                self.assertEqual(r['detection']['intended_code']['k'], 0)  # the stub's code is nobody's intended code

    def test_a_crash_is_an_error_and_never_detection(self):
        run, doc = run_harness('crash')
        self.assertEqual(ODES.validate(doc), [])
        self.assertIn('errors_present', flag_ids(doc))
        for r in generated(doc)['categories']:
            if r['expected_verdict'] != 'not_applicable':
                self.assertEqual(r['verdicts'], {'reject': 0, 'accept': 0, 'abstain': 0, 'error': r['n_eff']})
                self.assertEqual(r['detection']['any_code']['k'], 0)
                self.assertEqual(r['errored'], {'k': r['n_eff'], 'n': r['n_eff']})
                self.assertEqual(r['metric_impact']['changed'], {'k': None, 'n': 0})

    def test_abstain_is_neither_detection_nor_acceptance(self):
        _, doc = run_harness('abstain')
        self.assertEqual(ODES.validate(doc), [])
        self.assertIn('abstains_on_every_mutant', flag_ids(doc))
        for r in generated(doc)['categories']:
            if r['expected_verdict'] != 'not_applicable':
                self.assertEqual((r['detection']['any_code']['k'], r['false_acceptance']['k'], r['abstained']['k']), (0, 0, r['n_eff']))

    def test_partial_verifier_shows_mixed_detection_per_category(self):
        run, doc = run_harness('partial')
        self.assertEqual(ODES.validate(doc), [])
        self.assertEqual(flag_ids(doc), set())
        g = generated(doc)
        for cat in ('W1', 'W2', 'D1', 'D2', 'R1'):
            r = row(g, cat)
            self.assertEqual(r['detection']['any_code'], {'k': r['n_eff'], 'n': r['n_eff']}, cat)
            self.assertGreater(r['n_eff'], 0)
        for cat in ('S1', 'S4', 'I2', 'J1', 'W3', 'A1'):
            r = row(g, cat)
            self.assertEqual(r['detection']['any_code']['k'], 0, cat)
            self.assertEqual(r['false_acceptance']['k'], r['n_eff'], cat)
        for cat in ('B', 'F'):
            r = row(g, cat)
            self.assertEqual(r['expected_verdict'], 'accept')
            self.assertEqual(r['verdicts']['accept'], r['n_eff'])
        self.assertEqual(row(g, 'Q')['expected_verdict'], 'not_applicable')
        # intended-code detection is localized: W1 mutants refused with the verifier's wire code, D1 with the contract code
        self.assertEqual(row(g, 'W1')['detection']['intended_code'], {'k': row(g, 'W1')['n_eff'], 'n': row(g, 'W1')['n_eff']})
        # metric impact is conditioned on false acceptance: R4 second ledger rows are accepted by this stub and change the excess duplicates
        r4 = row(g, 'R4')
        self.assertEqual(r4['metric_impact']['changed']['n'], r4['verdicts']['accept'])
        self.assertTrue(any(d['measure'] == 'excess_duplicate_effects' for d in r4['metric_impact']['deltas']))
        self.assertEqual(row(g, 'W1')['metric_impact']['changed'], {'k': None, 'n': 0})  # nothing accepted: n/a, never 0

    def test_denominators_are_never_pooled(self):
        with tempfile.TemporaryDirectory() as tmp:
            mini_odes(tmp)
            seeds = corpus.load_seed_corpus(Path(tmp), corpus.load_seed_map(SUITE / 'seed-map.json'), 'abc')
            run, doc = run_harness('partial', seeds=seeds)
        self.assertEqual(ODES.validate(doc), [])
        mr = doc['mutation_report']
        self.assertEqual([c['provenance'] for c in mr['family_t']], ['seed', 'generated'])
        self.assertEqual([c['provenance'] for c in mr['clean']], ['generated', 'seed_valid_fixtures'])
        self.assertEqual(len({c['corpus_digest'] for c in mr['family_t'] + mr['clean']}), 4)
        seed = mr['family_t'][0]
        for r in seed['categories']:
            self.assertIsNone(r['detection'])
            self.assertIsNone(r['metric_impact'])
            self.assertEqual(r['n_eff'], r['n_gen'])
        self.assertEqual(sum(r['n_eff'] for r in seed['categories']), 2)  # the unclassified fixture is counted aside, not in a category
        self.assertEqual(mr['extensions']['x-qualification-harness']['seed_corpus']['unclassified'], 1)
        self.assertEqual(mr['family_s'], [])
        # per scenario tables repeat the same shape over their own slots
        scn = generated(doc)['scenarios']
        self.assertEqual([s['scenario_id'] for s in scn], sorted(t.trace_id for t in TINY))
        for s in scn:
            for r in s['categories']:
                self.assertEqual(r['n_gen'] - r['n_noop'] - r['n_na'], r['n_eff'])

    def test_report_is_byte_identical_for_a_fixed_seed(self):
        a = json.dumps(run_harness('partial')[1], indent=1)
        b = json.dumps(run_harness('partial')[1], indent=1)
        self.assertEqual(a, b)

    def test_the_report_is_report_only_and_states_its_limits(self):
        _, doc = run_harness('partial')
        self.assertIs(doc['mutation_report']['report_only'], True)
        ids = {n['id'] for n in doc['does_not_prove']}
        self.assertEqual(ids, set(report.NON_CLAIMS))
        self.assertEqual(doc['checks'], [])
        self.assertEqual(doc['report_kind'], 'verification_report')
        text = json.dumps(doc)
        self.assertNotIn('"attestation"', text)
        self.assertNotIn('"score"', text)
        subject_digests = {i['digest'] for i in doc['subject']['inputs']}
        self.assertIn(doc['mutation_report']['operator_set_digest'], subject_digests)

    def test_a_report_with_an_altered_count_is_refused_by_the_validator(self):
        _, doc = run_harness('partial')
        r = row(generated(doc), 'W1')
        r['verdicts']['accept'] += 1
        self.assertIn('verdict_sum_mismatch', {v.code for v in ODES.validate(doc)})

    def test_end_to_end_through_external_processes_on_a_small_corpus(self):
        traces = [BY_ID['default-applied']]
        slots, dropped = corpus.generate(traces, 7, 1, [o for o in operators.OPERATORS if o.category in ('W1', 'R1', 'B')])
        for mode in ('accept', 'crash'):
            r = runner.Runner(f'{sys.executable} {STUB_PATH} --mode {mode} --run-record {{run_record}} [--proposal {{proposal_export}}] [--ledger {{destination_ledger}}]')
            run = report.execute(r, traces, slots, None, jobs=2)
            data = (SUITE / 'operators.json').read_bytes()
            doc = report.build(run, traces=traces, slots=slots, duplicates_dropped=dropped, seeds=None, clean_manifest=MANIFEST, operator_set_bytes=data,
                               operator_set_digest=jsonio.digest(data), seed=7, draws=1, frozen_revision='test', generated_at='2026-10-18T00:00:00+00:00', command=mode)
            with self.subTest(mode=mode):
                self.assertEqual(ODES.validate(doc), [])
                self.assertEqual(r.calls, 1 + len([s for s in slots if s.status == 'effective']))
                w1 = row(generated(doc), 'W1')
                self.assertEqual(w1['verdicts']['accept' if mode == 'accept' else 'error'], w1['n_eff'])


if __name__ == '__main__':
    unittest.main()
