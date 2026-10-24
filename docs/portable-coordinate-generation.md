# 座標スキルの世代交代と着弾時解決

座標スキルの対象集合を選択時に固定し、遅延packetの着弾では正本と同じ対象名から現在の世代へ解決する処理を、共通Slang実行器へ接続した。CUDA／Metalは同じhelper・入力・native比較器を使用する。

正本の`HitEvent`は対象名を保持し、`BossScript.hit_target`は着弾時のactive runを探す。選択時が世代1で、着弾までに同名対象が再出現した場合は世代2へ着弾する。選択snapshotの世代1は書き換えない。再出現せず消滅した場合はpool HP／hitsを変更せず、種別に基づく総量・阻止量の計上と吸血は継続する。

部位へのtyped impactの後、対象viewが生存していなければ死亡通知を処理する。期限切れも対象に含む。既に死亡登録済みなら再通知を省き、正本の冪等性を保持する。これにより、同じpacketの閾値達成が死亡による未達分清算より先に実行される。

## 実証

新しいsealed入口`coordinate-generation`は88入力（native75／拒否13）。追加12正例は部位／阻止対象の消滅と再出現、両種共存、吸血、世代2カウンタ、破壊、着弾後の再出現、slotごとの混合世代、期限切れ時の閾値→死亡順を検査する。静的入力検査ではCPU戦闘・着弾関数を禁止し、結果を事前計算してpackingしていないことを確認する。

初回87入力は期限切れ部位の死亡登録が不足し、1入力で失敗した。初回package／raw／claim／比較結果を保持した。冪等な死亡処理と順序検査を追加した修正版88入力がApple M5のMetalでCPU正本と一致し、保存rawの独立監査でsealした。GPU実行は初回と修正版の2回、同package再試行0、Windows実行0。

修正版のGPU時間は0.032926秒、Slang生成2.167889秒、cold pipeline構築7.207689秒、共通実行関数12.334670秒。時間は入れ子を含むため合算しない。旧76入力の全33,026,560byteと出力318,767,104byte、sealed entryを完全保持した。本体81のsource閉包は既存sealed baselineと完全一致し、再実行していない。

保存結果コピーへの5改変（着弾世代、選択世代、死亡登録、混合slot世代、閾値と死亡の順序）をすべて検出し、raw原本SHAを保持した。source監査は2ファイルの全SHAと一意literal差分を照合し、過去ledgerへ正確に戻して検査する。sourceの追加5改変も拒否する。正本・共有binary64・厳密normalizerは変更していない。

最終固定packageは`9a8e3c5c0fe69f00e7b52836337383362b40a4eaa3c18087873669519dc37d49`。CPU37件、制御406件（Windows専用1skip）が成功した。full2910→compact1616の全残存record／byte／goldenを照合した。終了済みraw2件は4KiB疎化で707,969,024byteを回収し、全byte／SHA／inodeを保持、削除0。

## 次の統合

この対象名による解決を、実射撃groupの世代固定ActorHandleへ一律適用しない。groupは旧世代や不在対象を除外する別の正本契約を持つ。共通poolと明示的な解決方式を使用する。

主実行器との合成では、座標arenaと実射撃group arenaの静的重複が見つかった。現profileは別々であり、同時実行の実証ではない。[arena合成設計](gpu-arena-composition.md)に従い、共通schema・CLI合成検査・合成profileを優先する。手動aim、座標物理弾、元定義の混合world、公開受付は未完了。Windows数値基準の選択と保存object回収／リンクも未完了。全キャラ認定0・20gap分類・UI CPUを保持する。

検査記録は`research/coordinate-generation-evidence/`、集約は`research/portable-coordinate-generation-checkpoint.json`。
