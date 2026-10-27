"""Explicit named capacity queries on the shared carrier/event executor.

This model does not admit spatial Lock On or a complete character profile.
Lowering is local to this adapter; the public compiler still rejects the stat.
"""
import copy,math
from effect_target_count_policy import MODEL,STAT as STAT_NAME,validate_effect
from portable_specs import LIMITS as L,FIELDS as F

STAT=93
OP=44
MAGIC=0x54435131
SOURCE='gpu/effect_target_count_entry.slang'


def compile_program(chars,effects,script,base_atk,*,model):
    from portable_runtime import compile_program as compile_base
    if model!=MODEL:raise ValueError('Explicit named target-count model required')
    effects=copy.deepcopy(list(effects));commands=copy.deepcopy(script)
    original=[];lowered=[];queries=[];indices=set()
    for index,(effect,owner) in enumerate(effects):
        if validate_effect(effect):
            # This first external-event adapter has no physical-shot owner.
            # Never lower a two-shot duration to a time-only marker.
            if effect.get('duration_bullets',-1)!=-1:
                raise ValueError('Finite shot lifetime requires the physical battle consumer')
            original.append(index);lowered.append((dict(effect,stat=''),owner))
        else:lowered.append((effect,owner))
    if not original:raise ValueError('Named target-count definitions required')
    for step,cmd in enumerate(commands):
        if not isinstance(cmd,dict):
            if len(cmd)!=8 or cmd[1]!=0:raise ValueError('Only external notifications and named queries are admitted')
            continue
        if set(cmd)!={'op','time','who','marker','base_count','capacity_limit','index'} or cmd['op']!='named_target_count':
            raise ValueError('Exact named query descriptor required')
        t=cmd['time'];who=cmd['who'];base=cmd['base_count'];limit=cmd['capacity_limit'];index=cmd['index']
        if (type(t) not in (int,float) or not math.isfinite(t) or t<0 or type(who) is not int or not 0<=who<5
            or not isinstance(cmd['marker'],str) or not cmd['marker']
            or type(base) is not int or type(limit) is not int or not 0<=base<=limit<=2147483647 or limit==0
            or type(index) is not int or not 0<=index<L['COMMANDS'] or index in indices):
            raise ValueError('Finite integral named capacity query required')
        indices.add(index);queries.append((step,cmd));commands[step]=[t,2,0,who,-1,index,0,0]
    if not queries:raise ValueError('Named target-count queries required')
    words,meta=compile_base(chars,lowered,commands,base_atk)
    if len(meta['effects'])!=len(effects):raise ValueError('Named modifier definition identity changed')
    def symbol(name):
        if name not in meta['states']:
            if len(meta['states'])>=L['DEFINITIONS']:raise ValueError('Named capacity symbol limit')
            meta['states'][name]=len(meta['states'])
        return meta['states'][name]
    key=max(words[L['RECIPIENT_BASE']+i*8+6] for i in range(len(effects)))+1
    for i in original:
        effect=effects[i][0];at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
        words[at+F['KIND']]=0;words[at+F['STAT']]=STAT;words[at+F['TARGET_NAME']]=symbol(effect['target_effect'])
        words[L['RECIPIENT_BASE']+i*8+6]=key
    for step,q in queries:
        at=L['COMMAND_BASE']+step*8
        words[at]=OP;words[at+3:at+8]=[q['who'],symbol(q['marker']),q['base_count'],q['capacity_limit'],q['index']]
    meta['named_target_count']=dict(model=model,queries=[q for _,q in queries],definitions=original,stat=STAT,source=SOURCE,
        spatial_selection_verified=False,physical_shot_lifetime_verified=False,full_profile_verified=False)
    return words,meta


def decode(words,meta):
    import struct
    rows=[]
    for q in meta['named_target_count']['queries']:
        at=L['QUERY_BASE']+q['index']*L['QUERY_WORDS'];row=words[at:at+L['QUERY_WORDS']]
        if row[9]!=MAGIC:raise ValueError('Missing named target-count query output')
        number=lambda i:struct.unpack('<d',struct.pack('<II',*row[i:i+2]))[0]
        if number(0)!=q['time'] or row[2:6]!=[q['who'],meta['states'][q['marker']],q['base_count'],q['capacity_limit']]:
            raise ValueError('Named target-count output context differs')
        if any(row[10:]):raise ValueError('Unexpected named capacity output tail')
        rows.append(dict(time=number(0),who=row[2],marker=q['marker'],base_count=row[4],capacity_limit=row[5],capacity=row[6],additional_targets=number(7)))
    return rows
