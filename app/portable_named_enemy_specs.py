"""Opaque named-enemy operand in nonweapon MODE24..27; no runtime CPU choices."""
import copy
PREFIX='enemies_with_buff:'
ROUTE=11
MAGIC=0x4e455231
OFFSET=24

def name(effect):
    target=effect.get('target','self')
    return target[len(PREFIX):] if isinstance(target,str) and target.startswith(PREFIX) else None

def selection_name(effect):
    if effect.get('type')=='instant' and effect.get('stat')=='remove_named_buff' and effect.get('remove_scope','global')=='global':return None
    return name(effect)

def validate(effect,*,combat,world_frame):
    if selection_name(effect) is None:return
    if combat is None or not world_frame:raise ValueError('Named enemy recipients require a private combat world')
    if effect.get('type')=='buff':
        from portable_enemy_specs import ENEMY_BUFF_STATS
        from portable_status_specs import immunity
        if effect.get('stat') not in ENEMY_BUFF_STATS and effect.get('stat') not in (None,'') and not immunity(effect):raise ValueError('Unported named enemy buff consumer')
    elif effect.get('type')=='instant':
        if effect.get('stat') not in ('named_buff_duration_extend','remove_named_buff'):raise ValueError('Unported named enemy instant consumer')
    elif effect.get('type')!='damage':raise ValueError('Unported named enemy consumer')

def compiler_effect(effect):
    if name(effect) is None:return effect
    result=copy.deepcopy(effect);result['target']='boss';return result

def allocate_names(effects,states):
    for e,_ in effects:
        value=selection_name(e)
        if value is not None:states.setdefault(value,len(states))
    if len(states)>256:raise ValueError('Named enemy identity capacity exceeded')

def pack(words,L,effects,states):
    if not any(selection_name(e) is not None for e,_ in effects):return
    for i,(e,_) in enumerate(effects):
        value=selection_name(e)
        empty=e.get('name')=='' and (e.get('type')=='buff' or e.get('type')=='damage' and e.get('stat')=='dot_damage')
        if value is None and not empty:continue
        if e.get('type')=='weapon_change':raise ValueError('Named enemy payload overlaps weapon MODE')
        at=L['MODE_BASE']+i*L['MODE_WORDS']+OFFSET
        if any(words[at:at+4]):raise ValueError('Named enemy payload overlaps existing MODE data')
        words[at:at+4]=[MAGIC,0 if value is None else states[value]+1,int(value=='')|(int(empty)<<1),0]
