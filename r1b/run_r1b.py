#!/usr/bin/env python3
"""OCS-254-R1B targeted qualification runner (developer observation; stdlib only).

Subcommands:  run --work DIR --out DIR       fetch exact SHAs, run tests, mutations, write evidence; exit 1 on any FAIL/BLOCKED/SURVIVED
              annotate --out DIR --leg L     print GitHub annotations (chunks < 3500 chars) for leg replay|mutation|exchange
Verdicts: PASS / FAIL / BLOCKED (BLOCKED = a prerequisite or precondition could not be established; never PASS).
Replay runs from the fetched tree with PYTHONPATH=src (no editable install: nothing outside the hash-locked set is installed).
"""
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEX40 = re.compile(r"[0-9a-f]{40}")
CHUNK = 3300


def sh(cmd, cwd=None, env=None, log=None, timeout=900):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if log:
        Path(log).write_text("$ %s\n%s%s\n[rc=%d]\n" % (" ".join(map(str, cmd)), p.stdout, p.stderr, p.returncode))
    return p


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_tuple(t):
    for name, c in t["components"].items():
        for k in ("sha", "tree", "frozen_s3_baseline_sha", "frozen_s3_baseline_tree"):
            v = c.get(k, "")
            if not HEX40.fullmatch(v) or len(set(v)) < 4:
                raise SystemExit("tuple refusal: %s.%s is not a real 40-hex id: %r" % (name, k, v))


def fetch(t, work, out):
    ident, base = [], {}
    for name, c in t["components"].items():
        d = work / name
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        for cmd in (["git", "init", "-q"], ["git", "fetch", "-q", "--depth", "1", "https://github.com/cogno-us/" + c["repo"], c["sha"]],
                    ["git", "checkout", "-q", "--detach", "FETCH_HEAD"]):
            p = sh(cmd, cwd=d)
            if p.returncode:
                return None, "BLOCKED fetch %s: %s" % (name, p.stderr.strip()[:300])
        head = sh(["git", "rev-parse", "HEAD"], cwd=d).stdout.strip()
        tree = sh(["git", "rev-parse", "HEAD^{tree}"], cwd=d).stdout.strip()
        dirty = sh(["git", "status", "--porcelain", "--untracked-files=all", "--ignored"], cwd=d).stdout.strip()
        if head != c["sha"] or tree != c["tree"] or dirty:
            return None, "BLOCKED pin mismatch %s: HEAD %s tree %s dirty=%r" % (name, head, tree, dirty[:100])
        ident.append("%s\t%s\t%s\t%s\tfetched-under-test" % (name, c["repo"], head, tree))
        ident.append("%s\t%s\t%s\t%s\tfrozen-S3-baseline-context-only-not-fetched" % (name, c["repo"], c["frozen_s3_baseline_sha"], c["frozen_s3_baseline_tree"]))
        base[name] = d
    (out / "components-identity.tsv").write_text("name\trepo\tcommit\ttree\trole\n" + "\n".join(ident) + "\n")
    return base, None


def pytest(tree, extra, junit, log, replay):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
    env.pop("PYTHONPATH", None)
    if replay:
        env["PYTHONPATH"] = str(tree / "src")
    base = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rA", *extra]
    col = sh(base + ["--collect-only"], cwd=tree, env=env, log=str(log) + ".collect")
    ids = [l.split("::", 1)[1] for l in col.stdout.splitlines() if "::" in l]
    run = sh(base + ["--junitxml", str(junit)], cwd=tree, env=env, log=log)
    return ids, run.returncode


def parse_junit(junit):
    try:
        root = ET.parse(junit).getroot()
    except (OSError, ET.ParseError):
        return None
    res = []
    for tc in root.iter("testcase"):
        kids = {k.tag: k for k in tc}
        if "failure" in kids or "error" in kids:
            k = kids.get("failure", kids.get("error"))
            res.append((tc.get("name"), "error" if "error" in kids and "failure" not in kids else "failed",
                        ((k.get("message") or k.text or "").strip().splitlines() or [""])[0][:200]))
        elif "skipped" in kids:
            res.append((tc.get("name"), "skipped", (kids["skipped"].get("message") or "")[:200]))
        else:
            res.append((tc.get("name"), "passed", ""))
    return res


def fn_of(name):
    return name.split("[", 1)[0]


def r1_label(name):
    m = re.match(r"test_(R1_[A-Z]\d+[a-z]?)_", name)
    return m.group(1).replace("_", "-") if m else "R1-AUX"


def prov_key(fn):
    m = re.match(r"(test_R1_[A-Z]\d+[a-z]?)_", fn)
    return m.group(1) if m else fn


def source_blocks(path):
    blocks, cur, name = {}, [], None
    for line in Path(path).read_text().splitlines():
        m = re.match(r"def (test_\w+)\(", line)
        if m:
            if name:
                blocks[name] = "\n".join(cur)
            name, cur = m.group(1), []
        if name:
            cur.append(line)
    if name:
        blocks[name] = "\n".join(cur)
    return blocks


def classify(ids, results, expected_n, blocks, rev, evid, replay):
    """collected==executed, zero skips; per-test PASS/FAIL/BLOCKED rows (7 fields)."""
    problems = []
    if results is None:
        return [], ["junit missing or unreadable"]
    names = [r[0] for r in results]
    if len(ids) != expected_n:
        problems.append("collected %d != expected %d" % (len(ids), expected_n))
    if sorted(ids) != sorted(names):
        problems.append("collected ids != executed ids (%d vs %d)" % (len(ids), len(names)))
    rows = []
    for name, outcome, msg in results:
        fn = fn_of(name)
        src = blocks.get(fn, "")
        codes = sorted(set(re.findall(r"effective_configuration_(?:expected_(?:missing|malformed|mismatch|unsupported_profile)|record_missing)|schema_violation|candidate source identity mismatch[:\w. ]*|refs/replace", src)))
        declared = "declared in test: " + (", ".join(codes) if codes else "see test source")
        if "assert_trusted_marker" in src:
            declared = "accepted as caller_trusted_configuration_match (registry_authenticated False)" + ("; " + declared if codes else "")
        v = {"passed": "PASS", "failed": "FAIL"}.get(outcome, "BLOCKED")
        if problems and v == "PASS":
            v = "BLOCKED"
        obs = {"passed": "test passed", "failed": "test failed", "error": "test errored", "skipped": "test skipped"}[outcome]
        rows.append({"test_id": ("%s %s" % (r1_label(fn), name)) if replay else name,
                     "expected_behaviour": re.sub(r"^test_(R1_[A-Z]\d+[a-z]?_)?", "", fn).replace("_", " "),
                     "observed_behaviour": obs + (": " + msg if msg else ""),
                     "first_refusal_or_failure_boundary": (msg or declared) if v != "PASS" else declared,
                     "component_revision": rev, "verdict": v, "evidence_ref": "%s#%s" % (evid, name)})
    return rows, problems


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test_id", "expected_behaviour", "observed_behaviour", "first_refusal_or_failure_boundary", "component_revision", "verdict", "evidence_ref"])
        w.writeheader()
        w.writerows(rows)


def mutate(t, m, trees, work, out, tests_file, sel, replay):
    mid = m["id"]
    mdir = out / "mutation" / mid
    mdir.mkdir(parents=True)
    row = {"mutant": mid, "weakness": m["weakness"], "patch_sha256": sha256(HERE.parent / m["patch"]), "must_fail": m["must_fail"], "verdict": "BLOCKED", "detail": ""}
    copy = work / ("mutant-" + mid)
    shutil.rmtree(copy, ignore_errors=True)
    shutil.copytree(trees[m["component"]], copy, symlinks=True)
    patch = (HERE.parent / m["patch"]).resolve()
    chk = sh(["git", "apply", "--check", "--verbose", str(patch)], cwd=copy, log=mdir / "apply-check.log")
    if chk.returncode:
        row["detail"] = "git apply --check failed"
        return row
    stat = sh(["git", "apply", "--numstat", str(patch)], cwd=copy).stdout.strip().splitlines()
    sh(["git", "apply", str(patch)], cwd=copy, log=mdir / "apply.log")
    changed = sh(["git", "diff", "--numstat"], cwd=copy).stdout.strip().splitlines()
    if len(stat) != 1 or changed != stat or sh(["git", "diff", "--quiet"], cwd=copy).returncode == 0:
        row["detail"] = "mutant tree equals fixed tree or patch is not one file/one hunk: %r" % (changed,)
        return row
    (mdir / "mutant.diff").write_text(sh(["git", "diff"], cwd=copy).stdout)
    ids, _ = pytest(copy, sel, mdir / "junit.xml", mdir / "pytest.log", replay)
    res = parse_junit(mdir / "junit.xml")
    if res is None or not res:
        row["detail"] = "mutant run produced no junit"
        return row
    byfn = {}
    for name, outcome, msg in res:
        byfn.setdefault(fn_of(name), []).append(outcome)
    missing = [f for f in m["must_fail"] if f not in byfn]
    if missing:
        row["detail"] = "required tests absent from the run: %s" % missing
        return row
    mut_failed = {f: byfn[f].count("failed") + byfn[f].count("error") for f in m["must_fail"]}
    others = sorted({fn_of(n) for n, o, _ in res if o in ("failed", "error")} - set(m["must_fail"]))
    row["observed_failing_other_tests"] = others
    row["mutant_counts"] = {k: len(v) for k, v in byfn.items() if k in m["must_fail"]}
    row["mutant_failures_in_required"] = mut_failed
    survivors = [f for f in m["must_fail"] if mut_failed[f] != len(byfn[f])]
    if survivors:
        row["verdict"], row["detail"] = "MUTATION_SURVIVED", "required tests that still passed (fully or partly) on the mutant: %s" % survivors
    else:
        row["verdict"], row["detail"] = "MUTATION_DETECTED", "all required tests failed on the mutant; %d other test(s) also failed" % len(others)
    return row


def restored_check(t, trees, rows, out, sel_replay, sel_exch):
    """Re-run the must-fail tests on the (untouched, restored) fixed trees: they must PASS."""
    for comp, sel_base, replay in (("replay", sel_replay, True), ("exchange", sel_exch, False)):
        mine = [r for r in rows if r["component"] == comp]
        if not mine:
            continue
        funcs = sorted({f for r in mine for f in r["must_fail"]})
        d = out / "mutation" / ("restored-" + comp)
        d.mkdir(parents=True)
        tree = trees[comp]
        dirty = sh(["git", "status", "--porcelain", "--untracked-files=all"], cwd=tree).stdout.strip()
        extra = sel_base + ["-k", " or ".join(funcs)]
        pytest(tree, extra, d / "junit.xml", d / "pytest.log", replay)
        res = parse_junit(d / "junit.xml") or []
        ok = bool(res) and all(o == "passed" for _, o, _ in res) and not dirty and {fn_of(n) for n, _, _ in res} >= set(funcs)
        for r in mine:
            r["restored_fixed_tree"] = "PASS" if ok else "BLOCKED"
            if not ok and r["verdict"] == "MUTATION_DETECTED":
                r["verdict"], r["detail"] = "BLOCKED", "restored fixed tree did not pass the same tests (dirty=%r)" % dirty[:80]


def cmd_run(a):
    out, work = Path(a.out).resolve(), Path(a.work).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    tpath = HERE / "tuple.json"
    t = json.loads(tpath.read_text())
    shutil.copy(tpath, out / "tuple.json")
    (out / "tuple.json.sha256").write_text("%s  tuple.json\n" % sha256(tpath))
    print("tuple.json sha256", sha256(tpath))
    status = {"verdicts": {"PASS": 0, "FAIL": 0, "BLOCKED": 0}, "mutation": {}, "problems": []}
    check_tuple(t)
    trees, err = fetch(t, work, out)
    if err:
        status["problems"].append(err)
        finish(out, status, [], [], [])
        return 1
    env_txt = "python %s\n%s\n" % (sys.version, sh(["git", "--version"]).stdout.strip())
    (out / "env").mkdir(exist_ok=True)
    (out / "env" / "python-git.txt").write_text(env_txt)
    (out / "env" / "pip-freeze.txt").write_text(sh([sys.executable, "-m", "pip", "freeze"]).stdout)
    prov = json.loads((HERE / "provenance.json").read_text())

    legs = {}
    # Replay leg
    rt = trees["replay"]
    rfile = t["replay"]["test_file"]
    (out / "replay").mkdir(exist_ok=True)
    ids, rc = pytest(rt, [rfile], out / "replay" / "junit.xml", out / "replay" / "pytest.log", True)
    rows, probs = classify(ids, parse_junit(out / "replay" / "junit.xml"), t["replay"]["expected_tests"], source_blocks(rt / rfile),
                           t["components"]["replay"]["sha"], "replay/junit.xml", True)
    status["problems"] += ["replay: " + p for p in probs]
    prow = []
    for r in rows:
        fn = fn_of(r["test_id"].split(" ", 1)[1])
        e = prov["by_function"].get(prov_key(fn))
        if not e:
            r["verdict"] = "BLOCKED"
            status["problems"].append("replay: no provenance classification for " + fn)
            e = {"class": "UNCLASSIFIED", "note": ""}
        prow.append({"test_id": r["test_id"], "expected_digest_provenance": e["class"], "note": e["note"], "verdict": r["verdict"]})
    legs["replay"] = rows
    write_csv(out / "verdicts-replay.csv", rows)
    with open(out / "provenance.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test_id", "expected_digest_provenance", "note", "verdict"])
        w.writeheader()
        w.writerows(prow)

    # Exchange leg
    et = trees["exchange"]
    efile = t["exchange"]["test_file"]
    esel = [efile, "-k", " or ".join(t["exchange"]["functions"])]
    (out / "exchange").mkdir(exist_ok=True)
    ids, rc = pytest(et, esel, out / "exchange" / "junit.xml", out / "exchange" / "pytest.log", False)
    rows, probs = classify(ids, parse_junit(out / "exchange" / "junit.xml"), t["exchange"]["expected_tests"], source_blocks(et / efile),
                           t["components"]["exchange"]["sha"], "exchange/junit.xml", False)
    status["problems"] += ["exchange: " + p for p in probs]
    legs["exchange"] = rows
    write_csv(out / "verdicts-exchange.csv", rows)

    # Mutation leg (only meaningful if the fixed legs ran cleanly enough to compare; each mutant still reports on its own)
    mrows = []
    for m in t["mutants"]:
        c = m["component"]
        r = mutate(t, m, trees, work, out, None, [rfile] if c == "replay" else esel, c == "replay")
        r["component"] = c
        mrows.append(r)
    restored_check(t, trees, mrows, out, [rfile], esel)
    (out / "mutation-results.json").write_text(json.dumps(mrows, indent=1))
    finish(out, status, legs, mrows, prow)
    return 0 if status["ok"] else 1


def finish(out, status, legs, mrows, prow):
    for rows in (legs.values() if isinstance(legs, dict) else []):
        for r in rows:
            status["verdicts"][r["verdict"]] += 1
    per_leg = {k: {v: sum(1 for r in rows if r["verdict"] == v) for v in ("PASS", "FAIL", "BLOCKED")} for k, rows in (legs.items() if isinstance(legs, dict) else [])}
    for r in mrows:
        status["mutation"][r["mutant"]] = r["verdict"]
    status["per_leg"] = per_leg
    status["ok"] = (not status["problems"] and bool(per_leg) and status["verdicts"]["FAIL"] == 0 and status["verdicts"]["BLOCKED"] == 0
                    and bool(mrows) and all(r["verdict"] == "MUTATION_DETECTED" for r in mrows))
    (out / "status.json").write_text(json.dumps(status, indent=1))
    L = ["# Security R1B targeted (developer observation)", "",
         "Scope: modified boundaries only (Replay PR #82 expected-digest match, Exchange PR #64 replace-ref hardening). Developer observation: not Q7, not certification, no release or production hold changes.",
         "Success of any Replay case is a CALLER-TRUSTED CONFIGURATION MATCH only, never REGISTRY_AUTHENTICATED; Replay cannot infer where the expected digest came from.", "",
         "Overall: **%s**" % ("PASS" if status["ok"] else "FAIL/BLOCKED"), "", "| leg | PASS | FAIL | BLOCKED |", "|---|---|---|---|"]
    for k, v in per_leg.items():
        L.append("| %s | %d | %d | %d |" % (k, v["PASS"], v["FAIL"], v["BLOCKED"]))
    L += ["", "| mutant | verdict | restored fixed tree | detail |", "|---|---|---|---|"]
    for r in mrows:
        L.append("| %s | %s | %s | %s |" % (r["mutant"], r["verdict"], r.get("restored_fixed_tree", "-"), r["detail"]))
    if status["problems"]:
        L += ["", "Problems:"] + ["- " + p for p in status["problems"]]
    (out / "summary.md").write_text("\n".join(L) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("\n".join(L) + "\n")
    print("\n".join(L))
    sums = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            sums.append("%s  %s" % (sha256(p), p.relative_to(out).as_posix()))
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")


def esc(s):
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def cmd_annotate(a):
    out = Path(a.out)
    lines = []
    if a.leg in ("replay", "exchange"):
        rows = list(csv.DictReader(open(out / ("verdicts-%s.csv" % a.leg))))
        prov = {}
        if a.leg == "replay" and (out / "provenance.csv").exists():
            prov = {r["test_id"]: r["expected_digest_provenance"] for r in csv.DictReader(open(out / "provenance.csv"))}
        for r in rows:
            label, _, nm = r["test_id"].partition(" ") if a.leg == "replay" else ("", "", r["test_id"])
            par = nm[nm.find("["):][:48] if "[" in nm else ""
            short = (label if a.leg == "replay" else nm.split("[")[0][:62]) + par
            lines.append("%s %s | prov=%s | %s" % (r["verdict"], short, prov.get(r["test_id"], "-"), r["first_refusal_or_failure_boundary"][:70]) if prov
                         else "%s %s | %s" % (r["verdict"], short, r["first_refusal_or_failure_boundary"][:70]))
        bad = [l for l in lines if not l.startswith("PASS")]
    else:
        for r in json.load(open(out / "mutation-results.json")):
            lines.append("%s %s restored=%s | %s | patch %s | other failing=%s" % (r["verdict"], r["mutant"], r.get("restored_fixed_tree", "-"), r["weakness"],
                                                                                  r["patch_sha256"][:12], len(r.get("observed_failing_other_tests", []))))
        bad = [l for l in lines if not l.startswith("MUTATION_DETECTED")]
    chunks, cur = [], ""
    for l in lines:
        if len(cur) + len(l) + 1 > CHUNK:
            chunks.append(cur)
            cur = ""
        cur += l + "\n"
    if cur:
        chunks.append(cur)
    n = len(chunks)
    for i, c in enumerate(chunks, 1):
        print("::notice title=R1B %s verdicts %d/%d (%d lines, %d not-PASS)::%s" % (a.leg, i, n, len(lines), len(bad), esc(c.rstrip())))
    for l in bad[:9]:
        print("::error title=R1B %s not PASS::%s" % (a.leg, esc(l)))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--work", required=True); r.add_argument("--out", required=True)
    n = sp.add_parser("annotate"); n.add_argument("--out", required=True); n.add_argument("--leg", required=True, choices=["replay", "mutation", "exchange"])
    a = ap.parse_args()
    sys.exit(cmd_run(a) if a.cmd == "run" else cmd_annotate(a))
