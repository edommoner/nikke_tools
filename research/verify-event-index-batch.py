"""Preserve the eight old squads, adding on/off mode input in the same batch."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
files=list((ROOT/'app').glob('*.py'))+[ROOT/p for p in ('tests/test_detail_batch.py','scripts/verify-catalog-batch-detail.py','research/verify-event-index-batch.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','data/engine-effect-overrides.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromName('test_detail_batch.HeterogeneousBatchTests.test_independent_real_squads_keep_cpu_parity'))
stable=before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=result.wasSuccessful() and not result.skipped and stable,tests_run=result.testsRun,batch_squads=10,previous_squads_preserved=8,mode_policy_variants=[False,True],source_stable=stable,source_sha256=before)
(ROOT/'research/event-index-batch-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
