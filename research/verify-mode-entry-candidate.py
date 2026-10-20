"""Common candidate kernel and packer,with full readback retained before native checks."""
import array,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
import portable_runtime as runtime,portable_combat
from portable_specs import LIMITS as L
from mode_entry_native import data_context,observe

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 preparation=json.loads((ROOT/'research/portable-mode-entry-candidate-preparation.json').read_text());directory=Path(preparation['candidate_directory'])
 adapter=module('mode_entry_adapter',directory/'app/portable_runtime.py');combat=module('mode_entry_combat',directory/'app/portable_combat.py');core=module('mode_entry_core',ROOT/'scripts/verify-portable-combat.py')
 cases=json.loads((ROOT/'research/portable-mode-entry-inputs.json').read_text())['cases'];programs=[]
 original_pack=portable_combat.pack_mode;original_compile=core.compile_program
 portable_combat.pack_mode=combat.pack_mode;core.compile_program=adapter.compile_program
 try:
  for c in cases:
   with data_context(c):words,metadata=core.compile_case(c)
   words[0]=0x50455672;metadata['mode_entry_enabled']=any(words[L['MODE_BASE']+i*L['MODE_WORDS']+30] for i in range(words[1]));programs.append((words,metadata))
 finally:portable_combat.pack_mode=original_pack;core.compile_program=original_compile
 folder=ROOT/'research/portable-build'/('mode-entry-component-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 (folder/'input.bin').write_bytes(runtime.pack_programs(programs));one,many=runtime.execute,runtime.execute_batches
 def single(source,*a,**kw):assert source=='gpu/event_runtime.slang';return one(preparation['shader'],*a,**kw)
 def batches(source,*a,**kw):assert source=='gpu/event_runtime.slang';return many(preparation['shader'],*a,**kw)
 runtime.execute=single;runtime.execute_batches=batches
 try:raw,evidence=runtime.dispatch_programs(programs,backend='metal')
 finally:runtime.execute=one;runtime.execute_batches=many
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 out=array.array('I');out.frombytes(raw)
 if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  actual=runtime.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);native=None
  try:
   assert actual['status']==0,actual['status'];native=observe(c);core.contains(native['queries'],c['expected_queries'],c['name']+'.authored-native');core.contains(actual['queries'],native['queries'],c['name']+'.gpu-native');core.contains(actual['weapons'],native['weapons'],c['name']+'.physical-clock')
   if programs[i][1]['mode_entry_enabled']:
    start=(i*L['OUTPUT_WORDS']+159232)*4;actual['mode_entry_wait_until']=list(struct.unpack_from('<5d',raw,start));core.contains(actual['mode_entry_wait_until'],native['mode_entry_wait_until'],c['name']+'.entry-clock')
  except Exception as error:rows.append(dict(name=c['name'],passed=False,error=repr(error),actual=actual,native=native))
  else:rows.append(dict(name=c['name'],passed=True,actual=actual,native=native))
 result=dict(passed=all(r['passed'] for r in rows),cases=rows,captured=str(folder),preparation=preparation,**evidence,cpu_trace_used_as_gpu_input=False,production_adopted=False,validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/verify-mode-entry-candidate.py','research/build-mode-entry-cases.py','research/mode_entry_native.py','research/portable-mode-entry-inputs.json']})
 (ROOT/'research/portable-mode-entry-candidate-metal.json').write_text(json.dumps(result,indent=2)+'\n')
 assert result['passed'],[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'mode entry candidate cases match native firing/clock/state')
if __name__=='__main__':main()
