#!/usr/bin/env python3
"""Builds data/fixtures.json (fixture library plus a per-control fixture map) from data/negative-controls.jsonl.

SPDX-License-Identifier: Apache-2.0
Usage: build_fixtures.py <PACKAGE_DIR>   (stdlib only). Definitions only; it creates no key, record, claim or database.
"""
import json, re, sys, collections as C

P = sys.argv[1].rstrip('/') + '/'
LIB = {
 'FXB-CLOCK': ('Controllable clock', 'A clock schedule the runner sets (lock-time clock, check-time clock, rollback jump). Reusable now.', 'READY_NO_V1_CODE'),
 'FXB-SETS': ('Caller and registry set grids', 'The five-set relation grid in data/fixture-grids.json. Reusable now.', 'READY_NO_V1_CODE'),
 'FXB-AGES': ('Age value, boundary and invalid-input grids', 'Valid pairs, invalid inputs, boundary offsets in data/fixture-grids.json. Reusable now.', 'READY_NO_V1_CODE'),
 'FXB-KEYS': ('Synthetic signing keys', 'Throw-away key pairs generated at run time and discarded: signer A, signer B, a revoked key, an unknown key. Never an operational root. Verifier adapter format is not final.', 'NEEDS_V1_FORMAT'),
 'FXB-TRUST': ('Trust snapshot', 'Snapshot with version, expiry, per-scope min_epochs and issuer/key revocations; stale, expired and downgraded variants.', 'NEEDS_V1_FORMAT'),
 'FXB-RECORD': ('Typed registry records', 'Records for the five-set family and the F4/F5 age families: valid, widened, dropped field, unknown family, re-digested, wrong participation.', 'NEEDS_V1_FORMAT'),
 'FXB-SELECT': ('Selection statements', 'Select and withdraw statements with epochs, supersession, validity interval and scope key.', 'NEEDS_V1_FORMAT'),
 'FXB-CALLER': ('Caller policies and profiles', 'Caller LocalExecutionPolicy sets; Control Plane caller age values and ActionClass profile.', 'NEEDS_V1_FORMAT'),
 'FXB-CLAIM': ('Authorization claims', 'Claim with and without the claim-carried effective-policy binding; substituted, swapped and missing variants.', 'NEEDS_V1_FORMAT'),
 'FXB-APPROVAL': ('Approvals', 'Approval bound to profile P0 and to narrowed profile P1, with approval generation; the narrow-then-withdraw sequence.', 'NEEDS_V1_FORMAT'),
 'FXB-STATE': ('Durable-state images', 'SQLite images of selection state, revoked set and activation log: healthy, truncated, missing table, corrupted rows, restored-older, never seeded from a claim.', 'NEEDS_V1_FORMAT'),
 'FXB-RACE': ('Transaction-stage barriers', 'Hooks at named transaction stages (such as the destination _transaction_stage) to order revocation against the commit lock; repetition and seed recorded.', 'NEEDS_V1_FORMAT'),
 'FXB-ROUTE': ('Route hosts', 'A Route B atomic host (V1) and a Route A host (characterization only, never credited).', 'NEEDS_V1_FORMAT'),
 'FXB-EVIDENCE': ('Receipts, failure rows and replay inputs', 'Committed receipts and failure rows carrying identity and exact causes; substituted and omitted identity variants.', 'NEEDS_V1_FORMAT'),
}
CLASS = {
 'forged_selection': ['FXB-KEYS', 'FXB-TRUST', 'FXB-RECORD', 'FXB-SELECT'],
 'policy_digest_substitution': ['FXB-RECORD', 'FXB-SELECT', 'FXB-CLAIM'],
 'claim_identity_mismatch': ['FXB-CLAIM', 'FXB-SELECT', 'FXB-STATE', 'FXB-ROUTE'],
 'expiry': ['FXB-SELECT', 'FXB-TRUST', 'FXB-CLOCK', 'FXB-STATE', 'FXB-ROUTE'],
 'revocation': ['FXB-SELECT', 'FXB-TRUST', 'FXB-STATE', 'FXB-CLOCK', 'FXB-ROUTE'],
 'concurrent_revocation': ['FXB-RACE', 'FXB-STATE', 'FXB-CLOCK', 'FXB-ROUTE'],
 'required_policy_absence': ['FXB-SELECT', 'FXB-TRUST', 'FXB-STATE', 'FXB-CALLER', 'FXB-ROUTE'],
 'scope_required_ratchet': ['FXB-SELECT', 'FXB-STATE', 'FXB-CALLER'],
 'invalid_optional_as_withdrawal': ['FXB-SELECT', 'FXB-RECORD', 'FXB-CALLER', 'FXB-EVIDENCE'],
 'epoch_downgrade': ['FXB-SELECT', 'FXB-STATE', 'FXB-CLAIM'],
 'trust_snapshot_version': ['FXB-TRUST', 'FXB-KEYS'],
 'stale_approval_revival': ['FXB-APPROVAL', 'FXB-CALLER', 'FXB-AGES'],
 'restore_rollback': ['FXB-STATE', 'FXB-SELECT', 'FXB-TRUST'],
 'durable_state_loss': ['FXB-STATE', 'FXB-ROUTE'],
 'deny_all_vs_evaluator': ['FXB-SETS', 'FXB-CALLER', 'FXB-RECORD', 'FXB-EVIDENCE'],
 'freshness_invalid_input': ['FXB-AGES', 'FXB-CALLER', 'FXB-RECORD'],
 'freshness_boundary': ['FXB-AGES', 'FXB-CLOCK', 'FXB-CALLER'],
 'outage_extension': ['FXB-AGES', 'FXB-CALLER', 'FXB-CLOCK'],
 'confused_deputy': ['FXB-RECORD', 'FXB-SELECT', 'FXB-CLAIM'],
 'sync_manufacture': ['FXB-STATE', 'FXB-SELECT', 'FXB-TRUST'],
 'string_decision': ['FXB-EVIDENCE', 'FXB-CALLER', 'FXB-ROUTE'],
 'evidence_integrity': ['FXB-EVIDENCE', 'FXB-CLAIM'],
 'hostile_input': ['FXB-RECORD', 'FXB-STATE'],
 'transaction_integrity': ['FXB-RACE', 'FXB-STATE', 'FXB-ROUTE'],
 'route_a_bypass': ['FXB-ROUTE', 'FXB-SELECT', 'FXB-CLAIM'],
}
rows = [json.loads(l) for l in open(P + 'data/negative-controls.jsonl') if l.strip()]
errs, per = [], []
for r in rows:
    m = re.match(r'(FX-[A-Za-z]+-\d+)', r['synthetic_fixture'])
    if not m: errs.append(r['control_id'] + ' has no FX id'); continue
    base = CLASS.get(r['attack_class'])
    if base is None: errs.append(r['control_id'] + ' unmapped class ' + r['attack_class']); continue
    ready = all(LIB[b][2] == 'READY_NO_V1_CODE' for b in base)
    per.append({'fixture_id': m.group(1), 'control_id': r['control_id'], 'attack_class': r['attack_class'], 'description': r['synthetic_fixture'],
                'base_fixtures': base, 'readiness': 'READY_NO_V1_CODE' if ready else 'DEFINITION_ONLY_NEEDS_V1_FORMAT', 'status': r['status']})
ids = [p['fixture_id'] for p in per]
if len(ids) != len(set(ids)): errs.append('duplicate fixture ids')
if errs: print('FAIL', errs[:10]); sys.exit(1)
out = {'status': 'PREPARATION: definitions only; no key, record, claim or database has been created',
       'library': [{'id': k, 'name': v[0], 'definition': v[1], 'readiness': v[2]} for k, v in LIB.items()],
       'per_control': per}
json.dump(out, open(P + 'data/fixtures.json', 'w'), indent=1, ensure_ascii=False)
rc = C.Counter(p['readiness'] for p in per)
print('OK', len(per), dict(rc))
