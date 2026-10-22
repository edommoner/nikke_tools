# 分割PTXの最大関数オブジェクト実験

共通CLIの`partition-object`は、保存PTXからCPU生成・再構成監査済みの`focus.ptx`だけを、固定ptxas12.4.131で1回コンパイルする明示的な診断経路。元の`assemble`、PTX／CUBINキャッシュ、共通CUDA／Metal計算本文は変更しない。失敗からの自動切り替えではなく、独立した実験として指定する。

[NVIDIA CUDA12.4のptxas仕様](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-compiler-driver-nvcc/index.html#ptxas-options)の`--compile-only`（再配置可能オブジェクト生成）を使う。既存固定toolのSHA／version検査・PTX8.4／sm86検査・子processのJob所属監査を再利用し、flagsは既存`--gpu-name=sm_86 --opt-level=1 --fmad=false --verbose`に`--compile-only`を明示追加する。

## 入力と実行

freshな`compiler-commands` immutable packageでCPU preflightを通してから、Windowsで次を実行する。元producer package／captureと元cache／phase、分割candidateは既存の保存証拠を使い、再生成・再コンパイルを依頼しない。

```sh
python scripts/nikke_gpu.py partition-object \
  --capture /path/to/new-object-capture \
  --source-package /path/to/original-producer-package \
  --source-capture /path/to/original-ptx-capture \
  --cache-entry /path/to/cache/KEY.json --phases /path/to/original-ptx-capture/phases.jsonl \
  --candidate /path/to/audited-candidate --ptxas /path/to/pinned/ptxas.exe \
  --original-workspace /path/to/original-workspace --timeout 60
python scripts/nikke_gpu.py audit --capture /path/to/new-object-capture
```

親・子・事後監査で元producerの既存compile監査とcontainmentを再検査し、candidate全体を元cache／phaseから再構成する。元PTXのSHA・cache keyもproducerへ一致させ、候補側manifestの自己申告だけでは実行しない。実験originにproducer記録・plan SHA・focus名・入力byte/SHAを含む。

既存`run_job`／start gate／Windows observerを再利用する。2GiB／60秒上限・BelowNormal、ptxas待機55秒・cleanup5秒、独立した`partition-object-claimed-cuda.json`で同packageからの再実行を拒否する。親環境の一時変更は復元し、子TEMPは既存`validation_environment`でcapture配下へ分離する。NVRTC／CUDA driver／GPU APIは許可せず、remainderのコンパイルやlinkへ自動移行しない。

## 記録と未証明事項

`focus.o.partial`、stdout／stderr、phase journal、元入力copy、失敗は保持する。exit0かつELF64 little-endian／ET_REL／EM_CUDA／section範囲検査後にだけ`focus.o`を公開する。artifact種別は`diagnostic-relocatable-object`で通常CUBIN cacheへ登録しない。事後監査は正確なargv、tool/input/ELF identity、時系列、親子Job所属、2GiB cap、cleanupと環境観測を別々に検査する。

`object_verified`はこの1オブジェクト生成だけの検証で、`partition_legal_verified`／`link_verified`／`calculation_verified`はfalse。CLIはobject未検証ならexit1、環境維持がtrueと確認できなければexit2。service未識別を成功にしない。CPUの故障注入テストで使う合成ELFは実assemblerの証明ではない。

最大関数単独でも失敗するか、module全体の失敗と区別できる追加証拠を得る実験である。成功してもremainderコンパイル・101global／constantの解決・relocation／ABI・link・計算一致は未証明。失敗から必要メモリ量を推計しない。NVIDIA公式12.4.131 archiveの公開SHAとnvlink memberのbyte／SHAをMacで確認し、同archiveのptxasは既存固定toolと同一だった（`research/portable-device-linker-component-candidate.json`）。LICENSEも保持した。nvlink自体の実行版／link互換性は未確認で、Windowsへの導入はしていない。既存11.3を12.4生成objectへ流用しない。次のlink実験には対応toolの固定・全unitのオブジェクト生成・別の明示manifest／監査が必要。
