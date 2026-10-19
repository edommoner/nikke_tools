"""Shared native/GPU checks on both sides of the scratch-clear threshold."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_runtime import run_programs
from portable_status_oracle import compare
s=importlib.util.spec_from_file_location('clear_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
a=argparse.ArgumentParser();a.add_argument('--backend',choices=('cuda','metal'),default='metal');args=a.parse_args()
cases=[]
for count in (64,65):
 effects=[dict(name='boundary-pool-'+str(i),source='스킬1',type='buff',stat='debuff_immune_count',fixed_value=1,target='all_allies',duration=-1,max_stack=1,trigger=dict(timing=['event:full_reload'],condition=[])) for i in range(count)]
 effects.append(dict(name='harm',source='스킬1',type='buff',stat='atk_pct',fixed_value=-1,target='all_allies',duration=-1,max_stack=1000,polarity='harmful',trigger=dict(timing=['on_attack'],condition=[])))
 cases.append(dict(name='status-clear-boundary-'+str(count),effects=effects,combat=dict(weapons=[dict(enabled=False) for _ in range(5)],targets=[dict(hp=100000)]),stack_reference=True,status_reference=True,expected_queries=[dict(time=.63)],script=[[0,0,19,0,0,-1,0,0]]+[[i/100,0,7,0,0,-1,0,0] for i in range(1,63)]+[[.63,2,0,0,0,0,0,0]]))
out=run_programs([v.compile_case(c) for c in cases],backend=args.backend);results=out.pop('results');assert all(r['status']==0 for r in results)
rows=[dict(name=c['name'],passed=True,cpu=compare(c,r,v.contains)) for c,r in zip(cases,results)]
report=dict(passed=True,cases=rows,actual_statuses=[r['status'] for r in results],expected_statuses=[0,0],input_from_native_trace=False,validation_sha256={'research/verify-status-clear-boundaries.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},**out)
(P/f'portable-status-clear-boundaries-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Scratch threshold64/65 native and GPU passed',args.backend)
