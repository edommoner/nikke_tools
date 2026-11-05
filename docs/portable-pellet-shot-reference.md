この20ケースのCPU準備段階に続き、signed32下限を加えた21契約と共通GPU接続を検証しました。現行記録は[GPU接続](portable-pellet-shot-gpu.md)を参照してください。以下はCPU準備時の記録です。

# 1射内の散弾命中数: CPU契約

`reference --suite pellet-shot --out <新しいJSON>` を共通CLIへ追加しました。
正本CPUのみを実行し、packing・GPU build・GPU executeは既存の禁止ガードで遮断します。
GPU入力の受付・Slang実装・Metal実証はまだ追加していません。

20のliteral契約をfresh不変packageで検証しました。59射・62通知が成功し、
共通referenceの負例と旧失HP契約を含む3群18テストも9.392秒で成功しました。
報告は `research/portable-pellet-shot-reference-checkpoint.json`、元の全native報告は
`/tmp/nikke-pellet-shot-reference-v1-report.json` です。checkpointのSHAで保存元を結びます。
パッケージは `/tmp/nikke-pellet-shot-reference-v1.zip` に保持します。

## 正本で確認した挙動

- 判定は発射時に確定したpellets×muzzles。発射途中のpellet callbackで散弾数を増やしても、その射の閾値判定には反映しません。複数銃口ではダメージ係数が銃口ごとに適用され、単純な全packet分割と同一ではありません。
- 各pelletの通知を完了してから、1射内閾値通知、on_attack、銃口数分のhit_countの順です。1射内で得たATK buffは当該射のpacket damageを変更せず、次射へ反映します。
- 閾値は数値、次に元の文字列でソート。`5`、`05`、`+5`、` 5`、`５`は別通知です。通知だけを数値へ正規化すると正本と異なります。
- 完全一致する文字列は一度だけ通知。ただし同じdescriptorを効果に2回書くと正本candidate indexにより効果は2回発動します。別効果の同名閾値も通知は一度、各効果は発動します。
- 0・負閾値は各射で通知。大きい閾値、条件false、max_trigger上限、有限buff失効を独立に確認しました。通知試行と実際の効果発動回数は別です。
- autoとauto_warmupが対象。chargeは5pelletでもこの通知を発行しません。通常の累積命中数ではありません。
- 5番目の所有者を含む分離、発射中の散弾数変更、混在on_attack、重複descriptorを含みます。

観測器は実際のnotify呼出しと `_fire` のcaptured hit_count、戦闘後carrierを読みます。
追加buff照会は行わず、既存observerのnative全項目・traceをそのまま保持します。
profileの合成・失敗時の復旧、照会回数一致、通知identity／順序／回数／所有者／時刻、
stack、packet damage／count、総ダメージの故障注入を検査しました。

開発中の初期予想で、2銃口のdamageを全pelletで割る点、有限buffの再発動後stack、
別所有者caseで元の射手を停止する点を修正しています。GPU結果や既存goldenに合わせた変更ではありません。

## 次の接続

1. 元の閾値文字列を所有者ごとの静的IDへ写像し、数値閾値と別にdescriptorへ保持する。数値だけを比較してaliasを併合しない。
2. 共通SlangのfinishWeaponShotで、auto系のみ、captured countを使用し、gauge計算・on_attackより前へ通知を接続する。chargeや累積counterへ流用しない。
3. host／GPU双方で閾値・IDの範囲、一致、並び、重複の受付契約を検査する。既存target inheritanceにevent27は含まれず、対象を継承する変更は別の正本証明が必要。
4. CPU正負例→小さいMetalケース→実キャラ→旧1050保持の順で、不変packageと独立sealを使う。GPU source変更までは旧Metal回帰を繰り返さない。

今回GPU source・数値設計・Runtime ABI・旧golden・compiler証明書の変更は0です。
全キャラ認定0・UI CPU・ゴール未達を維持します。Windowsは7プロセス終了の原因unknown、
環境保全false・サービス未識別のため追加検証停止中です。ゲーム／動画の併用というユーザー回答は
因果関係を示しません。今回Windowsの照会・native・compile・GPU・再現操作は0です。
