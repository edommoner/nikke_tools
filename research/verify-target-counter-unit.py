"""Shared operation, data-migration and event boundaries; no GPU case copies."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
modules=['test_target_counter_runtime','test_impact_runtime','test_effect_runtime','test_effect_spec','test_reference_rewrite',
         'test_damage_query_runtime','test_resource_specs','test_effect_overrides','test_detail_build_contract']
files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'app').glob('*.py')}
    |{f'tests/{name}.py' for name in modules}|{'app/detail_effects.cu','app/detail_effects-build.json','app/detail_effects-sm86.json','research/verify-target-counter-unit.py','data/engine-effect-overrides.json'})
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
before=hashes();result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(modules));stable=before==hashes()
report=dict(passed=result.wasSuccessful() and not result.skipped and stable,tests_run=result.testsRun,skipped=len(result.skipped),
    failures=[dict(test=str(t),traceback=tb) for t,tb in result.failures+result.errors],source_stable=stable,source_sha256=before)
(ROOT/'research/target-counters-unit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
