"""Fictional owned D squad for normal detailed API acceptance."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
body=json.loads((ROOT/'research/detail-ally-conditions-api-fixture.json').read_text(encoding='utf-8'))
old=body['squad'][0];new='D : 킬러 와이프';body['squad'][0]=new
body['profile']['chars'][new]=body['profile']['chars'].pop(old)
for key in ('patches','stat_deltas'):
    if old in body.get(key,{}):body[key][new]=body[key].pop(old)
body['enemy']['core_px']=5;body['duration']=31
(ROOT/'research/detail-team-hits-api-fixture.json').write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Fictional D owned API fixture saved; no live-account acceptance claim')
