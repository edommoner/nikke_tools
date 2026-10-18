"""Focused acceptance for the changed cover capacity path through production imports."""
import hashlib,json,sys,time,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'app'),str(ROOT/'scripts')]
import detail_gpu
assert detail_gpu.DETAIL_ABI=='detail_cover_capacity_v37'
modules=['test_detail_cover_capacity','test_detail_cover_capacity_boundary']
files=['research/verify-cover-capacity-production.py','scripts/verify-cover-capacity.py','scripts/verify-cover-capacity-regressions.py','scripts/verify-cover-capacity-cube-carriers.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','scripts/verify-hp-edge.py','scripts/verify-hp-edge-real.py','scripts/verify-normal-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','app/gpu_service.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['tests/'+m+'.py' for m in modules]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};started=time.perf_counter()
suite=unittest.defaultTestLoader.loadTestsFromNames(modules);assert suite.countTestCases()==10
result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite);assert hashes=={p:sha(p) for p in files}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=result.wasSuccessful() and not result.skipped and result.testsRun==10,tests_run=result.testsRun,skipped=len(result.skipped),seconds=round(time.perf_counter()-started,3),modules=modules,abi=detail_gpu.DETAIL_ABI,whole_squad_cases=97,boundary_tests=6,full_normal118_rerun=False,objective_complete=False,scope='Changed cover-capacity and legacy cover/heal/HP/down paths; source-bound 97 whole-squad native cases plus six boundaries. Prior broader v36 suite is historical evidence, not a v37 full-suite claim.',failures=[dict(test=str(t),traceback=tb) for t,tb in result.failures+result.errors],source_sha256=hashes)
(ROOT/'research/detail-cover-capacity-production-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
