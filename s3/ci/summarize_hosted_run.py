#!/usr/bin/env python3
"""Evidence/summary helper for the hosted S3 C3 observation (.github/workflows/security-wiki-s3-current-tuple.yml).

SPDX-License-Identifier: Apache-2.0
Non-authorizing. Reads what the workflow steps and s3/run_wiki_s3.py left behind, writes ONLY into --hosted, never into the repository,
the component checkouts or --out. It does not run, rerun or alter any test, does not change expectations, and does not decide security
verdicts: the PASS/FAIL/BLOCKED column is a junit-derived preliminary classification of this one hosted observation (C3), separate from
C1 and C2, developer evidence only, not independent qualification.

    python s3/ci/summarize_hosted_run.py --hosted DIR --out RUNDIR --components DIR [--step-summary FILE]

Classification (junit): passed -> PASS; failure/error whose text shows host resource exhaustion (ENOSPC / "No space left on device" / pytest tmpdir creation failure) or a fixture setup error (case not reached) or a
skipped testcase -> BLOCKED; any other failure/error -> FAIL. Failing security cases do NOT make job_ok false. job_ok is false (and the
workflow gate step fails loudly) only if: the tuple guard did not run or refused; the dry check did not pass; the runner did not exit 0;
run.json/junit are missing; the junit testcase count or the collect-only count is not 41; a checkout was not pristine after the run.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED = 41
NAMES = ('control_plane', 'runtime', 'replay', 'evidence_pack', 'odes', 'exchange', 'manifest', 'registry')
BLOCK_MARKS = ('No space left on device', 'ENOSPC', 'errno 28', 'Errno 28', 'could not create numbered dir', 'failed on setup')


def read(p, default=''):
    try:
        return Path(p).read_text(errors='replace')
    except OSError:
        return default


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120).stdout.strip()
    except Exception as e:  # recorded, not hidden
        return f'UNAVAILABLE: {type(e).__name__}'


def rc_of(path):
    s = read(path).strip()
    return int(s) if s.lstrip('-').isdigit() else None


def classify(case):
    for tag in ('failure', 'error'):
        el = case.find(tag)
        if el is not None:
            text = f"{el.get('message') or ''}\n{el.text or ''}"
            first = (el.get('message') or el.text or '').strip().splitlines()[0][:300] if (el.get('message') or el.text) else ''
            return ('BLOCKED' if any(m in text for m in BLOCK_MARKS) else 'FAIL'), tag.upper(), first
    if case.find('skipped') is not None:
        el = case.find('skipped')
        return 'BLOCKED', 'SKIPPED', (el.get('message') or '')[:300]
    return 'PASS', 'PASS', ''


def node_id(case):
    return case.get('classname', '').replace('.', '/') + '.py::' + case.get('name', '')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--hosted', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--components', type=Path, required=True)
    ap.add_argument('--step-summary', type=Path, default=None)
    a = ap.parse_args(argv)
    H, raw = a.hosted, a.out / 'raw'
    H.mkdir(parents=True, exist_ok=True)
    problems = []

    # guard preflight (explicit call by the workflow; the runner calls the guard itself once Worker B's integration is on the branch)
    g_rc = rc_of(H / 'guard.rc')
    guard = {'label': 'workflow-level explicit call of s3/s3_tuple_guard.py before the run', 'returncode': g_rc,
             'outcome': 'OK' if g_rc == 0 else ('REFUSED' if g_rc is not None else 'NOT_RUN'),
             'stdout': read(H / 'guard.out'), 'stderr': read(H / 'guard.err'),
             'guard_sha256': sha256('s3/s3_tuple_guard.py') if Path('s3/s3_tuple_guard.py').exists() else None,
             'note': 'The runner writes its own guard result into the run output directory once the guard-integration branch is merged; that file, if present, is uploaded unchanged under run/.'}
    (H / 'guard-result-preflight.json').write_text(json.dumps(guard, indent=2) + '\n')
    if g_rc != 0:
        problems.append(f'tuple guard {guard["outcome"]} (rc={g_rc})')

    d_rc = rc_of(H / 'dry.rc')
    dry = {}
    try:
        dry = json.loads(read(H / 'dry.out') or '{}')
    except ValueError:
        pass
    (H / 'dry-check-result.json').write_text(json.dumps({'returncode': d_rc, 'stdout_json': dry, 'stderr': read(H / 'dry.err')}, indent=2) + '\n')
    if d_rc != 0 or dry.get('collected') != EXPECTED or dry.get('executed') != 0:
        problems.append(f'dry check did not pass (rc={d_rc}, collected={dry.get("collected")})')

    r_rc = rc_of(H / 'runner.rc')
    if r_rc != 0:
        problems.append(f'runner exit code {r_rc} (harness could not run to a complete 41-case record)')

    # run record
    run_json, rows, counts = {}, [], {'PASS': 0, 'FAIL': 0, 'BLOCKED': 0}
    junit_n = collect_n = None
    try:
        run_json = json.loads(read(raw / 'run.json') or '{}')
    except ValueError:
        pass
    if not run_json:
        problems.append('raw/run.json missing or unreadable')
    elif not run_json.get('checkouts_after_run_pristine', False):
        problems.append('component checkouts not pristine after the run: ' + '; '.join(run_json.get('checkout_problems', [])))
    collect_n = sum(1 for l in read(raw / 'collect-only.txt').splitlines() if '::' in l)
    try:
        cases = list(ET.parse(raw / 'junit.xml').getroot().iter('testcase'))
    except (ET.ParseError, OSError):
        cases = []
        problems.append('raw/junit.xml missing or unreadable')
    junit_n = len(cases)
    if junit_n != EXPECTED or collect_n != EXPECTED:
        problems.append(f'collected/executed != {EXPECTED} (collect-only {collect_n}, junit testcases {junit_n})')
    try:
        obs = json.loads(read(raw / 'obs.json') or '{}')
    except ValueError:
        obs = {}
    for c in cases:
        nid = node_id(c)
        verdict, jstat, boundary = classify(c)
        counts[verdict] += 1
        o = obs.get(nid, {})
        rows.append({'test_id': nid, 'junit_status': jstat, 'verdict_prelim': verdict, 'time_s': c.get('time', ''),
                     'first_failure_boundary': boundary, 'exchange_identity_check_calls': o.get('calls', ''),
                     'exchange_identity_check_raised': o.get('raised', ''), 'raw_evidence_reference': 'run/raw/junit.xml; run/raw/log.txt; run/raw/obs.json'})
    rows.sort(key=lambda r: r['test_id'])
    with (H / 'per-test-41.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['test_id', 'junit_status', 'verdict_prelim', 'time_s', 'first_failure_boundary', 'exchange_identity_check_calls',
                                          'exchange_identity_check_raised', 'raw_evidence_reference'])
        w.writeheader()
        w.writerows(rows)

    # environment + component identities
    comps = {n: {'head': run(['git', '-C', str(a.components / n), 'rev-parse', 'HEAD']), 'tree': run(['git', '-C', str(a.components / n), 'rev-parse', 'HEAD^{tree}'])} for n in NAMES}
    env = {'python_version': sys.version, 'platform': platform.platform(), 'machine': platform.machine(), 'cpu_count': os.cpu_count(),
           'runner_image': {k: os.environ.get(k) for k in ('ImageOS', 'ImageVersion', 'RUNNER_OS', 'RUNNER_ARCH', 'RUNNER_NAME', 'RUNNER_ENVIRONMENT')},
           'os_release': read('/etc/os-release'), 'git_version': run(['git', '--version']),
           'pip_freeze': run([sys.executable, '-m', 'pip', 'freeze']).splitlines(),
           'github': {k: os.environ.get(k) for k in ('GITHUB_REPOSITORY', 'GITHUB_EVENT_NAME', 'GITHUB_REF', 'GITHUB_SHA', 'GITHUB_WORKFLOW_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_RUN_NUMBER')},
           'qualification_head': run(['git', 'rev-parse', 'HEAD']), 'qualification_tree': run(['git', 'rev-parse', 'HEAD^{tree}']),
           'components': comps}
    (H / 'environment.json').write_text(json.dumps(env, indent=2, sort_keys=True) + '\n')
    (H / 'env-dump.txt').write_text(f"python: {sys.version}\nrunner image: {env['runner_image']}\ngit: {env['git_version']}\nqualification HEAD {env['qualification_head']} tree {env['qualification_tree']}\n"
                                    + ''.join(f'{n}: HEAD {v["head"]} tree {v["tree"]}\n' for n, v in comps.items()) + '--- pip freeze ---\n' + '\n'.join(env['pip_freeze']) + '\n')

    ok = not problems
    status = {'schema': 'cognous.s3-hosted-status/1', 'observation': 'C3 (GitHub-hosted, separate from C1 and C2); developer evidence; not independent qualification',
              'job_ok': ok, 'harness_problems': problems, 'counts_prelim': counts, 'collected_dry_check': dry.get('collected'),
              'collect_only_count': collect_n, 'junit_testcases': junit_n, 'guard_outcome': guard['outcome'], 'runner_returncode': r_rc,
              'pytest_returncode': run_json.get('pytest_returncode'), 'security_cases_failed': counts['FAIL'], 'blocked': counts['BLOCKED']}
    (H / 'hosted-status.json').write_text(json.dumps(status, indent=2) + '\n')

    # summary
    L = ['## Security Wiki S3 hosted observation (C3)', '',
         '> Separate GitHub-hosted observation of the frozen 41-case battery. Not C1 (38 PASS / 0 FAIL / 3 BLOCKED) and not C2 (41 PASS); developer evidence, not independent qualification. Verdicts below are junit-derived and preliminary.', '',
         f'| Harness ran to a complete record | tuple guard | dry check | collected (junit / collect-only) |', '|---|---|---|---|',
         f'| {"yes" if ok else "**NO**"} | {guard["outcome"]} | {"OK" if d_rc == 0 else "NOT OK"} | {junit_n} / {collect_n} (expected {EXPECTED}) |', '',
         '| PASS | FAIL | BLOCKED |', '|---|---|---|', f'| {counts["PASS"]} | {counts["FAIL"]} | {counts["BLOCKED"]} |', '']
    if problems:
        L += ['**Harness problems (job fails):**'] + [f'- {p}' for p in problems] + ['']
    nonpass = [r for r in rows if r['verdict_prelim'] != 'PASS']
    if nonpass:
        L += ['| Non-PASS case | Verdict | First boundary |', '|---|---|---|'] + [f'| `{r["test_id"].split("/")[-1]}` | {r["verdict_prelim"]} | {r["first_failure_boundary"].replace("|", "/")[:160]} |' for r in nonpass] + ['']
    L += ['Failing security cases are reported here and do not fail the job; the artifact (per-test CSV, junit, log, observer output, run.json, guard result, environment, SHA-256 of all files) is published regardless.']
    text = '\n'.join(L) + '\n'
    (H / 'summary.md').write_text(text)
    if a.step_summary:
        with a.step_summary.open('a') as f:
            f.write(text)
    if counts['FAIL'] or counts['BLOCKED']:
        print(f'::warning::hosted S3 observation: {counts["FAIL"]} FAIL, {counts["BLOCKED"]} BLOCKED (reported, job not failed on this account)')
    if not ok:
        print('::error::hosted S3 harness problem: ' + '; '.join(problems))

    # checksums of everything under the evidence root (run output included), written last
    ev = H.parent
    sums = sorted(p for p in ev.rglob('*') if p.is_file() and p.name != 'SHA256SUMS-all')
    (H / 'SHA256SUMS-all').write_text('\n'.join(f'{sha256(p)}  ./{p.relative_to(ev).as_posix()}' for p in sums) + '\n')
    return 0  # the workflow gate step reads hosted-status.json; this helper itself never hides a problem


if __name__ == '__main__':
    raise SystemExit(main())
