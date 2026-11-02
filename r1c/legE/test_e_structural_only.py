"""Leg E: structural-only mode stays explicitly UNQUALIFIED at the exact Replay SHA (developer observation, not a Registry-authentication claim).
Runs with PYTHONPATH=<replay>:<replay>/src; reuses the Replay fixtures through its own test helpers (read-only)."""
import json

from agent_replay_bundle.importers import import_bounded_workflow
from tests.test_registry_governed_effective_configuration import CUR_CP, SELECTOR, load

MARKER = "internal_consistency_only_registry_source_revision_unverified"


def test_default_mode_import_emits_the_unqualified_marker_and_no_registry_authenticated_label():
    cp, proposal = load("governed_executed")
    meta = import_bounded_workflow(cp, proposal=proposal, control_plane_revision=CUR_CP, control_plane_profile=SELECTOR).metadata
    assert meta["effective_configuration_verification"] == MARKER
    assert "registry_authenticated" not in meta and "registry_origin" not in meta
    assert "authenticated" not in json.dumps(meta).lower()  # no REGISTRY_AUTHENTICATED (or any *_authenticated) label in the default mode
