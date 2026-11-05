# 座標パケットの全順序SHA

固定shared入口の `PORTABLE_COORDINATE_EXISTING_HANDLERS` だけが、`coordinate_packet_history.slang` を有効にします。通常の座標trace writerを共用し、raw容量4096件を保ちながら、全packetの12wordを既存の共通SHA-256圧縮関数へ渡します。clockを含む全wordを対象にし、prefix以後も実着弾・通知・ダメージ集計を通常どおり実行します。

追加状態は64word。`CP_END=1305752`から、初期化済みcoordinate-clear-tailの先頭を専有し、次のlive arena1310720より前で終了します。`portable_coordinate_packet_history.audit_arena()` は既存Region監査でclear-tailを分割して所有を検査。入力・出力stride、Runtime、raw prefix容量、既存selection/pending容量は変更しません。初期化の一括clear後に初回recordで状態を作り、program終了で一度だけfinalizeします。

headerはmagic/version、全件数、raw容量4096、row幅12、stream上限1048576、finalized、block内word数。SHA state・最後のpadding block・digest・overflow時の最後のrowと予約ゼロも検査します。上限の超過・未finalize・不正countは失敗です。

CPU側は既存の全着弾観測 `landed_packets` を、元のtyped対象/generation・時刻・damage順に同じ12wordへ変換します。ケースが `coordinate_packet_history='ordered-sha256-v1'` を明示した場合だけ、共通sampled-parent比較器が `verify` を呼びます。markerなしの既存ケースは従来の全raw比較を保ちます。markerありでheaderが欠けた場合のfallbackはありません。

先頭min(N,4096)件は全wordと未使用ゼロを照合し、全N件のSHAと64word状態を照合。raw tailは保存しないためdigestから復元できません。結果にはraw保持数とstream側件数を残します。これは全順序の検証でありraw archivalではありません。

CPU検査は空列・境界4096/4097、prefix／digest／clock／metadata改変、stream上限超過、領域所有、厳密inverseを検査。元アンカーの実Metalで315／5031packetを確認し、独立fresh監査も成功。今回の実戦はBODYのみで、ADD世代を含む新方式の実戦認定は別途必要です。CUDA/Metalは同じwriter・SHA・Python verifierを使いますが、CUDA実機結果は未取得です。
