"""Child processes for the F-A1 OS/crash cases (real processes, real flock, real SIGKILL, real uid separation). Run with PYTHONPATH set to the pinned Runtime."""
import fcntl
import json
import os
import signal
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

mode, spec = sys.argv[1], json.loads(sys.argv[2])


def installer():
    from host.authorization_pin import InstallerConfig, TrustedAuthorizationInstaller
    cfg = InstallerConfig(pin_store_path=Path(spec["store"]), fence_dir=Path(spec["fences"]), anchor_path=Path(spec["anchor"]), log_path=Path(spec["log"]),
                          pin_store_id=spec["store_id"], exclusive_deadline_seconds=2.0)
    return TrustedAuthorizationInstaller(cfg)


if mode == "run":                         # the INSTALLER identity applies Control Plane assessments
    inst = installer()
    for a in spec["assessments"]:
        print(inst.apply_assessment(a).outcome, flush=True)
    inst.assert_custody()
    print("custody-ok", flush=True)
elif mode == "kill":                      # SIGKILL self at a stage, optionally with a hot journal
    inst = installer()

    def hook(name):
        if name == spec["stage"]:
            if spec.get("hot_journal"):
                conn = inst._conn
                conn.execute("PRAGMA cache_size=1")
                blob = "x" * 3000
                for i in range(400):
                    conn.execute("INSERT INTO authorization_pin_v1(pin_epoch, decision_id, status, row_json, pin_digest) VALUES (?,?,?,?,?)",
                                 (1000 + i, "junk", "active", blob, "sha256:" + "1" * 64))
            os.kill(os.getpid(), signal.SIGKILL)
    inst.stage_hook = hook
    inst.apply_assessment(spec["assessment"])
    sys.exit(3)                           # the kill stage was never reached
elif mode == "probe":                     # the EXECUTOR identity: what it must NOT and MAY do
    store, anchor, fences, log, fence, decision_id = (spec[k] for k in ("store", "anchor", "fences", "log", "fence", "decision_id"))
    store_dir, anchor_dir = os.path.dirname(store), os.path.dirname(anchor)

    def attempt(fn):
        try:
            fn()
            return "ALLOWED"
        except PermissionError:
            return "denied"
        except OSError as exc:
            return "denied:errno" + str(exc.errno)
        except sqlite3.Error as exc:
            return "denied:sqlite:" + str(exc)[:60]

    def create(path):
        os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))

    def sql_write(statement):
        def run():
            c = sqlite3.connect(store, timeout=0)
            c.execute(statement)
            c.commit()
            c.close()
        return run
    r = {}
    if spec["kind"] == "install":         # FA1-05: the supplier tries to install / replace a pin
        r["insert_forged_row"] = attempt(sql_write("INSERT INTO authorization_pin_v1(pin_epoch, decision_id, status, row_json, pin_digest) VALUES (99,'forged','active','{}','sha256:00')"))
        r["create_table"] = attempt(sql_write("CREATE TABLE intruder(x)"))
        r["journal_create"] = attempt(lambda: create(store + "-journal"))
        r["new_store_in_dir"] = attempt(lambda: create(os.path.join(store_dir, "forged.sqlite3")))
        r["fence_create_for_forged"] = attempt(lambda: create(os.path.join(fences, "f" * 64 + ".fence")))
        r["anchor_tmp_create"] = attempt(lambda: create(anchor + ".tmp.1"))
        r["anchor_replace_via_rename"] = attempt(lambda: (create(os.path.join(anchor_dir, "evil")), os.replace(os.path.join(anchor_dir, "evil"), anchor)))
    else:                                 # FA1-06 (a): modify / remove / re-permission what exists
        r["update_row_status"] = attempt(sql_write("UPDATE authorization_pin_v1 SET status='revoked'"))
        r["delete_rows"] = attempt(sql_write("DELETE FROM authorization_pin_v1"))
        r["drop_table"] = attempt(sql_write("DROP TABLE authorization_pin_v1"))
        for label, path in (("store", store), ("anchor", anchor), ("fence", fence), ("log", log)):
            r[label + "_open_write"] = attempt(lambda p=path: os.close(os.open(p, os.O_WRONLY)))
            r[label + "_append"] = attempt(lambda p=path: os.close(os.open(p, os.O_WRONLY | os.O_APPEND)))
            r[label + "_truncate"] = attempt(lambda p=path: os.truncate(p, 0))
            r[label + "_unlink"] = attempt(lambda p=path: os.unlink(p))
            r[label + "_rename"] = attempt(lambda p=path: os.rename(p, p + ".moved"))
            r[label + "_chmod"] = attempt(lambda p=path: os.chmod(p, 0o666))
        r["fence_dir_unlink_all"] = attempt(lambda: [os.unlink(os.path.join(fences, n)) for n in os.listdir(fences)])
    out = {"denied_attempts": r}
    # what the executor identity MAY do, through the Runtime guard's own reader: read-only open, read the anchor, take a shared flock on a read-only descriptor
    from engine.authorization_pin import AuthorizationPinConfig, PinReader
    reader = PinReader(AuthorizationPinConfig(pin_store_path=Path(store), fence_dir=Path(fences), anchor_path=Path(anchor), pin_store_id=spec["store_id"]))
    rows = reader.rows_for(decision_id)
    out["reader_rows"] = [(x["pin_epoch"], x["status"]) for x in rows]
    out["reader_anchor_committed_epoch"] = reader.read_anchor()["committed_epoch"]
    fd = os.open(fence, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
    out["shared_flock_on_ro_fd"] = "ok"
    out["euid"] = os.geteuid()
    print(json.dumps(out))
