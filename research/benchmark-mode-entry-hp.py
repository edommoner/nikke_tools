"""Post-verification isolated HP-basis reuse; retain every input/readback before assertions."""
import array,copy,datetime,hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='39bce8aa5c9c5f29f0653e80fc69855f19ad5ad6'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as rt
from portable_specs import ABI,LIMITS as L

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
def read_input(path):
 a=array.array('I');a.frombytes(Path(path).read_bytes())
 if sys.byteorder!='little':a.byteswap()
 count=a[0];assert len(a)==1+count*L['INPUT_WORDS']
 return [(list(a[1+i*L['INPUT_WORDS']:1+(i+1)*L['INPUT_WORDS']]),{}) for i in range(count)]
def write_input(path,items):
 with path.open('wb') as f:
  f.write(struct.pack('<I',len(items)))
  for words,_ in items:
   a=array.array('I',words)
   if sys.byteorder!='little':a.byteswap()
   f.write(a.tobytes())
def prepare(folder,name):
 target=folder/name;target.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as a:a.extractall(target,filter='data')
 if name=='candidate':
  path=target/'gpu/hp_attack_runtime.slang';s=path.read_text()
  old='void collectHPAttack(inout Runtime s,uint who,uint64_t when,inout uint64_t flat)\n{'
  assert s.count(old)==1
  s=s.replace(old,old+'\n    bool hpBasisValid=false;uint64_t hpBasis=0;')
  old='uint64_t basis=family==0 ? nativeAttackMaxHP(s,who,when) : s.baseAttack[d.owner];'
  assert s.count(old)==1
  s=s.replace(old,'if(family==0 && !hpBasisValid) { hpBasis=nativeAttackMaxHP(s,who,when);hpBasisValid=true; }\n            uint64_t basis=family==0 ? hpBasis : s.baseAttack[d.owner];')
  path.write_text(s)
 wrapper=target/(name+'_runtime.slang');wrapper.write_text('#include "gpu/event_runtime.slang"\n');return wrapper.relative_to(R).as_posix()
def main():
 assert ABI==0x50455672
 audit=load('portable-mode-entry-efficiency-plan');assert audit['candidate_source_audit_completed']
 for path,digest in audit['candidate_source_audit_sha256'].items():assert sha(R/path)==digest,path
 barrier=load('portable-mode-entry-timing-order');broad=load('portable-mode-entry-broad-validation');core=load('portable-combat-metal')
 assert barrier['passed'] and not barrier['verification_processes'] and barrier['windows_execution_and_transfer_terminal']
 assert broad['passed'] and broad['mac_gates']==47 and broad['source_commit']==SOURCE and core['passed']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True)
 folder=P/'portable-build'/('hp-basis-benchmark-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 paths={name:prepare(folder,name) for name in ('control','candidate')};one,many=rt.execute,rt.execute_batches
 def run(name,items,label):
  captured=folder/label;captured.mkdir();write_input(captured/'input.bin',items)
  def single(source,*a,**kw):assert source=='gpu/event_runtime.slang';return one(paths[name],*a,**kw)
  def multiple(source,*a,**kw):assert source=='gpu/event_runtime.slang';return many(paths[name],*a,**kw)
  rt.execute=single;rt.execute_batches=multiple
  try:raw,e=rt.dispatch_programs(items,backend='metal')
  finally:rt.execute=one;rt.execute_batches=many
  (captured/'readback.bin').write_bytes(raw);(captured/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
  e['captured']=str(captured);assert e['input_sha256']==sha(captured/'input.bin') and e['output_sha256']==sha(captured/'readback.bin')
  return raw,e
 parity={}
 suites=[('core',Path(core['mode_entry_existing_parity']['replay_source'])/'input.bin',core,4070)]
 for label,report,count in [('physical','portable-hp-attack-physical-metal',80),('health','portable-health-runtime-metal',20)]:
  proof=load(report);suites.append((label,Path(proof['captured'])/'input.bin',proof,count))
 for label,path,proof,count in suites:
  items=read_input(path);assert len(items)==count;parity[label]={}
  for name in paths:
   raw,e=run(name,items,'full-'+label+'-'+name);del raw
   assert e['input_sha256']==proof['input_sha256'] and e['output_sha256']==proof['output_sha256'],(label,name,e['captured'])
   parity[label][name]=e;print('full parity',label,name,count,flush=True)
  del items
 save('portable-mode-entry-hp-cache-parity',dict(passed=True,source_commit=SOURCE,parity=parity,production_adopted=False,captured=str(folder)))
 spec=importlib.util.spec_from_file_location('hp_benchmark_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 fixtures=v.fixtures();lookup={c['name']:c for c in fixtures};hp=[c for c in fixtures if c.get('hp_attack_reference')]
 multi=copy.deepcopy(next(c for c in hp if c['name']=='hp-attack-order-0-hp-positive,hp-negative,caster'))
 workloads={'ordinary':lookup['auto-magazine-reload'],'hp-single':hp[0],'hp-multiple':multi,'hp-fresh-rank':lookup['hp-attack-fresh-rank-0--1-True'],
  'mode-entry':next(c for c in fixtures if c.get('mode_entry_reference') and c['mode_entry_context']['scenario']=='reenter'),
  'pending-reference':next(c for c in fixtures if c.get('pending_scale_reference') and c['name']=='pending-reference-0-after-cast-change-33.333')}
 physical=read_input(suites[1][1]);workload_items={k:v.compile_case(c) for k,c in workloads.items()};workload_items['hp-sg-physical']=physical[2];del physical
 rows={}
 for label,program in workload_items.items():
  items=[program]*1024;samples={n:[] for n in paths};baseline=None
  for sample in range(4):
   for name in (list(paths) if sample%2==0 else list(reversed(paths))):
    raw,e=run(name,items,label+'-'+str(sample)+'-'+name)
    if baseline is None:baseline=raw
    assert raw==baseline,('Workload difference retained; no retry',e['captured'])
    samples[name].append(dict(warmup=sample==0,**e));print(label,sample,name,e['transport']['gpu_seconds'],flush=True)
  med={n:statistics.median(e['transport']['gpu_seconds'] for e in values[1:]) for n,values in samples.items()}
  ranges={n:[min(e['transport']['gpu_seconds'] for e in values[1:]),max(e['transport']['gpu_seconds'] for e in values[1:])] for n,values in samples.items()}
  ratio=med['candidate']/med['control'];rows[label]=dict(programs=1024,samples=samples,median_gpu_seconds=med,ranges=ranges,candidate_to_control_ratio=ratio,improves=ratio<=.98 and ranges['candidate'][1]<ranges['control'][0],regresses=ratio>=1.02 and ranges['candidate'][0]>ranges['control'][1])
  save('portable-mode-entry-hp-cache-benchmark-progress',dict(complete=False,source_commit=SOURCE,workloads=rows,captured=str(folder)))
 criteria=any(x['improves'] for k,x in rows.items() if k!='ordinary') and not any(x['regresses'] for x in rows.values())
 save('portable-mode-entry-hp-cache-benchmark',dict(passed=True,source_commit=SOURCE,criteria_met=criteria,production_adopted=False,workloads=rows,parity=parity,timing_order=barrier,captured=str(folder),tool_sha256=sha(__file__),scope='Apple M5 isolated local workloads, alternating order,warmup+3 samples. No CUDA speed/full-roster speed/physical memory claim. No production adoption before fresh verification.'))
 print('Efficiency criteria met:',criteria,'production unchanged',flush=True)
if __name__=='__main__':main()
