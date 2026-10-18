import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('v',Path('scripts/verify-extended-detail.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
b=dict(v.scenarios(False)[-1][1]);b.update(compute_backend='cuda_detail',verify_detail=True)
p=b['profile'];snapshot=v.a.import_data({**p,'_meta':{'is_demo':True}})
data={'format':'nikke-tools-session-v1','snapshot':snapshot,'profile':p,'teams':[b['squad']],'singleMode':True,'raidCount':1,'activeTeam':0,'patches':b.get('patches',{}),'deltas':b.get('stat_deltas',{}),'settings':{'duration':180,'level':400,'enemy-def':31784,'enemy-code':'풍압','core':50,'distance':25,'burst-policy':b['burst_policy'],'detail-backend':'cuda_verified'}}
Path('research/detail-crown-ui-fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
Path('research/detail-crown-api-fixture.json').write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8')
print('Created Crown + Alice owned-growth UI/API fixtures')
