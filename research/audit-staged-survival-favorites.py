"""Compile-only inventory for the staged interpreter; never overwrite production audit."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('survival_loader',ROOT/'scripts/staged-survival-runtime.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader);loader.install()
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('staged_inventory',ROOT/'scripts/audit-detail-support.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
r=audit.audit();r['stage_only']=True
r['compiler_source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/staging/v34/app/detail_gpu.py','research/staging/v34/app/survival_compat.py','scripts/audit-detail-support.py','scripts/detail_coverage.py','scripts/staged-survival-runtime.py']}
(ROOT/'research/detail-staged-survival-favorites.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:r[k] for k in ('accepted_contexts','total_contexts','complete')}))
