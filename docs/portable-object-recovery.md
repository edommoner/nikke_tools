# 中断した全PTXオブジェクトのCPU監査回収

`recover-object`は、全PTXのassemblerと内側Jobが正常終了し、外側packetが後続監査中に時間切れになった場合の明示的な回収経路。以前の`partition-object-recover`は形式検査で拒否されたfocusのpartial専用であり、元artifactsがない今回には適用しない。今回も既存`audit_partition_object_capture`を使い、計算器や監査器を複製しない。

```sh
python scripts/nikke_gpu.py recover-object \
  --source-package /absolute/original-compiler-package \
  --source-capture /absolute/original-packet/proof \
  --object-sha256 ORIGINAL_EXTERNALLY_RECORDED_SHA256 \
  --out /absolute/new-recovery
```

Windowsでは全CPU検査も既存Jobラッパーで囲む。requestは`source_package`、`source_capture`の絶対パスと`object_sha256`の正確な3キー。

```sh
python scripts/run-gpu-packet.py --stage recover-object --backend cuda \
  --capture /absolute/new-audit-packet --timeout 90 \
  --original-workspace /absolute/original-workspace --request /absolute/request.json
```

新しい回収コードを含むimmutable packageで実行する。sourceは中断した元packageとproofを指す。新packetのclaimはCPU監査専用で、元の実行claimは消費済みのまま保持する。

## 条件と証拠

- 元runはmodule-object／processing、元artifacts/result/failureは不存在。既存結果の置換や完成runの再解釈を拒否する。
- 元packet recipe、元package byte検査、original request、消費済み両claimを照合。outer timeout／inner exit0、両Jobの終了・2GiB・BelowNormal・gateと観測を検査する。元process欠落は拒否する。
- 元outer/proofの全通常ファイルと元manifest／claimのサイズ・SHAを新receiptへ保存する。別snapshotのrecordsを既存監査器へ明示的に渡し、元captureのartifacts.jsonを後付けしない。
- 元PTX/cache/producer、固定tool、全9phase、argv/ret0、tool子のJob所属、ELF、receiptを既存監査器で再検査する。以前報告された外部SHAとも一致させる。監査後に元snapshotを再計算し、途中の追加・削除・変更を拒否する。
- 新receiptのobject_verifiedと元stage成功は別。元stage_verifiedはfalse、元runはprocessing、計算／linkはfalse、native tool／NVRTC／driver／GPUは0。service未確認なら回収CLIもexit2、全stage成功にはしない。

出力は元package／capture／上流producer／cacheの外の新しい場所だけ。失敗時も別failure.jsonを残す。時間・メモリ上限を増やしたり、コンパイルを再実行したりする機能ではない。現段階ではこの回収receiptをJIT-link受付へ接続していない。
