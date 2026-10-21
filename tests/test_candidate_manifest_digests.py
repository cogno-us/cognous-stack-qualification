"""The digests that the newest candidate-manifest amendment states equal the digests of the files it names (RO-4, RP-9)."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['process/security-runtime-f5b-20261016-r13.json', 'process/v1-validation/v1-2026-10-16-a/freeze-manifest.json',
         'process/v1-validation/v1-2026-10-16-a/refreeze-log.json']


class CandidateManifestDigests(unittest.TestCase):
    def test_newest_candidate_amendment_states_the_actual_digests(self):
        twin = json.loads((ROOT / 'process/release-gate/preregistration.json').read_text())
        texts = [a['text'] for a in twin['amendments'] if a.get('text', '').startswith('Candidate manifest of the candidate g')]
        self.assertTrue(texts)
        text = texts[-1]
        actual = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES}
        for f, h in actual.items():
            self.assertIn(h, text, f)
        manifest = hashlib.sha256(''.join('%s %s\n' % (f, actual[f]) for f in FILES).encode()).hexdigest()
        self.assertIn('candidate manifest digest ' + manifest, text)
        self.assertEqual(len(re.findall(r'[0-9a-f]{64}', text)), 4)


if __name__ == '__main__':
    unittest.main()
