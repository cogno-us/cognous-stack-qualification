"""Addendum row ADD-TEST-G1 - Gate G1 "source and containment": exact source/config manifest with verified test identities,
network limits and reset procedure (Agentic testing addendum 7 G1).

SPDX-License-Identifier: Apache-2.0

The freeze manifest already verified the source pins (PASS). What was not asserted as a gate: the test-identity listing, the network
limits and the reset procedure of the scenario harness. This module executes those as checks and writes a manifest into the evidence:

  * source/config manifest: freeze-manifest file hashes re-verified against the bytes in this run, component pins of the loaded
    reference equal the profile, the CI job that runs the scenarios is pinned by SHA, secret-free, read-only and checks out without
    persisted credentials.
  * test identities: every test case of the retained scenario junit (the latest retained ``jobs/scenarios/junit.xml``) is listed;
    identities are unique, each resolves to a test function that still exists in ``suites/v1-scenarios``, and each case's retained
    scenario evidence names the same test and the frozen component pins. Retained failures are LISTED (they are findings, not
    identity errors) but are not asserted away.
  * network limits: the harness refuses IP connections (executed probe through the shared ``no_network`` fixture), and the evidence
    declares network none / paid model calls 0 / live effects 0.
  * reset procedure: a fresh work directory per run yields an identical empty initial state every time, an effect committed in one
    directory is invisible after a reset and leaves the previous directory untouched, pins are re-verified pristine before and after,
    and the pristine check detects every kind of drift (negative controls on a scratch repository; the pins are never modified).

Every case runs twice (D3). No product code, pin, profile or default is changed.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import socket
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

import _d02_d05_d09_helpers as H
import _pins
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

ROOT = H.ROOT
VALIDATION = ROOT / 'process/v1-validation/v1-2026-10-16-a'
SUITE = ROOT / 'suites/v1-scenarios'


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hub():
    hub = os.environ.get('SCN_HUB_DIR')
    if not hub:
        pytest.fail('SCN_HUB_DIR is not set; the hub files of the freeze manifest cannot be verified (not skipped, not a pass)')
    from pristine_checkout import require_pristine
    require_pristine(hub, H.FROZEN_HUB, 'hub')
    return Path(hub)


# ------------------------------------------------------------------------------------------------
# source / config manifest
# ------------------------------------------------------------------------------------------------

def test_add_test_g1_source_config_manifest_is_verified_against_bytes_in_this_run(request, record_property, tmp_path):
    hub = _hub()

    def trial(work, mp, checks):
        ref = H.reference()
        freeze = json.loads((VALIDATION / 'freeze-manifest.json').read_text())  # the ORIGINAL freeze: file hashes and tag identities
        resolved = _pins.RESOLVED_MANIFEST  # freeze manifest + APPLIED refreeze-log entries: the pins in force for this run
        manifest = {'validation_id': freeze['validation_id'], 'files': {}, 'components': {}, 'ci_job': {}}
        for rel, expected in freeze['hub_file_hashes'].items():
            actual = _sha256(hub / rel)
            manifest['files'][f'hub:{rel}'] = actual
            checks.equal(actual, expected, f'hub file {rel} matches the freeze manifest')
        for rel, expected in freeze['qualification_file_hashes'].items():
            actual = _sha256(ROOT / rel)
            manifest['files'][f'qualification:{rel}'] = actual
            checks.equal(actual, expected, f'qualification file {rel} matches the freeze manifest')
        checks.equal(freeze['identities']['hub']['head'], H.FROZEN_HUB, 'freeze manifest hub head equals the pin asserted by the harness')
        checks.equal(freeze['identities']['runtime']['sha'], _pins.ORIGINAL_MANIFEST['components_subject']['moltbot_safe']['sha'],
                     'freeze manifest runtime identity (tag pin) equals the originally frozen runtime pin')
        checks.equal(resolved['components_subject']['moltbot_safe']['sha'], H.FROZEN_RUNTIME,
                     'freeze manifest + refreeze overlay runtime sha equals the pin asserted by the harness')
        manifest['refreeze_applied'] = [{'id': e, 'component': k, 'from_sha': f, 'to_sha': to} for e, _g, k, f, to in _pins.APPLIED_REFREEZES]
        subject = resolved['components_subject']
        by_repo = {v['repository']: v['sha'] for v in subject.values()}
        for name, pin in ref.pins.items():
            manifest['components'][name] = {'repository': pin['repository'], 'commit': pin['commit'], 'tree': pin['tree']}
            frozen = by_repo.get(pin['repository'])
            checks.equal(frozen, pin['commit'], f'loaded component {name} equals the freeze manifest pin (with refreeze overlay)')
        profile = json.loads(_pins.PROFILE_PATH.read_text())
        for name in H.COMPONENT_NAMES:
            checks.equal(ref.pins[name]['commit'], profile['components'][name]['revision'], f'loaded {name} equals the qualification profile')
        # CI job that executes the scenarios: SHA-pinned, secret-free, read-only
        wf = yaml.safe_load((ROOT / '.github/workflows/v1-validation.yml').read_text())
        job = wf['jobs']['scenarios']
        text = json.dumps(job)
        checks.equal(wf.get('permissions'), {'contents': 'read'}, 'workflow default permissions are read-only')
        checks.expect('permissions' not in job, 'the scenarios job does not widen permissions')
        checks.expect('secrets.' not in text and 'GITHUB_TOKEN' not in text, 'the scenarios job references no secret or token')
        uses = [s for s in job['steps'] if 'uses' in s]
        checks.expect(all(re.search(r'@[0-9a-f]{40}$', s['uses']) for s in uses), 'every action in the scenarios job is pinned by commit SHA')
        checkouts = [s for s in uses if s['uses'].startswith('actions/checkout')]
        checks.expect(bool(checkouts) and all(s['with'].get('persist-credentials') is False for s in checkouts), 'every checkout in the scenarios job drops credentials')
        hub_checkout = [s for s in checkouts if s['with'].get('repository') == 'cogno-us/cognous-open-control-stack']
        checks.equal([s['with']['ref'] for s in hub_checkout], [H.FROZEN_HUB], 'the CI job checks out the frozen hub pin')
        manifest['ci_job'] = {'actions_pinned': len(uses), 'checkouts_without_credentials': len(checkouts), 'hub_ref': H.FROZEN_HUB, 'permissions': wf.get('permissions')}
        return {'source_config_manifest': manifest, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-TEST-G1', trial, expect_effects_gate=False)


# ------------------------------------------------------------------------------------------------
# test identities from the retained junit
# ------------------------------------------------------------------------------------------------

def _latest_retained_junit():
    runs = []
    for p in (ROOT / 'results/v1-validation/v1-2026-10-16-a').glob('*/jobs/scenarios/junit.xml'):
        m = re.search(r'-(\d+)$', p.parents[2].name)
        runs.append((int(m.group(1)) if m else 0, p))
    return max(runs)[1] if runs else None


def _functions(module_path):
    return {n.name for n in ast.walk(ast.parse(Path(module_path).read_text())) if isinstance(n, ast.FunctionDef)}


def test_add_test_g1_test_identities_from_retained_junit_are_listed_and_verified(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ref = H.reference()
        junit = _latest_retained_junit()
        checks.expect(junit is not None, 'a retained scenarios junit exists under results/v1-validation/v1-2026-10-16-a')
        if junit is None:
            return {'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
        cases = list(ET.parse(junit).getroot().iter('testcase'))
        checks.expect(len(cases) > 0, 'retained junit lists test cases')
        identities, seen, stale, mismatch, pins_bad, failing, no_evidence = [], set(), [], [], [], [], []
        cache = {}
        pins = {n: ref.pins[n]['commit'] for n in H.COMPONENT_NAMES}
        # a retained run is judged against the pin generation that produced it (original freeze or a later re-freeze of the
        # refreeze log), never against "whatever is loaded now"; evidence that matches NO generation, or that mixes generations,
        # is still drift. Which generation the retained junit belongs to is recorded below.
        gens = _pins.GENERATIONS
        evidence_pin_sets = []
        for tc in cases:
            classname, name = tc.get('classname'), tc.get('name')
            identity = f'{classname}::{name}'
            if identity in seen:
                checks.violations.append(f'duplicate test identity {identity}')
            seen.add(identity)
            module = classname.split('.')[-1]
            path = SUITE / f'{module}.py'
            base = name.split('[')[0]
            if not path.exists():
                stale.append(identity)
            else:
                funcs = cache.setdefault(module, _functions(path))
                if base not in funcs:
                    stale.append(identity)
            failed = tc.find('failure') is not None or tc.find('error') is not None
            if failed:
                failing.append(identity)
            props = [(p.get('name'), p.get('value')) for p in tc.iter('property')]
            if not props:
                no_evidence.append(identity)
            for pname, value in props:
                try:
                    ev = json.loads(value)
                except (TypeError, ValueError):
                    continue
                if pname == 'scenario_evidence' and ev.get('test') != name:
                    mismatch.append((identity, ev.get('test')))
                components = (ev.get('environment') or {}).get('components') if isinstance(ev, dict) else None
                if components is not None:
                    got = {k: v['commit'] for k, v in components.items()}
                    evidence_pin_sets.append(got)
                    if not any(got == g for _, g in gens):
                        pins_bad.append(identity)
            identities.append(identity)
        checks.equal(stale, [], 'every retained test identity resolves to a test function that still exists in suites/v1-scenarios')
        checks.equal(mismatch, [], 'retained evidence names the same test as its junit case')
        checks.equal(pins_bad, [], 'retained evidence records exactly the component pins of a frozen generation (original freeze or an applied re-freeze)')
        retained_generation = None
        try:
            retained_generation = _pins.classify_generation(evidence_pin_sets, gens)
        except _pins.RefreezeError as exc:
            if not pins_bad:  # unmatched sets are already reported above; this is the mixed-generation case
                checks.violations.append(str(exc))
        current_label = gens[-1][0]
        checks.expect(any(g == pins for _, g in gens), 'the pins loaded by this run are a frozen generation')
        assert len(identities) == len(set(identities))
        listing = hashlib.sha256('\n'.join(sorted(identities)).encode()).hexdigest()
        return {'retained_junit': str(junit.relative_to(ROOT)),
                'retained_junit_pin_generation': retained_generation and retained_generation[0], 'current_pin_generation': current_label,
                'retained_junit_is_current_generation': bool(retained_generation) and retained_generation[1] == len(gens) - 1, 'identity_count': len(identities), 'identities_sha256': listing,
                'identities_by_module': {m: sum(1 for i in identities if i.split('::')[0].endswith(m)) for m in sorted({i.split('::')[0].split('.')[-1] for i in identities})},
                'retained_failing_identities_listed_not_asserted': sorted(failing), 'retained_failing_count': len(failing),
                'retained_cases_without_any_evidence_property_listed_not_asserted': sorted(no_evidence),
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-TEST-G1', trial, expect_effects_gate=False)


# ------------------------------------------------------------------------------------------------
# network limits
# ------------------------------------------------------------------------------------------------

def test_add_test_g1_network_limits_are_enforced_and_declared(request, record_property, tmp_path, no_network):
    def trial(work, mp, checks):
        try:
            return _network_trial(checks, no_network)
        finally:
            no_network.clear()

    def _network_trial(checks, no_network):
        env = H.environment_identity()
        checks.equal((env['network'], env['paid_model_calls'], env['live_effects']), ('none', 0, 0), 'evidence declares network none, no paid model calls, no live effects')
        refused, probes = [], [(socket.AF_INET, ('127.0.0.1', 9)), (socket.AF_INET, ('192.0.2.1', 443))]
        try:
            socket.socket(socket.AF_INET6, socket.SOCK_STREAM).close()
            probes.append((socket.AF_INET6, ('::1', 9)))
        except OSError:
            pass  # IPv6 not available on this host: nothing to refuse, recorded by the probe count below
        for family, address in probes:
            s = socket.socket(family, socket.SOCK_STREAM)
            try:
                s.settimeout(1)
                s.connect(address)
                refused.append((repr(address), 'CONNECTED'))
            except PermissionError:
                refused.append((repr(address), 'refused-by-harness'))
            except OSError as exc:  # IPv6 unavailable would show up here before the harness patch is reached; record it
                refused.append((repr(address), f'os-error:{type(exc).__name__}'))
            finally:
                s.close()
        checks.equal([r[1] for r in refused], ['refused-by-harness'] * len(probes), 'every IP connection attempt is refused by the harness before any packet is sent')
        recorded = list(no_network)
        checks.equal(len(recorded), len(probes), 'the harness counts each refused attempt')
        # a UNIX-domain/local file path stays usable (SQLite needs files): the containment is IP-only by design
        pair = socket.socketpair()
        pair[0].close()
        pair[1].close()
        no_network.clear()  # the probe attempts were deliberate; clear so the teardown gate only sees accidental ones
        return {'probe': [(a, b) for a, b in refused], 'probes_executed': len(probes), 'recorded_attempts': len(recorded), 'declared': {k: env[k] for k in ('network', 'paid_model_calls', 'live_effects')},
                'scope': 'in-process socket.connect refusal for AF_INET/AF_INET6; the CI job additionally runs without secrets', 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    # run_case executes the trial twice; the shared fixture instance spans both runs and is cleared inside the trial
    H.run_case(request, record_property, tmp_path, 'ADD-TEST-G1', trial, expect_effects_gate=False)


# ------------------------------------------------------------------------------------------------
# reset procedure
# ------------------------------------------------------------------------------------------------

def _git(path, *args):
    subprocess.run(['git', '-C', str(path), *args], check=True, capture_output=True, text=True, timeout=60,
                   env=dict(os.environ, GIT_AUTHOR_NAME='g1', GIT_AUTHOR_EMAIL='g1@example.invalid', GIT_COMMITTER_NAME='g1', GIT_COMMITTER_EMAIL='g1@example.invalid'))


def test_add_test_g1_reset_procedure_exists_and_restores_identical_empty_initial_state(request, record_property, tmp_path):
    def trial(work, mp, checks):
        H.reference()
        H.assert_pins_still_pristine()
        digests, leak = [], []
        previous = None
        for n in range(3):  # three consecutive resets
            a = work / f'reset-{n}-a'
            b = work / f'reset-{n}-b'
            a.mkdir()
            b.mkdir()
            fa = H.flow_a(a, mp)
            fb = H.flow_b(b)
            sa, sb = H.db_summary(fa.dest.path), H.db_summary(fb.dest.path)
            checks.equal((sa['effects'], sb['effects']), ([], []), f'reset {n}: both destinations start with no effect')
            checks.equal(sa.get('effective_grants'), [('urn:cognous:grant:routine-1', 'active')], f'reset {n}: route A initial grant state')
            checks.equal([c for c in sb['claims']], [('claim-1', 'issued')], f'reset {n}: route B initial claim state')
            digests.append(H.digest({'a': sa, 'b': sb}))
            if previous is not None:
                before = H.db_summary(previous[0].dest.path)
                leak.append(len(before['effects']))  # effect committed in the previous directory must still be exactly 1
                checks.equal(len(H.db_summary(fa.dest.path)['effects']), 0, f'reset {n}: effect of the previous directory is invisible after the reset')
            ra, ea = H.execute_a(fa)
            rb, eb = H.execute_b(fb, fb.parts[0])
            checks.equal((H.result_view(ra, ea).get('status'), H.atomic_view(rb, eb).get('status')), ('executed', 'executed'), f'reset {n}: the reset state is usable (one effect each)')
            previous = (fa, fb)
        checks.equal(len(set(digests)), 1, 'initial state digest is identical across resets')
        checks.equal(leak, [1, 1], 'the previous directory keeps its own effect (the reset does not reach back into it)')
        H.assert_pins_still_pristine()
        return {'initial_state_digest': digests[0], 'resets': 3, 'previous_directory_effects_after_next_reset': leak,
                'procedure': 'fresh runner-owned work directory per run (run-1/run-2) + both destinations rebuilt from the frozen fixtures; pins re-verified pristine before and after',
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-TEST-G1', trial, expect_effects_gate=False)


@pytest.mark.parametrize('drift', ['untracked-file', 'ignored-bytecode', 'modified-tracked-file', 'assume-unchanged-hidden-edit', 'wrong-revision'])
def test_add_test_g1_reset_verification_detects_source_drift(request, record_property, tmp_path, drift):
    """Negative controls on a scratch repository (the real pins are never touched): the pristine check that gates every reset
    refuses each kind of drift, so a reset that failed to restore source would be caught."""
    def trial(work, mp, checks):
        from pristine_checkout import require_pristine
        repo = work / 'scratch'
        repo.mkdir()
        _git(repo, 'init', '-q')
        (repo / '.gitignore').write_text('*.pyc\n')
        (repo / 'module.py').write_text('VALUE = 1\n')
        _git(repo, 'add', '-A')
        _git(repo, 'commit', '-q', '-m', 'pinned')
        pin = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        checks.equal(require_pristine(repo, pin, 'scratch'), pin, 'baseline: the unmodified scratch checkout is pristine')
        revision = pin
        if drift == 'untracked-file':
            (repo / 'shadow.py').write_text('x = 1\n')
        elif drift == 'ignored-bytecode':
            (repo / 'module.pyc').write_bytes(b'\0')
        elif drift == 'modified-tracked-file':
            (repo / 'module.py').write_text('VALUE = 2\n')
        elif drift == 'assume-unchanged-hidden-edit':
            _git(repo, 'update-index', '--assume-unchanged', 'module.py')
            (repo / 'module.py').write_text('VALUE = 3\n')
        else:
            revision = '0' * 40
        try:
            require_pristine(repo, revision, 'scratch')
            detected = False
        except ValueError:
            detected = True
        checks.expect(detected, f'drift {drift} must be refused by the pristine check')
        return {'drift': drift, 'detected': detected, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-TEST-G1', trial, expect_effects_gate=False)
