# 元エマの被弾確率・回復条件

`original-probability-conditions` は元エマ編成の70定義を保持する30秒の4条件。既存ordered catalogue adapter、共通のsampled RNG、状態・イベント実行器、全戦闘比較器を使う。

| 条件 | 実被弾 | 元確率回復の実発動数 |
| --- | ---: | ---: |
| control | 0 | 0 |
| self-chipped | エマ64回 | 6 |
| self-wounded | 初期負傷1回＋エマ64回 | 6 |
| ally-chipped | ドレイク64回 | 0 |

元`received_hit_count:1`/`prob:5`を保持する。64連撃は既存の単一attack nodeの`hits=64, interval=.04`で宣言し、GPUへ発動時刻や確率判定結果を渡さない。初期負傷も実敵攻撃で作り、HP状態を直接書き換えない。全64/65被弾の件数、実HP被害、発動者、成功/不発、正の回復、回復直前のHP90%条件の高/低を検査する。別の味方が被弾しただけではエマ本人の回復を発動させず、元burstは負傷した味方を実際に回復する。

共通の受動観測器を拡張し、元instant handlerの実dispatchを元source rowへ記録する。HP/cover/hp_pctは保存状態だけを読み、追加の対象解決・数値照会はしない。既存timer activation readbackと照合する。全battle/weapon/skill/typed/history/healthと既存のsampled RNG比較も保持し、seed4301の結果をCUDA/Metal別の期待値へ分岐しない。

6/64は確率の統計的な推定ではない。この4条件は固定seedにおける元確率判定と回復の統合検証であり、全seed・全条件の認定ではない。既存の共通座標数値規約を使うprivate sampled worldで、通常UIの既定CPUモデルや実ゲーム空間規則を変更しない。

## 実GPUと保存結果

固定87c82125/package `50c273ee524def49300966f6b451c8a16cb08a4f5970a7695b35e717417e2817` のM5実GPU1回で4条件が一致。27群228テスト、fresh CPU4/104.170975秒、GPU3.152702秒。readback32,512,000byte。generation/pipeline必須hit、Slang呼出し0。pipeline API0.002964秒・library準備API0.007637秒は正の実測値。

GPU source、wire、Runtime、保護CPU4ファイル、strict normalizerは変更0。既存support/ビスケットを含む12テストも成功。最初の探索では64個の別attack nodeが既存32node容量に収まらずCPU準備で停止した。その失敗を保持し、64回という実被弾数を減らさず既存連撃入力へ表現を修正した。単体テストの初版診断文不一致も保存。今回のGPU失敗0/同claim retry0。

別fresh GPU禁止childの独立sealは117.877019秒/native4/parent receipt再利用なしで成功。goldenは `research/portable-original-probability-conditions-v1-expected.json`、独立receiptは `tests/fixtures/original-probability-conditions-independent-v1.json`、保存rawの件数は `tests/fixtures/original-probability-gpu-counts-v1.json`。原capture/input/readback/claimは保持し、追加GPU0。

## 共通CLIと未対応分類

共通CLIは `package --suite original-probability-conditions --out NEW.zip` → `unpack` → 固定packet自身の `run`。追加の元sceneは `original-catalogue-ordered` を使い、個別kernelや比較器を複製しない。

`original-probability-conditions-cache-only` は同じ4入力/source/golden/比較器にCUBIN/O1、compile cache必須hitとpaired generation必須hitを要求する。fallback compileを許さず、compile-planとsource certificateを実CUDA/driver成功へ昇格しない。現CUDA実機は未検証、今回Windows追加依頼0。

静的監査は前回の517依存、model-checkは記録されたroot10依存のSHA不変を再検査して再利用した。既存CLIのentry-planで保存inventoryの順位だけを再計算し、native/GPUを実行しない。元266profile中packing254/失敗12、先頭のreceived_dmg_splitは4profileに影響する正本仕様不足のまま。過去のGPU証明書がcurrent-sourceではないという制約も維持する。

catalogue1084は条件別scene数で、GPU対応済み人数ではない。全キャラ・全特殊効果・公開GPU受付は未完了。小証跡は `research/target-count-query-evidence/original-probability-conditions-metal-v1.json`、proof stemは `.portable-recovery/proofs/original-probability-conditions*20261030*`。
