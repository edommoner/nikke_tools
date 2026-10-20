"""Common conditional HP contract;record the pinned native omission explicitly."""
import argparse,array,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import dispatch_programs,pack_programs,decode
from portable_specs import LIMITS as L
from portable_health_oracle import observe

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--native-only',action='store_true');a=p.parse_args()
 spec=importlib.util.spec_from_file_location('core',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 cases=json.loads((ROOT/'tests/fixtures/portable-health-runtime.json').read_text())['cases'];programs=[v.compile_case(c) for c in cases]
 evidence={};captured=None;out=None
 if not a.native_only:
  folder=ROOT/'research/portable-build'/('health-runtime-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
  (folder/'input.bin').write_bytes(pack_programs(programs))
  raw,evidence=dispatch_programs(programs,backend=a.backend)
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');captured=str(folder)
  out=array.array('I');out.frombytes(raw)
  if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  native=observe(c);v.contains(native,c['expected_native_queries'],c['name']+'.pinned_native')
  gpu=None
  if out is not None:
   gpu=decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);assert gpu['status']==0;v.contains(gpu['queries'],c['expected_queries'],c['name']+'.authored_contract')
  rows.append(dict(name=c['name'],passed=True,native_queries=native,gpu=gpu,expected_contract=c['expected_queries'],
      known_cpu_difference='Pinned effective_max_hp walks active HP carriers without rechecking runtime conditions;current HP follows that stale maximum'))
 paths=['research/verify-health-runtime.py','tests/fixtures/portable-health-runtime.json','scripts/portable_health_oracle.py','app/portable_runtime.py',
        'research/upstream/nikke-calc-master/calculator/buff_manager.py']
 result=dict(passed=True,cases=rows,captured=captured,**evidence,cpu_trace_used_as_gpu_input=False,
    validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
    scope='20 explicit finite quantities,5 casters,self/allies,2 HP stat families,initial and condition-disabled observations;known native omission is retained,not normalized')
 suffix='native' if a.native_only else a.backend
 (ROOT/f'research/portable-health-runtime-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('20 conditional HP cases passed',suffix,';native discrepancy recorded explicitly')
if __name__=='__main__':main()
