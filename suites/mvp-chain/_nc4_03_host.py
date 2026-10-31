"""NC4-03 HOST-DEPENDENT subcases (separately identified; executed on the ratified bounded 2751 profile; never part of the deterministic mutation verdict).

SPDX-License-Identifier: Apache-2.0

Ruling D3 (issue #215 comment 6537418060): IPC directory mode 2751, socket 0660, peer-UID allowlist, bounded synthetic testing only; accepted residual = an outsider can stat
a known socket name, with no connect, listing or state disclosure. Not production. These subcases are NOT source mutations and share no code path with
``_nc4_03_mutations.run_deterministic``; that module never imports this one. A subcase result is PASS, FAIL (an observed fact contradicts the ratified profile) or
BLOCKED (the profile cannot be established or observed here: Yama absent, no named identities, not root, probe error). A BLOCKED or FAILED host subcase is reported
beside the deterministic verdict and can neither convert nor obscure it (``_nc4_03_mutations.compose``).

Profile: ``MVP_INGRESS_PROFILE=approved`` (default; dedicated users via MVP_INGRESS_USER, MVP_CLIENT_USER and MVP_IPC_GROUP) is the ratified profile. ``developer-optout`` runs the
same probes with root as the ingress and uid 65534 as the client for a LOCAL dry run only: facts are recorded under ``observed`` but the status is capped at BLOCKED, never PASS.
PROPOSED; Qualification owns the verdicts.
"""
from __future__ import annotations

import errno
import json
import os
import pathlib
import shutil
import signal
import socket
import stat
import sys
import tempfile
import time

import _ingress
import verdict

PASS, FAIL, BLOCKED = verdict.PASS, verdict.FAIL, verdict.BLOCKED
HOST_SET_PATH = pathlib.Path(__file__).resolve().parent / "nc4_03_host_subcases.v1.json"
OUTSIDER_UID = 65533  # environment-profile.proposed.v1.json: outsider_uid
OPTOUT_IPC_GID = 65532
SUBCASE_IDS = ("NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d")


def _child(uid, gid, groups, fn, timeout=20):
    """Run fn() in a forked child that dropped to uid:gid:groups and return its JSON-able result (dict with ok/error)."""
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(r)
            os.setgroups(groups)
            os.setresgid(gid, gid, gid)
            os.setresuid(uid, uid, uid)
            data = json.dumps({"ok": fn()}, default=str).encode()
        except BaseException as exc:  # noqa: BLE001
            data = json.dumps({"error": f"{type(exc).__name__}: {exc}"}).encode()
        while data:
            data = data[os.write(w, data):]
        os._exit(0)
    os.close(w)
    chunks, deadline = [], time.monotonic() + timeout
    os.set_blocking(r, False)
    while time.monotonic() < deadline:
        try:
            chunk = os.read(r, 65536)
        except BlockingIOError:
            time.sleep(0.01)
            continue
        if not chunk:
            break
        chunks.append(chunk)
    os.close(r)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    os.waitpid(pid, 0)
    return json.loads(b"".join(chunks) or b'{"error": "no output"}')


def _errno(exc):
    return errno.errorcode.get(getattr(exc, "errno", None), type(exc).__name__)


def identities():
    """(ident, ratified). Approved: named dedicated identities (ProfileBlocked propagates as BLOCKED). developer-optout: local dry run, never ratified."""
    mode = os.environ.get("MVP_INGRESS_PROFILE", "approved")
    if mode == "developer-optout":
        return ({"ingress_uid": 0, "ingress_gid": 0, "client_uid": _ingress.UNPRIV_UID, "client_gid": _ingress.UNPRIV_UID, "ipc_gid": OPTOUT_IPC_GID, "client_groups": [OPTOUT_IPC_GID]}, False)
    if mode != "approved":
        raise _ingress.ProfileBlocked(f"unknown MVP_INGRESS_PROFILE {mode!r} (approved or developer-optout)")
    return (_ingress._identities(), True)


def _cap(status, ratified, why_not_ratified):
    return (status, "") if ratified or status == BLOCKED else (BLOCKED, why_not_ratified)


NOT_RATIFIED = "MVP_INGRESS_PROFILE=developer-optout is a local dry run, not the ratified bounded 2751 profile: observed facts recorded, status capped at BLOCKED"


def sub_a_yama(ctx):
    scope = _ingress._read("/proc/sys/kernel/yama/ptrace_scope")
    why = _ingress.yama_block_reason(scope)
    obs = {"ptrace_scope": scope}
    if why:
        return BLOCKED, why, obs
    return PASS, "kernel.yama.ptrace_scope >= 1", obs


def sub_b_uid_separation(ctx):
    ident, ratified = ctx["ident"], ctx["ratified"]
    obs = {"ratified_profile": ratified, "ingress_uid": ident["ingress_uid"], "client_uid": ident["client_uid"], "outsider_uid": OUTSIDER_UID}
    if os.geteuid() != 0:
        return BLOCKED, "needs root to drop to the dedicated uids; cannot establish uid separation here", obs

    def probe():
        st = {}
        for line in open("/proc/self/status").read().splitlines():
            if line.startswith(("Uid:", "Gid:", "Groups:", "CapEff:")):
                k, *v = line.split()
                st[k.rstrip(":").lower()] = v
        return st
    client = _child(ident["client_uid"], ident["client_gid"], [], probe)
    outsider = _child(OUTSIDER_UID, OUTSIDER_UID, [], probe)
    if "error" in client or "error" in outsider:
        return BLOCKED, f"cannot drop privileges: {client.get('error') or outsider.get('error')}", obs
    c, o = client["ok"], outsider["ok"]
    obs.update(client_proc={"uid": c["uid"], "gid": c["gid"], "groups": c["groups"], "cap_eff": c["capeff"]}, outsider_proc={"uid": o["uid"], "gid": o["gid"], "groups": o["groups"], "cap_eff": o["capeff"]})
    facts = {"ingress_not_root_or_optout": ident["ingress_uid"] != 0 or not ratified,
             "client_nonzero_and_distinct_from_ingress": ident["client_uid"] not in (0, ident["ingress_uid"]),
             "client_and_ingress_distinct_primary_groups": ident["client_gid"] != ident["ingress_gid"],
             "outsider_distinct_from_ingress_and_client": OUTSIDER_UID not in (ident["ingress_uid"], ident["client_uid"]),
             "client_dropped_capabilities": set(c["capeff"]) <= {"0000000000000000"}, "outsider_dropped_capabilities": set(o["capeff"]) <= {"0000000000000000"},
             "client_effective_uid_is_declared": c["uid"][:2] == [str(ident["client_uid"])] * 2, "outsider_effective_uid_is_declared": o["uid"][:2] == [str(OUTSIDER_UID)] * 2}
    obs["facts"] = facts
    status = PASS if all(facts.values()) else FAIL
    s, why = _cap(status, ratified, NOT_RATIFIED)
    return s, why or ("dedicated ingress, client and outsider identities are distinct, unprivileged and without capabilities" if s == PASS else f"facts false: {[k for k, v in facts.items() if not v]}"), obs


def sub_c_ipc_2751(ctx):
    ident, ratified = ctx["ident"], ctx["ratified"]
    obs = {"ratified_profile": ratified, "ipc_gid": ident["ipc_gid"]}
    if os.geteuid() != 0:
        return BLOCKED, "needs root to create the ipc directory for the dedicated ingress identity and to drop to the client and outsider uids", obs
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="nc4-03-ipc-"))
    os.chmod(tmp, 0o755)
    ipc = tmp / "ipc"
    sock_path = ipc / "ingress.sock"
    srv_pid = None
    try:
        ipc.mkdir()
        os.chown(ipc, ident["ingress_uid"], ident["ipc_gid"])
        os.chmod(ipc, 0o2751)
        r, w = os.pipe()
        srv_pid = os.fork()
        if srv_pid == 0:  # the ingress side: bind, 0660, listen, accept until killed
            try:
                os.close(r)
                os.setgroups([])
                os.setresgid(ident["ingress_gid"], ident["ingress_gid"], ident["ingress_gid"])
                os.setresuid(ident["ingress_uid"], ident["ingress_uid"], ident["ingress_uid"])
                os.umask(0o007)
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.bind(str(sock_path))
                os.chmod(sock_path, 0o660)
                s.listen(4)
                os.write(w, b"1")
                while True:
                    c, _ = s.accept()
                    c.close()
            except BaseException as exc:  # noqa: BLE001
                os.write(w, ("E" + repr(exc)).encode())
                os._exit(1)
        os.close(w)
        os.set_blocking(r, False)
        ready, t0 = b"", time.monotonic()
        while not ready and time.monotonic() - t0 < 10:
            try:
                ready = os.read(r, 100)
            except BlockingIOError:
                time.sleep(0.02)
        os.close(r)
        if ready != b"1":
            return BLOCKED, f"ingress side could not create the socket: {ready!r}", obs
        dst, sst = os.lstat(ipc), os.lstat(sock_path)
        obs.update(dir_mode=oct(stat.S_IMODE(dst.st_mode)), dir_uid=dst.st_uid, dir_gid=dst.st_gid, socket_mode=oct(stat.S_IMODE(sst.st_mode)), socket_is_socket=stat.S_ISSOCK(sst.st_mode),
                   socket_uid=sst.st_uid, socket_gid=sst.st_gid)

        def outsider():
            res = {}
            try:
                st = os.stat(sock_path)
                res["stat_known_socket"] = "ok"
                res["stat_mode"] = oct(stat.S_IMODE(st.st_mode))
            except OSError as exc:
                res["stat_known_socket"] = _errno(exc)
            try:
                os.listdir(ipc)
                res["listdir"] = "ALLOWED"
            except OSError as exc:
                res["listdir"] = _errno(exc)
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect(str(sock_path))
                res["connect"] = "ALLOWED"
            except OSError as exc:
                res["connect"] = _errno(exc)
            return res

        def member():
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect(str(sock_path))
                return {"connect": "ok"}
            except OSError as exc:
                return {"connect": _errno(exc)}
        o = _child(OUTSIDER_UID, OUTSIDER_UID, [], outsider)
        m = _child(ident["client_uid"], ident["client_gid"], [ident["ipc_gid"]], member)
        if "error" in o or "error" in m:
            return BLOCKED, f"cannot drop privileges for the client probes: {o.get('error') or m.get('error')}", obs
        obs.update(outsider=o["ok"], group_member_client=m["ok"])
        facts = {"dir_mode_is_2751": obs["dir_mode"] == "0o2751", "dir_group_is_ipc_group": obs["dir_gid"] == ident["ipc_gid"], "socket_is_a_socket": obs["socket_is_socket"],
                 "socket_mode_is_0660": obs["socket_mode"] == "0o660", "socket_group_is_ipc_group_via_setgid": obs["socket_gid"] == ident["ipc_gid"],
                 "outsider_can_stat_known_name_residual": o["ok"]["stat_known_socket"] == "ok", "outsider_cannot_list_directory": o["ok"]["listdir"] == "EACCES",
                 "outsider_cannot_connect": o["ok"]["connect"] == "EACCES", "ipc_group_member_can_connect": m["ok"]["connect"] == "ok"}
        obs["facts"] = facts
        s_, why = _cap(PASS if all(facts.values()) else FAIL, ratified, NOT_RATIFIED)
        return s_, why or ("ratified 2751/0660 profile holds: outsider stats the known name only (accepted residual), cannot list or connect; the group member connects" if s_ == PASS
                           else f"facts false: {[k for k, v in facts.items() if not v]}"), obs
    finally:
        if srv_pid:
            try:
                os.kill(srv_pid, signal.SIGKILL)
                os.waitpid(srv_pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass
        shutil.rmtree(tmp, ignore_errors=True)


def sub_d_peer_allowlist(ctx):
    """The pinned hub ``server.serve`` against a stub core: an allowlisted client reaches the core, a socket-group member that is not on the allowlist gets PEER_NOT_ALLOWED
    before any request byte is read, and an empty allowlist is refused. Bounded synthetic: the stub core holds no authority."""
    ident, ratified, hub = ctx["ident"], ctx["ratified"], ctx.get("hub")
    obs = {"ratified_profile": ratified}
    if os.geteuid() != 0:
        return BLOCKED, "needs root to drop to the ingress, client and group-member uids", obs
    if not hub or not (pathlib.Path(hub) / "tools" / "mvp_ingress" / "server.py").is_file():
        return BLOCKED, "pinned hub checkout not available (MVP_HUB_DIR)", obs
    member_uid = 65531
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="nc4-03-peer-"))
    os.chmod(tmp, 0o755)
    srcdir = tmp / "hubcopy"
    shutil.copytree(pathlib.Path(hub) / "tools", srcdir / "tools", ignore=shutil.ignore_patterns("__pycache__", "mvp_env_record"))
    for d, _, fs in os.walk(srcdir):
        os.chmod(d, 0o755)
        for f in fs:
            os.chmod(pathlib.Path(d) / f, 0o644)
    ipc = tmp / "ipc"
    ipc.mkdir()
    os.chown(ipc, ident["ingress_uid"], ident["ipc_gid"])
    os.chmod(ipc, 0o2751)
    sock_path = ipc / "ingress.sock"
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(r)
            os.setgroups([])
            os.setresgid(ident["ingress_gid"], ident["ingress_gid"], ident["ingress_gid"])
            os.setresuid(ident["ingress_uid"], ident["ingress_uid"], ident["ingress_uid"])
            os.umask(0o007)
            sys.dont_write_bytecode = True
            sys.path.insert(0, str(srcdir))
            from tools.mvp_ingress import server as hub_server

            class StubCore:
                def handle(self, raw):
                    return {"status": "stub-core-reached"}
            try:
                hub_server.validate_allowed_uids([])
                empty = "ACCEPTED"
            except ValueError:
                empty = "refused"
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(str(sock_path))
            os.chmod(sock_path, 0o660)
            s.listen(4)
            os.write(w, ("1" + empty).encode())
            hub_server.serve(StubCore(), s, allowed_uids=[ident["client_uid"]], max_requests=2, read_timeout=3)
        except BaseException as exc:  # noqa: BLE001
            try:
                os.write(w, ("E" + repr(exc)).encode())
            finally:
                os._exit(1)
        os._exit(0)
    os.close(w)
    os.set_blocking(r, False)
    ready, t0 = b"", time.monotonic()
    while not ready and time.monotonic() - t0 < 15:
        try:
            ready = os.read(r, 100)
        except BlockingIOError:
            time.sleep(0.02)
    os.close(r)
    try:
        if not ready.startswith(b"1"):
            return BLOCKED, f"ingress side could not serve the stub core: {ready!r}", obs
        obs["empty_allowlist"] = ready[1:].decode()

        def ask():
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(str(sock_path))
            s.sendall(b"{}\n")
            return s.recv(4096).decode()
        allowed = _child(ident["client_uid"], ident["client_gid"], [ident["ipc_gid"]], ask)
        member = _child(member_uid, member_uid, [ident["ipc_gid"]], ask)
        if "error" in allowed or "error" in member:
            return BLOCKED, f"client probe could not run: {allowed.get('error') or member.get('error')}", obs
        obs.update(allowlisted_client_response=allowed["ok"].strip(), non_allowlisted_group_member_response=member["ok"].strip())
        facts = {"empty_allowlist_refused": obs["empty_allowlist"] == "refused", "allowlisted_client_reaches_core": "stub-core-reached" in allowed["ok"],
                 "non_allowlisted_group_member_refused": "PEER_NOT_ALLOWED" in member["ok"] and "stub-core-reached" not in member["ok"]}
        obs["facts"] = facts
        s_, why = _cap(PASS if all(facts.values()) else FAIL, ratified, NOT_RATIFIED)
        return s_, why or ("peer-UID allowlist enforced by the pinned server.serve: allowlisted uid served, non-allowlisted group member PEER_NOT_ALLOWED" if s_ == PASS
                           else f"facts false: {[k for k, v in facts.items() if not v]}"), obs
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except (ProcessLookupError, ChildProcessError):
            pass
        shutil.rmtree(tmp, ignore_errors=True)


PROBES = {"NC4-03a": ("yama_ptrace_scope", sub_a_yama), "NC4-03b": ("uid_separation", sub_b_uid_separation),
          "NC4-03c": ("ipc_2751_socket_profile", sub_c_ipc_2751), "NC4-03d": ("peer_uid_allowlist", sub_d_peer_allowlist)}


def run_host_subcases(hub_dir=None) -> dict:
    """All four subcases, each independently guarded: a probe exception is BLOCKED for that subcase only. Never raises, never reads the deterministic record."""
    out = {"schema": "cognous.nc4-03-host-record/1", "host_dependent": True, "affects_deterministic_verdict": False, "profile": os.environ.get("MVP_INGRESS_PROFILE", "approved"),
           "kernel": os.uname().release, "subcases": []}
    ctx = {"hub": hub_dir}
    try:
        ctx["ident"], ctx["ratified"] = identities()
        ctx_err = None
    except Exception as exc:  # noqa: BLE001 - ProfileBlocked or an unexpected lookup error: identity-dependent subcases are BLOCKED, Yama is not
        ctx_err = f"{type(exc).__name__}: {exc}"
    for sid, (name, fn) in PROBES.items():
        if sid != "NC4-03a" and ctx_err:
            out["subcases"].append({"id": sid, "name": name, "status": BLOCKED, "reason": ctx_err, "observed": {}})
            continue
        try:
            status, reason, observed = fn(ctx)
        except Exception as exc:  # noqa: BLE001
            status, reason, observed = BLOCKED, f"probe error: {type(exc).__name__}: {exc}", {}
        out["subcases"].append({"id": sid, "name": name, "status": status, "reason": reason, "observed": observed})
    return out


def scenario_observation(hub_dir=None) -> dict:
    """Observation record of scenario ``nc4_03_host`` (the v8 fragment): ``<id>.status`` fields; the scenario itself is never ``blocked`` as a whole so that one blocked
    subcase cannot block the others (each row judges its own status)."""
    rec = run_host_subcases(hub_dir)
    obs = {"status": "ran", "record": rec}
    for sc in rec["subcases"]:
        obs[sc["id"]] = {"status": sc["status"], "reason": sc["reason"]}
    return obs
