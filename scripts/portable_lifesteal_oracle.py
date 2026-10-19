"""Pinned native lifesteal and native CharState receipts, never GPU input."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from calculator.damage import calc_damage,default_hit_type
from calculator.sim_result import HitEvent
from portable_lifesteal_reference import native_lifesteal
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES

def observe(case):
    cfg=case['combat'];allies=case['environment']['allies'];attacks=case.get('base_atk',[1000]*5)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    for c,w in zip(chars,cfg['weapons']):authored_weapon(c,w)
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
    base={n:dict(atk=a,hp=h['base_hp'],**{'def':0}) for n,a,h in zip(NAMES,attacks,allies)}
    enemy={'def':0,'core_px':0,'code':None,'optimal_range_weapons':[]}
    state=dict(base_stats=base,hp={n:h['hp'] for n,h in zip(NAMES,allies)},hp_pct={n:h['hp']/h['base_hp']*100 for n,h in zip(NAMES,allies)},enemy=enemy,full_burst=False,rng_acc={},rng_expected=True,camera=set())
    bm=BM(chars,state=state);native=native_lifesteal();events=[];original=bm.notify
    def notify(event,t,caster,*args,**kw):
        events.append(dict(event=event,time=t,owner=NAMES.index(caster),source=NAMES.index(kw['heal_source']) if kw.get('heal_source') in NAMES else None));return original(event,t,caster,*args,**kw)
    bm.notify=notify
    actors=[authored_weapon_state(c,w,a) for c,w,a in zip(chars,cfg['weapons'],attacks)];started=False;total=[0]*5;queries=[]
    def land(ev,t):
        total[NAMES.index(ev.caster)]+=ev.damage;native(ev,bm,base,t)
    received={n:0.0 for n in NAMES};hits={n:0 for n in NAMES}
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        if op==4:
            if not started:
                for n in NAMES:bm.notify('battle_start',t,n)
                started=True
            bm.tick(t)
            for i,(actor,w) in enumerate(zip(actors,cfg['weapons'])):
                if w.get('enabled',True):
                    for ev in actor.tick(t,bm,enemy,dict(rng_mode='expected')):land(ev,t)
        elif op==18:
            if bm.is_down(NAMES[who]):continue
            buffs=bm.get_buffs(NAMES[who],'__enemy__',t)
            amount=calc_damage(base_atk=attacks[who],buffs=buffs,weapon=chars[who]['_weapon'],hit_type=default_hit_type(is_normal_atk=True,coeff=extra,is_final_atk=True),enemy_def=0,expected=True)['damage']
            bm.notify('hit_count',t,NAMES[who]);land(HitEvent(t=t,caster=NAMES[who],damage=amount,is_crit=False,hit_tag='normal'),t)
        elif op==30:pass
        elif op==25:
            from portable_health_oracle import apply_incoming
            for i,n in enumerate(NAMES):
                if arg & (1<<i):apply_incoming(bm,n,extra,extra2,t,received,hits)
        elif op==2:queries.append(dict(damage=total.copy(),allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n],down=bm.is_down(n)) for n in NAMES],attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        else:raise ValueError('Unsupported native lifesteal prototype stimulus')
    return dict(queries=queries,events=events)
