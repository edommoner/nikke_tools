"""Promote current 208-case/backend charge proofs; production acceptance follows."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-heal-charge-{group}-{backend}.json' for group in ('new','extra','legacy') for backend in ('native','ptx')]+['research/detail-heal-charge-cpu-reference.json','research/detail-heal-charge-cpu-squads.json','research/detail-heal-charge-extra-cpu.json','research/detail-heal-charge-cpu-legacy.json','research/detail-heal-charge-boundaries.json','research/detail-heal-charge-coverage.json','research/detail-heal-charge-favorites.json']
closure=set(reports)
for p in reports:
    r=json.loads((ROOT/p).read_text(encoding='utf-8'));assert r.get('passed',True),p
    hashes=r.get('source_sha256',r.get('compiler_source_sha256',{}));assert hashes and all(sha(f)==h for f,h in hashes.items()),p;closure.update(hashes)
    if r.get('group') in ('new','extra','legacy'):
        assert r['abi']=='detail_heal_charge_v42' and len(r['cases'])=={'new':20,'extra':10,'legacy':178}[r['group']] and r['not_run_cases']==0 and not r['cpu_trace_used_as_gpu_input']
        if r['group']!='legacy':assert all(x['workspace_bytes']==1088520 for x in r['cases'])
        if r['group']=='extra':
            edge=next(x for x in r['cases'] if x['name']=='charge-extra-release-inside-HP-edge');assert edge['GPU_immediate_release_HP_gain']>0 and abs(edge['GPU_immediate_release_HP_gain']-edge['independent_ATK_cap_expected_HP_gain'])<1e-6
    elif p.endswith('-cpu-reference.json'):assert len(r['cases'])==31
    elif p.endswith('-cpu-squads.json'):
        assert len(r['cases'])==20
        assert next(x for x in r['cases'] if x['name']=='raw-charge-Rem-sharing')['checks']['nontrivial_healing_share_really_active']
        assert next(x for x in r['cases'] if x['name']=='raw-charge-Marciana-storage')['checks']['overheal_reserve_really_filled']
    elif p.endswith('-extra-cpu.json'):assert len(r['cases'])==10
    elif p.endswith('-cpu-legacy.json'):assert len(r['cases'])==178
    elif p.endswith('-boundaries.json'):assert r['tests_run']==10 and not r['gpu_loaded']
    elif p.endswith('-coverage.json'):assert (r['supported'],r['characters'])==(162,203)
    elif p.endswith('-favorites.json'):assert (r['accepted_contexts'],r['total_contexts'])==(639,812)
cp_path='research/detail-heal-sharing-checkpoint.json';cp=json.loads((ROOT/cp_path).read_text(encoding='utf-8'));assert cp['passed'] and all(sha(p)==h for p,h in cp['source_sha256'].items())
# Prepare and syntax-check all text edits before copying any production file.
edits={}
p='app/engine_compat.py';s=(ROOT/p).read_text(encoding='utf-8');needle='    install_heal_sharing()\n';assert s.count(needle)==1 and 'install_heal_charge' not in s;edits[p]=s.replace(needle,needle+'    from heal_charge_compat import install as install_heal_charge\n    install_heal_charge()\n')
s=(ROOT/'research/heal-charge-fixtures.py').read_text(encoding='utf-8').replace('import importlib.util\n','import importlib.util,sys\n');needle="g=load('charge_runtime','scripts/staged-heal-charge-runtime.py').install()";assert s.count(needle)==1
edits['scripts/heal-charge-fixtures.py']=s.replace(needle,"sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
edits['scripts/heal-charge-extra-fixtures.py']=(ROOT/'research/heal-charge-extra-fixtures.py').read_text(encoding='utf-8')
mapping={'research/heal-charge-fixtures.py':'scripts/heal-charge-fixtures.py','research/heal-charge-extra-fixtures.py':'scripts/heal-charge-extra-fixtures.py','research/verify-heal-charge.py':'scripts/verify-heal-charge.py','research/verify-heal-charge-extra.py':'scripts/verify-heal-charge-extra.py'}
for source,target in [('research/verify-heal-charge.py','scripts/verify-heal-charge.py'),('research/verify-heal-charge-extra.py','scripts/verify-heal-charge-extra.py')]:
    s=(ROOT/source).read_text(encoding='utf-8')
    for a,b in mapping.items():s=s.replace(a,b)
    edits[target]=s.replace('research/staging/v42/app/','app/').replace("ROOT/'research/staging/v42/app'","ROOT/'app'").replace('stage_only=True','stage_only=False')
s=(ROOT/'research/probe-heal-charge-boundaries.py').read_text(encoding='utf-8').replace('research/heal-charge-fixtures.py','scripts/heal-charge-fixtures.py');edits['tests/test_detail_heal_charge_boundary.py']=s[:s.index("if __name__=='__main__':")]+"if __name__=='__main__':unittest.main()\n"
edits['tests/test_detail_heal_charge.py']='''"""Production received-healing accumulation, discharge and raw Delta squads."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('production_charge','scripts/verify-heal-charge.py');extra=load('production_charge_extra','scripts/verify-heal-charge-extra.py')
class HealChargeGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count);device=m.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,x in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,x,'native')['passed'])
        finally:device.close()
    def test_authored_received_healing_capacity_and_release(self):self.verify((x for x in m.fixtures('new') if not x[1].startswith('raw-')),16)
    def test_raw_Delta_Crown_Rem_and_Marciana(self):self.verify((x for x in m.fixtures('new') if x[1].startswith('raw-')),4)
    def test_colliding_lifetimes_capacity_and_nested_release(self):
        # Use the standalone driver's same-frame HP-gain control as well.
        self.verify(((extra,*x) for x in extra.extra.fixtures(extra.m.d)),10)
if __name__=='__main__':unittest.main()
'''
# The extra verifier exposes a library compare function below. Keep the
# independent immediate-release control in production unittest execution too.
p='tests/test_detail_healing_storage_boundary.py';s=(ROOT/p).read_text(encoding='utf-8');start=s.index('    def test_other_healing_families_still_reject(self):');end=s.index('    def test_zero_negative',start)
edits[p]=s[:start]+'''    def test_instant_storage_form_still_rejects(self):
        with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(v.E('wrong type','instant','heal_overcharge_store',5),v.N[0])])
'''+s[end:]
p='tests/test_detail_heal_sharing_boundary.py';s=(ROOT/p).read_text(encoding='utf-8');start=s.index('    def test_wrong_type_and_separate_storage_families_rejected(self):');end=s.index('    def test_CPU_extension',start)
edits[p]=s[:start]+'''    def test_wrong_healing_effect_types_rejected(self):
        for e in [v.E('wrong type','instant','heal_split',1),v.E('wrong type','instant','heal_overcharge_store_atk_pct',1),v.B('wrong type','heal_overcharge_discharge',1,target_effect='pool')]:
            with self.assertRaises(g.UnsupportedDetail):g.compile_effects(self.compiled['program']['chars'],[(e,v.N[0])])
'''+s[end:]
p='scripts/verify-normal-detail.py';s=(ROOT/p).read_text(encoding='utf-8');needle="    modules.append('test_detail_heal_sharing_boundary')";assert s.count(needle)==1;edits[p]=s.replace(needle,needle+"\n    modules.append('test_detail_heal_charge')\n    modules.append('test_detail_heal_charge_boundary')")
p='web/index.html';s=(ROOT/p).read_text(encoding='utf-8');needle='回復分配は、効果の重複による取り分とHP変化の順序を含む参照モデルで計算します。';assert s.count(needle)==1;edits[p]=s.replace(needle,needle+'受けた回復の蓄積・蓄積上限の補正・期限終了時の全体回復にも対応します。')
for p,s in edits.items():
    if p.endswith('.py'):compile(s,p,'exec')
closure.update([cp_path,'research/promote-heal-charge-v42.py','research/verify-heal-charge-backend.py','research/staging/v42/stage-base.json','research/staging/v42/scripts/build-combat.py','research/staging/v42/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v42-heal-charge-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    out=(archive/p).resolve();assert out.is_relative_to(archive.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_heal_charge_v42',objective_complete=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ['detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json','heal_charge_compat.py']:shutil.copy2(ROOT/'research/staging/v42/app'/name,ROOT/'app'/name)
for name in ['build-combat.py','build-detail-native.py']:shutil.copy2(ROOT/'research/staging/v42/scripts'/name,ROOT/'scripts'/name)
for p,s in edits.items():(ROOT/p).write_text(s,encoding='utf-8')
print('v42 installed from accepted stage. Production tests and normal API/browser acceptance remain required.')
