"""Probe harness: runs against the pinned Index checkout named by PROBE_INDEX_DIR (never modified)."""
import os
import sys
import pytest

INDEX_DIR = os.environ.get("PROBE_INDEX_DIR")
if INDEX_DIR:
    sys.path.insert(0, INDEX_DIR)


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
