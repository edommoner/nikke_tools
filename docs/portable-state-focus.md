# 遮蔽物・カメラ条件とfocus_fireの共有接続

`no_broken_cover_ally`（既存ID39）、`focusing`（ID30）を共通Slangへ接続した。前者は本人を含む生存者のcover HPを発動時だけ確認し、後者は無期限効果のruntime照会でbuff casterのカメラ所属を確認する。有限効果やpassiveの扱いは正本CPU契約を維持し、条件を常時trueへ折り畳まない。

`focus_fire`はprivate stat91として存在を扱い、64要素の数値vectorには入れない。正本compilerへ渡す一時形とGPUの実際のmarker定義を分け、protected compilerやCPUは変更していない。既存carrier/lazy/live queryへ接続し、値0・負数でも存在すれば有効。武器tickより前にGPUがcamera/marker/full burstから照準を確定する。addは着弾時の生存先、interrupt/penalty partはフレームの対象を保持し、同フレーム破壊後の挙動もCPUと照合した。座標・手動aimの一般化は今回の認定範囲に含めない。

部位への直接射撃は既存のtyped landing/counterを使い、part→bodyの味方通知を0の通知も含めて既存小数通知器へ渡す。二つ目の算術・通知実行器は作っていない。

## 同時刻照会と状態領域

CPUの`get_buffs`は同時刻・対象・versionが同じなら数値結果を再利用する。カメラ切替では破棄されないため、初期装弾照会で取得した値が最初の射撃にも使われる。一方`has_live_stat`のmarker確認は現在のカメラを読む。既存dictionary-query入口に、時刻/対象/除外/効果更新epochでcamera eligibilityを保持する層を接続し、selective live queryと分離した。共有の効果追加・終了・stack/HP更新で破棄する。

追加領域は既存revival bank直後のword770976、2080word、終端773056。既存領域と重ならず、診断末尾786416より前。Runtime field追加0、stride138952、CUDA定数48B。cacheは同時刻256 context上限で超過はerror64。初期化後の予約bitで有効化し、無関係な小さいprobeの出力へアクセスしない。追加の数値読み取り経路・全てのmutationへの適用は未検証なので、広いpromotionは保留している。

## 実証

- 最終packet `/tmp/nikke-state-focus-v6`、id `eaa6fdbd83066447e45a8ddf01eb772f6e91bad37e31da4f850e75d0bd99dbad`。新66入力＝native54/拒否12。Apple M5で成功し、独立fresh sealも成功。条件30＋照準24（待機16、実射撃8）。新物理履歴120射、省略なし。数値cacheとlive markerの差、効果更新後のcache破棄も含む。
- `/tmp/nikke-state-focus-retention-v1`、id `b8149d04e97bdc62762bda9382fe00a8e002980a737afb96fd2b808a0aa0bd80`。旧1264(native1000/拒否264)が同じ117sourceで成功・独立seal。旧全entriesとraw3,976,200,192Bを全byte保持した。合計1330(native1054/拒否276)。
- 新GPU0.047241秒、旧GPU10.696327秒。旧CPU事前68.957秒＋81群455検査157.253秒。旧生成cache必須hit/追加Slang0。独立sealはnative再利用なし。
- v5→v6の66入力raw207,618,048Bも全byte一致。保存rawにaim target/camera/tag/part notice/numeric damageの5故障をメモリ上で注入し全て拒否、GPU再実行0。
- 共通CLI `reference --suite focus-aim` は24正本CPU契約、GPU0/packing0。静的inventoryは230/266、base170/203、62分類へ改善。これは取り込み検査で、全キャラGPU認定ではない。

v1の数値cache差分と保存先重複、v2の静的penalty情報の再pack欠落、v3のpart/body通知差分は、原出力・claimとともに保持。CPU期待値・保護された数値処理・normalizerは変えていない。領域重複は専用bank割当で修正し、同じ期待値でv4以降が一致した。

分類更新後の最終不変packetもCPU22群133検査に成功した。最終Metal版とのsource/input/全66件native指紋を保持し、GPU再実行はない。

## 未完了範囲と次の作業

次は今回新規にpackingできた `비스킷`・`리틀 머메이드`・`릴리` の全定義3秒/30秒を優先して確認する（70/79/68効果、いずれもfavorite stage0）。この3編成もGPU認定はまだ0。そこで実際に使うreaderを先に監査する。

1. `focusing`を使う他の数値statについて、`plainQuantity`等のreaderとcache invalidationを正本consumerから監査する。今回のATK/dictionary-query経路の一致だけで、lifesteal等を認定しない。
2. 現在のtyped Actor橋はinterrupt名を解決できず、正本比較経路が`Unknown world actor`で停止する。pinned本体にinterrupt着弾処理はあるため、型・landing・creditの拡張が必要。part/projectileへ別名化しない。現在はfocus aim＋interrupt定義を含むauto武器をhost/GPUで拒否し、chargeも実際のinterrupt着弾はerror64。layer1等への受付範囲の再点検も必要。
3. 前段から残るrevival/random混在・random buff listを検証する。
4. 実キャラの全定義と追加readerを確認してから、旧golden群・本体compiler証明の一括promotionへ進む。新しい実証goldenは保存したが、2suiteは`development_only`のまま。
5. 現sourceのCUDA実行とNVRTC cache hitは未検証。Windows操作0、7プロセス終了原因unknown・環境保全falseを維持する。

新しい入口は`package --suite state-focus --develop`と`state-focus-retention`。不変packetをfresh展開して既存runを使い、消費したclaimを再利用しない。詳細SHA・分類・停止履歴・容量・保持証拠は`research/portable-state-focus-checkpoint.json`。全キャラ認定0、通常UIはCPU、全ゴールは未達。
