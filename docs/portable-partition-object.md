# 分割PTXの最大関数オブジェクト実験

共通CLIの`partition-object`は、保存PTXからCPU生成・再構成監査済みの`focus.ptx`だけを、固定ptxas12.4.131で1回コンパイルする明示的な診断経路。元の`assemble`、PTX／CUBINキャッシュ、共通CUDA／Metal計算本文は変更しない。失敗からの自動切り替えではなく、独立した実験として指定する。

[NVIDIA CUDA12.4のptxas仕様](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-compiler-driver-nvcc/index.html#ptxas-options)の`--compile-only`（再配置可能オブジェクト生成）を使う。既存固定toolのSHA／version検査・PTX8.4／sm86検査・子processのJob所属監査を再利用し、flagsは既存`--gpu-name=sm_86 --opt-level=1 --fmad=false --verbose`に`--compile-only`を明示追加する。

## 入力と実行

freshな`compiler-commands` immutable packageで共通`run --smoke`を実行し、CPU検査とJob事前検査を1回で通してから、Windowsで次を実行する。`run --smoke`にはCPU検査が含まれるため、同じpackageへ先に`--cpu-only --smoke`も実行して重複させない。元producer package／captureと元cache／phase、分割candidateは既存の保存証拠を使い、再生成・再コンパイルを依頼しない。

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

## 保存producerと現在の計算基準を区別する

Windowsの5801e81試行は、保存v135 producerに現在のheal-share証明書名を要求して、実ptxas／Job／capture／claimの生成前に停止した。元producerはdefinition-viewの証明書と796基準を持っており、現在の849基準とはGPU本文も異なる。証明書をコピーしたり、基準の同一性を偽って通してはならない。元失敗と小さなpeer reportは`research/portable-world-v135-focus-object-preflight-peer-report.json`へ保持した。

修正版の診断経路だけは`verify_package(..., historical_compiler=True)`を用いる。既存manifestのschema／package ID／全file byte・SHA・安全なpathを検査し、manifest内goldenと等しいJSON証明書の唯一の所有fileを、その元recordから選ぶ。基準fileもgoldenの`baseline_golden_sha256`と元recordへ結び付け、共有source closure全体と一致させる。欠落・曖昧な所有・改変・battle／計算成功の偽装は拒否する。元packageは読み取りだけで、差し替えや現行基準の追加はしない。

`assembly_origin`の通常経路は従来どおり同じsealed baselineを要求する。新しいobject診断のoriginだけは、元producerの監査・入力PTX・cache key・正規化指紋・元Jobを保持し、`historical_compiler_source=true`／`current_battle_equivalence_verified=false`を記録する。古いPTXを新しい実行器の計算証明や通常キャッシュhitとして扱わない。事前監査の失敗もfresh captureへ保存し、claimやJobを作る前に停止する。execution receiptがないcaptureのauditは成功へ進まず、未検証結果を返す。

## CUDA ELF版フィールドと、保存partialのCPU回収

75dc851のWindows実験は、ptxas12.4.131が0.315660秒・exit0で145,024byteを出力した後、検証器の`e_version==1`条件で停止した。Job全体のpeakは148,045,824byte、終了後Job空・欠落0。サービスは未識別のためpreservation=false。原結果は`research/portable-world-v135-focus-object-format-peer-report.json`へ出所付きで保存した。これだけでremainder／link／計算成立とは呼ばない。

`EI_VERSION=1`とCUDA ELFの非ゼロ`e_version`は別フィールドである。[NVIDIA/cuda-rustの修正#622](https://github.com/NVIDIA/cuda-rust/pull/622)にも同じ誤拒否の修正がある。検証器はEI_VERSIONの1を維持し、CUDA側versionは非ゼロを検査・実値を記録する。ET_REL／EM_CUDA／header・section表／payload範囲検査は維持し、ゼロversion、別machine／executable、切断sectionは引き続き拒否する。ツールとflagsの固定は変更しない。

```sh
python scripts/nikke_gpu.py partition-object-recover \
  --experiment-package /path/to/original-experiment/package \
  --capture /path/to/original-experiment/object \
  --partial-sha256 1d4db24389104fdf13574ca9be8fd6ab9badcbe80d18b4b175a1d06499ff0302 \
  --out /path/to/new-recovery/receipt.json
```

これはCPUだけの別レポート生成で、元run／失敗／claim／partialを変更せず、`.o`へのrename・claim消去・再コンパイルをしない。元immutable package／metadata inventory、producerと全candidate再構成、固定tool・入力、正確なargv、ret0、元Jobの親子・時系列・2GiB／60秒／BelowNormal／cleanupを再検査する。元journalがコンパイル正常終了後のValueErrorで停止した形であることを確認し、保存partial全体を新検証器で読む。

`--partial-sha256`は元実行の保存要約で独立に記録された値を渡す。現在のpartialを読み直して値を作り、元の記録に代えてはならない。通常`collect`のmetadata-only inventoryはrawやpartialを含まないため、その過去inventoryへ後からbinary recordを足さず、独立SHAを回収receiptへ明記する。partialと自己申告inventoryをまとめて再hashしても元SHAと一致しなければ拒否する。

成功時も`original_execution_passed=false`／`original_object_published=false`を維持し、別の`saved_object_cpu_verified`と`compiler_return_verified`へ記録する。preservation、link、計算の認定は別であり、サービス未識別はexit2。元captureやpackage／candidate／cacheの中を出力先にすること、既存回収receiptの上書きも拒否する。コンパイラー再実行・GPU実行・巨大raw転送はない。
