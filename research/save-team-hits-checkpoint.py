"""Record v28 only after current source-bound verification; keep full goal active."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def checked(path):
    report=json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
    assert report.get('passed'),path
    assert report.get('source_sha256'),path
    assert all(sha(p)==h for p,h in report['source_sha256'].items()),'Stale report: '+path
    return report
paths=['research/detail-team-hits-verification.json','research/detail-team-hits-long-verification.json',
       'research/detail-catalog-team-hits-verification.json','research/detail-normal-acceptance.json',
       'research/detail-team-hits-api-verification.json','research/detail-team-hits-ui-verification.json']
main,long,catalog,normal,api,ui=[checked(p) for p in paths]
assert len(main['cases'])==114 and all(r['passed'] for r in main['cases'])
assert sum(r['kind']=='battle' for r in main['cases'])==64
assert long['duration']==180 and len(long['cases'])==3
assert all(row['checks']['multiple_b3_bonus_cycles'] for row in long['cases'])
assert len(catalog['cases'])==270 and not catalog['not_executed']
assert normal['tests_run']==49 and normal['skipped']==0
assert api['compute']['backend']=='cuda_detail' and all(api['compute']['cpu_verification'].values())
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values())
node_raw=(ROOT/'research/detail-team-hits-node-tests.log').read_bytes()
node_log=node_raw.decode('utf-16' if node_raw.startswith(b'\xff\xfe') else 'utf-8-sig')
assert all(text in node_log for text in ('tests 22','pass 22','fail 0'))
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
coverage=json.loads((ROOT/'research/detail-coverage-team-hits.json').read_text(encoding='utf-8'))
assert coverage['supported']==135 and audit['accepted_contexts']==529
assert all(sha(p)==h for p,h in audit['compiler_source_sha256'].items())
capacity=json.loads((ROOT/'research/detail-capacity-cpu-audit.json').read_text(encoding='utf-8'))
assert capacity['current_effect_limit']==128 and capacity['burst_chain_example']['actual_pre_guard_effect_rows']>128
assert all(sha(p)==h for p,h in capacity['source_sha256'].items())
build=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
assert build['abi']=='detail_team_hits_v28' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_world.py','app/engine_worker.py','app/gpu_service.py','scripts/build-combat.py','scripts/build-detail-native.py','scripts/verify-team-hits-detail.py','scripts/verify-team-hits-long-detail.py','tests/test_detail_team_hits.py','scripts/verify-normal-detail.py','web/app.js','server.mjs']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
    feature='v28 global team part/body hits, attacker attribution, source-owner conditions, independent instance/shared-budget identities and expanded B3 bindings',
    abi=build['abi'],workspace_bytes_per_squad=api['compute']['workspace_bytes'],
    compiled_characters=135,catalog_characters=203,favorite_contexts_compiled=529,favorite_contexts_total=812,
    compilation_is_not_all_context_parity=True,primitive_cases_per_backend=25,whole_battle_cases=64,
    long_native_180_second_battles=3,catalog_cases=270,python_focused_tests_passed=49,node_tests_passed=22,
    normal_api_total=api['total'],normal_ui_total=ui['total'],reports=paths,
    source_sha256={f:sha(f) for f in files},report_sha256={f:sha(f) for f in paths},
    capacity_audit='research/detail-capacity-cpu-audit.json',capacity_audit_sha256=sha('research/detail-capacity-cpu-audit.json'),
    new_characters=['D : 킬러 와이프','루마니'],remaining=[
        '68 default characters and 283 favorite contexts remain rejected.',
        'The 128-effect limit also rejects some rich owned squads; a valid burst-chain example exceeds the limit in the current compiler.',
        'Mixed/periodic/weapon-change team listeners remain rejected; current raw team definitions are buff/damage.',
        'Incoming damage, cover/down/revive, healing storage, accumulation, moving boss/aim geometry and upstream omitted effects/cubes remain.',
        'Selected squads/settings and native long battles verified; not all favorite variants or combinations.'
    ])
(ROOT/'research/detail-team-hits-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';progress=json.loads(p.read_text(encoding='utf-8'))
assert progress['checkpoint']['abi']=='detail_ally_conditions_v27'
progress['previous_checkpoint']=progress['checkpoint'];progress['checkpoint']=checkpoint
progress.update(generated_at=checkpoint['generated_at'],current_work=None,objective_complete=False)
progress['team_hit_cpu_groundwork']['gpu_implemented']=True
progress['team_hit_cpu_groundwork']['gpu_scope']='v28 authored team-hit grammar; raw D/Rumani battles and native long cycles verified; mixed/periodic/weapon-change team grammar remains rejected.'
progress['next_implementation'].insert(0,'Increase effect capacity with all NE-dependent bitmaps/layouts updated; CPU audit research/detail-capacity-cpu-audit.json has concrete rich-profile failures at 128 rows.')
p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,objective_complete=False,abi=build['abi'],compiled=135)))
