"""Select existing regression witnesses by changed query dependencies."""
import hashlib
import importlib.util
import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ('tests', 'app', 'scripts')]
from verification_session import compare, stats, close


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


selected = [
    'test_detail_healing_storage.HealingStorageGPU.test_actual_raw_carriers_favorite_and_parts',
    'test_detail_heal_sharing.HealSharingGPU.test_actual_Rem_Nayuta_Crown_and_storage',
    'test_detail_heal_charge.HealChargeGPU.test_raw_Delta_Crown_Rem_and_Marciana',
    'test_detail_batch.HeterogeneousBatchTests.test_eight_independent_real_squads_keep_cpu_parity',
]
files = sorted({str(p.relative_to(ROOT)).replace('\\', '/')
    for directory, pattern in [('app', '*.py'), ('app', 'detail_effects*'), ('scripts', '*.py')]
    for p in (ROOT / directory).glob(pattern) if p.is_file()}
    | {f'tests/{s.split(".")[0]}.py' for s in selected}
    | {'research/verify-deferred-related.py'})


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}


before = hashes()
started = time.perf_counter()
result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(selected))
copy_row = {}
basis_rows = []
try:
    if result.wasSuccessful():
        copied = load('deferred_copy_control', 'scripts/verify-base-copy.py')
        name, body, extra = next(row for row in copied.fixtures() if row[0] == 'raw-copy-combined')
        copy_row = compare(copied, name, body, extra, 'native')
        basis = load('deferred_basis_control', 'scripts/verify-damage-basis-detail.py')
        fixtures = list(basis.real_fixtures())[:2]  # Existing additive/replacement raw squads.
        device = basis.Cuda()
        try:
            with patch.object(basis, 'real_fixtures', lambda: iter(fixtures)):
                basis_rows = basis.real_cases(device, 'native')
        finally:
            device.close()
    stable = before == hashes()
    report = dict(passed=result.wasSuccessful() and not result.skipped and stable
                  and copy_row.get('passed', False) and len(basis_rows) == 2 and all(row['passed'] for row in basis_rows),
        tests_run=result.testsRun, skipped=len(result.skipped), seconds=time.perf_counter() - started,
        source_stable=stable, source_sha256=before, selection=selected, copy_control=copy_row,
        basis_controls=basis_rows, recovery_reuse=stats(),
        scope='Existing raw storage5/sharing5/charge4, batch8 seed isolation, combined HP/ATK copy1 and raw HP attack-basis2. Unchanged ammo/pellet predicates are not repeated; no full-suite claim.',
        failures=[str(x) for x in result.failures + result.errors])
finally:
    close()
(ROOT / 'research/deferred-attack-related-native.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
