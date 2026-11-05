# 元ビスケットのHP閾値・発動上限

`original-threshold-conditions` は元ビスケット/ミランダ/ノア/センチ/ドレイクの72定義を保持する30秒の4ケース。同じordered catalogue adapter、状態・イベント実行器、全戦闘比較器を使う。キャラ別kernel、ダメージ計算器、第二の戦闘時計は追加しない。

| 条件 | 実入力 | 無敵/閾値回復の実発動数 |
| --- | --- | ---: |
| control | 被弾なし | 0 / 0 |
| first | 1秒にノアを負傷、2秒に後続被弾 | 1 / 1 |
| two | 上記に7秒のセンチ負傷、8秒の後続被弾 | 2 / 2 |
| exhausted | 上記に14秒のノア再負傷、14.1秒の後続被弾 | 2 / 2 |

外部攻撃のslotは1始まり。最初の後続被弾は実damageが正でHP/shield/cover/decoyの被害が全て0となり、元無敵が働く。2人目の後続被弾は実シールド吸収なので、無敵の独立証拠に数えない。3回目はHP50%未満に到達しても既存の発動上限で拒否され、回復dispatchなし、後続被弾はHPへ入る。

受動観測は既存support observerを共用する。`_activate`の呼出し回数ではなく、元の`_trigger_counts`が実際に増えた回数を元source rowごとに保存する。上限拒否の呼出しはattemptとして別記録。HP/cover/hp_pctは保存状態を読むだけで、追加の対象解決・数値照会はしない。GPUの既存timer activationsを同じ元rowへ逆対応させる。元武器・効果・owner・育成は変更せず、既存72定義のbindingも全件保持する。

## 現CPU規約とゲーム仕様を区別する

元正本の`ally_hp_below`は発動時にany-ally条件を見る。今回のinstant回復は防御型の解決済み対象へ入り、2人目が閾値に到達した時、既に50%超へ回復した1人目にも回復が入った。対象別のruntime buff条件と同じと推定しない。これを現在のCPU比較基準として固定するが、ゲーム仕様の認定ではない。保護CPU4ファイル・pinned upstreamは変更0。

前段CPU調査の受動観測あり/なしは全native結果が一致済み。出所は `research/target-count-query-evidence/original-biscuit-threshold-native-triage-v1.json`。今回の4条件は別の固定packetでfresh比較し、過去の調査結果をGPU成功へ付替えない。

## 実証とキャッシュ

固定035839db/package `7b188fc746322f169ac7cb405454158a4e0df1f771de249f5da367e54d34e101` のM5実GPU1回で全4一致。27群228テスト、fresh CPU4/74.072939秒、GPU2.444421秒、GPU child4.043789秒。readback32,512,000byte。generation/pipeline必須hit、Slang呼出し0。pipeline API0.003289秒・library準備API0.007911秒は正の実測値。

別fresh GPU禁止childの独立sealは85.135297秒/native4/parent receipt再利用なしで成功。保存GPU出力から元row2/3の実発動数0/1/2/2も再読し、input/rawのSHAを検査した。追加GPU0。同claim retry0。GPU273 source閉包と正規化CUDA/MSLは前のsupport4証跡と同一。今回GPU source/wire/Runtime/strict normalizer変更0。

共通CLIは `package --suite original-threshold-conditions --out NEW.zip` → `unpack` → 固定packet自身の `run`。追加の元sceneを調べる場合は `original-catalogue-ordered` を使う。goldenは `research/portable-original-threshold-conditions-v1-expected.json`、独立receiptは `tests/fixtures/original-threshold-conditions-independent-v1.json`、保存rawの発動数は `tests/fixtures/original-threshold-gpu-counts-v1.json`。

最終9ea39234のcache-only packet `84ffa9b9cf196626e6386a6f51f7d14919a37673b646f5bad0a5f2c68d6194d8` は29群257unitテスト成功。追加native全件/GPU実行はしていない。CUBIN/O1/2GiB/60秒compile-planはpolicy検査のみ成功した。

`original-threshold-conditions-cache-only` は同じ4入力・source・golden・比較器に、CUDA CUBIN/O1/compile cache必須hitとpaired generation必須hitを要求する。cache不在をfallback compileで隠さない。source certificateとcompile-planは実CUBIN/driver/GPUの成功証拠ではない。現CUDA実機は未検証、今回Windows追加依頼0。

catalogue1080は条件別sceneの件数。元266profileの静的packing254成功/12失敗/13分類と、全キャラ認定0は維持する。全条件・全キャラ・ゲーム空間規則・公開GPU受付は未完了。小証跡は `research/target-count-query-evidence/original-threshold-conditions-metal-v1.json`、proof stemは `.portable-recovery/proofs/original-threshold-conditions*20261030*`。
