"""The statuses of the refreeze log keep the prefix that the pin overlay reads and no longer say that a controller run is pending."""
import json
import unittest
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / 'process/v1-validation/v1-2026-10-16-a/refreeze-log.json'


class RefreezeLogStatus(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LOG.read_text(encoding='utf-8'))['entries']

    def test_every_entry_is_applied_and_none_is_pending(self):
        self.assertEqual(len(self.entries), 41)
        for e in self.entries:
            self.assertTrue(e['status'].startswith('APPLIED'), e['id'])
            self.assertNotIn('pending', e['status'], e['id'])

    def test_only_the_last_entry_of_each_component_is_qualified(self):
        last = {}
        for e in self.entries:
            last[e['component']] = e['id']
        for e in self.entries:
            qualified = e['status'].startswith('APPLIED (qualified:')
            self.assertEqual(qualified, e['id'] in last.values(), e['id'])


if __name__ == '__main__':
    unittest.main()
