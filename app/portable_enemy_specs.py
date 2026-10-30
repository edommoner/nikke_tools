"""Static enemy damage plans; selection and hit execution remain GPU owned."""
import re
from portable_damage_specs import DAMAGE_FAMILIES

ROUTES=dict(INHERITED=0,BODY=1,ALL=2,MAX_HP=3,CURRENT_HP=4,LOW_HP=5,NEAREST=6,TOP_DEF=7,LOW_DEF=8,TOP_ATK=9,RANDOM=10)

def lower_single_body_nearby(prepared):
    """Exact recipient specialization when the only logical enemy is BODY.

    Never infer neighbour distance or ordering. Additional actors or coordinate
    geometry keep this selector unsupported instead of silently losing hits.
    """
    import copy
    rows=[i for i,item in enumerate(prepared['effects']) if isinstance(item['effect'].get('target'),str)
          and item['effect']['target'].startswith('target_and_nearby:')]
    if not rows:return prepared,rows
    for i in rows:
        effect=prepared['effects'][i]['effect']
        match=re.fullmatch(r'target_and_nearby:([1-9][0-9]*)',effect['target'])
        if effect.get('type')!='damage' or match is None or int(match[1])>127:
            raise ValueError('Unsupported nearby recipient count or effect kind')
    enemy=prepared['enemy']
    from portable_actor_specs import compile_registry
    from calculator.boss_pattern import validate
    _,actors=compile_registry(validate(enemy.get('patterns') or []),pools=True)
    if len(actors)!=1 or int(actors[0].kind)!=0 or enemy.get('coord') is not None or enemy.get('has_parts') or enemy.get('part_break_interval',0):
        raise ValueError('Nearby specialization requires one plain boss and no other enemy actors')
    lowered=copy.deepcopy(prepared)
    for i in rows:lowered['effects'][i]['effect']['target']='boss'
    return lowered,rows


def damage_plan(effect):
    from portable_parent_fixed_specs import enabled
    if enabled(effect):
        from quantity_specs import validate_quantity
        validate_quantity(effect);return damage_plan(dict(effect,stat='damage'))
    if effect.get('stat')=='accum_split_damage':return damage_plan(dict(effect,stat='split_damage'))
    stat=effect.get('stat','')
    if not isinstance(stat,str):raise ValueError('Damage family must be a string')
    parts=stat.split(':')
    if len(parts)>2 or parts[0] not in DAMAGE_FAMILIES:raise ValueError('Unported damage family')
    hits=1
    if len(parts)==2:
        if not parts[1]:raise ValueError('Empty hit count reference')
        if parts[1].lstrip('-').isdigit():
            negative_landing=-256<=int(parts[1])<0
            if not negative_landing and (not re.fullmatch(r'(?:0|[1-9][0-9]*)',parts[1]) or not 0<=int(parts[1])<=256):raise ValueError('Damage hit count must be an integer in 0..256')
            hits=max(0,int(parts[1]))
    target=effect.get('target','target');count=1
    from portable_named_enemy_specs import name as named_enemy_name,ROUTE as NAMED_ENEMY_ROUTE
    if named_enemy_name(effect) is not None:return NAMED_ENEMY_ROUTE,128,hits
    if target=='enemies_random' or isinstance(target,str) and target.startswith('enemies_random:'):
        raw=target.partition(':')[2]
        if raw and (not re.fullmatch(r'[1-9][0-9]*',raw) or int(raw)>256):raise ValueError('Random enemy count must be1..256')
        if target.endswith(':'):raise ValueError('Missing random enemy count')
        return ROUTES['RANDOM'],min(int(raw or 1),128),hits
    if isinstance(target,str) and target.startswith(('enemies_code:','enemies_lowest_hp_code:')):
        parts=target.split(':')
        if len(parts) not in (2,3) or not parts[1] or len(parts)==3 and (not re.fullmatch(r'[1-9][0-9]*',parts[2]) or int(parts[2])>256):
            raise ValueError('Malformed enemy code selector')
        # Native has no add element codes and intentionally returns boss only.
        return ROUTES['BODY'],1,hits
    if target=='target':route=ROUTES['INHERITED']
    elif target in ('enemy','target_body','same_target','enemies_nearest_in_range') or isinstance(target,str) and target.startswith('same_target:') and bool(target.split(':',1)[1]):route=ROUTES['NEAREST']
    elif target=='boss':route=ROUTES['BODY']
    elif target in ('all_enemies','enemies_in_range'):route=ROUTES['ALL'];count=8
    else:
        match=re.fullmatch(r'enemies_(top_hp|highest_hp|lowest_hp|nearest|top_def|lowest_def|top_atk):([1-9][0-9]*)',target) if isinstance(target,str) else None
        if not match or not 1<=int(match[2])<=256:raise ValueError('Unported enemy damage selector')
        count=int(match[2]);route=ROUTES[dict(top_hp='MAX_HP',highest_hp='CURRENT_HP',lowest_hp='LOW_HP',nearest='NEAREST',top_def='TOP_DEF',lowest_def='LOW_DEF',top_atk='TOP_ATK')[match[1]]]
    return route,count,hits


ENEMY_BUFF_STATS=frozenset(('buff_stack_add','dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct','dmg_accum_rate_pct','atk_pct','atk_caster_based_pct','taunt','stun','stun_immune','def_pct','def_caster_based_pct','received_dmg_pct','dmg_scale_mag_pct','atk_buff_mag_pct','received_dmg_buff_mag_pct','stack_change_immune','buff_max_stack_add'))

def enemy_buff_plan(effect):
    """Same enemy selectors as damaging packets; current-target keeps context."""
    from portable_status_specs import immunity
    if effect.get('type')!='buff' or effect.get('stat') not in ENEMY_BUFF_STATS and effect.get('stat') not in (None,'') and not immunity(effect):return None
    target=effect.get('target','self')
    if not isinstance(target,str) or target.startswith('all') and target!='all_enemies' or target.startswith('self') or target.startswith('allies'):return None
    from enemy_recipient_specs import CURRENT_TARGETS
    if target in CURRENT_TARGETS:return ROUTES['INHERITED'],1
    try:route,count,_=damage_plan(dict(stat='damage',target=target))
    except ValueError:return None
    return route,count
