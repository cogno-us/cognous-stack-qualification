"""digests.json and DIGESTS.md are current and agree with the registered record; the dependency lock is complete."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
CMP = REPO / 'comparators'
SUITE = REPO / 'suites/cognous-open-control-stack'
TWIN = json.loads((REPO / 'process/release-gate/preregistration.json').read_text())
D = json.loads((CMP / 'digests.json').read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_digests_are_up_to_date():
    r = subprocess.run([sys.executable, str(CMP / 'wiki/harness/compute_digests.py'), '--check'], capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_file_of_the_package_is_listed_in_a_group():
    assert D['unlisted_files_check'] == []
    for rel, want in D['files'].items():
        assert sha(REPO / rel) == want, rel


def test_registered_files_agree_with_the_pre_registration_twin():
    rf = D['registered_files']
    subset = TWIN['comparator_subset']
    assert rf['suites/cognous-open-control-stack/benchmarks/governance/corner-plan.json'] == subset['corner']['plan_sha256']
    assert rf['suites/cognous-open-control-stack/benchmarks/governance/plan.json'] == subset['baseline']['plan_sha256']
    assert rf['suites/cognous-open-control-stack/benchmarks/governance/policy.rego'] == subset['policy_file']['sha256']
    assert D['registered_evaluate_function_source_sha256'] == TWIN['scoring']['oracle']['function_source_sha256']
    for rel, want in rf.items():
        assert sha(REPO / rel) == want, rel


def test_the_loader_pins_equal_the_recorded_digests():
    from comparators.wiki.harness import _base
    for rel, want in _base.PINNED_SHA256.items():
        assert D['registered_files']['suites/cognous-open-control-stack/' + rel] == want
    assert _base.EVALUATE_SOURCE_SHA256 == D['registered_evaluate_function_source_sha256']


def test_hub_files_equal_the_recorded_digests():
    hub = Path(os.environ['SCN_HUB_DIR'])
    for name, want in D['hub']['files_used_by_the_registered_sets_and_the_comparators'].items():
        assert sha(hub / 'reference_profiles' / name) == want, name
    for name, want in D['hub']['reference_profiles_tree'].items():
        assert sha(hub / 'reference_profiles' / name) == want, name
    assert D['hub']['revision'] == '8517818fbf817897aacfb6fe7898c22aea46fd95'


def test_the_opa_binary_is_the_pinned_one_when_present():
    binary = Path(os.environ['SCN_OPA'])
    assert sha(binary) == D['opa_binary_sha256_per_dependencies_json']
    assert D['opa_binary_sha256_per_dependencies_json'] == json.loads((SUITE / 'benchmarks/governance/dependencies.json').read_text())['opa']['sha256']


def lock_entries():
    text = (CMP / 'deps/requirements-comparator.lock').read_text()
    out, current = {}, None
    for line in text.splitlines():
        m = re.match(r'^([A-Za-z0-9_.\-]+)==([^\s\\]+)', line)
        if m:
            current = m.group(1).lower(); out[current] = {'version': m.group(2), 'hashes': []}
        h = re.search(r'--hash=sha256:([0-9a-f]{64})', line)
        if h and current:
            out[current]['hashes'].append(h.group(1))
    return out


def test_the_lock_pins_every_direct_pin_with_hashes_and_equals_the_registered_requirements():
    direct = {l.split('==')[0].lower().replace('_', '-'): l.split('==')[1] for l in (CMP / 'deps/requirements.pinned.txt').read_text().split() if '==' in l}
    registered = {l.split('==')[0].lower().replace('_', '-'): l.split('==')[1] for l in (SUITE / 'benchmarks/governance/requirements.txt').read_text().split() if '==' in l}
    assert direct == registered and len(direct) == 44
    lock = {k.replace('_', '-'): v for k, v in lock_entries().items()}
    assert {k: v['version'] for k, v in lock.items()} == direct
    assert all(len(v['hashes']) >= 1 for v in lock.values())
    dd = json.loads((SUITE / 'benchmarks/governance/dependencies.json').read_text())['python_direct']
    for name, ver in dd.items():
        assert direct[name] == ver


def test_the_lock_header_names_the_hash_install():
    head = (CMP / 'deps/requirements-comparator.lock').read_text().splitlines()[:4]
    assert any('--generate-hashes' in l for l in head) and any('--only-binary' in l for l in head)


def test_the_group_digests_are_recomputable():
    for name, g in D['groups'].items():
        lines = ''.join('%s  %s\n' % (sha(REPO / f), f) for f in sorted(g['files']))
        assert hashlib.sha256(lines.encode()).hexdigest() == g['group_sha256'], name
