"""Declared known limits as the controller reads them.

SPDX-License-Identifier: Apache-2.0

The declared set is derived, never typed in: it is the JSON twin of the pre-registration
(process/release-gate/preregistration.json) read as

    declared_known_limits (fix2_probes, authority_ra, wiki_derived)
    + every add_known_limit amendment
    - every withdraw_known_limit amendment          (amendments applied in the order of the twin)

Each declaration is normalised to one entry. An entry is one named test (DR-8) or one named
requirement; there is no wildcard and no pattern. A test entry is matched against a JUnit case by
two exact comparisons and nothing else:

    junit classname == dotted(repo-relative path without ".py")      ("tests/test_a.py" -> "tests.test_a")
    junit name      == the test name of the declaration, parameter included

Only entries with a controller component can be matched. The component of an entry is fixed here or in
the twin, never inferred from a result:

    cogno-us/<repo>:<path>::<name>   the component whose pinned repository is cogno-us/<repo> (EXTERNAL_REPO_COMPONENT)
    authority_ra declarations        the selector_component recorded in the twin (probes-control-plane)
    fix2 probes, wiki-derived        none: the controller does not collect these suites
    process/adversarial/tests ids    none: the controller does not collect this suite (inventory row X-19)

The entries are hashed (declared_set_sha256) and the hash is written into the controller report.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TWIN_REL = "process/release-gate/preregistration.json"
SCHEMA = "cognous.v1-validation-declared-set/1"

# Repository -> controller component key (the freeze-manifest keys; a unit test compares this table with the manifest).
EXTERNAL_REPO_COMPONENT = {
    "cogno-us/cognous-control-plane": "control_plane",
    "cogno-us/cognous-execution-runtime": "moltbot_safe",
    "cogno-us/cognous-replay-bundle": "replay_bundle",
    "cogno-us/cognous-governance-evidence-pack": "governance_evidence_pack",
    "cogno-us/open-decision-evidence-standard": "odes",
    "cogno-us/cognous-governed-exchange": "gax_imx_transport",
    "cogno-us/cognous-action-manifest": "action_manifest",
    "cogno-us/cognous-evidence-attestation": "bitrep",
    "cogno-us/cognous-evidence-registry": "the_index",
    "cogno-us/cognous-institutional-governance": "constitutional_authority",
}

_NAME = r"[A-Za-z_]\w*(?:\[[^\n]+\])?"
_EXTERNAL_ID = re.compile(r"^(cogno-us/[a-z0-9][a-z0-9-]*):([\w./-]+\.py)::(" + _NAME + r")$")
_LOCAL_ID = re.compile(r"^((?:suites|process/adversarial/tests)/[\w./-]+\.py)::(" + _NAME + r")$")
_BARE_ID = re.compile(r"^([\w.-]+\.py)::(" + _NAME + r")$")
_REQUIREMENT_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")


class DeclaredSetError(Exception):
    """The twin cannot be read as a declared set, or a supplied declared set differs from it."""


def dotted(path: str) -> str:
    """Repo-relative test file path -> the classname pytest writes into the JUnit report."""
    if not path.endswith(".py") or path.startswith("/") or ".." in path.split("/"):
        raise DeclaredSetError(f"not a repo-relative python test path: {path!r}")
    return path[:-3].replace("/", ".")


def _test_entry(id_, source, repository, path, name, component):
    return {"id": id_, "kind": "test", "source": source, "repository": repository, "path": path,
            "classname": dotted(path), "name": name, "component": component}


def _from_amendment_id(id_, source):
    m = _EXTERNAL_ID.match(id_)
    if m:
        repo, path, name = m.groups()
        if repo not in EXTERNAL_REPO_COMPONENT:
            raise DeclaredSetError(f"declaration {id_!r} names repository {repo!r}, which has no controller component in EXTERNAL_REPO_COMPONENT")
        return _test_entry(id_, source, repo, path, name, EXTERNAL_REPO_COMPONENT[repo])
    m = _LOCAL_ID.match(id_)
    if m:
        path, name = m.groups()
        return _test_entry(id_, source, None, path, name, None)
    if _REQUIREMENT_ID.match(id_):
        return {"id": id_, "kind": "requirement", "source": source, "repository": None, "path": None, "classname": None, "name": None, "component": None}
    raise DeclaredSetError(f"declaration {id_!r} is neither <repo>:<path>::<test>, suites/<path>::<test> nor a requirement id")


def normalise(twin: dict) -> list:
    """Declared entries in force, sorted by id. Raises DeclaredSetError on anything it cannot place exactly."""
    entries = {}

    def put(e):
        if e["id"] in entries:
            raise DeclaredSetError(f"duplicate declaration {e['id']!r}")
        entries[e["id"]] = e

    dk = twin.get("declared_known_limits")
    if not isinstance(dk, dict):
        raise DeclaredSetError("twin has no declared_known_limits object")
    for r in dk["fix2_probes"]["declared"]:
        m = _BARE_ID.match(r["id"])
        if not m or m.group(1) != Path(r["path"]).name:
            raise DeclaredSetError(f"fix2 declaration {r['id']!r} does not agree with its path {r['path']!r}")
        put(_test_entry(r["id"], "declared_known_limits.fix2_probes", None, r["path"], m.group(2), None))
    ra = dk["authority_ra"]
    for r in ra["declared"]:
        m = _BARE_ID.match(r["id"])
        if not m or m.group(1) != Path(r["path"]).name:
            raise DeclaredSetError(f"authority_ra declaration {r['id']!r} does not agree with its path {r['path']!r}")
        put(_test_entry(r["id"], "declared_known_limits.authority_ra", None, r["path"], m.group(2), ra["selector_component"]))
    for r in dk["wiki_derived"]["declared"]:
        m = _BARE_ID.match(r["id"])
        if not m or m.group(1) != Path(r["path"]).name:
            raise DeclaredSetError(f"wiki declaration {r['id']!r} does not agree with its path {r['path']!r}")
        put(_test_entry(r["id"], "declared_known_limits.wiki_derived", None, r["path"], m.group(2), None))
    for n, a in enumerate(twin.get("amendments", []), start=1):
        act = a.get("action")
        if act == "add_known_limit":
            put(_from_amendment_id(a["id"], f"amendment {n} ({a['timestamp']})"))
        elif act == "withdraw_known_limit":
            if a["id"] not in entries:
                raise DeclaredSetError(f"amendment {n} withdraws {a['id']!r}, which is not declared at that point")
            del entries[a["id"]]
    return sorted(entries.values(), key=lambda e: e["id"])


_HASHED = ("id", "kind", "repository", "path", "classname", "name", "component")


def canonical(entries) -> bytes:
    rows = [{k: e[k] for k in _HASHED} for e in sorted(entries, key=lambda e: e["id"])]
    return json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def declared_set_sha256(entries) -> str:
    return hashlib.sha256(canonical(entries)).hexdigest()


def committed_twin_bytes(twin_path: Path, root: Path = ROOT) -> tuple[bytes, str]:
    """(bytes, source). For the repository twin: the blob at git HEAD; the working tree must equal it.

    A twin that is not inside a git work tree (or git is unavailable) is read as given and the source says so.
    """
    twin_path = Path(twin_path).resolve()
    data = twin_path.read_bytes()
    try:
        rel = twin_path.relative_to(root).as_posix()
        proc = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{rel}"], capture_output=True, timeout=60)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return data, "file as given (not inside the repository or git unavailable)"
    if proc.returncode:
        return data, "file as given (no committed copy at HEAD)"
    if proc.stdout != data:
        raise DeclaredSetError(f"{rel} in the working tree differs from the committed copy at HEAD; the declared set is read from the committed twin only")
    return data, "committed copy at git HEAD (working tree identical)"


def load(twin_path: Path = None, require_committed: bool = False, declared_set_file: Path = None) -> dict:
    """The declared-set record the controller uses and writes into its report.

    require_committed: the twin must equal its copy at git HEAD (the aggregate sets this).
    declared_set_file: a previously written record; its entries must equal the entries derived from the twin, else refuse.
    """
    twin_path = Path(twin_path or ROOT / TWIN_REL)
    if require_committed:
        data, src = committed_twin_bytes(twin_path)
    else:
        data, src = twin_path.read_bytes(), "file as given (committed copy not required)"
    twin = json.loads(data.decode("utf-8"))
    entries = normalise(twin)
    digest = declared_set_sha256(entries)
    if declared_set_file is not None:
        supplied = json.loads(Path(declared_set_file).read_text(encoding="utf-8"))
        theirs = supplied.get("entries")
        if not isinstance(theirs, list):
            raise DeclaredSetError(f"{declared_set_file}: no entries list")
        try:
            their_digest = declared_set_sha256(theirs)
        except (KeyError, TypeError) as exc:
            raise DeclaredSetError(f"{declared_set_file}: malformed entries ({exc})") from exc
        if their_digest != digest or supplied.get("declared_set_sha256") != digest:
            raise DeclaredSetError(f"the supplied declared set ({supplied.get('declared_set_sha256')}) differs from the set derived from the committed twin ({digest})")
    ams = twin.get("amendments", [])
    return {"schema": SCHEMA,
            "twin": {"path": TWIN_REL if twin_path == (ROOT / TWIN_REL).resolve() else str(twin_path), "sha256": hashlib.sha256(data).hexdigest(), "source": src,
                     "amendments_in_force": len(ams), "latest_amendment_timestamp": ams[-1]["timestamp"] if ams else None},
            "match_rule": "junit classname == dotted(path without .py) and junit name == test name, both exact; no pattern",
            "declared_set_sha256": digest,
            "counts": {"entries": len(entries), "tests": sum(1 for e in entries if e["kind"] == "test"),
                       "requirements": sum(1 for e in entries if e["kind"] == "requirement"),
                       "matchable_by_controller": sum(1 for e in entries if e["component"])},
            "entries": entries}


def by_component(record: dict) -> dict:
    """component -> {(classname, name): entry} for the matchable test entries."""
    out = {}
    for e in record["entries"]:
        if e["kind"] == "test" and e["component"]:
            out.setdefault(e["component"], {})[(e["classname"], e["name"])] = e
    return out
