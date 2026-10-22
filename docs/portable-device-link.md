# 保存単一オブジェクトのdevice link

共通CLIの`link-object`は、検証済みの元module objectを固定nvlink12.4.131で1回だけリンクする診断経路。元PTX／objectを再生成せず、通常PTX／CUBIN cacheやbattle実行へ自動移行しない。

```sh
python scripts/nikke_gpu.py link-object \
  --capture /path/to/new-link \
  --object-package /path/to/saved-module-experiment/package \
  --object-capture /path/to/saved-module-experiment/module \
  --object-sha256 c92550d36a7bc5892ffcb9f002c297227b34f7184a74827394996c2afe44b79c \
  --nvlink /path/to/isolated/nvlink.exe \
  --original-workspace /path/to/original-workspace --timeout 60
python scripts/nikke_gpu.py audit --capture /path/to/new-link
```

元object captureは、そのpackageの`module-object-claimed-cuda.json`が記録した実際のpathを使う。期待SHAは元保存要約の値を固定し、現在のファイルから作り直して代用しない。元capture／package／claim／失敗／partial／回収receiptは変更しない。

## Toolとflags

NVIDIA公式CUDA12.4.1 redistributionのNVCC12.4.131 archiveとnvlink memberの両SHAを固定する（`research/portable-device-linker-component-candidate.json`）。Windowsでは隔離directoryへ保存し、LICENSEを保持する。既存SDK／PATH／driverを変更しない。toolのMZ／全byte SHAを起動前と終了後に照合する。版は公式archiveと固定binary hashによるidentityで、別の`--version`実行を成功根拠にしない。

flagsは`-arch=sm_86 --ignore-host-info --verbose`。[NVIDIA CUDA12.4のnvlink仕様](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-compiler-driver-nvcc/index.html#nvlink-options)に従い、host registrationがないDriver API用途で参照され得るdevice codeを削除しない。単一objectからcubinを出す工程は[NVIDIAのNVSHMEM例](https://docs.nvidia.com/nvshmem/release-notes-install-guide/install-guide/nvshmem-install-proc.html)にも記載されている。LTO／追加library／flags sweepは行わない。

## 共通実行器と証拠の範囲

focus／moduleと同じ`portable_partition_object.run`、native process inspector、Job／startgate／BelowNormal／2GiB／60秒／wait55＋cleanup5、専用claimと事後監査を使う。入力は`module.o`、出力は`linked.cubin.partial`→検証後`linked.cubin`。stageは`module_link_*`、providerは`diagnostic-nvlink`、artifactは`diagnostic-linked-cubin`、mode／claimは`link-object-only`／`link-object-claimed-cuda.json`で、通常cacheと区別する。

- 元moduleのimmutable packageは元certificate／baselineへ歴史監査し、元source／cache／phase／PTXとmodule objectの生成証拠、元Job、claim、metadata inventory、期待object SHAを再確認する。既知の欠落processや異常cleanupがある元実行は次へ進めない。service未識別を成功にしない。
- 親・子・事後監査で同じsource chainを再確認する。正確なargv／ret0／tool／input／output SHA、親子PID・作成時刻・Job所属・時系列・memory capを別々に検査する。
- CUDA ELF64 little-endian／ET_EXEC／EM_CUDA／非ゼロCUDA format version、sm86・64bit addressing、section／program tableとfile範囲、文字列／symbol tableを検査する。`portableEvents`の実行code sectionと、定義済み48byteの`SLANG_globalParams`を静的に確認する。ET_RELを実行可能CUBINと取り違えない。
- 別modeやsource_kind、wrong tool／hash、欠落symbol／誤target／切断payloadは拒否する。失敗・partial・claimを保持し、retry／fallback／再コンパイル／cap拡大をしない。

`link_verified`はこの静的linkと保存証拠の検証まで。driver load、実際のGPU binding／kernel、計算一致は未証明で、`calculation_verified=false`を維持する。元v135はcommands-onlyなので、現在のfull battle entryや全キャラ／全特殊効果対応と同一視しない。サービス未識別はpreservation=false／exit2。次の計算用cache接続には、full source／生成物／toolchain・artifact identityの一致と独立したGPU検証が必要である。

## 330b204のWindows失敗記録と次の確認

固定package／2010 file table／公式tool・LICENSEのSHA、元object全byte、元生成記録とJob／claimのCPU origin gateは一致。Windows CPU202全成功、Job smokeも成功した。link-objectは1回で失敗し、nvlink stdoutに`Could not open output file`、共通engineに`Native tool is not in the validation Job`が残った。戻り値・native child snapshotは元journalに保存されず、CUBINもなく、link／計算の認定はfalse。

外側Jobは31.986572秒、peak62,066,688byte／2GiB、timeoutなし、post空、欠落0、cleanup／観測errorなし。これはnative子の2PID所属証明とは別である。service未識別のpreservation=falseを維持。原本・失敗・claimは保持し、同条件retry／出力先変更／追加compiler・driver・GPUは行わない。小さいpeer summaryは`research/portable-world-v135-device-link-peer-report.json`。Macはsummary照合までで、Windows原本の独立監査ではない。

入力の`.o`には別の懸念がある。[LLVMのClangNVLinkWrapper](https://github.com/llvm/llvm-project/blob/main/clang/tools/clang-nvlink-wrapper/ClangNVLinkWrapper.cpp)は、生のNVPTX ELFをbyte-preserving copyで`.cubin`へ写してnvlinkへ渡す（fatbinaryのhost objectは`.o`）。今回の出力作成エラーを拡張子が原因と断定しない。元objectは変更せず、ACL／path／補助出力仕様と保存ELF symbolをCPUで確認してから、新しい明示的入力契約を選ぶ。

共通engineは、今後の所属確認拒否で`*_child/rejected`へ実際のsnapshotと`process.poll()`で取得可能な戻り値を残す。早期終了を成功とみなさず、元失敗の記録を作り直さない。新しい故障注入1件と既存link9＋focus16＋module5が成功。実toolの起動前に所属を観測できる仕組みは未実装であり、次のnative試行前に検討する。現行full compiler packageは準備済みだが、この失敗を無視してfull native試行を増やさない。
