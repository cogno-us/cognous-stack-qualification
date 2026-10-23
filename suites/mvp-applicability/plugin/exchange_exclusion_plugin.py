"""Pytest plugin: record, at the end of the mandatory battery session, whether any Exchange module was loaded (AP-06).

SPDX-License-Identifier: Apache-2.0

Load with ``-p exchange_exclusion_plugin`` (suites/mvp-applicability/plugin on PYTHONPATH). It writes a JSON observation into
MVP_ACCEPTANCE_DIR (else MVP_RESULTS_DIR) as exchange-exclusion-<MVP_EXCLUSION_TAG>.json (one file per pytest invocation of the battery). It records raw observations only; the gate (tools/mvp_acceptance_gate.py) judges them. A session that never wrote
the file is an incomplete verdict, so the check cannot be omitted by not loading the plugin.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOTS = ("experiments", "odex_gax_imx_reference", "governed_message_transport")
PATH_PATTERN = re.compile(r"(?i)(cognous-governed-exchange|governed[-_]exchange|odex_gax_imx)")


def scan(modules=None, paths=None) -> dict:
    modules = sys.modules if modules is None else modules
    paths = sys.path if paths is None else paths
    loaded = sorted(name for name in modules if name.split(".")[0] in ROOTS)
    by_file = []
    for name, mod in list(modules.items()):
        file = getattr(mod, "__file__", None)
        if isinstance(file, str) and PATH_PATTERN.search(file):
            by_file.append({"module": name, "file": file})
    path_hits = [p for p in paths if isinstance(p, str) and PATH_PATTERN.search(p)]
    return {"exchange_modules_loaded": loaded, "modules_from_exchange_paths": sorted(by_file, key=lambda d: d["module"]),
            "sys_path_exchange_entries": path_hits}


def pytest_sessionfinish(session, exitstatus):
    out = Path(os.environ.get("MVP_ACCEPTANCE_DIR") or os.environ.get("MVP_RESULTS_DIR") or ".")
    out.mkdir(parents=True, exist_ok=True)
    tag = re.sub(r"[^A-Za-z0-9_-]", "", os.environ.get("MVP_EXCLUSION_TAG") or "battery") or "battery"
    doc = {"schema": "cognous.mvp-exchange-exclusion-observation/1", "tag": tag, "scanned": "sys.modules and sys.path of the interpreter that ran the battery",
           **scan(), "pytest_exit_status": int(exitstatus)}
    (out / f"exchange-exclusion-{tag}.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
