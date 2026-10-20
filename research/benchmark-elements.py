"""Compare scalar field access after all current gates/transfer terminate.

Initial unlocalized Metal finding stays recorded. Every candidate output is
compared byte-for-byte/hash with its control; a mismatch is captured and stops.
"""
import copy,hashlib,importlib.util,io,json,statistics,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='14c8e2e61fd6eeb9950a13c76f217ae62ca82fd9'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as runtime
from portable_specs import ABI,LIMITS as L
class Captured(BaseException):pass
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
 folder=P/'portable-build'/('element-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
 if variant=='accessors':
  path=folder/'gpu/element_runtime.slang';s=path.read_text()
  old='''        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind==0 && d.stat==S_element_code_override && s.alive[row]!=0 &&
           d.damageRoute==code &&
           (s.activeRecipients[row]&(1U<<who))!=0) return true;'''
  new='''        uint row=s.orderedRows[pass];
        if(s.alive[row]==0 || (s.activeRecipients[row]&(1U<<who))==0) continue;
        uint definition=s.carrierDefinition[row];
        if(definition_kind(s.inputBase,definition)==0 &&
           definition_stat(s.inputBase,definition)==S_element_code_override &&
           definition_damageRoute(s.inputBase,definition)==code) return true;'''
  assert s.count(old)==1;path.write_text(s.replace(old,new))
 wrapper=folder/('element_'+variant+'_runtime.slang');wrapper.write_text('#include "gpu/event_runtime.slang"\n');return wrapper.relative_to(R).as_posix()
def main():
 assert ABI==0x5045566B
 barrier=load('portable-element-timing-order');broad=load('portable-element-broad-validation');current=load('portable-combat-metal')
 assert barrier['passed'] and barrier['windows_execution_and_transfer_terminal'] and not barrier['verification_processes']
 assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit']==SOURCE and broad['mac_gates']==31 and current['passed']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 spec=importlib.util.spec_from_file_location('element_benchmark_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 programs=[]
 def collect(p,**kwargs):programs.extend(p);raise Captured()
 report=P/'portable-combat-metal.json';saved=report.read_bytes();oldargv=sys.argv;sys.argv=[sys.argv[0],'--backend','metal'];v.run_programs=collect
 try:
  try:v.main()
  except Captured:pass
 finally:report.write_bytes(saved);sys.argv=oldargv
 assert len(programs)==2182
 paths={name:prepare(name) for name in ('control','accessors')};one,many=runtime.execute,runtime.execute_batches
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
   fail=P/'portable-build'/('element-'+name+'-nonmatching.bin');fail.write_bytes(raw);save('portable-element-candidate-failure',dict(passed=False,variant=name,evidence=e,raw_path=str(fail)));raise RuntimeError('Candidate/control output mismatch captured; no retry')
  parity[name]=e;del raw
 save('portable-element-candidate-parity',dict(passed=True,source_commit=SOURCE,programs=2182,all_input_and_output_bytes_equal=True,parity=parity))
 fixtures={c['name']:c for c in v.fixtures()};late=copy.deepcopy(fixtures['element-capacity-256-False']);marker=late['effects'].pop(1);owner=late['owners'].pop(1);late['effects'].append(marker);late['owners'].append(owner)
 workloads={'ordinary':fixtures['auto-magazine-reload'],'matching':fixtures['element-matrix-2-2-False'],'many-miss':fixtures['element-capacity-256-True'],'late-match':late,'rank-bullets':fixtures['element-physical-bullets-전격-4-allies_top_atk:1']}
 rows={}
 for label,c in workloads.items():
  items=[v.compile_case(c)]*32;samples={name:[] for name in paths};baseline=None
  for sample in range(4):
   for name in paths:
    raw,e=run(name,items)
    if baseline is None:baseline=raw
    if raw!=baseline:
     fail=P/'portable-build'/('element-'+label+'-'+name+'-nonmatching.bin');fail.write_bytes(raw);save('portable-element-candidate-failure',dict(passed=False,workload=label,variant=name,sample=sample,evidence=e,raw_path=str(fail)));raise RuntimeError('Workload mismatch captured; no retry')
    samples[name].append(dict(warmup=sample==0,**e));print(label,sample,name,e['transport']['gpu_seconds'],flush=True)
  medians={name:statistics.median(x['transport']['gpu_seconds'] for x in a[1:]) for name,a in samples.items()};ranges={name:[min(x['transport']['gpu_seconds'] for x in a[1:]),max(x['transport']['gpu_seconds'] for x in a[1:])] for name,a in samples.items()}
  rows[label]=dict(programs=32,median_gpu_seconds=medians,ranges=ranges,accessors_to_control_ratio=medians['accessors']/medians['control'],samples=samples)
 save('portable-element-benchmark',dict(passed=True,source_commit=SOURCE,all_2182_input_output_bytes_equal=True,production_change_adopted=False,parity=parity,workloads=rows,timing_order=barrier,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),initial_metal_finding_open=True,scope='Sequential warmup plus3 samples per variant,32 programs per workload on Apple M5. Initial unlocalized raw mismatch remains documented. No CUDA-speed/full-roster/physical-peak-memory claim; desktop GPU activity not excluded.'))
if __name__=='__main__':main()
