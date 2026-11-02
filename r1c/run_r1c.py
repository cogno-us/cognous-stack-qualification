#!/usr/bin/env python3
"""OCS-254-R1C targeted qualification runner (developer observation; stdlib only). Pattern: r1b/run_r1b.py (not imported; r1b is frozen evidence).

  run --work DIR --out DIR      fetch exact SHAs (HEAD + tree verified), run the legs in r1c/tuple.json, run the mutants, write evidence; exit 1 on any FAIL/BLOCKED/SURVIVED
  annotate --out DIR --legs L   print GitHub annotations (chunks < 3500 chars); L = comma list of leg ids, MUT for mutants
Verdicts: PASS / FAIL / BLOCKED (a prerequisite or precondition could not be established; never PASS) / SKIP_COVERED (skipped here, the same node PASSed in the leg
named by covered_by) / SKIP_DOCUMENTED (skip reason allow-listed in the leg). Only FAIL and BLOCKED fail the job; skips are counted and listed, never counted as PASS.
"""
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEX40 = re.compile(r"[0-9a-f]{40}")
TUPLE_FOR_LEGS = {}  # the tuple being run (set by cmd_run; read by realsource legs)
CHUNK = 3300
CODES = re.compile(r"effective_configuration_[a-z_]+|candidate source identity mismatch[:\w. ]*|refs/replace|exact qualified Replay revision|is not the pinned revision|[a-z_]+_(?:refused|mismatch|missing|malformed)")


def sh(cmd, cwd=None, env=None, log=None, timeout=1500):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if log:
        Path(log).write_text("$ %s\n%s%s\n[rc=%d]\n" % (" ".join(map(str, cmd)), p.stdout, p.stderr, p.returncode))
    return p


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_tuple(t):
    ids = [(n, k, c.get(k, "")) for n, c in t["components"].items() for k in ("sha", "tree")] + [("superseded", "sha", t["superseded_replay_pin"])]
    for n, k, v in ids:
        if not HEX40.fullmatch(v) or len(set(v)) < 4:
            raise SystemExit("tuple refusal: %s.%s is not a real 40-hex id: %r" % (n, k, v))


def fetch(t, work, out):
    dirs, errs, ident = {}, {}, []
    for name, c in t["components"].items():
        d = work / name
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        url = "https://github.com/cogno-us/" + c["repo"]
        fetch_cmd = ["git", "fetch", "-q", url, c["sha"]] if c.get("full_history") else ["git", "fetch", "-q", "--depth", "1", url, c["sha"]]
        why = None
        for cmd in (["git", "init", "-q"], fetch_cmd, ["git", "checkout", "-q", "--detach", "FETCH_HEAD"]):
            p = sh(cmd, cwd=d)
            if p.returncode:
                why = "BLOCKED fetch %s: %s" % (name, p.stderr.strip()[:300])
                break
        if not why:
            head = sh(["git", "rev-parse", "HEAD"], cwd=d).stdout.strip()
            tree = sh(["git", "rev-parse", "HEAD^{tree}"], cwd=d).stdout.strip()
            dirty = sh(["git", "status", "--porcelain", "--untracked-files=all", "--ignored"], cwd=d).stdout.strip()
            if head != c["sha"] or tree != c["tree"] or dirty:
                why = "BLOCKED pin mismatch %s: HEAD %s tree %s dirty=%r" % (name, head, tree, dirty[:100])
            ident.append("%s\t%s\t%s\t%s\t%s" % (name, c["repo"], head, tree, c["role"]))
        if why:
            errs[name] = why
        else:
            dirs[name] = d
    (out / "components-identity.tsv").write_text("name\trepo\tcommit\ttree\trole\n" + "\n".join(ident) + "\n")
    return dirs, errs


def parse_junit(junit):
    try:
        root = ET.parse(junit).getroot()
    except (OSError, ET.ParseError):
        return None
    res = []
    for tc in root.iter("testcase"):
        kids = {k.tag: k for k in tc}
        cls, name = tc.get("classname") or "", tc.get("name")
        if "failure" in kids or "error" in kids:
            k = kids.get("failure", kids.get("error"))
            res.append((cls, name, "failed", ((k.get("message") or k.text or "").strip().splitlines() or [""])[0][:200]))
        elif "skipped" in kids:
            res.append((cls, name, "skipped", (kids["skipped"].get("message") or "")[:300]))
        else:
            res.append((cls, name, "passed", ""))
    return res


def fn_of(name):
    return name.split("[", 1)[0]


def pytest(cwd, args, env_extra, junit, log):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH",) and not k.startswith(("ODES_", "AGEP_", "CP_SRC", "REPLAY_SRC"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", **env_extra)
    base = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rs", *args]
    col = sh(base + ["--collect-only"], cwd=cwd, env=env, log=str(log) + ".collect")
    ids = [l.split("::", 1)[1] for l in col.stdout.splitlines() if "::" in l]
    run = sh(base + ["--junitxml", str(junit)], cwd=cwd, env=env, log=log)
    return ids, run.returncode


def src_block(cwd, cls, fn):
    p = Path(cwd) / (cls.replace(".", "/") + ".py")
    try:
        txt = p.read_text()
    except OSError:
        return ""
    m = re.search(r"^def %s\(.*?(?=^def |^@pytest|\Z)" % re.escape(fn), txt, re.S | re.M)
    return m.group(0) if m else ""


def run_leg(leg, dirs, d, rev):
    """Execute one pytest leg; returns (rows, problems, results). Rows are the 7-field verdict records (skip verdicts resolved later)."""
    d.mkdir(parents=True, exist_ok=True)
    sub = lambda s: re.sub(r"\{(\w+)\}", lambda m: str(dirs[m.group(1)]), s)
    cwd = sub(leg["cwd"])
    pth = None
    if leg.get("pth"):  # python -I subprocesses ignore PYTHONPATH: a .pth file (same effect as the editable install in the consumer's CI) makes the source importable; removed after the leg
        import sysconfig
        pth = Path(sysconfig.get_paths()["purelib"]) / ("r1c-%s.pth" % leg["id"])
        pth.write_text("\n".join(sub(x) for x in leg["pth"]) + "\n")
    try:
        if leg.get("type") == "realsource":  # real-checkout verification cases (r1c/legC/realsource.py); writes the same junit.xml shape
            import importlib.util
            spec = importlib.util.spec_from_file_location("r1c_realsource", HERE / "legC" / "realsource.py")
            rs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rs)
            ids, rc = rs.execute(leg, dirs, d, TUPLE_FOR_LEGS, dirs["work"]), 0
        else:
            ids, rc = pytest(cwd, [sub(a) for a in leg["args"]], {k: sub(v) for k, v in leg.get("env", {}).items()}, d / "junit.xml", d / "pytest.log")
    finally:
        if pth:
            pth.unlink()
    res = parse_junit(d / "junit.xml")
    probs = []
    if res is None:
        return [], ["%s: junit missing or unreadable" % leg["id"]], []
    if leg.get("expected") is not None and len(ids) != leg["expected"]:
        probs.append("%s: collected %d != expected %d" % (leg["id"], len(ids), leg["expected"]))
    if sorted(i.split("::")[-1] for i in ids) != sorted(r[1] for r in res):
        probs.append("%s: collected ids != executed ids (%d vs %d)" % (leg["id"], len(ids), len(res)))
    rows = []
    for cls, name, outcome, msg in res:
        fn = fn_of(name)
        codes = sorted(set(CODES.findall(src_block(cwd, cls, fn))))[:4]
        rows.append({"test_id": name, "expected_behaviour": re.sub(r"^test_(R1_[A-Z]\d+[a-z]?_)?", "", fn).replace("_", " "),
                     "observed_behaviour": {"passed": "test passed", "failed": "test failed or errored", "skipped": "test skipped"}[outcome] + (": " + msg if msg else ""),
                     "first_refusal_or_failure_boundary": msg if outcome == "failed" and msg else ("declared in test: " + ", ".join(codes) if codes else "see test source"),
                     "component_revision": rev, "verdict": {"passed": "PASS", "failed": "FAIL"}.get(outcome, "SKIP?"), "evidence_ref": "%s/junit.xml#%s::%s" % (leg["id"], cls, name),
                     "_cls": cls, "_msg": msg})
    return rows, probs, res


def resolve_skips(leg, rows, passed_in):
    for r in rows:
        if r["verdict"] != "SKIP?":
            continue
        if (r["_cls"], r["test_id"]) in passed_in.get(leg.get("covered_by"), set()):
            r["verdict"] = "SKIP_COVERED"
        elif any(re.search(p, r["_msg"]) for p in leg.get("skip_ok", [])):
            r["verdict"] = "SKIP_DOCUMENTED"
        else:
            r["verdict"] = "BLOCKED"


def pin_row(leg, dirs, t):
    p = leg["pin"]
    m = re.search(p["regex"], (dirs[leg["component"]] / p["file"]).read_text(), re.M)
    got, want = (m.group(1) if m else None), t["components"][p["equals"]]["sha"]
    return {"test_id": "pin-%s" % leg["id"], "expected_behaviour": "consumer CUR Replay pin constant equals the Replay merge SHA under test",
            "observed_behaviour": "pin %s" % got, "first_refusal_or_failure_boundary": "%s (regex on the candidate source)" % p["file"],
            "component_revision": t["components"][leg["component"]]["sha"], "verdict": "PASS" if got == want else "FAIL", "evidence_ref": "%s/%s" % (leg["id"], p["file"])}


FIELDS = ["test_id", "expected_behaviour", "observed_behaviour", "first_refusal_or_failure_boundary", "component_revision", "verdict", "evidence_ref"]


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def mutate(t, m, leg, dirs, work, out, main_rows):
    mdir = out / "mutation" / m["id"]
    mdir.mkdir(parents=True)
    patch = (HERE.parent / m["patch"]).resolve()
    row = {"mutant": m["id"], "leg": m["leg"], "weakness": m["weakness"], "patch_sha256": sha256(patch), "must_fail": m["must_fail"], "verdict": "BLOCKED", "detail": ""}
    if m["component"] not in dirs or any(n not in dirs for n in leg["needs"]):
        row["detail"] = "prerequisite component unavailable"
        return row
    copy = work / ("mutant-" + m["id"])
    shutil.rmtree(copy, ignore_errors=True)
    shutil.copytree(dirs[m["component"]], copy, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
    if sh(["git", "apply", "--check", "--verbose", str(patch)], cwd=copy, log=mdir / "apply-check.log").returncode:
        row["detail"] = "git apply --check failed"
        return row
    stat = sh(["git", "apply", "--numstat", str(patch)], cwd=copy).stdout.strip().splitlines()
    sh(["git", "apply", str(patch)], cwd=copy, log=mdir / "apply.log")
    changed = sh(["git", "diff", "--numstat"], cwd=copy).stdout.strip().splitlines()
    if len(stat) != 1 or changed != stat:
        row["detail"] = "patch is not exactly one file (or did not change the tree): %r" % (changed,)
        return row
    (mdir / "mutant.diff").write_text(sh(["git", "diff"], cwd=copy).stdout)
    mrows, probs, res = run_leg(leg, dict(dirs, **{m["component"]: copy}), mdir, "mutant")
    if not res:
        row["detail"] = "mutant run produced no junit"
        return row
    outcome = {}
    for _, name, o, _ in res:
        outcome.setdefault(name, []).append(o)
    sel = {req: [n for n in outcome if n == req or fn_of(n) == req] for req in m["must_fail"]}
    absent = [r for r, ns in sel.items() if not ns]
    if absent:
        row["detail"] = "required tests absent from the mutant run: %s" % absent
        return row
    fixed = [r for r in main_rows if any(r["test_id"] in ns for ns in sel.values())]
    fixed_ok = bool(fixed) and all(r["verdict"] == "PASS" for r in fixed)
    survivors = [n for ns in sel.values() for n in ns if outcome[n] != ["failed"] * len(outcome[n])]
    row["fixed_tree_same_tests"] = "PASS" if fixed_ok else "NOT_PASS"
    row["other_failing_tests"] = len({n for n, o in outcome.items() if "failed" in o} - {n for ns in sel.values() for n in ns})
    if not fixed_ok:
        row["detail"] = "the same tests did not all pass on the fixed tree"
    elif survivors:
        row["verdict"], row["detail"] = "MUTATION_SURVIVED", "still passing on the mutant: %s" % survivors[:4]
    else:
        row["verdict"], row["detail"] = "MUTATION_DETECTED", "all required tests failed on the mutant (%d other failing)" % row["other_failing_tests"]
    return row


def cmd_run(a):
    out, work = Path(a.out).resolve(), Path(a.work).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    tpath = Path(a.tuple).resolve() if a.tuple else HERE / "tuple.json"  # default unchanged; --tuple selects e.g. r1c/tuple-final.json
    t = json.loads(tpath.read_text())
    if a.legs:  # rerun a subset (e.g. after rebinding the Exchange): legs and the mutants attached to them; the full tuple file is still recorded
        sel = a.legs.split(",")
        unknown = [x for x in sel if x not in {l["id"] for l in t["legs"]}]
        if unknown:
            raise SystemExit("unknown leg ids: %s" % unknown)
        t["legs"] = [l for l in t["legs"] if l["id"] in sel]
        t["mutants"] = [m for m in t["mutants"] if m["leg"] in sel]
    TUPLE_FOR_LEGS.update(t)
    shutil.copy(tpath, out / tpath.name)
    (out / (tpath.name + ".sha256")).write_text("%s  %s\n" % (sha256(tpath), tpath.name))
    print(tpath.name, "sha256", sha256(tpath))
    check_tuple(t)
    status = {"problems": [], "legs": {}, "mutation": {}}
    dirs, errs = fetch(t, work, out)
    status["problems"] += list(errs.values())
    dirs.update(work=work, r1c=HERE)
    (out / "env").mkdir(exist_ok=True)
    (out / "env" / "python-git.txt").write_text("python %s\n%s\n" % (sys.version, sh(["git", "--version"]).stdout.strip()))
    (out / "env" / "pip-freeze.txt").write_text(sh([sys.executable, "-m", "pip", "freeze"]).stdout)
    legs = {l["id"]: l for l in t["legs"]}
    rows_by, passed_in = {}, {}
    for leg in t["legs"]:
        lid, rows = leg["id"], []
        if leg.get("type") == "extract":
            for n in leg["names"]:
                src = [r for r in rows_by.get(leg["from"], []) if r["test_id"] == n]
                rows.append(dict(src[0], test_id=n, evidence_ref="%s (extracted from leg %s)" % (src[0]["evidence_ref"], leg["from"])) if src else
                            {"test_id": n, "expected_behaviour": "", "observed_behaviour": "not found in leg " + leg["from"], "first_refusal_or_failure_boundary": "BLOCKED",
                             "component_revision": "", "verdict": "BLOCKED", "evidence_ref": leg["from"]})
        else:
            missing = [n for n in leg["needs"] if n not in dirs]
            if missing:
                why = "; ".join(errs.get(n, "unavailable") for n in missing)
                rows = [{"test_id": "leg-" + lid, "expected_behaviour": leg["title"], "observed_behaviour": "not executed", "first_refusal_or_failure_boundary": why[:300],
                         "component_revision": "", "verdict": "BLOCKED", "evidence_ref": lid}]
            else:
                rev = t["components"][leg["component"]]["sha"]
                rows, probs, _ = run_leg(leg, dirs, out / lid, rev)
                status["problems"] += probs
                if probs:
                    for r in rows:
                        if r["verdict"] == "PASS":
                            r["verdict"] = "BLOCKED"
                if "pin" in leg:
                    rows.append(pin_row(leg, dirs, t))
                passed_in[lid] = {(r["_cls"], r["test_id"]) for r in rows if r["verdict"] == "PASS" and "_cls" in r}
                resolve_skips(leg, rows, passed_in)
        rows_by[lid] = rows
        write_csv(out / ("verdicts-%s.csv" % lid), rows)
        status["legs"][lid] = {v: sum(1 for r in rows if r["verdict"] == v) for v in ("PASS", "FAIL", "BLOCKED", "SKIP_COVERED", "SKIP_DOCUMENTED")}
    mrows = []
    for m in t["mutants"]:
        mrows.append(mutate(t, m, legs[m["leg"]], dirs, work, out, rows_by.get(m["leg"], [])))
    (out / "mutation-results.json").write_text(json.dumps(mrows, indent=1))
    for comp, d in dirs.items():
        if comp in t["components"] and sh(["git", "status", "--porcelain", "--untracked-files=all"], cwd=d).stdout.strip():
            status["problems"].append("component tree %s is dirty after the run" % comp)
    return finish(out, t, status, mrows)


def finish(out, t, status, mrows):
    for r in mrows:
        status["mutation"][r["mutant"]] = r["verdict"]
    bad = sum(v["FAIL"] + v["BLOCKED"] for v in status["legs"].values())
    status["ok"] = (not status["problems"] and len(status["legs"]) == len(t["legs"]) and bad == 0 and len(mrows) == len(t["mutants"])
                    and all(r["verdict"] == "MUTATION_DETECTED" for r in mrows))
    (out / "status.json").write_text(json.dumps(status, indent=1))
    rep = t.get("report", {})
    L = [rep.get("title", "# Security R1C targeted (developer observation on CANDIDATE heads)"), "",
         rep.get("scope", "Scope: affected boundaries only. ODES #143 and Pack #66 are candidate PR heads, not merge SHAs; rebinding to merge SHAs is a follow-up edit of r1c/tuple.json. Not Q7, not certification, no release claim."),
         "A Replay trusted match is a CALLER-TRUSTED CONFIGURATION MATCH only, never Registry authentication; structural-only mode stays UNQUALIFIED.", "",
         "Overall: **%s**" % ("PASS" if status["ok"] else "FAIL/BLOCKED"), "", "| leg | PASS | FAIL | BLOCKED | SKIP_COVERED | SKIP_DOCUMENTED |", "|---|---|---|---|---|---|"]
    for k, v in status["legs"].items():
        L.append("| %s | %d | %d | %d | %d | %d |" % (k, v["PASS"], v["FAIL"], v["BLOCKED"], v["SKIP_COVERED"], v["SKIP_DOCUMENTED"]))
    L += ["", "| mutant | verdict | fixed tree same tests | detail |", "|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |" % (r["mutant"], r["verdict"], r.get("fixed_tree_same_tests", "-"), r["detail"]) for r in mrows]
    if status["problems"]:
        L += ["", "Problems:"] + ["- " + p for p in status["problems"]]
    (out / "summary.md").write_text("\n".join(L) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("\n".join(L) + "\n")
    print("\n".join(L))
    sums = ["%s  %s" % (sha256(p), p.relative_to(out).as_posix()) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"]
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return 0 if status["ok"] else 1


def esc(s):
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


TAG = os.environ.get("R1C_TAG", "R1C")


def emit(title, lines, bad):
    chunks, cur = [], ""
    for l in lines:
        if len(cur) + len(l) + 1 > CHUNK:
            chunks.append(cur)
            cur = ""
        cur += l + "\n"
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks, 1):
        print("::notice title=%s %s %d/%d (%d lines, %d not-PASS)::%s" % (TAG, title, i, len(chunks), len(lines), len(bad), esc(c.rstrip())))
    for l in bad[:4]:
        print("::error title=%s %s not PASS::%s" % (TAG, title, esc(l)))


def cmd_annotate(a):
    out = Path(a.out)
    for leg in a.legs.split(","):
        if leg == "MUT":
            lines = ["%s %s [%s] fixed=%s | %s | patch %s | other failing=%s" % (r["verdict"], r["mutant"], r["leg"], r.get("fixed_tree_same_tests", "-"), r["weakness"][:60], r["patch_sha256"][:12],
                                                                              r.get("other_failing_tests", "-")) for r in json.load(open(out / "mutation-results.json"))]
            emit("mutants", lines, [l for l in lines if not l.startswith("MUTATION_DETECTED")])
            continue
        if a.skip_missing and not (out / ("verdicts-%s.csv" % leg)).exists():
            print("::notice title=%s leg %s::not run in this invocation (leg subset)" % (TAG, leg))
            continue
        rows = list(csv.DictReader(open(out / ("verdicts-%s.csv" % leg))))
        short = lambda r: "%s %s | %s" % (r["verdict"], r["test_id"][:78], r["first_refusal_or_failure_boundary"][:56])
        bad = [short(r) for r in rows if r["verdict"] != "PASS"]
        counts = {}
        for r in rows:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        head = "SUMMARY leg %s rows=%d %s" % (leg, len(rows), " ".join("%s=%d" % kv for kv in sorted(counts.items())))
        emit("leg " + leg, [head] + ([short(r) for r in rows] if len(rows) <= 100 else bad), bad)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--work", required=True); r.add_argument("--out", required=True)
    r.add_argument("--tuple", default=None); r.add_argument("--legs", default=None)
    n = sp.add_parser("annotate"); n.add_argument("--out", required=True); n.add_argument("--legs", required=True); n.add_argument("--skip-missing", action="store_true")
    a = ap.parse_args()
    sys.exit(cmd_run(a) if a.cmd == "run" else cmd_annotate(a))
