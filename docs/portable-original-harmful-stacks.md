# 元アンカーの有害スタック減算

`coordinate-original-harmful-stack` はドラー／アンカー：イノセントメイド／ドレイク／マスト：ロマンティックメイド／N102の完全元編成、全82定義・武器・成長・既定autoを保持する2入力です。seed3901、6秒対照と86秒。効果書換え・CPU算出の発火予定のGPU入力はありません。育成profileへ任意controlを入れる探索は既存検査に拒否され、その境界を変更していません。

元の3回目フルバーストは78.783333秒に発生。先にマストの有害stack「취기」が3へ増え、アンカーの元 `debuff_stack_remove` が3→2へ減らします。所属・activation時刻・無期限を保持し、減算通知の合成なし、最終stack2まで比較。対照は発火0・stack1を検査します。既存stack／resource観測器・比較器を再利用し、比較器のfield引数を追加、旧 `original_stacks` 既定動作は同じです。

## 観測とCLIの効率

不変コードsnapshotから同じ6秒／86秒の全native指紋と外側の生成イベント索引を、Python観測filter有効／無効で照合し、全一致しました。86秒は観測142.272687秒／42.563530秒。これらは同時に行った同値性検査の実測で、制御された性能ベンチマークではありません。新ケースだけ明示opt-inし、旧ケースの既定値・CPU数値・正本は変更していません。

このCPU同値性検査のコードsnapshotは、制御ケースだけをmanifestへ登録した不変packageです。検査自体は凍結adapterの両ケースを準備し、各input/native/索引を記録しています。whole-suiteやGPU認定に流用せず、後続の完全2入力packageがそのinput/native指紋と一致することを確認しました。GPU独立監査は別に全2ケースをfresh再計算しています。

共通CLI `cases` にはsuite情報を入力準備へ渡し忘れる既存不具合があり、`case_names` APIへまとめて修正しました。実ケースの列挙・CPU戦闘禁止・GPU0を検査。開発checkoutで `python scripts/nikke_gpu.py cases --suite coordinate-original-harmful-stack` を使えます。compactの列挙コマンド拒否は維持しています。

## 長い戦闘のパケット履歴

初回Metalは比較器の観測名指定漏れと、約70秒でのstatus64を検出。後者は座標raw trace4096件の上限で、減算前に停止していました。CPUの全着弾列は5031件で、失敗GPUの先頭4096件が全word一致。ケースを短縮せず、共通SHA-256による全件比較を追加しました。先頭raw4096件・入力109968word・出力1769856word・Runtime138952byteは維持します。

全5031件の時刻・owner・対象kind/slot/generation・damage・flagsを順番どおり検査。先頭4096件はrawも全word比較し、残935件はrawとして保持せず、全件SHAに含めます。digestからraw tailは復元できません。raw容量4096／stream上限1048576を明示し、値・時計の比較除外やnormalizer緩和はありません。[codec・領域所有](portable-coordinate-packet-history.md)。

修正版M5は全2status0・CPU一致。全315／5031パケットのdigest一致、GPU9.068120秒・新pipeline91.563034秒。実GPU計2回（原比較失敗1保持・修正版1成功）、同claim retry0。別GPU禁止childの全2fresh監査52.867548秒、live parent receiptなしでseal。旧cover入口CUDA/MSL原生成物も全byte保持し、厳密inverseを追加しました。source変更に必要な生成・初回Metal pipeline構築をcache hitと数えません。

## 保存・最終状態

修正版の最初の起動は、GPU開始前の1GiB reserve検査で停止。今回作成した不変snapshotの同一manifest payloadをhardlinkで共有し、各packageの全byte hashを再検査。元ZIP・manifest・結果・raw・実行claimは維持しました。共有したpayloadは合計226,592,712byte、対象5snapshotだけです。raw reader終了後、原失敗／成功readbackをSHA・size・inode保持で疎化し20,840,448byteの割当を回収、raw削除0。

最終packet `/tmp/nikke-original-harmful-stack-final-v1.zip`（db9ccd15…、2010files）は関連32／制御476成功（Windows専用1skip）。全payload hash／checkout byteと実GPU source/input/native/outputを検査。最終generation cache必須hit・Slang0。詳細は `research/portable-original-harmful-stacks-checkpoint.json` と `research/original-harmful-stack-evidence/`。

全266静的分類は247packing／失敗19／kind拒否0／旧入口から受付拡張8、全profileは旧記録と一致。受付数をGPU対応数へ読み替えません。次は元ドロシー／トロニーの蓄積放出34、アインのfeather35、シンデレラの弾消費37。今回のADD/世代での元実戦・減算floor境界や他variant、packing19、現在のCUDA実機・warm cache、公開GPU・全キャラ認定も未完。全キャラ0／UI CPU／ゴール未達、Windows新規依頼0です。
