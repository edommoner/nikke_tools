"""Promote the exact blocked-stage correction after both complete GPU suites."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();closure=set()
for backend in ('native','ptx'):
    for label,count in [('burst',None),('heal',3),('full',42),('regression',80),('long',4)]+([('repeated-long',4)] if backend=='native' else []):
        path=f'research/detail-survival-burstfix-{backend}-{label}.json';r=json.loads((ROOT/path).read_text(encoding='utf-8'))
        assert r['passed'] and not r['not_run_cases'] and r['abi']=='detail_survival_v34',path
        assert len(r['cases'])==count if count is not None else len(r['cases'])>=48
        for p,h in r['source_sha256'].items():assert sha(p)==h,(path,p)
        closure.update(r['source_sha256']);closure.add(path)
archive=ROOT/'research/ports/v34-burstfix-staged-verified';assert not archive.exists()
for p in sorted(closure):
    target=archive/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_survival_v34',objective_complete=False,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json'):
    shutil.copy2(ROOT/'research/staging/v34/app'/name,ROOT/'app'/name)
assert 'temporarily use CPU' not in (ROOT/'app/detail_gpu.py').read_text(encoding='utf-8')
s=(ROOT/'scripts/verify-staged-survival.py').read_text(encoding='utf-8')
s=s.replace("loader=load('survival_staging_loader','scripts/staged-survival-runtime.py');g=loader.install()","sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
s=s.replace('research/staging/v34/app/','app/').replace("'scripts/staged-survival-runtime.py',",'')
s=s.replace('scripts/verify-staged-survival.py','scripts/verify-survival-detail.py').replace('stage_only=True','stage_only=False').replace('research/detail-staged-survival-verification.json','research/detail-survival-verification.json')
s=s.replace('Whole-squad staged GPU down/revive parity against the explicit CPU bridge.','Whole-squad production GPU down/revive parity against the explicit CPU bridge.').replace('The normal v33 application is untouched.','This verifier imports the ordinary application modules.')
(ROOT/'scripts/verify-survival-detail.py').write_text(s,encoding='utf-8')
shutil.copy2(ROOT/'research/survival-test-template.py',ROOT/'tests/test_detail_survival.py')
print('Promoted the verified burst-wait correction and removed the temporary CPU guard; ordinary acceptance still required.')
