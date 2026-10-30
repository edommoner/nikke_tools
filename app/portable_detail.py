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
    from portable_enemy_specs import lower_single_body_nearby
    original=prepared
    prepared,nearby=lower_single_body_nearby(prepared)
    def finish(source,iw,ow,words,metadata):
        if nearby:
            metadata['real_prepared_input']['single_body_nearby']=dict(rows=nearby,
                original_effects=[copy.deepcopy(original['effects'][i]) for i in nearby],
                neighbour_geometry_inferred=False)
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
    view = decode(block[:159744], metadata)
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
    result = SimpleNamespace(squad_total=sum(values), char_total=dict(zip(names, values)),
        duration=run.config['duration'], log=None, boss_unmodeled={})
    payload = engine_worker.sim.payload(run, result)
    camera = metadata['real_prepared_input']['camera']
    note = ' · '.join(camera) if camera else '없음'
    if len(camera) > 1:
        note += '  [camera_mode="shared" — 비현실적 상한]'
    events = [dict(time=0., event='카메라 초점: '+note, character='')]
    for row in view['burst_trace']:
        event, who = row['event'], row['owner']
        if event not in (1,2,3,4,5,6,7,8,9) or not -1 <= who < 5:
            raise RuntimeError('Invalid shared burst event')
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
    warnings = ['固定条件の静止ボスを仮定した参考値です。ボス固有パターンと生存は未検証です。']
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
        if body.get('burst_gauge_mode','fixed') != 'accumulate':
            raise UnsupportedPortable('共通GPU詳細は現在「バーストゲージ：実蓄積」で利用できます。固定周期はCPUで計算します。')
        # These need product history/operation projections, not silent omission.
        if body.get('enemy',{}).get('patterns') or body.get('enemy',{}).get('parts'):
            raise UnsupportedPortable('製品用GPUのボス行動・パーツ結果変換は未接続です。')
        if any(any(k != 'weapon_mode_swap' or v for k,v in c.get('control',{}).items()) for c in prepared['chars']):
            raise UnsupportedPortable('製品用GPUの手動操作結果変換は未接続です。')
        source, input_words, output_words, words, metadata = compile_product(prepared)
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
    except (UnsupportedPortable,ValueError,RuntimeError,OSError) as error:
        record.update(backend='cpu',error=str(error));save()
        cpu = engine_worker.evaluate(body)
        cpu['compute'] = dict(requested=requested,backend='cpu',capture_id=folder.name,fallback_reason='共通GPUの未対応条件または実行エラーのため、CPUで計算しました。',unsupported=[dict(reason=str(error))],gpu_execution_verified=record['gpu_execution_verified'],**historical_status)
        return cpu
