"""Promote only the exact staged binaries which passed both full backends."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
closure=set()
for backend in ('native','ptx'):
    for label,count in (('heal',3),('full',39),('regression',80),('long',4)):
        path=f'research/detail-staged-survival-{backend}-{label}.json'
        r=json.loads((ROOT/path).read_text(encoding='utf-8'))
        assert r['passed'] and len(r['cases'])==count and not r['not_run_cases'],path
        assert r['abi']=='detail_survival_v34'
        for p,h in r['source_sha256'].items():assert sha(p)==h,(path,p)
        closure.update(r['source_sha256']);closure.add(path)
path='research/detail-staged-survival-repeated-long.json'
r=json.loads((ROOT/path).read_text(encoding='utf-8'))
assert r['passed'] and len(r['cases'])==4 and not r['not_run_cases'] and all(x['positive_control'] for x in r['cases'])
for p,h in r['source_sha256'].items():assert sha(p)==h,(path,p)
closure.update(r['source_sha256']);closure.add(path)
assert (ROOT/'research/ports/v33/archive-manifest.json').exists()
archive=ROOT/'research/ports/v34-staged-verified'
assert not archive.exists(),'Verified stage archives are immutable.'
for p in sorted(closure):
    target=archive/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_survival_v34',objective_complete=False,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json','survival_compat.py'):
    shutil.copy2(ROOT/'research/staging/v34/app'/name,ROOT/'app'/name)
path=ROOT/'app/engine_compat.py';s=path.read_text(encoding='utf-8');needle='def install():\n    from calculator.buff_manager import BuffManager'
assert needle in s and 'install_survival' not in s
s=s.replace(needle,'def install():\n    from survival_compat import install as install_survival\n    install_survival()\n    from calculator.buff_manager import BuffManager')
path.write_text(s,encoding='utf-8')
path=ROOT/'server.mjs';s=path.read_text(encoding='utf-8')
old=".update(readFileSync(path.join(root, 'app/engine_compat.py')))"
assert old in s and "path.join(root, 'app/survival_compat.py')" not in s
s=s.replace(old,old+".update(readFileSync(path.join(root, 'app/survival_compat.py')))")
path.write_text(s,encoding='utf-8')
path=ROOT/'tests/test_detail_incoming.py';s=path.read_text(encoding='utf-8')
s=s.replace('def test_true_down_rejects_entire_result_and_context_recovers(self):','def test_true_down_matches_cpu_and_context_recovers(self):')
old="   with self.assertRaisesRegex(v.v.g.UnsupportedDetail,'lethal incoming hit'):v.v.g.evaluate_full(d,v.v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')"
new="   gpu=v.v.g.evaluate_full(d,v.v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')\n   cpu=v.v.a.evaluate(b)\n   self.assertTrue(v.v.v.resolve_verification(gpu,cpu)['compute']['cpu_verification']['matched'])\n   self.assertTrue(gpu['_down_mask'])"
assert old in s;s=s.replace(old,new);path.write_text(s,encoding='utf-8')
# The ordinary verifier imports the promoted modules, never the staging loader.
s=(ROOT/'scripts/verify-staged-survival.py').read_text(encoding='utf-8')
s=s.replace('loader=load(\'survival_staging_loader\',\'scripts/staged-survival-runtime.py\');g=loader.install()',"sys.path.insert(0,str(ROOT/'app'))\nimport engine_worker\nimport detail_gpu as g")
s=s.replace('research/staging/v34/app/','app/').replace("'scripts/staged-survival-runtime.py',",'')
s=s.replace('scripts/verify-staged-survival.py','scripts/verify-survival-detail.py')
s=s.replace('stage_only=True','stage_only=False').replace('research/detail-staged-survival-verification.json','research/detail-survival-verification.json')
s=s.replace('Whole-squad staged GPU down/revive parity against the explicit CPU bridge.','Whole-squad production GPU down/revive parity against the explicit CPU bridge.').replace('The normal v33 application is untouched.','This verifier imports the ordinary application modules.')
(ROOT/'scripts/verify-survival-detail.py').write_text(s,encoding='utf-8')
s=(ROOT/'scripts/verify-staged-revival-compat.py').read_text(encoding='utf-8')
needle="bridge=load('staged_survival_compat','research/staging/v34/app/survival_compat.py');bridge.install();bridge.install()"
assert needle in s
s=s.replace(needle,'import engine_compat\nengine_compat.install();engine_compat.install()')
s=s.replace('scripts/verify-staged-revival-compat.py','scripts/verify-revival-compat.py').replace('research/staging/v34/app/survival_compat.py','app/survival_compat.py').replace('research/detail-staged-revival-compat-verification.json','research/detail-survival-cpu-compat-verification.json').replace('Staged CPU revival','Production CPU revival')
(ROOT/'scripts/verify-revival-compat.py').write_text(s,encoding='utf-8')
shutil.copy2(ROOT/'research/survival-test-template.py',ROOT/'tests/test_detail_survival.py')
path=ROOT/'scripts/verify-normal-detail.py';s=path.read_text(encoding='utf-8')
assert "modules.append('test_detail_survival')" not in s
s=s.replace("modules.append('test_detail_incoming')","modules.append('test_detail_incoming')\n    modules.append('test_detail_survival')")
s=s.replace("'app/detail_boss.py','app/gpu_service.py'","'app/detail_boss.py','app/gpu_service.py','app/engine_compat.py','app/survival_compat.py','scripts/verify-survival-detail.py'")
path.write_text(s,encoding='utf-8')
path=ROOT/'web/index.html';s=path.read_text(encoding='utf-8')
old='戦闘不能・復活、敵からのデバフ、座標などは未対応です。'
assert old in s
s=s.replace(old,'戦闘不能・復活と復活時のパッシブ復元にも対応します。HP閾値をまたぐ発動・敵からのデバフ・座標などには未対応の条件が残っています。')
path.write_text(s,encoding='utf-8')
print('Promoted verified survival v34; ordinary application/API verification still required.')
