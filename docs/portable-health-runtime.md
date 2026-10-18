# 共通の味方HP・防御・回復

`gpu/health_runtime.slang` を共通イベント実行器へ接続しました。CUDA／Metalは同じ状態・数値演算・効果定義・fixtureを使います。CPUで回復量や途中のHPを計算してGPUへ渡しません。

## 入力と状態

`environment.allies` は5人分の初期状態で、各要素に `base_hp`、`hp`、`base_defense` を指定できます。省略時は基礎／現在HPが1,000,000、防御0です。基礎HPは正、現在HPは0以上・基礎HP以下、基礎防御は非負、すべて有限値とし、有効最大HPや履歴などの計算済み状態は受け付けません。

GPUで現在HP、有効最大HP、HP割合、有効防御、実際に増えた回復HPを保持し、各queryと最終状態の `allies` から読み戻します。割合・量・加算順は共通のsoftware binary64を使います。最大HPが非正または非有限になればstatus 16で拒否します。

ABIは `0x5045563A`、入力8,192語・出力20,480語です。HPの全queryを保持するため出力を拡張しました。Swiftには転送レイアウトの上限だけを変更し、HP計算は置いていません。

## 接続した効果

- `def_pct` と `def_caster_based_pct`：受領者の基礎防御への百分率と、施術者の基礎防御からの定額加算を分けます。既存コンパイラーでは味方def_pctと敵防御低下に同じ数値IDを使うため、味方の防御効果であることを別途梱包し、敵へのダメージ計算へ混入させません。
- `max_hp_pct`／`max_hp_only_pct`：最大HPの百分率を集計します。前者は既存モデルの規約に従い、1適用分の施術者基礎HP×百分率を現在HPへ付与し、後者は現在HPを増やしません。受領者側の最大HPと施術者側の付与基準を同一と仮定しません。
- `hp_caster_based_pct`／`hp_only_caster_based_pct`：施術者の基礎HPから求めた定額分を最大HPへ加えます。前者だけ現在HPも付与します。
- `max_hp_from_max_hp_pct`：適用時の施術者の有効最大HPからスナップショットを作ります。更新時は自分の旧スナップショットを一度除いて測り、増えた差分だけ現在HPへ付与します。失効後の再適用は新しいスナップショットと付与を作り、古い差分を引き継ぎません。
- `heal_hp_pct`：通常は受領者の基礎HP、`scaling: max_hp` は施術者の有効最大HPを基準にします。受領者の `heal_received_pct` と施術者の `outgoing_heal_pct` をそれぞれ0以上の倍率に制限して乗算します。後者は既存の宣言済みCPUモデルを共用した規約です。
- `current_hp_reduce`：現在HPに `1 − value / 100` を乗じ、下限0へ制限します。最大HPから定額を引く処理ではありません。

現在HPの付与は体力回復として数えません。通常の回復は最大HPで制限し、回復量0や満タンへの回復でも元の受領者へ `event:heal_received` を1回送ります。施術者の情報を通知に保持するため、`not_self_caused_heal` を評価できます。

チーム回復の受領者は部隊順です。各受領者への適用とその同期した子通知を完了してから次へ進みます。例えば最初の受領者の回復通知で施術者の最大HPが増えた場合、後続の施術者最大HP基準の回復は更新後の値を読みます。GPU内の同じ明示スタックを使い、通知の再入や回数制限も共通実行器で処理します。

`self_hp_above`、`self_hp_below`、`self_hp_max`、`ally_hp_below` を接続しました。above／belowは境界を含みます。無期限passiveの条件は再評価し、ally_hp_belowは発動時の「該当者がいるか」と、読み取り時の受領者自身の割合を区別します。

## CPUとの差異と検証

固定CPUでは `max_hp_pct` の失効時に現在HPを切り詰めず、現在1,500／最大1,000が残る場合があります。共通GPUは現在HPをその時点の最大HP以下に保持します。`max-hp-expiry-clamps-to-current-maximum` ではGPUの手書き期待値1,000とCPUの実観測1,500を分けて検査し、`known_health_cpu_differences` に保存します。この差異へ合わせるためにGPUの上限を外していません。

25ケースの手書き期待値は `tests/fixtures/portable-health.json` にあり、統合検証は212正例・7拒否です。GPUの読み戻し後、独立したCPUのBuffManagerとinstant handlersを実行し、上記1件以外では全員のHP・最大HP・割合・防御と攻撃補正を一致させます。CPUの実行結果はGPU入力にしません。実回復量と既知差異の正しさは手書き期待値でも検査します。

HTTP APIは受領者間の子通知順とHP／回復量、初期HPが不正な場合の400応答を検証します。旧イベント16ケース・拒否2件、単体19件、全203体の効果を除く武器動作の回帰も維持しています。

HP・防御の定義がないときの走査と、HPに関係しない効果の重複同期を省きました。同じ共通ソースの全走査版と、32定義・64入力・3秒間のGPU進行を各3回比較し、入力／全出力ハッシュを一致させています。MetalのGPU時間中央値は184.27msから81.60msへ約55.7%短縮しました。これは固定した機構測定であり、実編成の速度を証明するものではありません。

```sh
.venv/bin/python scripts/verify-portable-combat.py --backend metal
.venv/bin/python scripts/verify-portable-api.py --backend metal
.venv/bin/python scripts/benchmark-portable-health.py --label before
.venv/bin/python scripts/benchmark-portable-health.py --label after
```

最新の両GPU照合状況は `research/portable-combat-checkpoint.json`、前段187ケースの両GPU一致は `portable-combat-v9-checkpoint.json` に固定しています。

## 残る接続

敵からの被弾・防御計算、HP閾値を横切る通知、ダウン／復活、lifesteal、回復の共有／蓄積、シールド・カバー、対象の動的な選択と複数キャリア、HPに基づくスケーリングは未接続です。受け付けない効果・条件・対象指定は引き続き拒否します。実編成のGPU検証済みは0体、通常画面もCPUのままです。全203体の入力監査や武器だけの成功を、全キャラ・全特殊効果の対応済み件数には加えません。
