"""Consistency checks for docs/release-gate/pre-registration.md and process/release-gate/preregistration.json.

Static only: nothing is run, no suite and no comparator. The checks tie the page and its JSON twin to each other and to the
repository: scenario ids exist in the two plans, Wiki case ids exist in the catalog and are in scope, declared known-limit tests
exist, and the frozen part of the page and of the twin has not been edited (changes are appended as amendments).
"""
import ast
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/release-gate/pre-registration.md"
TWIN = ROOT / "process/release-gate/preregistration.json"
INVENTORY = ROOT / "process/release-gate/inventory.json"
INVENTORY_DOC = ROOT / "docs/test-inventory.md"
APPLICABILITY = ROOT / "scenarios/ai-security-wiki/applicability.json"
CATALOG = ROOT / "scenarios/ai-security-wiki/catalog.json"
GOV = ROOT / "suites/cognous-open-control-stack/benchmarks/governance"
RUNNER = ROOT / "suites/cognous-open-control-stack/tools/run_comparative_governance.py"
REQUIREMENTS = ROOT / "process/v1-validation/v1-2026-10-16-a/requirements.json"

MARK = "## Amendments (appended only)"
IN_SCOPE = {"APPLICABLE", "PARTLY_COVERED"}
EXPRESSIBLE = {"yes", "partly", "no"}
REQUIRED_TERMS = {"pass", "fail", "known limit", "not claimed", "not applicable", "skipped", "xfail", "not expressible",
                  "could not check"}
AMENDMENT_ACTIONS = {"add_known_limit", "withdraw_known_limit", "confirm_proposed", "other"}
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
SCENARIO_ROW = re.compile(r"^\| \d+ \| `([^`]+)` \|$", re.M)
CASE_ROW = re.compile(r"^\| `(TC-[A-Z0-9]+-\d+)` \| (\w+) \| ([\w-]+) \| [^|]* \| (yes|partly|no) \|", re.M)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def section(doc, start, end):
    i = doc.index(start)
    j = doc.index(end, i + len(start))
    return doc[i:j]


def has_function(path, name, decorator=None):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            if decorator is None:
                return True
            return any(isinstance(d, ast.Call) and getattr(d.func, "id", None) == decorator for d in node.decorator_list)
    return False


def base_name(test_id):
    return test_id.split("::")[1].split("[")[0]


class PreregistrationBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.twin = load(TWIN)
        cls.inventory = load(INVENTORY)
        cls.applicability = load(APPLICABILITY)
        cls.cases = {c["id"]: c for c in cls.applicability["cases"]}


class Shape(PreregistrationBase):
    def test_header_fields(self):
        t = self.twin
        self.assertEqual(t["schema"], "cognous.release-gate.preregistration/1")
        self.assertIs(t["recorded_before_any_run"], True)
        self.assertIs(t["derived_from_results"], False)
        self.assertEqual(t["document"], "docs/release-gate/pre-registration.md")
        self.assertIsInstance(t["amendments"], list)
        self.assertNotRegex(self.doc.split(MARK)[0], r"\d{4}-\d\d-\d\dT\d\d:\d\d")  # the registration time is the host's merge time

    def test_scope_text_is_the_repository_scope_text(self):
        scope = self.twin["scope_text"]
        self.assertIn(scope, INVENTORY_DOC.read_text(encoding="utf-8"))
        self.assertIn(scope, self.doc)
        for needle in ("Bounded synthetic profile only", "configured by Cognous", "not independent certification",
                       "not production readiness", "operational trust stays on HOLD"):
            self.assertIn(needle, scope)

    def test_criteria_are_the_agreed_eight(self):
        criteria = {c["id"]: c["text"] for c in self.twin["criteria"]}
        self.assertEqual(list(criteria), [f"PC-{n}" for n in range(1, 9)])
        self.assertIn("100%", criteria["PC-1"])
        for word in ("OCS-1", "OCS-2", "OCS-3", "individual-component", "cross-component"):
            self.assertIn(word, criteria["PC-1"])
        self.assertIn("no unexplained skips and no unexplained xfails", criteria["PC-2"])
        self.assertIn("listed separately", criteria["PC-3"])
        self.assertIn("recorded before the result is seen", criteria["PC-4"])
        for word in ("19 corner", "24 baseline", "pre-registered per case", "identical scoring"):
            self.assertIn(word, criteria["PC-5"])
        self.assertIn("a comparator passes and OCS does not", criteria["PC-6"])
        self.assertIn(self.twin["scope_text"], criteria["PC-7"])
        self.assertIn("only where both", criteria["PC-8"])
        for text in criteria.values():
            self.assertIn(text, self.doc)

    def test_definitions_cover_the_required_terms(self):
        terms = {d["term"] for d in self.twin["definitions"]}
        self.assertTrue(REQUIRED_TERMS <= terms, REQUIRED_TERMS - terms)
        for d in self.twin["definitions"]:
            self.assertTrue(d["text"].strip(), d["term"])
            self.assertIn(f"- **{d['term']}.** {d['text']}", self.doc)

    def test_rule_lists_appear_in_the_page_in_order(self):
        for key, prefix in (("declaration_rules", "DR"), ("reporting", "RP"), ("run_order", "RO"), ("decisions_open", "OD")):
            items = self.twin[key]
            self.assertEqual([i["id"] for i in items], [f"{prefix}-{n}" for n in range(1, len(items) + 1)], key)
            for i in items:
                self.assertIn(f"- **{i['id']}.** {i['text']}", self.doc, i["id"])
        proposed = self.twin["scoring"]["proposed"]
        self.assertEqual([i["id"] for i in proposed], [f"PR-{n}" for n in range(1, len(proposed) + 1)])
        for i in proposed:
            self.assertIn(f"- **{i['id']}.** {i['text']}", self.doc, i["id"])
        self.assertIn("PROPOSED", self.doc)

    def test_the_page_names_every_required_part(self):
        for heading in ("## 1. Purpose", "## 2. The publication criteria", "## 3. Definitions",
                        "## 4. How a known limit or a reclassification is declared before a run", "## 5. The comparator subset",
                        "## 6. Scoring: identical for OCS and for each comparator", "## 7. Cases a comparator cannot express",
                        "## 8. Known limits declared for the run", "## 9. Reporting format", "## 10. Order of runs",
                        "## 11. Who may change this page after a run", "## 12. Decisions still open", MARK):
            self.assertIn(heading, self.doc)

    def test_relative_links_resolve(self):
        for target in re.findall(r"\]\((\.\./[^)#]+)\)", self.doc):
            self.assertTrue((DOC.parent / target).resolve().exists(), target)


class ComparatorSets(PreregistrationBase):
    def test_corner_and_baseline_ids_match_the_plans(self):
        subset = self.twin["comparator_subset"]
        for key, plan_name, count in (("corner", "corner-plan.json", 19), ("baseline", "plan.json", 24)):
            plan_bytes = (GOV / plan_name).read_bytes()
            plan = json.loads(plan_bytes)
            ids = [c["id"] for c in plan["cases"]]
            self.assertEqual(subset[key]["scenario_ids"], ids, key)
            self.assertEqual(len(ids), count)
            self.assertEqual(len(set(ids)), count)
            self.assertEqual(subset[key]["plan_sha256"], sha(plan_bytes), f"{key} plan changed: record an amendment")
            self.assertEqual(subset[key]["seeds"], plan["seeds"])
            self.assertEqual(subset[key]["repetitions"], plan["repetitions"])
            self.assertEqual(subset[key]["plan"], f"suites/cognous-open-control-stack/benchmarks/governance/{plan_name}")

    def test_both_plans_name_the_three_configurations(self):
        configs = [c["id"] for c in self.twin["comparator_subset"]["configurations"]]
        self.assertEqual(len(configs), 3)
        for plan_name in ("corner-plan.json", "plan.json"):
            self.assertEqual(load(GOV / plan_name)["profiles"], configs)

    def test_policy_file_and_scoring_function_are_pinned(self):
        subset = self.twin["comparator_subset"]
        self.assertEqual(subset["policy_file"]["sha256"], sha((GOV / "policy.rego").read_bytes()),
                         "policy file changed: record an amendment")
        source = RUNNER.read_text(encoding="utf-8")
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
        digest = sha(ast.get_source_segment(source, node).encode("utf-8"))
        self.assertEqual(self.twin["scoring"]["oracle"]["function_source_sha256"], digest,
                         "scoring function changed: record an amendment")
        self.assertIs(self.twin["scoring"]["identical_for_every_configuration"], True)
        self.assertIs(self.twin["scoring"]["aggregate_score"], False)
        self.assertIs(self.twin["scoring"]["ranking"], False)

    def test_page_lists_the_same_scenario_ids(self):
        subset = self.twin["comparator_subset"]
        corner_text = section(self.doc, "### 5.1 Corner scenarios (19)", "### 5.2 Baseline scenarios (24)")
        baseline_text = section(self.doc, "### 5.2 Baseline scenarios (24)", "### 5.3 Wiki subset")
        self.assertEqual(SCENARIO_ROW.findall(corner_text), subset["corner"]["scenario_ids"])
        self.assertEqual(SCENARIO_ROW.findall(baseline_text), subset["baseline"]["scenario_ids"])

    def test_the_scoring_outcomes_are_declared(self):
        outcomes = set(self.twin["scoring"]["outcomes"])
        self.assertEqual(outcomes, {"pass", "fail", "not expressible", "not claimed", "could not check"})
        self.assertEqual(len(self.twin["scoring"]["trial_passes_when"]), 4)
        self.assertTrue(self.twin["scoring"]["pilot_specification_lacks"])


class WikiSubset(PreregistrationBase):
    def test_every_case_is_in_the_catalog_and_in_scope(self):
        wiki = self.twin["comparator_subset"]["wiki"]
        catalog_ids = {s["id"] for s in load(CATALOG)["scenarios"]}
        for row in wiki["included"] + wiki["excluded"]:
            self.assertIn(row["id"], catalog_ids, row["id"])
            self.assertIn(row["id"], self.cases, row["id"])
            case = self.cases[row["id"]]
            self.assertIn(case["classification"], IN_SCOPE, row["id"])
            self.assertEqual(row["classification"], case["classification"], row["id"])
            self.assertEqual(row["split"], case["split"], row["id"])
            self.assertEqual(row["components"], case["components"], row["id"])

    def test_the_pool_is_exactly_the_in_scope_cases(self):
        wiki = self.twin["comparator_subset"]["wiki"]
        pool = {cid for cid, c in self.cases.items() if c["classification"] in IN_SCOPE}
        ids = [r["id"] for r in wiki["included"]] + [r["id"] for r in wiki["excluded"]]
        self.assertEqual(len(ids), len(set(ids)), "a case is both included and excluded, or listed twice")
        self.assertEqual(set(ids), pool)
        self.assertEqual(wiki["in_scope_cases"], len(pool))
        self.assertEqual(self.twin["basis"]["applicability_version"], self.applicability["applicability_version"])
        self.assertEqual(self.twin["basis"]["catalog_source_commit"], self.applicability["catalog_source_commit"])

    def test_each_row_has_a_reason_and_inclusion_follows_the_rule(self):
        wiki = self.twin["comparator_subset"]["wiki"]
        for row in wiki["included"] + wiki["excluded"]:
            self.assertGreater(len(row["reason"].split()), 6, row["id"])
            self.assertIn(row["engine_could_express"], EXPRESSIBLE, row["id"])
            self.assertTrue(row["reason"].startswith("Asks"), row["id"])
        for row in wiki["included"]:
            self.assertIn(row["engine_could_express"], {"yes", "partly"}, f"{row['id']}: a case a generic engine cannot express is not included")
            self.assertTrue(row["included"])
        for row in wiki["excluded"]:
            self.assertFalse(row["included"])
        self.assertTrue(any(r["engine_could_express"] == "no" for r in wiki["excluded"]))

    def test_exclusion_does_not_rest_on_a_missing_comparator_check(self):
        # An exclusion is justified by the object of the case, never by what a configuration was or was not built to check.
        for row in self.twin["comparator_subset"]["wiki"]["excluded"]:
            for phrase in ("comparator fails", "comparator did not", "OCS passes", "OCS fails"):
                self.assertNotIn(phrase, row["reason"], row["id"])

    def test_page_tables_agree_with_the_twin(self):
        wiki = self.twin["comparator_subset"]["wiki"]
        inc_text = section(self.doc, "#### Included (", "#### Excluded (")
        exc_text = section(self.doc, "#### Excluded (", "## 6. Scoring")
        for rows, text in ((wiki["included"], inc_text), (wiki["excluded"], exc_text)):
            parsed = [(m[0], m[1], m[2], m[3]) for m in CASE_ROW.findall(text)]
            expected = [(r["id"], r["classification"], r["split"], r["engine_could_express"]) for r in rows]
            self.assertEqual(parsed, expected)
            for r in rows:
                self.assertIn(r["reason"], text, r["id"])
        self.assertIn(f"Included ({len(wiki['included'])})", self.doc)
        self.assertIn(f"Excluded ({len(wiki['excluded'])})", self.doc)

    def test_the_open_budget_decision_is_recorded(self):
        ids = [r["id"] for r in self.twin["comparator_subset"]["wiki"]["included"]]
        self.assertIn("TC-D13-003", ids)
        self.assertTrue(any("TC-D13-003" in d["text"] for d in self.twin["decisions_open"]))


class DeclaredKnownLimits(PreregistrationBase):
    def test_fix2_probe_declarations(self):
        fx = self.twin["declared_known_limits"]["fix2_probes"]
        known_limits_md = (ROOT / "suites/fix2-probes/KNOWN_LIMITS.md").read_text(encoding="utf-8")
        self.assertEqual(len(fx["declared"]), 7)
        self.assertEqual(fx["listed_in_source"], 22)
        self.assertEqual(fx["not_declared_resolved"]["count"], 15)
        self.assertEqual(len(fx["not_declared_resolved"]["ids"]), 15)
        declared = {r["id"] for r in fx["declared"]}
        self.assertEqual(len(declared), 7)
        self.assertFalse(declared & set(fx["not_declared_resolved"]["ids"]))
        # A declaration withdrawn by an appended amendment (the probe now passes and its mark was removed) is no longer
        # listed in KNOWN_LIMITS.md; the original entry stays in the record and the test function must still exist.
        withdrawn = {a["id"] for a in self.twin["amendments"] if a["action"] == "withdraw_known_limit"}
        every_declared = set(declared)
        every_declared |= {r["id"] for r in self.twin["declared_known_limits"]["wiki_derived"]["declared"]}
        added = {a["id"] for a in self.twin["amendments"] if a["action"] == "add_known_limit" and a.get("id")}
        self.assertLessEqual(withdrawn, every_declared | added, "an amendment withdraws a test that was never declared")
        for r in fx["declared"]:
            path = ROOT / r["path"]
            self.assertTrue(has_function(path, base_name(r["id"])), r["id"])
            if r["id"] in withdrawn:
                continue
            self.assertIn(f"`{r['id']}`", known_limits_md, r["id"])
            self.assertTrue(r["declared_reason"].startswith("known limit:"), r["id"])
            self.assertIn(r["suite"], {s["id"] for s in self.inventory["suites"]})
        for test_id in fx["not_declared_resolved"]["ids"]:
            self.assertTrue(has_function(ROOT / "suites/fix2-probes" / test_id.split("::")[0], base_name(test_id)), test_id)
            self.assertTrue(test_id.endswith("]"), test_id)

    def test_authority_ra_declarations(self):
        ra = self.twin["declared_known_limits"]["authority_ra"]
        self.assertEqual(ra["requirement"], "ADD-AUTH-RA")
        self.assertEqual(ra["selector_regex"], "probe_addauthra_")
        self.assertEqual(len(ra["declared"]), 6)
        requirement = next(r for r in load(REQUIREMENTS)["requirements"] if r["id"] == "ADD-AUTH-RA")
        selectors = {s["component"]: s["re"] for s in requirement["selectors"]}
        self.assertEqual(selectors.get(ra["selector_component"]), ra["selector_regex"])
        path = ROOT / "suites/v1-probes/test_authority_ra_probes.py"
        known_limits_md = (ROOT / "suites/v1-probes/KNOWN_LIMITS.md").read_text(encoding="utf-8")
        for r in ra["declared"]:
            name = base_name(r["id"])
            self.assertIn(ra["selector_regex"], name)
            self.assertTrue(has_function(path, name, decorator="known_limit"), f"{name} is not marked as a strict expected failure")
            self.assertIn(f"`{r['id']}`", known_limits_md, r["id"])
        self.assertIn("never counted as a pass", ra["junit_note"])
        self.assertIn("inconclusive", ra["junit_note"])

    def test_wiki_derived_declarations(self):
        # The declared set is the registered set plus the add_known_limit amendments for suites/wiki-derived, less the
        # withdraw_known_limit amendments. It must equal the set the inventory names (still an equality, over the larger set).
        wd = self.twin["declared_known_limits"]["wiki_derived"]
        named = set(self.inventory["wiki"]["known_limit_tests_named"])
        prefix = "suites/wiki-derived/"
        amendments = self.twin["amendments"]
        added = [a for a in amendments if a["action"] == "add_known_limit" and a["id"].startswith(prefix)]
        withdrawn = {a["id"][len(prefix):] for a in amendments if a["action"] == "withdraw_known_limit" and a["id"].startswith(prefix)}
        ids = [r["id"] for r in wd["declared"]] + [a["id"][len(prefix):] for a in added]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertLessEqual(withdrawn, set(ids), "an amendment withdraws a test that was never declared")
        self.assertEqual(set(ids) - withdrawn, named, "the inventory and this page list different known-limit tests: record an amendment")
        for a in added:
            filename, func = a["id"][len(prefix):].split("::")
            self.assertIn("known_limit", func)
            self.assertTrue(has_function(ROOT / "suites/wiki-derived" / filename, func), a["id"])
            m = re.match(r"Suite (W-[IX]), case `(TC-[A-Z0-9]+-\d+)`", a["text"])
            self.assertIsNotNone(m, a["id"])
            self.assertIn(m.group(2), self.cases, a["id"])
            expected = "W-I" if self.cases[m.group(2)]["split"] == "individual-component" else "W-X"
            self.assertEqual(m.group(1), expected, a["id"])
        for r in wd["declared"]:
            self.assertIn("known_limit", base_name(r["id"]))
            self.assertTrue(has_function(ROOT / r["path"], base_name(r["id"])), r["id"])
            self.assertIn(r["case"], self.cases)
            self.assertIn(r["suite"], {"W-I", "W-X"})
            expected = "W-I" if self.cases[r["case"]]["split"] == "individual-component" else "W-X"
            self.assertEqual(r["suite"], expected, r["id"])

    def test_page_lists_every_declared_known_limit(self):
        dk = self.twin["declared_known_limits"]
        ids = ([r["id"] for r in dk["fix2_probes"]["declared"]] + [r["id"] for r in dk["authority_ra"]["declared"]]
               + [r["id"] for r in dk["wiki_derived"]["declared"]])
        self.assertEqual(len(ids), 20)
        section_text = section(self.doc, "## 8. Known limits declared for the run", "## 9. Reporting format")
        for test_id in ids:
            self.assertEqual(section_text.count(f"| `{test_id}` |"), 1, test_id)
        for test_id in dk["fix2_probes"]["not_declared_resolved"]["ids"]:
            self.assertEqual(section_text.count(f"- `{test_id}`"), 1, test_id)
            self.assertNotIn(f"| `{test_id}` |", section_text)

    def test_declared_suites_exist_in_the_inventory(self):
        inventory_ids = {s["id"] for s in self.inventory["suites"]}
        for gate in self.twin["gates"]["categories"]:
            self.assertIn(gate["gate"], {"OCS-1", "OCS-2", "OCS-3"})
        self.assertEqual(self.twin["gates"]["result_columns"],
                         ["PASSING", "PASSING-AS-KNOWN-LIMIT", "SKIPPED-WITH-REASON"])
        for key in ("fix2_probes", "authority_ra"):
            self.assertIn(self.twin["declared_known_limits"][key]["suite"], inventory_ids)


class FrozenAndAmendments(PreregistrationBase):
    def test_the_frozen_part_of_the_page_is_unchanged(self):
        frozen = self.doc.split(MARK)[0]
        self.assertEqual(self.doc.count(MARK), 1)
        self.assertEqual(sha(frozen.encode("utf-8")), self.twin["document_frozen_sha256"],
                         "the registered text was edited: append an amendment instead")

    def test_the_frozen_part_of_the_twin_is_unchanged(self):
        frozen = {k: v for k, v in self.twin.items() if k not in ("amendments", "document_frozen_sha256", "frozen_json_sha256")}
        digest = sha(json.dumps(frozen, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
        self.assertEqual(digest, self.twin["frozen_json_sha256"], "the registered data was edited: append an amendment instead")

    def test_amendments_are_appended_and_agree_with_the_page(self):
        amendments = self.twin["amendments"]
        tail = self.doc.split(MARK)[1]
        headings = re.findall(r"^### Amendment (\d+) \((\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\)$", tail, re.M)
        self.assertEqual(len(headings), len(amendments), "the page and the twin carry different amendments")
        previous = ""
        for n, (a, h) in enumerate(zip(amendments, headings), start=1):
            self.assertEqual(int(h[0]), n)
            self.assertEqual(h[1], a["timestamp"])
            self.assertRegex(a["timestamp"], TIMESTAMP)
            self.assertGreaterEqual(a["timestamp"], previous, "amendments are in time order")
            previous = a["timestamp"]
            self.assertIn(a["action"], AMENDMENT_ACTIONS)
            self.assertTrue(a["reason"].strip())
            self.assertTrue(a["text"].strip())
            self.assertIn(a["text"], tail)
            self.assertIn(a["reason"], tail)
            if a["action"] in ("add_known_limit", "withdraw_known_limit"):
                self.assertTrue(a["id"].strip())

    def test_declared_known_limits_still_exist_unless_withdrawn(self):
        # An amendment may withdraw a declaration (for example when a test is renamed); the original entry stays in the record.
        withdrawn = {a["id"] for a in self.twin["amendments"] if a["action"] == "withdraw_known_limit"}
        dk = self.twin["declared_known_limits"]
        entries = dk["fix2_probes"]["declared"] + dk["authority_ra"]["declared"] + dk["wiki_derived"]["declared"]
        for r in entries:
            if r["id"] in withdrawn:
                continue
            self.assertTrue(has_function(ROOT / r["path"], base_name(r["id"])), f"{r['id']} no longer exists: withdraw it by amendment")


if __name__ == "__main__":
    unittest.main()
