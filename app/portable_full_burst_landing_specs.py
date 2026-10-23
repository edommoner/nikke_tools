"""Static opt-in plan for full-burst landing; live gates/counts stay GPU-owned."""
from attack_timing_specs import full_burst_landing

def validate(effect,*,combat,world_frame):
    if 'land_in_full_burst' not in effect:return
    if combat is None or not world_frame:raise ValueError('Full-burst landing requires a private combat world')
    full_burst_landing(effect,3)

def compiler_effect(effect):
    if 'land_in_full_burst' not in effect:return effect
    stat=effect.get('stat','');root,sep,suffix=stat.partition(':')
    if sep and suffix.lstrip('-').isdigit() and int(suffix)<0:return dict(effect,stat=root+':0')
    return effect

def plan(effect,caster):
    return full_burst_landing(effect,caster.get('burst_stage',caster['_weapon'].get('burst_stage')))

MAGIC=0x46424c31
OFFSET=17
