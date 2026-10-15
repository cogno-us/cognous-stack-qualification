"""Fail closed when the dedicated qualification lacks exact accepted checkouts."""
import importlib
import os
from pathlib import Path
import subprocess
import pytest

@pytest.fixture(scope="session", autouse=True)
def exact_merged_dependencies():
    profile=os.environ.get("GAX_RUNTIME_COMPATIBILITY_PROFILE")
    assert profile in {"merged-producers-v1","typed-refusal-candidate-20261015"}
    pins = {
        "agent_control_plane": "d3dadee70bd319812b207389ab1e0f6efe511916",
        "engine.producer_contract": "c3c3ee7188b9367cf70b08074b9c40a5c70c94ac",
        "agent_replay_bundle": "459e4ba62fca49364aebb0050cd5fb2dd5a71bfa",
        "odes": "c5e9a0f3695ae836b803be06c46d2c669642ee03",
        "agent_governance_evidence_pack": "b4baccd823d2a73be276c1de745b19cf7c56a0d6",
    }
    if profile=="typed-refusal-candidate-20261015":
        pins={
            "agent_control_plane":"c7f122ba3a6e39f9268a7163c99be3ee514cd97e",
            "engine.producer_contract":"309e194c1b0a3de23e11e20133e6eaf88875e48a",
            "agent_replay_bundle":"83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a",
            "odes":"25c7ad608c2e6fd9f450e075db6bbf3ee4091a49",
            "agent_governance_evidence_pack":"1e789c7d67a897097445faef1813fb0cd22d55e5",
        }
    from experiments.odex_gax_imx_reference.gax_ref_runtime import load_executor_runtime
    load_executor_runtime()
    for name, expected in pins.items():
        module = importlib.import_module(name)
        actual = subprocess.check_output(["git", "-C", str(Path(module.__file__).parent), "rev-parse", "HEAD"], text=True, timeout=10).strip()
        assert actual == expected, (name, actual, expected)
    manifest = Path(os.environ["UPSTREAM_MANIFEST_EXAMPLE"])
    actual = subprocess.check_output(["git", "-C", str(manifest.parent), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    assert actual == "46c950bed37fe3812000895430bc0312d29e37ce"
