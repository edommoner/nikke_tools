"""Independent pinned CPU state/instant handlers, evaluated after GPU readback."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from calculator import timeline
from timer_registry_cases import NAMES


def observe(case):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
    allies=case['environment']['allies']
    base={n:dict(atk=1000,hp=a['base_hp'],**{'def':a.get('base_defense',0)}) for n,a in zip(NAMES,allies)}
    state=dict(base_stats=base,hp={n:a.get('hp',a['base_hp']) for n,a in zip(NAMES,allies)},
               hp_pct={n:a.get('hp',a['base_hp'])/a['base_hp']*100 for n,a in zip(NAMES,allies)},
               enemy={'def':0},full_burst=False,rng_acc={},rng_expected=True)
    bm=BM(chars,state=state)
    timeline._register_instant_handlers(bm,{n:object() for n in NAMES},None)
    events={0:'battle_start',7:'on_attack',19:'event:full_reload'}
    queries=[]
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        bm.tick(t)
        if op==0:bm.notify(events[event],t,NAMES[who])
        elif op==2:
            queries.append(dict(allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n],defense=bm._effective_def(n)) for n in NAMES],
                                attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        elif op!=18:raise ValueError('Unsupported health reference stimulus')
    return queries
