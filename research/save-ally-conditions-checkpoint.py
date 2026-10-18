"""Record v27 only after current source-bound reports pass; never complete goal."""
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
main_path='research/detail-ally-conditions-verification.json'
route_path='research/detail-ally-routing-verification.json'
catalog_path='research/detail-catalog-ally-conditions-verification.json'
normal_path='research/detail-normal-acceptance.json'
api_path='research/detail-ally-conditions-api-verification.json'
ui_path='research/detail-ally-conditions-ui-verification.json'
main=checked(main_path);routing=checked(route_path);catalog=checked(catalog_path)
normal=checked(normal_path);api=checked(api_path);ui=checked(ui_path)
assert len(main['cases'])==98 and all(row['passed'] for row in main['cases'])
assert len(routing['cases'])==6
assert len(catalog['cases'])==266 and not catalog['not_executed']
assert normal['tests_run']==44 and normal['skipped']==0
node_log=(ROOT/'research/detail-ally-conditions-node-tests.log').read_bytes()
node_log=node_log.decode('utf-16' if node_log.startswith(b'\xff\xfe') else 'utf-8-sig')
assert all(text in node_log for text in ('tests 22','pass 22','fail 0'))
assert api['compute']['backend']=='cuda_detail' and all(api['compute']['cpu_verification'].values())
assert ui['backend']=='cuda_detail' and all(ui['cpu_verification'].values())
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
coverage=json.loads((ROOT/'research/detail-coverage-ally-conditions.json').read_text(encoding='utf-8'))
assert coverage['supported']==133 and audit['accepted_contexts']==521
assert all(sha(p)==h for p,h in audit['compiler_source_sha256'].items())
build=json.loads((ROOT/'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
assert build['abi']=='detail_ally_conditions_v27' and build['source_sha256']==sha('app/detail_effects.cu') and build['binary_sha256']==sha('app/detail_effects-sm86.cubin')
reports=[main_path,route_path,catalog_path,normal_path,api_path,ui_path]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/detail_world.py','app/gpu_service.py','scripts/verify-ally-conditions-detail.py','scripts/verify-ally-routing-detail.py','scripts/audit-ally-conditions.py','tests/test_detail_ally_conditions.py','scripts/verify-normal-detail.py','web/app.js','server.mjs']
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
    feature='v27 ally HP activation versus actual recipient runtime HP, defender ally complements',abi=build['abi'],
    compiled_characters=133,catalog_characters=203,favorite_contexts_compiled=521,favorite_contexts_total=812,
    compilation_is_not_all_context_parity=True,primitive_cases_per_backend=33,whole_battle_cases=32,
    raw_trina_cases=16,routing_native_cases=6,catalog_cases=266,python_focused_tests_passed=44,node_tests_passed=22,
    normal_api_total=api['total'],normal_ui_total=ui['total'],reports=reports,
    source_sha256={f:sha(f) for f in files},report_sha256={f:sha(f) for f in reports},
    new_characters=['트리나'],remaining=[
        '70 default characters and 291 favorite contexts remain rejected.',
        'Team part/body hit notifications with attacker attribution, multi-hit contexts and missing source constructs remain.',
        'Incoming damage, cover/down/revive, healing storage, accumulation, moving boss/aim geometry and upstream omitted effects/cubes remain.',
        'Selected character squads and settings verified; not all favorite variants or combinations.'
    ])
(ROOT/'research/detail-ally-conditions-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress_path=ROOT/'research/detail-expansion-next.json'
progress=json.loads(progress_path.read_text(encoding='utf-8'))
assert progress['checkpoint']['abi']=='detail_live_parts_v26'
progress['previous_checkpoint']=progress['checkpoint'];progress['checkpoint']=checkpoint
progress.update(generated_at=checkpoint['generated_at'],current_work=None,objective_complete=False)
progress_path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,objective_complete=False,abi=build['abi'],compiled=133)))
