"""Re-verify a security-runtime repetition and audit native Exchange rows read-only.

SPDX-License-Identifier: Apache-2.0
Emits GitHub notice annotations: a compact summary, the native audit and the
raw junit.xml, stdout.log and run.json-without-member-map (gzip+base64), so
hosted counts, hashes and destination rows can be read through the REST API
when the artifact archive itself cannot be downloaded. Writes nothing into the
repetition directory. Not a substitute for the archived native files.
"""
from __future__ import annotations
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

CASES = ('valid', 'revoked', 'lost_ack', 'crash', 'ownership')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


SIDECARS = ('-wal', '-shm', '-journal')


def require_no_sidecars(db):
    """Fail closed: immutable reads would silently ignore committed rows in a -wal."""
    db = Path(db)
    present = [db.name + suffix for suffix in SIDECARS if Path(str(db) + suffix).exists()]
    if present:
        raise ValueError(f'{db}: SQLite sidecar files present ({", ".join(present)}); refusing an immutable read that could miss committed rows')
    return []


def rows(db, query):
    require_no_sidecars(db)
    # Safe only because no sidecar exists: the main file is then the complete
    # committed state, and immutable=1 neither locks nor creates side files.
    con = sqlite3.connect(f'file:{db}?mode=ro&immutable=1', uri=True)
    try:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(query)]
    finally:
        con.close()


def audit(run):
    names = [c.get('name') for c in ET.parse(run/'junit.xml').getroot().iter('testcase')
             if 'test_exchange_repaired_chain' in c.get('name', '')]
    out = []
    for index, case in enumerate(CASES):
        if case not in names[index]:
            raise ValueError(f'unexpected Exchange case order: {names}')
        case_dir = run/'native'/f'test_exchange_repaired_chain_a{index}'
        db = case_dir/'target/sqlite/refunds.sqlite3'
        effects = rows(db, 'select effect_id,state from effects order by effect_id')
        attempts = rows(db, 'select attempt_id,effect_id from attempts order by attempt_id')
        failures = rows(db, 'select failure_class,reason_code,stage,attempt_id from failure_records_v1 order by failure_id')
        first = json.loads((case_dir/'exchange-first.json').read_text())['execution']
        second_path = case_dir/'exchange-second.json'
        second = json.loads(second_path.read_text())['execution'] if second_path.exists() else None
        expected = 0 if case == 'revoked' else 1
        ok = len(effects) == expected and len(attempts) == expected
        if case == 'revoked':
            ok = ok and not first.get('attempted') and len(failures) >= 1
        else:
            ok = ok and first.get('effect_id') == effects[0]['effect_id'] == attempts[0]['effect_id']
        if case in {'lost_ack', 'crash', 'ownership'}:
            ok = ok and second is not None and not second.get('attempted') and not second.get('newly_executed', False) \
                and second.get('effect_id') == first.get('effect_id')
        out.append({'case': case, 'db_sha256': sha(db), 'sqlite_sidecars': require_no_sidecars(db),
            'read_mode': 'immutable main file; no -wal/-shm/-journal present', 'effects': effects, 'attempts': attempts,
            'failure_records': failures, 'first_attempted': first.get('attempted'),
            'first_attempt_status': first.get('attempt_status'),
            'second_attempted': None if second is None else second.get('attempted'),
            'second_newly_executed': None if second is None else second.get('newly_executed', False),
            'second_attempt_status': None if second is None else second.get('attempt_status'),
            'redelivery_same_effect': None if second is None else second.get('effect_id') == first.get('effect_id'),
            'ok': ok})
    return out


def summarize(run):
    report = json.loads((run/'run.json').read_text())
    evidence = report['evidence']
    actual = {p.relative_to(run).as_posix(): sha(p) for p in sorted(run.rglob('*')) if p.is_file() and p != run/'run.json'}
    return {'counts': report['raw_junit_counts'], 'returncode': report['returncode'],
        'bounded_cases_passed': report['bounded_cases_passed'],
        'candidate_integration_passed': report['candidate_integration_passed'],
        'qualification_head': report['qualification_head'],
        'qualification_worktree_dirty': report['qualification_worktree_dirty'],
        'profile_file': report.get('profile_file'), 'suite_generation': report.get('suite_generation'),
        'exchange_compatibility_profile': report.get('exchange_compatibility_profile'),
        'source_revisions': {k: [v['revision'], v['tree']] for k, v in report['source_revisions'].items()},
        'source_hashes': report['source_hashes'], 'python': report['python'].split()[0],
        'evidence_members': len(evidence), 'evidence_manifest_sha256': canonical(evidence),
        'members_reverified': actual == evidence,
        'run_json_sha256': sha(run/'run.json'), 'junit_sha256': sha(run/'junit.xml'),
        'stdout_sha256': sha(run/'stdout.log')}


def packed(data):
    # mtime=0 keeps the encoding deterministic for identical bytes.
    return base64.b64encode(gzip.compress(data, mtime=0)).decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    run = args.run
    summary = summarize(run); cases = audit(run)
    report = json.loads((run/'run.json').read_text()); report.pop('evidence')
    ok = summary['members_reverified'] and summary['bounded_cases_passed'] and all(c['ok'] for c in cases)
    notices = [('summary', json.dumps(summary, sort_keys=True, separators=(',', ':'))),
        ('native audit', json.dumps(cases, sort_keys=True, separators=(',', ':'))),
        ('junit.xml gzip-base64', packed((run/'junit.xml').read_bytes())),
        ('stdout.log gzip-base64', packed((run/'stdout.log').read_bytes())),
        ('run.json without evidence map gzip-base64', packed(json.dumps(report, indent=2).encode()))]
    for title, body in notices:
        print(f'::notice title={run.name} {title}::{body}')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
