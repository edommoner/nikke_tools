import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
body=json.loads((ROOT/'research/detail-burst-stage-api-fixture.json').read_text(encoding='utf-8'))
old='D';who=body['squad'][0]
ui=json.loads((ROOT/'research/detail-burst-gauge-ui-fixture.json').read_text(encoding='utf-8'))
def rename(value):
 if isinstance(value,dict):return {(who if k==old else k):rename(v) for k,v in value.items()}
 if isinstance(value,list):return [rename(v) for v in value]
 return who if value==old else value
ui=rename(ui);ui['snapshot']['snapshot_id']='synthetic-burst-stage-v18'
(ROOT/'research/detail-burst-stage-ui-fixture.json').write_text(json.dumps(ui,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
