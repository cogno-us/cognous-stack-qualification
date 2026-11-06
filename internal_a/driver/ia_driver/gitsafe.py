"""Hardened, read-only git invocation for the Internal-A driver (stdlib only, fail-closed).

Design:
* the git binary is resolved once (shutil.which on the parent PATH) to an absolute path; argv is
  always a list, never a shell;
* a small ALLOWLIST of subcommands, each with an EXACT allowlist of options (no abbreviations, no
  caller-supplied -c/--git-dir/--work-tree/--output/--exec-path etc.); positional arguments may not
  start with '-' unless they follow '--';
* the environment is rebuilt from scratch (no inherited GIT_*; HOME is a nonexistent directory;
  system/global config disabled). Ownership checks are NOT weakened: safe.directory is never set,
  so git's "dubious ownership" refusal is surfaced as a GitError;
* output and runtime are capped; every invocation is logged as a 'git_read' event.

Residual risk (documented, not eliminated): a hostile repository can carry code-execution hooks in
its own .git/config (core.fsmonitor, core.sshCommand, core.gitProxy, core.pager, diff/merge/filter
drivers, aliases, include/includeIf, extensions) or in worktree-config / commondir indirection.
Defence in depth: (a) the -c overrides below force the dangerous knobs off even if config slipped
through, (b) `scan_git_config` refuses such repositories before any git process is started and
run_git enforces it on every call. The scan is a conservative line parser, not a full git-config
implementation; git itself may read config from places the scan does not model, which is why the
checkout must also be an unmodified frozen tree verified by a separate trusted process.
"""
from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import threading
import time

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
_STDERR_CAP = 64 * 1024
NONEXISTENT_HOME = "/nonexistent-ia-driver-home"

ALLOWED_SUBCOMMANDS = {
    "rev-parse": frozenset({"--verify", "--quiet", "--is-inside-work-tree", "--show-toplevel"}),
    "status": frozenset({"--porcelain", "--untracked-files=all", "--ignored", "-z",
                         "--ignore-submodules=none"}),
    "ls-files": frozenset({"-v", "-z", "-s", "--stage", "--cached"}),
    "ls-tree": frozenset({"-z", "-r", "--full-tree", "--name-only"}),
    "cat-file": frozenset({"-t", "-s", "-e", "-p"}),
}

# Refused even before the exact-allowlist check, so the error names the real problem.
_DANGEROUS_PREFIXES = (
    "--exec-path", "-c", "--git-dir", "--work-tree", "--output", "--config", "--namespace",
    "--super-prefix", "--exec", "--upload-pack", "--receive-pack", "--open-files",
    "--textconv", "--filters", "--ext-diff", "--paginate", "--attr-source", "--no-index",
)

_HARDENING_C = (
    "core.fsmonitor=false", "core.hooksPath=/dev/null", "core.untrackedCache=false",
    "core.pager=cat", "core.attributesFile=/dev/null", "core.excludesFile=/dev/null",
    "protocol.allow=never", "core.sshCommand=/bin/false", "core.askPass=/bin/false",
)

_git_bin = None


class GitError(Exception):
    def __init__(self, message, returncode=None, stderr=b""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


def resolve_git():
    """Resolve the git binary once (absolute, executable); cached for the process."""
    global _git_bin
    if _git_bin is None:
        found = shutil.which("git")
        if not found:
            raise GitError("git binary not found")
        _git_bin = os.path.realpath(found)
    return _git_bin


def build_env(git_bin, root):
    """Fully rebuilt environment; nothing is inherited from the parent."""
    path_dirs = []
    for d in (os.path.dirname(git_bin), "/usr/bin", "/bin"):
        if d not in path_dirs:
            path_dirs.append(d)
    return {
        "PATH": os.pathsep.join(path_dirs),
        "HOME": NONEXISTENT_HOME,
        "XDG_CONFIG_HOME": NONEXISTENT_HOME + "/xdg",
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_ASKPASS": "/bin/false",
        "GIT_PAGER": "cat",
        "GIT_CEILING_DIRECTORIES": os.path.dirname(os.path.abspath(root)) or "/",
    }


def validate_args(args):
    if not isinstance(args, (list, tuple)) or not args:
        raise GitError("git args must be a non-empty list")
    for a in args:
        if not isinstance(a, str) or "\0" in a:
            raise GitError("git args must be NUL-free strings")
    sub = args[0]
    if sub not in ALLOWED_SUBCOMMANDS:
        raise GitError(f"git subcommand {sub!r} is not on the allowlist")
    allowed_opts = ALLOWED_SUBCOMMANDS[sub]
    after_sep = False
    for a in args[1:]:
        if after_sep:
            continue
        if a == "--":
            after_sep = True
            continue
        low = a.lower()
        if low.startswith(_DANGEROUS_PREFIXES):
            raise GitError(f"dangerous git option refused: {a!r}")
        if a.startswith("-"):
            if a not in allowed_opts:
                raise GitError(f"git option {a!r} is not allowed for {sub}")
        elif a == "":
            raise GitError("empty git argument refused")
    return sub


def _check_root(root):
    if not isinstance(root, (str, os.PathLike)):
        raise GitError("root must be a path")
    root = os.fspath(root)
    if not os.path.isabs(root) or "\0" in root:
        raise GitError("root must be an absolute path")
    gd = os.path.join(root, ".git")
    if os.path.islink(gd) or not os.path.isdir(gd):
        raise GitError(".git is not a real directory (gitfile/symlink/absent refused)")
    return root


def scan_git_config(root):
    """Read-only scan of <root>/.git/config. Returns a list of violation strings (empty = ok)."""
    problems = []
    gd = os.path.join(root, ".git")
    for extra in ("config.worktree", "commondir"):
        if os.path.lexists(os.path.join(gd, extra)):
            problems.append(f".git/{extra} present (indirection refused)")
    cfg = os.path.join(gd, "config")
    try:
        with open(cfg, "rb") as fh:
            raw = fh.read(1024 * 1024 + 1)
    except OSError as e:
        return problems + [f".git/config unreadable: {e.__class__.__name__}"]
    if len(raw) > 1024 * 1024:
        return problems + [".git/config too large"]
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    # join backslash-continued lines
    text = re.sub(r"\\\n", "", text)
    section = sub = None
    refuse_keys = {
        "core": {"fsmonitor", "hookspath", "worktree", "gitproxy", "sshcommand", "pager", "editor",
                 "askpass", "trustctime", "checkstat", "ignorestat", "attributesfile",
                 "excludesfile", "untrackedcache", "alternaterefscommand", "splitindex",
                 "sparsecheckout", "usereplacerefs"},
        "diff": {"command", "textconv", "external"},
        "merge": {"driver", "tool"},
        "credential": {"helper"},
        "gpg": {"program"},
    }
    always_refused_sections = {"alias", "filter", "include", "includeif", "extensions",
                               "difftool", "mergetool", "pager", "url", "http", "credential",
                               "submodule", "uploadpack", "receivepack", "transfer", "protocol"}
    for lineno, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        while s:
            if s[0] in "#;":
                break
            if s[0] == "[":
                end = s.find("]")
                if end < 0:
                    problems.append(f"config line {lineno}: malformed section header")
                    s = ""
                    break
                hdr = s[1:end].strip()
                m = re.match(r'^([A-Za-z0-9.-]+)(?:\s+"(.*)")?$', hdr)
                if not m:
                    problems.append(f"config line {lineno}: unparseable section {hdr!r}")
                    section = sub = None
                else:
                    name = m.group(1).lower()
                    if "." in name and m.group(2) is None:
                        name, _, sub = name.partition(".")
                    else:
                        sub = m.group(2)
                    section = name
                    if section in always_refused_sections:
                        problems.append(f"config line {lineno}: section [{section}] refused")
                s = s[end + 1:].strip()
                continue
            key = re.split(r"[=\s]", s, maxsplit=1)[0].lower()
            if section in refuse_keys and key in refuse_keys[section]:
                problems.append(f"config line {lineno}: {section}.{key} refused")
            elif section == "remote" and key in ("vcs", "uploadpack", "receivepack",
                                                  "proxy", "proxyauthmethod"):
                problems.append(f"config line {lineno}: remote.{key} refused")
            elif section == "core" and key not in ("repositoryformatversion", "logallrefupdates",
                                                    "symlinks", "ignorecase", "precomposeunicode",
                                                    "filemode", "bare"):
                problems.append(f"config line {lineno}: core.{key} not in the accepted set")
            elif section == "core" and key == "filemode" and \
                    not re.match(r"^filemode\s*=\s*true\s*$", s, re.I):
                problems.append(f"config line {lineno}: core.filemode must be true")
            elif section is None:
                problems.append(f"config line {lineno}: key outside any section")
            break
    return problems


def _drain(stream, cap, out, flag):
    try:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                return
            room = cap + 1 - sum(len(c) for c in out)
            if room > 0:
                out.append(chunk[:room])
            if sum(len(c) for c in out) > cap:
                flag.append(True)
                return
    except (OSError, ValueError):
        return


def run_git(root, args, events, *, timeout=30, max_bytes=DEFAULT_MAX_BYTES, git_bin=None):
    """Run one allowlisted read-only git command in `root`; return stdout bytes or raise GitError.

    `git_bin` exists for tests (fake git); production callers leave it None."""
    root = _check_root(root)
    sub = validate_args(list(args))
    problems = scan_git_config(root)
    if problems:
        raise GitError("unsafe .git/config: " + "; ".join(problems))
    exe = git_bin or resolve_git()
    argv = [exe, "--no-pager", "--no-optional-locks", "--literal-pathspecs", "-C", root]
    for c in _HARDENING_C:
        argv += ["-c", c]
    argv += list(args)
    events.add("git_read", argv=list(argv), root=root, subcommand=sub)
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=build_env(exe, root), shell=False,
                                close_fds=True, start_new_session=True, cwd="/")
    except OSError as e:
        raise GitError(f"cannot start git: {e.__class__.__name__}") from None
    out, err, over, eover = [], [], [], []
    t1 = threading.Thread(target=_drain, args=(proc.stdout, max_bytes, out, over), daemon=True)
    t2 = threading.Thread(target=_drain, args=(proc.stderr, _STDERR_CAP, err, eover), daemon=True)
    t1.start()
    t2.start()

    def kill():
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass

    deadline = time.monotonic() + timeout
    timed_out = False
    while proc.poll() is None:
        if over:
            kill()
            break
        if time.monotonic() > deadline:
            timed_out = True
            kill()
            break
        time.sleep(0.01)
    proc.wait()
    t1.join(2)
    t2.join(2)
    for s in (proc.stdout, proc.stderr):
        try:
            s.close()
        except OSError:
            pass
    stderr = b"".join(err)
    if timed_out:
        raise GitError(f"git {sub} timed out after {timeout}s")
    if over:
        raise GitError(f"git {sub} output exceeded {max_bytes} bytes")
    if proc.returncode != 0:
        raise GitError(f"git {sub} failed (rc={proc.returncode}): "
                       f"{stderr[:300].decode('utf-8', 'replace').strip()}",
                       returncode=proc.returncode, stderr=stderr)
    return b"".join(out)
