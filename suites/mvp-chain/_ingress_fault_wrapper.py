"""Owner-side fault-injection entrypoint for the ONE supported-ingress ambiguity test (trusted qualification harness only).

SPDX-License-Identifier: Apache-2.0

Started by _ingress_ambiguity.py, as the owner uid, INSTEAD of ``python -m tools.mvp_ingress.server``; it then runs the pinned hub
``tools.mvp_ingress.server.main`` unchanged (same argv, same request schema, same ``simulate=None`` in IngressCore). The only
difference from the real ingress process is this owner-side seam, enabled solely by the environment of the process the owner
starts (a client cannot set it and nothing on the wire selects it):

  * the Runtime's own deterministic transaction seam ``AtomicAuthorityEffectDestination._transaction_stage('after_commit')`` raises
    ONCE, after the destination transaction has durably committed. The Runtime turns that into PostCommitObservationUnavailable
    (acknowledgement/observation unavailable after the effect attempt), exactly the failure class the existing seam is for.
  * capture-only wrappers record, to an owner-only directory outside the state tree, what the live call received: the ``simulate``
    value passed to ``execute_claim_atomic``, the executor's ExecutionResult fields, and a pickle of (claim_id, envelope) so the
    harness can run ``reconcile_claim`` itself afterwards. Capture changes no argument and no result.

This is not a fault-injection subsystem: one hook, one fault, one use.
"""
from __future__ import annotations

import json
import os
import pathlib
import pickle
import sys

sys.dont_write_bytecode = True


def _arg(name):
    argv = sys.argv
    return argv[argv.index(name) + 1]


def install(capture_dir: pathlib.Path):
    sys.path.insert(0, _arg("--runtime"))
    sys.path.insert(0, str(pathlib.Path(_arg("--control-plane")) / "src"))
    sys.path.insert(0, _arg("--control-plane"))
    from engine import local_authority_effect as lae
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor as Exe
    dest_cls = lae.AtomicAuthorityEffectDestination
    state = {"fired": 0}

    def write(name, doc):
        tmp = capture_dir / (name + ".tmp")
        tmp.write_text(json.dumps(doc, sort_keys=True, default=str))
        os.replace(tmp, capture_dir / name)

    original_stage = dest_cls._transaction_stage

    def stage(self, name):
        original_stage(self, name)
        if name == "after_commit" and state["fired"] == 0:
            state["fired"] = 1
            write("hook.json", {"fired": True, "stage": name})
            raise RuntimeError("injected by owner-side harness: acknowledgement unavailable after durable commit")

    dest_cls._transaction_stage = stage

    original_atomic = dest_cls.execute_claim_atomic

    def atomic(self, claim_id, snapshot, *args, **kwargs):
        write("atomic_call.json", {"claim_id": claim_id, "simulate": kwargs.get("simulate", "<absent>"), "kwargs": sorted(kwargs)})
        return original_atomic(self, claim_id, snapshot, *args, **kwargs)

    dest_cls.execute_claim_atomic = atomic

    original_execute = Exe.execute

    def execute(self, *, envelope, claim_id, simulate=None, attempt_id=None):
        with open(capture_dir / "envelope.pickle", "wb") as fh:
            pickle.dump({"claim_id": claim_id, "envelope": envelope}, fh)
        result = original_execute(self, envelope=envelope, claim_id=claim_id, simulate=simulate, attempt_id=attempt_id)
        obs = result.observation if isinstance(result.observation, dict) else {}
        write("executor_result.json", {"simulate_received": simulate, "status": result.status, "attempted": result.attempted,
                                       "acknowledged": result.acknowledged, "observed_state": result.observed_state,
                                       "effect_id": result.effect_id, "newly_executed": result.newly_executed, "error": result.error,
                                       "observation": obs})
        return result

    Exe.execute = execute


if __name__ == "__main__":
    install(pathlib.Path(os.environ["MVP_FAULT_CAPTURE_DIR"]))
    from tools.mvp_ingress.server import main
    sys.exit(main())
