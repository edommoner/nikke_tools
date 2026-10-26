"""Complete original preparation into the existing shared coordinate executor.

Only literal shapes, policies and original weapon metadata are normalized.
No CPU battle, target resolution, damage or time schedule enters the GPU input.
"""
import copy,hashlib,json
from portable_specs import LIMITS as L
SOURCE='gpu/world_coordinate_original_entry.slang'
INPUT_WORDS=109968
OUTPUT_WORDS=1769856

def compile_coordinate_battle(prepared,*,typed_aim_targets=None):
    from portable_world_roster_input import compile_world_battle
    from portable_projectile_specs import finalize_program
    from portable_coordinate_scene_specs import compile_scene,LAYOUT as C
    from portable_coordinate_area_specs import compile_area
    from portable_coordinate_matrix_specs import compiler_policy
    from portable_coordinate_core_specs import compile_core
    from portable_coordinate_aim_wire import pack as pack_aim
    from portable_cover_policy_specs import normalize as cover_normalize,pack as pack_cover
    from portable_squad_control_specs import pack as pack_squad
    from portable_squad_mode_specs import mark
    from portable_burst_control_specs import pack as pack_burst
    from portable_enemy_target_specs import META_BASE,normalize_seed
    from runner.spec import build_config
    from portable_actor_specs import compile_registry
    from calculator.boss_pattern import validate
    from portable_group_binding import lower,bind
    chars=prepared['chars'];names=[c['name'] for c in chars];enemy=prepared['enemy'];cfg=prepared['policies']['config']
    damage_names=[e['effect']['name'] for e in prepared['effects'] if e['effect'].get('type')=='damage']
    if len(damage_names)!=len(set(damage_names)):
        duplicates={n for n in damage_names if damage_names.count(n)>1}
        if any(not e['effect'].get('tick_interval') for e in prepared['effects'] if e['effect'].get('type')=='damage' and e['effect']['name'] in duplicates):raise ValueError('Original nonperiodic damage labels require owner-aware native observation')
    patterns=enemy.get('patterns') or [dict(id='portable-empty-world',kind='idle')]
    case=dict(name='original-coordinate',names=names,duration=cfg['duration'],enemy=copy.deepcopy(enemy),patterns=copy.deepcopy(patterns),controls=[copy.deepcopy(c.get('control',{})) for c in chars],control_mode=cfg.get('control_mode','solo'))
    lowered,original,owners=lower(prepared)
    words,meta=compile_world_battle(lowered,trace='full',allow_physical_interrupt=bool(cfg.get('aim_interrupt')),coordinate=True)
    if owners:bind(words,meta,original)
    finalize_program(words)
    if len(words)!=104400:raise ValueError('Original base world stride changed')
    scene,desc=compile_scene(dict(patterns=patterns,commands=[('capture',cfg['duration'],0,0)]),allow_core=True,allow_summons=True,allow_world_nodes=True)
    _,bindings=compile_registry(validate(patterns,coord=True),pools=True)
    for i,row in enumerate(desc['rows']):
        slots=[j for j,b in enumerate(bindings) if int(b.kind)==row['kind'] and b.identity==row['identity']]
        if len(slots)!=1:raise ValueError('Original coordinate actor binding is ambiguous')
        row['slot']=slots[0];scene[C['ROW_BASE']+i*C['ROW_WORDS']+5]=slots[0]
    area_case=copy.deepcopy(case)
    for control in area_case['controls']:control.pop('aim',None)
    if area_case['enemy']['coord'].get('auto_aim') is None:area_case['enemy']['coord']['auto_aim']=[0,0]
    with compiler_policy():area=compile_area(area_case,desc,explosion_ranges=[c['_weapon'].get('spot_explosion_range') for c in chars])
    words += [0x41475331,2,owners,1,0,0,0,0]+scene+area+compile_core(case,desc['patterns'])
    if len(words)!=108792:raise ValueError('Original coordinate core stride changed')
    words+=pack_aim(case,desc,meta,typed_targets=typed_aim_targets)
    policy_chars=copy.deepcopy(chars)
    for c in policy_chars:c.get('control',{}).pop('burst',None)
    policy=pack_cover(cover_normalize(policy_chars,prepared['base_atk'],enemy),names,meta['states']);words+=policy
    words=mark(words+pack_squad([],names))
    resolved=build_config(chars,cfg)
    waits={c['name']:c['control']['burst']['wait_own_cooldown'] for c in chars if 'wait_own_cooldown' in (c.get('control',{}).get('burst') or {})}
    words+=pack_burst(names,delays=resolved.get('burst_delay'),waits=waits,patterns=resolved.get('burst_pattern'),sequence=resolved.get('burst_sequence'))
    seed=normalize_seed(prepared['policies']['seed']);words[META_BASE+1:META_BASE+3]=[seed&0xffffffff,seed>>32];meta['enemy_targeting']['seed']=seed
    if len(words)!=INPUT_WORDS:raise ValueError('Original complete coordinate stride changed')
    if set(meta['binding_source_indices'])!=set(range(len(prepared['effects']))):raise ValueError('Original definition coverage is incomplete')
    if typed_aim_targets is not None or any(c.get('aim') for c in case['controls']):words[L['WORLD_META_BASE']+4]=0x46414330|int(bool(cfg.get('aim_interrupt')))
    meta['coordinate_original_input']=dict(all_effects_included=True,prepared_definitions=len(prepared['effects']),bound_definitions=len(meta['effects']),policy_mask=policy[2],original_weapon_metadata_preserved=True,original_controls_preserved=True,cpu_battle_executed=False,reference_kind='deterministic-common-cpu',physical_rng='sampled',definitions_sha256=hashlib.sha256(json.dumps(prepared['effects'],ensure_ascii=False,sort_keys=True).encode()).hexdigest())
    if owners:meta['coordinate_original_input']['group_owners']=owners
    return words,meta,bindings,desc
