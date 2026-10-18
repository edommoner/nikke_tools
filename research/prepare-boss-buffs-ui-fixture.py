"""A reviewable normal-UI session using the same fictional profile as API tests."""
import copy,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
b=json.loads((ROOT/'research/detail-boss-buffs-api-fixture.json').read_text(encoding='utf-8'))
r={'settings':{}}
patterns=copy.deepcopy(b['enemy']['patterns'])
for p in patterns:
 if p['id']=='armor':p['note']='防御1.5倍・被ダメージ−25%'
 if p['id']=='exposed':p['note']='防御0.7倍・被ダメージ＋33.33%（解除不可）'
settings={'enemy-def':b['enemy']['def'],'enemy-code':b['enemy']['code'],'duration':b['duration'],'level':b['level'],'core':b['enemy'].get('core_px',0),'distance':b['enemy']['distance']}
r.update(format='nikke-tools-session-v1',ui_version=3,saved_at=datetime.now(timezone.utc).isoformat(),snapshot={'profile':copy.deepcopy(b['profile']),'missing':{},'warnings':['GPU検証用の架空の所持・育成データです。'],'is_demo':True,'squad':b['squad']},profile=b['profile'],patches=b.get('patches',{}),deltas=b.get('stat_deltas',{}),squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],activeTeam=0,raidCount=5,singleMode=True,comparison=None,job=None,reference=None,enemyParts=b['enemy'].get('parts',[]),enemyPatterns=patterns,enemyContexts={'single':{'settings':settings,'parts':b['enemy'].get('parts',[]),'patterns':patterns,'presetId':'user:gpu-boss-buffs'}},customPresets=[{'id':'user:gpu-boss-buffs','mode':'single','label':'GPU検証：コア・距離・敵バフ','settings':settings,'parts':b['enemy'].get('parts',[]),'patterns':patterns}],excluded=[])
r['settings'].update(settings)
r['settings'].update({'detail-backend':'cuda_verified','shooting-policy':b.get('shooting_policy','auto'),'burst-policy':b.get('burst_policy','auto'),'burst-gauge-mode':b.get('burst_gauge_mode','fixed'),'random-seed':b.get('seed',0)})
(ROOT/'research/detail-boss-buffs-ui-fixture.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared fictional UI session with '+str(len(patterns))+' authored patterns')
