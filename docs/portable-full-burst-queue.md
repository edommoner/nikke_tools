# フルバースト着弾の再入と待機列の所有情報

共通Slangのprivate入口で、フルバースト着弾の生成中に追加された子・孫も、正本と同じ回に生成するよう修正した。旧実装は開始時の件数だけを走査し、新規mode2を次回へ残していた。動的に増える列を既存512枠の上限内で走査し、その間に追加されたmode1だけを次回へ残す。

旧バーストの確定済みbatchは、既存出力のP_PENDING_STATE_BASE+4から512×8wordへ一時保存する。生成後、物理着弾より前に消費済み待機枠を解放する。旧batchの着弾・traceは保存済みの値を読み、着弾通知から新たに追加された項目を消さない。成功後に一時領域をゼロへ戻す。Runtime、配列容量、入出力stride、最終pending counter形式は変えない。flagなしでは従来の配列・消費経路を使う。

通常の待機列にあるprefixと、フルバースト着弾の通知で追加されたtailを保持する。tailの移動は8wordの本体だけでなく、2wordの部位ダメージと38wordの周期／迎撃snapshotを同時にコピーし、slot参照を移動先へ更新する。現在の敵状態からsnapshotを再取得しない。迎撃の上位bitは保持し、非ゼロ参照が元slotに属することを確認する。

固定package `0078b96a4989f8ec21084cfaf5ad7502765fd665908d8a56de0dbff892c973db` のMetal267入力（native195、拒否72）と、GPU禁止の独立sealが成功した。追加7ケースはlive child、孫、初期列と再入の混在、旧bonusの次回残存、部位tail、迎撃tail、周期処理の共存。CPU正本のliteral時刻・数量・対象・順序を先に固定し、観測あり／なしのbattle、trace、RNG、照会・通知回数を保持した。GPUでは共通battle比較器と既存の部位・迎撃会計decodeを再利用する。

部位tailでは1260の本体と各1890の部位2件、迎撃tailでは追加1260を照合した。周期共存ケースの初回tickは次frameなので、低bit形式の周期snapshotが移動する場面の動的証拠にはならない。迎撃tailは上位bit付きsnapshotのslot移動を通る。

既存260入力（前回258＋元イレグ全76定義の3/30秒2件）はinput/native指紋および全817,889,280byteのreadbackが同一。Runtime全field layoutも同一（stride138952）。CPU24群174検査、skip0、52.754秒、正本事前15.774秒、Apple M5 GPU4.399秒、library1.466秒、pipeline8.360秒。実行時は生成cache必須hit、追加Slang0。CUDAとMSLは同じソースから事前生成したが、現CUDAの実行証拠はない。元258のゼロ領域だけをsparse化し、SHA・inode・全byteを保持して596,836,352byteの割当を回収した。

CLIは `full-burst-queue`（7入力）と `full-burst-queue-retention`（267入力）。後者の独立sealから前者の入力・出力部分と7fingerprintを抽出した。検証は展開済み固定packageをcwdにして実行する。source deltaは82b2c9fを基準とする独立の完全一致検査を先頭に追加し、従来のlanding/source証明へ逆投影する。過去の期待値・許容差・normalizerは変更していない。

残件は512枠境界の実動検証、物理着弾通知で追加された新mode2の終了時直接観測、周期snapshot移動、0hitの照会専用処理、HP basis照会順、広い実編成と現CUDA。静的受付件数を全キャラ対応として扱わない。development_only、全キャラ認証0、UI CPU、最終目標は未達。

Windowsへの追加操作は0。利用者は2026-10-22 19:04:25頃JSTの終了・再接続・再起動操作をしていないと回答した。ゲームや動画の並行利用が候補として挙がったが、7プロセス終了の因果関係は不明、環境保全falseを維持する。再実行で証拠を上書きしない。

記録は `research/portable-full-burst-queue-checkpoint.json` と `research/full-burst-queue-evidence/`。raw、入力、生成コード、固定package、claimは各 `/tmp/nikke-full-burst-queue-*` に保持する。
