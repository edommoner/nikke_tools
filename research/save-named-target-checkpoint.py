"""Hash-bound acceptance for named direct-attack targets; no tests or builds."""
import hashlib,json,re,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
reports=['research/named-target-native.json','research/named-target-ptx.json','research/named-target-owned-api.json','research/named-target-related-native.json','research/named-target-spec-unit.json','research/named-target-compile-migration.json']
receipts={p:read(p) for p in reports}
for p,r in receipts.items():
 assert r['passed'],p
 for source,digest in r.get('source_sha256',{}).items():assert sha(source)==digest,(p,source)
for backend in ('native','ptx'):
 r=receipts[f'research/named-target-{backend}.json'];assert len(r['cases'])==8 and all(c['passed'] for c in r['cases'])
 for row in r['cases'][4:]:assert row['final_health_equal'] and row['named_bonus_activations']
assert receipts['research/named-target-related-native.json']['tests_run']==2
assert receipts['research/named-target-spec-unit.json']['tests_run']==8
assert receipts['research/named-target-owned-api.json']['pure_gpu_and_verified_and_cpu_equal']
compile=receipts['research/named-target-compile-migration.json'];assert compile['previous_programs_unchanged']==902
snapshot=read('research/named-target-compile-snapshot.json')
assert (compile['standard_accepted'],compile['favorite_accepted'])==(snapshot['standard']['supported'],snapshot['favorite_accepted'])==(175,694)
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_named_attack_targets_v49'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin')
assert portable['ptx_sha256']==sha('app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1]);assert workspace==1103888
files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for directory,pattern in [('app','*.py'),('app','detail_effects*'),('app','*.mjs'),('scripts','*.py'),('scripts','*.mjs'),('tests','*.py'),('tests','*.mjs'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'server.mjs','README.md','package.json'})
additional=['research/named-target-contract.json','research/named-target-compile.json','research/named-target-compile-snapshot.json','research/named-target-api-fixture.json','research/save-named-target-checkpoint.py']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,abi=native['abi'],workspace_bytes_per_squad=workspace,scope='Named direct-attack bonus targets; single aimed enemy; static literal repetition; DoT ramps remain unsupported',standard_accepted=175,standard_total=203,favorite_accepted=694,favorite_total=812,previous_programs_unchanged=902,new_standard=compile['new_standard'],checks=dict(native_cases=8,portable_cases=8,existing_related_suites=2,existing_related_cases=20,lightweight_spec_and_boundary_tests=8,normal_owned_api=True),reports=reports,source_sha256={p:sha(p) for p in files+additional},remaining_standard=[r for r in snapshot['standard']['results'] if not r['supported']],test_selection='Targeted count/deferred phase regression. Earlier unit receipts overlap the final lightweight gate; do not add their counts. Frozen v48 full216 was not rerun and is not claimed as current full-suite evidence.',archive='research/ports/v49-named-targets-verified')
(ROOT/'research/named-target-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=ROOT/checkpoint['archive'];archive.mkdir(exist_ok=False)
for p in files+additional+reports+['research/named-target-checkpoint.json']:
 target=archive/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target);assert hashlib.sha256(target.read_bytes()).hexdigest()==sha(p)
print(json.dumps(dict(passed=True,files=len(files+additional+reports)+1,archive=str(archive)),ensure_ascii=True))
