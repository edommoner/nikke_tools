"""Promote only source-bound 178-case/backend proofs, then verify production."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-heal-sharing-{group}-{backend}.json' for group in ('new','legacy') for backend in ('native','ptx')]+['research/detail-heal-sharing-cpu-reference.json','research/detail-heal-sharing-cpu-squads.json','research/detail-heal-sharing-cpu-legacy.json','research/detail-heal-sharing-boundaries.json','research/detail-heal-sharing-coverage.json','research/detail-heal-sharing-favorites.json']
closure=set(reports)
for p in reports:
    r=json.loads((ROOT/p).read_text(encoding='utf-8'));assert r.get('passed',True),p
    hashes=r.get('source_sha256',r.get('compiler_source_sha256',{}));assert hashes and all(sha(f)==h for f,h in hashes.items()),p;closure.update(hashes)
    if p.endswith(('-new-native.json','-new-ptx.json','-legacy-native.json','-legacy-ptx.json')):
        count=25 if '-new-' in p else 153
        assert r['abi']=='detail_heal_sharing_v41' and len(r['cases'])==count and r['not_run_cases']==0 and not r['cpu_trace_used_as_gpu_input']
    elif p.endswith('-cpu-reference.json'):assert len(r['cases'])==19
    elif p.endswith('-cpu-squads.json'):
        assert len(r['cases'])==25
        for name,check in [('sharing-nested-HP-heal','nested_heal_really_executed'),('raw-sharing-Nayuta','raw_Nayuta_links_really_active'),('raw-sharing-two-RL','actual_Rem_8_links')]:assert next(x for x in r['cases'] if x['name']==name)['checks'][check]
    elif p.endswith('-cpu-legacy.json'):assert len(r['cases'])==153
    elif p.endswith('-boundaries.json'):assert r['tests_run']==5 and not r['gpu_loaded']
    elif p.endswith('-coverage.json'):assert (r['supported'],r['characters'])==(161,203)
    elif p.endswith('-favorites.json'):assert (r['accepted_contexts'],r['total_contexts'])==(635,812)
cp_path='research/detail-healing-storage-checkpoint.json';cp=json.loads((ROOT/cp_path).read_text(encoding='utf-8'));assert cp['passed'] and all(sha(p)==h for p,h in cp['source_sha256'].items())
closure.update([cp_path,'research/promote-heal-sharing-v41.py','research/staging/v41/stage-base.json','research/staging/v41/scripts/build-combat.py','research/staging/v41/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v41-heal-sharing-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    out=(archive/p).resolve();assert out.is_relative_to(archive.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_heal_sharing_v41',objective_complete=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json','heal_sharing_compat.py'):shutil.copy2(ROOT/'research/staging/v41/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v41/scripts'/name,ROOT/'scripts'/name)
p=ROOT/'app/engine_compat.py';s=p.read_text(encoding='utf-8');needle='    install_healing_storage()\n';assert needle in s and 'install_heal_sharing' not in s
s=s.replace(needle,needle+'    from heal_sharing_compat import install as install_heal_sharing\n    install_heal_sharing()\n');p.write_text(s,encoding='utf-8')
s=(ROOT/'research/heal-sharing-fixtures.py').read_text(encoding='utf-8').replace('import importlib.util\n','import importlib.util,sys\n').replace("g=load('sharing_runtime','scripts/staged-heal-sharing-runtime.py').install()","sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
(ROOT/'scripts/heal-sharing-fixtures.py').write_text(s,encoding='utf-8')
s=(ROOT/'research/verify-heal-sharing.py').read_text(encoding='utf-8').replace('research/heal-sharing-fixtures.py','scripts/heal-sharing-fixtures.py').replace('research/verify-heal-sharing.py','scripts/verify-heal-sharing.py').replace('research/staging/v41/app/','app/').replace("ROOT/'research/staging/v41/app'","ROOT/'app'").replace('stage_only=True','stage_only=False')
(ROOT/'scripts/verify-heal-sharing.py').write_text(s,encoding='utf-8')
s=(ROOT/'research/probe-heal-sharing-boundaries.py').read_text(encoding='utf-8').replace('research/heal-sharing-fixtures.py','scripts/heal-sharing-fixtures.py');s=s[:s.index("if __name__=='__main__':")]+"if __name__=='__main__':unittest.main()\n"
(ROOT/'tests/test_detail_heal_sharing_boundary.py').write_text(s,encoding='utf-8')
test='''"""Production recovery sharing, actual carriers and full squad parity."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('production_sharing',ROOT/'scripts/verify-heal-sharing.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class HealSharingGPU(unittest.TestCase):
    def verify(self,raw,count):
        cases=[x for x in m.fixtures('new') if x[1].startswith('raw-')==raw];self.assertEqual(len(cases),count);device=m.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,x in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,x,'native')['passed'])
        finally:device.close()
    def test_authored_weighted_shares_and_nested_HP_events(self):self.verify(False,20)
    def test_actual_Rem_Nayuta_Crown_and_storage(self):self.verify(True,5)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_heal_sharing.py').write_text(test,encoding='utf-8')
p=ROOT/'tests/test_detail_healing_storage_boundary.py';s=p.read_text(encoding='utf-8').replace('(-1,74.5,75)','(-1,74.5,10000)').replace(",v.B('separate','heal_split',1)",'');p.write_text(s,encoding='utf-8')
p=ROOT/'tests/test_detail_outgoing_healing_boundary.py';s=p.read_text(encoding='utf-8').replace('(-1,73.5,74)','(-1,73.5,10000)');p.write_text(s,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';s=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_healing_storage_boundary')";assert needle in s;s=s.replace(needle,needle+"\n    modules.append('test_detail_heal_sharing')\n    modules.append('test_detail_heal_sharing_boundary')");p.write_text(s,encoding='utf-8')
p=ROOT/'web/index.html';s=p.read_text(encoding='utf-8');needle='余剰回復の保存・被ダメージやHP消費による取り崩しにも対応します。';assert needle in s;s=s.replace(needle,needle+'回復分配は、効果の重複による取り分とHP変化の順序を含む参照モデルで計算します。');p.write_text(s,encoding='utf-8')
print('v41 installed from accepted stage. Production tests and ordinary API/browser acceptance still required.')
