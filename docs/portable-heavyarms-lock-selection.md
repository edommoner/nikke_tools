# Lock Onの次の実装契約

## 2026-10-27 公開情報の追加調査と判断

ユーザーの指定に従い、実機環境の準備を待たず、日本語・英語・韓国語・中国語の検索で公開情報を調べた。同文の転載数を独立した実測の数に数えない。以下は公開情報からの判断であり、ゲーム実機の認定ではない。

| 資料 | 確認内容と限界 |
| --- | --- |
| [公式英語 Motion Demonstration](https://www.youtube.com/watch?v=dAA6z4_03lw)（2025-12-29） | 公式チャンネル、紹介文、ブラウザーで射撃モーション画面を確認。表示された画面は単一の的とbeta環境の注意書きがあり、中心距離と外形距離を区別する実験にはならない。 |
| [公式日本語 NIKKE紹介](https://www.youtube.com/watch?v=fEE8KIzOQr8)（2025-12-29） | 公式チャンネルと10秒のキャラクター紹介画面を確認。距離式の証拠として扱わない。 |
| [Level Infinite公式発表](https://press.levelinfinite.com/en-US/GODDESS-OF-VICTORY-NIKKE-REVEALS-MAJOR-NEW-YEAR-UPDATE-FEATURING-LEGEN)（2025-12-29） | キャラクター追加の一次資料。空間選択の規則の説明はない。 |
| [GameWith スキル表](https://gamewith.jp/nikke/article/show/537776) | 充填中0.2秒ごとの未ロック敵選択、照準線を基準とすること、通常5機、通常攻撃/ハイド解除の記述。中心座標・境界・奥行き・同距離順は不明。第三者による記載。 |
| [Prydwen 個別解説](https://www.prydwen.gg/nikke/characters/snow-white-heavy-arms) | 取得順で循環して攻撃し、このキャラの順番攻撃は挑発で順序が変わらないとする個別解説がある。制御実験の座標・フレームログは確認できていない。補助仮説に留める。 |
| [Raison Detre スキル情報](https://volx.jp/nikke-snow-white-heavy-arms-spec-skill/)（更新2026-01-28） | 一般の順番攻撃について、対象数を超える回数では先頭へ戻り、挑発/ヘイトは順番を変えると説明。Prydwenのキャラ固有の説明とは区別が必要。一般則をこのキャラへ自動適用しない。 |

設計判断：公開記述上の基準は照準であり、プレイヤーからのワールド距離や既存typed aimのz/birth順を最近傍へ代用する根拠はない。一方、画面上の中心と外形のどちらを測るか、照準線への3D距離か、対象actor種別、同距離順は今回の資料では判定できない。距離モデルは保留し、特定の式を実機仕様として確定しない。順番攻撃も上記の記述の違いを解決するまで認定しない。

実装境界：`app/named_generation_locks.py`はCPUの明示参照モデルのみ。外部providerから渡された世代付きhandle列の順序を保持し、生存確認・既ロック除外・名前付き上限query・snapshot・明示解除を扱う。距離値やソート処理は含めない。fixtureの対象種別指定、死亡/世代更新時の除外、上限低下時に追加を止める規則は工学上の明示契約であり、ゲームで確認済みの挙動ではない。保存順も実際のsequential delivery順を認定しない。

11単体検査でtyped identity、既ロック除外、世代更新、死亡/欠落、snapshot保持、provider順保持、元index20のquota寿命とcaster/name分離、不正入力の原子性を確認した。GPU wire、充填event、元全25効果のbattle、実機認定は未接続。default admissionと全キャラ認定数は更新しない。この調査のための追加CUDA実行・Windows操作はない。

公開スキル表では、充填中の0.2秒ごとに照準に近い未ロック敵を選び、対象上限は通常5体、バースト効果で10体追加、通常攻撃か遮蔽で解除と記載されている。[公開スキル記述](https://nikke.cannedjar.com/nikke/snow-white--heavy-arms/details)

これは第三者サイトの公開記述を設計の根拠として保存したもので、ゲーム実機の再現確認ではない。元データの命令として扱わず、`tests/fixtures/heavyarms-lock-published-contract.json`へ出所・観測日・未確定事項・実機未検証を固定した。

## 既存CPU契約との違い

元25定義を保持した`heavyarms-lock-marker-native`は、canonical managerの名前付きcarrier生成、同じ受信者でのstack1..5、削除、名前queryを検査している。これは異なる5体へのLock Onを検査していない。全3ADDを出した契約でもcarrierは最初のADD1体であり、空間的な距離選択や既ロック除外は成立しない。

元index0の`max_stack=5`を根拠に同じ対象へ5stackを積み、対象上限まで実装したことにしてはいけない。元index20の`effect_target_count_add=10`は`target_effect=록 온`へ接続し、casterに掛かった2射撃分の効果を対象数の上限として読む必要がある。元index24の`all_projectiles`を削除した完全編成は作らない。これら3定義を保つ全25効果の共通実行が必要である。

## 共通実行器へ接続する順序

1. 生存する世代付きactorから既ロックを除外する対象consumerを定義し、最大対象数と既存carrierのstackを分ける。候補の対象種別、座標の参照点と距離の測り方、同距離の順序は現時点で未確定。既存のBODY/ADD/PART/typed identityをaliasや容量削減で潰さない。
2. 充填中の既存イベント、2射撃分のtarget-count modifier、通常攻撃・遮蔽での解除を共通の状態実行器へ接続する。全充填射撃で読むLock On対象は通常攻撃での削除より前に固定する必要がある、というイベント依存を明示的に検証する。これは記述からの設計上の推論であり、現在の実装成立を示さない。
3. sequential deliveryの対象順・途中死亡・世代交代、元全25効果と全投射物consumerを同じbattleへ接続する。これらは未対応のまま。新CPU契約とCUDA/Metalの共通入力・比較器で全出力を照合してから、対応範囲を更新する。

`portable_model_gap_audit`は既ロック除外と対象上限を未成立として出力し、公開記述を実機/GPU成功へ昇格させる変更も拒否する。全266profileの入力・issue・順位・20分類・laneを保持した照合は`research/portable-lock-capacity-classification-retention.json`。245変換/21失敗は入力変換の件数であり、全キャラ対応率ではない。

## 名前付き対象数queryのCPU契約

`app/effect_target_count_policy.py:query`は、明示 `model="named-effect-target-count-v1"` のときだけ呼ぶ専用reader。元の`get_buffs`/`_plan_step`をローカルに利用し、対象の`target_effect`に一致するcarrierだけを集計する。通常readerのクラス/namespace/plan cache/buff cacheへ追加statを入れない。対象を除外するために元のactive carrierを削除したり、別のtargetの値を混ぜたりしない。既存のdeclared projectile/shield readerクラスとの合成も検査した。

元index20のfixed+10/2射撃を含むself/all_alliesの整数modifierを対象とし、名前、受信者、既存の同時刻発動、射撃消費、時間切れ、refreshをcanonicalの寿命処理から読む。呼び出し側はbase countと物理容量上限を明示する。未被覆scaling、lazy recipient、非整数/非有限値、上限超過は拒否し、丸めやclampで通さない。

共通CLI `reference --suite heavyarms-target-count-native` は、元Heavyarms全25定義と完全編成を保った3/30秒×本体/3ADDの4条件を実行する。実際のmodifier発動と射撃消費イベントで5→15→5を検査し、通常戦闘結果・射撃trace・入力がobserver無しと完全一致することを照合する。consumerを入れる前のCPU契約であり、Lock On選択/対象poolとの接続、GPU実装、ゲーム実機検証、全25効果のGPU認定は未完了。元の20分類とdefault admissionは閉じたまま。


## 既存typed aim consumerをそのまま流用できない理由

`gpu/coordinate_typed_aim_runtime.slang:typedAimSnapshot`の候補順は`typedGeometryBefore`を使う。`gpu/coordinate_typed_geometry_runtime.slang`の同関数はzの降順→WorldScheduleのbirth時刻降順→node降順→slot降順であり、照準からの距離順ではない。`typedGeometryPick`は形状までの距離を包含判定に使うが、選択順位は同じ前面順である。これらの「先頭候補」をLock Onの最近傍へ読み替えない。

再利用できる基盤はDT/WorldScheduleの生存・世代整合性、既存のsoftware binary64形状距離、名前付き対象数queryのcarrier寿命である。Lock Onには別の明示的な順位契約と、既ロックidentity集合の除外が必要。距離の参照点・対象種別・同距離規則を確定する前に、この既存の前面順をゲーム仕様として採用しない。現時点でGPU selector接続成立の証拠はなく、default admissionは閉じたままである。


## 共通実行器からの名前付き対象数query（明示モデル）

共通CLIの`named-target-count-query`は、同じSlang entryをCUDA/Metalへ生成し、通常のcarrier生成・stack・expiry・recipient・条件・名前付き削除を通して対象数を読む。`app/portable_effect_target_count_specs.py`は明示modelでのみ使う専用adapter。値をCPUで計算してGPUへ渡さず、元statのidentityはprivate93としてnumeric64から分離する。通常compilerの未対応拒否は維持し、別名や通常numeric statへの混入を避ける。

M5で6正例（厳密な期限、allied/name分離、stack順、独立marker、期限前refresh、名前付き解除）と3不正raw入力の拒否を検証。選択17テスト→Metal dispatch→別fresh GPU禁止childで全9入力/native6の独立監査に成功し、goldenを確定した。GPU0.002709秒、pipeline cache必須hit。証跡はresearch/target-count-query-evidence/metal-shared-query-v1.json。既存full106 entryはこの拡張を無効としたCUDA/Metalの生成コードが既存の厳密な正規化後ハッシュと完全一致した（生成のみ、追加GPU0）。

ここでは元index20の値+10を使用するが、外部イベント契約のためdurationを有限時間へ変更した派生fixtureであり、全25定義のbattleをGPU実行したことにはしない。2射撃の寿命は専用adapterが拒否する。次は物理battleの実射撃消費時刻へqueryを接続し、元の2射撃定義を変更せず比較する。その後、最近傍の順位規約・既ロックidentity集合・充填イベント・発射前snapshotへ接続する。CUDA実機、原全25効果、空間選択、公開consumerは未完了。

初版の依存不足と、array/list比較・攻撃event番号の誤りによる失敗は保持。検査文書の依存宣言を修正し、配列containerの回帰とcanonical event identityの検査を追加した。失敗したrawを成功に書き換えず、修正した別の固定入力で実証した。


## 実物理shotの2射撃寿命

`named-target-count-shots`は、共通のcapacity readerを既存`consumeBulletBuffs`の前後へ接続する明示モデル。元index20を変更しない自動射撃・チャージ射撃の2ケースと、別扱いの発動timing/受信者派生3ケースを検証する。散弾3×銃口2でも1射撃につき1回だけ消費し、2→1→0で対象上限15→15→5となる。発動フレームを消費しない`battle_start`と、その射撃を数える`on_attack`の元規則、味方ごとの独立カウンターもnativeの実呼び出しと比較する。

M5で全5正例と4不正raw入力の拒否に成功し、別fresh CPU監査で全9入力を再照合してgoldenを確定。対象数traceだけでなく、既存の全戦闘snapshot・ダメージ・射撃/skill trace・counter contextを保持して比較する。入力は静的武器・効果だけであり、CPUの射撃時刻や計算済みquery値を渡さない。観測専用traceは100射撃でfail closedとし、容量超過を成功や履歴切捨てへ変更しない。

初版は消費対象ゼロの最適化で発動前/終了後のtraceが欠けたため、観測entryだけで全射撃を通すよう修正。通常entryは元の最適化を保持した。チャージfixtureの待機0.200秒はnative静的正規化0.215秒と不整合だったため、静的正本へ修正し、起動前の一致gateを追加。元9件のnative指紋は全保持し、失敗packet/raw/claimは保存している。

共通readerのrefactor後も、従来query9入力の全readback byteを新Metal実行と照合して完全一致。新しいv2 goldenは独立fresh監査から作成し、旧goldenを上書きしない。既存full106のCUDA/MSLは厳密な正規化後の生成ハッシュが元基準と一致（生成のみ）。変更sourceのfull106再seal・CUDA実機検証は未完了。

この証拠は元modifier定義を保持した専用の5人編成fixtureであり、Heavyarms全25効果の実行認定ではない。Lock Onの順位、既ロック集合、実敵pool/充填イベント/発射snapshot/全投射物consumerへの接続は引き続き必要。266profile/245入力変換/21失敗/20分類と全キャラ認定0、UI CPUは維持する。証跡はresearch/target-count-query-evidence/metal-physical-shots-v1.json。


## 実敵プールへ接続した世代付きmembership（明示モデル）

`named-generation-locks`は同じSlangの状態処理をCUDA/Metalへ生成し、既存WorldSchedule/actor poolの生存・世代と、既存の名前付き上限readerへ接続する。対象の生死や取得済み集合をCPUで事前計算して入力しない。既存のimmutable actor setを明示providerとして受け取り、その順で生存・同世代・未取得の先頭を1体取得する。これはproviderの既定BODY/PART/ADD順・ADD出生順を最近傍の仕様に採用することを意味しない。照準距離の順位付けは未接続である。

状態は型付きidentityと世代を保持し、死亡/世代更新時に除外、上限低下時には既存ロックを勝手に縮めず追加だけを停止する。取得順snapshotは既存set出力の未使用slotを明示予約して保存する。snapshot宛先の重複と既存set writerとの競合はGPU起動時に拒否する。通常攻撃/ハイドに相当する明示解除を受け、解除前snapshotを保持する。これらの寿命規則は参照モデルの契約で、ゲーム実機の認定ではない。

M5 Metalで10正例/6raw負例が成功し、別fresh GPU禁止childで全16入力を独立監査してgoldenを作成した。全pool・landing receipt・敵状態・候補setを従来native observerと比較し、ロック取得receiptと全520word snapshotも照合する。15体取得後の15→5、caster/name分離、死亡、3世代目への再出現と古い候補の拒否、取得前spawn待ち、明示解除、BODY/PART/ADD同一idの区別、128体の候補表を含む。128体の候補表では24回の取得を検査し、128ロックを取得したと主張しない。既存actor poolの128容量を保持し、typed projectile/shield領域はこのentryの対象外。

このfixtureのmodifierは元index20を有限時間へ派生したもの。元の2射撃定義を保つ物理証明は別suiteのままで、このstate entryとの合成、充填中0.2秒event、物理通常攻撃/ハイドeventの自動接続、発射前snapshot、sequential deliveryと元全25効果は未完了。

初回は空statへのloweringでkindが4となるのを0へ戻す処理がなく、GPU admissionが全正例を拒否した。新入力で既存query adapterと同じkind/stat/name/recipient key変換を適用し、GPU前の回帰検査を追加した。失敗captureは保持。Slangソースは初回と同一で、修正版はpipeline cache必須hit、GPU 0.019384125秒。実GPU計2回/同claim retry0。CUDAは同一ソースの生成までで実機未検証。Windows追加依頼0。

CLIは通常の`package --suite named-generation-locks`→固定packetから`run`→保存結果の`seal`を使う。旧entryに対する変更はopt-in macro内だけとし、sourceの逆投影は新しい完全一致ledgerで検査する。既存のgenerated-code normalizerや旧goldenを緩めない。`model-check`はこの部分実証を別フィールドへ記録し、従来の未対応分類/公開admission/全キャラ認定0を維持する。証跡は`research/target-count-query-evidence/metal-generation-locks-v1.json`。


## 充填周期・実射撃・元2射撃上限を合成（明示モデル）

`physical-generation-locks`は既存の周期activationと`during_charge`判定から共通membership取得を呼ぶ。充填開始からの独自タイマーや、CPUが作った発動/射撃scheduleは入力しない。元index20の定義を保った2射撃上限を同じresident battleで読み、実物理shotの既存消費処理へ接続した。通常攻撃の通知でmembershipを自動解除し、その物理着弾より前に取得した集合をimmutable snapshotへ保存する。

元index0はname/timing/condition/max_stackを保持する一方、statを空にし、targetをselfへ変更した**周期観測用projection**である。元の最近傍enemy carrierや全25効果を実装した証拠ではない。候補は各周期に実GPU上でBODY/ADDの生存・世代から新しくcaptureするが、順位は既存の明示set順だけであり距離規則にはしていない。通常攻撃解除は実eventに接続済み。実ハイドeventへの自動接続とsequential deliveryは未完了。

Metalで3正例/4raw負例が全成功し、別fresh GPU禁止childで全7入力を独立sealした。0.45秒充填で複数ロック→実射撃解除→次充填の再取得、元2射撃効果の15→15→5、0.1秒充填で周期gridをまたがず空集合で撃つ場合、取得後の実HP死亡が発射snapshotから除外される場合を検査した。通常戦闘全出力・skill trace・全物理上限消費traceを保持し、全周期receipt/時刻と全発射snapshotを比較する。snapshotの位置はGPUではfull_charge callback後・物理着弾前であり、このfixtureには敵状態を変えるfull_charge効果はない。元全25効果とのイベント順の検証は別途必要。

既存のactor/set/receipt/query領域を明示利用し、strideを増やさない。候補128、周期記録63、発射snapshot31の各上限で停止し、省略して成功にはしない。既存query traceの100物理shot上限も保持する。原本入力の通常set操作と診断queryの競合はGPU admissionで拒否する。GPU0.041235208秒、cold pipeline8.204335秒、実dispatch1/retry0。Windows追加要求0、CUDA実機は未確認。証跡は`research/target-count-query-evidence/metal-physical-locks-v1.json`。

共通coreを取得/snapshot関数へ抽出した従来`named-generation-locks`も16入力を新Metal実行・独立sealし、元input5,901,316byte/readback16,252,928byteを全保持した。v2 goldenを新規作成し、旧goldenと旧captureは保存。共通smoke66group/641検査（skip1）、全266profile/issue/20順位保持、default full106のCUDA/MSL厳密正規化hash保持（生成のみ）も成功。個別Metal計2dispatchで同claim再試行0。全キャラ認定0/20分類/UI CPUは維持する。


## スキルとの共有setを保つ専用arenaとfull_charge配送

最新版`physical-generation-locks`は出力末尾に専用arenaを追加し、出力806,912word/入力104,400wordとした。従来786,432wordの位置は保持する。候補520word、周期63×16word、発射31×520wordを既存のactor query/receipt/setから分離し、全32個の生存スキル対象set容量を維持する。従来版のsnapshotは所有権0のsetを借りていたため、スキルallocatorと併用する前に分離が必要だった。候補全word・全snapshot・空き領域/末尾paddingまで比較する。Python/Slang/Swiftの幅を揃え、別entryがこの幅を使う場合や、旧幅のまま呼ぶ場合は起動前に拒否する。

3つのfull_chargeスキル合成を追加し、native6/raw拒否4の全10入力が新Metalとfresh独立sealに成功。全敵へのキューダメージによる死亡、bossだけへのダメージ、死亡後の再召喚を含む。このダメージは通知直後には配送されず、snapshotの世代を保持した後にキューから着弾する。旧世代のsnapshotを新世代やBODYへ読み替えないことを検査した。照準距離・実ハイド・順番攻撃・全25効果認定の未完了は変わらない。

初版で再召喚ケースの最終graph_state[0][6]だけが0対1となった。native最終観測はfinishによるADD退場後のuntil_cleared述語を導出していたため、このarena entryだけ、GPUの実pool退場後に同じ最終述語を導出する。終了eventや死亡通知は追加せず、ログ/ダメージ/他状態の比較も維持する。旧defaultの終了graph観測へ一般化する移行・再認定は残件。失敗packet/rawを保持し、修正版の全10入力を新たにsealした。

旧7入力は全input byteが同じで、旧出力の全wordを明示された移設先か従来prefixへ対応付けて照合した。候補setの解放flag0だけは、独立scratchのflag1へ明示変更した。raw hashの完全一致とは主張しない。`physical-lock-arena-relocation-v1.json`に全領域の対応を記録。従来external-command core16入力は全input/readback byteを保持し、新v3 goldenへ切り替えた。旧golden/rawは保存する。

共通smokeの最初の失敗は新wire幅の厳密source監査への登録漏れであり、wire/Swift/backend/schemaの前後全文を新しい完全一致ledgerに追加して修正した。normalizerを変更したり、依存hashの確認を省略したりしていない。旧default106のCUDA/MSL生成は既存の厳密正規化hashと一致（生成のみ）。今回の実GPUはarena2回（初版失敗含む）/external core2回、同claim retry0。最後のexternal coreは生成Metalの全byte一致を確認してpipeline必須hitで実行した。Windows追加要求0。


## 実ハイド通知のCPU契約（2026-10-27）

`reference --suite physical-lock-cover-native --out NEW.json` を共通CLIへ追加。実CharStateの明示遮蔽制御から発生する `event:cover` を観測し、充填取消後に同casterのmembershipを解除する。充填中、別caster、cover_disabled、取得前の空集合、duration未指定のリロード終了待ちの5ケース。通常攻撃前snapshotとclear、遮蔽後の再取得も比較する。独自のタイマーやCPUで作った通知列をGPUへ渡さない。

physical observerは実通知だけを観測し、別の非観測native実行と全battle/trace/inputの一致を毎回検査する。外側の通知patchではこの透明性確認用の2回目も数えてしまうため、通知callbackは元observerの1回目のscope内に限定する。空集合の遮蔽もrevisionを1進める明示契約であり、ゲーム実測の認定ではない。

現在の104400入力wordのphysical入口は、既存の手動遮蔽制御を持たず5ケース全てをGPU前に拒否する。このCPU契約をMetal/CUDA成功へ昇格させない。次の接続では既存 `enterManualCover` → event31＋cover tagを使い、lock casterとtagの一致時にだけ解除する必要がある。手動状態の919744word領域を現physical専用arenaへ単純に足さず、共通arena監査で他の制御・履歴との非重複を先に確認する。距離規則、sequential delivery、元全25効果は引き続き未完了。


## 実ハイドと充填membershipのGPU合成（2026-10-27）

sealed `physical-lock-cover` は23入力（native11／raw拒否12）をM5 Metalとfresh独立監査で照合した。旧10入力の全入力payloadと全32,276,480byteのGPU出力を保持し、新5ケースは既存の手動遮蔽producerと同じweapon/reload/event実行器を使う。`event31`とcover tagの一致、さらにlock casterの一致で解除する。遮蔽禁止は通知を発生させず、別casterの遮蔽はロックを変えない。空集合の遮蔽もrevisionを進め、充填取消後・遮蔽後の再取得・発射前snapshotと通常攻撃での解除をnativeと照合する。

既存 `coordinate_manual_control_runtime.slang` の計算を共用し、手動状態80wordだけをlock snapshotの直後804096へ置く。入力104400／出力806912wordは不変、actor set32個の容量を保持。手動状態80wordと残りpadding、全戦闘/skill trace/射撃/二射撃quota/候補bufferを比較する。observerも既存 `world_coordinate_manual_native.capture`、比較器も `compare_manual` を再利用する。独立nativeの透明性確認用2回目へprofileや通知callbackを漏らさない。

GPU .046597秒、cold pipeline10.418701秒、独立監査8.449739秒。共通CPU642（Win1skip）・専用57検査が成功。共有source更新後の旧物理10／external16も新Metalとfresh sealを行い、全shader/input/output byteを保持。旧2入口は生成byteの同一確認後にpipeline必須cache hitを使用し、pipeline時間は各約.002秒。旧goldenを保持し、新v3/v4へCLIを更新する。default106の厳密CUDA/MSL生成hashも不変（生成のみ、CUDA再認定ではない）。全inventory fieldは旧arena版と一致、245変換/21失敗/20分類/全キャラ0/UI CPUを保持する。

証拠は `research/target-count-query-evidence/metal-physical-lock-cover-v1.json` と `physical-lock-cover-legacy-retention-v1.json`。今回はMetal3回、同claim retry0、Windows追加依頼0。距離選択・sequential delivery・元全25効果・現sourceのCUDA実機認定は未完了。


## 発射snapshotからヒット番号への共通選択部品（2026-10-27）

実CPU通知の追加観測では、`on_attack` → `full_charge_fire` → 元index8のnamed hit通知2回 → weapon hit通知、となった。元index4/8/9を変更せず追加したfixtureで、順番攻撃のhit予算は2、元index9の消費後は0になる。発射前snapshotは2対象を保持する。したがって、キュー生成時に現在membershipを読み直すことも、着弾時に消費後のgaugeからhit予算を読み直すこともできない。観測自体はターゲット選択policyを注入せず、全25効果の成立を認定しない。

`lock-delivery-policy` はsnapshotのslotとhit番号の対応だけを検証する共通整数部品。明示した `cycle-frozen-slot-v1` では `(hit-1) % snapshot_count` を使い、選択済みslotの型・identity・generationを保持する。current viewが欠落／死亡／別世代なら専用statusを返し、生きた別slotへ圧縮・再対象化しない。空集合は割り算前に分岐する。これは工学上の明示policyであり、ゲームの途中死亡・挑発・再対象化の実測規則ではない。`ready`も着弾・ダメージ成功ではなく、同世代の生存が確認できたことだけを表す。

同じSlang関数をCUDA/Metalへ生成し、Metal63入力（共通CPU policy46／raw拒否17）と別fresh GPU禁止監査で一致。128対象、256hit、全6kind、型別同identity、全5status、整数境界、重複identity、予約領域を検査。Python APIは可変listをsnapshotとして受け取らない。既存cover23/physical10/external16のGPU source閉包は全byte不変なので再コンパイル・再実行しない。

このprobeは実着弾キューやHP・カウンターを実行しない。次はpacketにsnapshot番号と発射時hit予算を保持し、既存 `landWorldSkillReceipt` のactor set／land処理へ接続する必要がある。元の32 actor setを借りてsnapshotを上書きせず、既存receipt codecの予約word／所有権を先に監査する。公開admission・全キャラ認定0・UI CPU・距離未確定を保持する。証跡は `target-count-query-evidence/metal-lock-delivery-policy-v1.json` と `lock-delivery-native-order-v1.json`。
