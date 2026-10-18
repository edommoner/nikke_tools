import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('f',Path('scripts/verify-full-detail.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
b=f.fixture(12,grown=True);p=b['profile'];snapshot=f.adapter.import_data({**p,'_meta':{'is_demo':True}})
data={'format':'nikke-tools-session-v1','snapshot':snapshot,'profile':p,'teams':[b['squad']],'singleMode':True,'raidCount':1,'activeTeam':0,'patches':b['patches'],'deltas':b['stat_deltas'],'settings':{'duration':12,'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':25,'burst-policy':'auto','detail-backend':'cuda_verified'}}
Path('research/detail-ui-fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
Path('research/detail-api-fixture.json').write_text(json.dumps({**b,'compute_backend':'cuda_detail','verify_detail':True},ensure_ascii=False),encoding='utf-8')

