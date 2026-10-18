"""Install only a fully source-bound v37 candidate; production acceptance follows."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-cover-capacity-{kind}-{backend}.json' for kind in ('authored','real','cube','regression') for backend in ('native','ptx')]+['research/detail-cover-capacity-boundary-verification.json']
closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if 'boundary' in path:assert r['tests_run']==6 and not r['skipped']
    else:
        expected=15 if '-authored-' in path else 6 if '-real-' in path else 2 if '-cube-' in path else 74
        assert r['abi']=='detail_cover_capacity_v37' and len(r['cases'])==expected and not r['not_run_cases'] and not r['cpu_trace_used_as_gpu_input']
    closure.update(r['source_sha256'])
base=json.loads((ROOT/'research/detail-survival-scaling-checkpoint.json').read_text(encoding='utf-8'));assert base['passed'] and all(sha(p)==h for p,h in base['source_sha256'].items())
closure.update(['research/promote-cover-capacity-v37.py','research/staging/v37/scripts/build-combat.py','research/staging/v37/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v37-cover-capacity-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    out=(archive/p).resolve();assert out.is_relative_to(archive.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_cover_capacity_v37',objective_complete=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json'):shutil.copy2(ROOT/'research/staging/v37/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v37/scripts'/name,ROOT/'scripts'/name)
for source,target in [('scripts/verify-staged-cover-capacity.py','scripts/verify-cover-capacity.py'),('research/verify-cover-capacity-regressions.py','scripts/verify-cover-capacity-regressions.py'),('research/verify-cover-capacity-cube-carriers.py','scripts/verify-cover-capacity-cube-carriers.py')]:
    text=(ROOT/source).read_text(encoding='utf-8')
    needle="g=load('capacity_stage_runtime','scripts/staged-cover-capacity-runtime.py').install()"
    text=text.replace(needle,"import sys\nsys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
    text=text.replace('scripts/verify-staged-cover-capacity.py','scripts/verify-cover-capacity.py').replace('research/verify-cover-capacity-regressions.py','scripts/verify-cover-capacity-regressions.py')
    text=text.replace('research/verify-cover-capacity-cube-carriers.py','scripts/verify-cover-capacity-cube-carriers.py')
    text=text.replace("'scripts/staged-cover-capacity-runtime.py',",'').replace('research/staging/v37/app/','app/').replace('stage_only=True','stage_only=False')
    (ROOT/target).write_text(text,encoding='utf-8')
text=(ROOT/'research/test_staged_cover_capacity_boundaries.py').read_text(encoding='utf-8').replace('scripts/verify-staged-cover-capacity.py','scripts/verify-cover-capacity.py')
text=text.split("if __name__=='__main__':")[0]+"if __name__=='__main__':unittest.main()\n"
(ROOT/'tests/test_detail_cover_capacity_boundary.py').write_text(text,encoding='utf-8')
test='''"""Production whole-squad quantities and prior cover/HP/heal lifecycles."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_capacity','scripts/verify-cover-capacity.py')
reg=load('production_capacity_legacy','scripts/verify-cover-capacity-regressions.py')
cube=load('production_capacity_cubes','scripts/verify-cover-capacity-cube-carriers.py')
class CoverCapacityGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count);device=v.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,extra in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_authored_cover_capacity(self):self.verify(((v,*x) for x in v.fixtures()),15)
    def test_actual_Tia_cover_cube_owned_growth_and_positions(self):self.verify(((v,*x) for x in v.real_fixtures()),6)
    def test_cover_cube_on_Moran_and_A2(self):self.verify(((cube.cap,*x) for x in cube.fixtures()),2)
    def test_prior_cover_heal_HP_down_lifecycles(self):self.verify(reg.fixtures(),74)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_cover_capacity.py').write_text(test,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';text=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_survival_scaling_boundary')";assert needle in text
text=text.replace(needle,needle+"\n    modules.append('test_detail_cover_capacity')\n    modules.append('test_detail_cover_capacity_boundary')");p.write_text(text,encoding='utf-8')
p=ROOT/'web/index.html';text=p.read_text(encoding='utf-8');needle='残HPに応じた効果量と、破壊済み遮蔽物の抽選・復活にも対応します。';assert needle in text
text=text.replace(needle,needle+'発動者の最大HPを参照する遮蔽物HP増加にも対応します。');p.write_text(text,encoding='utf-8')
print('Installed v37. Required: focused production10, ordinary API/browser and immutable checkpoint. Full goal incomplete.')
