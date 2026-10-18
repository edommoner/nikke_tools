"""Fictional owned growth for normal GPU UI/API acceptance, favorite stage zero."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for

body=body_for(['센티','리타','크라운','앨리스','모더니아'],35,True)
body.update(shooting_policy='character',burst_policy='rules',burst_gauge_mode='accumulate',
            seed=12345,compute_backend='cuda_detail',verify_detail=True)
for i,(name,char) in enumerate(body['profile']['chars'].items()):
    char['breakthrough']=i%4;char['core_enhancement']=4 if i%4==3 else 0
    char['cube']={'name':'렐릭 베어 큐브','level':1+3*i}
    for gear in char['equipment'].values():gear['level']=i%6
    char['equip_skills'].update(atk_pct=[11.11,11.11,12.34],charge_speed_pct=[2.34,2.34,4.3])
body['patches']={'센티':{'skill_levels':{'1':8},'equip_skills':{'charge_speed_pct':[3.2,3.2,5.1]}}}
body['stat_deltas']={'센티':{'atk':12345,'hp':100000,'def':345}}
snapshot=a.import_data({**copy.deepcopy(body['profile']),'_meta':{'is_demo':True}})
session=dict(format='nikke-tools-session-v1',snapshot=snapshot,profile=body['profile'],
    teams=[body['squad']],singleMode=True,raidCount=1,activeTeam=0,patches=body['patches'],deltas=body['stat_deltas'],
    settings={'duration':35,'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':25,
              'burst-policy':'rules','shooting-policy':'character','burst-gauge-mode':'accumulate',
              'random-seed':12345,'detail-backend':'cuda_verified'})
for kind,data in [('api',body),('ui',session)]:
    (ROOT/f'research/detail-shields-{kind}-fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created fictional Centi full-squad owned growth fixtures')
