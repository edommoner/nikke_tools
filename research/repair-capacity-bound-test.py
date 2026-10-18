"""Retest the sole stale assertion; preserve the complete failed run verbatim.

No production code or other test body changes. The final acceptance report is
explicitly an aggregation of 56 original passes and one focused rerun.
"""
import copy,hashlib,json,shutil,sys,time,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
report_path=ROOT/'research/detail-normal-acceptance.json'
initial=json.loads(report_path.read_text(encoding='utf-8'))
assert initial['tests_run']==57 and initial['skipped']==0 and not initial['passed']
assert len(initial['failures'])==1
target='test_out_of_bounds_groups_reject_before_any_cuda_access'
assert initial['failures'][0]['test'].startswith(target+' ')
assert all(sha(p)==h for p,h in initial['source_sha256'].items())
files=['research/detail-normal-acceptance.json','research/detail-normal-capacity-acceptance.log','tests/test_detail_charge_immunity.py']
for name in files:
    dst=ROOT/'research/ports/v29-initial'/name
    assert not dst.exists(),dst
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
name='tests/test_detail_charge_immunity.py';p=ROOT/name;old=p.read_text(encoding='utf-8')
assert old.count('for invalid in [-1,128,.5]:')==1
new=old.replace('for invalid in [-1,128,.5]:','for invalid in [-1,v.detail_gpu.NE,.5]:')
p.write_text(new,encoding='utf-8')
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'app'),str(ROOT/'scripts')]
started=time.perf_counter()
suite=unittest.defaultTestLoader.loadTestsFromName('test_detail_charge_immunity.ChargeImmunityTests.'+target)
result=unittest.TextTestRunner(verbosity=2).run(suite)
focused=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=result.wasSuccessful() and not result.skipped,tests_run=result.testsRun,seconds=time.perf_counter()-started,source_sha256={name:sha(name),'app/detail_gpu.py':sha('app/detail_gpu.py')},failures=[str(tb) for _,tb in result.failures+result.errors])
focused_path='research/detail-capacity-bound-retest.json'
(ROOT/focused_path).write_text(json.dumps(focused,indent=2)+'\n',encoding='utf-8')
assert focused['passed'] and focused['tests_run']==1
assert p.read_text(encoding='utf-8')==new
for file,h in initial['source_sha256'].items():
    if file!=name:assert sha(file)==h,file
final=copy.deepcopy(initial);final.update(generated_at=focused['generated_at'],passed=True,failures=[],seconds=initial['seconds']+focused['seconds'],
 verification_mode='Aggregated: 56 unchanged passing tests from the complete run and one stale bound assertion updated from literal 128 to NE, then rerun.',
 initial_tests_passed=56,focused_rerun_tests_passed=1,total_test_executions=58,
 initial_suite_report='research/ports/v29-initial/research/detail-normal-acceptance.json',focused_rerun_report=focused_path)
final['source_sha256'][name]=sha(name)
evidence=['research/repair-capacity-bound-test.py',focused_path,final['initial_suite_report'],'research/ports/v29-initial/tests/test_detail_charge_immunity.py']
final['source_sha256'].update({f:sha(f) for f in evidence})
report_path.write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=final['passed'],tests_run=57,initial_passed=56,focused_rerun_passed=1)))
