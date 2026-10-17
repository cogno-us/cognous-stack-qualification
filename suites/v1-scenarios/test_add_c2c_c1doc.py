"""Addendum row ADD-C2C-C1DOC - the same-host atomic profile is surfaced as optional C1 in the hub support documentation,
without being enabled by default and without enlarging its claims.

SPDX-License-Identifier: Apache-2.0

Requirement (Stokes addendum 8 P0): "Same-host atomic profile surfaced as C1 in support documentation without enabling it by
default". Previously a document review only; this module executes the review as text assertions against the hub checkout at the
frozen pin (SCN_HUB_DIR, verified pristine at 8517818fbf817897aacfb6fe7898c22aea46fd95) plus one behavioural check that the default
route does not activate the profile. No product text or code is changed.

Every case runs twice (D3) through the shared harness.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

import pytest

import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

NEGATORS = re.compile(r"\b(not|no|never|without|separate|neither|nor|optional|does not|unqualified|unchanged|remains?)\b", re.I)
STRICT_NEGATOR = re.compile(r"\b(not|no|never|without|neither|nor|unqualified)\b", re.I)


def _negated_before(sentence, match, window=70):
    """True when a strict negator occurs shortly BEFORE the claim term in the same sentence (a later 'not' does not rescue it)."""
    return STRICT_NEGATOR.search(sentence[max(0, match.start() - window):match.start()]) is not None
OVERCLAIMS = {
    'default': re.compile(r'\bdefault\b', re.I),
    'external': re.compile(r'\bexternal\b', re.I),
    'exactly-once': re.compile(r'exactly[- ]once', re.I),
    'distributed': re.compile(r'\bdistributed\b', re.I),
    'production': re.compile(r'\bproduction\b', re.I),
    'settlement': re.compile(r'\bsettlement\b', re.I),
    'selected': re.compile(r'\bselected\b', re.I),
}


def _hub():
    hub = os.environ.get('SCN_HUB_DIR')
    if not hub:
        pytest.fail('SCN_HUB_DIR is not set; the hub documentation at pin 8517818f cannot be checked (not skipped, not a pass)')
    from pristine_checkout import require_pristine
    require_pristine(hub, H.FROZEN_HUB, 'hub')
    return Path(hub)


def _sentences(text):
    flat = re.sub(r'\s+', ' ', re.sub(r'[|*`>#]', ' ', text))
    return [s.strip() for s in re.split(r'(?<=[.;])\s+', flat) if s.strip()]


def _c1_sentences(text):
    return [s for s in _sentences(text) if re.search(r'\bC1\b|same-host', s, re.I)]


def _release_status_violations(doc):
    checks = H.Checks()
    rows = [ln for ln in doc.splitlines() if ln.startswith('|')]
    c1 = [r for r in rows if re.search(r'\*\*C1\b', r)]
    c0 = [r for r in rows if re.search(r'\*\*C0\b', r)]
    c23 = [r for r in rows if re.search(r'\*\*C2/C3', r)]
    checks.equal((len(c0), len(c1), len(c23)), (1, 1, 1), 'release boundary table has exactly one C0, one C1 and one C2/C3 row')
    c1row = c1[0] if c1 else ''
    low = c1row.lower()
    for needle in ('optional', 'same-host', 'sqlite transaction', 'not enabled by the default release', 'not an external destination guarantee'):
        checks.expect(needle in low, f'C1 row lacks required statement: {needle!r}')
    checks.expect('selected default' not in low, 'C1 row must not be labelled the selected default')
    checks.expect('selected default' in (c0[0].lower() if c0 else ''), 'C0 remains the selected default')
    checks.expect('no release claim' in (c23[0].lower() if c23 else ''), 'C2/C3 keep "No release claim"')
    # Every sentence about C1 / same-host that uses a claim-enlarging term must also carry a negation/qualifier.
    unqualified = []
    for s in _c1_sentences(doc):
        for name, rx in OVERCLAIMS.items():
            for m in rx.finditer(s):
                if not _negated_before(s, m):
                    unqualified.append((name, s[:200]))
    checks.equal(unqualified, [], 'no C1/same-host sentence uses default/external/exactly-once/distributed/production/settlement/selected without a negation or qualifier')
    affirmative = [s[:200] for s in _c1_sentences(doc) if re.search(r'C1\b.{0,60}\b(is|are)\b.{0,30}\b(enabled|default|selected)\b', s, re.I) and not NEGATORS.search(s)]
    checks.equal(affirmative, [], 'no sentence affirms C1 is enabled/default/selected')
    checks.expect('separate profile evidence' in doc.lower() and 'not a 35-scenario release count' in doc.lower(),
                  'C1 profile CI evidence is kept separate from the 35-scenario release count')
    checks.expect('does not enable' in doc.lower() or 'not enabled' in doc.lower(), 'document states the default workflow does not enable the profile')

    return checks.violations


def test_add_c2c_c1doc_release_status_describes_optional_same_host_c1(request, record_property, tmp_path):
    hub = _hub()

    def trial(work, mp, checks):
        doc = (hub / 'docs/release-status.md').read_text()
        for v in _release_status_violations(doc):
            checks.violations.append(v)
        c1row = next((r for r in doc.splitlines() if re.search(r'\*\*C1\b', r) and r.startswith('|')), '')
        return {'document': 'docs/release-status.md', 'sha256': hashlib.sha256(doc.encode()).hexdigest(), 'c1_row': c1row.strip(),
                'c1_sentences_checked': len(_c1_sentences(doc)), 'hub_pin': H.FROZEN_HUB,
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-C1DOC', trial, expect_effects_gate=False)


def test_add_c2c_c1doc_readme_and_profile_docs_keep_c1_optional_without_enlarging_claims(request, record_property, tmp_path):
    hub = _hub()

    def trial(work, mp, checks):
        out = {}
        readme = (hub / 'README.md').read_text()
        profiles = (hub / 'docs/optional-execution-profiles.md').read_text()
        para = [p for p in re.split(r'\n\s*\n', readme) if 'same-host authority/effect profile' in p]
        checks.equal(len(para), 1, 'README has exactly one paragraph introducing the same-host authority/effect profile')
        p0 = (para[0] if para else '') + ' ' + (re.split(r'\n\s*\n', readme)[[i for i, p in enumerate(re.split(r'\n\s*\n', readme)) if 'same-host authority/effect profile' in p][0] + 1]
                                               if para else '')
        low = p0.lower()
        for needle in ('optional', 'does not enable it', 'external-destination atomicity', 'distributed authorization', 'production readiness'):
            checks.expect(needle in low, f'README profile paragraph lacks: {needle!r}')
        checks.expect(re.search(r'does not (establish|claim)[^.]*external-destination atomicity', low) is not None,
                      'README negates (does not establish) external-destination atomicity')
        checks.expect('mutually exclusive' in low and 'no combined guarantee' in low, 'README keeps refund-intent and authority/effect profiles exclusive with no combined guarantee')
        pl = profiles.lower()
        checks.expect('cooperating' in pl and 'same-host' in pl, 'optional-execution-profiles.md scopes the atomic profile to cooperating same-host participants')
        checks.expect('sacrifice availability' in pl, 'optional-execution-profiles.md discloses the availability trade-off')
        bad = [s[:200] for s in _c1_sentences(profiles) if re.search(r'external|distributed|exactly[- ]once|production', s, re.I) and not NEGATORS.search(s)]
        checks.equal(bad, [], 'optional-execution-profiles.md makes no unqualified external/distributed/exactly-once/production statement about the profile')
        out['readme_paragraph'] = re.sub(r'\s+', ' ', p0)[:400]
        return {**out, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-C1DOC', trial, expect_effects_gate=False)


def test_add_c2c_c1doc_evidence_snapshot_agrees_with_release_status_on_c1(request, record_property, tmp_path):
    hub = _hub()

    def trial(work, mp, checks):
        snap = json.loads((hub / 'collateral/evidence-snapshot.json').read_text())
        doc = (hub / 'docs/release-status.md').read_text()
        levels = snap['assurance_levels']
        checks.expect('optional' in levels['C1'].lower() and 'not enabled by default' in levels['C1'].lower(), 'snapshot C1 level is optional / not enabled by default')
        checks.expect(levels['C2'] == 'unqualified' and levels['C3'] == 'unqualified', 'snapshot C2/C3 unqualified')
        prof = [x for x in snap['separate_profile_evidence'] if x['id'] == 'c1-same-host-authority-effect']
        checks.equal(len(prof), 1, 'snapshot carries one C1 profile evidence entry')
        if prof:
            e = prof[0]
            checks.equal((e['status'], e['failures'], e['errors'], e['skips']), ('separate_optional_profile_ci', 0, 0, 0), 'snapshot C1 profile CI is separate and clean')
            for token in (str(e['workflow_run']), f"{e['passed_tests']} tests", e['control_plane_reviewed_source_sha'], e['execution_runtime_reviewed_source_sha']):
                checks.expect(token in doc, f'release-status.md does not carry C1 evidence value {token!r} from the snapshot')
            checks.expect('not default release' in e['scope'].lower() and 'not external destination atomicity' in e['scope'].lower(), 'snapshot C1 scope disclaims default release and external atomicity')
        # Observations (recorded, not part of this row's assertion): document/snapshot version and extension-contract drift.
        header = re.search(r'`version=([^`;]+)', doc)
        docs = {d['path']: d for d in snap['documents']}
        digest = hashlib.sha256((hub / 'docs/release-status.md').read_bytes()).hexdigest()
        ext_doc = re.search(r'v1-reference-extension-evidence/(\d+)', doc)
        ext_snap = [x['id'] for x in snap['separate_profile_evidence'] if x['id'].startswith('v1-reference-extension-evidence/')]
        observations = {'release_status_header_version': header.group(1) if header else None,
                        'snapshot_release_status_version': docs['docs/release-status.md']['version'],
                        'snapshot_release_status_sha256_matches_file': docs['docs/release-status.md']['document_sha256'] == digest,
                        'release_status_extension_contract': ext_doc.group(0) if ext_doc else None, 'snapshot_extension_contract': ext_snap}
        return {'observations_not_asserted': observations, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-C1DOC', trial, expect_effects_gate=False)


def test_add_c2c_c1doc_default_route_does_not_enable_the_atomic_profile(request, record_property, tmp_path):
    """Executed behaviour: the default (C0) route leaves the C1 profile inactive; only the explicit atomic executor activates it."""
    _hub()

    def trial(work, mp, checks):
        ref = H.reference()
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        flow_a = H.flow_a(work / 'a', mp)
        res, exc = H.execute_a(flow_a)
        checks.equal(H.result_view(res, exc).get('status'), 'executed', 'default route executes the exact request')
        flow_b = H.flow_b(work / 'b')
        H.execute_b(flow_b, flow_b.parts[0])

        def tables(path):
            conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
            try:
                names = sorted(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
                rows = conn.execute('SELECT COUNT(*) FROM authority_effect_profile_v1').fetchone()[0] if 'authority_effect_profile_v1' in names else None
                return names, rows
            finally:
                conn.close()
        a_tables, a_profile_rows = tables(flow_a.dest.path)
        b_tables, b_profile_rows = tables(flow_b.dest.path)
        c1_tables = {'authority_effect_profile_v1', 'authority_grants_v1', 'execution_claims_v1', 'authority_effect_receipts_v1', 'effect_budgets_v1'}
        checks.equal(sorted(c1_tables & set(a_tables)), [], 'default route destination holds none of the C1 profile tables')
        checks.expect(c1_tables <= set(b_tables) and b_profile_rows == 1, 'explicit atomic route activates the profile (positive control)')
        from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
        checks.expect(type(flow_a.executor) is ref.chain.PinnedControlPlaneExecutor, 'default route uses the PinnedControlPlaneExecutor')
        checks.expect(not isinstance(flow_a.executor, AtomicLocalControlPlaneExecutor), 'default executor is not the atomic executor')
        gate = H.effect_gate(H.db_summary(flow_a.dest.path), authorized_effect_ids={flow_a.env.effect_id})
        return {'default_route_tables': a_tables, 'default_route_profile_rows': a_profile_rows, 'atomic_route_profile_rows': b_profile_rows, **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-C1DOC', trial)


@pytest.mark.parametrize('mutation', ['c1-default', 'c1-external', 'c1-exactly-once', 'c1-selected'])
def test_add_c2c_c1doc_negative_control_enlarged_claim_is_detected(request, record_property, tmp_path, mutation):
    """Negative control: the checker flags a doc that enlarges the C1 claim (mutated copy of the real text, held in memory only)."""
    hub = _hub()

    def trial(work, mp, checks):
        doc = (hub / 'docs/release-status.md').read_text()
        checks.equal(_release_status_violations(doc), [], 'unmutated pinned document is clean (baseline for the control)')
        edits = {
            'c1-default': ('Not enabled by the default release and not an external destination guarantee.', 'Enabled in the default release.'),
            'c1-external': ('Not enabled by the default release and not an external destination guarantee.', 'Not enabled by the default release; it is an external destination guarantee.'),
            'c1-exactly-once': ('Same-host cooperating authority/effect ordering', 'Same-host cooperating authority/effect ordering with production exactly-once effects'),
            'c1-selected': ('**C1 — optional**', '**C1 — selected default**'),
        }
        old, new = edits[mutation]
        checks.expect(old in doc, 'mutation anchor present in the pinned document')
        mutated = doc.replace(old, new)
        found = _release_status_violations(mutated)
        checks.expect(bool(found), f'mutation {mutation} was NOT detected by the checker')
        return {'mutation': mutation, 'violations_detected': len(found), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-C1DOC', trial, expect_effects_gate=False)
