import array,copy,importlib.util,json,sys
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/p) for p in ('app','research','scripts')]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,root/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
cli=module('actor_fault_cli','scripts/nikke_gpu.py');m=cli.verify_package(root)
with cli.forbid_gpu():
 adapter=cli.open_suite(m);entries,_=cli.prepare_entries(adapter,m);name,_,d=entries[62];n=adapter.native_reference(d)
 with Path('/tmp/nikke-typed-actor-metal-v1/readback.bin').open('rb') as f:f.seek(62*2032000*4);block=array.array('I');block.frombytes(f.read(2032000*4))
 reader=module('actor_fault_reader','research/verify-world-skills.py');L=reader.L
 program=d[1]['binding_source_indices'].index(1);expected=[dict(e,row=program) for e in n['skill_trace'] if e['row']==1]
 def check(b):
  actual=[e for e in reader.skill_trace(b) if e['row']==program]
  assert actual==expected,'Original current-damage recipient, count, time and amount'
 check(block);assert len(expected)==5 and all(e['recipients']==[0] for e in expected)
 allrows=reader.skill_trace(block);index=next(i for i,e in enumerate(allrows) if e['row']==program);at=L['WORLD_SKILL_TRACE_BASE']+index*48
 rejected=[]
 for label in ('logical-enemy-retarget','amount-one-ulp','landing-clock-one-ulp','source-row'):
  bad=array.array('I',block)
  if label=='logical-enemy-retarget':
   # Keep the recipient bitset and packed list internally consistent. This is
   # a valid ADD address, but contradicts the actual manual typed aim's BODY.
   bad[at+12]=2;bad[at+16]=(bad[at+16]&0xffffff00)|2
  elif label=='amount-one-ulp':bad[at+8]^=1
  elif label=='landing-clock-one-ulp':bad[at+6]^=1
  else:bad[at]=0
  try:check(bad)
  except AssertionError:rejected.append(label)
  else:raise AssertionError('Accepted corruption: '+label)
 r=dict(case=name,fresh_native_cases=1,original_current_skill_events=len(expected),expected_logical_recipients=[0],retargeted_live_add_slot=1,rejected_faults=rejected,gpu_calls=0)
 Path('/tmp/nikke-typed-actor-faults-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
