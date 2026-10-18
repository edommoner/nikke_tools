"""Keep an unfinished v42 port distinct from accepted v41 production."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
paths=['research/detail-heal-charge-cpu-reference.json','research/detail-heal-charge-cpu-squads.json','research/detail-heal-charge-extra-cpu.json','research/detail-heal-charge-cpu-legacy.json','research/detail-heal-charge-boundaries.json','research/detail-heal-charge-coverage.json','research/detail-heal-charge-favorites.json']
reports={p:json.loads((ROOT/p).read_text(encoding='utf-8')) for p in paths}
for p,r in reports.items():
    assert r.get('passed',True),p
    for f,h in r.get('source_sha256',r.get('compiler_source_sha256',{})).items():assert sha(f)==h,(p,f)
cp=json.loads((ROOT/'research/detail-heal-sharing-checkpoint.json').read_text(encoding='utf-8'));assert cp['passed'] and all(sha(p)==h for p,h in cp['source_sha256'].items()),'Production changed'
groups={}
for group in ('new','extra','legacy'):
    for backend in ('native','ptx'):
        path=ROOT/f'research/detail-heal-charge-{group}-{backend}.json'
        if not path.exists():continue
        r=json.loads(path.read_text(encoding='utf-8'));fresh=all(sha(p)==h for p,h in r['source_sha256'].items())
        groups[group+'-'+backend]=dict(passed_current=r['passed'] and fresh,report_passed=r['passed'],source_current=fresh,completed_cases=len(r['cases']),planned_cases=r['planned_cases'])
all_gpu=len(groups)==6 and all(r['passed_current'] for r in groups.values())
progress=dict(generated_at=datetime.now(timezone.utc).isoformat(),previous_goal_turn_classification='progress',previous_goal_turn_evidence='v41 production checkpoint and immutable final archive; ordinary API/browser and both GPU backends accepted.',stage_abi='detail_heal_charge_v42',production_abi=cp['abi'],production_unchanged=True,stage_only=True,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,gpu_implemented_in_source=True,gpu_parity_verified=all_gpu,gpu_groups=groups,normal_application_promoted=False,independent_CPU_arithmetic_cases=len(reports[paths[0]]['cases']),CPU_squad_witnesses=len(reports[paths[1]]['cases']),CPU_extra_witnesses=len(reports[paths[2]]['cases']),historical_CPU_total_cases=len(reports[paths[3]]['cases']),boundary_tests=reports[paths[4]]['tests_run'],compiled_characters=reports[paths[5]]['supported'],catalog_characters=reports[paths[5]]['characters'],favorite_contexts=reports[paths[6]]['accepted_contexts'],favorite_total=reports[paths[6]]['total_contexts'],expected_workspace_bytes_per_squad=1088520,workspace_bytes_verified_by_passed_new_GPU_groups=any(r['passed_current'] for k,r in groups.items() if k.startswith('new-')),reports=paths,CPU_bridge_composition='Charge wraps BuffManager._dispatch_instant, knock_down, notify, apply_storage_body_heal and timeline._register_instant_handlers; future AST clones must preserve/reapply these wrappers. _activate composes the v40 storage snapshot with the new charge snapshot.',remaining=['Finish current legacy backends and rerun the extracted extra compare helper at its current hash.','Promote only accepted CPU/GPU artifacts, then normal production/API/browser verification.','Shield amplification, received damage sharing, damage accumulators, enemy effects, geometry and CPU/model gaps remain.'])
(ROOT/'research/detail-heal-charge-progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'));r['current_work']=progress;p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
initial=ROOT/'research/ports/v42-initial-raw-witnesses'
if initial.exists() and not (initial/'archive-manifest.json').exists():
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in initial.iterdir() if p.is_file()}
    (initial/'archive-manifest.json').write_text(json.dumps(dict(accepted_current_proof=False,reason='Initial CPU scenes retained all raw skills but did not demand nontrivial Rem sharing or Marciana buffer activation. Superseded by positive witnesses and revised slot order.',files=files),indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:progress[k] for k in ('stage_abi','production_unchanged','gpu_parity_verified','compiled_characters','objective_complete')}))
