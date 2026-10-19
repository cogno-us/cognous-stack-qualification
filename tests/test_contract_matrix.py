"""Unit tests for the contract-version compatibility matrix (suites/_contract_matrix.py).

The matrix replaces sha equality as the compatibility gate for components that sit on a boundary with a declared ODES
contract. These tests use synthetic vendored contract copies: the real components are not available to this repository's
own CI (the scenario run records the real matrix evaluation in every evidence file).
"""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'suites'))
import _contract_matrix as M  # noqa: E402

CONTRACT = 'execution-attempt-lifecycle'
VERSION = '0.1.0-draft'
REF_FILES = {'README.md': 'reference readme\n', 'schema.json': '{"reference": true}\n', 'validate.py': '# reference validator\n'}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def matrix():
    m = M.load_matrix()
    m = copy.deepcopy(m)
    ref = m['contracts'][CONTRACT]['versions'][VERSION]
    ref['files'] = {k: sha(v) for k, v in REF_FILES.items()}
    ref['reference_odes_commit'] = 'a' * 40
    return m


def vendor(base, name, *, role='producer', level='P', version=VERSION, contract=CONTRACT, files=None, extra=None, odes='a' * 40):
    """Write a component directory carrying a vendored contract copy plus its CONTRACT.json."""
    d = Path(base) / name / 'tests' / 'contracts' / CONTRACT
    d.mkdir(parents=True)
    content = dict(REF_FILES, **(files or {}))
    for rel, text in content.items():
        (d / rel).write_text(text)
    for rel, text in (extra or {}).items():
        (d / rel).write_text(text)
    listed = {rel: sha(text) for rel, text in content.items()}
    (d / 'CONTRACT.json').write_text(json.dumps({'contract': contract, 'contract_version': version, 'odes_commit': odes, 'role': role,
                                                  'conformance_level': level, 'files': listed}))
    return Path(base) / name


class Declarations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.m = matrix()

    def tearDown(self):
        self.tmp.cleanup()

    def comps(self, **kw):
        self.n = getattr(self, 'n', 0) + 1
        base = self.base / f'set{self.n}'
        out = {'runtime': vendor(base, 'runtime'), 'control_plane': vendor(base, 'control_plane'),
               'replay': vendor(base, 'replay', role='consumer', level='L')}
        out.update(kw)
        return out

    def rows(self, comps):
        return {r['boundary']: r for r in M.evaluate(comps, self.m)}

    def test_matching_declarations_conform_on_every_boundary(self):
        rows = M.evaluate(self.comps(), self.m)
        self.assertEqual([r['status'] for r in rows], ['conforms', 'conforms'])
        self.assertEqual(rows[0]['producer']['contract_version'], VERSION)
        self.assertEqual(M.require_matrix(self.comps(), self.m), rows)

    def test_missing_declaration_is_undeclared_not_conforming(self):
        comps = self.comps()
        (Path(comps['runtime']) / 'tests/contracts' / CONTRACT / 'CONTRACT.json').unlink()
        rows = self.rows(comps)
        self.assertEqual(rows['lifecycle-runtime-replay']['status'], M.UNDECLARED)
        self.assertEqual(rows['lifecycle-control-plane-replay']['status'], M.CONFORMS)
        with self.assertRaisesRegex(ValueError, 'lifecycle-runtime-replay undeclared'):
            M.require_matrix(comps, self.m)

    def test_component_absent_from_the_run_is_undeclared(self):
        comps = self.comps()
        del comps['replay']
        self.assertEqual({r['status'] for r in M.evaluate(comps, self.m)}, {M.UNDECLARED})

    def test_unknown_version_is_refused(self):
        comps = self.comps(runtime=vendor(self.base, 'rt2', version='0.2.0-draft'))
        row = self.rows(comps)['lifecycle-runtime-replay']
        self.assertEqual(row['status'], M.NONCONFORMING)
        self.assertTrue(any("declares version '0.2.0-draft'" in r for r in row['reasons']))

    def test_wrong_contract_role_and_level_are_refused(self):
        for kw, text in [({'contract': 'other-contract'}, "declares contract 'other-contract'"),
                         ({'role': 'consumer'}, "declares role 'consumer'"), ({'level': 'L'}, "conformance level 'L'"),
                         ({'level': 'S'}, "conformance level 'S'")]:
            with self.subTest(kw=kw):
                comps = self.comps(runtime=vendor(self.base, 'rt-' + next(iter(kw.values())), **kw))
                row = self.rows(comps)['lifecycle-runtime-replay']
                self.assertEqual(row['status'], M.NONCONFORMING)
                self.assertTrue(any(text in r for r in row['reasons']), row['reasons'])

    def test_consumer_level_floor_is_lower_than_producer_floor(self):
        comps = self.comps(replay=vendor(self.base, 'rp-s', role='consumer', level='S'))
        self.assertEqual(self.rows(comps)['lifecycle-runtime-replay']['status'], M.NONCONFORMING)
        comps = self.comps(replay=vendor(self.base, 'rp-p', role='consumer', level='P'))
        self.assertEqual(self.rows(comps)['lifecycle-runtime-replay']['status'], M.CONFORMS)

    def test_same_draft_version_string_with_different_content_is_refused(self):
        # The same 0.1.0-draft covered different content between ODES commits: a version string alone is not a declaration.
        comps = self.comps(runtime=vendor(self.base, 'rt-old', files={'schema.json': '{"older": true}\n'}, odes='d' * 40))
        row = self.rows(comps)['lifecycle-runtime-replay']
        self.assertEqual(row['status'], M.NONCONFORMING)
        self.assertTrue(any('schema.json differs from the reference' in r and 'dddddddd' in r for r in row['reasons']), row['reasons'])

    def test_vendored_copy_drift_is_refused(self):
        for mutate, text in [(lambda d: (d / 'validate.py').write_text('# edited\n'), 'modified: validate.py'),
                             (lambda d: (d / 'README.md').unlink(), 'missing: README.md'),
                             (lambda d: (d / 'extra.json').write_text('{}'), 'unlisted: extra.json')]:
            with self.subTest(text=text):
                comp = vendor(self.base, 'rt-' + text.split(': ')[0] + text.split(': ')[1], role='producer')
                mutate(comp / 'tests/contracts' / CONTRACT)
                row = self.rows(self.comps(runtime=comp))['lifecycle-runtime-replay']
                self.assertEqual(row['status'], M.NONCONFORMING)
                self.assertTrue(any(text in r for r in row['reasons']), row['reasons'])

    def test_bytecode_in_the_vendored_copy_is_not_drift(self):
        comp = vendor(self.base, 'rt-pyc', extra={})
        cache = comp / 'tests/contracts' / CONTRACT / '__pycache__'
        cache.mkdir()
        (cache / 'validate.cpython-312.pyc').write_bytes(b'x')
        self.assertEqual(self.rows(self.comps(runtime=comp))['lifecycle-runtime-replay']['status'], M.CONFORMS)

    def test_malformed_declaration_is_refused(self):
        comp = vendor(self.base, 'rt-bad')
        (comp / 'tests/contracts' / CONTRACT / 'CONTRACT.json').write_text('{not json')
        row = self.rows(self.comps(runtime=comp))['lifecycle-runtime-replay']
        self.assertEqual(row['status'], M.NONCONFORMING)
        self.assertTrue(any('unreadable' in r for r in row['reasons']))

    def test_version_compatibility_rules(self):
        self.assertTrue(M.versions_compatible('0.1.0-draft', '0.1.0-draft'))
        self.assertFalse(M.versions_compatible('0.1.0-draft', '0.1.1-draft'))  # drafts: identical only
        self.assertFalse(M.versions_compatible('0.1.0-draft', '0.1.0'))
        self.assertTrue(M.versions_compatible('1.0.0', '1.0.0'))
        self.assertTrue(M.versions_compatible('1.0.0', '1.2.0'))   # consumer newer minor
        self.assertFalse(M.versions_compatible('1.2.0', '1.0.0'))  # consumer older minor
        self.assertFalse(M.versions_compatible('1.0.0', '2.0.0'))  # major differs
        self.assertFalse(M.versions_compatible(None, '1.0.0'))
        self.assertFalse(M.versions_compatible('one', 'two'))

    def test_declares_reports_version_and_level(self):
        comps = self.comps()
        self.assertEqual(M.declares(comps['runtime'], CONTRACT, self.m), (VERSION, 'P'))
        self.assertIsNone(M.declares(self.base / 'nowhere', CONTRACT, self.m))


class Admission(unittest.TestCase):
    """admit_components: pristine always, matrix for declared boundaries, the sha pin for everything else."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.m = matrix()
        for name in ('runtime', 'control_plane'):
            vendor(self.base, name)
        vendor(self.base, 'replay', role='consumer', level='L')
        for name in ('evidence_pack', 'odes', 'exchange', 'manifest'):
            (self.base / name).mkdir()
        self.heads = {n: ('0' if n in ('runtime', 'control_plane', 'replay') else '1') * 40 for n in
                      ('runtime', 'control_plane', 'replay', 'evidence_pack', 'odes', 'exchange', 'manifest')}
        self.pristine_calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def admit(self, tested, names=None):
        profile = {n: {'revision': tested.get(n, self.heads[n])} for n in self.heads}

        def pristine(path, revision, label=None):
            self.pristine_calls.append((Path(path).name, revision))
            if revision != self.heads[Path(path).name]:
                raise ValueError(f'{label}: source revision mismatch')
            return revision
        return M.admit_components(self.base, profile, names or list(self.heads), pristine, lambda p: self.heads[Path(p).name], self.m)

    def test_governed_component_at_an_untested_revision_is_admitted_and_flagged(self):
        gates, rows = self.admit({'runtime': 'f' * 40, 'replay': 'e' * 40})
        self.assertEqual(gates['runtime'], {'gate': 'contract-matrix', 'revision': '0' * 40, 'tested_revision': 'f' * 40, 'tested_revision_match': False})
        self.assertEqual(gates['replay']['gate'], 'contract-matrix')
        self.assertFalse(gates['replay']['tested_revision_match'])
        self.assertTrue(gates['control_plane']['tested_revision_match'])
        self.assertEqual({r['status'] for r in rows}, {M.CONFORMS})
        # a dirty tree is still refused: the checkout is verified clean at the revision it actually has
        self.assertIn(('runtime', '0' * 40), self.pristine_calls)

    def test_sha_pinned_component_must_equal_its_pin(self):
        gates, _ = self.admit({})
        for name in ('evidence_pack', 'odes', 'exchange', 'manifest'):
            self.assertEqual(gates[name]['gate'], 'sha-pin')
        with self.assertRaisesRegex(ValueError, 'odes: source revision mismatch'):
            self.admit({'odes': 'f' * 40})

    def test_nonconforming_declaration_is_refused_even_at_the_tested_revision(self):
        (self.base / 'runtime/tests/contracts' / CONTRACT / 'validate.py').write_text('# edited\n')
        with self.assertRaisesRegex(ValueError, 'runtime: contract matrix refuses the checkout'):
            self.admit({})

    def test_undeclared_component_falls_back_to_the_old_sha_gate(self):
        (self.base / 'runtime/tests/contracts' / CONTRACT / 'CONTRACT.json').unlink()
        gates, rows = self.admit({})
        self.assertEqual(gates['runtime']['gate'], 'sha-pin')
        self.assertEqual(gates['replay']['gate'], 'sha-pin')  # its boundary with the runtime is undeclared
        self.assertEqual(gates['control_plane']['gate'], 'contract-matrix')
        with self.assertRaisesRegex(ValueError, 'runtime: source revision mismatch'):
            self.admit({'runtime': 'f' * 40})


class RealMatrixFile(unittest.TestCase):
    def test_matrix_is_well_formed(self):
        m = M.load_matrix()
        self.assertEqual(m['schema'], 'cognous.contract-matrix/1')
        for contract, spec in m['contracts'].items():
            for version, ref in spec['versions'].items():
                self.assertEqual(set(ref['files']), {'README.md', 'schema.json', 'validate.py'})
                self.assertEqual(len(ref['reference_odes_commit']), 40)
        for b in m['boundaries']:
            self.assertIn(b['contract'], m['contracts'])
            self.assertIn(b['producer_min_level'], M.LEVEL_ORDER)
            self.assertIn(b['consumer_min_level'], M.LEVEL_ORDER)
        self.assertEqual(M.governed_components(m), ['control_plane', 'replay', 'runtime'])
        self.assertEqual(M.sha_pinned_components(m), ['evidence_pack', 'exchange', 'manifest', 'odes'])
        self.assertFalse(set(M.governed_components(m)) & set(M.sha_pinned_components(m)))

    def test_every_profile_component_has_a_gate(self):
        m = M.load_matrix()
        profile = json.loads((ROOT / 'process/security-runtime-f5b-20261016-r10.json').read_text())
        self.assertEqual(set(profile['components']), set(M.governed_components(m)) | set(M.sha_pinned_components(m)))


if __name__ == '__main__':
    unittest.main()
