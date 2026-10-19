"""Historical experiment: run with the pre-optimization a198969 app/scripts tree.
Copy this research tool and its completion receipts into that checkout first.
The baseline input compiler is intentionally not emulated by current code.
"""
import hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='dd1050c'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L,ABI

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def candidate_text(text):
 marker='bool protectionMarker(inout Runtime s,uint who,uint kind,uint64_t when)\n{'
 amp='uint64_t nextShieldAmplification(inout Runtime s,uint who,uint64_t when)\n{'
 assert text.count(marker)==text.count(amp)==text.count('        enabled=1;')==1
 return text.replace(marker,marker+'\n    if((commands[s.inputBase+P_PROTECTION_META_BASE]&(kind==4 ? 2U : 4U))==0) return false;').replace(amp,amp+'\n    if((commands[s.inputBase+P_PROTECTION_META_BASE]&8U)==0) return 0;').replace('        enabled=1;','        enabled|=1U|(kind==4 ? 2U : 0U)|(kind==7 ? 4U : 0U)|(kind==3 ? 8U : 0U);')
def prepare(variant):
 folder=P/'portable-build'/('protection-mask-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
 if variant=='mask':
  p=folder/'gpu/protection_runtime.slang';p.write_text(candidate_text(p.read_text()))
  p=folder/'gpu/portable_schema.slang';s=p.read_text();assert s.count('PORTABLE_ABI = 1346721380U')==1;p.write_text(s.replace('PORTABLE_ABI = 1346721380U','PORTABLE_ABI = 1346721381U'))
 source=folder/(variant+'_protection_runtime.slang');source.write_text('#include "gpu/event_runtime.slang"\n');return source.relative_to(R).as_posix()
def masked(packed):
 b=bytearray(packed);count=struct.unpack_from('<I',b)[0]
 for program in range(count):
  base=4+program*L['INPUT_WORDS']*4;at=base+L['PROTECTION_META_BASE']*4
  struct.pack_into('<I',b,base,struct.unpack_from('<I',b,base)[0]^1)
  if struct.unpack_from('<I',b,at)[0]!=1:continue
  n=struct.unpack_from('<I',b,base+4)[0];flags=0
  for row in range(n):
   kind=struct.unpack_from('<I',b,base+(L['PROTECTION_DEFINITION_BASE']+row)*4)[0]&255
   if kind:flags|=1|(2 if kind==4 else 4 if kind==7 else 8 if kind==3 else 0)
  struct.pack_into('<I',b,at,flags)
 return bytes(b)
def workloads(v):
 rows={}
 for name,count,batch,hits,both in (('one',1,128,32,False),('thirty-two',32,32,16,False),('all256',256,4,4,False),('markers-and-amplifier',32,32,16,True)):
  def effect(n,stat,value=None):
   e=dict(name=n,source='스킬1',type='buff',stat=stat,target='self',duration=-1,max_stack=1,trigger=dict(timing=['on_attack'],condition=[]))
   if value is not None:e['fixed_value']=value
   return e
  effects=([effect('next','next_shield_hp_pct',50)] if both else [])+[effect('shield-'+str(i),'shield_from_max_hp_pct',10) for i in range(count)]+([effect('immutable','shield_invincible')] if both else [])
  case=dict(name=name,effects=effects,script=[[0,0,7,0,0,-1,0,0]]+[[i/100,31,1,0,1,-1,1,100] for i in range(1,hits+1)],environment=dict(allies=[dict(base_hp=1000000) for _ in range(5)]))
  packed=pack_programs([v.compile_case(case)]*batch);rows[name]=dict(shields=count,programs=batch,hits=hits,markers_and_amplifier=both,control=packed,mask=masked(packed))
 return rows

def main():
 assert ABI==0x50455664,'Run this historical experiment against the pre-optimization a198969 app/scripts tree'
 order=load('portable-protection-timing-order');gates=load('portable-protection-global-gates');assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes'] and gates['passed'] and gates['complete']
 assert load('portable-protection-pre-optimization')['passed']
 production=source_hashes('gpu/event_runtime.slang');current=load('portable-combat-metal')
 s=importlib.util.spec_from_file_location('protection_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 authored=workloads(v) # Preflight every timing input before any GPU dispatch.
 paths={variant:prepare(variant) for variant in ('control','mask')}
 import portable_runtime
 original=portable_runtime.execute;parity={}
 def compare(source,entry,packed,iw,ow,backend):
  assert source=='gpu/event_runtime.slang' and backend=='metal' and not parity
  outputs=[]
  for variant in paths:
   raw,e=execute(paths[variant],entry,packed if variant=='control' else masked(packed),iw,ow,backend);outputs.append(raw);parity[variant]=e
  assert outputs[0]==outputs[1] and parity['control']['output_sha256']==current['output_sha256']
  save('portable-protection-candidate-parity',dict(passed=True,inputs=len(current['actual_statuses']),all_output_bytes_equal=True,source_commit=SOURCE,input_changes='ABI XOR1 maps valid64 to65 and preserves rejection of invalid ABIs. Protection header1 changes to a validated static type mask; bad header values are retained.',parity=parity))
  return outputs[0],parity['control']
 report=P/'portable-combat-metal.json';saved=report.read_bytes();portable_runtime.execute=compare
 try:sys.argv=[sys.argv[0],'--backend','metal'];v.main()
 finally:report.write_bytes(saved);portable_runtime.execute=original
 rows={}
 for name,work in authored.items():
  samples={variant:[] for variant in paths};expected=None
  for sample in range(4):
   for variant in paths:
    raw,e=execute(paths[variant],'portableEvents',work[variant],L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
    if expected is None:expected=raw
    assert raw==expected
    for i in range(work['programs']):
     offset=i*L['OUTPUT_WORDS'];assert struct.unpack_from('<I',raw,offset*4)[0]==0
     hits=struct.unpack_from('<I',raw,(offset+L['INCOMING_STATE_BASE']+2)*4)[0];assert hits==work['hits']
    samples[variant].append(dict(warmup=sample==0,**e));print(name,sample,variant,e['transport']['gpu_seconds'],flush=True)
  medians={variant:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for variant,values in samples.items()}
  ranges={variant:[min(x['transport']['gpu_seconds'] for x in values[1:]),max(x['transport']['gpu_seconds'] for x in values[1:])] for variant,values in samples.items()}
  rows[name]=dict(programs=work['programs'],shields=work['shields'],hits=work['hits'],markers_and_amplifier=work['markers_and_amplifier'],median_gpu_seconds=medians,mask_to_control_ratio=medians['mask']/medians['control'],ranges=ranges,samples=samples)
 assert production==source_hashes('gpu/event_runtime.slang')
 save('portable-protection-benchmark',dict(passed=True,production_change_adopted=False,source_commit=SOURCE,production_source_sha256=production,all_positive_and_negative_output_words_equal=True,inputs=len(current['actual_statuses']),parity=parity,workloads=rows,timing_order=order,scope='Sequential warmup plus3 samples per variant. Isolated1/32/256 shields and marker-present control, explicit pierce hits, no full-roster or CUDA-speed or peak-memory claim; desktop GPU activity not excluded.'))
if __name__=='__main__':main()
