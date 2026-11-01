"""ER-06-3 probes for the supported runtime (cognous-execution-runtime, "Moltbot Safe" names retained).

Scope is exactly what the pinned code claims: database-path confinement under an execution root, local-policy
and effective-grant admission, and host-secret isolation of the OpenShell CLI wrapper. Filesystem/process/network
isolation beyond that is a declared limitation and is NOT asserted here.
Run against the pinned checkout named by PROBE_RUNTIME_DIR.
"""
import json
import os
import stat
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

from conftest import pin_dir


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_RUNTIME_DIR")


def op_and_policy():
    from engine.safe_executor import ExecutionOperation, LocalExecutionPolicy, commitment
    payload = {"refund_reason": "probe"}
    op = ExecutionOperation(
        actor="urn:cognous:identity:agent-1", principal="urn:cognous:principal:service",
        institution_id="urn:cognous:institution:demo", authority_domain="customer-refunds",
        manifest_id="refund-integration-v1-1", manifest_version="1.1", manifest_digest="sha256:" + "a" * 64,
        proposal_commitment="sha256:" + "b" * 64, action_id="refund.issue",
        adapter_id="urn:cognous:adapter:synthetic-refund", target="urn:cognous:synthetic-account:customer-1",
        payload=payload, payload_commitment=commitment(payload), requested_permissions=("refund.issue",),
        amount=50.0, unit="USD", effects=1, authority_context_id="urn:cognous:authority-context:refund-demo",
        requirement_id="urn:cognous:requirement:refund-t1", grant_id="urn:cognous:grant:refund-1",
        grant_revision="1", effective_max_effects=1)
    pol = LocalExecutionPolicy(
        allowed_institutions=frozenset({op.institution_id}), allowed_authority_domains=frozenset({op.authority_domain}),
        allowed_adapters=frozenset({op.adapter_id}), allowed_actions=frozenset({op.action_id}),
        allowed_target_prefixes=("urn:cognous:synthetic-account:",), allowed_units=frozenset({"USD"}),
        max_amount=1000.0, max_effects=1)
    return op, pol


def snap(op, effect="effect-1"):
    from engine.safe_executor import EXECUTION_ENVELOPE_VERSION, ExecutionEnvelope, snapshot_envelope
    return snapshot_envelope(ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", effect, op))


# ------------------------------------------------------------ path traversal
@pytest.mark.parametrize("name", ["../escape.sqlite3", "../../escape.sqlite3", "sub/../../escape.sqlite3"])
def test_probe_path_traversal_relative_database_name_denied_and_nothing_created(tmp_path, name):
    from engine.safe_executor import DurableRefundDestination
    root = tmp_path / "root"
    with pytest.raises(PermissionError):
        DurableRefundDestination(root, name)
    assert not (tmp_path / "escape.sqlite3").exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["root"]
    assert list(root.glob("**/*.sqlite3")) == []


def test_probe_path_traversal_absolute_database_name_denied_and_nothing_created(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    outside = tmp_path / "outside.sqlite3"
    with pytest.raises(PermissionError):
        DurableRefundDestination(tmp_path / "root", str(outside))
    assert not outside.exists()


def test_probe_path_traversal_confinement_control_in_root_database_is_accepted(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    d = DurableRefundDestination(tmp_path / "root", "ok.sqlite3")  # control: the detector is not reject-all
    assert d.path.parent == d.root and d.path.exists()


# ------------------------------------------------------------------ symlinks
def test_probe_symlink_database_file_to_outside_denied_and_target_untouched(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    root = tmp_path / "root"; root.mkdir()
    real = tmp_path / "real.sqlite3"; real.write_bytes(b"")
    (root / "refunds.sqlite3").symlink_to(real)
    with pytest.raises(PermissionError):
        DurableRefundDestination(root)
    assert real.read_bytes() == b""


def test_probe_symlink_dangling_database_link_to_outside_does_not_create_outside_file(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    root = tmp_path / "root"; root.mkdir()
    target = tmp_path / "planted.sqlite3"
    (root / "refunds.sqlite3").symlink_to(target)  # dangling: exists() is False
    with pytest.raises(PermissionError):
        DurableRefundDestination(root)
    assert not target.exists()


def test_probe_symlink_root_directory_and_parent_component_denied(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    real = tmp_path / "real"; real.mkdir()
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    with pytest.raises(PermissionError):
        DurableRefundDestination(tmp_path / "link")
    with pytest.raises(PermissionError):
        DurableRefundDestination(tmp_path / "link" / "nested")
    assert list(real.iterdir()) == []


# --------------------------------------------------------- adapter/policy bypass
@pytest.mark.parametrize("field,value", [
    ("adapter_id", "urn:cognous:adapter:other"), ("action_id", "refund.admin"),
    ("target", "urn:cognous:prod-account:customer-1"), ("unit", "EUR"), ("amount", 1000.01),
    ("institution_id", "urn:cognous:institution:other"), ("authority_domain", "payroll"),
])
def test_probe_policy_bypass_out_of_scope_operation_denied_with_no_effect(tmp_path, field, value):
    from engine.safe_executor import DurableRefundDestination, LocalDestinationExecutor
    op, pol = op_and_policy()
    dest = DurableRefundDestination(tmp_path / "state")
    ex = LocalDestinationExecutor(dest, pol)
    bad = replace(op, **{field: value})
    with pytest.raises(PermissionError):
        ex.execute_snapshot(snap(bad))
    assert dest.effect_count(op.grant_id) == 0
    assert dest.observe("effect-1")["state"] == "absent"
    assert any(r["failure_class"] == "policy_denial" for r in dest.failure_history())
    # control: the in-scope operation through the same executor does execute
    assert ex.execute_snapshot(snap(op, "effect-2")).status == "executed"


def test_probe_policy_bypass_payload_tampered_after_commitment_is_refused(tmp_path):
    from engine.safe_executor import DurableRefundDestination, LocalDestinationExecutor
    op, pol = op_and_policy()
    dest = DurableRefundDestination(tmp_path / "state")
    tampered = replace(op, payload={"refund_reason": "swapped after approval"})  # commitment still the original
    with pytest.raises(ValueError, match="commitment"):
        LocalDestinationExecutor(dest, pol).execute_snapshot(snap(tampered))
    assert dest.effect_count(op.grant_id) == 0


def test_probe_policy_bypass_effect_id_cannot_be_rebound_to_different_operation(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    op, _ = op_and_policy()
    dest = DurableRefundDestination(tmp_path / "state")
    dest.commit(snap(op))
    other = replace(op, amount=1.0)
    with pytest.raises(PermissionError, match="different operation"):
        dest.commit(snap(other))
    assert dest.effect_count(op.grant_id) == 1


def test_probe_policy_bypass_cumulative_effect_budget_enforced_across_effect_ids(tmp_path):
    from engine.safe_executor import DurableRefundDestination
    op, _ = op_and_policy()
    dest = DurableRefundDestination(tmp_path / "state")
    dest.commit(snap(op, "effect-1"))
    with pytest.raises(PermissionError, match="max_effects"):
        dest.commit(snap(op, "effect-2"))
    assert dest.effect_count(op.grant_id) == 1


def test_probe_permissions_legacy_engine_denies_unlisted_agent_and_never_executes(tmp_path):
    from engine.engine import AgentEngine
    perm = tmp_path / "permissions.json"
    perm.write_text(json.dumps({"agent1": ["write"]}), encoding="utf-8")
    eng = AgentEngine(tmp_path / "sandbox", perm, tmp_path / "audit.log")
    with pytest.raises(PermissionError):
        eng.execute_action("intruder", {"type": "write", "target": "x", "params": {}})
    with pytest.raises(PermissionError):
        eng.execute_action("agent1", {"type": "delete", "target": "x", "params": {}})
    res = eng.execute_action("agent1", {"type": "write", "target": "x", "params": {}})
    assert res["executed"] is False and res["status"] == "unsupported"
    assert list((tmp_path / "sandbox").iterdir()) == []  # no side effect even for an allowed action


# ------------------------------------------------------------ credential misuse
def test_probe_credential_revoked_or_foreign_grant_refused_at_commit(tmp_path):
    from engine.effective_grant import DERIVATION, EffectiveGrantDestination
    op, _ = op_and_policy()
    s = snap(op)
    dest = EffectiveGrantDestination(tmp_path / "state")
    digest = dest.set_effective_grant(principal=op.principal, grant_id=op.grant_id, revision="1", permissions=["refund.issue"])
    # grant revoked after the caller captured its digest: the captured digest is not a bearer credential
    dest.set_effective_grant(principal=op.principal, grant_id=op.grant_id, revision="2", permissions=["refund.issue"], status="revoked")
    with pytest.raises(PermissionError, match="effective_grant_changed_at_commit"):
        dest.commit(s, expected_effective_grant_digest=digest, effective_grant_derivation_version=DERIVATION)
    # grant re-issued to a different principal cannot be used by the original principal's operation: the final runtime
    # refuses the re-issue itself (a grant id stays bound to one principal for the life of the database); an earlier
    # runtime accepted it and refused the commit. Either way the original operation must not commit.
    try:
        d2 = dest.set_effective_grant(principal="urn:cognous:principal:someone-else", grant_id=op.grant_id, revision="3", permissions=["refund.issue"])
    except PermissionError as exc:
        assert "already bound to another principal" in str(exc)
    else:
        with pytest.raises(PermissionError, match="effective_grant_changed_at_commit"):
            dest.commit(s, expected_effective_grant_digest=d2, effective_grant_derivation_version=DERIVATION)
    assert dest.effect_count(op.grant_id) == 0


def test_probe_credential_host_secrets_not_inherited_by_openshell_cli_subprocess(tmp_path, monkeypatch):
    import hashlib
    from engine.openshell_environment import OpenShellCLI
    fake = tmp_path / "fake-cli"
    fake.write_text(f"#!{sys.executable}\nimport json, os\nprint(json.dumps(dict(os.environ)))\n", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    home = tmp_path / "home"; home.mkdir()
    for k in ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "OPENAI_API_KEY", "DOCKER_HOST", "BASH_ENV"):
        monkeypatch.setenv(k, "host-secret-value")
    cfg = SimpleNamespace(cli_sha256=hashlib.sha256(fake.read_bytes()).hexdigest(), gateway="gw", workspace="ws", timeout_seconds=5)
    seen = json.loads(OpenShellCLI(str(fake), str(home)).run(cfg, ["gateway", "info"]))
    assert "host-secret-value" not in json.dumps(seen)
    assert set(seen) <= {"HOME", "PATH", "XDG_CONFIG_HOME", "LC_CTYPE", "PWD", "SHLVL", "_"}
    assert seen["HOME"] == str(home.resolve())


def test_probe_credential_cli_binary_substitution_refused_by_digest(tmp_path):
    from engine.openshell_environment import OpenShellCLI
    fake = tmp_path / "fake-cli"
    fake.write_text("#!/bin/sh\necho substituted\n", encoding="utf-8"); fake.chmod(0o755)
    home = tmp_path / "home"; home.mkdir()
    cfg = SimpleNamespace(cli_sha256="0" * 64, gateway="gw", workspace="ws", timeout_seconds=5)
    with pytest.raises(PermissionError, match="digest"):
        OpenShellCLI(str(fake), str(home)).run(cfg, ["x"])
