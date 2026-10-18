"""Publish verified scope only after production/API/browser gates pass."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
focused=json.loads((ROOT/'research/detail-cover-capacity-production-verification.json').read_text(encoding='utf-8'));assert focused['passed'] and focused['tests_run']==10 and not focused['skipped']
for path in ('research/detail-cover-capacity-api-verification.json','research/detail-cover-capacity-browser-verification.json'):assert json.loads((ROOT/path).read_text(encoding='utf-8'))['passed']
p=ROOT/'README.md';text=p.read_text(encoding='utf-8');assert '## GPU詳細計算 v37' not in text
section='''## GPU詳細計算 v37

ティアやレリックカバーキューブの「発動者の最大HPを参照する遮蔽物HP増加」をGPUで計算します。通常の遮蔽物HP割合とは別に合算し、最大HPの変化・期限切れ・対象の確定順も反映します。破壊済みの遮蔽物は最大HPが増えても復活させません。CPUの専用照会に合わせ、ダメージ計算用の対象別弾数スタック補正を使わずに値を読みます。

専用15、ティアの実スキル部隊6、モラン/A2のカバーキューブ装備2、既存の遮蔽物・回復・HP通知・戦闘不能・復活74を、native/PTXそれぞれで照合しました。各97ケースで部隊合計・各人・バースト・基礎ステータス・HP/遮蔽物推移・乱数状態を確認しています。通常経路は変更箇所を対象に10テスト（97部隊ケースと境界6件）を再実行し、APIと画面からのCPU照合付き/GPU単独も通過しました。v37で全118テストを再実行したという記録ではありません。前版の広い108テストはv36の履歴として保存しています。

`research/detail-cover-capacity-checkpoint.json` に検証範囲を記録します。`research/detail-cover-capacity-ui-fixture.json` は架空の育成・装備データで、ティアとカバーキューブLv4を通常画面から確認できます。124,093,862→仮ATK＋12,000/HP＋100,000/DEF＋250で126,240,621となり、部隊全体でCPUと一致しました。実アカウント取り込み成功や高速化を示すものではありません。

固定版データの通常153/203人、宝もの等601/812条件は変換可能です。変換可能という集計は全編成での一致を意味しません。ベイの被ダメージ分配、デコイ回復、回復量の蓄積、敵デバフ/DOT、座標などは引き続き未対応です。次のデコイ回復は`research/detail-decoy-healing-cpu-reference.json`にCPU専用の10ケースを整理しており、GPU対応としては数えていません。

'''
needle='## GPU詳細計算 v36\n';assert needle in text;text=text.replace(needle,section+needle,1);p.write_text(text,encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';j=json.loads(p.read_text(encoding='utf-8'));j['status']='v37 caster-max-HP cover capacity native/PTX97 each, boundary6, focused production10 (97 squad cases), API/browser and Node26 passed. Full objective incomplete.'
j['current_boundary']['gpu_compiler']='v37 covers original-caster live-maximum-HP cover capacity, with direct CPU value semantics for percentage and flat cover carriers, plus all prior supported paths. Remaining definitions reject explicitly.'
j['next_required_work'][0]['requirements']=['Port decoy_heal_pct using the CPU-only ten-case reference; include same-time stable healing order and zero-HP recipients retained in a multi-recipient carrier.','Continue received_dmg_split/Bay, cover controls, healing overcharge storage, enemy debuffs/DOT, geometry and pinned engine omissions.']
j['cover_capacity_checkpoint']='research/detail-cover-capacity-checkpoint.json';j['objective_complete']=False;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated verified v37 scope and explicit remaining work.')
