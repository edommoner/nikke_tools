"""Independent pinned CPU state/instant handlers, evaluated after GPU readback."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from calculator import timeline
from timer_registry_cases import NAMES


def observe(case, *, with_carriers=False, with_cover=False):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
    allies=case['environment']['allies']
    base={n:dict(atk=1000,hp=a['base_hp'],**{'def':a.get('base_defense',0)}) for n,a in zip(NAMES,allies)}
    state=dict(base_stats=base,hp={n:a.get('hp',a['base_hp']) for n,a in zip(NAMES,allies)},
               hp_pct={n:a.get('hp',a['base_hp'])/a['base_hp']*100 for n,a in zip(NAMES,allies)},
               enemy={'def':0},full_burst=False,rng_acc={},rng_expected=True)
    state.update(cover_base_hp={n:a.get('base_cover_hp',2000000) for n,a in zip(NAMES,allies)},cover_max_hp={n:a.get('base_cover_hp',2000000) for n,a in zip(NAMES,allies)},cover_hp={n:a.get('cover_hp',a.get('base_cover_hp',2000000)) for n,a in zip(NAMES,allies)})
    cover_damage={n:0.0 for n in NAMES}
    bm=BM(chars,state=state)
    timeline._register_instant_handlers(bm,{n:object() for n in NAMES},None)
    events={0:'battle_start',7:'on_attack',17:'event:cover_healed',19:'event:full_reload',36:'event:cover_hit'}
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
        if with_cover and case.get('environment',{}).get('cover_sync',True):
            for n in NAMES:bm.sync_cover_hp(n,t)
        if op==0:bm.notify(events[event],t,NAMES[who])
        elif op==2:
            queries.append(dict(allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n],defense=bm._effective_def(n),down=bm.is_down(n),received_damage=received[n],received_hits=hits[n]) for n in NAMES],
                                attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        elif op==26:
            for i,n in enumerate(NAMES):
                if arg & (1<<i) and not bm.is_down(n) and bm.cover_alive(n) and extra:
                    taken=min(bm.state['cover_hp'][n],extra);cover_damage[n]+=taken;bm.state['cover_hp'][n]-=taken
                    if bm.state['cover_hp'][n]<=0:bm.break_cover(n)
                    bm.notify('event:cover_hit',t,n)
        elif op==25:
            for i,n in enumerate(NAMES):
                if arg & (1<<i):land(n,extra,extra2,t)
        elif op!=18:raise ValueError('Unsupported health reference stimulus')
        if with_cover and op==2:queries[-1]['covers']=[dict(hp=bm.state['cover_hp'][n],max_hp=bm.state['cover_max_hp'][n],effective_max_hp=bm.cover_max_hp(n,t),damage=cover_damage[n]) for n in NAMES]
    if with_carriers:
        carriers=[]
        for ab in bm._active:
            definition=next(i for i,(e,_) in enumerate(raw) if e is ab.effect)
            carriers.append(dict(definition=definition,effect=ab.effect['name'],
                                 recipients=sum(1<<NAMES.index(n) for n in (ab.target_chars or [])),
                                 lazy_pending=ab.target_chars is None,stacks=ab.stack,end=1e30 if ab.expires_at==float('inf') else ab.expires_at,
                                 activated=ab.activated_at,hp_snapshot=ab.hp_bonus_flat))
        return dict(queries=queries,carriers=carriers)
    return queries
