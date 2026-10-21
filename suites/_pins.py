"""The ONE source of the pinned identities used by the V1 validation harness (scenario helpers, probes and tools/).

SPDX-License-Identifier: Apache-2.0

Pins resolve as   freeze-manifest.json  (original, never edited)
             overridden by   refreeze-log.json  entries whose status matches STATUS_APPLIED_RE (APPLIED or APPLIED-IN-WORKFLOW, optional parenthesised note).

Each entry carries component / from_sha / to_sha.  Entries apply in file order; an entry whose from_sha is not the pin in force
at that point (manifest value or the previous entry's to_sha) raises ``RefreezeError``.  Entries whose status does not match it
(for example PROPOSED, AUTHORISED, WITHDRAWN) are ignored.  Re-freeze steps are therefore data edits to the log
(plus the r1 profile named by ``V1_PROFILE``); no literal in the helpers has to change.

Importable without side effects other than reading the two JSON files (lazily).  tools/ adds this directory to sys.path.
Environment overrides (tests, later re-freezes): V1_VALIDATION_ID, V1_PROFILE (profile path relative to the repo root).
"""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("components_subject", "components_lock_remainder", "components_optional")
ORIGINAL_PROFILE = "process/security-runtime-f5b-20261016.json"
R1_PROFILE = "process/security-runtime-f5b-20261016-r1.json"  # the qualification profile of RF-2..RF-6 (profile components re-frozen)
R2_PROFILE = "process/security-runtime-f5b-20261016-r2.json"  # the qualification profile of RF-2..RF-10 (supersedes r1)
# An entry is applied only when its status is exactly "APPLIED" or "APPLIED-IN-WORKFLOW", optionally followed by one parenthesised
# note (all forms used in the retained refreeze log). Anything else (APPLIED-REVERTED, APPLIEDX, ...) is not applied.
STATUS_APPLIED_RE = re.compile(r"APPLIED(?:-IN-WORKFLOW)?(?: \([^\n]*\))?")
# A note that says the entry is NOT in force contradicts the status; such an entry is not applied (E-5).
STATUS_NOTE_CONTRADICTION_RE = re.compile(
    r"revert|withdr[ae]w|rolled[ -]?back|rollback|do[ -]?not[ -]?appl|not[ -]?applied|not[ -]?authori[sz]ed|unauthori[sz]ed|propos|reject|cancel|void|invalid",
    re.I)
SHA_RE = re.compile(r"[0-9a-f]{40}")

# Explicit mapping of a refreeze-log "component" to the freeze-manifest (section, key).  The log uses the manifest key
# (e.g. 'the_index'); the profile / suite names (runtime, replay, evidence_pack, exchange, manifest) are accepted as aliases.
LOG_COMPONENT_TO_MANIFEST = {
    # components_subject (manifest key, then qualification-profile / hub-profile name)
    "control_plane": ("components_subject", "control_plane"),
    "moltbot_safe": ("components_subject", "moltbot_safe"), "runtime": ("components_subject", "moltbot_safe"),
    "replay_bundle": ("components_subject", "replay_bundle"), "replay": ("components_subject", "replay_bundle"),
    "governance_evidence_pack": ("components_subject", "governance_evidence_pack"),
    "evidence_pack": ("components_subject", "governance_evidence_pack"),
    "odes": ("components_subject", "odes"),
    "gax_imx_transport": ("components_subject", "gax_imx_transport"), "exchange": ("components_subject", "gax_imx_transport"),
    "action_manifest": ("components_subject", "action_manifest"), "manifest": ("components_subject", "action_manifest"),
    # components_lock_remainder
    "bitrep": ("components_lock_remainder", "bitrep"),
    "the_index": ("components_lock_remainder", "the_index"),
    "constitutional_authority": ("components_lock_remainder", "constitutional_authority"),
    # components_optional
    "prp": ("components_optional", "prp"),
    "research_intelligence": ("components_optional", "research_intelligence"),
    "tfa": ("components_optional", "tfa"),
}


class RefreezeError(ValueError):
    """The refreeze log is inconsistent with the freeze manifest."""


def validation_id():
    return os.environ.get("V1_VALIDATION_ID", "v1-2026-10-16-a")


def validation_dir(vid=None):
    return ROOT / "process" / "v1-validation" / (vid or validation_id())


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_manifest(path=None):
    return load_json(path or validation_dir() / "freeze-manifest.json")


def load_refreeze_log(path=None):
    """The refreeze log, or None when the file does not exist (no overlay)."""
    p = Path(path) if path else validation_dir() / "refreeze-log.json"
    return load_json(p) if p.exists() else None


def is_applied(entry):
    status = str(entry.get("status", ""))
    return STATUS_APPLIED_RE.fullmatch(status) is not None and STATUS_NOTE_CONTRADICTION_RE.search(status) is None


def _locate(manifest, component):
    if component not in LOG_COMPONENT_TO_MANIFEST:
        raise RefreezeError(f"refreeze entry names unknown component {component!r}; known: {sorted(LOG_COMPONENT_TO_MANIFEST)}")
    group, key = LOG_COMPONENT_TO_MANIFEST[component]
    if key not in manifest.get(group, {}):
        raise RefreezeError(f"refreeze component {component!r} maps to {group}.{key}, which is not in the freeze manifest")
    return group, key


def applied_entries(log):
    return [e for e in (log or {}).get("entries", []) if is_applied(e)]


def apply_overlay(manifest, log):
    """Return (resolved_manifest, applied) - a deep copy of ``manifest`` whose component shas carry the APPLIED log entries.

    ``applied`` lists (entry_id, group, key, from_sha, to_sha) in application order.  Only component ``sha`` fields change;
    identities.*, hub and qualification identities and every file hash stay as frozen."""
    resolved = copy.deepcopy(manifest)
    if log is not None:
        if log.get("validation_id") != manifest.get("validation_id"):
            raise RefreezeError(f"refreeze log is for {log.get('validation_id')!r} (validation_id is required), manifest for {manifest.get('validation_id')!r}")
        ids = [e.get("id") for e in log.get("entries", [])]
        dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
        if dup or None in ids:
            raise RefreezeError(f"refreeze log has duplicate or missing entry ids: {dup or 'missing id'}")
    applied = []
    for entry in applied_entries(log):
        eid = entry.get("id", "?")
        group, key = _locate(resolved, entry.get("component"))
        spec = resolved[group][key]
        frm, to = entry.get("from_sha"), entry.get("to_sha")
        if not frm or not to:
            raise RefreezeError(f"refreeze entry {eid} lacks from_sha/to_sha")
        if not isinstance(to, str) or not SHA_RE.fullmatch(to):
            raise RefreezeError(f"refreeze entry {eid}: to_sha {to!r} is not a 40-character lowercase hex commit")
        if frm != spec["sha"]:
            raise RefreezeError(f"refreeze entry {eid} ({entry.get('component')}): from_sha {frm} does not equal the pin in force {spec['sha']}")
        if entry.get("repository") not in (None, spec["repository"]):
            raise RefreezeError(f"refreeze entry {eid}: repository {entry.get('repository')} != manifest repository {spec['repository']}")
        spec["sha"] = to
        applied.append((eid, group, key, frm, to))
    return resolved, applied


def resolve_manifest(manifest_path=None, log_path=None, overlay=True):
    manifest = load_manifest(manifest_path)
    if not overlay:
        return manifest, []
    return apply_overlay(manifest, load_refreeze_log(log_path))


def component_pins(manifest):
    """{manifest_key: (repository, sha)} for every pinned component of a (resolved) manifest."""
    return {key: (spec["repository"], spec["sha"]) for g in GROUPS for key, spec in manifest.get(g, {}).items()}


def pinned_sources(manifest):
    """Subject + lock-remainder components, the hub head and the qualification closeout: {key: (repository, sha)}."""
    pins = {}
    for group in ("components_subject", "components_lock_remainder"):
        for key, spec in manifest[group].items():
            pins[key] = (spec["repository"], spec["sha"])
    ident = manifest["identities"]
    pins["hub"] = (ident["hub"]["repository"], ident["hub"]["head"])
    pins["qualification"] = (ident["qualification"]["repository"], ident["qualification"]["closeout"])
    return pins


def profile_pins(manifest):
    """{profile component name: sha} for the seven subject components (profile_key of each components_subject entry)."""
    return {spec["profile_key"]: spec["sha"] for spec in manifest["components_subject"].values()}


def generations(manifest, log):
    """Cumulative pin generations of the seven profile components: [(label, {profile name: sha})].

    Generation 0 is the original freeze; a new generation is appended when an applied entry changes a profile component.
    Used to identify which pin set produced a retained evidence file (a run is internally one generation)."""
    gens = [("original-freeze", profile_pins(manifest))]
    current = copy.deepcopy(manifest)
    for entry in applied_entries(log):
        current, _ = apply_overlay(current, {"validation_id": manifest.get("validation_id"), "entries": [entry]})
        pins = profile_pins(current)
        if pins != gens[-1][1]:
            gens.append((entry.get("id", "?"), pins))
    return gens


def classify_generation(evidence_pin_sets, gens):
    """Map retained-evidence pin sets ({profile name: commit} each) to ONE generation of ``gens``.

    Returns (label, index).  Raises RefreezeError when a set matches no generation (drift) or the sets span generations."""
    found = set()
    for pins in evidence_pin_sets:
        hits = [i for i, (_, g) in enumerate(gens) if dict(pins) == g]
        if not hits:
            raise RefreezeError(f"evidence pins {dict(pins)} match no frozen generation")
        found.add(hits[0])
    if len(found) > 1:
        raise RefreezeError("retained evidence mixes pin generations: " + ", ".join(gens[i][0] for i in sorted(found)))
    if not found:
        return None, None
    i = found.pop()
    return gens[i][0], i


def select_profile(log, root=None):
    """Newest ``process/security-runtime-f5b-20261016-r<N>.json`` whose ``refreeze_ids`` are all APPLIED in ``log``.

    Falls back to the original profile when no revision profile qualifies (nothing re-frozen yet)."""
    import re
    base = Path(root) if root else ROOT
    applied = {e.get("id") for e in applied_entries(log)}
    cands = []
    for f in (base / "process").glob("security-runtime-f5b-20261016-r*.json"):
        m = re.fullmatch(r"security-runtime-f5b-20261016-r(\d+)\.json", f.name)
        if m:
            cands.append((int(m.group(1)), f))
    for _, f in sorted(cands, key=lambda c: c[0], reverse=True):
        ids = load_json(f).get("refreeze_ids") or []
        if ids and set(ids) <= applied:
            return f.relative_to(base).as_posix()
    return ORIGINAL_PROFILE


# ---------------------------------------------------------------- resolved constants (manifest + overlay)
_MANIFEST = load_manifest()
_ORIGINAL_MANIFEST = copy.deepcopy(_MANIFEST)
_RESOLVED, APPLIED_REFREEZES = apply_overlay(_MANIFEST, load_refreeze_log())
_P = _RESOLVED["components_subject"]
_O = _ORIGINAL_MANIFEST

RESOLVED_MANIFEST = _RESOLVED
ORIGINAL_MANIFEST = _ORIGINAL_MANIFEST
GENERATIONS = generations(_ORIGINAL_MANIFEST, load_refreeze_log())
# The profile follows the overlay: the newest r<N> profile whose refreeze_ids are all applied, else the original
# (V1_PROFILE still overrides, and the controller workflow sets it explicitly).
PROFILE_RELPATH = os.environ.get("V1_PROFILE") or select_profile(load_refreeze_log())
PROFILE_PATH = ROOT / PROFILE_RELPATH

FROZEN_HUB = _RESOLVED["identities"]["hub"]["head"]
FROZEN_RUNTIME = _P["moltbot_safe"]["sha"]
FROZEN_CONTROL_PLANE = _P["control_plane"]["sha"]
FROZEN_REPLAY = _P["replay_bundle"]["sha"]
FROZEN_EVIDENCE_PACK = _P["governance_evidence_pack"]["sha"]
FROZEN_ODES = _P["odes"]["sha"]
FROZEN_EXCHANGE = _P["gax_imx_transport"]["sha"]
FROZEN_MANIFEST_COMPONENT = _P["action_manifest"]["sha"]
FROZEN_BITREP = _RESOLVED["components_lock_remainder"]["bitrep"]["sha"]
FROZEN_INDEX = _RESOLVED["components_lock_remainder"]["the_index"]["sha"]
# Index: the freeze pin and the re-frozen pin are both accepted by the Index scenarios (old pin: defects expected to FAIL).
OLD_INDEX_PIN = _O["components_lock_remainder"]["the_index"]["sha"]
REFROZEN_INDEX_PIN = FROZEN_INDEX

# the pins the scenario helpers and C14 compare against, by qualification-profile / ODES-provenance name
PROFILE_PINS = profile_pins(_RESOLVED)
C14_PINS = {"control_plane": FROZEN_CONTROL_PLANE, "moltbot_safe": FROZEN_RUNTIME, "replay": FROZEN_REPLAY}
