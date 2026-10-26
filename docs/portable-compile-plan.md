# 固定パッケージのコンパイル計画

Windowsへ送る前に、不変パッケージ自身のCLIとcwdで以下を実行します。

```sh
python scripts/nikke_gpu.py compile-plan --artifact-kind cubin --ptxas-level 1 \
  --memory-limit-mb 2048 --timeout 60 --out NEW_PLAN.json
```

`passed`とpackage IDを照合してから、同じ引数で`compile`を依頼します。`compile`のbackendはCUDA固定で、`--backend`はありません。既存CLIのsealed戦闘パッケージはCUBIN用コンパイルを受け付けます。`compiler-full--...`の診断パッケージはPTX・2GiB・ptxas level指定なしに固定されており、その制約を維持します。artifactの自動fallbackはありません。

計画はパッケージの全file/source/goldenを検査したうえで、artifact・予算・purposeの互換性だけを判定します。GPU、Slang、NVRTC、Job、claim、cacheへの書込みは行いません。SDKや依存の存在、コンパイラ成功、Windows containment／preservation、計算一致は別のゲートです。計画JSONを既存の成功証拠へ読み替えません。

PTX診断パッケージへCUBINを依頼した失敗は、Windowsの`resident-compile-v1-preflight`に保存しています。実コンパイル・claimは0でした。修正後はsealed `coordinate-resident-arc`を使います。親・child・監査・計画は同じ`compiler_diagnostic_policy`を呼び、旧PTX制約を共有します。互換性、旧制約、budget、development拒否を含む11検査を通しました。
