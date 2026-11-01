"""Snapshot retention and portable verification must reject incomplete evidence."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_serial_qualification import retain_snapshot
from verify_exchange import load, snapshot, verify


class ExchangeTests(unittest.TestCase):
    def test_backup_incorporates_committed_wal_and_is_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source.db';saved=root/'saved.db'
            with sqlite3.connect(source) as db:
                db.execute('PRAGMA journal_mode=WAL')
                db.executescript('CREATE TABLE objects(kind TEXT,id TEXT,body TEXT);CREATE TABLE effects(id TEXT,payload TEXT);CREATE TABLE events(seq INTEGER,body TEXT,previous TEXT,head TEXT);')
                db.execute("INSERT INTO effects VALUES('effect','synthetic')");db.commit()
                retain_snapshot(source,saved)
                db.execute("DELETE FROM effects");db.commit()
            before=hashlib.sha256(saved.read_bytes()).hexdigest()
            self.assertEqual(snapshot(saved)['effects'],[{'id':'effect','payload':'synthetic'}])
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(),before)
            self.assertFalse(Path(str(saved)+'-wal').exists())

    def test_strict_json_rejects_duplicates_and_nonfinite_values(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bad.json'
            for value in ('{"x":1,"x":2}','{"x":NaN}'):
                path.write_text(value)
                with self.assertRaises(ValueError):load(path)

    def test_verifier_rejects_missing_unlisted_changed_and_unsafe_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);payload=root/'payload.txt';payload.write_text('actual')
            entry={'file':'payload.txt','bytes':6,'sha256':hashlib.sha256(b'actual').hexdigest()}
            for entries,pattern in [([], 'Missing or unlisted'),
                                    ([{**entry,'sha256':'0'*64}], 'File bytes changed'),
                                    ([{**entry,'file':'../payload.txt'}], 'Unsafe path'),
                                    ([entry,entry], 'Duplicate manifest entry')]:
                (root/'manifest.json').write_text(json.dumps({'format_version':'cognous-reciprocal-evidence/1','artifacts':entries}))
                with self.assertRaisesRegex(ValueError,pattern):verify(root)
            payload.unlink()
            (root/'manifest.json').write_text(json.dumps({'format_version':'cognous-reciprocal-evidence/1','artifacts':[entry]}))
            with self.assertRaisesRegex(ValueError,'Missing or unlisted'):verify(root)


if __name__=='__main__':unittest.main()
