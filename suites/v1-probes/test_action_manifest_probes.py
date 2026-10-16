"""V1 validation probe for the Agent Action Manifest (docx recommendation 04): ER-04-4 'Any schema change has migration notes'.

Run against the pinned checkout named by PROBE_ACTION_MANIFEST_DIR, which must carry FULL git history (the probe-suite
`--full-history` flag unshallows it). A failing probe is a recorded product finding.

Rule used, derived from the pinned repository's own docs and git history (documented here so the check is reviewable):

* The repo has no migrations/ directory and no per-schema changelog file. tools/validate_migrations.py in the qualification
  repo checks test-file relocation, not schema evolution, so it is not evidence for this requirement.
* Observed practice in the pinned history: the manifest v1.1 PR (#4) recorded its schema changes in CHANGELOG.md; the W0 doc
  docs/w0-c1-c6-contracts.md declares itself a statement of "contract bytes and migration rules" with a Compatibility section
  for the 1.2 proposal generation; the validation-report schema change is described in CHANGELOG.md.
* Migration-note corpus = CHANGELOG.md plus docs/*.md whose title/status lines (first 12 lines) use the word "migration".
  Text is lower-cased and '_', '-', '/', backticks and whitespace are folded to one space.
* Schema-changing unit = a first-parent (mainline) commit or merged PR, after the baseline unit that first added schemas/,
  whose diff against its first parent touches a schemas/*.schema.json file (added or modified). The root/baseline
  creation of the v1.0 schema set is not a "change".
* Check A (per unit and schema): the change is covered if the SAME unit also touched a corpus file (CHANGELOG.md or a
  migration doc), or, failing that, if the pinned corpus names the schema (file stem, stem minus a trailing generic word
  when two or more words remain, or the stem without a _vN_M suffix). Units covered only by a different unit's note are
  reported as timing gaps in the test properties; they do not fail, because the requirement asks that notes exist.
* Check B (per version identifier): every version a schema pins (manifest_version / schema_version const or enum, or a
  _vN_M file suffix), other than the 1.0 baseline, appears as a version token in the corpus.
* Check C (non-vacuity): history is complete, the corpus is non-empty, and at least one schema-changing unit was found.
"""
import glob
import json
import os
import re
import subprocess

import pytest

from conftest import pin_dir


@pytest.fixture(scope="module")
def root():
    return pin_dir("PROBE_ACTION_MANIFEST_DIR")


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def norm(text):
    return re.sub(r"[\s_\-`*/]+", " ", text.lower())


def note_files(root):
    """Repo-relative paths of the migration-note corpus."""
    out = []
    if os.path.isfile(os.path.join(root, "CHANGELOG.md")):
        out.append("CHANGELOG.md")
    for path in sorted(glob.glob(os.path.join(root, "docs", "*.md"))):
        head = "\n".join(open(path, encoding="utf-8").read().splitlines()[:12]).lower()
        if "migration" in head:
            out.append("docs/" + os.path.basename(path))
    return out


def corpus(root):
    return {f: norm(open(os.path.join(root, f), encoding="utf-8").read()) for f in note_files(root)}


def schema_docs(root):
    return {os.path.basename(p): json.load(open(p, encoding="utf-8"))
            for p in sorted(glob.glob(os.path.join(root, "schemas", "*.schema.json")))}


GENERIC = ("requirement", "policy", "limits", "report", "hint", "action")


def name_variants(filename):
    stem = norm(filename[: -len(".schema.json")]).strip()
    base = re.sub(r" v\d+ \d+$", "", stem)
    variants = {stem, base}
    for v in list(variants):
        words = v.split()
        if len(words) > 2 and words[-1] in GENERIC:
            variants.add(" ".join(words[:-1]))
    return variants


def declared_versions(root):
    out = {}
    for fn, doc in schema_docs(root).items():
        for key in ("manifest_version", "schema_version"):
            prop = (doc.get("properties") or {}).get(key) or {}
            vals = [prop["const"]] if "const" in prop else list(prop.get("enum") or [])
            for v in vals:
                out.setdefault(str(v), []).append(f"{fn}:{key}")
        m = re.search(r"_v(\d+)_(\d+)\.schema\.json$", fn)
        if m:
            out.setdefault(f"{m.group(1)}.{m.group(2)}", []).append(f"{fn}:filename")
    out.pop("1.0", None)
    return out


def has_token(text, version):
    return re.search(r"(?<![\d.])v?" + re.escape(version) + r"(?![\d])", text) is not None


def schema_units(root):
    """[(short sha, subject, {schema files changed}, {all files changed})] for post-baseline first-parent units."""
    units, baseline_seen = [], False
    for sha in git(root, "rev-list", "--first-parent", "--reverse", "HEAD").split():
        if not git(root, "show", "-s", "--format=%P", sha).strip():
            continue  # root commit
        rows = [r.split("\t") for r in git(root, "diff", "--name-status", f"{sha}^1", sha).splitlines()]
        changed = {r[-1] for r in rows}
        sch = {os.path.basename(p) for p in changed if re.fullmatch(r"schemas/[^/]+\.schema\.json", p)}
        if not sch:
            continue
        if not baseline_seen:
            baseline_seen = True  # first unit that introduces schemas/: the v1.0 baseline, not a change
            continue
        units.append((sha[:7], git(root, "show", "-s", "--format=%s", sha).strip(), sch, changed))
    return units


def test_probe_er044_history_is_complete_and_has_schema_changes(root):
    assert git(root, "rev-parse", "--is-shallow-repository").strip() == "false", \
        "pinned checkout is shallow; run with --full-history so schema-change history can be evaluated"
    assert git(root, "rev-parse", "HEAD").strip(), "not a git checkout"
    c = corpus(root)
    assert "CHANGELOG.md" in c and len(c["CHANGELOG.md"]) > 200, "no CHANGELOG.md with content in the pinned repo"
    assert schema_units(root), "no post-baseline schema-changing unit found; check is vacuous"


def test_probe_er044_every_schema_change_has_a_migration_note(root, record_property):
    c = corpus(root)
    notes = set(c)
    uncovered, timing = [], []
    units = schema_units(root)
    for sha, subject, sch, changed in units:
        same_unit = bool(notes & changed)
        for fn in sorted(sch):
            named = [f for f, text in c.items() if any(v in text for v in name_variants(fn))]
            if not same_unit and not named:
                uncovered.append(f"{sha} {fn} ({subject})")
            elif not same_unit:
                timing.append(f"{sha} {fn} noted only elsewhere in {named}")
    record_property("schema_changing_units", "; ".join(f"{u[0]}:{','.join(sorted(u[2]))}" for u in units))
    record_property("note_corpus", ",".join(sorted(notes)))
    record_property("timing_gaps_not_failed", " | ".join(timing))
    assert not uncovered, f"schema changes with no migration/changelog note in the same unit or naming the schema (corpus {sorted(notes)}): {uncovered}"


def test_probe_er044_every_schema_version_identifier_has_a_migration_note(root):
    c = corpus(root)
    missing = {v: src for v, src in declared_versions(root).items()
               if not any(has_token(text, v) for text in c.values())}
    assert not missing, f"schema version identifiers with no migration/changelog note (corpus {sorted(c)}): {missing}"
