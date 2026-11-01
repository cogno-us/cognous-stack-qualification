"""Omit zero-byte transient .lock files from retained evidence and list each one.

SPDX-License-Identifier: Apache-2.0
Windows cannot check out the long lock-file names; the files carry no content.
A non-empty .lock file is never omitted: the tool refuses instead.
"""
import hashlib
import json
import os
import sys

dest = sys.argv[1]
slim_native = "--slim-native" in sys.argv
omitted = []
slim = {"kept": [], "omitted_files": 0, "omitted_bytes": 0}
if slim_native:
    keep = {"junit.xml", "stdout.log", "source-run-summary.json", "result.json"}
    ndir = os.path.join(dest, "jobs", "native")
    for root, _, files in os.walk(ndir):
        for name in files:
            path = os.path.join(root, name)
            if name in keep:
                slim["kept"].append(os.path.relpath(path, dest).replace(os.sep, "/"))
            else:
                slim["omitted_files"] += 1
                slim["omitted_bytes"] += os.path.getsize(path)
                os.remove(path)
    slim["note"] = ("Native per-case trees omitted from this run's retention: same suite, same pins; full native evidence is retained "
                    "for the baseline and the final authoritative run. JUnit, stdout and summaries are kept.")
for root, _, files in os.walk(dest):
    for name in files:
        if name.endswith(".lock"):
            path = os.path.join(root, name)
            data = open(path, "rb").read()
            if data:
                sys.exit(f"refusing to omit non-empty lock file: {path}")
            omitted.append({"path": os.path.relpath(path, dest).replace(os.sep, "/"), "bytes": 0,
                            "sha256": hashlib.sha256(data).hexdigest()})
            os.remove(path)
out = {"omitted_lock_files": omitted}
if slim_native:
    out["slim_native"] = slim
json.dump(out, open(os.path.join(dest, "omitted-lock-files.json"), "w"), indent=1)
print(f"omitted {len(omitted)} empty lock files")
