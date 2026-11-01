"""N4 refusal-test template: one reusable shape for every effect-time refusal scenario.

SPDX-License-Identifier: Apache-2.0

A refusal scenario built on this module asserts five things, in this order, and fails with the leg letter that broke:

  (a) negative      the destination ledger holds no row for the effect id (read through an independent connection);
  (b) refusal row   the refusal row names the effect id, the failed check (reason code) and the input versions
                    (expected and observed) of every input the scenario declares as changed;
  (c) control       the identical call with the grant unchanged reaches the destination (same effect id, one ledger row,
                    no refusal row). A revocation scenario also asserts that the permitted control ran at the same
                    enforcement point as the refusal and that the policy version it observed there equals the policy
                    version the refusal row observed;
  (d) mutation      with the refusal writer disabled the same scenario must FAIL leg (b) (the refusal itself still
                    blocks the effect; only the evidence row disappears). A mutation that survives is a template failure;
  (e) provenance    the scenario states whether "expected today" comes from reading the code or from a run, and names
                    the source. It is reported with the result, never inferred.

Holder classification (see ``classify_holders``): a holder of authority that produced no refusal is ``coverage_unknown``.
It is never reported as "expired", "revoked" or "inactive". The report carries two lists: witnessed refusals, and
unenumerated authority needing containment.

The module is route-agnostic. A scenario supplies an ``Adapter`` (see ``RouteAAdapter`` for the control plane, runtime and
effective-grant destination used by the V1 suites). Nothing here changes a component, a pin or a default; the only
mutation is an instance-level replacement of the refusal writer, applied to a disposable flow.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import sqlite3
import sys
from typing import Any, Callable, Iterable

PROVENANCE_KINDS = ('code-reading', 'run')
CLASSIFICATION_WITNESSED = 'witnessed_refusal'
CLASSIFICATION_UNKNOWN = 'coverage_unknown'
CLASSIFICATIONS = (CLASSIFICATION_WITNESSED, CLASSIFICATION_UNKNOWN)
LEGS = ('a', 'b', 'c', 'd', 'e')


class RefusalTemplateFailure(AssertionError):
    """A template leg failed. ``leg`` is one of ``LEGS``."""

    def __init__(self, leg: str, message: str):
        super().__init__(f'refusal template leg ({leg}) failed: {message}')
        self.leg = leg
        self.detail = message


@dataclasses.dataclass(frozen=True)
class Provenance:
    """Leg (e): where "expected today" comes from. ``kind`` is ``code-reading`` or ``run``; ``source`` names the evidence
    (file and symbol for a code reading; pinned commit plus the test or run id for a run)."""
    kind: str
    source: str

    def validate(self) -> None:
        if self.kind not in PROVENANCE_KINDS:
            raise RefusalTemplateFailure('e', f'provenance kind must be one of {PROVENANCE_KINDS}, got {self.kind!r}')
        if not str(self.source).strip():
            raise RefusalTemplateFailure('e', 'provenance must name its source')


@dataclasses.dataclass(frozen=True)
class ChangedInput:
    """An input the scenario changes; the refusal row must carry both of its versions."""
    input_type: str
    input_id: str


@dataclasses.dataclass(frozen=True)
class RefusalSpec:
    name: str
    reasons: tuple[str, ...]                 # failed check: every code must appear in the refusal row's reasons
    changed_inputs: tuple[ChangedInput, ...]  # inputs whose expected and observed versions the row must carry
    provenance: Provenance
    revocation: bool = False                  # revocation probes also run the policy-bound permitted control
    stage: str | None = None                  # optional: required refusal stage (for example effect_time_revalidation)


class Adapter:
    """What a route must provide. All methods take the flow object returned by ``build``."""

    def build(self, work: pathlib.Path, mp: Any) -> Any:  # fresh, identical flow per call
        raise NotImplementedError

    def apply_change(self, flow: Any) -> None:  # the authority change under test
        raise NotImplementedError

    def execute(self, flow: Any) -> Any:  # the supported effect-time call; returns an opaque outcome
        raise NotImplementedError

    def effect_id(self, flow: Any) -> str:
        raise NotImplementedError

    def ledger_effect_ids(self, flow: Any) -> list[str]:  # independent read of the destination ledger
        raise NotImplementedError

    def refusal_rows(self, flow: Any) -> list[dict]:  # refusal rows as plain dicts
        raise NotImplementedError

    def disable_refusal_writer(self, flow: Any) -> None:  # leg (d); instance level only
        raise NotImplementedError

    def policy_versions_observed_at_enforcement(self, flow: Any, stage: str | None) -> dict[str, str]:
        """policy input id -> version observed by the check at the enforcement point (control side)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------------------------- checks

def _row_for(adapter: Adapter, flow: Any, effect_id: str) -> list[dict]:
    return [r for r in adapter.refusal_rows(flow) if r.get('effect_id') == effect_id]


def check_negative(adapter: Adapter, flow: Any, effect_id: str) -> None:
    """Leg (a)."""
    ledger = adapter.ledger_effect_ids(flow)
    if effect_id in ledger:
        raise RefusalTemplateFailure('a', f'destination ledger has a row for refused effect id {effect_id} ({len(ledger)} row(s))')


def check_refusal_row(adapter: Adapter, flow: Any, effect_id: str, spec: RefusalSpec) -> dict:
    """Leg (b). Returns the matching refusal row."""
    rows = _row_for(adapter, flow, effect_id)
    if not rows:
        raise RefusalTemplateFailure('b', f'no refusal row names effect id {effect_id}')
    row = rows[-1]
    missing = [code for code in spec.reasons if code not in (row.get('reasons') or [])]
    if missing:
        raise RefusalTemplateFailure('b', f'refusal row does not name failed check(s) {missing}; row reasons {row.get("reasons")}')
    if spec.stage is not None and row.get('stage') != spec.stage:
        raise RefusalTemplateFailure('b', f'refusal stage {row.get("stage")!r} != required {spec.stage!r}')
    changed = {(c.get('input_type'), c.get('input_id')): c for c in (row.get('changed_inputs') or [])}
    for want in spec.changed_inputs:
        got = changed.get((want.input_type, want.input_id))
        if got is None:
            raise RefusalTemplateFailure('b', f'refusal row does not name changed input {want.input_type}:{want.input_id}')
        if not got.get('expected_version') or not got.get('observed_version'):
            raise RefusalTemplateFailure('b', f'refusal row lacks expected/observed version for {want.input_type}:{want.input_id}: {got}')
    return row


def policy_versions_in_row(row: dict) -> dict[str, str]:
    """Policy versions the refusal's own resolution observed (input id -> version)."""
    out: dict[str, str] = {}
    for item in row.get('resolution_inputs') or []:
        if item.get('input_type') == 'policy':
            version = (item.get('observed') or {}).get('version')
            if version is not None:
                out[item['input_id']] = str(version)
    return out


def check_control(adapter: Adapter, control_flow: Any, effect_id: str, spec: RefusalSpec, refusal_row: dict) -> dict:
    """Leg (c). ``control_flow`` is a fresh identical flow with NO change applied, executed through the same call."""
    control_id = adapter.effect_id(control_flow)
    if control_id != effect_id:
        raise RefusalTemplateFailure('c', f'control is not the identical call: effect id {control_id} != refused effect id {effect_id}')
    ledger = adapter.ledger_effect_ids(control_flow)
    if ledger.count(effect_id) != 1:
        raise RefusalTemplateFailure('c', f'control did not reach the destination exactly once (rows for effect id: {ledger.count(effect_id)})')
    if _row_for(adapter, control_flow, effect_id):
        raise RefusalTemplateFailure('c', 'control produced a refusal row')
    report = {'control_effect_rows': ledger.count(effect_id)}
    if spec.revocation:
        stage = refusal_row.get('stage')
        observed_at_control = adapter.policy_versions_observed_at_enforcement(control_flow, stage)
        observed_in_refusal = policy_versions_in_row(refusal_row)
        if not observed_in_refusal or not observed_at_control:
            raise RefusalTemplateFailure('c', 'revocation control needs a policy version observed at the enforcement point on both sides '
                                              f'(control {observed_at_control}, refusal {observed_in_refusal})')
        if observed_at_control != observed_in_refusal:
            raise RefusalTemplateFailure('c', f'permitted control observed policy {observed_at_control} but the refusal observed {observed_in_refusal}: '
                                              'the control is not bound to the policy version seen at the enforcement point')
        report.update(control_enforcement_stage=stage, bound_policy_versions=observed_at_control)
    return report


# ---------------------------------------------------------------------------------------------- classification

def classify_holders(holders: Iterable[dict], refusal_rows: Iterable[dict]) -> dict:
    """Two lists. A holder is witnessed only if a refusal row names it as a changed input or by effect id.

    A holder with no refusal is ``coverage_unknown``: no refusal was produced, so nothing is known about whether its
    authority still stands. It is never labelled "expired" (or revoked, lapsed, inactive).

    ``holders``: dicts with ``holder_id`` and optional ``kind`` and ``effect_ids``.
    """
    rows = list(refusal_rows)
    witnessed, unenumerated = [], []
    for holder in holders:
        hid = holder['holder_id']
        effects = set(holder.get('effect_ids') or ())
        hits = [r for r in rows if hid in {c.get('input_id') for c in (r.get('changed_inputs') or [])} or r.get('effect_id') in effects]
        if hits:
            witnessed.append({'holder_id': hid, 'kind': holder.get('kind'), 'classification': CLASSIFICATION_WITNESSED,
                              'refusals': [{'refusal_id': r.get('refusal_id'), 'effect_id': r.get('effect_id'), 'reasons': list(r.get('reasons') or [])} for r in hits]})
        else:
            unenumerated.append({'holder_id': hid, 'kind': holder.get('kind'), 'classification': CLASSIFICATION_UNKNOWN,
                                 'note': 'no refusal produced; authority status unknown, needs containment or a probe'})
    return {'witnessed_refusals': witnessed, 'unenumerated_authority_needing_containment': unenumerated}


# ---------------------------------------------------------------------------------------------- driver

@dataclasses.dataclass
class RefusalResult:
    name: str
    effect_id: str
    refusal_row: dict
    control: dict
    mutation: dict
    provenance: Provenance
    legs_passed: tuple[str, ...]

    def evidence(self) -> dict:
        return {'scenario': self.name, 'effect_id': self.effect_id, 'legs_passed': list(self.legs_passed),
                'refusal': {k: self.refusal_row.get(k) for k in ('refusal_id', 'stage', 'reasons', 'changed_inputs')},
                'control': self.control, 'mutation': self.mutation,
                'expected_today_provenance': {'kind': self.provenance.kind, 'source': self.provenance.source}}


def run_refusal_scenario(adapter: Adapter, spec: RefusalSpec, work_root: pathlib.Path, mp_factory: Callable[[], Any]) -> RefusalResult:
    """Run legs (a)-(e). ``mp_factory`` returns a fresh ``pytest.MonkeyPatch`` (undone by the driver). Raises on the first failed leg."""
    work_root = pathlib.Path(work_root)

    def fresh(label: str):
        path = work_root / label
        path.mkdir(parents=True, exist_ok=False)
        mp = mp_factory()
        return adapter.build(path, mp), mp

    spec.provenance.validate()  # (e) is checked up front: an unlabelled expectation never reaches the other legs
    mps = []
    try:
        flow, mp = fresh('refused'); mps.append(mp)
        effect_id = adapter.effect_id(flow)
        adapter.apply_change(flow)
        adapter.execute(flow)
        check_negative(adapter, flow, effect_id)                         # (a)
        row = check_refusal_row(adapter, flow, effect_id, spec)         # (b)

        control_flow, mp = fresh('control'); mps.append(mp)
        adapter.execute(control_flow)
        control = check_control(adapter, control_flow, effect_id, spec, row)  # (c)

        mutant, mp = fresh('mutant'); mps.append(mp)                    # (d)
        adapter.disable_refusal_writer(mutant)
        adapter.apply_change(mutant)
        adapter.execute(mutant)
        mutation = {'writer_disabled': True}
        try:
            check_refusal_row(adapter, mutant, adapter.effect_id(mutant), spec)
        except RefusalTemplateFailure as caught:
            if caught.leg != 'b':
                raise
            mutation.update(detected=True, failed_leg='b', detail=caught.detail)
        else:
            raise RefusalTemplateFailure('d', 'mutation survived: with the refusal writer disabled leg (b) still passed')
        # The refusal itself must still block the effect; only the evidence row is removed.
        check_negative(adapter, mutant, adapter.effect_id(mutant))
        mutation['effect_still_blocked'] = True
        return RefusalResult(spec.name, effect_id, row, control, mutation, spec.provenance, LEGS)
    finally:
        for mp in mps:
            mp.undo()


# ---------------------------------------------------------------------------------------------- route A adapter

class RouteAAdapter(Adapter):
    """Control plane revalidation + runtime PinnedControlPlaneExecutor + effective-grant destination (the V1 reference).

    Uses the real objects built by ``suites/v1-scenarios/_d02_d05_d09_helpers`` (needs ``SCN_COMPONENTS_DIR``; the pins are
    verified pristine by that module). ``change`` is a callable ``(helpers, flow) -> None``; the default revokes the grant at
    the control-plane resolver.
    """

    def __init__(self, change: Callable[[Any, Any], None] | None = None):
        here = pathlib.Path(__file__).resolve().parent / 'v1-scenarios'
        if str(here) not in sys.path:
            sys.path.insert(0, str(here))
        import _d02_d05_d09_helpers as H  # noqa: E402  (lazy: importing this module must not need the pinned reference)
        self.H = H
        self._change = change or (lambda h, flow: h.revoke_resolver(flow))

    def build(self, work, mp):
        return self.H.flow_a(work, mp)

    def apply_change(self, flow):
        self._change(self.H, flow)

    def execute(self, flow):
        return self.H.execute_a(flow)

    def effect_id(self, flow):
        return flow.d.effect_id

    def ledger_effect_ids(self, flow):
        uri = pathlib.Path(flow.dest.path).resolve().as_uri() + '?mode=ro'
        conn = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            return [r[0] for r in conn.execute('SELECT effect_id FROM effects ORDER BY effect_id')]
        finally:
            conn.close()

    def refusal_rows(self, flow):
        return [r.model_dump(mode='json') for r in flow.f.records.load().refusals]

    def disable_refusal_writer(self, flow):
        flow.f.records.append_refusal = lambda value: None  # instance level; the class and the pin are untouched

    def policy_versions_observed_at_enforcement(self, flow, stage):
        # The refusal stage 'effect_time_revalidation' is recorded by the 'effect' resolution check on the control side.
        wanted = 'effect' if stage in (None, 'effect_time_revalidation') else stage
        checks = [c.model_dump(mode='json') for c in flow.f.records.load().resolution_checks if c.stage == wanted]
        out: dict[str, str] = {}
        for check in checks[-1:]:
            for item in check.get('inputs') or []:
                if item.get('input_type') == 'policy' and (item.get('observed') or {}).get('version') is not None:
                    out[item['input_id']] = str(item['observed']['version'])
        return out


def report_json(result: RefusalResult, classification: dict) -> str:
    """Stable text for ``record_property``: the result evidence plus the two classification lists."""
    return json.dumps({**result.evidence(), 'holder_classification': classification}, indent=2, sort_keys=True, default=str)
