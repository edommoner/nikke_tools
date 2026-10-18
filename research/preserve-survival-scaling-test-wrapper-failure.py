"""Keep the failed acceptance harness and verified production prefix immutable."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
path='research/detail-normal-acceptance.json';r=json.loads((ROOT/path).read_text(encoding='utf-8'))
assert not r['passed'] and r['tests_run']==96 and len(r['failures'])==1 and not r['skipped']
assert "AttributeError: module 'production_scaling_actual' has no attribute 'compare'" in r['failures'][0]['traceback']
assert all(sha(p)==h for p,h in r['source_sha256'].items())
closure=set(r['source_sha256'])|{path,'research/detail-survival-scaling-normal-tests.log','research/preserve-survival-scaling-test-wrapper-failure.py','research/promote-survival-scaling-v36.py'}
out=ROOT/'research/ports/v36-production-before-test-wrapper-fix';assert not out.exists()
for p in sorted(closure):
    dest=(out/p).resolve();assert dest.is_relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dest)
(out/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,gpu_mismatch=False,passed_prefix_tests=95,failing_harness_test=1,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
print('Preserved exact harness failure and unchanged 95-test production prefix.')
