"""Document the verified v39 model and preserve the larger unfinished scope."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
focused=json.loads((ROOT/'research/detail-outgoing-healing-production-verification.json').read_text(encoding='utf-8'));assert focused['passed'] and focused['tests_run']==8 and not focused['skipped']
for path in ('research/detail-outgoing-healing-api-verification.json','research/detail-outgoing-healing-browser-verification.json'):assert json.loads((ROOT/path).read_text(encoding='utf-8'))['passed']
p=ROOT/'README.md';text=p.read_text(encoding='utf-8');assert '## GPU詳細計算 v39' not in text
section='''## GPU詳細計算 v39

与える体力回復量の増加とレリックヒーリングキューブをGPUで処理します。元のCPUエンジンにはこの効果が未実装だったため、上流の固定ソースは変更せず `app/outgoing_healing_compat.py` でCPU参照モデルを補っています。体力回復は「元の回復量 × 受け手の回復倍率 × 回復を使ったキャラの与回復倍率」です。各倍率を0以上に制限し、同じ種類の補正を加算します。吸血の回復元は攻撃者とする固定版の既存規約を使います。遮蔽物・シールド・デコイの修復や復活には、この体力回復用の倍率を追加しません。実機で全相互作用を検証したという意味ではありません。

専用19ケース、プリカ/シラツルの実スキルを省かない4部隊（通常育成とヒーリングキューブLv4装備）、既存のHP・遮蔽物・デコイ・戦闘不能/復活など101ケースをnative/PTXそれぞれで照合しました。各124ケースで部隊合計・各人・バースト時刻・基礎ステータス・HP/遮蔽物推移・乱数状態等を比較します。CPU観測値をGPU入力には使いません。別途手計算7件、通常経路の重点8テスト（124部隊ケースと境界5件）、API/画面のCPU照合付き/GPU単独、Node26件も通過しています。通常経路の全テストをv39で再実行したという記録ではありません。

`research/detail-outgoing-healing-checkpoint.json` に検証範囲を保存します。`research/detail-outgoing-healing-ui-fixture.json` は架空の所持・装備データです。プリカ/ヒーリングキューブLv4/スキル7・5・9、30秒・バーストゲージ実蓄積で、取り込み時88,288,865から仮ATK＋12,000/HP＋100,000/DEF＋250で91,290,847となり、CPU補完モデルとGPUで一致します。実アカウント取り込みと高速化は未検証です。

固定版データの通常156/203人、宝もの等613/812条件が変換可能です。変換可能という集計は全編成での一致を意味しません。ソラの回復量保存、ミサトのシールド関連効果など、別の未対応効果を持つ編成は引き続き拒否します。回復量の蓄積/分配、被ダメージ分配、敵デバフ/DOT、座標やCPUモデルの不足を含め、全キャラ・全特殊効果のGPU化は継続中です。

'''
needle='## GPU詳細計算 v38\n';assert needle in text;text=text.replace(needle,section+needle,1);p.write_text(text,encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';j=json.loads(p.read_text(encoding='utf-8'));j['status']='v39 outgoing body healing and Healing cube: declared CPU model, native/PTX124 each, boundary5, focused production8, API/browser and Node26 passed. Full objective incomplete.'
j['current_boundary']['gpu_compiler']='v39 supports outgoing healing source/recipient multipliers and Healing cube in the declared CPU extension, plus prior supported paths. Other unsupported definitions still reject.'
j['next_required_work'][0]['requirements']=['Continue heal_overcharge_store, heal_overcharge_store_atk_pct/discharge and heal_split with explicit CPU and GPU models; do not treat ignored CPU stats as successful support.','Continue shield_dmg_pct/Misato, received_dmg_split/Bay, cover controls, enemy debuffs/DOT, geometry and pinned CPU/model omissions.']
j['outgoing_healing_checkpoint']='research/detail-outgoing-healing-checkpoint.json';j['objective_complete']=False;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Documented v39 CPU extension, verified scope and remaining full objective.')
