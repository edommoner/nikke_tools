import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'research/detail-boss-clock-api-fixture.json').read_text(encoding='utf-8'))
p['enemy']['patterns'] += [dict(id='armor',kind='buff',delay=1,until={'time':4},enemy={'def_mult':1.5,'def_add':-1000,'received_dmg_pct':-25}),dict(id='exposed',kind='buff',delay=3,until={'time':7},enemy={'def_mult':.7,'received_dmg_pct':33.33},irremovable=True)]
(ROOT/'research/detail-boss-buffs-api-fixture.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=(ROOT/'scripts/smoke-detail-boss-clock.mjs').read_text(encoding='utf-8').replace("kind:'buff',enemy:{def_mult:2}","kind:'vanish'").replace('detail-boss-clock-api-verification.json','detail-boss-buffs-api-verification.json').replace("'scripts/smoke-detail-boss-clock.mjs'","'scripts/smoke-detail-boss-buffs.mjs'")
(ROOT/'scripts/smoke-detail-boss-buffs.mjs').write_text(s,encoding='utf-8')
p=ROOT/'web/app.js';s=p.read_text(encoding='utf-8').replace("r.event==='start'?'開始':'終了'","r.event==='start'?'開始':r.event==='dispel'?'解除':'終了'");p.write_text(s,encoding='utf-8')
p=ROOT/'web/index.html';s=p.read_text(encoding='utf-8').replace('移動・コア以外のボス行動や座標・生存などはGPUで未対応です。','コア・距離・敵の防御力と被ダメージ変化に対応しています。敵の攻撃・座標・生存などはGPUで未対応です。');p.write_text(s,encoding='utf-8')
