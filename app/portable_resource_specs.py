"""Static resource identities and wire policy; quantities/notifications stay GPU owned."""
import math
from resource_specs import minimum_remaining,resource_marker
OPS={'gauge_charge':1,'gauge_consume':2,'gauge_consume_as_ammo':3,'gauge_max_add':4,'gauge_charge_enabled':5}

def operation(effect):return OPS.get(effect.get('stat'),0)

def validate(effect):
    op=operation(effect)
    if not op:return
    if effect.get('type')!=('buff' if op>=4 else 'instant'):raise ValueError('Resource operation has the wrong effect kind')
    if not isinstance(effect.get('gauge_id'),str) or not effect['gauge_id'] or ':' in effect['gauge_id']:raise ValueError('Resource identity requires a nonempty simple name')
    if op==4:
        literal=effect.get("fixed_value",0)
        if type(literal)==int and (literal.bit_length()>1023 or int(float(literal))!=literal):raise ValueError("Resource cap literal loses integer precision")
    if op==5:resource_marker(effect)
    if 'gauge_max' in effect:
        value=effect['gauge_max']
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('Resource cap must be finite and nonnegative')
    minimum_remaining(effect)

def identities(effects,script,limit):
    keys={}
    def add(name):
        if not isinstance(name,str) or not name or ':' in name:raise ValueError('Invalid resource identity')
        keys.setdefault(name,len(keys))
    from portable_reference_specs import hit_reference,scale_reference
    from staged_dot_specs import specification as staged_specification
    for effect,owner in effects:
        staged=staged_specification(effect,owner,effects)
        if staged is not None and isinstance(staged.count,str):add(staged.count)
        mode,name=hit_reference(effect)
        if mode:add(name)
        scale,name=scale_reference(effect)
        if scale:add(name)
        if operation(effect):add(effect['gauge_id'])
        for t in effect.get('trigger',{}).get('timing',[]):
            if t.startswith('every_stack:'):add(t.split(':')[1])
        for c in effect.get('trigger',{}).get('condition',[]):
            if c.startswith(('gauge_above:','gauge_below:','gauge_eq:','gauge_mod:')):add(c.split(':')[1])
    for cmd in script:
        if len(cmd)==8 and cmd[1]==28:add(cmd[4])
    if len(keys)>limit:raise ValueError('Resource identity capacity exceeded')
    return keys

def pack(words,index,row,limits,effect,keys,states,double_words):
    op=operation(effect);at=limits['RESOURCE_DEFINITION_BASE']+index*10
    if op:
        flags=int('gauge_max' in effect and op<=3) | (int('fixed_value' in effect or 'values' in effect)<<1)
        words[at:at+10]=[op,keys[effect['gauge_id']]+1,flags,0,*double_words(effect.get('gauge_max',0) if op<=3 else 0),*double_words(effect.get('fixed_value',0) if op==4 else 0),*double_words(minimum_remaining(effect))]
    inverse={v:k for k,v in states.items()}
    for slot in range(int(row[144])):
        at=limits['EVENT_BASE']+index*limits['EVENT_WORDS']+slot*8
        if words[at]==30:words[at+4]=keys[inverse[int(row[145+slot*7+3])]]
    for slot in range(int(row[14])):
        kind,name,arg=row[15+slot*3:18+slot*3]
        if int(kind) in (18,19,20,21):
            at=limits['CONDITION_BASE']+index*limits['CONDITION_WORDS']+slot*4;words[at+1]=keys[inverse[int(name)]]
            if int(kind)==21:
                if arg!=int(arg) or not 1<=arg<=2**31-1:raise ValueError('Resource modulus outside positive wire range')
                rem=row[66+slot]
                if rem!=int(rem) or not -2**31<=rem<=2**31-1:raise ValueError('Resource remainder outside signed wire range')
                words[limits['RESOURCE_CONDITION_BASE']+index*3+slot]=int(rem)&0xffffffff
