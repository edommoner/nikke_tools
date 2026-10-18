"""Source-bound v30 named-duration repair checkpoint; full migration stays active."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def checked(name):
    r=json.loads((ROOT/name).read_text(encoding='utf-8-sig'));assert r['passed'],name
    assert r['source_sha256'] and all(sha(p)==h for p,h in r['source_sha256'].items()),'Stale '+name
    return r
paths=['research/detail-named-capacity-verification.json','research/detail-capacity-named-mask-verification.json','research/detail-catalog-named-capacity-verification.json','research/detail-normal-acceptance.json','research/detail-named-low-ptx-verification.json','research/detail-named-capacity-long-verification.json','research/detail-named-capacity-api-verification.json','research/detail-named-capacity-ui-verification.json']
named,cap,catalog,normal,low,long,api,ui=[checked(p) for p in paths]
batch_path='research/detail-named-capacity-batch-verification.json';batch=checked(batch_path);paths.append(batch_path)
assert len(batch['cases'])==33 and batch['launches']==5
assert len(named['cases'])==76 and all(r['passed'] for r in named['cases'])
assert sum(r['kind']=='battle' for r in named['cases'])==12
assert len(cap['cases'])==30 and len(catalog['cases'])==270 and not catalog['not_executed']
assert normal['tests_run']==64 and normal['skipped']==0 and not normal['failures']
assert len(low['cases'])>=14 and len(long['cases'])==2
assert all(r['duration']==180 and r['extension_times'] and r['state_index']>=128 for r in long['cases'])
assert api['compute']['backend']=='cuda_detail' and all(api['compute']['cpu_verification'].values())
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values())
build=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
assert build['abi']=='detail_named_capacity_v30' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
before_path='research/ports/v29/research/detail-named-capacity-before.json'
before=json.loads((ROOT/before_path).read_text(encoding='utf-8'))
assert any(r['index']==128 and r.get('error_type')=='IndexError' for r in before['cases'])
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
assert audit['accepted_contexts']==529 and all(sha(p)==h for p,h in audit['compiler_source_sha256'].items())
raw=(ROOT/'research/detail-named-capacity-node-tests.log').read_bytes();log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert all(t in log for t in ('tests 22','pass 22','fail 0'))
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_world.py','app/engine_worker.py','app/gpu_service.py','scripts/build-combat.py','scripts/build-detail-native.py','scripts/verify-named-capacity-detail.py','scripts/verify-named-capacity-regression.py','scripts/verify-named-capacity-batch.py','scripts/verify-normal-detail.py','tests/test_detail_named.py','tests/test_detail_named_capacity.py','research/detail-bitfield-domains.json','research/boss-gpu-integration-notes.json','research/save-named-capacity-checkpoint.py','web/app.js','server.mjs',before_path]
remaining=['68 default characters and 283 favorite contexts remain rejected.',
 'Dynamic active-slot/target-history bounds remain fail-closed; definition and named-state masks cover 256.',
 'Mixed/periodic/weapon-change team listeners, incoming damage, cover/down/revive, healing storage, accumulation, moving boss/aim geometry and upstream omitted effects/cubes remain.',
 'Authored inactive padding deliberately raises named-state IDs in Crust fixtures; this is not an unpadded real-account observation or all-combination verification.']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
 feature='v30 repair the remaining 128-bit named-duration mask; all eight words, state 255, expiry shortening, DoT timers, raw Crust tap/hold high-ID battles',abi=build['abi'],effect_capacity=256,named_state_capacity=256,effect_row_words=294,workspace_bytes_per_squad=api['compute']['workspace_bytes'],
 compiled_characters=135,catalog_characters=203,favorite_contexts_compiled=529,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,
 named_cases=76,capacity_regression_cases=30,catalog_cases=270,low_state_ptx_cases=len(low['cases']),python_focused_tests_passed=64,node_tests_passed=22,long_native_180_second_battles=2,
 normal_api_total=api['total'],normal_ui_total=ui['total'],reports=paths,source_sha256={f:sha(f) for f in files},report_sha256={f:sha(f) for f in paths},remaining=remaining)
(ROOT/'research/detail-named-capacity-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';progress=json.loads(p.read_text(encoding='utf-8'))
assert progress['checkpoint']['abi']=='detail_capacity_v29'
progress['previous_checkpoint']=progress['checkpoint'];progress['checkpoint']=checkpoint
progress.update(generated_at=checkpoint['generated_at'],objective_complete=False,current_work=None,live_world_dependency_notes='research/boss-gpu-integration-notes.json')
p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:checkpoint[k] for k in ('passed','abi','objective_complete','named_cases','python_focused_tests_passed','normal_api_total','normal_ui_total')}))
