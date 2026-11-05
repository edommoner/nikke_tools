# 元編成の蓄積ダメージ放出

`coordinate-original-accum` はドロシー／トロニーを含む完全5人編成を、元73／74効果・成長・武器・既定autoのまま比較します。各1秒対照／18秒、seed4001。効果書換え・CPU算出の発火予定はGPUへ入れません。同じ `world_coordinate_original_shared_entry.slang` と既存の蓄積handlerを使い、数値・wire・Runtime・GPUソースの変更はありません。

元CPUでは、ドロシーの「낙인」は3.366667秒に作成、5.20秒に上限へ到達しても放出せず、13.366667秒の期限切れで10,593,140.108261758を取り出し、整数10,593,140の分配ダメージを生成します。トロニーは5.20／8.00／10.766667／13.533333秒の上限到達と同時に4回放出します。取り出す量は各carrierの実capと一致し、後半の実split補正を含むパケット量は2,184,012／7,372,327／7,162,860／7,601,330。放出後のlive amount=0・done、名前archive=0と、次carrierの再作成も保持します。

既存の `world_damage_accum_native.capture` と `portable_damage_accum_observation.compare_final` を再利用。実dispatch数は既存timer、全戦闘・RNG・対象・生成／着弾履歴は共通比較器で検査します。通常式や連撃ループを通らない蓄積放出の生成記録が不足していたため、共通 `creation_indices` に元 `_handle_damage_eff` が実際に追加した単発HitEventの観測を追加しました。着弾時にstatから欠落記録を推定するfallbackは追加せず、記録のない蓄積パケットは拒否します。元CPU計算は変更していません。

探索snapshotのmanifestは対照1件のみですが、凍結adapterから全4件をCPU観測しました。この探索をwhole-suite／GPU証明には使いません。後の完全4入力packageがその全input/native指紋と一致することを確認しています。破損検査はnotice欠落・取り出す量・消費後archive・時刻の改変を拒否します。

GPU実行・独立監査の確定結果は `research/portable-original-accumulation-checkpoint.json` を参照してください。この代表ケースだけではADD／世代・全モデル・全元キャラの認定にはなりません。現CUDAの実計算／compile cache、公開GPU受付、kind35／37、19packing失敗も残ります。

M5 Metalは全4入力status0・CPU一致。実GPU1回1.741963秒、同key/archiveの必須pipeline hit0.002726秒、Slang追加0。別GPU禁止childで全4fresh55.963184秒・live parent receiptなしでseal。元入力・native指紋を保持し、両CUDA/MSL生成物は前の2入力と全byte同一です。CUDA実compiler cacheや実launchの成功には読み替えません。

最終packet `/tmp/nikke-original-accum-final-v1.zip`（bccd155a…、1990files）は関連26／共通制御480検査成功（Windows専用1skip）。全payload SHA／checkout bytesと実GPU source/input/native/outputを照合し、最終generation必須hit・Slang0。共有展開で1986payload・56,655,264byteを共有し、ZIP／manifestは個別に保持します。

容量検査は最初約81MB不足したためGPUを開始せず、完了済み24元編成snapshotのmanifestに含まれない再生成可能なPython bytecodeだけを整理しました。payload全hashを前後で確認、割当184,180,736byte回収・raw/ZIP/結果/claim削除0。最終検査はbytecode抑制を実証していますが、独立importや設定を変える故障注入後には2cacheファイルが残っており、全プロセスのbytecode生成禁止は主張しません。今回のreadbackも全reader終了後にSHA/size/inode保持で疎化し21,561,344byteを回収、raw削除0。

全266profileの静的inventoryを再実行し、247packing／19失敗／kind拒否0／受付拡張8は前回の全profileと一致。packingをGPU対応数へ換算しません。kind34は上記元BODY代表ケースを実証した段階で、ADD／世代・他variantを含む全対応ではありません。次は元アイン35とシンデレラ：クリスタルウェーブ37。全キャラ認定0／通常UI CPU／目標未達、Windows新規依頼0です。
