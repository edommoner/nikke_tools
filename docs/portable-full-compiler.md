# 現行戦闘本体のcompiler-only package

`compiler-full`は`heal-share-regression`と同じfull entryを、既存のcompiler-only経路へ渡す。追加wrapper、GPU計算本文の変更、生成コードの正規化変更はない。現在のMetal849実証に保存した全110 source SHAとCUDA/Metalの両generated_normalizedを、そのまま別のsource-only証明書へ固定する。新しいMetalやCUDAの実行結果を作ったとは扱わない。

```sh
python scripts/nikke_gpu.py package --suite compiler-full --out /path/to/new.zip
python scripts/nikke_gpu.py unpack --archive /path/to/new.zip --dest /path/to/new-package
```

source-only証明書のentriesは空、calculation_verifiedとexecutable_battle_verifiedはfalse。既存`compile`のPTX限定・2GiB・60秒とdriver拒否、保存compile auditとcache checkを再利用する。通常battle、module check、development/case指定は拒否する。CPU preflightとcompiler-only成功から戦闘計算成功へ昇格させない。

`compiler-commands`のsource closureは基準closureにcommands wrapperを1個追加したもの。`compiler-full`は基準closureと完全同一で、full entryを比較から除外しない。fullでは生成指紋も基準と完全一致が必要。選択はCLIの登録suiteから行い、証明書の任意フィールドや大小関係から推測しない。historical auditは元のimmutable証明書と基準を使う。

まず保存旧commands objectのlink実験を終え、その結果を評価する。fullの実コンパイルを自動開始したり、旧commands CUBINをfullのcacheに代用したりしない。次に必要な独立実験を固定packageで実施し、object、link、driverと小さな実編成の数値比較を段階ごとに区別する。現時点ではfull CUDA計算と全キャラ・全特殊効果対応は未完了。
