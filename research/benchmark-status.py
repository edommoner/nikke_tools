"""Measure touched-name scratch clearing only after verification/transfer end."""
import hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='8c1735b'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
 folder=P/'portable-build'/('status-clear-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
 if variant=='touched':
  p=folder/'gpu/status_runtime.slang';text=p.read_text();needle='''void clearImmunityScratch(inout Runtime s)
{ for(uint word=0;word<P_DEFINITIONS*4;word++) results[s.resourceOutput+P_IMMUNITY_SCRATCH_BASE+word]=0; }''';assert text.count(needle)==1
  replacement='''void clearImmunityScratch(inout Runtime s,uint count)
{
    uint scratch=s.resourceOutput+P_IMMUNITY_SCRATCH_BASE;
    if(count<=64)
    {
        for(uint group=0;group<count;group++)
        {
            uint name=results[scratch+P_DEFINITIONS*3+group];
            results[scratch+name*2]=0;results[scratch+name*2+1]=0;
            results[scratch+P_DEFINITIONS*2+name]=0;results[scratch+P_DEFINITIONS*3+group]=0;
        }
    }
    else for(uint word=0;word<P_DEFINITIONS*4;word++) results[scratch+word]=0;
}'''
  text=text.replace(needle,replacement).replace('clearImmunityScratch(s);return blocked;','clearImmunityScratch(s,count);return blocked;');p.write_text(text)
 source=folder/(variant+'_status_event_runtime.slang');source.write_text('#include "gpu/event_runtime.slang"\n');return source.relative_to(R).as_posix()
def workloads(v):
 rows={}
 for pools,batch in ((1,64),(32,32),(255,4)):
  effects=[dict(name='pool-'+str(i),source='스킬1',type='buff',stat='debuff_immune_count',fixed_value=1,target='all_allies',duration=-1,max_stack=1,trigger=dict(timing=['event:full_reload'],condition=[])) for i in range(pools)]
  effects.append(dict(name='harm',source='스킬1',type='buff',stat='atk_pct',fixed_value=-1,target='all_allies',duration=-1,max_stack=1000,polarity='harmful',trigger=dict(timing=['on_attack'],condition=[])))
  case=dict(name='charge-pools-'+str(pools),effects=effects,script=[[0,0,19,0,0,-1,0,0]]+[[i/100,0,7,0,0,-1,0,0] for i in range(1,64)])
  program=v.compile_case(case);rows[str(pools)]=dict(pools=pools,programs=batch,packed=pack_programs([program]*batch))
 return rows

def main():
 order=load('portable-status-timing-order');gates=load('portable-status-global-gates');assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes'] and gates['passed'] and gates['complete']
 production=source_hashes('gpu/event_runtime.slang');current=load('portable-combat-metal')
 s=importlib.util.spec_from_file_location('status_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 authored=workloads(v) # Preflight every timing input before any GPU dispatch.
 paths={variant:prepare(variant) for variant in ('control','touched')}
 import portable_runtime
 original=portable_runtime.execute;parity={}
 def compare(source,entry,packed,iw,ow,backend):
  assert source=='gpu/event_runtime.slang' and backend=='metal' and not parity
  outputs=[]
  for variant in paths:
   raw,e=execute(paths[variant],entry,packed,iw,ow,backend);outputs.append(raw);parity[variant]=e
  assert outputs[0]==outputs[1] and parity['control']['output_sha256']==current['output_sha256']
  save('portable-status-candidate-parity',dict(passed=True,inputs=1625,all_output_bytes_equal=True,source_commit=SOURCE,parity=parity))
  return outputs[0],parity['control']
 report=P/'portable-combat-metal.json';saved=report.read_bytes();portable_runtime.execute=compare
 try:sys.argv=[sys.argv[0],'--backend','metal'];v.main()
 finally:report.write_bytes(saved);portable_runtime.execute=original
 rows={}
 for name,work in authored.items():
  samples={variant:[] for variant in paths};expected=None
  for sample in range(4):
   for variant in paths:
    raw,e=execute(paths[variant],'portableEvents',work['packed'],L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
    if expected is None:expected=raw
    assert raw==expected
    for i in range(work['programs']):
     offset=i*L['OUTPUT_WORDS'];assert struct.unpack_from('<I',raw,offset*4)[0]==0
     active=sum(struct.unpack_from('<I',raw,(offset+L['CARRIER_STATE_BASE']+j*L['CARRIER_WORDS']+4)*4)[0]&1 for j in range(L['CARRIERS']))
     assert active==work['pools']+int(work['pools']<63),(name,active)
    samples[variant].append(dict(warmup=sample==0,**e));print(name,sample,variant,e['transport']['gpu_seconds'],flush=True)
  medians={variant:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for variant,values in samples.items()}
  ranges={variant:[min(x['transport']['gpu_seconds'] for x in values[1:]),max(x['transport']['gpu_seconds'] for x in values[1:])] for variant,values in samples.items()}
  rows[name]=dict(programs=work['programs'],pools=work['pools'],mutation_events=63,median_gpu_seconds=medians,touched_to_control_ratio=medians['touched']/medians['control'],ranges=ranges,samples=samples)
 assert production==source_hashes('gpu/event_runtime.slang')
 save('portable-status-benchmark',dict(passed=True,production_change_adopted=False,source_commit=SOURCE,production_source_sha256=production,all_positive_and_negative_output_words_equal=True,inputs=1625,parity=parity,workloads=rows,timing_order=order,scope='One activation plus 63 all-ally harmful applications, 1/32/255 immunity pools, batches64/32/4. Sequential warmup plus three samples. Not a full roster speed or peak-memory claim; desktop GPU activity not excluded.'))
if __name__=='__main__':main()
