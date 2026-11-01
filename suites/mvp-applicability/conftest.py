"""mvp-applicability wiring (proposed). Every test FAILS, never skips, when an input is missing.

SPDX-License-Identifier: Apache-2.0

Inputs (environment):
  MVP_HUB_DIR         pinned hub checkout (tools/mvp_ingress)
  MVP_PIN_FILE        the resolved tuple pin file of this run (default process/mvp-chain/tuple-pin.proposed.json)
  MVP_IDENTITY_FILE   candidate identity inputs (default process/mvp-acceptance/candidate-identity.inputs.json)
  MVP_APPLICABILITY   the applicability mapping (default process/mvp-acceptance/mvp-applicability.proposed.v1.json)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def mapping_path() -> Path:
    return Path(os.environ.get("MVP_APPLICABILITY") or ROOT / "process" / "mvp-acceptance" / "mvp-applicability.proposed.v1.json")


def identity_path() -> Path:
    return Path(os.environ.get("MVP_IDENTITY_FILE") or ROOT / "process" / "mvp-acceptance" / "candidate-identity.inputs.json")


def pin_path() -> Path:
    return Path(os.environ.get("MVP_PIN_FILE") or ROOT / "process" / "mvp-chain" / "tuple-pin.proposed.json")


@pytest.fixture(scope="session")
def mapping():
    return json.loads(mapping_path().read_text())


@pytest.fixture(scope="session")
def hub_ingress_dir():
    raw = os.environ.get("MVP_HUB_DIR")
    if not raw:
        pytest.fail("MVP_HUB_DIR is not set; the ingress cannot be inspected")
    path = Path(raw) / "tools" / "mvp_ingress"
    if not path.is_dir():
        pytest.fail(f"{path} is not a directory")
    return path


@pytest.fixture(scope="session")
def repo_root():
    return ROOT


@pytest.fixture(scope="session")
def identity_file():
    return identity_path()


@pytest.fixture(scope="session")
def pin_file():
    return pin_path()
