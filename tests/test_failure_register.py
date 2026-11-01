"""Failure-register closure-evidence labels (C12): validation, conservative back-fill, no status change."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import failure_register as FR  # noqa: E402

REGISTER = ROOT/'process/v1-validation/v1-2026-10-16-a/failure-register.json'


def doc():
    return json.loads(REGISTER.read_text(encoding='utf-8'))


class ClosureEvidence(unittest.TestCase):
    def test_committed_register_is_valid_and_in_format(self):
        raw = REGISTER.read_text(encoding='utf-8')
        self.assertEqual(FR.validate(json.loads(raw)), [])
        self.assertEqual(FR.dumps(json.loads(raw)), raw, 'register format: indent=1, ensure_ascii=False, trailing newline')

    def test_committed_register_matches_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        schema = json.loads((ROOT/'schemas/failure-register.schema.json').read_text())
        jsonschema.validate(doc(), schema)
        bad = doc()
        bad['entries'][0]['closure_evidence'] = {'label': 'trust-me', 'owner': 'x'}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)

    def test_verified_entries_are_labelled_and_unverified_are_not(self):
        for entry in doc()['entries']:
            if entry['status'] == 'FIXED-UNVERIFIED':
                self.assertNotIn('closure_evidence', entry, entry['id'])
            if entry['status'] == 'VERIFIED':
                self.assertIn('closure_evidence', entry, entry['id'])

    def test_backfill_is_conservative_and_changes_nothing_else(self):
        original = doc()
        for entry in original['entries']:
            entry.pop('closure_evidence', None)
        work = copy.deepcopy(original)
        added = FR.backfill(work)
        self.assertEqual(sorted(added), sorted(e['id'] for e in original['entries'] if e['status'] == 'VERIFIED'))
        for before, after in zip(original['entries'], work['entries']):
            extra = {k: v for k, v in after.items() if k not in before}
            if before['status'] == 'VERIFIED':
                self.assertEqual(extra, {'closure_evidence': {'label': 'machine-asserted', 'owner': 'unassigned'}})
            else:
                self.assertEqual(extra, {}, before['id'])
            self.assertEqual({k: v for k, v in after.items() if k != 'closure_evidence'}, before)
        self.assertEqual({k: v for k, v in work.items() if k != 'entries'}, {k: v for k, v in original.items() if k != 'entries'})
        self.assertEqual(FR.backfill(work), [], 'idempotent')

    def test_validation_refuses_overclaims(self):
        base = doc()
        verified = next(e for e in base['entries'] if e['status'] == 'VERIFIED')
        unverified = next(e for e in base['entries'] if e['status'] == 'FIXED-UNVERIFIED')

        def with_ce(entry, value):
            d = copy.deepcopy(base)
            target = next(e for e in d['entries'] if e['id'] == entry['id'])
            target['closure_evidence'] = value
            return FR.validate(d)
        self.assertEqual(with_ce(verified, {'label': 'human-validated', 'owner': 'A. Reviewer'}), [])
        self.assertTrue(with_ce(verified, {'label': 'human-validated', 'owner': 'unassigned'}))
        self.assertTrue(with_ce(verified, {'label': 'independently-checked', 'owner': ''}))
        self.assertTrue(with_ce(verified, {'label': 'verified', 'owner': 'x'}))
        self.assertTrue(with_ce(verified, {'label': 'machine-asserted'}))
        self.assertTrue(with_ce(unverified, {'label': 'machine-asserted', 'owner': 'unassigned'}))


if __name__ == '__main__':
    unittest.main()
