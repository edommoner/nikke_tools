"""Static opt-in lowering only; no native battle or authored hit/group lists."""
import copy
from portable_specs import LIMITS as L,FIELDS as F
from portable_trigger_specs import pack_event_candidates
from portable_runtime import double_words
from attack_group_specs import simultaneous_threshold
from portable_projectile_roster_input import compile_projectile_battle
SOURCE='gpu/world_attack_group_entry.slang'
INPUT_WORDS=104408
OUTPUT_WORDS=1048576
HEADER=800000
SLOTS=800032
SLOT_WORDS=536
LOG=820000
LOG_CAPACITY=64
PACKETS=860000
COMPACT=PACKETS+L['LANDINGS']
COMPACT_WORDS=OUTPUT_WORDS-COMPACT

def compile_battle(prepared,*,routing,declared_effects=(),group_history='fixed64'):
    if routing not in ('native','all-logical-enemies'):raise ValueError('Explicit native or logical-enemy routing required')
    if group_history not in ('fixed64','compact'):raise ValueError('Explicit fixed64 or compact group history required')
    enemy=prepared['enemy']
    if enemy.get('has_parts') or enemy.get('coord') is not None or enemy.get('part_break_interval',0):raise ValueError('Plain body/add world required')
    patterns=enemy.get('patterns',[])
    if any(p.get('kind') not in ('idle','summon') or p.get('kind')=='summon' and (p.get('spec',{}).get('attack') or p.get('spec',{}).get('self_destruct')) for p in patterns):raise ValueError('Only plain idle/summon patterns supported')
    lowered=copy.deepcopy(prepared);owner=prepared['chars'][0]['name']
    for effect in declared_effects:lowered['effects'].append(dict(effect=copy.deepcopy(effect),owner=owner))
    original=copy.deepcopy(lowered['effects']);names=[c['name'] for c in prepared['chars']];owners=0
    for item in lowered['effects']:
        effect=item['effect'];timings=effect.get('trigger',{}).get('timing',[])
        if any(t.startswith('event:__portable_attack_group_') for t in timings):raise ValueError('Reserved private lowering namespace')
        for t in timings:
            if t.startswith('multi_hit:'):
                simultaneous_threshold(t)
                if effect.get('target') not in ('self','target') or effect.get('trigger',{}).get('condition') or effect.get('type') not in ('buff','damage') or effect.get('type')=='damage' and (effect.get('stat')!='bonus_damage' or effect.get('target')!='target' or effect.get('tick_interval')):raise ValueError('Unsupported original multi_hit child')
                owners|=1<<names.index(item['owner'])
        effect['trigger']['timing']=['event:__portable_attack_group_'+str(simultaneous_threshold(t)) if t.startswith('multi_hit:') else t for t in timings]
    if owners==0:raise ValueError('At least one original or explicit declared listener required')
    words,metadata=compile_projectile_battle(lowered)
    for row,source in enumerate(metadata['binding_source_indices']):
        effect=original[source]['effect'];timings=effect['trigger']['timing']
        count=words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['TRIGGER_COUNT']]
        if count!=len(timings):raise ValueError('Unexpected trigger expansion')
        for slot,timing in enumerate(timings):
            if not timing.startswith('multi_hit:'):continue
            threshold=simultaneous_threshold(timing);at=L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8
            if words[at]!=31:raise ValueError('Expected named-event static intermediate')
            words[at:at+8]=[62,*double_words(threshold),0,threshold,0,0,0]
            if slot==0:words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['EVENT']]=62
    pack_event_candidates(words,L)
    assert len(words)==104400
    words.extend([0x41475331,2 if routing=='native' else 1,owners,int(group_history=='compact'),0,0,0,0]);assert len(words)==INPUT_WORDS
    metadata['real_prepared_input']['declared_attack_group_policy']=dict(routing=routing,listener_owners=owners,game_geometry_verified=False,source_effects=original,cpu_trace_used_as_gpu_input=False)
    return words,metadata
