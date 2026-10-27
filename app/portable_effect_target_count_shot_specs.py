"""Static physical-world binding; no shot schedule or query values are packed."""
import copy,struct
from portable_specs import LIMITS as L,FIELDS as F
from portable_effect_target_count_specs import STAT
from effect_target_count_policy import MODEL,validate_effect

SOURCE='gpu/world_effect_target_count_shot_entry.slang'
INPUT=104400
OUTPUT=786432
HEAD=L['QUERY_BASE']+L['QUERY_WORDS']
TRACE=HEAD+16
CAPACITY=100
WORDS=20
MAGIC=0x54435331
assert TRACE+CAPACITY*WORDS==L['QUERY_BASE']+L['COMMANDS']*L['QUERY_WORDS']

def compile_case(parent,case,*,model):
    if model!=MODEL:raise ValueError('Explicit named capacity shot model required')
    c=copy.deepcopy(case);indices=[]
    for i,effect in enumerate(case['effects']):
        if validate_effect(effect):
            if effect.get('duration_bullets',-1)<=0:raise ValueError('Physical shot lifetime required')
            indices.append(i);c['effects'][i]=dict(effect,stat='')
    if len(indices)!=1:raise ValueError('Shot observation requires one named modifier definition')
    words,meta,bindings=parent.compile_case(c)
    bound=[i for i,source in enumerate(meta['binding_source_indices']) if source in indices]
    if len(bound)!=1:raise ValueError('Shot observation requires one statically bound modifier')
    row=bound[0];effect=case['effects'][indices[0]];name=effect['target_effect']
    if name not in meta['states']:
        if len(meta['states'])>=L['DEFINITIONS']:raise ValueError('Named marker symbol capacity exceeded')
        meta['states'][name]=len(meta['states']);words[L['WORLD_META_BASE']+1]=len(meta['states'])
    at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];words[at+F['KIND']]=0;words[at+F['STAT']]=STAT;words[at+F['TARGET_NAME']]=meta['states'][name]
    meta['named_count_physical']=dict(model=model,row=row,marker=name,original_definition=copy.deepcopy(effect),base_count=5,capacity_limit=128)
    return words,meta,bindings

def decode(block,meta):
    h=list(block[HEAD:HEAD+16]);context=meta['named_count_physical']
    if h[:2]!=[MAGIC,1] or h[2]>CAPACITY or h[3:6]!=[meta['states'][context['marker']],5,128] or any(h[6:]):
        raise ValueError('Invalid named shot observation header')
    number=lambda r,i:struct.unpack('<d',struct.pack('<II',*r[i:i+2]))[0]
    events=[]
    for index in range(h[2]):
        row=list(block[TRACE+index*WORDS:TRACE+(index+1)*WORDS])
        if row[0]>=5 or any(v not in (0,1) for v in [*row[11:14],row[16]]) or row[17]:raise ValueError('Invalid named shot context')
        events.append(dict(who=row[0],time=number(row,2),
            before=dict(capacity=row[4],additional=number(row,6),remaining=row[1],present=bool(row[12]),activated=number(row,14),skipped=bool(row[11])),
            after=dict(capacity=row[5],additional=number(row,8),remaining=row[10],present=bool(row[13]),activated=number(row,18),skipped=bool(row[16]))))
    if any(block[TRACE+h[2]*WORDS:TRACE+CAPACITY*WORDS]):raise ValueError('Unexpected named shot trace tail')
    return events
