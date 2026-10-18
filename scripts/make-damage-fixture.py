import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,a
b=body_for(['리타','마스트 : 로망틱 메이드','치사토','아니스 : 스파클링 서머','헬름'],60,True);b.update(compute_backend='cuda_detail',verify_detail=True)
p=b['profile'];snapshot=a.import_data({**p,'_meta':{'is_demo':True}})
u={'format':'nikke-tools-session-v1','snapshot':snapshot,'profile':p,'teams':[b['squad']],'singleMode':True,'raidCount':1,'activeTeam':0,'patches':{},'deltas':{},'settings':{'duration':60,'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':25,'burst-policy':'auto','detail-backend':'cuda_verified'}}
(ROOT/'research/detail-damage-api-fixture.json').write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8');(ROOT/'research/detail-damage-ui-fixture.json').write_text(json.dumps(u,ensure_ascii=False,indent=2),encoding='utf-8')
