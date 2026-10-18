"""Measure effect capacity with fictional rich growth, without CPU/GPU battles."""
import copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as a
import detail_gpu as gpu
fixture_path='research/detail-team-hits-api-fixture.json'
fixture=json.loads((ROOT/fixture_path).read_text(encoding='utf-8'))
growth=copy.deepcopy(fixture['profile']['chars'][fixture['squad'][0]])
account=copy.deepcopy(fixture['profile'].get('_account',{}))
accepted={r['character'] for r in json.loads((ROOT/'research/detail-coverage-team-hits.json').read_text(encoding='utf-8'))['results'] if r['supported']}
audit=json.loads((ROOT/'research/detail-all-effects-audit.json').read_text(encoding='utf-8'))
accepted_contexts={(r['character'],r['favorite_stage']) for r in audit['favorite_stage_matrix'] if r['accepted']}
class Captured(Exception):pass
rows=[]
for subject,meta in a.META.items():
    if not isinstance(meta,dict) or subject.startswith(('_','test_')) or a.spec.is_preview(subject):continue
    names=[subject]+[n for n in ['리타','크라운','앨리스','모더니아','루주'] if n!=subject][:4]
    for favorite in range(4):
        chars={n:copy.deepcopy(growth) for n in names};chars[subject]['favorite_stage']=favorite
        measured={}
        def capture(cs,effects):
            own=[e for e,n in effects if n==subject]
            team=sum(any(t.startswith(('part_hit_count:','body_hit_count:')) for t in e.get('trigger',{}).get('timing',[])) for e in own)
            measured.update(raw_effects=len(own),team_definitions=team,expanded_lower_bound=len(own)+4*team)
            raise Captured()
        body=dict(profile=dict(chars=chars,_account=account),squad=names,duration=1,level=400,
                  enemy={'def':31784,'core_px':5,'code':'풍압','distance':25},
                  burst_policy='auto',shooting_policy='auto',_compile_gpu_detail=True)
        try:
            with patch.object(gpu,'compile_effects',capture):a.evaluate(body)
        except Captured:pass
        except Exception as error:measured['setup_error']=str(error)
        rows.append(dict(character=subject,favorite=favorite,standard_compiler_accepted=subject in accepted,context_compiler_accepted=(subject,favorite) in accepted_contexts,**measured))
maximum={}
for row in rows:
    if 'expanded_lower_bound' not in row:continue
    if row['character'] not in maximum or row['expanded_lower_bound']>maximum[row['character']]['expanded_lower_bound']:maximum[row['character']]=row
def heaviest(pool):
    selected=sorted(pool,key=lambda r:-r['expanded_lower_bound'])[:5]
    return dict(characters=selected,expanded_lower_bound=sum(r['expanded_lower_bound'] for r in selected),limit=gpu.NE)
maximum_accepted={}
for row in rows:
    if not row['context_compiler_accepted'] or 'expanded_lower_bound' not in row:continue
    if row['character'] not in maximum_accepted or row['expanded_lower_bound']>maximum_accepted[row['character']]['expanded_lower_bound']:maximum_accepted[row['character']]=row
all_max=heaviest(maximum.values());accepted_max=heaviest(maximum_accepted.values())
pool=list(maximum_accepted.values())
selected=[max((r for r in pool if str(a.META[r['character']].get('burst_stage'))==stage),key=lambda r:r['expanded_lower_bound']) for stage in ('1','2','3')]
used={r['character'] for r in selected};selected+=sorted((r for r in pool if r['character'] not in used),key=lambda r:-r['expanded_lower_bound'])[:2]
chain=dict(characters=selected,expanded_lower_bound=sum(r['expanded_lower_bound'] for r in selected),limit=gpu.NE)
for example in (accepted_max,chain):
    chosen=example['characters'];names=[r['character'] for r in chosen]
    chars={r['character']:{**copy.deepcopy(growth),'favorite_stage':r['favorite']} for r in chosen}
    body=dict(profile=dict(chars=chars,_account=account),squad=names,duration=1,level=400,enemy={'def':31784,'core_px':5,'code':'풍압','distance':25},burst_policy='auto',shooting_policy='auto',_compile_gpu_detail=True)
    try:
        result=a.evaluate(body);example.update(actual_compiler_accepted=True,actual_effect_rows=len(result['program']['effects']))
    except gpu.UnsupportedDetail as error:
        example.update(actual_compiler_accepted=False,issues=error.issues)
        trace=error.__traceback__
        while trace:
            if trace.tb_frame.f_code.co_name=='compile_effects':
                example['actual_pre_guard_effect_rows']=len(trace.tb_frame.f_locals['rows'])
                example['actual_pre_guard_named_states']=len(trace.tb_frame.f_locals['states'])
            trace=trace.tb_next
files=['scripts/audit-detail-capacity.py',fixture_path,'app/detail_gpu.py','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_preparation_only=True,cpu_battle_executed=False,gpu_battle_executed=False,
    current_effect_limit=gpu.NE,cases=rows,heaviest_all=all_max,heaviest_standard_accepted=accepted_max,burst_chain_example=chain,
    scope='Fictional rich growth reused across characters; expanded effect lower bound, excludes target-list descriptors. Standard accepted set is compile-only, not rich-profile or squad parity.',
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
(ROOT/'research/detail-capacity-cpu-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cases=len(rows),measured=len(maximum),heaviest_all=all_max['expanded_lower_bound'],heaviest_standard_accepted=accepted_max['expanded_lower_bound'],limit=gpu.NE)))
