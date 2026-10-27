"""Original prepared roster, weapon, controls and every source effect retained."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
composition=load('original_lock_composition','research/verify-lock-projectile-composition.py')
enemy=load('original_lock_enemy','research/verify-lock-enemy-carriers.py')

def prepare_case(duration=3,adds=0):
    from portable_heavyarms_lock_cases import fixtures,source_definitions,NAME
    from portable_coordinate_original_cases import prepare_case as original_case
    from portable_charge_clock_specs import normalize_static_clock
    row=copy.deepcopy(next(r for r in fixtures() if r['body'].get('duration')==duration))
    patterns=[dict(id='typed',kind='idle',until=dict(time=duration))]
    if adds:patterns.insert(0,dict(id='lock-wave',kind='summon',spec=dict(count=adds,hp=1e30)))
    row.update(name='original-heavyarms/'+str(duration)+'s/'+str(adds)+'adds',coord=None,patterns=patterns)
    row['body']['enemy']['patterns']=copy.deepcopy(patterns)
    original,prepared=original_case(row)
    c=copy.deepcopy(composition.fixtures()[0])
    for key in ('name','names','duration','seed','enemy','patterns','effects','owners','base_atk','skill_levels','controls','combat','environment','original_run','control_mode'):c[key]=original[key]
    c.update(packet_skill=source_definitions()[8]['name'],max_attacks=128,source_effect_identity=True,observe_named_state=True,state_queries=[],observe_authored_effect_lookup=True)
    c['post_fire_delays']=normalize_static_clock(prepared['chars'],prepared['base_atk'],prepared['enemy'])
    original_defs=[e['effect'] for e in prepared['effects'] if e['owner']==NAME]
    if any(e not in original_defs for e in source_definitions()):raise ValueError('Original Heavyarms definition missing')
    return c,prepared

def compile_case(c):
    from unittest.mock import patch
    from portable_projectile_roster_input import compile_projectile_battle
    from portable_actor_specs import compile_registry
    from calculator.boss_pattern import validate
    def original_pack(lowered):
        prepared=copy.deepcopy(c['original_run']['prepared']);prepared['enemy']=copy.deepcopy(c['enemy'])
        prepared['effects']=[dict(effect=copy.deepcopy(e),owner=c['names'][owner]) for e,owner in zip(lowered['effects'],lowered['owners'],strict=True)]
        words,meta=compile_projectile_battle(prepared,trace='full')
        _,bindings=compile_registry(validate(c['patterns']),pools=True)
        return words,meta,bindings
    with patch.object(enemy.parent.parent,'compile_case',original_pack),patch.object(composition.typed.base,'compile_case',enemy.compile_case):
        words,domain=composition.typed.compile_case(c)
    return words,domain[1],domain[2]

def native_reference(domain):return composition.native_reference(domain,enemy_carrier=True)
