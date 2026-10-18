"""Save a scoped v22 checkpoint only after each acceptance gate has passed."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def log_rows(path):
    b=(ROOT/path).read_bytes();t=b.decode('utf-16' if b.startswith(b'\xff\xfe') else 'utf-8-sig')
    return [json.loads(line) for line in t.splitlines() if line.startswith('{')]
def save(path,data):(ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

normal=read('research/detail-normal-acceptance.json')
ptx=read('research/detail-shield-lifecycle-ptx.json')
raw=read('research/detail-shield-squads-verification.json')
api=read('research/detail-shields-api-verification.json')
ui=read('research/detail-shields-ui-verification.json')
common=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx',
        'app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
for report in (normal,ptx,raw,api,ui):
    assert report['passed'],report.get('scope')
    for f in common:assert report['source_sha256'][f]==hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),f
assert normal['tests_run']==28 and not normal['skipped']
assert len(ptx['cases'])==21 and len(raw['cases'])==24
assert all(r['passed'] for r in raw['cases'])
native=[r for r in log_rows('research/detail-normal-acceptance.log') if 'shield_snapshots' in r.get('checks',{})]
assert len(native)==21 and all(r['passed'] for r in native)
node=(ROOT/'research/detail-current-node-tests.log').read_bytes()
node=node.decode('utf-16' if node.startswith(b'\xff\xfe') else 'utf-8-sig')
assert 'pass 20' in node and 'fail 0' in node
merged=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,cpu_trace_used_as_gpu_input=False,
    scope=ptx['scope'],cases=native+ptx['cases'],source_sha256=ptx['source_sha256'])
save('research/detail-shield-lifecycle-verification.json',merged)
coverage=read('research/detail-coverage-shields.json');audit=read('research/detail-all-effects-audit.json')
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
    feature='v22 shield quantities and normal-screen detailed GPU acceptance',abi='detail_shields_v22',
    workspace_bytes_per_squad=299928,compiled_characters=coverage['supported'],catalog_characters=coverage['characters'],
    favorite_contexts_compiled=audit['accepted_contexts'],favorite_contexts_total=audit['total_contexts'],
    compilation_is_not_all_context_parity=True,current_catalog_verified=False,
    python_focused_tests_passed=normal['tests_run'],python_focused_seconds=normal['seconds'],node_tests_passed=20,
    shield_subsystem_cases=42,raw_full_squad_cases=24,normal_api_total=api['total'],normal_ui_total=ui['total'],
    reports=['research/detail-normal-acceptance.json','research/detail-shield-lifecycle-verification.json',
             'research/detail-shield-squads-verification.json','research/detail-shields-api-verification.json',
             'research/detail-shields-ui-verification.json'],
    remaining=['All characters/favorite variants and all effects are not ported.',
               'Authored shield-layer stimuli do not implement boss HP/cover damage or survival.',
               'No new current-catalog-wide parity or full 121-test regression claim.',
               'Unsupported effects, including heal_overcharge_store, fall back to CPU.'],
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in common+[
        'app/gpu_service.py','server.mjs','web/app.js','web/index.html','scripts/verify-shield-squads-detail.py',
        'scripts/verify-normal-detail.py','tests/test_detail_shields.py']})
save('research/detail-shields-checkpoint.json',report)
progress=read('research/detail-expansion-next.json')
progress['generated_at']=report['generated_at'];progress['objective_complete']=False
progress['previous_checkpoint_path']='research/detail-squad-checkpoint.json'
progress['checkpoint']={**report,'path':'research/detail-shields-checkpoint.json'}
progress.pop('current_work',None)
save('research/detail-expansion-next.json',progress)
plan=read('research/detail-shield-lifecycle-plan.json')
plan.update(gpu_implemented=True,objective_complete=False,cpu_reference_cases=21,
            subsystem_cases_verified=42,raw_full_squad_cases_verified=24,
            checkpoint='research/detail-shields-checkpoint.json',full_incoming_boss_combat_implemented=False)
save('research/detail-shield-lifecycle-plan.json',plan)
print(json.dumps({k:report[k] for k in ['passed','objective_complete','compiled_characters','favorite_contexts_compiled','python_focused_tests_passed','shield_subsystem_cases','raw_full_squad_cases']}))
