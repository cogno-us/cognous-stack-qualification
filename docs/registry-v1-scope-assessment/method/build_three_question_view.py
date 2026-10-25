#!/usr/bin/env python3
"""Derives data/three-question-view.{csv,json} from the canonical crosswalk (read-only on the crosswalk).

SPDX-License-Identifier: Apache-2.0
Usage: build_three_question_view.py <DATA_DIR>   (stdlib only).

Separates three questions that the single registry_dependency column conflated:
  A. Does existing OCS code enforce the protection?            -> existing_protection + evidence_status (copied verbatim)
  B. Would central registry management improve the customer's
     ability to govern the protection?                         -> q_b_governance_benefit (derived; vocabulary below)
  C. Is registry management necessary for the V1 capability?   -> q_c_v1_necessity_basis (derived; vocabulary below)

Nothing here re-rates a scenario. registry_dependency keeps its meaning: whether the scenario's REQUIRED OBSERVATION depends
on a registry-supplied value. UNNECESSARY therefore never says that central governance has no value; it says either that
no governable value exists for the scenario, or that a value exists but the scenario's outcome does not depend on it.
"""
import csv, json, sys

D = sys.argv[1].rstrip('/') + '/'
rows = list(csv.DictReader(open(D + 'canonical-scenario-crosswalk.csv')))

PROFILES = [('A', {'F1a', 'F1b'}), ('B', {'F1a', 'F1b', 'F1c', 'F4', 'F5'}),
            ('C', {'F1a', 'F1b', 'F1c', 'F4', 'F5', 'F6'}), ('D', {'F1a', 'F1b', 'F1c', 'F4', 'F5', 'F6', 'F1d'})]
# Relaxing toggles are code-owned by rule (R07 fitness matrix, P0 extractability test): no governable value even though F5 is mapped.
TOGGLE_ONLY = {'TC-L05-013'}

# q_b vocabulary
B_IDENTIFIED = 'BENEFIT_IDENTIFIED'                     # registry_dependency BENEFICIAL
B_UNDETERMINED = 'BENEFIT_UNDETERMINED'                 # registry_dependency UNKNOWN (waits on a ruling or unverified source)
B_VALUE_EXISTS = 'GOVERNABLE_VALUE_EXISTS_OUTCOME_INDEPENDENT'  # UNNECESSARY, a family value is mapped; the scenario outcome does not depend on it
B_NONE = 'NO_GOVERNABLE_VALUE'                          # no deployment-tunable parameter (mandatory gate logic, evidence format, relaxing toggle, method scenario)
B_NA = 'NOT_ASSESSED_OUT_OF_SCOPE'


def fams(r):
    return [f for f in r['registry_family'].replace(' ', '').split(',') if f and f not in ('NONE', 'UNMAPPED')]


def smallest_profile(fs):
    for name, s in PROFILES:
        if set(fs) <= s:
            return name
    return 'NONE'


out = []
for r in rows:
    fs = fams(r)
    has_unmapped = 'UNMAPPED' in r['registry_family'].replace(' ', '').split(',')
    if r['priority'] == 'OUT_OF_SCOPE':
        qb, qc, basis = B_NA, 'NOT_ASSESSED', 'crosswalk priority OUT_OF_SCOPE (not a registry-parameter candidate); not assessed for Q-B or Q-C'
    else:
        dep = r['registry_dependency']
        if dep == 'BENEFICIAL':
            qb = B_IDENTIFIED
        elif dep == 'UNKNOWN':
            qb = B_UNDETERMINED
        elif dep == 'REQUIRED':
            qb = 'BENEFIT_IDENTIFIED_REQUIRED'
        else:  # UNNECESSARY
            qb = B_NONE if (not fs or r['scenario_id'] in TOGGLE_ONLY) else B_VALUE_EXISTS
        if not fs or r['scenario_id'] in TOGGLE_ONLY:
            qc, basis = 'NOT_REGISTRY_PARAMETER_RELATED', 'no governable parameter mapped; registry management is not part of what this scenario would need'
        else:
            qc = 'BY_PROFILE_DEFINITION_IF_FAMILY_SELECTED'
            basis = ('under plan v1.3 section 1 the V1 profile as defined in draft plan v1.3 section 1 (not approved or frozen by this package) must be externally governed, so registry management is '
                     'necessary for the selected fields by definition; this corpus cannot establish it independently')
    out.append({
        'scenario_id': r['scenario_id'],
        'q_a_existing_protection': r['existing_protection'],
        'q_a_evidence_status_named_cases_only': r['evidence_status'],
        'q_a_qualification_status': r['qualification_status'],
        'q_b_governance_benefit': qb,
        'q_b_basis_registry_dependency': r['registry_dependency'],
        'mapped_families': r['registry_family'].replace(' ', ''),
        'q_c_v1_necessity_basis': qc,
        'smallest_covering_profile': ('NONE_UNMAPPED_CONSTRAINT' if has_unmapped else smallest_profile(fs)) if (fs and r['priority'] != 'OUT_OF_SCOPE') else '',
        'q_c_note': basis,
    })

cols = list(out[0])
with open(D + 'three-question-view.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(out)
json.dump(out, open(D + 'three-question-view.json', 'w'), indent=1)

import collections as C
ins = [o for o in out if o['q_b_governance_benefit'] != B_NA]
print(len(out), len(ins))
print(C.Counter(o['q_b_governance_benefit'] for o in ins))
print(C.Counter((o['q_a_existing_protection'], o['q_b_governance_benefit']) for o in ins).most_common(20))
