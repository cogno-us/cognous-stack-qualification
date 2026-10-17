"""N4 worked example: effect-time refusal after a grant revocation, asserted with the refusal-test template.

SPDX-License-Identifier: Apache-2.0

Scenario: the grant is revoked at the control-plane resolver after the decision and before the effect. Route A (control plane
revalidation, runtime PinnedControlPlaneExecutor, effective-grant destination), real objects from the pinned reference.
This is a template example, not a catalog scenario; it maps to no requirement row and changes no verdict.

Provenance of "expected today" (leg e): ``run``. The expected reason code, refusal stage and version strings below were read off
a run against the pinned reference (see the evidence property), not taken from the source. Where a future scenario takes its
expectation from the code instead, it must say ``code-reading`` and cite file and symbol.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _refusal_template as T  # noqa: E402
import _d02_d05_d09_helpers as H  # noqa: E402
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401,E402  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

GRANT = 'urn:cognous:grant:routine-1'
SPEC = T.RefusalSpec(
    name='n4-example-route-a-grant-revoked-before-effect',
    reasons=('grant_revoked',),
    changed_inputs=(T.ChangedInput('grant', GRANT),),
    provenance=T.Provenance('run', 'pinned reference (profile r4 control plane and runtime) via this test, record_property n4_refusal_template'),
    revocation=True,
    stage='effect_time_revalidation')


def test_n4_example_revoked_grant_refusal_through_the_template(tmp_path, record_property):
    adapter = T.RouteAAdapter()
    result = T.run_refusal_scenario(adapter, SPEC, tmp_path, pytest.MonkeyPatch)
    assert result.legs_passed == T.LEGS
    # Holder classification: the grant produced a refusal; the mandate and identity were never probed and produced none.
    holders = [{'holder_id': GRANT, 'kind': 'grant'},
               {'holder_id': 'urn:cognous:issuance:1', 'kind': 'mandate'},
               {'holder_id': 'urn:cognous:identity:refund-agent-1', 'kind': 'identity'}]
    report = T.classify_holders(holders, [result.refusal_row])
    assert [h['holder_id'] for h in report['witnessed_refusals']] == [GRANT]
    assert [h['holder_id'] for h in report['unenumerated_authority_needing_containment']] == ['urn:cognous:issuance:1', 'urn:cognous:identity:refund-agent-1']
    assert {h['classification'] for h in report['unenumerated_authority_needing_containment']} == {T.CLASSIFICATION_UNKNOWN}
    record_property('n4_refusal_template', T.report_json(result, report))


def test_n4_example_missing_provenance_label_is_refused_before_any_run(tmp_path):
    bad = T.RefusalSpec(SPEC.name, SPEC.reasons, SPEC.changed_inputs, T.Provenance('guess', 'somewhere'), True, SPEC.stage)
    with pytest.raises(T.RefusalTemplateFailure) as caught:
        T.run_refusal_scenario(T.RouteAAdapter(), bad, tmp_path, pytest.MonkeyPatch)
    assert caught.value.leg == 'e'


def test_n4_example_wrong_expected_reason_fails_leg_b(tmp_path):
    wrong = T.RefusalSpec(SPEC.name, ('grant_expired',), SPEC.changed_inputs, SPEC.provenance, True, SPEC.stage)
    with pytest.raises(T.RefusalTemplateFailure) as caught:
        T.run_refusal_scenario(T.RouteAAdapter(), wrong, tmp_path, pytest.MonkeyPatch)
    assert caught.value.leg == 'b'


def test_n4_example_change_that_does_not_refuse_fails_leg_a(tmp_path):
    adapter = T.RouteAAdapter(change=lambda h, flow: None)  # nothing changed: the effect reaches the destination
    with pytest.raises(T.RefusalTemplateFailure) as caught:
        T.run_refusal_scenario(adapter, SPEC, tmp_path, pytest.MonkeyPatch)
    assert caught.value.leg == 'a'
