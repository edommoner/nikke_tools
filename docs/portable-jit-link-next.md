# 保存device objectのメモリリンク候補

native Python子のCreateFileW／20byte write／flush／closeはWindowsで成立したが、nvlink.exeの出力作成は未解決。出力suffix比較は終了し、原失敗は保持する。次の候補は[NVIDIA nvJitLink12.4](https://docs.nvidia.com/cuda/archive/12.4.1/nvjitlink/index.html)のAddData→Complete→GetLinkedCubin。結果をメモリから取り出す標準APIであり、CLIのファイル出力に自動fallbackする経路は作らない。

## 現在できた部分

`portable_jit_link.link_cubin`は、既に読み込まれたlibraryを受け取り、元ET_REL／EM_CUDAの全bytesをNVJITLINK_INPUT_CUBIN=1で渡す。固定optionsは`-arch=sm_86 -verbose`のみ。PTX／LTO-IR／LTO／source compileは受け付けず、numeric bodyや既存ptxas flagsを変更しない。12.4 API版と全戻り値、error/info log、Destroy1回とhandle clearを検査し、共通validate_cubinでET_EXEC／sm86／portableEvents／48byte paramsを確認する。

公式CUDA12.4.1のnvJitLink12.4.127 archive／DLL／header／LICENSEをMacでSHA固定した。DLLは38,247,424byte、SHA `2da9da786b85c100ba122f931a49c5c1eda83c32e3fa36814c2ef470e45fa9b1`。同梱headerのversioned ABI（例：`__nvJitLinkCreate_12_4`）とVersionのexportを確認した。DLL/SDK配布物は共有せず、metadataは`research/portable-nvjitlink-component-candidate.json`へ保存する。

## 未完了の境界

このprimitiveにはDLL load、Job起動、origin監査、cache publicationがない。返す診断のsource_origin_verified／containment_verified／calculation_verifiedはfalse。実Windows linkやdriver非活動の証明でもない。静的PE importsにnvcudaはなくても、動的driver利用がないとは断定しない。NVIDIAのシステム要件もCUDA driverを含むため、実行時の確認を省略しない。

CLIへの接続を実装した。条件は元object package/producer/cache/phase/Job/claim/固定SHAの再監査、専用claim、固定DLLのpre/post SHA、許可するDLL/APIの限定、実Job/PID/2GiB/60秒とcleanup、API stageと結果bytes/ELFの保存監査。programからdriver APIを呼ばず、unexpected driver moduleも確認対象とする。通常NVRTC cacheへの偽装登録や自動fallbackはしない。下記の固定パッケージ検査後にWindowsで1回だけ実DLLを確認する。

元v135はcommands-only。API診断が成立しても、準備済みcompiler-fullの現行sourceを別にcompile/object/linkし、通常実行・cache・実編成比較へ接続する必要がある。全キャラ／全特殊効果GPU対応は未完了である。

## 共通CLI接続（実Windowsは未検証）

明示的な`jit-link-object`は既存object controller／bounded child／Job観測／collectを再利用する。元object全chainの監査と専用claimからだけ開始し、DLL pre/post SHA、現在Jobの実PID・作成時刻・2GiB、ロード前／ロード後／リンク後のnvcuda module観測を記録する。子のCUDA cacheは無効化し専用directoryへ限定する。API journalの全entered/returnedと戻り値、ログ、Destroy、linked ELF、raw input全byte、親Job cleanupを事後監査する。origin/containmentはcontrollerが独立に判断し、primitiveのfalse値は書き換えない。

新しい故障注入9検査を含むfresh CPU248件は247成功／Windows1skip。コードは検査packetと全byte一致。実DLL load／link／driver／GPUはまだ0。`research/portable-jit-link-controller-checkpoint.json`に保存した。compiler-only packageでは`run --smoke --cpu-only`がCPU経路で、smokeなしはbattle拒否になる。

```powershell
& $py $cli jit-link-object --capture $freshCapture --timeout 60 `
  --object-package $originalObjectPackage --object-capture $originalObjectCapture `
  --object-sha256 c92550d36a7bc5892ffcb9f002c297227b34f7184a74827394996c2afe44b79c `
  --nvjitlink $pinnedDll --original-workspace $originalWorkspace
```

元object captureは元packageの`module-object-claimed-cuda.json`にあるcaptureから解決する。失敗済みnvlink.exe／ptxas／NVRTCは再実行しない。API成功でも旧commands-onlyのリンク診断であり、本体CUDA／計算／全キャラ認定へ昇格しない。service未識別・欠落等のpreservation=falseも別に維持する。
