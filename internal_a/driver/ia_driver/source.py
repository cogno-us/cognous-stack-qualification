"""Fail-closed verification of explicitly provided source checkout roots (real git working trees).

The driver records OBSERVED values only. Expected commit/tree are used for structural checks and
refusals; the evaluator performs the authoritative value comparison against the oracle."""
from __future__ import annotations

import hashlib
import os
import re
import stat

from . import gitsafe
from .gitsafe import GitError

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
MAX_FILE_BYTES = 16 * 1024 * 1024

DEFAULT_PREFIXES = {
    "orchestrator": "orch",
    "action_manifest": "am",
    "control_plane": "cp",
    "replay_bundle": "rb",
    "evidence_pack": "pk",
}


def _blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec - git object id


class _Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail=""):
        self.items.append({"name": name, "ok": bool(ok), "detail": str(detail)})
        return bool(ok)


def _valid_rel(rel):
    if not isinstance(rel, str) or not rel or "\0" in rel or "\\" in rel or rel.startswith("/"):
        return False
    return all(p not in ("", ".", "..") for p in rel.split("/"))


def _read_regular_file(root, rel):
    """Return (bytes|None, problem|None). No symlink components; regular file only."""
    cur = root
    parts = rel.split("/")
    for i, part in enumerate(parts):
        cur = os.path.join(cur, part)
        try:
            st = os.lstat(cur)
        except FileNotFoundError:
            return None, "missing"
        except OSError as e:
            return None, f"unreadable ({e.__class__.__name__})"
        if stat.S_ISLNK(st.st_mode):
            return None, "symlink component"
        if i < len(parts) - 1 and not stat.S_ISDIR(st.st_mode):
            return None, "parent is not a directory"
        if i == len(parts) - 1 and not stat.S_ISREG(st.st_mode):
            return None, "not a regular file"
    try:
        fd = os.open(cur, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
    except OSError as e:
        return None, f"unreadable ({e.__class__.__name__})"
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return None, "not a regular file"
        if st.st_size > MAX_FILE_BYTES:
            return None, "too large"
        with os.fdopen(fd, "rb", closefd=False) as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            return None, "too large"
        return data, None
    finally:
        os.close(fd)


def _parse_ls_files_stage(raw):
    ents = []
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        mode, sha, stage = (meta.split(b" ") + [b"", b"", b""])[:3]
        ents.append((mode.decode(), sha.decode(), stage.decode(), path.decode("utf-8", "surrogateescape")))
    return ents


def verify_checkout(label, root, *, expected_commit, expected_tree, files, events, timeout=30):
    c = _Checks()
    observed = {"commit": None, "tree": None, "files": {}}
    notes = []
    result = {"label": label, "ok": False, "checks": c.items, "observed": observed,
              "refusals": [], "notes": notes}

    def finish():
        bad = [x for x in c.items if not x["ok"]]
        result["refusals"] = [f"{x['name']}: {x['detail']}" for x in bad]
        result["ok"] = not bad and bool(c.items)
        return result

    # ---- structural: root and .git ------------------------------------------------------
    root_s = os.fspath(root) if isinstance(root, (str, os.PathLike)) else None
    ok = (root_s is not None and os.path.isabs(root_s) and "\0" not in root_s
          and not os.path.islink(root_s) and os.path.isdir(root_s)
          and os.path.realpath(root_s) == os.path.normpath(root_s))
    c.add("root_real_directory", ok, root_s if ok else
          f"root {root_s!r} is not an absolute real directory (symlink/relative/non-canonical)")
    if not ok:
        return finish()
    if not (isinstance(expected_commit, str) and _HEX40.match(expected_commit)
            and isinstance(expected_tree, str) and _HEX40.match(expected_tree)):
        c.add("expected_ids_wellformed", False, "expected commit/tree must be 40 lowercase hex")
        return finish()
    gd = os.path.join(root_s, ".git")
    is_dir = os.path.isdir(gd) and not os.path.islink(gd)
    c.add("git_dir_is_directory", is_dir, ".git" if is_dir else
          ".git is not a real directory (gitfile/symlink/worktree indirection refused)")
    if not is_dir:
        return finish()
    alt = [p for p in ("objects/info/alternates", "objects/info/http-alternates")
           if os.path.lexists(os.path.join(gd, p))]
    c.add("no_alternates", not alt, ", ".join(alt) or "none")
    cfg = gitsafe.scan_git_config(root_s)
    c.add("git_config_safe", not cfg, "; ".join(cfg) or "ok")
    if alt or cfg:
        return finish()

    def git(args):
        return gitsafe.run_git(root_s, args, events, timeout=timeout)

    try:
        top = git(["rev-parse", "--show-toplevel"]).decode("utf-8", "replace").strip()
        c.add("toplevel_is_root", os.path.realpath(top) == root_s, top)

        head = git(["rev-parse", "--verify", "HEAD"]).decode().strip()
        observed["commit"] = head if _HEX40.match(head) else None
        c.add("head_full_hex", bool(_HEX40.match(head)), head)
        c.add("head_matches_expected", head == expected_commit, f"observed {head}")

        tree = git(["rev-parse", "--verify", "HEAD^{tree}"]).decode().strip()
        observed["tree"] = tree if _HEX40.match(tree) else None
        c.add("tree_matches_expected", tree == expected_tree, f"observed {tree}")

        st = git(["status", "--porcelain", "--untracked-files=all", "--ignored", "-z",
                  "--ignore-submodules=none"])
        c.add("worktree_clean", st == b"", st[:400].decode("utf-8", "replace").replace("\0", " | ")
              or "clean (no dirty, untracked or ignored entries)")

        flags = git(["ls-files", "-v", "-z"])
        badflags = []
        for rec in flags.split(b"\0"):
            if rec and rec[:1] != b"H":
                badflags.append(rec.decode("utf-8", "replace"))
        c.add("index_flags_plain", not badflags,
              "; ".join(badflags[:10]) or "no assume-unchanged/skip-worktree/other flags")

        stage = _parse_ls_files_stage(git(["ls-files", "-s", "-z"]))
        gitlinks = [e[3] for e in stage if e[0] == "160000"]
        c.add("no_gitlinks", not gitlinks, "; ".join(gitlinks[:10]) or "none")
        unmerged = [e[3] for e in stage if e[2] != "0"]
        c.add("no_unmerged_entries", not unmerged, "; ".join(unmerged[:10]) or "none")
        symlinks = sorted(e[3] for e in stage if e[0] == "120000")
        if symlinks:
            notes.append("adverse: symlinks in tree: " + ", ".join(symlinks[:50]))
        index_blob = {e[3]: e[1] for e in stage if e[2] == "0"}

        listed = list(files)
        paths_ok = [r for r in listed if _valid_rel(r)]
        c.add("listed_paths_wellformed", len(paths_ok) == len(listed),
              "ok" if len(paths_ok) == len(listed) else
              "malformed: " + ", ".join(repr(r) for r in listed if not _valid_rel(r))[:300])
        c.add("no_listed_symlink_in_index", not (set(paths_ok) & set(symlinks)),
              ", ".join(sorted(set(paths_ok) & set(symlinks))[:10]) or "none")

        tree_blob = {}
        if paths_ok:
            lt = git(["ls-tree", "-r", "-z", "--full-tree", "HEAD", "--"] + paths_ok)
            for rec in lt.split(b"\0"):
                if not rec:
                    continue
                meta, _, path = rec.partition(b"\t")
                mode, typ, sha = meta.decode().split(" ")[:3]
                tree_blob[path.decode("utf-8", "surrogateescape")] = (mode, typ, sha)
    except (GitError, ValueError, UnicodeDecodeError) as e:
        c.add("git_commands", False, f"{e.__class__.__name__}: {e}")
        return finish()

    # ---- per-file: worktree bytes vs HEAD blob vs index blob --------------------------------
    for rel in listed:
        if not _valid_rel(rel):
            observed["files"][rel] = {"missing": True, "reason": "malformed path"}
            continue
        events.add("file_read", path=rel, root=root_s)
        data, problem = _read_regular_file(root_s, rel)
        tb = tree_blob.get(rel)
        if data is None:
            observed["files"][rel] = {"missing": True, "reason": problem,
                                      "tree_blob": tb[2] if tb else None}
            c.add(f"file:{rel}", False, f"worktree file {problem}")
            continue
        blob = _blob_id(data)
        observed["files"][rel] = {"sha256": hashlib.sha256(data).hexdigest(), "git_blob": blob,
                                  "tree_blob": tb[2] if tb else None, "size": len(data)}
        problems = []
        if tb is None:
            problems.append("not in HEAD tree")
        else:
            if tb[1] != "blob" or tb[0] not in ("100644", "100755"):
                problems.append(f"HEAD entry is {tb[0]} {tb[1]}, not a regular blob")
            if blob != tb[2]:
                problems.append(f"worktree blob {blob} != HEAD blob {tb[2]}")
        if index_blob.get(rel) != (tb[2] if tb else None):
            problems.append("index blob differs from HEAD blob")
        c.add(f"file:{rel}", not problems, "; ".join(problems) or "worktree == index == HEAD")
    return finish()


def oracle_identity_keys(oracle, prefixes=None):
    """Read ONLY the key sets (never the expected values) of QA-S1.1 and QA-S2.1.

    Returns {"components": [names], "paths": {component: [relpath, ...]}}."""
    prefixes = prefixes or DEFAULT_PREFIXES
    rev = {v: k for k, v in prefixes.items()}
    cases = oracle.get("cases", oracle) if isinstance(oracle, dict) else oracle
    found = {}

    def walk(o):
        if isinstance(o, dict):
            if o.get("id") in ("QA-S1", "QA-S2"):
                found[o["id"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(cases)
    if set(found) != {"QA-S1", "QA-S2"}:
        raise ValueError("oracle lacks QA-S1/QA-S2")
    s1 = next(o for o in found["QA-S1"]["observations"] if o["id"] == "QA-S1.1")
    s2 = next(o for o in found["QA-S2"]["observations"] if o["id"] == "QA-S2.1")
    comps = sorted(list(s1["expected"].keys()))  # keys only
    paths = {comp: [] for comp in comps}
    for k in list(s2["expected"].keys()):  # keys only
        pre, _, rel = k.partition(":")
        if pre not in rev or rev[pre] not in paths or not rel:
            raise ValueError(f"unexpected file_identity key {k!r}")
        paths[rev[pre]].append(rel)
    return {"components": comps, "paths": paths}


def build_identity_records(results, key_prefixes=None):
    """results: {component: verify_checkout result}. Only OBSERVED values are copied.

    A missing/unreadable file is omitted from the sha256/git_blob maps (so the evaluator's exact
    comparison fails) and listed in `flags`; an unobserved commit/tree is likewise omitted."""
    prefixes = key_prefixes or DEFAULT_PREFIXES
    commits, trees, sha, blob, flags = {}, {}, {}, {}, []
    for comp, res in results.items():
        if comp not in prefixes:
            raise ValueError(f"no key prefix for component {comp!r}")
        obs = res.get("observed", {})
        if obs.get("commit"):
            commits[comp] = obs["commit"]
        else:
            flags.append(f"{comp}: commit not observed")
        if obs.get("tree"):
            trees[comp] = obs["tree"]
        else:
            flags.append(f"{comp}: tree not observed")
        for rel, rec in obs.get("files", {}).items():
            key = f"{prefixes[comp]}:{rel}"
            if not isinstance(rec, dict) or rec.get("missing") or "sha256" not in rec:
                flags.append(f"{key}: missing/unreadable ({rec.get('reason') if isinstance(rec, dict) else '?'})")
                continue
            sha[key] = rec["sha256"]
            blob[key] = rec["git_blob"]
        if not res.get("ok"):
            flags.append(f"{comp}: checkout verification refused ({len(res.get('refusals', []))} refusals)")
    return {"source_identity": {"commits": commits, "trees": trees},
            "file_identity": {"sha256": sha, "git_blob": blob},
            "flags": flags}
