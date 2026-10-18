"""Inventory the ordinary v36 compiler; compilation is not battle parity."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import detail_gpu
assert detail_gpu.DETAIL_ABI=='detail_survival_scaling_v36'
from detail_coverage import coverage
files=['research/audit-production-survival-scaling.py','scripts/detail_coverage.py','scripts/audit-detail-support.py','app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
r=coverage();r.update(source_sha256=hashes,objective_complete=False,gpu_battle_verified=False)
(ROOT/'research/detail-survival-scaling-coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sp=importlib.util.spec_from_file_location('scaling_production_inventory',ROOT/'scripts/audit-detail-support.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
f=m.audit();f['compiler_source_sha256']=hashes
(ROOT/'research/detail-all-effects-audit.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert hashes=={p:sha(p) for p in files}
print(json.dumps(dict(abi=detail_gpu.DETAIL_ABI,compiled=r['supported'],catalog=r['characters'],favorite_contexts=f['accepted_contexts'],favorite_total=f['total_contexts'],objective_complete=False)))
