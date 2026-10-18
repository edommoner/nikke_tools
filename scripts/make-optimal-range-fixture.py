"""Fictional owned Agent Bunny profile for the normal application path."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker as a
body=json.loads((ROOT/'research/detail-charge-immunity-api-fixture.json').read_text(encoding='utf-8'))
before,after='리버렐리오','에이드 : 에이전트 바니'
for key in ('profile','patches','stat_deltas'):
    group=body['profile']['chars'] if key=='profile' else body[key]
    if before in group:group[after]=group.pop(before)
body['squad']=[after if n==before else n for n in body['squad']]
body['enemy'].update(distance=30,core_px=50)
snapshot=a.import_data({**copy.deepcopy(body['profile']),'_meta':{'is_demo':True}})
session=dict(format='nikke-tools-session-v1',snapshot=snapshot,profile=body['profile'],teams=[body['squad']],
    singleMode=True,raidCount=1,activeTeam=0,patches=body['patches'],deltas=body['stat_deltas'],
    settings={'duration':60,'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':30,
              'burst-policy':'rules','shooting-policy':'character','burst-gauge-mode':'accumulate',
              'random-seed':12345,'detail-backend':'cuda_verified'})
for kind,data in [('api',body),('ui',session)]:
    (ROOT/f'research/detail-optimal-range-{kind}-fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created fictional Agent Bunny fixtures; raw skills retained')
