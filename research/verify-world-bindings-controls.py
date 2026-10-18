"""Reuse existing mixed-world, incoming and recovery tests after layout change."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('tests/test_detail_boss_clock.py','tests/test_detail_incoming.py','scripts/verify-boss-clock-detail.py','scripts/verify-incoming-detail.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','data/engine-effect-overrides.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
suite=unittest.defaultTestLoader.loadTestsFromNames(['test_detail_boss_clock.BossClockGPUTests','test_detail_incoming.IncomingGPU'])
r=unittest.TextTestRunner(verbosity=1).run(suite)
stable=before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=r.wasSuccessful() and not r.skipped and stable,tests_run=r.testsRun,source_stable=stable,source_sha256=before,failures=[dict(test=str(t),traceback=tb) for t,tb in r.failures+r.errors],scope='Existing world clock, mixed six-world batch, incoming targeting/defence, live mode, RNG and overflow recovery. Reused classes, no per-character matrix.')
(ROOT/'research/world-bindings-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(not report['passed'])
