"""Prepare comparison of an early exit for enemy-state existence checks after all current gates/transfer terminate.

Initial unlocalized Metal finding stays recorded. Production is unchanged by this tool. Every candidate output is
compared byte-for-byte/hash with its control; a mismatch is captured and stops.
"""
import copy,hashlib,importlib.util,io,json,statistics,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='795a9e5b684796b3b6a2fb9b59546e60401a5503'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as runtime
from portable_specs import ABI,LIMITS as L
class Captured(BaseException):pass
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
 folder=P/'portable-build'/('target-state-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
 if variant=='candidate':
  path=folder/'gpu/event_runtime.slang';source=path.read_text()
  old='uint64_t targetStateStack(inout Runtime s,int name,uint64_t when,out bool present)'
  new='uint64_t targetStateStack(inout Runtime s,int name,uint64_t when,bool wantCount,out bool present)'
  assert source.count(old)==1;source=source.replace(old,new)
  old='targetStateStack(s,name,when,present)'
  assert source.count(old)==1;source=source.replace(old,'targetStateStack(s,name,when,kind==C_TARGET_STACK,present)')
  old='if(member) { present=true;count=larger(count,carrierStackValue(s,slot)); }'
  assert source.count(old)==1
  source=source.replace(old,'if(member) { present=true;if(!wantCount) return ONE;count=larger(count,carrierStackValue(s,slot)); }')
  path.write_text(source)
 wrapper=folder/('target_state_'+variant+'_runtime.slang');wrapper.write_text('#include "gpu/event_runtime.slang"\n');return wrapper.relative_to(R).as_posix()
def main():
 assert ABI==0x5045566E
 barrier=load('portable-target-states-timing-order');broad=load('portable-target-states-broad-validation');current=load('portable-combat-metal')
 assert barrier['passed'] and barrier['windows_execution_and_transfer_terminal'] and not barrier['verification_processes']
 assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit']==SOURCE and broad['mac_gates']==35 and current['passed']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 spec=importlib.util.spec_from_file_location('target-state_benchmark_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 programs=[]
 def collect(p,**kwargs):programs.extend(p);raise Captured()
 report=P/'portable-combat-metal.json';saved=report.read_bytes();oldargv=sys.argv;sys.argv=[sys.argv[0],'--backend','metal'];v.run_programs=collect
 try:
  try:v.main()
  except Captured:pass
 finally:report.write_bytes(saved);sys.argv=oldargv
 assert len(programs)==2754
 paths={name:prepare(name) for name in ('control','candidate')};one,many=runtime.execute,runtime.execute_batches
 def run(name,items):
  def single(source,*args,**kwargs):
   assert source=='gpu/event_runtime.slang';return one(paths[name],*args,**kwargs)
  def sequence(source,*args,**kwargs):
   assert source=='gpu/event_runtime.slang';return many(paths[name],*args,**kwargs)
  runtime.execute=single;runtime.execute_batches=sequence
  try:return runtime.dispatch_programs(items,backend='metal')
  finally:runtime.execute=one;runtime.execute_batches=many
 parity={}
 for name in paths:
  raw,e=run(name,programs)
  if e['input_sha256']!=current['input_sha256'] or e['output_sha256']!=current['output_sha256']:
   fail=P/'portable-build'/('target-state-'+name+'-nonmatching.bin');fail.write_bytes(raw);save('portable-target-states-candidate-failure',dict(passed=False,variant=name,evidence=e,raw_path=str(fail)));raise RuntimeError('Candidate/control output mismatch captured; no retry')
  parity[name]=e;del raw
 save('portable-target-states-candidate-parity',dict(passed=True,source_commit=SOURCE,programs=2754,all_input_and_output_bytes_equal=True,parity=parity))
 fixtures={c['name']:c for c in v.fixtures()}
 workloads={'ordinary':fixtures['auto-magazine-reload'],
            'absent':fixtures['target-state-absent-0-target_state:'],
            'present':fixtures['target-state-exact-4-2-target_state:'],
            'multiple-enemies':fixtures['target-state-any-live-enemy'],
            'periodic':fixtures['target-state-dot-target_state:'],
            'stack-maximum':fixtures['target-state-max-3-5']}


 rows={}
 for label,c in workloads.items():
  items=[v.compile_case(c)]*32;samples={name:[] for name in paths};baseline=None
  for sample in range(4):
   for name in paths:
    raw,e=run(name,items)
    if baseline is None:baseline=raw
    if raw!=baseline:
     fail=P/'portable-build'/('target-state-'+label+'-'+name+'-nonmatching.bin');fail.write_bytes(raw);save('portable-target-states-candidate-failure',dict(passed=False,workload=label,variant=name,sample=sample,evidence=e,raw_path=str(fail)));raise RuntimeError('Workload mismatch captured; no retry')
    samples[name].append(dict(warmup=sample==0,**e));print(label,sample,name,e['transport']['gpu_seconds'],flush=True)
  medians={name:statistics.median(x['transport']['gpu_seconds'] for x in a[1:]) for name,a in samples.items()};ranges={name:[min(x['transport']['gpu_seconds'] for x in a[1:]),max(x['transport']['gpu_seconds'] for x in a[1:])] for name,a in samples.items()}
  rows[label]=dict(programs=32,median_gpu_seconds=medians,ranges=ranges,candidate_to_control_ratio=medians['candidate']/medians['control'],samples=samples)
 save('portable-target-states-benchmark',dict(passed=True,source_commit=SOURCE,all_2754_input_output_bytes_equal=True,production_change_adopted=False,parity=parity,workloads=rows,timing_order=barrier,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),initial_metal_finding_open=True,scope='Sequential warmup plus3 samples per variant,32 programs per workload on Apple M5. Initial unlocalized raw mismatch remains documented. No CUDA-speed/full-roster/physical-peak-memory claim; desktop GPU activity not excluded.'))
if __name__=='__main__':main()
