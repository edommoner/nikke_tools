"""Shared acceptance/encoding for legacy trigger and predicate descriptors.
Values come from detail_gpu.compile_effects; no battle state is produced here.
"""
import math
import re
from world_condition_specs import ENEMY_COUNT_ABOVE,ENEMY_COUNT_BELOW,TARGET_IS_BOSS,TARGET_IS_ADD
from portable_code_specs import TARGET_CODE,PREFIX as CODE_PREFIX,condition_id


class UnsupportedTrigger(ValueError):
    """An actionable missing descriptor, independent of diagnostic wording."""
    reason = 'trigger'

    def __init__(self, message, *, domain, descriptor):
        self.operator = dict(domain=domain, descriptor=descriptor)
        super().__init__(message)

CONDITIONS=dict(FOCUSING=30,NO_BROKEN_COVER_ALLY=39,SELF_UNDYING=38,TRIGGER_HIT_CRIT=28,TARGET_STUNNED=23,SELF_STUN_IMMUNE=24,TARGET_STATE=16,NOT_TARGET_STATE=17,TARGET_STACK=6,CORE=35,OPTIMAL_RANGE=33,PROB=26,SHIELD=12,GAUGE_ABOVE=18,GAUGE_BELOW=19,GAUGE_EQ=20,GAUGE_MOD=21,COVER_ALIVE=36,COVER_BROKEN=37,FULL=1,NOT_FULL=2,SELF_STATE=3,NOT_SELF_STATE=4,SELF_STACK=5,
                BACK_ROW=7,STAT_ABOVE=8,HP_ABOVE=9,HP_BELOW=10,HP_MAX=11,NOT_SELF_HEAL=13,CAST=14,NOT_CAST=15,STATIC=25,CHARGING=29,
                BURST1_ALLY=31,NO_BURST1_ALLY=32,ALLY_HP_BELOW=34,TARGET_CODE=TARGET_CODE,ENEMIES_ABOVE=ENEMY_COUNT_ABOVE,
                ENEMIES_BELOW=ENEMY_COUNT_BELOW,TARGET_BOSS=TARGET_IS_BOSS,TARGET_ADD=TARGET_IS_ADD)
EVENTS=frozenset((0,1,2,3,4,6,7,8,9,10,11,12,14,16,17,18,19,20,21,26,27,29,30,31,32,36,37,38,43,46,48,49,59,60))
COUNT=r'(?:[1-9][0-9]*|\{0\})'
SIMPLE=r'event:shield_applied|event:shield_consumed|feather_tick|source_tick:.+|event:cover_healed|event:cover_hit|received_hit|event:lethal_hit|event:self_down|event:ally_down|event:heal_received|battle_start|passive|on_attack|hit_count|burst_cast|full_burst_start|full_burst_end|event:full_reload|last_bullet|last_bullet_fire|full_charge|full_charge_fire|full_charge_hit|squad_ammo_consume|pellet_hit'
COUNTERS=rf'(?:part_hit_count|body_hit_count|crit_hit_count|core_hit_count|core_hit|received_hit_count|on_attack_count|hit_count|squad_ammo_consume|pellet_hit|pellet_hit_count|full_charge_fire_count|full_charge_count|full_charge_hit_count|burst_cast_count|full_burst_start_count|full_burst_end_count|full_burst_start_exact):{COUNT}'
HP_NUMBER=r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
HP_TIMING=rf'hp_below:{HP_NUMBER}|hp_below_count:{HP_NUMBER}:[1-9][0-9]*|event:(?:ally_hp_below|adjacent_hp_below):{HP_NUMBER}|event:adjacent_hp_max'
# Names are opaque suffixes: colons, whitespace and Unicode remain significant.
# Reserve structured event prefixes so malformed HP/end descriptors and unported
# accumulator/counter events cannot fall through to the generic named event.
TIMING=rf'every_stack:[^:]+:[1-9][0-9]*|event:(?!(?:state_end|ally_hp_below|adjacent_hp_below|accum_full|target_counter_complete):)[\s\S]+|{HP_TIMING}|{SIMPLE}|{COUNTERS}|burst_enter:[123]|burst_enter_count:[123]:{COUNT}|event:state_end:[\s\S]+|hit_count:[^:]+:{COUNT}|stack_reach:[^:]+:[1-9][0-9]*'
CONDITION=rf'focusing|no_broken_cover_ally|self_undying|trigger_hit_crit|target_stunned|self_stun_immune|(?:target_state|not_target_state):[\s\S]*|target_stack_above:[\s\S]*:[0-9]+|core_hit|optimal_range|prob:[\s\S]+|during_shield|gauge_(?:above|below|eq):[^:]+:{HP_NUMBER}|gauge_mod:[^:]+:[1-9][0-9]*:[+-]?[0-9]+|self_cover_alive|not_self_cover_alive|not_self_caused_heal|self_hp_max|(?:self_hp_above|self_hp_below|ally_hp_below):[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)|during_full_burst|not_during_full_burst|during_charge|burst_casted|burst_not_casted|has_burst1_ally|no_burst1_ally|has_defender_ally|no_defender_ally|squad_ally_exists|back_row|target_is_boss|target_is_add|target_code:[\s\S]*|(?:self_state|not_self_state):[\s\S]*|self_stack_above:[^:]+:[0-9]+|enemy_count_(?:above|below):[+-]?[0-9]+|self_stat_above:(?:atk_pct|crit_rate|crit_dmg|accuracy_pct):[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'


def validate_input(eff,*,world_frame=False):
    from portable_probability_specs import validate as validate_probability
    trigger=eff.get('trigger',{})
    if not isinstance(trigger,dict) or set(trigger)-{'timing','condition'}:raise ValueError('Invalid trigger object')
    timings=trigger.get('timing',[]);conditions=trigger.get('condition',[])
    if not isinstance(timings,list) or not 1<=len(timings)<=8:raise ValueError('Expected 1..8 trigger descriptors')
    if not isinstance(conditions,list) or len(conditions)>3:raise ValueError('Expected at most three predicates')
    validate_probability(eff)
    from portable_target_state_specs import parse as target_predicate
    for condition in conditions:
        if isinstance(condition,str):target_predicate(condition)
    for timing in timings:
        if not isinstance(timing,str):raise ValueError('Invalid timing')
        from portable_pellet_shot_specs import parse as parse_pellet_shot
        try:pellet_shot=parse_pellet_shot(timing)
        except ValueError as error:raise UnsupportedTrigger(str(error),domain='timing',descriptor=timing) from error
        if pellet_shot is not None:continue
        if timing.startswith('event:'):
            from detail_gpu import EVENT
            if timing in EVENT and EVENT[timing] not in (EVENTS|frozenset((5,22,23,33,34,35,39,42,44,45)) if world_frame else EVENTS):raise UnsupportedTrigger('Unported trigger timing: '+timing,domain='timing',descriptor=timing)
        from portable_charge_control_specs import parse_hold
        if world_frame and parse_hold(timing) is not None:continue
        if timing.startswith('every:'):
            if not timing.endswith('s'):raise ValueError('Periodic timing requires native seconds suffix')
            try:period=float(timing[6:].removesuffix('s'))
            except ValueError:raise ValueError('Invalid periodic timing') from None
            if not math.isfinite(period) or period<=0:raise ValueError('Periodic timing must be positive and finite')
        elif not re.fullmatch(TIMING,timing) and not (world_frame and timing in ('enemy_death','crit_hit','core_hit')):raise UnsupportedTrigger('Unported trigger timing: '+timing,domain='timing',descriptor=timing)
    for condition in conditions:
        if condition in ('focusing','no_broken_cover_ally') and not world_frame:raise ValueError('Cover/camera predicates require a private combat world')
        if condition=='no_broken_cover_ally' and 'passive' in timings:raise UnsupportedTrigger('Cover predicate requires explicit activation',domain='condition',descriptor=condition)
        if condition=='self_undying':
            if not world_frame:raise ValueError('Live marker predicate requires private combat world')
            if 'passive' in timings:raise UnsupportedTrigger('Live marker predicate requires explicit activation',domain='condition',descriptor=condition)
        if condition=='trigger_hit_crit' and not world_frame:raise ValueError('Hit-critical context requires private combat world')
        if condition in ('target_stunned','self_stun_immune') and not world_frame:raise ValueError('Stun predicate requires private combat world')
        if not isinstance(condition,str) or not re.fullmatch(CONDITION,condition):raise UnsupportedTrigger('Unported predicate: '+str(condition),domain='condition',descriptor=condition)


def pack_descriptors(words,index,row,L,F,double_words,*,effect=None,states=None,world_frame=False,shot_tags=None):
    n=int(row[144]);nc=int(row[14])
    if not 1<=n<=8 or not 0<=nc<=3:raise ValueError('Descriptor capacity exceeded')
    for slot in range(n):
        event,threshold,mode,tag,value,passive,stage=row[145+slot*7:152+slot*7]
        if event not in (EVENTS|frozenset((5,22,23,33,34,35,39,42,44,45)) if world_frame else EVENTS) or mode not in (0,1,2,3):raise ValueError('Unported compiled trigger')
        if event!=6 and (threshold!=int(threshold) or not (-(2**31) if event==27 else 0)<=threshold<=2**31-1):raise ValueError('Invalid discrete trigger threshold')
        if event==27:
            from portable_pellet_shot_specs import parse
            parsed=parse(effect['trigger']['timing'][slot]) if effect is not None else None
            if parsed is None or max(1,parsed[0])!=threshold or shot_tags is None or mode!=0 or tag!=-1 or value!=0 or passive!=0 or stage!=-1:raise ValueError('Invalid compiled per-shot descriptor')
            threshold=parsed[0]
            tag=shot_tags[parsed[1]]
            stage=0
        if (mode or event in (7,8,30)) and threshold<=0:raise ValueError('Trigger threshold must be positive')
        if event==6 and (not math.isfinite(threshold) or threshold<=0):raise ValueError('Invalid compiled period')
        if event==9 and (value!=int(value) or not 0<=value<=2**31-1):raise ValueError('Invalid stack reach value')
        at=L['EVENT_BASE']+index*L['EVENT_WORDS']+slot*8
        edge=stage in (-11,-12,-13,-14)
        if edge and (event not in (31,48) or not math.isfinite(value)):raise ValueError('Invalid compiled HP edge')
        payload=double_words(value) if edge or event==39 else [int(value)&0xffffffff,int(passive)]
        words[at:at+8]=[int(event),*double_words(threshold),int(mode),int(tag)&0xffffffff,*payload,int(stage)&0xffffffff]
    for slot in range(nc):
        kind,name,arg=row[15+slot*3:18+slot*3]
        conditions=effect.get('trigger',{}).get('condition',[]) if effect is not None else []
        if slot<len(conditions) and conditions[slot].startswith(CODE_PREFIX):
            # Legacy kind22 is a CPU-folded boolean. Never copy it into the
            # portable execution contract; encode the original exact code ID.
            kind,name,arg=TARGET_CODE,condition_id(conditions[slot],states),0
        if slot<len(conditions):
            from portable_target_state_specs import parse as target_predicate
            target=target_predicate(conditions[slot])
            if target is not None:
                kind,text,arg=target;name=states[text]
        if kind not in CONDITIONS.values() or kind==8 and (name not in (0,5,6,21) or not math.isfinite(arg)):raise ValueError('Unported compiled predicate')
        if kind==38 and (not world_frame or name!=0 or arg!=0):raise ValueError('Invalid compiled live marker predicate')
        if kind==26 and (name!=0 or not math.isfinite(arg) or not 0<=arg<=1):raise ValueError('Invalid compiled probability')
        at=L['CONDITION_BASE']+index*L['CONDITION_WORDS']+slot*4
        words[at:at+4]=[int(kind),int(name)&0xffffffff,*double_words(arg)]
    at=L['DEFINITION_BASE']+index*L['DEFINITION_WORDS']
    words[at+F['TRIGGER_COUNT']]=n;words[at+F['CONDITION_COUNT']]=nc
    words[at+F['FLAGS']]=int(bool(row[69])) | (int(bool(row[217]))<<1)
    words[at+F['PERIOD']:at+F['PERIOD']+2]=double_words(row[44])


def pack_event_candidates(words,L):
    """Immutable candidates only; descriptor credit/multiplicity stays on GPU."""
    start=L['EVENT_CANDIDATE_BASE'];size=64*L['MASK_WORDS']
    words[start:start+size]=[0]*size
    for row in range(words[1]):
        count=words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+26]
        for slot in range(count):
            event=words[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8]
            if not 0<=event<64:raise ValueError('Event candidate ID outside wire range')
            words[start+event*L['MASK_WORDS']+row//32] |= 1<<(row%32)
