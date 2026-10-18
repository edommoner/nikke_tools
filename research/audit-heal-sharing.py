"""Staged compiler inventory. Acceptance is not battle parity."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('sharing_runtime',ROOT/'scripts/staged-heal-sharing-runtime.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);g=m.install()
sys.path.insert(0,str(ROOT/'scripts'))
from detail_coverage import coverage
files=['research/audit-heal-sharing.py','scripts/staged-heal-sharing-runtime.py','scripts/detail_coverage.py','scripts/audit-detail-support.py','research/staging/v41/app/detail_gpu.py','research/staging/v41/app/heal_sharing_compat.py','app/healing_storage_compat.py','app/outgoing_healing_compat.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/data/parsed_nikke.json','research/upstream/nikke-calc-master/data/base_stat_tables/cube.json']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
r=coverage();r.update(abi=g.DETAIL_ABI,stage_only=True,gpu_battle_verified=False,objective_complete=False,source_sha256=hashes)
(ROOT/'research/detail-heal-sharing-coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sp=importlib.util.spec_from_file_location('sharing_inventory',ROOT/'scripts/audit-detail-support.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);f=m.audit();f.update(abi=g.DETAIL_ABI,stage_only=True,objective_complete=False,compiler_source_sha256=hashes)
(ROOT/'research/detail-heal-sharing-favorites.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert hashes=={p:sha(p) for p in files}
print(json.dumps(dict(abi=g.DETAIL_ABI,compiled=r['supported'],catalog=r['characters'],favorite_contexts=f['accepted_contexts'],favorite_total=f['total_contexts'],objective_complete=False)))
