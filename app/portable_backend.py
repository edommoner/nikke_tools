"""Slang C++ build and native CPU buffer transport; no game arithmetic here."""
from portable_file_identity import file_digest
import ctypes as C
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import tempfile
import selectors
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
from portable_wire_layout import MAX_INPUT_WORDS,MAX_OUTPUT_WORDS,LARGE_OUTPUT_WORDS
READBACK_CHUNK_BYTES=8*1024*1024





def source_hashes(source):
    from portable_slang_generation import source_hashes as generate_hashes
    return generate_hashes(ROOT,source)


def build(source,entry,*,target=None):
    from portable_slang_generation import build as generate
    return generate(ROOT,source,entry,**({"target":target} if target is not None else {}))










def validate_composed_stride(source,input_words,output_words):
    if source in ('gpu/product_weighted_target_battle_entry.slang','gpu/product_weighted_fixed_target_battle_entry.slang'):
        return validate_composed_stride('gpu/product_weighted_battle_entry.slang',input_words,output_words)
    if source in ('gpu/product_ammo_weighted_battle_entry.slang','gpu/product_ammo_weighted_fixed_battle_entry.slang'):
        from portable_weighted_battle_wire import AMMO_INPUT,check_schema
        from portable_product_resource_budget import SUPPLY_OUTPUT_WORDS
        check_schema(ROOT)
        if (input_words,output_words)!=(AMMO_INPUT,SUPPLY_OUTPUT_WORDS):raise ValueError('Ammo/weighted requires complete disjoint banks')
        return
    from portable_product_s2_entries import ALIASES
    if source in ALIASES:return validate_composed_stride(ALIASES[source],input_words,output_words)
    if source in ('gpu/product_named_carriers_group_battle_entry.slang','gpu/product_named_carriers_fixed_group_battle_entry.slang'):
        return validate_composed_stride(source.replace('product_named_carriers_','product_',1),input_words,output_words)
    if source in ('gpu/product_ordinary_lock_battle_entry.slang','gpu/product_ordinary_lock_fixed_battle_entry.slang'):
        return validate_composed_stride(source.replace('product_ordinary_lock_','product_',1),input_words,output_words)
    if source in ('gpu/product_movement_range_cover_battle_entry.slang','gpu/product_movement_range_cover_fixed_battle_entry.slang'):
        from portable_product_movement_range import check_cover_schema,COVER_INPUT,OUTPUT
        check_cover_schema(ROOT)
        if (input_words,output_words)!=(COVER_INPUT,OUTPUT):raise ValueError('Movement/range/cover requires all three complete disjoint banks')
        return
    if source in ('gpu/product_movement_range_battle_entry.slang','gpu/product_movement_range_fixed_battle_entry.slang'):
        from portable_product_movement_range import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Movement/range requires complete disjoint consumer arenas')
        return
    if source in ('gpu/product_add_battle_entry.slang','gpu/product_add_group_battle_entry.slang',
                  'gpu/product_add_fixed_battle_entry.slang','gpu/product_add_fixed_group_battle_entry.slang',
                  'gpu/product_add_target_battle_entry.slang','gpu/product_add_fixed_target_battle_entry.slang',
                  'gpu/product_add_group_target_battle_entry.slang','gpu/product_add_fixed_group_target_battle_entry.slang'):
        from portable_add_attack_battle_wire import check_schema,LAYOUT
        from portable_add_self_destruct_wire import check_schema as check_retirement
        check_schema(ROOT);check_retirement(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):
            raise ValueError('Product ADD attacks require the complete shared source/retirement wire')
        return
    if source in ('gpu/product_fixed_battle_entry.slang','gpu/product_fixed_group_battle_entry.slang',
                  'gpu/product_fixed_target_battle_entry.slang','gpu/product_fixed_group_target_battle_entry.slang'):
        # Identical wire; only the guarded fixed-readiness consumer differs.
        return validate_composed_stride(source.replace('gpu/product_fixed_','gpu/product_',1),input_words,output_words)
    if source=='gpu/product_group_target_battle_entry.slang':
        from portable_destructible_roster_input import check_group_wire,GROUP_INPUT_WORDS,OUTPUT_WORDS
        check_group_wire(ROOT)
        if (input_words,output_words)!=(GROUP_INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Product group target requires its complete carrier and group wire')
        return
    if source in ('gpu/world_weighted_incoming_entry.slang','gpu/world_weighted_incoming_diagnostic_entry.slang','gpu/product_weighted_battle_entry.slang','gpu/product_weighted_fixed_battle_entry.slang','gpu/product_weighted_group_battle_entry.slang','gpu/product_weighted_fixed_group_battle_entry.slang','gpu/product_coordinate_weighted_battle_entry.slang','gpu/product_coordinate_weighted_fixed_battle_entry.slang'):
        from portable_weighted_battle_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if source.startswith('gpu/product_coordinate_weighted_'):
            from portable_logical_geometry_wire import check_schema as logical_schema,LAYOUT as G,SCRATCH
            from portable_weighted_battle_wire import LAYOUT as W
            logical_schema(ROOT)
            if G['BASE']+G['WORDS']!=W['BASE'] or SCRATCH['OUTPUT_WORDS']!=W['OUTPUT_BASE']:
                raise ValueError('Coordinate and weighted banks must remain disjoint and contiguous')
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Weighted incoming requires complete literal weights and owned receipt banks')
        return
    from portable_product_programs import PROGRAMS
    named_carrier_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('named-carriers-')}
    if source in named_carrier_sources:
        if (input_words,output_words)!=(104400,786432):raise ValueError('Named carriers require the complete ordinary BODY wire')
        return
    coordinate_cover_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('coordinate-cover-')}
    if source in coordinate_cover_sources:
        from portable_cover_defense_wire import check_schema,LAYOUT as C,INPUT,OUTPUT
        from portable_logical_geometry_wire import check_schema as coordinate_schema,LAYOUT as G,SCRATCH
        check_schema(ROOT);coordinate_schema(ROOT)
        if G['BASE']+G['WORDS']!=C['BASE'] or SCRATCH['OUTPUT_WORDS']!=C['OUTPUT_BASE']:
            raise ValueError('Coordinate and cover banks must remain disjoint and contiguous')
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Coordinate/cover requires both complete input and receipt banks')
        return
    range_cover_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('named-range-cover-')}
    if source in range_cover_sources:
        from portable_cover_defense_wire import check_schema,LAYOUT as C,OUTPUT
        from portable_named_range_battle_wire import check_schema as range_schema,INPUT as R,OUTPUT as RO
        check_schema(ROOT);range_schema(ROOT)
        if RO!=C['OUTPUT_BASE']:raise ValueError('Named range and cover banks must remain disjoint and contiguous')
        if (input_words,output_words)!=(R+C['WORDS'],OUTPUT):raise ValueError('Named range/cover requires both complete declaration and receipt banks')
        return
    lock_cover_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('lock-cover-')}
    if source in lock_cover_sources:
        from portable_lock_typed_layout import check,INPUT as LI,OUTPUT as LO
        from portable_cover_defense_wire import check_schema,LAYOUT as C,OUTPUT
        from portable_product_locks import check_cover_history
        check(ROOT);check_schema(ROOT);check_cover_history(ROOT)
        if LO>C['OUTPUT_BASE'] or (input_words,output_words)!=(LI+C['WORDS'],OUTPUT):raise ValueError('Lock On/cover requires complete disjoint arenas')
        return
    movement_cover_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('movement-cover-')}
    if source in movement_cover_sources:
        from portable_cover_defense_wire import check_schema,LAYOUT as C,OUTPUT
        from portable_enemy_movement_wire import check_schema as movement_schema,INPUT as M,OUTPUT as MO
        check_schema(ROOT);movement_schema(ROOT)
        if MO!=C['OUTPUT_BASE']:raise ValueError('Movement and cover receipt banks must remain disjoint and contiguous')
        if (input_words,output_words)!=(M+C['WORDS'],OUTPUT):raise ValueError('Movement/cover requires both complete declaration and receipt banks')
        return
    ammo_cover_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('ammo-cover-')}
    if source in ammo_cover_sources:
        from portable_cover_defense_wire import check_schema,LAYOUT as C,OUTPUT
        from portable_enemy_ammo_wire import check_schema as ammo_schema,LAYOUT as A
        check_schema(ROOT);ammo_schema(ROOT)
        if A['OUTPUT_WORDS']!=C['OUTPUT_BASE']:raise ValueError('Ammo and cover receipt banks must remain disjoint and contiguous')
        if (input_words,output_words)!=(A['INPUT_WORDS']+C['WORDS'],OUTPUT):raise ValueError('Ammo/cover requires both complete declaration and receipt banks')
        return
    healing_cover_sources={p['source'] for n,p in PROGRAMS.items() if n.startswith('healing-cover-')}
    if source in healing_cover_sources:
        from portable_cover_defense_wire import check_schema,LAYOUT as C,OUTPUT
        from portable_enemy_healing_wire import check_schema as healing_schema,INPUT_WORDS as H,OUTPUT as HO
        check_schema(ROOT);healing_schema(ROOT)
        if HO['OUTPUT_WORDS']!=C['OUTPUT_BASE']:raise ValueError('Healing and cover receipt banks must remain disjoint and contiguous')
        if (input_words,output_words)!=(H+C['WORDS'],OUTPUT):raise ValueError('Healing/cover requires both disjoint complete declaration and receipt banks')
        return
    cover_sources={'gpu/world_cover_defense_entry.slang'}|{
        p['source'] for n,p in PROGRAMS.items() if n.startswith(('cover-','default-cover-'))}
    if source in cover_sources or output_words==2048912:
        from portable_cover_defense_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if source not in cover_sources or (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Cover DEF requires complete independent bases and receipt bank')
        return
    if source=='gpu/world_coordinate_typed_ordered_history_entry.slang':
        from portable_recipient_order_observation import check_layout,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Recipient-order observation requires the complete history wire')
        return
    if source=='gpu/world_moving_many_entry.slang':
        from portable_moving_many_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Maximum-slot motion requires complete untruncated frame/segment banks')
        return
    if source in ('gpu/world_moving_typed_entry.slang','gpu/world_moving_frames_entry.slang'):
        from portable_moving_typed_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Moving typed execution requires all physical, logical, movement and frozen aim banks')
        return
    if source in ('gpu/world_enemy_movement_entry.slang','gpu/product_movement_battle_entry.slang','gpu/product_movement_fixed_battle_entry.slang'):
        from portable_enemy_movement_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Movement requires complete collider, marker and motion banks')
        return
    if source=='gpu/world_enemy_ammo_self_destruct_entry.slang':
        from portable_enemy_ammo_self_destruct_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('Final-queue magazines require both complete banks and disjoint receipts')
        return
    if source in ('gpu/world_enemy_ammo_entry.slang','gpu/product_ammo_battle_entry.slang','gpu/product_ammo_fixed_battle_entry.slang','gpu/product_ammo_group_battle_entry.slang','gpu/product_ammo_fixed_group_battle_entry.slang','gpu/product_ammo_target_battle_entry.slang','gpu/product_ammo_fixed_target_battle_entry.slang'):
        from portable_enemy_ammo_wire import check_schema,LAYOUT
        check_schema(ROOT)
        from portable_product_ammo import LONG_PLAIN_OUTPUT_WORDS
        from portable_product_resource_budget import SUPPLY_OUTPUT_WORDS
        allowed={LAYOUT['OUTPUT_WORDS']}
        if source.startswith('gpu/product_ammo_'):allowed.update((LONG_PLAIN_OUTPUT_WORDS,SUPPLY_OUTPUT_WORDS))
        if input_words!=LAYOUT['INPUT_WORDS'] or output_words not in allowed:raise ValueError('Enemy ammo requires complete actor and resource banks')
        return
    if source=='gpu/world_add_self_destruct_entry.slang':
        from portable_add_self_destruct_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('Self-destruct requires complete ADD input and receipt arena')
        return
    if source=='gpu/world_add_attack_battle_entry.slang':
        from portable_add_attack_battle_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('ADD attack battle requires its complete logical and firing wire')
        return
    if source in ('gpu/world_lock_projectile_entry.slang','gpu/world_original_lock_composition_entry.slang','gpu/world_original_lock_health_parts_entry.slang','gpu/product_lock_battle_entry.slang','gpu/product_lock_fixed_battle_entry.slang'):
        from portable_lock_typed_layout import check,INPUT,OUTPUT
        check(ROOT)
        if source in ('gpu/world_original_lock_composition_entry.slang','gpu/world_original_lock_health_parts_entry.slang','gpu/product_lock_battle_entry.slang','gpu/product_lock_fixed_battle_entry.slang'):
            from portable_original_lock_layout import check as check_original
            check_original(ROOT)
        if source in ('gpu/product_lock_battle_entry.slang','gpu/product_lock_fixed_battle_entry.slang'):
            from portable_original_lock_layout import PRODUCT_OUTPUT
            OUTPUT=PRODUCT_OUTPUT
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Lock/projectile composition requires its complete disjoint arenas')
        return
    if source in ('gpu/world_lock_packet_entry.slang','gpu/world_lock_delivery_entry.slang'):
        from portable_lock_packet_layout import check,INPUT,OUTPUT
        check(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Lock packets require the full lock/manual/queue wire')
        return
    if source=='gpu/world_physical_lock_cover_entry.slang':
        from portable_physical_lock_cover_layout import check,INPUT,OUTPUT
        check(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Physical cover requires the complete lock/manual arena wire')
        return
    if source in ('gpu/world_lock_enemy_carrier_entry.slang','gpu/world_lock_enemy_carrier_diagnostic_entry.slang'):
        from portable_physical_lock_layout import check,INPUT,OUTPUT
        check(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Enemy lock carriers require the complete physical arena wire')
        return
    if source=='gpu/world_physical_locks_entry.slang' or output_words==806912:
        from portable_physical_lock_layout import check,INPUT,OUTPUT
        check(ROOT)
        if source!='gpu/world_physical_locks_entry.slang' or (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Physical locks require their separate arena wire')
        return
    if source in ('gpu/world_named_range_battle_entry.slang','gpu/product_named_range_battle_entry.slang','gpu/product_named_range_fixed_battle_entry.slang'):
        from portable_named_range_battle_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Named radial battle requires its complete declared wire')
        return
    if source in ('gpu/world_enemy_healing_entry.slang','gpu/product_healing_battle_entry.slang','gpu/product_healing_fixed_battle_entry.slang','gpu/product_healing_group_battle_entry.slang','gpu/product_healing_fixed_group_battle_entry.slang','gpu/product_coordinate_healing_battle_entry.slang','gpu/product_coordinate_healing_fixed_battle_entry.slang'):
        from portable_enemy_healing_wire import check_schema,INPUT_WORDS,OUTPUT
        check_schema(ROOT)
        if source.startswith('gpu/product_coordinate_healing_'):
            from portable_logical_geometry_wire import check_schema as logical_schema,LAYOUT as G,SCRATCH
            from portable_enemy_healing_wire import LAYOUT as H
            logical_schema(ROOT)
            if G['BASE']+G['WORDS']!=H['BASE'] or SCRATCH['OUTPUT_WORDS']!=OUTPUT['OUTPUT_WORDS']:
                raise ValueError('Coordinate and healing require adjacent complete banks')
        if (input_words,output_words)!=(INPUT_WORDS,OUTPUT['OUTPUT_WORDS']):raise ValueError('Enemy healing requires its complete declared source wire')
        return
    if source in ('gpu/product_typed_lock_battle_entry.slang','gpu/product_typed_lock_fixed_battle_entry.slang'):
        from portable_product_typed_lock import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Typed weapons and Lock On require complete shared arenas')
        return
    if source in ('gpu/product_coordinate_lock_battle_entry.slang','gpu/product_coordinate_lock_fixed_battle_entry.slang'):
        from portable_product_coordinate_lock import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Coordinate Lock On requires complete disjoint arenas')
        return
    if source in ('gpu/product_typed_battle_entry.slang','gpu/product_typed_fixed_battle_entry.slang'):
        from portable_product_typed import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Typed product requires complete coordinate/typed/skill/logical banks')
        return
    if source in ('gpu/product_coordinate_add_battle_entry.slang','gpu/product_coordinate_add_fixed_battle_entry.slang'):
        from portable_add_attack_battle_wire import check_schema,LAYOUT as A
        from portable_add_self_destruct_wire import check_schema as retirement_schema
        from portable_logical_geometry_wire import check_schema as logical_schema,LAYOUT as G,SCRATCH
        check_schema(ROOT);retirement_schema(ROOT);logical_schema(ROOT)
        if G['BASE']+G['WORDS']!=A['BASE'] or SCRATCH['OUTPUT_WORDS']!=A['OUTPUT_WORDS']:
            raise ValueError('Coordinate and ADD require their complete disjoint input banks and registered output')
        if (input_words,output_words)!=(A['INPUT_WORDS'],A['OUTPUT_WORDS']):raise ValueError('Coordinate ADD requires the complete shared source/retirement wire')
        return
    if source in ('gpu/world_coordinate_logical_actor_entry.slang','gpu/product_coordinate_battle_entry.slang','gpu/product_coordinate_fixed_battle_entry.slang'):
        from portable_logical_geometry_wire import check_schema,LAYOUT,SCRATCH
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['BASE']+LAYOUT['WORDS'],SCRATCH['OUTPUT_WORDS']):raise ValueError('Logical ADD geometry requires its complete registered wire')
        return
    if source=='gpu/world_coordinate_resident_frames_entry.slang':
        from portable_coordinate_resident_arc_specs import check_layout,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Resident frames require the complete106 wire')
        return
    if source=='gpu/world_coordinate_resident_arc_entry.slang' or output_words==2064786:
        from portable_coordinate_resident_arc_specs import check_layout,SOURCE,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if source!=SOURCE or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Resident arc requires the complete registered tail wire')
        return
    if source in ('gpu/world_coordinate_typed_entry.slang','gpu/world_coordinate_typed_weapon_entry.slang','gpu/world_coordinate_typed_aim_entry.slang','gpu/world_coordinate_typed_actor_entry.slang','gpu/world_coordinate_typed_owner_entry.slang','gpu/world_coordinate_typed_logical_owner_entry.slang','gpu/world_coordinate_typed_history_entry.slang') or output_words==2032000:
        from portable_coordinate_typed_specs import check_layout,SOURCE,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if source=='gpu/world_coordinate_typed_history_entry.slang':
            from portable_skill_history import check_layout as check_history
            check_history(ROOT)
        if source not in (SOURCE,'gpu/world_coordinate_typed_weapon_entry.slang','gpu/world_coordinate_typed_aim_entry.slang','gpu/world_coordinate_typed_actor_entry.slang','gpu/world_coordinate_typed_owner_entry.slang','gpu/world_coordinate_typed_logical_owner_entry.slang','gpu/world_coordinate_typed_history_entry.slang') or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Coordinate typed targets require the complete registered wire')
        return
    if source in ('gpu/world_coordinate_policy_entry.slang','gpu/world_coordinate_squad_entry.slang','gpu/world_coordinate_squad_mode_entry.slang','gpu/world_coordinate_burst_control_entry.slang','gpu/world_coordinate_mode_actions_entry.slang','gpu/world_coordinate_auto_reload_entry.slang','gpu/world_coordinate_healing_entry.slang','gpu/world_coordinate_original_entry.slang','gpu/world_coordinate_original_clock_entry.slang','gpu/world_coordinate_original_resource_entry.slang','gpu/world_coordinate_original_ammo_entry.slang','gpu/world_coordinate_original_stack_entry.slang','gpu/world_coordinate_original_cleanse_entry.slang','gpu/world_coordinate_original_slot_entry.slang','gpu/world_coordinate_original_reload_entry.slang','gpu/world_coordinate_original_shield_entry.slang','gpu/world_coordinate_original_cover_entry.slang','gpu/world_coordinate_original_shared_entry.slang') or output_words==1769856:
        expected={'gpu/world_coordinate_policy_entry.slang':109656,'gpu/world_coordinate_squad_entry.slang':109792,'gpu/world_coordinate_squad_mode_entry.slang':109792,'gpu/world_coordinate_burst_control_entry.slang':109968,'gpu/world_coordinate_mode_actions_entry.slang':109968,'gpu/world_coordinate_auto_reload_entry.slang':109968,'gpu/world_coordinate_healing_entry.slang':109968,'gpu/world_coordinate_original_entry.slang':109968,'gpu/world_coordinate_original_clock_entry.slang':109968,'gpu/world_coordinate_original_resource_entry.slang':109968,'gpu/world_coordinate_original_ammo_entry.slang':109968,'gpu/world_coordinate_original_stack_entry.slang':109968,'gpu/world_coordinate_original_cleanse_entry.slang':109968,'gpu/world_coordinate_original_slot_entry.slang':109968,'gpu/world_coordinate_original_reload_entry.slang':109968,'gpu/world_coordinate_original_shield_entry.slang':109968,'gpu/world_coordinate_original_cover_entry.slang':109968,'gpu/world_coordinate_original_shared_entry.slang':109968}
        if source not in expected or (input_words,output_words)!=(expected[source],1769856):raise ValueError('Cover policy requires its complete registered wire')
        return
    if source in ('gpu/world_coordinate_sampling_burst_entry.slang','gpu/world_coordinate_sampling_vital_entry.slang','gpu/world_coordinate_manual_entry.slang') or output_words==1769472:
        from portable_coordinate_sampled_burst_wire import SOURCE,INPUT_WORDS,OUTPUT_WORDS,check_schema
        check_schema(ROOT)
        if source not in (SOURCE,'gpu/world_coordinate_sampling_vital_entry.slang','gpu/world_coordinate_manual_entry.slang') or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
            raise ValueError('Sampled burst requires its complete registered wire')
        return
    if source in ('gpu/world_coordinate_group_entry.slang','gpu/world_coordinate_mixed_entry.slang','gpu/world_coordinate_sampling_entry.slang','gpu/world_coordinate_sampling_parent_entry.slang','gpu/world_coordinate_sampling_skill_entry.slang') or output_words==1507328:
        from portable_coordinate_group_wire import INPUT_WORDS,OUTPUT_WORDS,check_schema
        check_schema(ROOT)
        if source not in ('gpu/world_coordinate_group_entry.slang','gpu/world_coordinate_mixed_entry.slang','gpu/world_coordinate_sampling_entry.slang','gpu/world_coordinate_sampling_parent_entry.slang','gpu/world_coordinate_sampling_skill_entry.slang') or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
            raise ValueError('Coordinate group requires the complete registered wire')
        return
    if output_words==1310720 or source=='gpu/world_coordinate_composed_entry.slang':
        from portable_arena_specs import audit_profile
        plan=audit_profile('combined-v1')
        if source in ('gpu/world_coordinate_aim_entry.slang','gpu/world_coordinate_control_entry.slang'):
            from portable_coordinate_aim_wire import INPUT_WORDS,OUTPUT_WORDS,check_schema
            check_schema(ROOT)
            if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
                raise ValueError('Coordinate aim requires the complete authored wire')
        elif source in ('gpu/world_coordinate_core_entry.slang','gpu/world_coordinate_cache_entry.slang'):
            from portable_coordinate_core_specs import INPUT_WORDS,OUTPUT_WORDS,check_schema
            check_schema(ROOT)
            if source=='gpu/world_coordinate_cache_entry.slang':
                from portable_coordinate_cache_specs import check_schema as check_cache_schema
                check_cache_schema(ROOT)
            if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
                raise ValueError('Coordinate live core stride requires the complete wire')
        elif source=='gpu/world_coordinate_physical_entry.slang':
            from portable_coordinate_physical_specs import audit_arena
            physical=audit_arena(ROOT)
            if (input_words,output_words)!=(physical['input_words'],physical['output_words']):
                raise ValueError('Coordinate physical stride requires the complete wire')
        elif source!='gpu/world_coordinate_composed_entry.slang' or (input_words,output_words)!=(plan['input_words'],plan['output_words']):
            raise ValueError('Composed stride requires the registered shared entry and complete wire')


def validate_product_ammo_versions(source,packed,input_words,output_words,count):
    """A physical dispatch has one explicitly owned resource output stride."""
    from portable_product_s2_entries import ALIASES
    source=ALIASES.get(source,source)
    if source in ('gpu/product_ammo_weighted_battle_entry.slang','gpu/product_ammo_weighted_fixed_battle_entry.slang'):
        from portable_enemy_ammo_wire import LAYOUT as E
        for i in range(count):
            if struct.unpack_from('<I',packed,4*(1+i*input_words+E['BASE']+1))[0]!=3:raise ValueError('Ammo/weighted requires its v3 resource tail')
        return
    if source not in tuple('gpu/product_ammo_'+stem+'battle_entry.slang' for stem in ('','fixed_','group_','fixed_group_','target_','fixed_target_')):return
    from portable_enemy_ammo_wire import LAYOUT as E
    from portable_product_ammo import LONG_PLAIN_OUTPUT_WORDS
    from portable_product_resource_budget import SUPPLY_OUTPUT_WORDS
    if output_words not in (E['OUTPUT_WORDS'],LONG_PLAIN_OUTPUT_WORDS,SUPPLY_OUTPUT_WORDS):
        raise ValueError('Enemy ammo input version and output stride disagree')
    version=3 if output_words==SUPPLY_OUTPUT_WORDS else 2 if output_words==LONG_PLAIN_OUTPUT_WORDS else 1
    for i in range(count):
        if struct.unpack_from('<I',packed,4*(1+i*input_words+E['BASE']+1))[0]!=version:
            raise ValueError('Enemy ammo input version and output stride disagree')

def execute(source, entry, packed, input_words, output_words, backend='native', *, readback_path=None):
    if backend != 'native':
        raise ValueError('Explicit native backend required')
    if type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=MAX_INPUT_WORDS or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in LARGE_OUTPUT_WORDS:
        raise ValueError('Invalid portable word strides')
    validate_composed_stride(source,input_words,output_words)
    if len(packed)<4:raise ValueError('Invalid portable wire dimensions')
    count, = struct.unpack_from('<I', packed)
    if not 1 <= count <= 65536 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff or len(packed) != (1+count*input_words)*4:
        raise ValueError('Invalid portable wire dimensions')
    validate_product_ammo_versions(source,packed,input_words,output_words,count)
    if readback_path is not None and Path(readback_path).is_symlink():raise ValueError('Fresh readback destination required')
    destination=Path(readback_path).resolve() if readback_path is not None else None
    partial=destination.with_name(destination.name+'.partial') if destination is not None else None
    if destination is not None and (destination.exists() or partial.exists() or partial.is_symlink() or not destination.parent.is_dir()):
        raise ValueError('Fresh readback destination and partial required')
    outputs, hashes = build(source, entry,target="cpp")
    directory = ROOT/'research/portable-build'
    with tempfile.TemporaryDirectory(prefix='dispatch-', dir=directory) as tmp:
        input_path, output_path = Path(tmp)/'input.bin', partial if destination is not None else Path(tmp)/'output.bin'
        input_path.write_bytes(packed)
        from portable_native import build_host, run_host
        if entry!='portableEvents':raise ValueError('Native product host requires portableEvents')
        host,build_receipt=build_host(ROOT,outputs['cpp'])
        transport=run_host(host,input_path,output_path,input_words,output_words,count,min(count*600,4800))
        transport['build']=build_receipt
        raw=None if destination is not None else output_path.read_bytes()
    if destination is not None:
        from portable_capture_storage import file_digest as capture_digest
        if raw is not None or not partial.is_file() or partial.is_symlink() or partial.stat().st_size!=count*output_words*4 or transport['cases']!=count or transport['command_status']!='completed' or transport.get('input_bytes')!=len(packed) or transport.get('output_bytes')!=count*output_words*4:
            raise RuntimeError('Incomplete file readback')
        output_digest=capture_digest(partial)
    else:output_digest=hashlib.sha256(raw).hexdigest()
    if (destination is None and len(raw)!=count*output_words*4) or hashes!=source_hashes(source):
        raise RuntimeError('Invalid native output or source changed during execution')
    if destination is not None:
        with partial.open('r+b') as stream:os.fsync(stream.fileno())
        # Publish without replacing an existing result, keeping the partial on failure.
        os.link(partial,destination);partial.unlink()
        if os.name!='nt':
            fd=os.open(destination.parent,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
    return raw, dict(transport=transport, source_sha256=hashes,
                    generated_sha256={k:file_digest(p) for k,p in outputs.items()},
                    input_sha256=hashlib.sha256(packed).hexdigest(), output_sha256=output_digest,
                    native_execution_verified=True,gpu_execution_verified=False, backend=backend)
