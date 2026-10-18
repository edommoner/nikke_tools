"""Read-only next-port inventory while v20 regression is running."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
engine=ROOT/'research/upstream/nikke-calc-master/data'
meta=json.loads((engine/'parsed_nikke.json').read_text(encoding='utf-8'));raw=json.loads((engine/'parsed_skills.json').read_text(encoding='utf-8'))
coverage=json.loads((ROOT/'research/detail-coverage-random.json').read_text(encoding='utf-8'));rows={r['character']:r for r in coverage['results']};accepted={n for n,r in rows.items() if r['supported']}
subjects=[]
for name,effects in raw.items():
 found=[e for e in effects if 'squad_ally_exists' in e.get('trigger',{}).get('condition',[])] if isinstance(effects,list) else []
 if not found:continue
 squad=meta.get(name,{}).get('squad')
 buddies=[n for n,m in meta.items() if isinstance(m,dict) and n!=name and squad and m.get('squad')==squad and n in rows]
 subjects.append(dict(character=name,squad=squad,buddies=buddies,already_accepted_buddies=[n for n in buddies if n in accepted],effects=found,current_compile=rows.get(name)))
plan=dict(feature='squad_ally_exists static squad metadata condition',implemented=False,objective_complete=False,subjects=subjects,
 cpu_rule='Pinned BuffManager._condition_ok reads caster squad from _NIKKE; requires a different squad member with the same nonempty squad. It does not filter downed allies; costumes use their own metadata. Not a runtime-condition prefix.',
 candidate_port='Compile an immutable true/false predicate from source metadata; existing literal condition25 may encode it, but passive registration/gating must match independent CPU references before acceptance.',
 verification_gates=['Positive and negative buddies, caster alone, dummy/no metadata and costume variants','Authored timing: battle start, passive, finite duration, conditional-finite passive and counters','Retain complete raw character skills and use whole five-member native/PTX comparisons','Owned equipment and normal API/UI; repeat regression after an actual change'],
 current_v20_frozen=True,notes='Do not change host/kernel until full118 session82409 finishes and v20 evidence is checkpointed. This inventory is not implementation or damage parity.')
(ROOT/'research/detail-squad-condition-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'character':s['character'],'accepted_buddies':s['already_accepted_buddies'],'issues':s['current_compile'].get('issues',[]) if s['current_compile'] else []} for s in subjects],ensure_ascii=True))
