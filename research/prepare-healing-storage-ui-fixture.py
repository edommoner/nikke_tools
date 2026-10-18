"""Fictional raw Marciana growth, Healing cube and public temporary edits."""
import copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('storage_ui_fixture',ROOT/'research/probe-healing-storage-squads.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
_,b,x=next(x for x in m.fixtures() if x[0]=='raw-storage-마르차나');assert not x
c=b['profile']['chars']['마르차나'];c.update(core_enhancement=2,breakthrough=3,affinity=20,skill_levels={'1':7,'2':5,'3':9},collection_stage='SR15',cube={'name':'렐릭 힐링 큐브','level':4});c['equip_skills'].update(atk_pct=[11.11,11.11,12.34],charge_speed_pct=[2.34,2.34,4.3])
b={k:v for k,v in b.items() if not k.startswith('_debug')};b.update(compute_backend='cuda_detail',verify_detail=True,stat_deltas={'마르차나':{'atk':12000,'hp':100000,'def':250}})
session=json.loads((ROOT/'research/detail-outgoing-healing-ui-fixture.json').read_text(encoding='utf-8'))
session.update(saved_at=datetime.now(timezone.utc).isoformat(),profile=b['profile'],patches={},deltas=b['stat_deltas'],squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],enemyPatterns=b['enemy']['patterns'],enemyParts=[])
session['snapshot'].update(profile=copy.deepcopy(b['profile']),squad=b['squad'],is_demo=True,warnings=['マルチャーナの余剰回復保存とヒーリングキューブのGPU検証用に作成した架空の所持・装備データです。'])
settings={'enemy-def':b['enemy']['def'],'enemy-code':b['enemy']['code'],'duration':b['duration'],'level':b['level'],'core':b['enemy']['core_px'],'distance':b['enemy']['distance']}
session['settings']={**settings,'detail-backend':'cuda_verified','shooting-policy':b['shooting_policy'],'burst-policy':b['burst_policy'],'burst-gauge-mode':b['burst_gauge_mode'],'random-seed':b['seed']}
preset=copy.deepcopy(session['customPresets'][0]);preset.update(id='user:gpu-healing-storage',label='GPU検証：マルチャーナの余剰回復保存',settings=settings,patterns=b['enemy']['patterns'],parts=[])
session['customPresets']=[preset];session['enemyContexts']={'single':dict(settings=settings,parts=[],patterns=b['enemy']['patterns'],presetId=preset['id'])}
for path,data in [('research/detail-healing-storage-api-fixture.json',b),('research/detail-healing-storage-ui-fixture.json',session)]:
    (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=(ROOT/'scripts/smoke-detail-outgoing-healing.mjs').read_text(encoding='utf-8').replace('outgoing-healing','healing-storage').replace('detail_outgoing_healing_v39','detail_healing_storage_v40').replace('프리카','마르차나').replace('1074184','1078280')
s=s.replace("'app/outgoing_healing_compat.py',","'app/outgoing_healing_compat.py','app/healing_storage_compat.py',")
(ROOT/'scripts/smoke-detail-healing-storage.mjs').write_text(s,encoding='utf-8')
print('Prepared ordinary raw Marciana owned-growth/Healing-cube API and UI inputs; no private debug or real account data.')
