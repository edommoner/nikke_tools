"""One definition clock, retained recipients and single-stack named DoT union."""
from portable_enemy_specs import damage_plan


def periodic_groups(effects):
    names={}
    for i,(e,owner) in enumerate(effects):
        if e.get('name'):names.setdefault((owner,e['name']),[]).append(i)
    groups={}
    for ids in names.values():
        if len(ids)<2:continue
        if all(effects[i][0].get('type')=='damage' and effects[i][0].get('stat')=='dot_damage' and effects[i][0].get('tick_interval') and effects[i][0].get('max_stack',1)==1 for i in ids):
            for i in ids:groups[i]=ids[0]+1
    return groups


def periodic_flags(effect,group,*,world_frame=False):
    if effect.get('type')!='damage' or not effect.get('tick_interval'):return 0
    retained=world_frame or damage_plan(effect)[0]>=2 or group!=0
    return int(retained) | (int(effect.get('scaling')=='stack_count')<<1) | (int(bool(effect.get('name')))<<2)
