# 2026-10-28 M5 Metalとfresh独立監査で14入力をseal

修正版688de06e/package80c86ed0…は14入力すべて全比較成功。GPU4.886496秒、冷PSO58.768053秒、fresh事前CPU587.491141秒。親のnative6/creation context6を再利用した比較の追加native0。別fresh GPU禁止14群は667.090273秒、親結果再利用0で全一致した。同時作成golden/source証明書を通常CLIへ登録。旧18入力も同sourceで再認定済み、全旧input/native/readback byteを保持した。

死亡条件のv4との差は4word（query/最終/全体overkillとattempted lands）のみ。他13件の全readback byteは同一。失敗v4/raw/claimを保持し、再試行していない。元69定義/6条件の宣言モデルを検証した範囲であり、ゲーム幾何/デフォルトproducer/全キャラ/現CUDAの認定ではない。通常enemy-healingと同一計算のenemy-healing-cache-onlyを使える。CUBIN/O1/paired generationの必須guardは従来profileを再利用する。以下は設計・実装の履歴。

# 元アンの回復量低下を実ADD回復へ接続するCPU契約

`reference --suite enemy-healing-common --out NEW.json`は、元アン：ミラクルフェアリーの5人編成/全69定義を保持し、元の敵向け`heal_received_pct`を実際の有限ADD回復へ接続する。privateな明示環境モデルであり、既定CPUやゲームの回復規則への同値、GPU実証ではない。GPU入力変換と共通Slang consumerを実装中。Metal実行・独立監査は未成立。

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

## 共通GPUへの実装経路（実機認定前）

`enemy-healing`は開発専用suite。元6条件とraw拒否8件を同じCUDA/Metal adapterへ渡す。入力は既存logical geometry prefix115,680wordを保持し、EHL1/version1の4,368wordを追加した120,048word。32行×136wordに既存node番号・flat binary64量・最大127個の既存actor slotを順序付きで保持する。CPUで計算した時刻列/HP/世代は渡さない。source graph/registry/有限HPのowner bytesを既存compilerから再照合する。private packing scope外では敵heal_received_pctの受付を変更しない。

共通Slangは既存world frameのpool同期直後・overlay/tick前に回復し、初期frame0も既存source generationを一度だけ消費する。出力1,867,648以降の旧未使用領域にheader16・node別seen32・最大1,024件×32wordのreceiptを置く。HPは従来pool+4、stack/寿命/世代付き敵carrierは従来consumer、数値は従来software binary64である。見えない旧世代は既存actorFieldMemberで除外し、hit/score/overkillを書き換えない。stride/entryを明示登録し、旧entryへの新stride混入をCPUで拒否する。

比較器は全回復receipt・未使用row/予約word、全ADDの最終HP/hit/世代/退場・raw得点/overkillと実SimResultのキャラ別roundを先に検査する。その後、検証済みの追加bankだけをゼロへ投影し、従来の全battle/physical/group/skill-history比較器をそのまま実行する。旧nativeの値や比較項目を置換しない。既存7ファイル（初版6）の変更は固定9b3f84ccからの全文SHA/完全一致inverseで記録し、旧source監査へ合成する。生成コードnormalizerは変更しない。

現時点のwire8/新runtime gate5/元モデル11の計24検査と、旧logical source/arena5検査が成功。完全native事前検査、paired生成、Metal実行、fresh独立sealはこれから行う。開発suiteの登録や単体検査をGPU成功と扱わない。

## 最初のMetal実行で見つかった同射撃内の死亡後packet

v4/package2d9216cb…はM5で14入力を1回実行し、5正例＋8拒否が全比較成功、死亡済み1件だけ過剰ダメージ不一致。実GPU4.8772秒、冷PSO58.8500秒、fresh CPU約580秒。成功したtransportを計算全成功へ昇格させず、raw/claim/失敗を保持。GPU再試行0。共通CLIのfresh保存group3監査でも同じ失敗を保持した。

回復receipt/得点/最終HPを保存readbackと最小native health診断で切り分け、GPU85404対CPU498896のraw overkillに特定。既存logical direct配送が、前のpelletで死亡した同世代ADDを`alive==0`で早期dropしていた。正本hit_addはその残packetを過剰ダメージへ加算する。新修正はstale世代の拒否を残し、同世代は既存ActorPoolLandへ渡すだけ。既存の不受理receiptにより命中/得点/counter/group/traceは発生しない。別のHP/算術/通知器は追加しない。HP1への10→20の実hit_addがscore1/overkill29/hits0になる回帰検査も追加した。

比較器のraw score/overkill assertに項目/実値/期待値の説明を追加し、比較内容は維持。旧logical entryの同じconsumerにも作用するため、旧13/5入力の現source再認定も必要。古いgolden/証明書を新sourceへ付け替えない。新固定packetで14入力のMetal＋fresh独立sealを行う。まだ修正版のGPU成功はない。
