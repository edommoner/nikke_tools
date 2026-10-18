"""Independent pinned CharState/BuffManager for up to five authored shooters.
Only evaluated after GPU readback; its shots/stacks never become GPU input.
"""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from calculator import timeline,buff_manager
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES


def _observe(case):
    config=case['combat'];weapons=config['weapons']
    if len(weapons)!=5 or any(w.get('stage',0) for w in weapons):raise ValueError('Bullet oracle needs five non-burst weapon descriptors')
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    for char,weapon in zip(chars,weapons):authored_weapon(char,weapon)
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
    allies=case.get('environment',{}).get('allies',[dict(base_hp=1000000) for _ in range(5)])
    attacks=case.get('base_atk',[1000]*5)
    base={n:dict(atk=a,hp=h['base_hp'],**{'def':h.get('base_defense',0)}) for n,a,h in zip(NAMES,attacks,allies)}
    enemy=dict(defense=0,core_px=0,code=None,optimal_range_weapons=[])
    enemy['def']=config['targets'][0].get('defense',0)
    state=dict(base_stats=base,enemy=enemy,full_burst=False,rng_acc={},rng_expected=True,camera=set(),
               hp={n:h.get('hp',h['base_hp']) for n,h in zip(NAMES,allies)},
               hp_pct={n:h.get('hp',h['base_hp'])/h['base_hp']*100 for n,h in zip(NAMES,allies)})
    bm=BM(chars,state=state)
    actors=[authored_weapon_state(c,w,a) for c,w,a in zip(chars,weapons,attacks)]
    timeline._register_instant_handlers(bm,dict(zip(NAMES,actors)),None)
    commands=[];next_frame=0
    for command in case['script']:
        if command[1]==24:
            while next_frame<=10800 and next_frame/60<=command[0]:
                commands.append([next_frame/60,4,0,0,0,-1,0,0]);next_frame+=1
        else:commands.append(command)
    totals=[0]*5;shots=[0]*5;started=False;queries=[]
    events={7:'on_attack',8:'hit_count',10:'full_charge',11:'full_charge_fire',12:'full_charge_hit',
            14:'last_bullet',19:'event:full_reload',20:'pellet_hit',21:'last_bullet_fire',26:'squad_ammo_consume'}
    for t,op,event,who,arg,index,extra,extra2 in commands:
        if op==4:
            if not started:
                for name in NAMES:bm.notify('battle_start',t,name)
                for name,actor in zip(NAMES,actors):actor.ammo=actor._full_ammo(bm,t)
                started=True
            bm.tick(t)
            for i,(actor,w) in enumerate(zip(actors,weapons)):
                if not w.get('enabled',False) or bm.is_down(NAMES[i]):continue
                hits=actor.tick(t,bm,enemy,{'rng_mode':'expected'})
                totals[i]+=sum(hit.damage for hit in hits);shots[i]+=int(bool(hits))
        elif op==0:bm.notify(events[event],t,NAMES[who])
        elif op==2:
            queries.append(dict(damage=totals.copy(),attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES],
                                combat=dict(weapons=[dict(ammo=a.ammo,shots=n) for a,n in zip(actors,shots)]),
                                allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n]) for n in NAMES]))
        else:raise ValueError('Bullet oracle supports authored frames, external notifications and queries')
    carriers=[]
    for ab in bm._active:
        definition=next(i for i,(e,_) in enumerate(raw) if e is ab.effect)
        record=dict(definition=definition,effect=ab.effect['name'],recipients=sum(1<<NAMES.index(n) for n in (ab.target_chars or [])),
                    stacks=ab.stack,end=1e30 if ab.expires_at==float('inf') else ab.expires_at,activated=ab.activated_at,lazy_pending=ab.target_chars is None)
        if ab.effect.get('duration_bullets',-1)>0:
            record.update(bullet_left=ab.bullets_left,recipient_bullets=[ab.bullets_per_target.get(n,0) for n in NAMES],recipient_stack_overrides=[ab.per_char_stacks.get(n,0) for n in NAMES])
        carriers.append(record)
    return dict(queries=queries,carriers=carriers)


def observe(case):
    saved={n:buff_manager._NIKKE[n] for n in NAMES}
    try:
        for name,w in zip(NAMES,case['combat']['weapons']):
            replacement=dict(saved[name]);charge=w.get('raw_charge',w.get('charge',1) if w.get('mode')=='charge' else 0)
            if charge:replacement['charge_time']=charge
            else:replacement.pop('charge_time',None)
            buff_manager._NIKKE[name]=replacement
        return _observe(case)
    finally:
        for name,metadata in saved.items():buff_manager._NIKKE[name]=metadata
