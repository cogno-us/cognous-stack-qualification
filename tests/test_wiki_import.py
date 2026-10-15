"""Meaningful rejection tests for the upstream import boundary, using synthetic pages."""
import copy
import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('sync', Path(__file__).resolve().parents[1] / 'tools/sync_ai_security_wiki.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class ImportBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.page = self.root / 'source/10_Test_Case_Library/L06-fixture.md'
        self.page.parent.mkdir(parents=True)
        self.page.write_text('---\ntitle: "Synthetic fixture"\nauthor: Test Author\ncoauthors: Test Coauthor\n---\n\n### TC-L06-001: Synthetic case\n\n[Control](../control.md)\n\n**Procedure**\n\n1. Use a synthetic sink.\n')
        (self.root / 'LICENSE').write_text('Attribution-ShareAlike 4.0 International\nSynthetic license fixture for parser tests only.\n')
        (self.root / 'README.md').write_text('Synthetic fixture\n')
        (self.root / 'AUTHORS').write_text('Test Author\n')
        self.commit()
        self.policy = {'source_commit': self.git('rev-parse', 'HEAD').strip(), 'approved_license_sha256': hashlib.sha256((self.root / 'LICENSE').read_bytes()).hexdigest(), 'source_glob': 'source/10_Test_Case_Library/*.md'}

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True, stderr=subprocess.DEVNULL)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def test_license_change_is_blocked(self):
        (self.root / 'LICENSE').write_text('Changed license')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'LICENSE changed'):
            sync.build(self.root, self.policy, True)

    def test_missing_author_is_blocked(self):
        self.page.write_text(self.page.read_text().replace('author: Test Author\n', '').replace('coauthors: Test Coauthor\n', ''))
        self.commit()
        with self.assertRaisesRegex(ValueError, 'Missing author'):
            sync.build(self.root, self.policy, True)

    def test_removed_credit_is_blocked(self):
        policy = copy.deepcopy(self.policy)
        policy['pages'] = [{'path': 'source/10_Test_Case_Library/L06-fixture.md', 'authors': ['Test Author', 'Former Contributor']}]
        with self.assertRaisesRegex(ValueError, 'Attribution removed'):
            sync.build(self.root, policy)

    def test_moved_case_cannot_drop_prior_credit(self):
        policy = copy.deepcopy(self.policy)
        policy['pages'] = [{'path': 'source/10_Test_Case_Library/old-name.md', 'authors': ['Former Contributor'], 'case_ids': ['TC-L06-001']}]
        with self.assertRaisesRegex(ValueError, 'Attribution removed from case'):
            sync.build(self.root, policy)

    def test_removed_case_requires_review(self):
        policy = dict(self.policy, case_ids=['TC-L06-001', 'TC-L06-002'])
        with self.assertRaisesRegex(ValueError, 'manual retirement review'):
            sync.build(self.root, policy)

    def test_duplicate_case_is_blocked(self):
        self.page.write_text(self.page.read_text() + '\n### TC-L06-001: Duplicate\n')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'Duplicate source test ID'):
            sync.build(self.root, self.policy, True)

    def test_new_revision_requires_explicit_update(self):
        (self.root / 'README.md').write_text('Changed fixture metadata')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'revision differs'):
            sync.build(self.root, self.policy)

    def test_source_must_be_clean(self):
        self.page.write_text(self.page.read_text() + '\nUncommitted data\n')
        with self.assertRaisesRegex(ValueError, 'must be clean'):
            sync.build(self.root, self.policy)

    def test_import_is_deterministic_and_preserves_credit_and_pins(self):
        first = sync.build(self.root, self.policy)
        self.assertEqual(first, sync.build(self.root, self.policy))
        text = first[Path('scenarios/ai-security-wiki/pages/L06-fixture.md')].decode()
        self.assertTrue(text.startswith('---\n'))
        self.assertIn('Test Author', text)
        self.assertIn('Test Coauthor', text)
        self.assertIn('/blob/' + self.policy['source_commit'] + '/source/control.md', text)
        self.assertIn('SPDX-License-Identifier: CC-BY-SA-4.0', text)


if __name__ == '__main__':
    unittest.main()
