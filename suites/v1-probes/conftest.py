"""Probe harness: runs against ONE pinned checkout per job, named by an env var (never modified).

One env var per component. Test modules whose env var is unset are not collected (so the existing
Index job is unchanged and a missing job yields no results, which the aggregator reports as
INCONCLUSIVE rather than as a pass).
"""
import os
import sys
import pytest

# module file -> env var naming the pinned checkout it needs
MODULE_ENV = {
    "test_index_probes.py": "PROBE_INDEX_DIR",
    "test_index_supersession_probes.py": "PROBE_INDEX_DIR",
    "test_bitrep_probes.py": "PROBE_BITREP_DIR",
    "test_runtime_probes.py": "PROBE_RUNTIME_DIR",
    "test_replay_probes.py": "PROBE_REPLAY_DIR",
    "test_evidence_pack_probes.py": "PROBE_EVIDENCE_PACK_DIR",
    "test_odes_probes.py": "PROBE_ODES_DIR",
    "test_control_plane_probes.py": "PROBE_CONTROL_PLANE_DIR",
    "test_action_manifest_probes.py": "PROBE_ACTION_MANIFEST_DIR",
    "test_odes_extension_probes.py": "PROBE_ODES_DIR",
    "test_provenance_probes.py": "PROBE_PINS_DIR",
    "test_authority_probes.py": "PROBE_AUTHORITY_DIR",
    "test_authority_ra_probes.py": "PROBE_CONTROL_PLANE_DIR",
}
# Env vars whose directory must NOT be put on sys.path: documentation/provenance probes read files only, and PROBE_PINS_DIR is
# a directory of several checkouts, not a package root.
NO_SYSPATH = {"PROBE_ACTION_MANIFEST_DIR", "PROBE_PINS_DIR"}
collect_ignore = [m for m, v in MODULE_ENV.items() if not os.environ.get(v)]

INDEX_DIR = os.environ.get("PROBE_INDEX_DIR")
for _var in sorted(set(MODULE_ENV.values()) - NO_SYSPATH):
    _d = os.environ.get(_var)
    if _d:
        # src-layout packages expose their code under src/; flat repos under the root.
        for _p in (os.path.join(_d, "src"), _d):
            if os.path.isdir(_p):
                sys.path.insert(0, _p)


def pin_dir(var):
    d = os.environ.get(var)
    if not d:
        pytest.fail(f"{var} is not set; probe cannot run against the pinned component")
    return d


@pytest.fixture
def index_client():
    if not INDEX_DIR:
        pytest.fail("PROBE_INDEX_DIR is not set; probe cannot run against the pinned Index")
    from fastapi.testclient import TestClient
    from app.claims import service as cs
    from app.evidence import service as es
    from app.governance import service as gs
    from app.api import claims, evidence, governance
    cs.claims_service = cs.ClaimsService()
    es.evidence_service = es.EvidenceService()
    gs.governance_service = gs.GovernanceService()
    claims.claims_service = cs.claims_service
    evidence.evidence_service = es.evidence_service
    governance.governance_service = gs.governance_service
    from app.main import app
    return TestClient(app)
