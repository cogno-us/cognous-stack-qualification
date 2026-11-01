"""Evidence pack probes for the renderer hardening of the final pin round (qualification first).

A backslash in pack text is escaped before a pipe in the Markdown renderer, so a table cell cannot be closed early by a
trailing backslash. Red at evidence pack 4fbbd344 by design, green at the final pin. Run against PROBE_EVIDENCE_PACK_DIR.
"""
from pathlib import Path

import pytest

from conftest import pin_dir


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_EVIDENCE_PACK_DIR")


def test_probe_markdown_renderer_escapes_a_backslash_before_a_pipe():
    from agent_governance_evidence_pack.loader import load_evidence_pack
    from agent_governance_evidence_pack.renderer import render_markdown
    pack = load_evidence_pack(Path(pin_dir("PROBE_EVIDENCE_PACK_DIR")) / "examples" / "customer_service_agent_evidence_pack.json")
    pack.agent_overview.owner = "a\\|b\\"
    text = render_markdown(pack)
    assert "a\\|b\\ " not in text and "a\\|b\\\n" not in text
    assert "a&#92;\\|b&#92;" in text
