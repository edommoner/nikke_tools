# 保存device objectのメモリリンク候補

native Python子のCreateFileW／20byte write／flush／closeはWindowsで成立したが、nvlink.exeの出力作成は未解決。出力suffix比較は終了し、原失敗は保持する。次の候補は[NVIDIA nvJitLink12.4](https://docs.nvidia.com/cuda/archive/12.4.1/nvjitlink/index.html)のAddData→Complete→GetLinkedCubin。結果をメモリから取り出す標準APIであり、CLIのファイル出力に自動fallbackする経路は作らない。

## 現在できた部分

`portable_jit_link.link_cubin`は、既に読み込まれたlibraryを受け取り、元ET_REL／EM_CUDAの全bytesをNVJITLINK_INPUT_CUBIN=1で渡す。固定optionsは`-arch=sm_86 -verbose`のみ。PTX／LTO-IR／LTO／source compileは受け付けず、numeric bodyや既存ptxas flagsを変更しない。12.4 API版と全戻り値、error/info log、Destroy1回とhandle clearを検査し、共通validate_cubinでET_EXEC／sm86／portableEvents／48byte paramsを確認する。

公式CUDA12.4.1のnvJitLink12.4.127 archive／DLL／header／LICENSEをMacでSHA固定した。DLLは38,247,424byte、SHA `2da9da786b85c100ba122f931a49c5c1eda83c32e3fa36814c2ef470e45fa9b1`。同梱headerのversioned ABI（例：`__nvJitLinkCreate_12_4`）とVersionのexportを確認した。DLL/SDK配布物は共有せず、metadataは`research/portable-nvjitlink-component-candidate.json`へ保存する。

## 未完了の境界

このprimitiveにはDLL load、Job起動、origin監査、cache publicationがない。返す診断のsource_origin_verified／containment_verified／calculation_verifiedはfalse。実Windows linkやdriver非活動の証明でもない。静的PE importsにnvcudaはなくても、動的driver利用がないとは断定しない。NVIDIAのシステム要件もCUDA driverを含むため、実行時の確認を省略しない。

次は既存CLIのbounded childへ明示modeとして接続する。必要条件は元object package/producer/cache/phase/Job/claim/固定SHAの再監査、専用claim、固定DLLのpre/post SHA、許可するDLL/APIの限定、実Job/PID/2GiB/60秒とcleanup、API stageと結果bytes/ELFの保存監査。programからdriver APIを呼ばず、unexpected driver moduleも確認対象とする。通常NVRTC cacheへの偽装登録や自動fallbackはしない。条件が揃うまでWindowsへDLL load/linkを依頼しない。

元v135はcommands-only。API診断が成立しても、準備済みcompiler-fullの現行sourceを別にcompile/object/linkし、通常実行・cache・実編成比較へ接続する必要がある。全キャラ／全特殊効果GPU対応は未完了である。
