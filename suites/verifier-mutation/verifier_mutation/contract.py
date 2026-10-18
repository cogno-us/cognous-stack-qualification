"""The ODES ``verification-report`` validator, vendored at ``../contract/verification-report`` (see its CONTRACT.json).

The harness validates every report it emits and every per-trace report a verifier prints with this reference validator. It does
not re-implement the contract.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

VENDORED = Path(__file__).resolve().parents[1] / "contract" / "verification-report"
_CACHE: dict[Path, ModuleType] = {}


def load(contract_dir: Path | None = None) -> ModuleType:
    directory = (contract_dir or VENDORED).resolve()
    if directory not in _CACHE:
        spec = importlib.util.spec_from_file_location(f"_odes_verification_report_{len(_CACHE)}", directory / "validate.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # dataclasses in the validator need the module registered
        spec.loader.exec_module(module)
        _CACHE[directory] = module
    return _CACHE[directory]
