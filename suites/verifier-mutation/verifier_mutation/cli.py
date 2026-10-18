"""Command line: ``python -m verifier_mutation {capture,capture-extra,operator-set,code-names,check-corpus,report}`` (run with ``PYTHONPATH=suites/verifier-mutation``).

Report-only. ``report`` exits 0 when it produced a valid report, whatever the verifier scored; it exits 2 when the operator set is not the
frozen one, the corpus does not match its manifest, or the report it built is refused by the ODES validator; ``--strict`` additionally
exits 3 when the harness raised any flag (the verifier is not measuring anything). No flag is a scenario verdict.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import corpus, operators, report
from .jsonio import digest
from .runner import Runner
from .trace import load_clean_corpus

HERE = Path(__file__).resolve().parent
SUITE = HERE.parent
REPO = SUITE.parent.parent
OPERATOR_SET = SUITE / "operators.json"
IMPLEMENTATION_FILES = ("jsonio.py", "operators.py", "corpus.py", "trace.py")


def operator_set_doc(seed: int = corpus.DEFAULT_SEED, draws: int = corpus.DEFAULT_DRAWS) -> dict[str, Any]:
    return {
        "kind": "verifier-mutation-operator-set", "family": "T", "harness_version": report.HARNESS_VERSION, "operator_version": operators.OPERATOR_VERSION,
        "seed": seed, "draws_per_variant": draws,
        "implementation_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in IMPLEMENTATION_FILES},
        "categories_with_operator": operators.categories_with_operator(),
        "categories_without_operator": list(operators.CATEGORIES_WITHOUT_OPERATOR),
        "expected_accept_categories": list(operators.EXPECTED_ACCEPT),
        "intended_codes": {
            "status": "frozen post-hoc after run 1 (703cdde1); not held-out",
            "basis": "catalogue version 2 drops intended-code names that do not exist in the verifier and adds the codes the verifier emits for the damage, chosen after run 1 and the V3a follow-up were read",
            "primary_figure": "any_code detection; localized (intended-code) figures are secondary",
            "vocabulary": "verifier-code-names.json",
        },
        "supersedes": {"operator_version": "1", "qualification_revision": "703cdde145c5818c0eef0de3da4d923953a673f5",
                       "operator_set_digest": "sha256:98ede4eeb0ff252a7bd9a9b39e85f43394fee9732c089381afa8210c8b798514"},
        "operators": operators.operator_catalogue(),
    }


def operator_set_bytes(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _summary(doc: dict[str, Any]) -> list[str]:
    """One line per corpus and category, each over its own denominator; nothing is summed across categories or corpora."""
    out = []
    mr = doc["mutation_report"]
    for c in mr["family_t"]:
        out.append(f"family T, {c['corpus_id']} ({c['provenance']}): category  n_eff  reject accept abstain error")
        for r in c["categories"]:
            v = r["verdicts"]
            extra = ""
            if r["regression"]:
                extra = "  intended code " + report.render_fraction(r["regression"]["refused_with_intended_code"])
            elif r["detection"]:
                extra = "  detection " + report.render_fraction(r["detection"]["any_code"]) + "  false acceptance " + report.render_fraction(r["false_acceptance"])
            out.append(f"  {r['category']:<2} {r['expected_verdict']:<14} {r['n_eff']:>5}  {v['reject']:>6} {v['accept']:>6} {v['abstain']:>7} {v['error']:>5}{extra}")
    for c in mr["clean"]:
        out.append(f"clean, {c['corpus_id']}: false rejection per category")
        out.append("  " + "  ".join(f"{r['category']} {report.render_fraction(r['false_rejection'])}" for r in c["rows"]))
    for f in mr["extensions"]["x-qualification-harness"]["flags"]:
        out.append(f"FLAG {f['id']}: {f['k']}/{f['n']}  {f['detail']}")
    return out


def cmd_report(a: argparse.Namespace) -> int:
    frozen = OPERATOR_SET.read_bytes() if OPERATOR_SET.exists() else b""
    set_doc = json.loads(frozen) if frozen else None
    if set_doc is None or operator_set_bytes(operator_set_doc(set_doc["seed"], set_doc["draws_per_variant"])) != frozen:
        print("operators.json is not the frozen operator set of this code: run `operator-set --write` and commit it before any verifier run", file=sys.stderr)
        return 2
    try:
        manifest, traces = load_clean_corpus(Path(a.clean_corpus))
    except (OSError, ValueError, KeyError) as exc:
        print(f"clean corpus refused: {exc}", file=sys.stderr)
        return 2
    seeds = None
    if a.odes:
        revision = a.odes_revision or _git(["rev-parse", "HEAD"], Path(a.odes)) or "unknown"
        seeds = corpus.load_seed_corpus(Path(a.odes), corpus.load_seed_map(SUITE / "seed-map.json"), revision)
    slots, dropped = corpus.generate(traces, set_doc["seed"], set_doc["draws_per_variant"])
    runner = Runner(a.verifier_cmd, timeout=a.timeout, contract_dir=Path(a.contract_dir) if a.contract_dir else None)
    run = report.execute(runner, traces, slots, seeds, jobs=a.jobs)
    family_s = json.loads(Path(a.family_s).read_text(encoding="utf-8")) if a.family_s else None
    doc = report.build(
        run, traces=traces, slots=slots, duplicates_dropped=dropped, seeds=seeds, clean_manifest=manifest, operator_set_bytes=frozen, operator_set_digest=digest(frozen),
        seed=set_doc["seed"], draws=set_doc["draws_per_variant"], frozen_revision=a.frozen_revision or _git(["rev-parse", "HEAD"], REPO) or "unknown",
        generated_at=a.generated_at, command=a.verifier_cmd,
        verifier_hint={"name": a.verifier_name, "version": a.verifier_version, "source_revision": a.verifier_revision}, per_scenario=not a.no_per_scenario, family_s=family_s)
    violations = report.validate(doc, a.contract_dir)
    if violations:
        for v in violations[:20]:
            print(f"harness report refused by the ODES validator: {v.code} {v.path}: {v.message}", file=sys.stderr)
        return 2
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for line in _summary(doc):
        print(line)
    print(f"wrote {a.out} ({runner.calls} verifier runs); the report validates against the ODES verification-report contract")
    return 3 if (a.strict and doc["mutation_report"]["extensions"]["x-qualification-harness"]["flags"]) else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="verifier_mutation")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture", help="capture the clean corpus from the control plane (needs its virtualenv)")
    c.add_argument("--control-plane", required=True)
    c.add_argument("--out", default=str(SUITE / "corpus" / "clean"))
    e = sub.add_parser("capture-extra", help="add the post-run-1 trace (lost acknowledgement, failed follow-up observation) to the existing clean corpus")
    e.add_argument("--control-plane", required=True)
    e.add_argument("--out", default=str(SUITE / "corpus" / "clean"))
    o = sub.add_parser("operator-set", help="write or check operators.json (the frozen operator set)")
    o.add_argument("--write", action="store_true")
    n = sub.add_parser("code-names", help="write or check verifier-code-names.json from a verifier clone at a revision (reads source with git; runs nothing)")
    n.add_argument("--verifier", required=True, help="clone of cogno-us/cognous-open-control-stack-verifier")
    n.add_argument("--revision", required=True)
    n.add_argument("--write", action="store_true")
    k = sub.add_parser("check-corpus", help="check the clean corpus against its manifest")
    k.add_argument("--clean-corpus", default=str(SUITE / "corpus" / "clean"))
    r = sub.add_parser("report", help="run the verifier over the corpora and write the mutation report")
    r.add_argument("--verifier-cmd", required=True, help="e.g. 'cognous-verify --run-record {run_record} [--proposal {proposal_export}] [--ledger {destination_ledger}]'")
    r.add_argument("--out", required=True)
    r.add_argument("--clean-corpus", default=str(SUITE / "corpus" / "clean"))
    r.add_argument("--odes", help="checkout of cogno-us/open-decision-evidence-standard (adds the seed corpus)")
    r.add_argument("--odes-revision")
    r.add_argument("--contract-dir", help="verification-report contract directory (default: the vendored copy)")
    r.add_argument("--family-s", help="JSON list of family S context corpora (counts supplied by their own tools; never run here)")
    r.add_argument("--frozen-revision")
    r.add_argument("--generated-at")
    r.add_argument("--jobs", type=int, default=4)
    r.add_argument("--timeout", type=float, default=60.0)
    r.add_argument("--no-per-scenario", action="store_true")
    r.add_argument("--strict", action="store_true", help="exit 3 when the harness raised a flag")
    r.add_argument("--verifier-name", default="unknown")
    r.add_argument("--verifier-version", default="unknown")
    r.add_argument("--verifier-revision", default="unknown")
    a = p.parse_args(argv)
    if a.cmd == "capture":
        from .capture import capture
        m = capture(Path(a.control_plane), Path(a.out))
        print(f"captured {len(m['traces'])} traces at control plane {m['control_plane_revision']}")
        return 0
    if a.cmd == "capture-extra":
        from .capture import capture_unobserved
        m = capture_unobserved(Path(a.control_plane), Path(a.out))
        print(f"corpus now holds {len(m['traces'])} traces (control plane {m['control_plane_revision']})")
        return 0
    if a.cmd == "operator-set":
        if OPERATOR_SET.exists():
            old = json.loads(OPERATOR_SET.read_text(encoding="utf-8"))
            seed, draws = old["seed"], old["draws_per_variant"]
        else:
            seed, draws = corpus.DEFAULT_SEED, corpus.DEFAULT_DRAWS
        data = operator_set_bytes(operator_set_doc(seed, draws))
        if a.write:
            OPERATOR_SET.write_bytes(data)
            print(f"wrote {OPERATOR_SET} ({digest(data)})")
            return 0
        same = OPERATOR_SET.exists() and OPERATOR_SET.read_bytes() == data
        print("operator set matches the code" if same else "operators.json differs from the code")
        return 0 if same else 1
    if a.cmd == "code-names":
        from .codenames import vocabulary_bytes, vocabulary_doc
        target = SUITE / "verifier-code-names.json"
        data = vocabulary_bytes(vocabulary_doc(Path(a.verifier), a.revision))
        if a.write:
            target.write_bytes(data)
            print(f"wrote {target} ({digest(data)})")
            return 0
        same = target.exists() and target.read_bytes() == data
        print("verifier-code-names.json matches the verifier source" if same else "verifier-code-names.json differs from the verifier source")
        return 0 if same else 1
    if a.cmd == "check-corpus":
        try:
            _, traces = load_clean_corpus(Path(a.clean_corpus))
        except (OSError, ValueError, KeyError) as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 1
        print(f"{len(traces)} traces match the manifest")
        return 0
    return cmd_report(a)
