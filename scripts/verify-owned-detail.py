"""Combined owned-data acceptance: real five-member battles, no CPU event replay."""
import argparse,copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_gpu import evaluate_full
from gpu_selector import Cuda
from gpu_service import resolve_verification


def fixtures():
    # Fictional owned growth, including gear, overload arrays, cubes, collection,
    # per-character console and account console. Retain every raw character skill.
    base=json.loads((ROOT/'research/detail-charge-immunity-api-fixture.json').read_text(encoding='utf-8'))
    base.update(duration=60,_debug_random_state=True)
    for variant in ('imported','growth-and-stats','reordered'):
        for shooting in ('auto','character'):
            for gauge in ('fixed','accumulate'):
                body=copy.deepcopy(base)
                body.update(shooting_policy=shooting,burst_gauge_mode=gauge,burst_policy='rules')
                if variant=='imported':body.update(patches={},stat_deltas={})
                if variant=='reordered':body['squad']=list(reversed(body['squad']))
                yield f'{variant}-{shooting}-{gauge}',body
    # Exercise automatic candidate choice and the cycle preference using a real
    # alternate B2. The same imported entries are kept when positions change.
    spec=importlib.util.spec_from_file_location('owned_full_fixtures',ROOT/'scripts/verify-full-detail.py')
    full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
    for policy in ('auto','rules','mast3'):
        for reverse in (False,True):
            body=full.fixture(90,policy,grown=True,reverse=reverse)
            body.update(seed=12345,shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True)
            yield f'mast-{policy}-'+('right' if reverse else 'left'),body


def verify(device,backend):
    rows=[]
    for name,body in fixtures():
        compiled=adapter.evaluate({**body,'_compile_gpu_detail':True})
        gpu=evaluate_full(device,compiled,module_backend=backend)
        cpu=adapter.evaluate(body)
        final_rng=list(random.getstate()[1])
        resolved=resolve_verification(gpu,cpu)
        checks=resolved['compute']['cpu_verification'].copy()
        checks['final_random_state_equal']=gpu['_random_state']==final_rng
        checks['actual_gpu_execution']=resolved['compute']['backend']=='cuda_detail'
        checks['nonzero_battle']=cpu['total_damage']>0
        checks['burst_exercised']=any(e['event']=='full_burst 시작' for e in cpu['burst_timeline'])
        row=dict(name=name,backend=backend,passed=all(checks.values()),checks=checks,
                 cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],
                 members=cpu['members'],burst_count=sum(e['event']=='full_burst 시작' for e in cpu['burst_timeline']),
                 burst_patterns=cpu['burst_patterns'],gpu_ms=gpu['compute'].get('elapsed_ms'))
        if not row['passed']:row.update(cpu_bursts=cpu['burst_timeline'],gpu_bursts=gpu['burst_timeline'],gpu_members=gpu['members'])
        rows.append(row)
        print(json.dumps(dict(name=name,backend=backend,passed=row['passed'],checks=checks),ensure_ascii=True),flush=True)
    return rows


def positive_controls(rows):
    """Parity alone must not pass if owned growth or squad order is ignored."""
    indexed={(r['backend'],r['name']):r for r in rows}
    checks={}
    for backend in sorted({r['backend'] for r in rows}):
        for shooting in ('auto','character'):
            for gauge in ('fixed','accumulate'):
                suffix=f'{shooting}-{gauge}'
                imported=indexed[backend,'imported-'+suffix]
                grown=indexed[backend,'growth-and-stats-'+suffix]
                reordered=indexed[backend,'reordered-'+suffix]
                checks[f'{backend}-{suffix}']={
                    'growth_changes_damage':imported['cpu_total']!=grown['cpu_total'],
                    'positions_change_damage':grown['cpu_total']!=reordered['cpu_total'],
                }
    return checks


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--backend',choices=['native','ptx','both'],default='both')
    args=parser.parse_args()
    files=['scripts/verify-owned-detail.py','scripts/verify-full-detail.py','research/detail-charge-immunity-api-fixture.json',
           'app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json',
           'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    device=Cuda()
    try:rows=[r for b in (('native','ptx') if args.backend=='both' else (args.backend,)) for r in verify(device,b)]
    finally:device.close()
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
    controls=positive_controls(rows)
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows) and all(all(c.values()) for c in controls.values()),
        device=device.name,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,
        positive_controls=controls,
        scope='18 authored full-squad settings per backend with raw skills and fictional owned data; not all characters or all combinations.')
    (ROOT/'research/detail-owned-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
