"""Subprocess probe (N26, Exchange): call the Exchange strict source-identity check of profile security-runtime-current-20261031-r3 over a candidate Control Plane checkout.
usage: probe_exchange.py <exchange-root> <cp-root> <replay-src>      Prints {"pins":{...}, "result": "..."}. Exchange code is not modified."""
import json
import os
import sys
from pathlib import Path

os.environ["GAX_RUNTIME_COMPATIBILITY_PROFILE"] = "security-runtime-current-20261031-r3"
exchange, cp_root, replay_src = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
for entry in (replay_src, str(cp_root / "src"), str(exchange / "experiments")):
    sys.path.insert(0, entry)
os.environ.setdefault("UPSTREAM_MANIFEST_EXAMPLE", str(cp_root / "tests" / "fixtures" / "refund_integration_v1_1.manifest.json"))
import odex_gax_imx_reference.gax_ref_runtime as g  # noqa: E402

pins = {k: getattr(g, k) for k in ("CP_REVISION", "REPLAY_REVISION", "ODES_REVISION", "EVIDENCE_PACK_REVISION")}
try:
    g._verify_refusal_profile_sources(cp_root, None)
    result = "accepted"
except BaseException as exc:
    result = type(exc).__name__ + ": " + str(exc)
print(json.dumps({"pins": pins, "strict_profile": g.RUNTIME_COMPATIBILITY_PROFILE in g.STRICT_SOURCE_PROFILES, "result": result}, sort_keys=True))
