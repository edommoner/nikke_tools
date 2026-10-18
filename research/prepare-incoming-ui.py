"""Prepare a fictional saved session and a production-parser validation script."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'web/index.html';text=p.read_text(encoding='utf-8')
old='コア・距離・敵の防御力と被ダメージ変化に対応しています。敵の攻撃・座標・生存などはGPUで未対応です。'
new='コア・距離・敵バフに加え、敵の攻撃対象、シールド・遮蔽物・分身・HPの被弾、不屈・無敵・被ダメージ分配をGPUで処理します。戦闘不能・復活、敵からのデバフ、座標などは未対応です。'
assert old in text or new in text
if old in text:text=text.replace(old,new);p.write_text(text,encoding='utf-8')
source=(ROOT/'research/prepare-boss-buffs-ui-fixture.py').read_text(encoding='utf-8').replace('detail-boss-buffs-','detail-incoming-').replace('user:gpu-boss-buffs','user:gpu-incoming').replace('GPU検証：コア・距離・敵バフ','GPU検証：敵の攻撃・HP変化').replace('防御1.5倍・被ダメージ−25%','防御1.3倍・被ダメージ−20%')
exec(compile(source,str(ROOT/'research/prepare-boss-buffs-ui-fixture.py'),'exec'),{'__file__':str(ROOT/'research/prepare-boss-buffs-ui-fixture.py'),'__name__':'incoming_ui_fixture'})
source=(ROOT/'scripts/verify-boss-buffs-ui-session.mjs').read_text(encoding='utf-8').replace('detail-boss-buffs-','detail-incoming-').replace('verify-boss-buffs-ui-session.mjs','verify-incoming-ui-session.mjs').replace("session.enemyPatterns.length,4","session.enemyPatterns.length,3").replace("p.kind==='buff').length,2","p.kind==='buff').length,1").replace('patterns:4','patterns:3').replace('the API-tested profile, deltas and boss conditions','the API smoke input profile, deltas and boss conditions; API execution is verified separately')
(ROOT/'scripts/verify-incoming-ui-session.mjs').write_text(source,encoding='utf-8')
