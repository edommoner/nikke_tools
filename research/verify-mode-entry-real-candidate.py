"""Full real Laplace profiles through isolated shared entry-delay implementation."""
import array,copy,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime as runtime,portable_combat
from portable_specs import LIMITS as L

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 prep=json.loads((ROOT/'research/portable-mode-entry-candidate-preparation.json').read_text());directory=Path(prep['candidate_directory']);adapter=module('real_entry_adapter',directory/'app/portable_runtime.py');combat=module('real_entry_combat',directory/'app/portable_combat.py')
 roster=module('real_entry_roster',ROOT/'scripts/verify-portable-roster-battles.py');reference=roster.reference
 from portable_roster_input import compile_static_battle
 from detail_coverage import body_for
 old_compile=runtime.compile_program;old_pack=portable_combat.pack_mode;plans=[];programs=[]
 def compile(*a,**kw):
  words,meta=adapter.compile_program(*a,**kw);words[0]=0x50455672;return words,meta
 runtime.compile_program=compile;portable_combat.pack_mode=combat.pack_mode
 try:
  for grown in (False,True):
   body={**body_for(roster.roster_for('라플라스 : 얼티밋 히어로'),duration=180,grown=grown),'burst_gauge_mode':'accumulate'};prepared=roster.adapter.evaluate({**body,'_portable_static_inputs':True});assert prepared['cpu_battle_executed'] is False
   programs.append(compile_static_battle(prepared,trace='burst'));plans.append((body,prepared))
 finally:runtime.compile_program=old_compile;portable_combat.pack_mode=old_pack
 folder=ROOT/'research/portable-build'/('mode-entry-real-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 (folder/'input.bin').write_bytes(runtime.pack_programs(programs));one,many=runtime.execute,runtime.execute_batches
 def single(source,*a,**kw):assert source=='gpu/event_runtime.slang';return one(prep['shader'],*a,**kw)
 def batch(source,*a,**kw):assert source=='gpu/event_runtime.slang';return many(prep['shader'],*a,**kw)
 runtime.execute=single;runtime.execute_batches=batch
 try:raw,evidence=runtime.dispatch_programs(programs,backend='metal')
 finally:runtime.execute=one;runtime.execute_batches=many
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 out=array.array('I');out.frombytes(raw)
 if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,(body,prepared) in enumerate(plans):
  gpu=runtime.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);gpu['mode_entry_wait_until']=list(struct.unpack_from('<5d',raw,(i*L['OUTPUT_WORDS']+159232)*4));cpu=reference.native_reference(copy.deepcopy(body));diff=reference.compare_native_result(gpu,prepared,cpu,program=programs[i])
  rows.append(dict(character=body['squad'][0],grown=bool(i),passed=gpu['status']==0 and not diff,differences=diff,gpu=gpu,native=cpu))
 result=dict(passed=all(r['passed'] for r in rows),preparation=prep,captured=str(folder),cases=rows,**evidence,cpu_trace_used_as_gpu_input=False,production_adopted=False,driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Two180-second whole real profiles with entry delay and activation-only conditions;strict existing native comparison,not all-character certification.')
 (ROOT/'research/portable-mode-entry-real-candidate-metal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert result['passed'],[(r['grown'],r['differences']) for r in rows if not r['passed']]
 print('Both full Laplace180-second profiles match original CPU on isolated candidate')
if __name__=='__main__':main()
