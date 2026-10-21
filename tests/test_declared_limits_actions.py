"""E4: an amendment with an unknown action must not be silently ignored when the declared set is derived."""
import copy, json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import declared_limits as DL  # noqa: E402

TWIN = ROOT / DL.TWIN_REL
EXPECTED_SHA = '51bb22945a8a5e525f689fc9a2053f150127aab0cc32b95fd26442eeba69e5d7'


class AmendmentActions(unittest.TestCase):
    def test_real_preregistration_still_derives_the_same_declared_set(self):
        rec = DL.load(TWIN)
        self.assertEqual(rec['declared_set_sha256'], EXPECTED_SHA)
        self.assertEqual(len(rec['entries']), 75)

    def test_every_action_in_the_real_twin_is_in_the_allow_list(self):
        actions = {a.get('action') for a in json.loads(TWIN.read_text())['amendments']}
        self.assertLessEqual(actions, DL.KNOWN_ACTIONS)

    def test_a_typo_action_raises(self):
        twin = json.loads(TWIN.read_text())
        bad = copy.deepcopy(twin)
        bad['amendments'].append({'action': 'add_known_limits', 'id': 'cogno-us/cognous-control-plane:tests/test_x.py::test_y', 'timestamp': 't'})
        with self.assertRaisesRegex(DL.DeclaredSetError, 'unknown action'):
            DL.normalise(bad)

    def test_a_missing_action_raises(self):
        bad = json.loads(TWIN.read_text())
        bad['amendments'].append({'id': 'x', 'timestamp': 't'})
        with self.assertRaises(DL.DeclaredSetError):
            DL.normalise(bad)


if __name__ == '__main__':
    unittest.main()
