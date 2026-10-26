# 生成キャッシュの内容を保持するfilesystem圧縮

共通CLI `compress-generation-cache --cache ABSOLUTE_CACHE --out NEW_CAPTURE` は、派生Slang生成キャッシュを検査するCPU専用コマンドです。`--apply` を付けるとmacOSのAPFS/HFS filesystem圧縮を適用します。CUDA／MSLのペア・reflectionの全データ、JSON形式、key、全ファイルの論理byte/SHAは変更しません。generation cacheのconsumerコードも変更せず、既存キーを使い続けます。

```sh
python scripts/nikke_gpu.py compress-generation-cache \
  --cache /tmp/nikke-slang-generation-cache-v1 \
  --out /tmp/nikke-cache-compression-UNIQUE --apply
```

各regular keyed JSONを既存cache validatorで検査し、競合claimがあれば開始しません。既存claim機構の中で別ファイルへ圧縮し、全byte/SHA・4artifactのhash・圧縮flagを検査してから、同じ内容の完成ファイルへatomic置換します。破損candidateは公開前に拒否し、原本と失敗記録を保持します。ソース・計算capture・raw・ZIP・数値／normalizerには触れません。派生cacheのinodeは変わります。Windowsではこの圧縮操作を拒否し、整合性／claimの共通テストは実行できます。

初回コピー実証では8,497,625byteの内容を保ち、割当8,499,200→1,753,088byteでした。sandboxでのコピーは圧縮flagなしの不正candidateとなり、公開前に検出しました。ホスト権限でのコピーはbyte/SHA/flagの検査を満たしました。元cacheを置き換える前の検査で検出しています。

実適用は371entry／4artifactずつを検査し、全key・byte・SHA一致。割当は2,651,963,392→534,904,832byte、2,117,058,560byteを回収しました。source/captureの変更0、compiler/GPU呼び出し0です。既存の固定パッケージから同じkeyでgeneration必須hit・Slang0も確認しました。空き容量は約1.5→3.5GiBとなり、検証ケースを減らさず次のreadback予算を確保できました。

これは容量の改善です。read latencyやCUDA driver cache hitの実証ではありません。NTFS圧縮やWindowsでの新規操作も行っていません。小さな記録は `research/cache-filesystem-compression-evidence/`、全planとentry単位の前後検査は `/tmp/nikke-cache-fs-compress-v1` に保持しています。
