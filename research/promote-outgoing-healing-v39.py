"""Promote v39 only after both GPU backends and prior101 pass at current hashes."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=[f'research/detail-outgoing-healing-{kind}-{backend}.json' for kind in ('authored','real','regression') for backend in ('native','ptx')]+['research/detail-outgoing-healing-boundary-verification.json','research/detail-outgoing-healing-fixture-audit.json','research/detail-outgoing-healing-cpu-reference.json']
closure=set(reports)
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if '-boundary-' in path:assert r['tests_run']==5 and not r['skipped']
    elif any('-'+k+'-' in path for k in ('authored','real','regression')):
        count=19 if '-authored-' in path else 4 if '-real-' in path else 101
        assert r['abi']=='detail_outgoing_healing_v39' and len(r['cases'])==count and not r.get('not_run_cases') and not r['cpu_trace_used_as_gpu_input']
    closure.update(r['source_sha256'])
base=json.loads((ROOT/'research/detail-decoy-healing-checkpoint.json').read_text(encoding='utf-8'));assert base['passed'] and all(sha(p)==h for p,h in base['source_sha256'].items())
closure.update(['research/promote-outgoing-healing-v39.py','research/staging/v39/scripts/build-combat.py','research/staging/v39/scripts/build-detail-native.py'])
archive=ROOT/'research/ports/v39-outgoing-healing-staged-verified';assert not archive.exists(),'Archives are immutable.'
for p in sorted(closure):
    out=(archive/p).resolve();assert out.is_relative_to(archive.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(archive/'archive-manifest.json').write_text(json.dumps(dict(abi='detail_outgoing_healing_v39',objective_complete=False,production_acceptance_pending=True,files={p:sha(p) for p in sorted(closure)}),indent=2)+'\n',encoding='utf-8')
for name in ('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','detail_effects-sm86.cubin','detail_effects-sm86.json','outgoing_healing_compat.py'):shutil.copy2(ROOT/'research/staging/v39/app'/name,ROOT/'app'/name)
for name in ('build-combat.py','build-detail-native.py'):shutil.copy2(ROOT/'research/staging/v39/scripts'/name,ROOT/'scripts'/name)
p=ROOT/'app/engine_compat.py';s=p.read_text(encoding='utf-8');needle='    install_survival_scaling()\n';assert needle in s and 'install_outgoing_healing' not in s
s=s.replace(needle,needle+'    from outgoing_healing_compat import install as install_outgoing_healing\n    install_outgoing_healing()\n');p.write_text(s,encoding='utf-8')
for source,target in [('scripts/verify-staged-outgoing-healing.py','scripts/verify-outgoing-healing.py'),('research/verify-outgoing-healing-regressions.py','scripts/verify-outgoing-healing-regressions.py')]:
    text=(ROOT/source).read_text(encoding='utf-8');text=text.replace('import argparse,hashlib,importlib.util,json\n','import argparse,hashlib,importlib.util,json,sys\n')
    lines=text.splitlines();found=[i for i,l in enumerate(lines) if l.startswith('g=load(')];assert len(found)==1
    i=found[0];lines[i:i+1]=["sys.path.insert(0,str(ROOT/'app'))",'import engine_worker','import detail_gpu as g'];text='\n'.join(lines)+'\n'
    text=text.replace('scripts/verify-staged-outgoing-healing.py','scripts/verify-outgoing-healing.py').replace('research/verify-outgoing-healing-regressions.py','scripts/verify-outgoing-healing-regressions.py').replace("'scripts/staged-outgoing-healing-runtime.py',",'').replace('research/staging/v39/app/','app/').replace('stage_only=True','stage_only=False')
    (ROOT/target).write_text(text,encoding='utf-8')
text=(ROOT/'research/test_staged_outgoing_healing_boundaries.py').read_text(encoding='utf-8').replace('scripts/verify-staged-outgoing-healing.py','scripts/verify-outgoing-healing.py');text=text.split("if __name__=='__main__':")[0]+"if __name__=='__main__':unittest.main()\n";(ROOT/'tests/test_detail_outgoing_healing_boundary.py').write_text(text,encoding='utf-8')
test='''"""Production CPU-extension/GPU parity for outgoing healing and prior101."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=load('production_outgoing_heals','scripts/verify-outgoing-healing.py')
reg=load('production_outgoing_legacy','scripts/verify-outgoing-healing-regressions.py')
class OutgoingHealingGPU(unittest.TestCase):
    def verify(self,cases,count):
        cases=list(cases);self.assertEqual(len(cases),count);device=v.v.s.v.v.v.Cuda()
        try:
            for oracle,name,b,extra in cases:
                with self.subTest(name=name):self.assertTrue(oracle.compare(device,name,b,extra,'native')['passed'])
        finally:device.close()
    def test_authored_body_healing_source_and_recipient(self):self.verify(((v,*x) for x in v.fixtures()),19)
    def test_actual_raw_healers_with_owned_healing_cube(self):self.verify(((v,*x) for x in v.real_fixtures()),4)
    def test_prior101_layers_HP_cover_decoy_and_survival(self):self.verify(reg.fixtures(),101)
if __name__=='__main__':unittest.main()
'''
(ROOT/'tests/test_detail_outgoing_healing.py').write_text(test,encoding='utf-8')
p=ROOT/'scripts/verify-normal-detail.py';text=p.read_text(encoding='utf-8');needle="    modules.append('test_detail_decoy_healing_boundary')";assert needle in text;text=text.replace(needle,needle+"\n    modules.append('test_detail_outgoing_healing')\n    modules.append('test_detail_outgoing_healing_boundary')");p.write_text(text,encoding='utf-8')
p=ROOT/'web/index.html';text=p.read_text(encoding='utf-8');needle='デコイの残量回復にも対応します。';assert needle in text;text=text.replace(needle,needle+'与える回復量増加とヒーリングキューブにも対応します。');p.write_text(text,encoding='utf-8')
print('Installed v39; production/API/browser verification remains required. Full objective incomplete.')
