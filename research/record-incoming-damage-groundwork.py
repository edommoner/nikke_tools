import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ref=json.loads((ROOT/'research/detail-incoming-damage-cpu-reference.json').read_text(encoding='utf-8'))
assert ref['cpu_reference_verified'] and not ref['gpu_implemented'] and len(ref['cases'])==20
assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in ref['source_sha256'].items())
p=ROOT/'research/boss-gpu-integration-notes.json';r=json.loads(p.read_text(encoding='utf-8'))
for item in r['next_required_work']:
 if 'source' in item:item['source']=item['source'].replace('_boss_targets','_attack_targets')
r['incoming_damage_cpu_groundwork']={'report':'research/detail-incoming-damage-cpu-reference.json','cases':20,'gpu_implemented':False,'coverage':['Final defense and recipient incoming-damage modifiers','Non-piercing shield overflow stops at the shield; later shields first','Piercing hits each shield, cover and HP; decoy interception remains separate','Cover during reload, disabled cover and shield-before-cover priority','Equal damage sharing with received_hit only on the original target','Invincibility, undying, lethal-hit reaction before the blow and down events'],'model_gap_to_resolve':'The literal legacy damage_reduction_pct marker does not change the pinned CPU incoming formula in the controlled case. Do not count a matching omission as game correctness.'}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
