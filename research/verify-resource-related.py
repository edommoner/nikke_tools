"""Instruction-width and dispatcher integration regression, existing cases only."""
import hashlib
import importlib.util
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ('app', 'scripts', 'tests')]
from gpu_selector import Cuda

spec = importlib.util.spec_from_file_location('resource_deferred_controls', ROOT / 'scripts/verify-deferred-attack-detail.py')
v = importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
files = sorted({str(p.relative_to(ROOT)).replace('\\', '/')
    for directory, pattern in [('app', '*.py'), ('app', 'detail_effects*'), ('scripts', '*.py')]
    for p in (ROOT / directory).glob(pattern) if p.is_file()}
    | {'tests/test_detail_batch.py', 'data/engine-effect-overrides.json', 'research/verify-resource-related.py'})


def hashes():return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}


before = hashes();started = time.perf_counter()
result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromName(
    'test_detail_batch.HeterogeneousBatchTests.test_eight_independent_real_squads_keep_cpu_parity'))
rows = []
if result.wasSuccessful():
    device = Cuda()
    try:rows = v.verify(device, 'native') + v.legacy.phase_cases(device, 'native')
    finally:device.close()
stable = before == hashes()
report = dict(passed=result.wasSuccessful() and not result.skipped and stable and len(rows) == 14 and all(r['passed'] for r in rows),
    tests_run=result.testsRun, skipped=len(result.skipped), source_stable=stable,
    source_sha256=before, seconds=time.perf_counter() - started, deferred_controls=rows,
    scope='Existing8 heterogeneous squads/RNG plus14 cast/landing/gate/HP/magnitude/legacy controls exercise the new row width. Unchanged HP arithmetic quantities and old healing fanout are not repeated; no full-suite claim.')
(ROOT / 'research/resource-limits-related-native.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
