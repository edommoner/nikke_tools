"""Canonical victim/RNG/landing contract, shared across CUDA and Metal."""
import argparse,array,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as rt
from portable_specs import LIMITS as L
from portable_enemy_target_oracle import observe,compare
from portable_enemy_target_validation import programs as rejections

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--native-only',action='store_true');a=p.parse_args()
 s=importlib.util.spec_from_file_location('canonical_victims',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 cases=json.loads((R/'tests/fixtures/portable-enemy-targets.json').read_text())['cases'];items=[v.compile_case(c) for c in cases];bad,rejected=rejections(cases,v.compile_case)
 evidence={};out=None;folder=None
 if not a.native_only:
  folder=R/'research/portable-build'/('enemy-victim-component-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(rt.pack_programs(items+bad))
  raw,evidence=rt.dispatch_programs(items+bad,backend=a.backend);(folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');out=array.array('I');out.frombytes(raw)
  if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  native=actual=None
  try:
   if out is None:
    native=observe(c)
    if c['name'].startswith('enemy-long-rng-'):assert (native['rng']['draws'],native['rng']['index'])==(627,3)
    if c['name']=='enemy-source-time-between-frames':assert [r['targets'] for r in native['selection']]==[[0],[1]]
   else:
    actual=rt.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],items[i][1]);assert actual['status']==0,actual['status'];native=compare(c,actual,v.contains)
  except Exception as error:rows.append(dict(name=c['name'],passed=False,error=repr(error),native=native,actual=actual))
  else:rows.append(dict(name=c['name'],passed=True,native=native,actual=actual))
 statuses=[] if out is None else [out[(len(cases)+i)*L['OUTPUT_WORDS']] for i in range(len(bad))]
 passed=all(r['passed'] for r in rows) and (out is None or statuses==[r['status'] for r in rejected])
 paths=['app/portable_enemy_target_specs.py','scripts/portable_enemy_target_oracle.py','scripts/portable_enemy_target_validation.py','scripts/portable_target_rng_oracle.py','tests/fixtures/portable-enemy-targets.json','research/verify-enemy-targets.py']
 result=dict(passed=passed,cases=rows,rejected_cases=rejected,gpu_rejections_checked=out is not None,actual_rejection_statuses=statuses,captured=str(folder) if folder else None,cpu_selected_targets_used_as_gpu_input=False,cpu_rng_state_used_as_gpu_input=False,validation_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},**evidence)
 suffix='native' if a.native_only else a.backend
 (R/f'research/portable-enemy-victims-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert passed,[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'canonical victim/RNG/landing cases passed',suffix)
if __name__=='__main__':main()
