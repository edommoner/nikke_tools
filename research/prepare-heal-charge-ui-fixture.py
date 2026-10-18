"""Prepare fictional Delta/Crown growth, equipment and ordinary API acceptance."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mapping={'렘':'델타 : 닌자 시프','마르차나':'크라운','user:gpu-heal-sharing':'user:gpu-heal-charge','GPU検証：レムの回復分配':'GPU検証：デルタの回復蓄積','レムの回復分配とヒーリングキューブのGPU検証用に作成した架空の所持・装備データです。':'デルタの回復蓄積・放出とヒーリングキューブのGPU検証用に作成した架空の所持・装備データです。'}
def transform(value):
    if isinstance(value,dict):return {mapping.get(k,k):transform(v) for k,v in value.items()}
    if isinstance(value,list):return [transform(v) for v in value]
    return mapping.get(value,value) if isinstance(value,str) else value
b=transform(json.loads((ROOT/'research/detail-heal-sharing-api-fixture.json').read_text(encoding='utf-8')))
assert len(b['profile']['chars'])==len(b['squad'])==5
assert b['burst_policy']=='auto' and b['shooting_policy']=='character' and b['burst_gauge_mode']=='accumulate'
assert b['profile']['chars']['델타 : 닌자 시프']['equip_skills']['atk_pct']==[11.11,11.11,12.34]
assert not any(k.startswith('_debug') for k in b)
(ROOT/'research/detail-heal-charge-api-fixture.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
session=transform(json.loads((ROOT/'research/detail-heal-sharing-ui-fixture.json').read_text(encoding='utf-8')))
session.update(saved_at=datetime.now(timezone.utc).isoformat(),profile=b['profile'],deltas=b['stat_deltas'],squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],enemyPatterns=b['enemy']['patterns'])
(ROOT/'research/detail-heal-charge-ui-fixture.json').write_text(json.dumps(session,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=(ROOT/'scripts/smoke-detail-heal-sharing.mjs').read_text(encoding='utf-8').replace('4336','4338').replace('heal-sharing','heal-charge').replace('detail_heal_sharing_v41','detail_heal_charge_v42').replace('1078280','1088520').replace('렘','델타 : 닌자 시프')
s=s.replace("'app/heal_sharing_compat.py'","'app/heal_sharing_compat.py','app/heal_charge_compat.py'")
(ROOT/'research/smoke-detail-heal-charge.mjs').write_text(s,encoding='utf-8')
print('Prepared fictional owned-data and normal API inputs; not executed.')
