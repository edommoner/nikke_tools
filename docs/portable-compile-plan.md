# 固定パッケージのコンパイル計画

Windowsへ送る前に、不変パッケージ自身のCLIとcwdで以下を実行します。

```sh
python scripts/nikke_gpu.py compile-plan --artifact-kind cubin --ptxas-level 1 \
  --memory-limit-mb 2048 --timeout 60 --out NEW_PLAN.json
```

`passed`とpackage IDを照合してから、同じ引数で`compile`を依頼します。`compile`のbackendはCUDA固定で、`--backend`はありません。既存CLIのsealed戦闘パッケージはCUBIN用コンパイルを受け付けます。`compiler-full--...`の診断パッケージはPTX・2GiB・ptxas level指定なしに固定されており、その制約を維持します。artifactの自動fallbackはありません。

計画はパッケージの全file/source/goldenを検査したうえで、artifact・予算・purposeの互換性だけを判定します。GPU、Slang、NVRTC、Job、claim、cacheへの書込みは行いません。SDKや依存の存在、コンパイラ成功、Windows containment／preservation、計算一致は別のゲートです。計画JSONを既存の成功証拠へ読み替えません。

PTX診断パッケージへCUBINを依頼した失敗は、Windowsの`resident-compile-v1-preflight`に保存しています。実コンパイル・claimは0でした。修正後はsealed `coordinate-resident-arc`を使います。親・child・監査・計画は同じ`compiler_diagnostic_policy`を呼び、旧PTX制約を共有します。互換性、旧制約、budget、development拒否を含む11検査を通しました。

Windows v3ではdevice検査は成功しましたが、共通smokeのSwift修復fixtureが`write_text`でLFをCRLFへ変換し、固定SHA検査に拒否されました。v4ではfixtureをUTF-8 bytesで書き、実ファイルSHAも検査します。CRLF候補を拒否する負例を追加し、実運用の修復SHA／normalizerは変更していません。Macの共通60群581検査が成功し、計算コードと106goldenはv3と同一です。旧失敗は保存したまま新規packetのみを使います。


## 共通packetのO1経路

`run-gpu-packet.py --stage compile-cubin-o1 --backend cuda --capture NEW --timeout 180 --original-workspace ORIGINAL` は、既存の共通CLI `compile --artifact-kind cubin --ptxas-level 1 --memory-limit-mb 2048 --timeout 60` へ渡します。外側全工程180秒と内側コンパイルchild60秒を分け、既存O0／PTXと同じJob・claim・監査を使います。コンパイルchildの60秒にNVRTC単体60秒を保証する意味はなく、内部の検査・生成もその予算内です。CPUの固定argv・30/60/180秒境界・Metal拒否・original workspace必須・偽driver/GPU成功拒否を含む20検査が成功しました。新O1 stageの実Windows確認はまだ行っていません。

v4の保存報告（Windows report commit `a0844950`）では、個別driverの外側60秒が先に切れました。開始から最初のpackage検査等11.573秒、inner observation2.119秒、child package検査11.283秒、Slang9.754秒を経て、35.007秒時点でNVRTC entered。約24.995秒の未完了区間後に親timeoutであり、NVRTC所要時間や内部の失敗原因は断定できません。親peak645,595,136byte／cleanup後メンバー0、内側終了観測とpreservationは未確認、CUBIN／完成cacheなし。compile／cache claimを保持しています。

今回のclaimは再使用しません。次の候補は、保存生成物・cacheのidentityを確認して生成を省けるかと、既存PTX-only→object/link経路による工程の分離です。共有計算を削る、上限を拡大する、同条件のNVRTCを単純に再試行する判断には使いません。
