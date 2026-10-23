"""Observation only (AP-06): when MVP_INGRESS_MODULE_DUMP names a file, write this interpreter's loaded modules there at exit.

SPDX-License-Identifier: Apache-2.0
Placed on PYTHONPATH of the pinned hub ingress server by suites/mvp-chain/_ingress.py. The server exits through sys.exit on SIGTERM, so
atexit runs. No import, no behaviour change; a missing dump is an incomplete verdict at the gate.
"""
import atexit
import json
import os
import sys


def _dump():
    path = os.environ.get("MVP_INGRESS_MODULE_DUMP")
    if not path:
        return
    try:
        mods = {name: getattr(mod, "__file__", None) for name, mod in list(sys.modules.items())}
        with open(path, "w") as fh:
            json.dump({"schema": "cognous.mvp-ingress-modules/1", "pid": os.getpid(), "run_id": os.environ.get("MVP_RUN_ID"), "modules": mods, "sys_path": list(sys.path)}, fh, sort_keys=True)
    except Exception:  # noqa: BLE001  (observation only)
        pass


atexit.register(_dump)
