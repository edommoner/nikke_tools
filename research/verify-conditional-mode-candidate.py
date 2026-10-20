"""Isolated admission candidate:remove one guard,retain the common GPU unchanged."""
import array,copy,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime as runtime
from portable_specs import LIMITS as L

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 base=subprocess.check_output(['git','rev-parse','0ae6a14'],cwd=ROOT,text=True).strip();subprocess.run(['git','diff','--exit-code',base,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
 source=subprocess.check_output(['git','show',base+':app/portable_runtime.py'],cwd=ROOT,text=True)
 guard="            if row[7]<0 and row[14]>0:raise UnsupportedPortable('Infinite conditional weapon mode is not ported')\n"
 assert source.count(guard)==1
 folder=ROOT/'research/portable-build'/('conditional-mode-candidate-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 path=folder/'candidate_adapter.py';path.write_text(source.replace(guard,''));candidate=module('conditional_mode_candidate_adapter',path)
 roster=module('conditional_mode_roster',ROOT/'scripts/verify-portable-roster-battles.py');reference=roster.reference
 from portable_roster_input import compile_static_battle
 from detail_coverage import body_for
 name='라플라스 : 얼티밋 히어로';plans=[];programs=[];original=runtime.compile_program
 runtime.compile_program=candidate.compile_program
 try:
  for grown in (False,True):
   body={**body_for(roster.roster_for(name),duration=180,grown=grown),'burst_gauge_mode':'accumulate'}
   prepared=roster.adapter.evaluate({**body,'_portable_static_inputs':True});assert prepared['cpu_battle_executed'] is False
   programs.append(compile_static_battle(prepared,trace='burst'));plans.append((body,prepared))
 except Exception as error:
  (ROOT/'research/portable-conditional-mode-candidate.json').write_text(json.dumps(dict(passed=False,stage='compile-refused-before-GPU',error=repr(error),captured=str(folder),gpu_executed=False,base_source_commit=base,production_guard_removed=False,candidate_adapter_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),indent=2)+'\n')
  raise
 finally:runtime.compile_program=original
 (folder/'input.bin').write_bytes(runtime.pack_programs(programs));raw,evidence=runtime.dispatch_programs(programs,backend='metal')
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 out=array.array('I');out.frombytes(raw)
 if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,(body,prepared) in enumerate(plans):
  gpu=runtime.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);cpu=reference.native_reference(copy.deepcopy(body));diff=reference.compare_native_result(gpu,prepared,cpu)
  rows.append(dict(character=name,grown=bool(i),passed=gpu['status']==0 and not diff,differences=diff,gpu=gpu,native=cpu))
 result=dict(passed=all(r['passed'] for r in rows),base_source_commit=base,production_guard_removed=False,root_compute_sources_changed=False,candidate_adapter_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),removed_exact_guard=guard,driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),captured=str(folder),cases=rows,**evidence,cpu_trace_used_as_gpu_input=False,scope='Two complete180-second real profiles with only the admission guard removed in an isolated adapter. Not certification of arbitrary conditional modes or permission to remove the production guard.')
 (ROOT/'research/portable-conditional-mode-candidate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 assert result['passed'],[(r['grown'],r['differences']) for r in rows if not r['passed']]
 print('Two real Laplace profiles match original CPU with isolated admission candidate;production guard retained')
if __name__=='__main__':main()
