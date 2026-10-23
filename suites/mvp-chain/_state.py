"""Shared mutable state of one mvp-chain run: the environment verdict inputs and the raw observation record.

SPDX-License-Identifier: Apache-2.0
Observations are facts the harness read from the components. Nothing in this module or in _chain.py computes a verdict.
"""
from __future__ import annotations

import os
from pathlib import Path

OBS: dict = {}
ENV: dict = {"problems": [], "dirs": {}, "expected": {}, "wired": False}
RESULTS_DIR: Path | None = None


def results_dir() -> Path:
    global RESULTS_DIR
    if RESULTS_DIR is None:
        import tempfile
        raw = os.environ.get("MVP_RESULTS_DIR")
        RESULTS_DIR = Path(raw) if raw else Path(tempfile.mkdtemp(prefix="mvp-chain-"))
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR
