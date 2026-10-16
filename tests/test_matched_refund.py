"""The matched account adapter must conserve cents and reject stale state."""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_matched_refund import ADAPTER_SQL, readback


class MatchedAccountTests(unittest.TestCase):
    def test_exact_debit_and_stale_version_refusal_are_atomic(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.db'
            with sqlite3.connect(path) as db:
                db.executescript('CREATE TABLE effects(effect_id TEXT PRIMARY KEY,target TEXT,amount REAL,unit TEXT,payload_json TEXT);CREATE TABLE attempts(attempt_id TEXT);'+ADAPTER_SQL)
                db.execute("INSERT INTO account VALUES('synthetic-wallet:refund-demo-001',10000,1)")
                db.execute("INSERT INTO effects VALUES('effect:synthetic-refund-001','synthetic-wallet:refund-demo-001',10,'USD',?)",('{"refund_cents":1000,"expected_state_version":1,"currency":"USD","effect_id":"effect:synthetic-refund-001"}',))
                db.commit()
                self.assertEqual(db.execute('SELECT balance_cents,version FROM account').fetchone(),(9000,2))
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("INSERT INTO effects VALUES('another','synthetic-wallet:refund-demo-001',10,'USD',?)",('{"refund_cents":1000,"expected_state_version":1,"currency":"USD","effect_id":"another"}',))
                self.assertEqual(db.execute('SELECT count(*) FROM effects').fetchone()[0],1)
            observed=readback(path)
            self.assertEqual(observed['account']['balance_cents'],9000)
            self.assertEqual(len(observed['writer_effects']),1)
            self.assertTrue(observed['read_only_verified'])


if __name__=='__main__':unittest.main()
