"""Fictional owned Red Hood and authored live parts for ordinary API/UI checks."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker as a
body=json.loads((ROOT/'research/detail-optimal-range-api-fixture.json').read_text(encoding='utf-8'))
before,after='에이드 : 에이전트 바니','레드 후드'
for key in ('profile','patches','stat_deltas'):
 group=body['profile']['chars'] if key=='profile' else body[key]
 if before in group:group[after]=group.pop(before)
body['squad']=[after if n==before else n for n in body['squad']];body['duration']=30
parts=[dict(name='装甲',hp=0,reach=1),dict(name='砲台',hp=100000,reach=2)]
body['enemy'].update(parts=parts,distance=30,core_px=50)
snapshot=a.import_data({**copy.deepcopy(body['profile']),'_meta':{'is_demo':True}})
settings={'duration':30,'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':30,
          'burst-policy':'rules','shooting-policy':'character','burst-gauge-mode':'accumulate','random-seed':12345,'detail-backend':'cuda_verified'}
session=dict(format='nikke-tools-session-v1',snapshot=snapshot,profile=body['profile'],teams=[body['squad']],singleMode=True,raidCount=1,activeTeam=0,
 patches=body['patches'],deltas=body['stat_deltas'],enemyParts=parts,enemyContexts={'single':{'settings':{k:v for k,v in settings.items() if k in ('duration','level','enemy-def','enemy-code','core','distance')},'parts':parts,'presetId':''}},settings=settings)
for kind,data in [('api',body),('ui',session)]:
 (ROOT/f'research/detail-live-parts-{kind}-fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created fictional Red Hood growth with unbreakable armor and a breakable turret')
