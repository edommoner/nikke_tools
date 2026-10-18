"""Resume only the corrected harness tail; verify every prefix runtime hash first."""
import hashlib,json,sys,time,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'app'),str(ROOT/'scripts')]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
archive='research/ports/v36-production-before-test-wrapper-fix'
manifest=json.loads((ROOT/archive/'archive-manifest.json').read_text(encoding='utf-8'))
assert all(sha(archive+'/'+p)==h for p,h in manifest['files'].items())
prefix_path=archive+'/research/detail-normal-acceptance.json';prior=json.loads((ROOT/prefix_path).read_text(encoding='utf-8'))
assert not prior['passed'] and prior['tests_run']==96 and not prior['skipped'] and len(prior['failures'])==1
assert "AttributeError: module 'production_scaling_actual' has no attribute 'compare'" in prior['failures'][0]['traceback']
changed='tests/test_detail_survival_scaling.py'
assert all(sha(p)==h for p,h in prior['source_sha256'].items() if p!=changed),'Previously accepted runtime or prefix tests changed.'
old=(ROOT/archive/changed).read_text(encoding='utf-8');new=(ROOT/changed).read_text(encoding='utf-8')
needle="                with self.subTest(name=name):self.assertTrue(verifier.compare(device,name,b,extra,'native')['passed'])"
replacement="                with self.subTest(name=name):\n                    compare=verifier.compare if hasattr(verifier,'compare') else verifier.v.compare\n                    self.assertTrue(compare(device,name,b,extra,'native')['passed'])"
assert old.replace(needle,replacement)==new and old!=new,'Only the missing wrapper selection may change.'
modules=['test_detail_survival_scaling','test_detail_survival_scaling_boundary'];assert prior['modules'][-2:]==modules
files=set(prior['source_sha256'])|{'research/verify-survival-scaling-normal-tail.py',prefix_path,archive+'/archive-manifest.json'}
hashes={p:sha(p) for p in sorted(files)};started=time.perf_counter()
suite=unittest.defaultTestLoader.loadTestsFromNames(modules);assert suite.countTestCases()==13
result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
assert hashes=={p:sha(p) for p in hashes},'Source changed during tail acceptance.'
passed=result.wasSuccessful() and not result.skipped and result.testsRun==13
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=passed,tests_run=95+result.testsRun,skipped=len(result.skipped),seconds=round(prior['seconds']+time.perf_counter()-started,3),modules=prior['modules'],
    failures=[{'test':str(t),'traceback':tb} for t,tb in result.failures+result.errors],scope=prior['scope']+' Includes lost-HP/cover-revival and actual Moran/Biscuit squads.',
    execution='95 previously passed tests with unchanged runtime and prefix source hashes, plus the corrected 13-test tail. The original failing wrapper invocation is excluded.',
    verified_prefix_tests=95,tail_tests_run=result.testsRun,prefix_evidence=prefix_path,prefix_source_hashes_verified=True,source_sha256=hashes)
(ROOT/'research/detail-normal-acceptance.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'research/detail-survival-scaling-normal-tail-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if passed else 1)
