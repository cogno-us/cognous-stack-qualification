# VERIFICATION STUB ONLY: emulates the CUR names the unmerged Replay/ODES PRs add, so that the 'cur' branch can be IMPORTED for collect-only.
# Values are the current CP/Runtime pins; nothing is executed. Not part of the patch.
import importlib.abc, importlib.machinery, sys
def _fix(mod):
    n=mod.__name__
    if n=='agent_replay_bundle.importers':
        mod.CONTROL_PLANE_CUR_REVISION='b19c47ddd020409d24e52e70b11359c46265edbb'; mod.MOLTBOT_CUR_REVISION='f7a55e2a8494801e49193f9f46935f0a971c248d'
    if n=='odes.common':
        mod.CUR_REVISIONS={'stub':1}; mod.CUR_PROFILE_VERSION='stub'
class F(importlib.abc.MetaPathFinder):
    def find_spec(self,name,path,target=None):
        if name not in('agent_replay_bundle.importers','odes.common'):return None
        sys.meta_path.remove(self)
        try: spec=importlib.util.find_spec(name)
        finally: sys.meta_path.insert(0,self)
        ld=spec.loader; orig=ld.exec_module
        def ex(m,orig=orig):
            orig(m); _fix(m)
        ld.exec_module=ex; return spec
import importlib.util
sys.meta_path.insert(0,F())
