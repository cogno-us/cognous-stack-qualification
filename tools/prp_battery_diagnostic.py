"""POST HOC diagnostic of core constraints. Does not alter the frozen scorer.

This analysis was defined after outputs were observed. It is not confirmatory,
not a replacement primary endpoint, and does not establish general efficacy.
"""
import json
from pathlib import Path
import prp_battery_evaluation as b

FIELDS={
 '01A':['action','action_state','target_ids','payload_id','unresolved_fields'],
 '01B':['action','action_state','target_ids','payload_id'],
 '01C':['action','action_state','target_ids','payload_id','unresolved_fields'],
 '02A':['action','target_ids','payload_id','unresolved_fields'],
 '02B':['action','action_state','target_ids','payload_id'],
 '02C':['action','target_ids','payload_id'],
 '03A':['action','target_ids','unresolved_fields'],
 '03B':['action','target_ids'],
 '03C':['action','target_ids','answer'],
 '04A':['action','target_ids','payload_id','answer'],
 '04B':['action','target_ids','payload_id'],
 '04C':['action','target_ids','payload_id','clarification'],
 '05A':['action','target_ids','correction_reference'],
 '05B':['action','target_ids','correction_reference'],
 '05C':['action','target_ids','correction_reference'],
 '06A':['action','target_ids','unresolved_fields','answer'],
 '06B':['action','target_ids','answer'],
 '06C':['action','target_ids','unresolved_fields'],
 '07A':['action','clarification','unresolved_fields','target_ids'],
 '07B':['action','target_ids','clarification'],
 '07C':['action','clarification','unresolved_fields','target_ids'],
 '08A':['action','answer','clarification','target_ids'],
 '08B':['action','answer','clarification','target_ids'],
 '08C':['action','answer','clarification','target_ids']}

def audit(case,trial):
    d=trial['decision'];identity=case['id'];options=[]
    if trial['stop_reason'] or not d:return {'core_constraints_met':False,'reason':'Incomplete execution'}
    for expected in case['oracle']['accepted']:
        actions=[expected['action']]
        if identity in ('03C','08A','08B','08C'):actions=['none','report']
        if identity=='05C':actions=['hold','none']
        for action in actions:options.append(expected|{'action':action})
    matched=any(all(b.normalize(k,d[k])==b.normalize(k,e[k]) for k in FIELDS[identity]) for e in options)
    evidence=set(d['evidence_ids']);known={r['id'] for r in case['input']['records']}
    support=set(case['oracle']['required_evidence'])<=evidence and evidence<=known
    return {'core_constraints_met':matched and support,'checked_fields':FIELDS[identity],'supporting_evidence_met':support,'semantic_prose_score':'NOT EVALUATED'}

def main(path):
    m=json.loads((path/'manifest.json').read_text());cases={c['id']:c for c in json.loads((path/'cases.json').read_text())}
    rows=[{'case_id':t['case_id'],'repetition':t['repetition'],'condition':t['condition'],**audit(cases[t['case_id']],t)} for t in m['trials']]
    return {'status':'POST HOC DIAGNOSTIC ONLY','original_scorer_unchanged':True,'general_efficacy_established':False,'limitations':['Rules defined after seeing outputs; not a preregistered endpoint or independent validation.','Checks selected substantive decision fields and evidence support; does not score all prose claims.','Cannot be used to replace the failed primary measurement or claim PRP benefit.'], 'counts':{arm:{'core_constraints_met':sum(r['core_constraints_met'] for r in rows if r['condition']==arm),'trials':sum(r['condition']==arm for r in rows)} for arm in ('baseline','prp')},'trials':rows,
      'measurement_defects':[{'defect':'Correct free-text answers rejected because expected answer was NONE or a terse numeric token','example_cases':['01A','01B','01C','03A','03B','05A','05B','07A','07C']},
       {'defect':'No external action classified as a false block even when routine answer was correct','example_cases':['08A','08B','08C']},
       {'defect':'Correct unknown-entitlement prose classified as a critical invented fact because it was not the exact string UNKNOWN','example_cases':['06C']},
       {'defect':'Equivalent abstention or state metadata rejected without a wrong selected consequence','example_cases':['02C','04A','05A','05C']} ]}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();r=main(a.evidence);(a.evidence/'posthoc-diagnostic.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='trials'},indent=2))
