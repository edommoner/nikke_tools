# 共通比較器と親プロセス内oracle再利用

`destructible-body-heal-share-retention` の通常実行は、既存の `ParentOracles` でCPU事前照合の値を同じ親processの比較へ渡します。従来は集約adapterが別adapterの `compare` へ委譲していたためnative providerを検出できず、事前照合後にも52編成を再計算していました。集約compareを `native_reference(domain)` と共通 `compare_body_consumers` へ直結しました。発動条件等のnative契約は元の各native_referenceを引き続き通り、battle／武器／typed着弾／HP／全員のhealing／必要なpoolの検査は残ります。

新しいcache形式・ファイル上のCPU値・GPU入力へのイベント列はありません。既存libraryのprocess／thread／package／capture所有権、1回だけの利用、provider identity、入力／値のstamp、未知protocol時のfresh fallbackは変更しません。`audit`・独立seal・保存結果監査へParentOraclesを渡しません。CUDA／Metalのsource・effect定義・Runtime・binary64・strict normalizer・goldenも変更しません。

実fixtureの旧吸血／新共有回復2ケースでnative呼出し1回と出力破損の拒否を確認し、既存の所有者違い・入力／provider／値の変更・例外終了・fallback等13検査も成功しました。終了処理の模擬テストは、実ホストの容量不足が先に発火する問題を修正しました。この1テストだけ容量検査を成功前提にして2回呼ばれることを検査し、狙ったtransport失敗へ到達させます。本番の容量検査は変更していません。

登録CPU検査は71から86へ増えたため、このsuiteだけCPU枠を事前に120秒へ設定しました（実測91.286212秒）。GPU／compiler／Windowsの枠は変更しません。固定compact package `b58be3b4359065180727b5c05e57eddf6ad80c57db12cb085369caa695acff31` は1585 files／7,281,453byteです。通常Metal61入力は全件一致し、52 nativeを再利用・追加native0・拒否9でした。通常比較の観測時間は2.051859秒で、前のfresh比較約72秒を省きました。CPU事前照合は引き続き52編成を計算し、72.634067秒です。旧61入力の全255,852,544byte rawとinput／native指紋は一致し、goldenは不変です。時間比は独立benchmarkではなく、同じ既存比較器の各実行記録です。

別processのfresh監査はGPU build／executeを禁止し、実際のnative呼出し52回・再利用0を計測して75.438829秒で成功しました。全61行のgoldenと全raw hashも一致します。共通制御372件（Windows専用1skip）が成功し、実行後の全1585 payload SHAとcheckoutとの一致を確認しました。全根拠は `research/portable-destructible-parent-checkpoint.json` に記録します。

## 未対応の再分類

共通CLI `inventory` を現在のsourceで再実行し、全266プロフィール・packing245（base185）・未対応21プロフィール／20分類を確認しました。静的準備だけでCPU戦闘／GPU呼出し0、全キャラ認定0、通常UI CPUです。20分類は全て `reference_model_gap` で、投射物／盾の補正・対象処理5分類、cover DEF、敵の移動・位置・範囲・対象数・敵回復／弾薬、仕様保留の被ダメージ分配、multi_hitのbattle producerなどです。`multi_hit:2`／`multi_hit:4` は既存attack group foundationとlistenerがありますが、戦闘所有のdistinct typed-target groupをopen／sealするproducerがありません。次の実装候補はニヒリスター／ベロータのこの発生元です。受付だけを開いて対応済みにせず、正本契約→共通実行器→Metal／必要な短いCUDAへ進めます。

Windows追加操作0、現full battle CUDA実機／compile cache実測は未確認。過去7プロセス終了の原因unknown／保全false、全目標未達を維持します。
