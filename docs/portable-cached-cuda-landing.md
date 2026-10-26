# コンパイラDLLを載せない明示的なCUDA実行profile

cold実行v4はCUBIN生成2.586690秒・module読込まで成功し、launchがcode2で失敗しました。保存cacheのfile-only hitは確認済み。内Job peak2098597888byteと失敗との因果関係、GPU空き・stack/local量は未観測です。原因を断定せず、NVRTCを同じdriverプロセスへ載せない条件を別の固定profileで検査します。原失敗・claim・CUBINを保持し、同じcold実行を繰り返しません。

`coordinate-landing-cache-only` は元の40/native26・source/input/native/output/goldenをそのまま使います。専用の計算実装はありません。実行前と実行子でcache必須・既存絶対cache directory・CUBIN/O1を要求。保存generated.cuをCPUより前に既存strict normalizerでMetal基準へ照合し、file-only probeを行います。source相違やmissならworker/実行claim前に停止します。この保存sourceは事前検査だけに使い、実行時は現在sourceから再生成し、元のexact-byte cache engineで再検証します。cache key/normalizer/ABI/数値/Job上限は変更しません。

CUDA実行子はNVRTCとbuiltinsのWinDLL/CDLL要求をnative loaderより前に拒否します。監査もrequired flag・観測marker・唯一のcache hit・NVRTC要求なしを検査。cache profileの成立は数値計算の成立ではなく、既存の全readback比較・native trace・Job・環境確認は別途維持します。

```sh
python scripts/nikke_gpu.py run --backend cuda --capture NEW --timeout 180 \
  --original-workspace EXISTING --require-cache --compile-cache ABS_CACHE \
  --cached-cuda-source SAVED_generated.cu --artifact-kind cubin --ptxas-level 1
```

既存SDKと専用MPFR依存の一時環境を使います。standaloneなのでresident generation-cache flagsは指定しません。Macは同一数値sourceのMetal基準を再利用し、新GPU0。固定package49fb9d41…の関連43・制御532（Win1skip）・fresh CPU40/native26が成功。7故障注入検査はcache必須、異なるartifact/options、保存source相違、required miss、NVRTC/builtinsのloader前拒否、driver許可、監査の欠落/不正markerなどを含みます。Windowsの新しい起動結果は未取得です。
