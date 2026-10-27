# 実ADDの座標と通常射撃を結ぶCPU契約

`reference --suite logical-actor-geometry-common --out NEW.json`は、元ベロータ5人編成の全68定義/実武器/育成を保ち、通常RLの着弾をBODYと実ADDへ接続するCPU契約。元`multi_hit:4`、敵防御低下`그리디`、子攻撃`그리디 2`を使い、観測用effectを挿入しない。新しい明示座標モデルであり、既定CPU戦闘との同値やGPU実証ではない。

## 必要だった接続

元のWorldSchedule/actor registryはADDの生存・HP・世代を持つが、canonical GeometryはPART/妨害物の形状を扱う。従来の単一typed shieldやPARTを敵数へ読み替えても、通常RLが複数論理敵へ当たるproducerにはならない。

`coordinate_logical_actor_geometry`は、配置されたADD labelへliteralな円/回転矩形を結ぶ明示scope。登録済みADD以外、重複、未知形状、非有限値を拒否する。BODY/PART/typed actorへの偽装や、独立HP/敵pool/時計を追加しない。1〜127個のcollider上限は全GPU actor容量の認定ではなく、GPU統合時には既存BODY/PART等を含む全体容量も検査する必要がある。

実際の`_fire`/`_charge_fire`ごとに生存世代と幾何を固定し、既存`_coord_pellet`と共通sampling/shape数値規約にpoint抽選・critical・係数・packet順を計算させる。新しく計算式を持たない。前面ADDを通常のbody-hitとして通知する分類だけを明示し、PART分類と既存coreチャンネルは保つ。この戻り値境界はchecked source rewriteで外側5returnだけを検査する。内部のdamage/hit helperは書換えない。投影対象外の射撃は元の関数へそのまま返す。

作られたpacketの同一objectを既存`_land`へ渡し、landing中だけ宛先を世代付き論理labelへ接続する。通常routing/HP/overkill/lifesteal/counterは元処理を使い、終わればeventのtarget/toを戻す。同じlabelでも別世代ならlive filterを通さない。group子packetは元の凍結集合のvisibilityを使う。新scopeが親の1対象visibilityで子集合を上書きしない。既存の32 group/128 targetのcollectorと通知器を再利用する。

BODYの通常packetを本体へ、ADD colliderのpacketをそのADDへ渡すこと自体が、この明示空間モデルの追加契約。射撃を全敵へ複製するroutingではない。自動照準、画面投影、未知のゲーム距離/Lock On、skill扱いの武器変更、全形状/全容量/全世代遷移の認定ではない。

## 元6条件

| 条件 | 確認する動作 |
|---|---|
| BODY＋ADD3、3秒 | 実RLで4敵group→元の防御低下と追加攻撃 |
| BODY＋ADD2、3秒 | 3敵では4敵通知を出さない |
| ADD1体が範囲外、3秒 | collider登録数ではなく実着弾集合で判定 |
| BODY＋ADD2＋実PART、3秒 | PARTは実着弾するが4体目の敵に数えない |
| 1HP ADD3、3秒 | 宣言spawn後の元射撃で退場。子攻撃は死んだADDへ再配送しない |
| BODY＋ADD3、30秒 | 元burst/射撃/周期処理を含む長時間のgroup/子着弾 |

retirement条件は、他の元射手を止めずliteral1.51秒spawnを使う。敵HP・source effect・射撃時刻を上書きしない。比較は元chars/config/seed/武器と全effect/ownerのidentity、全SimResult、group/実receipt/子着弾、敵def fieldの実recipient handle、全point/drawとphysical RNG stateを保存する。PARTの着弾は全SimResultで、BODY/ADDのgroup membershipは既存receipt streamで照合し、両者を同じstreamと扱わない。

## 検査と境界

専用10検査は実4敵/実PART/退場、決定性、同名別世代の拒否、packet復元、投影対象外fallback、未知/非ADD binding、全alias復元を含む。元の全group処理・source rewriteも回帰検査する。`portable_missing_consumer_audit`は従来のtyped opt-in追加より古い2引数期待で失敗したため、変更前HEADの両source byteが一致することを確認し、実際の3引数・両False default・型/依存guardを厳密に検査するよう修正した。default True、未知引数、型guard削除の負例を保持する。既定producerは引き続き未設置。

最初のreference失敗は、scalar requestへ座標PARTを混入したものと、PART着弾をgroup専用receiptへ要求したもの。scalar request identityとdeclared coordinate worldを分け、実PARTは全SimResultへ要求して修正。失敗ファイルは保持する。旧packetでの監査再実行はpinned IMPL-STATUS.md未同梱で失敗し、baseline成功とは扱わない。

CLIは全6件をGPU/packing禁止で実行し、`reference_model_gap=True`、`historical_native_equivalence=False`、`gpu_wire_connected=False`を保持する。`multi_hit`の分類にはこのCPU契約を別フィールドで付け、既存Metal証明や全キャラ対応へ昇格させない。default GPU suiteには登録しない。

## 次のMetal接続

1. literal colliderから既存actor poolのnode/slotへ結ぶ共通wireを作り、raw入力の重複/型/容量/所有権をCPU/Slang/Swiftで一致させる。ADD HPをtyped destructible poolへ複製しない。
2. 現sampled physical executorのshot snapshotとshape判定へ接続し、実BODY/ADD着弾とbody-hit通知を既存landing/groupへ渡す。第二のsampler、damage式、時計を作らない。
3. 既存CUDAMetal共通Slang entryから明示的に有効化し、旧entryの生成byte/既存goldenは保持する。完全なsource inverseとRuntime/arena監査が先。
4. 元6件のfull native期待から固定packetを作り、M5実GPU1回＋GPU禁止fresh sealを行う。CUDAは同じ計算/テストとbounded cache経路を使い、旧Windows transactionが終端不明な間は新runを送らない。

今回GPU/Slang変更とGPU実行は0。全キャラ/全特殊効果/公開GPU受付は未達。
