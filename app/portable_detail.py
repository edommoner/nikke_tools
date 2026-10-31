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


def verified_transport(evidence, backend):
    timing = 'gpu_seconds' if backend == 'metal' else 'host_dispatch_seconds'
    try:
        transport = evidence['transport']
        valid = (evidence['backend'] == backend and evidence['gpu_execution_verified'] is True
            and transport['command_status'] == 'completed' and type(transport['cases']) is int and transport['cases'] == 1
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
    """Select an existing wire by actual effect requirements, never by character."""
    from portable_product_ammo import required as ammo_required,compile_product as compile_ammo
    if not prepared.get('_product_ammo_compiled') and ammo_required(prepared):
        return compile_ammo(prepared,compile_product)
    from portable_product_weighted import required as weighted_required,compile_product as compile_weighted
    if not prepared.get('_product_weighted_compiled') and weighted_required(prepared):
        return compile_weighted(prepared,compile_product)
    from portable_product_cover import required as cover_required,compile_product as compile_cover
    if not prepared.get('_product_cover_compiled') and cover_required(prepared):
        return compile_cover(prepared,compile_product)
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
    gauge_mode=prepared['policies']['config'].get('burst_gauge_mode','fixed')
    if gauge_mode not in ('fixed','accumulate'):raise UnsupportedPortable('Unported burst gauge mode')
    fixed=gauge_mode=='fixed'
    if fixed and manual_cover:
        raise UnsupportedPortable('Fixed burst with manual cover needs a combined literal control header')
    if fixed:
        cfg=prepared['policies']['config']
        first=cfg.get('first_burst_time',3.)
        regen=[c.get('burst_regen_time',2.) for c in prepared['chars']]
        if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=180 for v in [first,*regen]):
            raise UnsupportedPortable('Fixed burst delays require finite binary64 seconds in [0,180]')
        # Reuse existing static lowering; readiness itself is supplied below.
        # This copy is validation input only, never a simulated CPU schedule.
        prepared=copy.deepcopy(prepared)
        prepared['policies']['config']['burst_gauge_mode']='accumulate'
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
            from portable_specs import LIMITS as limits
            base=limits['WORLD_CONTROL_INPUT_BASE']
            version=words[base+1]
            tap_mask=words[base+5] if version==2 else 0
            if (version not in (1,2) or version==1 and any(words[base+5:base+16])
                    or version==2 and (not 0<tap_mask<32 or any(words[base+6:base+16]))):
                raise UnsupportedPortable('Fixed burst requires a canonical automatic or tap control header')
            words[base+1]=5 if tap_mask else 4
            if tap_mask:words[base+10]=tap_mask
            words[base+5:base+10]=[0x46424731,*struct.unpack('<II',struct.pack('<d',first)),*struct.unpack('<II',struct.pack('<d',max(regen)))]
            metadata['real_prepared_input']['policy']=copy.deepcopy(original['policies'])
            metadata['product_fixed_burst']=dict(first_seconds=first,member_regen_seconds=regen,
                readiness_regen_seconds=max(regen),CPU_state_or_schedule_as_input=False)
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
    def capture(run, stats):
        if captured:
            raise RuntimeError('Expected one original preparation')
        captured['run'] = run
        def observe(manager):
            # Constructor metadata only: do not execute a CPU battle to obtain it.
            run._portable_detail_model_warnings = manager.effect_model_warnings()
        return original(run, stats, observe_manager=observe)
    with patch.object(portable_roster_input, 'prepare_static_inputs', capture):
        prepared = engine_worker.evaluate({**body, '_portable_static_inputs': True})
    if not captured or prepared['cpu_battle_executed'] is not False:
        raise RuntimeError('Original static preparation did not complete')
    return prepared, captured['run']


def decode_payload(body, prepared, run, metadata, block):
    ammo_attempts=None
    if not block or block[0]!=0:
        raise UnsupportedPortable('Shared battle status: '+str(block[0] if block else 'missing')+(' (history capacity exceeded)' if block and block[0] in (2,8) else ''))
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
    if metadata.get('product_enemy_healing'):
        from portable_product_healing import read_result
        model=read_result(block,metadata,names,run.config['duration'])
        if model is not None:
            from product_reference_models import WARNING
            payload['reference_models']=model;payload['app_warnings'].append(WARNING)
    if metadata.get('product_weighted_incoming'):
        from portable_product_weighted import read_result
        from product_reference_models import warning
        model=read_result(block,metadata,names,run.config['duration'])
        if model is not None:
            payload['reference_models']=model;payload['app_warnings'].append(warning(model['declarations']))
    if metadata.get('product_cover_defense'):
        from portable_product_cover import read_result
        from product_reference_models import warning
        model=read_result(block,metadata,names,run.config['duration'])
        if model is not None:
            payload['reference_models']=model;payload['app_warnings'].append(warning(model['declarations']))
    if metadata.get('product_enemy_ammo'):
        from portable_product_ammo import read_result
        from product_reference_models import warning
        model=read_result(block,metadata)
        ammo_attempts=model['enemy_ammo']['attempts'] if model is not None else []
        if model is not None:
            payload['reference_models']=model;payload['app_warnings'].append(warning(model['declarations']))
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
        sources=query_sources(block,metadata,ammo_attempts=ammo_attempts)
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


def evaluate(body):
    """One isolated product request; reject unsupported conditions before dispatch."""
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
        with patch.dict(os.environ,policy) if policy else nullcontext():
            context=saved_program(source,folder) if explicit_image else nullcontext()
            with context as artifact_receipt:
                history=artifact_receipt['identity'].get('historical_link_environment') if artifact_receipt is not None else None
                if history is not None:
                    from portable_linked_artifact import validate_historical_environment
                    validate_historical_environment(history)
                    historical_status.update(historical_link_preservation_verified=False,
                        historical_link_missing_processes_count=len(history['missing_identities']),historical_link_termination_cause=history['termination_cause'])
                    record.update(historical_status)
                raw, evidence = execute(source,'portableEvents',packed,input_words,output_words,backend,readback_path=folder/'readback.bin')
                if raw is not None:raise RuntimeError('Expected bounded file readback')
                (folder/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if artifact_receipt is not None:
            if evidence.get('transport',{}).get('compile_artifact')!=artifact_receipt:
                raise RuntimeError('Saved product CUBIN transport receipt mismatch')
            record['artifact_receipt']=artifact_receipt
            historical_status['saved_cubin_admission']='verified';record.update(historical_status)
        transport, timing = verified_transport(evidence,backend)
        record.update(gpu_execution_verified=evidence['gpu_execution_verified'],input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'])
        block = array.array('I');block.frombytes((folder/'readback.bin').read_bytes())
        if sys.byteorder != 'little':block.byteswap()
        payload = decode_payload(body,prepared,run,metadata,block)
        payload['compute'] = dict(requested=requested,backend=requested,capture_id=folder.name,device=evidence['transport']['device'],
            elapsed_ms=(time.perf_counter()-started)*1000,gpu_execution_verified=True,
            input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'],source=source,
            scope='shared autonomous battle; CPU verified for this request')
        payload['compute'][timing] = transport[timing]
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
