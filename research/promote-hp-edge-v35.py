"""Install only the native/PTX verified HP-edge candidate, then run UI acceptance."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=['research/detail-hp-edge-separated-native.json','research/detail-hp-edge-separated-ptx.json','research/detail-hp-edge-boundary-verification.json']
closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if '-separated-' in path:
        assert r['abi']=='detail_hp_edge_v35' and len(r['cases'])==39 and not r['not_run_cases']
        assert not r['cpu_trace_used_as_gpu_input']
    else:assert r['tests_run']==5 and r['skipped']==0
    closure.update(r['source_sha256'])
previous=json.loads((ROOT/'research/detail-survival-checkpoint.json').read_text(encoding='utf-8'))
assert previous['passed'] and all(sha(p)==h for p,h in previous['source_sha256'].items()),'Production changed since v34 acceptance.'
for path,field in [('research/detail-hp-edge-staged-coverage.json','source_sha256'),('research/detail-hp-edge-staged-favorites.json','compiler_source_sha256')]:
    inventory=json.loads((ROOT/path).read_text(encoding='utf-8'));assert all(sha(p)==h for p,h in inventory[field].items()),path
    closure.add(path);closure.update(inventory[field])
closure.update(['research/promote-hp-edge-v35.py','research/staging/v35/scripts/build-combat.py','research/staging/v35/scripts/build-detail-native.py','research/detail-hp-edge-separated-native.log','research/detail-hp-edge-separated-ptx.log','research/detail-hp-edge-boundary-tests.log','research/detail-hp-edge-api-fixture.json','research/detail-hp-edge-ui-fixture.json'])
archive=ROOT/'research/ports/v35-hp-edge-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    target=(archive/p).resolve();assert target.is_relative_to(archive.resolve());target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_hp_edge_v35',objective_complete=False,stage_only=True,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json'):
    shutil.copy2(ROOT/'research/staging/v35/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v35/scripts'/name,ROOT/'scripts'/name)
for source,target in [('verify-staged-hp-edge.py','verify-hp-edge.py'),('verify-staged-hp-edge-real.py','verify-hp-edge-real.py'),('verify-staged-hp-edge-namespace.py','verify-hp-edge-namespace.py')]:
    text=(ROOT/'scripts'/source).read_text(encoding='utf-8')
    if source=='verify-staged-hp-edge.py':
        needle="g=load('hp_edge_stage_loader','scripts/staged-hp-edge-runtime.py').install()"
        assert needle in text
        text=text.replace(needle,"import sys\nsys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
    text=text.replace('scripts/verify-staged-hp-edge.py','scripts/verify-hp-edge.py').replace('scripts/verify-staged-hp-edge-real.py','scripts/verify-hp-edge-real.py').replace('scripts/verify-staged-hp-edge-namespace.py','scripts/verify-hp-edge-namespace.py')
    text=text.replace("'scripts/staged-hp-edge-runtime.py',",'').replace('research/staging/v35/app/','app/').replace('stage_only=True','stage_only=False')
    text=text.replace('research/detail-hp-edge-staged-native.json','research/detail-hp-edge-native.json').replace('research/detail-hp-edge-staged-real-native.json','research/detail-hp-edge-real-native.json')
    (ROOT/'scripts'/target).write_text(text,encoding='utf-8')
boundary=(ROOT/'research/test_staged_hp_edge_boundaries.py').read_text(encoding='utf-8').replace('scripts/verify-staged-hp-edge.py','scripts/verify-hp-edge.py')
(ROOT/'tests/test_detail_hp_edge_boundary.py').write_text(boundary,encoding='utf-8')
test='''"""Whole-squad HP-edge acceptance through ordinary production modules."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
hp=load('production_hp_authored','scripts/verify-hp-edge.py')
real=load('production_hp_real','scripts/verify-hp-edge-real.py')
ns=load('production_hp_namespace','scripts/verify-hp-edge-namespace.py')
class HPEdgeGPU(unittest.TestCase):
    def verify(self,verifier,count):
        cases=list(verifier.fixtures());self.assertEqual(len(cases),count);device=hp.s.v.v.v.Cuda()
        try:
            for name,b,extra in cases:
                with self.subTest(name=name):self.assertTrue(verifier.compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_HP_transitions_and_notification_order(self):self.verify(hp,24)
    def test_actual_A2_Soline_and_Flora_whole_squads(self):self.verify(real,12)
    def test_self_HP_and_named_notifications_have_distinct_namespaces(self):self.verify(ns,3)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_hp_edge.py').write_text(test,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';text=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_survival')"
assert needle in text and 'test_detail_hp_edge' not in text
text=text.replace(needle,needle+"\n    modules.append('test_detail_hp_edge')\n    modules.append('test_detail_hp_edge_boundary')")
p.write_text(text,encoding='utf-8')
p=ROOT/'web/index.html';text=p.read_text(encoding='utf-8');needle='HP閾値をまたぐ発動・敵からのデバフ・座標などには未対応の条件が残っています。';assert needle in text
text=text.replace(needle,'HP閾値をまたぐ発動、到達回数、味方・隣接HPの通知にも対応します。敵からのデバフ・座標などには未対応の条件が残っています。');p.write_text(text,encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';j=json.loads(p.read_text(encoding='utf-8'));j['current_work']=dict(phase='v35 native/PTX HP39 + boundary5 accepted; production95/API/browser acceptance pending',objective_complete=False,staged_archive=str(archive.relative_to(ROOT)).replace('\\','/'));p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Installed verified v35 sources. Required next gates: normal95, API and browser; full all-effects goal remains active.')
