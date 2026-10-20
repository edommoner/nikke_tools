"""Shared CUDA/Metal component validation;capture input/readback before assertions."""
import argparse,array,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import dispatch_programs,pack_programs,decode
from portable_specs import LIMITS as L
from portable_hp_attack_oracle import observe
from portable_hp_attack_validation import rejection_programs

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--native-only',action='store_true');args=p.parse_args()
 spec=importlib.util.spec_from_file_location('hp_attack_core',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 cases=json.loads((ROOT/'tests/fixtures/portable-hp-attack.json').read_text())['cases'];programs=[v.compile_case(c) for c in cases];bad,rejections=rejection_programs(cases,v.compile_case)
 evidence={};captured=None;out=None
 if not args.native_only:
  stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'research/portable-build'/('hp-attack-component-'+stamp);folder.mkdir()
  (folder/'input.bin').write_bytes(pack_programs(programs+bad));raw,evidence=dispatch_programs(programs+bad,backend=args.backend)
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');captured=str(folder)
  out=array.array('I');out.frombytes(raw)
  if sys.byteorder!='little':out.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  actual=None;native=None
  try:
   native=observe(c);v.contains(native['queries'],c['expected_queries'],c['name']+'.native')
   if out is not None:
    actual=decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);assert actual['status']==0,actual['status']
    v.contains(actual['queries'],c['expected_queries'],c['name']+'.gpu');v.contains(actual['queries'],native['queries'],c['name']+'.native_gpu')
  except Exception as e:rows.append(dict(name=c['name'],passed=False,error=repr(e),native=native,actual=actual))
  else:rows.append(dict(name=c['name'],passed=True,native=native,actual=actual))
 paths=['app/portable_hp_attack_specs.py','scripts/portable_hp_attack_oracle.py','scripts/portable_hp_attack_validation.py','tests/fixtures/portable-hp-attack.json','research/build-hp-attack-cases.py','research/verify-hp-attack.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/damage.py']
 statuses=[] if out is None else [out[(len(cases)+i)*L['OUTPUT_WORDS']] for i in range(len(bad))]
 passed=all(r['passed'] for r in rows) and (out is None or statuses==[r['status'] for r in rejections]);result=dict(passed=passed,cases=rows,rejected_cases=rejections,actual_rejection_statuses=statuses,captured=captured,cpu_trace_used_as_gpu_input=False,**evidence,validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
 suffix='native' if args.native_only else args.backend
 (ROOT/f'research/portable-hp-attack-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 assert passed,[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'HP-derived attack cases passed',suffix)
if __name__=='__main__':main()
