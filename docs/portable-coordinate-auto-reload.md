# 自動装填の保留と射撃後待機

`coordinate-auto-reload` は旧313入力に通知・期限・mode境界の9worldを追加する共通CUDA／Metalの検証入口です。Runtime／wire容量を増やさず、既存のready／charging／post-delay状態と保留フラグを使います。

正本の `_pending_auto_reload` は適格な射撃で立ち、射撃後待機を完了した `_tick_charge` が実行して解除します。coverでreadyへ戻ると、その後の新しい射撃の待機終了まで通知を遅らせます。速度効果が途中で切れて次の射撃が不適格でも、保留をfalseへ上書きしません。mode開始／終了での破棄は既存 `app/weapon_mode_runtime.py` の共通契約を維持します。

GPUはこれまで待機時計だけを見て実行し、cover後に通知が早まりました。共通weapon tickにpost-delay完了を集約し、保留をORで保持します。さらに正本の `was_ready` を保ち、coverでreadyへ戻ったmode chargeは弾倉を補充し、通常のpost-delayから戻る場合は補充しません。control producerで先にphaseをreadyへ変更しません。

既存のpassive manual observerへopt-inで `_auto_reload` と実pending状態を追加しました。既存ケースでは返り値を変えません。通知からのdamage／攻撃力効果を元比較器で照合し、無通知先のケースも最終pendingとammoを比較します。CPUで操作時刻表や装填結果を計算してGPUへ入力しません。

最初の8入力はMetalで5一致・3差分。待機判定修正後の322入力は321一致で、最後の無通知先・待機途中終了がmode弾倉補充漏れを検出しました。元の失敗raw／claimを保持しています。旧313と初8の入力・native指紋は不変、補充修正前後も全322の入力・native指紋は同一です。goldenを差分へ合わせて書き換えません。

`seal --audit-receipt NEW_PATH` は同じfresh子監査のPID・比較domain件数・再利用なし・所要時間・入出力SHAを保存します。goldenとsource certificateと同じ1回の監査を使い、件数不明・live parent再利用・同一process・出力衝突を拒否します。`native_cases`は比較したdomain件数で、低水準の関数呼出しをinstrumentした値ではありません。GPU／Windows／compiler上限180秒、GPU禁止saved監査上限240秒を維持します。

全キャラ認定・公開受付・現CUDA／warm cache性能の確認は別の残件です。自動装填とdown／復活、通知からのmode変更・容量変更、healing storage／混在actorの元定義を引き続き検査します。


## 固定実証と残件

修正版の固定packet `/tmp/nikke-auto-reload-develop-v4`（`6b24922b…`）とcapture `/tmp/nikke-auto-reload-metal-v4` は、275 native＋47拒否の全322入力がApple M5 Metalで一致しました。GPU0.697421秒／初回PSO93.756371秒、CPU事前192.452146秒／通常比較8.671853秒です。通常比較は同じ親の275基準を再利用し、追加native計算0。別processのGPU禁止fresh監査は210.929726秒で全322／275 native domainを照合し、live parent receiptなしを明示しました。この同じ監査からgoldenと専用full-source certificateを作成し、sealed suiteへ登録しています。証明書はCUDAのcompile／cache／実行成功を意味しません。

旧313の全input／native指紋は不変です。312件の全2,208,780,288byteを保持し、残る `automatic-reload-cover` の全word検査ではfield処理workの件数43→42・累積work130→129の2wordだけが変わりました（512176／512178）。ダメージ・イベント・状態のwordは同一です。初版修正の321成功入力との比較でも316件全byteを保持し、5件は同じwork統計2wordのみ変化。元の失敗1件はammo0→1とwork統計だけが変わりました。全313／全321 raw保持とは主張せず、原失敗と全rawを保持します。

CUDA／Metalの生成ペアは必須cache hit・compiler0で、実GPU captureの生成物と両方の全byteが同一でした。CUDA計算・warm cache速度の実機証拠は未取得です。`research/coordinate-auto-reload-evidence/` に元失敗・成功・独立監査・全word差分・test-only更新・復元検査付きsource archiveの記録を置いています。新sourceの実GPUは8入力・322入力・修正版322入力の計3回、同claim retry0。容量停止／テスト更新／独立監査はGPU追加0です。


最終compact `85d28d12…`（1871 files／8,716,209byte）は選択33・共通制御470（Windows専用1skip）成功、全payloadとcheckoutの全byteを終了後も確認しました。CLI分岐のimport scopeを既存復旧検査が検出した元失敗も保存しています。rawは全reader終了後にbyte／SHA／inodeを保った疎化で保持し、削除していません。全キャラ認定0／UI CPUを維持します。
