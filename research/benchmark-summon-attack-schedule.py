"""Actor-shared real attack/HP execution over long periods without due shots."""
import argparse,hashlib,importlib.util,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from gpu_selector import Cuda
import detail_gpu as g
s=importlib.util.spec_from_file_location('source_attack_setup',ROOT/'scripts/verify-summon-sources-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/verify-summon-sources-detail.py',ROOT/'scripts/summon_source_cases.py',ROOT/'tests/test_target_counter_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'app/detail_effects-sm86.cubin',ROOT/'app/detail_effects-sm86.json']
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    attack=dict(coeff=100,atk=101,target='slot:1',pierce=True,hits=16,interval=2)
    bm,boss,enemy,program=v.prepare([dict(id='wave',kind='summon',spec=dict(name='npc',count=127,hp=1e9,attack=attack,attack_at=.5))])
    script=[[i/60,15,0,0,0,-1,0,0] for i in range(7201)]
    script += [[120,2,134,0,126,0,0,0],[120,5,0,0,0,-1,0,0],[120,2,119,0,0,1,0,0],[120,2,117,0,0,2,0,0]]
    stimulus=hashlib.sha256(json.dumps([program,script],sort_keys=True).encode()).hexdigest();device=Cuda();samples=[];semantic=None
    try:
        for iteration in range(6):
            result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend='native')
            source,receiver,first=result['queries'][0]
            assert source[2:7]==[1,1,0,0,0] and source[11]==128 and receiver[:5]==[7968,10000,10000,10000,10000]
            assert first[12]==2032 and math.isclose(first[0],.5) and first[3]==1 and first[11]==2,first
            assert result['totals'][0]==[0]*5
            value=dict(queries=result['queries'],totals=result['totals'])
            if semantic is not None:assert semantic==value
            semantic=value
            if iteration:samples.append(result['timings_ms']['kernel_cuda'])
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,source_sha256=before,stimulus_sha256=stimulus,semantic=semantic,world_frames=7201,source_actors=127,actual_incoming_hits=2032,repetitions=5,kernel_ms=samples,median_kernel_ms=statistics.median(samples),scope='Actual source schedule and incoming HP execution with127 live sources,120seconds and long periods without shots. This is not autonomous outgoing target routing or a whole-game speedup claim.')
    if args.baseline:
        prior=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert prior['passed'] and prior['stimulus_sha256']==stimulus and prior['semantic']==semantic
        report['comparison']=dict(baseline=args.baseline,kernel_speedup=prior['median_kernel_ms']/report['median_kernel_ms'])
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,median_kernel_ms=report['median_kernel_ms'],comparison=report.get('comparison'))))

if __name__=='__main__':main()
