# 1回の独立監査からsealとソース証明を作成する

新規のcomplete worldをMetalで検証した後、既存の独立監査を一度だけ実行して、戦闘goldenとコンパイル用source certificateを作成できる。

```sh
python scripts/nikke_gpu.py seal \
  --package-root /tmp/IMMUTABLE_PACKAGE \
  --capture /tmp/SAVED_METAL_CAPTURE \
  --out /tmp/NEW_METAL_GOLDEN.json \
  --compiler-certificate /tmp/NEW_SOURCE_CERTIFICATE.json \
  --timeout 180
```

`audit_saved_metal` が固定package自身のprocess／importsでGPU禁止の全比較を実行し、その同じ結果から既存の `portable_compiler_certificate.certificate` を呼ぶ。goldenのUTF-8 byteをsource証明のbaseline SHAへ結び付ける。保存済みgoldenや「前の監査は成功した」というJSONだけを信頼して再利用する機構ではない。

出力は新しい別々のpathを指定する。既存pathと同じpathへの衝突、filtered case、probe suiteはnative監査の前に拒否する。監査中のmanifest変化、package ID差、未成功の計算、source差を検出した場合は、golden／certificateを作成しない。出力中のfilesystem failureで一方だけが作成された場合は保持し、同じ出力へ上書きしない。GPUの再実行は不要である。

従来の`seal --out`だけの操作と、過去のsealed Metal結果をfresh監査する`compiler-certificate`は維持する。source certificateはCUDAコンパイル・link・cache hit・GPU計算・resource保全の成功を意味しない。共同作成のreportも`compiler_verified=false`／`cache_hit_verified=false`を保持する。full sourceのaliasは既存registryから解決し、入力のラベルでprobeをfull worldへ昇格させない。

CPU検査は同じfresh auditの1回だけの利用、既存certificateとの一致、filter／probe拒否、manifest変化、package・source・計算不一致、出力衝突、従来の単独sealを含む。
