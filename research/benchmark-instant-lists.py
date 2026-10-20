"""Historical60a10b6 experiment; guarded by complete Mac/CUDA receipts.
The candidate keeps32-bit Frame.value and spills only ordered delivery high bits
into32 output scratch words. It does not add Runtime arrays or change outputs.
"""
import hashlib,importlib.util,io,json,re,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='60a10b6'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_specs import ABI,LIMITS as L
from portable_runtime import pack_programs
from portable_backend import execute,source_hashes
load=lambda n:json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def compact_text(text):
 old=subprocess.check_output(['git','show','b8ae1c7:gpu/event_runtime.slang'],cwd=R,text=True)
 pattern=r'struct Frame\s*\{.*?\n\};';before=re.search(pattern,text,re.S).group();after=re.search(pattern,old,re.S).group();assert before!=after;text=text.replace(before,after)
 helper='''bool wideFrameOrder(uint mode) { return mode==5 || mode==6 || mode==11 || mode==12 || mode==13 || mode==24; }
uint64_t readFrameValue(inout Runtime s,uint mode,uint low,int depth)
{
    if(!wideFrameOrder(mode) || commands[s.inputBase+P_RECIPIENT_META_BASE]==0) return low;
    return uint64_t(low)|(uint64_t(results[s.resourceOutput+P_FRAME_VALUE_HIGH_BASE+uint(depth)])<<32);
}
void writeFrameValue(inout Runtime s,inout Frame frames[32],int depth,uint64_t value)
{
    frames[depth].value=uint(value);
    if(commands[s.inputBase+P_RECIPIENT_META_BASE]!=0 && wideFrameOrder(frames[depth].mode)) results[s.resourceOutput+P_FRAME_VALUE_HIGH_BASE+uint(depth)]=uint(value>>32);
}
'''
 at=text.rfind('[noinline]',0,text.index('void pushFrame('));assert at>=0;text=text[:at]+helper+text[at:]
 needle='frames[depth] = f; s.maxDepth';assert text.count(needle)==1
 text=text.replace(needle,'frames[depth] = f; if(commands[s.inputBase+P_RECIPIENT_META_BASE]!=0 && wideFrameOrder(mode)) results[s.resourceOutput+P_FRAME_VALUE_HIGH_BASE+uint(depth)]=uint(value>>32); s.maxDepth')
 # Recover each frame value once; numeric-only modes never read the scratch plane.
 for begin,end in (('void advanceBuffActivation(', 'void dispatch('),('void dispatch(', 'void timerPass(')):
  a,b=text.index(begin),text.index(end);chunk=text[a:b];assert chunk.count('Frame f = frames[depth];')==1
  chunk=chunk.replace('f.value','savedValue').replace('Frame f = frames[depth];','Frame f = frames[depth]; uint64_t savedValue=readFrameValue(s,f.mode,f.value,depth);')
  text=text[:a]+chunk+text[b:]
 text,count=re.subn(r'frames\[depth\]\.value\s*=\s*recipientOrder;',r'writeFrameValue(s,frames,depth,recipientOrder);',text);assert count==3,count
 needle='    results[output] = s.error; results[output+1] = queries;';assert text.count(needle)==1
 text=text.replace(needle,'    if(commands[input+P_RECIPIENT_META_BASE]!=0) for(uint i=0;i<32;i++) results[output+P_FRAME_VALUE_HIGH_BASE+i]=0;\n'+needle)
 return text

def prepare(variant):
 folder=P/'portable-build'/('instant-lists-frame-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
 if variant=='compact':
  p=folder/'gpu/event_runtime.slang';p.write_text(compact_text(p.read_text()))
  p=folder/'gpu/portable_schema.slang';s=p.read_text();assert s.count('PORTABLE_ABI = 1346721383U')==1;s=s.replace('PORTABLE_ABI = 1346721383U','PORTABLE_ABI = 1346721384U')
  needle='static const uint P_RECIPIENT_ORDER_BASE = 155648U;';assert s.count(needle)==1;s=s.replace(needle,needle+'\nstatic const uint P_FRAME_VALUE_HIGH_BASE = 156672U;');p.write_text(s)
 source=folder/(variant+'_split_runtime.slang');source.write_text('#include "gpu/event_runtime.slang"\n');return source.relative_to(R).as_posix()
def compact_input(packed):
 data=bytearray(packed)
 for program in range(struct.unpack_from('<I',data)[0]):
  at=4+program*L['INPUT_WORDS']*4;struct.pack_into('<I',data,at,struct.unpack_from('<I',data,at)[0]^ABI^0x50455668)
 return bytes(data)
def workloads(v):
 rows={}
 def effect(name,stat,target='self',**kw):
  e=dict(name=name,source='스킬1',type='buff',stat=stat,target=target,duration=-1,max_stack=1,trigger=dict(timing=['on_attack'],condition=[]));e.update(kw);return e
 for name,targets,batch in (('ordinary',None,64),('one-group','all_allies',64),('composite-three',['self','allies_lowest_hp_excl:2'],64),('duplicate-audience-21',['self']*21,16),('instant-heal-21',['self']*21,16)):
  effects=[effect('group','received_dmg_split_even',targets)] if targets else [effect('ordinary','atk_pct',fixed_value=10)]
  script=[[0,0,7,0,0,-1,0,0]]+[[i/100,31,0,0,1,-1,1,100] for i in range(1,33)]
  if name=='duplicate-audience-21':
   effects[0].update(duration=.001,event_scope='recipients')
   effects.append(effect('observer','atk_pct',fixed_value=10,max_stack=100,trigger=dict(timing=['event:group'],condition=[])))
   script=sum(([[i,0,7,0,0,-1,0,0],[i+.01,31,0,0,1,-1,1,100]] for i in range(30)),[])
  if name=='instant-heal-21':
   effects=[dict(name='heal',source='스킬1',type='instant',stat='heal_hp_pct',fixed_value=1,target=['self']*21,trigger=dict(timing=['on_attack'],condition=[]))]
   script=[[i/100,0,7,0,0,-1,0,0] for i in range(32)]
  case=dict(name=name,effects=effects,script=script,environment=dict(allies=[dict(base_hp=1000000) for _ in range(5)]))
  packed=pack_programs([v.compile_case(case)]*batch);rows[name]=dict(programs=batch,control=packed,compact=compact_input(packed))
 return rows

def main():
 assert load('portable-instant-list-normal-fixed-metal')['full_instant_list_supported'],'Resolve ordered instant delivery before measuring efficiency'
 assert ABI==0x50455667,'Run with the historical60a10b6 app/scripts input compiler'
 order=load('portable-instant-lists-timing-order');pre=load('portable-instant-lists-pre-optimization');g=load('portable-instant-lists-global-gates')
 assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes'] and pre['passed'] and g['passed'] and g['complete']
 production=source_hashes('gpu/event_runtime.slang');assert production==pre['source_sha256'];current=load('portable-combat-metal');assert current['output_sha256']==pre['output_sha256']
 s=importlib.util.spec_from_file_location('benchmark_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 authored=workloads(v);paths={name:prepare(name) for name in ('control','compact')}
 import portable_runtime
 original=portable_runtime.execute;parity={}
 def compare(source,entry,packed,iw,ow,backend):
  assert source=='gpu/event_runtime.slang' and backend=='metal' and not parity
  outputs=[]
  for variant in paths:
   raw,e=execute(paths[variant],entry,packed if variant=='control' else compact_input(packed),iw,ow,backend);outputs.append(raw);parity[variant]=e
  assert outputs[0]==outputs[1] and parity['control']['output_sha256']==current['output_sha256']
  save('portable-instant-lists-candidate-parity',dict(passed=True,inputs=1824,all_output_bytes_equal=True,source_commit=SOURCE,input_changes='ABI XOR15 maps67 to68; every other byte remains unchanged and invalid ABI values remain invalid.',parity=parity))
  return outputs[0],parity['control']
 saved=(P/'portable-combat-metal.json').read_bytes();portable_runtime.execute=compare
 try:sys.argv=[sys.argv[0],'--backend','metal'];v.main()
 finally:(P/'portable-combat-metal.json').write_bytes(saved);portable_runtime.execute=original
 rows={}
 for name,work in authored.items():
  samples={variant:[] for variant in paths};expected=None
  for sample in range(4):
   for variant in paths:
    raw,e=execute(paths[variant],'portableEvents',work[variant],L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
    if expected is None:expected=raw
    assert raw==expected
    for i in range(work['programs']):assert struct.unpack_from('<I',raw,i*L['OUTPUT_WORDS']*4)[0]==0
    samples[variant].append(dict(warmup=sample==0,**e));print(name,sample,variant,e['transport']['gpu_seconds'],flush=True)
  medians={k:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for k,values in samples.items()}
  ranges={k:[min(x['transport']['gpu_seconds'] for x in values[1:]),max(x['transport']['gpu_seconds'] for x in values[1:])] for k,values in samples.items()}
  rows[name]=dict(programs=work['programs'],median_gpu_seconds=medians,compact_to_control_ratio=medians['compact']/medians['control'],ranges=ranges,samples=samples)
 assert production==source_hashes('gpu/event_runtime.slang')
 save('portable-instant-lists-benchmark',dict(passed=True,production_change_adopted=False,source_commit=SOURCE,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),production_source_sha256=production,inputs=1824,all_positive_and_negative_output_words_equal=True,parity=parity,workloads=rows,timing_order=order,scope='Sequential warmup plus3 samples per variant; ordinary hits, one group, composite-three group 21-recipient broadcasts and ordered instant healing. No full-roster/CUDA-speed/peak-memory claim; desktop GPU activity is not excluded.'))
if __name__=='__main__':main()
