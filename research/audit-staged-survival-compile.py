import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
loader=load('survival_loader','scripts/staged-survival-runtime.py');g=loader.install();sys.path.insert(0,str(ROOT/'scripts'))
from detail_coverage import coverage
r=coverage();(ROOT/'research/detail-staged-survival-coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=json.loads((ROOT/'research/detail-incoming-coverage.json').read_text(encoding='utf-8'));previous={r['character'] for r in before['results'] if r['supported']}
print(json.dumps(dict(compiled=r['supported'],catalog=r['characters'],newly_compiled=[x['character'] for x in r['results'] if x['supported'] and x['character'] not in previous],gpu_verified=False),ensure_ascii=True))
