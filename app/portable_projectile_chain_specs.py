"""Static named completion metadata; runtime packets and callbacks stay shared."""
PREFIX='weapon_hit:'
EVENT=51
STAT=92
FLAG=524288

def ordinary(effect):return effect.get('type')=='buff' and effect.get('stat')=='buff_stack_add'
def reference(timing):return timing[len(PREFIX):] if isinstance(timing,str) and timing.startswith(PREFIX) else None
def compiler_effect(effect):
    out=dict(effect,stat='') if ordinary(effect) else dict(effect)
    timings=effect.get('trigger',{}).get('timing',[])
    if any(reference(t) is not None for t in timings):out['trigger']=dict(effect['trigger'],timing=['event:'+reference(t) if reference(t) is not None else t for t in timings])
    if out.get('type')=='damage' and out.get('stat')=='accum_split_damage':
        out.pop('fixed_value',None);out.pop('values',None)
    stat=out.get('stat','')
    if out.get('type')=='damage' and isinstance(stat,str) and stat.rpartition(':')[2].startswith('-') and stat.rpartition(':')[2][1:].isdigit():out['stat']=stat.rpartition(':')[0]+':0'
    return out

def negative_count(effect):
    stat=effect.get('stat','');parts=stat.rsplit(':',1) if isinstance(stat,str) else []
    return len(parts)==2 and parts[1].startswith('-') and parts[1][1:].isdigit() and -256<=int(parts[1])<0

def validate(effect,combat,world_frame):
    if ordinary(effect) or any(reference(t) is not None for t in effect.get('trigger',{}).get('timing',[])) or negative_count(effect):
        if combat is None or not world_frame:raise ValueError('Projectile handler completion requires a private combat world')
    if ordinary(effect) and effect.get('scaling') not in (None,):raise ValueError('Unported ordinary stack-carrier scaling')
