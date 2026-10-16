"""Read-only, standard-library verification of a Cognous exchange evidence package.

SPDX-License-Identifier: Apache-2.0
Verifies bytes, native audit/state correlations and named local assertions.
Does not authenticate issuers, rerun the runtime or certify full interoperability.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sqlite3
import sys
from xml.etree import ElementTree


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key] = value
    return result


def load(path):
    def invalid(value):
        raise ValueError('Nonfinite JSON value: '+value)
    return json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def snapshot(path):
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1', uri=True) as db:
        db.row_factory = sqlite3.Row
        require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'SQLite integrity')
        effects = [dict(row) for row in db.execute('SELECT * FROM effects ORDER BY id')]
        objects = [dict(row) for row in db.execute("SELECT * FROM objects WHERE kind NOT IN ('command','admin-sequence','checkpoint') ORDER BY kind,id")]
        events = [{'seq':row[0], 'body':json.loads(row[1]), 'previous':row[2], 'head':row[3]}
                  for row in db.execute('SELECT seq,body,previous,head FROM events ORDER BY seq')]
    return {'effects':effects, 'objects':objects, 'events':events}


def check_case(root, trial):
    case = trial['case']
    expected = trial['variant']['expected']
    where = root/'native/trials'/f"{case['variant']}-{case['trial']}"
    initial = snapshot(where/'initial.db')
    final = snapshot(where/'destination.db')
    for stored, observed in [(initial, case['initial_observation']), (final, case['observation'])]:
        require(stored['effects'] == observed['effects'], 'SQLite effect/readback disagreement')
        require(stored['objects'] == observed['business_objects'], 'SQLite objects/readback disagreement')
        require(digest({'objects':stored['objects'], 'effects':stored['effects']}) == observed['business_digest'], 'State commitment')
        require(observed['effect_count'] == len(stored['effects']), 'Observed multiplicity')
        require(observed['read_only_verified'] is True, 'Missing observer write-denial control')
    require(not initial['effects'] and case['reset_verified'] is True, 'Reset not verified')
    require(case['initial_business_digest'] == case['initial_observation']['business_digest'], 'Initial commitment')
    require(final['events'] == case['events'], 'SQLite audit/readback disagreement')
    previous = '0'*64
    for seq, event in enumerate(case['events'], 1):
        canonical = json.dumps({'seq':seq, 'body':event['body'], 'previous':previous},
                               sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        require(event['seq'] == seq and event['previous'] == previous and
                event['head'] == hashlib.sha256(canonical).hexdigest(), 'Native audit chain')
        previous = event['head']
    attempts = case['attempts']
    require(len(attempts) == len(trial['requests']), 'Attempt/request count')
    require(len({a['attempt_id'] for a in attempts}) == len(attempts), 'Attempt identity collision')
    for request, attempt in zip(trial['requests'], attempts):
        require(digest(request) == attempt['request_digest'], 'Request commitment')
        body = request['body']
        require(attempt['attempt_id'] == body.get('id', body.get('nonce')), 'Attempt/request identity')
    correlated = [e for e in case['events'] if e['body'].get('request_digest') == attempts[-1]['request_digest']]
    require(bool(correlated) and correlated[-1]['body']['status'] == case['responses'][-1]['status'], 'Outcome audit correlation')
    response = case['responses'][-1]
    require(response.get('reason', response.get('status')) == expected['response'], 'Unexpected admission response')
    require(len(final['effects']) == expected['effect_count'], 'Unexpected effect count')
    if 'payload' in expected:
        payloads = [e['payload'] if case['variant'].startswith('approval-') else json.loads(e['payload']) for e in final['effects']]
        require(payloads == [expected['payload']], 'Unexpected payload')
    if expected.get('state_unchanged'):
        require(case['observation']['business_digest'] == case['initial_business_digest'], 'Unexpected business state change')
    if expected.get('recovery'):
        require(len(attempts) == 2 and attempts[0]['acknowledgement'] == 'UNKNOWN', 'Historical acknowledgement')
        require(len({a['effect_id'] for a in attempts}) == 1, 'Recovery effect identity')
        committed = snapshot(where/'post_commit.db')
        require(committed['effects'] == final['effects'] and len(committed['effects']) == 1, 'Recovery duplicated or changed effect')
        require(trial['post_commit_readback']['effects'] == committed['effects'], 'Pre-retry readback')
        require(response['result']['duplicate'] is True, 'Native deduplication not established')
    require(case['result']['verdict'] == 'PASS' and not case['result']['failures'] and not case['result']['missing'], 'Nonpassing trial')


def verify(root):
    root = Path(root).resolve()
    manifest = load(root/'manifest.json')
    require(manifest['format_version'] == 'cognous-reciprocal-evidence/1', 'Package version')
    files = {}
    for item in manifest['artifacts']:
        name = item['file']
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts and str(path) == name and '\\' not in name and name not in ('manifest.json','.'), 'Unsafe path')
        require(name not in files, 'Duplicate manifest entry')
        files[name] = item
    actual = set()
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Symlink in package')
        if path.is_file() and path != root/'manifest.json':
            actual.add(path.relative_to(root).as_posix())
    require(actual == set(files), 'Missing or unlisted payload file')
    for name, item in files.items():
        data = (root/name).read_bytes()
        require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'File bytes changed: '+name)
        if name.endswith('.json'):
            load(root/name)
    record = load(root/'native/record.json')
    plan = load(root/'native/plan.json')
    require(record['plan_sha256'] == digest(plan) == record['profile']['sha256'], 'Frozen plan commitment')
    require(record['sources'] == manifest['sources'], 'Source identity mapping')
    require(record['profile']['selected'] is False and record['assurance']['production_authorized'] is False and record['assurance']['release_authorized'] is False, 'Unexpected authorization claim')
    require(manifest['interoperability_verdict'] == 'NOT TESTED' and manifest['issuer_authentication'] == 'NOT VERIFIED BY PORTABLE VERIFIER', 'Unsupported external assurance')
    expected = {(v['id'], i) for v in plan['variants'] for i in range(1, plan['repetitions']+1)}
    seen = set()
    for case in record['cases']:
        key = (case['variant'], case['trial'])
        require(key not in seen and key in expected, 'Duplicate or unknown trial')
        seen.add(key)
        trial = load(root/'native/trials'/f"{key[0]}-{key[1]}"/'trial.json')
        require(trial['case'] == case, 'Native record/trial disagreement')
        require(trial['variant'] == next(v for v in plan['variants'] if v['id'] == key[0]), 'Variant expectation changed')
        check_case(root, trial)
    require(seen == expected, 'Missing trial')
    for name, sha in record['artifacts'].items():
        require(files['native/'+name]['sha256'] == sha, 'Native artifact commitment')
    calibration = record['calibration']
    require(calibration['critical_defects_detected'] == calibration['critical_defects_total'] == 6 and calibration['false_alarms'] == 0 and calibration['missing_observation_inconclusive'], 'Calibration outcome')
    require(calibration['clean_control']['verdict'] == 'PASS', 'Clean calibration control')
    for name, probe in calibration['probes'].items():
        require(probe['verdict'] == ('INCONCLUSIVE' if name == 'missing-observation' else 'FAIL'), 'Calibration probe')
    exemplar = load(root/'native/trials/lost-ack-retry-1/trial.json')
    require(load(root/'transport.json') == {'attempts':exemplar['case']['attempts'], 'responses':exemplar['case']['responses'], 'writer_entry':'NOT INSTRUMENTED; native duplicate admission is exercised'}, 'Transport mapping')
    require(load(root/'observation.json') == exemplar['case']['observation'], 'Exemplar observation')
    require(load(root/'post_commit_readback.json') == exemplar['post_commit_readback'], 'Exemplar pre-retry observation')
    require(load(root/'fixture.json') == {'variant':exemplar['variant'], 'clock':exemplar['clock'], 'initial_observation':exemplar['case']['initial_observation'], 'requests':exemplar['requests']}, 'Fixture mapping')
    require((root/'destination/synthetic-destination.db').read_bytes() == (root/'native/trials/lost-ack-retry-1/destination.db').read_bytes(), 'Exemplar database copy')
    suite = ElementTree.parse(root/'test-results.xml').getroot()
    require(int(suite.attrib['tests']) == len(seen) and int(suite.attrib['failures']) == 0 and int(suite.attrib['errors']) == 0, 'JUnit summary')
    require({(e.attrib['classname'], int(e.attrib['name'])) for e in suite.findall('testcase')} == seen, 'JUnit trial identities')
    return {'package_bytes':'PASS', 'sqlite_and_native_correlations':'PASS', 'named_local_trials':len(seen),
            'recovery':'native duplicate admission; writer-free reconciliation NOT ESTABLISHED',
            'interoperability':'NOT TESTED', 'issuer_authentication':'NOT VERIFIED',
            'observer_independence':'same trusted OS account, separate read-only process'}


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 2, 'usage: python verify_export.py <package-directory>')
        print(json.dumps(verify(sys.argv[1]), indent=2, sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, ElementTree.ParseError) as exc:
        print('VERIFICATION FAILED: '+str(exc), file=sys.stderr)
        raise SystemExit(1)
