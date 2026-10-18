"""Compile-only favorite inventory; accepted definitions are not battle proof."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_favorite_loader',ROOT/'scripts/staged-hp-edge-runtime.py');loader=importlib.util.module_from_spec(sp);sp.loader.exec_module(loader);loader.install()
sys.path.insert(0,str(ROOT/'scripts'))
sp=importlib.util.spec_from_file_location('hp_favorite_audit',ROOT/'scripts/audit-detail-support.py');audit=importlib.util.module_from_spec(sp);sp.loader.exec_module(audit)
r=audit.audit();r.update(stage_only=True,gpu_battle_verified=False)
r['compiler_source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/staging/v35/app/detail_gpu.py','app/survival_compat.py','app/engine_compat.py','app/engine_worker.py','scripts/audit-detail-support.py','scripts/detail_coverage.py','scripts/staged-hp-edge-runtime.py','research/audit-staged-hp-edge-favorites.py')}
(ROOT/'research/detail-hp-edge-staged-favorites.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:r[k] for k in ('accepted_contexts','total_contexts','complete')}))
