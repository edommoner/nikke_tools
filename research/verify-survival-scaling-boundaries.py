"""Source-bound pre-CUDA and CPU revival-context acceptance for v36."""
import hashlib,importlib.util,json,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('scaling_boundary_acceptance',ROOT/'research/test_staged_survival_scaling_boundaries.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
suite=unittest.defaultTestLoader.loadTestsFromModule(m);result=unittest.TextTestRunner(verbosity=2).run(suite)
files=['research/test_staged_survival_scaling_boundaries.py','research/verify-survival-scaling-boundaries.py','scripts/staged-survival-scaling-runtime.py','research/staging/v36/app/detail_gpu.py','research/staging/v36/app/survival_scaling_compat.py','app/engine_compat.py','app/survival_compat.py','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=result.wasSuccessful() and not result.skipped,tests_run=result.testsRun,skipped=len(result.skipped),gpu_run=False,stage_only=True,objective_complete=False,failures=[str(t)+'\n'+tb for t,tb in result.failures+result.errors],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-survival-scaling-boundary-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
