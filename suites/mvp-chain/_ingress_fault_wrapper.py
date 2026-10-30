"""Owner-side fault-injection entrypoint for the ONE supported-ingress ambiguity test (trusted qualification harness only).

SPDX-License-Identifier: Apache-2.0

Started by _ingress_ambiguity.py, as the owner uid, INSTEAD of ``python -m tools.mvp_ingress.server``; it then runs the pinned hub
``tools.mvp_ingress.server.main`` unchanged (same argv, same request schema, same ``simulate=None`` in IngressCore). The only
difference from the real ingress process is this owner-side seam, enabled solely by the environment of the process the owner
starts (a client cannot set it and nothing on the wire selects it). ``MVP_FAULT_MODE`` is REQUIRED: a comma-separated set of tokens
(absent or unknown tokens: the wrapper refuses to start; there is no default). Product tokens:

  * ``after_commit``: the Runtime's own deterministic transaction seam ``AtomicAuthorityEffectDestination._transaction_stage('after_commit')``
    raises ONCE (first execute only), after the destination transaction has durably committed. The Runtime turns that into
    PostCommitObservationUnavailable (acknowledgement/observation unavailable after the effect attempt).
  * ``bind_fresh``: the synthetic approval binds exactly the request id ``case-1`` (hub synthetic_host.APPROVED_REQUEST_ID). A fresh
    request id would therefore be HELD at decide and never reach the executor, which proves nothing about destination duplicate
    prevention. This token makes the owner-side host build every proposal with that bound correlation id, so a fresh ingress request
    reaches provision and execute a second time and is denied with no second effect (at the pinned tuple by the authoritative effect budget, which is checked
    before the operation-identity guard; this does NOT discriminate the guard from the budget). The wire schema,
    the request ids and the ingress ledger are untouched; the first request (already ``case-1``) is unchanged.

Negative-control tokens (mutations, never used by the product run): ``none`` (no fault), ``forced_simulate`` (a caller-controlled
simulate reaches the executor), ``before_commit`` (raise before the commit, so no effect is durable), ``allow_second_commit`` (the
destination operation guard and record are skipped and the effect budget is un-spent from the second execute on).

Capture-only wrappers record, to an owner-only directory outside the state tree, per call N (1-based): the ``simulate`` value passed to
``execute_claim_atomic`` (``atomic_call.N.json``) and the executor's ExecutionResult fields (``executor_result.N.json``), plus a
pickle of (claim_id, envelope) of the FIRST call only (``envelope.pickle``) so the harness can run ``reconcile_claim`` on the first
claim. Capture changes no argument and no result. This is not a fault-injection subsystem: one hook, one fault, one use.
"""
from __future__ import annotations

import json
import os
import pathlib
import pickle
import sys

sys.dont_write_bytecode = True

TOKENS = frozenset({"after_commit", "bind_fresh", "none", "forced_simulate", "before_commit", "allow_second_commit"})


def parse_modes(raw):
    if raw is None or not raw.strip():
        raise SystemExit("MVP_FAULT_MODE is required (comma-separated tokens: %s)" % ",".join(sorted(TOKENS)))
    modes = frozenset(t.strip() for t in raw.split(",") if t.strip())
    if not modes or not modes <= TOKENS:
        raise SystemExit("unknown MVP_FAULT_MODE token(s): %s" % ",".join(sorted(modes - TOKENS)))
    return modes


def _arg(name):
    argv = sys.argv
    return argv[argv.index(name) + 1]


def install(capture_dir: pathlib.Path, modes):
    sys.path.insert(0, _arg("--runtime"))
    sys.path.insert(0, str(pathlib.Path(_arg("--control-plane")) / "src"))
    sys.path.insert(0, _arg("--control-plane"))
    from engine import local_authority_effect as lae
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor as Exe
    dest_cls = lae.AtomicAuthorityEffectDestination
    state = {"fired": 0, "exec_calls": 0, "atomic_calls": 0}

    def write(name, doc):
        tmp = capture_dir / (name + ".tmp")
        tmp.write_text(json.dumps(doc, sort_keys=True, default=str))
        os.replace(tmp, capture_dir / name)

    original_stage = dest_cls._transaction_stage

    def stage(self, name):
        original_stage(self, name)
        if "after_commit" in modes and name == "after_commit" and state["fired"] == 0:
            state["fired"] = 1
            write("hook.json", {"fired": True, "stage": name})
            raise RuntimeError("injected by owner-side harness: acknowledgement unavailable after durable commit")
        if "before_commit" in modes and name == "after_effect_insert_before_commit" and state["fired"] == 0:
            state["fired"] = 1
            write("hook.json", {"fired": True, "stage": name})
            raise RuntimeError("NEGATIVE-CONTROL MUTATION: failure before the commit")

    dest_cls._transaction_stage = stage

    original_atomic = dest_cls.execute_claim_atomic

    def atomic(self, claim_id, snapshot, *args, **kwargs):
        state["atomic_calls"] += 1
        write("atomic_call.%d.json" % state["atomic_calls"],
              {"claim_id": claim_id, "simulate": kwargs.get("simulate", "<absent>"), "kwargs": sorted(kwargs)})
        return original_atomic(self, claim_id, snapshot, *args, **kwargs)

    dest_cls.execute_claim_atomic = atomic

    if "allow_second_commit" in modes:  # NEGATIVE-CONTROL MUTATION: the operation guard and record are skipped from the second execute on
        from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as OD
        orig_guard, orig_record = OD._operation_guard, OD._operation_record

        def guard(self, conn, snapshot, operation_id):
            if state["exec_calls"] < 2:
                return orig_guard(self, conn, snapshot, operation_id)

        def record(self, conn, snapshot, operation_id):
            if state["exec_calls"] < 2:
                return orig_record(self, conn, snapshot, operation_id)

        OD._operation_guard, OD._operation_record = guard, record

        original_atomic_2 = dest_cls.execute_claim_atomic

        def atomic_unbudgeted(self, claim_id, snapshot, *args, **kwargs):
            if state["exec_calls"] >= 2:  # the authoritative effect budget would stop the second commit before the operation guard: un-spend it
                with self._connect() as conn:
                    conn.execute("UPDATE effect_budgets_v1 SET used_effects=0")
            return original_atomic_2(self, claim_id, snapshot, *args, **kwargs)

        dest_cls.execute_claim_atomic = atomic_unbudgeted

    if "bind_fresh" in modes:
        from tools.mvp_ingress import synthetic_host as sh
        original_build = sh.SyntheticHost.build_proposal

        def build(self, fields):
            return original_build(self, fields).model_copy(update={"correlation_id": sh.APPROVED_REQUEST_ID})

        sh.SyntheticHost.build_proposal = build

    original_execute = Exe.execute

    def execute(self, *, envelope, claim_id, simulate=None, attempt_id=None):
        state["exec_calls"] += 1
        n = state["exec_calls"]
        if "forced_simulate" in modes:  # NEGATIVE-CONTROL MUTATION: a wrapper that lets a caller-controlled value reach simulate
            simulate = "lost_ack"
        if n == 1:
            with open(capture_dir / "envelope.pickle", "wb") as fh:
                pickle.dump({"claim_id": claim_id, "envelope": envelope}, fh)
        result = original_execute(self, envelope=envelope, claim_id=claim_id, simulate=simulate, attempt_id=attempt_id)
        obs = result.observation if isinstance(result.observation, dict) else {}
        write("executor_result.%d.json" % n, {"claim_id": claim_id, "simulate_received": simulate, "status": result.status, "attempted": result.attempted,
                                               "acknowledged": result.acknowledged, "observed_state": result.observed_state,
                                               "effect_id": result.effect_id, "newly_executed": result.newly_executed, "error": result.error,
                                               "observation": obs})
        return result

    Exe.execute = execute


if __name__ == "__main__":
    install(pathlib.Path(os.environ["MVP_FAULT_CAPTURE_DIR"]), parse_modes(os.environ.get("MVP_FAULT_MODE")))
    from tools.mvp_ingress.server import main
    sys.exit(main())
