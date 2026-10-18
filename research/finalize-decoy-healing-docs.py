"""Document accepted decoy-healing scope after ordinary acceptance."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
focused=json.loads((ROOT/'research/detail-decoy-healing-production-verification.json').read_text(encoding='utf-8'));assert focused['passed'] and focused['tests_run']==10 and not focused['skipped']
for path in ('research/detail-decoy-healing-api-verification.json','research/detail-decoy-healing-browser-verification.json'):assert json.loads((ROOT/path).read_text(encoding='utf-8'))['passed']
p=ROOT/'README.md';text=p.read_text(encoding='utf-8');assert '## GPU詳細計算 v38' not in text
section='''## GPU詳細計算 v38

ライのデコイ回復をGPUで処理します。発動者の最終最大HPまたは対象のデコイ容量を基準にし、生成時刻が新しいものから回復します。同時刻なら元の保持順を使います。完全に消滅したデコイを新規生成せず、複数対象の一部だけ残量が0の場合は固定CPU版の回復規則に合わせます。周期回復・重複対象・発動者の戦闘不能も含めています。

専用21、ライの実スキルを省かない7部隊、既存の層処理/HP/遮蔽物/戦闘不能/復活73を、native/PTXそれぞれで照合しました。各101ケースで部隊合計・各人・バースト・基礎ステータス・両乱数状態・HP/遮蔽物推移に加え、デコイの名前別残量・容量・保持数を毎フレーム比較します。CPU観測値はGPU入力に渡しません。通常経路の重点10テスト（101部隊ケースと境界7件）、画面/APIからのCPU照合付き/GPU単独、Node26件も通過しました。v38で全128テストを再実行したという記録ではありません。

`research/detail-decoy-healing-checkpoint.json` に検証範囲を保存します。`research/detail-decoy-healing-ui-fixture.json` は架空の育成・装備データで、ライ/ベアーキューブLv4/スキル7・5・9を通常画面から確認できます。102,183,669→仮ATK＋12,000/HP＋100,000/DEF＋250で104,575,894となり、CPU版と一致しました。実アカウント取り込みと高速化は未検証です。

先頭のライが戦闘不能となる配置では、固定CPU版でもバーストに入らず戦闘不能のまま残るケースがあり、これも負の対照として一致を確認しています。復活する別配置と区別し、復活だけでは消滅したデコイを再生成しない固定版の挙動も確認します。これは実機の判断やモデルの正しさを保証しません。

固定版データの通常154/203人、宝もの等605/812条件が変換可能です。変換可能という集計は全編成での一致を意味しません。回復量の蓄積/分配、与回復量、ベイの被ダメージ分配、敵デバフ/DOT、座標などに未対応が残ります。全キャラ・全特殊効果のGPU化は継続中です。

'''
needle='## GPU詳細計算 v37\n';assert needle in text;text=text.replace(needle,section+needle,1);p.write_text(text,encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';j=json.loads(p.read_text(encoding='utf-8'));j['status']='v38 decoy healing native/PTX101 each, named every-frame quantities, boundary7, focused production10, API/browser and Node26 passed. Full objective incomplete.'
j['current_boundary']['gpu_compiler']='v38 supports decoy healing with live caster-maximum-HP or snapshot-capacity bases, newest activation order and stable equal-time order, plus prior supported paths. Unsupported definitions remain rejected.'
j['next_required_work'][0]['requirements']=['Continue heal_overcharge_store, outgoing healing and healing split/storage through independent CPU references and actual raw squads.','Continue received_dmg_split/Bay, cover controls, enemy debuffs/DOT, geometry and pinned CPU/model omissions.']
j['decoy_healing_checkpoint']='research/detail-decoy-healing-checkpoint.json';j['objective_complete']=False;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Updated verified v38 scope and remaining effects.')
