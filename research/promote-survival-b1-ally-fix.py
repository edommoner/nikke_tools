"""Promote the B1 composition correction after focused native/PTX acceptance."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();closure=set()
ap=argparse.ArgumentParser();ap.add_argument('--native-candidate',action='store_true');args=ap.parse_args()
for backend in (('native',) if args.native_candidate else ('native','ptx')):
    for label,count in [('heal',3),('full',49)]+([('repeated-long',4)] if backend=='native' else []):
        path=f'research/detail-survival-b1-{backend}-{label}.json';r=json.loads((ROOT/path).read_text(encoding='utf-8'))
        assert r['passed'] and r['focused_b1'] and not r['not_run_cases'] and len(r['cases'])==count,path
        assert r['abi']=='detail_survival_v34'
        for p,h in r['source_sha256'].items():assert sha(p)==h,(path,p)
        closure.update(r['source_sha256']);closure.add(path)
if not args.native_candidate:
    archive=ROOT/'research/ports/v34-survival-final-staged-verified';assert not archive.exists()
    for p in sorted(closure):
        out=archive/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
    (archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_survival_v34',objective_complete=False,scope='Final B1/count-limited-target correction: affected survival cases and long repeated lethal battles; complete ordinary suite is the next gate.',files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json'):
    src='research/staging/v34/app/'+name;dst='app/'+name
    if sha(src)!=sha(dst):shutil.copy2(ROOT/src,ROOT/dst)
assert 'temporarily use CPU' not in (ROOT/'app/detail_gpu.py').read_text(encoding='utf-8')
s=(ROOT/'scripts/verify-staged-survival.py').read_text(encoding='utf-8')
s=s.replace("loader=load('survival_staging_loader','scripts/staged-survival-runtime.py');g=loader.install()","sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
s=s.replace('research/staging/v34/app/','app/').replace("'scripts/staged-survival-runtime.py',",'')
s=s.replace('scripts/verify-staged-survival.py','scripts/verify-survival-detail.py').replace('stage_only=True','stage_only=False').replace('research/detail-staged-survival-verification.json','research/detail-survival-verification.json')
s=s.replace('Whole-squad staged GPU down/revive parity against the explicit CPU bridge.','Whole-squad production GPU down/revive parity against the explicit CPU bridge.').replace('The normal v33 application is untouched.','This verifier imports the ordinary application modules.')
target=ROOT/'scripts/verify-survival-detail.py'
if target.read_text(encoding='utf-8')!=s:target.write_text(s,encoding='utf-8')
if sha('research/survival-test-template.py')!=sha('tests/test_detail_survival.py'):shutil.copy2(ROOT/'research/survival-test-template.py',ROOT/'tests/test_detail_survival.py')
print('Prepared the native-verified candidate; PTX and complete normal acceptance remain.' if args.native_candidate else 'Archived both verified backends; unchanged production files were not rewritten during normal acceptance.')
