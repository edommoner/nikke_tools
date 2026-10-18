"""Fail-closed application adapter for shared GPU effect/event execution.

This is an external-stimulus evaluator, not the autonomous weapon/burst loop.
No CPU simulation or CPU-produced state is supplied to the GPU.
"""
import math
import re
import struct

from portable_backend import execute
from portable_damage_specs import BUFFS,DAMAGE_FAMILIES
from portable_specs import ABI, LIMITS as L, FIELDS as F, check_schema


class UnsupportedPortable(ValueError):
    pass


class PortableExecutionError(RuntimeError):
    def __init__(self,results,evidence):
        self.results=results
        self.evidence=evidence
        self.statuses=[r['status'] for r in results]
        super().__init__('Portable GPU execution failed closed: '+str(self.statuses))


def double_words(value):
    if isinstance(value, bool) or not isinstance(value, (float,int)) or not math.isfinite(value):
        raise ValueError('Finite numeric input required')
    return list(struct.unpack('<II',struct.pack('<d',value)))


def validate_effect(eff, *, combat=None):
    allowed = {'name','source','type','stat','fixed_value','values','duration','duration_values',
               'target','trigger','note','polarity','favorite','_source_tag','_quant_group','max_ammo_reduction_exclusive','trigger_values','max_stack','max_trigger','tick_interval','tick_start','target_effect','target_skill'}
    effect_allowed=allowed | ({'scaling'} if eff.get('stat')=='heal_hp_pct' else set()) | ({'toggle','weapon_type','damage_coeff','max_ammo','duration_bullets','charge','charge_time','full_charge_mult','reload_time','fire_rate','fire_rate_max','warmup_bullets','pellets','muzzles','post_fire_delay','cover_during_delay','first_damage_coeff','max_ammo_buff_applies','burst_energy','core_dmg_mult'} if eff.get('type')=='weapon_change' else set())
    if set(eff)-effect_allowed:
        raise UnsupportedPortable('Unported effect fields: '+', '.join(sorted(set(eff)-effect_allowed)))
    from portable_trigger_specs import validate_input
    try:validate_input(eff)
    except ValueError as error:raise UnsupportedPortable(str(error)) from error
    kind,stat,target=eff.get('type'),eff.get('stat'),eff.get('target','self')
    if combat is None and stat in ('attack_speed_pct','mg_warmup_speed_pct','reload_speed_pct','reload_ratio_pct','accuracy_pct','max_ammo_pct','max_ammo_flat','charge_speed_pct','charge_speed_caster_based_pct','charge_time_flat','charge_time_fixed','charge_speed_buff_immune','charge_speed_debuff_immune','charge_speed_overflow_conversion_pct'):
        raise UnsupportedPortable('Weapon modifier requires combat mechanics')
    if combat is None and set(eff.get('trigger',{}).get('condition',[])) & {'during_charge','burst_casted','burst_not_casted','has_burst1_ally','no_burst1_ally'}:
        raise UnsupportedPortable('Predicate requires combat-owned charge/burst state')
    if kind=='buff':
        if (stat not in BUFFS and not (isinstance(stat,str) and re.fullmatch(r'burst_stage_override:(?:[123A]|reenter[123])',stat))) or target not in ('self','all_allies'):
            raise UnsupportedPortable('Unported buff or recipient selector')
    elif kind=='damage':
        if stat not in DAMAGE_FAMILIES or target not in ('target','boss'):
            raise UnsupportedPortable('Unported damage family or geometry')
    elif kind=='instant':
        if stat in ('heal_hp_pct','current_hp_reduce'):
            if target not in ('self','all_allies'):raise UnsupportedPortable('Unported health recipient selector')
            if eff.get('scaling') not in (None,'max_hp'):raise UnsupportedPortable('Unported healing basis')
        elif stat not in ('remove_named_buff','force_skill_use','burst_reentry') or target!='self':
            raise UnsupportedPortable('Unported instant or recipient selector')
    elif kind=='weapon_change':
        if combat is None or target!='self':raise UnsupportedPortable('Weapon mode requires combat and self recipient')
        if eff.get('tick_interval'):raise UnsupportedPortable('Periodic weapon-mode activation is not ported')
    else:raise UnsupportedPortable('Unported effect kind')
    if (stat=='burst_reentry' or isinstance(stat,str) and stat.startswith('burst_stage_override:')) and (combat is None or target!='self'):
        raise UnsupportedPortable('Burst stage state requires combat and self recipient')
    if eff.get('_source_tag') is not None and not isinstance(eff['_source_tag'],str):raise UnsupportedPortable('Invalid quantity source tag')
    if eff.get('_quant_group') is not None and type(eff['_quant_group']) not in (str,int):raise UnsupportedPortable('Invalid quantity group')
    if 'max_ammo_reduction_exclusive' in eff and (kind!='buff' or stat!='max_ammo_pct' or type(eff['max_ammo_reduction_exclusive']) is not bool):raise UnsupportedPortable('Invalid exclusive ammo reduction')
    if 'cover_during_delay' in eff and type(eff['cover_during_delay']) is not bool:raise UnsupportedPortable('Charge delay cover policy must be boolean')
    if 'max_ammo_buff_applies' in eff and type(eff['max_ammo_buff_applies']) is not bool:raise UnsupportedPortable('Invalid mode ammo-buff policy')
    if stat=='charge_time_fixed' and 'fixed_value' in eff and not 0<=eff['fixed_value']<=180:raise UnsupportedPortable('Invalid fixed charge time')
    if stat=='charge_time_fixed' and 'values' in eff:raise UnsupportedPortable('Fixed charge time needs a literal fixed_value or bare presence marker')
    # Count/stack bounds are discrete. Do not truncate malformed definitions.
    for key in ('max_stack','max_trigger'):
        value=eff.get(key,1 if key=='max_stack' else -1)
        if type(value) is not int or not -1<=value<=2**31-1 or key=='max_stack' and value==0:
            raise ValueError('Invalid '+key)


def compile_program(chars, effects, script, base_atk, *, defense=0, core_ratio=0, core_bonus=1, combat=None, allies=None):
    import detail_gpu as legacy
    check_schema()
    effects = list(effects)
    if not 1<=len(effects)<=L['DEFINITIONS']:raise UnsupportedPortable('Portable definition capacity exceeded')
    for eff, owner in effects:validate_effect(eff,combat=combat)
    program=legacy.compile_effects(chars,effects)
    if len(program['effects'])!=len(effects) or not 1<=len(effects)<=L['DEFINITIONS']:
        raise UnsupportedPortable('Portable definition capacity or expansion exceeded')
    seen_names={}
    for i,((eff,owner),row) in enumerate(zip(effects,program['effects'])):
        key=(owner,eff.get('name'));previous=seen_names.get(key,[])
        equipment=eff.get('type')=='buff' and eff.get('_source_tag')=='equipment'
        prior_equipment=all(effects[j][0].get('type')=='buff' and effects[j][0].get('_source_tag')=='equipment' for j in previous)
        distinct_stat=all(effects[j][0].get('stat')!=eff.get('stat') for j in previous)
        independent_quantity=eff.get('stat') in ('max_ammo_pct','charge_speed_pct','charge_speed_caster_based_pct')
        if previous and not (equipment and prior_equipment and
                             (distinct_stat and int(row[43])==-1 or independent_quantity and int(row[43]) in previous)):
            raise UnsupportedPortable('Multiple named carriers require distinct equipment components or verified quantity groups')
        seen_names.setdefault(key,[]).append(i)
    if not 1<=len(script)<=L['COMMANDS'] or len(base_atk)!=5:
        raise ValueError('Invalid portable command/base-stat dimensions')
    words=[0]*L['INPUT_WORDS'];words[0:3]=[ABI,len(effects),len(script)];words[5]=1
    for i,attack in enumerate(base_atk):
        if attack<0:raise ValueError('Negative base attack')
        words[8+2*i:10+2*i]=double_words(attack)
    for at,value in [(18,defense),(20,core_ratio),(22,core_bonus)]:
        if value<0:raise ValueError('Negative enemy/geometry input')
        words[at:at+2]=double_words(value)
    allies=allies if allies is not None else [{} for _ in range(5)]
    if not isinstance(allies,list) or len(allies)!=5:raise ValueError('Expected five initial ally states')
    for who,ally in enumerate(allies):
        if not isinstance(ally,dict) or set(ally)-{'base_hp','hp','base_defense'}:raise ValueError('Unsupported initial ally state')
        base=ally.get('base_hp',1000000);current=ally.get('hp',base);defense_value=ally.get('base_defense',0)
        for value in (base,current,defense_value):double_words(value)
        if not 0<base<=1e30 or not 0<=current<=base or not 0<=defense_value<=1e30:raise ValueError('Invalid initial ally health/defense')
        at=L['HEALTH_BASE']+who*L['HEALTH_WORDS']
        words[at:at+6]=[*double_words(base),*double_words(current),*double_words(defense_value)]
    words[24:26]=double_words(.15);words[26:28]=double_words(.5)
    for index,row in enumerate(program['effects']):
        compact=[0]*L['DEFINITION_WORDS']
        fields={'OWNER':int(row[0]),'KIND':int(row[1]),'STAT':int(row[2]),'NAME':int(row[3]),
                'MAX_STACK':int(row[9]),'BUDGET':int(row[57]),'IMMEDIATE':int(row[60]),
                'PRESERVE':int(effects[index][0].get('stat')=='dot_damage'),
                'EVENT':int(row[145]),'THRESHOLD':int(row[146]),'COUNT_MODE':int(row[147]),
                'EVENT_NAME':int(row[148]),'TARGET_NAME':int(row[36]),
                'FORCE_MASK':int(row[legacy.B3_MASK]),'RECIPIENTS':31 if row[4]==1 else 1<<int(row[0]),
                'TARGET':int(effects[index][0].get('target')=='boss'), 'STAGE_ARG':int(row[151]),
                'STAGE_OVERRIDE':int(row[252]),'REENTRY':int(row[253]),'TOGGLE':int(bool(int(row[213]) & 128)), 'DAMAGE_FLAGS':int(row[39])}
        for key,value in fields.items():compact[F[key]]=value & 0xffffffff
        for key,offset in [('VALUE',6),('DURATION',7),('INTERVAL',59)]:compact[F[key]:F[key]+2]=double_words(row[offset])
        at=L['DEFINITION_BASE']+index*L['DEFINITION_WORDS'];words[at:at+len(compact)]=compact
        from portable_trigger_specs import pack_descriptors
        pack_descriptors(words,index,row,L,F,double_words)
        # Quantity component identity is the source/group tuple, not its display name.
        # The pinned legacy equipment alias collapses components before rounding.
        extra=L['DEFINITION_EXTRA_BASE']+index*L['DEFINITION_EXTRA_WORDS']
        words[extra:extra+8]=[int(row[45]),int(row[55]),(-1 if int(row[2]) in (18,20,37) else int(row[43])) & 0xffffffff,int(row[213]),
                              *double_words(row[138]),int(row[139]),int(row[209])]
        force=L['FORCE_BASE']+index*L['MASK_WORDS']
        words[force:force+L['MASK_WORDS']]=[int(row[legacy.B3_MASK+k]) for k in range(L['MASK_WORDS'])]
        health=L['HEALTH_DEFINITION_BASE']+index*L['HEALTH_DEFINITION_WORDS']
        words[health:health+2]=[int(row[50]),int(effects[index][0].get('stat')=='def_pct') | (int(effects[index][0].get('stat')=='received_dmg_pct')<<1)]
        if row[1]==2:
            if row[7]<0 and row[14]>0:raise UnsupportedPortable('Infinite conditional weapon mode is not ported')
            from portable_combat import pack_mode
            pack_mode(words,index,row,double_words)
    combat_meta = None
    if combat is not None:
        from portable_combat import pack_combat
        combat_meta=pack_combat(words,combat,double_words)
        for eff,owner in effects:
            if eff.get('stat')=='accuracy_pct':
                recipients=range(5) if eff.get('target')=='all_allies' else [next(i for i,c in enumerate(chars) if c['name']==owner)]
                if any(words[L['WEAPON_MECHANICS_BASE']+i*L['WEAPON_MECHANICS_WORDS']+17]==0 for i in recipients):
                    raise UnsupportedPortable('Accuracy modifier requires explicit spread/core geometry for every recipient')
    if combat is not None and defense != 0:
        raise UnsupportedPortable('Combat uses explicit per-target defense')
    previous=-1; previous_frame=None; frame_mode=None
    for i,cmd in enumerate(script):
        if len(cmd)!=8:raise ValueError('Expected eight-word stimulus command')
        t,op,event,owner,arg,query,extra,extra2=cmd
        double_words(t)
        if not 0<=t<=180 or t<previous:raise ValueError('Commands must have monotonic times in 0..180 seconds')
        previous=t
        if op==25:
            if any(type(v) is not int for v in (op,event,owner,arg,query)) or event or owner or query!=-1 or not 1<=arg<=31:
                raise ValueError('Invalid incoming body-attack descriptor')
            double_words(extra);double_words(extra2)
            if not 0<=extra<=1e30 or not 0<=extra2<=1e6:raise ValueError('Invalid incoming attack/coefficient')
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*double_words(t),0,0,arg,0,0]
            at=L['INCOMING_BASE']+i*L['INCOMING_WORDS'];words[at:at+4]=[*double_words(extra),*double_words(extra2)]
            continue
        if op in (4,20,21,22,24):
            if combat is None:raise UnsupportedPortable('Combat command requires combat configuration')
            if any(type(v) is not int for v in (op,event,owner,arg,query,extra2)) or event or extra2 or not 0<=owner<5:
                raise ValueError('Invalid combat command')
            if op in (4,24):
                if frame_mode is not None and frame_mode!=op:raise UnsupportedPortable('Do not mix explicit frames and GPU timeline advancement')
                frame_mode=op
            if op==24:
                if arg!=0 or extra!=0:raise ValueError('Timeline advance has no shot payload')
            if op==4:
                if arg!=0 or extra!=0:raise ValueError('Frame has no shot payload')
                if previous_frame is None and t!=0 or previous_frame is not None and t<=previous_frame:
                    raise ValueError('Combat frames must start at zero and increase strictly')
                previous_frame=t
            if op in (20,21,22) and not 0<=arg<len(combat['targets']):raise ValueError('Invalid target slot')
            if op==21:
                double_words(extra)
                if not 1<=extra<=1e30:raise ValueError('Invalid spawn HP')
            elif extra!=0:raise ValueError('Unexpected combat payload')
            at=L['COMMAND_BASE']+i*8
            words[at:at+8]=[op,*double_words(t),event,owner,arg,*(double_words(extra) if op==21 else [query & 0xffffffff,0])]
            continue
        if op not in (0,2,18) or any(type(v) is not int for v in (op,event,owner,arg,query,extra2)):
            raise UnsupportedPortable('Only external notify, normal impact and query commands are connected')
        if op!=18 and (type(extra) is not int or extra):raise UnsupportedPortable('Unexpected stimulus payload')
        if op==18:
            double_words(extra)
            if event or not 0<extra<=1e6:raise UnsupportedPortable('Invalid normal-impact coefficient')
        if not 0<=owner<5 or extra2 or (op==0 and (event not in (0,1,2,3,4,7,8,10,11,12,14,19,20,21,26,29,49) or event==49 and not 0<=arg<len(program['states']))):
            raise UnsupportedPortable('Unsupported stimulus event, owner, or payload')
        if op==2 and (event!=0 or query<0 or query>=L['COMMANDS']):raise ValueError('Invalid query index')
        if combat is not None and op==0 and event in (0,1,2,3,4):raise UnsupportedPortable('Combat emits its own startup and burst notifications')
        at=L['COMMAND_BASE']+i*8
        words[at:at+8]=[op,*double_words(t),event,owner,*(double_words(extra) if op==18 else [arg & 0xffffffff,query & 0xffffffff]),0]
    return words,dict(states=program['states'],names=[c['name'] for c in chars],effects=[e['name'] for e,n in effects],combat=combat_meta,timeline=frame_mode==24)


def decode(words,metadata):
    def number(at):return struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
    if words[1]>L['COMMANDS'] or words[2]>L['TRACE']:
        raise RuntimeError('Invalid portable output dimensions')
    queries=[]
    for i in range(words[1]):
        at=L['QUERY_BASE']+i*L['QUERY_WORDS']
        queries.append(dict(time=number(at),damage=[number(at+2+2*k) for k in range(5)],
                            active_timer_mask=words[at+12],active_timer_mask_words=list(words[L['TIMER_MASK_BASE']+i*L['MASK_WORDS']:L['TIMER_MASK_BASE']+(i+1)*L['MASK_WORDS']]),generation=words[at+13],
                            stack_depth=words[at+14],timer_clock=words[at+15],
                            attack_buffs=[number(at+16+2*k) for k in range(5)]))
    if metadata.get('combat') is not None:
        for i,q in enumerate(queries):
            at=L['COMBAT_QUERY_BASE']+i*L['COMBAT_QUERY_WORDS']
            q['combat']=dict(weapons=[dict(ammo=words[at+6*k],shots=words[at+6*k+1],next=number(at+6*k+2),reload_until=number(at+6*k+4)) for k in range(5)],
                             phase=words[at+30],cast_mask=words[at+31],gauge=number(at+32),action=number(at+34),full_end=number(at+36),target=words[at+38])
            states=L['COMBAT_STATE_QUERY_BASE']+i*L['COMBAT_STATE_QUERY_WORDS']
            q['combat']['targets']=[dict(generation=words[states+8*j],active=bool(words[states+8*j+1]),hp=number(states+8*j+2),damage=number(states+8*j+4),hits=words[states+8*j+6]) for j in range(len(metadata['combat']['targets']))]
            for who,w in enumerate(q['combat']['weapons']):
                at=states+64+who*8
                w.update(ready=number(at),charge_until=number(at+2),charging=bool(words[at+4]),aim=words[at+5],mode_index=words[at+6]-1,mode_shots=words[at+7])
            q['combat'].update(reentry_slot=bool(words[states+104]),reentry_done=words[states+105],casts=list(words[states+106:states+111]))
    for index,q in enumerate(queries):
        at=L['HEALTH_QUERY_BASE']+index*L['HEALTH_QUERY_WORDS']
        q['allies']=[dict(hp=number(at+who*10),max_hp=number(at+who*10+2),hp_pct=number(at+who*10+4),defense=number(at+who*10+6),healing=number(at+who*10+8)) for who in range(5)]
    for index,q in enumerate(queries):
        at=L['INCOMING_QUERY_BASE']+index*L['INCOMING_QUERY_WORDS']
        for who,ally in enumerate(q['allies']):ally.update(received_damage=number(at+who*4),received_hits=words[at+who*4+2],down=bool(words[at+who*4+3]))
    weapon_states=[]
    if metadata.get('combat') is not None:
        for who in range(5):
            at=L['WEAPON_STATE_BASE']+who*L['WEAPON_STATE_WORDS']
            weapon_states.append(dict(warm=number(at),last_fire=number(at+2),last_interval=number(at+4),
                                      post_reload_until=number(at+6),spread=number(at+8),probability=number(at+10),probability_evaluations=words[at+12],pending_auto_reload=bool(words[at+13]),charge_started_at=number(at+14)))
    trace=[]
    for i in range(words[2]):
        at=L['TRACE_BASE']+i*L['TRACE_WORDS'];row=words[at]
        if row>=len(metadata['effects']):raise RuntimeError('Invalid trace definition')
        trace.append(dict(effect=metadata['effects'][row],time=number(at+1),epoch=words[at+3],
                          generation=words[at+4],depth=words[at+5],next_due=number(at+6)))
    timers=[]
    for i,name in enumerate(metadata['effects']):
        at=L['STATE_BASE']+i*10
        timers.append(dict(effect=name,due=number(at),expiry=number(at+2),epoch=words[at+4],
                           order=words[at+5],active=bool(words[at+6]),stacks=words[at+7],activations=words[at+8],
                           target_slot=words[L['TIMER_TARGET_BASE']+2*i],target_generation=words[L['TIMER_TARGET_BASE']+2*i+1],
                           trigger_counts=list(words[L['COUNTER_STATE_BASE']+8*i:L['COUNTER_STATE_BASE']+8*i+8]),
                           every_due=number(L['PERIOD_STATE_BASE']+i*4),every_interval=number(L['PERIOD_STATE_BASE']+i*4+2)))
    if words[4]>64:raise RuntimeError('Invalid burst trace count')
    burst_trace=[]
    for i in range(words[4]):
        at=L['BURST_TRACE_BASE']+i*8
        burst_trace.append(dict(time=number(at),event=words[at+2],owner=words[at+3]-1))
    targets=[]
    if metadata.get('combat') is not None:
        for i,t in enumerate(metadata['combat']['targets']):
            at=L['TARGET_STATE_BASE']+i*10
            targets.append(dict(kind=t.get('kind',0),identity=t.get('identity',i),generation=words[at],active=bool(words[at+1]),hp=number(at+2),damage=number(at+4),hits=words[at+6]))
    at=L['HEALTH_STATE_BASE']
    health=[dict(hp=number(at+who*10),max_hp=number(at+who*10+2),hp_pct=number(at+who*10+4),defense=number(at+who*10+6),healing=number(at+who*10+8)) for who in range(5)]
    at=L['INCOMING_STATE_BASE']
    for who,ally in enumerate(health):ally.update(received_damage=number(at+who*4),received_hits=words[at+who*4+2],down=bool(words[at+who*4+3]))
    return dict(allies=health,weapons=weapon_states,status=words[0],queries=queries,trace=trace,timers=timers,targets=targets,burst_trace=burst_trace,trace_total=words[6],burst_trace_total=words[7],frames=words[8],max_stack_depth=words[3])


def run_programs(programs, *, backend='metal'):
    if not programs or len(programs)>L['BATCH']:raise ValueError('Portable batch capacity exceeded')
    words=[len(programs)]
    for program,metadata in programs:
        if len(program)!=L['INPUT_WORDS']:raise ValueError('Invalid program stride')
        words.extend(program)
    packed=struct.pack('<'+'I'*len(words),*words)
    raw,evidence=execute('gpu/event_runtime.slang','portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend)
    output=struct.unpack('<'+'I'*(len(programs)*L['OUTPUT_WORDS']),raw)
    results=[decode(output[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],metadata) for i,(_,metadata) in enumerate(programs)]
    if any(r['status'] for r in results):
        raise PortableExecutionError(results,evidence)
    return dict(results=results,**evidence,application_event_runtime_connected=True,autonomous_battle_connected=False,weapon_burst_target_connected=any(m.get('combat') is not None for _,m in programs),
                gpu_timeline_connected=any(m.get('timeline',False) for _,m in programs))


def evaluate(body):
    """Application worker entry; callers supply definitions and external events."""
    compiled=compile_program(body['chars'],[(item['effect'],item['owner']) for item in body['effects']],
                             body['script'],body['base_atk'],combat=body.get('combat'),**body.get('environment',{}))
    return run_programs([compiled],backend=body.get('backend','metal'))
