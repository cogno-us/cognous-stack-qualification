"""Contract-version compatibility matrix: the compatibility gate for the boundaries that carry a declared contract.

SPDX-License-Identifier: Apache-2.0

Alpha decoupling, phase P4 of cogno-us/cognous-control-plane#38. Until now a component was admitted into a scenario run
only when its checkout equalled the pinned sha (``require_pristine``). For a boundary that is governed by an ODES contract
(today: execution-attempt-lifecycle between the runtime, the Control Plane and Replay) the gate is now:

    each component declares "conforms to contract <name> <version> at level <S|L|P>" in its vendored CONTRACT.json
    (written by ODES ``contracts/tools/vendor_contract.py``), and this matrix checks the declaration per boundary.

The sha pins in the freeze manifest, the refreeze log and the profile stay as the recorded *tested revision*: a run
records the revision that actually ran and whether it equals the tested revision. They are no longer the compatibility
gate for a matrix-governed component. Components without a declared contract on any boundary (evidence pack, ODES,
exchange, manifest in the current matrix) keep the sha pin as their gate; the matrix says so explicitly.

A declared version string is not enough while a contract is a draft (the same ``0.1.0-draft`` covered different content
between ODES d1e17fa1 and a9db024c), so a declaration also has to carry the exact reference file digests of that version,
and the vendored copy must be free of drift. Nothing here establishes that the component *behaves* as declared; that is
what the producer and consumer conformance suites in the component repositories show. This module checks the paper trail.

Stdlib only; importable without side effects.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_RELPATH = "process/v1-validation/v1-2026-10-16-a/contract-matrix.json"
LEVEL_ORDER = {"S": 1, "L": 2, "P": 3}
CONFORMS, NONCONFORMING, UNDECLARED = "conforms", "nonconforming", "undeclared"


class MatrixError(ValueError):
    """The matrix file itself is malformed."""


def load_matrix(path=None):
    p = Path(path) if path else ROOT / MATRIX_RELPATH
    matrix = json.loads(p.read_text(encoding="utf-8"))
    if matrix.get("schema") != "cognous.contract-matrix/1":
        raise MatrixError("unsupported contract matrix schema")
    return matrix


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def drift_findings(root):
    """Modified, missing or unlisted files of a vendored contract copy (SHA-256 against its CONTRACT.json)."""
    root = Path(root)
    listed = json.loads((root / "CONTRACT.json").read_text(encoding="utf-8")).get("files", {})
    findings = []
    for rel, digest in sorted(listed.items()):
        path = root / rel
        if not path.is_file():
            findings.append(f"missing: {rel}")
        elif _sha256(path) != digest:
            findings.append(f"modified: {rel}")
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(root).as_posix()
        if rel != "CONTRACT.json" and rel not in listed:
            findings.append(f"unlisted: {rel}")
    return findings


def read_declaration(component_dir, contract, matrix):
    """The component's declaration for ``contract``, or None when it carries none. Raises nothing for a malformed file."""
    rel = matrix["declaration_path"].format(contract=contract)
    path = Path(component_dir) / rel
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("declaration is not an object")
        data["_dir"] = str(path.parent)
        return data
    except ValueError as exc:
        return {"_malformed": str(exc), "_dir": str(path.parent)}


def _version_key(version):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?", version or "")
    return (int(m[1]), int(m[2]), int(m[3]), m[4]) if m else None


def versions_compatible(producer_version, consumer_version):
    """Draft versions (``-`` suffix) must be identical. Released versions: same major, consumer minor >= producer minor."""
    p, c = _version_key(producer_version), _version_key(consumer_version)
    if p is None or c is None:
        return False
    if p[3] or c[3]:
        return producer_version == consumer_version
    return p[0] == c[0] and c[1] >= p[1]


def check_declaration(decl, contract, role, min_level, matrix):
    """Reasons a declaration does not satisfy (contract, role, min_level); empty list means it does."""
    if decl is None:
        return ["no declaration"]
    if "_malformed" in decl:
        return [f"declaration unreadable: {decl['_malformed']}"]
    reasons = []
    if decl.get("contract") != contract:
        reasons.append(f"declares contract {decl.get('contract')!r}, boundary needs {contract!r}")
    version = decl.get("contract_version")
    versions = matrix["contracts"].get(contract, {}).get("versions", {})
    if version not in versions:
        reasons.append(f"declares version {version!r}, matrix knows {sorted(versions)}")
    if decl.get("role") != role:
        reasons.append(f"declares role {decl.get('role')!r}, boundary needs {role!r}")
    level = decl.get("conformance_level")
    if LEVEL_ORDER.get(level, 0) < LEVEL_ORDER[min_level]:
        reasons.append(f"declares conformance level {level!r}, boundary needs at least {min_level!r}")
    ref = versions.get(version)
    if ref:
        files = decl.get("files", {})
        for name, digest in sorted(ref["files"].items()):
            if files.get(name) != digest:
                reasons.append(f"{name} differs from the reference {version} content (declared odes_commit "
                               f"{str(decl.get('odes_commit'))[:8]}, reference {ref['reference_odes_commit'][:8]})")
    try:
        reasons += [f"vendored copy drift: {f}" for f in drift_findings(decl["_dir"])]
    except (OSError, ValueError) as exc:
        reasons.append(f"vendored copy unreadable: {exc}")
    return reasons


def evaluate(components, matrix=None):
    """Evaluate every boundary. ``components`` maps a profile component name to its checkout directory.

    Returns a list of rows ``{boundary, contract, status, reasons, producer, consumer}`` in matrix order.
    A boundary whose component is not in ``components`` is reported ``undeclared``.
    """
    matrix = matrix or load_matrix()
    rows = []
    for b in matrix["boundaries"]:
        contract = b["contract"]
        sides, reasons, declared = {}, [], {}
        for role, min_key in (("producer", "producer_min_level"), ("consumer", "consumer_min_level")):
            name = b[role]
            directory = components.get(name)
            decl = read_declaration(directory, contract, matrix) if directory is not None else None
            problems = check_declaration(decl, contract, role, b[min_key], matrix)
            declared[role] = decl
            sides[role] = {"component": name, "contract_version": (decl or {}).get("contract_version"),
                           "conformance_level": (decl or {}).get("conformance_level"),
                           "odes_commit": (decl or {}).get("odes_commit"), "problems": problems}
            reasons += [f"{role} {name}: {p}" for p in problems]
        undeclared = any(declared[r] is None for r in declared)
        if not reasons and not versions_compatible(sides["producer"]["contract_version"], sides["consumer"]["contract_version"]):
            reasons.append("producer and consumer versions are not compatible")
        status = CONFORMS if not reasons else UNDECLARED if undeclared else NONCONFORMING
        rows.append({"boundary": b["id"], "contract": contract, "status": status, "reasons": reasons, **sides})
    return rows


def governed_components(matrix=None):
    """Profile component names whose compatibility gate is the matrix (they sit on at least one boundary)."""
    matrix = matrix or load_matrix()
    return sorted({b[r] for b in matrix["boundaries"] for r in ("producer", "consumer")})


def sha_pinned_components(matrix=None):
    matrix = matrix or load_matrix()
    return sorted(matrix.get("sha_pin_gate", {}).get("components", []))


def gate_record(name, head, tested_revision, matrix=None):
    """How a component was admitted: by the matrix (revision recorded, tested-revision match reported) or by its sha pin."""
    matrix = matrix or load_matrix()
    if name in governed_components(matrix):
        return {"gate": "contract-matrix", "revision": head, "tested_revision": tested_revision,
                "tested_revision_match": head == tested_revision}
    return {"gate": "sha-pin", "revision": head, "tested_revision": tested_revision, "tested_revision_match": head == tested_revision}


def require_matrix(components, matrix=None):
    """Raise ValueError unless every boundary conforms. Returns the rows."""
    rows = evaluate(components, matrix)
    bad = [r for r in rows if r["status"] != CONFORMS]
    if bad:
        raise ValueError("contract matrix: " + "; ".join(f"{r['boundary']} {r['status']} ({'; '.join(r['reasons'])})" for r in bad))
    return rows


def declares(component_dir, contract, matrix=None):
    """The declared (version, level) of a component for ``contract``, or None. Used by version-aware tests."""
    matrix = matrix or load_matrix()
    decl = read_declaration(component_dir, contract, matrix)
    if not decl or "_malformed" in decl:
        return None
    return decl.get("contract_version"), decl.get("conformance_level")


def admit_components(base, profile_components, names, require_pristine, head_of, matrix=None):
    """Admit the component checkouts of a scenario run.

    ``profile_components`` is the qualification profile's ``components`` map (name -> {revision}), ``require_pristine``
    is tools/pristine_checkout.require_pristine and ``head_of(path)`` returns a checkout's HEAD. For each name:

    * every checkout must be pristine (a modified or untracked file is always refused);
    * a component whose boundaries all conform is admitted by the matrix: its HEAD is recorded with the tested revision
      (the profile pin) and whether they are equal;
    * a component with a declared-but-nonconforming boundary is refused (ValueError naming the reasons);
    * a component with no declaration (an older tuple that predates the contract) or a component outside the matrix is
      admitted only at its pinned revision (the old gate).

    Returns ``(gates, rows)``: ``gates`` maps name -> gate record, ``rows`` is the matrix evaluation.
    """
    matrix = matrix or load_matrix()
    paths = {n: Path(base) / n for n in names}
    rows = evaluate({n: p for n, p in paths.items() if n in governed_components(matrix)}, matrix)
    gates = {}
    for name in names:
        tested = profile_components[name]["revision"]
        mine = [r for r in rows if name in (r["producer"]["component"], r["consumer"]["component"])]
        if name in governed_components(matrix) and mine:
            bad = [r for r in mine if r["status"] == NONCONFORMING]
            if bad:
                raise ValueError(f"{name}: contract matrix refuses the checkout: " + "; ".join(
                    f"{r['boundary']}: {'; '.join(r['reasons'])}" for r in bad))
            if all(r["status"] == CONFORMS for r in mine):
                head = head_of(paths[name])
                require_pristine(paths[name], head, name)  # clean tree; the revision is recorded, not compared
                gates[name] = gate_record(name, head, tested, matrix)
                continue
        require_pristine(paths[name], tested, name)  # sha-pin gate (no declared contract on this component's boundaries)
        gates[name] = {"gate": "sha-pin", "revision": tested, "tested_revision": tested, "tested_revision_match": True}
    return gates, rows
