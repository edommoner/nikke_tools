# 同一byte witnessによるfresh native監査

`partitioned-witness-native-audit`と`partitioned-current-envelope-audit`は、同一の106入力を保ったまま、長い正本計算をMacへ置き、Windowsでは原CUDA captureの短いCPU再読取りだけを行う経路。GPU/コンパイラー呼出し0、元claim/ledger/rawを変更しない。計算本体・期待値・strict normalizerは共通のまま。

## Mac側

固定した新packet自身をcwdにする。

```text
python scripts/nikke_gpu.py partitioned-witness-native-audit --source-package EXECUTED_CUDA_PACKET --witness-package ORIGINAL_METAL_PACKET --witness-capture ORIGINAL_METAL_CAPTURE --generation-package CURRENT_METAL_PACKET --generation-capture CURRENT_METAL_CAPTURE --cuda-summary PINNED_PEER_SUMMARY --out NEW_AUDIT --timeout 180 --group-size 8
```

元Metalの失敗flat-wire captureは既存address auditorで再監査し、失敗の記録は保持する。全875,469,264byteのrawと全106論理行が、固定CUDA要約と現sourceのgoldenに一致することを要求する。数値/statusの除外は追加しない。0.2秒や対象選択などのゲーム仮説をこの監査で認定しない。

14群のfresh GPU禁止childで、既存`portable_partitioned_native.compare_readback`を実行する。元`compare`もこの同じループを呼び、古いcaptureの入口は変更しない。各群は全inputを再構成し、全raw/論理SHAを再読し、選択したcaseの本来のnative比較と拒否stageを検査する。集約は重複/欠落・親PID/同一child・timeout・native件数・全元fingerprintを検査する。Python/native状態はchildへ渡さない。群サイズは容量や計算範囲を減らす設定ではない。

現Metalの生成元packetはseal前のdevelopment packetなので、input/source/native期待の正確なprojectionを照合する。存在しないsealed出力欄を作らない。捕捉済みCUDA/MSLの元byte SHA/sizeと現goldenの厳密正規化を両方検査する。古いMetalの生成物を現CUDAの生成証拠へ付け替えない。

成功しても、この結果はMetal由来のwitnessに対するnative一致である。`witness_calculation_verified=true`と`conditional_cuda_native_equivalence_verified=true`、`original_cuda_capture_observed=false`、`pending_original_cuda_envelope_audit=true`、`calculation_verified=false`を同時に保持する。

## Windows側

事前CPU unit検査では、新規に所有する検証root内へ子プロセスの`TMP`/`TEMP`/`TMPDIR`を固定する。共有環境は変更しない。通常の一時ファイル操作が成功してもsandboxがhardlinkやprocess観測を拒否する場合がある。その場合は起動のpermission modeを確認し、認可された範囲の通常承認経路を使う。ACL/OS変更、別経路での回避、`os.link`境界や検査の削除で通さない。拒否/失敗を保持し、未実行のenvelopeと元GPU claimを区別する。

```text
python scripts/nikke_gpu.py partitioned-current-envelope-audit --source-package EXECUTED_CUDA_PACKET --source-capture ORIGINAL_CUDA_CAPTURE --capture NEW_CPU_AUDIT --original-workspace ORIGINAL_WORKSPACE --timeout 180
```

既存のJob/start gate/BelowNormal/2GiBを使う別CPU監査。原実行の全artifact・exact source/paired generation/loaded CUBIN・prepared host/input・元claim/ledger・7launch/sync/106readbackの引数traceと実readback全byteを確認する。原observationsを既存比較器で再計算し、process保持とservice保持を分ける。コンパイラー/driverのロード・実行は禁止。正本戦闘のnative再計算は0。

原CUDAの親/子stageは書き換えない。原captureと新監査の保全結果も別。サービス識別が未確認なら環境/overallを成功にしない。Windows側もnative witnessと照合するまでは`calculation_verified=false`。2つの証拠を結ぶ共通joinの認定は別の最終段階であり、片方の成功やpeer要約だけでは成立しない。

原GPU全出力はWindowsに保持する。公開共有は小さな要約だけにし、raw/PTX/CUBIN・環境snapshotを新たに送らない。全キャラ/全特殊効果・canonical consumer・公開GPU受付はこの固定106入力とは別の未完了範囲。
