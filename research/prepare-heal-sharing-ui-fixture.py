"""Fictional owned growth with actual Rem/Marciana/Alice skill definitions."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
original=json.loads((ROOT/'research/detail-healing-storage-api-fixture.json').read_text(encoding='utf-8'))
mapping={'마르차나':'렘','프리카':'마르차나','user:gpu-healing-storage':'user:gpu-heal-sharing','GPU検証：マルチャーナの余剰回復保存':'GPU検証：レムの回復分配','マルチャーナの余剰回復保存とヒーリングキューブのGPU検証用に作成した架空の所持・装備データです。':'レムの回復分配とヒーリングキューブのGPU検証用に作成した架空の所持・装備データです。'}
def transform(value):
    if isinstance(value,dict):return {mapping.get(k,k):transform(v) for k,v in value.items()}
    if isinstance(value,list):return [transform(v) for v in value]
    return mapping.get(value,value) if isinstance(value,str) else value
b=transform(original)
assert len(b['profile']['chars'])==len(b['squad'])==5
assert b['burst_policy']=='auto' and b['shooting_policy']=='character' and b['burst_gauge_mode']=='accumulate'
assert b['profile']['chars']['렘']['equip_skills']['atk_pct']==[11.11,11.11,12.34]
assert not any(k.startswith('_debug') for k in b)
(ROOT/'research/detail-heal-sharing-api-fixture.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
session=transform(json.loads((ROOT/'research/detail-healing-storage-ui-fixture.json').read_text(encoding='utf-8')))
session.update(saved_at=datetime.now(timezone.utc).isoformat(),profile=b['profile'],deltas=b['stat_deltas'],squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],enemyPatterns=b['enemy']['patterns'])
(ROOT/'research/detail-heal-sharing-ui-fixture.json').write_text(json.dumps(session,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=(ROOT/'scripts/smoke-detail-healing-storage.mjs').read_text(encoding='utf-8').replace('4335','4336').replace('healing-storage','heal-sharing').replace('detail_healing_storage_v40','detail_heal_sharing_v41').replace('마르차나','렘')
s=s.replace("'app/healing_storage_compat.py'","'app/healing_storage_compat.py','app/heal_sharing_compat.py'")
(ROOT/'research/smoke-detail-heal-sharing.mjs').write_text(s,encoding='utf-8')
print('Created fictional owned-data fixture and ordinary API smoke; not executed.')
