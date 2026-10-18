"""Promote only current 153-case/backend storage proofs and CPU/boundary evidence."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-healing-storage-{kind}-{backend}.json' for kind in ('authored','extra','real','regression') for backend in ('native','ptx')]+['research/detail-healing-storage-boundary-verification.json','research/detail-healing-storage-cpu-reference.json','research/detail-healing-storage-cpu-squads.json','research/detail-healing-storage-cpu-legacy.json'];closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if '-boundary-' in path:assert r['tests_run']==7 and not r['skipped']
    elif path.endswith('-cpu-reference.json'):assert len(r['cases'])==21
    elif path.endswith('-cpu-squads.json'):
        assert len(r['cases'])==13
        case=next(x for x in r['cases'] if x['name']=='raw-storage-마르차나');assert case['checks']['same_cast_S2_heal_fills_storage'] and case['checks']['GPU_definitions_put_storage_before_S2_heal']
    elif path.endswith('-cpu-legacy.json'):assert len(r['cases'])==124
    else:
        count=8 if '-authored-' in path else 16 if '-extra-' in path else 5 if '-real-' in path else 124
        assert r['abi']=='detail_healing_storage_v40' and len(r['cases'])==count and not r['not_run_cases'] and not r['cpu_trace_used_as_gpu_input']
        if '-extra-' in path:
            assert r['actual_workspace_bytes_per_squad']==[1078280]
            assert all(bool(x['cpu_revives']) for x in r['cases'] if x['name'].endswith('-revives'))
    closure.update(r['source_sha256'])
base=json.loads((ROOT/'research/detail-outgoing-healing-checkpoint.json').read_text(encoding='utf-8'));assert base['passed'] and all(sha(p)==h for p,h in base['source_sha256'].items())
closure.update(['research/promote-healing-storage-v40.py','research/verify-healing-storage-backend.py','research/staging/v40/scripts/build-combat.py','research/staging/v40/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v40-healing-storage-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    out=(archive/p).resolve();assert out.is_relative_to(archive.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_healing_storage_v40',objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json','healing_storage_compat.py'):shutil.copy2(ROOT/'research/staging/v40/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v40/scripts'/name,ROOT/'scripts'/name)
p=ROOT/'app/engine_compat.py';s=p.read_text(encoding='utf-8');needle='    install_outgoing_healing()\n';assert needle in s and 'install_healing_storage' not in s;s=s.replace(needle,needle+'    from healing_storage_compat import install as install_healing_storage\n    install_healing_storage()\n');p.write_text(s,encoding='utf-8')
# Pure authored definitions are useful in ordinary tests without a staged loader
# or the CPU preflight CLI's execution path.
s=(ROOT/'research/probe-healing-storage-squads.py').read_text(encoding='utf-8');head=s.split('\nrows=[];fill=')[0];fixtures=s[s.index('def fixtures():'):s.index('\ndef main():')]
head=head.replace("g=load('storage_runtime','scripts/staged-healing-storage-runtime.py').install()","sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
(ROOT/'scripts/healing-storage-fixtures.py').write_text(head+'\n'+fixtures+'\n',encoding='utf-8')
mapping={'scripts/verify-staged-healing-storage.py':'scripts/verify-healing-storage.py','research/verify-healing-storage-extra.py':'scripts/verify-healing-storage-extra.py','research/healing-storage-extra-fixtures.py':'scripts/healing-storage-extra-fixtures.py','research/verify-healing-storage-regressions.py':'scripts/verify-healing-storage-regressions.py','research/probe-healing-storage-squads.py':'scripts/healing-storage-fixtures.py'}
for source,target in list(mapping.items())[:-1]:
    text=(ROOT/source).read_text(encoding='utf-8')
    if source.endswith('regressions.py'):
        text=text.replace('import argparse,hashlib,importlib.util,json\n','import argparse,hashlib,importlib.util,json,sys\n')
        needle="g=load('storage_regression_runtime','scripts/staged-healing-storage-runtime.py').install()";assert needle in text;text=text.replace(needle,"sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
    for old,new in mapping.items():text=text.replace(old,new)
    text=text.replace("'scripts/staged-healing-storage-runtime.py',",'').replace('research/staging/v40/app/','app/').replace('stage_only=True','stage_only=False')
    (ROOT/target).write_text(text,encoding='utf-8')
text=(ROOT/'research/test_staged_healing_storage_boundaries.py').read_text(encoding='utf-8').replace('scripts/verify-staged-healing-storage.py','scripts/verify-healing-storage.py');text=text.split("if __name__=='__main__':")[0]+"if __name__=='__main__':unittest.main()\n";(ROOT/'tests/test_detail_healing_storage_boundary.py').write_text(text,encoding='utf-8')
test='''"""Production stored-healing lifecycle, quantities and prior124 GPU paths."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_healing_storage','scripts/verify-healing-storage.py')
extra=load('production_storage_extra','scripts/healing-storage-extra-fixtures.py')
reg=load('production_storage_legacy','scripts/verify-healing-storage-regressions.py')
class HealingStorageGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count);device=v.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,x in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,x,'native')['passed'])
        finally:device.close()
    def test_authored_storage_frames(self):self.verify(((v,*x) for x in v.d.fixtures() if not x[0].startswith('raw-')),8)
    def test_overlap_snapshots_HP_predicates_and_revival(self):self.verify(((v,*x) for x in extra.fixtures()),16)
    def test_actual_raw_carriers_favorite_and_parts(self):self.verify(((v,*x) for x in v.d.fixtures() if x[0].startswith('raw-')),5)
    def test_prior124_outgoing_HP_cover_decoy_survival(self):self.verify(reg.fixtures(),124)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_healing_storage.py').write_text(test,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';s=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_outgoing_healing_boundary')";assert needle in s;s=s.replace(needle,needle+"\n    modules.append('test_detail_healing_storage')\n    modules.append('test_detail_healing_storage_boundary')");p.write_text(s,encoding='utf-8')
p=ROOT/'web/index.html';s=p.read_text(encoding='utf-8');needle='与える回復量増加とヒーリングキューブにも対応します。';assert needle in s;s=s.replace(needle,needle+'余剰回復の保存・被ダメージやHP消費による取り崩しにも対応します。');p.write_text(s,encoding='utf-8')
print('Installed v40 sources; focused production11 and ordinary API/browser acceptance remain required. Full goal incomplete.')
