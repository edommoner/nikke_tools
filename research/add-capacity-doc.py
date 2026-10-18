"""Publish capacity documentation only after the verified v29 checkpoint."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'research/detail-capacity-checkpoint.json').read_text(encoding='utf-8'))
assert c['passed'] and c['abi']=='detail_capacity_v29'
path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
marker='効果・名前付き状態の上限拡張（v29）'
assert marker not in text
text=text.replace('（`research/detail-capacity-cpu-audit.json`）','（`research/ports/v28/research/detail-capacity-cpu-audit.json`）')
text=text.replace('今後は効果数に依存するビット列・状態領域も含めて容量を拡張します。','この容量制限はv29で拡張しました。')
doc=f'''{marker}を実装しました。1部隊の定義数と名前付き状態を128から256へ拡張し、バースト追加ダメージが除外する後続バフと、発動回数軽減の参照ビット列も256ビットへ変更しました。所有者や共有発動回数の参照を保持し、旧領域と重ならない位置に配置しています。ABIは `detail_capacity_v29`、効果行は286要素、作業領域は1部隊{c['workspace_bytes_per_squad']:,}バイトです。上限超過・動的スロット超過は結果を採用せず、通常画面では理由付きでCPUへ切り替えます。

架空の所持・装備データで、v28では128件の上限により拒否された172件・98状態の5人編成を照合しました。自動／周期バースト、射撃オート／キャラ別操作、固定ゲージ／実蓄積の8通りについて、nativeとPTXで部隊合計・各メンバー・バースト履歴・基礎ステータス・パーツ結果・最終乱数状態が一致しています。効果番号31／32／127／128／255の軽減参照、129番以降の部隊共有発動回数、235件の編成でのB3バフ除外も照合し、計30ケースが通過しました。nativeでは172件の編成を180秒まで追加確認しています。`python scripts/verify-capacity-detail.py --backend both` と `--backend native --long --output research/detail-capacity-long-verification.json` で再実行できます。

現在の受理キャラ135人の5人編成を各1条件ずつ照合したnative／PTX計270ケース、所持装備・仮ステータス・配置変更・マスト運用を組み合わせた36ケース、Pythonの通常経路57テスト、Node22テストが通過しました。通常APIの172件編成は{c['normal_api_total']:,}、通常画面のD編成は{c['normal_ui_total']:,}がCPU版と一致しました。通常画面上部の「詳細計算」で「GPU詳細＋CPU照合」を選び、「この部隊を計算」で実行できます。照合には独立したCPU戦闘計算を使い、CPUが決めた発動履歴やダメージをGPU入力へ流用していません。育成データは架空であり、実アカウントの取り込み成功の検証とは区別しています。

記録は `research/detail-capacity-verification.json`、`research/detail-capacity-long-verification.json`、`research/detail-catalog-capacity-verification.json`、`research/detail-normal-acceptance.json`、`research/detail-owned-acceptance.json`、`research/detail-capacity-api-verification.json`、`research/detail-capacity-ui-verification.json`、ソース照合付きの `research/detail-capacity-checkpoint.json` にあります。容量準備監査は `research/detail-capacity-cpu-audit.json`、v28の失敗時の監査は `research/ports/v28/research/detail-capacity-cpu-audit.json` です。

容量拡張によって対応するキャラや特殊効果が増えたわけではありません。コンパイル受理は135／203人、宝ものを含む条件は529／812のままで、全キャラ・全特殊効果の移植は継続中です。動的な有効バフの512スロット、対象履歴などには別の上限があり、全編成・全条件の一致や速度向上を示す検証ではありません。

'''
anchor='## 詳細GPU版の実装・CPU照合\n\n'
assert anchor in text;text=text.replace(anchor,anchor+doc,1)
path.write_text(text,encoding='utf-8');print('README v29 added')
