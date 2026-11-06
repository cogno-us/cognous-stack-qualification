"""Interpreter/environment collection for the Internal-A driver (stdlib only).

Compares a pip-compile lock (name==version plus --hash entries) with the distributions visible to
the CURRENT interpreter, and records isolation flags and sys.path. Observation only: it never
installs anything."""
from __future__ import annotations

import hashlib
import importlib.metadata
import os
import platform
import re
import sys

_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([^\s\;]+)")
DEFAULT_TOOLING_ALLOW = ("pip", "setuptools", "wheel")


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(text):
    """Return ({name: version}, {name: hash_count}, errors)."""
    pins, hashes, errors = {}, {}, []
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.endswith("\\"):
            line = line[:-1].strip()
        if not line or line.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        if line.startswith("--hash="):
            if cur is None:
                errors.append(f"hash without a pin: {line[:60]}")
            else:
                hashes[cur] += 1
            continue
        if line.startswith("-"):
            continue
        m = _PIN.match(line)
        if not m:
            errors.append(f"unparseable lock line: {line[:80]}")
            cur = None
            continue
        name = norm(m.group(1))
        if name in pins:
            errors.append(f"duplicate pin: {name}")
        pins[name] = m.group(2)
        hashes[name] = hashes.get(name, 0)
        cur = name
        for h in re.findall(r"--hash=\S+", line):
            hashes[name] += 1
    return pins, hashes, errors


def _installed(dists):
    out, dup = {}, []
    for d in dists:
        name, ver = d
        n = norm(name)
        if n in out and out[n] != ver:
            dup.append(n)
        elif n in out:
            dup.append(n)
        out[n] = ver
    return out, sorted(set(dup))


def _real_distributions():
    for d in importlib.metadata.distributions():
        name = d.metadata["Name"]
        if name:
            yield name, d.version


def collect_environment(lock_path, *, allow_extra=(), allow_tooling=DEFAULT_TOOLING_ALLOW,
                        expected_sys_path=None, distributions=None):
    """`allow_extra`: distribution names allowed beyond the lock (the four component distributions).
    `expected_sys_path`: iterable of paths; when given, every sys.path entry must resolve to one.
    `distributions`: test seam, iterable of (name, version); default is the real interpreter."""
    errors = []
    try:
        with open(lock_path, "rb") as fh:
            raw = fh.read()
        lock_sha = hashlib.sha256(raw).hexdigest()
        pins, hashes, perr = parse_lock(raw.decode("utf-8"))
        errors += perr
    except (OSError, UnicodeDecodeError) as e:
        raw, lock_sha, pins, hashes = b"", None, {}, {}
        errors.append(f"lock unreadable: {e.__class__.__name__}")
    if not pins and lock_sha:
        errors.append("lock contains no pins")
    unhashed = sorted(n for n, c in hashes.items() if c == 0)
    if unhashed:
        errors.append("pins without --hash: " + ", ".join(unhashed[:10]))

    installed, dups = _installed(distributions if distributions is not None else _real_distributions())
    if dups:
        errors.append("duplicate distributions visible: " + ", ".join(dups))
    allowed = {norm(a) for a in allow_extra} | {norm(a) for a in allow_tooling}
    missing = sorted(n for n in pins if n not in installed)
    extra = sorted(n for n in installed if n not in pins and n not in allowed)
    mismatched = {n: {"lock": pins[n], "installed": installed[n]}
                  for n in sorted(pins) if n in installed and installed[n] != pins[n]}

    flags = {"isolated": sys.flags.isolated, "dont_write_bytecode": sys.flags.dont_write_bytecode,
             "ignore_environment": sys.flags.ignore_environment, "no_user_site": sys.flags.no_user_site}
    flags_ok = bool(flags["isolated"]) and bool(flags["dont_write_bytecode"])
    path_entries = list(sys.path)
    unexpected_path = None
    if expected_sys_path is not None:
        exp = {os.path.realpath(p) for p in expected_sys_path}
        unexpected_path = [p for p in path_entries if p == "" or os.path.realpath(p) not in exp]

    ok = (not errors and not missing and not extra and not mismatched and flags_ok
          and (unexpected_path is not None and not unexpected_path))
    return {
        "python": {"version": platform.python_version(),
                   "implementation": platform.python_implementation(),
                   "executable": sys.executable},
        "platform": {"system": platform.system(), "machine": platform.machine(),
                     "platform": platform.platform()},
        "distributions": dict(sorted(installed.items())),
        "lock_sha256": lock_sha,
        "locked": dict(sorted(pins.items())),
        "missing_from_env": missing,
        "extra_in_env": extra,
        "mismatched_versions": mismatched,
        "sys_flags": flags,
        "sys_flags_ok": flags_ok,
        "sys_path": path_entries,
        "unexpected_sys_path": unexpected_path,
        "errors": errors,
        "ok": ok,
    }
