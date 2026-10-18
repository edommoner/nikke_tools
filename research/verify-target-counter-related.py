"""Existing no-counter, typed-landing and legacy deferred controls reused once."""
import hashlib,importlib.util,json,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from gpu_selector import Cuda
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for directory,pattern in
    [('app','*.py'),('app','detail_effects*'),('scripts','*.py')]
    for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'tests/test_detail_batch.py','research/verify-target-counter-related.py','data/engine-effect-overrides.json'})
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
before=hashes();started=time.perf_counter()
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromName('test_detail_batch.HeterogeneousBatchTests.test_eight_independent_real_squads_keep_cpu_parity'))
rows=[]
if result.wasSuccessful():
    typed=load('counter_existing_impacts','scripts/verify-typed-impacts-detail.py')
    legacy=load('counter_existing_legacy','scripts/verify-named-target-detail.py')
    device=Cuda()
    try:rows=[typed.quantities(device,'native')]+typed.squads(device,'native')+legacy.phase_cases(device,'native')
    finally:device.close()
stable=before==hashes()
report=dict(passed=result.wasSuccessful() and not result.skipped and stable and len(rows)==7 and all(r['passed'] for r in rows),
    tests_run=result.testsRun,skipped=len(result.skipped),batch_squads=8,cases=rows,source_stable=stable,source_sha256=before,seconds=time.perf_counter()-started,
    scope='Existing8 heterogeneous/RNG squads,3 typed-transport/landing controls and4 legacy cast-landing controls. Fixtures/comparators reused; no full-suite claim.')
(ROOT/'research/target-counters-related-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
