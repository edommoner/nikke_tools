"""Independent damage/routing/accounting components, not a full CPU battle.
Uses the pinned BuffManager, calc_damage, BossScript.route and hit_add after GPU
readback. This deliberately does not certify deferred landing or boss schedules.
"""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from calculator.damage import calc_damage,default_hit_type
from calculator.boss_pattern import BossScript,Pattern,SummonSpec,DEFAULT_BOSS_ATK,_Add,ENEMY,AIM_ADDS
from calculator.sim_result import HitEvent
from timer_registry_cases import NAMES


def observe(case):
    config=case['combat'];targets=config['targets'];attacks=case.get('base_atk',[1000]*5)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
    enemy=dict(**{'def':targets[0].get('defense',0)},core_px=0,code=None,optimal_range_weapons=[],atk=targets[0].get('attack',DEFAULT_BOSS_ATK))
    bm=BM(chars,state=dict(base_stats={n:dict(atk=a,hp=1000000,**{'def':case.get('environment',{}).get('allies',[{} for _ in NAMES])[NAMES.index(n)].get('base_defense',0)}) for n,a in zip(NAMES,attacks)},enemy=enemy,
                         full_burst=False,rng_acc={},rng_expected=True))
    pattern=Pattern(idx=0,id='authored-adds',kind='summon',after=())
    boss=BossScript([pattern],enemy,lambda *_:False);run=boss._runs[0];run.active=True
    run.adds=[_Add(id=f'__enemy__:{i}',name=f'__enemy__:{i}',spec=SummonSpec(name=f'__enemy__:{i}',hp=t['hp'],atk=t.get('attack',0)),order=i,gone='' if t.get('active',True) else '퇴장') for i,t in enumerate(targets) if i]
    auto=config.get('automatic_add_aim',[False]*5)
    boss.aim_of={n:AIM_ADDS if auto[i] else 'body' for i,n in enumerate(NAMES)};bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,caster=caster)
    raw_damage=[0]*5;body_damage=[0]*5;overkill=[0]*5;target_damage=[0]*len(targets);target_scored=[0]*len(targets);packets=[];gauge=config.get('initial_gauge',0)
    normal_target=0;native_hits=[0]*len(targets)
    def damage(effect,caster,t,*,normal=False):
        nonlocal gauge,normal_target
        who=NAMES.index(caster);parts=effect['stat'].split(':');kind=parts[0];hits=1
        coefficient=effect.get('fixed_value',effect.get('values',{}).get('10',0));target=effect['target']
        if effect.get('scaling')=='stack_count' and kind=='dot_damage':
            entry=next((a for a in bm._active if a.caster==caster and a.effect.get('name')==effect.get('name')),None)
            coefficient*=entry.stack if entry is not None else 0
        if coefficient==0:return
        # Same precedence as the original timeline's hit_count block; live
        # quantities come from original BuffManager.ref_count, never GPU state.
        if effect.get('hit_count_gauge_ref'):
            hits=int(bm.state.get('gauges',{}).get(caster,{}).get(effect['hit_count_gauge_ref'],0))
        elif len(parts)>1 and parts[1].lstrip('-').isdigit():hits=int(parts[1])
        elif len(parts)>1:
            value=bm.ref_count(caster,parts[1]);hits=value if value is not None else 1
        elif effect.get('scaling')=='stack_count' and kind!='dot_damage':
            value=bm.ref_count(caster,effect.get('scaling_ref',''));hits=value if value is not None else 1
        for hit in range(hits):
            buffs=bm.get_buffs(caster,'__enemy__',t)
            ht=default_hit_type(is_normal_atk=kind=='auto_damage',coeff=coefficient,is_final_atk=True,is_full_burst=bm.state['full_burst'],
                is_burst_damage=kind in ('burst_damage','armor_break_burst_damage'),
                is_aoe_burst=kind in ('burst_damage','armor_break_burst_damage') and target=='all_enemies',
                is_single_burst=kind in ('burst_damage','armor_break_burst_damage') and target.startswith('enemies_') and target.endswith(':1'),
                is_armor_break_damage=kind in ('armor_break_damage','armor_break_burst_damage'),is_split=kind=='split_damage',
                is_dot=kind=='dot_damage',is_sequential=kind=='sequential_damage',is_projectile_attachment=kind=='projectile_attachment_damage',
                is_projectile_explosion=kind=='projectile_explosion_damage',is_pierce_damage=kind=='pierce_damage',is_core_damage=kind=='core_damage',is_core=kind=='core_damage')
            amount=calc_damage(base_atk=attacks[who],buffs=buffs,weapon=chars[who]['_weapon'],hit_type=ht,enemy_def=enemy['def'],expected=True)['damage']
            retained=None
            if effect.get('tick_interval'):
                entry=next((a for a in bm._active if a.effect is effect and a.caster==caster),None)
                if entry is not None and entry.target_chars is not None:retained=tuple(x for x in entry.target_chars if x.startswith('__enemy__'))
            event=HitEvent(t=t,caster=caster,damage=amount,is_crit=False,hit_tag=kind,rule=target,split=kind=='split_damage',to=retained)
            selected=boss.route(event);mask=0
            for name,weight in selected:
                index=0 if name==ENEMY else int(name.split(':')[1]);share=amount if weight==1.0 else round(amount*weight);mask|=1<<index
                raw_damage[who]+=share;target_damage[index]+=share;native_hits[index]+=1
                if normal:normal_target=index
                if index:
                    actor=run.adds[index-1];scored=min(share,actor.spec.hp-actor.dealt) if actor.alive else 0
                    boss.hit_add(HitEvent(t=t,caster=caster,damage=share,is_crit=False,hit_tag=kind),name,t)
                else:scored=share;body_damage[who]+=share
                target_scored[index]+=scored;overkill[who]+=share-scored
            if not normal:packets.append(dict(target_order=[0 if name==ENEMY else int(name.split(':')[1]) for name,_ in selected],effect=effect['name'],time=t,target_mask=mask,hit_index=hit+1,hit_count=hits,weighted_amount=amount*(selected[0][1] if selected else 1.0),delivered_amount=(amount if not selected or selected[0][1]==1.0 else round(amount*selected[0][1]))))
            bm.notify('hit_count' if normal else 'hit_count:'+effect['name'],t,caster)
        if not bm.state['full_burst']:gauge=min(100,gauge+config['weapons'][who].get('gauge',0)*hits)
    bm.register_damage_handler(damage)
    queries=[];started=False;spawn_order=len(targets);periodic_snapshots=[];clock_ids={}
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        if op==4:
            if not started:
                for n in NAMES:bm.notify('battle_start',t,n)
                started=True
            bm.tick(t)
        elif op==0:
            bm.tick(t);bm.notify({7:'on_attack',8:'hit_count',19:'event:full_reload'}[event],t,NAMES[who])
        elif op==18:damage(dict(stat='auto_damage',target='',fixed_value=extra,name=''),NAMES[who],t,normal=True)
        elif op==20:boss.aim_of[NAMES[who]]=AIM_ADDS if arg else 'body'
        elif op==27:boss.aim_of[NAMES[who]]=AIM_ADDS if arg else 'body'
        elif op==22:
            if arg==0:raise ValueError('Native BossScript body is always present')
            if case.get('periodic_reference'):bm.drop_enemies([run.adds[arg-1].id],t)
            run.adds[arg-1].gone='퇴장';bm._invalidate_buffs_cache()
        elif op==21:
            if arg==0:raise ValueError('Native BossScript body is always present')
            if case.get('periodic_reference'):bm.drop_enemies([run.adds[arg-1].id],t)
            run.adds[arg-1]=_Add(id=f'__enemy__:{arg}',name=f'__enemy__:{arg}',spec=SummonSpec(name=f'__enemy__:{arg}',hp=extra,atk=targets[arg].get('attack',0)),order=spawn_order)
            spawn_order+=1;bm._invalidate_buffs_cache()
        elif op==2:
            queries.append(dict(body_damage=body_damage.copy(),add_damage=[boss.add_dealt.get(n,0) for n in NAMES],damage=raw_damage.copy(),scored_damage=[body_damage[i]+boss.add_dealt.get(n,0) for i,n in enumerate(NAMES)],add_overkill=overkill.copy(),
                                attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES],combat=dict(gauge=gauge)))
            if case.get('periodic_reference'):
                bindings=[]
                for idx,(effect,owner) in enumerate(raw):
                    entry=next((a for a in bm._active if a.effect is effect and a.caster==owner),None)
                    timer=bm._dot_timers.get(id(effect));identity=getattr(timer,'clock',None)
                    if identity is not None:clock_ids.setdefault(identity,len(clock_ids)+1)
                    bindings.append(dict(definition=idx,active=entry is not None,targets=list(entry.target_chars or []) if entry else [],stack=entry.stack if entry else 0,due=timer[1] if timer else 0,expiry=timer[2] if timer else 0,clock=clock_ids.get(identity,0)))
                periodic_snapshots.append(bindings)
            if case.get('normal_aim_reference'):
                queries[-1]['combat'].update(target=normal_target,targets=[dict(damage=amount,hits=hits) for amount,hits in zip(target_damage,native_hits)])
        else:raise ValueError('Enemy component oracle supports notifications, aim, add life changes, authored frames and queries')
    return dict(queries=queries,packets=packets,target_scored_damage=target_scored,periodic_snapshots=periodic_snapshots)
