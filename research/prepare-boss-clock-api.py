import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'research/detail-named-capacity-api-fixture.json').read_text(encoding='utf-8'))
p['duration']=20
p['enemy']['core_px']=0
p['enemy']['patterns']=[dict(id='core-window',kind='core',delay=.7,until={'time':1.1},core_px=6,after=['start','core-window'],repeat=0),dict(id='near-window',kind='move',delay=2,until={'time':3},distance=5)]
(ROOT/'research/detail-boss-clock-api-fixture.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=(ROOT/'scripts/smoke-detail.mjs').read_text(encoding='utf-8')
s=s.replace("const port=4330", "const port=4333")
s=s.replace("const c=await job", "for(const row of g.results){assert.ok(row.result.boss_timeline.length>0);assert.equal(row.result.compute.cpu_verification.boss_timeline_equal,true);}\n const c=await job")
s=s.replace("console.log(JSON.stringify(report));", "report.boss_timeline=g.results[1].result.boss_timeline;report.patterns_verified=true;writeFileSync('research/detail-boss-clock-api-verification.json',JSON.stringify(report,null,2)+'\\n');console.log(JSON.stringify(report));")
s=s.replace("'scripts/smoke-detail.mjs',", "'scripts/smoke-detail-boss-clock.mjs','app/detail_boss.py','web/phase-model.mjs',")
(ROOT/'scripts/smoke-detail-boss-clock.mjs').write_text(s,encoding='utf-8')
p=ROOT/'web/index.html';s=p.read_text(encoding='utf-8').replace('座標・移動・阻止部位は扱いません。','座標・パーツ個別の移動・阻止部位は扱いません。').replace('複数のコアは最大値、距離は後から始まった行動を使います。','コアを出し入れする場合、基本のコア径を0にしてください。複数のコアは最大値、距離は後から始まった行動を使い、同時開始なら下の行を優先します。');p.write_text(s,encoding='utf-8')
