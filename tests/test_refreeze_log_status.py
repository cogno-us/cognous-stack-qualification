"""The statuses of the refreeze log keep the prefix that the pin overlay reads, and only the entries of the newest
unqualified candidate say that a controller run is pending."""
import json
import unittest
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / 'process/v1-validation/v1-2026-10-16-a/refreeze-log.json'
PENDING = set()  # no entry awaits a controller run: g8-r10 (run 39690459403, results #216) has been made, so the text `pending full controller run` is retired
PROBED_ONLY = {'RF-45', 'RF-46', 'RF-47', 'RF-48'} | {'RF-%d' % i for i in range(49, 62)}  # probed by g6-r10 (RF-45), g7-r10 (run 39642578239) or g8-r10 (run 39690459403): unreduced mandatory verdict INCOMPLETE; not marked qualified, so RF-36 stays the last qualified authority entry
# RF-46 and RF-48 are probed unchanged by g7-r10 and g8-r10 because their pins stay in force


class RefreezeLogStatus(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LOG.read_text(encoding='utf-8'))['entries']

    def test_every_entry_is_applied_and_only_the_newest_are_pending(self):
        self.assertEqual(len(self.entries), 61)
        for e in self.entries:
            self.assertTrue(e['status'].startswith('APPLIED'), e['id'])
            self.assertEqual('pending' in e['status'], e['id'] in PENDING, e['id'])
            if int(e['id'][3:]) >= 55 or e['id'] in ('RF-46', 'RF-48'):
                self.assertIn('39690459403', e['status'], e['id'])  # the run g8-r10 that probed it
                self.assertIn('not marked qualified', e['status'], e['id'])

    def test_last_qualified_entry_of_each_component_is_marked(self):
        last = {}
        for e in self.entries:
            if e['id'] not in PENDING | PROBED_ONLY:
                last[e['component']] = e['id']
        for e in self.entries:
            if e['id'] in PENDING:
                continue
            if e['id'] in PROBED_ONLY:
                self.assertFalse(e['status'].startswith('APPLIED (qualified'), e['id'])
                continue
            marked = e['status'].startswith('APPLIED (qualified')
            self.assertEqual(marked, e['id'] in last.values() or e['id'] == 'RF-1', e['id'])


if __name__ == '__main__':
    unittest.main()
