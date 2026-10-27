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
