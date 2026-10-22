# 現行戦闘本体のcompiler-only package

`compiler-full`は`heal-share-regression`と同じfull entryを、既存のcompiler-only経路へ渡す。追加wrapper、GPU計算本文の変更、生成コードの正規化変更はない。現在のMetal849実証に保存した全110 source SHAとCUDA/Metalの両generated_normalizedを、そのまま別のsource-only証明書へ固定する。新しいMetalやCUDAの実行結果を作ったとは扱わない。

```sh
python scripts/nikke_gpu.py package --suite compiler-full --out /path/to/new.zip
python scripts/nikke_gpu.py unpack --archive /path/to/new.zip --dest /path/to/new-package
```

source-only証明書のentriesは空、calculation_verifiedとexecutable_battle_verifiedはfalse。既存`compile`のPTX限定・2GiB・60秒とdriver拒否、保存compile auditとcache checkを再利用する。通常battle、module check、development/case指定は拒否する。CPU preflightとcompiler-only成功から戦闘計算成功へ昇格させない。

`compiler-commands`のsource closureは基準closureにcommands wrapperを1個追加したもの。`compiler-full`は基準closureと完全同一で、full entryを比較から除外しない。fullでは生成指紋も基準と完全一致が必要。選択はCLIの登録suiteから行い、証明書の任意フィールドや大小関係から推測しない。historical auditは元のimmutable証明書と基準を使う。

まず保存旧commands objectのlink実験を終え、その結果を評価する。fullの実コンパイルを自動開始したり、旧commands CUBINをfullのcacheに代用したりしない。次に必要な独立実験を固定packageで実施し、object、link、driverと小さな実編成の数値比較を段階ごとに区別する。現時点ではfull CUDA計算と全キャラ・全特殊効果対応は未完了。

## d1594d9 現行full PTX実証

別compiler-full package `a247319b8676029b05d317ca37d2b88d79576447e2bfdf594335d166b08915b2`をWindowsでも全2020files/table一致で固定。直前commands packetと同じcontroller/testsは全byte一致のため、CPU248/native gateの再実行は省略した。NVRTC compile1回は14.953秒で成功、PTX7,099,843B／SHA `c9a35121db6842b207741e8ae3b3820865145ec486c27defcae617b8dc57756a`、peak506,089,472B／2GiB／post空／cleanup正常／欠落0。source110と両生成指紋は基準一致、既存23,526file保持。保存CPU audit1回もcompiler_verified。service未識別のpreservationfalseと計算falseを維持。Macはpeer summaryまででraw独立監査ではない。記録は`research/portable-full-ptx-peer-report.json`。

現行full PTXからmodule-object1回→成功時のみJITlink1回を別claim/captureで依頼した。NVRTC／CPU248／native smokeの再実行や、旧commands CUBINの流用は不要。最終linkの共通CPU監査から元compiler/objectの全chainを再利用し、別の重複auditは増やさない。

## 本体へのCUBIN再利用接続条件

通常NVRTC cacheと区別した明示providerを使う。現行full証明書と全source、生成CUDAの全byte、prelude、NVRTC/ptxas/nvJitLinkの実binary SHAとoptions、元PTX/object/linked CUBIN、producer→object→linkのclaim/Job/receiptを結ぶ。古いcommands originやnormalized一致だけでは受け付けない。生成元のpath差があっても既存normalizerの除外を増やさず、raw CUDA全byteが一致しなければ拒否する。

live compilerを自動fallbackで呼ばず、共通`_cuda_module`のCUBIN load／既存params48B／既存実行・readbackを再利用する。数値本文・state/effects・input/output ABIは変更しない。compile receiptをNVRTC hitに偽装せず、専用artifact-admission eventとprovider identityをtransport/独立監査へ接続する。失敗origin、欠落、tool/header/source変更、old commands混入を負例として閉じる。

この接続後にだけ、既にMetalで保存済みのheal-share-rosters4をCUDAで短く1回比較する。リンクやmodule load成功は計算成功と区別し、readback/native/Metal保存結果の一致を必要とする。全キャラ・全特殊効果の認定とparts GPU実装はその後も残る。

## 現行full object／CUBIN実証

同じ固定full packetから保存PTXの全byteを使い、ptxas12.4.131のmodule-object1回とnvJitLink12.4.127のlink1回が成功した。ptxasは6.483811秒／return0／peak267,169,792B、object4,141,360B／SHA `b658a7f41034b55b9f81c99b00513d1768c193a917cdbc88332ea8d6e40ed2e8`。JIT providerは0.210278秒／全API9return0／Destroy成立／peak84,570,112B、CUBIN3,877,904B／SHA `91aacb335dc3355d72b652736bcd5c1bbca20798bdd8d661962c577793a45578`／params48B。driver moduleは3観測ともfalse。

両Jobは実2GiB／post空／cleanup正常／欠落0。元25,589file・object/claim・親環境を保持。最終CPU audit1回も元compiler/object chainからlink/containmentを認定した。追加NVRTC／driver／GPU0、retry0。service未識別のpreservationfalse、計算false／全キャラ認定0を維持。Macはpeer summaryまで。記録は`research/portable-full-object-link-peer-report.json`。これで現行本体のPTX→object→CUBINは実証でき、次は上記の明示providerと通常実行／独立監査への接続、実編成4ケースのGPU数値比較である。
