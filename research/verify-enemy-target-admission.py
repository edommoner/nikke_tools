"""Isolated shared candidate raw admission;save all bytes before assertions."""
import argparse,array,datetime,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts'),str(R/'research')]
import portable_runtime as rt
from portable_specs import LIMITS as L
from enemy_target_validation import programs
import importlib.util
s=importlib.util.spec_from_file_location('victim_candidate',R/'research/verify-enemy-target-candidate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');a=p.parse_args();core=v.core_module();cases=json.loads((R/'research/portable-enemy-target-inputs.json').read_text())['cases'];items,rejections=programs(cases,lambda c:v.compile_case(c,core));prep=json.loads((R/'research/portable-enemy-target-candidate-preparation.json').read_text())
 folder=R/'research/portable-build'/('enemy-target-admission-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(rt.pack_programs(items))
 one,many=rt.execute,rt.execute_batches
 def single(source,*args,**kw):assert source=='gpu/event_runtime.slang';return one(prep['shader'],*args,**kw)
 def multiple(source,*args,**kw):assert source=='gpu/event_runtime.slang';return many(prep['shader'],*args,**kw)
 rt.execute=single;rt.execute_batches=multiple
 try:raw,evidence=rt.dispatch_programs(items,backend=a.backend)
 finally:rt.execute=one;rt.execute_batches=many
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');out=array.array('I');out.frombytes(raw)
 if sys.byteorder!='little':out.byteswap()
 statuses=[out[i*L['OUTPUT_WORDS']] for i in range(len(items))];passed=statuses==[r['status'] for r in rejections]
 report=dict(passed=passed,rejections=rejections,actual_statuses=statuses,captured=str(folder),preparation=prep,production_adopted=False,**evidence)
 (R/f'research/portable-enemy-target-admission-{a.backend}.json').write_text(json.dumps(report,indent=2)+'\n');assert passed,[(r['name'],s) for r,s in zip(rejections,statuses) if s!=r['status']]
 print(len(items),'enemy target raw rejection cases passed',a.backend)
if __name__=='__main__':main()
