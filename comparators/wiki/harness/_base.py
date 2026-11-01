"""Locating the pinned qualification and hub trees; no pinned file is copied or edited.

Environment:
  SCN_QUAL_SUITE_DIR  suites/cognous-open-control-stack of the pinned qualification checkout
                      (default: the suite directory of this repository)
  SCN_HUB_DIR         the hub checkout that holds reference_profiles/ (required; the hub revision is named in
                      comparators/digests.json under "hub")
No network access is used here or by any module of the package.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SUITE = REPO / 'suites' / 'cognous-open-control-stack'

# Full digests of the pinned scoring and application files (relative to the suite directory).
PINNED_SHA256 = {
    'tools/run_comparative_governance.py': 'b0a396b8d37645b257171d5668292a396acfdc1d540b7748f27dc8ccf9003159',
    'benchmarks/governance/adapters.py': '0ce74ab58c07b6ae7d3baaadcb9ce8a6d080c6347f25a8dcfe2b9e1585340c10',
    'benchmarks/governance/policy.rego': '712b0f8cda4de050bdf72c411bf79614a46cfc47837a560fc6f8efbd4df04f62',
    'benchmarks/governance/dependencies.json': 'b505ea1da7c3404dfa181696dcb4833befef547fe17823429bf11b5cfd4809aa',
    'benchmarks/governance/requirements.txt': 'affe2fce90ea7f0ebc15ca4fa4e33439c198acabd81140be98c16bf88270e095',
    'benchmarks/governance/corner-plan.json': '35ca4ee5a2b695f3a4655f97dbd3d949055895674001fc52ec020ff286eb0162',
    'benchmarks/governance/plan.json': '47f28898e342f9c6448943d5d2bc3daefeac536f3dff29c50e4def73cd9d1a63',
}
EVALUATE_SOURCE_SHA256 = '4fcd7eff77039cc0439c5324025b5ba54a35e83f3822ee5be6df6eccebb67ad5'


def suite_dir():
    return Path(os.environ.get('SCN_QUAL_SUITE_DIR', DEFAULT_SUITE)).resolve()


def hub_dir():
    value = os.environ.get('SCN_HUB_DIR')
    if not value:
        raise RuntimeError('SCN_HUB_DIR is not set: point it at a hub checkout that holds reference_profiles/')
    return Path(value).resolve()


def sha256_of(rel):
    return hashlib.sha256((suite_dir() / rel).read_bytes()).hexdigest()


def check_pins():
    """Refuse to continue when a pinned file differs from the recorded digest."""
    for rel, want in PINNED_SHA256.items():
        if sha256_of(rel) != want:
            raise RuntimeError('pinned file differs from the recorded digest: ' + rel)


def setup_paths():
    for p in (hub_dir(), suite_dir()):  # suite first on sys.path, hub merged as namespace package
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    check_pins()


def pinned_adapters():
    setup_paths()
    from benchmarks.governance import adapters
    return adapters


def pinned_runner():
    """Import the whole pinned runner file by path (its own module globals stay untouched)."""
    setup_paths()
    spec = importlib.util.spec_from_file_location('pinned_run_comparative_governance',
                                                  suite_dir() / 'tools/run_comparative_governance.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
