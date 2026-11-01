"""Product battle adapter: original preparation -> shared GPU -> original payload.

No CPU battle, damage or event schedule is used as GPU input. Until broader
product admission is established every successful GPU result is CPU-checked.
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
from types import SimpleNamespace
from unittest.mock import patch
import uuid

import engine_worker
from portable_runtime import UnsupportedPortable, decode
from portable_projectile_roster_input import compile_projectile_battle, INPUT_WORDS, OUTPUT_WORDS
from portable_backend import execute
from portable_product_artifact import descriptor_file, saved_program

SOURCE = 'gpu/product_battle_entry.slang'
ROOT = Path(__file__).resolve().parents[1]
BACKENDS = {'metal_detail': 'metal', 'cuda_shared_detail': 'cuda'}


def execution_environment(backend):
    """Require warm generation plus an explicit saved image or native cache."""
    if backend == 'metal':
        return {}
    if platform.system() != 'Windows':
        raise UnsupportedPortable('共通CUDA詳細はWindowsで利用できます。')
    keys=('NIKKE_SLANG_GENERATION_CACHE',) if descriptor_file() is not None else ('NIKKE_SLANG_GENERATION_CACHE','NIKKE_CUDA_COMPILE_CACHE')
    for key in keys:
        value = os.environ.get(key)
        if not value or not Path(value).is_absolute() or not Path(value).is_dir():
            raise UnsupportedPortable('共通CUDAの実行用キャッシュが未準備です: '+key)
    return dict(NIKKE_SLANG_GENERATION_REQUIRED='1', NIKKE_CUDA_CACHE_REQUIRED='1',
                NIKKE_CUDA_ARTIFACT='cubin', NIKKE_CUDA_PTXAS_OPT_LEVEL='1')


def verified_transport(evidence, backend, *, cases=1):
    timing = 'gpu_seconds' if backend == 'metal' else 'host_dispatch_seconds'
    try:
        transport = evidence['transport']
        valid = (evidence['backend'] == backend and evidence['gpu_execution_verified'] is True
            and transport['command_status'] == 'completed' and type(transport['cases']) is int and transport['cases'] == cases
            and isinstance(transport['device'], str) and bool(transport['device'])
            and type(transport[timing]) in (int,float) and math.isfinite(transport[timing]) and transport[timing] >= 0
            and all(isinstance(evidence[k],str) and len(evidence[k]) == 64
                and all(c in '0123456789abcdef' for c in evidence[k]) for k in ('input_sha256','output_sha256')))
    except (KeyError, TypeError, OverflowError):
        valid = False
    if not valid:
        raise RuntimeError('Shared GPU execution metadata is incomplete or unverified')
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
        raise UnsupportedPortable('Shared world clock readback is missing or incomplete; the GPU result is rejected')


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
        raise UnsupportedPortable('Declared CPU reference consumer requires its matching shared GPU product wire; no model may be silently omitted')
    from portable_enemy_specs import lower_single_body_nearby
    original=prepared
    # The product promises the canonical battle's named-carrier lifecycle.
    # Keep every equipment definition and let the existing shared GPU carrier
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
            words,metadata=compile_body_modifier_group_roster(prepared)
            return finish(GROUP_SOURCE,GROUP_INPUT_WORDS,group_ow,words,metadata)
        from portable_destructible_roster_input import compile_body_modifier_roster, INPUT_WORDS as iw, OUTPUT_WORDS as ow
        words,metadata=compile_body_modifier_roster(prepared)
        return finish('gpu/product_target_battle_entry.slang',iw,ow,words,metadata)
    grouped = any(t.startswith('multi_hit:') for item in prepared['effects']
        for t in item['effect'].get('trigger',{}).get('timing',[]))
    if grouped:
        from portable_battle_attack_group_input import compile_battle, INPUT_WORDS as iw, OUTPUT_WORDS as ow
        words, metadata = compile_battle(prepared,routing='native')
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
        boss_mode(run.enemy) # Preserve native mode validation before any GPU allocation.
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
        raise RuntimeError('Invalid GPU damage totals')
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
        if metadata.get('product_ammo_healing'):
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
        if metadata.get('product_movement_range_cover'):
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


def _evaluation(body):
    """Prepare and finish one request around a single deferred GPU boundary."""
    if not isinstance(body,dict) or body.get('compute_backend') not in BACKENDS:
        raise ValueError('Expected an explicit shared GPU detail request')
    requested = body['compute_backend']
    backend = BACKENDS[requested]
    body = copy.deepcopy({k:v for k,v in body.items() if not k.startswith('_')})
    if type(body.get('verify_detail',False)) is not bool:
        raise ValueError('CPU照合の指定が不正です。')
    started = time.perf_counter()
    capture_root = Path(os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT',ROOT/'research/portable-build/product-detail'))
    folder = capture_root / uuid.uuid4().hex
    folder.mkdir(parents=True,exist_ok=False)
    record = dict(requested=requested, capture_id=folder.name, gpu_execution_verified=False, cpu_battle_used_as_gpu_input=False)
    explicit_image=backend=='cuda' and 'NIKKE_SHARED_CUDA_ARTIFACTS' in os.environ
    historical_status=dict(saved_cubin_admission='not_admitted') if explicit_image else {}
    record.update(historical_status)
    def save():
        (folder/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try:
        record['request_sha256'] = hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        policy = execution_environment(backend)
        prepared, run = prepare(body)
        # These need product history/operation projections, not silent omission.
        from detail_world import read_parts
        parts=read_parts(body.get('enemy',{}).get('parts',[]))
        # The shared world compiler normalizes original tap/hold controls.
        # Its admission still rejects unconnected aim/cover/reload/burst axes.
        source, input_words, output_words, words, metadata = compile_product(prepared)
        if parts and [p['name'] for p in parts]!=[p['name'] for p in metadata.get('product_parts',[])]:
            raise UnsupportedPortable('Original part identities disagree with the shared world registry')
        wire = array.array('I',[1,*words])
        if sys.byteorder != 'little':wire.byteswap()
        packed = wire.tobytes()
        (folder/'input.bin').write_bytes(packed)
        record['source'] = source
        evidence,artifact_receipt,member = yield dict(source=source,input_words=input_words,output_words=output_words,
            packed=packed,backend=backend,policy=policy,explicit_image=explicit_image,folder=folder,
            historical_status=historical_status,record=record)
        if artifact_receipt is not None:
            if evidence.get('transport',{}).get('compile_artifact')!=artifact_receipt:
                raise RuntimeError('Saved product CUBIN transport receipt mismatch')
            record['artifact_receipt']=artifact_receipt
            historical_status['saved_cubin_admission']='verified';record.update(historical_status)
        transport, timing = verified_transport(evidence,backend,cases=member['cases'] if member else 1)
        input_hash=member['input_sha256'] if member else evidence['input_sha256']
        output_hash=member['output_sha256'] if member else evidence['output_sha256']
        record.update(gpu_execution_verified=evidence['gpu_execution_verified'],input_sha256=input_hash,output_sha256=output_hash)
        if member:record['batch']=member
        block = array.array('I');block.frombytes((folder/'readback.bin').read_bytes())
        if sys.byteorder != 'little':block.byteswap()
        payload = decode_payload(body,prepared,run,metadata,block)
        payload['compute'] = dict(requested=requested,backend=requested,capture_id=folder.name,device=evidence['transport']['device'],
            elapsed_ms=(time.perf_counter()-started)*1000,gpu_execution_verified=True,
            input_sha256=input_hash,output_sha256=output_hash,source=source,
            scope='shared autonomous battle; CPU verified for this request')
        payload['compute'][timing] = transport[timing]
        if member:
            payload['compute']['batch']=member
            payload['compute']['input_sha256_scope']='logical single-case framing; physical transfer is batch.transport_input_sha256'
            payload['compute']['timing_scope']='shared batch transport; not an individual case duration'
        payload['compute'].update(historical_status)
        if artifact_receipt is not None:
            payload['compute']['artifact_provider']=artifact_receipt['identity']['provider']
            payload['compute']['artifact_key']=artifact_receipt['key']
        # Compare the complete product result, not just the damage total. CPU is
        # run strictly after GPU readback and cannot provide any GPU state.
        cpu = engine_worker.evaluate(body)
        (folder/'cpu-payload.json').write_text(json.dumps(cpu,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        differences = [key for key in payload.keys() | cpu.keys() if key != 'compute' and
            (key not in payload or key not in cpu or payload[key] != cpu[key])]
        record.update(cpu_verification=dict(matched=not differences,differing_fields=differences),elapsed_seconds=time.perf_counter()-started)
        (folder/'gpu-payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if differences:
            cpu['compute'] = dict(requested=requested,backend='cpu',capture_id=folder.name,fallback_reason='共通GPUとCPUの照合に差があったため、CPUの結果を表示しています。',
                gpu_result_rejected=True,cpu_verification=record['cpu_verification'],**historical_status)
            record['backend']='cpu';save();return cpu
        payload['compute']['cpu_verification']=record['cpu_verification']
        record['backend']=requested;save();return payload
    except (UnsupportedPortable,ValueError,RuntimeError,OSError,KeyError,TypeError,ImportError) as error:
        unsupported=dict(getattr(error,'effect_context',{}),reason=str(error))
        record.update(backend='cpu',error=str(error),error_type=type(error).__name__,unsupported=[unsupported]);save()
        cpu = engine_worker.evaluate(body)
        cpu['compute'] = dict(requested=requested,backend='cpu',capture_id=folder.name,fallback_reason='共通GPUの未対応条件または実行エラーのため、CPUで計算しました。',unsupported=[unsupported],gpu_execution_verified=record['gpu_execution_verified'],**historical_status)
        return cpu


MAX_PRODUCT_BATCH=8


def _execute_prepared(plans):
    """One actual transport for compatible prepared cases, with honest views."""
    first=plans[0];count=len(plans)
    if not 1<=count<=MAX_PRODUCT_BATCH:raise ValueError('Shared detail batch exceeds its bounded case count')
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
        with patch.dict(os.environ,first['policy']) if first['policy'] else nullcontext():
            context=saved_program(first['source'],folder) if first['explicit_image'] else nullcontext()
            with context as receipt:
                history=receipt['identity'].get('historical_link_environment') if receipt is not None else None
                if history is not None:
                    from portable_linked_artifact import validate_historical_environment
                    validate_historical_environment(history)
                    for p in plans:
                        p['historical_status'].update(historical_link_preservation_verified=False,
                            historical_link_missing_processes_count=len(history['missing_identities']),historical_link_termination_cause=history['termination_cause'])
                        p['record'].update(p['historical_status'])
                raw,evidence=execute(first['source'],'portableEvents',packed,first['input_words'],first['output_words'],first['backend'],readback_path=folder/'readback.bin')
                if raw is not None:raise RuntimeError('Expected bounded file readback')
                write('evidence.json',evidence)
        if count==1:return [(evidence,receipt,None)]
        if receipt is not None and evidence.get('transport',{}).get('compile_artifact')!=receipt:
            raise RuntimeError('Saved product CUBIN transport receipt mismatch')
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
            gpu_execution_verified=True,scope='Shared physical transport only; each member has its own complete CPU result check',members=members))
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
    raise RuntimeError('A product request may have only one GPU execution boundary')


def evaluate(body):
    """Original single-request behavior through the same batch-capable engine."""
    generator=_evaluation(body)
    try:
        try:plan=next(generator)
        except StopIteration as finished:return finished.value
        try:outcome=_execute_prepared([plan])[0]
        except Exception as error:return _finish_evaluation(generator,error=error)
        return _finish_evaluation(generator,outcome=outcome)
    finally:generator.close()


def evaluate_many(bodies):
    """Preserve row identity and per-case CPU checks in bounded shared dispatches."""
    if not isinstance(bodies,list) or not 1<=len(bodies)<=MAX_PRODUCT_BATCH:
        raise ValueError('Shared detail evaluations must contain one to eight requests')
    results=[None]*len(bodies);groups={};generators=[]
    try:
        for index,body in enumerate(bodies):
            generator=_evaluation(body);generators.append(generator)
            try:plan=next(generator)
            except StopIteration as finished:results[index]=dict(result=finished.value);continue
            except (Exception,SystemExit) as error:results[index]=dict(error=str(error));continue
            key=(plan['source'],plan['input_words'],plan['output_words'],plan['backend'],tuple(sorted(plan['policy'].items())),plan['explicit_image'],str(plan['folder'].parent))
            groups.setdefault(key,[]).append((index,generator,plan))
        for group in groups.values():
            try:
                outcomes=_execute_prepared([p for _,_,p in group]);error=None
                if len(outcomes)!=len(group):raise RuntimeError('Shared batch result count mismatch')
            except Exception as failure:outcomes=[None]*len(group);error=failure
            for (index,generator,_),outcome in zip(group,outcomes):
                try:results[index]=dict(result=_finish_evaluation(generator,outcome=outcome,error=error))
                except (Exception,SystemExit) as failure:results[index]=dict(error=str(failure))
        return results
    finally:
        for generator in generators:generator.close()
