"""Default-deny runtime boundary (sys.addaudithook). Installed once per interpreter; inert until activated.

While active it DENIES (raises AuditDenied and records a 'denied_operation' event): network (socket/http/urllib/ftp/smtp...),
process creation or replacement (subprocess, os.system/exec*/spawn*/fork/posix_spawn, pty), ctypes/foreign code, and any
filesystem MUTATION outside the case scratch directory. Reads outside the allowed prefixes are recorded (kind file_read,
outside_allowed=True) for the reviewer. Audit hooks cannot be removed; that is the point. A hook cannot see everything
(see README residual trust): it is a tripwire plus a block, not a sandbox.
"""
from __future__ import annotations

import os
import sys

DENY_PREFIXES = ("socket.", "ssl.", "http.client.", "urllib.Request", "ftplib.", "smtplib.", "imaplib.", "poplib.", "nntplib.", "telnetlib.",
                 "webbrowser.", "pty.", "ctypes.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "os.forkpty",
                 "os.startfile", "multiprocessing.", "asyncio.subprocess")
# filesystem mutation events -> index of the path argument(s) to check against scratch
MUTATING = {"os.remove": (0,), "os.rename": (0, 1), "os.rmdir": (0,), "os.mkdir": (0,), "os.chmod": (0,), "os.chown": (0,), "os.link": (0, 1),
            "os.symlink": (1,), "os.truncate": (0,), "os.utime": (0,), "os.setxattr": (0,), "os.removexattr": (0,), "shutil.copyfile": (0, 1),
            "shutil.rmtree": (0,), "shutil.move": (0, 1), "shutil.copymode": (1,), "shutil.copystat": (1,), "shutil.chown": (0,), "tempfile.mkstemp": (),
            "tempfile.mkdtemp": ()}
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


class AuditDenied(RuntimeError):
    pass


class _State:
    active = False
    scratch = None
    read_prefixes = ()
    events_fd = None
    sink = None
    installed = False


S = _State()


def _norm(p):
    try:
        return os.path.realpath(os.fsdecode(p))
    except (TypeError, ValueError):
        return None


def _under(path, roots):
    return path is not None and any(path == r or path.startswith(r.rstrip(os.sep) + os.sep) for r in roots)


def _record(ev):
    if S.sink is not None:
        S.sink.append(ev)
    if S.events_fd is not None:
        import json
        try:
            os.write(S.events_fd, (json.dumps(ev, sort_keys=True) + "\n").encode())
        except OSError:
            pass


def _deny(name, detail):
    _record({"kind": "denied_operation", "audit_event": name, "detail": str(detail)[:200]})
    raise AuditDenied(f"ia_driver audit: {name} denied ({str(detail)[:120]})")


def _hook(name, args):
    if not S.active:
        return
    if name.startswith(DENY_PREFIXES):
        _deny(name, args)
    if name == "open":
        path, mode, flags = (list(args) + [None, None, None])[:3]
        p = _norm(path) if not isinstance(path, int) else None
        writing = (isinstance(flags, int) and bool(flags & _WRITE_FLAGS)) or (isinstance(mode, str) and any(c in mode for c in "wax+"))
        if writing and not _under(p, [S.scratch]):
            _deny(name, f"write outside scratch: {path!r}")
        if not writing and p is not None and not _under(p, S.read_prefixes):
            _record({"kind": "file_read", "path": p, "outside_allowed": True})
        return
    if name in MUTATING:
        for i in MUTATING[name]:
            if i < len(args) and not _under(_norm(args[i]), [S.scratch]):
                _deny(name, f"mutation outside scratch: {args[i]!r}")
        if not MUTATING[name]:                      # tempfile.*: location is chosen by tempfile; refuse
            _deny(name, "tempfile creation is not permitted")


def install():
    if not S.installed:
        sys.addaudithook(_hook)
        S.installed = True


def activate(scratch_dir, read_prefixes, events_file=None, sink=None):
    """Turn the policy on. scratch_dir must exist. events_file (inside scratch) receives denials immediately."""
    install()
    S.scratch = os.path.realpath(scratch_dir)
    S.read_prefixes = tuple(os.path.realpath(p) for p in read_prefixes)
    S.sink = sink
    S.events_fd = os.open(events_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600) if events_file else None
    S.active = True


def deactivate():
    """For the PARENT/tests only; a child never calls this. The hook stays installed but inert."""
    S.active = False
    if S.events_fd is not None:
        os.close(S.events_fd)
        S.events_fd = None


def classify_module(file, roots, std_prefixes, site_prefixes):
    f = _norm(file)
    if f is None:
        return "unknown"
    if _under(f, roots):
        return "component_or_pinned_source"
    if _under(f, site_prefixes):
        return "dependency"
    if _under(f, std_prefixes):
        return "stdlib"
    return "UNEXPECTED"


def loaded_module_report(roots, std_prefixes, site_prefixes, driver_prefixes=()):
    """Every module in sys.modules with a file, classified. Built-ins have no file and are listed as builtin."""
    rep = []
    for name, mod in sorted(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        cls = "driver" if _under(_norm(f), [os.path.realpath(p) for p in driver_prefixes]) else classify_module(f, [os.path.realpath(r) for r in roots],
                                                                                                           [os.path.realpath(p) for p in std_prefixes],
                                                                                                           [os.path.realpath(p) for p in site_prefixes])
        rep.append({"module": name, "file": _norm(f), "class": cls})
    return rep
