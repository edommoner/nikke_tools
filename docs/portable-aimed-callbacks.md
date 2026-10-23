# 狙った対象への複数packetとカウンター子効果

共有着弾継続処理を使う20ケースを共通CLIへ追加しました。body／partカウンター、貫通／散弾（3pellet×2銃口）／爆発／狙った部位の貫通と爆発、子効果のATK100%／吸血40%の組合せです。各ケースで実際に一度の閾値完了が起こり、発射済みpacketを変えずに次の射撃へATKが反映されます。吸血はbody／partの完了通知後の値を読みます。

`reference --suite aimed-callback`はGPU・packing禁止で20契約、104射・440 returned packet・20完了を固定します。追加観測器は正本のbuff照会・live stat照会・random.sample回数、全battle／skill traceを保持しました。比較側にも既存のcanonical着弾通知とprivate kind6橋を残し、追加packet／focus観測だけを外して比較します。canonical通知を無効化してしまった初期テストと、chargeの初回発射時刻を0と誤認した初期契約の開発失敗は記録しています。CPU基準・ダメージ・閾値・数値期待値は変更していません。

共通CLIの`aimed-callback`を固定packageからMetalで1回実行し、20入力の全battle、HP／pool、カウンター完了／残存、named状態、skill trace、割り込み合計／extra会計、直接private着弾184行が一致しました。440 returned packetのCPU契約を、440行のGPU個別traceと取り違えないでください。独立seal成功、GPU0.05524秒、CPU4群17検査18.356秒でした。生成cache hitで追加Slang0です。最終の分類器も含む固定packageのCPU5群21検査も18.508秒で成功しました。

GPU sourceは122通常／123診断の全ファイルが前回のsealed1405／診断12と同一です。既存1405の保持証拠はそのソースと保存結果を再利用し、全体再実行をしていません。今回の20を旧1405と合わせた単一batchで実行したという意味ではありません。数値、strict normalizer、ABI、Runtime、容量は不変。CUDAとMetalの別実装・別の意味テストは作っていません。

これはdevelopment_onlyの対象world／callback範囲です。全キャラ認定0、通常画面CPU、目標未達。次は全定義実編成の対象worldへ接続し、より広いcallbackを確認します。Windowsは追加操作0、原因unknown・保全falseによる停止を維持し、現sourceのCUDA数値一致は未確認です。raw・個人設定は共有しません。

根拠: `research/portable-aimed-callback-checkpoint.json`と`research/portable-world-aimed-callback-short-expected.json`。
