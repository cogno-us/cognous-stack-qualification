"""Evidence pack probes (PROBE2_PACK_DIR): the installed-distribution check for the Replay dependency.

The check that the importable Replay code is the pinned revision must be about the code that is imported, not only about the
installed distribution metadata. Each case runs in a child interpreter whose sys.path holds a throw-away directory layout:
``site-real`` carries a package and distribution metadata naming the pinned commit, ``site-other`` carries a different package of the
same import name. The control puts only the real layout on the path (the check passes); the probe puts the other layout ahead of
it (the check must refuse because the code that would be imported is not the one the metadata describes).
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from _support import pending
from conftest import checkout

PINNED = "1" * 40

CHILD = textwrap.dedent('''
    import json, sys
    pack_src, expected, *paths = sys.argv[1:]
    sys.path[:0] = paths          # earlier entries win
    sys.path.insert(len(paths), pack_src)
    sys.dont_write_bytecode = True
    import agent_governance_evidence_pack.importer as imp
    try:
        imp._require_pinned_replay_distribution(expected)
        print(json.dumps({"refused": False}))
    except imp.ImportContractError as exc:
        print(json.dumps({"refused": True}))
''')


@pytest.fixture(autouse=True)
def _pin():
    checkout("PROBE2_PACK_DIR")


def layout(root, name, *, with_metadata):
    site = root / name
    package = site / "agent_replay_bundle"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(f"WHICH = {name!r}\n")
    if with_metadata:
        info = site / "agent_replay_bundle-0.1.0.dist-info"
        info.mkdir()
        (info / "METADATA").write_text("Metadata-Version: 2.1\nName: agent-replay-bundle\nVersion: 0.1.0\n")
        (info / "direct_url.json").write_text(json.dumps(
            {"url": "https://github.com/cogno-us/cognous-replay-bundle", "vcs_info": {"vcs": "git", "commit_id": PINNED}}))
        (info / "RECORD").write_text("agent_replay_bundle/__init__.py,,\n")
    return site


def refused(tmp_path, *sites, expected=PINNED):
    script = tmp_path / "child.py"
    script.write_text(CHILD)
    pack_src = str(Path(checkout("PROBE2_PACK_DIR")) / "src")
    out = subprocess.run([sys.executable, str(script), pack_src, expected, *map(str, sites)], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-400:]
    return json.loads(out.stdout.splitlines()[-1])["refused"]


def test_distribution_and_code_together_are_accepted(tmp_path):
    real = layout(tmp_path, "site-real", with_metadata=True)
    assert refused(tmp_path, real) is False


def test_other_pinned_commit_is_refused(tmp_path):
    real = layout(tmp_path, "site-real", with_metadata=True)
    assert refused(tmp_path, real, expected="2" * 40) is True


@pending()
def test_code_ahead_on_the_path_of_the_distribution_is_refused(tmp_path):
    real = layout(tmp_path, "site-real", with_metadata=True)
    other = layout(tmp_path, "site-other", with_metadata=False)
    assert refused(tmp_path, other, real) is True
