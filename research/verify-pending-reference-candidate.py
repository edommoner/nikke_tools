"""Exact shared pending-reference packets and malformed entry-delay admission."""
import array,copy,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
import portable_runtime as runtime,portable_combat
from portable_specs import LIMITS as L,FIELDS as F
from pending_reference_context import data_context
from pending_reference_native import observe
from mode_entry_native import data_context as entry_context

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 prep=json.loads((ROOT/'research/portable-mode-entry-candidate-preparation.json').read_text());directory=Path(prep['candidate_directory']);adapter=module('pending_entry_adapter',directory/'app/portable_runtime.py');combat=module('pending_entry_combat',directory/'app/portable_combat.py');core=module('pending_entry_core',ROOT/'scripts/verify-portable-combat.py')
 cases=json.loads((ROOT/'research/portable-pending-reference-inputs.json').read_text())['cases'];programs=[];bad=[];rejections=[];oldpack=portable_combat.pack_mode;oldcompile=core.compile_program
 portable_combat.pack_mode=combat.pack_mode;core.compile_program=adapter.compile_program
 try:
  for c in cases:
   with data_context(c):w,m=core.compile_case(c)
   w[0]=0x50455672;programs.append((w,m))
  e=json.loads((ROOT/'research/portable-mode-entry-inputs.json').read_text())['cases'][0]
  with entry_context(e):w,m=core.compile_case(e)
  w[0]=0x50455672;pos=L['MODE_BASE']+2*L['MODE_WORDS']+28;d=L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']
  variants=[('flag',{pos+2:2}),('reserved',{pos+3:1}),('missing-flag',{pos:runtime.double_words(.39)[0],pos+1:runtime.double_words(.39)[1],pos+2:0}),('kind',{d+F['KIND']:0}),('noncombat',{3:0}),('nonmode-payload',{L['MODE_BASE']+30:1})]
  for label,value in [('negative',-1),('nan',None),('inf',None),('large',181)]:
   bits=[0,0x7ff80000] if label=='nan' else [0,0x7ff00000] if label=='inf' else runtime.double_words(value)
   variants.append((label,{pos:bits[0],pos+1:bits[1]}))
  for label,changes in variants:
   words=w.copy()
   for p,v in changes.items():words[p]=v
   bad.append((words,copy.deepcopy(m)));rejections.append(dict(name='mode-entry-invalid-'+label,status=64))
 finally:portable_combat.pack_mode=oldpack;core.compile_program=oldcompile
 folder=ROOT/'research/portable-build'/('pending-reference-component-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(runtime.pack_programs(programs+bad));one,many=runtime.execute,runtime.execute_batches
 def single(source,*a,**kw):return one(prep['shader'],*a,**kw)
 def batch(source,*a,**kw):return many(prep['shader'],*a,**kw)
 runtime.execute=single;runtime.execute_batches=batch
 try:raw,evidence=runtime.dispatch_programs(programs+bad,backend='metal')
 finally:runtime.execute=one;runtime.execute_batches=many
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');out=array.array('I');out.frombytes(raw)
 if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  actual=runtime.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);native=None
  try:
   assert actual['status']==0,actual['status']
   with data_context(c):native=observe(c)
   core.contains(native['queries'],c['expected_queries'],c['name']+'.authored');core.contains(actual['queries'],native['queries'],c['name']+'.native');core.contains(actual['trace'],native['packets'],c['name']+'.native-packets')
  except Exception as error:rows.append(dict(name=c['name'],passed=False,error=repr(error),actual=actual,native=native))
  else:rows.append(dict(name=c['name'],passed=True,actual=actual,native=native))
 statuses=[out[(len(cases)+i)*L['OUTPUT_WORDS']] for i in range(len(bad))];result=dict(passed=all(r['passed'] for r in rows) and statuses==[64]*len(bad),cases=rows,rejected_cases=rejections,actual_rejection_statuses=statuses,captured=str(folder),preparation=prep,**evidence,cpu_trace_used_as_gpu_input=False,production_adopted=False,validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/verify-pending-reference-candidate.py','research/pending_reference_context.py','research/pending_reference_native.py','research/portable-pending-reference-inputs.json']})
 (ROOT/'research/portable-pending-reference-candidate-metal.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],([(r['name'],r.get('error')) for r in rows if not r['passed']],statuses);print(len(rows),'pending reference cases and',len(bad),'entry-delay rejections passed')
if __name__=='__main__':main()
