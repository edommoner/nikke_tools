"""Complete original definitions plus one explicitly declared typed damage probe.

This is the existing typed Frame route, not public coordinate/weapon targeting.
"""
import copy,struct
from portable_target_modifier_input import lower_effect,pack_axes
from portable_projectile_roster_input import compile_projectile_battle
from destructible_world_runtime import compile_bindings
from destructible_skill_specs import coefficient

SOURCE='gpu/destructible_original_modifier_entry.slang'
INPUT_WORDS=110112
OUTPUT_WORDS=1048576

def pack_target_input(words,meta,original,patterns,bindings,probe_row,probe_kind,max_attacks,*,weapon_only=False,logical_owner_bindings=False):
    """Same typed input block at either arena base; no battle/schedule evaluation."""
    if type(weapon_only) is not bool or weapon_only and probe_row is not None:raise ValueError('Weapon-only descriptor cannot name a skill probe')
    if type(logical_owner_bindings) is not bool or logical_owner_bindings and not weapon_only:raise ValueError('Logical owners require their explicit weapon-only descriptor')
    if logical_owner_bindings:
        from coordinate_typed_actor_policy import validate_bindings,LOGICAL_FIELD_MODE
        validate_bindings({'mode':LOGICAL_FIELD_MODE},bindings)
    axes=pack_axes(words,meta,[r['effect'] for r in original]);source=0xffffffff if weapon_only else meta['binding_source_indices'].index(probe_row)
    _,_,rows=compile_bindings([dict(id=p['id']) for p in patterns],bindings)
    if any(int(r.handle.kind)!=probe_kind for r in rows):raise ValueError('Probe binding kind must match its declared typed route')
    if probe_kind==3 and not logical_owner_bindings and any(r.owner is None or (int(r.owner.kind),r.owner.identity,r.owner.generation)!=(0,0,1) for r in rows):raise ValueError('HP probe requires the explicit boss owner generation')
    extra=[0]*5712;extra[2320]=len(rows)
    for slot,row in enumerate(rows):
        at=2328+slot*12;owner=[0xffffffff,0,0] if row.owner is None else [int(row.owner.kind),row.owner.identity,row.owner.generation]
        extra[at:at+8]=[row.node,int(row.handle.kind),row.handle.identity,*struct.unpack('<II',struct.pack('<d',row.capacity)),*owner]
    extra[5120:5124]=[source,max_attacks,1,0x44425431];extra[5136]=0x444d4231;extra[5168:5424]=axes;extra[5680:5684]=[0x48534931,0,0,1]
    if not weapon_only:extra[5424+source]=probe_kind
    return extra,axes

def compile_probe(prepared,bindings,probe_row,*,max_attacks=128,probe_kind=2):
    if type(probe_row) is not int or not 0<=probe_row<len(prepared['effects']):raise ValueError('Explicit declared probe source required')
    if type(max_attacks) is not int or not 1<=max_attacks<=128:raise ValueError('Bounded original probe attacks required')
    if type(probe_kind) is not int or probe_kind not in (2,3):raise ValueError('Explicit projectile or HP shield probe kind required')
    original=prepared['effects'];probe=original[probe_row]['effect']
    if probe.get('target')!=('all_projectiles' if probe_kind==2 else 'boss'):raise ValueError('Explicit typed probe target required')
    if probe_kind==3 and any(i!=probe_row and row['effect'].get('type')=='damage' and row['effect'].get('target')=='boss' for i,row in enumerate(original)):raise ValueError('HP probe requires no other literal boss damage selectors')
    character=next(c for c in prepared['chars'] if c['name']==original[probe_row]['owner']);coefficient(dict(probe,target='all_projectiles'),character)
    if prepared['enemy'].get('coord') is not None:raise ValueError('Coordinate typed target binding is not yet declared')
    nearby=[i for i,r in enumerate(original) if r['effect'].get('target')=='target_and_nearby:2']
    if nearby:
        # A closed one-enemy universe has no neighbours. This specialization
        # is forbidden as soon as a part, summon/ADD or geometry is declared;
        # it does not admit this selector in the general compiler.
        from portable_actor_specs import compile_registry
        from calculator.boss_pattern import validate
        _,actors=compile_registry(validate(prepared['enemy']['patterns']),pools=True)
        if len(actors)!=1 or int(actors[0].kind)!=0 or prepared['enemy'].get('has_parts') or prepared['enemy'].get('part_break_interval',0):raise ValueError('Nearby specialization requires one plain boss and no other enemy actors')
    lowered=copy.deepcopy(prepared)
    for dest,item in zip(lowered['effects'],original,strict=True):dest['effect']=lower_effect(item['effect'])
    for index in nearby:lowered['effects'][index]['effect']['target']='boss'
    lowered['effects'][probe_row]['effect']['target']='boss'
    words,meta=compile_projectile_battle(lowered);extra,axes=pack_target_input(words,meta,original,prepared['enemy']['patterns'],bindings,probe_row,probe_kind,max_attacks)
    words.extend(extra)
    if len(words)!=INPUT_WORDS:raise ValueError('Typed original modifier input stride changed')
    meta['declared_original_modifier_probe']=dict(original_definitions=probe_row,probe_source=probe_row,axis_rows=axes,single_boss_nearby_rows=nearby,coordinate=False,automatic_projectile_aim=False,in_game_rules_verified=False)
    return words,meta
