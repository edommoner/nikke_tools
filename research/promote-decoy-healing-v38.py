"""Promote only independently verified decoy-healing native/PTX sources."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-decoy-healing-{kind}-{backend}.json' for kind in ('authored','real','regression') for backend in ('native','ptx')]+['research/detail-decoy-healing-boundary-verification.json'];closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if 'boundary' in path:assert r['tests_run']==7 and not r['skipped']
    else:assert r['abi']=='detail_decoy_healing_v38' and len(r['cases'])==(21 if '-authored-' in path else 7 if '-real-' in path else 73) and not r['not_run_cases'] and not r['cpu_trace_used_as_gpu_input']
    closure.update(r['source_sha256'])
base=json.loads((ROOT/'research/detail-cover-capacity-checkpoint.json').read_text(encoding='utf-8'));assert base['passed'] and all(sha(p)==h for p,h in base['source_sha256'].items())
closure.update(['research/promote-decoy-healing-v38.py','research/staging/v38/scripts/build-combat.py','research/staging/v38/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v38-decoy-healing-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    out=(archive/p).resolve();assert out.is_relative_to(archive.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_decoy_healing_v38',objective_complete=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json'):shutil.copy2(ROOT/'research/staging/v38/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v38/scripts'/name,ROOT/'scripts'/name)
for source,target in [('scripts/verify-staged-decoy-healing.py','scripts/verify-decoy-healing.py'),('research/verify-decoy-healing-regressions.py','scripts/verify-decoy-healing-regressions.py')]:
    text=(ROOT/source).read_text(encoding='utf-8');needle="g=load('decoy_stage_runtime','scripts/staged-decoy-healing-runtime.py').install()"
    text=text.replace(needle,"sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
    text=text.replace('scripts/verify-staged-decoy-healing.py','scripts/verify-decoy-healing.py').replace('research/verify-decoy-healing-regressions.py','scripts/verify-decoy-healing-regressions.py').replace("'scripts/staged-decoy-healing-runtime.py',",'').replace('research/staging/v38/app/','app/').replace('stage_only=True','stage_only=False')
    (ROOT/target).write_text(text,encoding='utf-8')
text=(ROOT/'research/test_staged_decoy_healing_boundaries.py').read_text(encoding='utf-8').replace('scripts/verify-staged-decoy-healing.py','scripts/verify-decoy-healing.py');text=text.split("if __name__=='__main__':")[0]+"if __name__=='__main__':unittest.main()\n";(ROOT/'tests/test_detail_decoy_healing_boundary.py').write_text(text,encoding='utf-8')
test='''"""Whole-squad and named decoy state through ordinary production modules."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_decoy_heals','scripts/verify-decoy-healing.py')
reg=load('production_decoy_legacy','scripts/verify-decoy-healing-regressions.py')
class DecoyHealingGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count);device=v.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,extra in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_authored_decoy_frames_and_healing(self):self.verify(((v,*x) for x in v.fixtures()),21)
    def test_actual_Rei_skills_owned_growth_and_down_revival(self):self.verify(((v,*x) for x in v.real_fixtures()),7)
    def test_prior_layers_HP_cover_and_survival(self):self.verify(reg.fixtures(),73)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_decoy_healing.py').write_text(test,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';text=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_cover_capacity_boundary')";assert needle in text;text=text.replace(needle,needle+"\n    modules.append('test_detail_decoy_healing')\n    modules.append('test_detail_decoy_healing_boundary')");p.write_text(text,encoding='utf-8')
p=ROOT/'web/index.html';text=p.read_text(encoding='utf-8');needle='発動者の最大HPを参照する遮蔽物HP増加にも対応します。';assert needle in text;text=text.replace(needle,needle+'デコイの残量回復にも対応します。');p.write_text(text,encoding='utf-8')
print('Installed v38. Required: focused production10, ordinary API/browser and checkpoint. Full objective remains incomplete.')
