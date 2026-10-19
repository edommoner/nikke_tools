"""Measure an isolated name prefilter after all correctness/transfer gates end."""
import hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ba890da'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
 folder=P/'portable-build'/('stack-operators-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as a:a.extractall(folder,filter='data')
 if variant=='prefilter2':
  p=folder/'gpu/stack_runtime.slang';s=p.read_text();needle='''        if(s.alive[slot]==0) continue;
        Definition carrier=readDefinition(s.inputBase,definition);''';assert s.count(needle)==1
  s=s.replace(needle,'''        if(s.alive[slot]==0) continue;
        // Pure immutable name rejection before loading unrelated fields/members.
        if((own || !maximum && d.targetName>=0) && definition_name(s.inputBase,definition)!=uint(d.targetName)) continue;
        Definition carrier=readDefinition(s.inputBase,definition);''');s=s.replace('if(carrier.name!=uint(d.targetName) || (members&(1U<<d.owner))==0)','if((members&(1U<<d.owner))==0)')
  s=s.replace('if(d.targetName>=0) { if(carrier.name!=uint(d.targetName)) continue;floor=0; }','if(d.targetName>=0) { floor=0; }');p.write_text(s)
 source=folder/(variant+'_event_runtime.slang');source.write_text('#include "gpu/event_runtime.slang"\n');return source.relative_to(R).as_posix()
def main():
 order=load('portable-stack-operators-timing-order');g=load('portable-stack-operators-global-gates');assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes'] and g['passed'] and g['complete']
 production=source_hashes('gpu/event_runtime.slang');paths={v:prepare(v) for v in ('control','prefilter2')}
 spec=importlib.util.spec_from_file_location('stack_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 import portable_runtime
 original=portable_runtime.execute;parity={}
 def compare(source,entry,packed,iw,ow,backend):
  assert source=='gpu/event_runtime.slang' and backend=='metal' and not parity
  outputs=[]
  for variant in paths:
   raw,e=execute(paths[variant],entry,packed,iw,ow,backend);outputs.append(raw);parity[variant]=e
  assert outputs[0]==outputs[1],'Every output word, including negative inputs and unused tails, must agree'
  save('portable-stack-operators-v2-candidate-parity',dict(passed=True,source_commit=SOURCE,inputs=1528,all_output_bytes_equal=True,parity=parity))
  return outputs[0],parity['control']
 portable_runtime.execute=compare
 # The verifier emits its regular report at the end. Keep its fixed-production
 # report bytes intact; this comparison uses archived copies, never new inputs.
 report=P/'portable-combat-metal.json';saved=report.read_bytes()
 try:
  sys.argv=[sys.argv[0],'--backend','metal'];v.main()
 finally:report.write_bytes(saved);portable_runtime.execute=original
 workloads={}
 def buff(name):return dict(name=name,source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=-1,max_stack=31,trigger=dict(timing=['battle_start'],condition=[]))
 for name,same in [('32-distinct-names',False),('32-matching-residents',True)]:
  effects=[buff('seed' if same else 'seed-'+str(i)) for i in range(32)]
  if same:
   for i,e in enumerate(effects):e['source']='스킬'+str(i%3+1);e['max_stack']=31+i
  operation=dict(name='operation',source='스킬1',type='instant',stat='buff_stack_add',fixed_value=1,target='self',target_effect='seed' if same else 'seed-0',trigger=dict(timing=['on_attack'],condition=[]))
  effects.append(operation)
  program=v.compile_case(dict(name=name,effects=effects,script=[[0,0,0,0,0,-1,0,0]]+[[i/100,0,7,0,0,-1,0,0] for i in range(1,64)]))
  packed=pack_programs([program]*64);samples={k:[] for k in paths};expected=None
  for sample in range(4):
   for variant in paths:
    raw,e=execute(paths[variant],'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
    if expected is None:expected=raw
    assert raw==expected and all(struct.unpack_from('<I',raw,i*L['OUTPUT_WORDS']*4)[0]==0 for i in range(64))
    active=sum(struct.unpack_from('<I',raw,(L['CARRIER_STATE_BASE']+i*L['CARRIER_WORDS']+4)*4)[0]&1 for i in range(L['CARRIERS']));assert active==32,(name,active)
    samples[variant].append(dict(warmup=sample==0,**e));print(name,sample,variant,e['transport']['gpu_seconds'],flush=True)
  medians={k:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for k,values in samples.items()}
  ranges={k:[min(x['transport']['gpu_seconds'] for x in values[1:]),max(x['transport']['gpu_seconds'] for x in values[1:])] for k,values in samples.items()}
  workloads[name]=dict(median_gpu_seconds=medians,prefilter_to_control_ratio=medians['prefilter2']/medians['control'],ranges=ranges,samples=samples)
 assert production==source_hashes('gpu/event_runtime.slang')
 save('portable-stack-operators-v2-benchmark',dict(passed=True,production_change_adopted=False,source_commit=SOURCE,production_source_sha256=production,all_positive_and_negative_output_words_equal=True,inputs=1528,parity=parity,workloads=workloads,timing_order=order,scope='Archived pure immutable name prefilter; sequential warmup plus three samples, 64 programs times 63 mutation events plus initial activation. No roster-wide speed or peak-memory claim. Desktop GPU activity not excluded.'))
if __name__=='__main__':main()
