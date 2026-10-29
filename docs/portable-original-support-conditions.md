# 元support編成の負傷・遮蔽物・シールド条件

`original-support-conditions` は元編成catalogueと既存ordered実行経路に、30秒の4条件を追加する。

| 条件 | 元定義数 | 正例・対照 |
| --- | ---: | --- |
| Naga-injured | 70 | 2人の負傷、本人の遮蔽物被弾、回復と遮蔽物修復。シールド依存効果は0回 |
| Tia-injured | 75 | 遮蔽物被弾・修復、lifesteal、クールタイム短縮、シールド生成 |
| Naga-Tia-shield | 74 | 無被弾の対照。シールド依存効果が発動。満HPへの呼出しを正の回復量として数えない |
| Naga-Tia-injured-shield | 74 | 負傷・遮蔽物被弾・回復、6秒の実攻撃をシールドが吸収しHP被害0 |

元effect/owner/装備/武器/育成は保持する。pairはナガ、ティア、ドレイク、N102、メアリー。被弾は外部入力の1始まりslot指定、ハイドは既存manual sequenceを使う。元入力identity検査後に返却worldのコピーへ適用し、元preparedを変更しない。貫通攻撃はハイド中も遮蔽物とHPの両方に入るため、遮蔽物だけの被弾には非貫通攻撃を使う。

既存 `world_coordinate_typed_ordered_history_entry.slang` と共通状態・イベント実行器を使う。GPU source、保護CPU4ファイル、strict normalizerは前回1d78fb1dから変更0。nativeの受動観測は元handlerをそのまま呼び、元source row/owner/name/statと実HP・cover差分を記録する。GPUの既存timer activationsを元rowへ逆写像し、選択効果の発動回数も比較する。従来の全戦闘・状態・履歴比較は保持する。

## 保存済み実証

固定6b2f43c1 / package `4dce0418486e6842d43405bfdb2f856f2150ca2a3edd1796bd9b9a6d16d53a6b` のM5実GPU1回が4入力で成功。GPU2.524232秒、GPU child4.160491秒、readback32,512,000byte。generationとMetal pipelineは必須hit、Slang呼出し0。pipeline生成API0.002902秒・library準備API0.007632秒は計測されており、全コンパイルAPIが0秒という意味ではない。

別fresh processの独立sealもnative4/88.015379秒/GPU0/parent receipt再利用なしで成功。保存GPU readbackの被弾と最終coverは受動観測追加前のCPU snapshotとも一致した。soloティアの選択効果2回は、full burstを2巡完了したという認定ではない。

最終e224f1e3のcache-only packet `c6cb14e50bd9b561fdcd5f5a99ec30fe6c03ce29d5db17ef0de386827e776eec` は29群258テスト成功。unit-checkであり、fresh native全件やGPUの追加実行ではない。CUBIN/O1/2GiB/60秒のcompile-planもpolicy検査のみ成功。

小証跡は `research/target-count-query-evidence/original-support-conditions-metal-v1.json`、goldenは `research/portable-original-support-conditions-v1-expected.json`、独立receiptは `tests/fixtures/original-support-conditions-independent-v1.json`。原captureと失敗したCPU準備も `.portable-recovery/proofs/original-support-conditions*20261030*` に保持。同claim再実行0。

## 共通CLIと残件

通常は共通CLIで `package --suite original-support-conditions --out NEW.zip`、`unpack`、固定packet自身の `run` を使う。任意の追加元条件は `original-catalogue-ordered` の開発経路を使い、個別executor/verifierを複製しない。

`original-support-conditions-cache-only` は同じ4入力/source/golden/comparisonで、CUDAのCUBIN/O1とcompile cache必須hit、paired generation必須hitを要求する。実CUDAと実CUBIN hitは未検証。今回Windows追加依頼0。

catalogue1076入力の追加4は条件別sceneで、新しい4キャラではない。元profile266の静的packingは254成功/12失敗/13分類。これはGPU戦闘対応数ではない。cover_def_pct、敵回復/弾薬、received_dmg_split、空間Lock On等の未対応と、各宣言モデルのCUDA実証は残る。全キャラ・全特殊効果・公開GPU受付は未完了。
