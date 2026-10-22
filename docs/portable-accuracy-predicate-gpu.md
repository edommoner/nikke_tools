# 命中率条件の共通GPU接続（保持検証待ち）

`self_stat_above:accuracy_pct:N` を既存の共有 `readStat` / `activationConditions` とソフトウェアbinary64の厳密比較へ接続した。条件の順序・発動時照会を変えず、状態fieldや算術実装は追加していない。hostはstat ID 21を受付し、compiled thresholdの有限値を検査する。GPUの通常受付とactor-field受付は同一の `validStatAbovePredicate` を使い、既存ID 0/5/6と21だけを許可してNaN/無限大を拒否する。

共通CLIの `accuracy-predicate` は26正例＋6不正raw（負/範囲外/未対応stat、NaN、正負無限大）、`accuracy-predicate-rosters` は原文全定義モダニア3秒/30秒。Apple M5で両方が成功し、保存結果の独立CPU sealも成功。両者の到達GPUソース指紋は同一。正例28はnative全項目・保存形式の技能trace・物理履歴を既存比較器で照合した。30秒の物理履歴はnative2343、GPU2048、省略295で、省略数も一致した。全履歴をGPUに保存できたという主張ではない。

主32はCPU15群102検査17.761秒、GPU0.043992秒。実2は同102検査17.893秒、GPU3.645644秒。前者はSlang2生成、後者は必須cache hitで追加生成0。同一親CPU結果は26/2正例を再利用し、独立sealはfresh CPU照合を維持した。生成CUDAは同じSlangの生成物であり、Windows CUDA実行やNVRTC cache hitの証拠ではない。

初回v1はactor-field層を開通させておらず全32がstatus64。既存診断マクロを使った同じ先頭1入力でstage8000/row2を確認し、発動器を変えず受付を追加した。v2は新deltaを既存query-boundary監査へ未登録だったため、4検査失敗でGPU前に停止。正確なdelta逆投影を追加したv3で成功した。旧監査SHAを変更せず、追加sourceも厳密SHAと一意置換で保護する。全失敗raw、ログ、claimを保持し、入力とCPU期待値を変更していない。

静的packingは226/266、base166/203、69分類（consumer研究4/model gap3/review62）。全キャラ認定0、UI CPU。既存1169入力の証拠は変更前GPUソースであり、今回ソースでの全保持検証は未完了。新規34の限定証拠を全体認定へ加算しない。両suiteはdevelopment_onlyを維持し、独立seal済みgoldenを保存したが正式受付のpromotionは保留する。

次の旧1169保持実行は約0.49GBのinput＋3.68GBのoutputと14GiBの予備容量が必要。現在の空きでは足りず未開始。既存のrawや失敗証拠を削除していない。容量を確保して同ソースで全entriesとrawを保持比較し、compiler certificateと回帰を通した後にpromotionする。

Windows追加操作0、7プロセス終了原因unknown・保全falseを維持する。全目標未達。各package ID、指紋、transport、失敗、範囲は `research/portable-accuracy-predicate-gpu-checkpoint.json` を参照。
