"""T00: the R2 chain runs against exactly the pinned PRIVATE PREVIEW QUALIFICATION TUPLE sources (HEAD and tree verified, work trees clean, no shadow modules, no canonical component-lock touched)."""
import sys

import pytest

import harness as H
import source_identity as SI


@pytest.mark.parametrize("name", sorted(SI.EXPECTED_SHAS))
@pytest.mark.row("S0", "source provenance: git rev-parse HEAD and HEAD^{tree} equal sources.json; work tree clean (no modified/untracked/ignored file, no hiding index flag)", kind="structure")
def test_pinned_source_is_exactly_the_declared_commit_and_tree_and_clean(name):
    spec = H.SOURCES[name]
    path = H.src(name)
    H.check("%s HEAD == pinned sha" % name, H.git(name, "rev-parse", "HEAD") == spec["sha"] == SI.EXPECTED_SHAS[name])
    H.check("%s HEAD^{tree} == pinned tree" % name, H.git(name, "rev-parse", "HEAD^{tree}") == spec["tree"])
    pin = SI.check_pin(path, spec)
    H.check("%s check_pin has no problem" % name, pin["problems"] == [], pin["problems"])
    out = [l for l in H.git(name, "status", "--porcelain", "--untracked-files=all", "--ignored").splitlines() if not SI.is_benign_pyc(path, l[3:].strip('"'))]
    H.check("%s git status --porcelain --untracked-files=all --ignored is empty (CPython timestamp .pyc caches aside)" % name, out == [], out[:5])
    flags = [l for l in H.git(name, "ls-files", "-v").splitlines() if l[0] != "H"]
    H.check("%s no assume-unchanged/skip-worktree flag" % name, flags == [], flags[:5])
    problems = SI.check_clean(path)
    H.check("%s content of every tracked file equals the HEAD tree; no shadow/startup file at root" % name, problems == [], problems[:5])
    H.note("observed", {"sha": pin["observed_sha"], "tree": pin["observed_tree"]})


@pytest.mark.row("S0", "manifest: sources.json is the PRIVATE PREVIEW QUALIFICATION TUPLE with exactly the three pinned SHAs and is not canonical", kind="structure")
def test_manifest_has_label_and_exact_shas():
    m = SI.load_sources()
    H.check("label + exact SHAs", SI.check_manifest(m) == [], SI.check_manifest(m))
    H.check("label text", m["label"] == "PRIVATE PREVIEW QUALIFICATION TUPLE" and "NOT canonical" in m["statement"])
    H.check("no qualification head is self-recorded in the file", "qualification" not in m["sources"])
    H.check("schema", m["schema"] == "r2-private-preview-qualification-tuple/1")
    H.check("register and parent", m["register"].endswith("#259") and m["parent"].endswith("#254"))
    H.check("constitution pin", m["constitution"].endswith("@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b"))


@pytest.mark.row("S0", "no local shadow module: every chain module and every loaded module of a pinned top-level name resolves inside its pinned dir; pinned entries lead sys.path", kind="structure")
def test_loaded_modules_resolve_inside_the_pinned_dirs_and_pinned_paths_lead_sys_path():
    entries = SI.pinned_sys_path_entries(H.SRC_DIR)
    pins = SI.pinned_dirs(H.SRC_DIR)
    # the harness' bootstrap and this module's notion of the pinned entries agree
    H.check("harness sys.path setup includes every pinned entry", SI.check_sys_path_order(entries) == [], SI.check_sys_path_order(entries))
    mods = SI.check_module_files(entries, pins=pins)
    H.check("chain modules and same-named loaded modules resolve inside the pins", mods == [], mods)
    found = {m: sys.modules[m].__file__ for m in SI.CHAIN_MODULES}
    H.check("every chain module has a __file__ under its pin", all(SI._under(f, pins[SI.CHAIN_MODULES[m]]) for m, f in found.items()))
    H.note("module_files", found)
    H.check("harness.assert_modules_from_pins agrees", bool(H.assert_modules_from_pins()))


@pytest.mark.row("S0", "canonical component-lock.json is neither referenced by the tuple nor modified in the qualification checkout", kind="structure")
def test_canonical_component_lock_is_untouched():
    p = SI.check_component_lock()
    H.check("component-lock unchanged vs git HEAD and not referenced", p == [], p)


@pytest.mark.row("S0", "the qualification revision under test is recorded at run time (git rev-parse HEAD / GITHUB_SHA) and the full report is ok", kind="structure")
def test_source_identity_report_is_ok_and_records_the_qualification_revision():
    rep = SI.source_identity_report(H.SRC_DIR)
    H.check("report ok", rep["ok"], rep["problems"][:5])
    q = rep["qualification"]
    H.check("qualification HEAD recorded (or GITHUB_SHA)", bool(q.get("head") or q.get("github_sha")), q)
    H.check("report names the label and is non-canonical", rep["label"] == SI.LABEL and rep["canonical"] is False)
    H.note("qualification", q)
    H.publish_artifact("source-identity.json", rep)
