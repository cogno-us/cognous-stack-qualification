"""Unit tests for the re-freeze overlay resolver (suites/_pins.py) and its use by tools/v1_validation.py."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402

VAL = ROOT / 'process/v1-validation/v1-2026-10-16-a'
A, B, C = 'a' * 40, 'b' * 40, 'c' * 40


def manifest():
    return json.loads((VAL / 'freeze-manifest.json').read_text())


def entry(component, frm, to, status='APPLIED-IN-WORKFLOW (pending full controller run)', eid='RF-X', **kw):
    return dict(id=eid, component=component, from_sha=frm, to_sha=to, status=status, **kw)


def log(*entries):
    return {'validation_id': 'v1-2026-10-16-a', 'entries': list(entries)}


class Overlay(unittest.TestCase):
    def test_no_log_is_identity(self):
        m = manifest()
        resolved, applied = _pins.apply_overlay(m, None)
        self.assertEqual(resolved, m)
        self.assertEqual(applied, [])

    def test_applied_entry_overrides_and_original_is_untouched(self):
        m = manifest()
        orig = m['components_subject']['moltbot_safe']['sha']
        resolved, applied = _pins.apply_overlay(m, log(entry('runtime', orig, A)))
        self.assertEqual(resolved['components_subject']['moltbot_safe']['sha'], A)
        self.assertEqual(m['components_subject']['moltbot_safe']['sha'], orig)
        self.assertEqual(applied[0][1:3], ('components_subject', 'moltbot_safe'))
        # only the sha changed
        r2 = copy.deepcopy(resolved)
        r2['components_subject']['moltbot_safe']['sha'] = orig
        self.assertEqual(r2, m)

    def test_component_key_mapping_manifest_key_and_profile_alias(self):
        m = manifest()
        idx = m['components_lock_remainder']['the_index']['sha']
        r, _ = _pins.apply_overlay(m, log(entry('the_index', idx, A)))
        self.assertEqual(r['components_lock_remainder']['the_index']['sha'], A)
        for alias, (group, key) in {'runtime': ('components_subject', 'moltbot_safe'), 'replay': ('components_subject', 'replay_bundle'),
                                    'evidence_pack': ('components_subject', 'governance_evidence_pack'), 'odes': ('components_subject', 'odes'),
                                    'exchange': ('components_subject', 'gax_imx_transport'), 'manifest': ('components_subject', 'action_manifest'),
                                    'control_plane': ('components_subject', 'control_plane'), 'bitrep': ('components_lock_remainder', 'bitrep')}.items():
            cur = m[group][key]['sha']
            r, _ = _pins.apply_overlay(m, log(entry(alias, cur, B)))
            self.assertEqual(r[group][key]['sha'], B, alias)
        # every profile name of the seven subject components is mapped to its manifest key via profile_key
        for key, spec in m['components_subject'].items():
            self.assertEqual(_pins.LOG_COMPONENT_TO_MANIFEST[spec['profile_key']], ('components_subject', key))
        # every manifest component is reachable by its own key
        for g in _pins.GROUPS:
            for key in m.get(g, {}):
                self.assertEqual(_pins.LOG_COMPONENT_TO_MANIFEST[key], (g, key))

    def test_from_sha_mismatch_raises_clear_error(self):
        m = manifest()
        with self.assertRaisesRegex(_pins.RefreezeError, r'RF-X.*from_sha .* does not equal the pin in force'):
            _pins.apply_overlay(m, log(entry('the_index', C, A)))

    def test_entries_chain_and_a_skipped_link_is_an_error(self):
        m = manifest()
        orig = m['components_subject']['odes']['sha']
        r, applied = _pins.apply_overlay(m, log(entry('odes', orig, A, eid='RF-1'), entry('odes', A, B, eid='RF-2')))
        self.assertEqual(r['components_subject']['odes']['sha'], B)
        self.assertEqual([a[0] for a in applied], ['RF-1', 'RF-2'])
        with self.assertRaises(_pins.RefreezeError):  # second entry names the manifest pin again instead of the previous to_sha
            _pins.apply_overlay(m, log(entry('odes', orig, A, eid='RF-1'), entry('odes', orig, B, eid='RF-2')))

    def test_non_applied_entries_are_ignored_even_if_inconsistent(self):
        m = manifest()
        for status in ('PROPOSED', 'AUTHORISED', 'WITHDRAWN', 'PENDING', '', 'NOT APPLIED'):
            r, applied = _pins.apply_overlay(m, log(entry('the_index', C, A, status=status)))  # from_sha is wrong: not even checked
            self.assertEqual(r, m, status)
            self.assertEqual(applied, [])
        r, applied = _pins.apply_overlay(m, log(entry('the_index', m['components_lock_remainder']['the_index']['sha'], A, status='APPLIED')))
        self.assertEqual(len(applied), 1)

    def test_unknown_component_repository_mismatch_and_wrong_validation_id(self):
        m = manifest()
        with self.assertRaisesRegex(_pins.RefreezeError, 'unknown component'):
            _pins.apply_overlay(m, log(entry('nope', A, B)))
        cur = m['components_subject']['odes']['sha']
        with self.assertRaisesRegex(_pins.RefreezeError, 'repository'):
            _pins.apply_overlay(m, log(entry('odes', cur, A, repository='cogno-us/other')))
        bad = log(entry('odes', cur, A))
        bad['validation_id'] = 'other'
        with self.assertRaisesRegex(_pins.RefreezeError, 'refreeze log is for'):
            _pins.apply_overlay(m, bad)
        with self.assertRaisesRegex(_pins.RefreezeError, 'lacks from_sha/to_sha'):
            _pins.apply_overlay(m, log({'id': 'RF-Y', 'component': 'odes', 'status': 'APPLIED'}))

    def test_generations_and_classification(self):
        m = manifest()
        orig = _pins.profile_pins(m)
        rt = m['components_subject']['moltbot_safe']['sha']
        lg = log(entry('the_index', m['components_lock_remainder']['the_index']['sha'], A, eid='RF-1'), entry('runtime', rt, B, eid='RF-2'))
        gens = _pins.generations(m, lg)
        self.assertEqual([g[0] for g in gens], ['original-freeze', 'RF-2'])  # an Index-only entry does not start a profile generation
        new = dict(orig, runtime=B)
        self.assertEqual(_pins.classify_generation([orig, orig], gens), ('original-freeze', 0))
        self.assertEqual(_pins.classify_generation([new], gens), ('RF-2', 1))
        self.assertEqual(_pins.classify_generation([], gens), (None, None))
        with self.assertRaisesRegex(_pins.RefreezeError, 'match no frozen generation'):  # drift: one commit differs
            _pins.classify_generation([dict(orig, odes=C)], gens)
        with self.assertRaisesRegex(_pins.RefreezeError, 'mixes pin generations'):
            _pins.classify_generation([orig, new], gens)
        with self.assertRaises(_pins.RefreezeError):  # partial component set is not a generation
            _pins.classify_generation([{k: v for k, v in orig.items() if k != 'runtime'}], gens)


class CurrentPins(unittest.TestCase):
    """Resolved pins equal the literals that used to be hard-coded (no behaviour change at the current pins)."""
    def test_resolved_pins_equal_todays_literals(self):
        self.assertEqual(_pins.FROZEN_HUB, '8517818fbf817897aacfb6fe7898c22aea46fd95')
        self.assertEqual(_pins.FROZEN_RUNTIME, 'e20f92e104aba2ba6ad06120d8549c6170eaf63f')
        self.assertEqual(_pins.FROZEN_CONTROL_PLANE, 'a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5')
        self.assertEqual(_pins.FROZEN_REPLAY, '79ba16d48b9be1e059b3045989c7df960c3df1c2')
        self.assertEqual(_pins.FROZEN_EVIDENCE_PACK, '893aca8dfb27ba5c5f3e833f2d29210ca7fc92e3')
        self.assertEqual(_pins.FROZEN_ODES, 'eb83220c82f942e429a5e3ef5f677fdd5057ef84')
        self.assertEqual(_pins.FROZEN_EXCHANGE, '8be6c6b80da8c5038d66419f84c10cc529f78137')
        self.assertEqual(_pins.FROZEN_MANIFEST_COMPONENT, '2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e')
        self.assertEqual(_pins.FROZEN_BITREP, '5b5077dafde232a7801cb425c4efddcffb468723')
        self.assertEqual(_pins.OLD_INDEX_PIN, 'd5e45d275cb301d9684b543e93b05997991d1cf2')
        self.assertEqual(_pins.FROZEN_INDEX, 'd17b8ac2b8445d385fbf51185a35914b2d8b835c')  # RF-1 applied through the overlay
        self.assertEqual(_pins.REFROZEN_INDEX_PIN, 'd17b8ac2b8445d385fbf51185a35914b2d8b835c')
        self.assertEqual(_pins.C14_PINS, {'control_plane': 'a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5',
                                          'moltbot_safe': 'e20f92e104aba2ba6ad06120d8549c6170eaf63f',
                                          'replay': '79ba16d48b9be1e059b3045989c7df960c3df1c2'})
        self.assertEqual(_pins.PROFILE_RELPATH, 'process/security-runtime-f5b-20261016.json')

    def test_profile_pins_equal_the_original_qualification_profile(self):
        prof = json.loads((ROOT / 'process/security-runtime-f5b-20261016.json').read_text())
        self.assertEqual(_pins.PROFILE_PINS, {k: v['revision'] for k, v in prof['components'].items()})

    def test_repo_log_applies_cleanly_and_only_changes_the_index(self):
        m = manifest()
        r, applied = _pins.apply_overlay(m, _pins.load_refreeze_log())
        self.assertEqual([a[0] for a in applied], ['RF-1'])
        changed = {(g, k) for g in _pins.GROUPS for k in m.get(g, {}) if m[g][k]['sha'] != r[g][k]['sha']}
        self.assertEqual(changed, {('components_lock_remainder', 'the_index')})
        self.assertEqual(len(_pins.GENERATIONS), 1)

    def test_no_pin_literal_left_in_helpers(self):
        pinned = {s['sha'] for g in _pins.GROUPS for s in manifest().get(g, {}).values()} | {manifest()['identities']['hub']['head'],
                                                                                              'd17b8ac2b8445d385fbf51185a35914b2d8b835c'}
        import re
        for f in ('_d02_d05_d09_helpers.py', '_d06_d07_d08_helpers.py', '_c_2b_helpers.py', '_index_signing.py', 'test_scn_c14.py', 'test_add_test_g1.py', 'test_asw_s.py'):
            src = (ROOT / 'suites/v1-scenarios' / f).read_text()
            code = '\n'.join(l for l in src.splitlines() if not l.lstrip().startswith('#'))
            lits = set(re.findall(r"['\"]([0-9a-f]{40})['\"]", code))
            self.assertFalse(lits & pinned, f)
        probe = (ROOT / 'suites/v1-probes/_index_signing.py').read_text()
        self.assertEqual(probe, (ROOT / 'suites/v1-scenarios/_index_signing.py').read_text())


class ToolOverlay(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'tools/v1_validation.py'), *args], capture_output=True, text=True)

    def plan(self, *extra):
        p = self.run_tool('plan', '--manifest', str(VAL / 'freeze-manifest.json'), *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return {(i['component']): i['sha'] for i in json.loads(p.stdout)['include']}

    def test_plan_without_overlay_is_the_original_manifest(self):
        m = manifest()
        shas = self.plan()
        self.assertEqual(shas['the_index'], m['components_lock_remainder']['the_index']['sha'])

    def test_plan_with_overlay_uses_applied_entries(self):
        shas = self.plan('--refreeze-log', str(VAL / 'refreeze-log.json'))
        self.assertEqual(shas['the_index'], 'd17b8ac2b8445d385fbf51185a35914b2d8b835c')
        self.assertEqual(shas['moltbot_safe'], manifest()['components_subject']['moltbot_safe']['sha'])

    def test_plan_with_inconsistent_log_fails_loudly(self, tmp=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'log.json'
            p.write_text(json.dumps(log(entry('the_index', C, A))))
            r = self.run_tool('plan', '--manifest', str(VAL / 'freeze-manifest.json'), '--refreeze-log', str(p))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('does not equal the pin in force', r.stderr)
            p.write_text(json.dumps(log(entry('the_index', C, A, status='PROPOSED'))))
            self.assertEqual(self.run_tool('plan', '--manifest', str(VAL / 'freeze-manifest.json'), '--refreeze-log', str(p)).returncode, 0)


if __name__ == '__main__':
    unittest.main()
