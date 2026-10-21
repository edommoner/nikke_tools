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
