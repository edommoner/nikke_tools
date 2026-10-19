"""Independent pinned B3 controller/calculator and boss routing components.
Only authored raw inputs are used. Observations run after GPU readback; this
component oracle is separate from the real-squad original-CPU battle check.
"""
import copy
import engine_worker
from calculator import timeline,buff_manager
from calculator.buff_manager import BuffManager
from calculator.damage import calc_damage,default_hit_type
from calculator.boss_pattern import BossScript,Pattern,SummonSpec,_Add,ENEMY,AIM_ADDS
from calculator.sim_result import HitEvent
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES


def _observe(case, innate):
    cfg=case['combat'];weapons=cfg['weapons'];attacks=case.get('base_atk',[1000]*5)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    for c,w in zip(chars,weapons):authored_weapon(c,w)
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
    state=dict(base_stats={n:dict(atk=a,hp=1000000,**{'def':0}) for n,a in zip(NAMES,attacks)},
        hp={n:a.get('hp',a.get('base_hp',1000000)) for n,a in zip(NAMES,case.get('environment',{}).get('allies',[{}]*5))},hp_pct={n:a.get('hp',a.get('base_hp',1000000))/a.get('base_hp',1000000)*100 for n,a in zip(NAMES,case.get('environment',{}).get('allies',[{}]*5))},
        full_burst=False,rng_acc={},rng_expected=True,burst_casted={},burst_cycle_users={},
        burst_stages={n:str(w.get('stage',0)) for n,w in zip(NAMES,weapons)},
        burst_gauge=cfg.get('initial_gauge',0),burst_gauge_charging=True,camera=set())
    enemy=dict(**{'def':cfg['targets'][0].get('defense',0)},core_px=0,code=None,optimal_range_weapons=[])
    state['enemy']=enemy;bm=BM(chars,state=state)
    actors={n:authored_weapon_state(c,w,a) for n,c,w,a in zip(NAMES,chars,weapons,attacks)}
    pattern=Pattern(idx=0,id='pending-components',kind='summon',after=())
    boss=BossScript([pattern],enemy,lambda *_:False);run=boss._runs[0];run.active=True
    run.adds=[_Add(id=f'add:{i}',name=f'add:{i}',spec=SummonSpec(name=f'add:{i}',hp=t['hp']),order=i,gone='' if t.get('active',True) else '퇴장') for i,t in enumerate(cfg['targets']) if i]
    boss.aim_of={n:'body' for n in NAMES};bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,caster=caster)
    total=[0]*5;body=[0]*5;packets=[];enqueued=0;fired=0;immediate=[];pending_packets=[]
    def land(event,cast_time=None,hit_index=1,hit_count=1):
        who=NAMES.index(event.caster);selected=boss.route(event);mask=0
        for target,weight in selected:
            index=0 if target==ENEMY else int(target.split(':')[1]);mask|=1<<index
            share=event.damage if weight==1 else round(event.damage*weight)
            total[who]+=share
            if index:boss.hit_add(HitEvent(t=event.t,caster=event.caster,damage=share,is_crit=False,hit_tag=event.hit_tag),target,event.t)
            else:body[who]+=share
        packets.append(dict(effect=event.skill_name,time=event.t,pending_burst=cast_time is not None,cast_time=cast_time,
            target_order=[0 if target==ENEMY else int(target.split(':')[1]) for target,_ in selected],target_mask=mask,hit_index=hit_index,hit_count=hit_count,delivered_amount=event.damage))
    class Controller(timeline.BurstController):
        def _fire_pending_burst_dmg(self,t,bm):
            nonlocal fired,pending_packets
            before=list(self._pending_burst_dmg);events=super()._fire_pending_burst_dmg(t,bm);offset=0
            for _,eff,hits in before:
                for hit in range(hits):pending_packets.append((events[offset],eff['_component_cast_time'],hit+1,hits));offset+=1
            assert offset==len(events)
            fired+=len(before);return events
    ctrl=Controller(chars,dict(burst_gauge_mode='accumulate'),actors,enemy)
    timeline._register_instant_handlers(bm,actors,ctrl)
    def damage(e,caster,t):
        nonlocal enqueued
        value=e.get('fixed_value',e.get('values',{}).get('10',0));parts=e['stat'].split(':');hits=int(parts[1]) if len(parts)>1 else 1
        if not value:return
        if e['stat']=='bonus_damage' and 'burst_cast' in e['trigger']['timing'] and innate[caster]=='3':
            count=1
            if e.get('target','').startswith('same_target:'):
                ref=e['target'].split(':',1)[1];parent=next(x for x,n in raw if n==caster and x['name']==ref);p=parent['stat'].split(':');count=int(p[1]) if len(p)>1 else 1
            ctrl._pending_burst_dmg.append((caster,{**e,'_coeff':value,'_component_cast_time':t,'_exclude_buffs':timeline._later_burst_cast_buffs(bm,caster,e)},count));enqueued+=1;return
        for hit in range(hits):
            buffs=bm.get_buffs(caster,'__enemy__',t)
            ht=default_hit_type(is_normal_atk=False,is_full_burst=state['full_burst'],coeff=value,is_final_atk=True,is_burst_damage=parts[0]=='burst_damage',is_sequential=parts[0]=='sequential_damage')
            amount=calc_damage(base_atk=actors[caster].base_atk,buffs=buffs,weapon=actors[caster].weapon,hit_type=ht,enemy_def=enemy['def'],expected=True)['damage']
            immediate.append((HitEvent(t=t,caster=caster,damage=amount,is_crit=False,hit_tag=parts[0],skill_name=e['name'],rule=e['target']),None,hit+1,hits))
            bm.notify('hit_count:'+e['name'],t,caster)
        bm.add_burst_gauge(actors[caster]._burst_gain(buffs,hits),t,caster,e['name'])
    bm.register_damage_handler(damage)
    commands=[];frame=0;clock=0.0;acc=cfg.get('clock')=='accumulated'
    for command in case['script']:
        if command[1]==24:
            while frame<=10800 and (clock if acc else frame/60)<=command[0]:
                commands.append([clock if acc else frame/60,4,0,0,0,-1,0,0]);frame+=1
                if acc:clock+=1/60
        else:commands.append(command)
    queries=[];started=False
    for t,op,event,who,arg,index,extra,extra2 in commands:
        if op==4:
            if not started:
                for n in NAMES:bm.notify('battle_start',t,n)
                started=True
            bm.tick(t)
            for packet in immediate:land(*packet)
            immediate.clear();ctrl.tick(t,bm,state)
            for packet in pending_packets:land(*packet)
            pending_packets.clear()
        elif op==0:bm.notify({7:'on_attack',19:'event:full_reload'}[event],t,NAMES[who])
        elif op==20:boss.aim_of[NAMES[who]]=AIM_ADDS if arg else 'body'
        elif op==25:
            for i,n in enumerate(NAMES):
                if arg & (1<<i):state['hp'][n]=max(0,state['hp'][n]-max(extra*extra2/100,1));bm.sync_hp(n)
        elif op==2:
            for packet in immediate:land(*packet)
            immediate.clear()
            phase=ctrl._phase;phase_id=0 if phase=='idle' else 4 if phase=='switching' else 5 if phase=='full_burst' else int(phase.split(':')[1])
            queries.append(dict(damage=total.copy(),body_damage=body.copy(),pending_burst=dict(count=len(ctrl._pending_burst_dmg),enqueued=enqueued,fired=fired),attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES],combat=dict(phase=phase_id,gauge=state['burst_gauge'])))
        else:raise ValueError('Unported pending component stimulus')
    return dict(queries=queries,packets=packets,**(dict(carrier_births=__import__('portable_carrier_observer').records(bm,raw)) if case.get('inspect_carrier_activation') else {}))


def observe(case):
    innate={n:str(engine_worker.META[n]['burst_stage']) for n in NAMES};tables=[]
    for table in (buff_manager._NIKKE,timeline._NIKKE):
        if not any(table is prior for prior,_ in tables):tables.append((table,{n:table[n] for n in NAMES}))
    try:
        for table,saved in tables:
            for n,w in zip(NAMES,case['combat']['weapons']):
                metadata=dict(saved[n]);metadata.update(burst_stage=str(w.get('stage',0)),burst_cooldown=w.get('cooldown',40));metadata['charge_time']=0;table[n]=metadata
        return _observe(case,innate)
    finally:
        for table,saved in tables:
            for n,metadata in saved.items():table[n]=metadata
