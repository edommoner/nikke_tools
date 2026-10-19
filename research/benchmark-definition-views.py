"""Bounded sequential GPU input-view controls; never replays a CPU battle.
Run only after global gates and the fixed-source Windows transfer are terminal.
"""
import argparse,array,copy,hashlib,importlib.util,json,re,shutil,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs,decode
from portable_specs import LIMITS as L
P=ROOT/'research'
def load(name):return json.loads((P/(name+'.json')).read_text())
def save(name,value):(P/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def require_terminal():
 gates=load('portable-removal-global-gates');order=load('portable-removal-timing-order')
 assert gates['passed'] and gates['complete'] and order['passed']
 assert order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
 return order

def prepare(variant):
 directory=P/'portable-build'/('definition-view-'+variant)
 shutil.copytree(ROOT/'gpu',directory/'gpu',dirs_exist_ok=True)
 replaced=0
 if variant=='record':
  # Make every former scalar read materialize the exact production decoder.
  # Keep the canonical scalar definitions themselves: rewriting those would recurse.
  for p in (directory/'gpu').glob('*.slang'):
   if p.name=='definition_runtime.slang' or 'probe' in p.name:continue
   text=p.read_text();start=0
   while True:
    match=re.search(r'\bdefinition_(\w+)\(',text[start:])
    if not match:break
    at=start+match.start();args=start+match.end();end=args;depth=1
    while depth:
     if text[end]=='(':depth+=1
     elif text[end]==')':depth-=1
     end+=1
    replacement='readDefinition('+text[args:end]+'.'+match[1]
    text=text[:at]+replacement+text[end:];start=at+len(replacement);replaced+=1
   p.write_text(text,newline='\n')
  assert replaced==66,replaced
 source=directory/('portable_definition_'+variant+'.slang')
 source.write_text('#include "gpu/event_runtime.slang"\n',newline='\n')
 return source.relative_to(ROOT).as_posix(),replaced

def run(source,programs):
 raw,evidence=execute(source,'portableEvents',pack_programs(programs),L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
 for i in range(len(programs)):assert int.from_bytes(raw[i*L['OUTPUT_WORDS']*4:i*L['OUTPUT_WORDS']*4+4],'little')==0
 return raw,evidence

def verifier():
 sp=importlib.util.spec_from_file_location('view_cases',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);return v

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('parity','timing'),required=True);args=parser.parse_args()
 order=require_terminal();production=source_hashes('gpu/event_runtime.slang');v=verifier()
 if args.phase=='parity':
  programs=[v.compile_case(c) for c in v.fixtures()]
  first=None;rows={}
  for variant in ('record','scalar'):
   source,replaced=prepare(variant);raw,evidence=run(source,programs)
   if first is None:first=raw
   else:assert raw==first,'Different complete GPU output buffers'
   rows[variant]=dict(replaced_sites=replaced,**evidence)
  assert production==source_hashes('gpu/event_runtime.slang')
  save('portable-definition-view-parity',dict(passed=True,scope='All 1092 positive authored inputs, every output word including queue/history padding; production negative gates remain separately verified',positive_inputs=len(programs),full_output_bytes=len(first),byte_identical_outputs=True,production_source_sha256=production,variants=rows,timing_order=order))
  print('Input view full-output parity passed',len(programs),flush=True);return
 parity=load('portable-definition-view-parity');assert parity['passed'] and parity['production_source_sha256']==production
 case=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='removal-default-global'))
 template=copy.deepcopy(case['effects'][0]);extra=L['DEFINITIONS']-len(case['effects'])
 for i in range(extra):
  e=copy.deepcopy(template);e.update(name='Filler'+str(i),fixed_value=1);case['effects'].append(e);case['owners'].append(0)
 case['name']='removal-256-definitions-input-view-stress'
 # The added independent fixed +1 all-allied states survive exact-name removal.
 for q in case['expected_queries']:q['attack_buffs']=[x+extra for x in q['attack_buffs']]
 program=v.compile_case(case);batch=32;programs=[program]*batch;rows={k:[] for k in ('record','scalar')};expected_hash=None
 for sample in range(4):
  for variant in ('record','scalar'):
   source,_=prepare(variant);raw,evidence=run(source,programs)
   words=array.array('I');words.frombytes(raw[:L['OUTPUT_WORDS']*4])
   if sys.byteorder!='little':words.byteswap()
   actual=decode(words,program[1]);v.contains(actual['queries'],case['expected_queries'])
   if expected_hash is None:expected_hash=evidence['output_sha256']
   assert evidence['output_sha256']==expected_hash
   rows[variant].append(dict(warmup=sample==0,**evidence));print('view timing',sample,variant,evidence['transport']['gpu_seconds'],flush=True)
 assert production==source_hashes('gpu/event_runtime.slang')
 medians={k:statistics.median(r['transport']['gpu_seconds'] for r in a[1:]) for k,a in rows.items()}
 save('portable-definition-view-benchmark',dict(passed=True,scope='Bounded sequential isolated 256-definition exact-name removal, 32 programs per sample; one warmup and three measured samples each; not a general speed or peak-memory claim',definitions=L['DEFINITIONS'],batch=batch,clock_source='MTLCommandBuffer GPU timestamps',all_output_hashes_equal=True,production_source_sha256=production,median_gpu_seconds=medians,scalar_to_record_ratio=medians['scalar']/medians['record'],samples=rows,timing_order=order,private_definition_nominal_bytes_removed=248*256))
 print('Input view benchmark complete',medians,flush=True)
if __name__=='__main__':main()
