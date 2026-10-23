# 実戦投射物カウンターと同期子効果の共通GPU実証

共通CLI `destructible-battle`を44入力（native31・拒否13）へ拡張し、Apple M5のMetalで全件一致、保存rawを別プロセスで再比較する独立sealも成功した。今回GPUソースは変更せず、実戦scheduler・既存Frame・target-counter実行器をそのまま使う。CUDA/Metalで同じ効果定義・入力・比較器を共有するが、この44入力のCUDA実機検証は未完了である。

## 実証した動作

投射物への実際の着弾から、閾値到達、破壊時完了、破壊時取消、全兄弟の先行latch、子によるrefresh、元世代の失効、所有者限定・分隊共有、self状態/stack条件までを検証した。完了epoch・対象kind/id/generation・元attack ID・receipt・battle出力を比較し、完了後のcontext領域も空であることを確認した。CPUのprofiling用eventsだけは既存world-counter比較契約と同じ扱いとした。

|ケース|実測したCPU/Metal共通結果|
|---|---|
|閾値2の完了で攻撃力上昇|typed量968→968→1086、通常body1086|
|兄弟の完了とrefresh後の破壊|threshold epoch1・threshold epoch2・death epoch3、通常body1322|
|同じproducerへの子・孫の再入|親968・子1086・孫1204。後続兄弟が先に壊れた場合は親の古いreceiptを不配達にする|
|再入中も各攻撃の量を固定|両対象の最終残量6742、親の後続着弾量968を維持|
|明示bossへの子DEF効果|typed968→1021→1021、通常body1021|
|generic named子の対象context解放|typed968→1140→1140、通常body1140|

深さ別scratchを持つ既存非再帰Frameを再利用し、別のイベント実行器やダメージ式は増やしていない。全キャラクター・元プロフィールの全効果・投射物ごとのDEFや専用倍率・盾迎撃までの証明ではない。

## CPU比較経路の未定義対象ガード

summonを持たない戦闘では、旧scoped CPU adapterが未知の投射物対象条件やfield操作をbodyへ近似していた。`target_state:marker`とcurrent `target`のDEF操作で再現した。共有compiler/nativeの既存logical boss/add拒否は維持し、scoped adapterにもtyped context中の未定義condition/recipientを明示拒否するガードを追加した。保護対象のcanonical CPU/compilerは変更していない。終了・例外時にresolverとcondition callbackを元へ戻す検査も追加した。

投射物をboss/addへ分類するowner policyや、投射物そのものへの現在対象field操作は未対応である。一方、明示boss selectorと、generic named子でtyped contextを解放した後の通常対象selectorは別々に実GPUの正例で確認した。

## 固定成果物と再利用

38→42→44入力の異なる固定packageを各1回実行し、同一claimの再試行は0。ガード修正後の42入力は保存結果replayと独立sealで確認し、GPU追加0だった。最終44入力のpackageは`411d2a6f5e0d9ebe729f6d76d1b3fd43000e378f5ffed75a6c98251b5fbde37e`、GPU0.066852秒、pipeline0.002634秒、raw184549376byte。今回のwarm pipelineは約0.003秒だったが、恒久cacheやWindowsでの性能保証にはしない。

独立seal後にgoldenを登録し、最終sealed package `4153fcd0b9f7ae465c9b3dc0769fff0bf68f0eb1fcb74fe9908a72ff1f7b9f8a`をfresh unpackしてCPU138検査（skip0）・native31が成功した。sealed生成は必須cache hit、追加Slang0/GPU0。実GPU4blockを入力・全raw SHAとともに保存し、epoch/actor/attack ID/量/context残留の故障注入を検出する。

既存`readback-retain`で旧25入力104857600byte、38入力159383552byte、42入力176160768byteと各input/native/output指紋を保持した。原rawを削除していない。typed全152sourceおよび正規化前CUDA/MSL生成byteは旧25と同一。通常492の全147sourceも同一なので、通常492のGPUを再実行していない。これらのbyte/source監査は新たな数値計算や現在のCUDA実機の証明ではない。

証拠は`research/destructible-counter-battle-evidence/manifest.json`と同ディレクトリの小さな監査記録、checkpointは`research/portable-destructible-counter-battle-checkpoint.json`。個人設定・raw・toolchainはGitHub共有に含めない。

## 残件とWindows

全266プロフィール・packing245/base185・残20分類のissue/順位を保持した。全キャラ認定0、通常UIはCPU、全目標は未達。次はtyped logical recipient/owner policy、対象別DEF・投射物/盾固有補正、元の全定義プロフィールの接続を優先する。

今回Windowsの状態観測は利用できず、新しいrun依頼は0。準備済みCUBIN O0実験も未実施。過去の7プロセス終了について、ユーザーはアプリ/ターミナル終了・再接続・再起動を操作していないと回答した。ゲーム/動画利用の可能性はあるが、終了原因を確定する証拠ではなく、cause unknown・環境保全未確認の扱いを維持する。
