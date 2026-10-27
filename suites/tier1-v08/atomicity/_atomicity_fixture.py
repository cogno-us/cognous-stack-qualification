"""Worker B fixture and orchestration helpers (atomicity area).

Fixture mechanics are REUSED from the Runtime component tests (imported, not copied): `test_registry_selection_authority` (Env, select_stmt,
trust, REC, GS), `test_registry_selection_effect_guard` (make_claim, binding_of, op_changes, effect_policy) and
`test_atomic_route_valid_flow_identity` (operation). All assertions and oracles in this area are this worker's own.
Orchestration: every actor in a race or crash case is a distinct OS process started with subprocess; ordering uses file barriers and one process
holding a write lock at a named seam.  SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMP = Path(os.environ["V08_COMPONENTS_DIR"]).resolve()

import test_atomic_route_valid_flow_identity as flow  # noqa: E402
import test_registry_selection_authority as v4  # noqa: E402
import test_registry_selection_effect_guard as g  # noqa: E402
from agent_control_plane.bounded import commitment as cp_commitment  # noqa: E402
from engine import registry_selection_authority as sa  # noqa: E402
from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor  # noqa: E402
from engine.local_authority_effect import AtomicAuthorityEffectDestination  # noqa: E402
from engine.safe_executor import EXECUTION_ENVELOPE_VERSION, ExecutionEnvelope, snapshot_envelope  # noqa: E402

EFFECT_TABLES = ("effects", "attempts", "attempt_events", "authority_effect_receipts_v1", "execution_claims_v1", "effect_budgets_v1")


def envelope_i(i: int, max_effects: int = 1, **over) -> ExecutionEnvelope:
    op = dataclasses.replace(flow.operation(), **{**g.op_changes(), "effective_max_effects": max_effects, **over})
    return ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, f"decision-{i}", f"effect-{i}", op)


class World:
    """A governed destination (baselined, snapshot-synced, one ACTIVE required selection) with pre-provisioned claims claim-1..claim-n."""

    def __init__(self, base: Path, n_claims: int = 1, *, max_effects: int = 1, budgets: dict | None = None):
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.max_effects = max_effects
        self.e = v4.Env(self.base).boot()
        self.stmt = v4.select_stmt(v4.REC)
        self.e.activate(self.stmt)
        self.dest = self.e.dest
        for i in range(1, n_claims + 1):
            self.add_claim(i, budget=(budgets or {}).get(i))

    @property
    def db(self) -> Path:
        return self.dest.path

    @property
    def anchor(self) -> Path:
        return self.e.anchor

    def add_claim(self, i: int, budget: str | None = None) -> ExecutionEnvelope:
        env = envelope_i(i, self.max_effects)
        raw = g.make_claim(env, self.e.now, binding=g.binding_of(self.e.state()), claim_id=f"claim-{i}")
        if budget:
            raw.pop("claim_commitment")
            raw["budget_id"] = budget
            raw["claim_commitment"] = cp_commitment(raw)
        self.dest.provision_claim(raw)
        return env

    def fresh_dest(self) -> AtomicAuthorityEffectDestination:
        d = AtomicAuthorityEffectDestination(self.base / "dest", clock=lambda: self.e.now)
        d.configure_selection_authority(self.anchor)
        return d


# ---------------------------------------------------------------------------------------------------------------- database observation
def _tables(conn) -> list:
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def dump_db(path: Path) -> dict:
    """{table: [row_count, sha256 of the sorted rows]} for EVERY table in sqlite_master."""
    conn = sqlite3.connect(str(path))
    try:
        out = {}
        for t in _tables(conn):
            rows = sorted(repr(tuple(r)) for r in conn.execute(f'SELECT * FROM "{t}"'))
            out[t] = [len(rows), hashlib.sha256("\n".join(rows).encode()).hexdigest()]
        return out
    finally:
        conn.close()


def effect_dump(path: Path) -> dict:
    return {k: v for k, v in dump_db(path).items() if k in EFFECT_TABLES}


def counts(path: Path) -> dict:
    conn = sqlite3.connect(str(path))
    try:
        one = lambda q: conn.execute(q).fetchone()[0]  # noqa: E731
        out = {t: one(f"SELECT COUNT(*) FROM {t}") for t in ("effects", "attempts", "attempt_events", "authority_effect_receipts_v1")}
        out["budget_used"] = one("SELECT COALESCE(SUM(used_effects),0) FROM effect_budgets_v1")
        out["claims"] = {r[0]: r[1] for r in conn.execute("SELECT claim_id, state FROM execution_claims_v1 ORDER BY claim_id")}
        out["log_head"] = conn.execute("SELECT activation_sequence FROM selection_log_v1 ORDER BY activation_sequence DESC LIMIT 1").fetchone()
        out["log_head"] = out["log_head"][0] if out["log_head"] else None
        return out
    except sqlite3.Error as exc:
        return {"unreadable": f"{type(exc).__name__}: {exc}"}
    finally:
        conn.close()


def anchor_info(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        a = json.loads(raw)["anchor"]
        return {"head_sequence": a["head_sequence"], "head_entry_hash": a["head_entry_hash"], "sha256": hashlib.sha256(raw).hexdigest()}
    except Exception as exc:  # noqa: BLE001
        return {"error": type(exc).__name__}


# ---------------------------------------------------------------------------------------------------------------- process orchestration
class Child:
    def __init__(self, script: str, spec: dict, tmp: Path, label: str):
        self.label = label
        spec = {**spec, "label": label, "comp": str(COMP)}
        sp = tmp / f"{label}.spec.json"
        sp.write_text(json.dumps(spec))
        self.out_path, self.err_path = tmp / f"{label}.stdout", tmp / f"{label}.stderr"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OCS_REGISTRY_PIN_DIR=str(COMP / "registry"))
        self.started_ns = time.monotonic_ns()
        with open(self.out_path, "wb") as so, open(self.err_path, "wb") as se:
            self.p = subprocess.Popen([sys.executable, str(HERE / script), str(sp)], stdout=so, stderr=se, cwd=str(tmp), env=env)
        self.pid = self.p.pid

    def wait(self, timeout: float = 90.0):
        try:
            return self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()
            return "timeout"

    def kill9(self):
        self.p.kill()  # SIGKILL
        return self.p.wait()

    def result(self):
        try:
            for line in reversed(self.out_path.read_text().splitlines()):
                if line.startswith("V08PROBE "):
                    return json.loads(line[len("V08PROBE "):])
        except Exception:  # noqa: BLE001
            return None
        return None

    def summary(self) -> dict:
        return {"label": self.label, "pid": self.pid, "returncode": self.p.returncode, "result": self.result(),
                "stderr_tail": self.err_path.read_text()[-600:] if self.err_path.exists() else None}


def kill_all(children) -> None:
    for c in children:
        if c.p.poll() is None:
            c.p.kill()
            c.p.wait()


def read_events(path: Path) -> list:
    out = []
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def wait_event(path: Path, label: str, name: str, children, timeout: float = 90.0):
    """The first event `name` of `label`, or None (timeout, or the process died without emitting it)."""
    owner = next((c for c in children if c.label == label), None)
    deadline = time.monotonic() + timeout
    while True:
        for e in read_events(path):
            if e["label"] == label and e["name"] == name:
                return e
        if owner is not None and owner.p.poll() is not None:
            for e in read_events(path):
                if e["label"] == label and e["name"] == name:
                    return e
            return None
        if time.monotonic() > deadline:
            return None
        time.sleep(0.01)


def touch(path: Path) -> int:
    t = time.monotonic_ns()  # taken BEFORE the barrier file appears, so any later event is provably after it
    Path(path).write_text("1")
    return t


def ev_time(events: list, label: str, name: str):
    for e in events:
        if e["label"] == label and e["name"] == name:
            return e["t"]
    return None


class Checks:
    """safety = a failed check is a BREACH; exercise = a failed check means the case did not deliver what it set out to (INCONCLUSIVE)."""

    def __init__(self):
        self.items = []

    def safety(self, name, cond, **detail):
        self.items.append(("safety", name, bool(cond), detail))

    def exercise(self, name, cond, **detail):
        self.items.append(("exercise", name, bool(cond), detail))

    def apply(self, ev: dict, note: str = "") -> str:
        bad_s = [i[1] for i in self.items if i[0] == "safety" and not i[2]]
        bad_e = [i[1] for i in self.items if i[0] == "exercise" and not i[2]]
        ev["verdict"] = "BREACH" if bad_s else "INCONCLUSIVE" if bad_e else "HELD"
        ev["observed"]["checks"] = [{"kind": k, "name": n, "ok": ok, **d} for k, n, ok, d in self.items]
        ev["note"] = (note + " | " if note else "") + (f"failed safety: {bad_s}" if bad_s else "") + (f" failed exercise: {bad_e}" if bad_e else "")
        return ev["verdict"]


def exec_spec(w_base: Path, i: int, tmp: Path, *, hooks=None, go=None, attempt_id=None, max_effects: int = 1) -> dict:
    return {"base": str(w_base), "index": i, "attempt_id": attempt_id or f"att-{i}-{int(time.time_ns())}", "max_effects": max_effects,
            "events": str(tmp / "events.jsonl"), "go": str(go) if go else None, "hooks": hooks or {}}
