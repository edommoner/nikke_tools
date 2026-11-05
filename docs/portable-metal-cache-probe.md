# Metalのキャッシュ事前点検

`metal-cache-probe` はGPU・driver・compilerを呼ばず、保存済みMetal実行のidentityと、現在の生成MSL／Swift consumer、キャッシュrecord／archiveのサイズ・SHAを照合する。record／archiveのsymlink、欠落、同サイズの破損、ソース／consumer不一致と、読取中の変更を拒否する。archiveは最大512MiB、recordは64KiBに制限し、読取専用である。

固定packageをcwdにして実行する。生成cacheを使う場合も、先に `generation --develop --require-generation-cache` で現在の生成物を検証する。

```sh
python scripts/nikke_gpu.py metal-cache-probe \
  --reference-capture /tmp/previous-successful-metal-capture \
  --generated-metal /tmp/current-generation/generated.metal \
  --cache /tmp/private-metal-pipeline-cache \
  --require-hit --out /tmp/new-metal-cache-probe.json
```

`hit_snapshot=true` は、その時点で参照identityとarchiveの全byteが一致したという意味である。以前のcaptureのdevice／OS情報を使うので、`context_current_verified=false` を維持する。現在のdriverによるarchive受付、GPU計算成功や将来のcache hitは証明しない。参照receipt自体の `hit` がfalseでも、その実行で作成されたarchiveを点検できる。

実行時は引き続き `run --require-generation-cache --require-metal-pipeline-cache` を指定し、実機のdevice／OS／sourceを使った既存の厳密な再検証を必須にする。ファイルの事前点検を理由に、CPUゲート・実GPU比較・独立sealを省略しない。

失敗はreportへ保存し、`--require-hit` 指定時はexit2で停止する。キャッシュを作成・更新・削除する機能はない。CUDAは既存の `cache-probe` と `--require-cache`／`--require-generation-cache` を使う。どちらの事前検査も計算証拠とは分けて扱う。


## 必須cacheのclaim前gate

通常 `run --backend metal --metal-pipeline-cache ABS --require-metal-pipeline-cache` は、現在のdevice/registry/OS buildと、現在sourceから生成したMSL、実Swift consumer、resident strideから同じcache keyを組み立てる。cache archive/recordの読取・サイズ・SHA検査には既存file-only probeの共通readerを使う。miss/破損/世代・OS違いはCPU tests/native計算/worker/実行claimの前に停止し、captureへmetal-cache-preflight.jsonを残す。

このgateはCPU Slang source generationを行うが、Metal library/pipeline生成やkernel dispatchは行わない。任意cache modeやCPU-only/smokeではsource生成を追加しない。device visibilityに追加したos_buildはProcessInfoから取得し、過去の成功結果から推測しない。file snapshotは予約ではないため、実行子のnative archive検査とfailOnBinaryArchiveMissは引き続き必須。required missを同じrequest内でwarm modeへfallbackさせない。

前回claim消費後にcache missで停止した旧23packetは変更せず保持した。今回のhost gate修正を含む新packetは、GPU source/input/native指紋を旧packetと完全一致確認し、実missがclaim前に止まることを先に検証。その未使用claimで別の明示的な初回warm requestを1回実行し、Metal23/独立監査/旧全output byte保持を確認した。旧claimを削除・再送・付替えしていない。生成後はfile-only probeと現在identityのgate正例もGPU追加0で成功した。
