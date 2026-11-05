"""One literal multi-hit lowering and event binding for real roster inputs."""
import copy
from attack_group_specs import simultaneous_threshold
from portable_specs import LIMITS as L,FIELDS as F
from portable_trigger_specs import pack_event_candidates
from portable_runtime import double_words

def lower(prepared):
    lowered=copy.deepcopy(prepared);original=copy.deepcopy(prepared['effects'])
    names=[c['name'] for c in prepared['chars']];owners=0
    for item in lowered['effects']:
        e=item['effect'];timings=e.get('trigger',{}).get('timing',[])
        if any(t.startswith('event:__portable_attack_group_') for t in timings):raise ValueError('Reserved private lowering namespace')
        for t in timings:
            if not t.startswith('multi_hit:'):continue
            simultaneous_threshold(t)
            if e.get('target') not in ('self','target') or e.get('trigger',{}).get('condition') or e.get('type') not in ('buff','damage') or e.get('type')=='damage' and (e.get('stat')!='bonus_damage' or e.get('target')!='target' or e.get('tick_interval')):raise ValueError('Unsupported original multi_hit child')
            owners|=1<<names.index(item['owner'])
        e['trigger']['timing']=['event:__portable_attack_group_'+str(simultaneous_threshold(t)) if t.startswith('multi_hit:') else t for t in timings]
    return lowered,original,owners

def bind(words,metadata,original):
    for row,source in enumerate(metadata['binding_source_indices']):
        if source>=len(original):
            if row not in metadata.get('boss_debuffs',{}).get('definitions',()) or words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['OWNER']]!=5:
                raise ValueError('Unowned appended group definition')
            continue
        timings=original[source]['effect']['trigger']['timing']
        if words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['TRIGGER_COUNT']]!=len(timings):raise ValueError('Unexpected trigger expansion')
        for slot,t in enumerate(timings):
            if not t.startswith('multi_hit:'):continue
            threshold=simultaneous_threshold(t);at=L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8
            if words[at]!=31:raise ValueError('Expected named-event static intermediate')
            words[at:at+8]=[62,*double_words(threshold),0,threshold,0,0,0]
            if slot==0:words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['EVENT']]=62
    pack_event_candidates(words,L)
