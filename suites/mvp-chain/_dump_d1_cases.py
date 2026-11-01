"""Run inside the pinned hub checkout (cwd = hub root): dump D1's adversarial inputs as JSON. Qualification reuses the inputs only;
it does not reuse D1's expected codes or any D1 verdict.

SPDX-License-Identifier: Apache-2.0
"""
import json
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
import tests.test_mvp_ingress_boundary as t  # noqa: E402

print(json.dumps({
    "cases_hex": [c.values[0].hex() for c in t.CASES],
    "good": t.GOOD,
    "simulate_hex": [b.hex() for b in t.SIMULATE],
    "forbidden_members": t.FORBIDDEN_MEMBERS,
    "hand_built_claim": t.HAND_BUILT_CLAIM,
}))
