"""Evaluate checked integer specialization only after verification/transfer end."""
import array,hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L
SOURCE='8516256'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant,entry):
 folder=P/'portable-build'/('stack-increment-'+variant);folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as a:a.extractall(folder,filter='data')
 source=folder/(variant+'_'+entry+'.slang')
 define='#define PORTABLE_STACK_INCREMENT_INTEGER_CANDIDATE\n' if variant=='integer' else ''
 if entry=='stress':
  text='''#include "gpu/binary64.slang"
#include "gpu/stack_numeric.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")][numthreads(1,1,1)]
void stress(uint3 thread:SV_DispatchThreadID) {
 uint id=thread.x;if(id>=commands[0]) return;
 uint input=1+id*4,current=commands[input],cap=commands[input+1],iterations=commands[input+2],status=0;
 for(uint i=0;i<iterations;i++) { current=checkedStackIncrement(current,cap,status);if(status!=0) break; }
 results[id*2]=current;results[id*2+1]=status;
}
'''
 else:text='#include "gpu/'+entry+'.slang"\n'
 source.write_text(define+text);return source.relative_to(R).as_posix()
def main():
 order=load('portable-stack-foundation-timing-order');gates=load('portable-stack-foundation-global-gates')
 assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
 assert gates['passed'] and gates['complete'] and len(gates['gates'])==22
 original=source_hashes('gpu/event_runtime.slang')
 spec=importlib.util.spec_from_file_location('stack_cases',P/'verify-stack-foundation.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
 spec=importlib.util.spec_from_file_location('stack_main_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 numeric=struct.pack('<I',len(n.numeric_cases()))+b''.join(struct.pack('<dd4I',*c) for c in n.numeric_cases())
 programs=[v.compile_case(c) for c in v.fixtures()]
 rows={}
 for variant in ('general','integer'):
  rows[variant]={}
  for name,entry,packed,iw,ow in [('event_runtime','portableEvents',pack_programs(programs),L['INPUT_WORDS'],L['OUTPUT_WORDS']),('stack_numeric_probe','stackNumericProbe',numeric,8,2)]:
   raw,evidence=execute(prepare(variant,name),entry,packed,iw,ow,'metal')
   rows[variant][name]=evidence
   if variant=='general':rows['expected_'+name]=hashlib.sha256(raw).hexdigest()
   assert hashlib.sha256(raw).hexdigest()==rows['expected_'+name]
  print('all-word parity',variant,flush=True)
 workloads={}
 for name,cap in [('finite-cap',31),('unlimited',0xffffffff)]:
  packed=struct.pack('<I',64)+b''.join(struct.pack('<4I',i,cap,16384,0) for i in range(64));samples={k:[] for k in ('general','integer')};expected=None
  for sample in range(4):
   for variant in samples:
    raw,e=execute(prepare(variant,'stress'),'stress',packed,4,2,'metal')
    if expected is None:expected=raw
    assert raw==expected and all(struct.unpack_from('<2I',raw,i*8)[1]==0 for i in range(64))
    samples[variant].append(dict(warmup=sample==0,**e));print(name,sample,variant,e['transport']['gpu_seconds'],flush=True)
  medians={k:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for k,values in samples.items()}
  ranges={k:[min(x['transport']['gpu_seconds'] for x in values[1:]),max(x['transport']['gpu_seconds'] for x in values[1:])] for k,values in samples.items()}
  workloads[name]=dict(median_gpu_seconds=medians,integer_to_general_ratio=medians['integer']/medians['general'],ranges=ranges,samples=samples)
 effects=[dict(name='stack-'+str(i),source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=-1,max_stack=31,trigger=dict(timing=['battle_start'],condition=[])) for i in range(32)]
 program=v.compile_case(dict(name='increment-battle-stress',effects=effects,script=[[i/100,0,0,0,0,-1,0,0] for i in range(64)]))
 packed=pack_programs([program]*64);samples={k:[] for k in ('general','integer')};expected=None
 for sample in range(4):
  for variant in samples:
   raw,e=execute(prepare(variant,'event_runtime'),'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
   if expected is None:expected=raw
   assert raw==expected and all(struct.unpack_from('<I',raw,i*L['OUTPUT_WORDS']*4)[0]==0 for i in range(64))
   samples[variant].append(dict(warmup=sample==0,**e));print('battle-32-buffs',sample,variant,e['transport']['gpu_seconds'],flush=True)
 medians={k:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for k,values in samples.items()}
 ranges={k:[min(x['transport']['gpu_seconds'] for x in values[1:]),max(x['transport']['gpu_seconds'] for x in values[1:])] for k,values in samples.items()}
 workloads['battle-32-buffs']=dict(median_gpu_seconds=medians,integer_to_general_ratio=medians['integer']/medians['general'],ranges=ranges,samples=samples)
 assert original==source_hashes('gpu/event_runtime.slang')
 save('portable-stack-increment-benchmark',dict(passed=True,production_change_adopted=False,source_commit=SOURCE,production_source_sha256=original,all_positive_output_words_equal=True,positive_inputs=1149,numeric_inputs=len(n.numeric_cases()),parity=rows,workloads=workloads,timing_order=order,scope='Two component stress workloads: 64 programs times 16384 increments, plus production event executor with 32 buffs times 64 events times 64 programs. Sequential warmup plus 3 samples. Not roster battle speed or memory. Desktop GPU activity not excluded.'))
if __name__=='__main__':main()
