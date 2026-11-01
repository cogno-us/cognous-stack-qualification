"""E-5: a parenthesised note must not contradict the APPLIED status; the log needs a validation_id and unique entry ids."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402

M = _pins.load_manifest()
CUR = M['components_lock_remainder']['bitrep']['sha']
A, B = 'a' * 40, 'b' * 40


def entry(eid, frm, to, status='APPLIED'):
    return {'id': eid, 'component': 'bitrep', 'status': status, 'from_sha': frm, 'to_sha': to}


class StatusNote(unittest.TestCase):
    def test_a_note_that_contradicts_the_status_is_not_applied(self):
        for s in ('APPLIED (REVERTED: do not apply)', 'APPLIED (withdrawn by RF-47)', 'APPLIED-IN-WORKFLOW (PROPOSED only, not authorised)',
                  'APPLIED (reverted)', 'APPLIED (NOT APPLIED)', 'APPLIED (rejected)', 'APPLIED (rolled back)', 'APPLIED (cancelled)',
                  'APPLIED (do-not-apply)', 'APPLIED (not authorized)'):
            self.assertFalse(_pins.is_applied({'status': s}), s)

    def test_the_status_forms_of_the_retained_log_stay_applied(self):
        for e in _pins.load_refreeze_log()['entries']:
            self.assertTrue(_pins.is_applied(e), e['id'])
        self.assertTrue(_pins.is_applied({'status': 'APPLIED (superseded by RF-44; the runs probed this revision and neither qualified it)'}))


class LogShape(unittest.TestCase):
    def test_duplicate_entry_ids_are_refused_even_when_one_is_not_applied(self):
        log = {'validation_id': M['validation_id'], 'entries': [entry('RF-46', CUR, A, 'PROPOSED'), entry('RF-46', CUR, B)]}
        with self.assertRaisesRegex(_pins.RefreezeError, 'duplicate'):
            _pins.apply_overlay(M, log)

    def test_a_log_without_validation_id_is_refused(self):
        with self.assertRaisesRegex(_pins.RefreezeError, 'validation_id'):
            _pins.apply_overlay(M, {'entries': [entry('RF-46', CUR, A)]})

    def test_a_well_formed_log_applies(self):
        r, applied = _pins.apply_overlay(M, {'validation_id': M['validation_id'], 'entries': [entry('RF-46', CUR, A)]})
        self.assertEqual(r['components_lock_remainder']['bitrep']['sha'], A)


if __name__ == '__main__':
    unittest.main()
