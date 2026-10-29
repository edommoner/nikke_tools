# Lock Onの次の実装契約

## 公開資料の品質を含めた最終判断（2026-10-29）

実機環境を待たず、日英韓の検索と本文取得で判断した。採用するのは、公式番組を出所とする[ファミ通のスキル記述](https://www.famitsu.com/article/202512/62211)の未ロック敵・照準線基準・0.2秒周期・5対象/+10対象・攻撃/ハイド解除。距離の数値式を推定して実機仕様へ昇格させる根拠は今回の調査では得られなかった。中心/外形、画面投影/3D照準線距離、同距離順、PART資格は未確定を維持する。

転載間の差は仕様分岐としない。[Game8](https://game8.jp/nikke/753724)の取得本文は未ロック条件が欠け、照準線の句が重複し、対象数の単位も弾数になっている。[GameWith](https://gamewith.jp/nikke/article/show/537776)の取得本文は照準線条件を省略している。多数決でそれらを混ぜず、発表由来の全文を優先する。[Prydwen](https://www.prydwen.gg/nikke/characters/snow-white-heavy-arms)の単一対象への複数順番攻撃は、同一handleへの重複ロックとは区別する。映像取得失敗は視認済みとせず、NIKKE.GGは検索索引と403の制約を保持する。

この調査はここで区切る。同じスキル文の再検索では数値式は確定しないため、次の調査条件を「距離候補を識別する制御実験か明示数値仕様の発見」とする。ユーザーの実機環境提供待ちを再開せず、独立した未対応GPU機能を進める。既存provider順・計算・golden・受付は変更しない。出所別の制約は `research/target-count-query-evidence/heavyarms-online-source-quality-20261029.json`。今回のGPU実行/Windows依頼0。

## 公開情報の追加照合：距離式の決定根拠は増えていない

2026-10-29再確認：ファミ通の全文とPrydwen本文を取得し、取得周期・上限・解除・取得順循環を再確認。NIKKE.GGは検索索引のみで直接取得403。距離式を区別する新たな制御実験は得られていない。実機環境の回答待ちは不要で、未確定規則を仮定せず他のGPU対応を継続する。出所と取得制約は `research/target-count-query-evidence/heavyarms-online-recheck-20261029.json`。

ユーザーの「ネット上の情報をかき集めて判断」の指定に従い、上記調査を再照合した。[公式告知画像の転載と筆者の実使用観察](https://ore-game.com/nikke/post/snow-white-heavy-arms/)（更新2026-01-30）は、照準線を基準にした未ロック敵の選択を掲載している。ただし筆者の単体相手への「重複してロックオン」という観察は、単一ロックへの複数順番攻撃と区別する計測を伴わず、distinct handleの重複許可を導入する根拠にはしない。中心対外形・投影距離対3D距離・同距離順を区別する実験も確認できなかった。

今回も公式番組/予告動画の直接取得はcache miss、NIKKE.GG本記事は403だった。動画を視認したとは扱わない。既存の公開記述に基づく取得規則と、未確定の数値距離式を分離する判断を維持する。実機環境の回答待ちは不要であり、独立した未対応項目の開発を止めない。今回の計算コード変更・GPU実行・Windows依頼は0。

## 2026-10-28 追加判断：振替は発射前、発射後の死亡は失発という公開記述

[NIKKE.GGの著者記事](https://nikke.gg/snow-white-heavy-arms-analysis-should-you-pull/)（lzzy、掲載上の更新2026-01-08）の検索索引本文で、順番攻撃の**発射前**に予定対象が死亡した場合は残りのロック対象へ振替、**発射後から着弾前**に死亡した場合は失発するという区別を確認した。直接取得は403、画像/動画は今回未確認で、制御実験としての認定ではない。同一記事の再取得は独立した根拠を増やさない。[Prydwen](https://www.prydwen.gg/nikke/characters/snow-white-heavy-arms)の取得順循環・固有の挑発例外は本文で再確認した。

設計上の判断は、発射時の振替policyと着弾時の既存世代/生存検査を分けること。発射済みpacketを着弾時に別敵へ自動振替する根拠にはしない。振替先、全滅、同frame順、PART資格、中心/外形/奥行き距離は未確定であり、既存の明示dropモデルやgoldenを変更しない。実機待ちを解消するための公開情報上の判断であり、全25効果/公開GPU受付へ昇格しない。出所・取得制約は `research/target-count-query-evidence/heavyarms-online-launch-boundary-20261028.json`。この調査によるGPU/Windows追加実行0。

## 2026-10-28 ネット調査による選択規則の判断

実機環境を待たず公開情報で判断する指定に従い、日本語・英語・韓国語の公開記述を照合した。スキル記述で支持されるのは、照準を基準に未ロック敵を充填中0.2秒ごとに選ぶこと、通常5対象、バーストで10対象追加、通常攻撃/ハイドで解除すること。[公式発表](https://press.levelinfinite.com/en-US/GODDESS-OF-VICTORY-NIKKE-REVEALS-MAJOR-NEW-YEAR-UPDATE-FEATURING-LEGEN)はキャラ追加の一次資料だが距離式は説明していない。[公式番組を出所とするスキル全文](https://www.famitsu.com/article/202512/62211)は取得できたが、番組動画自体の今回の取得は失敗したため、映像を確認したとは扱わない。

[Prydwen](https://www.prydwen.gg/nikke/characters/snow-white-heavy-arms)には取得順循環と挑発で順番が変わらないというキャラ固有の説明がある。[NIKKE.GG](https://nikke.gg/snow-white-heavy-arms-analysis-should-you-pull/)の死亡時振替は検索索引で読めるが、直接取得は403で振替先の決定法は不明。[韓国プレイヤーの実使用分析](https://gall.dcinside.com/mgallery/board/view/?id=gov&no=4485865)にも照準基準と対象数表示、単一ロックへ攻撃を集中させる説明がある。ただしリンク画像は今回未確認であり、中心/外形/奥行き/同距離を区別する実験とは扱わない。[記者のゲームプレイ分析](https://trees.gamemeca.com/view.php?gid=1769754)からも距離式は確定できない。

判断：照準基準の取得規則は設計根拠として使う。数値距離式、同距離順、PART候補資格、死亡時の決定的な振替先は未確定のまま保持する。現行の明示provider順や死亡policyを黙って変更せず、既存typed aimの奥行き/birth/slot順を最近傍としない。実機環境の提供待ちで他のGPU対応を止めない。新しい制御実験か公式数値仕様が得られた時に再調査し、同じスキル文章の転載を何度も探索する作業は重ねない。計算変更/GPU実行/Windows依頼は0。出所・取得制約・判断は `research/target-count-query-evidence/heavyarms-online-selection-decision-20261028.json`。

## 2026-10-28 実パーツ・負傷・回復条件を同じ実行器で検証

`original-lock-health-parts`は7つの30秒実編成とraw拒否4件。元25定義/実編成91定義を削らず、永続PART2個/破壊可能PART2個、通常編成の負傷とCPR、メアリーを先に配置した実編成のburst回復、メアリー低HP、パーツ＋負傷、パーツ＋負傷＋遅延ADDを実行する。編成変更は元bodyの変更として保存し、元input identityで効果/owner順/実武器/育成/configを検査する。単なるhas_parts=Trueではなく、元base flagはFalseで実live nodeに支配させる。PART上の実extra_hits/extra_dealt、破壊通知、全戦闘状態を照合する。

HP条件の独立した受動監査は、元の防御効果が高HP時だけ発火し、低HP時は発火せず、5秒後の全5人の実被ダメージが変わることを確認した。観測を加えた全native指紋は固定基準と同一。このCPU監査は初版package718a776a…に属するが、修正版66bef718…の全golden/input/native期待とGPU sourceが初版と完全一致することを別途検査しており、出所を付替えていない。

新entryは`PORTABLE_HEAL_SHARE_DIAGNOSTIC`を定義して既存original composition entryをincludeするだけ。回復・条件判定・part着弾・敵攻撃の計算/時計/通知器は複製していない。既存diagnosticの204行（12/12/12/42/42/42/42）を、元heal_sourceを保持して既存native_records/gpu_recordsで全比較した。観測専用のHP/adjacent_hp通知を既存projectionが除く範囲は明示して保持し、それを全通知履歴の証明へ拡大しない。Runtime140008byte/input109536/output1310720word、512行の既存healing bank、全fraction/team/lock/typed history容量は不変。

固定338d2280/package66bef718…のM5実GPU1回が全11入力成功、別fresh GPU禁止sealも成功（136.12秒）。95unit/CPU全11、GPU2.21711秒/PSO9.61304秒、必須generation hit/Slang0。初版はentry未登録でGPU計算前に停止し、失敗とclaimを保持したまま別packageへ修正。ガードを広く解除せず、明示entry/完全wireだけを登録しexact inverseを追加した。さらにCLIのpackage/run開始時にも同じentry-wire検査を行い、再発時のCPU全件照合を避ける。関連79テスト成功。

既存GPU405ファイルはf51bbe9eから全byte不変。初版/修正版のCUDA/MSL原byteも全同一で、hostの登録修正による余計なcompiler呼出しは0。source保持は旧suiteのcurrent-source GPU再認定ではなく、既存の古い証明書を昇格させない。`original-lock-health-parts-cache-only`は同じ計算/入力/golden/比較器をCUBIN/O1必須とresident paired generation必須に接続する。現CUDA実機/実CUBIN hitは未確認、Windows新依頼0。

これでPARTへのLock On規則や距離/同距離順、死亡時振替、全条件分岐、全キャラを認定していない。公開GPU admission/UIは従来通り。証跡は `target-count-query-evidence/metal-original-health-parts-v2.json`、`original-mary-hp-condition-v1.json`、`original-health-parts-legacy-source-retention-v1.json`、`original-health-parts-v1-predevice-failure.json`。

## 2026-10-28 元ハイド解除と15対象バーストを実編成へ接続

`original-lock-controls` は旧8入力を保持した17入力（native9/raw拒否8）の共通CUDA/Metal suite。実編成/実武器/全91定義（Heavyarms元25定義を含む）はそのまま使う。本人の0秒/0.35秒ハイド、本体のみ/3ADD、別ownerのハイドをliteral `control.sequence` で与え、nativeの本来の入力identity検査後とGPUの静的packingへ同じ宣言を適用する。育成profileへのcontrol混入を拒否する既存境界は変更しない。`portable_declared_manual_sequences.apply` は既存owner・非空8件以内・有限で順序付きの時刻/duration・明示coverのみを受け付け、既存sequenceの上書きを拒否する。canonical CPU4ファイルとupstreamは未変更。

新しいハイド時計/解除処理は追加せず、既存manual normalize/pack、共通control executor、元row2 `remove_named_buff`、actor carrier、lock generation clear、既存manual比較を使う。原入力・effect/owner順・武器の検査を済ませてから操作overlayを適用したことをnative identityに明示する。CPU受動観測では0.35秒に元row2が発火し、実敵`__enemy__`のmarkerが消え、state_end通知後に取得が再開する。観測on/offのmutationと固定native全指紋は同一。呼出しcoverageは従来24entry＋今回row2で全25entryに達したが、全分岐の認定ではない。

30秒16ADDでは実元burstにより15個の異なるhandleを2射撃でsnapshotし、その後5へ戻ることを必須契約にした。単なるcapacity変数の値ではなく、全pulse/shot/packet/typed/battle/通知履歴と最終状態を比較する。生存対象のみであり、距離式と死亡時再配送を仮定していない。PART/負傷・回復の分岐、空間順位、死亡時振替、他キャラ/variant、全キャラ/公開受付は残る。

固定1754ba71/package2b01f589…のM5実GPU1回が全17入力一致、別fresh GPU禁止childのsealも成功。GPU2.59235秒・PSO0.00227秒、generation/PSO必須hit、Slang0、Runtime140008byte・input109536/output1310720word不変。既存CLI `readback-retain` で旧8caseのinput/native/outputと全41943040byteを保持した。生成CUDA/MSLは正規化前の全byteも同一であり、既存CUBIN再利用に適するsourceであるが、現CUDA実機/実cache hitは未確認。

v1はCPU群の実測から上限を調整するためGPU未実行。v2は旧比較goldenの梱包漏れをCPU gateで検出しGPU0/claim0、成功へ書換えない。修正は既存AUDIT_FILESにも依存を登録し、同じ漏れをnative準備前に止める。関連16controller検査成功。CPU群のfixture全再生成という重複を除いた後も同じ4テストは成功し38.15秒（以前85.91秒）。比較や旧入力の保持検査を削って高速化していない。GPUの再実行0。

通常は `package --suite original-lock-controls --out NEW.zip` → `unpack` → 固定packetの `run` を使う。`original-lock-controls-cache-only` は同じscript/source/input/golden/比較器を使うCUBIN/O1必須・paired generation必須の経路。cache不在なら既存compile-planで別途予算を検証し、fallback compileは行わない。Windowsの新実行依頼0、既存status取得はhost unavailable、終端判定や再送はしない。証跡は `target-count-query-evidence/metal-original-lock-controls-v3.json`、`original-lock-controls-cli-retention-v1.json`、`original-cover-source-activation-v1.json`。

## 2026-10-27 配送dispositionを保持した発射体合成をMetalでseal

共通CLI `lock-projectile-composition` は12入力（native7／拒否5）をM5 Metal＋別fresh GPU禁止監査でsealした。元の5条件に、名前付き完了通知の子攻撃とtypedカウンター完了の子攻撃を追加。履歴行の削除や比較項目の除外で前回差分を通していない。元5件のnative skill trace全行は、前回の失敗診断に保存した値と完全一致する。

実際のtyped配送は従来のexecutorで同frameに処理する。その後nativeが作る本体向け仮packetに対応する**監査receipt**を、GPUでも既存LandingReceipt/2048slotキューへenqueueし、既存drainの次frame時刻で記録する。数量はtyped処理が既に凍結したbinary64をcopyし、ダメージを再計算しない。履歴の従来recipients列はnative dispatcher入口の要求（BODY）として保持し、別の `receipt_fates` が `suppressed_native_body` / `ordinary_world_route` とActor副作用の可否を明示する。抑止receiptはlog後に戻り、land/counter/healへ入らない。実typedのHP・counter・通知と、全battle状態も従来通り比較する。

enqueueはtyped target-counterの子処理後、通常のnamed-hit子処理前に行う。既存 `pushSkillHit` 呼出しの局所wrapperだけを合成entryへ配線し、nativeのappend順と一致させる。子効果を削除したり、二つ目の時計を作ったりしない。名前付き完了を扱う既存PORTABLE_PROJECTILE_CHAINと、その既存前提PORTABLE_FULL_BURST_LANDINGを有効化した。新しい完了通知handlerは追加していない。

144wordのfate bankを1069056..1069200へ追加（header16＋既存skill trace128行のflag128）。全flag・未使用行・header予約word・残りtailを照合してから、旧lock arenaの厳密projectorへ渡す。旧領域の全wordと32 actor sets/128 typed targets/2048queue/31shot snapshot/38link traceは保持。input109536/output1310720、resident Runtime140008byteは不変。traceMode1を要求し、診断を省いたまま成功にしない。現scopeはこれら7条件であり、終了frameで未drainの監査receiptや2048同時queue、全25定義を認定したものではない。

最初の新packet0f5e2a40（code8d3a9b33）は、従来5条件とcounter-childは全比較成功したが、named-childが既存完了flag未接続でadmission64。失敗を保持。8e43b374では前提のfull-burst queryが未接続でCPU生成エラーとなりGPU/claim0。修正3c21e08eの固定packet8422e8a3は全12成功、GPU0.113912秒、PSO9.358276秒、独立監査12.005718秒。今回実GPU2（失敗1＋成功1）、同claim retry0。前回の5e895206の失敗も全artifact hashを再確認して保持し、成功へ付替えない。

v3 package作成は `--native-baseline-package` で、CPU全payload/inputの一致を監査したv1の期待指紋だけを再利用。変更はGPU entryと既存inverse ledgerのGPU current部だけと検証され、package時native再計算0。run内部では全CPU/native gateをfresh実行し、sealもfresh独立監査。保存GPU出力の再利用ではない。

今回は旧live9/packet8/cover23/physical10/external16と本体106の全GPU source閉包が前回と一致。旧生成/旧GPUの再実行0で既存goldenを保持する。変更は新合成entryとその専用実装へ隔離した。CPU typed observerの追加dataは観測のみで、従来元発射体8件の全native指紋も保持する。

`lock-projectile-cache-only` は同じ12入力・同じgolden・同じ共通計算のCUBIN/O1専用入口。既存の保存CUDA source/required CUBIN hit/NVRTC禁止に加えて、`--require-generation-cache --generation-cache ABS` を実行前から要求する。監査でもpaired generation hit/Slang呼出し0を要求し、CUBINだけhitしてSlangを再生成するfallbackを認めない。従来standaloneのcache profileは変更しない。現CUDA実機は未検証で、Windows新実行依頼0（既存continuationのstatus取得を1回試したがhost unavailable、再送なし）。

証跡は `target-count-query-evidence/metal-packet-fates-v3.json` / `packet-fates-v1-diagnostic.json` / `packet-fates-failure-and-default-retention-v1.json`。全25定義、元index0の敵carrier/距離順位、死亡振替、公開GPU/全キャラ認定は引き続き未完了。

追加の既存typed battleテスト21件は17成功、保存fixtureのsource guard4件が失敗した。変更前0dc09543のコードを独立領域へ展開して同じ4guardを実行し、全件同じ不一致を再現した。guardや旧fixtureを弱めて通していない。今回の新12入力はfresh capture/native/独立監査による認定で、旧履歴全体の再認定ではない。旧source guardの更新/再実証は残件として `target-count-query-evidence/preexisting-typed-source-guards-v1.json` に記録する。

## 2026-10-27 発射体との合成と、残っている配送履歴の差分

`lock-projectile-composition`は既存のtyped発射体executorとlive lock executorを同じWorldSchedule/DFS stackへ配線する開発入口。元index24のall_projectiles定義を変更せず追加した5ケース（生存3体、破壊3体、burst後に出現する空対象、128体、ハイド）と不正typed wire4件を使う。元index4/8/9/20も保持するが、index0は周期self projectionのままで、全25定義の認定ではない。新しいダメージ計算・第二の戦闘時計・CPU配送表を導入しない。

従来のtyped領域786432..1048576を全保持し、lock/manual/queue-link領域の全20480wordを1048576..1069056へ移す。32 live actor sets、128 typed targets、31 lock snapshots、2048 queue slots、38件の診断上限を保持する。既存登録の出力幅1310720、入力109536を用い、追加tailの全zero検査と、旧lock全wordの一対一移設検査を行う。旧entryの既定offsetは0で生成code不変。以後の拡張本体は新entryに留め、旧entryのsource閉包に追加includeしない。

最初のCPU生成はresident reflectionがGenerationLocksの入れ子structを拒否して停止した（GPU/claim0）。既存の数値leaf検証を入れ子にも適用し、structの反射size/alignment、親子範囲、絶対offset、末尾、重複name、深さ/leaf上限を確認するよう修正。scalar/arrayだけの旧plan形式は変えない。CUDA/Metalの全plan一致、sizeof/alignof static_assert、48byteのCUDA bindingを維持。実反射はRuntime140008byte、locks1044byte、全7leafの絶対配置を両backendで照合した。生成cacheはこの検証器のSHAを既にkeyに含むため、旧keyへ付替えない。関連reflection5検査（入れ子負例8種）とgeneration-cache13検査が成功。

code76b931c6、固定packet5e895206の9入力をM5 Metalで1回実行した。5正例のstatus0、不正4件は64。全5件のbattle/HP/状態とtyped state/全receiptはnativeと一致。ただしtyped対象が実在する4件のskill traceに差があり、全比較は失敗、sealなし。空対象1件のみ全比較成功であり、それを全合成成功へ読み替えない。

原因の切り分け：native typed拡張は通常handlerのscalar/通知を使うため本体向けHitEventを生成し、実際の発射体への配送後、次frameの`_land`に挿入したskip guardで本体着弾を抑止する。既存`world_skill_native.inspect`はそのwrapper呼出しをBODY recipientのskill traceとして記録する。一方、GPUは同frameの実typed receiptだけを記録し、本体仮packetを生成しない。battle/typed出力が一致していても、この履歴差分は残す。比較器から行を除く、失敗captureを成功に変更する、同claimを再送することは行わない。次に、実配送と抑止された仮packetのdispositionを明示して両側の履歴契約を揃える必要がある。原正本の計算や厳密normalizerは変更しない。

失敗raw/claim/artifactsはpersistent proofsのlock-projectile-composition-v1-metalに保持。全9件のCPU-only再診断は`target-count-query-evidence/lock-projectile-composition-v1-failure-diagnostic.json`。新合成はdevelopment_onlyのまま、GPU対応数/全25/全キャラ認定は追加しない。Windowsの新実行依頼は0。

## 2026-10-27 発射snapshotから既存着弾経路への接続

共通CLI `live-lock-delivery` は9入力（明示モデル4正例、未確定死亡policy/不正wireの拒否5）をM5 Metalで1回実行し、別fresh GPU禁止childの全出力/native比較でsealした。`require-live-frozen-slot-v1`は発射時snapshotの取得順とhit番号から生存・同世代の対象へ配送する。空snapshotは空集合とし、BODYへfallbackしない。死亡・欠落・世代違いを検出した場合はerror64で停止する。これは未知の振替を実装したことにも、死亡時dropを採用したことにもならない。

新しい処理はtransient actor setへ宛先を1つcaptureするだけで、`landWorldSkillReceipt` → `land` → `counterPhysicalPacket` → healという既存処理を通る。新しいダメージ計算、CPU計算済み配送表、HP/counter/healの複製はない。snapshot専用arena、live actor set32、queue2048、input104400/output806912、診断trace38は不変。今回の実配送fixtureはBODY/ADDで、全actor種別や2048同時queueの認定ではない。

充填2対象のBODY→ADD、4hit/3対象の循環、通常攻撃解除後のsnapshot保持、ハイド、空snapshot、実ADDダメージによるskill counter完了と吸血回復を照合した。配送前死亡→再出現ケースは拒否正例。元index4/8/9/20を保持するpartial fixtureで、index0は周期self projectionのまま。全25定義・距離選択・ゲーム準拠の再対象化は未完了。明示selectorのため正本の未実装recipientを拡張しており、canonical battle equivalenceとは主張しない。

CPU観測器のpatch scopeをcontext managerへ抽出した。元の受動観測はobserver無しのfresh正本との全battle/trace/input一致を保持し、従来packet4件の全native SHAも保持する。新規約はfreshな同規約の再実行で全battle/trace/inputを比較し、追加診断の有無による差がないことを検査する。比較対象をcanonicalと黙って読み替えない。

`WORLD_PACKET_CAPTURE`を一度だけ共有着弾境界へ追加し、既定は完全な従来fallback。拡張本体は新entryからだけincludeし、将来その本体を変更する度に全legacy source閉包へ入ることを避ける。今回の共有hookによるsource変更は新exact inverse ledgerで監査。従来packet8/cover23/physical10/external16は生成CUDA/MSLの既存厳密hashと全input/native指紋を先に確認し、required pipeline hitで各1回Metal＋fresh独立sealした。全input/readback byteを保持。新goldenは順にv2/v3/v5/v6、旧版は保存。本体106の厳密生成hashも保持（生成のみ、現在sourceのCUDA認定へ付替えない）。

実装code4c0c114c、packet15aa4c45。新consumerのGPU時間0.057052秒、初回archive作成11.105610秒、独立監査6.390641秒。追加GPUは新1＋従来4、同claim retry0。最初の独立生成比較スクリプトでnormalizerの戻り値を誤ってhashしたCPU診断失敗2件は記録し、既存normalizer自体は変更していない。実計算失敗ではない。

`live-lock-delivery-cache-only` は同じsource/入力/比較器/goldenを既存のCUBIN必須・O1・required cache・保存CUDA source検査・NVRTC禁止profileへ接続した入口。新しいCUDA実機成功ではない。Windowsは旧continuationのstatusだけを1回確認したがhost unavailable、再送/再実行は行っていない。証拠は `target-count-query-evidence/metal-live-lock-delivery-v1.json` と `live-lock-delivery-legacy-retention-v1.json`。

## 2026-10-27 追加検索：配送前死亡の記述と実装判断

実機環境を待たず公開情報で判断するという指定に従い、英日韓の追加検索を行った。今回の判断は次の通り。資料の記述を開発指示や独立した戦闘oracleとして実行しない。

| 項目 | 公開情報からの判断 | 実装での扱い |
| --- | --- | --- |
| 取得条件・通常上限・解除 | 日英スキル表で、充填中0.2秒、照準に近い未ロック対象、通常5体、通常攻撃/ハイド解除が一致。 | 既存の状態・寿命契約の根拠にする。 |
| 通常の配送順 | Prydwen個別解説は取得順で循環すると明記。 | 明示モデルの有力な根拠。ただし実測認定とは分ける。 |
| 挑発 | Prydwenは**他の順番攻撃と異なり**このキャラでは挑発が取得順を変えないと明記。一般説明と直ちに矛盾とは判定しない。 | 一般の挑発処理を無条件に適用しない。キャラ固有例外の公開記述として保持。 |
| 配送前の対象死亡 | NIKKE.GGの著者記事は、予定対象が死亡した場合は残りのロック対象へ振り替わると説明。 | 現在の死亡slotでdropする`cycle-frozen-slot-v1`をゲーム準拠consumerへ昇格させない。振替先の選択は別契約が必要。 |
| 距離式・同距離順・対象種別 | 中心/外形/3D奥行き、同距離順、PART等を判定できる制御実験は今回も未取得。 | 確定しない。provider順を最近傍へ読み替えない。 |

出所は [Prydwen個別解説](https://www.prydwen.gg/nikke/characters/snow-white-heavy-arms)、[NIKKE.GG著者記事](https://nikke.gg/snow-white-heavy-arms-analysis-should-you-pull/)（著者lzzy、掲載上の更新2026-01-08）、[スキル表を掲載するファミ通](https://www.famitsu.com/article/202512/62211)、[一般の順番攻撃説明](https://volx.jp/nikke-snow-white-heavy-arms-spec-skill/)。NIKKE.GGは直接openが403だったが、検索エンジンが返した同URLの索引本文で死亡時振替の説明を確認した。埋込画像/動画、フレームログ、再現入力は確認していない。同一URLの複数検索結果を複数の独立根拠とは数えない。

死亡時振替は公開情報上の有力仮説まで進められるが、「残りのどれか」という説明から、次の生存対象、先頭から再走査、均等化、乱数のどれかを決めることはできない。全滅時、消失と死亡の違い、同identityの再出現、途中spawnへの追加ロックも未確定。距離式や決定的振替アルゴリズムを推測でゲーム仕様にしない。

次のconsumerは、snapshot/世代検査と既存actor land/counter/heal経路を再利用し、死亡時policyを独立した明示契約にする。`cycle-frozen-slot-v1`の既存63ケースと8件のpacket証跡は変更せず、dropモデルの部分実証として保持する。生存対象だけの配送検査と、死亡時に未確定policyを要求する境界を分ける。公開admission、全25効果/全キャラ認定を開ける根拠にはしない。

今回の更新は調査と設計判断のみ。GPUソース・計算・goldenは未変更、GPU/Windows追加実行0。機械可読の出所・不確実性は `research/target-count-query-evidence/heavyarms-online-delivery-reassessment-v1.json` に保存。

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


## 実着弾キューへのsnapshotリンク（2026-10-27）

sealed `lock-packet-bindings` は8入力（native4／raw拒否4）をMetalとfresh独立監査で照合した。通常充填、短い充填の空snapshot、配送前の全敵ダメージによる死亡と次世代再出現、ハイド後の4hit/3targetを含む。元index4/8/9と元index20を保持するpartial fixtureであり、元全25効果ではない。snapshot番号と既存receiptのhit/hitsをstore/load両地点で照合する。選択slotのlive statusも記録するが、実際の着弾対象はまだ従来のnamed routingのままで、snapshot slotへ配送する処理は未接続。

既存receipt at+7は周期snapshot番号に使用されるため再利用しない。全2048 queue slotのtoken bankを804176..806224、31shotの時刻を806224..806286、headerを806288..806304、16word×38件の診断traceを806304..806912へ置く。入力104400/出力806912word、live actor set32個、queue2048は不変。診断38件を超えると拒否し、queue容量を減らしたりtraceを黙って捨てない。loadでtokenを解放し、終了時の全2048wordがzeroであること、全shot時刻・alignment・trace・tailを比較する。

既存native観測器は名前参照の可変hit数を1としていた。新しい明示flag下だけ、実 `_handle_damage_eff` がappendした自身のHitEvent数と順番を読み、正本の計算や通知を変更せずhit/hitsを観測する。旧caseのflagはfalseのまま。全battle・HP・skill/射撃trace・quota・候補を保持する透明性比較も継続する。GPU .047511秒、fresh監査4.013988秒。

default106のCUDA/MSL厳密生成hashは不変（生成のみ）。旧physical10/external16は新sourceでMetalと独立sealを完了し、全shader/input/output byteを保持、新v4/v5 goldenへ接続。旧cover23の現source再認定は、必須pipeline cacheが未保存でGPU起動前に停止したため未完了。旧sealed cover packetは保持し、失敗packetのclaimを消さず再送しない。現checkoutのcover23通常packageはsource相違のguardで拒否される。次にpre-claimのMetal cache調査・復旧経路を整備する必要がある。

証跡は `target-count-query-evidence/metal-lock-packet-bindings-v1.json`、`lock-packet-legacy10-16-retention-v1.json`、`lock-packet-legacy23-predevice-failure-v1.json`。全inventory fieldを保持し、全キャラ0・public GPU false・UI CPUは維持する。次の機能はsnapshot slotを既存actor land/counter/heal処理へ適用するconsumer。距離・挑発・再対象化の実機仕様は未認定。


## cover23の現source再認定を復旧（2026-10-27）

claim前Metal cache gateを実装・テストしたhost修正版a4f9ac2eの固定packetで、旧失敗と同じkey6fb2d307…のmissがtests/native/worker/claim前に停止することを確認。旧packetのGPU source全closure、全input/native指紋、旧claim SHAを保持した。新packetの未使用claimで初回cache作成を明示して1回だけMetal23を実行し、別fresh監査でv2 goldenを作成した。全CUDA/MSL生成byte・入力・74,235,904byteの出力が元cover23と同一。現checkoutの通常cover23 package作成も復旧対象となる。配送対象slotをHPへ適用するconsumerは引き続き未接続。

## 公開情報再確認：実機待ちをせず進める境界

ユーザーのネット調査指定に従い、ファミ通のスキル全文（0.2秒、未ロック敵、照準線基準、通常5機、攻撃/ハイド解除、バースト+10）とPrydwenの取得順循環・キャラ固有の挑発例外を再確認した。NIKKE.GGの死亡時振替は検索索引本文で確認できるが、直接取得は403であり振替先の決定法は得られていない。Level Infinite公式発表にも距離式の説明はない。今回の追加検索では、中心/外形/3D距離や同距離順を区別できる制御実験は見つからなかった。既存の判断を維持し、判明した状態・寿命・配送順のモデルを使って開発を進める。距離順位と死亡時の決定的な振替は未確定事項として保持する。全キャラ認定や実機一致へ昇格させない。再確認の出所と取得方法は `research/target-count-query-evidence/heavyarms-online-delivery-reassessment-v1.json` の `recheck` に記録。今回は調査記録のみで、計算変更・GPU実行・Windows依頼はない。

## 2026-10-28 発生元IDの保持と次の変換制限

型付きパケットの登録行IDを生成時からBODY抑止監査まで保持し、受動的なnative履歴観測にも渡した。同名のbuffをdamage発生元へ誤対応させず、登録IDの型・名前・owner・damage種別を検査する。共通CLIの固定packetで10グループ65テスト、既存12入力/native7のCPU事前検査に成功。旧7ケースの全履歴と旧typed8戦闘指紋は保持。同名のtyped/通常damageはnativeで別の発生元として観測できるが、GPU入力変換は依然 `Multiple named non-buff carriers are not ported` で拒否する。複数typed定義も短いadapterの1定義制限が残る。今回の変更を同名複数効果のGPU認定へ昇格させない。発見時の失敗と最終receiptは `research/target-count-query-evidence/packet-source-identity-native-v1.json`。GPUコード変更・GPU実行・Windows依頼は0。元index0の敵carrier/空間順位と全25効果の接続が引き続き優先課題。

## 2026-10-28 元の敵ロックcarrierと状態照会をMetal接続

`enemy-lock-carriers` は元index0/1/2/6/20を保持し、自己向けの観測用markerを元の敵向けtargetへ戻した。入力変換ではlock_onを既存の名前付きenemy markerへ下ろすが、原定義のtarget・0.2秒・max_stack・寿命は変更しない。候補順位は既存の明示body/spawn-order providerであり、ゲームの照準距離を認定しない。ロック取得で選んだ世代付きhandleを既存actor-setのleaseに渡し、MODE25→MODE19で既存carrierを活性化する。独自のtimer・actor pool・buff実行器は追加しない。元の名前付き被ダメージ増加と通常攻撃/ハイド解除も既存consumerへ接続した。

固定32630ddfの7入力（native4、拒否3）はApple M5の実MetalとGPU禁止の独立sealに成功。実GPU時間0.05085秒、PSO必須hit、7グループ53テスト成功。通常、死亡、短チャージ、死亡後再召喚を戦闘全体・履歴・ロックsnapshot・敵状態まで比較する。死亡したcarrierの空recipientをnative観測器が味方へ誤分類していた点は、実carrierに残るimmutable enemy_recipient_keyで修正し、空carrierを含む全行保持のテストを追加した。計算本体や比較対象を省いて合わせていない。v1/v2初期化拒否、診断entryのwire拒否、診断stage404、v3観測分類差分を保持し、同じclaimは再実行していない。証跡は `research/target-count-query-evidence/metal-enemy-lock-carriers-v4.json`。

CUDA/Metalは同じSlang・入力・比較器を使用する。`enemy-lock-carriers-cache-only` は同じsealed計算の既存CUBIN必須hit経路で、standaloneなのでresident用generation flagを要求しない。CUDA実機/CUBIN hitは今回未検証、Windows依頼0。共通ファイルのopt-in変更について旧sourceの正確な逆投影を保持するが、旧suiteのcurrent-source GPU再認定は別途必要。旧goldenを新sourceへ書き換えて成功扱いにはしない。次はこの敵carrier接続を既存typed projectile/順番配送と合成し、元の全25定義へ進める。距離式、死亡時の振替規則、公開admission、全キャラ認定は未完了。

## 2026-10-28 元25定義・実編成91定義の合成をMetal実証

`original-lock-composition` は元のHeavyarms全25定義、装備/共通分を含む本人34定義、支援4人を含む91定義を削除せず、実武器・実設定・実base statで実行する。元の登録順/owner/武器/configをnative実行時にも照合し、自己向けmarkerへの置換や架空の射撃間隔を使わない。既存の敵carrier・世代ロック・実射撃snapshot・順番配送queue・typed敵弾・fate監査を1つの時計へ接続した。候補順位は明示body/spawn-order providerであり、未確定の照準距離モデルの実機認定ではない。

固定8fd51499、package 0d4b4748…の3/30秒×本体のみ/3ADDの4戦闘とraw拒否4入力が、Apple M5 MetalとGPU禁止の独立sealに成功。9群71検査も成功。30秒は射撃742回・ロック取得110回・順番配送リンク190行・skill113行・端数通知2240行・team通知1120行を全行比較し、通知省略0。元のraw/履歴を省いて合わせず、既存1310720ワード内の未使用領域へ5つの専用bankを配置した。旧bankは空のままであること、新bankの全行/全padding/末尾を検査する。全13種類の履歴容量をfresh native事前検査で確認し、不足はGPU claim前に拒否する。v1のmetadata不足/照会100件上限とv3の通知省略差分を保持、v2は基準固定のみでGPU未実行。同claim再実行0。

実GPU2.2474秒、冷PSO約9.3935秒、CPU事前比較約49.34秒。paired Slang生成は必須cache hit・compiler0。旧7suiteと本体106のCUDA/MSL生成はstrict normalized SHAが従来と同一で、normalizer除外は追加しない。旧source mapのGPU再認定は未完了で、旧goldenを新sourceへ書き換えていない。`original-lock-composition-cache-only` は同じ計算/goldenを使い、CUBIN cacheとpaired generationの両方の必須hitを要求する。Windowsは旧transactionのstatus読取り1回だけを試みたがhost unavailableでterminalとは判断せず、再送/追加GPU実行0。

この実証は全定義を含む特定の実編成/worldでの等価性であり、全条件分岐・実機・全キャラ認定ではない。全編成でのcover、parts、負傷/heal、距離と死亡時振替、他キャラ/variantの検査は残る。公開admissionとUI CPU、全キャラ認定0を維持。証跡 `research/target-count-query-evidence/metal-original-lock-composition-v4.json`、生成保持 `original-lock-legacy-generation-retention-v2.json`。

追加のCPU受動監査では、各caseをdiagnostics有/無の2回観測し、固定goldenの全native fingerprintを保持した。30秒では元row0..24のうち24定義に `_activate` entryがあり、未観測はrow2のevent:coverだけだった。3秒ではrow16/17/23も未観測。entry呼出しは実効果適用やGPU全分岐の認定ではなく、次の未対応分類の根拠である。特にparts対象や負傷状態はこのworldに存在しない。出所 `research/target-count-query-evidence/original-lock-native-activation-coverage-v1.json`。
# 2026-10-30 公開情報による再判断

ユーザーの指定に従い実機の提供待ちをせず、公開スキル全文と著者の実使用分析を再照合した。照準線基準の未ロック敵選択は支持されるが、中心/外形・投影/3D距離・同距離順を区別する追加実験は見つからなかった。既存の数値距離式を未確定とする判断を維持し、推測で共通実行器やgoldenを変更しない。同一記述の再探索を継続条件にせず、他の未対応項目を進める。出所と取得制約は `research/target-count-query-evidence/heavyarms-online-decision-20261030.json`。今回の計算変更・GPU実行・Windows依頼は0。
