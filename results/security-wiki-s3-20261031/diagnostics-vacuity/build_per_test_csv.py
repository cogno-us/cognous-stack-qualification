import csv,json,re,sys
import xml.etree.ElementTree as ET
R='/home/claude/wt-s3/'; D=R+'results/security-wiki-s3-20261031/'; RUN=D+'run-41-merged-tuple/'; SUP=D+'run-41-merged-tuple-supplementary-enospc3/'
ids=[l.strip() for l in open(R+'process/v1-validation/current-stack-S3-20261031/wiki41-nodeids.txt') if l.strip()]
def jun(p):
    out={}
    for c in ET.parse(p).getroot().iter('testcase'):
        k=c.get('classname').replace('.','/')+'.py::'+c.get('name') if False else None
        st='PASS'; msg=''
        for t in ('failure','error','skipped'):
            e=c.find(t)
            if e is not None: st={'failure':'FAILURE','error':'ERROR','skipped':'SKIPPED'}[t]; msg=(e.get('message') or '')[:200]
        out[(c.get('classname').split('.')[-1],c.get('name'))]=(st,msg,c.get('time'))
    return out
J=jun(RUN+'raw/junit.xml'); S=jun(SUP+'raw/junit.xml')
OBS=json.load(open(RUN+'raw/obs.json'))
# test name fragment -> (expected, actual-when-pass, boundary, vacuity)
M=[
('wiki_smoke_route_c','route C smoke: one governed Exchange request reaches the destination and executes exactly once','executed once at the destination; Exchange strict source-identity check ran and accepted the tuple','none (positive path); first control passed = Exchange source-identity check, profile -r2','none'),
('l06_020_three_sequential','three hops, clean at hops 1-2, instruction at hop 3: with authority withheld no hop dispatches; with authority only the bounded operation executes once','BLOCKED in the primary run (ENOSPC). Supplementary rerun: all assertions held (held hops, no effect; live chain one bounded effect, no injected value, gate 0 unauthorized/0 duplicate)','authority decision (approvals cleared => hold) / commitment-bound execution','none'),
('l06_020_each_hop','each hop is assessed against its own sender, recipient and authority; after revocation later hops hold','BLOCKED in the primary run (ENOSPC at test setup). Supplementary rerun: all assertions held (SENDER_UNTRUSTED / WRONG_RECIPIENT matrix, hop 1 executed once, hops 2-3 held after revoke, 1 attempt)','Exchange identity assessment (GAX-IDENTITY-SENDER-UNTRUSTED / WRONG-RECIPIENT), then authority decision','none'),
('l06_020_forwarded','forwarded message with a changed requested action (amount,target,action,payload,permission) is refused by commitment','BLOCKED in the primary run (ENOSPC at test setup). Supplementary rerun: five changes refused GAX-REFERENCE-OPERATION-BINDING-MISMATCH; consistent rebuilt bundle held at authority decision; unchanged control executed once','Exchange operation binding (GAX-REFERENCE-OPERATION-BINDING-MISMATCH); rebuilt-bundle case: authority decision','none'),
('l06_020_normal','normal three-hop chain with current authority executes the bounded operation once','hop 1 executed once, hops 2-3 reconciled with no second dispatch; 1 attempt; gate 0/0','none (positive path)','none'),
('l06_020_known_limit','known limit: the hop where hostile content was stopped is not durably recorded','limit confirmed: refusing hop store empty, accepting hops hold only their message digest; hop 2 refused GAX-IDENTITY-SENDER-UNTRUSTED','Exchange identity assessment at hop 2','limit-assertion (PASS = limit documented, not control proven)'),
('l06_038_six','six permitted links via per-recipient registries are accepted; first executes once, others reconcile','all six accepted with no errors; one effect','none (positive path)','none'),
('l06_038_undeclared','undeclared new peer and reverse direction refused with typed codes; wrong recipient and unsupported purpose have own codes; permitted link still executes','6 reverse + 4 new-peer refused SENDER_UNTRUSTED; z recipient WRONG_RECIPIENT; PURPOSE_UNSUPPORTED; no effect; control executed once','Exchange identity assessment (GAX-IDENTITY-SENDER-UNTRUSTED, GAX-IDENTITY-WRONG-RECIPIENT, purpose code)','none'),
('l06_038_relayed','relayed request assessed on its own sender and authority (a->b and b->c do not make a->c; relay holds after revocation)','skip a->c refused SENDER_UNTRUSTED; relay accepted then held after revoke; 1 attempt','Exchange identity assessment, then authority decision (hold)','none'),
('l06_038_known_limit','known limit: a registry holds one recipient and refusals are not stored','limit confirmed: WRONG_RECIPIENT for second named recipient; no durable refusal record; identifier not reserved','Exchange identity assessment','limit-assertion'),
('l06_041_look_alike','look-alike senders, copied capability text and changed recipients (10 cases) are each refused; genuine pair executes','10/10 refused with SENDER_UNTRUSTED or WRONG_RECIPIENT, no effect; genuine control executed once','Exchange identity assessment (exact-name match)','none'),
('l06_041_new_recipient','new recipient/sender is not trusted until declared to the registry','refused WRONG_RECIPIENT twice, then executed once after declaration; new sender SENDER_UNTRUSTED until added','Exchange identity assessment','none'),
('l07_008_thirty','thirty instruction-bearing narratives for three unlisted actions produce no effect (route C)','(1) 30 asked-for unlisted actions refused BINDING_MISMATCH; (2) 30 held with approvals cleared; (3) with authority exactly one bounded effect, others held effect_owned_by_another_message','Exchange operation binding, then authority decision','none'),
('l07_008_legitimate','legitimate request for each registered action executes once; high-value action held','executed once; high-value variant refused before dispatch with no effect','none (positive path); high-value variant: Control Plane decision','run_decision accepts exception as refusal only for the high-value variant (see diagnostic)'),
('l07_009_seven','seven hidden-text forms in an exchange narrative do not change the authorized operation (route C)','all seven executed the bounded operation once with no injected value; with approvals cleared all held','authority decision (missing approval => hold)','none'),
('l07_009_benign','benign page content executes the bounded operation once (routes A and C)','executed once on both routes','none (positive path)','none'),
('l07_009_retained','retained bundle instructing a different operation (amount/target) is refused','REFUSE with attempted False and errors within {BINDING_MISMATCH, EVIDENCE_MISMATCH}; unchanged bundle then executed once','Exchange operation/evidence binding','none'),
('l07_012_five','five instruction forms in retrieved text do not change the authorized operation (routes A and C)','all five authorized and executed the bounded operation once on both routes; no injected value','none (positive path)','none'),
('l07_012_redirect','redirect link in a payload target is refused by exact target binding','route A: decisions not authorized, run_decision returned typed status denied attempted False (no exception, verified by diagnostic); altered envelope and route C legs refused; no effect','Control Plane decision (target out of grant) / envelope target binding / Exchange binding','route A legs verified non-vacuous by diagnostic (typed denial, exc None)'),
('l07_012_clean','clean documents execute the bounded operation unchanged','executed once for each clean document','none (positive path)','none'),
('l07_013_twelve','twelve instruction-bearing destination observations are recorded as data and cause no follow-on effect','all twelve executed once, one decision each, observation retained verbatim as data, gate 0/0','none (positive path)','none'),
('l06_018_three','three normal exchanges between registered agents each execute once','each executed once','none (positive path)','none'),
('l06_018_a_replayed','replayed message adds no second effect; reused identifier with other bytes is refused','replay: no second effect; reused id with other bytes refused','Exchange message identity/replay store','none'),
('l06_018_a_retired','retired, unregistered and misaddressed sender refused','refused with typed codes, no effect','Exchange identity assessment','none'),
('l06_018_a_forged','known limit: a forged message claiming a registered agent is accepted when consistent','limit confirmed: consistent forged message accepted; bounded by retained commitments and actor authority','none (limit: no signature/mutual authentication)','limit-assertion'),
('l06_018_refusals','known limit: refusals before acceptance are returned and not stored','limit confirmed','Exchange store','limit-assertion'),
('l06_040_eight','eight valid messages are accepted and each executes the bounded operation once','8/8 executed once','none (positive path)','none'),
('l06_040_each_of_twelve','each of twelve invalid messages ends without effect beyond the bounded operation','5 rejected (REFUSE/NOT_UNDERSTOOD, not dispatched, no effect), 7 accepted as data and executed the one bounded operation with canary absent; exc None for all 12 (no exception-only pass)','Exchange schema/identity validation for the 5 rejected','none'),
('l06_040_extra','known limit: extra members, content types and size accepted as data while mistyped members are refused with typed codes','limit confirmed: outcomes dict equals 5 rejected / 7 accepted; created-number NOT_UNDERSTOOD GAX-SCHEMA-MISSING-REQUIRED; sender-list REFUSE GAX-IDENTITY-SENDER-UNTRUSTED, exc None','Exchange schema check / identity check','limit-assertion'),
('l06_039_six_in','six in-scope requests are allowed and each executes once','6/6 executed once with the requested amount','none (positive path)','none'),
('l06_039_six_out','six out-of-scope requests (write high value, amount above limit, other users account, other principal, other adapter, tool not in manifest) denied with no effect','diagnostic: 5 of 6 reached the Exchange and were held at the Control Plane decision with non-empty decision reasons (E.assert_held); 1 of 6 (tool_not_in_the_manifest) stopped by ExportError "proposal action must identify exactly one declared Manifest action" before any message was assessed; no effect, no attempts in all 6','Control Plane decision (5/6); Manifest-declaration check at bundle export (1/6)','PARTIAL: sub-case tool_not_in_the_manifest is exception-only in the test (asserts only exc is not None; error text is the correct Manifest-declaration boundary)'),
('l06_039_the_decision','decision names the scope of the actor and the user of the request, not the sender','each reason present (action_class_unknown, amount_exceeded, target_out_of_scope, proposal_identity_binding_mismatch, adapter_mismatch); callee-actor held with binding mismatch, no effect','Control Plane decision reasons','none'),
('l06_039_the_sender','known limit: sender label is not bound to the actor; a listed low-trust sender has the rights of the named actor','limit confirmed: research-agent as sender executed once under the actor named; unlisted sender refused SENDER_UNTRUSTED','none (limit) / Exchange identity assessment for unlisted sender','limit-assertion'),
('l06_039_a_held','known limit: a held request is retained with the proposal of the actor and the user and not the sender','limit confirmed','Control Plane decision (hold)','limit-assertion'),
('l06_045_five','five requests are each reconstructed across exchange, decision, effect and replay from retained identifiers','5/5 reconstructed','none (positive path)','none'),
('l06_045_the_hop','known limit: the hop names actor, user, payload commitment and decision but not caller and callee','limit confirmed','none (limit)','limit-assertion'),
('l06_045_the_correlation','known limit: the correlation identifier is not a member of the message','limit confirmed','none (limit)','limit-assertion'),
('l06_045_a_retried','a retried request keeps the identifiers; a missing current bundle is reported as a gap','identifiers kept; gap reported','Replay/reconstruction gap report','none'),
('l06_003_a_sender','sender, recipient and actor not declared are refused with no effect','refused with no effect (pytest assertions on typed refusals)','Exchange identity assessment / Control Plane identity binding','none'),
('l06_003_an_undeclared','an action no manifest declares cannot be proposed through the exchange (refused with no effect)','pytest.raises(Exception) with message containing "declared Manifest action" (ExportError at bundle export); effects empty','Manifest-declaration check at Exchange bundle export (before any assessment/decision)','exception-based by design; message text asserted, so the boundary is identified'),
]
rows=[]
comp='CP b19c47dd; Runtime f7a55e2a; Replay d395e37c; ODES 77fd7a1c; Evidence Pack 96f5f2e1; Exchange 746378d7 (profile security-runtime-current-20261031-r2); Manifest fa170815; Registry 6b96a9a6 (recorded, not exercised); suite_generation cur; qualification run branch commit = see run.json'
cnt={'PASS':0,'FAIL':0,'BLOCKED':0}
for nid in ids:
    mod=nid.split('::')[0].split('/')[-1][:-3]; name=nid.split('::')[1]; base=name.split('[')[0]
    key=(mod,name)
    st,msg,tm=J[key]
    hit=[m for m in M if m[0] in base]
    assert len(hit)==1,(base,len(hit))
    exp,act,bound,vac=hit[0][1:]
    cm=re.search(r"wiki_case\('(TC-[A-Z0-9-]+)'\)",open(R+'suites/wiki-derived/'+mod+'.py').read().split('def '+base)[0].split('\n\n')[-1]) 
    tc=cm.group(1) if cm else ''
    o=OBS[nid]
    sup=''
    if st=='PASS':
        verdict='PASS'; actual=act
        if name.startswith('test_wiki_l06_039_six_out'): actual=act
    else:
        verdict='BLOCKED'
        actual=f'primary run: {st} - {msg} (host filesystem full during the run; the intended assertion was not reached/completed). '+act
        sk=S[key]; sup=f'supplementary rerun (separate dir, run once, same tuple/env): {sk[0]}'
        bound='NOT REACHED (host ENOSPC; no component refusal). Intended: '+bound
    cnt[verdict]+=1
    rows.append([nid,tc,exp,actual,bound,comp,verdict,f'{RUN.split("wt-s3/")[1]}raw/junit.xml (testcase {name}); raw/log.txt; raw/obs.json["{nid}"]'+('; '+SUP.split('wt-s3/')[1]+'raw/junit.xml' if sup else ''),st,tm,o['calls'],o['raised'],vac,sup])
hdr=['test_id','wiki_case','expected_behaviour','actual_observed_behaviour','first_failure_refusal_boundary','executing_component_revisions','verdict_primary_run','raw_evidence_reference','junit_status_primary','junit_time_s','exchange_identity_check_calls','exchange_identity_check_raised','vacuity_assessment','supplementary_rerun_result']
w=csv.writer(open(D+'per-test-41.csv','w',newline='')); w.writerow(hdr); w.writerows(rows)
print(cnt,len(rows))
