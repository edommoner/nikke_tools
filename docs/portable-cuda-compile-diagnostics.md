# 保存結果によるCUDAコンパイルの切り分け

新版の計算一致は未確認です。v110の本体O1 CUBIN生成は、60秒・Job 2GiBの制限内でNVRTC約30.109秒後に`ptxas Memory allocation failure`となり、artifactはありません。メモリ上限との因果は未確定です。成功キャッシュを作れていないため、required-cacheのhitによる新版実行も証明できていません。同一条件の再コンパイルや上限拡大は行っていません。

## 新しい観測

共通CLIの`compiler-stats`は、保存generated CUDAのbyteとevidenceを照合して関数の構造を測れます。回復貯蔵追加後の記録は`research/portable-storage-admission-compiler-stats.json`です。これは字数等の計測で、compilerの時間／メモリ原因ではありません。

共通`ptx-stats`は、保存済みv105 PTXキャッシュのidentity/keyと原byteを既存verified compile receiptへ照合しました。WindowsでCPU3テスト成功後、BelowNormal・5秒上限の1回解析が約1.16秒で完了しました。PTXは8,234,026byte、188関数。原PTX／cache／元capture／以前の解析失敗を保持し、NVRTC・driver・context・GPUは0です。原PTXはWindowsに残し、Macが回収した構造化報告は`research/portable-v105-saved-ptx-stats-sanitized.json`です。原byteのMac独立再監査ではありません。

主な仮想宣言は次のとおりです。

| 関数 | PTX行数 | 仮想register宣言数 | local宣言byte |
| --- | ---: | ---: | ---: |
| portableEvents | 27,946 | 17,691 | 164,296 |
| dispatch | 30,822 | 18,065 | 9,496 |
| weaponFrameBody | 47,688 | 28,295 | 1,176 |

実レジスタ数、実行時のspill量、stack frame量、compilerメモリ不足の原因には換算しません。古いv105 PTXの観測であり、最新ソースのPTX計測とも区別します。

## 次に測定する対象

`gpu/combat_runtime.slang`の`weaponFrameBody`は既にnoinlineです。単に同じ属性を重ねる案は採用しません。約100行の共通武器制御に多くのinline helperが入り、古いPTXで約47,688行になった点を、関数境界を検討する入口にします。また`Runtime`の大きなprivate状態とentryのlocal宣言との関係は仮説であり、ここから直ちにglobal bufferへ全面移行しません。

1. 生成CUDAの実byte・呼出関係を使って、武器処理内の単一のhelper境界を比較対象に選ぶ。CUDA専用の計算実装は増やさない。
2. 同じ数値順序とcallback順序を保つ共通Slang変更をCPUとMetal235回帰で検証し、旧input／raw差分を検査する。
3. その変更がcompile working setを減らすという具体的な仮説を持てた場合だけ、既存の60秒・2GiB以内でcompiler-only比較を1回行う。成功してもCUDAの数値一致は別検証とする。

大きな機能を5種類外してWindowsで一括試行する案は採用しません。まず上記の観測を使い、必要な短い比較だけを行います。

## 現ソースの字句上の呼出関係

共通CLIのcompiler-stats --caller weaponFrameBody_0で、最新の保存生成byteを証拠SHAへ照合しました。rootから最大3段、noinline境界で止まる探索は64関数を訪問し、打切りなしでした。直接のeffectiveChargeに加え、startChargeControl／waitChargeControlから同じhelperへの経路があり、その先のrawEffectiveChargeはnoinline未指定です。生成CUDA上の同関数は約125行です。実際のcompiler inliningやメモリ原因とは区別します。

次の候補はrawEffectiveCharge一箇所の共通noinline境界とします。変更前の数値基準はsealed Metal327で、同一入力・全rawを確認してからWindowsの必要なcompiler-only1回を検討します。古いv105 PTXと最新コードは別sourceなので、PTXのvirtual register数の因果比較へ直結させません。呼出関係はresearch/portable-weapon-query-call-graph.jsonを参照してください。

rawEffectiveChargeの共通noinline候補はMetal327で検証し、全nativeと旧全rawが一致しました。生成CUDAも当該属性1行だけの変更でした。変更後の保存呼出関係は63関数を訪問して境界で停止し、同関数のnoinlineを確認しています。これは字句上の境界の確認であり、backendのメモリ／時間改善ではありません。次はsealed sourceに対するWindows compiler-only O1を60秒／2GiB以内で1回に限定します。

## v112の保存結果と次の判断

固定13ac263の候補はWindows compiler-only1回でNVRTC30.344秒後にallocation failure、artifact0・kernel0・retry0でした。Job2GiB／60秒を維持し、最大2,148,286,464byte。上限との因果は未確定、noinlineの改善も未立証です。cleanup／post空／missing0は確認しましたが、service未識別なので環境保持falseを維持します。Mac受領のstructured reportは独立raw監査ではありません。reportはportable-world-v112-compiler-sanitized.jsonです。

単一helperへのnoinlineを順に追加する試行はここで止めます。最新PTXを取得する診断や大きいprivate状態の配置変更は、比較仮説を先に固定してから必要な短い1検証を検討します。同じ失敗source/runtime/optionsの再試行や上限拡大はしません。新しい周期割合補正はMetal361で一致しましたが、CUDA新版の数値一致は未確認です。

## NVRTCの版を変える独立仮説

最新のWindowsファイルmetadata確認では、CUDA_PATHはv11.3で、指定toolkit直下に別の版はありませんでした（約0.66秒、DLL load／compile／GPU0）。原metadata報告はportable-cuda-compiler-inventory.jsonです。古いFileVersion文字列をnvrtcVersion API結果と同一視しません。

次の候補は、既存共通GPUソース・O1・60秒／2GiBを維持し、compiler binaryだけをNVIDIA配布のNVRTC12.4.127へ変える1回のcompiler-only検証です。NVIDIAの[Windows導入文書](https://docs.nvidia.com/cuda/archive/12.5.0/cuda-installation-guide-microsoft-windows/index.html)にあるcomponent wheelを使い、[固定配布metadata](https://pypi.org/pypi/nvidia-cuda-nvrtc-cu12/12.4.127/json)のWindows wheel19,751,955byte・SHAを固定しました。global導入せず専用フォルダーへ展開し、子プロセスだけCUDA_PATHを指定します。元toolkit／driver／PATH／親環境は変えません。

成功条件はELF CUBINと厳密cache receiptの取得・独立監査であり、最新版CUDA計算一致や速度改善ではありません。版変更がcompilerメモリを下げる保証はありません。失敗時の別版巡回、PTX-only fallback、同条件retry、上限拡大は行いません。既存成功cacheとのキー互換性を偽装せず、compiler DLLの実byte identityで別cacheにします。準備と実行結果をportable-cuda-nvrtc12-hypothesis.jsonで区別します。

## v119のbuiltins依存と共通loader修正

固定f7b42e7でwheel／1823file manifest／CPU21件は一致しましたが、NVRTC12.4はreturn7「failed to open nvrtc-builtins64_124.dll」で停止しました。1回・13.351秒、Job peak473,661,440byte、post空、driver／context／kernel0、artifact0／cache-checkなし。これは依存ロード失敗であり、メモリ改善の成功・失敗ではありません。process欠落0・元workspace／親環境保持が報告されましたが、service未識別なので環境保持はfalseです。原報告をportable-world-v119-compiler-sanitized.jsonに残しました。

PythonのAddDllDirectoryだけでは、NVRTC内部の名前による依存ロードへ検索範囲が伝わらない可能性があります。共通portable_backendはcompiler rootにNVRTC／builtinsが各1個あることを確認し、primaryの後でbuiltinsも絶対パスから読み込み、handleをコンパイル終了まで保持するようにしました。同じ配布元の対応libraryが必要という[NVIDIAの規約](https://docs.nvidia.com/cuda/archive/12.4.1/nvrtc/index.html#nvrtc-builtins-library)を維持し、pin済みwheelの2 DLLを使います。別配布物を混ぜたりPATHを変えたりしません。

既存のsource／compiler全DLL／header／flagsのbyte identity、cache schema/key、compile中のhash再検査は変えません。cache hit／required missではfactoryを呼ばず、DLL load0を保持します。欠落／複数候補はcache／DLL前、明示ロード失敗はnvrtcCreateProgram前に止まります。単一候補の検査だけで任意の2 libraryのversion互換性を証明したとは扱いません。

全CPU745件中744成功・Windows専用1skip。DLL失敗をloadedと先に記録する既存journalも、entered→成功時loaded／失敗時raisedへ修正し、compiler CLI8・artifact12・cache12のCPU故障注入を確認しました。ここまでfake DLLであり、Windowsの実依存ロードは未確認です。次の固定packageだけを新しいloader条件で最大1回確認します。元v119を再実行・上書きせず、同じ上限・O1・compiler byteを維持します。
