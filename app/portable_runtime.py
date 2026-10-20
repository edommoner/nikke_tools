"""Fail-closed application adapter for shared GPU effect/event execution.

This is an external-stimulus evaluator, not the autonomous weapon/burst loop.
No CPU simulation or CPU-produced state is supplied to the GPU.
"""
import math
import hashlib
import array
import sys
import re
import struct

from portable_backend import execute,execute_batches
from portable_enemy_specs import damage_plan,enemy_buff_plan
from portable_recipient_specs import admitted as recipient_admitted, pack as pack_recipients
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
    if isinstance(eff.get('target'),list):
        for target in eff['target']:
            if target!=[]:validate_effect(dict(eff,target=target),combat=combat)
    from portable_resource_specs import operation as resource_operation,validate as validate_resource
    resource_op=resource_operation(eff);validate_resource(eff)
    from portable_protection_specs import policy as protection_policy
    protection=protection_policy(eff)
    from periodic_source_specs import specification as source_specification
    source_spec=source_specification(eff)
    from portable_removal_specs import plan as removal_plan
    removal=removal_plan(eff,combat=combat)
    from portable_duration_extend_specs import plan as duration_extend_plan
    extension=duration_extend_plan(eff,combat=combat)
    from portable_stack_specs import plan as stack_plan,operation as stack_operation
    stack=stack_plan(eff,combat=combat)
    from portable_status_specs import cleanse_plan,immunity
    cleansing=cleanse_plan(eff,combat=combat)
    if eff.get('type')=='damage' and not isinstance(eff.get('stat',''),str):raise UnsupportedPortable('Damage family must be a string')
    from portable_element_specs import enabled as element_override,validate as validate_element
    validate_element(eff)
    allowed = {'name','source','type','stat','fixed_value','values','duration','duration_values',
               'target','trigger','note','polarity','favorite','_source_tag','_quant_group','max_ammo_reduction_exclusive','trigger_values','max_stack','max_trigger','tick_interval','tick_start','target_effect','target_skill'}
    if eff.get('type')=='damage' and eff.get('stat')=='dot_damage':allowed |= {'ramp_interval','ramp_damage_stack','post_ramp_tick_delay'}
    if element_override(eff):allowed |= {'target_code'}
    if removal is not None:allowed |= {'remove_scope'}
    if protection&255==1:allowed |= {'end_on_shield_consumed'}
    if source_spec:allowed |= {'periodic_source','feather_id','feather_slots','feather_interval_base','feather_interval_step_pct'}
    if resource_op:allowed |= {'gauge_id','gauge_max'}
    if eff.get('type')=='damage':
        allowed |= {'hit_count_gauge_ref'}
        if eff.get('scaling')=='stack_count' and eff.get('stat','').split(':')[0]!='dot_damage':allowed |= {'scaling','scaling_ref'}
        from portable_reference_specs import hit_reference
        hit_reference(eff)
    if eff.get('type')=='buff' and eff.get('scaling')=='stack_count' or eff.get('type')=='damage' and eff.get('stat')=='dot_damage' and eff.get('scaling')=='stack_count' and eff.get('scaling_ref'):
        allowed |= {'scaling','scaling_ref'}
        from portable_reference_specs import scale_reference
        try:scale_reference(eff)
        except ValueError as error:raise UnsupportedPortable(str(error)) from error
    if stack is not None and stack[0] in (20,21):allowed |= {'scaling','scaling_ref'}
    if resource_op in (2,3):allowed |= {'minimum_remaining'}
    if eff.get('type')=='buff':allowed=allowed | {'duration_bullets','event_scope'}
    effect_allowed=allowed | ({'scaling'} if eff.get('stat') in ('heal_hp_pct','cover_heal_pct','cover_hp_pct','shield_heal_pct','decoy_heal_pct') or eff.get('type')=='damage' and eff.get('stat')=='dot_damage' else set()) | ({'toggle','weapon_type','damage_coeff','max_ammo','duration_bullets','charge','charge_time','full_charge_mult','reload_time','fire_rate','fire_rate_max','warmup_bullets','pellets','muzzles','post_fire_delay','cover_during_delay','first_damage_coeff','max_ammo_buff_applies','burst_energy','core_dmg_mult'} if eff.get('type')=='weapon_change' else set())
    if set(eff)-effect_allowed:
        raise UnsupportedPortable('Unported effect fields: '+', '.join(sorted(set(eff)-effect_allowed)))
    from portable_trigger_specs import validate_input
    try:validate_input(eff)
    except ValueError as error:raise UnsupportedPortable(str(error)) from error
    kind,stat,target=eff.get('type'),eff.get('stat'),eff.get('target','self')
    if stat in ('pierce_enabled','armor_break_enabled'):
        # Presence ignores magnitude, but malformed authored quantities still fail closed.
        if 'fixed_value' in eff:double_words(eff['fixed_value'])
        quantities=eff.get('values',{})
        if not isinstance(quantities,dict):raise ValueError('Flag quantities must be a level mapping')
        for value in quantities.values():double_words(value)
    if protection and not recipient_admitted(target,instant=(protection&255) in (5,6)):raise UnsupportedPortable('Unported protection recipient selector')
    if kind=='damage' and 'scaling' in eff and (eff['scaling']!='stack_count' or stat.split(':')[0]=='dot_damage' and (stat!='dot_damage' or not eff.get('tick_interval'))):raise UnsupportedPortable('Periodic damage scaling requires an own-stack DoT clock')
    if stat=='cover_hp_pct' and eff.get('scaling') not in (None,'max_hp','stack_count'):raise UnsupportedPortable('Unported cover HP basis')
    if kind=='buff' and stack is None and 'duration_bullets' in eff:
        bullets=eff['duration_bullets']
        if type(bullets) is not int or bullets!=-1 and not 1<=bullets<=2**31-1:raise UnsupportedPortable('Invalid bullet lifetime')
        if bullets!=-1 and combat is None:raise UnsupportedPortable('Bullet lifetime requires combat-owned physical shots')
    if combat is None and isinstance(target,str) and ('burst_casted' in target or target=='all_allies_burst_not_casted'):
        raise UnsupportedPortable('Recipient selector requires combat-owned burst state')
    if combat is None and stat in ('ammo_charge_pct','ammo_charge_flat','fullburst_duration','burst_cooldown','burst_cooldown_reduce','burst_charge_pct','attack_speed_pct','mg_warmup_speed_pct','reload_speed_pct','reload_ratio_pct','accuracy_pct','max_ammo_pct','max_ammo_flat','charge_speed_pct','charge_speed_caster_based_pct','charge_time_flat','charge_time_fixed','charge_speed_buff_immune','charge_speed_debuff_immune','charge_speed_overflow_conversion_pct'):
        raise UnsupportedPortable('Weapon/burst modifier requires combat mechanics')
    if combat is None and set(eff.get('trigger',{}).get('condition',[])) & {'during_charge','burst_casted','burst_not_casted','has_burst1_ally','no_burst1_ally'}:
        raise UnsupportedPortable('Predicate requires combat-owned charge/burst state')
    if 'event_scope' in eff and eff['event_scope'] not in ('squad','recipients'):
        raise UnsupportedPortable('Invalid named event audience')
    if kind=='buff':
        if (stat not in BUFFS and stat not in (None,'','stack_change_immune') and not immunity(eff) and not protection and stack is None and resource_op not in (4,5) and not (isinstance(stat,str) and re.fullmatch(r'burst_stage_override:(?:[123A]|reenter[123])',stat))) or not (recipient_admitted(target) or enemy_buff_plan(eff) is not None or stack is not None):
            raise UnsupportedPortable('Unported buff or recipient selector')
        if enemy_buff_plan(eff) is not None:
            if combat is None:raise UnsupportedPortable('Enemy buff requires combat-owned targets')
            if eff.get('duration_bullets',-1)!=-1:raise UnsupportedPortable('Enemy buff finite bullet recipient clocks are not ported')
    elif kind=='damage':
        try:
            route,_,_=damage_plan(eff)
            if route>=2 and combat is None:raise ValueError('Enemy selection requires combat-owned targets')
        except ValueError as error:raise UnsupportedPortable(str(error)) from error
    elif kind=='instant':
        if protection or cleansing is not None or stack is not None or removal is not None or extension is not None or source_spec or resource_op in (1,2,3):pass
        elif stat in ('ammo_charge_pct','ammo_charge_flat','heal_hp_pct','cover_heal_pct','cover_revive','current_hp_reduce','burst_cooldown_reduce','burst_charge_pct'):
            if not recipient_admitted(target,instant=True):raise UnsupportedPortable('Unported health recipient selector')
            if eff.get('scaling') not in (None,'max_hp') or stat not in ('heal_hp_pct','cover_heal_pct','current_hp_reduce') and eff.get('scaling') is not None:raise UnsupportedPortable('Unported healing basis')
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


def compile_program(chars, effects, script, base_atk, *, defense=0, core_ratio=0, core_bonus=1, combat=None, allies=None, cover_sync=True, native_landing=False, enemy_code=None, geometry=None):
    import detail_gpu as legacy
    from portable_stack_specs import plan as stack_plan,operation as stack_operation,value as stack_value,pack_metadata as pack_stack_metadata
    check_schema()
    effects = list(effects)
    if not 1<=len(effects)<=L['DEFINITIONS']:raise UnsupportedPortable('Portable definition capacity exceeded')
    if any(e.get('stat')=='lifesteal_pct' for e,_ in effects) and (not native_landing or combat is None):raise UnsupportedPortable('Lifesteal requires native landing phases')
    for eff, owner in effects:validate_effect(eff,combat=combat)
    from portable_source_specs import validate_sources,pack as pack_source
    validate_sources(effects)
    from portable_staged_specs import descriptors as staged_descriptors,pack as pack_staged
    staged=staged_descriptors(effects)
    from portable_element_specs import enabled as element_override,STAT as ELEMENT_OVERRIDE_STAT,code_tag,legacy_effect
    from portable_geometry_specs import compiler_chars,required as geometry_required
    if geometry is None and geometry_required(effects):raise UnsupportedPortable('Core/range effects require literal geometry input')
    geometry_chars=compiler_chars(chars,geometry)
    from portable_target_state_specs import compiler_effect as target_compiler_effect
    program=legacy.compile_effects(geometry_chars,[(target_compiler_effect(dict(e,stat='') if e.get('type')=='buff' and e.get('stat') is None else legacy_effect(e)),owner) for e,owner in effects])
    from portable_target_state_specs import allocate_names as target_state_names
    target_state_names(effects,program['states'])
    source_query_indices={}
    for command in script:
        if len(command)==8 and command[1]==29:
            name=command[4]
            if not isinstance(name,str) or not name:raise ValueError('Invalid periodic source query name')
            program['states'].setdefault(name,len(program['states']))
    from portable_resource_specs import identities,pack as pack_resource,operation as resource_operation
    resource_keys=identities(effects,script,L['RESOURCE_KEYS']);resource_query_indices={}
    for name in resource_keys:program['states'].setdefault(name,len(program['states']))
    from portable_code_specs import code_names
    world_code,world_name_count=code_names(effects,enemy_code,program['states'],L['DEFINITIONS'])
    if len(program['states'])>L['DEFINITIONS']:raise UnsupportedPortable('Reference name capacity exceeded')
    nodes=program['effects'][len(effects):]
    if any(int(row[1])!=-1 or int(row[4])==17 for row in nodes) or len(nodes)>L['RECIPIENT_NODES']:raise UnsupportedPortable('Invalid ordered recipient nodes')
    program['effects']=program['effects'][:len(effects)]
    program['mode_weapons']=program['mode_weapons'][:len(effects)]
    if len(program['effects'])!=len(effects) or not 1<=len(effects)<=L['DEFINITIONS']:
        raise UnsupportedPortable('Portable definition capacity or expansion exceeded')
    from portable_periodic_specs import periodic_groups, periodic_flags
    periodic=periodic_groups(effects)
    if periodic and combat is None:raise UnsupportedPortable('Named periodic target union requires combat-owned targets')
    seen_names={}
    for index,(eff,owner) in enumerate(effects):
        key=(owner,eff.get('name'));previous=seen_names.get(key,[])
        resource_instant=resource_operation(eff) in (1,2,3) and all(resource_operation(effects[j][0]) in (1,2,3) for j in previous)
        source_instant=eff.get('stat') in ('periodic_source_refresh','feather_refresh') and all(effects[j][0].get('stat') in ('periodic_source_refresh','feather_refresh') for j in previous)
        stack_coexist=bool(stack_operation(eff) or any(stack_operation(effects[j][0]) for j in previous)) and all(effects[j][0].get('type')=='buff' or stack_operation(effects[j][0]) for j in previous) and (eff.get('type')=='buff' or bool(stack_operation(eff)))
        if previous and not stack_coexist and not periodic.get(index) and not resource_instant and not source_instant and (eff.get('type')!='buff' or any(effects[j][0].get('type')!='buff' for j in previous)):
            raise UnsupportedPortable('Multiple named non-buff carriers are not ported')
        seen_names.setdefault(key,[]).append(index)
    duration_groups={key:i+1 for i,key in enumerate(dict.fromkeys((owner,e.get('source'),e.get('name')) for e,owner in effects if e.get('stat')=='fullburst_duration'))}
    def stat_identity(effect):return (effect.get('type'),effect.get('stat') if effect.get('type')=='buff' else effect.get('stat',''))
    stat_keys={key:i for i,key in enumerate(dict.fromkeys(stat_identity(e) for e,_ in effects))}
    if not 1<=len(script)<=L['COMMANDS'] or len(base_atk)!=5:
        raise ValueError('Invalid portable command/base-stat dimensions')
    words=[0]*L['INPUT_WORDS'];words[0:3]=[ABI,len(effects),len(script)];words[5]=1
    words[L['WORLD_META_BASE']:L['WORLD_META_BASE']+3]=[world_code,world_name_count,sum(element_override(e) for e,_ in effects)]
    if type(cover_sync) is not bool:raise ValueError('Cover synchronization policy must be boolean')
    words[7]=int(cover_sync)
    if type(native_landing) is not bool or native_landing and combat is None:raise ValueError('Native landing phases require combat and a boolean policy')
    words[L['LANDING_META_BASE']]=int(native_landing)
    words[L['RESOURCE_META_BASE']]=len(resource_keys)
    for name,key in resource_keys.items():words[L['RESOURCE_NAME_BASE']+key]=program['states'][name]
    for i,attack in enumerate(base_atk):
        if attack<0:raise ValueError('Negative base attack')
        words[8+2*i:10+2*i]=double_words(attack)
    for at,value in [(18,defense),(20,core_ratio),(22,core_bonus)]:
        if value<0:raise ValueError('Negative enemy/geometry input')
        words[at:at+2]=double_words(value)
    allies=allies if allies is not None else [{} for _ in range(5)]
    if not isinstance(allies,list) or len(allies)!=5:raise ValueError('Expected five initial ally states')
    for who,ally in enumerate(allies):
        if not isinstance(ally,dict) or set(ally)-{'base_hp','hp','base_defense','base_cover_hp','cover_hp'}:raise ValueError('Unsupported initial ally state')
        base=ally.get('base_hp',1000000);current=ally.get('hp',base);defense_value=ally.get('base_defense',0)
        for value in (base,current,defense_value):double_words(value)
        if not 0<base<=1e30 or not 0<=current<=base or not 0<=defense_value<=1e30:raise ValueError('Invalid initial ally health/defense')
        at=L['HEALTH_BASE']+who*L['HEALTH_WORDS']
        words[at:at+6]=[*double_words(base),*double_words(current),*double_words(defense_value)]
        cover_base=ally.get('base_cover_hp',2000000);cover_current=ally.get('cover_hp',cover_base)
        for value in (cover_base,cover_current):double_words(value)
        if not 0<cover_base<=1e30 or not 0<=cover_current<=cover_base:raise ValueError('Invalid initial cover HP')
        at=L['COVER_BASE']+who*4;words[at:at+4]=[*double_words(cover_base),*double_words(cover_current)]
    words[24:26]=double_words(.15);words[26:28]=double_words(.5)
    from portable_recipient_specs import pack as pack_node
    for index,node in enumerate(nodes):
        scratch=[0]*8;pack_node(scratch,0,node,dict(L,RECIPIENT_BASE=0),{'type':'buff','target':'self'},0,False,0)
        at=L['RECIPIENT_NODE_BASE']+index*8;words[at:at+8]=scratch
    words[L['RECIPIENT_META_BASE']]=len(nodes)
    def target_key(target):return tuple(target_key(x) for x in target) if isinstance(target,list) else target
    recipient_limits=dict(L,_AUTHORED_DEFINITIONS=len(effects))
    lazy_groups={}
    for (eff,owner),row in zip(effects,program['effects']):
        if eff.get('type')=='buff' and not stack_operation(eff) and int(row[4]) in (5,6,7,15,16):
            lazy_groups.setdefault((owner,target_key(eff.get('target'))),len(lazy_groups)+1)
    merge_groups={}
    def merge_key(index,row):
        eff,owner=effects[index]
        if not row[205] or not eff.get('name') or eff.get('_source_tag')=='equipment' and int(row[2]) in (18,20,37):return None
        return owner,eff['name'],stat_identity(eff)[1],int(row[9])
    for index,row in enumerate(program['effects']):
        key=merge_key(index,row)
        if key is not None:merge_groups[key]=merge_groups.get(key,0)+1
    from portable_removal_specs import plan as removal_plan
    from portable_status_specs import cleanse_plan,immunity
    from portable_duration_extend_specs import plan as duration_extend_plan,members as duration_extend_members
    for index,row in enumerate(program['effects']):
        stack=stack_plan(effects[index][0],combat=combat)
        extension=duration_extend_plan(effects[index][0],combat=combat)
        removal=removal_plan(effects[index][0],combat=combat)
        cleansing=cleanse_plan(effects[index][0],combat=combat)
        if cleansing is not None:
            if cleansing[0]==1:pack_recipients(words,index,row,recipient_limits,effects[index][0],stat_keys[stat_identity(effects[index][0])],False,0)
            else:
                packet=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS'];words[packet:packet+8]=[*cleansing[1],0,0,0,0,0,0]
            words[L['RECIPIENT_BASE']+index*8+7]=0
        if stack is not None:
            if stack[1]==1 or enemy_buff_plan(effects[index][0]) is not None:pack_recipients(words,index,row,recipient_limits,effects[index][0],stat_keys[stat_identity(effects[index][0])],False,0)
            else:
                packet=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS'];words[packet:packet+8]=[*stack[2],0,0,0,0,0,0]
        if stack is not None:words[L['RECIPIENT_BASE']+index*8+7]=0
        if extension is not None and extension[0]==1:pack_recipients(words,index,row,recipient_limits,effects[index][0],stat_keys[stat_identity(effects[index][0])],False,0)
        if extension is not None and extension[0]==2:
            if extension[1][0] in (7,8) and any(t.get('defense',0)!=0 for t in combat['targets'][1:]):raise UnsupportedPortable('Enemy defense ranking requires zero add defenses in the current boss model')
            packet=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS'];words[packet:packet+8]=[*extension[1],0,0,0,0,0,0]
        if removal is not None and removal[0]==1:pack_recipients(words,index,row,recipient_limits,effects[index][0],stat_keys[stat_identity(effects[index][0])],False,0)
        if removal is not None and removal[0]==2:
            packet=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS'];words[packet:packet+8]=[*removal[1],0,0,0,0,0,0]
        if row[1] in (0,4,5,6,7,8,12,13,14,24,27,30,31):pack_recipients(words,index,row,recipient_limits,effects[index][0],stat_keys[stat_identity(effects[index][0])],merge_groups.get(merge_key(index,row),0)>1,lazy_groups.get((effects[index][1],target_key(effects[index][0].get('target'))),0) if effects[index][0].get('type')=='buff' else 0)
        if effects[index][0].get('type')=='damage':
            route,count,hits=damage_plan(effects[index][0])
            from portable_reference_specs import hit_reference
            if not hit_reference(effects[index][0])[0] and int(row[61])!=hits:raise UnsupportedPortable('Unported compiled hit count')
            from calculator.timeline import BURST_GAUGE_EXCEPTIONS
            override=BURST_GAUGE_EXCEPTIONS.get(effects[index][1],{}).get(effects[index][0].get('name'),{}).get('burst_energy',-1)
            at=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS']
            eff,owner=effects[index];caster=next(c for c in chars if c['name']==owner)
            pending=eff.get('stat')=='bonus_damage' and 'burst_cast' in eff.get('trigger',{}).get('timing',[]) and str(caster['_weapon'].get('burst_stage',''))=='3'
            if pending and combat is None:raise UnsupportedPortable('Pending B3 bonus damage requires the combat controller')
            from named_target_specs import resolve_named_attack
            named=None if staged[index] is not None else resolve_named_attack(eff,owner,effects)
            pending_hits=named.deferred_bonus_hits if pending and named is not None else 1
            if pending_hits>256:raise UnsupportedPortable('Pending named attack count exceeds 256')
            words[at:at+8]=[route,count,hits,int(eff['stat'].split(':')[0]=='auto_damage'),*double_words(override),int(pending),pending_hits if pending else 0]
            if pending:
                later_names={e.get('name') for e,n in effects[index+1:] if n==owner and e.get('type')=='buff' and 'burst_cast' in e.get('trigger',{}).get('timing',[]) and e.get('name')}
                mask=L['PENDING_EXCLUDE_BASE']+index*L['MASK_WORDS']
                for other,(e,n) in enumerate(effects):
                    if n==owner and e.get('name') in later_names:words[mask+other//32] |= 1<<(other%32)
        if int(row[1]) in (7,30) and (row[6]<0 or int(row[1])==30 and row[6]==0):raise UnsupportedPortable('Cover heal/revival requires nonnegative healing or positive revival')
        duration=L['DURATION_DEFINITION_BASE']+index*2
        eff,owner=effects[index]
        if eff.get('stat')=='fullburst_duration':words[duration:duration+2]=[duration_groups[(owner,eff.get('source'),eff.get('name'))],int('burst_cast' in eff.get('trigger',{}).get('timing',[]))]
        bullet=L['BULLET_DEFINITION_BASE']+index*2
        lifetime=int(row[62]) if effects[index][0].get('type')=='buff' and stack is None else -1
        words[bullet:bullet+2]=[lifetime if lifetime>0 else 0,int(row[63]) if lifetime>0 else 0]
        periodic_at=L['PERIODIC_DEFINITION_BASE']+index*2
        words[periodic_at:periodic_at+2]=[periodic_flags(effects[index][0],periodic.get(index,0)),periodic.get(index,0)]
        compact=[0]*L['DEFINITION_WORDS']
        fields={'OWNER':int(row[0]),'KIND':4 if row[1]==12 else int(row[1]),'STAT':int(row[2]),'NAME':int(row[3]),
                'MAX_STACK':int(row[9]),'BUDGET':int(row[57]),'IMMEDIATE':int(row[60]),
                'PRESERVE':int(effects[index][0].get('stat')=='dot_damage'),
                'EVENT':int(row[145]),'THRESHOLD':int(row[146]),'COUNT_MODE':int(row[147]),
                'EVENT_NAME':int(row[148]),'TARGET_NAME':int(row[36]),
                'FORCE_MASK':int(row[legacy.B3_MASK]),'RECIPIENTS':31 if row[4]==1 else 1<<int(row[0]),
                'TARGET':cleansing[0] if cleansing is not None else stack[1] if stack is not None else extension[0] if extension is not None else removal[0] if removal is not None else int(bool(effects[index][0].get('name'))) if row[1] in (2,13) else int(effects[index][0].get('target')=='boss'), 'STAGE_ARG':int(row[151]),
                'STAGE_OVERRIDE':int(row[252]),'REENTRY':int(row[253]),'TOGGLE':int(bool(int(row[213]) & 128)), 'DAMAGE_FLAGS':int(row[39])}
        if element_override(eff):fields.update(KIND=0,STAT=ELEMENT_OVERRIDE_STAT)
        for key,value in fields.items():compact[F[key]]=value & 0xffffffff
        for key,offset in [('VALUE',6),('DURATION',7),('INTERVAL',59)]:compact[F[key]:F[key]+2]=double_words(row[offset])
        if element_override(eff):
            compact[F['VALUE']:F['VALUE']+2]=[0,0]
            packet=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS']
            words[packet:packet+8]=[code_tag(eff,program['states']),0,0,0,0,0,0,0]
        if stack is not None:
            if stack[0] in (18,20,21) and not effects[index][0].get('target_effect'):compact[F['TARGET_NAME']]=0xffffffff
            compact[F['VALUE']:F['VALUE']+2]=double_words(stack_value(effects[index][0],chars[int(row[0])]))
            if stack[0]==19:compact[F['INTERVAL']:F['INTERVAL']+2]=[0,0]
        at=L['DEFINITION_BASE']+index*L['DEFINITION_WORDS'];words[at:at+len(compact)]=compact
        from portable_protection_specs import pack as pack_protection
        pack_protection(words,index,eff,L)
        from portable_trigger_specs import pack_descriptors
        pack_descriptors(words,index,row,L,F,double_words,effect=effects[index][0],states=program['states'])
        if effects[index][0].get('stat')=='stack_change_immune':words[at+F['FLAGS']] |= 8
        policy=immunity(eff)
        if policy:
            words[L['STATUS_META_BASE']] |= 1 | (2 if policy==3 else 0)
            words[at+F['FLAGS']] |= policy<<4
            if policy==3 and ('fixed_value' in eff or 'values' in eff):words[at+F['FLAGS']] |= 64
            words[at+F['TARGET_NAME']]=int(row[263]) if policy==2 else 0xffffffff
        if cleansing is not None:words[L['STATUS_META_BASE']] |= 4
        # Quantity component identity is the source/group tuple, not its display name.
        # The pinned legacy equipment alias collapses components before rounding.
        extra=L['DEFINITION_EXTRA_BASE']+index*L['DEFINITION_EXTRA_WORDS']
        words[extra:extra+8]=[int(row[45]),int(row[55]),0xffffffff,int(row[213]),
                              *double_words(row[138]),int(row[139]),int(row[209])]
        force=L['FORCE_BASE']+index*L['MASK_WORDS']
        words[force:force+L['MASK_WORDS']]=[int(row[legacy.B3_MASK+k]) for k in range(L['MASK_WORDS'])]
        if extension is not None:
            words[force:force+L['MASK_WORDS']]=[0]*L['MASK_WORDS']
            for matched in duration_extend_members(effects[index][0],effects):words[force+matched//32]|=1<<(matched%32)
        health=L['HEALTH_DEFINITION_BASE']+index*L['HEALTH_DEFINITION_WORDS']
        words[health:health+4]=[int(row[50]),int(effects[index][0].get('stat')=='def_pct') | (int(effects[index][0].get('stat')=='received_dmg_pct')<<1),
                              (int(bool(eff.get('name'))) | (int(eff.get('event_scope')=='recipients')<<1) | ((int(row[204])+1)<<2)) if eff.get('type')=='buff' and stack is None else 0,int(enemy_buff_plan(eff) is not None)]
        if enemy_buff_plan(eff) is not None:
            route,count=enemy_buff_plan(eff);packet=L['DAMAGE_DEFINITION_BASE']+index*L['DAMAGE_DEFINITION_WORDS']
            words[packet:packet+8]=[route,count,0,0,0,0,0,0]
        pack_resource(words,index,row,L,effects[index][0],resource_keys,program['states'],double_words)
        from portable_reference_specs import pack as pack_reference
        pack_reference(words,index,L,effects[index][0],resource_keys,program['states'],F)
        pack_source(words,index,row,L,effects[index][0],double_words)
        spec=staged[index]
        parent=next((i for i,(e,n) in enumerate(effects) if n==owner and spec is not None and e.get('name')==spec.reference),-1)
        pack_staged(words,index,spec,L,resource_keys,double_words,parent)
        if row[1]==2:
            if row[7]<0 and row[14]>0:raise UnsupportedPortable('Infinite conditional weapon mode is not ported')
            from portable_combat import pack_mode
            pack_mode(words,index,row,double_words)
    from portable_geometry_specs import pack as pack_geometry
    pack_geometry(words,geometry,effects,program['effects'],chars,L,double_words)
    pack_stack_metadata(words,L,effects,double_words)
    from portable_staged_specs import pack_index
    pack_index(words,staged,L)
    combat_meta = None
    if combat is not None:
        from portable_combat import pack_combat
        combat_meta=pack_combat(words,combat,double_words)
        for eff,owner in effects:
            enemy_plan=enemy_buff_plan(eff)
            if (eff.get('type')=='damage' and damage_plan(eff)[0] in (7,8) or enemy_plan is not None and enemy_plan[0] in (7,8)) and any(t.get('defense',0)!=0 for t in combat['targets'][1:]):raise UnsupportedPortable('Enemy defense ranking requires zero add defenses in the current boss model')
            if eff.get('stat')=='accuracy_pct':
                # Static filters may select any ally. Require geometry for all
                # candidates rather than silently compiling an unmodelled hit rate.
                recipients=range(5) if eff.get('target','self')!='self' else [next(i for i,c in enumerate(chars) if c['name']==owner)]
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
        if op==28:
            if any(type(v) is not int for v in (op,event,owner,query,extra,extra2)) or event or not 0<=owner<5 or not 0<=query<L['COMMANDS'] or extra or extra2:raise ValueError('Invalid resource query')
            key=resource_keys[arg];resource_query_indices[query]=True
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[28,*double_words(t),0,owner,key,query,0]
            continue
        if op==26:
            if any(type(v) is not int for v in (op,event,owner,arg,query,extra2)) or event or owner or query!=-1 or extra2 or not 1<=arg<=31:raise ValueError('Invalid cover-layer damage descriptor')
            double_words(extra)
            if not 0<=extra<=1e30:raise ValueError('Invalid cover-layer damage')
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*double_words(t),0,0,arg,*double_words(extra)]
            continue
        if op==31:
            if any(type(v) is not int for v in (op,event,owner,arg,query)) or event not in (0,1) or not 0<=owner<=31 or query!=-1 or not 1<=arg<=31:raise ValueError('Invalid layered incoming descriptor')
            double_words(extra);double_words(extra2)
            if not 0<=extra<=1e30 or not 0<=extra2<=1e6:raise ValueError('Invalid incoming attack/coefficient')
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*double_words(t),event,owner,arg,0,0]
            at=L['INCOMING_BASE']+i*L['INCOMING_WORDS'];words[at:at+4]=[*double_words(extra),*double_words(extra2)]
            continue
        if op==25:
            if any(type(v) is not int for v in (op,event,owner,arg,query)) or event or owner or query!=-1 or not 1<=arg<=31:
                raise ValueError('Invalid incoming body-attack descriptor')
            double_words(extra);double_words(extra2)
            if not 0<=extra<=1e30 or not 0<=extra2<=1e6:raise ValueError('Invalid incoming attack/coefficient')
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*double_words(t),0,0,arg,0,0]
            at=L['INCOMING_BASE']+i*L['INCOMING_WORDS'];words[at:at+4]=[*double_words(extra),*double_words(extra2)]
            continue
        if op==29:
            if any(type(v) is not int for v in (op,event,owner,query,extra,extra2)) or event or not 0<=owner<5 or not 0<=query<L['COMMANDS'] or query in source_query_indices or extra or extra2:
                raise ValueError('Invalid periodic source query')
            source_query_indices[query]=dict(time=t,owner=owner,name=arg)
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*double_words(t),0,owner,program['states'][arg],query,0]
            continue
        if op in (4,20,21,22,24,27):
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
            if op==27 and arg not in (0,1):raise ValueError('Invalid automatic add aim policy')
            if op==21:
                double_words(extra)
                if not 1<=extra<=1e30:raise ValueError('Invalid spawn HP')
            elif extra!=0:raise ValueError('Unexpected combat payload')
            at=L['COMMAND_BASE']+i*8
            words[at:at+8]=[op,*double_words(t),event,owner,arg,*(double_words(extra) if op==21 else [query & 0xffffffff,0])]
            continue
        if op==30:
            if not native_landing or any(type(v) is not int for v in (op,event,owner,arg,query,extra,extra2)) or event or owner or arg or query!=-1 or extra or extra2:raise ValueError('Invalid landing flush command')
            at=L['COMMAND_BASE']+i*8;words[at:at+8]=[op,*double_words(t),0,0,0,0,0]
            continue
        if op not in (0,2,18) or any(type(v) is not int for v in (op,event,owner,arg,query,extra2)):
            raise UnsupportedPortable('Only external notify, normal impact and query commands are connected')
        if op!=18 and (type(extra) is not int or extra):raise UnsupportedPortable('Unexpected stimulus payload')
        if op==18:
            double_words(extra)
            if event or not 0<extra<=1e6:raise UnsupportedPortable('Invalid normal-impact coefficient')
        if not 0<=owner<5 or extra2 or (op==0 and (event not in (0,1,2,3,4,7,8,10,11,12,14,17,18,19,20,21,26,29,36,43,49) or event==49 and not 0<=arg<len(program['states']))):
            raise UnsupportedPortable('Unsupported stimulus event, owner, or payload')
        if op==2 and (arg < -1 or arg >= (len(combat['targets']) if combat else 1)):raise ValueError('Invalid enemy modifier query target')
        if op==2 and (event!=0 or query<0 or query>=L['COMMANDS']):raise ValueError('Invalid query index')
        if combat is not None and op==0 and event in (0,1,2,3,4):raise UnsupportedPortable('Combat emits its own startup and burst notifications')
        at=L['COMMAND_BASE']+i*8
        words[at:at+8]=[op,*double_words(t),event,owner,*(double_words(extra) if op==18 else [arg & 0xffffffff,query & 0xffffffff]),0]
    if words[6] and frame_mode!=24:raise UnsupportedPortable('Accumulated clock requires GPU-generated frames')
    from portable_trigger_specs import pack_event_candidates
    pack_event_candidates(words,L)
    from portable_probability_specs import definitions as probability_definitions
    return words,dict(probability_definitions=probability_definitions(effects),ordered_recipients=bool(nodes),protection_enabled=bool(words[L['PROTECTION_META_BASE']] or any(c[1]==31 for c in script)),status_policy=words[L['STATUS_META_BASE']],status_names=program['states'],stack_operators=any(stack_operation(e) for e,_ in effects),enemy_buff_definitions=[enemy_buff_plan(e) is not None for e,_ in effects],native_landing=native_landing,source_definitions=[dict(name=next((k for k,v in program['states'].items() if v==int(row[304])),None),owner=int(row[0]),legacy=bool(row[137])) if int(row[1])==35 else None for row in program['effects']],source_query_indices=source_query_indices,resource_names=list(resource_keys),resource_query_indices=sorted(resource_query_indices),states=program['states'],names=[c['name'] for c in chars],effects=[e['name'] for e,n in effects],bullet_lifetimes=[max(0,e.get('duration_bullets',0)) if e.get('type')=='buff' else 0 for e,n in effects],combat=combat_meta,timeline=frame_mode==24)


def decode(words,metadata):
    def number(at):return struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
    if words[1]>L['COMMANDS'] or words[2]>L['TRACE']:
        raise RuntimeError('Invalid portable output dimensions')
    def lifetime(at):
        value=number(at)
        return math.copysign(1e30,value) if math.isinf(value) else value
    queries=[]
    for i in range(words[1]):
        at=L['QUERY_BASE']+i*L['QUERY_WORDS']
        accounting=L['DAMAGE_ACCOUNTING_QUERY_BASE']+i*40
        pending=L['PENDING_QUERY_BASE']+i*4
        queries.append(dict(enemy_modifiers=dict(defense_pct=number(at+26),defense_flat=number(at+28),received_damage_pct=number(at+30)),pending_burst=dict(count=words[pending],enqueued=words[pending+1],fired=words[pending+2]),body_damage=[number(accounting+20+2*k) for k in range(5)],add_damage=[number(accounting+30+2*k) for k in range(5)],scored_damage=[number(accounting+2*k) for k in range(5)],add_overkill=[number(accounting+10+2*k) for k in range(5)],time=number(at),damage=[number(at+2+2*k) for k in range(5)],
                            active_timer_mask=words[at+12],active_timer_mask_words=list(words[L['TIMER_MASK_BASE']+i*L['MASK_WORDS']:L['TIMER_MASK_BASE']+(i+1)*L['MASK_WORDS']]),generation=words[at+13],
                            stack_depth=words[at+14],timer_clock=words[at+15],
                            attack_buffs=[number(at+16+2*k) for k in range(5)]))
    if metadata.get('combat') is not None:
        for i,q in enumerate(queries):
            at=L['COMBAT_QUERY_BASE']+i*L['COMBAT_QUERY_WORDS']
            q['combat']=dict(weapons=[dict(ammo=struct.unpack('<i',struct.pack('<I',words[at+6*k]))[0],shots=words[at+6*k+1],next=number(at+6*k+2),reload_until=number(at+6*k+4)) for k in range(5)],
                             phase=words[at+30],cast_mask=words[at+31],gauge=number(at+32),action=number(at+34),full_end=number(at+36),target=words[at+38],clock='accumulated' if words[at+39] else 'grid')
            states=L['COMBAT_STATE_QUERY_BASE']+i*L['COMBAT_STATE_QUERY_WORDS']
            q['combat']['targets']=[dict(generation=words[states+8*j],active=bool(words[states+8*j+1]),hp=number(states+8*j+2),damage=number(states+8*j+4),hits=words[states+8*j+6]) for j in range(len(metadata['combat']['targets']))]
            for who,w in enumerate(q['combat']['weapons']):
                at=states+64+who*8
                w.update(ready=number(at),charge_until=number(at+2),charging=bool(words[at+4]),aim=words[at+5],mode_index=words[at+6]-1,mode_shots=words[at+7])
            q['combat'].update(last_b3_caster=words[states+111]-1,last_b3_cast_time=number(states+124),last_full_start=number(states+126),cooldown_applied=[number(states+112+2*k) for k in range(5)],cooldown_wait_mask=words[states+122],gauge_charging=bool(words[states+123]),reentry_slot=bool(words[states+104]),reentry_done=words[states+105],casts=list(words[states+106:states+111]))
    for index,q in enumerate(queries):
        at=L['HEALTH_QUERY_BASE']+index*L['HEALTH_QUERY_WORDS']
        q['allies']=[dict(hp=number(at+who*10),max_hp=number(at+who*10+2),hp_pct=number(at+who*10+4),defense=number(at+who*10+6),healing=number(at+who*10+8)) for who in range(5)]
    for index,q in enumerate(queries):
        at=L['COVER_QUERY_BASE']+index*40
        q['covers']=[dict(hp=number(at+who*8),max_hp=number(at+who*8+2),effective_max_hp=number(at+who*8+4),damage=number(at+who*8+6)) for who in range(5)]
    for index,q in enumerate(queries):
        at=L['INCOMING_QUERY_BASE']+index*L['INCOMING_QUERY_WORDS']
        for who,ally in enumerate(q['allies']):ally.update(received_damage=number(at+who*4),received_hits=words[at+who*4+2],down=bool(words[at+who*4+3]))
    def protection_summary(at):
        return [dict(shield=number(at+w*10),shield_capacity=number(at+w*10+2),decoy=number(at+w*10+4),decoy_capacity=number(at+w*10+6),has_shield=bool(words[at+w*10+8]),has_decoy=bool(words[at+w*10+9])) for w in range(5)]
    if metadata.get('protection_enabled'):
        for i,q in enumerate(queries):q['protection']=protection_summary(L['PROTECTION_QUERY_BASE']+i*50)
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
        packet=L['DAMAGE_TRACE_BASE']+i*10
        pending=L['PENDING_TRACE_BASE']+i*4
        trace.append(dict(pending_burst=bool(words[pending]),cast_time=number(pending+1) if words[pending] else None,weighted_amount=number(packet+8),target_order=[((words[packet+6]>>(4*k))&15)-1 for k in range(words[packet+7])],target_mask=words[packet],basis=words[packet+1],hit_index=words[packet+2],hit_count=words[packet+3],delivered_amount=number(packet+4),effect=metadata['effects'][row],time=number(at+1),epoch=words[at+3],
                          generation=words[at+4],depth=words[at+5],next_due=number(at+6)))
    timers=[]
    for i,name in enumerate(metadata['effects']):
        at=L['STATE_BASE']+i*10
        timers.append(dict(effect=name,due=number(at),expiry=lifetime(at+2),epoch=words[at+4],
                           order=words[at+5],active=bool(words[at+6]),stacks=words[at+7],activations=words[at+8],
                           target_slot=words[L['TIMER_TARGET_BASE']+2*i],target_generation=words[L['TIMER_TARGET_BASE']+2*i+1],
                           trigger_counts=list(words[L['COUNTER_STATE_BASE']+8*i:L['COUNTER_STATE_BASE']+8*i+8]),
                           every_due=number(L['PERIOD_STATE_BASE']+i*4),every_interval=number(L['PERIOD_STATE_BASE']+i*4+2)))
    if words[4]>L['BURST_TRACE']:raise RuntimeError('Invalid burst trace count')
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
    if words[9]>L['CARRIERS']:raise RuntimeError('Invalid resident carrier count')
    carriers=[]
    for i in range(words[9]):
        at=L['CARRIER_STATE_BASE']+i*L['CARRIER_WORDS'];definition=words[at+1]
        if definition>=len(metadata['effects']) or words[at]>=L['CARRIERS']:raise RuntimeError('Invalid resident identity')
        carriers.append(dict(slot=words[at],definition=definition,effect=metadata['effects'][definition],recipients=words[at+2],
                             stacks=words[at+3],active=bool(words[at+4]&1),lazy_pending=bool(words[at+4]&2),end=lifetime(at+5),activated=number(at+7),order=words[at+9],hp_snapshot=number(at+10)))
        if metadata.get('ordered_recipients'):
            pos=L['RECIPIENT_ORDER_BASE']+words[at]*2;encoded=words[pos]|(words[pos+1]<<32)
            carriers[-1]['recipient_order']=[((encoded>>(i*3))&7)-1 for i in range(21) if (encoded>>(i*3))&7 and words[at+2]&(1<<(((encoded>>(i*3))&7)-1))]
        if metadata.get('enemy_buff_definitions',[False]*len(metadata['effects']))[definition]:
            carriers[-1]['enemy_generation']=words[at+12] or None
            if metadata.get('stack_operators') or metadata.get('status_policy',0):
                generations=list(words[at+13:at+18])+list(words[at+18:at+21]) if words[at+4]&4 else [words[at+12]]*8
                carriers[-1]['enemy_generations']={str(i):g for i,g in enumerate(generations) if (g!=0 if words[at+4]&4 else words[at+2]&(1<<(i+5)))}
        if metadata.get('bullet_lifetimes',[0]*len(metadata['effects']))[definition]:
            left=words[at+12];carriers[-1].update(bullet_left=left-2**32 if left>=2**31 else left,recipient_bullets=list(words[at+13:at+18]),recipient_stack_overrides=list(words[at+18:at+23]))
    if metadata.get('protection_enabled'):
        for carrier in carriers:
            carrier['protection']={}
            if not carrier['active']:continue
            object=words[L['PROTECTION_MAP_BASE']+carrier['slot']]
            if not object:continue
            if object>L['PROTECTION_OBJECTS']:raise RuntimeError('Invalid protection object')
            base=L['PROTECTION_OBJECT_BASE']+(object-1)*L['PROTECTION_OBJECT_WORDS']
            if words[base+20]!=carrier['order']:continue
            kind=words[base+22]&255
            carrier['protection']=dict(kind=kind,current={str(w):number(base+w*4) for w in range(5) if words[base+23]&(1<<w)},capacity={str(w):number(base+w*4+2) for w in range(5) if words[base+23]&(1<<w)})
    at=L['COVER_STATE_BASE']
    covers=[dict(hp=number(at+who*8),max_hp=number(at+who*8+2),effective_max_hp=number(at+who*8+4),damage=number(at+who*8+6)) for who in range(5)]
    pending=L['PENDING_STATE_BASE'];count=words[pending]
    if count>L['PENDING']:raise RuntimeError('Invalid pending queue dimensions')
    queue=[]
    for index in range(count):
        at=pending+4+index*8;definition=words[at]
        if definition>=len(metadata['effects']):raise RuntimeError('Invalid pending definition')
        queue.append(dict(effect=metadata['effects'][definition],cast_time=number(at+1),coefficient=number(at+3),hits=words[at+5],amount=number(at+6)))
    periodic=[]
    for i in range(len(metadata['effects'])):
        at=L['PERIODIC_STATE_BASE']+i*12
        periodic.append(dict(flags=words[at],group=words[at+1],target_order=[((words[at+2]>>(4*k))&15)-1 for k in range(8) if (words[at+2]>>(4*k))&15],target_generations=list(words[at+4:at+12])))
    captures=[];active_slots={c['slot'] for c in carriers if c['active']}
    for slot in range(L['CARRIERS']):
        capture=L['REFERENCE_CAPTURE_BASE']+slot*3;flags=words[capture]
        if not flags:continue
        value=number(capture+1);captures.append(dict(slot=slot,present=bool(flags&1),dot=bool(flags&2),value=value,active=slot in active_slots))
        if flags&2 and slot in active_slots:
            if slot<len(timers):timers[slot]['stacks']=int(value)
            for carrier in carriers:
                if carrier['slot']==slot:carrier['stacks']=int(value)
    from portable_resource_decode import resource_readback
    resource_state=resource_readback(words,metadata,L,number)
    source_count=words[L['SOURCE_HEADER_BASE']]
    if source_count>L['SOURCES']:raise RuntimeError('Invalid periodic source output count')
    sources=[]
    for index in range(source_count):
        at=L['SOURCE_STATE_BASE']+index*L['SOURCE_STATE_WORDS'];row=words[at]-1
        if not 0<=row<len(metadata['source_definitions']) or metadata['source_definitions'][row] is None:raise RuntimeError('Invalid periodic source descriptor readback')
        sources.append(dict(**metadata['source_definitions'][row],definition=row,epoch=words[at+1],scheduled=bool(words[at+2]),count=words[at+3],refreshed=number(at+4),next_at=number(at+6) if words[at+2] else None))
    source_queries=[]
    for index,query in sorted(metadata['source_query_indices'].items(),key=lambda p:int(p[0])):
        at=L['SOURCE_QUERY_BASE']+int(index)*8
        source_queries.append(dict(**query,present=bool(words[at]),count=words[at+1],epoch=words[at+2],scheduled=bool(words[at+3]),next_at=number(at+4) if words[at+3] else None))
    staged_rows=[]
    for row in range(len(metadata['effects'])):
        at=L['STAGED_STATE_BASE']+row*6
        if words[at]:staged_rows.append(dict(definition=row,active=row in active_slots,generation=words[at],sequence=words[at+1],total=words[at+2],index=words[at+3],start=number(at+4)))
    landing=L['LANDING_HEADER_BASE'];pending_landings=[]
    if not 0<=words[landing+1]<=words[landing]<=L['LANDINGS']:raise RuntimeError('Invalid landing queue dimensions')
    for i in range(words[landing+1],words[landing]):
        at=L['LANDING_STATE_BASE']+i*L['LANDING_WORDS']
        packed=words[at];mask=(packed>>11)&511;counts=words[at+6]
        pending_landings.append(dict(definition=packed&255,target=(packed>>8)&7,retained_mask=0xffffffff if mask==256 else mask,retained_order=words[at+1],amount=number(at+2),time=number(at+4),hit=counts&511,hits=(counts>>9)&511,depth=(counts>>18)&63,epoch=words[at+7]))
    immunity_usage=[]
    if metadata.get('status_policy',0)&2:
        for who in range(13):
            for name,key in metadata['status_names'].items():
                used=number(L['IMMUNITY_USED_BASE']+(who*L['DEFINITIONS']+key)*2)
                if used:immunity_usage.append(dict(recipient=who,name=name,used=used))
    protection_hits=[]
    if metadata.get('protection_enabled'):
        for index in range(L['COMMANDS']*5):
            records=[(L['PROTECTION_HIT_BASE']+index*16,index%5)]
            records += [(L['SPLIT_HIT_BASE']+(index*4+k)*16,None) for k in range(4)]
            for at,owner in records:
                if words[at+2]:protection_hits.append(dict(time=number(at),owner=(words[at+3]>>3)&7 if owner is None else owner,pierce=bool(words[at+3]&1),down=bool(words[at+3]&4),damage=number(at+4),shield=number(at+6),cover=number(at+8),decoy=number(at+10),hp=number(at+12),hp_after=number(at+14)))
    probability=[]
    for definition in metadata.get('probability_definitions',[]):
        for owner in range(5):
            at=L['PROBABILITY_STATE_BASE']+(definition*5+owner)*2
            probability.append(dict(definition=definition,owner=owner,value=number(at),bits=f'{words[at]|words[at+1]<<32:016x}'))
    return dict(**(dict(probability=probability) if probability else {}),**(dict(protection=protection_summary(L['PROTECTION_STATE_BASE']),protection_hits=protection_hits) if metadata.get('protection_enabled') else {}),**(dict(immunity_usage=immunity_usage) if metadata.get('status_policy',0) else {}),landing_queue=dict(native=bool(metadata.get('native_landing')),enqueued=words[landing+2],landed=words[landing+3],drains=words[landing+4],peak=words[landing+5],entries=pending_landings),staged_applications=staged_rows,periodic_sources=sources,source_queries=source_queries,reference_captures=captures,**resource_state,periodic_bindings=periodic,pending_burst=dict(count=count,enqueued=words[pending+1],fired=words[pending+2],entries=queue),covers=covers,body_damage=[number(L['DAMAGE_ACCOUNTING_STATE_BASE']+20+2*k) for k in range(5)],add_damage=[number(L['DAMAGE_ACCOUNTING_STATE_BASE']+30+2*k) for k in range(5)],scored_damage=[number(L['DAMAGE_ACCOUNTING_STATE_BASE']+2*k) for k in range(5)],add_overkill=[number(L['DAMAGE_ACCOUNTING_STATE_BASE']+10+2*k) for k in range(5)],target_scored_damage=[number(L['DAMAGE_ACCOUNTING_STATE_BASE']+40+2*k) for k in range(len((metadata.get('combat') or {}).get('targets',[])))],bullet_lifetimes=dict(active_carriers=words[15]),lazy_cache=dict(entries=words[10],evaluations=words[11],reuses=words[12],pending=words[13],mapped_pending=words[14]),carriers=carriers,allies=health,weapons=weapon_states,status=words[0],queries=queries,trace=trace,timers=timers,targets=targets,burst_trace=burst_trace,trace_total=words[6],burst_trace_total=words[7],frames=words[8],max_stack_depth=words[3])


def pack_programs(programs):
    if not programs or len(programs)>L['BATCH']:raise ValueError('Portable batch capacity exceeded')
    words=array.array('I',[len(programs)])
    if words.itemsize!=4:raise RuntimeError('Portable wire requires 32-bit unsigned words')
    for program,metadata in programs:
        if len(program)!=L['INPUT_WORDS']:raise ValueError('Invalid program stride')
        words.extend(program)
    if sys.byteorder!='little':words.byteswap()
    return words.tobytes()


def dispatch_programs(programs, *, backend='metal', batch_size=None):
    """Keep independent programs ordered while bounding each GPU allocation."""
    size=L['BATCH'] if batch_size is None else batch_size
    if type(size) is not int or not 1<=size<=L['BATCH']:raise ValueError('Invalid portable dispatch batch size')
    if not programs or len(programs)>0xffffffff:raise ValueError('Invalid portable program count')
    if len(programs)<=size:
        return execute('gpu/event_runtime.slang','portableEvents',pack_programs(programs),L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend)
    batches=[pack_programs(programs[i:i+size]) for i in range(0,len(programs),size)]
    replies=execute_batches('gpu/event_runtime.slang','portableEvents',batches,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend)
    if len(replies)!=len(batches):raise RuntimeError('Incomplete portable dispatch sequence')
    reference=replies[0][1]
    for (raw,evidence),packed in zip(replies,batches):
        count,=struct.unpack_from('<I',packed)
        if len(raw)!=count*L['OUTPUT_WORDS']*4 or not evidence['gpu_execution_verified'] or evidence['backend']!=backend:raise RuntimeError('Invalid portable dispatch evidence')
        for field in ('source_sha256','generated_sha256'):
            if evidence[field]!=reference[field]:raise RuntimeError('GPU source changed between dispatches')
    raw=b''.join(x[0] for x in replies)
    digest=hashlib.sha256(struct.pack('<I',len(programs)))
    for packed in batches:digest.update(memoryview(packed)[4:])
    transport=dict(reference['transport'],cases=len(programs),session_dispatches=len(batches),pipeline_instances=1,buffer_allocations=2,input_bytes=sum(len(p) for p in batches),output_bytes=len(raw))
    transport.pop('session_dispatch_index',None)
    for field in ('gpu_seconds','host_dispatch_seconds'):
        if field in transport:transport[field]=sum(e['transport'][field] for _,e in replies)
    evidence=dict(reference,transport=transport,input_sha256=digest.hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),dispatches=[e for _,e in replies],logical_input_hash='uint32 total count followed by all ordered program words; per-dispatch headers excluded')
    return raw,evidence


def run_programs(programs, *, backend='metal', batch_size=None):
    raw,evidence=dispatch_programs(programs,backend=backend,batch_size=batch_size)
    output=array.array('I');output.frombytes(raw)
    if len(output)!=len(programs)*L['OUTPUT_WORDS']:raise RuntimeError('Invalid GPU output stride')
    if sys.byteorder!='little':output.byteswap()
    results=[decode(output[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],metadata) for i,(_,metadata) in enumerate(programs)]
    if any(r['status'] for r in results):
        raise PortableExecutionError(results,evidence)
    return dict(results=results,**evidence,application_event_runtime_connected=True,autonomous_battle_connected=False,weapon_burst_target_connected=any(m.get('combat') is not None for _,m in programs),
                gpu_timeline_connected=any(m.get('timeline',False) for _,m in programs))


def evaluate(body):
    """Application worker entry; callers supply definitions and external events."""
    compiled=compile_program(body['chars'],[(item['effect'],item['owner']) for item in body['effects']],
                             body['script'],body['base_atk'],combat=body.get('combat'),**body.get('environment',{}))
    result=run_programs([compiled],backend=body.get('backend','metal'))
    from staged_dot_specs import RAMP_FIELDS,MODEL_WARNING
    if any(RAMP_FIELDS.intersection(item['effect']) for item in body['effects']):result.setdefault('app_warnings',[]).append(MODEL_WARNING)
    if any(spec and spec['legacy'] for spec in compiled[1]['source_definitions']):
        from periodic_source_specs import LEGACY_WARNING
        result.setdefault('app_warnings',[]).append(LEGACY_WARNING)
    if any(item['effect'].get('stat')=='lifesteal_pct' for item in body['effects']):
        from portable_lifesteal_reference import MODEL_WARNING as LIFESTEAL_WARNING
        result.setdefault('app_warnings',[]).append(LIFESTEAL_WARNING)
    return result
