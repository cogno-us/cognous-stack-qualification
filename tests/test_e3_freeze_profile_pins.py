"""E-3: the freeze profile checks run in both directions: an empty components map, a profile that omits a pinned subject component and a
stale constitutional_authority section must each fail (they passed with zero or too few checks)."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402
import v1_validation as v  # noqa: E402

PROFILE = json.loads((ROOT / _pins.PROFILE_RELPATH).read_text())
RESOLVED = _pins.RESOLVED_MANIFEST


def failed(prof, **kw):
    return [c[0] for c in v.profile_pin_checks(prof, RESOLVED, 'qualification', **kw) if not c[1]]


class ProfilePinChecks(unittest.TestCase):
    def test_the_repository_profile_equals_manifest_plus_overlay(self):
        self.assertEqual(failed(PROFILE, require_authority=True), [])

    def test_every_pinned_subject_component_is_checked(self):
        names = [c[0] for c in v.profile_pin_checks(PROFILE, RESOLVED, 'qualification')]
        for spec in RESOLVED['components_subject'].values():
            self.assertTrue(any(f"lists pinned subject component {spec['profile_key']} " in n for n in names), spec['profile_key'])

    def test_empty_components_map_fails(self):
        self.assertTrue(failed(dict(PROFILE, components={})))
        self.assertTrue(failed({k: x for k, x in PROFILE.items() if k != 'components'}))

    def test_a_profile_omitting_a_pinned_subject_component_fails(self):
        for omit in [spec['profile_key'] for spec in RESOLVED['components_subject'].values()]:
            prof = copy.deepcopy(PROFILE)
            del prof['components'][omit]
            bad = failed(prof)
            self.assertTrue(any(f'pinned subject component {omit} ' in n for n in bad), omit)

    def test_a_profile_component_at_another_revision_fails(self):
        prof = copy.deepcopy(PROFILE)
        prof['components']['odes']['revision'] = '0' * 40
        self.assertTrue(failed(prof))

    def test_a_stale_constitutional_authority_section_fails(self):
        prof = copy.deepcopy(PROFILE)
        prof['constitutional_authority']['revision'] = PROFILE['constitutional_authority'].get('previous_revision') or '0' * 40
        self.assertEqual([n for n in failed(prof) if 'constitutional_authority' in n], ['qualification profile constitutional_authority equals the pinned authority'])

    def test_a_missing_authority_section_fails_only_when_the_overlay_moved_the_authority(self):
        prof = {k: x for k, x in PROFILE.items() if k != 'constitutional_authority'}
        self.assertEqual(failed(prof), [])
        self.assertTrue(failed(prof, require_authority=True))


if __name__ == '__main__':
    unittest.main()
