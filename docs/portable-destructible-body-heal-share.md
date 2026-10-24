# 盾・吸血・蓄積混在の共有回復を監査へ接続

既存の共通Slang `beginHealShareFrame`／`advanceHealShareFrame` をそのまま使い、回復先ごとの実HP増加と累積healingを照合します。CUDA／Metalの新しい回復式やshader分岐はありません。HSI6単一bossモデルに対する実証であり、ゲーム仕様・全world・全キャラの認定ではありません。

元レム・ミルク・アニス・N102と、元ノワールまたは元トロニーの全73定義を保持します。3／30秒×HP盾／hit盾／破壊後bodyの12編成です。レムの初期carrierは本人とRL2人へ1/3ずつ配り、burstで全体carrierが加わる30秒側では本人・RL2人が各2/8、残り2人が各1/8になります。共有のpresence・生存・lazy対象・配分順序と丸めは既存実行器が所有します。トロニー編成は蓄積も共存させます。

`world_heal_share_native.capture` は既存のplan／portion／通知観測をcontext managerとして再利用します。実際の `body_heal` 呼出し時HPと返されたclamp後HPを記録し、返却後にcallerが行うHP代入や同期を先行実行しません。追加numeric query・回復callbackはありません。旧observerの公開結果には新receiptを混ぜず、新しいtyped auditだけが `healing_recipients` を使います。例外時は元profileへ戻します。code objectを毎回hashせず、監視するcodeへの強参照とidentity検索を使います。

共有なしの履歴には以前のsource receiptを使い、共有ありでは明示 `body_heal_sharing_v1=True` と受益者receiptを要求します。回復元本人のHP差を配分先へ推定しません。比較器はquery／最終累積healingを5人全員について厳密照合します。保存rawの破損注入では、以前の比較が最終HP欄を見ずquery応答だけを見ていた穴も見つかりました。最終HP・maxHP・HP%・DEFを同じnative最終queryへ照合するguardを追加しました。計算側・normalizerを変更した対応ではありません。

開発12入力はMetal／native全件一致、GPU3.680799秒、cached pipeline0.002819秒です。初回はCPU成功後の容量検査でGPU前に停止しました。原失敗と未消費claimを確認し、既存rawをbyte／SHA／inode保持のまま疎化した後、別captureで初めてGPUを実行しました。保存raw2blockの全5人query／最終healingとHPへの24破損、誤った回復元への帰属、明示audit省略を拒否します。既存共有回復のreference／lifesteal／target検査も成功しました。

## 61入力の保持と独立seal

共通CLI `destructible-body-heal-share-retention` 61入力（native52／拒否9）がMetal全件一致し、別processのGPU0監査で独立sealしました。旧49は全input／native指紋と全205,520,896byteのrawが同じindexで一致しました。新12と旧49のGPU source hash、および生成CUDA／Metalの正規化前の全byteも同じです。GPU10.169563秒、cached pipeline0.002997秒、CPU71検査87.795897秒／90秒枠、native52事前照合72.304384秒でした。独立sealのCPU枠は実測72秒に基づき90秒を明示し、GPU／Windows枠は拡張していません。

```sh
python scripts/nikke_gpu.py package --suite destructible-body-heal-share-retention --compact --out /tmp/heal-share61.zip
```

単独12は開発用のままです。旧golden・容量不足のGPU前停止・raw・claimは保持します。最終小型packageは1583 files／7,275,395byte。CPU71件89.150秒／90秒枠、native52件72.096秒、共通制御372件（Windows専用1skip）が成功し、全payload SHAとcheckoutとの一致も確認しました。全SHAと記録は `research/portable-destructible-body-heal-share-checkpoint.json` を参照してください。

全キャラ認定0・通常UI CPU・packing245/266・base185/203・残20 model gapを維持します。Windows追加実行0、現full battle CUDA実機・cache速度は未検証です。過去7プロセス終了原因unknown／環境保全falseも維持します。次は貫通・元ドロシー、parts／coords／ADD混在、同期子放出境界と、共通GPU本体のCUDA compile負荷の改善です。CLIの次の効率化候補は、共通adapterからnative providerを直結し、既存ParentOraclesで同じ親processの事前計算を通常監査へ再利用することです。独立sealや保存結果監査へcacheを持ち込まず、計算項目を省かないことが条件です。
