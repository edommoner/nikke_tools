# 武器変更の参照弾数を共通実行器へ接続

`weapon_change.max_ammo_scaling_ref`を、既存の参照解決器・弾薬容量memo・通常の武器フェーズへ接続しました。CUDA／Metalは同じSlang、静的descriptor、入力と比較器を使います。CPUで戦闘中の弾数を先に計算する経路は追加していません。

正本はpinned `timeline.CharState._full_ammo`／`_tick_weapon_change`／`_finish_reload`と`BuffManager.ref_count`です。参照の優先順位はownerのゲージ→召喚体の生存数→名前付きcarrierのstack。名前がないNoneは倍率1、登録済みの値0は容量0です。参照値を整数へ切り詰めて表記弾数に掛け、モード進入／再進入と再装填完了時に固定します。進入前の即時弾薬操作で一度取得していても、実際の進入時には取り直します。進入待ち中に値が変わる場合もCPUと同じです。参照がある場合、`max_ammo_buff_applies`の真偽にかかわらず通常の最大弾数buffを加えません。sentinel `max_ammo=-1`は参照を使いません。

容量0を単純に射撃前終了へ置き換えていません。正本は通常の射撃処理の後に「全弾発射時」を検査するため、通常の容量0では再装填開始処理の後に終了し、無限弾薬が有効なら1発撃ってから終了します。base弾薬の復元と`state_end`通知は既存の終了経路と同じ順序です。持続モードは再装填可能ですが、durationまたはduration_bulletsのあるモードでは開始した再装填をモード中に完了しない正本の規約も保持します。

入力の既存referenceテーブル第4語にkey9bit／name8bitを格納し、別kind・非combat・不一致のidentity・未知bit・sentinelへの不正descriptorを拒否します。Runtime配列の追加0、stride138952、CUDA定数48バイトです。表記容量は厳密な整数値1..10000（またはsentinel -1）と明示的な単純参照名を必要とし、実行時は非負の参照値を整数化し、表記弾数との積はsigned32最大値まで。範囲外は明示的なerrorで、wrap／丸め直し／CPUへの無条件fallbackは行いません。binary64、整数変換本体、pow、CPU正本、strict normalizerは変更していません。

CPU契約は`reference --suite mode-capacity`の29件。None／0／小数切り詰め、owner、参照優先順位、expiry後も保持するsnapshot、entry wait、再進入、再装填、最大弾数buffの非適用、チャージ、散弾・2銃口、sentinel、即時回復／除去／進入前取得を含みます。観測はnativeの実呼び出しをprofileし、追加の状態照会をしません。終了時にリセットされる_wc_shotsの差を発数と誤認しないよう、実際の_fire／_charge_fireの戻りを観測し、物理発数とpellet packet数を別に検査しています。全既存nativeフィールドとskill traceの保持も確認しました。

Metal実機のsealed suiteは`mode-capacity`32（native26／拒否6）、追加だけを実行した`mode-capacity-instant`3、E.H.の全定義を含む`mode-capacity-rosters`2（3秒／30秒）。追加3件のために最初の32入力をGPUで再実行していません。E.H.の物理履歴は152／1388件・省略0。30秒のnative観測では容量1のモードが4.0166…秒から4.4333…秒まで実行され、実際に1 packet発射することも確認しています。複数倍の容量は独立ケースで検証しています。

同じ最終GPU sourceで既存849、部位63、ナユタ／レム4、味方バースト16、ルピー2も全件一致・独立seal。合計971入力、旧934の全input/native/output entriesとraw2,938,109,952バイトを全byte保持しました。CPU回帰330件成功・失敗0です。既存のレム30秒55件省略などの履歴容量制約は残ります。過去のquery／weapon／definitionのfixtureは置換せず、4ファイルの有限deltaを逆変換して元のSHA／tokenへ照合します。

途中で見つかったsealのCWD混在も修正しました。古いadapterには相対パスのimportがあり、呼び出し元checkoutのfactoryを読むとSaved input mismatchで正しく拒否されました。sealの子プロセスを検証packageのCWDで起動し、2つの異なるoracleを置いた実子プロセステストで修正前の失敗・修正後の成功を確認しました。32入力の保存結果をCPUだけで再監査し、package自身からのsealと完全一致。元のGPU claim／captureは保持しています。

旧query guardの3失敗はGPU前に停止し、claimも未作成でした。承認対象の有限deltaだけを既存guardへ接続した新packageで回帰検査を通しました。正本の60Hz時刻と再装填可能条件を誤った当初のfixture想定、source refreshの不正scalar、終了時の発数観測の修正もcheckpointへ記録しています。

最終sealed packageをfresh展開し、CPU52検査と32入力／native26の事前照合を通しました（GPU0、claimなし）。source certificateの14検査、release時のCPU29契約のsource identityも再確認しています。

full114／commands115のsource certificateを実証と両生成から更新しました。新しいCUDAコンパイル／リンク／計算一致の証明ではありません。Windowsの追加GPU・コンパイル・native戦闘は0、7プロセス終了の原因unknown／環境保全falseを維持します。静的packing220/266・base160/203・75分類をGPU対応率とは扱いません。通常UIはCPU、全キャラGPU認定0、最終ゴールは未完了です。

使用例（新規出力先、既存venvのPythonを使用）:

```sh
python scripts/nikke_gpu.py reference --suite mode-capacity --out /tmp/mode-capacity-reference.json
python scripts/nikke_gpu.py package --suite mode-capacity --out /tmp/mode-capacity.zip
python scripts/nikke_gpu.py unpack --archive /tmp/mode-capacity.zip --dest /tmp/mode-capacity
```

run／auditは展開したpackageをCWDにして実行してください。sealは明示されたpackageをCWDにするよう修正済みです。証拠・hash・失敗・制限は`research/portable-mode-capacity-checkpoint.json`に集約しました。
