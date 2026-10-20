"""Compare reuse of hit-count binary64 conversion after all current gates/transfer terminate.

Initial unlocalized Metal finding stays recorded. Production is unchanged by this tool. Candidate reuses the binary64 conversion of hit count; numerical operation order is unchanged. Every candidate output is
compared byte-for-byte/hash with its control; a mismatch is captured and stops.
"""
import array,copy,hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='20e213bf28544a3ad2709fdc852d239eed108b5e'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as runtime
from portable_specs import ABI,LIMITS as L
class Captured(BaseException):pass
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
 folder=P/'portable-build'/('burst-charge-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
 if variant=='candidate':
  path=folder/'gpu/burst_runtime.slang';source=path.read_text()
  old='uint64_t gain=f64Mul(f64Mul(coefficient,f64FromI64(hits)),multiplier);'
  assert source.count(old)==1 and source.count('f64FromI64(hits)')==2
  source=source.replace(old,'uint64_t hitCount=f64FromI64(hits);\n    uint64_t gain=f64Mul(f64Mul(coefficient,hitCount),multiplier);')
  source=source.replace('f64Mul(f64FromI64(hits),readStat','f64Mul(hitCount,readStat')
  path.write_text(source)
 wrapper=folder/('burst_charge_'+variant+'_runtime.slang');wrapper.write_text('#include "gpu/event_runtime.slang"\n');return wrapper.relative_to(R).as_posix()
def save_input(path,items):
 with path.open('wb') as stream:
  stream.write(struct.pack('<I',len(items)))
  for words,_ in items:
   block=array.array('I',words)
   if sys.byteorder!='little':block.byteswap()
   stream.write(block.tobytes())
def file_sha(path):
 digest=hashlib.sha256()
 with path.open('rb') as stream:
  while chunk:=stream.read(8*1024*1024):digest.update(chunk)
 return digest.hexdigest()
def main():
 assert ABI==0x50455670
 barrier=load('portable-burst-charge-timing-order');broad=load('portable-burst-charge-broad-validation');current=load('portable-combat-metal')
 assert barrier['passed'] and barrier['windows_execution_and_transfer_terminal'] and not barrier['verification_processes']
 assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit']==SOURCE and broad['mac_gates']==41 and current['passed']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 spec=importlib.util.spec_from_file_location('burst_charge_benchmark_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 programs=[]
 def collect(p,**kwargs):programs.extend(p);raise Captured()
 report=P/'portable-combat-metal.json';saved=report.read_bytes();oldargv=sys.argv;sys.argv=[sys.argv[0],'--backend','metal'];v.run_programs=collect
 try:
  try:v.main()
  except Captured:pass
 finally:report.write_bytes(saved);sys.argv=oldargv
 assert len(programs)==3331
 hp_current=load('portable-health-runtime-metal')
 hp_cases=json.loads((R/'tests/fixtures/portable-health-runtime.json').read_text())['cases']
 fixtures={c['name']:c for c in v.fixtures()}
 charge=json.loads((R/'tests/fixtures/portable-burst-charge-speed.json').read_text())['cases']
 skills=json.loads((R/'tests/fixtures/portable-burst-charge-skills.json').read_text())['cases']
 workloads={'ordinary':fixtures['auto-magazine-reload'],
            'charge-first':charge[0], 'charge-last':charge[-1],
            'mode-callback':next(c for c in skills if c['burst_charge_skill_context']['scenario']=='mode-skill'),
            'conditional-hp':next(c for c in hp_cases if c['name']=='conditional-hp-0-hp_caster_based_pct-all_allies')}
 save('portable-burst-charge-benchmark-plan',dict(source_commit=SOURCE,workloads={k:c['name'] for k,c in workloads.items()},
      adoption_rule='At least one feature workload median improves by2% with disjoint ranges; no workload regresses by2% with disjoint ranges. Otherwise reject.',
      samples_per_variant=3,warmups_per_variant=1,alternating_order=True,programs_per_workload=1024))

 paths={name:prepare(name) for name in ('control','candidate')};one,many=runtime.execute,runtime.execute_batches
 def run(name,items):
  def single(source,*args,**kwargs):
   assert source=='gpu/event_runtime.slang';return one(paths[name],*args,**kwargs)
  def sequence(source,*args,**kwargs):
   assert source=='gpu/event_runtime.slang';return many(paths[name],*args,**kwargs)
  runtime.execute=single;runtime.execute_batches=sequence
  try:return runtime.dispatch_programs(items,backend='metal')
  finally:runtime.execute=one;runtime.execute_batches=many
 hp_programs=[v.compile_case(c) for c in hp_cases];assert len(hp_programs)==20
 parity={}
 for name in paths:
  folder=P/'portable-build'/('burst-charge-full-'+name);folder.mkdir(parents=True,exist_ok=False)
  save_input(folder/'input.bin',programs)
  assert file_sha(folder/'input.bin')==current['input_sha256']
  raw,e=run(name,programs)
  (folder/'readback.bin').write_bytes(raw)
  (folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
  if e['input_sha256']!=current['input_sha256'] or e['output_sha256']!=current['output_sha256']:
   fail=P/'portable-build'/('burst-charge-'+name+'-nonmatching.bin');fail.write_bytes(raw);save('portable-burst-charge-candidate-failure',dict(passed=False,variant=name,evidence=e,raw_path=str(fail)));raise RuntimeError('Candidate/control output mismatch captured; no retry')
  parity[name]=e;del raw
  save_input(folder/'health-input.bin',hp_programs)
  assert file_sha(folder/'health-input.bin')==hp_current['input_sha256']
  hp_raw,hp_e=run(name,hp_programs)
  (folder/'health-readback.bin').write_bytes(hp_raw)
  (folder/'health-evidence.json').write_text(json.dumps(hp_e,indent=2)+'\n')
  if hp_e['input_sha256']!=hp_current['input_sha256'] or hp_e['output_sha256']!=hp_current['output_sha256']:
   save('portable-burst-charge-candidate-failure',dict(passed=False,variant=name,health_runtime=True,evidence=hp_e,captured=str(folder)));raise RuntimeError('HP candidate/control mismatch captured;no retry')
  parity[name]['additional_health_runtime']=hp_e;del hp_raw
 save('portable-burst-charge-candidate-parity',dict(passed=True,source_commit=SOURCE,programs=3331,additional_health_cases=20,all_additional_health_input_output_bytes_equal=True,all_input_and_output_bytes_equal=True,parity=parity))
 rows={}
 for label,c in workloads.items():
  items=[v.compile_case(c)]*1024;samples={name:[] for name in paths};baseline=None
  for sample in range(4):
   for name in (list(paths) if sample%2==0 else list(reversed(paths))):
    raw,e=run(name,items)
    if baseline is None:baseline=raw
    if raw!=baseline:
     fail=P/'portable-build'/('burst-charge-'+label+'-'+name+'-nonmatching.bin');fail.write_bytes(raw);fail.with_suffix('.baseline.bin').write_bytes(baseline);save_input(fail.with_suffix('.input.bin'),items);save('portable-burst-charge-candidate-failure',dict(passed=False,workload=label,variant=name,sample=sample,evidence=e,raw_path=str(fail)));raise RuntimeError('Workload mismatch captured; no retry')
    samples[name].append(dict(warmup=sample==0,**e));print(label,sample,name,e['transport']['gpu_seconds'],flush=True)
  medians={name:statistics.median(x['transport']['gpu_seconds'] for x in a[1:]) for name,a in samples.items()};ranges={name:[min(x['transport']['gpu_seconds'] for x in a[1:]),max(x['transport']['gpu_seconds'] for x in a[1:])] for name,a in samples.items()}
  rows[label]=dict(programs=1024,median_gpu_seconds=medians,ranges=ranges,candidate_to_control_ratio=medians['candidate']/medians['control'],samples=samples)
 save('portable-burst-charge-benchmark',dict(passed=True,source_commit=SOURCE,all_3331_input_output_bytes_equal=True,all_additional20_health_input_output_bytes_equal=True,production_change_adopted=False,parity=parity,workloads=rows,timing_order=barrier,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),initial_metal_finding_open=True,scope='Alternating variant order,warmup plus3 samples per variant,1024 programs per workload on Apple M5. Initial unlocalized raw mismatch remains documented. No CUDA-speed/full-roster/physical-peak-memory claim; desktop GPU activity not excluded.'))
if __name__=='__main__':main()
