"""V1 validation probes for shared requirement SR-3: 'Public repositories do not acquire proprietary ISS or private IGPG logic'.

Run with PROBE_PINS_DIR = a directory holding one exact checkout per pinned public source, named by freeze-manifest key
(components_subject.*, components_lock_remainder.*, `hub`, `qualification`), and PROBE_FREEZE_MANIFEST = the freeze
manifest. The probe-suite `--pins-manifest` option builds this directory. A failing probe is a recorded product finding.

Scan method: for every git-tracked file of every pinned checkout (git ls-files; .git excluded), scan the path and the
content for marker terms. Text files are decoded as UTF-8 (errors replaced); files with a NUL byte in the first 8 KiB are
treated as binary and scanned as bytes (never skipped silently); .zip archives are opened (up to 2 nesting levels) and each
member is scanned as its own file, reported as `archive.zip!member` and counted in files scanned. Every hit is recorded, never suppressed.

Marker terms (derived ONLY from public statements in the pinned sources, which this probe re-verifies each run):
  ISS   - hub README.md "ISS, Navalia and private research remain outside this public integration"; hub LICENSING.md;
          hub docs/private-evaluator/README.md "Do not share private ISS/IGPG implementations"
  IGPG  - the same private-evaluator README statement; hub docs/engineering-register.md (CR16 "IGPG Practice System")
  AoM   - hub docs/engineering-register.md "Extend versioned public interfaces without exposing private AoM or ISS
          mechanisms" (named there as a private mechanism alongside ISS)
Matching: ISS / IGPG / AoM are case-sensitive whole words (so "ISSUE", "MISS", "aom" do not match); path tokens are matched
case-insensitively on whole path components words. No private repository or private corpus is read, so this is a lexical
provenance screen, NOT clearance of semantic/derived proprietary logic.

False-positive handling (transparent, nothing removed from the report): a hit whose paragraph (blank-line-delimited block,
or +-2 lines for JSON/long lines) contains exclusion/boundary language - proprietary, private, outside, exclude, remain
out, do not, never, not introduce/import/publish/export/use/expose, exposing, keep ... out, preserve, no public export,
prohibit, must not, clearance - is classified `boundary-statement` (the file SAYS the logic is excluded, which is what SR-3 asks).
All other hits are `unclassified` and FAIL the probe. Binary-file hits are always `unclassified`.
Output: JSON report written to $PROBE_REPORT_DIR/sr3-provenance-report.json (if set) with method, terms, per-repo files
scanned, every hit, and the same totals as junit properties.
"""
import io
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

import pytest

from conftest import pin_dir

TERMS = {"ISS": r"\bISS\b", "IGPG": r"\bIGPG\b", "AoM": r"\bAoM\b"}
BOUNDARY = re.compile(
    r"proprietary|private|outside|exclu|remain out|out of scope|do not|don't|never|keep .{0,40} out|preserve|"
    r"no public export|prohibit|must not|not (introduce|import|publish|export|use|expose)|exposing|clearance", re.I)
# public statements that justify each marker term: (repo key, file glob regex, required text regex)
EVIDENCE = {
    "ISS": ("hub", "README.md", r"ISS, Navalia and private research remain outside this public integration"),
    "IGPG": ("hub", "docs/private-evaluator/README.md", r"private ISS/IGPG implementations"),
    "AoM": ("hub", "docs/engineering-register.md", r"without exposing private AoM or ISS mechanisms"),
}


def pins_root():
    return Path(pin_dir("PROBE_PINS_DIR"))


def manifest():
    return json.loads(Path(pin_dir("PROBE_FREEZE_MANIFEST")).read_text(encoding="utf-8"))


def expected_pins(m):
    pins = {}
    for group in ("components_subject", "components_lock_remainder"):
        for key, spec in m[group].items():
            pins[key] = (spec["repository"], spec["sha"])
    pins["hub"] = (m["identities"]["hub"]["repository"], m["identities"]["hub"]["head"])
    pins["qualification"] = (m["identities"]["qualification"]["repository"], m["identities"]["qualification"]["closeout"])
    return pins


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def tracked(repo):
    out = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8", "replace").split("\0") if p]


def classify(lines, idx):
    para_lo = idx
    while para_lo > 0 and lines[para_lo - 1].strip():
        para_lo -= 1
    para_hi = idx
    while para_hi + 1 < len(lines) and lines[para_hi + 1].strip():
        para_hi += 1
    lo, hi = (para_lo, para_hi) if para_hi - para_lo <= 12 else (max(0, idx - 2), min(len(lines) - 1, idx + 2))
    return "boundary-statement" if BOUNDARY.search("\n".join(lines[lo:hi + 1])) else "unclassified"


def scan_blob(key, rel, data, hits, stats, depth=0):
    """Scan one file's bytes (path token + content); recurse into zip archives."""
    stats["files_scanned"] += 1
    for term in TERMS:  # path tokens (case-insensitive whole words)
        if re.search(r"(?<![A-Za-z0-9])" + term + r"(?![A-Za-z0-9])", rel, re.I):
            hits.append({"repo": key, "file": rel, "line": 0, "term": term, "where": "path", "class": "unclassified", "text": rel})
    if rel.lower().endswith(".zip") and depth < 2 and zipfile.is_zipfile(io.BytesIO(data)):
        stats["archives_expanded"] += 1
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                if not info.is_dir():
                    scan_blob(key, f"{rel}!{info.filename}", z.read(info), hits, stats, depth + 1)
        return
    if b"\0" in data[:8192]:
        stats["binary_files_scanned_as_bytes"] += 1
        for term, rx in TERMS.items():
            for m in re.finditer(rx.encode(), data):
                hits.append({"repo": key, "file": rel, "line": 0, "term": term, "where": "binary", "class": "unclassified",
                             "text": data[max(0, m.start() - 40):m.end() + 40].decode("utf-8", "replace")})
        return
    lines = data.decode("utf-8", "replace").splitlines()
    for i, line in enumerate(lines):
        for term, rx in TERMS.items():
            if re.search(rx, line):
                hits.append({"repo": key, "file": rel, "line": i + 1, "term": term, "where": "content",
                             "class": classify(lines, i), "text": line.strip()[:200]})


def scan_repo(key, repo):
    stats, hits = {"files_scanned": 0, "binary_files_scanned_as_bytes": 0, "archives_expanded": 0}, []
    for rel in tracked(repo):
        path = Path(repo) / rel
        if path.is_file():
            scan_blob(key, rel, path.read_bytes(), hits, stats)
    return stats, hits


def test_probe_sr3_pinned_checkouts_match_the_freeze_manifest():
    root = pins_root()
    pins = expected_pins(manifest())
    assert len(pins) == 12, f"expected 7 subject + 3 lock-remainder components + hub + qualification, got {sorted(pins)}"
    bad = {}
    for key, (repository, sha) in pins.items():
        repo = root / key
        if not (repo / ".git").exists():
            bad[key] = "missing checkout"
        elif git(repo, "rev-parse", "HEAD").strip() != sha:
            bad[key] = f"HEAD {git(repo, 'rev-parse', 'HEAD').strip()} != pin {sha}"
        elif git(repo, "status", "--porcelain").strip():
            bad[key] = "working tree modified"
    assert not bad, bad


def test_probe_sr3_marker_terms_are_evidenced_by_public_statements_in_the_pins():
    root = pins_root()
    missing = []
    for term, (key, rel, rx) in EVIDENCE.items():
        f = root / key / rel
        if not f.is_file() or not re.search(rx, f.read_text(encoding="utf-8", errors="replace")):
            missing.append(f"{term}: {key}/{rel} !~ {rx!r}")
    assert not missing, f"marker term not (or no longer) evidenced by a public statement: {missing}"


def test_probe_sr3_scanner_control_flags_logic_and_classifies_boundary_statements(tmp_path):
    """Calibrated control: the scanner must flag a synthetic proprietary-logic file and classify an exclusion statement."""
    repo = tmp_path / "ctl"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "leak.py").write_text("def score():\n    # ISS weighting kernel\n    return 1\n")
    (repo / "notes.md").write_text("ISS and IGPG mechanisms remain private and are excluded from this repository.\n")
    (repo / "iss").mkdir()
    (repo / "iss" / "x.txt").write_text("nothing\n")
    (repo / "blob.bin").write_bytes(b"\0\0IGPG\0")
    (repo / "benign.md").write_text("The ISSUE tracker and MISS counts are unrelated.\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    stats, hits = scan_repo("ctl", repo)
    by = {(h["file"], h["term"], h["where"]): h["class"] for h in hits}
    assert by[("leak.py", "ISS", "content")] == "unclassified"
    assert by[("notes.md", "ISS", "content")] == "boundary-statement" and by[("notes.md", "IGPG", "content")] == "boundary-statement"
    assert by[("iss/x.txt", "ISS", "path")] == "unclassified"
    assert by[("blob.bin", "IGPG", "binary")] == "unclassified"
    assert not [h for h in hits if h["file"] == "benign.md"]
    assert stats["files_scanned"] == 5 and stats["binary_files_scanned_as_bytes"] == 1
    # archive members are scanned individually
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("inner/leak.py", "ISS kernel = 1\n")
    (repo / "bundle.zip").write_bytes(buf.getvalue())
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    stats2, hits2 = scan_repo("ctl", repo)
    assert stats2["archives_expanded"] == 1
    assert any(h["file"] == "bundle.zip!inner/leak.py" and h["class"] == "unclassified" for h in hits2)


def test_probe_sr3_no_unclassified_proprietary_marker_hits_in_pinned_public_sources(record_property):
    root = pins_root()
    pins = expected_pins(manifest())
    per_repo, all_hits = {}, []
    for key, (repository, sha) in sorted(pins.items()):
        stats, hits = scan_repo(key, root / key)
        per_repo[key] = {"repository": repository, "sha": sha, **stats, "hits": len(hits)}
        all_hits.extend(hits)
    unclassified = [h for h in all_hits if h["class"] == "unclassified"]
    report = {
        "schema": "cognous.v1-sr3-provenance-scan/1",
        "method": __doc__.split("Scan method:")[1].split("Marker terms")[0].strip(),
        "terms": {t: rx for t, rx in TERMS.items()},
        "term_evidence": {t: {"repo": k, "file": f, "statement": s} for t, (k, f, s) in EVIDENCE.items()},
        "false_positive_handling": "hits in a paragraph containing exclusion/boundary language are classified boundary-statement, listed, and not failing; everything else (incl. path and binary hits) is unclassified and fails",
        "limits": "lexical screen of pinned public trees only; no private corpus; optional components (prp, research_intelligence, tfa) not in scope",
        "repositories": per_repo,
        "files_scanned_total": sum(r["files_scanned"] for r in per_repo.values()),
        "hits_total": len(all_hits),
        "hits_by_class": {c: sum(1 for h in all_hits if h["class"] == c) for c in ("boundary-statement", "unclassified")},
        "hits": all_hits,
    }
    out = os.environ.get("PROBE_REPORT_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "sr3-provenance-report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    record_property("sr3_repositories_scanned", len(per_repo))
    record_property("sr3_files_scanned", report["files_scanned_total"])
    record_property("sr3_hits_total", report["hits_total"])
    record_property("sr3_hits_boundary_statement", report["hits_by_class"]["boundary-statement"])
    record_property("sr3_hits_unclassified", report["hits_by_class"]["unclassified"])
    assert report["files_scanned_total"] > 0 and len(per_repo) == 12
    assert not unclassified, "unclassified proprietary-marker hits: " + json.dumps(
        [f"{h['repo']}:{h['file']}:{h['line']} {h['term']} [{h['where']}] {h['text'][:100]}" for h in unclassified], indent=1)
