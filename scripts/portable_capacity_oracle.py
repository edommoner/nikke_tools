"""Independent CPU BuffManager for authored large definition tables.
Forced slots resolve the authored definitions rather than unrelated catalog skills.
"""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES


def observe(case):
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES},enemy={'def':0},full_burst=False,rng_acc={}))
    queries=[]
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        bm.tick(t)
        if op==0:bm.notify({0:'battle_start',7:'on_attack'}[event],t,NAMES[who])
        elif op==2:queries.append([bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES])
        else:raise ValueError('Capacity state oracle needs notify/query stimuli')
    return queries
