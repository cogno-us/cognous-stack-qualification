"""Source-identity checks of the R2 joined chain (PRIVATE PREVIEW QUALIFICATION TUPLE; preview-only, NOT canonical).

Pure functions shared by test_00_sources.py (positive), test_01_source_identity.py (adversarial negatives against temp copies) and the harness / run_chain.py
(`source_identity_report()` is dumped to source-identity.json). Source identity is never inferred from version strings, branch names or `main`:
only `git rev-parse HEAD`, `HEAD^{tree}`, a clean work tree (incl. untracked and ignored files, assume-unchanged / skip-worktree flags and a content hash of every
tracked file against the HEAD tree), the absence of interpreter-startup / shadow-module files at the roots and the `__file__` of every loaded module.

Every check function returns a list of problem strings (empty list == check passed); it never raises for a detected defect.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAIN = HERE.parent
SOURCES_JSON = CHAIN / "sources.json"
LABEL = "PRIVATE PREVIEW QUALIFICATION TUPLE"
EXPECTED_SHAS = {
    "control_plane": "46372de34ef1ce882cff1aa9664c38a98afb2a3b",
    "registry": "7de0ec9f8471c7a2ff630eb4035fa24d60b5e2eb",
    "replay": "6651abef2dfc0960b09907ed268db45e809ee814",
}
SHADOW_FILE_NAMES = ("sitecustomize.py", "usercustomize.py", "sitecustomize", "usercustomize")
# modules the chain imports (the same imports harness.py makes); top-level package -> pinned source that must own it
CHAIN_MODULES = {
    "agent_control_plane": "control_plane",
    "agent_control_plane.bounded": "control_plane",
    "agent_control_plane.registry_f4_age_governance": "control_plane",
    "registry_successor": "registry",
    "registry_successor.v2_verified_selection": "registry",
    "registry_adapters.ed25519_verifier": "registry",
    "registry_consumer.evidence_verifier": "registry",
    "agent_replay_bundle": "replay",
    "agent_replay_bundle.importers": "replay",
    "agent_replay_bundle.registry_evidence": "replay",
    "agent_replay_bundle.effective_configuration": "replay",
}
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_REPLACE_REF_BASE", "GIT_NAMESPACE")


def load_sources(path: Path | None = None) -> dict:
    return json.loads((path or SOURCES_JSON).read_text())


def src_dir() -> Path:
    """The directory fetch_sources.sh populated: env R2_SRC_DIR, else SRC_DIR."""
    v = os.environ.get("R2_SRC_DIR") or os.environ.get("SRC_DIR")
    if not v:
        raise RuntimeError("R2_SRC_DIR (or SRC_DIR) is not set; run fetch_sources.sh <dir> first")
    return Path(v).resolve()


def git(path: Path, *args: str, check: bool = True) -> str:
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    r = subprocess.run(["git", "--no-replace-objects", "-C", str(path), *args], capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError("git %s failed in %s: %s" % (" ".join(args), path, r.stderr.strip()))
    return r.stdout.rstrip("\n")


class SourceIdentityRefusal(Exception):
    """Raised by require() when a source-identity check reports problems; `.code` is the typed refusal code (usable with harness.expect_refusal)."""

    def __init__(self, code: str, problems: list[str]):
        super().__init__("%s: %s" % (code, "; ".join(problems)[:600]))
        self.code, self.problems = code, problems


def require(code: str, problems: list[str]) -> None:
    if problems:
        raise SourceIdentityRefusal(code, problems)


# ------------------------------------------------------------------ manifest checks
def check_manifest(manifest: dict) -> list[str]:
    """sources.json carries the label and exactly the three pinned SHAs (and nothing claims canonical status)."""
    p: list[str] = []
    if manifest.get("label") != LABEL or LABEL not in manifest.get("statement", ""):
        p.append("manifest does not carry the label %r" % LABEL)
    if "NOT canonical" not in manifest.get("statement", ""):
        p.append("manifest does not state it is NOT canonical")
    srcs = manifest.get("sources", {})
    if set(srcs) != set(EXPECTED_SHAS):
        p.append("source names %s != %s" % (sorted(srcs), sorted(EXPECTED_SHAS)))
    for name, sha in EXPECTED_SHAS.items():
        got = srcs.get(name, {}).get("sha")
        if got != sha:
            p.append("%s sha %r != expected %s" % (name, got, sha))
        if len(srcs.get(name, {}).get("tree", "")) != 40:
            p.append("%s has no 40-hex tree" % name)
    for k in ("repo", "dir", "role", "interface"):
        for name, s in srcs.items():
            if not s.get(k):
                p.append("%s lacks %s" % (name, k))
    return p


# ------------------------------------------------------------------ work-tree checks
def check_pin(path: Path, spec: dict) -> dict:
    """HEAD and HEAD^{tree} of the checkout at `path` against spec['sha'] / spec['tree']. Returns observed values and problems."""
    out = {"observed_sha": None, "observed_tree": None, "problems": []}
    try:
        out["observed_sha"] = git(path, "rev-parse", "HEAD")
        out["observed_tree"] = git(path, "rev-parse", "HEAD^{tree}")
    except Exception as e:  # not a git checkout at all
        out["problems"].append("cannot read git identity: %s" % e)
        return out
    if out["observed_sha"] != spec["sha"]:
        out["problems"].append("HEAD %s != pinned %s" % (out["observed_sha"], spec["sha"]))
    if out["observed_tree"] != spec["tree"]:
        out["problems"].append("tree %s != pinned %s" % (out["observed_tree"], spec["tree"]))
    return out


def is_benign_pyc(path: Path, rel: str) -> bool:
    """CPython's own import-time bytecode cache (<dir>/__pycache__/<mod>.cpython-NNN.pyc, timestamp-validated: header flags == 0, so it is checked against the
    source mtime+size and cannot be an unchecked-hash override). Importing the pinned sources necessarily creates these; set PYTHONDONTWRITEBYTECODE=1 (or
    strict_bytecode=True) to forbid them entirely. Anything else under __pycache__ is NOT benign."""
    parts = Path(rel).parts
    if len(parts) < 2 or parts[-2] != "__pycache__" or not parts[-1].endswith(".pyc") or ".cpython-" not in parts[-1]:
        return False
    try:
        with open(path / rel, "rb") as fh:
            head = fh.read(16)
        return len(head) >= 16 and head[4:8] == b"\0\0\0\0"
    except OSError:
        return False


def check_clean(path: Path, strict_bytecode: bool = False) -> list[str]:
    """No modified / untracked / ignored file, no assume-unchanged / skip-worktree flag, tracked content equals the HEAD tree, no startup/shadow files at the roots.
    The only tolerated extras are CPython timestamp-validated __pycache__ .pyc files (see is_benign_pyc) unless strict_bytecode."""
    p: list[str] = []
    tolerated = (lambda rel: False) if strict_bytecode else (lambda rel: is_benign_pyc(path, rel))
    try:
        st = git(path, "status", "--porcelain", "--untracked-files=all", "--ignored")
    except Exception as e:
        return ["git status failed: %s" % e]
    st = "\n".join(l for l in st.splitlines() if not (l.startswith(("!! ", "?? ")) and tolerated(l[3:].strip('"')))) 
    if st:
        p.append("work tree not clean: " + "; ".join(st.splitlines()[:10]))
    # assume-unchanged ('h'..) / skip-worktree ('S'/'s') / other non-'H' tags hide edits from `git status`
    for line in git(path, "ls-files", "-v").splitlines():
        tag, name = line[0], line[2:]
        if tag != "H":
            p.append("index flag %r on %s (assume-unchanged/skip-worktree/other hides edits)" % (tag, name))
    # flag-independent: hash every tracked regular file and compare to the HEAD tree blob
    tree = {}
    for line in git(path, "ls-tree", "-r", "-z", "--full-tree", "HEAD").split("\0"):
        if not line:
            continue
        meta, name = line.split("\t", 1)
        mode, typ, oid = meta.split()
        tree[name] = (mode, typ, oid)
    regular = [n for n, (m, t, _) in tree.items() if m in ("100644", "100755")]
    missing = [n for n in regular if not (path / n).is_file()]
    for n in missing[:10]:
        p.append("tracked file missing from work tree: %s" % n)
    present = [n for n in regular if n not in set(missing)]
    if present:
        env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
        r = subprocess.run(["git", "--no-replace-objects", "-C", str(path), "hash-object", "--no-filters", "--stdin-paths"],
                           input="\n".join(present) + "\n", capture_output=True, text=True, env=env)
        hashes = r.stdout.split()
        if r.returncode != 0 or len(hashes) != len(present):
            p.append("hash-object failed: %s" % r.stderr.strip())
        else:
            for n, h in zip(present, hashes):
                if h != tree[n][2]:
                    p.append("content of %s differs from HEAD tree blob" % n)
    # nothing may exist in the work tree that the HEAD tree lacks (belt and braces for ignored/untracked files)
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel = os.path.relpath(root, path)
        for f in files:
            n = f if rel == "." else os.path.join(rel, f)
            if n not in tree and not tolerated(n):
                p.append("file not in HEAD tree: %s" % n)
        if rel == ".":
            for f in files:
                if f in SHADOW_FILE_NAMES or f.endswith(".pth"):
                    p.append("interpreter-startup/shadow file at the source root: %s" % f)
    return p


def pinned_sys_path_entries(sources_root: Path) -> list[Path]:
    """Ordered sys.path front for the chain; mirrors the rw01 harness bootstrap (CP root + CP src, Replay src, Registry root + vendored engine + Registry tests)."""
    s = lambda n: sources_root / load_sources()["sources"][n]["dir"]
    return [s("control_plane"), s("control_plane") / "src", s("replay") / "src", s("registry"),
            s("registry") / "baseline" / "execution-runtime", s("registry") / "tests"]


def pinned_dirs(sources_root: Path) -> dict[str, Path]:
    return {n: (sources_root / sp["dir"]).resolve() for n, sp in load_sources()["sources"].items()}


# ------------------------------------------------------------------ module / sys.path checks
def _owned_top_level(entries: list[Path]) -> dict[str, Path]:
    """top-level module/package name -> the FIRST pinned sys.path entry that provides it."""
    owned: dict[str, Path] = {}
    for e in entries:
        if not e.is_dir():
            continue
        for child in sorted(e.iterdir()):
            if child.name.startswith((".", "__")):
                continue
            if child.is_dir() and (child / "__init__.py").exists():
                owned.setdefault(child.name, e)
            elif child.is_file() and child.suffix == ".py":
                owned.setdefault(child.stem, e)
    return owned


def _under(f: str | Path, root: Path) -> bool:
    try:
        Path(os.path.realpath(f)).relative_to(os.path.realpath(root))
        return True
    except ValueError:
        return False


def check_sys_path_order(entries: list[Path], path: list[str] | None = None) -> list[str]:
    """Every pinned entry is on sys.path, in the declared relative order, and no NON-pinned entry that precedes the last pinned one provides a module or package
    name that a pinned entry provides (so nothing can shadow a pinned source by path precedence). Other entries (e.g. the battery dir) may precede."""
    path = sys.path if path is None else path
    real = [os.path.realpath(x) if x else os.path.realpath(os.getcwd()) for x in path]
    want = [os.path.realpath(e) for e in entries]
    p: list[str] = []
    idx = []
    for w in want:
        if w not in real:
            p.append("pinned entry %s is not on sys.path" % w)
        else:
            idx.append(real.index(w))
    if p:
        return p
    if idx != sorted(idx):
        p.append("pinned entries are not in the declared order on sys.path: %s" % real)
    owned = _owned_top_level(entries)
    for r in real[:max(idx) + 1]:
        if r in want or not os.path.isdir(r):
            continue
        clash = sorted(set(_owned_top_level([Path(r)])) & set(owned))
        if clash:
            p.append("non-pinned sys.path entry %s precedes the pinned sources and provides %s" % (r, clash))
    return p


def check_module_files(entries: list[Path], modules: dict[str, str] | None = None, pins: dict[str, Path] | None = None,
                       sys_modules: dict | None = None) -> list[str]:
    """Import each chain module, require its __file__ inside the expected pinned source dir, and require EVERY loaded module whose top-level name is provided by a
    pinned entry to resolve into that same entry (a same-named module resolving elsewhere is a shadow override)."""
    import importlib
    modules = CHAIN_MODULES if modules is None else modules
    pins = pins or {}
    sm = sys.modules if sys_modules is None else sys_modules
    p: list[str] = []
    for mod, owner in modules.items():
        try:
            m = importlib.import_module(mod)
        except Exception as e:
            p.append("cannot import %s: %s" % (mod, e))
            continue
        f = getattr(m, "__file__", None)
        if not f:
            p.append("%s has no __file__ (namespace package or built-in)" % mod)
        elif owner in pins and not _under(f, pins[owner]):
            p.append("%s resolves to %s, outside pinned %s (%s)" % (mod, f, owner, pins[owner]))
    owned = _owned_top_level(entries)
    for name, m in list(sm.items()):
        top = name.split(".")[0]
        if top not in owned:
            continue
        f = getattr(m, "__file__", None)
        if f and not _under(f, owned[top]):
            p.append("shadow: loaded module %s at %s is not under pinned entry %s" % (name, f, owned[top]))
        for loc in list(getattr(m, "__path__", []) or []):
            if not _under(loc, owned[top]):
                p.append("shadow: package %s has path %s outside pinned entry %s" % (name, loc, owned[top]))
    return p


def check_component_lock(repo_root: Path | None = None) -> list[str]:
    """No tracked component-lock.json of the qualification repo is modified vs git HEAD, and sources.json does not point at one."""
    p: list[str] = []
    m = load_sources()
    for n, s in m["sources"].items():
        if "component-lock" in json.dumps(s):
            p.append("source %s references component-lock" % n)
    root = repo_root or CHAIN.parent
    try:
        tracked = [x for x in git(root, "ls-files").splitlines() if x.endswith("component-lock.json")]
    except Exception:
        return p  # not a git checkout (e.g. exported tree): nothing to compare
    for x in tracked:
        if git(root, "status", "--porcelain", "--", x):
            p.append("%s modified vs HEAD" % x)
        if git(root, "ls-files", "-v", "--", x).startswith(("h", "S", "s")):
            p.append("%s carries a hiding index flag" % x)
    return p


# ------------------------------------------------------------------ evidence
def qualification_revision(repo_root: Path | None = None) -> dict:
    root = repo_root or CHAIN.parent
    rec = {"github_sha": os.environ.get("GITHUB_SHA"), "head": None, "tree": None, "dirty_under_r2_chain": None, "tuple_label": LABEL}
    try:
        rec["head"] = git(root, "rev-parse", "HEAD")
        rec["tree"] = git(root, "rev-parse", "HEAD^{tree}")
        rec["dirty_under_r2_chain"] = bool(git(root, "status", "--porcelain", "--untracked-files=all", "--", "r2_chain"))
    except Exception as e:
        rec["error"] = str(e)
    return rec


def source_identity_report(sources_root: Path | None = None, entries: list[Path] | None = None, check_modules: bool = True) -> dict:
    """The dict run_chain.py dumps to source-identity.json. `ok` is True only if every source and module check passed."""
    root = Path(sources_root) if sources_root else src_dir()
    manifest = load_sources()
    entries = entries if entries is not None else pinned_sys_path_entries(root)
    pins = pinned_dirs(root)
    report: dict = {"schema": "r2-source-identity-report/1", "label": LABEL, "preview_only": True, "canonical": False, "manifest_schema": manifest["schema"],
                    "qualification": qualification_revision(), "sources": {}, "problems": []}
    report["problems"] += ["manifest: " + x for x in check_manifest(manifest)]
    for name, spec in manifest["sources"].items():
        pin = check_pin(pins[name], spec)
        clean_problems = check_clean(pins[name])
        report["sources"][name] = {
            "repo": spec["repo"], "role": spec["role"], "interface": spec["interface"], "dir": str(pins[name]),
            "expected_sha": spec["sha"], "expected_tree": spec["tree"],
            "observed_sha": pin["observed_sha"], "observed_tree": pin["observed_tree"],
            "clean": not clean_problems, "problems": pin["problems"] + clean_problems, "module_files": {},
        }
    if check_modules:
        mod_problems = check_sys_path_order(entries) + check_module_files(entries, pins=pins)
        for mod, owner in CHAIN_MODULES.items():
            m = sys.modules.get(mod)
            if m is not None and getattr(m, "__file__", None):
                report["sources"][owner]["module_files"][mod] = os.path.realpath(m.__file__)
        report["modules_checked"] = sorted(CHAIN_MODULES)
        report["problems"] += ["modules: " + x for x in mod_problems]
    else:
        report["modules_checked"] = []
    report["problems"] += ["component-lock: " + x for x in check_component_lock()]
    for name, s in report["sources"].items():
        report["problems"] += ["%s: %s" % (name, x) for x in s["problems"]]
    report["ok"] = not report["problems"]
    return report


if __name__ == "__main__":  # python source_identity.py <src_dir>  -> JSON report (static checks only, no module import)
    r = source_identity_report(Path(sys.argv[1]) if len(sys.argv) > 1 else None, check_modules=False)
    print(json.dumps(r, indent=1, sort_keys=True))
    sys.exit(0 if r["ok"] else 1)
