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


R2_PINS = {'control_plane': 'a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5', 'runtime': '4a83b175d2ef0e65a7ee22a0513bb94a5fdf3a6f',
           'replay': 'def0ee0f3af713283ea3cd13f0caf79e1607b651', 'odes': '5675f1b96d95ba69510656bf73b1006110ef5b57',
           'evidence_pack': '505a3590114705b7ebf736b92dd189f338134635', 'exchange': 'ec6ba5bdaaf3a53db312790de5e60e90c3b92fe4'}
# P4 generation (r3, r4): the pins of the decoupling plan's mains (RF-11..RF-16)
P4_PINS = {'control_plane': '26a7e6594eb535827ccc248cbca36a7d119d613b', 'runtime': '3024ef6e6ecf7da22e5f4fdf90d873f93b2a55c9',
           'replay': '9aab3f6c34d2721ef1be3f6468b71dc3bad99a2a', 'odes': 'c5f4e2d0015ccdc94127a4025a6b605fc7fbdcbd',
           'evidence_pack': '54df6984dd418e2e0a09f89e54f281493475831c', 'exchange': '914db78dc3a4dbcc4abc79159f0ac0b7c1edc144'}
# Programme 2 generation (r5): the mains after the opt-in profile work and the input-handling hardening (RF-18..RF-22); exchange unchanged
R5_PINS = {'control_plane': '3cd17ead6b24301290ad1e50ae4b22bbd93c12fb', 'runtime': '11de097c450d3ad4d89f9add41b00e38e7cc2c7c',
           'replay': '46e8bd7c263f5075cac3a7a9defcb265384f40e9', 'odes': '0663d5a24a2d94b83f51f611f30b3b3f144d6c5d',
           'evidence_pack': '4fbbd34418f8dce7a536879d7bd0378737179f47', 'exchange': '914db78dc3a4dbcc4abc79159f0ac0b7c1edc144'}
# Programme 2 gap fixes (r6): ODES with the P2 compatibility tuple (#97) and the exchange compatibility profile (#37) (RF-23, RF-24)
NEW = dict(R5_PINS, odes='81979784117588d199da6fdceb05264f8c5903a6', exchange='7172dde6b1117d8ecf2a6ff224f6059f05ad21b6')
R1_PINS = {'runtime': '4a83b175d2ef0e65a7ee22a0513bb94a5fdf3a6f', 'replay': '0cfe7a6319930bccad3e9027a1dfbe3d6e29d657',
           'odes': '4e6d11691b9dea56a70026b6519159cf0e0ffd8b', 'evidence_pack': '683246e05d291308211778ec48045df65466461f',
           'exchange': 'da95378228b8f3205af49a86e68ba722961f6af0'}
R1 = 'process/security-runtime-f5b-20261016-r1.json'
R2 = 'process/security-runtime-f5b-20261016-r2.json'
R3 = 'process/security-runtime-f5b-20261016-r3.json'
R4 = 'process/security-runtime-f5b-20261016-r4.json'
R5 = 'process/security-runtime-f5b-20261016-r5.json'
R6 = 'process/security-runtime-f5b-20261016-r6.json'
AUTH_OLD = 'fb3d97938969a89e149e8ff8db2756091d1233fc'
AUTH_NEW = 'cbc39e79a1328a74b6cb1aba0cd1e5149164865d'  # RF-17: institutional-governance main with the F-15 fix (#51)


class CurrentPins(unittest.TestCase):
    """Resolved pins equal the pins in force: the freeze manifest plus RF-1 (Index), RF-2..RF-16 (the P4 generation of the decoupling plan), RF-17 (the constitutional authority, F-15), RF-18..RF-22 (the Programme 2 generation) and RF-23, RF-24 (the ODES and exchange compatibility gap fixes)."""
    def test_resolved_pins_equal_todays_literals(self):
        self.assertEqual(_pins.FROZEN_HUB, '8517818fbf817897aacfb6fe7898c22aea46fd95')
        self.assertEqual(_pins.FROZEN_RUNTIME, NEW['runtime'])
        self.assertEqual(_pins.FROZEN_CONTROL_PLANE, NEW['control_plane'])
        self.assertEqual(_pins.FROZEN_REPLAY, NEW['replay'])
        self.assertEqual(_pins.FROZEN_EVIDENCE_PACK, NEW['evidence_pack'])
        self.assertEqual(_pins.FROZEN_ODES, NEW['odes'])
        self.assertEqual(_pins.FROZEN_EXCHANGE, NEW['exchange'])
        self.assertEqual(_pins.FROZEN_MANIFEST_COMPONENT, '2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e')
        self.assertEqual(_pins.FROZEN_BITREP, '5b5077dafde232a7801cb425c4efddcffb468723')
        self.assertEqual(_pins.OLD_INDEX_PIN, 'd5e45d275cb301d9684b543e93b05997991d1cf2')
        self.assertEqual(_pins.FROZEN_INDEX, 'd17b8ac2b8445d385fbf51185a35914b2d8b835c')  # RF-1 applied through the overlay
        self.assertEqual(_pins.REFROZEN_INDEX_PIN, 'd17b8ac2b8445d385fbf51185a35914b2d8b835c')
        self.assertEqual(_pins.C14_PINS, {'control_plane': NEW['control_plane'],
                                          'moltbot_safe': NEW['runtime'], 'replay': NEW['replay']})
        self.assertEqual(_pins.PROFILE_RELPATH, R6)  # the newest profile whose refreeze_ids are all applied
        self.assertEqual(_pins.RESOLVED_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'], AUTH_NEW)  # RF-17 through the overlay
        self.assertEqual(_pins.ORIGINAL_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'], AUTH_OLD)

    def test_profile_pins_equal_the_r6_qualification_profile(self):
        prof = json.loads((ROOT / R6).read_text())
        self.assertEqual(_pins.PROFILE_PINS, {k: v['revision'] for k, v in prof['components'].items()})

    def test_r1_profile_is_the_original_with_only_the_five_revisions_changed(self):
        orig = json.loads((ROOT / _pins.ORIGINAL_PROFILE).read_text())
        r1 = json.loads((ROOT / R1).read_text())
        self.assertEqual(r1['supersedes_profile'], _pins.ORIGINAL_PROFILE)
        self.assertEqual(r1['refreeze_ids'], ['RF-2', 'RF-3', 'RF-4', 'RF-5', 'RF-6'])
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r1[key], False)
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations'):
            r1.pop(key); orig.pop(key, None)
        for name, rev in R1_PINS.items():
            self.assertNotEqual(orig['components'][name]['revision'], rev)
            r1['components'][name]['revision'] = orig['components'][name]['revision']
        self.assertEqual(r1, orig)  # includes the exchange compatibility profile name and additional_source_hashes

    def test_r2_profile_is_r1_with_only_replay_odes_pack_exchange_changed(self):
        r1 = json.loads((ROOT / R1).read_text())
        r2 = json.loads((ROOT / R2).read_text())
        self.assertEqual(r2['profile_id'], 'security-runtime-f5b-20261016-r2')
        self.assertEqual(r2['supersedes_profile'], R1)
        self.assertEqual(r2['refreeze_ids'], ['RF-%d' % i for i in range(2, 11)])
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r2[key], False)
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations'):
            r1.pop(key); r2.pop(key)
        for name in ('replay', 'odes', 'evidence_pack', 'exchange'):
            self.assertNotEqual(r1['components'][name]['revision'], r2['components'][name]['revision'])
            r2['components'][name]['revision'] = r1['components'][name]['revision']
        self.assertEqual(r2, r1)  # runtime/control_plane/manifest and the exchange compatibility profile name unchanged

    def test_r3_profile_is_r2_with_only_the_six_p4_pins_and_the_generation_changed(self):
        r2 = json.loads((ROOT / R2).read_text())
        r3 = json.loads((ROOT / R3).read_text())
        self.assertEqual(r3['profile_id'], 'security-runtime-f5b-20261016-r3')
        self.assertEqual(r3['supersedes_profile'], R2)
        self.assertEqual(r3['refreeze_ids'], ['RF-%d' % i for i in range(2, 17)])
        self.assertEqual((r3['suite_generation'], r3['exchange_compatibility_profile']), ('p4', 'security-runtime-p4-20261017'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r3[key], False)
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'suite_generation', 'exchange_compatibility_profile'):
            r2.pop(key, None); r3.pop(key)
        for name in ('control_plane', 'runtime', 'replay', 'odes', 'evidence_pack', 'exchange'):
            self.assertNotEqual(r2['components'][name]['revision'], r3['components'][name]['revision'])
            r3['components'][name]['revision'] = r2['components'][name]['revision']
        self.assertEqual(r3, r2)  # the manifest component is unchanged

    def test_r4_profile_is_r3_with_only_the_authority_pin_changed(self):
        r3 = json.loads((ROOT / R3).read_text())
        r4 = json.loads((ROOT / R4).read_text())
        self.assertEqual(r4['profile_id'], 'security-runtime-f5b-20261016-r4')
        self.assertEqual(r4['supersedes_profile'], R3)
        self.assertEqual(r4['refreeze_ids'], ['RF-%d' % i for i in range(2, 18)])
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r4[key], False)
        self.assertEqual(r4['constitutional_authority'], {'repository': 'cogno-us/cognous-institutional-governance',
                                                          'revision': AUTH_NEW, 'previous_revision': AUTH_OLD})
        self.assertEqual(r4['constitutional_authority']['revision'],
                         _pins.RESOLVED_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'])
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'constitutional_authority'):
            r3.pop(key, None); r4.pop(key)
        self.assertEqual(r4, r3)  # every component revision, the suite generation and the exchange compatibility profile are r3's

    def test_r5_profile_is_r4_with_only_the_five_programme2_pins_and_the_generation_changed(self):
        r4 = json.loads((ROOT / R4).read_text())
        r5 = json.loads((ROOT / R5).read_text())
        self.assertEqual(r5['profile_id'], 'security-runtime-f5b-20261016-r5')
        self.assertEqual(r5['supersedes_profile'], R4)
        self.assertEqual(r5['refreeze_ids'], ['RF-%d' % i for i in range(2, 23)])
        self.assertEqual((r5['suite_generation'], r5['exchange_compatibility_profile']), ('p2', 'security-runtime-p4-20261017'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r5[key], False)
        self.assertEqual(r5['constitutional_authority'], r4['constitutional_authority'])
        for name in ('control_plane', 'runtime', 'replay', 'odes', 'evidence_pack'):
            self.assertEqual(r5['components'][name]['revision'], R5_PINS[name])
            self.assertEqual(r4['components'][name]['revision'], P4_PINS[name])
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'suite_generation'):
            r4.pop(key, None); r5.pop(key)
        for name in ('control_plane', 'runtime', 'replay', 'odes', 'evidence_pack'):
            r5['components'][name]['revision'] = r4['components'][name]['revision']
        self.assertEqual(r5, r4)  # exchange, manifest, authority and the exchange compatibility profile are r4's

    def test_r6_profile_is_r5_with_only_the_odes_and_exchange_pins_and_the_exchange_profile_changed(self):
        r5 = json.loads((ROOT / R5).read_text())
        r6 = json.loads((ROOT / R6).read_text())
        self.assertEqual(r6['profile_id'], 'security-runtime-f5b-20261016-r6')
        self.assertEqual(r6['supersedes_profile'], R5)
        self.assertEqual(r6['refreeze_ids'], ['RF-%d' % i for i in range(2, 25)])
        self.assertEqual((r6['suite_generation'], r6['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r6[key], False)
        self.assertEqual(r6['constitutional_authority'], r5['constitutional_authority'])
        for name in ('odes', 'exchange'):
            self.assertEqual(r6['components'][name]['revision'], NEW[name])
            self.assertEqual(r5['components'][name]['revision'], R5_PINS[name])
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'exchange_compatibility_profile'):
            r5.pop(key, None); r6.pop(key)
        for name in ('odes', 'exchange'):
            r6['components'][name]['revision'] = r5['components'][name]['revision']
        self.assertEqual(r6, r5)  # control plane, runtime, Replay, evidence pack, manifest, authority and the suite generation are r5's

    def test_select_profile_picks_newest_fully_applied_profile(self):
        done = 'APPLIED-IN-WORKFLOW (pending full controller run)'
        ids = lambda n: log(*[entry('odes', A, B, status=done, eid='RF-%d' % i) for i in range(2, n + 1)])
        self.assertEqual(_pins.select_profile(None), _pins.ORIGINAL_PROFILE)
        self.assertEqual(_pins.select_profile(ids(1)), _pins.ORIGINAL_PROFILE)
        self.assertEqual(_pins.select_profile(ids(6)), R1)          # r2 needs RF-7..RF-10 too
        self.assertEqual(_pins.select_profile(ids(9)), R1)
        self.assertEqual(_pins.select_profile(ids(10)), R2)          # r3 needs RF-11..RF-16 too
        self.assertEqual(_pins.select_profile(ids(15)), R2)
        self.assertEqual(_pins.select_profile(ids(16)), R3)          # r4 needs RF-17 too
        self.assertEqual(_pins.select_profile(ids(17)), R4)          # r5 needs RF-18..RF-22 too
        self.assertEqual(_pins.select_profile(ids(21)), R4)
        self.assertEqual(_pins.select_profile(ids(22)), R5)          # r6 needs RF-23, RF-24 too
        self.assertEqual(_pins.select_profile(ids(23)), R5)
        self.assertEqual(_pins.select_profile(ids(24)), R6)
        partial = ids(10); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R1)
        partial = ids(16); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R2)
        partial = ids(17); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R3)
        partial = ids(22); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R4)
        partial = ids(24); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R5)

    def test_original_profile_and_freeze_manifest_are_unedited(self):
        import hashlib
        frozen = manifest()['qualification_file_hashes'][_pins.ORIGINAL_PROFILE]
        self.assertEqual(hashlib.sha256((ROOT / _pins.ORIGINAL_PROFILE).read_bytes()).hexdigest(), frozen)
        self.assertEqual(manifest()['components_subject']['moltbot_safe']['sha'], 'e20f92e104aba2ba6ad06120d8549c6170eaf63f')

    def test_repo_log_applies_cleanly_and_changes_the_index_the_authority_and_the_six_components(self):
        m = manifest()
        r, applied = _pins.apply_overlay(m, _pins.load_refreeze_log())
        self.assertEqual([a[0] for a in applied], ['RF-%d' % i for i in range(1, 25)])
        changed = {(g, k) for g in _pins.GROUPS for k in m.get(g, {}) if m[g][k]['sha'] != r[g][k]['sha']}
        self.assertEqual(changed, {('components_lock_remainder', 'the_index'), ('components_subject', 'moltbot_safe'),
                                   ('components_subject', 'control_plane'),
                                   ('components_subject', 'replay_bundle'), ('components_subject', 'odes'),
                                   ('components_subject', 'governance_evidence_pack'), ('components_subject', 'gax_imx_transport'),
                                   ('components_lock_remainder', 'constitutional_authority')})
        self.assertEqual(len(_pins.GENERATIONS), 23)  # original + RF-2..RF-16 + RF-18..RF-24; RF-1 (Index) and RF-17 (authority) are not seven-component profile generations
        self.assertEqual([g[0] for g in _pins.GENERATIONS], ["original-freeze"] + ["RF-%d" % i for i in range(2, 17)] + ["RF-%d" % i for i in range(18, 25)])

    def test_no_pin_literal_left_in_helpers(self):
        pinned = {s['sha'] for g in _pins.GROUPS for s in manifest().get(g, {}).values()} | {manifest()['identities']['hub']['head'],
                                                                                              'd17b8ac2b8445d385fbf51185a35914b2d8b835c'} | set(NEW.values())
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
        self.assertEqual(shas['moltbot_safe'], NEW['runtime'])
        self.assertEqual(shas['replay_bundle'], NEW['replay'])
        self.assertEqual(shas['odes'], NEW['odes'])
        self.assertEqual(shas['governance_evidence_pack'], NEW['evidence_pack'])
        self.assertEqual(shas['gax_imx_transport'], NEW['exchange'])
        self.assertEqual(shas['control_plane'], NEW['control_plane'])
        self.assertEqual(shas['action_manifest'], manifest()['components_subject']['action_manifest']['sha'])

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
