"""Replay probes for the input-bound and value-shape hardening of the final pin round (qualification first).

A signature value must be 64 lowercase hex characters before any comparison, the dictionary import API must refuse input it
cannot bound (instead of exhausting the stack), and text taken from a bundle must not carry terminal control characters into the
command line output. They are red at Replay 46e8bd7c by design and green at the final pin. Run against PROBE_REPLAY_DIR.
"""
import pytest

from conftest import pin_dir


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_REPLAY_DIR")


@pytest.mark.parametrize("value", ["", "zz", "A" * 64, "a" * 63, "a" * 65, "é" * 64, "٣" * 64, ("a" * 64) + "\n"])
def test_probe_hmac_value_must_be_lowercase_sha256_hex(value):
    from agent_replay_bundle.signing import is_hex_digest
    assert not is_hex_digest(value)


def test_probe_hmac_value_accepts_lowercase_hex():
    from agent_replay_bundle.signing import is_hex_digest
    assert is_hex_digest("0123456789abcdef" * 4)


def test_probe_dictionary_api_refuses_input_nested_beyond_its_bound():
    from agent_replay_bundle import ImportContractError, import_bounded_workflow
    from agent_replay_bundle import importers
    value = []
    for _ in range(importers.MAX_RECORD_DEPTH + 5):
        value = [value]
    with pytest.raises(ImportContractError):
        import_bounded_workflow({"x-deep": value}, control_plane_revision=importers.CONTROL_PLANE_P2_REVISION)


def test_probe_cli_text_from_a_bundle_carries_no_control_characters():
    from agent_replay_bundle.cli import _t
    out = _t("a\x1b[31mred\x07\r\nb")
    assert "\x1b" not in out and "\x07" not in out and "\r" not in out
