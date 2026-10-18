"""Keep the accepted production checkpoint separate from an unfinished port."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
paths=['research/detail-heal-sharing-cpu-reference.json','research/detail-heal-sharing-cpu-squads.json','research/detail-heal-sharing-cpu-legacy.json','research/detail-heal-sharing-boundaries.json','research/detail-heal-sharing-coverage.json','research/detail-heal-sharing-favorites.json']
reports={p:json.loads((ROOT/p).read_text(encoding='utf-8')) for p in paths}
for p,r in reports.items():
    assert r.get('passed',True),p
    for source,h in r.get('source_sha256',r.get('compiler_source_sha256',{})).items():assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h,(p,source)
cp=json.loads((ROOT/'research/detail-healing-storage-checkpoint.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in cp['source_sha256'].items()),'Production changed'
groups={}
for group in ('new','legacy'):
    for backend in ('native','ptx'):
        path=ROOT/f'research/detail-heal-sharing-{group}-{backend}.json'
        if path.exists():
            r=json.loads(path.read_text(encoding='utf-8'));assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in r['source_sha256'].items())
            groups[group+'-'+backend]=dict(passed=r['passed'],completed_cases=len(r['cases']),planned_cases=r['planned_cases'])
all_gpu=len(groups)==4 and all(r['passed'] for r in groups.values())
progress=dict(generated_at=datetime.now(timezone.utc).isoformat(),stage_abi='detail_heal_sharing_v41',production_abi=cp['abi'],production_unchanged=True,stage_only=True,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,gpu_implemented_in_source=True,gpu_built=(ROOT/'research/staging/v41/app/detail_effects-sm86.cubin').exists(),gpu_parity_verified=all_gpu,gpu_groups=groups,normal_application_promoted=False,independent_CPU_arithmetic_cases=len(reports[paths[0]]['cases']),CPU_squad_witnesses=len(reports[paths[1]]['cases']),historical_CPU_total_cases=len(reports[paths[2]]['cases']),boundary_tests=reports[paths[3]]['tests_run'],compiled_characters=reports[paths[4]]['supported'],catalog_characters=reports[paths[4]]['characters'],favorite_contexts=reports[paths[5]]['accepted_contexts'],favorite_total=reports[paths[5]]['total_contexts'],reports=paths,remaining=['Finish any pending native/PTX regression cases.','Promote only accepted CPU/GPU artifacts, then normal API and browser verification.','ATK-based storage/discharge, shield amplification, received damage sharing, enemy effects and model gaps remain.'])
(ROOT/'research/detail-heal-sharing-progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'));r['current_work']=progress;p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:progress[k] for k in ('stage_abi','production_unchanged','gpu_parity_verified','compiled_characters','objective_complete')}))
