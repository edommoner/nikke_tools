"""Interleaved real eight-squad kernels; static-count optimization experiment."""
import copy,hashlib,importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a
from gpu_selector import Cuda
import detail_gpu as g
prior=ROOT/'research/ports/v73-world-conditions-native-stage/app/detail_gpu.py'
s=importlib.util.spec_from_file_location('dynamic_count_before_specialization',prior);old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),prior,ROOT/'research/world-conditions-api-fixture.json',ROOT/'scripts/detail_coverage.py',ROOT/'app/detail_effects.cu',ROOT/'app/detail_effects-sm86.cubin',ROOT/'app/detail_effects-sm86.json']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
fixture=json.loads((ROOT/'research/world-conditions-api-fixture.json').read_text(encoding='utf-8'))
requests={'dynamic':[],'static':[]};generators=[];changed=0
try:
    for delta in range(1000,8001,1000):
        body=copy.deepcopy(fixture);body['seed']=12345;body['stat_deltas']={body['squad'][0]:{'atk':delta}}
        current=a.evaluate({**body,'_compile_gpu_detail':True})
        dynamic=old.compile_full(current['prepared'],lambda c:current['base_stats'][c['name']],body,current['policy'],current['requested_policy'])
        for qb,qa in zip(dynamic['program']['effects'],current['program']['effects']):
            expected=qb.copy()
            for j in range(int(qb[14])):
                at=15+j*3
                if qb[at] in (40,41):
                    expected[at:at+3]=[22,0,int(1>=qb[at+2] if qb[at]==40 else 1<=qb[at+2])];changed+=1
            assert expected==qa
        for kind,compiled in (('dynamic',dynamic),('static',current)):
            evaluation=g._full_evaluation(None,compiled);generators.append(evaluation);requests[kind].append(next(evaluation))
    assert changed==16
    script=requests['static'][0]['script']
    assert all(row['script']==script for group in requests.values() for row in group)
    device=Cuda();samples={k:[] for k in requests};semantic=None
    try:
        for iteration in range(4):
            for kind in (('dynamic','static') if iteration%2==0 else ('static','dynamic')):
                rows=requests[kind]
                result=g.run(device,[r['program'] for r in rows],script,[r['enemy'] for r in rows],[r['base_stats'] for r in rows],module_backend='native',seeds=[r['seed'] for r in rows])
                value=dict(queries=result['queries'],totals=result['totals'])
                if semantic is not None:assert semantic==value
                semantic=value
                if iteration:samples[kind].append(result['timings_ms']['kernel_cuda'])
    finally:device.close()
finally:
    for evaluation in generators:evaluation.close()
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
medians={kind:statistics.median(values) for kind,values in samples.items()}
report=dict(passed=True,source_sha256=before,kernel_ms=samples,median_kernel_ms=medians,kernel_ratio=medians['dynamic']/medians['static'],repetitions=3,alternating_order=True,candidates=8,folded_conditions=changed,semantic_sha256=hashlib.sha256(json.dumps(semantic,sort_keys=True).encode()).hexdigest(),overall_speedup_claim=False,scope='Actual45s five-member squad simulations; compilation, API and transfer are outside CUDA-event time. Small differences require interpretation; no whole-system speedup claim.')
(ROOT/'research/world-conditions-specialization-benchmark.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,median_kernel_ms=medians,kernel_ratio=report['kernel_ratio'])))
