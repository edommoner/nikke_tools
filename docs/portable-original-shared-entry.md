# 固定の共通入口と元ライの分身回復

`coordinate-original-shared`（既存cover復活6入力）と `coordinate-original-decoy`（元ライ3入力）は同じ `gpu/world_coordinate_original_shared_entry.slang` を使用します。既存handlerの元定義ケースを追加するたびに入口macroを増やす方法を改め、入力・証拠とGPUコードの変更を分離しました。CUDA/Metalは同じSlang計算本体・比較器・ケースを使います。実装を修正するときは通常どおりsource/cache identityを変え、古い結果を再認定しません。

固定入口では既存kind18/20/21/31/34/35/37を定義受付へ接続しました。これはruntime対応の認定ではありません。`entry-inventory --suite coordinate-original-shared --out UNIQUE.json` は旧cover入口との比較を残し、全266中247入力変換、変換失敗19、kind拒否0、受付拡張8profileを別々に報告します。`expanded_kind_effects` と `expanded_kind_operator_priorities` から元定義・依存を調べられます。全キャラ認定0・通常UI CPUを維持しています。

## データ追加時の生成再利用

生成・反射とtransport consumerを厳密に照合するCPU専用CLIを追加しました。既存のpackage検査・artifact検査・generation receipt監査を再利用します。

```sh
python scripts/nikke_gpu.py source-reuse \
  --reference-package /tmp/nikke-original-shared-final-v1 \
  --candidate-package /tmp/nikke-original-decoy-final-v1 \
  --reference-generation /tmp/nikke-original-shared-final-generation-v1 \
  --candidate-generation /tmp/nikke-original-decoy-final-generation-v1 \
  --require-hit --out /tmp/new-source-reuse.json
```

6→3入力でデータ指紋は変わり、GPU source closure・compiler/options/host identity・CUDA/MSL生成物と両reflection・consumerは一致。追加Slangコンパイル0を確認しました。生成CUDAを改変した負例はreceipt不一致で拒否しました。既存cache key・normalizerは緩めていません。このCLIは計算成功やCUDA compiler cacheのhitを証明しません。新入力にはCPU事前検査・実GPU・独立fresh監査・sealが引き続き必要です。

Metal実機では固定入口の初回pipeline構築93.271503秒に対し、分身3入力は同じarchive/keyの必須hitで0.002885秒、GPU実行0.703215秒でした。CUDAの実compiler/cache/launchは未取得です。Windowsへ新しい大規模ビルドを依頼していません。

## 元ライの実効果と比較器の修正

元ライ全72定義、完全5人編成・武器・成長・autoを保持し、seed3601・各8秒で満タン／実損傷→回復→再被弾／実破壊を比較しました。元の60回攻撃時回復とburst中の周期回復、分身96%最大HP・期限240秒を使い、CPU算出の発火予定は入力しません。有限timerの条件は登録時に固定されるため、破壊後の配送試行も残し、回復量0・再生成なしを確認します。

既存shield observer/readerを汎用化し、全battle・packet・RNG・control・healthに加え実回復・残存分身・期限・timer位相を比較。初回GPUは全status0でしたが2ケースが期限読取りで失敗しました。host readerがserialized配列indexではなくruntime slotをexpiry helperへ渡していたためです。index0／slot2／期限240を実rawで確認し、readerだけ訂正しました。異なるindex/slotの回帰検査も追加しています。

GPU source・全input/native指紋・rawを保持したsaved replayで全3一致、独立fresh監査14.403379秒・GPU0でsealしました。失敗capture・claimは保持し、同claim再試行0／reader修正後GPU0。固定入口の既存6件も独立監査103.122062秒で成功し、旧coverの全42,476,544byteと一致しました。旧shield9件はnative指紋・訂正readerでの保存出力比較を保持。旧cover入口のCUDA/MSL生成物も全byte一致です。

最終不変packetは関連22／27検査と各制御476検査に成功（Windows専用1skip）。全1981／1993 payloadのSHA・checkout bytes、実GPU source/input/native/outputとの一致を確認しました。全reader終了後、3captureをsize・SHA・inode保持で疎化し62,521,344byteの割当を回収、raw削除0。詳細は `research/portable-original-shared-entry-checkpoint.json` と `research/original-shared-entry-evidence/` を参照してください。

次は固定入口のまま元stack初期化18・敵stack20/21・蓄積放出34・feather35・弾消費37の正の発火を優先します。packing19件、敵回復・元武器group対象・召喚攻撃、現CUDA/warm cache、公開GPU・全キャラ認定も未完です。
