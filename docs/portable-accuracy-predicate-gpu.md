# 命中率条件の共通GPU接続

`self_stat_above:accuracy_pct:N` を既存の共有 `readStat` / `activationConditions` とソフトウェアbinary64の厳密比較へ接続した。発動時の条件順序・stat照会を保ち、状態fieldや算術実装は追加していない。hostはstat ID 21と有限thresholdを受付し、GPUの通常受付とactor-field受付は同一の `validStatAbovePredicate` で既存ID 0/5/6と21だけを許可する。未対応ID、NaN、正負無限大は実行前に拒否する。

共通CLIの `accuracy-predicate` は26正例＋6不正raw、`accuracy-predicate-rosters` は原文全定義モダニア3秒/30秒、`accuracy-predicate-retention` は旧1169入力。全てApple M5で同一の到達GPUソースにより成功し、独立CPU sealも成功した。計1203入力（native955/拒否248）の限定証明で、全キャラ認定ではない。旧全entriesとraw3677356032Bが全byte一致し、26旧goldenはentries/input/outputを保ってsourceと生成指紋だけを更新した。3suiteの通常経路への昇格を完了した。

26契約は0/負値/隣接binary64/最小subnormal、順序依存加算、期限、所有者、stack前後、条件の短絡順を固定する。実モダニア30秒の8判定は最初の5回が14%、残り3回が5.44%を照会して成立した。固定boolやバフ有無で置き換えない。物理履歴は3秒112件・省略0、30秒はnative2343/GPU2048・省略295で、省略数も比較する。旧範囲にある既知の履歴省略も保持しており、全履歴をGPU保存できたという主張ではない。

主32はCPU102検査17.761秒/GPU0.043992秒、実2は同102検査17.893秒/GPU3.645644秒。旧1169はCPU事前66.177秒＋回帰72群423検査129.281秒、GPU10.694823秒。旧保持実行は生成cache必須hitで追加Slang0。同一親CPU結果は843正例を再利用し、84正例をfresh照合、242入力を拒否。独立sealでは再利用しない。正式packageのCPU102検査とfull116/commands117 certificate14検査も成功した。CUDAは同じSlangから生成するが、今回のWindows CUDA実行やNVRTC cache hitは未確認。

初回v1はactor-field層の受付が未接続で全32がstatus64。同じ先頭1入力の診断でstage8000/row2を確認し、発動器を変えず受付を追加した。v2は新deltaをquery-boundary監査へ未登録だったため4検査失敗でGPU前に停止。厳密なdelta逆投影を追加したv3で成功した。旧監査SHAを変更せず、追加sourceもSHAと一意置換で保護する。全失敗raw/ログ/claimを保持し、入力とCPU期待値を変更していない。

保持検証の容量不足は `sparsify-raw` でゼロ領域だけを未割り当てにして解消した。元rawを同じpath/inode/長さ/全SHAで保持し、raw/claims削除0。事前に未圧縮input488174404B＋output3677356032B＋予備14GiBを実空きで確認してから実行した。詳細はdocs/portable-sparse-raw.md。

静的packing226/266、base166/203、69分類（consumer研究4/model gap3/review62）はGPU認定ではない。UI CPU、全キャラ認定0、全目標未達。Windows追加操作0、7終了原因unknown・環境保全falseを維持する。次は正本consumerのある未対応効果を契約化して共有実装へ進む。package/指紋/transport/失敗/範囲はresearch/portable-accuracy-predicate-gpu-checkpoint.jsonを参照。
