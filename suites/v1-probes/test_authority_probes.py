"""ER-03-1 probes: docx section 03 (Alvorada constitutional governance) acceptance lines that the pinned
component's own tests do not exercise (see process/v1-validation/v1-2026-10-16-a/acceptance-map-03.json).

Run against the checkout named by PROBE_AUTHORITY_DIR (cogno-us/cognous-institutional-governance at the frozen pin).
The pinned tree is only read: no file under it is written, and child processes run with bytecode writing disabled.
Probes call the pin's own reference checker/harness and read its documents; an assertion that fails is a finding about the
pinned component, not a harness error. The Authority Context harness needs the pin's optional dependency
(testing/harness/requirements-authority.txt); if it is missing the probe FAILS, it never skips.
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from conftest import pin_dir

PROFILE = "process/implementation/public-stack-v0.1"


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_AUTHORITY_DIR")


@pytest.fixture(scope="module")
def root():
    return Path(os.environ["PROBE_AUTHORITY_DIR"]).resolve()


@pytest.fixture(scope="module")
def harness(root):
    sys.path.insert(0, str(root / "testing" / "harness"))
    try:
        import authority_context as ac  # needs jsonschema only when schema_errors() is called
        import run_authority_context as rac
    finally:
        sys.path.remove(str(root / "testing" / "harness"))
    return ac, rac


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def table_rows(path):
    """Markdown pipe-table rows (header first, separator removed) as lists of stripped cells."""
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in Path(path).read_text(encoding="utf-8").splitlines() if line.startswith("|")]
    return [r for r in rows if not all(set(c) <= set("-: ") for c in r)]


def tree_digest(path):
    h = hashlib.sha256()
    for p in sorted(Path(path).rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(path)).encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


# ------------------------------------------------------------------ R1: implementation profile mapping
MAPPING_COLUMNS = ["provision", "accountable", "manifest", "runtime control or human procedure", "evidence",
                   "escalation, appeal, continuity and remedy", "implementation / test status"]


def test_probe_er031_mapping_links_provisions_to_controls_procedures_evidence_and_accountable_owners(root):
    rows = table_rows(root / PROFILE / "MAPPING.md")
    header, body = [c.lower() for c in rows[0]], rows[1:]
    assert len(header) == len(MAPPING_COLUMNS) and all(want in got for want, got in zip(MAPPING_COLUMNS, header)), header
    assert len(body) >= 10, "the mapping must cover the provisions, not a token row"
    for row in body:
        assert len(row) == len(header), row[0]
        blank = [header[i] for i, c in enumerate(row) if not c.strip()]
        assert not blank, f"{row[0]!r} leaves {blank} empty"


def test_probe_er031_every_mapping_row_declares_its_implementation_status_and_claims_no_enforcement(root):
    text = (root / PROFILE / "MAPPING.md").read_text(encoding="utf-8")
    vocab = dict(re.findall(r"\b([NPRTE]) = ([^;.\n]+)", text))
    assert set(vocab) == set("NPRTE"), vocab  # the declared status vocabulary
    for row in table_rows(root / PROFILE / "MAPPING.md")[1:]:
        status = row[-1]
        tokens = re.match(r"^([NPRTE](?:/[NPRTE])*)\b", status)
        assert tokens, f"{row[0]!r}: status cell does not start with a declared status token: {status!r}"
        assert "E" not in tokens.group(1).split("/"), f"{row[0]!r} claims operational enforcement: {status!r}"
        # 'unsupported'/'untested' must be explicit rather than implied by an absent token
        assert re.search(r"unsupported|unimplemented|does not|not (?:validated|implemented|tested)|no |only|not established|need", status, re.I), \
            f"{row[0]!r} does not state what remains unsupported or untested: {status!r}"
    assert re.search(r"no\s+E\s+claims", text, re.I)


# ------------------------------------------------------------------ R2: consequence tiers
def _tier_table(root):
    rows = table_rows(root / "process" / "PROPORTIONAL_GOVERNANCE.md")
    start = next(i for i, r in enumerate(rows) if r[0].lower() == "tier")
    return rows[start], [r for r in rows[start + 1:] if re.match(r"T[0-4]\b", r[0])]


def test_probe_er031_every_tier_t0_to_t4_names_its_evidence_and_review_burden(root):
    header, tiers = _tier_table(root)
    assert [r[0][:2] for r in tiers] == ["T0", "T1", "T2", "T3", "T4"]
    ev, burden = (next(i for i, h in enumerate(header) if k in h.lower()) for k in ("evidence", "review"))
    for r in tiers:
        assert len(r[ev]) > 20 and len(r[burden]) > 20, r[0]
    # review intensity must visibly rise: the reserved/competent-human requirement appears from T2 upward, not at T0/T1
    assert all(re.search(r"competent human|reserved human", r[burden], re.I) for r in tiers[2:])
    assert not any(re.search(r"competent human prior|actual competent human", r[burden], re.I) for r in tiers[:2])


def test_probe_er031_standing_class_grants_are_limited_to_routine_tiers_and_reserved_tiers_need_case_approval(root, harness):
    ac, rac = harness
    header, tiers = _tier_table(root)
    burden = next(i for i, h in enumerate(header) if "review" in h.lower())
    assert re.search(r"standing human approval of action class", tiers[0][burden], re.I)
    assert re.search(r"delegated", tiers[1][burden], re.I)
    # executable half: a T2 requirement without approval obligations is itself rejected, a T4 can never be a routine grant
    bases = jload(root / "testing/fixtures/authority-context/bases.json")
    hc = copy.deepcopy(bases["higher-consequence"])
    hc["context"]["requirement"]["approvals"] = []
    assert "missing_reserved_approval_requirement" in ac.reference_errors(hc["context"], hc["snapshot"], hc["action"], hc["now"])
    routine = copy.deepcopy(bases["routine"])
    routine["context"]["requirement"]["consequence"]["tier"] = "T4"
    assert "reserved_constitutional_process" in ac.reference_errors(routine["context"], routine["snapshot"], routine["action"], routine["now"])


def test_probe_er031_continuity_route_is_mandatory_for_every_context_regardless_of_tier(root):
    schema = jload(root / PROFILE / "authority-context.schema.json")
    required = schema["properties"]["conflicts"]["required"]
    assert {"escalation_ref", "appeal_ref", "continuity_ref", "remedy_ref"} <= set(required)
    for name in ("routine", "higher-consequence"):
        ctx = jload(root / PROFILE / "examples" / f"{name}.json")
        assert all(ctx["conflicts"][k] for k in ("escalation_ref", "appeal_ref", "continuity_ref", "remedy_ref")), name


def test_probe_er031_tier_declares_a_delay_limit(root):
    """docx 03 recommendation 2 asks for consequence tiers connected to delay limits. The profile deliberately supplies no universal
    limit; this probe asks only that a delay limit is a declared, tier-linked concept somewhere an implementer would read it:
    a column/clause of the tier table, a requirement field in the Authority Context schema, or a row of the provision mapping."""
    header, tiers = _tier_table(root)
    in_tier_table = any(re.search(r"delay|deadline|time limit|maximum (?:age|wait)", c, re.I) for r in tiers for c in r) \
        or any(re.search(r"delay|deadline|time limit", h, re.I) for h in header)
    schema_text = (root / PROFILE / "authority-context.schema.json").read_text(encoding="utf-8")
    in_schema = re.search(r'"[a-z_]*(?:delay|deadline|latency|time_limit|sla)[a-z_]*"', schema_text, re.I) is not None
    tier_row = next(r for r in table_rows(root / PROFILE / "MAPPING.md") if r[0].lower().startswith("proportional guidance"))
    in_mapping = re.search(r"delay|deadline|time limit", " ".join(tier_row), re.I) is not None
    assert in_tier_table or in_schema or in_mapping, \
        "no delay limit is linked to any consequence tier (tier table, Authority Context schema, provision mapping)"


# ------------------------------------------------------------------ A1: customer-service worked example
def test_probe_er031_shipped_worked_example_files_are_the_executed_fixture_bases(root):
    bases = jload(root / "testing/fixtures/authority-context/bases.json")
    for example, base in (("routine", "routine"), ("higher-consequence", "higher-consequence")):
        ex = jload(root / PROFILE / "examples" / f"{example}.json")
        ref = jload(root / PROFILE / "examples" / f"{example}-reference-input.json")
        assert ex == bases[base]["context"], f"{example}.json differs from the fixture context the oracle executes"
        for key in ("snapshot", "action", "now"):
            assert ref[key] == bases[base][key], f"{example}-reference-input.json {key} differs from the executed fixture"


def test_probe_er031_worked_example_traces_authority_through_effect_and_remedy(root, harness):
    ac, rac = harness
    doc = (root / PROFILE / "WORKED_CASES.md").read_text(encoding="utf-8")
    table = table_rows(root / PROFILE / "WORKED_CASES.md")
    stages = [r[0].lower() for r in table[1:]]
    for want in ("governing basis", "issued grant", "before effect", "effect / observation", "remedy / continuity"):
        assert any(want in s for s in stages), (want, stages)
    assert "customer-service" in doc.lower() and "refund" in doc.lower()
    # authority end of the trace executes; the effect/appeal narrative is disclosed as proposed, not executed
    assert re.search(r"effect/appeal\s+steps\s+below\s+are\s+proposed\s+and\s+have\s+not\s+been\s+executed", doc, re.I | re.S)
    bases = jload(root / "testing/fixtures/authority-context/bases.json")
    for name in ("routine", "higher-consequence"):
        b = bases[name]
        assert ac.reference_errors(b["context"], b["snapshot"], b["action"], b["now"]) == [], name
        post = [o for o in b["context"]["requirement"]["evidence"] if o["kind"] == "post_effect"]
        assert post and all(o["unknown_behavior"] == "reconcile_no_blind_retry" for o in post), name


# ------------------------------------------------------------------ A2: visibly different process burdens
def test_probe_er031_routine_and_severe_cases_carry_visibly_different_process_burdens(root, harness):
    ac, rac = harness
    routine = jload(root / PROFILE / "examples" / "routine.json")["requirement"]
    severe = jload(root / PROFILE / "examples" / "higher-consequence.json")["requirement"]
    assert routine["consequence"]["tier"] < severe["consequence"]["tier"]
    assert routine["approvals"] == [] and severe["approvals"], "routine needs no per-case approval; the severe case must"
    assert all(a["independent_of_actor"] for a in severe["approvals"])
    assert len(severe["evidence"]) >= len(routine["evidence"])
    assert severe["permissions"][0]["max_amount"] > routine["permissions"][0]["max_amount"]
    # the burden is enforced, not just declared: the severe case fails when its approval is removed, the routine case does not need one
    bases = jload(root / "testing/fixtures/authority-context/bases.json")
    sev = copy.deepcopy(bases["higher-consequence"])
    sev["context"]["grant"]["approval_refs"] = []
    assert "missing_or_invalid_approval" in ac.reference_errors(sev["context"], sev["snapshot"], sev["action"], sev["now"])
    rt = bases["routine"]
    assert ac.reference_errors(rt["context"], rt["snapshot"], rt["action"], rt["now"]) == []


# ------------------------------------------------------------------ A3: four concepts remain distinct
def test_probe_er031_reference_results_never_say_allow_or_executed_and_the_schema_refuses_decision_fields(root, harness):
    ac, rac = harness
    result = rac.execute()
    assert result["status"] == "EXECUTED_LOCAL_REFERENCE_CHECKS"
    assert result["runtime_enforcement"] is False and result["independently_reviewed"] is False
    for row in result["results"]:
        assert set(row) == {"id", "schema_valid", "reference_errors", "oracle_satisfied"}, set(row)
    bases = jload(root / "testing/fixtures/authority-context/bases.json")
    for field in ("allowed", "runtime_decision", "decision", "executed"):
        ctx = copy.deepcopy(bases["routine"]["context"])
        ctx[field] = True
        assert ac.schema_errors(ctx), f"schema accepted a '{field}' field: structure must not carry a permission decision"


def test_probe_er031_capability_authentication_evidence_and_permission_fail_independently(root, harness):
    """One defect at a time: each of the four layers must be refused on its own, with its own reason, and a pass on the other three
    must not rescue it. (capability = grant scope vs requirement envelope; authentication = issuer/identity binding;
    evidence acceptance = required evidence fact; lawful permission = adopted basis / issued grant.)"""
    ac, rac = harness
    bases = jload(root / "testing/fixtures/authority-context/bases.json")

    def errors(mutate):
        b = copy.deepcopy(bases["higher-consequence"])
        mutate(b)
        return ac.reference_errors(b["context"], b["snapshot"], b["action"], b["now"])

    first_ev = lambda b: next(iter(b["snapshot"]["evidence"]))
    assert errors(lambda b: None) == []
    cap = errors(lambda b: b["action"].update(amount=b["action"]["amount"] * 10))
    auth = errors(lambda b: b["snapshot"].update(issuers=[]))
    evid = errors(lambda b: b["snapshot"]["evidence"].pop(first_ev(b)))
    perm = errors(lambda b: b["snapshot"].update(authority_bases=[]))
    assert "action_out_of_scope" in cap and "untrusted_issuer_mandate" not in cap and "missing_or_stale_evidence" not in cap
    assert "untrusted_issuer_mandate" in auth and "action_out_of_scope" not in auth and "missing_or_stale_evidence" not in auth
    assert "missing_or_stale_evidence" in evid and "untrusted_issuer_mandate" not in evid and "action_out_of_scope" not in evid
    assert "missing_authority_basis" in perm and "untrusted_issuer_mandate" not in perm and "missing_or_stale_evidence" not in perm


# ------------------------------------------------------------------ A4: existing tests and archived results keep their scope
def _run_verifier(root, script):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, "-B", script], cwd=root / "testing" / "harness", env=env,
                          capture_output=True, text=True, timeout=600)


@pytest.mark.parametrize("script", ["verify_snapshot.py", "verify_film_review.py", "verify_authorization_effect.py"])
def test_probe_er031_archived_results_still_verify_by_hash_and_deterministic_replay(root, script):
    proc = _run_verifier(root, script)
    assert proc.returncode == 0, proc.stdout[-800:] + proc.stderr[-800:]
    assert proc.stdout.startswith("PASS"), proc.stdout[-400:]


def test_probe_er031_new_authority_checks_do_not_alter_the_archived_results(root, harness):
    """Executing the Authority Context reference checks must not write to the archived results, and the checks the pin has
    already recorded must keep their recorded outcome. The check count is DERIVED, not fixed: the pin may add reference
    checks (F-15 added seven) but every recorded check must still be executed with its recorded outcome, every executed
    check must satisfy its oracle, and the executed set must equal the declared fixture set. (F-15 / P4 revision 2026-10-17:
    replaced the literal 44.)"""
    ac, rac = harness
    before = tree_digest(root / "testing" / "results")
    result = rac.execute()
    assert tree_digest(root / "testing" / "results") == before
    declared = [c["id"] for c in jload(root / "testing/fixtures/authority-context/cases.json")]
    executed = [r["id"] for r in result["results"]]
    assert len(set(declared)) == len(declared), "duplicate fixture ids"
    assert executed == declared and result["fixture_count"] == len(declared), "executed checks differ from the declared fixture set"
    assert result["passed"] == result["fixture_count"] and all(r["oracle_satisfied"] for r in result["results"]), \
        [r["id"] for r in result["results"] if not r["oracle_satisfied"]]
    # the pin's recorded run: every recorded check is still executed with the same outcome (new checks may be added)
    recorded = jload(root / "testing/fixtures/authority-context/results.json")
    live = {r["id"]: r for r in result["results"]}
    assert recorded["fixture_count"] == len(recorded["results"]) and recorded["fixture_count"] <= result["fixture_count"]
    for row in recorded["results"]:
        assert live.get(row["id"]) == row, f"recorded check {row['id']} is missing or changed"


def test_probe_er031_archived_results_retain_their_synthetic_and_unreviewed_scope(root):
    """The scope of an archived result (synthetic execution, no independent review) is carried by its machine-readable
    results.json (execution_status / review_status), which the pin's verifiers hash. It used to be asserted by README wording
    ('synthetic' must appear); the pin moved run commentary to the central test hub (stack-qualification
    results/readme-commentary), so the README is now a pointer and its wording is documentation, not the guarantee.
    (F-15 / P4 revision 2026-10-17.) Asserted instead: each archive directory still has its results and manifest, its
    results.json is marked EXECUTED_SYNTHETIC and NOT_INDEPENDENTLY_REVIEWED, and no README upgrades the status
    (no claim of proven efficacy or field success)."""
    archives = [d for d in sorted((root / "testing" / "results").iterdir()) if d.is_dir()]
    assert len(archives) >= 3, [d.name for d in archives]
    for d in archives:
        assert (d / "results.json").is_file() and (d / "manifest.json").is_file(), d.name
        res = jload(d / "results.json")
        assert res["execution_status"] == "EXECUTED_SYNTHETIC", d.name
        assert res["review_status"] == "NOT_INDEPENDENTLY_REVIEWED", d.name
        readme = d / "README.md"
        if readme.is_file():
            text = readme.read_text(encoding="utf-8")
            assert not re.search(r"proven (?:efficacy|governance)|field (?:pilot )?success", text, re.I) or \
                re.search(r"not (?:a )?field", text, re.I), d.name
    ae = jload(root / "testing/results/2026-10-05-authorization-effect-v1/results.json")
    assert ae["execution_status"] == "EXECUTED_SYNTHETIC" and ae["review_status"] == "NOT_INDEPENDENTLY_REVIEWED"


# ------------------------------------------------------------------ dependencies / drafting constraints
def test_probe_er031_profile_is_labelled_proposed_and_not_adopted_and_makes_no_ratification_claim(root):
    readme = (root / PROFILE / "README.md").read_text(encoding="utf-8")
    assert "PROPOSED PENDING GOVERNOR REVIEW. NOT ADOPTED, RATIFIED OR A RUNTIME." in readme
    assert "PROPOSED CROSS-COMPONENT INTERFACE; PENDING GOVERNOR REVIEW." in (root / PROFILE / "AUTHORITY_CONTEXT.md").read_text(encoding="utf-8")
    assert "INVENTED CASES; NO INSTITUTION, GRANT, APPROVAL OR EFFECT IS REAL." in (root / PROFILE / "WORKED_CASES.md").read_text(encoding="utf-8")
    negation = re.compile(r"\b(?:not|no|never|unratified|unadopted|without|cannot|pending|nor|neither|unsupported|unimplemented|"
                          r"propos\w+|requires?|reserved|separately|distinct)\b", re.I)
    for md in sorted((root / PROFILE).glob("*.md")):
        for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b(?:has been|is|was|are|were) (?:formally )?(?:ratified|adopted|enacted)\b", line, re.I):
                assert negation.search(line), f"{md.name}:{n} affirms adoption/ratification: {line.strip()[:160]}"


def test_probe_er031_outcome_feedback_cannot_adopt_change_and_adoption_needs_a_recorded_human_act(root, harness):
    ac, rac = harness
    bases = jload(root / "testing/fixtures/authority-context/bases.json")

    def errors(change, adoption_records=()):
        b = copy.deepcopy(bases["routine"])
        b["context"]["change"] = change
        b["snapshot"]["human_adoption_records"] = list(adoption_records)
        return ac.reference_errors(b["context"], b["snapshot"], b["action"], b["now"])

    ref = "urn:example:record:adoption"
    # a proposal alone (feedback) is never an adoption: an adoption reference nobody recorded is refused
    assert "unadopted_amendment" in errors({"kind": "policy_proposal", "proposal_ref": "urn:example:proposal:p", "adoption_record_ref": ref})
    assert "unadopted_amendment" in errors({"kind": "constitutional_proposal", "proposal_ref": "urn:example:proposal:p", "adoption_record_ref": ref})
    # a proposal with no adoption reference is a valid object and changes nothing
    assert "unadopted_amendment" not in errors({"kind": "policy_proposal", "proposal_ref": "urn:example:proposal:p", "adoption_record_ref": None})
    # only a separately recorded human adoption record is accepted, and it never makes a T4 change a routine grant
    assert "unadopted_amendment" not in errors({"kind": "policy_proposal", "proposal_ref": "urn:example:proposal:p", "adoption_record_ref": ref}, [ref])
    t4 = copy.deepcopy(bases["routine"])
    t4["context"]["requirement"]["consequence"]["tier"] = "T4"
    t4["snapshot"]["human_adoption_records"] = [ref]
    t4["context"]["change"] = {"kind": "constitutional_proposal", "proposal_ref": "urn:example:proposal:p", "adoption_record_ref": ref}
    assert "reserved_constitutional_process" in ac.reference_errors(t4["context"], t4["snapshot"], t4["action"], t4["now"])


def test_probe_er031_profile_provides_requirements_to_manifest_and_control_plane_without_issuing_grants(root):
    rows = {r[0].lower(): r for r in table_rows(root / PROFILE / "README.md") if len(r) == 3}
    for consumer in ("action manifest", "control plane"):
        assert consumer in rows, list(rows)
        assert len(rows[consumer][1]) > 40 and len(rows[consumer][2]) > 40
    assert re.search(r"requirement", rows["action manifest"][1], re.I)
    assert re.search(r"grant", rows["control plane"][1], re.I)
    assert re.search(r"neither issues a grant", rows["action manifest"][2], re.I)
    assert re.search(r"cannot become a production allow", rows["control plane"][2], re.I)


def test_probe_er031_profile_imports_no_private_mechanisms_or_coordination_experiment_artifacts(root):
    """Documentary guard for the docx 03 dependency: scan the profile, its fixtures and harness for private-mechanism markers
    (the Architecture of Mind / ISS mechanisms named by the Register as private) and for the old coordination experiment."""
    marker = re.compile(r"Architecture of Mind|\bAoM\b|\bISS\b|ISSMIN|coordination experiment|proprietary", re.I)
    scanned = list((root / PROFILE).rglob("*")) + list((root / "testing/fixtures/authority-context").rglob("*")) + \
        [root / "testing/harness/authority_context.py", root / "testing/harness/run_authority_context.py"]
    hits = []
    for p in scanned:
        if p.is_file():
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if marker.search(line):
                    hits.append(f"{p.relative_to(root)}:{n}: {line.strip()[:120]}")
    assert not hits, hits


# ------------------------------------------------------------------ history-based scope probes (need the pinned checkout's full history)
BASELINE = "76cdff90d0370632faa4e033749c552fd6bbd37d"  # the baseline named in the profile README ("Sources and scope")

# RE-BASELINED 2026-10-17 (F-15 / P4, owner instruction; see docs/authority-probe-rebaseline.md).
# The baseline commit is unchanged. What changed is the split of what the pin must guarantee:
#
# NORMATIVE_IMMUTABLE: the normative and evidential artifacts. No file that existed at BASELINE may be modified, deleted or
#   renamed (additions are allowed): constitutional text and drafts, history, archived results (data, manifests and verifier
#   inputs; only their README commentary may move), the battery/sources/protocol, applications, the pre-existing harness
#   scripts and the authorization/effect contract.
# DOCUMENTATION_METADATA: files whose wording may change without affecting any guarantee: citation, licence/notice and
#   repository metadata, root and directory READMEs, docs/. Archived-result READMEs are here because the pin moved run
#   commentary to the central test hub; the archives' scope is asserted from their machine-readable results.json instead.
# Everything else that was modified (for example process/PROPORTIONAL_GOVERNANCE.md, tests/test_bootstrap.py) may only be
#   EXTENDED: a removed line must reappear as the prefix of an added line (a column or sentence appended), never rewritten.
# tools/validate_bootstrap.py is the one reviewed refactor exception (linear-time duplicate detection, symlink refusal,
#   a new schedule-O instrument check): it is guarded by tests/test_bootstrap.py, which is append-only above.
NORMATIVE_IMMUTABLE = ("constitution/", "constitutional-design/", "history/", "testing/results/", "testing/battery/",
                       "testing/sources/", "testing/PROTOCOL.md", "applications/", "testing/harness/run_reference.py",
                       "testing/harness/run_authorization_effect.py", "testing/harness/run_film_review.py",
                       "testing/harness/test_authorization_effect.py", "testing/harness/test_film_review_adapter.py",
                       "testing/harness/verify_snapshot.py", "testing/harness/verify_authorization_effect.py",
                       "testing/harness/verify_film_review.py", "tests/test_reviewed_artifact_digest.py",
                       "process/AUTHORIZATION_EFFECT_CONTRACT.md")
DOCUMENTATION_METADATA = ("CITATION.cff", "LICENSE", "NOTICE.md", "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
                          "CODE_OF_CONDUCT.md", "docs/")
REVIEWED_REFACTOR = ("tools/validate_bootstrap.py",)


def _is_documentation(path):
    return path.startswith(DOCUMENTATION_METADATA) or path.endswith("/README.md")


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=300)


def _history(root):
    if _git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        pytest.fail("pinned checkout is shallow; run this probe job with --full-history")
    proc = _git(root, "merge-base", "--is-ancestor", BASELINE, "HEAD")
    assert proc.returncode == 0, f"profile baseline {BASELINE} is not an ancestor of the pin"


def _is_immutable(path):
    # archived-result READMEs carry commentary only; everything else under the immutable prefixes is fixed
    return path.startswith(NORMATIVE_IMMUTABLE) and not (path.startswith("testing/results/") and path.endswith("/README.md"))


def test_probe_er031_profile_commits_only_add_to_the_baseline_and_never_rewrite_existing_content(root):
    """Between the baseline the profile names and the pin, no path is deleted, renamed or type-changed, and no normative
    file loses or rewrites an existing line. Documentation and citation metadata may be rewritten (they carry no guarantee);
    other modified files may only be extended (a removed line must reappear with text appended, e.g. a new table column or
    sentence). Revised 2026-10-17 from 'no existing line removed anywhere' (see the constants above)."""
    _history(root)
    names = _git(root, "diff", "--name-status", BASELINE, "HEAD").stdout.splitlines()
    assert names, "no change between baseline and pin"
    kinds = Counter(line.split("\t")[0][0] for line in names)
    assert set(kinds) <= {"A", "M"}, f"deleted/renamed/type-changed paths between baseline and pin: {names}"
    modified = [line.split("\t", 1)[1] for line in names if line[0] == "M"]
    rewritten = []
    for path in modified:
        if _is_documentation(path) or path in REVIEWED_REFACTOR:
            continue
        diff = _git(root, "diff", "-U0", "--no-color", BASELINE, "HEAD", "--", path).stdout.splitlines()
        removed = [l[1:].rstrip() for l in diff if l.startswith("-") and not l.startswith("---")]
        added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
        rewritten += [f"{path}: {r[:100]!r}" for r in removed if not any(a.startswith(r) for a in added)]
    assert not rewritten, f"existing normative lines removed or rewritten (not merely extended): {rewritten}"
    # the tier table keeps its original columns and cells; F-15 may only append the delay-limit column
    old = _git(root, "show", f"{BASELINE}:process/PROPORTIONAL_GOVERNANCE.md").stdout
    new = (root / "process/PROPORTIONAL_GOVERNANCE.md").read_text(encoding="utf-8")
    cells = lambda text: [[c.strip() for c in l.strip().strip("|").split("|")] for l in text.splitlines()
                          if re.match(r"\|\s*(?:Tier\b|T[0-4]\b)", l)]
    old_rows, new_rows = cells(old), cells(new)
    assert len(old_rows) == len(new_rows) == 6 and all(n[:len(o)] == o for o, n in zip(old_rows, new_rows)), \
        "the baseline tier table cells were changed"


def test_probe_er031_constitutional_text_archives_and_pre_existing_checks_are_untouched_since_the_baseline(root):
    """The normative and evidential artifacts the pin must guarantee are byte-identical to the baseline: no file that existed
    at the baseline under NORMATIVE_IMMUTABLE is modified, deleted or renamed (additions are allowed), the immutable draft
    constitution and every archived-result data file are byte-identical, and the baseline test names of the pin's own
    repository suite are all still present. Documentation and citation metadata are no longer protected (re-baselined
    2026-10-17, see the constants above)."""
    _history(root)
    changed = _git(root, "diff", "--name-status", "--diff-filter=MDRT", BASELINE, "HEAD").stdout.splitlines()
    touched = [c for c in changed if _is_immutable(c.split("\t")[-1]) or _is_immutable(c.split("\t")[1])]
    assert not touched, touched
    # the immutable draft constitution and the archived result data are byte-identical to the baseline
    for path in ("constitutional-design/drafts/CONSTITUTION_v0.1.md",):
        then = _git(root, "show", f"{BASELINE}:{path}").stdout
        assert then and then == (root / path).read_text(encoding="utf-8"), path
    archived = [p for p in _git(root, "ls-tree", "-r", "--name-only", BASELINE, "testing/results").stdout.splitlines()
                if not p.endswith("/README.md")]
    assert len(archived) >= 15, archived
    for path in archived:
        assert (root / path).is_file(), f"archived result file removed: {path}"
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == \
            hashlib.sha256(subprocess.run(["git", "-C", str(root), "show", f"{BASELINE}:{path}"], capture_output=True, timeout=300).stdout).hexdigest(), path
    # pre-existing repository checks may be added to but not dropped
    names = lambda text: set(re.findall(r"^\s+def (test_\w+)\(", text, re.M))
    old_tests = names(_git(root, "show", f"{BASELINE}:tests/test_bootstrap.py").stdout)
    assert len(old_tests) > 100
    missing = old_tests - names((root / "tests/test_bootstrap.py").read_text(encoding="utf-8"))
    assert not missing, sorted(missing)[:10]


# ------------------------------------------------------------------ R2: human approval path for outcome-driven change
def test_probe_er031_human_approval_path_for_outcome_driven_governance_change_is_documented(root):
    ctx = (root / PROFILE / "AUTHORITY_CONTEXT.md").read_text(encoding="utf-8")
    row = next(r for r in table_rows(root / PROFILE / "AUTHORITY_CONTEXT.md") if r[0].lower().startswith("outcome feedback"))
    assert re.search(r"proposal", row[1], re.I) and re.search(r"separately adopts", row[1], re.I)
    assert re.search(r"no benchmark|majority of agent outputs|successful run", row[1], re.I)
    mapping = next(r for r in table_rows(root / PROFILE / "MAPPING.md") if "virtuous recursion" in r[0].lower())
    assert re.search(r"human", mapping[1], re.I) and re.search(r"proposal vs adoption record", mapping[2], re.I)
    assert re.search(r"does not amend Constitution|require actual human reserved process", mapping[3], re.I)
    recursion = (root / "process" / "VIRTUOUS_RECURSION.md").read_text(encoding="utf-8")
    assert re.search(r"human", recursion, re.I) and re.search(r"no automatic|never automatic|not automatic|cannot (?:amend|adopt)", recursion, re.I), \
        "VIRTUOUS_RECURSION.md must state that outcome-driven change is human-authorized, never automatic"
    assert "Outcome feedback" in ctx
