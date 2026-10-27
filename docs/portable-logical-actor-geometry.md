# 実ADDの座標と通常射撃を結ぶCPU契約

`reference --suite logical-actor-geometry-common --out NEW.json`は、元ベロータ5人編成の全68定義/実武器/育成を保ち、通常RLの着弾をBODYと実ADDへ接続するCPU契約。元`multi_hit:4`、敵防御低下`그리디`、子攻撃`그리디 2`を使い、観測用effectを挿入しない。新しい明示座標モデルであり、既定CPU戦闘との同値やGPU実証ではない。

## 必要だった接続

元のWorldSchedule/actor registryはADDの生存・HP・世代を持つが、canonical GeometryはPART/妨害物の形状を扱う。従来の単一typed shieldやPARTを敵数へ読み替えても、通常RLが複数論理敵へ当たるproducerにはならない。

`coordinate_logical_actor_geometry`は、配置されたADD labelへliteralな円/回転矩形を結ぶ明示scope。登録済みADD以外、重複、未知形状、非有限値を拒否する。BODY/PART/typed actorへの偽装や、独立HP/敵pool/時計を追加しない。1〜127個のcollider上限は全GPU actor容量の認定ではなく、GPU統合時には既存BODY/PART等を含む全体容量も検査する必要がある。

元のpublic requestがexpected modeであることをidentity検査した後、既存`common_sampling_policy`を適用する。元numeric policy保持や既定CPU同値とは主張しない。実際の`_fire`/`_charge_fire`ごとに生存世代と幾何を固定し、既存`_coord_pellet`と共通sampling/shape数値規約にpoint抽選・critical・係数・packet順を計算させる。新しく計算式を持たない。前面ADDを通常のbody-hitとして通知する分類だけを明示し、PART分類と既存coreチャンネルは保つ。この戻り値境界はchecked source rewriteで外側5returnだけを検査する。内部のdamage/hit helperは書換えない。投影対象外の射撃は元の関数へそのまま返す。

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

### literal入力wireの実装

`portable_logical_geometry_wire.compile_logical_geometry` は従来の座標入力109,968語を全byte保持し、末尾5,712語にLAG1/version1の明示bankを追加する。header32、最大127行×32語、actor slot逆引き128語、残り1,488語はzero予約。各行は既存actor slot/kind/identity/source/run/ordinalとliteralな形状・z・共通binary64回転係数だけを持つ。HP・世代・spawn時刻・着弾予定・damageは入れない。全体128 actorの上限は元registry compilerがBODY/PART込みで検査する。

raw検査は既存registry headerとADD bindingの一致、行と逆引きの一対一、common matrix bytes、全予約語zeroを要求する。別label/PART/BODYへのbinding、重複slot、非有限形状、不正型、容量超過を拒否する。Slang定数は同じPython layoutから生成し、既存arena auditorで入力所有権を検査する。このbankは旧typed bankと同サイズだが別protocolで、typed actorやHPへ読み替えない。

専用8検査で元6条件すべての全68定義保持と既存入力一致、最大127 collider＋BODY、実PARTとの分離、raw破損、共通回転、入力非変更を確認。既存幾何10/group9/source rewrite3も成功。共通CLIのoriginal-catalogue検査リストへ登録した。誤ったファイル名でsource rewrite検査を指定した最初のコマンドは0件/終了5であり、実在の`test_reference_rewrite.py`の3件を改めて実行した。0件を成功には含めない。

今回の追加はstatic入力lowering。新Slang entry、Swift admission、snapshot/landing consumer、Metal実行・独立sealは未実装。`gpu_wire_connected=False`と全キャラ未認定を維持する。旧GPU source/生成物/cache identityを変更せず、Windows新依頼・GPU実行・Slangコンパイルは0。

### 共通shot snapshot・着弾consumerの実装（実GPU未認定）

新`world_coordinate_logical_actor_entry.slang`は既存original shared entryを使い、通常射撃のCS_FRAMEへ生存中の実ADD handleを追加する。z→既存poolのbirth→node→ordinal→provenanceの降順で既存PART/妨害物と合流する。技能のCP_FRAMEは変更しない。形状は既存software binary64の判定へ渡し、ADDの非core通常量も既存`damageFromFactors`から取得する。整数親量は既存PacketIntegerSumへ渡す。独自のHP・時計・sampler・damage式は追加しない。

BODYは凍結したBODY世代へ、ADDは実slot/凍結世代へ直接着弾する。死亡/別世代への配送は拒み、通常landingのreceipt tailを元のBODY/ADD routingと新direct routingで共有する。通知のbody-hit分類、distinct group、credit/overkill、counter/lifestealは元のconsumerを使う。skill扱いの武器変更では新幾何を有効にしない。新scratchは既存skill履歴continuation直後の2,048語＋16語で、全入出力領域の所有権と非重複を検査する。履歴は既存2,048行/48語の共通codecで、新headerのmagic/versionを明示admitする。

固定compiler-only snapshotから新entryのCUDA/MSL生成と両reflection検査に成功（約4.18秒）。Runtimeは既存と同じ138,952byte、alignment8、CUDA constants48byte。旧history entryも現sourceから生成し、保存済みCUDA/MSL/両reflectionの原byteが全て一致した（約4.15秒）。この生成・reflection検査はCUDAコンパイルやGPU実行証明ではない。共通code変更の逆投影は5既存sourceと5追加shaderを厳密hash/差分で固定し、旧監査chainへ接続した。normalizer/旧goldenは変更しない。

全戦闘の既存観測chainとの合成で、初回はshot wrapperのlocalsにある`self`がLogicalGeometryになり失敗した。wrapperをchecked ASTのshot scopeへ変え、元の`self/t/bm`と関数名を保持した。group/passive wrapperより前に設置する順序を要求し、逆順はaliasを復元して拒否する。最初の逆順rewriteのNameError、旧arena監査へ逆投影を未接続だった回帰失敗2件も成功に数えない。修正後の旧group/source rewrite/arena19検査は全成功。CPU契約6件の全native出力は変更前の固定結果と完全一致した。

既存full native chainも新modelへ合成し、元効果/武器/設定のidentity、物理packet、全point/draw/RNG、group/子着弾を保持する。新しい比較器を作るための別battleではない。common CLIの検査群へ専用source/arena4件と実full native合成/逆順拒否2件を追加した。新runtimeのSwift wire admission、GPU suite/全出力比較への登録、固定packetのMetal実行＋fresh sealは次の作業であり、まだ未実施。公開受付・全キャラ認定・現CUDA実機認定は変更しない。Windows新依頼0。

最終的に全6件を既存full native observerへ通し、group/実receipt/子/子着弾/全point/全draw/624語RNG＋index/logical shot/packet/pellet channelの全10項目が固定CPU契約と完全一致した（85.46秒）。軽量な元CPU契約の再照合は全native byte相当を1.37秒で保持。両者を同じ検証費用やGPU認定とは扱わない。新entryのrequired paired generation cacheは0.43秒、hit/Slang0を既存receipt監査で確認し、cold receiptも別途保持した。CUBIN/NVRTC cacheやCUDA実機hitの証明ではない。出所・失敗・保持結果は`logical-actor-runtime-generation-v1.json`、詳細はprivate proofへ保存する。

今回GPU/Slang変更とGPU実行は0。全キャラ/全特殊効果/公開GPU受付は未達。

## 固定packetでの最終検査

固定27466a62/package0175fe99…のown CLIがCPU全6条件を2.34秒で検証し、全native/receipt/point/draw/624語RNGをprivate5,351,260byteに保存した。30秒では実group15/元4敵通知15/子着弾60、retirementは死んだ3ADDへ子を配らずBODY1着弾。専用10検査と元group等の検査成功、固定packetの25群226unit/CUBIN O1・2GiB・60秒compile-plan policyも成功。旧GPU entryの生成cache必須hit/Slang0、CUDA/MSL/両reflectionの原byteを直前のsealed captureから保持したが、新しい論理幾何のGPU実証ではない。GPU/Windows新run0。出所・失敗・範囲は`logical-actor-geometry-cpu-v1.json`と`logical-actor-reference-final-checks-v1.json`。
