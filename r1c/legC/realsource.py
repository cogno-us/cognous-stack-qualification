"""Real-source legs for the R1C r3 observation (stdlib only). Imported by run_r1c.py for legs with "type": "realsource".

Each case is one of:
  kind "pin"    - a 40-hex constant found by regex in a file of a fetched component must equal a component SHA (no execution);
  kind "verify" - Exchange's source verifier (gax_ref_runtime._verify_refusal_profile_sources, or the public load_executor_runtime) is run in a FRESH
                  interpreter (child_verify.py) with profile P against REAL fetched checkouts; the observed ACCEPTED/REFUSED (and, for a refusal, the
                  module named in "candidate source identity mismatch: <module>" or an expected text) must equal the expectation.
A "derive" step makes a throwaway copy of one source checkout (dirty tracked file / git replace ref) in the work directory (never in the evidence dir).
The leg writes a junit.xml in pytest's shape so the generic runner machinery (verdict CSV, annotations, mutation controls) applies unchanged.
"""
import json, os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROLES = ("cp", "runtime", "manifest", "replay", "odes", "pack")
GIT_ID = ["-c", "user.name=r1c", "-c", "user.email=r1c@example.invalid"]


def _git(cwd, *args, inp=None):
    p = subprocess.run(["git", *GIT_ID, *args], cwd=cwd, capture_output=True, text=True, input=inp, timeout=120)
    if p.returncode:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()[:200]))
    return p.stdout.strip()


def _derive(op, src, dst, rel=None):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, symlinks=True)
    if op == "dirty_entry":  # a tracked module that is executed by the import
        with open(dst / rel, "a") as f:
            f.write("\n# r1c: tracked-file modification (dirty checkout)\n")
    elif op == "dirty_other":  # a tracked file that is NOT an entry module (whole-tree check)
        with open(dst / "README.md", "a") as f:
            f.write("\nr1c: tracked-file modification (dirty checkout)\n")
    elif op == "replace":  # HEAD still names the pin, a refs/replace entry stands a different commit in for it
        head, tree = _git(dst, "rev-parse", "HEAD"), _git(dst, "rev-parse", "HEAD^{tree}")
        other = _git(dst, "commit-tree", tree, "-m", "r1c replacement commit")
        _git(dst, "replace", head, other)
        assert _git(dst, "for-each-ref", "refs/replace/").strip(), "replace ref not created"
        assert _git(dst, "rev-parse", "HEAD") == head, "HEAD moved"
    else:
        raise ValueError("unknown derive op " + op)


def _pin_case(case, dirs, t):
    base = Path(dirs[case["component"]])
    text = (base / case["file"]).read_text()
    if case.get("after"):
        i = text.find(case["after"])
        if i < 0:
            return "failed", "anchor %r not found in %s" % (case["after"], case["file"]), {}
        text = text[i:]
    m = re.search(case["regex"], text, re.M)
    got = m.group(1) if m else None
    want = t["components"][case["equals"]]["sha"]
    info = {"file": case["file"], "found": got, "want": want}
    if got == want:
        return "passed", "", info
    return "failed", "pin %s != %s in %s" % (got, want, case["file"]), info


class NotPristine(Exception):
    pass


def _pristine(name, dirs, work, leg_id):
    """A fresh copy of a fetched component WITHOUT bytecode caches or any other untracked/ignored file (earlier test legs import from the
    fetched checkouts and leave __pycache__ behind; Exchange's verifier correctly refuses such files, so this leg verifies clean copies).
    The copy must be exactly clean (git status --porcelain --untracked-files=all --ignored empty), else the case is BLOCKED, never PASS."""
    dst = Path(work) / "rs-pristine" / leg_id / name
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(dirs[name], dst, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    dirty = _git(dst, "status", "--porcelain", "--untracked-files=all", "--ignored")
    if dirty or _git(dst, "rev-parse", "HEAD") != _git(Path(dirs[name]), "rev-parse", "HEAD"):
        raise NotPristine("BLOCKED: pristine copy of %s is not clean: %r" % (name, dirty[:120]))
    return dst


def _verify_case(case, dirs, t, d, work, leg_id):
    srcs = {r: _pristine(case["sources"][r], dirs, work, leg_id) for r in ROLES}
    if case.get("derive"):
        role, op = case["derive"]["role"], case["derive"]["op"]
        dst = Path(work) / ("rs-%s-%s" % (leg_id, re.sub(r"\W+", "_", case["name"])))
        _derive(op, srcs[role], dst, case["derive"].get("file"))
        srcs[role] = dst
    manifest = srcs["manifest"] / "examples" / "customer_service_agent.manifest.json"
    arg = {"exchange": str(dirs[case["exchange"]]), "profile": case["profile"], "entry": case.get("entry", "verify"),
           "paths": [str(srcs["replay"] / "src"), str(srcs["odes"] / "src"), str(srcs["pack"] / "src")],
           "cp": str(srcs["cp"]), "runtime": str(srcs["runtime"]), "manifest_file": str(manifest)}
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH" and not k.startswith(("GAX_", "GIT_DIR", "GIT_OBJECT", "GIT_ALTERNATE", "GIT_REPLACE"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cwd = Path(work) / "rs-cwd"
    cwd.mkdir(exist_ok=True)
    p = subprocess.run([sys.executable, "-B", str(HERE / "child_verify.py"), json.dumps(arg)], cwd=cwd, env=env, capture_output=True, text=True, timeout=600)
    line = next((l for l in p.stdout.splitlines() if l.startswith("CHILD_RESULT ")), None)
    (d / "cases").mkdir(exist_ok=True)
    (d / "cases" / (re.sub(r"\W+", "_", case["name"]) + ".log")).write_text("args: %s\nrc=%d\nstdout:\n%s\nstderr:\n%s\n" % (json.dumps(arg, indent=1), p.returncode, p.stdout, p.stderr[-2000:]))
    if not line:
        return "failed", "no CHILD_RESULT (rc=%d): %s" % (p.returncode, p.stderr.strip()[-200:]), {}
    res = json.loads(line[len("CHILD_RESULT "):])
    exp, msg = case["expect"], res.get("message", "")
    info = {"status": res["status"], "message": msg, "profile": res.get("profile"), "pins": res.get("pins")}
    if res["status"] != exp:
        return "failed", "expected %s observed %s %s" % (exp, res["status"], msg[:140]), info
    if exp == "REFUSED":
        need = case.get("expect_text") or ("candidate source identity mismatch: " + case["expect_module"])
        if need not in msg:
            return "failed", "refused for another reason: %r (wanted %r)" % (msg[:160], need), info
    else:  # ACCEPTED: the modules that were imported must come from the verified checkouts
        for mod, f in (res.get("modules") or {}).items():
            role = {"agent_control_plane.bounded": "cp", "engine.producer_contract": "runtime", "agent_replay_bundle.importers": "replay",
                    "odes.exporter": "odes", "agent_governance_evidence_pack.importer": "pack"}[mod]
            if case.get("entry", "verify") == "verify" and not str(Path(f).resolve()).startswith(str(srcs[role].resolve())):
                return "failed", "accepted but %s imported from %s" % (mod, f), info
    return "passed", "", info


def execute(leg, dirs, d, t, work):
    """Run every case; write d/junit.xml; return the case names (the 'collected ids')."""
    shutil.rmtree(Path(work) / "rs-pristine" / leg["id"], ignore_errors=True)
    suite = ET.Element("testsuite", name="realsource-" + leg["id"])
    names, detail = [], {}
    for case in leg["cases"]:
        names.append(case["name"])
        tc = ET.SubElement(suite, "testcase", classname="realsource." + leg["id"], name=case["name"])
        try:
            outcome, msg, info = _pin_case(case, dirs, t) if case["kind"] == "pin" else _verify_case(case, dirs, t, d, work, leg["id"])
        except NotPristine as e:
            outcome, msg, info = "blocked", str(e), {}
        except Exception as e:  # noqa: BLE001 - a case that cannot be set up is a failure, never a pass
            outcome, msg, info = "failed", "case could not be executed: %r" % (e,), {}
        if outcome == "failed":
            ET.SubElement(tc, "failure", message=msg)
        elif outcome == "blocked":
            ET.SubElement(tc, "skipped", message=msg)  # a skip that no leg allow-lists is resolved to BLOCKED by the runner
        detail[case["name"]] = {"outcome": outcome, "expect": case.get("expect", "pin-equals"), "info": info}
    ET.ElementTree(suite).write(d / "junit.xml", encoding="utf-8", xml_declaration=True)
    (d / "realsource-detail.json").write_text(json.dumps(detail, indent=1))
    return names
