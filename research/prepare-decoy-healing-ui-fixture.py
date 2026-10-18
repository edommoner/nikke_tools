"""Fictional raw-skill Rei owned growth, gear and hypothetical base deltas."""
import copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('decoy_ui_fixture',ROOT/'scripts/verify-staged-decoy-healing.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
_,b,extra=next(x for x in m.real_fixtures() if x[0]=='raw-Rei-decoy-heal-owned-growth');assert not any(extra.values())
b={k:v for k,v in b.items() if not k.startswith('_debug')};b.update(compute_backend='cuda_detail',verify_detail=True)
session=json.loads((ROOT/'research/detail-cover-capacity-ui-fixture.json').read_text(encoding='utf-8'))
session.update(saved_at=datetime.now(timezone.utc).isoformat(),profile=b['profile'],patches={},deltas=b['stat_deltas'],squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],enemyPatterns=b['enemy']['patterns'],enemyParts=[])
session['snapshot'].update(profile=copy.deepcopy(b['profile']),squad=b['squad'],is_demo=True,warnings=['ライのデコイ回復のGPU検証用に作成した架空の所持・装備データです。'])
settings={'enemy-def':b['enemy']['def'],'enemy-code':b['enemy']['code'],'duration':b['duration'],'level':b['level'],'core':b['enemy']['core_px'],'distance':b['enemy']['distance']}
session['settings']={**settings,'detail-backend':'cuda_verified','shooting-policy':b['shooting_policy'],'burst-policy':b['burst_policy'],'burst-gauge-mode':b['burst_gauge_mode'],'random-seed':b['seed']}
preset=copy.deepcopy(session['customPresets'][0]);preset.update(id='user:gpu-decoy-healing',label='GPU検証：ライのデコイ回復',settings=settings,patterns=b['enemy']['patterns'],parts=[])
session['customPresets']=[preset];session['enemyContexts']={'single':dict(settings=settings,parts=[],patterns=b['enemy']['patterns'],presetId=preset['id'])}
for path,data in [('research/detail-decoy-healing-api-fixture.json',b),('research/detail-decoy-healing-ui-fixture.json',session)]:
    (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text=(ROOT/'scripts/smoke-detail-cover-capacity.mjs').read_text(encoding='utf-8').replace('cover-capacity','decoy-healing').replace('detail_cover_capacity_v37','detail_decoy_healing_v38').replace('티아','라이').replace('Ordinary Tia owned-growth and Cover-cube requests with complete raw skills.','Ordinary Rei owned-growth and decoy-healing requests with complete raw skills.')
(ROOT/'scripts/smoke-detail-decoy-healing.mjs').write_text(text,encoding='utf-8');print('Prepared ordinary raw Rei owned-growth API/browser inputs; no live account data.')
