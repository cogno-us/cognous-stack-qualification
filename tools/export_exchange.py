"""Package actual serial trial evidence for reciprocal review; never run an effect.

SPDX-License-Identifier: Apache-2.0
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree

from trajectory_contract import ROOT, validate_record
from pristine_checkout import require_pristine
from verify_exchange import verify


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def export(run, output, hub, log):
    record = json.loads((run/'record.json').read_text())
    plan = json.loads((run/'plan.json').read_text())
    validate_record(record, plan, json.loads((ROOT/'scenarios/catalog.json').read_text()), artifact_root=run)
    for label, source in [('qualification', ROOT), ('hub', hub)]:
        expected = record['sources'][label]
        require_pristine(source,expected['commit'],label)
        if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip() != expected['commit']:
            raise ValueError('Source changed before export: '+label)
        for name, sha in expected['files'].items():
            if hashlib.sha256((source/name).read_bytes()).hexdigest() != sha:
                raise ValueError('Source bytes changed before export: '+name)
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(run, output/'native')
    shutil.copy2(ROOT/'tools/verify_exchange.py', output/'verify_export.py')
    for label, source in [('qualification',ROOT), ('hub',hub)]:
        paths = set(record['sources'][label]['files']) | {'LICENSE'}
        if (source/'NOTICE').exists(): paths.add('NOTICE')
        if label == 'qualification': paths |= {'tools/export_exchange.py','tools/verify_exchange.py','tools/requirements-ci.lock','tools/requirements-serial.txt'}
        for name in sorted(paths):
            destination = output/'evidence/source'/label/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source/name, destination)
    shutil.copy2(ROOT/'LICENSE', output/'LICENSE')
    write(output/'evidence/source-identities.json', record['sources'])
    write(output/'evidence/evaluator-calibration.json', record['calibration'])
    write(output/'evidence/dependencies.json', json.loads(subprocess.check_output([sys.executable,'-m','pip','list','--format=json'], text=True)))
    shutil.copy2(log, output/'evidence/serial-command.log')
    exemplar = json.loads((run/'trials/lost-ack-retry-1/trial.json').read_text())
    write(output/'fixture.json', {'variant':exemplar['variant'], 'clock':exemplar['clock'],
                                 'initial_observation':exemplar['case']['initial_observation'], 'requests':exemplar['requests']})
    write(output/'transport.json', {'attempts':exemplar['case']['attempts'], 'responses':exemplar['case']['responses'],
                                   'writer_entry':'NOT INSTRUMENTED; native duplicate admission is exercised'})
    write(output/'observation.json', exemplar['case']['observation'])
    write(output/'post_commit_readback.json', exemplar['post_commit_readback'])
    (output/'destination').mkdir()
    shutil.copy2(run/'trials/lost-ack-retry-1/destination.db', output/'destination/synthetic-destination.db')
    counts = Counter(c['result']['verdict'] for c in record['cases'])
    suite = ElementTree.Element('testsuite', name='actual-native-local-trials', tests=str(len(record['cases'])),
                                failures=str(len(record['cases'])-counts['PASS']), errors='0', skipped='0')
    for case in record['cases']:
        test = ElementTree.SubElement(suite,'testcase',classname=case['variant'],name=str(case['trial']))
        if case['result']['verdict'] != 'PASS':
            ElementTree.SubElement(test,'failure',message=case['result']['verdict']).text=json.dumps(case['result'])
    ElementTree.ElementTree(suite).write(output/'test-results.xml', encoding='utf-8', xml_declaration=True)
    (output/'README_FOR_JERRY.md').write_text('''# Cognous bounded native-local test evidence

This package contains actual synthetic SQLite executions: 18 named variants, two diagnostic repetitions each. See manifest.json for exact commits and the frozen profile. No paid model calls or production actions were made.

Verify using Python 3 standard library only:

    python verify_export.py .

The verifier checks every listed file, snapshots, native audit chains, state/attempt correlations and named local expectations. It does not rerun the original runtime, validate issuer signatures or certify cross-system interoperability. The complete semantic trajectory evaluator additionally requires the pinned dependencies and schemas retained in evidence/source/qualification; its source and native test runner are retained for inspection.

To rerun the original test battery, clone the qualification and hub repositories at manifest.sources commits into pristine separate directories; install the hash-locked hub tools/requirements-release.lock and qualification tools/requirements-ci.lock into an isolated Python environment. Run with PYTHONDONTWRITEBYTECODE=1:

    python qualification/tools/run_serial_qualification.py --hub hub --output new-native-result

Reproduction produces new keys and signatures, so identical output-byte hashes are not expected. Compare assertions and source identities. test-results.xml is generated from the actual retained trial outcomes, not a separate pytest rerun.

D04: the first acknowledgement is deliberately discarded after synchronous apply returned and a committed snapshot was read. The store is reopened, a distinct request/attempt is submitted for the same logical effect, and native admission returns duplicate with one effect retained. This is NOT writer-free reconciliation. Private writer entry is not instrumented. No process kill, power-loss, external financial settlement or delayed writer is exercised.

Important asymmetry: this Cognous fixture inserts the payload "synthetic" as one local effect. It is not Jerry's USD 100 to USD 90 refund fixture. No account balance/version mapping or matched-request comparative verdict is claimed. The same OS account remains trusted, despite the separate read-only observer process. Operational observer independence and full selected-stack acceptance are unestablished.

Replay and Evidence Pack exports for these native local receipt families are unsupported/NOT RUN. The native/ files are original records and a qualification sidecar, not renamed Replay or Evidence Pack records. Authority belongs to local synthetic fixture grants and keys; no institutional authority, SCQOS execution, production readiness, or release approval follows.

All raw state is synthetic. No private signing keys are exported; public Ed25519 registries and signed requests are retained where available. Approval-fixture HMAC keys are deliberately absent. Native audit hashes verify consistency, not signer authenticity. No external bundle/source has been copied into this archive. Public source retains original Apache-2.0 license and notices in evidence/source. Do not send this package automatically: owner review precedes any transmission.
''')
    (output/'CROSSWALK.md').write_text('''# Cognous native evidence crosswalk

| Shared requirement | Actual evidence | Scope/gap |
|---|---|---|
| Exact configuration | manifest.sources, native/plan.json, evidence/source/ | Nonselected native hub profiles; selected-lock component entries are context only |
| Intended effect | fixture.requests, native trial requests, effects.request | Request SHA-256 and native effect binding; payload is synthetic, not monetary refund |
| Authority/intervention | native trial events and SQLite objects | Local synthetic grants; revocation and approval variants recorded separately; no institutional authority claim |
| Attempt/acknowledgement | transport.json, native trial case.attempts | Stable effect, distinct command/nonce IDs; first D04 acknowledgement stays UNKNOWN |
| Commitment and fault placement | post_commit_readback.json and native/trials/lost-ack-retry-1/post_commit.db | Readback is taken after synchronous apply returned and before retry; no network-fault or physical crash witness |
| Destination consequence | observation.json and destination/synthetic-destination.db | One synthetic insertion; no fabricated balance or state-version equivalence |
| Recovery | native D04 responses[-1].result.duplicate and snapshots | Reopened-store duplicate admission; private writer-entry absence NOT ESTABLISHED |
| Observer | case.observation and read_only_verified | Separate process with write-denial probe; shared OS account remains trusted |
| Native exports | native events/responses/SQLite state | Replay/Evidence Pack adapters unsupported/NOT RUN for this family |
| Case outcomes | native/record.json, native/plan.json, test-results.xml | Named local assertions only; catalog acceptance unchanged |

Canonicalization: qualification digest uses UTF-8 JSON, sorted keys, compact separators, ensure_ascii=True and allow_nan=False. Native audit hash uses ensure_ascii=False over {seq,body,previous}; original native source is retained. State commitments cover {objects: business_objects, effects: effects}, excluding command/admin-sequence/checkpoint objects as documented in the runner. Request commitments cover the entire retained signed request. Native effects.request is the separate runtime projection of execute arguments excluding verifier_status and issuer_claims. Do not equate those two request digests. Hashes are unkeyed; signatures and legitimate authority are separate checks.

Each architecture establishes its own findings before comparison. The provided format supports reciprocal inspection; no SCQOS validator or REACHABLE assessment has been executed here. Missing native fields and mismatched action semantics remain explicit gaps.
''')
    manifest = {'format_version':'cognous-reciprocal-evidence/1', 'architecture':'Cognous native local hub fixtures',
                'run_id':output.name, 'created_at':datetime.now(timezone.utc).isoformat(), 'sources':record['sources'],
                'profile':record['profile'], 'scenario_ids':sorted({c['scenario_id'] for c in record['cases']}),
                'trials':len(record['cases']), 'counts':dict(counts), 'interoperability_verdict':'NOT TESTED',
                'issuer_authentication':'NOT VERIFIED BY PORTABLE VERIFIER',
                'readiness':'READY FOR SCOPED LOCAL EVIDENCE REVIEW; NOT MATCHED-REQUEST COMPARISON ACCEPTANCE',
                'artifacts':[]}
    for path in sorted(output.rglob('*')):
        if path.is_file():
            manifest['artifacts'].append({'file':path.relative_to(output).as_posix(), 'bytes':path.stat().st_size,
                                          'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    write(output/'manifest.json',manifest)
    result = verify(output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run','output','hub','log'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    export(args.run.resolve(), args.output.resolve(), args.hub.resolve(), args.log.resolve())
