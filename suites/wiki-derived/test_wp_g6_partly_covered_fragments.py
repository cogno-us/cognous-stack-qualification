"""Scenario-derived tests: the in-scope fragments of two PARTLY_COVERED cases (work package G6).

SPDX-License-Identifier: Apache-2.0

Two catalog cases are classified PARTLY_COVERED. Each test here checks only the fragment that the applicability file names as inside
the declared scope, and says so. The rest of each case is outside the stack by design and is not tested, and nothing here claims it.

* TC-L06-003, shadow agent detection: the fragment is that an actor, a sender or a recipient that is not declared to the stack is
  refused with no effect. OCS does not discover agents and keeps no inventory of them, with or without an active or inactive state.
* TC-L06-026, agent runtime file and network egress restrictions: the fragment is the confinement of the destination database path
  to its configured root, against traversal and link escapes. OCS does not restrict an agent's file reads, network destinations,
  domains or DNS lookups, and gives no egress or credential-isolation assurance.

Existing coverage that these tests sit next to (not copied): the unregistered-action and unregistered-agent family of
``suites/v1-scenarios/test_asw_a.py`` and the confinement scenario ``test_scn_c10.py``.

Cases of the same group that are deliberately not given a test here:

* the policy-to-control mapping case (L02, number 002): the in-scope content is a static mapping document that the probes of
  ``suites/v1-probes/test_authority_probes.py`` read from an optional checkout (``PROBE2_*``) that is not part of the prepared
  reference; a test here would check a file, not a behaviour of the pinned stack, and would overstate coverage;
* the throughput and peak-load case (L08, number 033): the only evidence is the report-only ingress-pressure scenario D06, which is
  not a performance claim, so a test here would overstate coverage;
* the D09 case 004 and the D13 case 003: outside by design and not claimed (owner decision); no wrapper is added.
"""
from __future__ import annotations

import copy
import importlib
import os
from pathlib import Path

import pytest

import _wiki_helpers as W
import _wp_g_common as G
import test_wp_e_exchange_injection as E
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')


def tree(root):
    """Every path below ``root`` with its kind and, for a file, its size (a snapshot that notices anything created or removed)."""
    out = {}
    for path in sorted(Path(root).rglob('*')):
        rel = str(path.relative_to(root))
        out[rel] = ('link', os.readlink(path)) if path.is_symlink() else (('dir', 0) if path.is_dir() else ('file', path.stat().st_size))
    return out


# ================================================================================================ TC-L06-003
@wiki_case('TC-L06-003')
def test_wiki_l06_003_a_sender_a_recipient_and_an_actor_that_are_not_declared_are_refused_with_no_effect(tmp_path, monkeypatch):
    """Fragment only: refusal of an undeclared party. Nothing is discovered."""
    def flow(name):
        path = tmp_path / name
        path.mkdir()
        return W.route_c(path, monkeypatch)

    f = flow('control')  # positive control: the declared sender, recipient and actor execute once
    E.assert_executed_once(E.run_msg(f, E.make_msg(f, 'declared')))
    E.bounded_rows(E.effects(f))

    f = flow('sender')
    res = E.run_msg(f, E.make_msg(f, 'shadow-sender', sender='shadow-agent-on-a-workstation'))
    E.assert_refused(res, E.SENDER_UNTRUSTED)
    assert E.effects(f) == []

    f = flow('recipient')
    res = E.run_msg(f, E.make_msg(f, 'shadow-recipient', recipient='shadow-recipient'))
    E.assert_refused(res, E.WRONG_RECIPIENT)
    assert E.effects(f) == []

    f = flow('actor')  # a request that names an acting identity the authority source does not know
    bundle = copy.deepcopy(f.bundle)
    next(r for r in bundle['records'] if r['record_type'] == 'runtime_proposal')['data']['actor'] = 'urn:cognous:identity:shadow-agent'
    proposal = f.gax.runtime_proposal_model(bundle)
    commitment = G.chain().commitment(proposal.model_dump(mode='json', exclude_none=False))
    for approval in f.r.approvals.values():
        approval.proposal_commitment = commitment
    res = E.run_msg(f, E.make_msg(f, 'shadow-actor', bundle=bundle), bundle=bundle)
    E.assert_held(res)
    assert E.effects(f) == [] and W.destination_summary(f)['attempts'] == []


@wiki_case('TC-L06-003')
def test_wiki_l06_003_an_undeclared_action_is_refused_with_no_effect(tmp_path, monkeypatch):
    """Fragment only: an action that no manifest declares cannot be proposed through the exchange."""
    f = W.route_c(tmp_path, monkeypatch)
    bundle = copy.deepcopy(f.bundle)
    next(r for r in bundle['records'] if r['record_type'] == 'runtime_proposal')['data']['action_id'] = 'urn:cognous:action:shadow-agent-v1'
    message = E.make_msg(f, 'shadow-action', bundle=bundle)
    with pytest.raises(Exception) as exc:  # the exchange cannot export the retained bundle for an action the manifest does not declare
        E.run_msg(f, message, bundle=bundle)
    assert 'declared Manifest action' in str(exc.value)
    assert E.effects(f) == []


@wiki_case('TC-L06-003')
def test_wiki_l06_003_the_registry_is_a_set_of_names_and_not_an_inventory_known_limit(tmp_path, monkeypatch):
    """Limit: the registry that refuses undeclared parties records no discovery, no state of an agent and no history of a refusal."""
    f = W.route_c(tmp_path, monkeypatch)
    members = {n for n in vars(f.registry)}
    assert members == {'trusted_senders', 'trusted_recipients', 'recipient', 'relying_purpose'}  # names only: no state, owner or last-seen member
    E.run_msg(f, E.make_msg(f, 'shadow', sender='shadow-agent'))
    assert {n for n in vars(f.registry)} == members and f.registry.trusted_senders == {E.SENDER}  # a refusal adds nothing to the registry


# ================================================================================================ TC-L06-026
def destination_classes():
    G.h()
    return [importlib.import_module('engine.safe_executor').DurableRefundDestination,
            importlib.import_module('engine.effective_grant').EffectiveGrantDestination]


def layout(path):
    outside = path / 'outside'
    outside.mkdir()
    (outside / 'victim.sqlite3').write_bytes(b'victim')
    (outside / 'secret.txt').write_text('synthetic')
    sandbox = path / 'sandbox'
    return sandbox, outside


def attempt_construct(cls, root, name=None):
    try:
        cls(root) if name is None else cls(root, name)
    except Exception as exc:
        return type(exc).__name__
    return None


@wiki_case('TC-L06-026')
def test_wiki_l06_026_traversal_in_the_database_name_is_refused_and_nothing_is_created_outside_the_root(tmp_path):
    """Fragment only: the database path stays inside its root. Reads and network access of an agent are not restricted by this."""
    for cls in destination_classes():
        base = tmp_path / cls.__name__
        base.mkdir()
        sandbox, outside = layout(base)
        before = tree(base)
        names = ['../escape.sqlite3', 'a/../../escape.sqlite3', '../outside/planted.sqlite3', '..', str(outside / 'abs.sqlite3'), '/etc/cognous-g6-planted.sqlite3']
        for name in names:
            assert attempt_construct(cls, sandbox, name) == 'PermissionError', (cls.__name__, name)
            assert not Path('/etc/cognous-g6-planted.sqlite3').exists()
        created = set(tree(base)) - set(before)
        assert created <= {'sandbox'} and tree(base).get('outside/victim.sqlite3') == before['outside/victim.sqlite3']  # at most the root itself exists
        assert not [p for p in tree(base) if p.startswith('outside/') and p not in ('outside/victim.sqlite3', 'outside/secret.txt')]
        # control: a database inside the root is accepted, so the refusals are not a refusal of everything
        assert attempt_construct(cls, sandbox, 'inside.sqlite3') is None and (sandbox / 'inside.sqlite3').exists()


@wiki_case('TC-L06-026')
def test_wiki_l06_026_a_link_that_leads_out_of_the_root_is_refused_and_the_target_is_untouched(tmp_path):
    for cls in destination_classes():
        base = tmp_path / cls.__name__
        base.mkdir()
        sandbox, outside = layout(base)
        variants = {}
        root_link = base / 'link_root'
        root_link.symlink_to(outside, target_is_directory=True)
        variants['root_is_a_link'] = (root_link, None)
        parent_link = base / 'link_parent'
        parent_link.symlink_to(outside, target_is_directory=True)
        variants['parent_of_root_is_a_link'] = (parent_link / 'root', None)
        sandbox.mkdir()
        (sandbox / 'refunds.sqlite3').symlink_to(outside / 'victim.sqlite3')
        variants['database_is_a_link_to_an_outside_file'] = (sandbox, None)
        sandbox2 = base / 'sandbox2'
        sandbox2.mkdir()
        (sandbox2 / 'refunds.sqlite3').symlink_to(outside / 'planted-by-link.sqlite3')
        variants['database_is_a_dangling_link_to_outside'] = (sandbox2, None)
        sandbox3 = base / 'sandbox3'
        sandbox3.mkdir()
        (sandbox3 / 'sub').symlink_to(outside, target_is_directory=True)
        variants['database_in_a_linked_subdirectory'] = (sandbox3, 'sub/planted.sqlite3')
        for name, (root, db) in variants.items():
            assert attempt_construct(cls, root, db) in ('PermissionError', 'OSError', 'ValueError'), (cls.__name__, name)
        assert (outside / 'victim.sqlite3').read_bytes() == b'victim'
        assert sorted(p.name for p in outside.iterdir()) == ['secret.txt', 'victim.sqlite3']  # nothing was planted outside


@wiki_case('TC-L06-026')
def test_wiki_l06_026_the_confinement_covers_the_database_path_only_known_limit(tmp_path):
    """Limit: the check is made on the destination database path; a file read or a network destination of an agent is not restricted
    and no egress assurance follows. The test shows the extent of what is checked: a path outside the root is refused, while the
    constructor accepts any root the host configures, including one that names a sensitive directory."""
    G.h()
    for cls in destination_classes():
        base = tmp_path / cls.__name__
        base.mkdir()
        elsewhere = base / 'configured-elsewhere'
        assert attempt_construct(cls, elsewhere) is None  # the root is the host's choice; the stack confines to it and does not choose it
        assert (elsewhere / 'refunds.sqlite3').exists()
