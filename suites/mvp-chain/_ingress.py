"""NC4 driver: the real MVP trusted-host ingress (hub tools/mvp_ingress, Unix socket), attacked as an unprivileged uid.

SPDX-License-Identifier: Apache-2.0

Verdict inputs are INDEPENDENT observations made by this harness as the owner uid (table content hashes of the destination and
authority store before and after the attack phase, effect/claim/ledger rows, uids, stat of the state tree and socket); the ingress's own
responses are recorded but never decide reachability. If the environment cannot run the client as a different unprivileged uid the
scenario is BLOCKED with the reason; it is never a pass. simulate=None / operation-identity-source are SOURCE-LEVEL assertions
(AST scan of the pinned hub source plus D1's own AST tests), labelled as such. Nothing here claims protection against code running as the
ingress uid or root, and the ingress imports Control Plane test fixtures in-process (known limitation, recorded in KL-01).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile

import _kwflow
import _state

UNPRIV_UID = 65534
SURFACES = ["provision_claim", "execute_claim_atomic", "simulate", "set_grant_status", "set_approval_status", "set_policy_state",
            "set_evidence_state", "raw_sql_destination_write"]
PROBE = r'''
import json, os, sqlite3, sys
sys.dont_write_bytecode = True
state, client_path, sock, pid, plan = sys.argv[1:6]
import importlib.util
spec = importlib.util.spec_from_file_location("declared_client", client_path)
cl = importlib.util.module_from_spec(spec); spec.loader.exec_module(cl)
out = {"uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(), "groups": os.getgroups()}
def attempt(name, fn):
    try:
        fn(); out[name] = "SUCCEEDED"
    except Exception as e:
        out[name] = type(e).__name__
dest = os.path.join(state, "atomic", "refunds.sqlite3")
if json.load(open(plan))["direct"]:
    attempt("listdir_state", lambda: os.listdir(state))
    attempt("open_destination", lambda: open(dest, "rb"))
    attempt("sqlite_destination_rw_delete", lambda: sqlite3.connect(dest).execute("DELETE FROM effects"))
    attempt("sqlite_destination_rw_insert", lambda: sqlite3.connect(dest).execute("INSERT INTO effects(effect_id) VALUES('x')"))
    attempt("sqlite_authority_rw_grant", lambda: sqlite3.connect(dest).execute("UPDATE authority_grants_v1 SET status='revoked'"))
    attempt("sqlite_destination_ro", lambda: sqlite3.connect("file:" + dest + "?mode=ro", uri=True).execute("SELECT * FROM effects"))
    attempt("sqlite_ledger", lambda: sqlite3.connect(os.path.join(state, "ingress.db")).execute("DELETE FROM requests"))
    attempt("create_in_state", lambda: open(os.path.join(state, "planted"), "w"))
    attempt("open_run_record", lambda: open(os.path.join(state, "cp", "run.json"), "rb"))
    attempt("stat_destination", lambda: os.stat(dest))
    attempt("chmod_state", lambda: os.chmod(state, 0o777))
    attempt("rename_state", lambda: os.rename(state, state + ".moved"))
    attempt("proc_mem", lambda: open("/proc/%s/mem" % pid, "rb").read(1))
    attempt("kill_ingress", lambda: os.kill(int(pid), 9))
resp = []
for hexbody in json.load(open(plan))["bodies_hex"]:
    try:
        r = cl.submit_bytes(sock, bytes.fromhex(hexbody))
        resp.append({"outcome": r.get("outcome"), "code": r.get("code")})
    except Exception as e:
        resp.append({"transport_error": type(e).__name__})
out["responses"] = resp
print(json.dumps(out))
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tables_digest(db_path):
    """Content hash of every table of the destination/authority store (owner-side, read-only), plus row counts."""
    conn = sqlite3.connect(pathlib.Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        out = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
            rows = sorted(conn.execute(f'SELECT * FROM "{name}"').fetchall(), key=repr)
            out[name] = {"n": len(rows), "sha256": sha(json.dumps(rows, default=str).encode())}
        return out
    finally:
        conn.close()


def ledger_rows(path):
    conn = sqlite3.connect(pathlib.Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return conn.execute("SELECT * FROM requests").fetchall()
    finally:
        conn.close()


def state_tree_stat(state):
    entries, bad = [], []
    me = os.geteuid()
    for root, dirs, files in os.walk(state):
        for name in dirs + files:
            p = pathlib.Path(root) / name
            st = p.lstat()
            kind = "dir" if stat.S_ISDIR(st.st_mode) else "reg" if stat.S_ISREG(st.st_mode) else "other"
            mode = stat.S_IMODE(st.st_mode)
            entries.append({"path": str(p.relative_to(state)), "kind": kind, "mode": oct(mode), "uid": st.st_uid})
            if st.st_uid != me or (kind == "dir" and mode != 0o700) or (kind == "reg" and mode & 0o077) or kind == "other":
                bad.append(str(p.relative_to(state)))
    top = pathlib.Path(state).lstat()
    return {"n_entries": len(entries), "entries": entries, "violations": bad, "top_mode": oct(stat.S_IMODE(top.st_mode)), "top_uid": top.st_uid}


def ast_simulate_scan(hub):
    findings, files = [], sorted((pathlib.Path(hub) / "tools" / "mvp_ingress").glob("*.py"))
    for f in files:
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "simulate":
                        findings.append({"file": f.name, "line": node.lineno, "is_constant_none": isinstance(kw.value, ast.Constant) and kw.value.value is None})
                    if kw.arg is None and not isinstance(kw.value, ast.Dict):
                        findings.append({"file": f.name, "line": node.lineno, "kwargs_forwarding_non_literal": True,
                                     "callee": ast.unparse(node.func)[:80], "source": ast.unparse(kw.value)[:100]})
    return {"files_scanned": [f.name for f in files], "simulate_keywords": findings,
            "all_simulate_keywords_constant_none": bool([x for x in findings if "is_constant_none" in x]) and all(x["is_constant_none"] for x in findings if "is_constant_none" in x),
            "non_literal_kwargs_forwarding": [x for x in findings if x.get("kwargs_forwarding_non_literal")]}


def run(work):
    obs = {"source_level": {}, "limitations": {}}
    hub = _state.ENV["dirs"].get("hub")
    obs["source_level"] = {"scope": "SOURCE-LEVEL assertions (AST over the pinned hub source and D1's own AST tests), not execution observations"}
    if not hub:
        return {"status": "blocked", "blocked_reason": "hub checkout not provided (MVP_HUB_DIR)", "ingress": {"probe_ran": False}}
    hub = pathlib.Path(hub)
    obs["source_level"].update(ast_simulate_scan(hub))  # v3 predicate inputs, still recorded as raw history (incl. non_literal_kwargs_forwarding)
    obs["source_level"]["kwflow"] = _kwflow.scan_dir(hub)  # v4 NC4-03 data-flow / call-boundary predicate (PROPOSED, see _kwflow.py)
    host_src = (hub / "tools" / "mvp_ingress" / "synthetic_host.py").read_text()
    obs["limitations"] = {"ingress_imports_cp_test_fixtures": "tests.test_runtime_authority" in host_src,
                          "note": "trusted ingress process loads the Control Plane component's tests package (synthetic resolver fixture) in-process; not client reachable; no production authority"}
    ast_test = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_mvp_ingress_boundary.py", "-k", "simulate"],
                              cwd=hub, env={**os.environ, "PYTHONPATH": os.pathsep.join([str(hub)] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])),
                                            "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=300)
    obs["source_level"]["d1_ast_test_exit_code"] = ast_test.returncode
    obs["source_level"]["d1_ast_test_tail"] = ast_test.stdout[-300:]
    # environment capabilities for the unprivileged client
    env_info = {"euid": os.geteuid(), "ptrace_scope": _read("/proc/sys/kernel/yama/ptrace_scope"), "kernel": os.uname().release,
                "cap_eff": next((l.split()[1] for l in _read("/proc/self/status").splitlines() if l.startswith("CapEff")), None)}
    obs["environment"] = env_info
    if os.geteuid() != 0:
        return {**obs, "status": "blocked", "ingress": {"probe_ran": False},
                "blocked_reason": "environment cannot run the client as a distinct unprivileged uid (needs root to drop to uid 65534); NC4 is never passed without that"}
    dump = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("_dump_d1_cases.py")), str(hub)], cwd=hub,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=120)
    if dump.returncode != 0:
        return {**obs, "status": "blocked", "ingress": {"probe_ran": False}, "blocked_reason": "cannot load D1 adversarial cases: " + dump.stderr[-300:]}
    cases = json.loads(dump.stdout)
    base = pathlib.Path(tempfile.mkdtemp(prefix="mvp-nc4-"))
    os.chmod(base, 0o755)
    state, sock = base / "state", str(base / "ingress.sock")
    cmd = [sys.executable, "-m", "tools.mvp_ingress.server", "--state-dir", str(state), "--socket", sock,
           "--control-plane", _state.ENV["dirs"]["control_plane"], "--runtime", _state.ENV["dirs"]["runtime"], "--socket-mode", "666"]
    penv = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=os.pathsep.join([str(hub)] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])))
    proc = subprocess.Popen(cmd, cwd=hub, env=penv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = proc.stdout.readline()
        if line.strip() != "READY":
            proc.kill()
            return {**obs, "status": "blocked", "ingress": {"probe_ran": False}, "blocked_reason": "ingress did not start: " + proc.stderr.read()[-500:]}
        shutil.copy(hub / "tools" / "mvp_ingress" / "client.py", base / "client.py")
        (base / "probe.py").write_text(PROBE)
        for f in ("client.py", "probe.py"):
            os.chmod(base / f, 0o644)
        dest = state / "atomic" / "refunds.sqlite3"
        good, hb = cases["good"], cases["hand_built_claim"]
        bodies = [bytes.fromhex(h) for h in cases["simulate_hex"]]
        bodies += [json.dumps({**good, "request_id": "case-1", k: "x"}).encode() for k in cases["forbidden_members"]]
        bodies += [json.dumps({**good, "claim": hb}).encode(), json.dumps(hb).encode(), json.dumps({**good, "set_grant_status": "revoked"}).encode(),
                   json.dumps({**good, "set_approval_status": "revoked"}).encode(), json.dumps({**good, "provision_claim": True}).encode(),
                   json.dumps({**good, "execute_claim_atomic": True}).encode()]
        bodies += [bytes.fromhex(h) for h in cases["cases_hex"]]

        def client(phase, hex_bodies, direct):
            plan = base / f"plan-{phase}.json"
            plan.write_text(json.dumps({"direct": direct, "bodies_hex": hex_bodies}))
            os.chmod(plan, 0o644)
            def drop():
                os.setgroups([])
                os.setgid(UNPRIV_UID)
                os.setuid(UNPRIV_UID)
            p = subprocess.run(["/usr/bin/python3", "-I", str(base / "probe.py"), str(state), str(base / "client.py"), sock, str(proc.pid), str(plan)],
                               preexec_fn=drop, env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"}, capture_output=True, text=True, timeout=600)
            if p.returncode != 0:
                return {"error": p.stderr[-500:]}
            return json.loads(p.stdout)

        def snapshot():
            return {"dest_tables": tables_digest(dest), "ledger": ledger_rows(state / "ingress.db"), "state_stat": state_tree_stat(state)}

        before = snapshot()
        attack = client("attack", [b.hex() for b in bodies], True)
        if "error" in attack:
            return {**obs, "status": "blocked", "ingress": {"probe_ran": False}, "blocked_reason": "unprivileged client failed to run: " + attack["error"]}
        after_attack = snapshot()
        sock_mode = oct(stat.S_IMODE(os.stat(sock).st_mode))
        legit = client("legit", [json.dumps(good).encode().hex(), json.dumps(good).encode().hex()], False)
        after_legit = snapshot()
        outcomes = {}
        for r in attack["responses"]:
            key = r.get("outcome") or "transport_error"
            outcomes[key] = outcomes.get(key, 0) + 1
        d_before, d_after = before["dest_tables"], after_attack["dest_tables"]
        changed = sorted(t for t in set(d_before) | set(d_after) if d_before.get(t) != d_after.get(t))
        def rows(t):
            return d_after.get(t, {}).get("n")
        reached = []
        if changed:  # any table at all moved during the attack phase
            by_surface = {"provision_claim": ["execution_claims_v1", "effect_budgets_v1"], "execute_claim_atomic": ["effects", "attempts", "authority_effect_receipts_v1", "operation_effects_v1"],
                          "set_grant_status": ["authority_grants_v1"], "set_approval_status": ["authority_approvals_v1"], "set_policy_state": ["authority_policies_v1"],
                          "set_evidence_state": ["authority_evidence_v1"]}
            for surface, tbls in by_surface.items():
                if any(t in changed for t in tbls):
                    reached.append(surface)
            if any(t not in sum(by_surface.values(), []) for t in changed):
                reached.append("raw_sql_destination_write")
        if outcomes.get("executed", 0) or outcomes.get("unknown", 0):
            reached.append("simulate")
        if any(attack.get(k) == "SUCCEEDED" for k in attack if k not in ("responses",)):
            reached.append("raw_sql_destination_write")
        if after_attack["ledger"] != before["ledger"]:
            reached.append("ingress_ledger_write")
        if after_attack["state_stat"]["violations"] or (state.parent / "state.moved").exists() or (state / "planted").exists():
            reached.append("state_tree_modified")
        reached = sorted(set(reached))
        legit_counts = {"effects": after_legit["dest_tables"].get("effects", {}).get("n"), "claims_rows": after_legit["dest_tables"].get("execution_claims_v1", {}).get("n")}
        conn = sqlite3.connect(dest.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            claim_states = dict(conn.execute("SELECT state, count(*) FROM execution_claims_v1 GROUP BY state").fetchall())
        finally:
            conn.close()
        direct_keys = [k for k in attack if k not in ("responses", "uid", "euid", "gid", "groups")]
        obs["ingress"] = {
            "probe_ran": True, "hub_head": _state.ENV["heads"].get("hub"), "server_pid_alive_after": proc.poll() is None,
            "ingress_uid": os.geteuid(), "client_uid": attack["uid"], "client_euid": attack["euid"], "client_groups": attack["groups"],
            "client_is_distinct_unprivileged": attack["uid"] == attack["euid"] == UNPRIV_UID and os.geteuid() != UNPRIV_UID and attack["groups"] == [],
            "socket_mode": sock_mode, "state_tree_owner_only_before": before["state_stat"]["violations"] == [] and before["state_stat"]["top_mode"] == "0o700",
            "state_tree_owner_only_after": after_legit["state_stat"]["violations"] == [] and after_legit["state_stat"]["top_mode"] == "0o700",
            "state_tree_n_entries": after_legit["state_stat"]["n_entries"], "state_tree_top": [after_legit["state_stat"]["top_mode"], after_legit["state_stat"]["top_uid"]],
            "n_attack_bodies": len(bodies), "attack_outcomes": outcomes, "attack_tables_changed": changed,
            "direct_access_results": {k: attack[k] for k in direct_keys},
            "direct_access_all_denied": all(attack[k] in ("PermissionError", "OperationalError") for k in direct_keys),
            "attempted_surfaces": sorted(set(SURFACES) | {"ingress_ledger_write", "state_tree_modified"}),
            "reached_surfaces": reached,
            "legit_after": {"responses": legit.get("responses"), **legit_counts, "claim_states": claim_states,
                            "exactly_one_effect_one_consumed_claim": legit_counts["effects"] == 1 and claim_states == {"consumed": 1}},
            "attacker_could_not_stop_ingress": proc.poll() is None,
            "evidence_basis": "owner-side table content hashes before/after the attack phase, ledger rows, stat of the state tree, client uid/groups; not ingress self-report",
            "kernel_hardening": env_info,
        }
        return {**obs, "status": "ran"}
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(base, ignore_errors=True)


def _read(path):
    try:
        return pathlib.Path(path).read_text().strip()
    except OSError as exc:
        return f"unavailable: {type(exc).__name__}"
