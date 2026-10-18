"""Record independent pre-CUDA validation gates with exact source hashes."""
import hashlib,importlib.util,json,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_boundary_tests',ROOT/'research/test_staged_hp_edge_boundaries.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
suite=unittest.defaultTestLoader.loadTestsFromModule(m);result=unittest.TextTestRunner(verbosity=2).run(suite)
files=['research/test_staged_hp_edge_boundaries.py','research/verify-hp-edge-boundaries.py','scripts/verify-staged-hp-edge.py','scripts/staged-hp-edge-runtime.py','research/staging/v35/app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=result.wasSuccessful() and not result.skipped,tests_run=result.testsRun,skipped=len(result.skipped),stage_only=True,objective_complete=False,gpu_combat_run=False,failures=[str(t)+'\n'+tb for t,tb in result.failures+result.errors],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-hp-edge-boundary-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
