"""Inventory staged max-HP cover-capacity grammar, without claiming GPU parity."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
load('capacity_inventory_loader','scripts/staged-cover-capacity-runtime.py').install();sys.path.insert(0,str(ROOT/'scripts'))
from detail_coverage import coverage
r=coverage();previous=json.loads((ROOT/'research/detail-survival-scaling-coverage.json').read_text(encoding='utf-8'));old={x['character'] for x in previous['results'] if x['supported']}
files=['research/audit-staged-cover-capacity.py','scripts/detail_coverage.py','scripts/audit-detail-support.py','scripts/staged-cover-capacity-runtime.py','research/staging/v37/app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','research/upstream/nikke-calc-master/data/parsed_skills.json'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
r.update(stage_only=True,gpu_battle_verified=False,objective_complete=False,source_sha256=hashes,newly_compiled=[x['character'] for x in r['results'] if x['supported'] and x['character'] not in old])
(ROOT/'research/detail-staged-cover-capacity-coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=load('capacity_favorite_inventory','scripts/audit-detail-support.py').audit();f.update(stage_only=True,gpu_battle_verified=False,compiler_source_sha256=hashes)
(ROOT/'research/detail-staged-cover-capacity-favorites.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(compiled=r['supported'],catalog=r['characters'],newly_compiled=r['newly_compiled'],favorite_contexts=f['accepted_contexts'],favorite_total=f['total_contexts'],gpu_battle_verified=False),ensure_ascii=True))
