# Compiler専用compactと現在のPTX cache owner

現在は `compiler-full--coordinate-resident-arc` もcompact化できます。固定942b009e…はfull3,546→compact2,066ファイルで、残存全byte／GPU source／pinned reference／fixture／goldenを保持。Macの共通packet `tests`段階でcompiler20群207検査、`smoke`段階で60群585検査（1skip）、既存生成cacheの必須hit・Slang0・sealed指紋一致、PTX/2GiB/60秒planが成功しました。入力/native0の診断用であり、本体106のCUDA計算成功やWindows高速化は未実証です。以下の旧attack-group-mixedの記録も保持します。

`compiler-full--attack-group-mixed` のcompiler-onlyパッケージを既存Python依存解決器でcompact化できるようにした。アダプターがNoneなのはliteral `compiler_only=True` の場合だけ許可し、CPU20群・共通smoke39群をrootとして残す。他の未検証compiler aliasのcompact受付は広げていない。通常suiteのroot集合・GPU source・pinned reference・fixture・goldenは保持する。

## パッケージとCPU検証

固定package `9bf571abcd56509f0e1feb0b308f35d53dbbd18b3a0ada016c329ed30ef0b9b5` はfull2892→compact1578ファイル。残存全record/サイズ/SHA/byteとgoldenが一致。compiler CPU191（20群、skip0）と共通制御395（39群、Windows専用1skip）が成功した。Macは既存生成cache必須で現full sourceのCUDA/MSL/両reflectionを検査し、Slang/NVRTC/driver/GPU0でsealed生成指紋に一致した。

```sh
python scripts/nikke_gpu.py package \
  --suite compiler-full--attack-group-mixed --compact --out PACKAGE.zip
```

これはコンパイル診断用で入力/native0。通常戦闘や全キャラ対応の認定ではない。compiler用にcase adapterを作ったり、CPUテストを省略したりはしない。既存の `selected-suite-python-v1` を再利用し、cacheのidentity/schema/key/normalizerは変更していない。

## Windowsでの保存成果物再利用

最初に旧保存PTXのcacheをfile-only `cache-probe --artifact-kind ptx --require-hit` で確認し、約.146秒でhitした。NVRTC・driver・GPU0、元cache/claimは変更していない。

現packageに対して2段階だけを各1回実行した。外90秒・内60秒、fresh Job2GiB/BelowNormal/開始gate/観測/cleanupを維持。

1. 明示generation stageは新しいsource closure用の生成cacheがmissし、paired Slangを2回実行。約9.099秒で生成し、sealed CUDA/MSL指紋へ一致した。全stage38.682秒。NVRTC/driver/GPU0。
2. 続くfile-only cache-probeがhitした場合だけ、generation cache/compile cacheを両方必須にしてcompile-ptx stageを実行。Slang0/NVRTC0/ptxas0/driver0/GPU0で、既存PTX9554090byteを約.122秒で読み取った。全stage26.929秒、compiler/containment true、calculation false。古いownerの記録を再ラベルせず、現package自身のproducer/captureを作った。

全Jobは開始gate・低優先度・2GiB上限を確認し、終了後空・timeoutなし。監視process欠落0。サービス状態は未確認のため環境保全falseであり、compile stage全体もfalseのまま。生成/cache復元成功と保全/計算を混同しない。過去のプロセス欠落原因はunknownを維持する。

旧cold NVRTC26.302秒に対し、今回のartifact読取は.122秒。ただし全体時間はパッケージ検査、OS file cache、実行経路が異なるため、end-to-endの改善率は認定しない。新しいCUDA計算を証明したとも扱わない。

## 次の接続と保持境界

現在のsource/ownerで保存PTXを使えることが確認できたので、次は既存のmodule-object/JIT-link経路をこのproducerへ接続し、短いCUDA計算を確認する。後段でowner/source/cache/claimの照合を省略しない。今回ptxas/link/driverは実行していない。

raw・Windowsの詳細compiler/Job/phase資料は両hostに保存し、追加公開していない。小さいMac検証・保持記録は `research/compiler-compact-cache-evidence/` と `research/portable-compiler-compact-cache-checkpoint.json`。数値基準の回答待ち、全キャラ0/20gap/UI CPU、全目標未達は継続する。


## 共通packetによるコンパイラ関連テスト

`run-gpu-packet.py --stage tests --backend cuda --capture NEW --timeout 180 --original-workspace ORIGINAL` は、固定packetを検査後、既存の`cpu_test_groups`／`_tests`を呼びます。compiler-only packetに戦闘adapterやnative preflightを作らず、登録された全群の順序・件数・終了状態を親でも再検査します。結果は`cpu_tests_verified`で、`cpu_reference_verified`／`calculation_verified`／`compiler_verified`はfalseです。counterはpacket controllerの呼出し範囲であり、テスト内部の偽SDK／偽transportは実機証拠になりません。tests段階にも排他的なclaim・fresh Job・start gate・BelowNormal・2GiB・観測とcleanupを使います。

最初のローカルv4では、worker全体への追加build禁止が既存の偽SDK生成cache検査を止めました。追加guardは取り消し、既存のテスト実行方式・全検査を維持し、結果scopeの負例も含めてv6を固定し、207検査が成功しました。旧失敗2ログをresident-ptx-compact-v1へ保存しています。元のCPU/auditのGPU禁止ガードやnormalizerは変更していません。

次のWindows検証は、共通tests→smoke→generationで現在のpaired cacheを1回準備し、sealed指紋を確認した場合のみ、生成cache必須で共通compile-ptxを1回使います。外側180秒・内側compiler child60秒／2GiBは既存仕様。旧v4 CUBINの未完了compile/cache claimには触れません。PTXとCUBINは別artifact identityであり、PTX成功だけをCUDA計算成功としません。object／link／driver／kernelはこの依頼に含めません。


## v2：共通smokeのCPU枠を分離

Windows v1はtests207成功後、smokeが34/60群・354検査でCPU worker60秒timeoutしました。外側180秒には達せず、generation／PTX compileは未実行。保存報告`ee7bf329`をmanifest/SHA検証して回収しました。v2は共通smokeの枠を180秒へ明示分離し、compiler単体testsの既定60秒／compiler child60秒／2GiBは保持します。Mac固定33415559…でtests207／smoke586成功、生成cacheはv1と同じkeyで必須hit・Slang0、PTX plan成功。GPU・upstream・goldenはv1から全保持。未対応分類を精密化したLock OnのCPU4契約のコードも同梱しています。

新しいv2だけで共通tests→smoke→generation→生成cache必須のcompile-ptxを使います。旧v1の段階を再実行したり、claimを消したりしません。Windows v2の成功はまだ確認していません。
