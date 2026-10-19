"""Static stack policies; mutations, target selection and notices stay GPU owned."""
import math
import struct
from portable_recipient_specs import admitted
from portable_enemy_specs import enemy_buff_plan

KINDS={'buff_stack_add':16,'buff_stack_remove':17,'buff_stack_init':18,'buff_max_stack_add':19,'debuff_stack_add':20,'debuff_stack_remove':21}
META_MAGIC=0x53544b31

def operation(effect):return KINDS.get(effect.get('stat'),0)

def plan(effect,*,combat=None):
    op=operation(effect)
    if not op:return None
    if effect.get('type')!=('buff' if op==19 else 'instant'):raise ValueError('Stack operation has the wrong effect kind')
    if not isinstance(effect.get('target_effect',''),str):raise ValueError('Stack reference name must be a string')
    if effect.get('scaling') not in (None,'stack_count') or effect.get('scaling') and op not in (20,21):raise ValueError('Only debuff stack operations support a stack reference')
    if effect.get('scaling_ref') is not None and (not isinstance(effect['scaling_ref'],str) or ':' in effect['scaling_ref']):raise ValueError('Invalid stack delta reference')
    target=effect.get('target','self')
    if not isinstance(target,str):raise ValueError('Stack target must be a string')
    from calculator.buff_manager import _NIKKE
    if admitted(target,instant=True) or target in _NIKKE:return op,1,None
    enemy=enemy_buff_plan(dict(type='buff',stat='def_pct',target=target))
    if enemy is not None:
        if combat is None:raise ValueError('Enemy stack operations require combat-owned targets')
        return op,2,enemy
    raise ValueError('Unported stack-operation recipient selector')

def value(effect,char):
    from calculator.buff_manager import _get_skill_lv
    op=operation(effect)
    if 'fixed_value' in effect:
        raw=effect['fixed_value']
        if type(raw) is int and raw.bit_length()>1023:raise ValueError('Stack delta is outside finite binary64 input')
        if type(raw) not in (int,float) or not math.isfinite(raw):raise ValueError('Stack delta must be finite')
        if op==19 and type(raw) is int and int(float(raw))!=raw:raise ValueError('Maximum-stack literal loses integer precision')
        return float(raw)
    values=effect.get('values') or {}
    result=float(values.get(_get_skill_lv(char,effect),values.get('10',1 if op==19 else 0)))
    if not math.isfinite(result):raise ValueError('Stack delta must be finite')
    return result

def pack_metadata(words,L,effects,double_words):
    if not any(operation(e) for e,_ in effects):return
    # MODE_BASE is a tagged union: weapon modes retain all 32 original words.
    # Nonweapon records carry the literal native duration and init binding.
    for i,(e,owner) in enumerate(effects):
        if e.get('type')=='weapon_change':continue
        buff=e.get('type')=='buff'
        duration=e.get('duration')
        bits=[0,0x7ff00000] if duration in (None,-1) else double_words(duration)
        selected=next((j+1 for j,(target,caster) in enumerate(effects) if caster==owner and target.get('type')=='buff' and target.get('name')==e.get('target_effect') and e.get('target_effect')),0) if operation(e)==18 else 0
        at=L['MODE_BASE']+i*L['MODE_WORDS']
        from calculator.buff_manager import _has_runtime_cond
        runtime=buff and _has_runtime_cond(e.get('trigger',{}).get('condition',[]),math.inf if duration in (None,-1) else duration,e.get('duration_bullets',-1))
        words[at:at+6]=[META_MAGIC,int(buff),*bits,selected,int(runtime)]
