# Metalパイプラインの永続キャッシュ

共通CLI `run` に `--metal-pipeline-cache DIR` と `--require-metal-pipeline-cache` を追加した。既定は無効。CUDAの既存 `--compile-cache`／`--require-cache` とSlang生成cacheはそのまま維持する。計算本体・入力・golden・strict normalizerは変更しない。

固定packageを新規展開し、そのルートで実行する。

```sh
python scripts/nikke_gpu.py run --backend metal \
  --capture /tmp/NEW_CAPTURE \
  --slang-root /path/to/slang \
  --generation-cache /tmp/nikke-slang-generation-cache-v1 \
  --require-generation-cache \
  --metal-pipeline-cache /tmp/nikke-metal-pipeline-cache-v1
```

同じ生成コードの既存archiveを必須にする場合は `--require-metal-pipeline-cache` を加える。各runは新しいcaptureと未使用の固定packageを使い、消費済みclaimを削除・再実行しない。意図したcold／warm比較だけは、事前に同じZIPから固定した2つの新規展開で各1回行う。

このcacheはAppleの [MTLBinaryArchive](https://developer.apple.com/documentation/metal/mtlbinaryarchive) を使う。生成MSLの全byte、Swift consumerの全byte、entry、Runtime stride、threadgroup幅1、math mode `.safe`、GPU名／registry ID、OS buildからkeyを作る。生成コードの正規化をcache keyに使わない。各archiveのサイズとSHAをreceiptへ記録し、別GPU・OS・option・consumerでは別keyになる。

読み出しと公開はkeyごとのflock内で行う。archiveとreceiptの公開途中を別readerが未完成と誤認しない。完全に公開されていないentryや破損は自動修復・上書きせず停止する。cold時はarchiveへ関数を追加してからpipelineを作り、既存の物理Runtime reflection照合後にfsync／renameで公開する。hit時も `.failOnBinaryArchiveMiss` を指定し、保存binaryに必要な関数がなければ暗黙の再コンパイルへ進まない。具体的な利用手順とfallback禁止はAppleの [binary archive作成・読込手順](https://developer.apple.com/documentation/metal/creating-binary-archives-from-device-built-pipeline-state-objects) に従う。

cache必須missと破損はSwift側でlibrary compileより前に停止する。現段階では共通CLIのCPU正本検査後にこの確認を行う。CUDAのCPU前処理より前のcache-preflightとは区別する。既存archiveは削除・期限切れ処理せず、実行後のrawも従来の回収手順で保持する。

## 実測と検証範囲

Apple M5の実 `attack-group-native-route` 53入力（native42／拒否11）をcold／warmで比較した。競合修正版v5はpipeline準備が **90.964848秒→0.002401秒**、GPU計算は2.144520秒→2.108135秒だった。library compileは別途残る。これは1組の準備時間比較であり、探索全体や全機能の速度倍率ではない。

両試行で全53入力が一致し、元の222,298,112byte readback、入力・native・生成物・comparison全文も既存成功分と完全一致する。warmは `required=true`、`hit=true`、`native_archive_miss_rejected=true`、archive compile0秒を記録した。別processの独立正本監査も成功し、その監査は外部cacheディレクトリが利用できなくても保存証拠からGPU0で実行できた。archiveのhit単独を計算証明にはしない。

小さな実機検査ではcache無効／cold／別入力でのwarm／別kernelのcoldを各1回実行した。cache必須のsource変更、archive破損、SHAが正しい別kernel注入は実行前に拒否した。最後の負例はファイルの存在・SHAだけをhit証明にしないための検査である。receiptを一時的に退避しkey lockを保持する公開途中の注入でも、readerはロック待ち後に元receiptを読み、正常に実行した。

初期v4の53入力cold／warmも成功したが、source点検で公開途中の先行readに競合の余地があったため修正した。v4のcapture・claim・archiveは保持し、修正後v5も別の固定packageで検証した。小さなnative検査はv2／v4／v5に各4回、実53入力はv4／v5に各2回で、この作業のGPU dispatch合計は16回。Windows操作・GPU再試行・raw削除は0。通常の開発時にこの比較を毎回実行する必要はない。

最終package `037ef7aa88cd9fecdfc5a2297e350d3ecc94307d00710e2a81f62b4803a2be4a` は、実行済みv5からreplay時の監査器差し替え拒否とその負例だけを追加した。Swift consumer・cache key・計算・入力・正本・比較器は同一。制御380検査（Windows専用1skip）に成功し、最終全payload SHAをcheckoutへ照合した。詳細は `research/metal-pipeline-cache-evidence` と `research/portable-metal-pipeline-cache-checkpoint.json`。

現ソースのCUDA本体コンパイル／cacheの実機性能、長時間group log64、部位／座標／盾、全キャラ対応は継続課題。通常UIはCPU、全体目標は未達である。Slang生成cache、CUDA compile cache、Metal pipeline cache、計算結果の証明をそれぞれ分けて扱う。
