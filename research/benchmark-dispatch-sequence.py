"""Compare dispatch sizes only after all correctness/transfer gates terminate."""
import argparse,hashlib,importlib.util,json,statistics,struct,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ff9a10d175f266708e2d572132b045f1c04083bb'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import dispatch_programs
from portable_specs import LIMITS as L
class Collected(BaseException):pass

def load(n):return json.loads((P/(n+'.json')).read_text())
def main():
    barrier=load('portable-dispatch-sequence-timing-order');assert barrier['passed'] and barrier['windows_execution_and_transfer_terminal'] and not barrier['verification_processes']
    broad=load('portable-dispatch-sequence-broad-validation');assert broad['passed'] and broad['mac_gates']==31 and broad['source_commit']==SOURCE
    baseline=load('portable-dispatch-sequence-metal');assert baseline['passed'] and baseline['source_commit']==SOURCE
    subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
    spec=importlib.util.spec_from_file_location('sequence_benchmark_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    programs=[]
    def collect(p,**kwargs):programs.extend(p);raise Collected()
    path=P/'portable-combat-metal.json';saved=path.read_bytes();oldargv=sys.argv;sys.argv=[sys.argv[0],'--backend','metal'];v.run_programs=collect
    try:
        try:v.main()
        except Collected:pass
    finally:path.write_bytes(saved);sys.argv=oldargv
    assert len(programs)==2006;programs+=programs[:44];samples={str(size):[] for size in (2048,1024,512)}
    for sample in range(4):
        for size in (2048,1024,512):
            start=time.perf_counter();raw,e=dispatch_programs(programs,backend='metal',batch_size=size);wall=time.perf_counter()-start
            assert e['input_sha256']==baseline['input_sha256'] and e['output_sha256']==baseline['output_sha256']
            assert e['source_sha256']==baseline['source_sha256'];assert len(raw)==2050*L['OUTPUT_WORDS']*4;del raw
            counts=[d['transport']['cases'] for d in e['dispatches']]
            rows=dict(warmup=sample==0,wall_seconds=wall,gpu_seconds=e['transport']['gpu_seconds'],dispatch_counts=counts,allocated_wire_buffer_bytes=(1+max(counts)*L['INPUT_WORDS'])*4+max(counts)*L['OUTPUT_WORDS']*4,evidence=e)
            samples[str(size)].append(rows);print(size,sample,wall,rows['gpu_seconds'],flush=True)
    summaries={}
    for size,rows in samples.items():
        measured=rows[1:];summaries[size]=dict(median_gpu_seconds=statistics.median(x['gpu_seconds'] for x in measured),gpu_range=[min(x['gpu_seconds'] for x in measured),max(x['gpu_seconds'] for x in measured)],median_wall_seconds=statistics.median(x['wall_seconds'] for x in measured),wall_range=[min(x['wall_seconds'] for x in measured),max(x['wall_seconds'] for x in measured)],allocated_wire_buffer_bytes=measured[0]['allocated_wire_buffer_bytes'],dispatch_counts=measured[0]['dispatch_counts'])
    out=dict(passed=True,source_commit=SOURCE,programs=2050,all_input_and_output_bytes_equal=True,samples=samples,summaries=summaries,production_default_changed=False,timing_order=barrier,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Sequential warmup and3 samples per size on Apple M5 with all2050 inputs. Buffer bytes are requested wire allocation sizes, not measured peak/device-private memory. Desktop GPU activity is not excluded; no CUDA speed claim.')
    (P/'portable-dispatch-sequence-benchmark.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
