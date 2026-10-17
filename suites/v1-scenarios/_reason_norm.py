"""Shared reason/exception-text normaliser for scenario observations.

SPDX-License-Identifier: Apache-2.0

Strips run-specific identifiers (UUIDs, long hex digests) so that two runs of the same case can be compared
for determinism. Any raised or exception string recorded into an observation must pass through here, so a
real rejection reports as a clean FAIL rather than a spurious determinism mismatch caused by a random id
inside the message. It only rewrites the recorded text; it never alters what is asserted.
"""
from __future__ import annotations

import re

_UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
_HEX_RE = re.compile(r'sha256:[0-9a-f]{64}|[0-9a-f]{32,}')


def normalise_reason(text):
    """Strip run-specific identifiers so two runs can be compared."""
    return _HEX_RE.sub('<hex>', _UUID_RE.sub('<uuid>', str(text)))[:200]


def exc_summary(exc):
    """'TypeName: normalised message' for recording an exception in an observation."""
    return f'{type(exc).__name__}: {normalise_reason(exc)}'
