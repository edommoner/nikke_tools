"""Fictional Liberalio owned growth for normal GPU application verification."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as a
body=json.loads((ROOT/'research/detail-immunity-api-fixture.json').read_text(encoding='utf-8'))
before,after='에이드','리버렐리오'
for group in [body['profile']['chars'],body['patches'],body['stat_deltas']]:
    if before in group:group[after]=group.pop(before)
body['squad']=[after if n==before else n for n in body['squad']];body['enemy']['core_px']=50
snapshot=a.import_data({**copy.deepcopy(body['profile']),'_meta':{'is_demo':True}})
session=dict(format='nikke-tools-session-v1',snapshot=snapshot,profile=body['profile'],
    teams=[body['squad']],singleMode=True,raidCount=1,activeTeam=0,patches=body['patches'],deltas=body['stat_deltas'],
    settings={'duration':body['duration'],'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':25,
              'burst-policy':'rules','shooting-policy':'character','burst-gauge-mode':'accumulate',
              'random-seed':12345,'detail-backend':'cuda_verified'})
for kind,data in [('api',body),('ui',session)]:
    (ROOT/f'research/detail-charge-immunity-{kind}-fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created fictional Liberalio owned growth fixtures, core enabled; no omitted source skills')
