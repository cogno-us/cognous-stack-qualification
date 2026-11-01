import json,sys,collections
for rev in sys.argv[2:]:
    rows=[json.loads(l) for l in open(f'{sys.argv[1]}/raw/{rev}/readj_evidence.jsonl')]
    by=collections.defaultdict(lambda:[0,0])
    for r in rows:
        if r['kind'] in('CHECK_PASS','CHECK_FAIL'):
            g=r['case'].split('[')[0]; by[g][0 if r['kind']=='CHECK_PASS' else 1]+=1
    print(rev,{k:{'pass':v[0],'fail':v[1]} for k,v in by.items()})
    lit=[r for r in rows if r.get('check','').endswith('literal_flags') or r.get('check')=='literal_flags']
    g1=[r for r in lit if r['case'].startswith('G1')]
    print(' G1 literal flags: names_code',sum(bool(r.get('reason_names_code')) for r in g1),'durable',sum(bool(r.get('durable_effect_time_refusal')) for r in g1),'of',len(g1))
    g2=[r for r in rows if r['case'].startswith('G2') and r.get('check')=='C2_message_matches_documented_text']
    print(' G2 message match',sum(r['match'] for r in g2),'of',len(g2), 'other msgs',sorted(set(r['msg'] for r in g2 if not r['match'])))
    raw=[r for r in rows if r['kind']=='RAW']
    ph=collections.Counter()
    for r in raw:
        e=r['out']['effects']; ph[(r['case'].split('[')[0],tuple(e['check_event_phases']),e['resolution_checks_delta'],tuple(e['changed_keys']))]+=1
    for k,v in ph.items(): print(' journal',k,v)
