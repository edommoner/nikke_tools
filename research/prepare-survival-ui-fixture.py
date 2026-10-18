"""Fictional owned/gear fixture shared by ordinary UI and API checks."""
import copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('survival_fixture',ROOT/'scripts/verify-staged-survival.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
_,b,_=next(x for x in m.fixtures() if x[0]=='raw-new-라푼젤-death')
b={k:v for k,v in b.items() if not k.startswith('_debug')}
b.update(compute_backend='cuda_detail',verify_detail=True,stat_deltas={'앨리스':dict(atk=12000,hp=100000,**{'def':250})})
session=json.loads((ROOT/'research/detail-incoming-ui-fixture.json').read_text(encoding='utf-8'))
session.update(saved_at=datetime.now(timezone.utc).isoformat(),profile=b['profile'],patches={},deltas=b['stat_deltas'],squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],enemyPatterns=b['enemy']['patterns'],enemyParts=[])
session['snapshot'].update(profile=copy.deepcopy(b['profile']),squad=b['squad'],is_demo=True,warnings=['GPU検証用の架空の所持・装備データです。'])
settings={'enemy-def':b['enemy']['def'],'enemy-code':b['enemy']['code'],'duration':b['duration'],'level':b['level'],'core':b['enemy']['core_px'],'distance':b['enemy']['distance']}
session['settings']={**settings,'detail-backend':'cuda_verified','shooting-policy':b['shooting_policy'],'burst-policy':b['burst_policy'],'burst-gauge-mode':b['burst_gauge_mode'],'random-seed':b['seed']}
preset=copy.deepcopy(session['customPresets'][0]);preset.update(id='user:gpu-survival',label='GPU検証：戦闘不能と復活',settings=settings,patterns=b['enemy']['patterns'],parts=[])
session['customPresets']=[preset];session['enemyContexts']={'single':dict(settings=settings,parts=[],patterns=b['enemy']['patterns'],presetId=preset['id'])}
for path,data in [('research/detail-survival-api-fixture.json',b),('research/detail-survival-ui-fixture.json',session)]:
    (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Saved fictional Rapunzel revival fixtures, with mixed growth and temporary Alice stat deltas.')
