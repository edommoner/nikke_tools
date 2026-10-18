"""v40 compilation inventory; compilation is not GPU battle verification."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
sp=importlib.util.spec_from_file_location('storage_loader',ROOT/'scripts/staged-healing-storage-runtime.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);g=m.install()
from detail_coverage import coverage
files=['research/audit-staged-healing-storage.py','scripts/staged-healing-storage-runtime.py','scripts/detail_coverage.py','scripts/audit-detail-support.py','research/staging/v40/app/detail_gpu.py','research/staging/v40/app/healing_storage_compat.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','research/upstream/nikke-calc-master/data/parsed_skills.json'];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
r=coverage();r.update(source_sha256=hashes,objective_complete=False,gpu_battle_verified=False,cpu_model_extended=True,abi=g.DETAIL_ABI)
(ROOT/'research/detail-staged-healing-storage-coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sp=importlib.util.spec_from_file_location('storage_inventory',ROOT/'scripts/audit-detail-support.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);f=a.audit();f.update(compiler_source_sha256=hashes,objective_complete=False,gpu_battle_verified=False,cpu_model_extended=True,abi=g.DETAIL_ABI)
(ROOT/'research/detail-staged-healing-storage-favorites.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert hashes=={p:sha(p) for p in files}
print(json.dumps(dict(abi=g.DETAIL_ABI,compiled=r['supported'],catalog=r['characters'],favorite_contexts=f['accepted_contexts'],favorite_total=f['total_contexts'],objective_complete=False)))
