# 中断した保存readbackのCPU回収監査

`recover-readback` は、保存CUBINのCUDA子が正常終了し、親が比較中に外側時間制限へ達した場合だけを扱う。元stage・claim・run・欠落した記録は変更しない。別のsnapshot inventoryを検査し、元immutable package自身の通常監査器でfresh native比較、全readback、生成物、出所、Job、観測を再検査する。CPU値の保存キャッシュやlive parentは使わない。

```sh
python scripts/nikke_gpu.py recover-readback \
  --source-package /absolute/original-package \
  --source-capture /absolute/original-stage/proof \
  --output-sha256 EXTERNALLY_RECORDED_64_LOWERCASE_HEX \
  --out /absolute/new-recovery
```

Windowsでは新immutable packetの共通wrapperを使う。requestは`source_package`、`source_capture`、`output_sha256`の正確な3キー。前2つは絶対path。

```sh
python scripts/run-gpu-packet.py --stage recover-readback --backend cuda \
  --capture /absolute/new-recovery-stage --timeout 180 \
  --original-workspace /absolute/original-workspace --request /absolute/request.json
```

元recipeは`gpu-linked`、元runはsealed CUDA battle／`preflight`、両claimは元場所を指すことが必要。元outerはterminal timeout、元innerはtimeoutなし／exit0／passed、両Jobと観測は既存object回収の共通ゲートで検査する。元CPUテスト全群とnative preflightも必須。`artifacts/result/failure/comparison.json`が既に存在するcaptureはこの限定経路では扱わない。

元outer/proofの全通常ファイル（rawを含む）とmanifest／claimsを監査前後にサイズ・SHAで照合する。元CLIを読込み、controllerへ先にimportされた参照・transportとの混在を防ぐため、全app/GPU/upstreamとresearch Pythonも元manifestとの一致が必要（実行に使わない回収器2ファイルだけ除く）。原本へ後付けartifactsやcomparisonは生成しない。

回収結果の`calculation_verified`と、元の`original_stage_verified=false`は別の事実。サービス未識別なら`preservation_verified=false`／exit2を維持する。CPU回収にもBelowNormal・2GiB・180秒を適用し、GPU／compiler／driverの追加起動、自動再実行、上限変更はない。全キャラ認定や公開GPU受付の追加ではない。
