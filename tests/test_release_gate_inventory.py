"""Consistency checks for docs/test-inventory.md and process/release-gate/inventory.json.

Static only: no suite is run and no count that comes from another repository or from a run is re-measured.
"""
import glob
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "process/release-gate/inventory.json"
DOC = ROOT / "docs/test-inventory.md"
APPLICABILITY = ROOT / "scenarios/ai-security-wiki/applicability.json"
WIKI_SUITE = ROOT / "suites/wiki-derived"

CATEGORIES = {"1", "2", "3I", "3X"}
LOCATIONS = {"this_repository", "other_repository", "private_repository", "not_yet_in_repository"}
STATUSES = {"PASS", "ENV", "FAIL", "PARTIAL", "NOT_RUN_HERE", "NOT_RUN", "PLAN"}
COUNT_BASES = {"measured_native", "measured_overlay", "collected_at_main", "collected_at_inventory", "declared",
               "workflow_defined", "tool_reported", "plan"}
REQUIRED = {"id": str, "category": str, "name": str, "repository": (str, type(None)), "location": str, "paths": list,
            "run_command": str, "env_vars": list, "expected_count": (int, type(None)), "count_basis": str, "status": str,
            "state_note": str, "known_limit": bool}
CASE_ID = re.compile(r"TC-[A-Z]\d+-\d+")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class InventoryShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = load(INVENTORY)
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.suites = cls.inv["suites"]

    def test_every_suite_row_validates(self):
        for row in self.suites:
            for key, kind in REQUIRED.items():
                self.assertIn(key, row, f"{row.get('id')} lacks {key}")
                self.assertIsInstance(row[key], kind, f"{row['id']}.{key}")
            self.assertIn(row["category"], CATEGORIES, row["id"])
            self.assertIn(row["location"], LOCATIONS, row["id"])
            self.assertIn(row["status"], STATUSES, row["id"])
            self.assertIn(row["count_basis"], COUNT_BASES, row["id"])
            self.assertTrue(all(isinstance(v, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*", v) for v in row["env_vars"]), row["id"])
            self.assertTrue(all(isinstance(p, str) and not p.startswith("/") and ".." not in p.split("/") for p in row["paths"]), row["id"])
            if row["expected_count"] is None:
                self.assertIn(row["count_basis"], {"workflow_defined", "tool_reported", "plan"}, f"{row['id']}: a missing count needs a reason")
            else:
                self.assertGreaterEqual(row["expected_count"], 0)
            if row["location"] == "private_repository":
                self.assertIsNone(row["repository"], row["id"])
            if row["repository"] is not None:
                self.assertTrue(row["repository"].startswith("cogno-us/"), row["id"])
            if row.get("parent"):
                self.assertIn(row["parent"], {r["id"] for r in self.suites}, row["id"])

    def test_ids_are_unique_and_cover_the_three_categories(self):
        ids = [r["id"] for r in self.suites]
        self.assertEqual(len(ids), len(set(ids)))
        for n in range(1, 16):
            self.assertIn(f"C1-{n:02d}", ids)
        for n in range(1, 18):
            self.assertIn(f"X-{n:02d}", ids)
        self.assertIn("W-I", ids)
        self.assertIn("W-X", ids)
        self.assertEqual({r["category"] for r in self.suites}, CATEGORIES)

    def test_declared_paths_exist_in_this_repository(self):
        for row in self.suites:
            if row["location"] == "this_repository":
                self.assertTrue(row["paths"], f"{row['id']} is in this repository but names no path")
            else:
                if row["location"] == "not_yet_in_repository":
                    self.assertEqual(row["paths"], [], row["id"])
            for p in row["paths"]:
                if row["location"] != "this_repository":
                    continue
                if "*" in p:
                    matches = glob.glob(str(ROOT / p))
                    self.assertTrue(matches, f"{row['id']}: no match for {p}")
                    if "workflow_glob_expected" in row:
                        self.assertEqual(len(matches), row["workflow_glob_expected"], row["id"])
                else:
                    self.assertTrue((ROOT / p).exists(), f"{row['id']}: missing {p}")

    def test_probe_rows_are_marked_as_the_state_before_their_resolution(self):
        rows = {r["id"]: r for r in self.suites}
        for rid in ("X-01", "X-02"):
            self.assertTrue(rows[rid]["being_resolved"], rid)
            self.assertIn("before T4a", rows[rid]["state_basis"], rid)
        blockers = {b["id"]: b for b in self.inv["blockers"]}
        self.assertEqual(len(blockers), 12)
        self.assertEqual(blockers["B-01"]["state"], "being_resolved")
        self.assertEqual(blockers["B-06"]["state"], "being_resolved")

    def test_page_and_inventory_list_the_same_suite_ids(self):
        in_page = set(re.findall(r"^\| ((?:C1-\d\d[a-z]?|X-\d\d|W-[IX])) \|", self.doc, re.M))
        self.assertEqual(in_page, {r["id"] for r in self.suites})

    def test_page_states_the_counts_of_the_inventory(self):
        for row in self.suites:
            if row["expected_count"] is not None and row["category"] in {"1", "2"}:
                match = re.search(rf"^\| {re.escape(row['id'])} \|.*$", self.doc, re.M)
                self.assertIn(f"| {row['expected_count']:,} (", match.group(0), row["id"])
            if row["expected_count"] is None and row["category"] in {"1", "2"}:
                self.assertIn("not counted", re.search(rf"^\| {re.escape(row['id'])} \|.*$", self.doc, re.M).group(0), row["id"])

    def test_wording_stays_neutral_and_the_scope_text_is_present(self):
        text = (self.doc + INVENTORY.read_text(encoding="utf-8")).lower()
        for word in ("certified", "vulnerab", "exploit", "attack"):
            self.assertNotIn(word, text)
        for phrase in ("not independent certification", "not production readiness", "operational trust stays on hold",
                       "configured by cognous", "bounded synthetic profile"):
            self.assertIn(phrase, self.doc.lower())
        scope = self.inv["scope_text"].lower()
        for phrase in ("bounded synthetic profile", "configured by cognous", "not independent certification",
                       "not production readiness", "operational trust stays on hold"):
            self.assertIn(phrase, scope)


class WikiCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = load(INVENTORY)
        cls.app = load(APPLICABILITY)
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.cases = {c["id"]: c for c in cls.app["cases"]}
        cls.wiki = cls.inv["wiki"]
        cls.rows = {r["id"]: r for r in cls.inv["suites"]}

    def test_class_counts_match_applicability_json(self):
        classes = {}
        for case in self.app["cases"]:
            classes[case["classification"]] = classes.get(case["classification"], 0) + 1
        self.assertEqual(self.wiki["upstream_cases"], len(self.app["cases"]))
        self.assertEqual(
            (self.wiki["upstream_cases"], self.wiki["applicable"], self.wiki["partly_covered"], self.wiki["not_applicable"]),
            (656, 20, 45, 591))
        self.assertEqual(classes, {"APPLICABLE": 20, "PARTLY_COVERED": 45, "NOT_APPLICABLE": 591})
        self.assertEqual(self.app["counts"], classes)
        self.assertEqual(self.wiki["wiki_commit"], self.app["catalog_source_commit"])
        for line in ("| APPLICABLE | 20 |", "| PARTLY_COVERED | 45 |", "| NOT_APPLICABLE | 591 |", "| Total | 656 |"):
            self.assertIn(line, self.doc)

    def test_in_scope_split_matches_the_two_wiki_rows(self):
        inscope = [c for c in self.app["cases"] if c["classification"] != "NOT_APPLICABLE"]
        self.assertEqual(self.wiki["in_scope_cases"], len(inscope))
        for rid, split in (("W-I", "individual-component"), ("W-X", "cross-component")):
            mine = [c for c in inscope if c["split"] == split]
            w = self.rows[rid]["wiki"]
            self.assertEqual(w["cases"], len(mine), rid)
            self.assertEqual(w["applicable"], sum(c["classification"] == "APPLICABLE" for c in mine), rid)
            self.assertEqual(w["partly_covered"], sum(c["classification"] == "PARTLY_COVERED" for c in mine), rid)
            self.assertEqual(w["applicable"] + w["partly_covered"], w["cases"], rid)
        self.assertEqual(self.rows["W-I"]["wiki"]["cases"] + self.rows["W-X"]["wiki"]["cases"], len(inscope))
        applicable = [c for c in inscope if c["classification"] == "APPLICABLE"]
        status = [c["existing_implementation"]["status"] for c in applicable]
        self.assertEqual(self.wiki["applicable_existing_partial"], status.count("partial_existing"))
        self.assertEqual(self.wiki["applicable_needs_new"], status.count("needs_new_implementation"))

    def test_every_package_lists_exactly_the_case_ids_found_in_its_file(self):
        files = {p.name for p in WIKI_SUITE.glob("test_*.py")}
        self.assertEqual({Path(p["file"]).name for p in self.inv["wiki_packages"]}, files)
        covered = set()
        for pkg in self.inv["wiki_packages"]:
            path = ROOT / pkg["file"]
            self.assertTrue(path.exists(), pkg["file"])
            found = set(CASE_ID.findall(path.read_text(encoding="utf-8")))
            self.assertEqual(set(pkg["case_ids"]), found, pkg["package"])
            for cid in found:
                self.assertIn(cid, self.cases, cid)
                self.assertNotEqual(self.cases[cid]["classification"], "NOT_APPLICABLE", cid)
            self.assertEqual(set(pkg["cases_individual"]) | set(pkg["cases_cross"]), found)
            for cid in pkg["cases_individual"]:
                self.assertEqual(self.cases[cid]["split"], "individual-component")
            for cid in pkg["cases_cross"]:
                self.assertEqual(self.cases[cid]["split"], "cross-component")
            self.assertEqual(pkg["tests"], pkg["tests_individual"] + pkg["tests_cross"] + pkg["tests_without_case"], pkg["package"])
            covered |= found
        inscope = {c["id"] for c in self.app["cases"] if c["classification"] != "NOT_APPLICABLE"}
        self.assertEqual(set(self.wiki["in_scope_without_wiki_derived_test"]), inscope - covered)
        for rid, split in (("W-I", "individual-component"), ("W-X", "cross-component")):
            have = {c for c in covered if self.cases[c]["split"] == split}
            self.assertEqual(self.rows[rid]["wiki"]["cases_with_wiki_derived_tests"], len(have), rid)

    def test_wiki_test_counts_add_up(self):
        pk = self.inv["wiki_packages"]
        total = sum(p["tests"] for p in pk)
        self.assertEqual(total, self.wiki["wiki_derived_total_tests"])
        self.assertEqual(self.rows["W-I"]["expected_count"], sum(p["tests_individual"] for p in pk))
        self.assertEqual(self.rows["W-X"]["expected_count"], sum(p["tests_cross"] for p in pk))
        self.assertEqual(total, self.rows["W-I"]["expected_count"] + self.rows["W-X"]["expected_count"] + sum(p["tests_without_case"] for p in pk))
        self.assertIn(f"`suites/wiki-derived` holds {total} tests collected at main", self.doc)

    def test_every_wiki_case_is_listed_as_not_run_in_the_catalog(self):
        catalog = load(ROOT / "scenarios/ai-security-wiki/catalog.json")
        entries = catalog["scenarios"]
        self.assertEqual(len(entries), 656)
        self.assertEqual({e.get("status") for e in entries}, {"NOT RUN"})
        for rid in ("W-I", "W-X"):
            self.assertEqual(self.rows[rid]["status"], "NOT_RUN")

    def test_known_limit_tests_named_exist_in_the_suite(self):
        for name in self.wiki["known_limit_tests_named"]:
            fname, func = name.split("::")
            self.assertRegex((WIKI_SUITE / fname).read_text(encoding="utf-8"), rf"(?m)^def {re.escape(func)}\(")
            self.assertIn(f"`{name}`", self.doc)


if __name__ == "__main__":
    unittest.main()
