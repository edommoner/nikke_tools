"""Publish the verified v30 repair and retain the broader migration scope."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'research/detail-named-capacity-checkpoint.json').read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_named_capacity_v30'
path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
marker='名前付きバフ延長の256状態対応漏れ（v30）'
assert marker not in text
doc=f'''{marker}を修正しました。v29の効果数拡張後も、`named_buff_duration_extend` の参照が128ビットのまま残っていました。状態番号128以上の延長対象ではホストの配列例外を再現しています。参照領域を独立した8ワードへ移し、GPUも状態番号から直接ワードを選ぶ方式に統一しました。新ABIは `detail_named_capacity_v30`、効果行は294要素、作業領域は1部隊{c['workspace_bytes_per_squad']:,}バイトです。B3除外・発動回数軽減の参照位置は維持しています。状態番号256以上は明示的に拒否します。

状態番号31／32から254／255までの各ワード境界で、延長・短縮の32ケースを独立したCPU計算と照合しました。通常バフ、継続ダメージのタイマー、クラストの速射→フルチャージと保持→発射を加え、native／PTX計76ケースが一致しています。クラストの実スキルを残し、効果のない129定義を追加して状態番号141を意図的に作っています。実アカウントで自然にその番号になったという検証ではありません。180秒の2ケースでも延長発動をCPU側で観測し、部隊合計・各キャラ・バースト履歴・基礎ステータス・最終乱数状態が一致しました。

新しい形式で、従来の容量テスト30ケース、対応135人の検証編成をnative／PTXで各1条件ずつ計270ケース、既存の名前付き操作のPTX回帰{c['low_state_ptx_cases']}ケース、Python64テストとNode22テストが通過しました。高い状態番号・延長値の符号・空のプログラムを混ぜた33プログラムを5回の実バッチ実行に分け、参照が他部隊へ混線しないことも確認しました。通常APIは{c['normal_api_total']:,}、通常画面のD編成は{c['normal_ui_total']:,}がCPUと一致しています。所持・装備データは架空の値です。

記録は `research/detail-named-capacity-verification.json`、`research/detail-named-capacity-long-verification.json`、`research/detail-named-capacity-batch-verification.json`、`research/detail-capacity-named-mask-verification.json`、`research/detail-catalog-named-capacity-verification.json`、`research/detail-named-low-ptx-verification.json`、`research/detail-normal-acceptance.json`、`research/detail-named-capacity-api-verification.json`、`research/detail-named-capacity-ui-verification.json` にあり、ソースと結果の照合は `research/detail-named-capacity-checkpoint.json` に保存しています。再実行は `python scripts/verify-named-capacity-detail.py --backend both`、長時間は `--backend native --long --output research/detail-named-capacity-long-verification.json`、混在バッチは `python scripts/verify-named-capacity-batch.py` です。修正前の記録は `research/ports/v29/research/detail-named-capacity-before.json` と `research/ports/v29/research/detail-normal-acceptance.json` に残しています。

今回の修正で対応キャラ数は増えていません。受理は135／203人、宝ものを含む条件は529／812で、全キャラ・全特殊効果の移植は未完了です。ボスのライブ挙動・座標・被弾・遮蔽・復活などの統合依存関係は `research/boss-gpu-integration-notes.json` に記録しています。固定パーツ以外のボス機能を実装済みと示す資料ではありません。

'''
anchor='## 詳細GPU版の実装・CPU照合\n\n';assert anchor in text
text=text.replace(anchor,anchor+doc,1);path.write_text(text,encoding='utf-8')
print('README v30 repair added')
