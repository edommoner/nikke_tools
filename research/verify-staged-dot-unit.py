"""Native-stage CPU contracts; portable bundle contract runs on the final build."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
modules=['test_target_counter_runtime','test_impact_runtime','test_effect_runtime','test_effect_spec','test_reference_rewrite',
    'test_damage_query_runtime','test_resource_specs','test_effect_overrides','test_event_index_specs','test_periodic_source_runtime','test_staged_dot_runtime']
files=list((ROOT/'app').glob('*.py'))+[ROOT/f'tests/{name}.py' for name in modules]+[Path(__file__).resolve(),ROOT/'app/detail_effects.cu',ROOT/'app/detail_effects-sm86.json',ROOT/'data/engine-effect-overrides.json']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
stable=before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=result.wasSuccessful() and not result.skipped and stable,tests_run=result.testsRun,source_stable=stable,source_sha256=before,
    excluded_modules=['test_detail_build_contract'],scope='Native development stage before the required efficiency attempt; final portable bundle still pending.',
    failures=[dict(test=str(t),traceback=tb) for t,tb in result.failures+result.errors])
(ROOT/'research/staged-dot-unit-stage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
