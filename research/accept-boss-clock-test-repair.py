"""Combine the unchanged 64 passing tests with a full rerun of the repaired module.

The first attempt remains on disk. No production source changes are allowed
between attempts, and every failed test must belong to the rerun module.
"""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
p=ROOT/'research/detail-boss-clock-normal-first-attempt.json';old=json.loads(p.read_text(encoding='utf-8'))
assert old['tests_run']==70 and old['skipped']==0 and len(old['failures'])==1
assert 'test_distinct_worlds_are_isolated_in_one_concurrent_launch' in old['failures'][0]['test'] and 'test_detail_boss_clock.' in old['failures'][0]['test']
assert 'Query indices must be contiguous' in old['failures'][0]['traceback']
assert all(sha(f)==h for f,h in old['source_sha256'].items() if f!='tests/test_detail_boss_clock.py')
raw=(ROOT/'research/detail-boss-clock-repaired-tests.log').read_bytes();log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert 'Ran 6 tests' in log and '\nOK' in log and 'FAILED' not in log
r={**old,'generated_at':datetime.now(timezone.utc).isoformat(),'passed':True,'failures':[],
 'verification_method':'64 tests passed in the initial unchanged module set; all 6 tests in test_detail_boss_clock passed after repairing its missing readback command. Production sources are identical. This is a combined acceptance report, not a fresh 70-test execution.',
 'first_attempt':'research/detail-boss-clock-normal-first-attempt.json','repaired_module':'test_detail_boss_clock','rerun_log':'research/detail-boss-clock-repaired-tests.log',
 'source_sha256':{f:sha(f) for f in old['source_sha256']},'evidence_sha256':{f:sha(f) for f in ['research/detail-boss-clock-normal-first-attempt.json','research/detail-boss-clock-repaired-tests.log','research/accept-boss-clock-test-repair.py']}}
(ROOT/'research/detail-normal-acceptance.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'unchanged_tests':64,'repaired_module_tests':6,'production_sources_unchanged':True}))
