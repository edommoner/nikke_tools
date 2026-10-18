"""Strict CUDA effect interpreter and CPU-oracle verification boundary.
Supports autonomous five-member squads within the fail-closed compiled subset.
No effect is silently omitted. Scenario scripts contain external input events, never
CPU-calculated buff states, weapon transitions, damage, or shot times.
"""
from __future__ import annotations
import array,copy,ctypes as C,math,re,time,sys
from pathlib import Path
from gpu_combat import STAT as COARSE_STAT
from detail_world import EN,read_parts,patterns_for,packed_enemy
from detail_boss import WP,WB,WA,ACTOR_WORDS,BP,BL,BW,BH,BLOG,BQ,ILOG,WEAPONS,boss_effects,compile_world,validate_world,empty_world,UnsupportedBoss
from effect_spec import DETAIL_STAT as STAT, EXTRA_STAT as EXTRA, SCOPED_INERT as INERT, NAMED_MAGNITUDE
from base_copy_runtime import POLICIES as COPY_POLICIES
from named_target_specs import resolve_named_attack
from damage_basis_specs import damage_basis
from attack_timing_specs import full_burst_landing
from resource_specs import minimum_remaining,resource_marker,RESOURCE_MARKERS
from target_counter_specs import specification as counter_specification
from periodic_source_specs import specification as source_specification,MAX_SOURCES,MAX_SLOTS,LEGACY_WARNING as SOURCE_WARNING
from staged_dot_specs import specification as staged_specification,MAX_STEPS,MIN_GAP,MODEL_WARNING as STAGED_WARNING
from quantity_specs import validate_quantity,MAX_AMMO_SCALE,FIXED_PARENT_DAMAGE
from attack_group_specs import simultaneous_threshold,MAX_GROUPS,MAX_TARGETS
from weapon_mode_specs import toggle_flag,extra_ammo_count,TOGGLE_FLAG,AMMO_EQUIVALENT
from world_condition_specs import count_condition,specialize_static_counts,validate_target_predicate_policies,TARGET_IS_BOSS,TARGET_IS_ADD
from enemy_recipient_specs import selector_for,recipient_instruction,validate_gpu_fields,specialize_static_fields
from periodic_target_specs import AIM_COMMAND,required_aim_owners
EVENT={'battle_start':0,'passive':0,'full_burst_start':1,'full_burst_end':2,'burst_cast':3,'burst_enter':4,'enemy_spawn':5,'every':6,'on_attack':7,'hit_count':8,'stack_reach':9,'full_charge':10,'full_charge_fire':11,'full_charge_hit':12,'burst_cast_count':13,'last_bullet':14,'inactive':15,'event:heal_received':16,'event:cover_healed':17,'event:shield_applied':18,'event:full_reload':19,'pellet_hit':20,'last_bullet_fire':21,'crit_hit':22,'core_hit':23,'squad_ammo_consume':26,'pellet_hit_in_shot':27,'event:enemy_spawn':5,'received_hit':32,'enemy_death':33,'event:part_destroy':34,'event:projectile_destroy':35,'event:cover_hit':36,'event:lethal_hit':37,'event:self_down':38}
EVENT['non_full_charge_fire']=40
EVENT['event:ally_burst_cast']=42
EVENT['event:shield_consumed']=43
EVENT['event:ally_down']=46
NE,EW,CW,OW=256,344,169,48
MASK_WORDS=(NE+31)//32
B3_MASK,REDUCER_MASK,EXTEND_MASK=270,278,286
NT,TD,TS=8,145,7
DETAIL_ABI='detail_timer_registry_v81'
SNAPSHOT_HP_TARGETS=frozenset((0,1,2,3,8,9,10,11,12,13,18,20,21,22,23,24,25))
class UnsupportedDetail(ValueError):
 def __init__(self,issues):
  self.issues=issues if isinstance(issues,list) else [{'reason':str(issues)}]
  super().__init__(str(self.issues))

def compile_effects(chars,effects,*,enemy_fields=False):
 if len(chars)!=5 or len({c.get('name') for c in chars})!=5:raise ValueError('Detailed squads require five distinct characters')
 effects=list(effects)
 names=[c['name'] for c in chars];states={}
 def state(name):
  if name not in states:states[name]=len(states)
  return states[name]
 from calculator.buff_manager import _has_runtime_cond,_is_cond_finite_passive,_STAT_TO_BUFF
 stat_codes={name:i for i,name in enumerate(sorted({e.get('stat','') for e,n in effects if isinstance(e.get('stat',''),str)}))}
 rows=[];compiled=[];problems=[];groups={};equipment_states={};target_plans=[];target_keys={};counter_definitions={}
 # Each team listener has one immutable activation definition per attacker.
 # All five see the common event count; only the actual attacker activates.
 # This retains attacker-based levels/targets and source-owner conditions.
 team_origins={};team_budgets={};expanded=[];expanded_indices=[];source_rows=[[] for _ in effects]
 for index,(eff,caster) in enumerate(effects):
  timings=eff.get('trigger',{}).get('timing',[])
  team=[t.startswith(('part_hit_count:','body_hit_count:')) for t in timings]
  if any(team):
   if not all(team) or eff.get('type') not in ('buff','instant','damage') or eff.get('tick_interval') is not None:
    raise UnsupportedDetail([{'character':caster,'effect':eff.get('name','?'),'reason':'mixed, periodic or weapon-change team listener remains unsupported'}])
   if any(not t.split(':',1)[1].isdigit() or int(t.split(':',1)[1])<=0 for t in timings):
    raise UnsupportedDetail('team hit threshold must be a positive integer literal')
   for attacker in names:
    clone=copy.deepcopy(eff);team_origins[id(clone)]=(caster,id(eff));expanded.append((clone,attacker));expanded_indices.append(index)
  else:expanded.append((eff,caster));expanded_indices.append(index)
 effects=expanded
 def compile_target(target,q,owner):
  c=chars[owner]
  q[256]=int(isinstance(target,str))
  if isinstance(target,str):
   if target not in target_keys:target_keys[target]=len(target_keys)
   q[257]=target_keys[target]
  if isinstance(target,list):
   leaves=[]
   def flatten(items):
    for item in items:
     if isinstance(item,list):flatten(item)
     else:leaves.append(item)
   flatten(target);descriptors=[];bound=0
   for leaf in leaves:
    row=[0.0]*EW;row[0]=owner;row[1]=-1;row[43]=-1;row[57]=-1;row[64]=-1;row[65]=-1;row[136]=-1
    compile_target(leaf,row,owner);descriptors.append(row)
    kind=int(row[4]);count=int(row[5])
    if kind==4:raise UnsupportedDetail('enemy identities in ordered target lists are not yet implemented')
    bound+=1 if kind in (0,4) else 5 if kind in (1,9,10,12,13,14) else min(count,5-owner-1) if kind==2 else 1+min(count,int(owner>0)+int(owner<4)) if kind==3 else min(count,5-int(row[49]>0)) if kind in (5,6,7,15,16,21,22,23,24) else min(count,4 if kind==19 else 5) if kind in (19,20,25) else int(row[48]).bit_count()
   if bound>21:raise UnsupportedDetail('target list exceeds 21 ordered recipients')
   q[4]=17;q[48]=len(descriptors);target_plans.append((q,descriptors))
  elif isinstance(target,str) and re.fullmatch(r'allies_random(?:_with_debuff)?:[0-5]',target):
   q[4]=20 if '_with_debuff' in target else 19;q[5]=int(target.split(':')[1])
  elif isinstance(target,str) and re.fullmatch(r'allies_down_top_atk_excl:[1-5]',target):q[4]=22;q[5]=int(target.rsplit(':',1)[1])
  elif isinstance(target,str) and re.fullmatch(r'allies_down_class_random:[^:]+:[1-5]',target):
   _,role,count=target.split(':');q[4]=23;q[5]=int(count);q[48]=sum(1<<i for i,ch in enumerate(chars) if ch['_weapon'].get('class')==role)
  elif target=='self':q[4]=0
  elif target=='all_allies':q[4]=1
  elif target=='allies_below_def':q[4]=14
  elif target=='allies_burst3_persona_excl_self':q[4]=18;q[48]=sum(1<<i for i,ch in enumerate(chars) if i!=owner and str(ch.get('burst_stage') or ch['_weapon'].get('burst_stage'))=='3')
  elif target=='allies_burst_casted_burst3':q[4]=11;q[48]=sum(1<<i for i,ch in enumerate(chars) if str(ch.get('burst_stage') or ch['_weapon'].get('burst_stage'))=='3')
  elif isinstance(target,str) and target.startswith('allies_burst_casted_weapon:'):
   weapon=target.split(':',1)[1];q[4]=11;q[48]=sum(1<<i for i,ch in enumerate(chars) if ch['_weapon'].get('weapon_type')==weapon)
  elif isinstance(target,str) and target.startswith(('allies_with_buff:','allies_without_buff:')):
   from calculator.buff_manager import WEAPON_CHANGE_STATE
   name=target.split(':',1)[1];q[4]=12 if target.startswith('allies_with_buff:') else 13;q[5]=state(name);q[223]=1 if name==WEAPON_CHANGE_STATE else 2 if not name else 0
  elif isinstance(target,str) and re.fullmatch(r'allies_weapon_top_atk:[^:]+:[1-5]',target):
   _,weapon,count=target.split(':');q[4]=15;q[5]=int(count);q[48]=sum(1<<i for i,ch in enumerate(chars) if ch['_weapon'].get('weapon_type')==weapon)
  elif isinstance(target,str) and re.fullmatch(r'allies_lowest_atk_burst3:[1-5]',target):
   q[4]=16;q[5]=int(target.split(':')[1]);q[48]=sum(1<<i for i,ch in enumerate(chars) if str(ch.get('burst_stage') or ch['_weapon'].get('burst_stage'))=='3')
  elif target=='all_allies_burst_casted':q[4]=9
  elif target=='all_allies_burst_not_casted':q[4]=10
  elif target=='all_allies_excl_self':q[4]=8;q[48]=31^(1<<owner)
  elif isinstance(target,str) and target.startswith('same_target:'):
   if target!=eff.get('target'):raise UnsupportedDetail('named attack target in an ordered list remains unsupported')
   if staged_specification(eff,names[owner],effects) is not None:q[4]=4
   else:
    reference=resolve_named_attack(eff,names[owner],effects)
    q[4]=4;q[52]=reference.deferred_bonus_hits
  elif isinstance(target,str) and (target in ('target','boss','all_enemies','enemy','target_body','same_target') or target.startswith('enemies_')):q[4]=4
  elif isinstance(target,str) and re.fullmatch(r'allies_top_atk(_excl)?:[1-5]',target):q[4]=5;q[5]=int(target.split(':')[1]);q[49]=int('_excl' in target)
  elif isinstance(target,str) and re.fullmatch(r'allies_lowest_cover_hp:[1-5]',target):
   q[4]=21;q[5]=int(target.split(':')[1])
  elif isinstance(target,str) and re.fullmatch(r'allies_broken_cover_random:\d+',target):q[4]=25;q[5]=min(int(target.split(':')[1]),5)
  elif isinstance(target,str) and re.fullmatch(r'allies_top_def:[1-5]',target):q[4]=6;q[5]=int(target.split(':')[1])
  elif isinstance(target,str) and re.fullmatch(r'allies_lowest_hp(_excl)?:[1-5]',target):q[4]=7;q[5]=int(target.split(':')[1]);q[49]=int('_excl' in target)
  elif isinstance(target,str) and target.startswith(('allies_weapon:','allies_code:')):
   key,v=target.split(':');field='weapon_type' if key=='allies_weapon' else 'element_code';q[4]=8;q[48]=sum(1<<i for i,ch in enumerate(chars) if ch['_weapon'].get(field)==v)
  elif re.fullmatch(r'allies_right:[1-5]',target):q[4]=2;q[5]=int(target.split(':')[1])
  elif re.fullmatch(r'allies_adjacent:[1-5]',target):q[4]=3;q[5]=int(target.split(':')[1])

  elif isinstance(target,str) and target.startswith(('allies_class:','allies_code_excl_self:','allies_weapon_excl_self:','allies_code_weapon:','allies_code_weapon_leftmost:','allies_top_base_charge_time:','allies:')) or target in ('allies_squad','allies_burst3'):
   parts=target.split(':');selected=list(range(5));prefix=parts[0];live_limit=None
   lengths={'allies_class':(2,3),'allies_code_excl_self':(2,),'allies_weapon_excl_self':(2,),'allies_code_weapon':(3,),'allies_code_weapon_leftmost':(4,),'allies_top_base_charge_time':(2,),'allies':(2,),'allies_squad':(1,),'allies_burst3':(1,)}
   if len(parts) not in lengths[prefix]:raise UnsupportedDetail('malformed static target')
   count_index=2 if prefix=='allies_class' and len(parts)==3 else 3 if prefix=='allies_code_weapon_leftmost' else 1 if prefix in ('allies_top_base_charge_time','allies') else None
   if count_index is not None and not parts[count_index].isdigit():raise UnsupportedDetail('invalid static target count')

   if prefix=='allies_class':
    selected=[i for i,ch in enumerate(chars) if ch['_weapon'].get('class')==parts[1]]
    if len(parts)>2:selected=selected[:int(parts[2])]
   elif prefix in ('allies_code_excl_self','allies_weapon_excl_self'):
    key='element_code' if prefix=='allies_code_excl_self' else 'weapon_type';selected=[i for i,ch in enumerate(chars) if i!=owner and ch['_weapon'].get(key)==parts[1]]
   elif prefix.startswith('allies_code_weapon'):
    selected=[i for i,ch in enumerate(chars) if ch['_weapon'].get('element_code')==parts[1] and ch['_weapon'].get('weapon_type')==parts[2]]
    if prefix=='allies_code_weapon_leftmost':live_limit=int(parts[3])
   elif prefix=='allies_squad':
    squad=c['_weapon'].get('squad');selected=[i for i,ch in enumerate(chars) if i==owner or squad and ch['_weapon'].get('squad')==squad]
   elif prefix=='allies_burst3':selected=[i for i,ch in enumerate(chars) if str(ch.get('burst_stage') or ch['_weapon'].get('burst_stage'))=='3']
   elif prefix=='allies_top_base_charge_time':
    selected=[i for i,ch in enumerate(chars) if (ch['_weapon'].get('charge_time') or 0)>0];selected.sort(key=lambda i:-chars[i]['_weapon']['charge_time']);selected=selected[:int(parts[1])];q[141]=1;q[140]=sum((i+1)<<(3*k) for k,i in enumerate(selected))
   elif prefix=='allies':selected=selected[:int(parts[1])]
   q[4]=24 if live_limit is not None else 8;q[5]=min(live_limit,5) if live_limit is not None else 0;q[48]=sum(1<<i for i in selected)
  elif isinstance(target,str):
   from calculator.buff_manager import _NIKKE
   if target not in _NIKKE:raise UnsupportedDetail('target: '+target)
   q[4]=8;q[48]=1<<names.index(target) if target in names else 0
  else:raise UnsupportedDetail('target: '+str(target))
 for (eff,caster),source_index in zip(effects,expanded_indices):
  try:
   owner=names.index(caster);c=chars[owner];kind=eff.get('type');stat=eff.get('stat','');q=[0.0]*EW;q[0]=owner;q[3]=state(eff.get('name',''));q[10]=-1;q[43]=-1;q[57]=eff.get('max_trigger',-1);q[58]=len(rows);q[62]=eff.get('duration_bullets',-1);q[61]=1;q[64]=-1;q[65]=-1;q[136]=-1;q[35]=int(bool(eff.get('name','')))
   team_origin=team_origins.get(id(eff))
   if team_origin:
    q[268]=names.index(team_origin[0])+1
    if team_origin[1] not in team_budgets:team_budgets[team_origin[1]]=len(rows)
    # q[58] stays an instance identity. Only budgets and activation
    # probability accumulators share this separate, one-based key.
    q[269]=team_budgets[team_origin[1]]+1
   if not isinstance(q[57],int) or q[57]<-1:raise UnsupportedDetail('invalid maximum trigger count')
   q[259]=int(str(eff.get('polarity','')).startswith('harmful'))
   q[258]={'buff':0,'instant':1,'damage':2,'weapon_change':3}.get(kind,-1)
   allowed={'persist_on_revive','end_on_shield_consumed','source','name','type','stat','target','trigger','values','fixed_value','max_stack','duration','duration_values','duration_scaling','duration_scaling_ref','trigger_values','max_trigger','gauge_id','gauge_max','hit_count_gauge_ref','hits_parts','tick_interval','tick_start','duration_bullets','damage_formula','scaling','scaling_ref','target_effect','remove_scope','event_scope','weapon_type','damage_coeff','max_ammo','core_dmg_mult','note','polarity','favorite','_source_tag','_quant_group'}
   periodic_source=source_specification(eff)
   ammo_quantity,fixed_quantity=validate_quantity(eff)
   staged=staged_specification(eff,caster,effects)
   if staged:
    allowed|={'ramp_interval','ramp_damage_stack','post_ramp_tick_delay'}
    q[340:344]=[staged.gap,-1 if staged.damage_stack is None else staged.damage_stack,staged.count if isinstance(staged.count,int) else 4096+state(staged.count),staged.post_delay]
   if periodic_source:
    allowed|={'periodic_source','feather_id','feather_slots','feather_interval_base','feather_interval_step_pct'}
    q[304:308]=[state(periodic_source.name),len(periodic_source.lifetimes),periodic_source.base,periodic_source.reduction]
    q[308:308+len(periodic_source.lifetimes)]=periodic_source.lifetimes
    q[137]=int(periodic_source.legacy)
   if kind=='instant' and stat=='force_skill_use':allowed|={'target_skill'}
   counter=counter_specification(eff)
   if counter is not None:
    allowed|={'target_counter'}
    q[295:304]=[counter.threshold,int(counter.actor.kind),counter.actor.identity,counter.actor.generation,
                 counter.families,counter.outcomes,int(counter.preserve),int(counter.on_death),int(counter.owner_only)]
    key=(caster,eff['name'])
    if key in counter_definitions and counter_definitions[key]!=counter:raise UnsupportedDetail('Same named counter requires identical actor and credit policies')
    counter_definitions[key]=counter
   landing=full_burst_landing(eff,c.get('burst_stage',c['_weapon'].get('burst_stage')))
   if 'land_in_full_burst' in eff:allowed|={'land_in_full_burst'}
   floor=minimum_remaining(eff)
   if 'minimum_remaining' in eff:allowed|={'minimum_remaining'};q[294]=floor
   basis=damage_basis(eff)
   if basis.mode:allowed|={'scaling_hp_pct'};q[53]=basis.mode;q[54]=basis.hp_pct
   if 'max_ammo_reduction_exclusive' in eff:
    if kind!='buff' or stat!='max_ammo_pct' or type(eff['max_ammo_reduction_exclusive']) is not bool:raise UnsupportedDetail('Invalid exclusive maximum-ammo reduction')
    allowed|={'max_ammo_reduction_exclusive'};q[55]=int(eff['max_ammo_reduction_exclusive'])
   if kind=='buff' and stat in COPY_POLICIES:
    allowed|={'copy_from'}
    if eff.get('copy_from')!=COPY_POLICIES[stat].selector:raise UnsupportedDetail('unsupported base-stat copy selector')
    if any(key in eff for key in ('scaling','scaling_ref','duration_bullets','target_effect','hit_count_gauge_ref')):raise UnsupportedDetail('unsupported base-stat copy value or lifetime reference')
   q[213]=toggle_flag(eff)
   if kind=='weapon_change':allowed|={'toggle','charge','charge_time','full_charge_mult','reload_time','fire_rate','fire_rate_max','warmup_bullets','pellets','muzzles','post_fire_delay','cover_during_delay','first_damage_coeff','skill_damage','max_ammo_buff_applies','max_ammo_scaling_ref','entry_reload','burst_energy'}
   if set(eff)-allowed:raise UnsupportedDetail('effect fields: '+', '.join(sorted(set(eff)-allowed)))
   if 'remove_scope' in eff and not (kind=='instant' and stat=='remove_named_buff'):raise UnsupportedDetail('removal scope on a non-removal effect')
   if eff.get('event_scope','squad') not in ('squad','recipients'):raise UnsupportedDetail('unknown named event audience')
   if 'end_on_shield_consumed' in eff and (kind!='buff' or stat not in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct') or type(eff['end_on_shield_consumed']) is not bool):raise UnsupportedDetail('invalid shield consumption lifetime')
   q[260]=int(eff.get('end_on_shield_consumed',False))
   if 'persist_on_revive' in eff and type(eff['persist_on_revive']) is not bool:raise UnsupportedDetail('invalid revival persistence flag')
   q[245]=int(eff.get('persist_on_revive',False))
   q[201]=int(eff.get('event_scope')=='recipients');q[203]=q[204]=-1;q[206]=stat_codes.get(stat,-1);q[207]=int(stat in _STAT_TO_BUFF or stat=='atk_caster_based_pct' and eff.get('target','self') not in tuple('allies_random:'+str(n) for n in range(6)))
   base_stat=stat.split(':')[0] if isinstance(stat,str) else stat
   if q[62]!=-1 and (kind not in ('buff','weapon_change') or not isinstance(q[62],int) or q[62]<1):raise UnsupportedDetail('bullet lifetime requires a positive counter')
   if stat in ('gauge_charge','gauge_consume','gauge_consume_as_ammo','gauge_max_add'):
    if kind!=('buff' if stat=='gauge_max_add' else 'instant') or not isinstance(eff.get('gauge_id'),str) or not eff['gauge_id']:raise UnsupportedDetail('invalid gauge definition')
    q[1]={'gauge_charge':9,'gauge_consume':10,'gauge_consume_as_ammo':11,'gauge_max_add':12}[stat];q[64]=state(eff['gauge_id']);q[65]=eff.get('gauge_max',-1);q[70]=eff.get('fixed_value',0)
    if not isinstance(q[65],(int,float)) or not math.isfinite(q[65]) or 'gauge_max' in eff and q[65]<0:raise UnsupportedDetail('invalid gauge cap')
   elif stat in RESOURCE_MARKERS:q[1]=4;q[64]=state(resource_marker(eff))
   elif 'gauge_id' in eff or 'gauge_max' in eff:raise UnsupportedDetail('gauge fields on a nongauge effect')
   elif kind=='instant' and stat in ('buff_stack_add','buff_stack_remove','buff_stack_init','debuff_stack_add','debuff_stack_remove'):
    if not isinstance(eff.get('target_effect',''),str):raise UnsupportedDetail('invalid stack state name')
    q[1]={'buff_stack_add':16,'buff_stack_remove':17,'buff_stack_init':18,'debuff_stack_add':20,'debuff_stack_remove':21}[stat];q[36]=state(eff.get('target_effect',''));q[212]=int(bool(eff.get('target_effect')))
   elif kind=='buff' and stat in ('effect_interval','skill_cooldown'):
    if not isinstance(eff.get('target_effect',''),str):raise UnsupportedDetail('invalid periodic target name')
    q[1]=4;q[220]=1 if stat=='effect_interval' else 2;q[221]=state(eff.get('target_effect',''));q[222]=int(bool(eff.get('target_effect')))
   elif kind=='instant' and stat=='skill_cooldown_reduce_pct':q[1]=22
   elif periodic_source:q[1]=35
   elif kind=='instant' and stat=='force_reload':q[1]=23
   elif kind=='instant' and stat=='burst_charge_pct':q[1]=24
   elif kind=='instant' and stat=='debuff_cleanse':q[1]=26
   elif kind=='instant' and stat=='enemy_buff_cleanse':q[1]=28
   elif kind=='instant' and stat=='revive':q[1]=29
   elif kind=='instant' and stat=='cover_revive':q[1]=30
   elif kind=='instant' and stat=='decoy_heal_pct':q[1]=31
   elif kind=='instant' and stat=='heal_overcharge_discharge':
    if not isinstance(eff.get('target_effect'),str) or not eff['target_effect']:raise UnsupportedDetail('healing discharge requires a named target_effect')
    q[1]=32;q[36]=state(eff['target_effect'])
   elif kind=='instant' and stat=='force_skill_use':
    if eff.get('target_skill') not in ('스킬1','스킬2','스킬3'):raise UnsupportedDetail('force_skill_use requires a valid target_skill slot')
    q[1]=33;q[36]=int(eff['target_skill'][-1])
   elif kind=='damage' and stat=='accum_split_damage':
    if not isinstance(eff.get('target_effect'),str) or not eff['target_effect']:raise UnsupportedDetail('damage discharge requires a named target_effect')
    if any(key in eff for key in ('values','scaling','scaling_ref','hit_count_gauge_ref','damage_formula')) or eff.get('fixed_value',0)!=0 or eff.get('hits_parts',False):raise UnsupportedDetail('damage discharge uses stored damage, without coefficient or geometry modifiers')
    q[1]=34;q[36]=state(eff['target_effect'])
   elif kind=='buff' and stat=='dmg_accum_rate_pct':
    if 'target_effect' in eff and not isinstance(eff['target_effect'],str):raise UnsupportedDetail('invalid damage accumulation rate reference')
    q[1]=0;q[2]=83;q[212]=int('target_effect' in eff);q[36]=state(eff.get('target_effect',''));q[139]=int('values' in eff or 'fixed_value' in eff)
   elif kind=='buff' and stat=='accumulate_max_scale_pct':
    if 'target_effect' in eff and (not isinstance(eff['target_effect'],str) or not eff['target_effect']):raise UnsupportedDetail('invalid healing capacity target_effect')
    q[1]=0;q[2]=77;q[212]=int('target_effect' in eff);q[36]=state(eff.get('target_effect',''))
   elif kind=='buff' and stat in NAMED_MAGNITUDE:
    if not isinstance(eff.get('target_effect'),str) or not eff['target_effect']:raise UnsupportedDetail('named magnitude requires a nonempty target_effect')
    q[1]=0;q[2]=NAMED_MAGNITUDE[stat];q[36]=state(eff['target_effect'])
   elif kind=='instant' and stat=='shield_heal_pct':q[1]=27
   elif kind=='buff' and stat=='next_shield_hp_pct':q[1]=4;q[261]=1
   elif kind=='buff' and stat=='shared_shield_from_max_hp_pct':q[1]=0;q[2]=45
   elif kind=='buff' and stat=='shield_invincible':q[1]=4;q[213]=4
   elif kind=='buff' and stat=='debuff_immune':q[1]=4;q[262]=1
   elif kind=='buff' and isinstance(stat,str) and stat.startswith('debuff_immune:'):q[1]=4;q[262]=2;q[263]=state(stat.split(':',1)[1])
   elif kind=='buff' and stat=='debuff_immune_count':q[1]=4;q[262]=3
   elif kind=='buff' and stat in ('charge_speed_buff_immune','charge_speed_debuff_immune'):q[1]=4;q[213]=8 if stat=='charge_speed_buff_immune' else 16
   elif kind=='buff' and stat=='charge_speed_overflow_conversion_pct':q[1]=4;q[213]=64
   elif kind=='instant' and stat=='burst_reentry':
    value=eff.get('fixed_value')
    if not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>2147483647:raise UnsupportedDetail('invalid burst reentry stage')
    q[1]=25;q[254]=int(value)
   elif kind=='buff' and isinstance(stat,str) and re.fullmatch(r'burst_stage_override:(?:[123A]|reenter[123])',stat):
    q[1]=4
    if 'reenter' in stat:q[253]=int(stat[-1])
    else:q[252]=4 if stat.endswith(':A') else int(stat[-1])
   elif kind=='buff' and stat=='atk_from_hp_pct':q[1]=4;q[241]=1
   elif kind=='buff' and stat=='trigger_count_reduce':
    if not isinstance(eff.get('target_effect',''),str):raise UnsupportedDetail('invalid trigger reduction target')
    q[1]=4;q[243]=eff.get('fixed_value',0);q[244]=1
    if not isinstance(q[243],(int,float)) or not math.isfinite(q[243]) or abs(q[243])>1e8:raise UnsupportedDetail('invalid trigger reduction amount')
   elif kind=='buff' and stat=='reload_time_fixed':q[1]=4;q[242]=int('fixed_value' in eff or 'values' in eff)
   elif kind=='buff' and stat=='buff_max_stack_add':q[1]=19
   elif kind=='buff' and stat=='stack_change_immune':q[1]=4;q[211]=1
   elif kind=='buff' and stat in ('persona_state','stun_immune'):q[1]=4;q[213]=1 if stat=='persona_state' else 2
   elif kind=='buff' and stat=='def_pct':q[1]=0;q[2]=2
   elif kind=='buff' and stat=='':q[1]=4
   elif kind=='buff' and stat in EXTRA:
    if stat in ('optimal_range_min','optimal_range_max_pct') and any('_detail_range' not in ch for ch in chars):raise UnsupportedDetail('optimal range metadata is required')
    q[1]=0;q[2]=EXTRA[stat]
   elif kind=='buff' and stat in INERT:
    q[1]=4
   elif kind=='instant' and stat=='squad_ammo_consume_as':q[1]=AMMO_EQUIVALENT
   elif kind=='instant' and stat=='cover_heal_pct':q[1]=7
   elif kind=='instant' and stat=='heal_hp_pct':q[1]=6
   elif kind=='instant' and stat=='current_hp_reduce':q[1]=8
   elif kind=='instant' and stat in ('ammo_charge_pct','ammo_charge_flat'):q[1]=13 if stat=='ammo_charge_pct' else 14
   elif kind=='buff' and stat=='element_bonus_pct':q[1]=0;q[2]=17
   elif kind=='instant' and stat=='burst_cooldown_reduce':q[1]=5
   elif kind=='buff' and stat in STAT and stat not in ('crit_rate_skill','crit_dmg_skill','atk_flat','enemy_def_down_pct','enemy_def_down_flat'):q[1]=0;q[2]=STAT[stat]
   elif kind=='instant' and stat=='remove_named_buff':
    if not isinstance(eff.get('target_effect'),str):raise UnsupportedDetail('named removal requires a state name')
    if eff.get('remove_scope','global') not in ('global','target'):raise UnsupportedDetail('unknown named removal scope')
    q[1]=1;q[36]=state(eff['target_effect']);q[142]=int(eff.get('remove_scope')=='target')
   elif kind=='instant' and stat=='named_buff_duration_extend':
    if not isinstance(eff.get('target_effect'),str):raise UnsupportedDetail('duration extension requires a state name')
    q[1]=15
    # Exact name plus space-delimited child names, as in the pinned CPU engine.
    prefix=eff['target_effect'];words=[0]*MASK_WORDS
    if prefix:
     for other,who in effects:
      name=other.get('name','')
      if name==prefix or name.startswith(prefix+' '):
       index=state(name)
       if index>=NE:raise UnsupportedDetail('named duration extension exceeds state capacity')
       words[index//32]|=1<<(index%32)
    q[EXTEND_MASK:EXTEND_MASK+MASK_WORDS]=words
   elif kind=='weapon_change':
    q[1]=2
   elif fixed_quantity:q[1]=FIXED_PARENT_DAMAGE
   elif kind=='damage' and base_stat in ('damage','bonus_damage','burst_damage','split_damage','dot_damage','auto_damage','armor_break_damage','armor_break_burst_damage','sequential_damage','projectile_attachment_damage','projectile_explosion_damage','pierce_damage','core_damage'):
    q[1]=3;q[39]={'burst_damage':1,'split_damage':16,'dot_damage':128,'armor_break_damage':512,'armor_break_burst_damage':513,'sequential_damage':2,'projectile_attachment_damage':4,'projectile_explosion_damage':8,'pierce_damage':64,'core_damage':16384}.get(base_stat,0)
    if ':' in stat:
     suffix=stat.split(':',1)[1]
     if suffix.lstrip('-').isdigit():
      if not -256<=int(suffix)<=256:raise UnsupportedDetail('skill hit count exceeds bounds')
      q[61]=int(suffix)
     elif suffix:q[136]=state(suffix);q[137]=1
     else:raise UnsupportedDetail('empty skill hit count reference')
    if base_stat=='dot_damage' and not eff.get('tick_interval'):raise UnsupportedDetail('dot damage requires its periodic timer')
   else:raise UnsupportedDetail('effect type/stat: '+str(kind)+' / '+stat)
   if landing is not None:
    q[51]=2;q[52]=landing.count if isinstance(landing.count,int) else 4096+state(landing.count)
   if 'hit_count_gauge_ref' in eff:
    if kind!='damage' or not isinstance(eff['hit_count_gauge_ref'],str) or not eff['hit_count_gauge_ref']:raise UnsupportedDetail('invalid hit count gauge reference')
    q[136]=state(eff['hit_count_gauge_ref']);q[137]=2
   if 'hits_parts' in eff:
    if kind!='damage' or not isinstance(eff['hits_parts'],bool):raise UnsupportedDetail('invalid part-hit marker')
    if eff['hits_parts']:
     q[39]=int(q[39])|65536
     if c.get('_detail_has_parts',False):q[39]=int(q[39])|1024
   if kind=='damage' and int(q[39])&1:
    target=eff.get('target','self')
    if target=='all_enemies':q[39]=int(q[39])|4096
    elif isinstance(target,str) and target.startswith('enemies_') and target.endswith(':1'):q[39]=int(q[39])|8192
   interval=eff.get('tick_interval',0)
   if interval:
    if kind not in ('instant','damage') or not isinstance(interval,(int,float)) or not math.isfinite(interval) or interval<=0:raise UnsupportedDetail('invalid periodic timer')
    q[59]=interval;q[60]=int(eff.get('tick_start')=='immediate') if kind=='damage' else 2 if eff.get('duration')==-1 else 0
   elif 'tick_start' in eff:raise UnsupportedDetail('tick phase without an interval')
   if eff.get('damage_formula'):
    if kind!='damage' or eff['damage_formula']!='normal_attack':raise UnsupportedDetail('unknown skill damage formula')
    q[39]=int(q[39])|256|(8 if c['_weapon'].get('weapon_type')=='RL' else 0)
   target=eff.get('target','self')
   compile_target(target,q,owner)
   if counter is not None and q[4]!=4:raise UnsupportedDetail('Target counter carrier requires an enemy target; actor binding is explicit')
   if q[55]>0 and q[4]==4:raise UnsupportedDetail('Exclusive ammo reductions require allied targets')
   if kind=='buff' and stat in COPY_POLICIES:
    if q[4] not in SNAPSHOT_HP_TARGETS:raise UnsupportedDetail('base-stat copy requires synchronously resolved allied targets')
    q[36]=0 if stat=='atk_copy' else 1
   if kind=='buff' and stat=='max_hp_from_max_hp_pct' and q[4] not in SNAPSHOT_HP_TARGETS:raise UnsupportedDetail('maximum-HP snapshot requires synchronously resolved allied targets')
   if q[1]==34 and q[4]!=4:raise UnsupportedDetail('damage discharge requires an enemy target')
   if q[1] in (6,7,8,27,29,31) and q[4]==4:raise UnsupportedDetail('enemy heal target')
   c=chars[owner];lv=str(c.get('skill_levels',{}).get(eff.get('source','')[-1:],c.get('skill_level',10)))
   q[6]=1 if stat in ('stun','pierce_enabled','armor_break_enabled','charge_time_fixed') else eff.get('fixed_value',eff.get('values',{}).get(lv,0));duration=eff.get('duration');duration=(eff.get('duration_values') or {}).get(lv,(eff.get('duration_values') or {}).get('10',0)) if kind=='buff' and duration is None and 'duration_values' in eff else duration;q[7]=-1 if duration is None else duration;q[9]=eff.get('max_stack',1)
   if stat in ('dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct','dmg_accum_rate_pct','max_hp_from_max_hp_pct','atk_copy','hp_copy'):q[6]=eff.get('fixed_value',eff.get('values',{}).get(lv,eff.get('values',{}).get('10',0)))
   q[208]=-1 if eff.get('duration') is None else eff['duration'];q[209]=1 if str(eff.get('polarity','')).startswith('beneficial') else 2 if eff.get('polarity')=='harmful' else 3 if eff.get('polarity')=='harmful_irremovable' else 0;q[210]=int(kind=='buff');q[215]=-1;q[216]=q[4]
   if q[1]==AMMO_EQUIVALENT:
    extra_ammo_count(q[6])
    if q[4]!=0 or eff.get('scaling'):raise UnsupportedDetail('Ammo-equivalent notices require a literal caster quantity')
   if kind=='instant' and stat=='debuff_cleanse' and (not isinstance(q[6],(int,float)) or not math.isfinite(q[6])):raise UnsupportedDetail('invalid cleanse limit')
   if 'duration_scaling' in eff or 'duration_scaling_ref' in eff:
    if kind!='buff' or eff.get('duration_scaling')!='stack_count' or not isinstance(eff.get('duration_scaling_ref',''),str):raise UnsupportedDetail('invalid duration scaling')
    q[218]=1;q[219]=state(eff['duration_scaling_ref']) if eff.get('duration_scaling_ref') else -1
   if q[1]==29 and (not isinstance(q[6],(int,float)) or not math.isfinite(q[6]) or q[6]<=0):raise UnsupportedDetail('revive requires a positive HP percentage')
   if q[1]==30 and (not isinstance(q[6],(int,float)) or not math.isfinite(q[6]) or q[6]==0):raise UnsupportedDetail('cover revival requires a nonzero HP percentage')
   if q[1] in (16,17,18,19,20,21,22):q[6]=eff.get('fixed_value',(eff.get('values') or {}).get(lv,(eff.get('values') or {}).get('10',1 if q[1]==19 else 0)))
   if stat=='charge_time_fixed':q[138]=eff.get('fixed_value',0);q[139]=int('fixed_value' in eff)
   scaling=eff.get('scaling')
   max_hp_scale=scaling=='max_hp' and (kind=='instant' and stat in ('cover_heal_pct','heal_hp_pct','shield_heal_pct','decoy_heal_pct') or kind=='buff' and stat=='cover_hp_pct')
   if max_hp_scale:q[50]=1
   if basis.mode and q[1]!=3:raise UnsupportedDetail('HP attack basis requires coefficient damage')
   if kind=='instant' and stat=='shield_heal_pct' and scaling not in (None,'max_hp'):raise UnsupportedDetail('unsupported shield healing scale')
   if basis.mode:pass
   elif scaling=='lost_hp_pct' and kind=='buff':q[10]=-3
   elif ammo_quantity:
    if q[1]!=0:raise UnsupportedDetail('Final-ammunition scaling requires a numeric buff')
    q[10]=MAX_AMMO_SCALE
   elif scaling and not max_hp_scale:
    if scaling!='stack_count' or not eff.get('scaling_ref') and not (kind=='damage' and base_stat=='dot_damage'):raise UnsupportedDetail('scaling: '+str(scaling))
    q[10]=state(eff['scaling_ref']) if eff.get('scaling_ref') else -2
    if kind=='damage' and base_stat=='dot_damage':q[255]=state(eff.get('scaling_ref',''))
    if kind=='damage' and base_stat!='dot_damage' and ':' not in stat and 'hit_count_gauge_ref' not in eff and eff.get('scaling_ref'):q[136]=state(eff['scaling_ref']);q[137]=1
   if kind=='damage':
    from calculator.timeline import BURST_GAUGE_EXCEPTIONS
    energy=BURST_GAUGE_EXCEPTIONS.get(caster,{}).get(eff.get('name') or stat,{}).get('burst_energy')
    if energy is not None:q[250]=float(energy);q[251]=1
   seen_timings=set();period=None
   for timing in eff.get('trigger',{}).get('timing',[]):
    if timing.startswith('hit_count:') and len(timing.split(':'))>2 and '{' in timing:raise UnsupportedDetail('named skill-hit threshold requires an integer literal')
    q[46]=0;q[37]=-1;q[38]=0;q[71]=-1;stage=-1
    never_count='{0}' in timing and timing.startswith(('full_charge_fire_count:','full_charge_count:','full_charge_hit_count:','non_full_charge_fire_count:','core_hit:','core_hit_count:','crit_hit_count:','pellet_hit:','pellet_hit_count:','burst_cast_count:'))
    if never_count:timing=timing.replace('{0}','1')
    if '{0}' in timing:
     threshold=eff.get('trigger_values',{}).get(lv)
     if threshold is None:raise UnsupportedDetail('missing level-dependent trigger value')
     timing=timing.replace('{0}',str(threshold))
    if timing in ('full_charge','on_attack','hit_count','pellet_hit','core_hit','crit_hit','last_bullet','last_bullet_fire','event:full_reload','squad_ammo_consume'):q[63]=1
    if timing=='passive':q[11]=1
    if timing=='feather_tick':code=60;arg=0;q[37]=-1
    elif timing.startswith('source_tick:'):
     if not timing.split(':',1)[1]:raise UnsupportedDetail('Periodic source tick requires a name')
     code=59;arg=0;q[37]=state(timing.split(':',1)[1])
    elif timing.startswith('every:'):
     code=6;arg=float(timing.split(':')[1].rstrip('s'))
     if not math.isfinite(arg) or arg<=0:raise UnsupportedDetail('period must be positive')
     if not q[44]:q[44]=arg
    elif timing.startswith(('full_burst_start_count:','full_burst_end_count:','full_burst_start_exact:')):
     key,threshold=timing.split(':');code=1 if key.startswith('full_burst_start') else 2;arg=int(threshold);q[46]=3 if key.endswith('_exact') else 2
    elif timing.startswith(('full_charge_fire_count:','full_charge_count:','full_charge_hit_count:','non_full_charge_fire_count:','burst_cast_count:')):
     key,threshold=timing.split(':');code={'full_charge_fire_count':11,'full_charge_count':11,'full_charge_hit_count':12,'non_full_charge_fire_count':40,'burst_cast_count':3}[key];arg=int(threshold);q[46]=2 if key=='burst_cast_count' else 1
    elif timing.startswith('burst_enter_count:'):
     _,raw_stage,threshold=timing.split(':');code=4;stage=int(raw_stage);arg=int(threshold);q[46]=2
    elif timing.startswith('burst_enter:'):code=4;arg=int(timing.split(':')[1]);stage=arg
    elif timing.startswith('squad_burst_cast:'):code=41;arg=int(timing.split(':')[1]);stage=arg
    elif timing.startswith(('pellet_hit_count:','pellet_hit:','crit_hit_count:','core_hit_count:','core_hit:','squad_ammo_consume:','received_hit_count:','received_hit:')):
     key,threshold=timing.split(':');code={'pellet_hit_count':20,'pellet_hit':20,'crit_hit_count':22,'core_hit_count':23,'core_hit':23,'squad_ammo_consume':26,'received_hit_count':32,'received_hit':32}[key];arg=int(threshold);q[46]=1
    elif timing.startswith(('part_hit_count:','body_hit_count:')):
     key,threshold=timing.split(':');code=44 if key=='part_hit_count' else 45;arg=int(threshold);q[46]=1
    elif timing.startswith('pellet_hit_in_shot:'):code=27;arg=int(timing.split(':')[1])
    elif timing.startswith('hit_count:') and len(timing.split(':'))>2:
     parts=timing.split(':')
     if len(parts)!=3 or not parts[1] or parts[1].lstrip('-').isdigit() or not re.fullmatch(r'-?\d+',parts[2]):raise UnsupportedDetail('invalid named skill-hit threshold')
     code=49;arg=int(parts[2]);q[37]=state(parts[1]);q[46]=1
    elif timing.startswith('multi_hit:'):code=62;arg=simultaneous_threshold(timing)
    elif timing.startswith('hit_count:'):code=8;arg=int(timing.split(':')[1])
    elif timing.startswith('on_attack_count:'):code=7;arg=int(timing.split(':')[1])
    elif timing.startswith(('charge_hold:','charge_hold_count:')):
     parts=timing.split(':');raw=parts[1];seconds=float(raw)
     if not math.isfinite(seconds) or seconds<0:raise UnsupportedDetail('invalid charge hold threshold')
     code=39;arg=int(parts[2]) if parts[0]=='charge_hold_count' else 1;q[46]=1 if parts[0]=='charge_hold_count' else 0;q[37]=state('charge_hold:'+raw);q[38]=seconds
    elif timing.startswith('event:state_end:'):code=29;arg=0;q[37]=state(timing[len('event:state_end:'):])
    elif timing.startswith('event:accum_full:'):
     name=timing[len('event:accum_full:'):]
     if not name:raise UnsupportedDetail('accumulation-full event requires a state name')
     code=50;arg=0;q[37]=state(name)
    elif timing.startswith('every_stack:'):
     _,name,step=timing.split(':');code=30;arg=int(step);q[37]=state(name)
     if arg<=0:raise UnsupportedDetail('gauge crossing step must be positive')
    elif timing.startswith('stack_reach:'):
     _,name,count=timing.split(':');code=9;arg=0;q[37]=state(name);q[38]=int(count)
    elif timing.startswith(('hp_below:','hp_below_count:','event:ally_hp_below:','event:adjacent_hp_below:')) or timing=='event:adjacent_hp_max':
     code=31;arg=0
     if timing.startswith('hp_below_count:'):
      parts=timing.split(':')
      if len(parts)!=3:raise UnsupportedDetail('invalid HP crossing counter')
      raw=parts[1];arg=int(parts[2]);q[46]=3;key='hp_below:'+raw;stage=-11;code=48
     elif timing.startswith('hp_below:'):raw=timing.split(':',1)[1];key=timing;stage=-11;code=48
     elif timing.startswith('event:ally_hp_below:'):raw=timing.rsplit(':',1)[1];key=timing[6:];stage=-12
     elif timing.startswith('event:adjacent_hp_below:'):raw=timing.rsplit(':',1)[1];key=timing[6:];stage=-13
     else:raw='100';key=timing[6:];stage=-14
     q[38]=float(raw)
     if not math.isfinite(q[38]):raise UnsupportedDetail('HP crossing threshold must be finite')
     q[71]=state(key)
    elif timing.startswith('event:target_counter_complete:'):
     name=timing[len('event:target_counter_complete:'):]
     if not name:raise UnsupportedDetail('Counter completion requires a marker name')
     code=58;arg=0;q[37]=state(name)
    elif timing in EVENT:code=EVENT[timing];arg=1 if code in (7,8) else 0
    elif timing.startswith('event:'):code=31;arg=0;q[71]=state(timing[len('event:'):])
    else:raise UnsupportedDetail('timing: '+timing)
    reducible=timing.startswith(('on_attack_count:','hit_count:','full_charge_fire_count:','full_charge_count:','full_charge_hit_count:','non_full_charge_fire_count:','core_hit:','core_hit_count:','crit_hit_count:','pellet_hit:','pellet_hit_count:'))
    if reducible:
     stage=1
     if abs(arg)>1e8:raise UnsupportedDetail('invalid counter magnitude')
    if never_count:stage=2
    if (code in (7,8,27) or q[46]>0) and arg<1 and not reducible:raise UnsupportedDetail('counter threshold must be positive')
    tag=q[37] if code in (9,29,30,39,49,50,58,59) else q[71] if code in (31,48) else -1
    descriptor=(code,arg,q[46],tag,q[38] if code in (9,39) or stage<=-11 else 0,int(timing=='passive'),stage)
    index=int(q[144])
    if index>=NT:raise UnsupportedDetail('more than eight trigger descriptors')
    q[TD+index*TS:TD+(index+1)*TS]=descriptor;q[144]=index+1
    # Legacy fields are retained for low-event introspection and burst extension.
    if code<32:q[72+code*2]=arg;q[73+code*2]=q[46];q[12]=int(q[12])|1<<code
    q[13]=arg
   if not q[144]:raise UnsupportedDetail('missing trigger')
   cond=eff.get('trigger',{}).get('condition',[])
   if any(x in cond for x in ('self_undying','no_broken_cover_ally')) and 'passive' in eff.get('trigger',{}).get('timing',[]):raise UnsupportedDetail('Live marker/cover predicates currently require an explicit activation event')
   if len(cond)>3:raise UnsupportedDetail('more than three conditions')
   q[14]=len(cond)
   if cond and q[11] and q[7]>=0:
    if kind!='buff' or q[62]>=0:raise UnsupportedDetail('finite conditional passive requires a timed buff')
    q[69]=1
   activation_context=(caster,owner,c,lv)
   if team_origin:
    caster=team_origin[0];owner=names.index(caster);c=chars[owner];lv=str(c.get('skill_levels',{}).get(eff.get('source','')[-1:],c.get('skill_level',10)))
   for j,condition in enumerate(cond):
    typ=0;name=0;arg=0
    if condition.startswith(('gauge_above:','gauge_below:','gauge_eq:','gauge_mod:')):
     parts=condition.split(':');typ={'gauge_above':18,'gauge_below':19,'gauge_eq':20,'gauge_mod':21}[parts[0]];name=state(parts[1]);arg=float(parts[2])
     if typ==21:
      if not arg.is_integer() or arg<=0:raise UnsupportedDetail('invalid gauge modulus')
      q[66+j]=int(parts[3])
    elif condition=='during_full_burst':typ=1
    elif condition=='not_during_full_burst':typ=2
    elif condition.startswith(('self_state:','not_self_state:')):
     from calculator.buff_manager import WEAPON_CHANGE_STATE
     typ=3 if condition.startswith('self_state:') else 4;sname=condition.split(':',1)[1];name=state(sname);arg=1 if sname==WEAPON_CHANGE_STATE else 2 if not sname else 0
    elif condition.startswith('self_stack_above:'):
     _,s,threshold=condition.split(':');typ=5;name=state(s);arg=int(threshold)
    elif condition.startswith('self_hp_above:'):typ=9;arg=float(condition.split(':')[1])
    elif condition.startswith('self_hp_below:'):typ=10;arg=float(condition.split(':')[1])
    elif condition.startswith('ally_hp_below:'):
     typ=34;arg=float(condition.split(':')[1])
     if not math.isfinite(arg):raise UnsupportedDetail('invalid ally HP threshold')
    elif condition=='self_hp_max':typ=11
    elif condition=='self_cover_alive':typ=36
    elif condition=='not_self_cover_alive':typ=37
    elif condition=='self_undying':typ=38
    elif condition=='no_broken_cover_ally':typ=39
    elif condition.startswith('target_state:'):typ=16;name=state(condition[len('target_state:'):])
    elif condition.startswith('not_target_state:'):typ=17;name=state(condition[len('not_target_state:'):])
    elif condition=='during_shield':typ=12
    elif condition=='during_charge':typ=29
    elif condition=='focusing':typ=30
    elif condition=='not_self_caused_heal':typ=13
    elif condition=='burst_casted':typ=14
    elif condition=='burst_not_casted':typ=15
    elif condition=='has_burst1_ally':typ=31
    elif condition=='no_burst1_ally':typ=32
    elif condition in ('has_defender_ally','no_defender_ally'):
     from calculator.buff_manager import _NIKKE
     has=any(n!=caster and _NIKKE.get(n,{}).get('class')=='방어형' for n in names)
     typ=25;arg=int(has==(condition=='has_defender_ally'))
    elif condition=='squad_ally_exists':
     # Squad affiliation is immutable input metadata, not a battle result.
     # Keep the pinned CPU's original-name lookup, including costume variants.
     from calculator.buff_manager import _NIKKE
     squad=_NIKKE.get(caster,{}).get('squad');typ=25
     arg=int(bool(squad and any(n!=caster and _NIKKE.get(n,{}).get('squad')==squad for n in names)))
    elif condition.startswith('target_code:'):typ=22;arg=int(not c.get('_detail_enemy_code') or c['_detail_enemy_code']==condition.split(':',1)[1])
    elif condition=='target_stunned':typ=23
    elif condition=='self_stun_immune':typ=24
    elif condition.startswith(('enemy_count_above:','enemy_count_below:')):
     typ,arg=count_condition(condition)
    elif condition in ('target_is_boss','target_is_add'):typ=TARGET_IS_BOSS if condition=='target_is_boss' else TARGET_IS_ADD
    elif condition=='core_hit':
     # Pinned CPU means an enemy with an enabled core, not a sampled bullet
     # hit. This is immutable enemy input in the current static-boss model.
     core=c.get('_detail_enemy_core_px')
     if not isinstance(core,(int,float)) or not math.isfinite(core) or core<0:raise UnsupportedDetail('core presence metadata is required')
     typ=35;arg=0
    elif condition=='optimal_range':
     if '_detail_range' not in c:raise UnsupportedDetail('optimal range metadata is required')
     typ=33
    elif condition=='not_core':typ=27
    elif condition=='trigger_hit_crit':typ=28
    elif condition.startswith('prob:'):
     raw=condition.split(':',1)[1];typ=26
     if raw.startswith('{') and raw.endswith('}'):
      tv=eff.get('trigger_values',{})
      if not tv:typ=25;arg=0
      else:arg=float(tv.get(lv,tv.get('10')))/100
     else:arg=float(raw)/100
     if not math.isfinite(arg):raise UnsupportedDetail('nonfinite probability')
    elif condition=='front_row':raise UnsupportedDetail('front_row has no pinned CPU implementation')
    elif condition=='back_row':typ=7
    elif condition.startswith('self_stat_above:'):
     _,key,threshold=condition.split(':');typ=8;name=STAT[key];arg=float(threshold)
    else:raise UnsupportedDetail('condition: '+condition)
    q[15+j*3:18+j*3]=[typ,name,arg]
   caster,owner,c,lv=activation_context
   if kind=='weapon_change':
    from calculator.timeline import _MECHANICS,_DELAYS,_pick,CharState
    weapon=eff.get('weapon_type','SR');defaults=_MECHANICS['weapon_type_defaults'][weapon];over=_DELAYS.get('_weapon_change',{}).get(caster,{}).get(eff.get('name'),{})
    rate=c['_weapon'].get('weapon_change_fire_rate',{}).get(eff.get('source'));cdn={'fire_rate':rate,'fire_rate_max':rate} if rate else {}
    def coefficient(value):return float(value.get(lv,value.get('10',0))) if isinstance(value,dict) else float(value)
    q[26]=coefficient(eff.get('damage_coeff',{}));q[27]=eff.get('max_ammo',1);q[28]=float(_pick('fire_rate',over,eff,cdn,defaults,default=defaults.get('fire_rate_min',1)))
    q[24]=float(_pick('fire_rate_max',over,eff,cdn,defaults,default=q[28]) or q[28]);q[25]=int(_pick('pellets',over,eff,defaults,default=1));q[29]=int(_pick('muzzles',over,eff,default=1))
    q[30]=c.get('_detail_mode_optimal',{}).get(weapon,c.get('_optimal',False));q[40]=float(_pick('warmup_bullets',over,eff,defaults,default=1));q[41]=defaults.get('cooldown_time',1);q[42]=float(over.get('entry_delay',0))
    from calculator.buff_manager import optimal_range_of
    q[264:266]=optimal_range_of(caster,weapon)
    q[249]=float(_pick('burst_energy',over,eff,defaults,default=0))
    mode=defaults.get('type','charge')
    if eff.get('charge') is not None:mode='charge' if eff['charge'] else 'auto' if mode=='charge' else mode
    q[224]={'auto':1,'auto_warmup':2,'charge':3}[mode];q[225]=eff.get('charge_time',1);q[226]=eff.get('full_charge_mult',100)
    q[227]=float(_pick('post_fire_delay',over,eff,defaults,default=0));q[228]=eff.get('core_dmg_mult',c['_weapon'].get('core_dmg_mult',200))
    q[231]=bool(_pick('cover_during_delay',over,eff,default=CharState(c,1,None).cover_during_delay))
    q[232]=q[62];q[62]=-1;q[233]=bool(eff.get('max_ammo_buff_applies'));q[234]=state(eff['max_ammo_scaling_ref']) if eff.get('max_ammo_scaling_ref') else -1
    q[235]=bool(eff.get('skill_damage'));q[236]=coefficient(eff['first_damage_coeff']) if 'first_damage_coeff' in eff else -1
    q[237]=eff.get('reload_time',c['_weapon'].get('reload_time',1.5));q[238]=int(q[27]!=-1 and eff.get('duration') is None and eff.get('duration_bullets') is None)
    q[239]=bool(eff.get('entry_reload') and 'entry_delay' not in over);q[240]=int('entry_delay' in over or q[239])
    if q[27]!=-1 and (q[27]<1 or int(q[27])!=q[27]):raise UnsupportedDetail('invalid weapon-mode magazine')
    if q[28]<=0 or q[40]<=0 or not 1<=q[25]<=64 or not 1<=q[29]<=8:raise UnsupportedDetail('invalid weapon mode mechanics')
   if eff.get('_source_tag') in ('equipment','cube'):q[213]=int(q[213])|32
   group=(caster,eff.get('_source_tag'),eff.get('_quant_group') or len(rows),bool(q[55]))
   if group not in groups:groups[group]=len(groups)
   q[45]=groups[group]
   # Pinned CPU merges identical named equipment states and retains the first definition.
   # This includes distinct overload groups; compatibility is not an in-game correctness claim.
   if eff.get('_source_tag')=='equipment' and kind=='buff' and not cond:
    alias=(owner,eff.get('name'),stat,str(target),q[9])
    if alias in equipment_states:q[43]=equipment_states[alias]
    else:equipment_states[alias]=len(rows)
   q[217]=int(_has_runtime_cond(eff.get('trigger',{}).get('condition',[]),math.inf,q[62]))
   q[205]=int(kind=='buff' and q[62]<0 and not _has_runtime_cond(eff.get('trigger',{}).get('condition',[]),math.inf if q[7]<0 else 0) and not _is_cond_finite_passive(eff))
   if enemy_fields and recipient_instruction(q):q[48]=int(selector_for(eff.get('target','self')))
   source_rows[source_index].append(len(rows));rows.append(q);compiled.append((eff,caster))
  except (UnsupportedDetail,KeyError,TypeError,ValueError) as error:problems.append({'character':caster,'effect':eff.get('name','?'),'reason':str(error)})
 carriers=set()
 for q in rows:
  if q[1]==0 and q[2] in (81,82) and q[35]>0:
   if q[3] in carriers:raise UnsupportedDetail('ambiguous damage accumulator name aliases require explicit instance semantics')
   carriers.add(q[3])
 # Forced slot activation selects active definitions in authored order. The
 # existing mask storage is disjoint from B3 exclusions on this instruction.
 for q,(eff,caster) in zip(rows,compiled):
  if q[1]!=33:continue
  words=[0]*MASK_WORDS
  for k,(other,source) in enumerate(compiled):
   if source==caster and other is not eff and other.get('source')==eff['target_skill']:
    if k>=NE:raise UnsupportedDetail('forced skill exceeds definition mask capacity')
    words[k//32]|=1<<(k%32)
  q[B3_MASK:B3_MASK+MASK_WORDS]=words
 # The CPU matches raw timing strings, before level placeholders are resolved.
 for q,(eff,caster) in zip(rows,compiled):
  own=set(eff.get('trigger',{}).get('timing',[]))
  for k,(reducer,rcaster) in enumerate(compiled):
   name=reducer.get('target_effect','')
   if rcaster!=caster or reducer.get('type')!='buff' or reducer.get('stat')!='trigger_count_reduce' or not name:continue
   shared=eff.get('name')==name or any(caster==other and reg.get('name')==name and own.intersection(reg.get('trigger',{}).get('timing',[])) for reg,other in effects)
   if shared and k<NE:q[REDUCER_MASK+k//32]=int(q[REDUCER_MASK+k//32])|(1<<(k%32))
 def subscribed(code,tag):
  return any(int(r[TD+a*TS])==code and (code not in (9,29,30,31,50) or int(r[TD+a*TS+3])==tag) for r in rows for a in range(int(r[144])))
 for q,(eff,caster) in zip(rows,compiled):
  name=eff.get('name','');text='event:'+name
  if text in EVENT:code,tag=EVENT[text],-1
  elif text.startswith('event:state_end:'):code,tag=29,states.get(text[len('event:state_end:'):],-1)
  elif text.startswith('event:accum_full:'):code,tag=50,states.get(text[len('event:accum_full:'):],-1)
  else:code,tag=31,int(q[3])
  if name and subscribed(code,tag):q[202]=code+1;q[203]=tag
  tag=states.get('stat_applied:'+eff.get('stat',''),-1)
  if eff.get('stat') in ('dot_dmg_pct','split_dmg_pct') and tag>=0 and subscribed(31,tag):q[204]=tag
 for q in rows:
  if q[1]==18:
   q[215]=next((i for i,r in enumerate(rows) if r[0]==q[0] and r[3]==q[36] and r[210]>0),-1)
 plans={}
 for parent,descriptors in target_plans:
  key=tuple(tuple(row) for row in descriptors)
  if key not in plans:
   plans[key]=len(rows)
   for row in descriptors:row[58]=len(rows);rows.append(row)
  parent[5]=plans[key]
 if len(states)>NE:problems.append({'reason':f'more than {NE} named states'})
 if len(rows)>NE:problems.append({'reason':f'more than {NE} effects'})
 if problems:raise UnsupportedDetail(problems)
 counter_names={(int(r[0]),int(r[3])) for r in rows if r[1]==0 and r[2]==87}
 if any(r[1] in (16,17,18,19,20,21) and (int(r[0]),int(r[36])) in counter_names for r in rows):raise UnsupportedDetail('Counter progress is separate from named buff stack manipulation')
 try:validate_target_predicate_policies(rows)
 except ValueError as error:raise UnsupportedDetail(str(error)) from error
 if len({(q[0],q[304]) for q in rows if q[1]==35})>MAX_SOURCES:raise UnsupportedDetail('Periodic source capacity exceeded')
 return {'effects':rows,'states':states,'chars':chars,'source_rows':source_rows,'periodic_source_estimated':any(q[1]==35 and q[137]>0 for q in rows),'counter_single_body':any(s.single_body for s in counter_definitions.values()),'mode_weapons':[WEAPONS.index(e.get('weapon_type','SR')) if e.get('type')=='weapon_change' else -1 for e,n in compiled]+[-1]*(len(rows)-len(compiled))}

def weapon_rows(chars,base_stats):
 rows=[]
 for c in chars:
  w=c['_weapon'];r=[0.0]*CW;r[0]=base_stats[c['name']]['atk'];r[1]=w['damage_coeff'];r[2]=w['max_ammo'];r[4]=w['fire_rate'];r[12]=w.get('core_dmg_mult',200);r[13]=w.get('spread_end',10);r[14]=c.get('_optimal',False);r[15]=c.get('_element_match',False)
  from calculator.timeline import CharState
  st=CharState(c,r[0],None);r[3]=w['reload_time'];r[5]=st.fire_rate_max or st.fire_rate;r[6]=st.warmup_bullets;r[7]=st.post_reload_delay;r[8]=2 if st.fire_mode=='auto_warmup' else 1;r[9]=st.spread_start;r[10]=st._spread_shots_needed;r[11]=st.mech.get('cooldown_time',1);r[8]=3 if st.fire_mode=='charge' else r[8];r[16]=st.charge_time_base;r[17]=st.post_fire_delay;r[18]=st._min_fire_cycle;r[19]=w.get('full_charge_mult',100);r[20]=int(c.get('_detail_stage',0));r[21]=w.get('burst_cooldown',40);r[22]=c.get('_detail_pattern',0);r[23]=c.get('_detail_wait',0);r[24]=c.get('_detail_delay',0);r[25]=c.get('burst_regen_time',2);r[26]=w.get('weapon_type')=='RL';r[27]=c.get('_detail_burst_candidate',True);r[28]=base_stats[c['name']].get('hp',1);r[29]=w.get('charge_time') or 0;r[30]=base_stats[c['name']].get('def',0);r[31]=st.cover_during_delay;r[32]=st.pellets;r[33]=st.muzzles;r[34]=st.clip_count
  from calculator.buff_manager import _NIKKE
  r[44]=c.get('_detail_gauge_mode',0);r[45]=st.burst_energy;r[46]=_NIKKE.get(c['name'],{}).get('burst_energy',0);r[47]=_NIKKE.get(c['name'],{}).get('burst_energy_raw',r[46]/2)
  r[160]=c.get('_detail_explicit_stage',0);r[161]=c.get('_detail_red_hood',0);r[162]=c.get('_detail_innate_stage',0);r[163]=c.get('_detail_reenter_delay',.5)
  if type(c.get('weapon_mode_swap',False)) is not bool:raise ValueError('Invalid manual mode input flag')
  r[168]=int(c.get('weapon_mode_swap',False))
  if '_detail_range' in c:
   lo,hi,distance=c['_detail_range']
   if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (lo,hi)) or lo<0 or hi<lo or distance is not None and (not isinstance(distance,(int,float)) or not math.isfinite(distance)):raise ValueError('Invalid compiled optimal range')
   r[164:168]=[lo,hi,0 if distance is None else distance,1 if distance is None else 2]
  # Five exact 32-bit words encode explicitly prioritized cycles 1..160.
  for cycle in c.get('_detail_pattern_cycles',[]):
   word,bit=divmod(cycle-1,32);r[35+word]=int(r[35+word])|(1<<bit)
  controls=c.get('_detail_controls',[]);sequences=c.get('_detail_sequences',[]);r[40]=len(controls);r[41]=len(sequences);r[42]=c.get('_detail_camera',0);r[43]=c.get('_detail_control_mode',0)
  if len(controls)>8 or len(sequences)>8 or any(len(row)!=12 or not all(math.isfinite(v) for v in row) for row in controls) or any(len(row)!=2 or not all(math.isfinite(v) for v in row) for row in sequences):raise ValueError('Invalid compiled control schedule')
  for i,entry in enumerate(controls):r[48+i*12:60+i*12]=entry
  for i,entry in enumerate(sequences):r[144+i*2:146+i*2]=entry
  rows.extend(r)
 return rows

def module_image(device,backend='auto'):
 """Use a hash-checked architecture-specific binary; never compile on request."""
 from lifecycle_specs import gpu_source_matches
 if not gpu_source_matches():raise UnsupportedDetail('Lifecycle registry and generated CUDA dispatch differ; regenerate and rebuild')
 from impact_specs import gpu_source_matches as impact_source_matches
 if not impact_source_matches():raise UnsupportedDetail('Typed impact definitions and generated CUDA differ; regenerate and rebuild')
 from world_condition_specs import gpu_source_matches as world_conditions_match
 if not world_conditions_match():raise UnsupportedDetail('World predicate definitions and generated CUDA differ; regenerate and rebuild')
 from enemy_recipient_specs import gpu_source_matches as enemy_fields_match
 if not enemy_fields_match():raise UnsupportedDetail('Enemy recipient definitions and generated CUDA differ; regenerate and rebuild')
 import json,hashlib
 if backend not in ('auto','ptx','native'):raise ValueError('Invalid detailed module backend')
 root=Path(__file__).parent;cap=getattr(device,'compute_capability',None)
 if backend!='ptx' and cap:
  sm=cap[0]*10+cap[1];binary=root/f'detail_effects-sm{sm}.cubin';manifest=binary.with_suffix('.json')
  try:
   meta=json.loads(manifest.read_text(encoding='utf-8'));blob=binary.read_bytes()
   if meta.get('abi')==DETAIL_ABI and meta['sm']==sm and meta['source_sha256']==hashlib.sha256((root/'detail_effects.cu').read_bytes()).hexdigest() and meta['binary_sha256']==hashlib.sha256(blob).hexdigest():return blob,hashlib.sha256(blob).hexdigest(),f'cubin-sm{sm}'
  except (OSError,ValueError,KeyError):pass
 if backend=='native':raise UnsupportedDetail('No matching current native GPU module')
 try:
  raw=(root/'detail_effects.ptx').read_bytes();meta=json.loads((root/'detail_effects-build.json').read_text(encoding='utf-8'))
  if meta.get('abi')!=DETAIL_ABI or meta['source_sha256']!=hashlib.sha256((root/'detail_effects.cu').read_bytes()).hexdigest() or meta['ptx_sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('stale detailed PTX')
 except (OSError,ValueError,KeyError) as error:raise UnsupportedDetail('Detailed PTX build is missing or does not match the current source') from error
 blob=raw+b'\0';return blob,hashlib.sha256(blob).hexdigest(),'ptx'

def run(device,programs,script,enemies,base_stats,module_backend='auto',seeds=None):
 import random
 seeds=[0]*len(programs) if seeds is None else list(seeds)
 if len(seeds)!=len(programs) or any(type(seed) is not int or not 0<=seed<=4294967295 for seed in seeds):raise ValueError('Detailed GPU seed must be a uint32 integer')
 if not programs or len(programs)>2048 or len(script)>65536:raise ValueError('Detailed GPU bounds exceeded')
 if len(enemies)!=len(programs) or len(base_stats)!=len(programs):raise ValueError('Detailed batch input lengths differ')
 worlds=[]
 for p,enemy in zip(programs,enemies):
  if type(p.get('counter_single_body',False)) is not bool:raise ValueError('Invalid counter world constraint')
  w=p['world'] if 'world' in p else empty_world(int(enemy[2]) if len(enemy)>2 else 0)
  validate_world(w);worlds.append(w)
  bound_parts=[int(w[WA+1+i*ACTOR_WORDS+1]) for i in range(int(w[WA])) if w[WA+1+i*ACTOR_WORDS]==1]
  if sorted(bound_parts)!=list(range(int(enemy[2]) if len(enemy)>2 else 0)):raise ValueError('World bindings differ from the fixed part pool')
  if p.get('world',[0])[0] and (not any(r[1] in (4,15) for r in script) or sum(r[1]==5 for r in script)!=1):raise UnsupportedDetail('Live boss patterns require one complete squad or source schedule')
  if any(w[WB+i*BW]==7 for i in range(int(w[0]))) and any(r[1] in (3,4) for r in script):raise UnsupportedDetail('Autonomous summon target routing is not connected')
  if len(p['chars'])!=5 or len(p['effects'])>NE:raise ValueError('Invalid detailed program size')
  for i in range(int(w[0])):
   row=int(w[WB+i*BW+78])
   if row>=0:
    if row>=len(p['effects']):raise ValueError('Boss effect row exceeds definitions')
    q=p['effects'][row]
    if w[WB+i*BW]!=5 or q[1]!=0 or q[2]!=12 or q[4]!=4:raise ValueError('Boss effect row has incompatible semantics')
  boss_rows={int(w[WB+i*BW+78]) for i in range(int(w[0])) if w[WB+i*BW+78]>=0}
  damage_carriers=set()
  for index,r in enumerate(p['effects']):
   if len(r)!=EW or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in r) or not (0<=r[0]<5 or r[0]==5 and index in boss_rows) or int(r[2])!=r[2] or not 0<=r[2]<88:raise ValueError('Invalid compiled detailed effect')
   if int(r[14])!=r[14] or not 0<=r[14]<=3:raise ValueError('Invalid condition descriptor count')
   for j in range(int(r[14])):
    typ,name,threshold=r[15+j*3:18+j*3]
    if int(typ)!=typ or not 1<=typ<=43:raise ValueError('Invalid condition descriptor kind')
    if typ in (40,41) and (name!=0 or int(threshold)!=threshold or abs(threshold)>2**31-1):raise ValueError('Invalid world-count condition descriptor')
    if typ in (42,43) and (name!=0 or threshold!=0):raise ValueError('Invalid world-target condition descriptor')
   if r[2]==87 and r[1]==0:
    if r[258]!=0 or r[0]>=5 or r[4]!=4 or r[9]!=1 or not 0<r[295]<=1e12 or int(r[296])!=r[296] or not 0<=r[296]<6 or int(r[297])!=r[297] or not 0<=r[297]<2**28 or int(r[298])!=r[298] or not 1<=r[298]<2**31 or int(r[299])!=r[299] or not 1<=r[299]<=15 or r[300] not in (2,4,6) or r[301] not in (0,1) or r[302] not in (0,1) or r[303] not in (0,1):raise ValueError('Invalid target counter instruction')
   elif any(r[295:304]):raise ValueError('Target counter metadata on another instruction')
   if r[1]==0 and r[2] in NAMED_MAGNITUDE.values() and (r[0]>=5 or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid named magnitude reference')
   if r[2]==84 and (r[1]!=0 or r[258]!=0 or int(r[0])!=r[0] or r[0]>=5 or r[4] not in SNAPSHOT_HP_TARGETS):raise ValueError('Invalid maximum-HP snapshot instruction')
   if r[2] in (85,86) and (r[1]!=0 or r[258]!=0 or int(r[0])!=r[0] or r[0]>=5 or r[4] not in SNAPSHOT_HP_TARGETS or r[36]!=(0 if r[2]==85 else 1) or r[10]!=-1 or r[62]!=-1):raise ValueError('Invalid base-stat copy instruction')
   if r[245] not in (0,1):raise ValueError('Invalid revival persistence flag')
   if int(r[10])!=r[10] or not -4<=r[10]<NE or r[10]==-3 and r[258]!=0 or r[10]==-4 and (r[258]!=0 or r[1]!=0):raise ValueError('Invalid effect value scaling mode')
   if r[50] not in (0,1) or r[50] and not (r[258]==1 and r[1] in (6,7,27,31) or r[258]==0 and r[1]==0 and r[2]==70 and r[10]==-1):raise ValueError('Invalid maximum-HP value reference')
   if r[1]==31 and (r[258]!=1 or r[4]==4):raise ValueError('Invalid decoy healing instruction')
   if int(r[1])!=r[1] or not -1<=r[1]<=AMMO_EQUIVALENT:raise ValueError('Invalid detailed instruction kind')
   if int(r[213])!=r[213] or r[213]<0 or int(r[213])&TOGGLE_FLAG and (r[1]!=2 or r[258]!=3 or r[35]!=1):raise ValueError('Invalid weapon-mode toggle flag')
   if r[1]==AMMO_EQUIVALENT:
    extra_ammo_count(r[6])
    if r[258]!=1 or r[4]!=0 or r[10]!=-1:raise ValueError('Invalid ammo-equivalent instruction')
   if r[1]==36 and (r[258]!=2 or r[4]!=4 or r[10]!=-1 or r[59]!=0 or r[51]!=0 or r[136]!=-1 or r[39]!=0):raise ValueError('Invalid captured parent damage instruction')
   if r[1]==35:
    if r[258]!=1 or r[4]!=0 or int(r[0])!=r[0] or r[0]>=5 or int(r[304])!=r[304] or not 0<=r[304]<NE or int(r[305])!=r[305] or not 1<=r[305]<=MAX_SLOTS or r[137] not in (0,1):raise ValueError('Invalid periodic source instruction')
    source_specification(dict(type='instant',stat='periodic_source_refresh',periodic_source=dict(name='validated',slots=r[308:308+int(r[305])],base_interval=r[306],population_reduction_pct=r[307])))
    if any(r[308+int(r[305]):340]):raise ValueError('Nonzero unused periodic source slots')
   elif any(r[304:340]):raise ValueError('Periodic source metadata on another instruction')
   if r[340]>0:
    if r[1]!=3 or not int(r[39])&128 or r[10]!=-2 or r[59]<=0 or r[4]!=4 or r[51]!=0 or r[136]!=-1 or not MIN_GAP<=r[340]<=60 or int(r[341])!=r[341] or not -1<=r[341]<=MAX_STEPS or int(r[342])!=r[342] or not (0<=r[342]<=MAX_STEPS or 4096<=r[342]<4096+NE) or not 0<=r[343]<=3600 or int(r[9])!=r[9] or not (r[9]==-1 or 1<=r[9]<=MAX_STEPS):raise ValueError('Invalid staged periodic instruction')
   elif any(r[340:344]):raise ValueError('Staged metadata without an application clock')
   if r[1]==34 and (r[258]!=2 or int(r[0])!=r[0] or r[0]>=5 or r[4]!=4 or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid damage discharge reference')
   if r[1]==0 and r[2] in (81,82,83):
    if r[258]!=0 or int(r[0])!=r[0] or r[0]>=5 or int(r[3])!=r[3] or not 0<=r[3]<NE or r[35] not in (0,1):raise ValueError('Invalid damage accumulation carrier')
    if r[2] in (81,82) and r[35]>0:
     if r[3] in damage_carriers:raise ValueError('Ambiguous damage accumulation aliases')
     damage_carriers.add(r[3])
   if r[1]==0 and r[2]==83 and (r[212] not in (0,1) or r[139] not in (0,1) or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid damage accumulation rate')
   if r[1]==33:
    if r[258]!=1 or r[0]>=5 or r[36] not in (1,2,3):raise ValueError('Invalid forced skill slot')
    for word,bits in enumerate(r[B3_MASK:B3_MASK+MASK_WORDS]):
     if int(bits)!=bits or not 0<=bits<=4294967295:raise ValueError('Invalid forced skill definition mask')
     for bit in range(32):
      selected=word*32+bit
      if int(bits)&(1<<bit) and (selected>=len(p['effects']) or p['effects'][selected][0]!=r[0] or p['effects'][selected][1]<0 or selected==index):raise ValueError('Invalid forced skill definition reference')
   if r[1]==32 and (r[258]!=1 or r[0]>=5 or r[4]==4 or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid healing discharge instruction')
   if r[1]==0 and r[2] in (76,77) and (r[258]!=0 or r[0]>=5):raise ValueError('Invalid healing accumulation instruction')
   if r[1]==0 and r[2]==77 and (r[212] not in (0,1) or int(r[36])!=r[36] or not 0<=r[36]<NE):raise ValueError('Invalid healing capacity reference')
   if r[4]==25 and (int(r[5])!=r[5] or not 0<=r[5]<=5):raise ValueError('Invalid broken-cover target count')
   if r[53] not in (0,1,2) or not 0<=r[54]<=1000000 or (r[53]>0 and r[1]!=3) or (r[53]==0 and r[54]!=0):raise ValueError('Invalid HP damage basis')
   if not 0<=r[294]<=1e30 or r[294]>0 and r[1] not in (10,11):raise ValueError('Invalid resource-consumption minimum')
   if r[55] not in (0,1) or r[55]>0 and (r[1]!=0 or r[2]!=18):raise ValueError('Invalid exclusive ammo reduction')
   if r[51] not in (0,1,2) or r[51]>0 and (r[1]!=3 or r[4]!=4):raise ValueError('Invalid deferred attack mode')
   if int(r[52])!=r[52] or (not (-256<=r[52]<=256 or 4096<=r[52]<4096+NE) if r[51]==2 else not 0<=r[52]<=4096) or r[52]!=0 and (r[1]!=3 or r[4]!=4):raise ValueError('Invalid named attack target count')
   if r[4] in (22,23,24):
    if int(r[5])!=r[5] or not (0 if r[4]==24 else 1)<=r[5]<=5:raise ValueError('Invalid survival target count')
    if r[4] in (23,24) and (int(r[48])!=r[48] or not 0<=r[48]<=31):raise ValueError('Invalid survival target pool')
    if r[4]==24 and r[141]>0:
     if r[141]!=1 or int(r[140])!=r[140] or not 0<=r[140]<=32767:raise ValueError('Invalid survival target order')
     raw=int(r[140]);seen=set()
     while raw:
      digit=raw&7;raw>>=3
      if not 1<=digit<=5 or digit in seen:raise ValueError('Invalid survival target recipient')
      seen.add(digit)
   if r[1]==29 and (r[258]!=1 or r[6]<=0):raise ValueError('Invalid revival instruction')
   if r[1]==30 and (r[258]!=1 or r[6]==0):raise ValueError('Invalid cover revival instruction')
   if index in boss_rows and (r[0]!=5 or r[14]!=0 or r[10]!=-1 or r[7]!=-1 or r[9]!=1 or r[59]!=0 or r[62]!=-1 or r[144]!=1 or r[TD]!=15):raise ValueError('Invalid boss-owned inactive definition')
   if int(r[268])!=r[268] or not 0<=r[268]<=5:raise ValueError('Invalid team listener source owner')
   if int(r[269])!=r[269] or not 0<=r[269]<=NE:raise ValueError('Invalid team listener shared budget')
   if r[1]==0 and r[2] in (18,20,37) and (int(r[45])!=r[45] or not 0<=r[45]<NE):raise ValueError('Invalid ammo quantization group' if r[2]==18 else 'Invalid charge quantization group')
   if r[4]==17:
    first,count=r[5],r[48]
    if int(first)!=first or int(count)!=count or first<0 or count<0 or first+count>len(p['effects']) or any(node[1]!=-1 or node[4]==17 for node in p['effects'][int(first):int(first+count)]):raise ValueError('Invalid compiled target list')
   if int(r[144])!=r[144] or not 0<=r[144]<=NT:raise ValueError('Invalid detailed trigger descriptor count')
   for a in range(int(r[144])):
    d=r[TD+a*TS:TD+(a+1)*TS]
    if d[0]==49 and (d[3]<0 or d[2]!=1 or d[6]!=1):raise ValueError('Invalid named skill-hit descriptor')
    if d[0]==50 and (d[3]<0 or d[2]!=0 or d[1]!=0 or d[6]!=-1):raise ValueError('Invalid damage accumulation-full descriptor')
    if d[0]==62 and (int(d[1])!=d[1] or not 1<=d[1]<=MAX_TARGETS or d[2]!=0 or d[3]!=-1 or d[6]!=-1):raise ValueError('Invalid simultaneous-target descriptor')
    if d[6]<=-11 and (d[6] not in (-11,-12,-13,-14) or d[3]<0 or d[0]!=(48 if d[6]==-11 else 31)):raise ValueError('Invalid HP transition descriptor')
    if any(int(v)!=v for i,v in enumerate(d) if not (i==1 and d[0]==6 or i==4 and (d[0]==39 or d[6]<=-11))) or d[0]==6 and d[1]<=0 or not 0<=d[0]<128 or d[2] not in (0,1,2,3) or not -1<=d[3]<NE or d[5] not in (0,1):raise ValueError('Invalid detailed trigger descriptor')
    if (d[2]>0 or d[0] in (7,8,27,30)) and d[1]<1 and not (d[6]==1 and d[0] in (7,8,11,12,20,22,23,40,49)):raise ValueError('Invalid detailed trigger threshold')
  counter_names={(int(r[0]),int(r[3])) for r in p['effects'] if r[1]==0 and r[2]==87}
  validate_gpu_fields(p['effects'],any(w[WB+i*BW]==7 for i in range(int(w[0]))))
  if any(r[1] in (16,17,18,19,20,21) and (int(r[0]),int(r[36])) in counter_names for r in p['effects']):raise ValueError('Counter progress is separate from named buff stack manipulation')
 for en in enemies:
  if len(en) not in (2,EN) or not all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in en):raise ValueError('Invalid detailed enemy')
  if len(en)==EN:
   count=en[2]
   if int(count)!=count or not 0<=count<=32 or en[67] not in (0,1):raise ValueError('Invalid detailed parts world')
   if any(en[3+i*2]>1e15 or int(en[4+i*2])!=en[4+i*2] or not 1<=en[4+i*2]<=5 for i in range(int(count))):raise ValueError('Invalid detailed part target')
 if any(p.get('counter_single_body') and len(en)==EN and en[2]>0 for p,en in zip(programs,enemies)):raise UnsupportedDetail('Single-body capture credit is not defined for parts')
 for p in programs:validate_target_predicate_policies(p['effects'])
 n=len(programs);nq=sum(row[1]==2 for row in script)
 if any(len(en)==EN and en[2]>0 for en in enemies) and not any(row[1]==4 for row in script):
  if any(row[1]==3 for row in script) or any(row[1]==3 for program in programs for row in program['effects']):raise UnsupportedDetail('Live-part combat requires the autonomous squad loop; isolated authored part stimuli remain available')
 if not nq or sorted(int(row[5]) for row in script if row[1]==2)!=list(range(nq)):raise ValueError('Query indices must be contiguous')
 if any(len(row)!=8 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in row) or not 0<=row[0]<=180 or row[1] not in (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,AIM_COMMAND) or not 0<=row[3]<5 or row[1]==0 and (not 0<=row[2]<128 or int(row[2])!=row[2]) for row in script):raise ValueError('Invalid event program')
 initial_aims={int(row[3]) for row in script if row[0]==0 and row[1]==AIM_COMMAND}
 for p in programs:
  w=p.get('world') or empty_world();required=required_aim_owners(p['effects'],any(w[WB+i*BW]==7 for i in range(int(w[0]))))
  if not required<=initial_aims:raise UnsupportedDetail('Periodic target selection requires an explicit time0 aim input')
 from impact_specs import decode_command
 for row in script:
  if row[1] in (16,AIM_COMMAND) or row[1]==2 and row[2]==135:
   from impact_specs import ActorHandle
   if any(int(row[k])!=row[k] for k in ((2,3,4,5,7) if row[1]==16 else (2,3,4,5,6,7))):raise ValueError('Invalid enemy-field command descriptor')
   if row[1]==16:
    if row[2] not in EVENT.values() or not 0<=row[6]<=1 or row[7] not in (0,1):raise ValueError('Invalid target-aware notification')
    handle=ActorHandle(int(row[4])%8,int(row[4])//8,int(row[5]))
   elif row[1]==AIM_COMMAND:
    if row[2]!=0 or row[6]!=0 or row[7]!=0:raise ValueError('Invalid periodic aim input')
    handle=ActorHandle(int(row[4])%8,int(row[4])//8,int(row[5]))
   else:
    if not 0<=row[6]<63:raise ValueError('Invalid enemy-field stat query')
    handle=ActorHandle(int(row[4])%8,int(row[4])//8,int(row[7]))
   if int(handle.kind) not in (0,1,5):raise ValueError('Enemy-field actor policy is not connected')
  if row[1] in (8,14):
   for p in programs:decode_command(row,[c['name'] for c in p['chars']])
   if row[1]==14 and (int(row[4])%8!=5 or (int(row[2])//4)%4!=2):raise ValueError('Source landing requires a damaging add handle')
  if row[1]==9:
   from impact_specs import ActorHandle
   if any(int(row[k])!=row[k] for k in (2,4,5)) or row[3]!=0 or row[6]!=0 or row[7]!=0:raise ValueError('Invalid authored target death')
   ActorHandle(int(row[2]),int(row[4]),int(row[5]))
 if any(row[1]==0 and row[2]==58 for row in script):raise ValueError('Cannot author private target-counter completion events')
 if any(row[1]==0 and row[2] in (52,53,54) for row in script):raise ValueError('Cannot author private HP continuation events')
 if any(row[1]==0 and row[2] in (55,56) for row in script):raise ValueError('Cannot author private skill continuation events')
 if any(row[1]==0 and row[2]==61 for row in script):raise ValueError('Cannot author private staged damage continuations')
 if any(row[1]==0 and row[2]==62 for row in script):raise ValueError('Simultaneous-target notifications require a sealed attack group')
 if any(row[1] in (10,11,12,13) and (int(row[3])!=row[3] or int(row[4])!=row[4] or not 1<=row[4]<2**24 or row[5]!=-1 or int(row[6])!=row[6] or not (0 if row[1]==10 else 1)<=row[6]<2**31 or row[7]!=0 or row[1]==10 and (int(row[2])!=row[2] or not 1<=row[2]<=63) or row[1]!=10 and row[2]!=0) for row in script):raise ValueError('Invalid authored attack-group boundary')
 if any(row[1]==2 and row[2] in (131,132) and (int(row[3])!=row[3] or int(row[4])!=row[4] or not 1<=row[4]<2**24 or int(row[6])!=row[6] or (row[6]!=0 if row[2]==131 else not 1<=row[6]<2**31) or int(row[7])!=row[7] or not 0<=row[7]<10) for row in script):raise ValueError('Invalid attack-group query')
 if any(row[1]==2 and row[2]==133 and (int(row[4])!=row[4] or row[4]<0 or int(row[4])%8>5 or int(row[4])//8>=2**28 or int(row[6])!=row[6] or not 0<=row[6]<2**31 or row[7]!=0) for row in script):raise ValueError('Invalid world-actor query')
 if any(row[1]==2 and row[2]==134 and (int(row[4])!=row[4] or not 0<=row[4]<128 or row[6]!=0 or row[7]!=0) for row in script):raise ValueError('Invalid summon-source query')
 if any(row[1]==15 and any(row[k]!=0 for k in (2,3,4,6,7)) for row in script):raise ValueError('Invalid world-source frame')
 source_frames=[row[0] for row in script if row[1]==15]
 if source_frames and (source_frames[0]!=0 or any(row[1]==4 for row in script)):raise ValueError('Source frames require time0 and cannot mix with autonomous squad frames')
 if any(row[1]==4 for row in script) and any(d[TD+i*TS]==62 for p in programs for d in p['effects'] for i in range(int(d[144]))):raise UnsupportedDetail('Autonomous simultaneous-target producers are not connected')
 if any(row[1]==0 and row[2]==49 and (int(row[4])!=row[4] or not 0<=row[4]<NE) for row in script):raise ValueError('Invalid authored named skill-hit reference')
 if any(row[1]==0 and row[2]==50 and (int(row[4])!=row[4] or not 0<=row[4]<NE) for row in script):raise ValueError('Invalid authored accumulation-full reference')
 if any(row[1]==6 and (row[2] not in (0,1,2) or int(row[2])!=row[2] or row[6]<0 or row[7] not in (0,1)) for row in script):raise ValueError('Invalid authored shield operation')
 if any(row[1]==4 and (row[2] not in (0,1) or row[2]==1 and (row[6]<0 or row[7] not in (0,1))) for row in script):raise ValueError('Invalid mid-frame shield stimulus')
 if any(row[1]==2 and row[2]==111 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid shield state query')
 if any(row[1]==2 and row[2]==121 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid decoy state query')
 if any(row[1]==2 and row[2]==122 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid healing-storage query')
 if any(row[1]==2 and row[2]==123 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid healing-charge query')
 if any(row[1]==2 and row[2]==112 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid immunity pool query')
 if any(row[1]==2 and row[2]==115 and (int(row[4])!=row[4] or not 0<=row[4]<BLOG) for row in script):raise ValueError('Invalid boss log query')
 if any(row[1]==2 and row[2]==117 and (int(row[4])!=row[4] or not 0<=row[4]<ILOG) for row in script):raise ValueError('Invalid incoming log query')
 if any(row[1]==2 and row[2]==120 and (int(row[4])!=row[4] or not 0<=row[4]<1024) for row in script):raise ValueError('Invalid HP event log query')
 if any(row[1]==2 and row[2] in (110,118) and (int(row[4])!=row[4] or not 0<=row[4]<14) for row in script):raise ValueError('Invalid random state page')
 if any(row[1]==2 and row[2]==113 and row[4] not in (0,1) for row in script):raise ValueError('Invalid optimal range query')
 if any(row[1]==7 and (row[2] not in (0,1,2) or int(row[4])!=row[4] or not 0<=row[4]<=5 or row[6]<0 or int(row[7])!=row[7] or not -1<=row[7]<32) for row in script):raise ValueError('Invalid authored part stimulus')
 if any(row[1]==2 and row[2]==114 and (int(row[4])!=row[4] or not 0<=row[4]<32) for row in script):raise ValueError('Invalid part state query')
 if any(row[1]==2 and row[2]==124 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid damage accumulation query')
 if any(row[1]==2 and row[2]==125 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid base-stat copy query')
 if any(row[1]==2 and row[2]==130 and (int(row[4])!=row[4] or not 0<=row[4]<NE or any(row[4]>=len(p['effects']) or p['effects'][int(row[4])][340]<=0 for p in programs)) for row in script):raise ValueError('Invalid staged carrier query')
 if any(row[1]==2 and row[2]==129 and (int(row[4])!=row[4] or not 0<=row[4]<NE) for row in script):raise ValueError('Invalid periodic source query')
 if any(row[1]==2 and row[2]==127 and (int(row[4])!=row[4] or not -1<=row[4]<NE) for row in script):raise ValueError('Invalid target-counter query')
 if any(row[1]==2 and row[2]==128 and (row[0]!=0 or int(row[4])!=row[4] or not 0<=row[4]<128 or int(row[6])!=row[6] or not 0<=row[6]<6 or row[7]!=0) for row in script):raise ValueError('Event index inspection requires time0, event0..127 and page0..5')
 if any(b[0]<a[0] for a,b in zip(script,script[1:])):raise ValueError('Event times must be monotonic')
 if any(row[1]==2 and row[2]==106 and (int(row[4])!=row[4] or any(not 0<=row[4]<len(p['effects']) for p in programs)) for row in script):raise ValueError('Invalid probability accumulator query')
 if len(programs)*nq*OW*8>256*1024*1024:raise ValueError('Detailed trace exceeds 256 MiB; use smaller batches')
 for p in programs:
  for who in ({0,1,2,3,4} if any(row[1]==4 for row in script) else {int(row[3]) for row in script if row[1]==3}):
   from calculator.timeline import CharState
   char=p['chars'][who];st=CharState(char,1,None)
   if st.fire_mode not in ('auto','auto_warmup','charge') or not (1<=st.pellets<=64 and 1<=st.muzzles<=8 and 1<=st.clip_count<=32):raise UnsupportedDetail('Autonomous weapon mechanics exceed verified bounds')
 import hashlib
 init_started=time.perf_counter();blob,digest,module_format=module_image(device,module_backend)
 cached=getattr(device,'_detail_cached_module',None)
 if cached and cached[:2]==(digest,device.ctx.value):module,fn,state_bytes=cached[2:]
 else:
  if cached and cached[1]==device.ctx.value:
   unload=device.lib.cuModuleUnload;unload.argtypes=[C.c_void_p];unload.restype=C.c_int;device.call('cuModuleUnload',cached[2])
  module=C.c_void_p();fn=C.c_void_p();device.call('cuModuleLoadData',C.byref(module),C.cast(C.c_char_p(blob),C.c_void_p));device.call('cuModuleGetFunction',C.byref(fn),module,DETAIL_ABI.encode())
  get_global=device.lib.cuModuleGetGlobal_v2
  get_global.argtypes=[C.POINTER(C.c_uint64),C.POINTER(C.c_size_t),C.c_void_p,C.c_char_p];get_global.restype=C.c_int
  symbol=C.c_uint64();symbol_size=C.c_size_t();layout=C.c_uint()
  device.call('cuModuleGetGlobal_v2',C.byref(symbol),C.byref(symbol_size),module,b'detail_state_bytes_v42')
  if symbol_size.value!=C.sizeof(layout):raise RuntimeError('Invalid GPU detail workspace layout symbol')
  device.call('cuMemcpyDtoH_v2',C.cast(C.byref(layout),C.c_void_p),symbol,C.sizeof(layout))
  state_bytes=layout.value
  if not 1024<=state_bytes<=2*1024*1024:raise RuntimeError('Invalid GPU detail workspace size')
  shape=(C.c_uint*8)()
  device.call('cuModuleGetGlobal_v2',C.byref(symbol),C.byref(symbol_size),module,b'detail_boss_shape_v42')
  if symbol_size.value!=C.sizeof(shape):raise RuntimeError('Invalid GPU boss schema symbol')
  device.call('cuMemcpyDtoH_v2',C.cast(shape,C.c_void_p),symbol,C.sizeof(shape))
  if list(shape)!=[BP,BL,BW,BH,BLOG,BQ,WB,WP]:raise UnsupportedDetail('GPU boss bytecode layout differs from the host')
  from event_index_specs import EVENT_COUNT,MAX_DEFINITIONS,MAX_TRIGGERS,TRIGGER_BASE,TRIGGER_WIDTH
  plan_shape=(C.c_uint*5)()
  device.call('cuModuleGetGlobal_v2',C.byref(symbol),C.byref(symbol_size),module,b'detail_event_shape_v55')
  if symbol_size.value!=C.sizeof(plan_shape):raise RuntimeError('Invalid GPU event index schema symbol')
  device.call('cuMemcpyDtoH_v2',C.cast(plan_shape,C.c_void_p),symbol,C.sizeof(plan_shape))
  if list(plan_shape)!=[EVENT_COUNT,MAX_DEFINITIONS,MAX_TRIGGERS,TRIGGER_BASE,TRIGGER_WIDTH]:raise UnsupportedDetail('GPU event index layout differs from the host')
  source_shape=(C.c_uint*4)()
  device.call('cuModuleGetGlobal_v2',C.byref(symbol),C.byref(symbol_size),module,b'detail_source_shape_v57')
  if symbol_size.value!=C.sizeof(source_shape):raise RuntimeError('Invalid GPU periodic source schema symbol')
  device.call('cuMemcpyDtoH_v2',C.cast(source_shape,C.c_void_p),symbol,C.sizeof(source_shape))
  if list(source_shape)!=[MAX_SOURCES,MAX_SLOTS,EW,NE]:raise UnsupportedDetail('GPU periodic source layout differs from the host')
  device._detail_cached_module=(digest,device.ctx.value,module,fn,state_bytes)
 initialization_ms=round((time.perf_counter()-init_started)*1000,3)
 limit=device.lib.cuCtxSetLimit;limit.argtypes=[C.c_int,C.c_size_t];limit.restype=C.c_int
 if limit(0,131072):raise RuntimeError('CUDA detail stack limit setup failed')
 start=len(device.buffers);started=time.perf_counter()
 try:
  inputs=[array.array('d',(v for p,bs in zip(programs,base_stats) for v in weapon_rows(p['chars'],bs))),array.array('d',(v for p in programs for row in p['effects']+[[0]*EW]*(NE-len(p['effects'])) for v in row)),array.array('i',(len(p['effects']) for p in programs)),array.array('d',(v for enemy in enemies for v in list(enemy)+[0]*(EN-len(enemy)))),array.array('d',(v for w in worlds for v in w)),array.array('d',(v for row in script for v in row)),array.array('I',(v for seed in seeds for rng_seed in (seed,0) for v in random.Random(rng_seed).getstate()[1]))]
  queries=array.array('d',[0])*(n*nq*OW);totals=array.array('d',[0])*(n*5);status=array.array('i',[0])*n
  packed_at=time.perf_counter()
  # Each squad owns one State. The kernel initializes all live fields.
  workspace=C.c_uint64();device.call('cuMemAlloc_v2',C.byref(workspace),n*state_bytes);device.buffers.append(workspace)
  ptrs=[device.upload(x) for x in inputs];outptrs=[device.upload(x) for x in (queries,totals,status)]
  args=[*ptrs,C.c_int(len(script)),C.c_int(nq),C.c_int(n),*outptrs,workspace,C.c_int(sys.version_info>=(3,12))];params=(C.c_void_p*len(args))(*(C.cast(C.byref(x),C.c_void_p) for x in args))
  uploaded_at=time.perf_counter()
  # Each autonomous squad has a large, divergent device call graph. Giving it
  # its own block avoids mixed-squad warp execution faults seen on SM86 and
  # lets independent squads occupy separate multiprocessors.
  from cuda_timing import KernelTimer
  with KernelTimer(device) as timer:
   timer.start();device.call('cuLaunchKernel',fn,n,1,1,1,1,1,0,None,params,None);timer.stop();device.call('cuCtxSynchronize')
   kernel_ms=timer.elapsed()
  executed_at=time.perf_counter()
  for a,ptr in zip((queries,totals,status),outptrs):device.call('cuMemcpyDtoH_v2',C.cast((C.c_char*(len(a)*a.itemsize)).from_buffer(a),C.c_void_p),ptr,len(a)*a.itemsize)
  if any(status):raise RuntimeError('GPU detail capacity or target cache exceeded; result rejected: '+str(list(status)))
  downloaded_at=time.perf_counter()
  decoded_queries=[[list(queries[(i*nq+j)*OW:(i*nq+j+1)*OW]) for j in range(nq)] for i in range(n)]
  decoded_totals=[list(totals[i*5:i*5+5]) for i in range(n)];decoded_at=time.perf_counter()
  timings=dict(scope='batch',packing_host=(packed_at-started)*1000,allocation_upload_host=(uploaded_at-packed_at)*1000,
    kernel_cuda=kernel_ms,kernel_launch_sync_host=(executed_at-uploaded_at)*1000,
    readback_host=(downloaded_at-executed_at)*1000,decode_host=(decoded_at-downloaded_at)*1000)
  timings={key:round(value,3) if isinstance(value,float) else value for key,value in timings.items()}
  return {'queries':decoded_queries,'totals':decoded_totals,'backend':'cuda','detailed_subsystem':True,'full_simulation_verified':False,'initialization_ms':initialization_ms,'module_backend':module_format,'workspace_bytes':n*state_bytes,'elapsed_ms':round((decoded_at-started)*1000,3),'timings_ms':timings}
 finally:
  for ptr in device.buffers[start:]:
   # After a fatal device error, preserve the original error; the caller discards the context.
   device.lib.cuMemFree_v2(ptr)
  del device.buffers[start:]
  # Cached module is released with its owning CUDA context.



def compile_controls(char,st,names,config):
 """Compile authored controls and constants, never CPU-selected control times."""
 control=char.get('control') or {}
 if any(v for k,v in control.items() if k not in ('click','hold','tap_fire','sequence','priority','burst')):raise UnsupportedDetail('cover/reload/aim control is not yet implemented')
 if len(st._click_sched)>8 or len(st._ctrl_seq)>8:raise UnsupportedDetail('control schedule exceeds eight entries')
 entries=[]
 for entry in st._click_sched:
  if entry.get('anchor') is not None:raise UnsupportedDetail('anchored click schedule is not yet implemented')
  row=[0.0]*12;row[0]={'auto':0,'tap':1,'hold':2,'hold_until_close':3,'hold_judge':4}[entry['mode']]
  row[1]={'always':0,'burst_charge':1,'burst_chain':2,'own_full_burst':3,'after_own_fb':4}[entry['window']];row[2]=entry['_prio'];row[3]=entry.get('lead',.1)
  if entry['mode']=='tap':
   timing=entry['_timing'];row[4:9]=[timing['hold'],timing['charge'],timing['release'],timing['post'],timing['full_charge_interval']]
  gate=entry.get('gate')
  if gate:row[9]=int(gate['burst_stage']);row[10]=1<<names.index(gate['burst_user']) if gate['burst_user'] in names else 0
  entries.append(row)
 sequences=[]
 for action in st._ctrl_seq:
  if action.get('action')!='hold':raise UnsupportedDetail('cover sequence is not yet implemented')
  sequences.append([float(action.get('t',0)),float(action['until']) if action.get('until') is not None else -1])
 char['_detail_controls']=entries;char['_detail_sequences']=sequences
 char['_detail_control_mode']={'solo':0,'warn':1,'strict':2}[config.get('control_mode','solo')]

def compile_full(prepared,stats,body,policy,requested_policy):
 """Compile validated owned/growth data. No CPU simulation or event trace is used."""
 import copy
 from calculator.buff_manager import BuffManager
 from calculator.timeline import CharState,DEFAULT_CONFIG,DEFAULT_ENEMY,_resolve_cameras
 from gpu_combat import ELEMENT
 config={**DEFAULT_CONFIG,**prepared.config};enemy={**DEFAULT_ENEMY,**prepared.enemy};chars=copy.deepcopy(prepared.squad)
 if config.get('rng_mode','expected')!='expected':raise UnsupportedDetail('Detailed GPU probabilities require expected RNG mode')
 unsupported=[]
 if config.get('sequence'):unsupported.append({'reason':'squad control sequences are not yet implemented'})
 for k in ('burst_sequence','no_burst_char','max_burst_count'):
  if config.get(k) is not None:unsupported.append({'effect':k,'reason':'special burst control'})
 if config.get('burst_gauge_mode','fixed') not in ('fixed','accumulate'):unsupported.append({'reason':'unknown burst gauge mode'})
 if config.get('first_burst_time',3)!=3 or config.get('burst_switch_delay',.1)!=.1:unsupported.append({'reason':'nondefault burst clock'})
 parts=read_parts(body.get('enemy',{}).get('parts',[]))
 if enemy.get('coord') is not None:raise UnsupportedDetail('Coordinate boss geometry is not yet implemented')
 bs={c['name']:stats(c) for c in chars}
 names=[c['name'] for c in chars]
 try:camera=_resolve_cameras(chars,config)
 except ValueError as e:raise UnsupportedDetail(str(e))
 for c in chars:
  st=CharState(c,bs[c['name']]['atk'],enemy['code']);w=st.weapon;c['_weapon']=copy.deepcopy(w)
  try:compile_controls(c,st,names,config)
  except (UnsupportedDetail,KeyError,ValueError) as e:unsupported.append({'character':c['name'],'reason':str(e)})
  c['_detail_gauge_mode']=int(config.get('burst_gauge_mode','fixed')=='accumulate')
  c['_detail_camera']=sum(1<<i for i,n in enumerate(names) if n in camera)
  if st.reload_cancel_on_full:unsupported.append({'character':c['name'],'reason':'manual ammo reload cancellation not yet implemented'})
  stage=str(c.get('burst_stage') or w.get('burst_stage'))
  if stage not in ('1','2','3','A'):unsupported.append({'character':c['name'],'reason':'unknown burst stage'})
  else:c['_detail_stage']=4 if stage=='A' else int(stage)
  c['_detail_explicit_stage']=int(c.get('burst_stage') is not None)
  c['_detail_red_hood']=int(c['name']=='레드 후드')
  c['_detail_innate_stage']=4 if str(w.get('burst_stage'))=='A' else int(w.get('burst_stage') or 0)
  c['_detail_reenter_delay']=float(config.get('burst_reenter_delay',.5))
  if not math.isfinite(c['_detail_reenter_delay']) or c['_detail_reenter_delay']<0:unsupported.append({'reason':'invalid burst reentry delay'})
  pattern=config.get('burst_pattern',{}).get(c['name'])
  if pattern is not None:
   if isinstance(pattern,str) and re.fullmatch(r'every:[1-9][0-9]*',pattern):c['_detail_pattern']=int(pattern.split(':')[1])
   elif isinstance(pattern,list) and all(type(cycle) is int and 1<=cycle<=160 for cycle in pattern):
    c['_detail_pattern']=-1;c['_detail_pattern_cycles']=list(pattern)
   else:unsupported.append({'character':c['name'],'reason':'burst pattern requires every:N or a list of cycles 1..160'})
  c['_detail_delay']=config.get('burst_delay',{}).get(c['name'],0)
  c['_detail_wait']=((c.get('control') or {}).get('burst') or {}).get('wait_own_cooldown',0) or 0
  lo,hi=w.get('optimal_range',[0,0]);distance=enemy.get('distance')
  c['_optimal']=lo<=distance<=hi if distance is not None else st.weapon_type in enemy.get('optimal_range_weapons',[])
  c['_element_match']=ELEMENT.get(w.get('element_code'))==enemy['code']
  c['_detail_has_parts']=bool(enemy.get('has_parts',False))
  c['_detail_enemy_code']=enemy.get('code','')
  c['_detail_enemy_core_px']=enemy.get('core_px',0)
  from calculator.buff_manager import in_optimal_range,optimal_range_of
  lo,hi=optimal_range_of(c['name'],st.weapon_type)
  c['_detail_range']=[lo,hi,distance]
  c['_optimal']=in_optimal_range(enemy,c['name'],st.weapon_type,{})
  c['_detail_mode_optimal']={weapon:in_optimal_range(enemy,c['name'],weapon,{}) for weapon in ('AR','SMG','SG','SR','RL','MG')}
  if st.fire_mode not in ('auto','auto_warmup','charge') or not (1<=st.pellets<=64 and 1<=st.muzzles<=8 and 1<=st.clip_count<=32):unsupported.append({'character':c['name'],'reason':'weapon mode or pellet/muzzle/clip count exceeds GPU bounds'})
 if unsupported:raise UnsupportedDetail(unsupported)
 for c in chars:
  stage=c['_detail_stage'];peers=[x for x in chars if x['_detail_stage']==stage]
  c['_detail_burst_candidate']=stage==3 or c is peers[0] or any(x.get('_detail_pattern') or x.get('burst_stage') is not None for x in peers)
 bm=BuffManager(chars,state={'base_stats':bs,'enemy':enemy,'full_burst':False,'rng_acc':{}})
 # B3 bonus damage is deferred by the CPU engine; never accept it as immediate damage.
 extra,boss_indices=boss_effects(enemy,names[0])
 effects=list(bm._effects)+extra
 program=compile_effects(chars,effects,enemy_fields=True)
 if any(r[TD+i*TS]==62 for r in program['effects'] for i in range(int(r[144]))):raise UnsupportedDetail('Autonomous simultaneous-target producers are not connected')
 if program.get('counter_single_body') and parts:raise UnsupportedDetail('Single-body capture credit is not defined for parts')
 for q in program['effects']:
  if q[1]==0 and q[2]==87 and not (q[296]==0 and q[297]==0 and q[298]==1 or q[296]==1 and 0<=q[297]<len(parts) and q[298]==1):raise UnsupportedDetail('Target counter actor is outside the currently supported body/live-part world')
 program['cover_base_hp']=float(config.get('cover_hp',2000000))
 if any(p.get('kind')=='attack' for p in body.get('enemy',{}).get('patterns',[])):
  gaps=[{'character':owner,'effect':eff.get('name','?'),'reason':'Incoming model gap: '+eff.get('stat','')} for eff,owner in bm._effects if eff.get('stat') in ('damage_reduction_pct','force_move','cover_def_pct')]
  if gaps:raise UnsupportedDetail(gaps)
 program['boss_effect_rows']={pid:program['source_rows'][len(bm._effects)+i][0] for pid,i in boss_indices.items()}
 # The fixed-value boss definitions have a separate caster identity. Using a
 # Nikke here would let that Nikke's self-stack references read enemy states.
 for row in program['boss_effect_rows'].values():program['effects'][row][0]=5
 for i,(eff,owner) in enumerate(bm._effects):
  if eff.get('type')=='damage' and (eff.get('stat')=='bonus_damage' or eff.get('land_in_full_burst') is True) and 'burst_cast' in eff['trigger']['timing'] and str(next(c for c in chars if c['name']==owner)['_weapon'].get('burst_stage'))=='3':
   later={e.get('name') for e,n in bm._effects[i+1:] if n==owner and e.get('type')=='buff' and 'burst_cast' in e['trigger']['timing']}
   for row_index in program['source_rows'][i]:
    row=program['effects'][row_index];row[51]=1 if eff.get('stat')=='bonus_damage' else 2
    for j,(e,n) in enumerate(bm._effects):
     if n==owner and e.get('name') in later:
      for bound_index in program['source_rows'][j]:row[B3_MASK+bound_index//32]=int(row[B3_MASK+bound_index//32])|1<<(bound_index%32)
 try:program['world'],patterns=compile_world(enemy,parts,body,program)
 except (UnsupportedBoss,ValueError) as error:raise UnsupportedDetail(str(error)) from error
 has_add_sources=any(p['kind']=='summon' for p in patterns)
 if has_add_sources:raise UnsupportedDetail('Autonomous summon target routing is not connected')
 specialize_static_counts(program['effects'],has_add_sources=has_add_sources)
 specialize_static_fields(program['effects'],has_add_sources=has_add_sources)
 # Burst-recipient targets are sampled by the GPU and stored in independent
 # active slots. Definitions stay shared across recipient sets and event times.
 # Charge-cover automatic reload is executed by the GPU state machine.
 return {'program':program,'base_stats':bs,'enemy':packed_enemy(enemy,parts),'parts':parts,'patterns':patterns, 'prepared':prepared,'policy':policy,'requested_policy':requested_policy,'body':body}


def incoming_source_label(program,patterns,encoded):
 if encoded==0:return ''
 if not isinstance(encoded,(int,float)) or not math.isfinite(encoded) or int(encoded)!=encoded:raise RuntimeError('Invalid incoming source; GPU result rejected')
 index=int(encoded)-1;w=program['world']
 if not 0<=index<int(w[WA]):raise RuntimeError('Unknown incoming source; GPU result rejected')
 row=w[WA+1+index*ACTOR_WORDS:WA+1+(index+1)*ACTOR_WORDS];run=int(row[3])
 if row[0]!=5 or row[2]!=2 or not 0<=run<len(patterns) or patterns[run]['kind']!='summon':raise RuntimeError('Incompatible incoming source; GPU result rejected')
 return patterns[run]['summon_name']+'#'+str(int(row[4])+1)

def _full_evaluation(device,compiled):
 from types import SimpleNamespace
 import copy
 import engine_worker as adapter
 prepared=compiled['prepared'];body=compiled['body'];duration=float(body.get('duration',180));script=[]
 patterns=compiled.get('patterns',[]);parts=compiled.get('parts',[])
 incoming=any(p['kind']=='attack' or p['kind']=='summon' and compiled['program']['world'][WB+i*BW+80]>0 for i,p in enumerate(patterns))
 incoming_offset=267+(14 if body.get('_debug_random_state') else 0)+len(parts)+(BLOG if patterns else 0)
 incoming_state_offset=incoming_offset+(ILOG if incoming else 0)
 incoming_rng_offset=incoming_state_offset+(1 if incoming else 0)
 witness_base=incoming_rng_offset+(14 if body.get('_debug_boss_random_state') else 0)
 witness_times=[];incoming_times=[];frame_times=[];t=0.0
 while t<=duration:frame_times.append(t);t+=1/60
 incoming_frames_offset=witness_base+(len(frame_times) if patterns and body.get('_debug_boss_frames') else 0)
 scalar=body.get('_debug_scalar_query');scalar_times=[]
 if scalar is not None and (not isinstance(scalar,dict) or set(scalar)!={'who','key'} or type(scalar['who']) is not int or not 0<=scalar['who']<5 or type(scalar['key']) is not int or not 0<=scalar['key']<32):raise ValueError('Invalid scalar frame witness')
 scalar_offset=incoming_frames_offset+(len(frame_times) if incoming and body.get('_debug_incoming_frames') else 0)
 if '_debug_decoy_frames' in body and type(body['_debug_decoy_frames']) is not bool:raise ValueError('Invalid decoy frame witness')
 decoy_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==72}) if body.get('_debug_decoy_frames') else []
 decoy_offset=scalar_offset+(len(frame_times) if scalar is not None else 0);decoy_times=[]
 if '_debug_storage_frames' in body and type(body['_debug_storage_frames']) is not bool:raise ValueError('Invalid storage frame witness')
 storage_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==74}) if body.get('_debug_storage_frames') else []
 storage_offset=decoy_offset+(len(frame_times)*(1+len(decoy_keys)) if body.get('_debug_decoy_frames') else 0);storage_times=[]
 if '_debug_charge_frames' in body and type(body['_debug_charge_frames']) is not bool:raise ValueError('Invalid charge frame witness')
 charge_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2]==76}) if body.get('_debug_charge_frames') else []
 charge_offset=storage_offset+(len(frame_times)*(1+len(storage_keys)) if body.get('_debug_storage_frames') else 0);charge_times=[]
 if '_debug_damage_accum_frames' in body and type(body['_debug_damage_accum_frames']) is not bool:raise ValueError('Invalid damage accumulation frame witness')
 accum_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2] in (81,82)}) if body.get('_debug_damage_accum_frames') else []
 accum_offset=charge_offset+(len(frame_times)*(1+len(charge_keys)) if body.get('_debug_charge_frames') else 0);accum_times=[]
 if '_debug_base_copy_frames' in body and type(body['_debug_base_copy_frames']) is not bool:raise ValueError('Invalid base-stat copy frame witness')
 copy_keys=sorted({int(q[3]) for q in compiled['program']['effects'] if q[1]==0 and q[2] in (85,86)}) if body.get('_debug_base_copy_frames') else []
 copy_offset=accum_offset+((len(frame_times)+1)*(1+len(accum_keys)) if body.get('_debug_damage_accum_frames') else 0);copy_times=[]
 if '_debug_impact_frames' in body and type(body['_debug_impact_frames']) is not bool:raise ValueError('Invalid impact frame witness')
 impact_offset=copy_offset+((len(frame_times)+1)*(1+len(copy_keys)) if body.get('_debug_base_copy_frames') else 0);impact_times=[]
 counter_debug=body.get('_debug_target_counter_frames')
 if counter_debug is not None and (not isinstance(counter_debug,dict) or set(counter_debug)!={'who'} or type(counter_debug['who']) is not int or not 0<=counter_debug['who']<5):raise ValueError('Invalid target-counter frame witness')
 counter_offset=impact_offset+(len(frame_times)+1 if body.get('_debug_impact_frames') else 0);counter_times=[]
 weapon_debug=body.get('_debug_weapon_frames')
 if weapon_debug is not None and (not isinstance(weapon_debug,dict) or set(weapon_debug)!={'who'} or type(weapon_debug['who']) is not int or not 0<=weapon_debug['who']<5):raise ValueError('Invalid weapon frame witness')
 weapon_offset=counter_offset+(len(frame_times)+1 if counter_debug is not None else 0);weapon_times=[]
 for i in range(5):script.append([0,0,0,i,0,-1,0,0])
 for i in range(5):script.append([0,0,5,i,0,-1,0,0])
 for t in frame_times:
  script.append([t,4,0,0,0,-1,0,0])
  if patterns and body.get('_debug_boss_frames'):
   script.append([t,2,116,0,0,witness_base+len(witness_times),0,0]);witness_times.append(t)
  if incoming and body.get('_debug_incoming_frames'):
   script.append([t,2,119,0,0,incoming_frames_offset+len(incoming_times),0,0]);incoming_times.append(t)
  if scalar is not None:
   script.append([t,2,103,scalar['who'],scalar['key'],scalar_offset+len(scalar_times),0,0]);scalar_times.append(t)
  if body.get('_debug_decoy_frames'):
   for key in [-1]+decoy_keys:script.append([t,2,121,0,key,decoy_offset+len(decoy_times),0,0]);decoy_times.append((t,key))
  if body.get('_debug_storage_frames'):
   for key in [-1]+storage_keys:script.append([t,2,122,0,key,storage_offset+len(storage_times),0,0]);storage_times.append((t,key))
  if body.get('_debug_charge_frames'):
   for key in [-1]+charge_keys:script.append([t,2,123,0,key,charge_offset+len(charge_times),0,0]);charge_times.append((t,key))
  if body.get('_debug_damage_accum_frames'):
   for key in [-1]+accum_keys:script.append([t,2,124,0,key,accum_offset+len(accum_times),0,0]);accum_times.append((t,key))
  if body.get('_debug_base_copy_frames'):
   for key in [-1]+copy_keys:script.append([t,2,125,0,key,copy_offset+len(copy_times),0,0]);copy_times.append((t,key))
  if body.get('_debug_impact_frames'):
   script.append([t,2,126,0,0,impact_offset+len(impact_times),0,0]);impact_times.append(t)
  if counter_debug is not None:
   script.append([t,2,127,counter_debug['who'],-1,counter_offset+len(counter_times),0,0]);counter_times.append(t)
  if weapon_debug is not None:
   script.append([t,2,108,weapon_debug['who'],0,weapon_offset+len(weapon_times),0,0]);weapon_times.append(t)
 # Log readback is data produced by GPU, not CPU-selected burst times.
 script.append([duration,5,0,0,0,-1,0,0])
 if body.get('_debug_damage_accum_frames'):
  for key in [-1]+accum_keys:script.append([duration,2,124,0,key,accum_offset+len(accum_times),0,0]);accum_times.append((duration,key))
 if body.get('_debug_base_copy_frames'):
  for key in [-1]+copy_keys:script.append([duration,2,125,0,key,copy_offset+len(copy_times),0,0]);copy_times.append((duration,key))
 if body.get('_debug_impact_frames'):
  script.append([duration,2,126,0,0,impact_offset+len(impact_times),0,0]);impact_times.append(duration)
 if counter_debug is not None:
  script.append([duration,2,127,counter_debug['who'],-1,counter_offset+len(counter_times),0,0]);counter_times.append(duration)
 for i in range(256):script.append([duration,2,100,0,i,i,0,0])
 for i in range(5):script.append([duration,2,101,i,0,256+i,0,0])
 for i in range(5):script.append([duration,2,108,i,0,261+i,0,0])
 script.append([duration,2,109,0,0,266,0,0])
 if body.get('_debug_random_state'):
  for page in range(14):script.append([duration,2,110,0,page,267+page,0,0])
 parts=compiled.get('parts',[])
 part_offset=267+(14 if body.get('_debug_random_state') else 0)
 for i in range(len(parts)):script.append([duration,2,114,0,i,part_offset+i,0,0])
 boss_offset=part_offset+len(parts)
 if patterns:
  for i in range(BLOG):script.append([duration,2,115,0,i,boss_offset+i,0,0])
 if incoming:
  for i in range(ILOG):script.append([duration,2,117,0,i,incoming_offset+i,0,0])
  script.append([duration,2,119,0,0,incoming_state_offset,0,0])
 if body.get('_debug_boss_random_state'):
  for page in range(14):script.append([duration,2,118,0,page,incoming_rng_offset+page,0,0])
 hp_offset=sum(row[1]==2 for row in script)
 if body.get('_debug_hp_events'):
  for i in range(1024):script.append([duration,2,120,0,i,hp_offset+i,0,0])
 # One preparation/readback path for single battles and grouped candidates.
 # This schedule is host-authored; no CPU battle state is replayed.
 result=yield dict(program=compiled['program'],script=script,enemy=compiled['enemy'],base_stats=compiled['base_stats'],seed=body.get('seed',0))
 totals=result['totals'][0];names=[c['name'] for c in compiled['program']['chars']]
 fake=SimpleNamespace(squad_total=sum(totals),char_total=dict(zip(names,totals)),duration=duration,log=None,boss_unmodeled={})
 payload=adapter.sim.payload(prepared,fake)
 logs=result['queries'][0];count=int(logs[0][3]);timeline=[]
 if body.get('burst_gauge_mode','fixed')=='accumulate':
  camera=int(compiled['program']['chars'][0].get('_detail_camera',0));selected=[n for i,n in enumerate(names) if camera&(1<<i)]
  note=' · '.join(selected) if selected else '없음'
  if len(selected)>1:note+='  [camera_mode="shared" — 비현실적 상한]'
  timeline.append({'time':0.0,'event':'카메라 초점: '+note,'character':''})
 for row in logs[:count]:
  event=int(row[1]);who=int(row[2]);timeline.append({'time':round(row[0],3),'event':f'reenter:{event-6} 사용' if 7<=event<=9 else f'stage:{event} 사용' if event<4 else 'full_burst 시작' if event==4 else '게이지 만충 100.0% → 1단계 진입 (소모)' if event==6 else 'full_burst 종료','character':names[who] if who>=0 else ''})
 payload.update(weapon_mode_swap=body.get('weapon_mode_swap',False),shooting_policy=body.get('shooting_policy','auto'),base_stats=compiled['base_stats'],burst_policy=compiled['policy'],requested_burst_policy=compiled['requested_policy'],burst_patterns=prepared.config.get('burst_pattern',{}),burst_timeline=timeline,engine_revision=adapter.REVISION,hypothetical=any(any(body['profile']['chars'][n].get('equip_skills',{}).get(k)!=patch.get('equip_skills',{}).get(k) for k in patch.get('equip_skills',{})) for n,patch in body.get('patches',{}).items() if n in names) or any(any(v for v in f.values()) for f in body.get('stat_deltas',{}).values()),app_warnings=['固定条件の静止ボスを仮定した参考値です。ボス固有パターンと生存は未検証です。'],compute={'requested':'cuda_detail','backend':'cuda_detail','device':device.name,'elapsed_ms':result['elapsed_ms'],'initialization_ms':result['initialization_ms'],'module_backend':result['module_backend'],'workspace_bytes':result['workspace_bytes'],'scope':'five-member autonomous detailed simulation','parity':'regression-tested supported mechanics; not all characters'})
 payload['compute']['timings_ms']=result['timings_ms']
 if parts:
  payload['parts_state']=[dict(name=part['name'],damage=int(logs[part_offset+i][1]),hits=int(logs[part_offset+i][2]),destroyed=bool(logs[part_offset+i][0]),destroyed_at=round(logs[part_offset+i][3],6) if logs[part_offset+i][0] else None) for i,part in enumerate(parts)]
 if patterns:
  payload['app_warnings'][0]='設定したボス行動で計算した参考値です。座標・実機のギミック・生存などの再現は未検証です。'
  payload['boss_patterns']=copy.deepcopy(body.get('enemy',{}).get('patterns',[]))
  outcomes={1:'expired',2:'followed',3:'cleared',4:'end'}
  payload['boss_timeline']=[dict(time=round(r[0],6),pattern=patterns[int(r[1])]['id'],kind=patterns[int(r[1])]['kind'],event='start' if r[2]==0 else 'dispel' if r[2]==5 else 'end',outcome=outcomes.get(int(r[2]))) for r in logs[boss_offset:boss_offset+int(logs[boss_offset][3])]]
  if witness_times:payload['_boss_frames']=[dict(time=at,core=r[0],distance=r[1],weapon_mask=int(r[2]),log_count=int(r[3]),active_mask=int(r[4]),opens=[int(v) for v in r[5:5+len(patterns)]],defense=r[37],dispelled_mask=int(r[38])) for at,r in zip(witness_times,logs[witness_base:witness_base+len(witness_times)])]
 if incoming:
  count=int(logs[incoming_offset][12])
  if not 0<=count<=ILOG:raise RuntimeError('Invalid incoming hit count; GPU result rejected')
  payload['incoming_hits']=[dict(time=round(r[0],6),pattern=patterns[int(r[1])]['id'],target=names[int(r[2])],damage=round(r[3],6),pierce=bool(r[4]),decoy=round(r[5],6),shield=round(r[6],6),cover=round(r[7],6),hp=round(r[8],6),hp_after=round(r[9],6),down=bool(r[10]),by=incoming_source_label(compiled['program'],patterns,r[11])) for r in logs[incoming_offset:incoming_offset+count]]
  state=logs[incoming_state_offset]
  payload['_incoming_state']={n:dict(hp=state[i],cover_hp=state[5+i],cover_max_hp=state[10+i]) for i,n in enumerate(names)}
  payload['_down_mask']=int(state[15])
  if incoming_times:
   payload['_incoming_frames']=[dict(time=at,state={n:dict(hp=r[i],cover_hp=r[5+i],cover_max_hp=r[10+i]) for i,n in enumerate(names)}) for at,r in zip(incoming_times,logs[incoming_frames_offset:incoming_frames_offset+len(incoming_times)])]
   payload['_down_frames']=[dict(time=at,mask=int(r[15])) for at,r in zip(incoming_times,logs[incoming_frames_offset:incoming_frames_offset+len(incoming_times)])]
 if body.get('_debug_boss_random_state'):payload['_boss_random_state']=[int(v) for page in logs[incoming_rng_offset:incoming_rng_offset+14] for v in page][:625]
 payload['seed']=body.get('seed',0)
 if scalar_times:payload['_scalar_frames']=[dict(time=at,value=row[0]) for at,row in zip(scalar_times,logs[scalar_offset:scalar_offset+len(scalar_times)])]
 if decoy_times:payload['_decoy_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},capacity={n:row[6+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(decoy_times,logs[decoy_offset:decoy_offset+len(decoy_times)])]
 if storage_times:payload['_storage_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},capacity={n:row[6+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(storage_times,logs[storage_offset:storage_offset+len(storage_times)])]
 if charge_times:payload['_charge_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},base_capacity={n:row[6+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(charge_times,logs[charge_offset:charge_offset+len(charge_times)])]
 if accum_times:payload['_damage_accum_frames']=[dict(time=at,key=key,current={n:row[1+i] for i,n in enumerate(names)},capacity={n:row[6+i] for i,n in enumerate(names)},done={n:int(row[11+i]) for i,n in enumerate(names)},carriers=int(row[16]),archived=row[17]) for (at,key),row in zip(accum_times,logs[accum_offset:accum_offset+len(accum_times)])]
 if copy_times:payload['_base_copy_frames']=[dict(time=at,key=key,basis={n:row[1+i] for i,n in enumerate(names)},source={n:row[6+i] for i,n in enumerate(names)},gift={n:row[11+i] for i,n in enumerate(names)},carriers=int(row[16])) for (at,key),row in zip(copy_times,logs[copy_offset:copy_offset+len(copy_times)])]
 if impact_times:payload['_impact_frames']=[dict(time=at,fields=list(row)) for at,row in zip(impact_times,logs[impact_offset:impact_offset+len(impact_times)])]
 if counter_times:
  state_names={value:key for key,value in compiled['program']['states'].items()}
  payload['_target_counter_frames']=[]
  for at,row in zip(counter_times,logs[counter_offset:counter_offset+len(counter_times)]):
   last=None if row[2]==0 else dict(uid=int(row[8]),epoch=int(row[9]),owner=names[int(row[10])],name=state_names[int(row[11])],actor=[int(row[12]),int(row[13]),int(row[14])],credit=row[15],reason='death' if row[16] else 'threshold',time=row[17])
   payload['_target_counter_frames'].append(dict(time=at,active=int(row[0]),credit=row[1],completed=int(row[2]),latched=int(row[3]),dead_actors=int(row[4]),epoch=int(row[5]),last=last))
 if body.get('_debug_hp_events'):
  count=int(logs[hp_offset][3])
  if not 0<=count<=1024:raise RuntimeError('Invalid HP event log count')
  keys={value:key for key,value in compiled['program']['states'].items()}
  payload['_hp_events']=[dict(time=r[0],caster=names[int(r[1])],event=(keys[int(r[2])] if keys[int(r[2])].startswith('hp_below:') else 'event:'+keys[int(r[2])])) for r in logs[hp_offset:hp_offset+count]]
 if weapon_times:payload['_weapon_frames']=[dict(time=at,phase=int(row[1]),shots=int(row[6]),ammo=row[10],reloading_until=row[11]) for at,row in zip(weapon_times,logs[weapon_offset:weapon_offset+len(weapon_times)])]
 if body.get('_debug_random_state'):payload['_random_state']=[int(v) for page in logs[267:281] for v in page][:625]
 payload['burst_gauge_mode']=body.get('burst_gauge_mode','fixed')
 payload['compute']['burst_gauge']={'amount':logs[266][0],'charging':bool(logs[266][1]),'mode':body.get('burst_gauge_mode','fixed')}
 payload['compute']['final_hp']={n:{'hp':logs[256+i][0],'hp_pct':logs[256+i][1],'max_hp':logs[256+i][2]} for i,n in enumerate(names)}
 payload['compute']['final_control']={n:{'charging':bool(logs[261+i][0]),'phase':int(logs[261+i][1]),'full_at':logs[261+i][2],'release_at':logs[261+i][3],'owner':names[int(logs[261+i][4])] if logs[261+i][4]>=0 else '', 'camera_mask':int(logs[261+i][5]),'shots':int(logs[261+i][6]),'sequence_index':int(logs[261+i][7]),'preemptions':int(logs[261+i][8]),'normal_landed':bool(logs[261+i][9]),'ammo':logs[261+i][10],'reloading_until':logs[261+i][11]} for i,n in enumerate(names)}
 if any(r[4]==4 and r[1]==0 and r[2] not in (2,3,12,27) for r in compiled['program']['effects']):payload['app_warnings'].append('敵対象の能力変化も固定CPU版の集計規則に合わせています。CPUとの一致は実機の正しさを保証しません。')
 if compiled['requested_policy']=='mast3' and compiled['policy']=='auto':payload['app_warnings'].append('マスト不在のため全員オートで計算しました。')
 if compiled['program'].get('counter_single_body'):
  from target_counter_specs import SINGLE_BODY_WARNING
  payload['app_warnings'].append(SINGLE_BODY_WARNING)
 if compiled['program'].get('periodic_source_estimated'):payload['app_warnings'].append(SOURCE_WARNING)
 if any(row[340]>0 for row in compiled['program']['effects']):payload['app_warnings'].append(STAGED_WARNING)
 if payload['hypothetical']:payload['app_warnings'].append('育成変更・仮ステータスを含む計算です。')
 if any(r[43]>=0 for r in compiled['program']['effects']):payload['app_warnings'].append('固定CPU版に合わせ、同名・同種の装備効果は最初の定義へ統合しています。異なるオバロ値の実機再現は保証できません。')
 return payload

def _finish_full(evaluation,result):
 try:evaluation.send(result)
 except StopIteration as complete:return complete.value
 raise RuntimeError('Detailed evaluation must have exactly one GPU execution')

def evaluate_full(device,compiled,module_backend='auto'):
 evaluation=_full_evaluation(device,compiled)
 try:
  request=next(evaluation)
  result=run(device,[request['program']],request['script'],[request['enemy']],[request['base_stats']],module_backend=module_backend,seeds=[request['seed']])
  return _finish_full(evaluation,result)
 finally:evaluation.close()

def evaluate_full_many(device,compiled,module_backend='auto',batch_size=32):
 """Share command streams; keep each squad's state and result independent.

 Durations, debug queries and boss schedules group by exact command equality.
 Input order is restored after grouping. elapsed_ms is actual group latency;
 per-squad workspace and group workspace are both reported explicitly.
 """
 if type(batch_size) is not int or not 1<=batch_size<=32:raise ValueError('Detailed batch size must be 1..32')
 evaluations=[];groups={};results=[None]*len(compiled)
 try:
  for index,item in enumerate(compiled):
   evaluation=_full_evaluation(device,item);evaluations.append(evaluation);request=next(evaluation)
   key=tuple(tuple(command) for command in request['script'])
   groups.setdefault(key,[]).append((index,evaluation,request))
  for group in groups.values():
   for start in range(0,len(group),batch_size):
    chunk=group[start:start+batch_size];requests=[row[2] for row in chunk];size=len(chunk)
    result=run(device,[r['program'] for r in requests],requests[0]['script'],[r['enemy'] for r in requests],[r['base_stats'] for r in requests],module_backend=module_backend,seeds=[r['seed'] for r in requests])
    if len(result['queries'])!=size or len(result['totals'])!=size or result['workspace_bytes']%size:raise RuntimeError('Invalid detailed batch result layout')
    for offset,(index,evaluation,request) in enumerate(chunk):
     single={**result,'queries':[result['queries'][offset]],'totals':[result['totals'][offset]],'workspace_bytes':result['workspace_bytes']//size}
     payload=_finish_full(evaluation,single)
     if size>1:payload['compute'].update(batch_size=size,batch_elapsed_ms=result['elapsed_ms'],batch_workspace_bytes=result['workspace_bytes'],amortized_elapsed_ms=round(result['elapsed_ms']/size,3))
     results[index]=payload
  return results
 finally:
  for evaluation in evaluations:evaluation.close()

