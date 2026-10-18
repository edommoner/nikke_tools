"""Advance the active full-port goal only after source-bound v29 evidence."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def checked(name):
    r=json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
    assert r['passed'],name
    assert r['source_sha256'],name
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),'Stale '+name
    return r
paths=['research/detail-capacity-verification.json','research/detail-capacity-long-verification.json','research/detail-catalog-capacity-verification.json','research/detail-normal-acceptance.json','research/detail-owned-acceptance.json','research/detail-capacity-api-verification.json','research/detail-capacity-ui-verification.json']
main,long,catalog,normal,owned,api,ui=[checked(p) for p in paths]
assert len(main['cases'])==30 and all(r['passed'] for r in main['cases'])
assert len(long['cases'])==1 and long['cases'][0]['duration']==180
assert normal['tests_run']==57 and normal['skipped']==0
assert len(catalog['cases'])==270 and not catalog['not_executed']
assert len(owned['cases'])==36
assert api['compute']['backend']=='cuda_detail' and all(api['compute']['cpu_verification'].values())
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values())
audit=json.loads((ROOT/'research/detail-capacity-cpu-audit.json').read_text(encoding='utf-8'))
assert audit['current_effect_limit']==256 and audit['burst_chain_example']['actual_effect_rows']==172
assert audit['burst_chain_example']['actual_compiler_accepted']
assert all(sha(p)==h for p,h in audit['source_sha256'].items())
support=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
assert support['accepted_contexts']==529 and all(sha(p)==h for p,h in support['compiler_source_sha256'].items())
node_raw=(ROOT/'research/detail-capacity-node-tests.log').read_bytes()
node=node_raw.decode('utf-16' if node_raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert all(s in node for s in ('tests 22','pass 22','fail 0'))
build=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
assert build['abi']=='detail_capacity_v29' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_world.py','app/engine_worker.py','app/gpu_service.py','scripts/build-combat.py','scripts/build-detail-native.py','scripts/verify-capacity-detail.py','scripts/verify-normal-detail.py','tests/test_detail_capacity.py','tests/test_detail_counts.py','web/app.js','server.mjs']
files+=['tests/test_detail_charge_immunity.py','scripts/verify-capacity-regression-detail.py','scripts/make-capacity-fixture.py','research/save-capacity-checkpoint.py']
remaining=['68 default characters and 283 favorite contexts remain rejected.',
 'The definition/named-state bound is now 256; dynamic active-slot/target-history and other independent bounds remain fail-closed.',
 'Mixed/periodic/weapon-change team listeners remain rejected.',
 'Incoming damage, cover/down/revive, healing storage, accumulation, moving boss/aim geometry and upstream omitted effects/cubes remain.',
 'Rich squads, settings and native long battles verified here; not all favorite variants or character combinations.']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
 feature='v29 capacity 256 with eight-word B3 exclusion/reducer bitmaps, source-owner/shared-budget high IDs and rich 172-effect squads',abi=build['abi'],effect_capacity=256,named_state_capacity=256,active_slot_capacity=512,effect_row_words=286,
 workspace_bytes_per_squad=api['compute']['workspace_bytes'],compiled_characters=135,catalog_characters=203,favorite_contexts_compiled=529,favorite_contexts_total=812,compilation_is_not_all_context_parity=True,
 capacity_cases=len(main['cases']),long_native_180_second_battles=1,catalog_cases=len(catalog['cases']),owned_cases=len(owned['cases']),python_focused_tests_passed=normal['tests_run'],node_tests_passed=22,
 normal_api_total=api['total'],normal_ui_total=ui['total'],reports=paths,source_sha256={f:sha(f) for f in files},report_sha256={f:sha(f) for f in paths},capacity_audit_sha256=sha('research/detail-capacity-cpu-audit.json'),remaining=remaining)
(ROOT/'research/detail-capacity-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';progress=json.loads(p.read_text(encoding='utf-8'))
assert progress['checkpoint']['abi']=='detail_team_hits_v28'
progress['previous_checkpoint']=progress['checkpoint'];progress['checkpoint']=checkpoint
progress.update(generated_at=checkpoint['generated_at'],current_work=None,objective_complete=False)
progress['next_implementation']=[s for s in progress['next_implementation'] if not s.startswith('Increase effect capacity')]
p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:checkpoint[k] for k in ('passed','abi','objective_complete','capacity_cases','python_focused_tests_passed','normal_api_total','normal_ui_total')}))
