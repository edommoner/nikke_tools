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
    received={n:0.0 for n in NAMES};hits={n:0 for n in NAMES}
    def land(name,attack,coefficient,t):
        if bm.is_down(name):return
        amount=max(max(attack-bm._effective_def(name),0.0)*coefficient/100.0*max(0.0,1.0+bm.incoming_dmg_pct(name,t)/100.0),1.0)
        if bm.has_live_stat(name,'invincible',t):amount=0.0
        if amount and bm.state['hp'][name]-amount<=0 and bm.has_live_stat(name,'undying',t):amount=max(bm.state['hp'][name]-1.0,0.0)
        if amount and bm.state['hp'][name]-amount<=0:
            bm.notify('event:lethal_hit',t,name)
            if bm.has_live_stat(name,'undying',t):amount=max(bm.state['hp'][name]-1.0,0.0)
        fell=bool(amount) and bm.state['hp'][name]-amount<=0
        received[name]+=amount;hits[name]+=1
        if amount:
            bm.state['hp'][name]=max(0.0,bm.state['hp'][name]-amount)
            if not fell:bm.sync_hp(name)
        bm.notify('received_hit',t,name)
        if fell and not bm.is_down(name):
            bm.state['hp'][name]=0.0;bm.knock_down(name,t);bm.notify_down(name,t)
    queries=[]
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        bm.tick(t)
        if op==0:bm.notify(events[event],t,NAMES[who])
        elif op==2:
            queries.append(dict(allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n],defense=bm._effective_def(n),down=bm.is_down(n),received_damage=received[n],received_hits=hits[n]) for n in NAMES],
                                attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        elif op==25:
            for i,n in enumerate(NAMES):
                if arg & (1<<i):land(n,extra,extra2,t)
        elif op!=18:raise ValueError('Unsupported health reference stimulus')
    return queries
