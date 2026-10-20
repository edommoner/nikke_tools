"""Component/native gate for shared element advantage override."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import run_programs
from portable_element_oracle import observe,compare

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--backend',default='metal',choices=['metal','cuda']);parser.add_argument('--native-only',action='store_true');args=parser.parse_args()
 spec=importlib.util.spec_from_file_location('element_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 cases=json.loads((R/'tests/fixtures/portable-element-overrides.json').read_text())['cases']
 tracked=['app/portable_element_specs.py','app/portable_code_specs.py','app/portable_runtime.py','app/portable_damage_specs.py','scripts/portable_element_oracle.py','scripts/portable_enemy_oracle.py','scripts/portable_weapon_oracle.py','tests/fixtures/portable-element-overrides.json','research/verify-elements.py']
 hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked}
 result=run_programs([v.compile_case(c) for c in cases],backend=args.backend) if not args.native_only else None
 rows=[]
 for i,c in enumerate(cases):
  cpu=observe(c) if result is None else compare(c,result['results'][i],v.contains)
  if result is None:v.contains(cpu['queries'],c['expected_queries'],c['name'])
  rows.append(dict(name=c['name'],passed=True,native=cpu))
 for p,h in hashes.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
 report=dict(passed=True,cases=rows,validation_sha256=hashes,cpu_trace_used_as_gpu_input=False)
 if result is not None:report.update({k:x for k,x in result.items() if k!='results'})
 (R/('research/portable-element-overrides-'+('native' if args.native_only else args.backend)+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('element override',len(rows),'native' if args.native_only else args.backend,'passed')
if __name__=='__main__':main()
