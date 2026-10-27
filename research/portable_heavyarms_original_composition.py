"""Original prepared roster, weapon, controls and every source effect retained."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
composition=load('original_lock_composition','research/verify-lock-projectile-composition.py')
enemy=load('original_lock_enemy','research/verify-lock-enemy-carriers.py')

def prepare_case(duration=3,adds=0,*,cover=None,parts=False,injury=False,break_parts=False,mary_first=False,mary_low=False):
    from portable_heavyarms_lock_cases import fixtures,source_definitions,NAME
    from portable_coordinate_original_cases import prepare_case as original_case
    from portable_charge_clock_specs import normalize_static_clock
    row=copy.deepcopy(next(r for r in fixtures() if r['body'].get('duration')==duration))
    if any(type(v) is not bool for v in (parts,injury,break_parts,mary_first,mary_low)):raise ValueError('Explicit literal parts/injury scenario flags required')
    if break_parts and not parts or mary_low and not (injury and mary_first):raise ValueError('Invalid original scenario combination')
    if mary_first:row['body']['squad'][1],row['body']['squad'][4]=row['body']['squad'][4],row['body']['squad'][1]
    patterns=[dict(id='typed',kind='idle',until=dict(time=duration))]
    if parts:
        patterns.insert(0,dict(id='original-parts',kind='parts',delay=.5,targets=[dict(name='original-part-'+str(i),hp=1 if break_parts else 1e30,reach=1) for i in range(2)]))
    if injury:
        patterns.insert(0,dict(id='original-injury',kind='attack',delay=.5,spec=dict(atk=300000,coeff=100,target='all',pierce=True,hits=3,interval=.1)))
        patterns.append(dict(id='original-after-heal',kind='attack',delay=5.,spec=dict(atk=300000,coeff=100,target='all',pierce=True)))
    if mary_low:patterns.append(dict(id='original-low-mary',kind='attack',delay=.8,spec=dict(atk=2000000,coeff=100,target='slot:2',pierce=True)))
    if adds:patterns.insert(0,dict(id='lock-wave',kind='summon',delay=3. if parts else 0.,spec=dict(count=adds,hp=1e30)))
    row.update(name='original-heavyarms/'+str(duration)+'s/'+str(adds)+'adds',coord=None,patterns=patterns)
    row['body']['enemy']['patterns']=copy.deepcopy(patterns)
    if parts:row['name']+='/parts'
    if injury:row['name']+='/injury'
    if break_parts:row['name']+='/broken-parts'
    if mary_first:row['name']+='/mary-first'
    if mary_low:row['name']+='/low-mary'
    original,prepared=original_case(row)
    c=copy.deepcopy(composition.fixtures()[0])
    for key in ('name','names','duration','seed','enemy','patterns','effects','owners','base_atk','skill_levels','controls','combat','environment','original_run','control_mode'):c[key]=original[key]
    c.update(packet_skill=source_definitions()[8]['name'],max_attacks=128,source_effect_identity=True,observe_named_state=True,state_queries=[],observe_authored_effect_lookup=True)
    if cover is not None:
        from portable_declared_manual_sequences import apply
        owner,when,length=cover
        c['name']+='/cover-'+str(owner)+'-'+str(when)
        c['declared_manual_sequences']={c['names'][owner]:[dict(action='cover',t=when,duration=length)]}
        c['physical_cover_composition']=True
        operated=apply(prepared['chars'],c['declared_manual_sequences'])
        c['controls']=[copy.deepcopy(char['control']) for char in operated]
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
        if c.get('declared_manual_sequences'):
            from portable_declared_manual_sequences import apply
            prepared['chars']=apply(prepared['chars'],c['declared_manual_sequences'])
            prepared['policies']['controls']={char['name']:copy.deepcopy(char.get('control',{})) for char in prepared['chars']}
        prepared['effects']=[dict(effect=copy.deepcopy(e),owner=c['names'][owner]) for e,owner in zip(lowered['effects'],lowered['owners'],strict=True)]
        if c.get('physical_cover_composition'):
            # The existing manual producer owns literal action parsing and packing.
            # Import before patching: its captured legacy helpers stay unmodified.
            from portable_manual_control_specs import normalize,pack
            import portable_charge_control_specs as controls
            with patch.object(controls,'normalize_static_controls',normalize),patch.object(controls,'compile_policy',pack):
                words,meta=compile_projectile_battle(prepared,trace='full')
        else:words,meta=compile_projectile_battle(prepared,trace='full')
        _,bindings=compile_registry(validate(c['patterns']),pools=True)
        return words,meta,bindings
    with patch.object(enemy.parent.parent,'compile_case',original_pack),patch.object(composition.typed.base,'compile_case',enemy.compile_case):
        words,domain=composition.typed.compile_case(c)
    return words,domain[1],domain[2]

def native_reference(domain):return composition.native_reference(domain,enemy_carrier=True)
