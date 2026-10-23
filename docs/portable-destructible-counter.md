# 型付き着弾と既存カウンター実行器

共通CLI `destructible-counter` は、宣言された弾・HP盾・回数盾のGPU状態から、既存の対象別カウンターと同期子イベント実行器へ着弾を渡す。CUDA/Metalで同じ `destructible_impact_runtime.slang`、`collectTargetCounters`、`dispatch` を使い、別の進捗計算や完了ループは作らない。CPU側も既存の `publish_impact` と `target_death` を呼ぶ。

## 順序と意味

1. 既存のworld schedulerで時刻・生成世代を進め、解決済みImpactをtyped targetへ適用。
2. stale/dead/未生成の着弾は通知しない。受理した着弾は元のattacker/family/outcome/damage/credit/attack_idで既存collectorへ渡す。
3. 閾値を満たす全兄弟を先にlatchし、既存DFS実行器で同期完了通知・子バフ・カウンター更新を実行。
4. 壊れた場合は、その後に確定済みの種類・ID・世代をcounterの終了処理へ渡す。子イベントが更新した同世代のmarkerも正しいepochで処理する。

counter終了は既存の`on_death`契約であり、一般の敵本体死亡イベントではない。ownerは記述だけで、ownerの死亡やownerへの攻撃へ変換しない。HP消費の`took`と通知する元のresolved Impactは別の量である。ここでスコアやダメージ倍率を定義しない。ノード失効を破壊通知へ変換せず、古い世代のmarkerに新世代の着弾を加算しない。既存子イベントのエラーは伝播し、自動再試行やロールバックを加えない。

## 証拠

Metal18入力（宣言モデル正例13、raw拒否5）が一致し、独立seal成功。閾値・破壊・分数hit credit・blocked/miss・owner限定・stale世代・更新されたmarkerの親終了保護・同時完了兄弟と破壊順序を検査。実際の子`atk_pct`の0/11/22/33と、counter epoch・credit・actor・完了理由・元Impactを照合した。world状態は既存BossScript時計＋typed状態CPUモデルと比較する。

最終成功capture `/tmp/nikke-dc-metal18-v3`、package `3618292f…`。GPU約0.026794秒、cached pipeline約0.001578秒、readback56,623,104B。既存16入力はinput/native/output指紋とraw50,331,648Bを全保持。保存5blockのfixtureはepoch・actor・子バフ・world世代の改変検出付き。Windowsへ渡した固定package `9b2d57fb…` はCPU42検査とnative13事前検査に成功。その後、CPU APIも不正な対象種別・未登録攻撃者を状態変更前に拒否するようにし、最終Mac固定package `11a78f5c…` のCPU43検査・native13事前検査で全指紋を保持した。scopeの異なる13はゲーム全戦闘13例とは数えない。

最初のv1はliteral ABIをlanding entryへ渡したため全正例が入口status64。guardは正しく働いており、host descriptorだけを既存landing ABIへ修正した。v2のMetal16＋独立seal、その後v3のMetal18＋独立sealへ進み、同じGPUソースを使った。各失敗/capture/claimは保持。実runは生成cache必須hitで、追加Slang0。初回事前生成はCUDA/Metalの2呼び出し。CUDA生成約1.39MB。

検証driverは既存literal counter executorをresident Runtime163528Bとして使い、追加のtyped world/state領域はoutput600000以降、総stride786432word。型付き時計は既存`world_schedule.slang`とstate coreを使用する。通常戦闘入口のRuntime138952B・147ソースを変更しておらず、旧Metal33/46・戦闘証拠も保持する。driverのcounter/typed領域は別であり、通常戦闘の自動生成元を接続したとは主張しない。

静的inventoryを再監査し、全266記録・245 input SHA・20未対応分類と順位を保持。`all_projectiles` とprojectile/shield倍率の分類へ、この限定foundation証拠だけを追加した。分類は引き続きmodel gap、通常受付は拒否のまま。

## Windowsと残件

最終固定packetを履歴なし `codex/cuda-destructible-counter-v1-source`、commit `642ab82f78de7ba1e32f74ab264f5af6debd5a8a` の2filesで共有。Windowsにはこの18入力だけ、既存全stage JobのBelowNormal/2GiB/180秒（内側60秒）で1回依頼した。CPU42/native13 gateは同stage内で行い、別のCPU stage・通常4682入力・full battle・bench・cache-check・追加GPUは依頼しない。WindowsはCPU42/native13とSlang生成に成功したが、内側60秒でtimeout。外側は141.509秒でexit1、外側timeoutなし。Slang2呼び出し計3.996秒、生成全体9.197秒。NVRTC作成成功後にcompileへ入ったが戻りはなく、GPU起動/readback0のためCUDA数値は未確認。NVRTC開始後の観測可能時間は約28.646秒で、完了所要時間とは呼ばない。GPU childの全件verify16.481秒等も内側予算を使う。時間枠だけを拡大して再試行はしない。両Job2GiB/BelowNormal、外側peak1,255,882,752B/内側1,170,563,072B、終了後空・missing0。service未確認なので環境保持false、旧7欠落・旧timeout原因はunknown。生成cacheは完成し、NVRTC artifactは未完成のclaimを保持する。

生成ソースと絶対パスを含む16file reportの外部送信はauto-reviewが拒否。ソース・パス・PID・tokenを除く指紋/時間/判定4JSON＋manifestへ縮小した。縮小版の審査拒否はなかったがWindowsのGit認証がなく、設定を変えずCodex経由で元bytesをMacへ回収する。既存の厳密normalizerのSHA自体とCUDA/Metal normalized SHA、input SHAはMac sealed基準に一致する。正規化器の変更はない。

次は通常戦闘のtyped生成元・選択・着弾の接続、盾迎撃／倍率、破壊固有の効果通知の意味論である。本段階では解決済みImpactが入力で、自動武器・全キャラ・`all_projectiles`の実戦経路・ゲーム仕様の完全再現は未完了。
