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


class StrictStatusAndSha(unittest.TestCase):
    def test_status_forms_in_the_real_log_are_all_applied(self):
        entries = json.loads((VAL / 'refreeze-log.json').read_text())['entries']
        self.assertTrue(entries)
        for e in entries:
            self.assertTrue(_pins.is_applied(e), e['id'])

    def test_status_with_a_lookalike_prefix_is_not_applied(self):
        for status in ('APPLIED-REVERTED: withdrawn', 'APPLIED-REVERTED (x)', 'APPLIEDX', 'APPLIED (x', 'APPLIED  (x)', 'APPLIED-IN-WORKFLOWX', 'applied'):
            self.assertFalse(_pins.is_applied({'status': status}), status)
        for status in ('APPLIED', 'APPLIED (qualified: x)', 'APPLIED-IN-WORKFLOW', 'APPLIED-IN-WORKFLOW (pending full controller run g6-r10)'):
            self.assertTrue(_pins.is_applied({'status': status}), status)

    def test_a_reverted_entry_does_not_move_the_pin(self):
        m = manifest()
        frm = m['components_lock_remainder']['the_index']['sha']
        r, applied = _pins.apply_overlay(m, log(entry('the_index', frm, A, status='APPLIED-REVERTED: withdrawn')))
        self.assertEqual(applied, [])
        self.assertEqual(r['components_lock_remainder']['the_index']['sha'], frm)

    def test_to_sha_must_be_40_lowercase_hex(self):
        m = manifest()
        frm = m['components_lock_remainder']['the_index']['sha']
        for bad in ('main', 'a' * 39, 'A' * 40, 'a' * 41, 'g' * 40, ' ' + 'a' * 40, 'a' * 40 + '\n'):
            with self.assertRaisesRegex(_pins.RefreezeError, 'to_sha'):
                _pins.apply_overlay(m, log(entry('the_index', frm, bad, status='APPLIED')))

    def test_the_real_log_still_selects_the_same_profile_and_pins(self):
        rl = _pins.load_refreeze_log()
        self.assertEqual(len(_pins.applied_entries(rl)), len(rl['entries']))
        self.assertEqual(_pins.select_profile(rl), _pins.PROFILE_RELPATH)


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
R6_PINS = dict(R5_PINS, odes='81979784117588d199da6fdceb05264f8c5903a6', exchange='ba9fa16052a3d99b08d1d31b4f5dca2bdef0c608')
# Programme 2 documentation and alignment fixes (r7): ODES with the P4/P2 profile versions documented (#98) and the exchange with the p2 profile's ODES pin aligned (#39) (RF-25, RF-26)
R7_PINS = dict(R5_PINS, odes='e2cbc0dcee795d1ba100e028107fdfe6d0bc9e21', exchange='06f58c329fe5221a0bfed47e9af9dc02405a93c3')
# Programme 2 documentation cleanup and alignment (r8): ODES with the README, conformance and decision-36 documentation corrections (#99) and the exchange with the p2 profile's ODES pin aligned (#40) (RF-27, RF-28)
R8_PINS = dict(R5_PINS, odes='cdf704c88bb6542e3f1121a5ceb6cb03fc7d6a52', exchange='8721e8d358baaec3663b9183e09a14ae4e464e7c')
# Programme 2 current mains (r9): eight pins move together (RF-29..RF-36); the action manifest moves for the first time since the original freeze
R9_PINS = {'control_plane': '2bac7875391cad0a431fa0d75208b7ade39743e3', 'runtime': 'c4a05883266b815f39d97cbf2240406647985147',
           'replay': '2a7963b18d96eb2e9e4fdb1a09c7588cf5c0ef00', 'odes': '4bf1212860f4d7c5d4f26758485f91402ffed426',
           'evidence_pack': '80e24650bb089d3a0cb9c0063c5b4bcc4a436123', 'exchange': 'bf314f3884e60629c844b1d6cb248f4d76b31c1a',
           'manifest': 'ff5490828b2bf7f6a976da209f3f533701855687'}
# Programme 2 runtime-fix tuple (r10): five pins move together (RF-37..RF-41); control plane and manifest stay at r9's
R10_PINS = dict(R9_PINS, runtime='6b16962db140590b808f02b5c2cb11a217aec46f', replay='6a6a477495ac24e813f12bb0fe314acfe8bac9cf', evidence_pack='fd030615a782a064b89c57e8e40d7f220f99ff9e',
           odes='2893d935f1cb60d1854a3802cc32d739ddfd4efb', exchange='fdc2a410383396553254a39ae641c88b78ee13f1')
# Scan 3 and 4 current mains (r12): all seven pins moved together (RF-47..RF-53); the registry moved outside the profile (RF-54)
R12_PINS = {'control_plane': 'e77fe0ee8714617899592528e660a80fbb2e864a', 'runtime': 'cab4d9abc651c7efbafb429798d2c908f048bf5c',
       'replay': '53c0cd60d565ea1797ed0be87a2310c5b68b24f6', 'odes': 'dc5cf19d405ce885b287cde2f78519d3109b9ae6',
       'evidence_pack': '99ba3211450b25a18007b4b62907b072fe05c964', 'exchange': '81b0877e1a9a82c2a61b1bafe631a4691556355f',
       'manifest': 'fa170815ef96a54c233d0dd9da821b60debabf8b'}
# Scan 5 and 6 and wave 7 current mains with the Programme 2 re-ties (r13): six pins move together (RF-55..RF-60); the manifest stays at r12's (RF-48);
# the registry moves outside the profile (RF-61)
NEW = {'control_plane': '0a41faa972699f7ec3063967a14cd9bdd3e67d27', 'runtime': 'ec728da6dc301a664b331ac8986afd6e850a1273',
       'replay': '028f63d1c001f99580583888fa4b4e46d77a267b', 'odes': 'e86a25a1d660e74533337d38744e2934200a50ae',
       'evidence_pack': 'a3ebbb90559a44a88855139a182649d3792bb1ca', 'exchange': '7f7569b02666b99669a9fca61117ca1f4bce5f0d',
       'manifest': 'fa170815ef96a54c233d0dd9da821b60debabf8b'}
INDEX_PIN = 'b2485998b88256c2b322493800d1fba076814cbd'  # RF-61: registry main after scans 5 and 6 and wave 7; the index pin of the r13 candidate
INDEX_R12 = '8e10387f8b7808e5dd1965fea38b74141761d7a6'  # RF-54: the registry pin of g7-r10
INDEX_R10 = 'd25afe601454d60c561a4726e31c31d1ec40d99b'  # RF-44: the registry pin of g5-r10 and g6-r10
R8_MANIFEST = '2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e'  # the action manifest pin of the original freeze, unchanged through r8
R1_PINS = {'runtime': '4a83b175d2ef0e65a7ee22a0513bb94a5fdf3a6f', 'replay': '0cfe7a6319930bccad3e9027a1dfbe3d6e29d657',
           'odes': '4e6d11691b9dea56a70026b6519159cf0e0ffd8b', 'evidence_pack': '683246e05d291308211778ec48045df65466461f',
           'exchange': 'da95378228b8f3205af49a86e68ba722961f6af0'}
R1 = 'process/security-runtime-f5b-20261016-r1.json'
R2 = 'process/security-runtime-f5b-20261016-r2.json'
R3 = 'process/security-runtime-f5b-20261016-r3.json'
R4 = 'process/security-runtime-f5b-20261016-r4.json'
R5 = 'process/security-runtime-f5b-20261016-r5.json'
R6 = 'process/security-runtime-f5b-20261016-r6.json'
R7 = 'process/security-runtime-f5b-20261016-r7.json'
R8 = 'process/security-runtime-f5b-20261016-r8.json'
R9 = 'process/security-runtime-f5b-20261016-r9.json'
R10 = 'process/security-runtime-f5b-20261016-r10.json'
R11 = 'process/security-runtime-f5b-20261016-r11.json'
R12 = 'process/security-runtime-f5b-20261016-r12.json'
R13 = 'process/security-runtime-f5b-20261016-r13.json'
AUTH_OLD = 'fb3d97938969a89e149e8ff8db2756091d1233fc'
AUTH_R4 = 'cbc39e79a1328a74b6cb1aba0cd1e5149164865d'  # RF-17: institutional-governance main with the F-15 fix (#51); the authority pin of r4..r8
AUTH_R10 = '0124adcdceb8cee973f0631adb2639f14472df63'  # RF-36: institutional-governance commit before docs-only #59 (a descendant of d40522af); the authority pin of r9 and r10
AUTH_R11 = 'd4462697197d6eb4e76bbfc3d712c8c1dab27884'  # RF-45: merge commit of institutional-governance #60 (lineage validator fixes); the authority pin of r11
AUTH_NEW = '9b5ab721ae0684150e466c01e9d0d59ec61c3e00'  # RF-46: merge commit of institutional-governance #63 (scan 3 and 4 lineage hardening); the authority pin of r12 and r13


class CurrentPins(unittest.TestCase):
    """Resolved pins equal the pins in force: the freeze manifest plus RF-1 (Index), RF-2..RF-16 (the P4 generation of the decoupling plan), RF-17 (the constitutional authority, F-15), RF-18..RF-22 (the Programme 2 generation), RF-23, RF-24 (the ODES and exchange compatibility gap fixes) and RF-25, RF-26 (the ODES documentation fix and the exchange pin alignment) and RF-27, RF-28 (the ODES documentation cleanup and the second exchange pin alignment) and RF-29..RF-36 (the eight current mains: control plane, runtime, Replay, evidence pack, ODES, exchange, action manifest and the constitutional authority) and RF-37..RF-41 (the runtime fix and the four pins that follow it: Replay, evidence pack, ODES, exchange) and RF-45 (the authority lineage fixes) and RF-46..RF-53 (the scan 3 and 4 mains of the authority and the seven components) and RF-54 (the registry, outside the profile) and RF-55..RF-60 (the scan 5 and 6 and wave 7 mains and the Programme 2 re-ties of six components) and RF-61 (the registry, outside the profile)."""
    def test_resolved_pins_equal_todays_literals(self):
        self.assertEqual(_pins.FROZEN_HUB, '8517818fbf817897aacfb6fe7898c22aea46fd95')
        self.assertEqual(_pins.FROZEN_RUNTIME, NEW['runtime'])
        self.assertEqual(_pins.FROZEN_CONTROL_PLANE, NEW['control_plane'])
        self.assertEqual(_pins.FROZEN_REPLAY, NEW['replay'])
        self.assertEqual(_pins.FROZEN_EVIDENCE_PACK, NEW['evidence_pack'])
        self.assertEqual(_pins.FROZEN_ODES, NEW['odes'])
        self.assertEqual(_pins.FROZEN_EXCHANGE, NEW['exchange'])
        self.assertEqual(_pins.FROZEN_MANIFEST_COMPONENT, NEW['manifest'])
        self.assertEqual(_pins.ORIGINAL_MANIFEST['components_subject']['action_manifest']['sha'], R8_MANIFEST)  # the original freeze is never edited
        self.assertEqual(_pins.FROZEN_BITREP, '981036c315856c71207984797b0c4e48d3b3921d')  # RF-43 applied through the overlay
        self.assertEqual(_pins.OLD_INDEX_PIN, 'd5e45d275cb301d9684b543e93b05997991d1cf2')
        self.assertEqual(_pins.FROZEN_INDEX, INDEX_PIN)  # RF-1, RF-42, RF-44, RF-54 and RF-61 applied through the overlay
        self.assertEqual(_pins.REFROZEN_INDEX_PIN, INDEX_PIN)
        self.assertEqual(_pins.C14_PINS, {'control_plane': NEW['control_plane'],
                                          'moltbot_safe': NEW['runtime'], 'replay': NEW['replay']})
        self.assertEqual(_pins.PROFILE_RELPATH, R13)  # the newest profile whose refreeze_ids are all applied
        self.assertEqual(_pins.RESOLVED_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'], AUTH_NEW)  # RF-17, RF-36, RF-45 and RF-46 through the overlay
        self.assertEqual(_pins.ORIGINAL_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'], AUTH_OLD)

    def test_profile_pins_equal_the_r13_qualification_profile(self):
        prof = json.loads((ROOT / R13).read_text())
        self.assertEqual(_pins.PROFILE_PINS, {k: v['revision'] for k, v in prof['components'].items()})

    def test_controller_workflow_v1_profile_equals_the_profile_the_overlay_selects(self):
        import re
        text = (ROOT / '.github/workflows/v1-validation.yml').read_text()
        found = re.findall(r'^  V1_PROFILE: (\S+)$', text, flags=re.M)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0], _pins.select_profile(_pins.load_refreeze_log()))
        self.assertEqual(found[0], _pins.PROFILE_RELPATH)

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
                                                          'revision': AUTH_R4, 'previous_revision': AUTH_OLD})
        rf17 = next(e for e in _pins.load_refreeze_log()['entries'] if e['id'] == 'RF-17')
        self.assertEqual(r4['constitutional_authority']['revision'], rf17['to_sha'])  # r4 is the profile of RF-17; the later RF-36 moves the pin on
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
            self.assertEqual(r6['components'][name]['revision'], R6_PINS[name])
            self.assertEqual(r5['components'][name]['revision'], R5_PINS[name])
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'exchange_compatibility_profile'):
            r5.pop(key, None); r6.pop(key)
        for name in ('odes', 'exchange'):
            r6['components'][name]['revision'] = r5['components'][name]['revision']
        self.assertEqual(r6, r5)  # control plane, runtime, Replay, evidence pack, manifest, authority and the suite generation are r5's

    def test_r7_profile_is_r6_with_only_the_odes_and_exchange_pins_changed(self):
        r6 = json.loads((ROOT / R6).read_text())
        r7 = json.loads((ROOT / R7).read_text())
        self.assertEqual(r7['profile_id'], 'security-runtime-f5b-20261016-r7')
        self.assertEqual(r7['supersedes_profile'], R6)
        self.assertEqual(r7['refreeze_ids'], ['RF-%d' % i for i in range(2, 27)])
        self.assertEqual((r7['suite_generation'], r7['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r7[key], False)
        self.assertEqual(r7['constitutional_authority'], r6['constitutional_authority'])
        for name in ('odes', 'exchange'):
            self.assertEqual(r7['components'][name]['revision'], R7_PINS[name])
            self.assertEqual(r6['components'][name]['revision'], R6_PINS[name])
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations'):
            r6.pop(key, None); r7.pop(key)
        for name in ('odes', 'exchange'):
            r7['components'][name]['revision'] = r6['components'][name]['revision']
        self.assertEqual(r7, r6)  # control plane, runtime, Replay, evidence pack, manifest, authority, the suite generation and the exchange compatibility profile are r6's

    def test_r8_profile_is_r7_with_only_the_odes_and_exchange_pins_changed(self):
        r7 = json.loads((ROOT / R7).read_text())
        r8 = json.loads((ROOT / R8).read_text())
        self.assertEqual(r8['profile_id'], 'security-runtime-f5b-20261016-r8')
        self.assertEqual(r8['supersedes_profile'], R7)
        self.assertEqual(r8['refreeze_ids'], ['RF-%d' % i for i in range(2, 29)])
        self.assertEqual((r8['suite_generation'], r8['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r8[key], False)
        self.assertEqual(r8['constitutional_authority'], r7['constitutional_authority'])
        for name in ('odes', 'exchange'):
            self.assertEqual(r8['components'][name]['revision'], R8_PINS[name])
            self.assertEqual(r7['components'][name]['revision'], R7_PINS[name])
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations'):
            r7.pop(key, None); r8.pop(key)
        for name in ('odes', 'exchange'):
            r8['components'][name]['revision'] = r7['components'][name]['revision']
        self.assertEqual(r8, r7)  # control plane, runtime, Replay, evidence pack, manifest, authority, the suite generation and the exchange compatibility profile are r7's

    def test_r9_profile_is_r8_with_only_the_eight_component_pins_changed(self):
        r8 = json.loads((ROOT / R8).read_text())
        r9 = json.loads((ROOT / R9).read_text())
        self.assertEqual(r9['profile_id'], 'security-runtime-f5b-20261016-r9')
        self.assertEqual(r9['supersedes_profile'], R8)
        self.assertEqual(r9['refreeze_ids'], ['RF-%d' % i for i in range(2, 37)])
        self.assertEqual((r9['suite_generation'], r9['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r9[key], False)
        self.assertEqual(r9['constitutional_authority'], {'repository': 'cogno-us/cognous-institutional-governance',
                                                          'revision': AUTH_R10, 'previous_revision': AUTH_R4})
        self.assertEqual(r9['constitutional_authority']['revision'], AUTH_R10)  # RF-36 is r9's authority pin; RF-45 moves it on
        self.assertEqual(r8['constitutional_authority']['revision'], AUTH_R4)
        for name in ('control_plane', 'runtime', 'replay', 'odes', 'evidence_pack', 'exchange', 'manifest'):
            self.assertEqual(r9['components'][name]['revision'], R9_PINS[name])
            self.assertNotEqual(r8['components'][name]['revision'], R9_PINS[name])
        for name, rev in R8_PINS.items():
            self.assertEqual(r8['components'][name]['revision'], rev)
        self.assertEqual(r8['components']['manifest']['revision'], R8_MANIFEST)
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'constitutional_authority'):
            r8.pop(key, None); r9.pop(key)
        for name in ('control_plane', 'runtime', 'replay', 'odes', 'evidence_pack', 'exchange', 'manifest'):
            r9['components'][name]['revision'] = r8['components'][name]['revision']
        self.assertEqual(r9, r8)  # the suite generation and the exchange compatibility profile are r8's

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
        self.assertEqual(_pins.select_profile(ids(24)), R6)          # r7 needs RF-25, RF-26 too
        self.assertEqual(_pins.select_profile(ids(25)), R6)
        self.assertEqual(_pins.select_profile(ids(26)), R7)          # r8 needs RF-27, RF-28 too
        self.assertEqual(_pins.select_profile(ids(27)), R7)
        self.assertEqual(_pins.select_profile(ids(28)), R8)          # r9 needs RF-29..RF-36 too
        self.assertEqual(_pins.select_profile(ids(35)), R8)
        self.assertEqual(_pins.select_profile(ids(36)), R9)          # r10 needs RF-37..RF-41 too
        self.assertEqual(_pins.select_profile(ids(40)), R9)
        self.assertEqual(_pins.select_profile(ids(41)), R10)
        self.assertEqual(_pins.select_profile(ids(44)), R10)         # r11 needs RF-45 too
        self.assertEqual(_pins.select_profile(ids(45)), R11)
        self.assertEqual(_pins.select_profile(ids(46)), R11)         # r12 needs RF-46..RF-53 too
        self.assertEqual(_pins.select_profile(ids(52)), R11)
        self.assertEqual(_pins.select_profile(ids(53)), R12)         # RF-54 (the registry) is outside the profile
        self.assertEqual(_pins.select_profile(ids(54)), R12)
        self.assertEqual(_pins.select_profile(ids(55)), R12)         # r13 needs RF-55..RF-60 too
        self.assertEqual(_pins.select_profile(ids(59)), R12)
        self.assertEqual(_pins.select_profile(ids(60)), R13)         # RF-61 (the registry) is outside the profile
        self.assertEqual(_pins.select_profile(ids(61)), R13)
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
        partial = ids(26); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R6)
        partial = ids(28); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R7)
        partial = ids(36); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R8)
        partial = ids(41); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R9)
        partial = ids(53); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R11)
        partial = ids(60); partial['entries'][-1]['status'] = 'PROPOSED'
        self.assertEqual(_pins.select_profile(partial), R12)

    def test_r10_profile_is_r9_with_only_the_five_component_pins_changed(self):
        r9 = json.loads((ROOT / R9).read_text())
        r10 = json.loads((ROOT / R10).read_text())
        self.assertEqual(r10['profile_id'], 'security-runtime-f5b-20261016-r10')
        self.assertEqual(r10['supersedes_profile'], R9)
        self.assertEqual(r10['refreeze_ids'], ['RF-%d' % i for i in range(2, 42)])
        self.assertEqual((r10['suite_generation'], r10['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r10[key], False)
        self.assertEqual(r10['constitutional_authority'], r9['constitutional_authority'])  # unchanged: RF-36 stays the authority pin
        self.assertEqual(r10['constitutional_authority']['revision'], AUTH_R10)  # RF-36 is r10's authority pin; RF-45 moves it on
        for name in ('runtime', 'replay', 'odes', 'evidence_pack', 'exchange'):
            self.assertEqual(r10['components'][name]['revision'], R10_PINS[name])
            self.assertNotEqual(r9['components'][name]['revision'], R10_PINS[name])
            self.assertEqual(r9['components'][name]['revision'], R9_PINS[name])
        for name in ('control_plane', 'manifest'):  # these two stay at r9's pins
            self.assertEqual(r10['components'][name]['revision'], R10_PINS[name])
            self.assertEqual(r9['components'][name]['revision'], R9_PINS[name])
        self.assertEqual(r10['limitations'][:-1], r9['limitations'])  # r10 only appends one statement
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations'):
            r9.pop(key); r10.pop(key)
        for name in ('runtime', 'replay', 'odes', 'evidence_pack', 'exchange'):
            r10['components'][name]['revision'] = r9['components'][name]['revision']
        self.assertEqual(r10, r9)  # control plane, manifest, authority, the suite generation and the exchange compatibility profile are r9's

    def test_r11_profile_is_r10_with_only_the_authority_pin_changed(self):
        r10 = json.loads((ROOT / R10).read_text())
        r11 = json.loads((ROOT / R11).read_text())
        self.assertEqual(r11['profile_id'], 'security-runtime-f5b-20261016-r11')
        self.assertEqual(r11['supersedes_profile'], R10)
        self.assertEqual(r11['refreeze_ids'], ['RF-%d' % i for i in range(2, 42)] + ['RF-45'])  # RF-42..RF-44 move components outside the profile
        self.assertEqual((r11['suite_generation'], r11['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r11[key], False)
        self.assertEqual(r11['constitutional_authority'], {'repository': 'cogno-us/cognous-institutional-governance',
                                                           'revision': AUTH_R11, 'previous_revision': AUTH_R10})
        self.assertEqual(r11['constitutional_authority']['revision'], AUTH_R11)  # RF-45 is r11's authority pin; RF-46 moves it on
        self.assertEqual(r11['components'], r10['components'])  # the seven component pins are r10's
        self.assertEqual(r11['limitations'][:-1], r10['limitations'])  # r11 only appends one statement
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'constitutional_authority'):
            r10.pop(key); r11.pop(key)
        self.assertEqual(r11, r10)  # components, the suite generation and the exchange compatibility profile are r10's

    def test_r12_profile_moves_the_seven_components_and_the_authority_and_lists_every_subject(self):
        r11 = json.loads((ROOT / R11).read_text())
        r12 = json.loads((ROOT / R12).read_text())
        self.assertEqual(r12['profile_id'], 'security-runtime-f5b-20261016-r12')
        self.assertEqual(r12['supersedes_profile'], R11)
        self.assertEqual(r12['refreeze_ids'], ['RF-%d' % i for i in range(2, 42)] + ['RF-45'] + ['RF-%d' % i for i in range(46, 54)])  # RF-42..RF-44 and RF-54 move components outside the profile
        self.assertEqual((r12['suite_generation'], r12['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r12[key], False)
        self.assertEqual(r12['constitutional_authority'], {'repository': 'cogno-us/cognous-institutional-governance',
                                                           'revision': AUTH_NEW, 'previous_revision': AUTH_R11})
        self.assertEqual(r12['constitutional_authority']['revision'],
                         _pins.RESOLVED_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'])  # E-3: equal to the pin in force
        self.assertEqual(set(r12['components']), set(R12_PINS))  # every subject component is listed
        for name, rev in R12_PINS.items():
            self.assertEqual(r12['components'][name]['revision'], rev)
            self.assertNotEqual(r11['components'][name]['revision'], rev)
        self.assertEqual({k: v['revision'] for k, v in r12['components'].items()}, {k: v for k, v in R12_PINS.items()})  # retained unedited; r13 is the profile in force
        self.assertEqual(r12['limitations'][:-1], r11['limitations'])  # r12 only appends one statement
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations', 'constitutional_authority'):
            r11.pop(key); r12.pop(key)
        for name in R12_PINS:
            r12['components'][name]['revision'] = r11['components'][name]['revision']
        self.assertEqual(r12, r11)  # the suite generation, the exchange compatibility profile and every other member are r11's

    def test_r13_profile_moves_six_components_keeps_the_manifest_and_the_authority_and_lists_every_subject(self):
        r12 = json.loads((ROOT / R12).read_text())
        r13 = json.loads((ROOT / R13).read_text())
        self.assertEqual(r13['profile_id'], 'security-runtime-f5b-20261016-r13')
        self.assertEqual(r13['supersedes_profile'], R12)
        # RF-47 and RF-49..RF-53 are superseded by RF-55..RF-60; RF-46 (authority) and RF-48 (manifest) stay in force; RF-54 and RF-61 move the registry outside the profile
        self.assertEqual(r13['refreeze_ids'], ['RF-%d' % i for i in range(2, 42)] + ['RF-45', 'RF-46', 'RF-48'] + ['RF-%d' % i for i in range(55, 61)])
        self.assertEqual((r13['suite_generation'], r13['exchange_compatibility_profile']), ('p2', 'security-runtime-p2-20261018'))
        for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
            self.assertIs(r13[key], False)
        self.assertEqual(r13['constitutional_authority'], r12['constitutional_authority'])  # unchanged: RF-46 stays the authority pin
        self.assertEqual(r13['constitutional_authority']['revision'], AUTH_NEW)
        self.assertEqual(r13['constitutional_authority']['revision'],
                         _pins.RESOLVED_MANIFEST['components_lock_remainder']['constitutional_authority']['sha'])  # E-3: equal to the pin in force
        self.assertEqual(set(r13['components']), set(NEW))  # every subject component is listed
        for name, rev in NEW.items():
            self.assertEqual(r13['components'][name]['revision'], rev)
            if name == 'manifest':
                self.assertEqual(r12['components'][name]['revision'], rev)  # RF-48 stays: the manifest does not move
            else:
                self.assertNotEqual(r12['components'][name]['revision'], rev)
        self.assertEqual({k: v['revision'] for k, v in r13['components'].items()}, _pins.PROFILE_PINS)
        self.assertEqual(r13['limitations'][:-1], r12['limitations'])  # r13 only appends one statement
        for key in ('profile_id', 'supersedes_profile', 'refreeze_ids', 'note', 'limitations'):
            r12.pop(key); r13.pop(key)
        for name in NEW:
            r13['components'][name]['revision'] = r12['components'][name]['revision']
        self.assertEqual(r13, r12)  # the suite generation, the exchange compatibility profile, the authority and every other member are r12's

    def test_registry_move_is_outside_the_profile_and_the_attestation_pin_is_unchanged(self):
        log = _pins.load_refreeze_log()
        rf = {e['id']: e for e in log['entries']}
        self.assertEqual((rf['RF-54']['component'], rf['RF-54']['from_sha'], rf['RF-54']['to_sha']), ('the_index', INDEX_R10, INDEX_R12))
        self.assertEqual((rf['RF-61']['component'], rf['RF-61']['from_sha'], rf['RF-61']['to_sha']), ('the_index', INDEX_R12, INDEX_PIN))
        self.assertEqual(_pins.FROZEN_BITREP, '981036c315856c71207984797b0c4e48d3b3921d')  # RF-43 stays in force
        self.assertEqual([e['id'] for e in log['entries'] if e['component'] == 'bitrep'], ['RF-43'])

    def test_r12_entries_carry_the_owner_authority_and_the_pins_in_force_at_the_previous_head(self):
        rf = {e['id']: e for e in _pins.load_refreeze_log()['entries']}
        expect = {'RF-46': ('constitutional_authority', AUTH_R11, AUTH_NEW), 'RF-47': ('control_plane', R10_PINS['control_plane'], R12_PINS['control_plane']),
                  'RF-48': ('action_manifest', R10_PINS['manifest'], R12_PINS['manifest']), 'RF-49': ('moltbot_safe', R10_PINS['runtime'], R12_PINS['runtime']),
                  'RF-50': ('gax_imx_transport', R10_PINS['exchange'], R12_PINS['exchange']), 'RF-51': ('replay_bundle', R10_PINS['replay'], R12_PINS['replay']),
                  'RF-52': ('governance_evidence_pack', R10_PINS['evidence_pack'], R12_PINS['evidence_pack']), 'RF-53': ('odes', R10_PINS['odes'], R12_PINS['odes']),
                  'RF-54': ('the_index', INDEX_R10, INDEX_R12)}
        for eid, (comp, frm, to) in expect.items():
            e = rf[eid]
            self.assertEqual((e['component'], e['from_sha'], e['to_sha']), (comp, frm, to), eid)
            self.assertIn('do the fixes and merge. Then do all the refreeze etc.', e['authorised'], eid)
            self.assertIn('probed', e['status'], eid)  # g7-r10 (run 39642578239) probed them; restated by the r13 refreeze (RF-45 precedent: not marked qualified)
            self.assertIn('not marked qualified', e['status'], eid)
            self.assertIn('39642578239', e['status'], eid)
            self.assertEqual(e['status'].startswith('APPLIED-IN-WORKFLOW (pending full controller run g8-r10;'), eid in ('RF-46', 'RF-48'), eid)  # authority and manifest stay in force in r13

    def test_r13_entries_carry_the_owner_authority_and_the_pins_in_force_at_the_previous_head(self):
        rf = {e['id']: e for e in _pins.load_refreeze_log()['entries']}
        expect = {'RF-55': ('control_plane', R12_PINS['control_plane'], NEW['control_plane']), 'RF-56': ('moltbot_safe', R12_PINS['runtime'], NEW['runtime']),
                  'RF-57': ('replay_bundle', R12_PINS['replay'], NEW['replay']), 'RF-58': ('governance_evidence_pack', R12_PINS['evidence_pack'], NEW['evidence_pack']),
                  'RF-59': ('odes', R12_PINS['odes'], NEW['odes']), 'RF-60': ('gax_imx_transport', R12_PINS['exchange'], NEW['exchange']),
                  'RF-61': ('the_index', INDEX_R12, INDEX_PIN)}
        for eid, (comp, frm, to) in expect.items():
            e = rf[eid]
            self.assertEqual((e['component'], e['from_sha'], e['to_sha']), (comp, frm, to), eid)
            self.assertIn("don't refreeze anything. I want engineering fixes, then spot checks, then refreeze, then release.", e['authorised'], eid)
            self.assertEqual(e['status'], 'APPLIED-IN-WORKFLOW (pending full controller run g8-r10)', eid)
            for key in ('reason', 'behaviour_changes', 'open_item', 'historical_results_at_from_sha'):
                self.assertTrue(e[key], (eid, key))
            self.assertIn('39642578239', e['historical_results_at_from_sha'], eid)  # g7-r10 at the earlier pin is historical, not transferred
        self.assertEqual([e['id'] for e in rf.values() if 'pending' in e['status']], ['RF-46', 'RF-48'] + ['RF-%d' % i for i in range(55, 62)])
        self.assertIn('164 codes', rf['RF-55']['behaviour_changes'][1])  # invalid_manifest joins the 0.2 registry (CP #81)

    def test_original_profile_and_freeze_manifest_are_unedited(self):
        import hashlib
        frozen = manifest()['qualification_file_hashes'][_pins.ORIGINAL_PROFILE]
        self.assertEqual(hashlib.sha256((ROOT / _pins.ORIGINAL_PROFILE).read_bytes()).hexdigest(), frozen)
        self.assertEqual(manifest()['components_subject']['moltbot_safe']['sha'], 'e20f92e104aba2ba6ad06120d8549c6170eaf63f')

    def test_repo_log_applies_cleanly_and_changes_the_index_the_authority_and_the_seven_components(self):
        m = manifest()
        r, applied = _pins.apply_overlay(m, _pins.load_refreeze_log())
        self.assertEqual([a[0] for a in applied], ['RF-%d' % i for i in range(1, 62)])
        changed = {(g, k) for g in _pins.GROUPS for k in m.get(g, {}) if m[g][k]['sha'] != r[g][k]['sha']}
        self.assertEqual(changed, {('components_lock_remainder', 'the_index'), ('components_lock_remainder', 'bitrep'), ('components_subject', 'moltbot_safe'),
                                   ('components_subject', 'control_plane'),
                                   ('components_subject', 'replay_bundle'), ('components_subject', 'odes'),
                                   ('components_subject', 'governance_evidence_pack'), ('components_subject', 'gax_imx_transport'),
                                   ('components_subject', 'action_manifest'),
                                   ('components_lock_remainder', 'constitutional_authority')})
        self.assertEqual(len(_pins.GENERATIONS), 52)  # original + RF-2..RF-16 + RF-18..RF-35 + RF-37..RF-41 + RF-47..RF-53 + RF-55..RF-60; RF-1, RF-42, RF-44, RF-54 and RF-61 (Index), RF-43 (bitrep), RF-17, RF-36, RF-45 and RF-46 (authority) are not seven-component profile generations
        self.assertEqual([g[0] for g in _pins.GENERATIONS], ["original-freeze"] + ["RF-%d" % i for i in range(2, 17)] + ["RF-%d" % i for i in range(18, 36)] + ["RF-%d" % i for i in range(37, 42)] + ["RF-%d" % i for i in range(47, 54)] + ["RF-%d" % i for i in range(55, 61)])

    def test_no_pin_literal_left_in_helpers(self):
        pinned = {s['sha'] for g in _pins.GROUPS for s in manifest().get(g, {}).values()} | {manifest()['identities']['hub']['head'],
                                                                                              INDEX_PIN, '981036c315856c71207984797b0c4e48d3b3921d'} | set(NEW.values())
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
        self.assertEqual(shas['the_index'], INDEX_PIN)
        self.assertEqual(shas['moltbot_safe'], NEW['runtime'])
        self.assertEqual(shas['replay_bundle'], NEW['replay'])
        self.assertEqual(shas['odes'], NEW['odes'])
        self.assertEqual(shas['governance_evidence_pack'], NEW['evidence_pack'])
        self.assertEqual(shas['gax_imx_transport'], NEW['exchange'])
        self.assertEqual(shas['control_plane'], NEW['control_plane'])
        self.assertEqual(shas['action_manifest'], NEW['manifest'])
        self.assertNotEqual(shas['action_manifest'], manifest()['components_subject']['action_manifest']['sha'])  # RF-35 moved it
        self.assertNotEqual(shas['action_manifest'], R9_PINS['manifest'])  # RF-48 moves it on from RF-29..RF-36 (and stays in r13)
        self.assertEqual(shas['constitutional_authority'], AUTH_NEW)  # RF-46 (unchanged in r13)

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
