"""Report generator for the comparison (pre-registration RP-1 to RP-10 for the comparison part; amendments 74, 76 and the draft rules).

Input: the set tables of cells.build_set (one per set: corner, baseline, Wiki subset), the identity record of the run (RP-9) and, for the
Wiki subset, the plan file and the declarations file. Output: Markdown.

Every report carries: the scope text of PC-7 unchanged (RP-8), the caveats of the plans (RP-8), the identity record (RP-9), one table per set
with one row per case and one column per configuration (RP-4), the counts per configuration (RP-4, amendment 83), the counts of the oracle
(RP-5), the block "cases where a comparator passes and OCS does not" (RP-6, always present), the rule that a comparative statement appears
only for a set on which the configurations were run (RP-7), the reason text of every refusal and of every not-expressible or not-claimed
declaration, and the cross-reference column of amendment 76 labelled `different harness, not scored by this oracle`. There is no aggregate
score across sets and no ranking.
"""
import json
from pathlib import Path

from comparators.runner import cells as C

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

SCOPE_TEXT = json.loads((REPO / 'process/release-gate/preregistration.json').read_text())['scope_text']
RP8_CAVEATS = ('the corner plan was authored after inspection of the baseline code and is not blinded, and both plans had no independent review; '
               'the shared Cognous wire and signature helpers feed all three configurations')
COLUMN = {'cognous-protected-destination': 'OCS (protected destination)', 'opa-transactional-application': 'OPA application',
          'langgraph-opa-transactional-application': 'LangGraph plus OPA application'}
OCS = 'cognous-protected-destination'
CROSSREF_LABEL = 'different harness, not scored by this oracle'
NE_NC_MEANING = ('Not expressible says what the configured application can be asked: the declared interface of the configuration as it was built '
                 'for this comparison has no field, operation or state that the scenario needs. Not claimed describes the claims of the stack as '
                 'configured, as published before the plan. Neither says anything about what OPA or LangGraph could do in other hands, and neither '
                 'is a pass or a fail.')
SET_TITLES = {'corner': 'Corner scenarios', 'baseline': 'Baseline scenarios', 'wiki': 'Wiki subset'}


def cell_text(cell):
    o = cell['outcome']
    parts = [o]
    if o in (C.PASS, C.FAIL, C.COULD_NOT_CHECK, C.MASKED) and cell['trials']:
        parts.append('%d/%d trials' % (cell['trials_passed'], cell['trials']) if o != C.MASKED else '%d trials executed' % cell['trials'])
    text = ' '.join(parts)
    if cell['of'] > 1:
        text += '; asked %d of %d' % (cell['asked'], cell['of'])
    extra = []
    if cell['not_expressible']:
        extra.append('not expressible %d' % cell['not_expressible'])
    if cell['not_claimed']:
        extra.append('not claimed %d' % cell['not_claimed'])
    if cell['not_asked']:
        extra.append('not asked %d' % cell['not_asked'])
    if extra:
        text += ' [' + ', '.join(extra) + ']'
    return text


def _esc(s):
    return str(s).replace('|', '/').replace('\n', ' ')


def comparable(table):
    """RP-7: a comparative statement is allowed only for a set on which all configurations were run."""
    for p in table['profiles']:
        if not any(row['cells'][p]['outcome'] in (C.PASS, C.FAIL) for row in table['cases']):
            return False
    return True


def render_identity(identity, masked):
    if masked or not identity:
        return ['## Run identity (RP-9)', '', 'Plumbing run: no candidate identity is recorded because no result is reported.', '']
    cm = identity.get('candidate_manifest') or {}
    lines = ['## Run identity (RP-9)', '',
             '| Item | Value |', '| --- | --- |',
             '| Candidate id | %s |' % (identity.get('candidate_id') or 'not supplied'),
             '| Qualification commit | `%s` (working tree dirty: %s) |' % (identity.get('qualification_commit'), identity.get('working_tree_dirty')),
             '| Candidate manifest digest | `%s` |' % (cm.get('sha256') or 'not available'),
             '| Oracle (function `evaluate`, source sha256) | `%s` |' % identity['oracle']['evaluate_function_source_sha256'],
             '| Oracle (runner file sha256) | `%s` |' % identity['oracle']['runner_file_sha256'],
             '| Pre-registration commit | `%s` |' % identity['pre_registration']['commit'],
             '| Pre-registration page / twin sha256 | `%s` / `%s` |' % (identity['pre_registration']['page_sha256'], identity['pre_registration']['twin_sha256']),
             '| Amendments in force | %d (%s), last recorded %s |' % (identity['amendments_in_force']['count'], identity['amendments_in_force']['numbers'],
                                                                      identity['amendments_in_force']['last_timestamp'])]
    for label, f in identity['plan_files'].items():
        lines.append('| Plan file `%s` | `%s`, commit `%s`, sha256 `%s` |' % (label, f['path'], f['last_commit'], f['sha256']))
    return lines + ['']


def render_set(table, masked, plan=None, decl=None, crossref=None, gate_status=None):
    name = table['set']
    profiles = table['profiles']
    cols = [COLUMN.get(p, p) for p in profiles]
    total = table['counts'][profiles[0]]['scenarios']
    lines = ['## Set: %s' % table.get('title', SET_TITLES.get(name, name)), '',
             '%d cases, %d scenarios; trials expected per asked scenario: %d.' % (len(table['cases']), total, table['expected_trials']), '',
             '### Comparison table (RP-4)', '', '| Case | ' + ' | '.join(cols) + ' |', '| --- |' + ' --- |' * len(cols)]
    for row in table['cases']:
        label = row['id'] if row['title'] in (row['id'], '(masked twin)') else '%s (%s)' % (row['id'], _esc(row['title'])[:60])
        lines.append('| %s | ' % label + ' | '.join(_esc(cell_text(row['cells'][p])) for p in profiles) + ' |')
    lines += ['', 'A cell is one of pass, fail, not expressible, not claimed, could not check or not asked (masked in a plumbing run). A trial fraction '
              'counts the trials of asked scenarios only; scenarios that are not expressible, not claimed or not asked are never in a pass fraction.', '']
    lines += ['### Scenarios per configuration (RP-4, amendment 83)', '',
              '| Configuration | Scenarios | Asked | Not expressible | of which without executable steps in the plan file | Not claimed | Not asked | Could not check |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for p in profiles:
        c = table['counts'][p]
        lines.append('| %s | %d | %d | %d | %d | %d | %d | %d |' % (COLUMN.get(p, p), c['scenarios'], c['asked'], c['not_expressible'],
                                                                   c['not_expressible_plan_level'], c['not_claimed'], c['not_asked'], c['could_not_check']))
    lines.append('')
    if not masked:
        lines += ['### Counts of the oracle (RP-5)', '',
                  '| Configuration | Trials passed | Unexpected effects | Missing effects | False allows | False blocks | Denied calls | Durably recorded denials |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in profiles:
            o = table['oracle_counts'][p]
            lines.append('| %s | %d/%d | %d | %d | %d | %d | %d | %d |' % (COLUMN.get(p, p), o['passed'], o['case_trials'], o['unexpected_effect_count'],
                                                                           o['missing_effect_count'], o['false_allows'], o['false_blocks'],
                                                                           o['denied_calls'], o['durably_recorded_denials']))
        lines += ['', 'Wall times are descriptive only and are not reported here. There is no aggregate score across sets and no ranking.', '']
        lines += ['### Reason text of every refusal (RP-4)', '']
        any_reason = False
        for row in table['cases']:
            for p in profiles:
                reasons = row['cells'][p]['refusal_reasons']
                if reasons:
                    any_reason = True
                    lines.append('- %s, %s: ' % (row['id'], COLUMN.get(p, p)) + '; '.join('%s x%d' % (k, v) for k, v in reasons.items()))
        if not any_reason:
            lines.append('No refusal was recorded.')
        lines.append('')
    lines += render_rp6(table, masked)
    if name == 'wiki' and decl is not None and not masked:
        lines += render_declarations(table, decl)
        lines += render_crossref(table, decl, crossref, gate_status, masked)
    if name == 'wiki' and plan is not None and not masked:
        lines += render_not_asked(plan)
    lines += render_observations(table, masked)
    lines += ['### Statement on not expressible and not claimed', '', NE_NC_MEANING, '']
    if name == 'wiki' and plan is not None and not masked:
        d = plan['declarations']
        lines += ['### Declared conventions of the Wiki subset', '',
                  '- Declared time T: %s' % d['stated_time_T'], '- Status vocabulary: %s' % d['status_vocabulary'],
                  '- Clock: %s' % d['time_unit'], '- Seeds %s, repetitions %d.' % (plan['seeds'], plan['repetitions']),
                  '- Expected outcomes were written from the case text by one author and checked by one checker (amendment 75); a single check is a '
                  'weaker control than the two checks that PR-3 registered.',
                  '- Expected reason codes are omitted for every Wiki scenario: reason conformance holds by construction and the durable denial term '
                  'of the oracle still applies.', '']
    if table.get('not_run'):
        lines += ['### Not run', ''] + ['- %s: %s' % (k, v) for k, v in table['not_run'].items()] + ['']
    return lines


def render_rp6(table, masked):
    lines = ['### Cases where a comparator passes and OCS does not (RP-6)', '']
    if masked:
        return lines + ['Not evaluated: plumbing run, verdicts discarded.', '']
    if not comparable(table):
        return lines + ['Not evaluated: not all three configurations have a scored result on this set, so no comparative statement is made (RP-7).', '']
    a, b = C.comparator_passes_and_ocs_does_not(table, OCS)
    if not a and not b:
        return lines + ['None.', '']
    lines += ['Each case carries the same weight as any other row.', '']
    lines += ['(a) A comparator cell is pass and the OCS cell is fail or could not check:', '']
    lines += ['- %s: %s pass; OCS %s' % (x['case'], ', '.join(COLUMN[p] for p in x['comparators']), x['ocs']) for x in a] or ['None.']
    lines += ['', '(b) A comparator cell is pass and the OCS cell is not expressible or not claimed. This is not a fail and is not a comparative '
              'statement; the OCS cell is shown with its reason and its cross-reference (amendments 39 and 76):', '']
    lines += ['- %s: %s pass; OCS %s%s' % (x['case'], ', '.join(COLUMN[p] for p in x['comparators']), x['ocs'],
                                           ' (amendment 39: comparator results are shown without a comparative statement)' if x['case'] == 'TC-D13-003' else '')
              for x in b] or ['None.']
    return lines + ['']


def render_declarations(table, decl):
    lines = ['### Declarations for the protected destination (amendments 76 and the draft rule of citation)', '',
             'Plan file digest at the time the declarations were generated: `%s`. Each declaration cites an interface item of the destination and the '
             'sentence of the case it was written from; a not-claimed declaration cites a sentence published before the plan.' % decl['plan']['sha256'], '',
             '| Scenario | Status | Code | Reason | Interface items |', '| --- | --- | --- | --- | --- |']
    for r in decl['records']:
        if r['status'] == 'ASKED':
            continue
        lines.append('| %s | %s | %s | %s | %s |' % (r['scenario'], r['status'], r['reason_code'], _esc(r['reason']), ', '.join(r['interface_items'])))
    lines += ['', 'Counts: asked %d, not expressible %d, not claimed %d of %d executable scenarios. The full records with citations are in `ocs-column-declarations.json`.'
              % (decl['counts']['ASKED'], decl['counts']['NOT-EXPRESSIBLE'], decl['counts']['NOT-CLAIMED'], decl['counts']['executable_scenarios']), '']
    return lines


def render_crossref(table, decl, crossref, gate_status, masked):
    lines = ['### Cross-reference for the OCS cells that are not expressible or not claimed (%s)' % CROSSREF_LABEL, '',
             'These are test names at the components that claim the case. They are never scored by this oracle, never added to a pass fraction, and '
             'their outcomes are not shown in the scored columns. Gate status of a Wiki-derived test is given as supplied at report time.', '']
    if masked:
        return lines + ['Not shown in a plumbing run.', '']
    crossref = crossref or {}
    cases = crossref.get('cases', {})
    shown = False
    for row in table['cases']:
        cell = row['cells'][OCS]
        if not (cell['not_expressible'] or cell['not_claimed']):
            continue
        shown = True
        lines.append('- **%s** (OCS cell: %s)' % (row['id'], cell['outcome']))
        entries = cases.get(row['id'], [])
        if not entries:
            lines.append('  - no test names listed for this case')
        for e in entries:
            statuses = []
            for t in e['tests']:
                st = (gate_status or {}).get(t)
                statuses.append('%s [%s]' % (t, st if st else 'gate status not supplied'))
            lines.append('  - `%s`: %s' % (e['file'], '; '.join(statuses)))
    if not shown:
        lines.append('No OCS cell is not expressible or not claimed.')
    return lines + ['']


def render_not_asked(plan):
    lines = ['### Scenarios that are not asked of any configuration (listed with their reason, not scored)', '',
             '| Scenario | State in the plan file | Origin | Reason |', '| --- | --- | --- | --- |']
    for item in plan['non_executed']:
        lines.append('| %s | %s | %s | %s |' % (item['id'], item['state'], _esc(item['origin']), _esc(item.get('reason', ''))[:300]))
    return lines + ['']


def render_observations(table, masked):
    lines = ['### Observations of scenarios declared not claimed (run, retained, not scored, not counted in any pass fraction)', '']
    obs = table['unscored_observations']
    if not obs:
        return lines + ['None.', '']
    if masked:
        return lines + ['%d scenario runs executed in the plumbing run; verdicts discarded.' % len(obs), '']
    lines += ['| Configuration | Scenario | Trials | Observed outcome equals the expected outcome | Errors | Reasons |', '| --- | --- | ---: | ---: | ---: | --- |']
    for o in obs:
        x = o['observation']
        lines.append('| %s | %s | %d | %d | %d | %s |' % (COLUMN.get(o['profile'], o['profile']), o['scenario'], x['trials'], x.get('observed_equal_to_expected', 0),
                                                         x['errors'], _esc('; '.join('%s x%d' % kv for kv in x.get('reasons', {}).items()))))
    return lines + ['', 'These rows state what was observed; they are not a pass or a fail for the configuration (amendments 39 and 74).', '']


def render(tables, identity, masked=False, plan=None, decl=None, extra=None, crossref=None, gate_status=None, title=None):
    """Markdown of the report for the given set tables."""
    lines = ['# %s' % (title or ('Plumbing run of the comparison (verdicts discarded)' if masked else 'Comparison report')), '',
             '**Scope.** ' + SCOPE_TEXT, '',
             'Caveats that stay with every report (RP-8, unchanged): ' + RP8_CAVEATS + '.', '']
    if masked:
        lines += ['This is a plumbing run on renamed development twins. No verdict was stored or printed, no result is reported, and nothing here '
                  'is a comparison.', '']
    lines += render_identity(identity, masked)
    ran = [t['set'] for t in tables if comparable(t) and not masked]
    lines += ['## Comparative statements (RP-7)', '',
              'A comparative statement appears only for a set on which all configurations were run. Sets with a scored result for every configuration '
              'in this report: %s.' % (', '.join(ran) if ran else 'none'), '']
    for t in tables:
        lines += render_set(t, masked, plan if t['set'] == 'wiki' else None, decl if t['set'] == 'wiki' else None, crossref, gate_status)
    lines += ['No independent review and no hidden task set. No release or production authorization. Operational trust stays on HOLD.', '']
    return '\n'.join(lines)
