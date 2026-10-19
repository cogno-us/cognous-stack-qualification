"""Shared helpers of the work packages G1 to G6 (scenario-derived tests for the APPLICABLE cases).

SPDX-License-Identifier: Apache-2.0

Thin accessors over the helpers of ``suites/v1-scenarios`` (loaded on first use, through ``_wiki_helpers``) and a few small
functions that more than one package of this suite needs. Nothing here changes a component, a pin or a profile. The registry of
``test_wiki_skeleton.py`` scans test modules only, so this module carries no case id.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path

import _wiki_helpers as W

FOUR = ('valid', 'lost_ack', 'revoked', 'unreadable')
RUN_MEMBERS = ('bundle_id', 'generated_at')


def h():
    """The route helpers of suites/v1-scenarios, with the pinned reference verified and put on the import path (idempotent)."""
    helpers = W._h()
    helpers.reference()
    return helpers


def h2():
    """The export helpers of suites/v1-scenarios (producer runs, bundle, pack and ODES package, planted-defect catalogues)."""
    h()
    return importlib.import_module('_d06_d07_d08_helpers')


def c2b():
    h()
    return importlib.import_module('_c_2b_helpers')


def chain():
    return h2().reference().chain


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(value):
    """sha256 of the canonical JSON of a value, computed here and not by a component (an independent recomputation)."""
    return 'sha256:' + hashlib.sha256(canon(value)).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_four(root):
    """One producer run of each of four outcomes (applied, lost acknowledgement, revoked grant, unreadable status), exported to
    ``root`` and read back from the files."""
    H2 = h2()
    return {case: H2.build_exports(case, root) for case in FOUR}


def check_exports_unchanged(built):
    for case, ex in built.items():
        for name, expected in ex['sha256'].items():
            assert file_digest(ex['dir'] / name) == expected, f'exported original {case}/{name} was modified'


def load(ex, name):
    return h2().load_copy(ex, name)


def bundle_without_integrity(bundle):
    out = copy.deepcopy(bundle)
    out['integrity'] = []
    return out


def replay():
    h()
    return importlib.import_module('agent_replay_bundle')


def importers():
    h()
    return importlib.import_module('agent_replay_bundle.importers')


def reconstruct(journal, proposal, export, *, revision=None):
    ch = chain()
    return importers().import_bounded_workflow(
        copy.deepcopy(journal), proposal=copy.deepcopy(proposal), moltbot_export=copy.deepcopy(export),
        control_plane_revision=ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION if revision is None else revision).model_dump(mode='json')


def refusal_of(fn):
    """The typed refusal text of a call that must raise the importer's contract error, else None."""
    try:
        fn()
    except importers().ImportContractError as exc:
        return str(exc)
    return None


def records_of(bundle, kind):
    return [r for r in bundle['records'] if r['record_type'] == kind]


def scalar_paths(value, path=()):
    """Paths of every string or number leaf of a JSON value (booleans and nulls excluded)."""
    if isinstance(value, dict):
        for k in sorted(value):
            yield from scalar_paths(value[k], path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from scalar_paths(v, path + (i,))
    elif isinstance(value, str) or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        yield path


def alter_first_leaf(value):
    """Change the first scalar leaf of ``value`` in place; returns its path (None when there is no scalar)."""
    for path in scalar_paths(value):
        node = value
        for k in path[:-1]:
            node = node[k]
        old = node[path[-1]]
        node[path[-1]] = old + '~altered' if isinstance(old, str) else old + 1
        return path
    return None


def odes_layers(package, policy=None):
    """Layer name -> status of the recipient evaluation of an ODES package, in this process."""
    h()
    odes = importlib.import_module('odes')
    res = odes.evaluate_recipient_package(package, policy or {'supported_profiles': ['odes_cognous_stack_export_0_2']})
    return {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}


SEPARATE_CONSUMER = r'''
import json, sys
from odes import evaluate_recipient_package
pkg = json.load(open(sys.argv[1]))
res = evaluate_recipient_package(pkg, json.loads(sys.argv[2]))
print(json.dumps({'layers': {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}}, sort_keys=True))
'''


def separate_consumer(path, policy=None):
    """Layer statuses of an exported ODES package read from a file by a fresh process whose import path holds only the ODES and
    Replay source trees (no producer code)."""
    import os
    import subprocess
    import sys
    ref = h2().reference()
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    env['PYTHONPATH'] = os.pathsep.join(str(ref.paths[k] / 'src') for k in ('odes', 'replay'))
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    out = subprocess.run([sys.executable, '-s', '-c', SEPARATE_CONSUMER, str(path), json.dumps(policy or {'supported_profiles': ['odes_cognous_stack_export_0_2']})],
                         env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-400:]
    return json.loads(out.stdout)['layers']


# ------------------------------------------------------------------------------------------------ rule revision flows
REVISER = 'synthetic-principal:reviser'
SIGNER = 'synthetic-principal:signer'


def tb():
    h()
    return importlib.import_module('tests.test_bounded_authorization')


def tr():
    h()
    return importlib.import_module('tests.test_runtime_authority')


def rr():
    h()
    return importlib.import_module('agent_control_plane.rule_revision')


def digest_of(label):
    return chain().commitment({'synthetic-policy-content': label})


def revision(rid, to_label, from_label=None, *, signer=SIGNER, recorded_at=None):
    ba, ra = tb(), tr()
    return rr().RuleRevision(revision_id=rid, rule_kind='policy', rule_ref=ba.POLICY_REF, from_digest=digest_of(from_label) if from_label else None,
                             to_digest=digest_of(to_label), reviser=REVISER, signer=signer, authority_ref='synthetic-authority:1',
                             reason='synthetic', supersedes=None, recorded_at=recorded_at or ra.NOW.isoformat())


def rule_flow(tmp_path, monkeypatch, content='v1'):
    """Bounded workflow with the opt-in rule revision profile: the resolver reports the digest of the policy it runs."""
    ba, ra = tb(), tr()
    bounded = importlib.import_module('agent_control_plane.bounded')
    monkeypatch.setattr(bounded, '_now', lambda: ra.NOW)
    p, r, f, c = ra.setup_flow(tmp_path)
    f.rule_revision_profile = rr().RuleRevisionProfile(signers=[SIGNER])
    r.policies[ba.POLICY_REF].digest = digest_of(content)
    return p, r, f


def adopt(f, rid, to_label, from_label=None, **kw):
    return rr().append_rule_revision(f.records, f.rule_revision_profile, revision(rid, to_label, from_label, **kw))


def observe(r, label):
    r.policies[tb().POLICY_REF].digest = digest_of(label)


def decide(f, p):
    return f.decide(p, now=tr().NOW)


def rows(f):
    return [x.model_dump(mode='json') for x in f.records.load().rule_revisions]
