"""Real owned/growth preparation without CPU battle execution.

This stage exposes every real definition and policy. It does not silently
filter unsupported character effects or enable normal-UI GPU acceptance.
"""
import copy
from calculator.boss_pattern import DEFAULT_BOSS_ATK
from calculator.buff_manager import BuffManager
from calculator.timeline import DEFAULT_ENEMY, _NIKKE
from portable_weapon_input import normalize_static_weapon


def prepare_static_inputs(prepared, stats):
    enemy={**DEFAULT_ENEMY,**(prepared.enemy or {})}
    base={c['name']:stats(c) for c in prepared.squad}
    bm=BuffManager(prepared.squad,state=dict(base_stats=base,enemy=enemy,full_burst=False,rng_acc={}))
    chars=[{**copy.deepcopy(c),'_weapon':copy.deepcopy(_NIKKE[c['name']])} for c in prepared.squad]
    return dict(chars=chars,effects=[dict(effect=copy.deepcopy(e),owner=n) for e,n in bm._effects],
                base_atk=[base[c['name']]['atk'] for c in chars],
                allies=[dict(base_hp=base[c['name']]['hp'],base_defense=base[c['name']]['def']) for c in chars],
                weapons=[normalize_static_weapon(c,base[c['name']]['atk'],enemy) for c in chars],
                enemy=copy.deepcopy(enemy),policies=dict(config=copy.deepcopy(prepared.config),
                    controls={c['name']:copy.deepcopy(c.get('control',{})) for c in chars},auto=prepared.auto,expected=prepared.expected),
                cpu_battle_executed=False,full_battle_connected=False,all_character_effects_included=True)


def compile_static_battle(prepared, *, trace='summary'):
    """Connect complete real preparation for the currently modeled policies.

    This is an experimental input path, not full-catalog certification. Every
    prepared definition is compiled. Unsupported controls/worlds fail closed.
    """
    from portable_runtime import compile_program,UnsupportedPortable,validate_effect
    from calculator.timeline import DEFAULT_CONFIG,_resolve_cameras
    if prepared.get('cpu_battle_executed') is not False or prepared.get('all_character_effects_included') is not True:
        raise UnsupportedPortable('Expected complete static preparation without CPU battle execution')
    chars=prepared['chars'];names={c['name'] for c in chars};policies=prepared['policies'];cfg=policies['config']
    if len(chars)!=5 or len(names)!=5:raise UnsupportedPortable('Real portable battle needs five unique characters')
    allowed={'duration','rng_mode','burst_gauge_mode','first_burst_time','allow_unparsed','aim_interrupt','camera','camera_mode'}
    if set(cfg)-allowed or cfg.get('burst_gauge_mode')!='accumulate' or cfg.get('rng_mode')!='expected' or policies.get('expected') is not True:
        raise UnsupportedPortable('Unported real battle policy; expected accumulate mode is required')
    if cfg.get('allow_unparsed',False) or cfg.get('aim_interrupt',False):raise UnsupportedPortable('Unparsed effects/interrupt aiming are not accepted')
    if set(policies['auto'])!=names or any(policies['controls'].values()) or any(c.get('control') for c in chars):
        raise UnsupportedPortable('Real manual shooting/burst controls are not connected')
    enemy=prepared['enemy']
    if set(enemy)-{'def','code','core_px','has_parts','part_break_interval','optimal_range_weapons','distance','coord','atk','patterns'}:
        raise UnsupportedPortable('Unknown real enemy fields')
    if enemy.get('patterns') or enemy.get('coord') is not None or enemy.get('has_parts') or enemy.get('part_break_interval',0):
        raise UnsupportedPortable('Real enemy world/protection/part scheduling is not connected')
    cameras=_resolve_cameras(chars,{**DEFAULT_CONFIG,**cfg})
    weapons=[normalize_static_weapon(c,attack,enemy,camera=c['name'] in cameras) for c,attack in zip(chars,prepared['base_atk'])]
    for item in prepared['effects']:
        try:validate_effect(item['effect'],combat=dict(weapons=weapons))
        except ValueError as error:
            raise UnsupportedPortable(item['owner']+'/'+item['effect']['name']+' ('+item['effect'].get('stat','')+'): '+str(error)) from error
    duration=cfg['duration']
    program,metadata=compile_program(chars,[(x['effect'],x['owner']) for x in prepared['effects']],
        [[duration,24,0,0,0,-1,0,0],[duration,2,0,0,-1,0,0,0]],prepared['base_atk'],allies=prepared['allies'],cover_sync=False,
        combat=dict(weapons=weapons,targets=[dict(hp=1e30,defense=enemy['def'],attack=enemy.get('atk',DEFAULT_BOSS_ATK))],trace=trace,clock='accumulated'))
    metadata['real_prepared_input']=dict(all_character_effects_included=True,prepared_effects=len(prepared['effects']),
        camera=sorted(cameras),policies=copy.deepcopy(policies),cpu_battle_executed=False,full_catalog_certified=False)
    return program,metadata
