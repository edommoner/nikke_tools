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
