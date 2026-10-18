"""Interleave full detailed squad calculations against the frozen timer executor."""
import argparse,copy,hashlib,importlib.util,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a
from gpu_selector import Cuda
import detail_gpu as current
ap=argparse.ArgumentParser();ap.add_argument('--baseline-engine',default='research/ports/v80-periodic-targets-native-stage/app/detail_gpu.py');ap.add_argument('--output',default='research/periodic-targets-normal-performance.json');args=ap.parse_args()
old_source=ROOT/args.baseline_engine
spec=importlib.util.spec_from_file_location('periodic_normal_before',old_source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'research/enemy-fields-api-fixture.json',ROOT/'scripts/detail_coverage.py',old_source]+[d/n for d in (ROOT/'app',old_source.parent) for n in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
base=json.loads((ROOT/'research/enemy-fields-api-fixture.json').read_text(encoding='utf-8'));compiled=[]
for i in range(8):
    body=copy.deepcopy(base);body['seed']=12345;body['stat_deltas'][body['squad'][0]]['atk']+=1000*(i+1)
    compiled.append(a.evaluate({**body,'_compile_gpu_detail':True}))
def inputs():return hashlib.sha256(json.dumps([(c['program'],c['base_stats'],c['enemy'],c['body']) for c in compiled],sort_keys=True,ensure_ascii=True).encode()).hexdigest()
stimulus_sha256=inputs();semantic=None;device=Cuda()
def once(engine):
    global semantic
    started=time.perf_counter();results=engine.evaluate_full_many(device,compiled,module_backend='native',batch_size=8);wall=(time.perf_counter()-started)*1000
    assert all(r['compute']['batch_size']==8 for r in results)
    keys=('total_damage','members','base_stats','burst_timeline','seed','burst_policy','shooting_policy','burst_gauge_mode','parts_state','boss_timeline','incoming_hits','weapon_mode_swap')
    value=[{key:r.get(key) for key in keys} for r in results]
    if semantic is not None:assert value==semantic
    semantic=value
    return dict(wall_ms=wall,kernel_ms=results[0]['compute']['timings_ms']['kernel_cuda'])
samples={'before':[],'after':[]}
try:
    once(old);once(current)
    for i in range(3):
        for label,engine in ([('before',old),('after',current)] if i%2==0 else [('after',current),('before',old)]):samples[label].append(once(engine))
finally:device.close()
assert stimulus_sha256==inputs()
assert source_sha256=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_sha256}
summary={key:{'kernel_ms':statistics.median(r['kernel_ms'] for r in rows),'wall_ms':statistics.median(r['wall_ms'] for r in rows)} for key,rows in samples.items()}
report=dict(passed=True,source_sha256=source_sha256,stimulus_sha256=stimulus_sha256,semantic=semantic,samples=samples,medians=summary,kernel_speedup=summary['before']['kernel_ms']/summary['after']['kernel_ms'],wall_speedup=summary['before']['wall_ms']/summary['after']['wall_ms'],batch_squads=8,interleaved=True,normal_full_calculation=True,scope='45s detailed squad calculation; owned equipment and distinct temporary attack changes, weapons and burst included; no API transport or result cache')
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ('passed','medians','kernel_speedup','wall_speedup')}))
