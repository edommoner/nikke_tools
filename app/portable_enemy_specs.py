"""Static enemy damage plans; selection and hit execution remain GPU owned."""
import re
from portable_damage_specs import DAMAGE_FAMILIES

ROUTES=dict(INHERITED=0,BODY=1,ALL=2,MAX_HP=3,CURRENT_HP=4,LOW_HP=5,NEAREST=6,TOP_DEF=7,LOW_DEF=8,TOP_ATK=9)


def damage_plan(effect):
    stat=effect.get('stat','')
    if not isinstance(stat,str):raise ValueError('Damage family must be a string')
    parts=stat.split(':')
    if len(parts)>2 or parts[0] not in DAMAGE_FAMILIES:raise ValueError('Unported damage family')
    hits=1
    if len(parts)==2:
        if not re.fullmatch(r'[1-9][0-9]*',parts[1]) or not 1<=int(parts[1])<=256:raise ValueError('Damage hit count must be an integer in 1..256')
        hits=int(parts[1])
    target=effect.get('target','target');count=1
    if target=='target':route=ROUTES['INHERITED']
    elif target in ('enemy','target_body','same_target','enemies_nearest_in_range') or isinstance(target,str) and re.fullmatch(r'same_target:[^:]+',target):route=ROUTES['NEAREST']
    elif target=='boss':route=ROUTES['BODY']
    elif target in ('all_enemies','enemies_in_range'):route=ROUTES['ALL'];count=8
    else:
        match=re.fullmatch(r'enemies_(top_hp|highest_hp|lowest_hp|nearest|top_def|lowest_def|top_atk):([1-9][0-9]*)',target) if isinstance(target,str) else None
        if not match or not 1<=int(match[2])<=256:raise ValueError('Unported enemy damage selector')
        count=int(match[2]);route=ROUTES[dict(top_hp='MAX_HP',highest_hp='CURRENT_HP',lowest_hp='LOW_HP',nearest='NEAREST',top_def='TOP_DEF',lowest_def='LOW_DEF',top_atk='TOP_ATK')[match[1]]]
    if effect.get('tick_interval') and route not in (ROUTES['INHERITED'],ROUTES['BODY']):raise ValueError('Multi-target periodic damage requires per-recipient clocks')
    return route,count,hits


ENEMY_BUFF_STATS=frozenset(('def_pct','def_caster_based_pct','received_dmg_pct'))

def enemy_buff_plan(effect):
    """Same enemy selectors as damaging packets; current-target keeps context."""
    if effect.get('type')!='buff' or effect.get('stat') not in ENEMY_BUFF_STATS:return None
    target=effect.get('target','self')
    if not isinstance(target,str) or target.startswith('all') and target!='all_enemies' or target.startswith('self') or target.startswith('allies'):return None
    from enemy_recipient_specs import CURRENT_TARGETS
    if target in CURRENT_TARGETS:return ROUTES['INHERITED'],1
    try:route,count,_=damage_plan(dict(stat='damage',target=target))
    except ValueError:return None
    return route,count
