"""V1 validation probes for ODES (docx recommendation 09): ER-09-3 'Effect/attempt extensions are clearly proposed and
separately versioned'.

Run against the pinned checkout named by PROBE_ODES_DIR. A failing probe is a recorded product finding.

What counts as an "effect/attempt extension" in the pinned repo (derived from its own docs, docs/cognous-stack-field-mapping.md):
the base `pder-v0.1` schema has no native effect/attempt fields; effect IDs, attempt namespaces, destination effects,
observations, reconciliations etc. are carried by implementation PROFILES ("export profiles"), identified by the
`odes-cognous-stack-export-*` version strings and `odes_cognous_stack_export_*` ids that src/odes/common.py defines
(read with ast, nothing imported or executed). There is no separate effect/attempt JSON schema file.

Rules checked:
 1. Core isolation: the core schema (schema/pder-v0.1.schema.json) has no property named like effect/attempt, and the field
    mapping doc states that pder-v0.1 has no native effect/attempt fields.
 2. Separate versioning: every extension version string/id is distinct from every other and from the core identifiers
    (SCHEMA_VERSION, SCHEMA_NAME, DOCUMENT_VERSION, the core schema's own schema_version const and $id); the core schema
    version const equals common.SCHEMA_VERSION.
 3. Documented: every extension version string appears in at least one markdown doc of the repo.
 4. Clearly proposed: for each extension version, a markdown doc that names it carries a proposal marker word
    (proposal/proposed/informative/candidate/nonselected/draft) in its title/status header (first 8 lines) or in the same
    paragraph that names the version. A marker elsewhere in the same doc, or in another doc, does not count.
 5. Emitted packages (examples/producer-v2/*.package.json): profile.implementation_profile_version is a registered
    extension version, differs from profile.schema_version and record.schema_version, and the core schema version is
    carried unchanged next to it.
"""
import ast
import glob
import json
import os
import re

import pytest

from conftest import pin_dir

MARKER = re.compile(r"propos(al|ed)|informative|candidate|nonselected|draft", re.I)


@pytest.fixture(scope="module")
def root():
    return pin_dir("PROBE_ODES_DIR")


def common_constants(root):
    tree = ast.parse(open(os.path.join(root, "src", "odes", "common.py"), encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value.value
    return out


def extension_versions(root):
    return {k: v for k, v in common_constants(root).items() if v.startswith("odes-cognous-stack-export-")}


def extension_ids(root):
    return {k: v for k, v in common_constants(root).items() if v.startswith("odes_cognous_stack_export_")}


def md_docs(root):
    return {os.path.relpath(p, root): open(p, encoding="utf-8").read()
            for p in sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True))}


def core_schema(root):
    return json.load(open(os.path.join(root, "schema", "pder-v0.1.schema.json"), encoding="utf-8"))


def all_property_names(doc, acc=None):
    acc = set() if acc is None else acc
    if isinstance(doc, dict):
        for k, v in (doc.get("properties") or {}).items():
            acc.add(k)
            all_property_names(v, acc)
        for k, v in doc.items():
            if k != "properties":
                all_property_names(v, acc)
    elif isinstance(doc, list):
        for x in doc:
            all_property_names(x, acc)
    return acc


def test_probe_er093_extensions_are_found_and_not_vacuous(root):
    v, i = extension_versions(root), extension_ids(root)
    assert len(v) >= 2 and len(i) >= 2, f"no extension profile identifiers found in src/odes/common.py: {v} {i}"
    assert md_docs(root)


def test_probe_er093_core_schema_carries_no_effect_or_attempt_fields(root):
    names = {n for n in all_property_names(core_schema(root)) if re.search(r"effect|attempt", n, re.I)}
    assert not names, f"core pder-v0.1 schema defines effect/attempt properties: {sorted(names)}"
    mapping = open(os.path.join(root, "docs", "cognous-stack-field-mapping.md"), encoding="utf-8").read()
    assert re.search(r"`pder-v0\.1` has no native fields for effect IDs", mapping), \
        "field mapping no longer states that pder-v0.1 has no native effect/attempt fields"


def test_probe_er093_extension_versions_are_distinct_from_core_and_each_other(root):
    consts = common_constants(root)
    schema = core_schema(root)
    core = {consts["SCHEMA_VERSION"], consts["SCHEMA_NAME"], consts["DOCUMENT_VERSION"], schema.get("$id", ""), schema.get("title", "")}
    const = (schema["properties"]["schema_version"].get("const"), *(schema["properties"]["schema_version"].get("enum") or []))
    assert consts["SCHEMA_VERSION"] in const, f"core schema_version {const} != common.SCHEMA_VERSION {consts['SCHEMA_VERSION']}"
    ext = {**extension_versions(root), **extension_ids(root)}
    assert len(set(ext.values())) == len(ext), f"duplicate extension identifiers: {ext}"
    clash = {k: v for k, v in ext.items() if v in core}
    assert not clash, f"extension identifiers equal core identifiers: {clash}"
    assert all(re.search(r"\d+[._]\d+", v) for v in ext.values()), f"extension identifier without its own version number: {ext}"


def labelled(text, version):
    """Marker word in the doc's title/status header (first 8 lines) or in the same paragraph that names the version."""
    header = "\n".join(text.splitlines()[:8])
    paras = [para for para in re.split(r"\n\s*\n", text) if version in para]
    return bool(MARKER.search(header) or any(MARKER.search(para) for para in paras))


def test_probe_er093_every_extension_version_is_documented_and_labelled_proposed(root):
    docs = md_docs(root)
    undocumented, unlabelled = [], []
    for name, version in sorted(extension_versions(root).items()):
        naming = {p: t for p, t in docs.items() if version in t}
        if not naming:
            undocumented.append(f"{name}={version}")
        elif not any(labelled(t, version) for t in naming.values()):
            unlabelled.append(f"{name}={version} (named in {sorted(naming)})")
    assert not undocumented and not unlabelled, (
        f"extension versions not named in any markdown doc: {undocumented}; named only in docs with no "
        f"proposed/informative/candidate/nonselected/draft label: {unlabelled}")


def test_probe_er093_emitted_packages_carry_extension_version_separately_from_core_version(root):
    registered = set(extension_versions(root).values())
    core = common_constants(root)["SCHEMA_VERSION"]
    paths = sorted(glob.glob(os.path.join(root, "examples", "producer-v2", "*.package.json")))
    assert paths, "no emitted producer-v2 example packages found"
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        prof = d["profile"]
        ev = prof["implementation_profile_version"]
        assert ev in registered, f"{os.path.basename(p)}: {ev} is not a registered extension version"
        assert ev != prof["schema_version"] and ev != d["record"]["schema_version"], os.path.basename(p)
        assert prof["schema_version"] == core == d["record"]["schema_version"], f"{os.path.basename(p)}: core schema version altered"
