# 必須PTX cacheによるCUDA module確認

Windows v125は共通Slang本体のPTX生成とcache照合に成功しましたが、CUBIN生成とCUDA計算一致は未完了です。次の確認は、同じPTXをdriverへ渡したときのmodule load／JITと、entry・定数バッファABI・context終了だけを短いJobで検査します。戦闘入力を準備せず、バッファ確保・転送・同期・kernel実行は行いません。

```sh
python scripts/nikke_gpu.py module-check --capture <new-capture> \
  --original-workspace <original-checkout> --slang-root <existing-slang> \
  --compile-cache <v125-cache> --timeout 60
```

sealed Metal packageとWindowsを必須とし、PTX・cache-required・2GiBをCLI側で固定します。cache miss／無効receiptはdriverより前で停止し、NVRTC DLLロードも拒否します。Slang生成コードとsource closureは既存goldenへ照合し、normalizerは変更しません。専用のmodule-claimed-cuda.jsonを一度だけ作り、以前のcompile／GPU claimを消しません。既定のfresh BelowNormal Job・start gate・終了観測・cleanupを再利用し、時間枠は最大60秒です。

## 共通のdriver準備と終了

通常のCUDA実行とmodule-checkは同じ_cuda_module context managerを使います。cuInit、device取得、context作成、cuModuleLoadData、entry取得、SLANG_globalParams取得と32／48byteの検査、context破棄を共用しました。ABI検査は戦闘バッファ確保より前へ移しています。primary errorにcleanup errorをnoteとして付け、元の失敗を隠しません。

module-checkはdriver APIの許可リストを持ち、確保・コピー・同期・launch等の呼出しはnative関数へ達する前に拒否します。child専用のCUDA_CACHE_PATHをcapture内のdriver-cacheへ指定し、親の環境変数は変更しません。この指定だけでdriver JIT cache hitを認定しません。driver cacheのバイナリを小さいJSON／logのexportへ混ぜません。

## 既存監査器との接続

Journal、NativeLibrary、cache receipt、immutable package／artifact検査、Job containment、即時の環境観測を再利用します。監査はcache hit→driver load→必須APIの成功→context破棄→module確認のreturnという順序、同じ子PID、2GiB上限、post空を確認します。source／生成コード／PTX bytesとreceipt、Runtime reflection、ABIも照合します。欠落・途中append・scopeの書換え・不正なJobは成功になりません。

結果はmodule_verified、containment_verified、preservation_verified、calculation_verifiedを分けます。module_verified=trueでもcalculation_verified=false、kernel_calls=0、buffer_allocations=0です。サービス未識別は環境保持の成功へ変換せず、CLIはmodule成功と環境未認定を終了コード2で区別します。CUDAで計算したという証明ではありません。

## CPU確認と既存Metal証拠

CPU故障注入14検査で、cache miss、codegen drift、JITエラー、ABI不一致、禁止API／NVRTCロード、cleanup失敗、PTX改変、API観測欠落、順序違反、Job制約違反、scopeの改変、claim再使用とchild cache隔離を確認しました。resident transport3件と既存compiler／cache検査も再利用します。固定パッケージのportable系776検査は775成功・Windows専用1skip・失敗0でした。

共通GPU source closure、Metal側のbuild／実行、数値比較・cache identity・protected CPU baseline・normalizerは変更していません。関数AST／file byteの保持確認をportable-module-check-source-retention.jsonへ保存しました。Metal759の保存証拠を再利用し、同じGPU検証を再実行しません。Windowsではorchestration変更に対するrun --smokeを先に行い、登録CPU検査とfresh Jobが成功した場合だけmodule-checkを一度実行します。失敗時の同条件retry、NVRTCへのfallback、上限拡大は行いません。

通常UI CPU、全キャラGPU認定0、entry_reloadはCPU契約35件まで、目標未完了を維持します。

## 明示的なdriver JIT最適化

`module-check --jit-opt-level 1`で、同じ必須PTX cacheを`cuModuleLoadDataEx`へ渡します。省略時は従来の`cuModuleLoadData`です。`CU_JIT_OPTIMIZATION_LEVEL=7`、値0〜4（既定4）の仕様と、値を`void*`へcastするAPI契約に従います。NVRTCのPTX生成オプション・cache key・共通Slang・Metal goldenは変更しません。

- 公式enum／範囲: https://nvidia.github.io/cuda-python/cuda-bindings/latest/module/driver.html
- 公式module API: https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__MODULE.html

設定はrun.jsonとmodule receipt、journalに保存し、native呼出し直前にもoption番号・件数・scalar値を照合します。監査は選択したloaderだけを許可し、明示設定のnative照合記録も必須とします。JIT失敗時に既定設定へfallbackしません。通常の戦闘実行は従来設定のままです。明示JITでmoduleが成功しても、通常CUDA経路や計算一致の成功にはなりません。

Windows v126から受信した途中報告では、81 CPU smoke成功、PTX cache hit、driver／context作成成功の後、moduleロードがCUDA error218と`ptxas fatal: Memory allocation failure`で失敗しています。context破棄戻り値0・Job終了後空との報告ですが、接続断で最終保存JSONを未取得のため、独立監査済み結果とは扱いません。同条件の再実行は依頼しません。明示レベル1は別条件の候補で、CPU確認後もWindowsでの成功は未確認です。

明示JIT追加後の固定パッケージではportable系781件中779成功・Windows専用1skip・ps権限による1errorでした。同じ展開先の監査5件をプロセス観測権限付きで検証し全成功。元errorは保存しています。追加後のmodule故障注入は19件です。結果はportable-jit-level-development-checkpoint.jsonを参照してください。Windowsの明示JIT実行はまだありません。
