"""Product battle adapter: original preparation -> shared kernel -> original payload.

No CPU battle, damage or event schedule is used as kernel input. Until broader
product admission is established every successful shared-kernel result is CPU-checked.
Policy 2026-11-05: optimize jobs alone may defer checks to every displayed squad
plus a reproducible 1/8 sample; any mismatch escalates to the entire job. All
other job kinds retain fresh CPU full-payload verification of every request.
"""
import array
import copy
from contextlib import nullcontext
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import struct
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch
import uuid

import engine_worker
from portable_runtime import UnsupportedPortable, decode
from portable_projectile_roster_input import compile_projectile_battle, INPUT_WORDS, OUTPUT_WORDS
from portable_backend import execute

SOURCE = 'gpu/product_battle_entry.slang'
ROOT = Path(__file__).resolve().parents[1]
BACKENDS = {'native_detail': 'native', 'browser_detail': 'browser'}


def execution_environment(backend):
    """Require warm generation plus an explicit saved image or native cache."""
    if backend == 'browser':
        from portable_wasm import availability
        status=availability(ROOT)
        if not status['available']:raise UnsupportedPortable(status['reason'])
        return {}
    if backend == 'native':
        from portable_native import availability
        status=availability(ROOT)
        if not status['available']:raise UnsupportedPortable(status['reason'])
        return {}
    raise UnsupportedPortable('Unsupported execution backend')


def verified_transport(evidence, backend, *, cases=1):
    timing = 'browser_seconds' if backend=='browser' else 'host_seconds'
    try:
        transport = evidence['transport']
        valid = (evidence['backend'] == backend and evidence.get('browser_execution_reported' if backend=='browser' else 'native_execution_verified') is True
            and (backend!='native' or evidence.get('gpu_execution_verified') is not True)
            and (backend!='browser' or evidence.get('gpu_execution_verified') is False)
            and (backend!='browser' or evidence.get('native_execution_verified') is False and transport.get('timing_scope')=='client-reported')
            and transport['command_status'] == 'completed' and type(transport['cases']) is int and transport['cases'] == cases
            and isinstance(transport['device'], str) and bool(transport['device'])
            and type(transport[timing]) in (int,float) and math.isfinite(transport[timing]) and transport[timing] >= 0
            and all(isinstance(evidence[k],str) and len(evidence[k]) == 64
                and all(c in '0123456789abcdef' for c in evidence[k]) for k in ('input_sha256','output_sha256')))
    except (KeyError, TypeError, OverflowError):
        valid = False
    if not valid:
        raise RuntimeError('Shared kernel execution metadata is incomplete or unverified')
    return transport, timing


def compile_product(prepared):
    source,iw,ow,words,metadata=_compile_product(prepared)
    from portable_specs import LIMITS as L
    at=L['WORLD_FRAME_INPUT_BASE']
    if len(words)>at and words[at]!=0:
        if words[at]!=0x57533031 or not 1<=words[at+1]<=32:
            raise UnsupportedPortable('Invalid shared world clock input contract')
        metadata['product_world_frame_contract']=dict(nodes=words[at+1])
    return source,iw,ow,words,metadata


def validate_world_frame_readback(block,metadata):
    """Every compiled world, including an empty boss, must retain its clock."""
    contract=metadata.get('product_world_frame_contract')
    if contract is None:return
    from portable_specs import LIMITS as L
    base=L['WORLD_FRAME_OUTPUT_BASE'];count=contract['nodes']
    if (len(block)<base+788 or block[base]!=0 or not 1<=block[base+1]<=512 or list(block[base+784:base+788])!=[32,0,0,0]
        or any(block[base+16+i*24]!=0 for i in range(count))):
        raise UnsupportedPortable('Shared world clock readback is missing or incomplete; the compiled result is rejected')


def _compile_product(prepared):
    """Select an existing wire by actual effect requirements, never by character."""
    if 'typed_targets' in prepared.get('reference_models',{}):
        from portable_product_typed import compile_product as typed_product
        return typed_product(prepared)
    from portable_product_cover import required as cover_required,compile_product as compile_cover
    if 'coordinate' in prepared.get('reference_models',{}):
        if 'lock_on' in prepared['reference_models']:
            from portable_product_locks import compile_product as locks
            return locks(prepared,coordinate_model=prepared['reference_models']['coordinate'])
        from portable_product_weighted import required as weighted_required,compile_product as compile_weighted
        if not prepared.get('_product_weighted_compiled') and weighted_required(prepared):
            return compile_weighted(prepared,compile_product)
        from portable_product_healing import required as healing_required,compile_product as compile_healing
        if not prepared.get('_product_healing_compiled') and healing_required(prepared):
            return compile_healing(prepared,compile_product)
        if not prepared.get('_product_cover_compiled') and cover_required(prepared):
            return compile_cover(prepared,compile_product)
        from portable_product_coordinate import compile_product as coordinates
        return coordinates(prepared)
    from portable_product_movement import required as movement_required,compile_product as compile_movement
    from portable_product_locks import required as locks_required,compile_product as compile_locks
    from portable_product_named_range import required as range_required,compile_product as compile_range
    if movement_required(prepared) and not prepared.get('reference_models'):
        from portable_enemy_specs import plain_body_domain
        if plain_body_domain(prepared,unauthored=True):
            from portable_product_movement import compile_static_body
            return compile_static_body(prepared,_compile_product)
    if not prepared.get('_product_cover_compiled') and cover_required(prepared) and (range_required(prepared) or movement_required(prepared) or locks_required(prepared)):
        return compile_cover(prepared,compile_product)
    if range_required(prepared) and movement_required(prepared):
        from portable_product_movement_range import compile_product as compile_movement_range
        return compile_movement_range(prepared)
    if locks_required(prepared):return compile_locks(prepared)
    from portable_product_named_carriers import required as named_carriers_required,compile_product as compile_named_carriers
    if not prepared.get('_product_named_carriers_compiled') and not prepared.get('reference_models') and named_carriers_required(prepared):
        return compile_named_carriers(prepared,compile_product)
    if range_required(prepared):return compile_range(prepared)
    if movement_required(prepared):return compile_movement(prepared)
    if not prepared.get('_product_cover_compiled') and cover_required(prepared):
        return compile_cover(prepared,compile_product)
    from portable_product_ammo import required as ammo_required,compile_product as compile_ammo
    if not prepared.get('_product_ammo_compiled') and ammo_required(prepared):
        return compile_ammo(prepared,compile_product)
    from portable_product_weighted import required as weighted_required,compile_product as compile_weighted
    if not prepared.get('_product_weighted_compiled') and weighted_required(prepared):
        return compile_weighted(prepared,compile_product)
    from portable_product_healing import required,compile_product as compile_healing
    if not prepared.get('_product_healing_compiled') and required(prepared):
        return compile_healing(prepared,compile_product)
    if prepared.get('reference_models'):
        raise UnsupportedPortable('Declared CPU reference consumer requires its matching shared kernel product wire; no model may be silently omitted')
    from portable_enemy_specs import lower_single_body_nearby
    original=prepared
    # The product promises the canonical battle's named-carrier lifecycle.
    # Keep every equipment definition and let the existing shared kernel carrier
    # merge/refresh them exactly as native does. Standalone component-quantity
    # proofs retain their distinct, explicitly documented contract.
    prepared=dict(prepared,_product_native_equipment_carriers=True)
    manual_cover=any(a.get('action')=='cover' for c in prepared['chars'] for a in c.get('control',{}).get('sequence',[]))
    if manual_cover:
        if not prepared.get('_product_cover_compiled'):
            raise UnsupportedPortable('Manual cover requires the connected product cover consumer entry')
        prepared=dict(prepared,_product_manual_cover=True)
    from portable_product_fixed import lower as lower_fixed,attach as attach_fixed
    prepared,fixed_values=lower_fixed(prepared)
    fixed=fixed_values is not None
    from portable_product_add_attack import lower as lower_add_attacks
    prepared,add_patterns=lower_add_attacks(prepared)
    if 'burst_pattern' in prepared['policies']['config']:
        prepared=dict(prepared,_product_burst_patterns=True)
    prepared,nearby=lower_single_body_nearby(prepared)
    if any(p.get('kind') in ('attack','debuff') and p.get('spec',{}).get('debuffs') for p in original['enemy'].get('patterns',[])):
        prepared=dict(prepared,_product_boss_debuffs=True)
    def finish(source,iw,ow,words,metadata):
        if any(c.get('control') for c in original['chars']):
            from calculator.timeline import CharState,_when_label
            metadata['product_control_labels']=[
                [dict(mode=e['mode'],producer=_when_label(e)) for e in CharState(c,atk,original['enemy'].get('code'))._click_sched]
                for c,atk in zip(original['chars'],original['base_atk'])]
        if manual_cover:
            metadata['product_manual_cover_owners']=[i for i,c in enumerate(original['chars']) if any(a.get('action')=='cover' for a in c.get('control',{}).get('sequence',[]))]
        if original['enemy'].get('patterns'):
            from calculator.boss_pattern import validate,RESERVED_KINDS
            nodes=validate(copy.deepcopy(original['enemy']['patterns']))
            if any(p.kind in RESERVED_KINDS for p in nodes):
                raise UnsupportedPortable('Reserved boss pattern has no product execution model')
            metadata['product_world']=dict(nodes=[dict(id=p.id,kind=p.kind) for p in nodes],
                literal_pattern_identity_only=True,cpu_schedule_or_state_supplied=False)
            from portable_actor_specs import compile_registry
            registry_nodes=validate(copy.deepcopy(prepared['enemy']['patterns'])) if add_patterns is not None else nodes
            _,bindings=compile_registry(registry_nodes,pools=True)
            metadata['product_parts']=[dict(name=b.label,slot=slot,node=b.run)
                for slot,b in enumerate(bindings) if int(b.kind)==1 and nodes[b.run].id=='authored-live-parts']
        if nearby:
            metadata['real_prepared_input']['single_body_nearby']=dict(rows=nearby,
                original_effects=[copy.deepcopy(original['effects'][i]) for i in nearby],
                neighbour_geometry_inferred=False)
        if fixed:
            attach_fixed(words,metadata,original,fixed_values)
            source=source.replace('gpu/product_','gpu/product_fixed_',1)
        if prepared.get('_product_burst_patterns'):
            from portable_burst_control_specs import product_patterns
            from portable_specs import LIMITS as limits
            names=[c['name'] for c in prepared['chars']]
            patterns=prepared['policies']['config']['burst_pattern']
            packed=product_patterns(names,patterns)
            for who,value in enumerate(packed):
                words[limits['WEAPON_BASE']+who*limits['WEAPON_WORDS']+3]|=value
            if any(packed):metadata['product_burst_patterns']=dict(patterns=copy.deepcopy(patterns),encoded=packed,cpu_schedule_or_state_supplied=False)
        if add_patterns is not None:
            from portable_product_add_attack import attach
            return attach(source,words,metadata,prepared,add_patterns,original['enemy']['patterns'])
        return source,iw,ow,words,metadata
    from destructible_damage_policy import modifier_axis
    if any(modifier_axis(row['effect']) for row in prepared['effects']):
        if any(t.startswith('multi_hit:') for row in prepared['effects'] for t in row['effect'].get('trigger',{}).get('timing',[])):
            from portable_destructible_roster_input import compile_body_modifier_group_roster, GROUP_SOURCE, GROUP_INPUT_WORDS, OUTPUT_WORDS as group_ow
            from portable_battle_attack_group_input import product_history
            words,metadata=compile_body_modifier_group_roster(prepared,group_history=product_history(prepared))
            return finish(GROUP_SOURCE,GROUP_INPUT_WORDS,group_ow,words,metadata)
        from portable_destructible_roster_input import compile_body_modifier_roster, INPUT_WORDS as iw, OUTPUT_WORDS as ow
        words,metadata=compile_body_modifier_roster(prepared)
        return finish('gpu/product_target_battle_entry.slang',iw,ow,words,metadata)
    grouped = any(t.startswith('multi_hit:') for item in prepared['effects']
        for t in item['effect'].get('trigger',{}).get('timing',[]))
    if grouped:
        from portable_battle_attack_group_input import compile_battle, INPUT_WORDS as iw, OUTPUT_WORDS as ow
        from portable_battle_attack_group_input import product_history
        words, metadata = compile_battle(prepared,routing='native',group_history=product_history(prepared))
        return finish('gpu/product_group_battle_entry.slang', iw, ow, words, metadata)
    words, metadata = compile_projectile_battle(prepared)
    return finish(SOURCE, INPUT_WORDS, OUTPUT_WORDS, words, metadata)


def prepare(body):
    """Capture the existing Run while the original static hook prepares all effects."""
    import portable_roster_input
    original = portable_roster_input.prepare_static_inputs
    captured = {}
    coordinate_spec=None
    if 'coordinate' in body.get('reference_models',{}):
        from product_coordinate_model import normalize_product
        coordinate_spec=normalize_product(body['reference_models']['coordinate'])
    if 'typed_targets' in body.get('reference_models',{}):
        from product_typed_model import normalize_product as typed_model
        coordinate_spec={'coord':typed_model(body['reference_models']['typed_targets'])['coord']}
    def capture(run, stats):
        if captured:
            raise RuntimeError('Expected one original preparation')
        captured['run'] = run
        if coordinate_spec is not None:
            run.enemy['coord']=copy.deepcopy(coordinate_spec['coord'])
        from calculator.boss_pattern import boss_mode
        boss_mode(run.enemy) # Preserve native mode validation before any native allocation.
        def observe(manager):
            # Constructor metadata only: do not execute a CPU battle to obtain it.
            run._portable_detail_model_warnings = manager.effect_model_warnings()
        return original(run, stats, observe_manager=observe)
    with patch.object(portable_roster_input, 'prepare_static_inputs', capture):
        prepared = engine_worker.evaluate({**body, '_portable_static_inputs': True})
    if not captured or prepared['cpu_battle_executed'] is not False:
        raise RuntimeError('Original static preparation did not complete')
    if set(prepared.get('reference_models',{}))&{'coordinate','enemy_movement','named_range','typed_targets'}:
        captured['run'].expected=False
        captured['run'].config['rng_mode']='random'
    return prepared, captured['run']


def decode_payload(body, prepared, run, metadata, block):
    if metadata.get('product_ammo_cover') and not metadata.get('product_enemy_ammo'):
        raise UnsupportedPortable('inconsistent_ammo_metadata')
    ammo_attempts=None
    if not block or block[0]!=0:
        raise UnsupportedPortable('Shared battle status: '+str(block[0] if block else 'missing')+(' (history capacity exceeded)' if block and block[0] in (2,8) else ''))
    validate_world_frame_readback(block,metadata)
    view = decode(block if metadata.get('product_enemy_ammo') else block[:159744], metadata)
    if view['status'] != 0:
        raise UnsupportedPortable('Shared battle status: '+str(view['status']))
    if view['burst_trace_total'] != len(view['burst_trace']):
        raise UnsupportedPortable('Burst history capacity exceeded')
    if not view['queries']:
        raise RuntimeError('Missing final battle query')
    values = view['queries'][0]['damage']
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise RuntimeError('Invalid kernel damage totals')
    names = [c['name'] for c in prepared['chars']]
    from portable_world_result import read_product_control_log
    control_log=read_product_control_log(block,metadata,names,run.config['duration'],burst_trace=view['burst_trace'])
    result = SimpleNamespace(squad_total=sum(values), char_total=dict(zip(names, values)),
        duration=run.config['duration'], log=control_log, boss_unmodeled={})
    payload = engine_worker.sim.payload(run, result)
    camera = metadata['real_prepared_input']['camera']
    note = ' · '.join(camera) if camera else '없음'
    if len(camera) > 1:
        note += '  [camera_mode="shared" — 비현실적 상한]'
    fixed=body.get('burst_gauge_mode','fixed')=='fixed'
    events = [] if fixed else [dict(time=0., event='카메라 초점: '+note, character='')]
    for row in view['burst_trace']:
        event, who = row['event'], row['owner']
        if event not in (1,2,3,4,5,6,7,8,9) or not -1 <= who < 5:
            raise RuntimeError('Invalid shared burst event')
        if fixed and event==6:continue
        label = (f'reenter:{event-6} 사용' if 7 <= event <= 9 else
                 f'stage:{event} 사용' if event < 4 else
                 'full_burst 시작' if event == 4 else
                 '게이지 만충 100.0% → 1단계 진입 (소모)' if event == 6 else 'full_burst 종료')
        events.append(dict(time=round(row['time'],3), event=label, character=names[who] if who >= 0 else ''))
    requested = body.get('burst_policy','auto')
    policy = 'auto' if requested == 'mast3' and '마스트 : 로망틱 메이드' not in names else requested
    hypothetical = any(any(v != 0 for v in fields.values()) for fields in body.get('stat_deltas',{}).values())
    # engine_worker already validates and merges growth before constructing Run.
    for name, fields in body.get('patches',{}).items():
        if name in names:
            original = body['profile']['chars'][name].get('equip_skills',{})
            hypothetical |= any(original.get(k) != v for k,v in fields.get('equip_skills',{}).items())
    warnings = ['設定したボス行動で計算した参考値です。実機のギミックや生存の再現は未検証です。'
        if body.get('enemy',{}).get('patterns') else
        '固定条件の静止ボスを仮定した参考値です。ボス固有パターンと生存は未検証です。']
    warnings.extend(run._portable_detail_model_warnings)
    if requested == 'mast3' and policy == 'auto':
        warnings.append('マスト：ロマンチックメイドがいないため、3の倍数指定は適用せず全員オートで計算しました。')
    if hypothetical:
        warnings.append('仮ステータスを含みます。ゲーム内で可能な育成を示すものではありません。')
    payload.update(base_stats={n:dict(atk=prepared['base_atk'][i],hp=prepared['allies'][i]['base_hp'],**{'def':prepared['allies'][i]['base_defense']}) for i,n in enumerate(names)},
        burst_policy=policy, requested_burst_policy=requested, burst_patterns=copy.deepcopy(run.config.get('burst_pattern',{})),
        burst_timeline=events, shooting_policy=body.get('shooting_policy','auto'), weapon_mode_swap=body.get('weapon_mode_swap',False),
        burst_gauge_mode=body.get('burst_gauge_mode','fixed'), hypothetical=hypothetical,
        engine_revision=engine_worker.REVISION, app_warnings=warnings)
    models=[]
    if metadata.get('product_typed_lock'):
        from portable_product_typed_lock import read_result
        models.append(read_result(block,metadata,names,run.config['duration']))
    if metadata.get('product_typed_targets') and not metadata.get('product_typed_lock'):
        from portable_product_typed import read_result as typed_result
        models.append(typed_result(block,metadata,names,run.config['duration']))
    if metadata.get('product_coordinate') and not metadata.get('product_typed_lock'):
        from portable_product_coordinate import read_result,OUTPUT as COORDINATE_OUTPUT
        coordinate_block=(memoryview(block)[:COORDINATE_OUTPUT] if isinstance(block,array.array) else block[:COORDINATE_OUTPUT]) if metadata.get('product_coordinate_lock') else block[:COORDINATE_OUTPUT] if metadata.get('product_coordinate_cover') or metadata.get('product_coordinate_weighted') else block
        models.append(read_result(coordinate_block,metadata,names=names,duration=run.config['duration']))
    if metadata.get('product_enemy_healing') and not metadata.get('product_coordinate_healing'):
        from portable_product_healing import read_result
        from portable_enemy_healing_wire import OUTPUT as healing_output
        healing_block=block[:healing_output['OUTPUT_WORDS']] if metadata.get('product_healing_cover') else block
        if metadata.get('product_typed_healing'):
            if metadata.get('product_typed_lock'):
                from portable_product_typed_lock import HEALING_OUTPUT
            else:
                from portable_product_typed import HEALING_OUTPUT
            model=read_result(block,metadata,names,run.config['duration'],layout=HEALING_OUTPUT)
        elif metadata.get('product_ammo_healing'):
            from portable_enemy_healing_wire import AMMO_OUTPUT
            healing_block=block[:AMMO_OUTPUT['OUTPUT_WORDS']]
            model=read_result(healing_block,metadata,names,run.config['duration'],layout=AMMO_OUTPUT)
        else:model=read_result(healing_block,metadata,names,run.config['duration'])
        if model is not None:
            models.append(model)
    if metadata.get('product_weighted_incoming'):
        from portable_product_weighted import read_result
        model=read_result(block,metadata,names,run.config['duration'])
        if model is not None:
            models.append(model)
    if metadata.get('product_cover_defense'):
        from portable_product_cover import read_result
        options={}
        if metadata.get('product_typed_cover'):
            if metadata.get('product_typed_lock'):
                from portable_product_typed_lock import COVER_OUT,OUTPUT as TCO
            else:
                from portable_product_typed import COVER_OUT,OUTPUT as TCO
            options=dict(out=COVER_OUT,output=TCO)
        elif metadata.get('product_movement_range_cover'):
            from portable_product_movement_range import COVER_OUT,OUTPUT as MRO,check_cover_schema
            check_cover_schema();options=dict(out=COVER_OUT,output=MRO)
        model=read_result(block,metadata,names,run.config['duration'],**options)
        if model is not None:
            models.append(model)
    if metadata.get('product_enemy_ammo'):
        from portable_product_ammo import read_result
        from portable_enemy_ammo_wire import LAYOUT as AMMO
        ammo_block=block[:AMMO['OUTPUT_WORDS']] if metadata.get('product_ammo_cover') else block
        model=read_result(ammo_block,metadata)
        ammo_attempts=model['enemy_ammo']['attempts'] if model is not None else []
        if model is not None:
            models.append(model)
    if metadata.get('product_lock_on') and not metadata.get('product_typed_lock'):
        from portable_product_locks import read_result
        if metadata.get('product_coordinate_lock'):
            from portable_product_coordinate_lock import read_result
        model=read_result(block,metadata,run.config['duration'])
        if metadata.get('product_static_body_lock'):
            info=metadata['product_lock_on'];locks=model['lock_on']
            if (body.get('reference_models') or len(info['bindings'])!=1 or info['bindings'][0]['kind']!=0
                or info['declarations']['lock_on']['typed_bindings'] or locks['typed']['state'] or locks['typed']['attacks']
                or any(handle!=[0,0,1] for shot in locks['shots'] for handle in shot['handles'])):
                raise UnsupportedPortable('Static BODY Lock On specialization has a non-singleton actor domain')
            # All real lock/typed/packet banks were checked above. The
            # canonical undeclared CPU response has no declared-model fields.
        else:models.append(model)
    if metadata.get('product_movement_range'):
        from portable_product_movement_range import read_result as read_movement_range
        models.extend(read_movement_range(block,metadata,run.config['duration']))
    if metadata.get('product_enemy_movement') and not metadata.get('product_movement_range'):
        from portable_product_movement import read_result
        from portable_enemy_movement_wire import OUTPUT as MOVEMENT_OUTPUT
        movement_block=block[:MOVEMENT_OUTPUT] if metadata.get('product_movement_cover') else block
        model=read_result(movement_block,metadata,run.config['duration'])
        models.append(model)
    if metadata.get('product_named_range') and not metadata.get('product_movement_range'):
        from portable_product_named_range import read_result
        from portable_named_range_battle_wire import OUTPUT as RANGE_OUTPUT
        range_block=block[:RANGE_OUTPUT] if metadata.get('product_named_range_cover') else block
        model=read_result(range_block,metadata,run.config['duration'])
        models.append(model)
    if models:
        from product_reference_models import combine_public,warning
        payload['reference_models']=combine_public(models)
        # Match the product CPU order: base, effect models, declarations,
        # optional policy and hypothetical-growth notices. Keep list equality
        # strict; a later declaration must not reorder the other notices.
        payload['app_warnings'].insert(1+len(run._portable_detail_model_warnings),
            warning(payload['reference_models']['declarations']))
    if 'manual_cover_sequences' in body:
        payload['manual_cover_sequences']=copy.deepcopy(body['manual_cover_sequences'])
    if body.get('enemy',{}).get('parts'):
        from portable_world_result import read_product_parts
        from detail_world import read_parts
        payload['parts_state']=read_product_parts(block,metadata,read_parts(body['enemy']['parts']),run.config['duration'])
    if body.get('enemy',{}).get('patterns'):
        from portable_world_result import read_histories
        from portable_specs import LIMITS
        head=LIMITS['WORLD_FRAME_OUTPUT_BASE']
        if len(block)<LIMITS['WORLD_FRAME_OUTPUT_WORDS']:
            raise UnsupportedPortable('Incomplete product world readback')
        for offset,capacity in ((1,512),(2,2048),(6,2048),(7,1024)):
            if block[head+offset]>capacity:
                raise UnsupportedPortable('Product world history capacity exceeded')
        nodes=metadata['product_world']['nodes']
        for i in range(block[head+2]):
            at=head+2832+i*6;kind,node,arg=block[at:at+3]
            if kind not in (1,2,3,4,5,6,7,8) or node>=(len(names) if kind==6 else len(nodes)):
                raise UnsupportedPortable('Unknown product world history identity')
            if kind==2 and arg not in (1,2,3,4):
                raise UnsupportedPortable('Unknown product world closing outcome')
        from portable_product_add_attack import query_sources
        # Cover receipts were completely validated above. The ADD/ammo
        # reader owns its original full prefix, not the appended cover bank.
        sources=query_sources(ammo_block if metadata.get('product_ammo_cover') else block,metadata,ammo_attempts=ammo_attempts)
        world=read_histories(block,nodes,attack_sources=sources)
        if any(not math.isfinite(row['time']) or row['time']<0 for row in world['boss_log']):
            raise UnsupportedPortable('Invalid product world history time')
        for hit in world['hits']:
            if hit['owner']>=len(names) or any(not math.isfinite(hit[k]) or hit[k]<0
                    for k in ('time','damage','decoy','shield','cover','hp','hp_after')):
                raise UnsupportedPortable('Invalid product incoming hit record')
        kinds={node['id']:node['kind'] for node in nodes}
        payload['boss_patterns']=copy.deepcopy(body['enemy']['patterns'])
        payload['boss_timeline']=[dict(time=round(row['time'],6),pattern=row['pattern'],kind=kinds[row['pattern']],
            event=row['event'],outcome=row['outcome'] or None) for row in world['boss_log']
            if row['pattern']!='authored-live-parts' and row['event'] in ('start','end','dispel')]
        if any(p.get('kind')=='attack' or p.get('kind')=='summon' and p.get('spec',{}).get('attack')
               for p in body['enemy']['patterns']):
            payload['incoming_hits']=[dict(time=round(hit['time'],6),pattern=hit['pattern'],target=names[hit['owner']],
                damage=round(hit['damage'],6),pierce=hit['pierce'],decoy=round(hit['decoy'],6),shield=round(hit['shield'],6),
                cover=round(hit['cover'],6),hp=round(hit['hp'],6),hp_after=round(hit['hp_after'],6),down=hit['down'],by=hit.get('by',''))
                for hit in world['hits']]
    return payload


def _evaluation(body, *, verification='full'):
    """Prepare and finish one request around a single deferred execution boundary."""
    if not isinstance(body,dict) or body.get('compute_backend') not in BACKENDS:
        raise ValueError('Expected an explicit shared kernel detail request')
    if verification not in ('full', 'deferred'):raise ValueError('Invalid verification policy')
    requested = body['compute_backend']
    backend = BACKENDS[requested]
    body = copy.deepcopy({k:v for k,v in body.items() if not k.startswith('_') and k != 'verification'})
    if type(body.get('verify_detail',False)) is not bool:
        raise ValueError('CPU照合の指定が不正です。')
    started = time.perf_counter()
    capture_root = Path(os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT',ROOT/'research/portable-build/product-detail'))
    folder = capture_root / uuid.uuid4().hex
    folder.mkdir(parents=True,exist_ok=False)
    record = dict(verification=verification,requested=requested, capture_id=folder.name, native_execution_verified=False, browser_execution_reported=False, gpu_execution_verified=False, cpu_battle_used_as_gpu_input=False)
    explicit_image=False
    historical_status={}
    record.update(historical_status)
    def save():
        (folder/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stage='prepare'
    unsupported=None
    try:
        record['request_sha256'] = hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        prepared, run = prepare(body)
        policy = execution_environment(backend)
        # These need product history/operation projections, not silent omission.
        from detail_world import read_parts
        parts=read_parts(body.get('enemy',{}).get('parts',[]))
        # The shared world compiler normalizes original tap/hold controls.
        # Its admission still rejects unconnected aim/cover/reload/burst axes.
        stage='compile'
        source, input_words, output_words, words, metadata = compile_product(prepared)
        if parts and [p['name'] for p in parts]!=[p['name'] for p in metadata.get('product_parts',[])]:
            raise UnsupportedPortable('Original part identities disagree with the shared world registry')
        wire = array.array('I',[1,*words])
        if sys.byteorder != 'little':wire.byteswap()
        packed = wire.tobytes()
        (folder/'input.bin').write_bytes(packed)
        record['source'] = source
        stage='transport'
        evidence,artifact_receipt,member = yield dict(source=source,input_words=input_words,output_words=output_words,
            packed=packed,backend=backend,policy=policy,explicit_image=explicit_image,folder=folder,
            historical_status=historical_status,record=record)
        transport, timing = verified_transport(evidence,backend,cases=member['cases'] if member else 1)
        input_hash=member['input_sha256'] if member else evidence['input_sha256']
        output_hash=member['output_sha256'] if member else evidence['output_sha256']
        record.update(gpu_execution_verified=evidence.get('gpu_execution_verified',False),input_sha256=input_hash,output_sha256=output_hash)
        if backend=='native':record['native_execution_verified']=True
        if backend=='browser':record.update(browser_execution_reported=True,native_execution_verified=False)
        if member:record['batch']=member
        block = array.array('I');block.frombytes((folder/'readback.bin').read_bytes())
        if sys.byteorder != 'little':block.byteswap()
        stage='decode'
        payload = decode_payload(body,prepared,run,metadata,block)
        payload['compute'] = dict(requested=requested,backend=requested,capture_id=folder.name,device=evidence['transport']['device'],
            elapsed_ms=(time.perf_counter()-started)*1000,gpu_execution_verified=backend not in ('native','browser'),
            input_sha256=input_hash,output_sha256=output_hash,source=source,
            scope='shared autonomous battle; CPU verified for this request')
        if backend=='native':payload['compute'].update(native_execution_verified=True,scope='native CPU execution of the shared kernel; full CPU payload verified for this request')
        if backend=='browser':payload['compute'].update(browser_execution_reported=True,native_execution_verified=False,timing_scope='client-reported',scope='browser execution reported; full CPU payload verified for this request')
        payload['compute'][timing] = transport[timing]
        if member:
            payload['compute']['batch']=member
            payload['compute']['input_sha256_scope']='logical single-case framing; physical transfer is batch.transport_input_sha256'
            payload['compute']['timing_scope']='shared batch transport; not an individual case duration'
        payload['compute'].update(historical_status)
        if artifact_receipt is not None:
            payload['compute']['artifact_provider']=artifact_receipt['identity']['provider']
            payload['compute']['artifact_key']=artifact_receipt['key']
    except Exception as error:
        from engine_gpu_admission import UnsupportedEngineKeys
        if isinstance(error, UnsupportedEngineKeys):
            record.update(error=str(error),error_type=type(error).__name__,stage=stage)
            save()
            raise
        unsupported=dict(getattr(error,'effect_context',{}),reason=str(error))
        record.update(backend='cpu',error=str(error),error_type=type(error).__name__,stage=stage,
            traceback=traceback.format_exc(),unsupported=[unsupported]);save()

    if unsupported is not None:
        if requested == 'native_detail' and verification == 'deferred':
            marker=dict(stage=stage,reason=unsupported['reason'],unsupported=[unsupported],capture_id=folder.name)
            record['cpu_fallback_pending']=marker
            save();return dict(cpu_fallback_pending=marker)
        return _cpu_fallback(body,folder,record,started=started)

    if unsupported is None and verification == 'deferred':
        payload['compute'].update(cpu_verification=dict(status='pending'),scope='shared kernel; CPU payload verification pending')
        (folder/'gpu-payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        record.update(backend=requested,cpu_verification=dict(status='pending'),elapsed_seconds=time.perf_counter()-started)
        save();return payload

    # CPU evaluation is outside the compiled execution exception boundary and runs once per
    # request, after readback or a compiled execution failure. A CPU error is never retried or
    # misclassified as an unsupported compiled execution condition.
    try:
        cpu = engine_worker.evaluate(body)
    except Exception as error:
        record.update(cpu_error=dict(error=str(error),error_type=type(error).__name__,
            stage='cpu',traceback=traceback.format_exc()),elapsed_seconds=time.perf_counter()-started)
        try:save()
        except Exception as logging_error:error.add_note('CPU failure record could not be saved: '+type(logging_error).__name__)
        raise
    (folder/'cpu-payload.json').write_text(json.dumps(cpu,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    differences = payload_differences(payload,cpu)
    record.update(cpu_verification=dict(matched=not differences,differing_fields=differences),elapsed_seconds=time.perf_counter()-started)
    (folder/'gpu-payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if differences:
        cpu['compute'] = dict(requested=requested,backend='cpu',capture_id=folder.name,fallback_reason='共通カーネルとCPUの照合に差があったため、CPUの結果を表示しています。',
            gpu_result_rejected=True,cpu_verification=record['cpu_verification'],**historical_status)
        record['backend']='cpu';save();return cpu
    payload['compute']['cpu_verification']=record['cpu_verification']
    record['backend']=requested;save();return payload


def payload_differences(payload,cpu):
    differences = [key for key in payload.keys() | cpu.keys() if key != 'compute' and
        (key not in payload or key not in cpu or payload[key] != cpu[key])]
    return differences


def _cpu_fallback(body,folder,record,*,started=None):
    """Authoritative fallback construction shared by inline and fresh services."""
    if started is None:started=time.perf_counter()
    try:
        cpu=engine_worker.evaluate(body)
    except Exception as error:
        record['elapsed_seconds']=time.perf_counter()-started
        record['cpu_error']=dict(error=str(error),error_type=type(error).__name__,stage='cpu',traceback=traceback.format_exc())
        try:(folder/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        except Exception as logging_error:error.add_note('CPU failure record could not be saved: '+type(logging_error).__name__)
        raise
    (folder/'cpu-payload.json').write_text(json.dumps(cpu,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    historical_status={k:v for k,v in record.items() if k=='saved_cubin_admission' or k.startswith('historical_link_')}
    cpu['compute']=dict(requested=record['requested'],backend='cpu',capture_id=folder.name,
        fallback_reason='共通カーネルの未対応条件または実行エラーのため、CPUで計算しました。',unsupported=record['unsupported'],
        fallback_stage=record['stage'],gpu_execution_verified=record['gpu_execution_verified'],**historical_status)
    return cpu


def cpu_fallback_portable_detail(rows):
    """Stateless CPU fallback, bound to the failed native request capture."""
    if not isinstance(rows,list) or not 1<=len(rows)<=8:raise ValueError('Expected 1..8 fallback rows')
    results=[]
    for row in rows:
        body=copy.deepcopy({k:v for k,v in row['body'].items() if not k.startswith('_') and k!='verification'})
        capture_id=row['capture_id']
        if not isinstance(capture_id,str) or len(capture_id)!=32 or any(c not in '0123456789abcdef' for c in capture_id):
            raise ValueError('Invalid capture id')
        folder=Path(os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT',ROOT/'research/portable-build/product-detail'))/capture_id
        record=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        digest=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if record.get('request_sha256')!=digest or record.get('capture_id')!=capture_id:
            raise ValueError('Fallback request does not match capture')
        if record.get('requested')!='native_detail' or record.get('verification')!='deferred' or not record.get('cpu_fallback_pending'):
            raise ValueError('Capture is not a pending native fallback')
        results.append(_cpu_fallback(body,folder,record))
    return results


def verify_portable_detail(bodies_with_capture_ids):
    """Fresh CPU comparison of saved payloads; no retained preparation state."""
    if not isinstance(bodies_with_capture_ids,list) or not 1<=len(bodies_with_capture_ids)<=8:
        raise ValueError('Expected 1..8 verification rows')
    results=[]
    for row in bodies_with_capture_ids:
        body=copy.deepcopy({k:v for k,v in row['body'].items() if not k.startswith('_') and k!='verification'})
        capture_id=row['capture_id']
        if not isinstance(capture_id,str) or len(capture_id)!=32 or any(c not in '0123456789abcdef' for c in capture_id):
            raise ValueError('Invalid capture id')
        folder=Path(os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT',ROOT/'research/portable-build/product-detail'))/capture_id
        record=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        digest=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if record.get('request_sha256')!=digest or record.get('capture_id')!=capture_id:
            raise ValueError('Verification request does not match capture')
        payload=json.loads((folder/'gpu-payload.json').read_text(encoding='utf-8'))
        cpu=engine_worker.evaluate(body)
        (folder/'cpu-payload.json').write_text(json.dumps(cpu,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        differences=payload_differences(payload,cpu)
        check=dict(matched=not differences,differing_fields=differences)
        record.update(cpu_verification=check,verification='deferred-checked')
        if differences:
            historical_status={k:v for k,v in record.items() if k=='saved_cubin_admission' or k.startswith('historical_link_')}
            cpu['compute']=dict(requested=record['requested'],backend='cpu',capture_id=capture_id,
                fallback_reason='共通カーネルとCPUの照合に差があったため、CPUの結果を表示しています。',
                gpu_result_rejected=True,cpu_verification=check,**historical_status)
            record['backend']='cpu'
        (folder/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        results.append(dict(**check,cpu_result=cpu))
    return results


MAX_PRODUCT_BATCH=8
NATIVE_PRODUCT_BATCH=32


def batch_limit(bodies):
    return NATIVE_PRODUCT_BATCH if bodies and all(isinstance(b,dict) and b.get("compute_backend") in ("native_detail","browser_detail") for b in bodies) else MAX_PRODUCT_BATCH


def _execute_prepared(plans):
    """One actual transport for compatible prepared cases, with honest views."""
    first=plans[0];count=len(plans)
    if not 1<=count<=(NATIVE_PRODUCT_BATCH if first["backend"]=="native" else MAX_PRODUCT_BATCH):raise ValueError('Shared detail batch exceeds its bounded case count')
    key=lambda p:(p['source'],p['input_words'],p['output_words'],p['backend'],p['policy'],p['explicit_image'],p['folder'].parent)
    if any(key(p)!=key(first) for p in plans):raise ValueError('Shared detail transport requires identical source, wire, policy and capture root')
    folder=first['folder'] if count==1 else first['folder'].parent/('batch-'+uuid.uuid4().hex)
    if count>1:folder.mkdir(exist_ok=False)
    packed=first['packed'] if count==1 else struct.pack('<I',count)+b''.join(p['packed'][4:] for p in plans)
    if any(len(p['packed'])!=4+4*first['input_words'] or p['packed'][:4]!=struct.pack('<I',1) for p in plans):
        raise ValueError('Complete single-case framing required before batching')
    if count>1:(folder/'input.bin').write_bytes(packed)
    write=lambda name,value:(folder/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try:
        if count>1:
            from portable_capture_storage import space_status
            budget=space_status(folder,len(packed)+2*count*first['output_words']*4)
            write('storage-budget.json',budget)
            if not budget['passed']:raise RuntimeError('Insufficient space for shared batch and complete member readbacks')
        raw,evidence=execute(first['source'],'portableEvents',packed,first['input_words'],first['output_words'],first['backend'],readback_path=folder/'readback.bin')
        if raw is not None:raise RuntimeError('Expected bounded file readback')
        write('evidence.json',evidence)
        receipt=None
        if count==1:return [(evidence,receipt,None)]
        verified_transport(evidence,first['backend'],cases=count)
        data=(folder/'readback.bin').read_bytes();stride=first['output_words']*4
        if (len(data)!=count*stride or hashlib.sha256(packed).hexdigest()!=evidence['input_sha256']
                or hashlib.sha256(data).hexdigest()!=evidence['output_sha256']):
            raise RuntimeError('Shared batch full input/readback digest mismatch')
        members=[];returned=[]
        for index,p in enumerate(plans):
            block=data[index*stride:(index+1)*stride]
            member=dict(capture_id=folder.name,index=index,cases=count,input_words=first['input_words'],output_words=first['output_words'],
                input_sha256=hashlib.sha256(p['packed']).hexdigest(),output_sha256=hashlib.sha256(block).hexdigest(),
                transport_input_sha256=evidence['input_sha256'],transport_output_sha256=evidence['output_sha256'],
                input_scope='single-case framing of this exact physical batch member',output_scope='exact readback slice')
            (p['folder']/'readback.bin').write_bytes(block)
            (p['folder']/'batch-member.json').write_text(json.dumps(member,indent=2)+'\n')
            (p['folder']/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
            members.append(dict(member,capture_id=p['folder'].name));returned.append((evidence,receipt,member))
        write('result.json',dict(schema='product-batch-transport-v1',source=first['source'],backend=first['backend'],cases=count,
            gpu_execution_verified=first["backend"]!="native",**(dict(native_execution_verified=True) if first["backend"]=="native" else {}),scope='Shared physical transport only; each member has its own complete CPU result check',members=members))
        return returned
    except Exception as error:
        if count>1:write('result.json',dict(schema='product-batch-transport-v1',source=first['source'],backend=first['backend'],cases=count,
            scope='Failed shared transport; preserve all member failures',error=str(error),error_type=type(error).__name__,gpu_execution_verified=False))
        raise


def _finish_evaluation(generator,*,outcome=None,error=None):
    try:
        if error is None:generator.send(outcome)
        else:generator.throw(error)
    except StopIteration as finished:return finished.value
    raise RuntimeError('A product request may have only one compiled execution boundary')


def evaluate(body):
    """Original single-request behavior through the same batch-capable engine."""
    if isinstance(body,dict) and body.get('compute_backend')=='browser_detail':raise ValueError('ブラウザ計算は画面からジョブとして実行してください。')
    generator=_evaluation(body)
    try:
        try:plan=next(generator)
        except StopIteration as finished:return finished.value
        try:outcome=_execute_prepared([plan])[0]
        except Exception as error:return _finish_evaluation(generator,error=error)
        return _finish_evaluation(generator,outcome=outcome)
    finally:generator.close()


def evaluate_many(bodies, *, verification='full'):
    """Preserve row identity and per-case CPU checks in bounded shared dispatches."""
    if not isinstance(bodies,list) or not 1<=len(bodies)<=batch_limit(bodies):
        raise ValueError('Shared detail evaluations exceed the backend batch limit')
    if any(isinstance(b,dict) and b.get('compute_backend')=='browser_detail' for b in bodies):raise ValueError('ブラウザ計算は画面からジョブとして実行してください。')
    results=[None]*len(bodies);groups={};generators=[]
    try:
        for index,body in enumerate(bodies):
            generator=_evaluation(body,verification=verification);generators.append(generator)
            try:plan=next(generator)
            except StopIteration as finished:results[index]=dict(result=finished.value);continue
            except Exception as error:results[index]=dict(error=str(error));continue
            key=(plan['source'],plan['input_words'],plan['output_words'],plan['backend'],tuple(sorted(plan['policy'].items())),plan['explicit_image'],str(plan['folder'].parent))
            groups.setdefault(key,[]).append((index,generator,plan))
        from concurrent.futures import ThreadPoolExecutor
        from portable_native import HOST_THREADS
        from portable_throughput import split_threads
        native=[g for g in groups.values() if g[0][2]['backend']=='native' and not g[0][2]['policy'] and not g[0][2]['explicit_image']]
        budgets=([min(len(g),HOST_THREADS.get()) for g in native] if verification=='deferred' and HOST_THREADS.get() is not None else split_threads([len(g) for g in native],HOST_THREADS.get() or os.cpu_count() or 1))
        def dispatch(group,budget):
            token=HOST_THREADS.set(budget)
            try:return _execute_prepared([p for _,_,p in group])
            finally:HOST_THREADS.reset(token)
        with ThreadPoolExecutor(max_workers=min(len(native),HOST_THREADS.get() or os.cpu_count() or 1) or 1) as pool:
            futures={id(g):pool.submit(dispatch,g,b) for g,b in zip(native,budgets)}
            for group in groups.values():
                try:
                    outcomes=futures[id(group)].result() if id(group) in futures else _execute_prepared([p for _,_,p in group]);error=None
                    if len(outcomes)!=len(group):raise RuntimeError('Shared batch result count mismatch')
                except Exception as failure:outcomes=[None]*len(group);error=failure
                for (index,generator,_),outcome in zip(group,outcomes):
                    try:results[index]=dict(result=_finish_evaluation(generator,outcome=outcome,error=error))
                    except Exception as failure:results[index]=dict(error=str(failure))
        return results
    finally:
        for generator in generators:generator.close()


def _browser_rows(bodies, uploads=None, *, verification='full'):
    """Stateless prepare/finish around the existing single-yield evaluator."""
    import base64
    import gzip
    import io
    from portable_wasm import build_product
    if not isinstance(bodies,list) or not 1<=len(bodies)<=32 or any(not isinstance(b,dict) or b.get('compute_backend')!='browser_detail' for b in bodies):
        raise ValueError('Expected 1..32 browser detail evaluations')
    if uploads is not None and (not isinstance(uploads,list) or len(uploads)!=len(bodies)):
        raise ValueError('Browser upload row count mismatch')
    results=[];builds={}
    for index,body in enumerate(bodies):
        generator=_evaluation(body,verification=verification)
        try:
            try:plan=next(generator)
            except StopIteration as done:
                results.append(dict(result=done.value));continue
            try:
                digest=hashlib.sha256(plan['packed']).hexdigest()
                if uploads is None:
                    if plan['source'] not in builds:builds[plan['source']]=build_product(ROOT,plan['source'])[1]
                    receipt=builds[plan['source']]
                    wire=dict(source=plan['source'],input_words=plan['input_words'],output_words=plan['output_words'],
                        input_sha256=digest,wasm_identity=receipt['identity'],input_gzip_base64=base64.b64encode(gzip.compress(plan['packed'],mtime=0)).decode())
                    (plan['folder']/'browser-prepare.json').write_text(json.dumps(dict(phase='browser-prepare',record=plan['record'],wire=wire,build=receipt),indent=2)+'\n')
                    results.append(dict(wire=wire));continue
                upload=uploads[index]
                if not isinstance(upload,dict) or upload.get('input_sha256')!=digest:raise ValueError('Browser input sha256 mismatch')
                seconds=upload.get('browser_seconds')
                if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:raise ValueError('Invalid client-reported browser seconds')
                encoded=upload.get('readback_gzip_base64')
                if not isinstance(encoded,str) or len(encoded)>12*1024*1024:raise ValueError('Invalid browser readback encoding')
                expected=plan['output_words']*4
                with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded,validate=True))) as stream:raw=stream.read(expected+1)
                if len(raw)!=expected:raise ValueError('Browser readback length mismatch')
                device=upload.get('device')
                if not isinstance(device,str) or not device or len(device)>512:raise ValueError('Invalid browser device summary')
                evidence=dict(backend='browser',browser_execution_reported=True,gpu_execution_verified=False,native_execution_verified=False,
                    input_sha256=digest,output_sha256=hashlib.sha256(raw).hexdigest(),
                    transport=dict(command_status='completed',cases=1,device=device,browser_seconds=seconds,timing_scope='client-reported'))
                verified_transport(evidence,'browser')
                (plan['folder']/'readback.bin').write_bytes(raw)
                (plan['folder']/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
                outcome=(evidence,None,None);failure=None
            except Exception as error:
                outcome=None;failure=error
            result=_finish_evaluation(generator,outcome=outcome,error=failure)
            results.append(dict(result=result))
        except Exception as error:results.append(dict(error=str(error)))
        finally:generator.close()
    return results


def prepare_browser_wires(bodies, *, verification='full'):
    return _browser_rows(bodies,verification=verification)


def finish_browser(bodies,uploads, *, verification='full'):
    if not isinstance(uploads,list):raise ValueError('Browser uploads must be a list')
    return _browser_rows(bodies,uploads,verification=verification)
