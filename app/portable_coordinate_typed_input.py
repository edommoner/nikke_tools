"""Compose complete original coordinate inputs with the shared typed-target tail."""
import copy
from portable_coordinate_roster_input import compile_coordinate_battle
from portable_coordinate_typed_specs import *
from portable_original_modifier_probe_input import pack_target_input
from portable_target_modifier_input import lower_effect
from destructible_skill_specs import coefficient

def compile_coordinate_typed(prepared,bindings=(),probe_row=None,*,probe_kind=2,max_attacks=128,geometry=None,coordinate_weapon_targets=False):
    if type(coordinate_weapon_targets) is not bool:raise ValueError('Explicit coordinate weapon policy required')
    if coordinate_weapon_targets:
        if probe_row is not None or not bindings or geometry is None or geometry.get('point_source')!='caster_aim' or geometry.get('grow',0)!=0:raise ValueError('Typed coordinate weapons require live aim, zero authored grow and no skill probe')
        if type(probe_kind) is not int or probe_kind not in (2,3) or type(max_attacks) is not int or not 1<=max_attacks<=128:raise ValueError('Invalid typed coordinate weapon limits')
        original=prepared['effects'];lowered=copy.deepcopy(prepared)
        for dest,row in zip(lowered['effects'],original,strict=True):dest['effect']=lower_effect(row['effect'])
        words,meta,actors,scene=compile_coordinate_battle(lowered)
        extra,axes=pack_target_input(words,meta,original,prepared['enemy']['patterns'],bindings,None,probe_kind,max_attacks,weapon_only=True)
        from portable_typed_geometry_specs import pack
        shape_words,shape_meta=pack(geometry,len(bindings),probe_kind);extra[:2320]=shape_words;extra[13]=1
        meta['typed_geometry']=shape_meta
        meta['coordinate_typed_input']=dict(probe_source=None,probe_kind=probe_kind,axis_rows=axes,one_resident_runtime=True,shared_world_clock=True,automatic_typed_weapon_aim=False,coordinate_weapon_targets=True)
        return words+extra,meta,actors,scene
    if probe_row is None:
        if geometry is not None:raise ValueError('Typed geometry requires an explicit probe')
        if bindings:raise ValueError('Disabled typed route cannot own targets')
        words,meta,actors,scene=compile_coordinate_battle(prepared)
        return words+[0]*TARGET_INPUT_WORDS,meta,actors,scene
    if type(probe_row) is not int or not 0<=probe_row<len(prepared['effects']):raise ValueError('Explicit coordinate typed probe source required')
    if type(probe_kind) is not int or probe_kind not in (2,3) or type(max_attacks) is not int or not 1<=max_attacks<=128:raise ValueError('Invalid coordinate typed probe limits')
    original=prepared['effects'];effect=original[probe_row]['effect']
    if effect.get('target')!=('typed_point' if geometry is not None else 'all_projectiles' if probe_kind==2 else 'boss'):raise ValueError('Explicit typed probe selector required')
    if probe_kind==3 and any(i!=probe_row and row['effect'].get('type')=='damage' and row['effect'].get('target')=='boss' for i,row in enumerate(original)):raise ValueError('Unrouted literal boss damage would be intercepted')
    char=next(c for c in prepared['chars'] if c['name']==original[probe_row]['owner']);coefficient(dict(effect,target='all_projectiles'),char)
    lowered=copy.deepcopy(prepared)
    for dest,row in zip(lowered['effects'],original,strict=True):dest['effect']=lower_effect(row['effect'])
    lowered['effects'][probe_row]['effect']['target']='boss'
    words,meta,actors,scene=compile_coordinate_battle(lowered)
    extra,axes=pack_target_input(words,meta,original,prepared['enemy']['patterns'],bindings,probe_row,probe_kind,max_attacks)
    if geometry is not None:
        from portable_typed_geometry_specs import pack
        shape_words,shape_meta=pack(geometry,len(bindings),probe_kind);extra[:2320]=shape_words;extra[5424+meta['binding_source_indices'].index(probe_row)]=5;meta['typed_geometry']=shape_meta
    if not extra[2320]:raise ValueError('Active typed route requires explicit targets')
    meta['coordinate_typed_input']=dict(probe_source=probe_row,probe_kind=probe_kind,axis_rows=axes,one_resident_runtime=True,shared_world_clock=True,automatic_typed_weapon_aim=False)
    return words+extra,meta,actors,scene
