"""Actual HP-pool receipt workload; not a whole-battle throughput claim."""
import argparse,hashlib,importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from gpu_selector import Cuda
from impact_specs import ActorHandle,Impact,impact_command
import detail_gpu as g
s=importlib.util.spec_from_file_location('summon_lookup_setup',ROOT/'scripts/verify-summon-sources-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/verify-summon-sources-detail.py',ROOT/'scripts/summon_source_cases.py',ROOT/'tests/test_target_counter_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'app/detail_effects-sm86.cubin',ROOT/'app/detail_effects-sm86.json']
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    bm,boss,enemy,program=v.prepare([dict(id='wave',kind='summon',spec=dict(count=127,hp=1e9))])
    script=[[0,15,0,0,0,-1,0,0]]
    for repeat in range(256):
        for identity in range(127):
            command=impact_command(.1,Impact(v.NAMES[0],ActorHandle(5,identity),0,2,.25),v.NAMES);command[1]=14;script.append(command)
    script += [[.1,2,134,0,126,0,0,0],[.2,5,0,0,0,-1,0,0],[.2,2,126,0,0,1,0,0]]
    stimulus=hashlib.sha256(json.dumps([program,script],sort_keys=True).encode()).hexdigest();device=Cuda();samples=[];semantic=None
    try:
        for iteration in range(6):
            result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend='native')
            source,impact=result['queries'][0]
            assert source[2:7]==[1,1,0,64,0] and source[11:15]==[128,.25,0,8128],source
            assert impact[0]==32512 and impact[25:27]==[32512,8128] and result['totals'][0]==[0]*5,impact
            value=dict(queries=result['queries'],totals=result['totals'])
            if semantic is not None:assert semantic==value
            semantic=value
            if iteration:samples.append(result['timings_ms']['kernel_cuda'])
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,source_sha256=before,stimulus_sha256=stimulus,semantic=semantic,receipts=32512,repetitions=5,kernel_ms=samples,median_kernel_ms=statistics.median(samples),scope='Authored actual add HP updates and typed receipt publication across127 live actors. This is not autonomous weapon routing or a gameplay speedup claim.')
    if args.baseline:
        prior=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert prior['passed'] and prior['stimulus_sha256']==stimulus and prior['semantic']==semantic
        report['comparison']=dict(baseline=args.baseline,kernel_speedup=prior['median_kernel_ms']/report['median_kernel_ms'])
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,median_kernel_ms=report['median_kernel_ms'],comparison=report.get('comparison'))))

if __name__=='__main__':main()
