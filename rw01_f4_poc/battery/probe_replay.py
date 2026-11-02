"""Subprocess probe: run Replay's structural-only (old governed selector) and caller-trusted-digest modes at ANY Replay checkout over a list of CP run records and print one
canonical JSON line per (record, mode): the bundle JSON or the typed refusal (type, code, message). Byte-compared across Replay base/head (N23, N24).

usage: probe_replay.py <replay-src> <record-dir>...      (each dir holds control_plane_run.json and proposal.json)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from agent_replay_bundle import effective_configuration as EC  # noqa: E402
from agent_replay_bundle import importers as I  # noqa: E402

VOLATILE = {"bundle_id": "<uuid>", "generated_at": "<now>"}   # the only two members Replay fills from uuid4()/the clock; everything else is compared byte for byte


def norm(x):
    if isinstance(x, dict):
        return {k: (VOLATILE[k] if k in VOLATILE else norm(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(i) for i in x]
    return x


out = []
for d in [x for x in map(Path, sys.argv[2:]) if x.is_dir()]:
    cp = json.loads((d / "control_plane_run.json").read_text())
    proposal = json.loads((d / "proposal.json").read_text())
    digests = [x["binding"]["runtime_authority"]["effective_configuration"]["digest"] for x in cp["decisions"] if x.get("binding") and "effective_configuration" in (x["binding"].get("runtime_authority") or {})]
    modes = {"structural": {}, "trusted_match_correct": {"expected_effective_configuration_digest": digests[0] if digests else "sha256:" + "2" * 64},
             "trusted_match_wrong": {"expected_effective_configuration_digest": "sha256:" + "1" * 64}}
    for mode, kw in modes.items():
        try:
            res = I.import_bounded_workflow(json.loads(json.dumps(cp)), proposal=json.loads(json.dumps(proposal)), control_plane_revision=I.CONTROL_PLANE_CUR_REVISION,
                                            control_plane_profile=EC.REGISTRY_GOVERNED_PROFILE, **kw)
            out.append({"record": d.name, "mode": mode, "bundle": norm(res.model_dump(mode="json"))})
        except Exception as exc:
            out.append({"record": d.name, "mode": mode, "refused": [type(exc).__name__, getattr(exc, "code", None), str(exc)]})
print(json.dumps(out, sort_keys=True, indent=1))
