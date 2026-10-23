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


def state_tree_stat(state, owner_uid=None):
    entries, bad = [], []
    me = os.geteuid() if owner_uid is None else owner_uid
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


class ProfileBlocked(Exception):
    """The approved ingress profile cannot be established here: NC4 is BLOCKED (and the acceptance verdict INCOMPLETE), never run weaker."""


def _ids(pid):
    """Real/effective uid and gid of a running process as the kernel reports them."""
    fields = {}
    for line in _read(f"/proc/{pid}/status").splitlines():
        if line.startswith(("Uid:", "Gid:")):
            key, *vals = line.split()
            fields[key.rstrip(":").lower()] = [int(v) for v in vals]
    return fields


def _identities():
    """Resolve the dedicated ingress user, client user and IPC group by NAME (set by the workflow) to the real uids and gids on this host."""
    import grp
    import pwd
    names = {"ingress_user": os.environ.get("MVP_INGRESS_USER"), "client_user": os.environ.get("MVP_CLIENT_USER"), "ipc_group": os.environ.get("MVP_IPC_GROUP")}
    unset = sorted(k for k, v in names.items() if not v)
    if unset:
        raise ProfileBlocked(f"approved ingress profile: {unset} not named (MVP_INGRESS_USER, MVP_CLIENT_USER, MVP_IPC_GROUP); use MVP_INGRESS_PROFILE=developer-optout for a local run (verdict INCOMPLETE)")
    try:
        ing, cli, ipc = pwd.getpwnam(names["ingress_user"]), pwd.getpwnam(names["client_user"]), grp.getgrnam(names["ipc_group"])
    except KeyError as exc:
        raise ProfileBlocked(f"approved ingress profile: {exc} does not exist on this host") from None
    if 0 in (ing.pw_uid, cli.pw_uid) or ing.pw_uid == cli.pw_uid or ing.pw_gid == cli.pw_gid or ipc.gr_gid in (0, ing.pw_gid, cli.pw_gid):
        raise ProfileBlocked("approved ingress profile needs a non-root ingress user and client user with distinct primary groups and a dedicated IPC group")
    return {"ingress_user": ing.pw_name, "ingress_uid": ing.pw_uid, "ingress_gid": ing.pw_gid, "client_user": cli.pw_name, "client_uid": cli.pw_uid,
            "client_gid": cli.pw_gid, "ipc_group": ipc.gr_name, "ipc_gid": ipc.gr_gid, "client_groups": sorted(os.getgrouplist(cli.pw_name, cli.pw_gid))}


def yama_block_reason(ptrace_scope):
    """None when kernel.yama.ptrace_scope >= 1; otherwise why the boundary test is BLOCKED (Yama absent is unsupported, never a weaker substitute)."""
    if ptrace_scope in ("1", "2", "3"):
        return None
    return (f"kernel.yama.ptrace_scope is {ptrace_scope!r} (the approved profile requires >= 1; set it with sudo sysctl, or Yama is absent): "
            "the exact profile is unsupported, the boundary test is BLOCKED and no weaker environment is substituted")


def _drop(uid, gid, groups, umask=None):
    def drop():
        os.setgroups(groups)
        os.setresgid(gid, gid, gid)
        os.setresuid(uid, uid, uid)
        if umask is not None:
            os.umask(umask)
    return drop


def _run_as(uid, gid, fn):
    """Run fn() in a forked child that has dropped to uid:gid (umask 077) and return its JSON-able result. Owner-side observations are made as the ingress
    uid so that the harness (root) never creates a root-owned file (for example a sqlite shm/wal) inside the ingress state tree."""
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(r)
            _drop(uid, gid, [], 0o077)()
            data = json.dumps({"ok": fn()}, default=str).encode()
        except BaseException as exc:  # noqa: BLE001
            data = json.dumps({"error": f"{type(exc).__name__}: {exc}"}).encode()
        while data:
            data = data[os.write(w, data):]
        os._exit(0)
    os.close(w)
    chunks = []
    while True:
        chunk = os.read(r, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    os.close(r)
    os.waitpid(pid, 0)
    out = json.loads(b"".join(chunks) or b'{"error": "no output"}')
    if "error" in out:
        raise RuntimeError("owner-side observation failed: " + out["error"])
    return out["ok"]


def capture_environment_record(hub, ident, profile, *, state, sock, pid, dest, record_path):
    """Run the hub capture script (hub PR #219, pinned by sha256 in the environment profile) as root against THIS running ingress, then bind the record to this
    run with a gate-side envelope. The hub record is left byte-for-byte as the script wrote it."""
    rec_cfg = profile["hub_record"]
    script = pathlib.Path(hub) / rec_cfg["capture_script"]["path"]
    result = {"captured": False, "script": rec_cfg["capture_script"]["path"]}
    if not script.is_file():
        result["reason"] = "the hub checkout at the tuple sha has no capture script (the tuple's hub sha predates it)"
        return result
    heads = _state.ENV.get("heads") or {}
    evidence_label = "hosted-runner acceptance run %s, profile=approved" % (os.environ.get("MVP_RUN_ID") or "UNBOUND")
    cmd = [sys.executable, "-I", str(script), "--state-dir", str(state), "--socket", sock, "--ingress-pid", str(pid),
           "--ingress-uid", str(ident["ingress_uid"]), "--ingress-gid", str(ident["ingress_gid"]),
           "--client-uid", str(ident["client_uid"]), "--client-gid", str(ident["client_gid"]), "--outsider-uid", str(rec_cfg["outsider_uid"]),
           "--db", str(dest), "--authority-store", str(dest), "--ledger", str(pathlib.Path(state) / "ingress.db"),
           "--journal-mode", rec_cfg["journal_mode"], "--label", evidence_label, "--accept-unverified-pins", "--repo-root", str(hub), "--out", str(record_path)]
    for name, sha_ in sorted(heads.items()):
        cmd += ["--pin", f"{name}={sha_}"]
    for f in sorted((pathlib.Path(hub) / "tools" / "mvp_ingress").glob("*.py")):
        cmd += ["--pin", f"source_sha256.tools/mvp_ingress/{f.name}={sha(f.read_bytes())}"]
    man = rec_cfg["manifest"]
    manifest = pathlib.Path(_state.ENV["dirs"].get(man["component"], "/nonexistent")) / man["path"]
    if manifest.is_file():
        cmd += ["--manifest", str(manifest), "--pin", f"manifest_sha256.{manifest.name}={sha(manifest.read_bytes())}"]
    pathlib.Path(record_path).parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(cmd, cwd=hub, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=300)
    result.update(exit_code=p.returncode, stderr_tail=p.stderr[-300:])
    if not pathlib.Path(record_path).is_file():
        result["reason"] = "the capture script wrote no record"
        return result
    record_bytes = pathlib.Path(record_path).read_bytes()
    try:
        rec = json.loads(record_bytes)
    except ValueError:
        result["reason"] = "the capture script wrote an unreadable record"
        return result
    envelope = {"schema": "cognous.mvp-environment-record-envelope/1", "non_authorizing": True, "release": "HOLD",
                "record_sha256": rec.get("record_sha256"), "record_file_sha256": sha(record_bytes),
                "capture_script_path": rec_cfg["capture_script"]["path"], "capture_script_sha256": sha(script.read_bytes()),
                "hub_sha": heads.get("hub"), "environment_profile_sha256": sha((_PROFILE_PATH).read_bytes()), "capture_exit_code": p.returncode}
    for key, env_name in (("run_id", "MVP_RUN_ID"), ("qualification_sha", "MVP_QUALIFICATION_SHA")):
        if os.environ.get(env_name):
            envelope[key] = os.environ[env_name]
    (pathlib.Path(record_path).parent / "environment-record.envelope.json").write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    result.update(captured=True, overall=rec.get("overall"), record_sha256=rec.get("record_sha256"))
    return result


_PROFILE_PATH = pathlib.Path(__file__).resolve().parents[2] / "process" / "mvp-acceptance" / "environment-profile.proposed.v1.json"


def run(work):
    obs = {"source_level": {}, "limitations": {}}
    mode = os.environ.get("MVP_INGRESS_PROFILE", "approved")
    obs["profile"] = mode
    hub = _state.ENV["dirs"].get("hub")
    obs["source_level"] = {"scope": "SOURCE-LEVEL assertions (AST over the pinned hub source and D1's own AST tests), not execution observations"}
    if mode not in ("approved", "developer-optout"):
        return {"status": "blocked", "blocked_reason": f"unknown MVP_INGRESS_PROFILE {mode!r} (approved or developer-optout)", "ingress": {"probe_ran": False, "profile": mode}}
    optout = mode == "developer-optout"
    if not hub:
        return {"status": "blocked", "blocked_reason": "hub checkout not provided (MVP_HUB_DIR)", "ingress": {"probe_ran": False, "profile": mode}}
    hub = pathlib.Path(hub)
    obs["source_level"].update(ast_simulate_scan(hub))
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
    blocked = lambda why: {**obs, "status": "blocked", "ingress": {"probe_ran": False, "profile": mode}, "blocked_reason": why}  # noqa: E731
    if os.geteuid() != 0:
        return blocked("environment cannot run the ingress and client as other uids (needs root to drop privileges); NC4 is never passed without that")
    try:
        ident = ({"ingress_user": None, "ingress_uid": 0, "ingress_gid": 0, "client_user": None, "client_uid": UNPRIV_UID, "client_gid": UNPRIV_UID,
                  "ipc_group": None, "ipc_gid": None, "client_groups": []} if optout else _identities())
    except ProfileBlocked as exc:
        return blocked(str(exc))
    if not optout and yama_block_reason(env_info["ptrace_scope"]):
        return blocked(yama_block_reason(env_info["ptrace_scope"]))
    profile = json.loads(_PROFILE_PATH.read_text())
    dump = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("_dump_d1_cases.py")), str(hub)], cwd=hub,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=120)
    if dump.returncode != 0:
        return blocked("cannot load D1 adversarial cases: " + dump.stderr[-300:])
    cases = json.loads(dump.stdout)
    base = pathlib.Path(tempfile.mkdtemp(prefix="mvp-nc4-"))
    os.chmod(base, 0o755)
    state = base / "state"
    ipc_dir = base if optout else base / "ipc"
    sock = str(ipc_dir / "ingress.sock")
    dump_dir = base / "dump"
    module_dump = (dump_dir if not optout else base) / "ingress-modules.json"
    if not optout:
        # the ingress owns its 0700 state directory; the socket lives in a SEPARATE IPC directory (the setgid bit gives the socket the dedicated group; 2751: others may only
        # traverse, never list or write, so the outsider probe is denied by the socket's own mode and group, not by the directory)
        for d, mode_, gid in ((state, 0o700, ident["ingress_gid"]), (ipc_dir, 0o2751, ident["ipc_gid"]), (dump_dir, 0o700, ident["ingress_gid"])):
            d.mkdir()
            os.chown(d, ident["ingress_uid"], gid)
            os.chmod(d, mode_)
    cmd = [sys.executable, "-m", "tools.mvp_ingress.server", "--state-dir", str(state), "--socket", sock,
           "--control-plane", _state.ENV["dirs"]["control_plane"], "--runtime", _state.ENV["dirs"]["runtime"], "--socket-mode", "666" if optout else "660"]
    # observation only (AP-06): a sitecustomize in the ingress process writes its sys.modules at exit; it changes no behaviour
    probe_dir = pathlib.Path(__file__).resolve().parents[1] / "mvp-applicability" / "plugin" / "ingress_probe"
    dump_path = _state.results_dir() / "artifacts" / "ingress-modules.json"
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    penv = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MVP_INGRESS_MODULE_DUMP=str(module_dump),
                PYTHONPATH=os.pathsep.join([str(hub), str(probe_dir)] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])))
    if not optout:
        penv["HOME"] = "/nonexistent"
    proc = subprocess.Popen(cmd, cwd=hub, env=penv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            preexec_fn=None if optout else _drop(ident["ingress_uid"], ident["ingress_gid"], [], None))
    try:
        line = proc.stdout.readline()
        if line.strip() != "READY":
            proc.kill()
            return blocked("ingress did not start: " + proc.stderr.read()[-500:])
        shutil.copy(hub / "tools" / "mvp_ingress" / "client.py", base / "client.py")
        (base / "probe.py").write_text(PROBE)
        for f in ("client.py", "probe.py"):
            os.chmod(base / f, 0o644)
        dest = state / "atomic" / "refunds.sqlite3"
        ingress_ids = _ids(proc.pid)
        real_uid, real_gid = ingress_ids["uid"][0], ingress_ids["gid"][0]
        env_record = {"captured": False, "reason": "developer opt-out: no environment record is captured"}
        if not optout:
            # captured IN THIS RUN against the very process attacked below, as root, with the workflow's run id and qualification sha
            env_record = capture_environment_record(hub, ident, profile, state=state, sock=sock, pid=proc.pid, dest=dest,
                                                    record_path=_state.results_dir() / "artifacts" / "environment-record.json")
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
            drop = _drop(ident["client_uid"], ident["client_gid"], ident["client_groups"], None)
            p = subprocess.run(["/usr/bin/python3", "-I", str(base / "probe.py"), str(state), str(base / "client.py"), sock, str(proc.pid), str(plan)],
                               preexec_fn=drop, env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"}, capture_output=True, text=True, timeout=600)
            if p.returncode != 0:
                return {"error": p.stderr[-500:]}
            return json.loads(p.stdout)

        def snapshot():
            def observe():
                return {"dest_tables": tables_digest(dest), "ledger": [list(r) for r in ledger_rows(state / "ingress.db")], "state_stat": state_tree_stat(state, real_uid)}
            return observe() if optout else _run_as(real_uid, real_gid, observe)

        before = snapshot()
        attack = client("attack", [b.hex() for b in bodies], True)
        if "error" in attack:
            return {**obs, "status": "blocked", "ingress": {"probe_ran": False, "profile": mode}, "blocked_reason": "unprivileged client failed to run: " + attack["error"]}
        after_attack = snapshot()
        sock_st = os.stat(sock)
        sock_mode = oct(stat.S_IMODE(sock_st.st_mode))
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
        conn = sqlite3.connect(dest.resolve().as_uri() + "?mode=ro", uri=True) if optout else None
        try:
            if conn is None:
                claim_states = _run_as(real_uid, real_gid, lambda: dict(sqlite3.connect(dest.resolve().as_uri() + "?mode=ro", uri=True).execute(
                    "SELECT state, count(*) FROM execution_claims_v1 GROUP BY state").fetchall()))
            else:
                claim_states = dict(conn.execute("SELECT state, count(*) FROM execution_claims_v1 GROUP BY state").fetchall())
        finally:
            if conn is not None:
                conn.close()
        direct_keys = [k for k in attack if k not in ("responses", "uid", "euid", "gid", "groups")]
        obs["ingress"] = {
            "profile": mode, "probe_ran": True, "hub_head": _state.ENV["heads"].get("hub"), "server_pid_alive_after": proc.poll() is None,
            "ingress_uid": real_uid, "ingress_gid": real_gid, "ingress_is_root": real_uid == 0, "ingress_user": ident["ingress_user"],
            "client_uid": attack["uid"], "client_euid": attack["euid"], "client_gid": attack["gid"], "client_groups": attack["groups"], "client_user": ident["client_user"],
            "ipc_group": ident["ipc_group"], "ipc_gid": sock_st.st_gid, "socket_uid": sock_st.st_uid, "socket_gid": sock_st.st_gid,
            "socket_directory": str(ipc_dir), "state_directory": str(state),
            "client_is_distinct_unprivileged": (attack["uid"] == attack["euid"] == ident["client_uid"] and attack["uid"] not in (0, real_uid)
                                                and sorted(attack["groups"]) == sorted(ident["client_groups"]) and (optout or ident["ipc_gid"] in attack["groups"])),
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
            "environment_record": env_record,
            "evidence_basis": "owner-side table content hashes before/after the attack phase (read as the ingress uid), ledger rows, stat of the state tree, client uid/groups; not ingress self-report",
            "kernel_hardening": env_info,
        }
        return {**obs, "status": "ran"}
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        if module_dump.is_file():  # written at ingress exit by the observation-only sitecustomize
            shutil.copy(module_dump, dump_path)
        shutil.rmtree(base, ignore_errors=True)


def _read(path):
    try:
        return pathlib.Path(path).read_text().strip()
    except OSError as exc:
        return f"unavailable: {type(exc).__name__}"
