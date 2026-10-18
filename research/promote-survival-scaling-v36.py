"""Promote only source-bound, independently verified native/PTX v36 artifacts."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-survival-scaling-unitfix-{kind}-{backend}.json' for kind in ('authored','real') for backend in ('native','ptx')]
reports+=['research/detail-survival-scaling-boundary-verification.json']
reports+=['research/detail-survival-scaling-legacy-ptx.json']
closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if 'legacy' in path:
        assert r['abi']=='detail_survival_scaling_v36' and len(r['cases'])==r['planned_cases'] and r['planned_cases']>=64 and not r['not_run_cases']
    elif 'unitfix' in path:
        assert r['abi']=='detail_survival_scaling_v36' and len(r['cases'])==(28 if '-authored-' in path else 12)
        assert not r['not_run_cases'] and not r['cpu_trace_used_as_gpu_input']
    else:assert r['tests_run']==11 and r['skipped']==0
    closure.update(r['source_sha256'])
previous=json.loads((ROOT/'research/detail-hp-edge-checkpoint.json').read_text(encoding='utf-8'))
assert previous['passed'] and all(sha(p)==h for p,h in previous['source_sha256'].items()),'Production changed since v35 acceptance.'
closure.update(['research/promote-survival-scaling-v36.py','research/staging/v36/scripts/build-combat.py','research/staging/v36/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v36-survival-scaling-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    target=(archive/p).resolve();assert target.is_relative_to(archive.resolve());target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_survival_scaling_v36',objective_complete=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json','survival_scaling_compat.py'):
    shutil.copy2(ROOT/'research/staging/v36/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v36/scripts'/name,ROOT/'scripts'/name)
p=ROOT/'app/engine_compat.py';text=p.read_text(encoding='utf-8');needle='    install_survival()';assert needle in text
text=text.replace(needle,needle+'\n    from survival_scaling_compat import install as install_survival_scaling\n    install_survival_scaling()');p.write_text(text,encoding='utf-8')
p=ROOT/'server.mjs';text=p.read_text(encoding='utf-8');needle=".update(readFileSync(path.join(root, 'app/survival_compat.py')))";assert needle in text
text=text.replace(needle,needle+".update(readFileSync(path.join(root, 'app/survival_scaling_compat.py')))");p.write_text(text,encoding='utf-8')
for source,target in [('scripts/verify-staged-survival-scaling.py','scripts/verify-survival-scaling.py'),('research/verify-survival-scaling-real.py','scripts/verify-survival-scaling-real.py')]:
    text=(ROOT/source).read_text(encoding='utf-8')
    needle="g=load('scaling_stage_loader','scripts/staged-survival-scaling-runtime.py').install()"
    text=text.replace(needle,"sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
    text=text.replace('scripts/verify-staged-survival-scaling.py','scripts/verify-survival-scaling.py').replace('research/verify-survival-scaling-real.py','scripts/verify-survival-scaling-real.py')
    text=text.replace("'scripts/staged-survival-scaling-runtime.py',",'').replace('research/staging/v36/app/','app/').replace('stage_only=True','stage_only=False')
    (ROOT/target).write_text(text,encoding='utf-8')
text=(ROOT/'research/test_staged_survival_scaling_boundaries.py').read_text(encoding='utf-8')
start="sp=importlib.util.spec_from_file_location('survival_scaling_test_loader',ROOT/'scripts/staged-survival-scaling-runtime.py');loader=importlib.util.module_from_spec(sp);sp.loader.exec_module(loader);g=loader.install()"
assert start in text
text=text.replace(start,"import sys\nsys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport engine_compat as loader\nimport detail_gpu as g")
(ROOT/'tests/test_detail_survival_scaling_boundary.py').write_text(text,encoding='utf-8')
test='''"""Full squads through production v36, including raw Moran/Biscuit and owned gear."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_scaling_authored','scripts/verify-survival-scaling.py')
real=load('production_scaling_actual','scripts/verify-survival-scaling-real.py')
class SurvivalScalingGPU(unittest.TestCase):
    def verify(self,verifier,count):
        cases=list(verifier.fixtures());self.assertEqual(len(cases),count);device=v.s.v.v.v.Cuda()
        try:
            for name,b,extra in cases:
                with self.subTest(name=name):
                    compare=verifier.compare if hasattr(verifier,'compare') else verifier.v.compare
                    self.assertTrue(compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_lost_HP_and_cover_revival(self):self.verify(v,28)
    def test_actual_Moran_Biscuit_squads_and_growth(self):self.verify(real,12)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_survival_scaling.py').write_text(test,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';text=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_hp_edge_boundary')";assert needle in text
text=text.replace(needle,needle+"\n    modules.append('test_detail_survival_scaling')\n    modules.append('test_detail_survival_scaling_boundary')")
text=text.replace("'app/survival_compat.py',","'app/survival_compat.py','app/survival_scaling_compat.py',")
p.write_text(text,encoding='utf-8')
p=ROOT/'web/index.html';text=p.read_text(encoding='utf-8');needle='HP閾値をまたぐ発動、到達回数、味方・隣接HPの通知にも対応します。';assert needle in text
text=text.replace(needle,needle+'残HPに応じた効果量と、破壊済み遮蔽物の抽選・復活にも対応します。');p.write_text(text,encoding='utf-8')
print('Installed v36; production suite, ordinary API/browser and checkpoint remain required. Full goal incomplete.')
