"""Fictional owned Trina squad for normal API acceptance, no skill injection."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
body=json.loads((ROOT/'research/detail-live-parts-api-fixture.json').read_text(encoding='utf-8'))
old=body['squad'][0];new='트리나'
body['squad'][0]=new
body['profile']['chars'][new]=body['profile']['chars'].pop(old)
for field in ('patches','stat_deltas'):
    if old in body.get(field,{}):body[field][new]=body[field].pop(old)
body['duration']=31
(ROOT/'research/detail-ally-conditions-api-fixture.json').write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Fictional owned Trina API fixture saved; no live-account or positive-low-HP claim')
