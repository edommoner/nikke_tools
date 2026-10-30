"""Product battle adapter: original preparation -> shared GPU -> original payload.

No CPU battle, damage or event schedule is used as GPU input. Until broader
product admission is established every successful GPU result is CPU-checked.
"""
import array
import copy
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch
import uuid

import engine_worker
from portable_runtime import UnsupportedPortable, decode
from portable_projectile_roster_input import compile_projectile_battle, INPUT_WORDS, OUTPUT_WORDS
from portable_backend import execute

SOURCE = 'gpu/world_projectile_resident_entry.slang'
ROOT = Path(__file__).resolve().parents[1]


def prepare(body):
    """Capture the existing Run while the original static hook prepares all effects."""
    import portable_roster_input
    original = portable_roster_input.prepare_static_inputs
    captured = {}
    def capture(run, stats):
        if captured:
            raise RuntimeError('Expected one original preparation')
        captured['run'] = run
        return original(run, stats)
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
    if not isinstance(body,dict) or body.get('compute_backend') != 'metal_detail':
        raise ValueError('Expected an explicit Metal detail request')
    body = copy.deepcopy({k:v for k,v in body.items() if not k.startswith('_')})
    if type(body.get('verify_detail',False)) is not bool:
        raise ValueError('CPU照合の指定が不正です。')
    started = time.perf_counter()
    capture_root = Path(os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT',ROOT/'research/portable-build/product-detail'))
    folder = capture_root / uuid.uuid4().hex
    folder.mkdir(parents=True,exist_ok=False)
    record = dict(requested='metal_detail', gpu_execution_verified=False, cpu_battle_used_as_gpu_input=False)
    def save():
        (folder/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try:
        prepared, run = prepare(body)
        if body.get('burst_gauge_mode','fixed') != 'accumulate':
            raise UnsupportedPortable('Metal詳細は現在「バーストゲージ：実蓄積」で利用できます。固定周期はCPUで計算します。')
        # These need product history/operation projections, not silent omission.
        if body.get('enemy',{}).get('patterns') or body.get('enemy',{}).get('parts'):
            raise UnsupportedPortable('製品用GPUのボス行動・パーツ結果変換は未接続です。')
        if any(any(k != 'weapon_mode_swap' or v for k,v in c.get('control',{}).items()) for c in prepared['chars']):
            raise UnsupportedPortable('製品用GPUの手動操作結果変換は未接続です。')
        words, metadata = compile_projectile_battle(prepared)
        wire = array.array('I',[1,*words])
        if sys.byteorder != 'little':wire.byteswap()
        packed = wire.tobytes()
        (folder/'input.bin').write_bytes(packed)
        raw, evidence = execute(SOURCE,'portableEvents',packed,INPUT_WORDS,OUTPUT_WORDS,'metal',readback_path=folder/'readback.bin')
        if raw is not None:raise RuntimeError('Expected bounded file readback')
        (folder/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        record.update(gpu_execution_verified=evidence['gpu_execution_verified'],input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'])
        block = array.array('I');block.frombytes((folder/'readback.bin').read_bytes())
        if sys.byteorder != 'little':block.byteswap()
        payload = decode_payload(body,prepared,run,metadata,block)
        payload['compute'] = dict(requested='metal_detail',backend='metal_detail',device=evidence['transport']['device'],
            elapsed_ms=(time.perf_counter()-started)*1000,gpu_execution_verified=True,
            input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'],source=SOURCE,
            gpu_seconds=evidence['transport']['gpu_seconds'],scope='shared autonomous battle; CPU verified for this request')
        # Compare the complete product result, not just the damage total. CPU is
        # run strictly after GPU readback and cannot provide any GPU state.
        cpu = engine_worker.evaluate(body)
        (folder/'cpu-payload.json').write_text(json.dumps(cpu,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        differences = [key for key in payload.keys() | cpu.keys() if key != 'compute' and
            (key not in payload or key not in cpu or payload[key] != cpu[key])]
        record.update(cpu_verification=dict(matched=not differences,differing_fields=differences),elapsed_seconds=time.perf_counter()-started)
        (folder/'gpu-payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if differences:
            cpu['compute'] = dict(requested='metal_detail',backend='cpu',fallback_reason='共通GPUとCPUの照合に差があったため、CPUの結果を表示しています。',
                gpu_result_rejected=True,cpu_verification=record['cpu_verification'])
            record['backend']='cpu';save();return cpu
        payload['compute']['cpu_verification']=record['cpu_verification']
        record['backend']='metal_detail';save();return payload
    except (UnsupportedPortable,ValueError,RuntimeError,OSError) as error:
        record.update(backend='cpu',error=str(error));save()
        cpu = engine_worker.evaluate(body)
        cpu['compute'] = dict(requested='metal_detail',backend='cpu',fallback_reason='共通GPUの未対応条件または実行エラーのため、CPUで計算しました。',unsupported=[dict(reason=str(error))],gpu_execution_verified=record['gpu_execution_verified'])
        return cpu
