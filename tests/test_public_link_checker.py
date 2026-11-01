import importlib.util
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('public_links',Path(__file__).resolve().parents[1]/'tools/check_public_links.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PublicLinks(unittest.TestCase):
    def test_private_targets_and_credentials_rejected(self):
        for url in ('http://github.com','https://user:pass@github.com','https://github.com:444'):
            with self.assertRaises(ValueError):m.safe_url(url)
        with patch.object(socket,'getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(ValueError):m.safe_url('https://github.com')
    def test_public_targets_allowed_and_fragment_not_claimed(self):
        with patch.object(socket,'getaddrinfo',return_value=[(2,1,6,'',('140.82.114.3',443))]):
            self.assertEqual(m.safe_url('https://github.com/a#anchor'),'https://github.com/a')
    def test_unavailable_is_not_pass(self):
        with patch.object(m,'safe_url',side_effect=ValueError('unavailable')):
            self.assertEqual(m.check('https://example.invalid')['disposition'],'unverified_network_or_target')
    def test_navigation_extracts_sources_without_uploading_file_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'doc.md').write_text('[x](https://github.com/o/r)\n')
            self.assertEqual(m.links(root,['doc.md']),{'https://github.com/o/r':['doc.md']})
            with self.assertRaises(ValueError):m.links(root,['../outside'])

    def test_proxy_resolution_fallback_is_allowlisted_only(self):
        with patch.object(socket,'getaddrinfo',side_effect=socket.gaierror()):
            self.assertEqual(m.safe_url('https://github.com/a'),'https://github.com/a')
            with self.assertRaises(ValueError):m.safe_url('https://unknown.invalid')
