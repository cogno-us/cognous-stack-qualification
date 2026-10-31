"""Scratch diagnostic plugin: logs, for the vacuity-prone helpers, whether an exception or a typed result ended each call. Observer only; wraps nothing that changes outcomes."""
import json,os,sys
LOG=os.environ['VAC_OUT']; rec=[]
def pytest_runtest_call(item):
    mod=sys.modules.get(item.module.__name__)
    E=sys.modules.get('test_wp_e_exchange_injection'); 
    if E is not None and not getattr(E,'_vd',False):
        E._vd=True; orig=E.run_decision
        def rd(flow,proposal=None,decision=None):
            r,x=orig(flow,proposal,decision); rec.append({'test':item.name,'fn':'run_decision','res_status':getattr(r,'status',None),'attempted':getattr(r,'attempted',None),'exc':x}); return r,x
        E.run_decision=rd
        if hasattr(E,'refused_before_dispatch'): pass
    if mod is not None and item.module.__name__.endswith('g5_exchange_messages_and_correlation') and not getattr(mod,'_vd',False):
        mod._vd=True; oa=mod.attempt; orq=mod.request_for
        def att(flow,message,**kw):
            r,x=oa(flow,message,**kw); rec.append({'test':item.name,'fn':'attempt','handling':(r or {}).get('assessment',{}).get('permitted_handling') if r else None,'exc':x}); return r,x
        mod.attempt=att
        def rq(flow,name,text=None):
            m,b,x=orq(flow,name,text); rec.append({'test':item.name,'fn':'request_for','name':name,'message_built':m is not None,'exc':x}); return m,b,x
        mod.request_for=rq
def pytest_sessionfinish(session):
    json.dump(rec,open(LOG,'w'),indent=1)
