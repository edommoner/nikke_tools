# 元アンの回復量低下を実ADD回復へ接続するCPU契約

`reference --suite enemy-healing-common --out NEW.json`は、元アン：ミラクルフェアリーの5人編成/全69定義を保持し、元の敵向け`heal_received_pct`を実際の有限ADD回復へ接続する。privateな明示環境モデルであり、既定CPUやゲームの回復規則への同値、GPU実証ではない。GPU入力変換/Slang consumer/Metal実行はまだない。

## 既存処理の所有権

`enemy_healing_model`の宣言は既存idle node ID、既存ADD label列、flat回復量だけ。WorldSchedule/BossScriptの既存`run.opens`遷移を消費し、新しい時計や予定着弾表を作らない。既存source frame呼び出し2箇所をchecked ASTで包み、world遷移直後・元のstate-effect/buff tick前に実行する。同じ初期t0フレームが2度呼ばれてもsource generationを一度だけ消費する。

健康は元の`_Add.dealt`に保持する。finite capは元`SummonSpec.hp`、世代/生存は元registry/source runであり、第二のHP poolを作らない。BODY/PART、未登録label、hit-count HP、非有限HP、共通32node/128actor超過は拒否する。死亡/未出現/退場したADDへは回復せず、復活を実装しない。hitsと既存`boss.add_dealt`累積得点は回復処理で変更しない。

倍率は既存`BuffManager.heal_received_mult`を呼ぶ。新consumerがenemy labelをqueryするときだけ既存の`enemy_field_visible`を既存`_live`と併用し、同名でも古い世代のcarrierを読まない。味方へ読み替えず、元の69効果/owner/武器/育成/設定/seedを既存observerがidentity検査する。heap clockや独自のstat合算式は追加しない。

## 元6条件

| 条件 | 確認すること |
|---|---|
| Lv10 | 元の-78.93%から約0.2107倍を実HP回復へ反映。期限後は1倍 |
| Lv1 | 元の-43.41%から約0.5659倍を実HP回復へ反映 |
| 上限 | 大きなliteral回復を最大HPでclip。hits/累積damageは維持 |
| 死亡済み | 回復/再生存/追加得点を発生させない |
| 再出現 | 既存waveを繰り返し、世代2へ世代1の未期限切れ効果を渡さない。同じsource frameで確認 |
| 小数回復後の撃破 | 異なるliteral HPの2waveを使い、元の戦闘で小数HP credit/overkillを実際に発生させる |

通常は1/25/35/55秒のidle宣言、再出現条件は1/25/26/35秒の宣言。実発動時刻は元schedulerのフレーム/epsilon規約を使い、literal時刻へ丸めない。回復量の無効果を対応済みとして通さず、元デバフによる正の実回復と、回復が実際の生存/得点へ影響する既存`BossScript.hit_add`検査を行う。

## 数値境界

新HP処理の順序は、既存倍率query→`requested = flat * multiplier`→`applied = min(requested, dealt)`→`dealt -= applied`。整数へ途中変換しない。既存HP表現を使うため、公開HP表示用の計算とeffective gainも別に記録する。

最初の小数撃破assertはSimResultが小数totalを返すと仮定して失敗した。元timelineは`round(boss.add_dealt[owner])`をキャラごとに行い、その和を公開add_totalにする。overkillも最後にroundする。元コードを変更せず、内部の未丸めledgerと公開結果を両方保存して検査する。GPU移植でもraw creditを先にintへ落とす、全キャラ合算してからroundする、既存整数sidecarへ合わせるために回復量を整数化する、という変更はしない。

## 次のGPU接続

1. source node/amount/既存actor slotのliteral wireを定義し、node kindと有限damage-owned HPをCPU/Slang/Swiftの受付で一致させる。既存LAG予約領域を使うならversion/明示entryを変え、旧入力を黙って読み替えない。
2. 既存world frameのactor-pool同期後、CPUと同じphaseへsource-open処理を接続する。HPはactor poolの既存dealt、世代とstat合算は既存enemy fields。別時計・HP heapを作らない。
3. stat42の敵向け受付をprivate opt-inへ限定し、原効果を削除/味方targetへ変換しない。デフォルト拒否を維持する。
4. 小数HPを含む既存score/overkill経路を監査し、内部float creditとキャラ別最終roundを共通化する。元の全状態/履歴/HP/得点比較へ回復receiptを追加し、固定packetでMetal1回＋独立fresh sealへ進む。

CPU専用11検査は実倍率、HP上限、score/hit維持、実生存差、死亡拒否、未期限切れ旧世代、入力/容量/HP型拒否、二重t0、alias復元、小数creditと公開roundを含む。分類はreference_model_gapを維持し、別の宣言CPU契約として記録する。今回GPU/CUDA/Windows新実行は0。
