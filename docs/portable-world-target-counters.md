## 2026-10-21 初期敵出現通知をMetal27・CUDA27で実証

計算sourcecb4400977032fdac69621c9f1fa5a6dff34e8c31・private ABI86/mode15で、event:enemy_spawn（元のevent5）をworld定義の受付と共通startupへ接続しました。全員のbattle_start→全員の初期enemy_spawn→初期magazineの順で一度だけ実行し、召喚敵1体ごとの既存通知は同じdispatchを使います。CUDA/Metalに別のイベント実行器・数量計算・効果定義は追加していません。new入口のevent5定義は旧mode13では拒否します。

Metal27＝native22実戦＋拒否5が初回成功しました。Apple M5 command completed、GPU0.063310秒、input10526116bytes/readback70778880bytesを保存。初期通知5回、即時/遅延2体、127体の計640通知とowner順序・binary64時刻、再出現、全5owner、別ownerのbattle_start状態、初期装弾、gauge、敵fieldのscope/stack、trigger budget、vanish、同フレームの敵攻撃、128対象への通常skill/DoTを完全nativeで照合しました。既存timer・queue・counter・Actor着弾順序を保持し、DoT初回は既存のt=0 timer passを使います。

CPU429検査、旧15入口CUDA/MSL生成物厳密一致、保存raw/Git source/nativeのGPU禁止監査に成功しました。出力は既存655360wordのまま、612112に8word head、612120から4096件×4wordの通知観測をGPUが記録します。128Actorの敵攻撃力・periodic packet bankと重ならず、容量超過はstatus64です。旧入口の生成結果を保持し、旧923以下・通常4682を再実行していません。Metal GPU1回・source1種・同一source/input retry0。

CPU初回の「0.2秒以上」という観測assertは、実native累積clockが0x1.9999999999999p-3だったため不正でした。浮動小数点sumのPython版による差も避け、nativeと同じ12回の逐次加算を厳密比較します。丸め/許容誤差は追加せず、初回native20件をportable-world-spawn-native-initial.jsonへ保持しました。旧生成物の空行1行差も空展開フックを既存行に置いて解消し、正規化規則は変更していません。失敗したCPU生成照合はportable-build/world-spawn-initial-generation.json/.logへ保持。

Windows v98は固定a7f4b777845dee039f9d873df7eea272d4debf07（17ファイル280180bytes）、codex/cuda-world-v98-sourceで成功しました。CPU47検査・GPU禁止27入力/native22・source SHA80照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・114.941192秒・exit0。保存3JSON計66029bytesを取得し、全input/output/native/generated fingerprint・API50phase・元HEAD/status/service保持・residual0・retry0・旧923以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v98-cuda-validation.json、seal-world-v98-cuda.pyを参照。turn01a15c43-0306-7782-94cc-7e37a28380aeはcompleted、cursor182、idleで、再依頼は不要です。

実203キャラ＋21お気に入りの段階1/2/3＝266プロファイルを静的再監査しました。own定義のPython事前検査通過はbase95→97、全133→137です。바이퍼（通常＋お気に入り1/2）と아크레인저 블랙の4プロファイルが増え、差分をportable-world-spawn-catalog-delta.jsonへ保存しました。CPU battle/GPU build/execute禁止・実呼出し0。GPU kind admission・容量・real roster/world配線・全キャラ戦闘認証を示す数字ではありません。

通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。次はcharge/part/crit判定、未接続buff/selector（explosion_range、effect_interval、trigger_count_reduce、stun等）、source攻撃/interrupt・skill追加part到達、動的操作/復活、周期gone/expiry/dispelを含む全組合せ、容量/長時間/全変種の認証を進めます。永続条件付き味方HP/防御とhit-only max-HP rankのnative不整合も残ります。効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 敵攻撃力fieldをMetal37・CUDA37で実証

計算source0395cad4130cadf32d560efa0df5551d374f7f10・private ABI85/mode13で、敵へのatk_pct/atk_caster_based_pctを既存のresident・stack・期限・Actor recipient・名前付き状態へ接続しました。CUDA/Metalは同じSlang本体と28実戦・不正9入力を使います。出力幅655360wordは前段階のまま、periodic snapshotの後611856から128Actor×2wordの実GPU queryを保存します。CPU計算済みの敵攻撃力や被害量は入力しません。

nativeのenemy_atk_down_flatは術者の基礎攻撃力×割合をresident順に合計し、ボス攻撃力へ加算して0以上に制限します。この値をtarget選択・5人への着弾より前に一発ごと捕捉し、途中のHP条件変化で残りの対象を再計算しません。敵へのatk_pctはnativeの被ダメージ式では読まれませんが、get_buffsの対象側分岐ではこちらの与ダメージのatk_pctに入るため、既存の順序付きcollectStatsへ接続しました。味方のrank/base-stat helperへは混ぜていません。nativeが召喚敵の発射元IDを復元できずflat補正を適用しない既知の制約も残ります。

修正版Metal37＝native28実戦＋拒否9はすべて一致しました。M5 command completed、GPU0.139797秒、input14424676bytes/readback96993280bytesを保存済み。基礎ATKと味方buffの区別、正負・0clamp、expiry、stack/refresh、複数owner/alias、HP runtime条件と有限条件のlatch、7rank、128対象、遅延spawn/再世代、全battle/field/名前付き状態を照合。CPU418検査、旧14入口のCUDA/MSL厳密一致、保存raw/Git source/nativeのGPU禁止監査にも成功しました。

初回22c8ca3の35入力は不一致を保持しています。既存status観測の有効化だけで保存出力をCPU再監査し22/28が一致、残るatk_pct与ダメージ3件とHP条件受付3件を共通処理へ修正しました。初回raw・initial-metal・observer-replay・findingを保持し、同一source/input GPU retry0です。今回のMetalは異なる固定source2種で計2回。旧入口は14生成物の厳密一致を確認して旧923以下と通常4682のGPU再実行をしていません。

skill/pendingの古いshort goldenはこの変更前のa51ea7dでも現行生成物と異なりました。この2入口は追跡ファイルのcleanな固定a51ea7d worktreeから生成して比較し、今回の変更後も厳密一致を確認しました。normal等の旧11とperiodicも従来基準に一致。正規化規則を追加して差を隠していません。portable-world-enemy-attack-generation-baseline.jsonに両方の値と固定source SHAを保持しています。

Windows v97は固定970aed0d7921de429c3808ec73a7115b0dcd2386、codex/cuda-world-v97-source（16ファイル252144bytes）で成功しました。指定CPU36検査・GPU禁止37入力/native28・source SHA78照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・112.762323秒・exit0。保存3JSON計66976bytesを取得し、全input/output/native/generated fingerprint・API50phase・元HEAD/status/service保持・residual0・retry0・旧923以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v97-cuda-validation.json、seal-world-v97-cuda.pyを参照。turn01a15c33-bbcf-75e1-b3d9-08c4d7753dceはcompleted、cursor174、idleで、再依頼は不要です。

実203キャラ＋21お気に入り段階1/2/3＝266プロファイルを静的再監査し、own定義のPython事前検査通過がbase85→95、全121→133へ増えました。12の新規プロファイルをportable-world-enemy-attack-catalog-delta.jsonに保存。CPU battle/GPU build/executeは禁止して呼出し0です。これはGPU kind admission・容量・real roster/world配線・戦闘認証の証明ではありません。

通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。敵対象の他field/selector、enemy_spawn通知、charge/part/crit、source攻撃/interrupt・skill追加part到達、動的操作/復活、周期gone/expiry/dispelの全組合せ、永続条件付き味方HP/防御とhit-only max-HP rankのnative不整合、容量/長時間/全変種認証を進めます。効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 DoT・一般周期ダメージをMetal923・CUDA45で実証

計算source1f059919037de30f722b121064cd4be819cc87e1・private ABI84/mode11で、DoT/一般周期ダメージを既存timer・stack・reference・binary64数量計算・共通Actor着弾へ接続しました。256定義と2048着弾パケットそれぞれに、128対象の順序/bitset/捕捉birth ordinalを38wordで保存します。既存のchecked monotonic add birth ordinalを使い、後から生まれた同slotの世代へ再結合しません。aliasによる対象unionでも、作成済みパケットは不変です。通常timer更新→queue drain→burst/射撃の順序を保持し、即時DoTを別の早着弾経路にしていません。

Metal923＝native32実戦＋不正13＋旧878が成功しました。全数量/着弾traceに加え、実際のnative timer・carrier・named predicate状態を一致検査しました。128対象、7rank、同名alias、再出現世代、own stack/refresh、参照stack、通常式、一般周期3hit、DOT credit/counter子、致死/生存addからの登録・回復を含みます。CPU408検査、旧11入口CUDA/MSL生成物厳密一致、保存raw/Git source/nativeのGPU禁止監査に成功。legacy UIの全キャラ対応を意味しません。

新入口だけ出力655360wordへ拡張し、不変snapshot領域を追加しました。従来の524288word prefixを旧878入力すべてで完全保持し、追加tailは0です。従来入口の出力幅は変更していません。共通backend/Metal transportは従来の範囲と新655360だけを許可し、未検証524289などはbuild前に拒否します。2GiB未満の互いに重ならない700件＋223件の2バッチで、各input/readback/evidenceを即保存しました。source2種・Metal計4 dispatch（初回2＋修正版2）、同一source/input retry0です。

初回7fffac4の全数量・packet traceと旧878 prefixは一致しました。finish後pool aliveでbefore_finishの捕捉membershipを削った観測差2件と、prepare hookを通らない実native periodic ActiveBuff UIDを数えなかったordinal差1件を、保存readbackのCPU再監査だけで解消し32実戦一致を確認しました。観測項目を無視・丸めてはいません。残るNaN intervalのstatus0は、共通周期判定を正の有限binary64 intervalへ修正し、NaN/Infinity/負値を実GPUで拒否しました。初回raw/observer-replay/findingを保持しています。portable-world-periodic-validation.json、seal-world-periodic-metal.pyを参照。

Windows v96は固定4554b0b61ce98375deee8aedeb262729915e3e0f（21ファイル346136bytes）で新45入力/native32だけを検証しました。CPU65検査・GPU禁止45入力・source SHA76照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、111.904949秒・exit0。保存3JSON計70803bytesだけを取得し、全input/output/native/trace/generated fingerprint、API50phase、元HEAD/status/service保持、残存0、retry0、旧878以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v96-cuda-validation.json、seal-world-v96-cuda.py。turn01a15c1c-6a59-7803-bb5e-a9787bfd22fdはcompleted、cursor167、idle。再実行依頼は不要です。

実データを全203キャラ＋お気に入り21キャラの段階1/2/3、計266プロファイルで静的監査しました。own定義のPython事前検査通過はbase85/203、全プロファイル121/266です。全定義を実owned/growth準備から取得し、除外や架空効果を使っていません。CPU battle/GPU build/executeを禁止して呼出し0を実測しました。これはGPU kind admission・capacity・policy wiring・戦闘認証ではありません。portable-world-catalog-definition-readiness.jsonに全target/field/trigger/conditionと不受理理由を保存しています。

次はこの実キャラ一覧から、敵atk_pct/atk_caster_based_pct等の未接続numeric field・selector、event:enemy_spawn等の通知、charge/part/crit判定、source攻撃/interrupt・追加part到達、revive/controlへ進みます。DoTのmid-frame gone/expiry/dispelを含む全効果組合せとreal roster/world入力接続も引き続き認証が必要です。

通常画面CPU・public world false・全203変種の戦闘認証0、legacy unexplained Metal14c8e2e OPENを維持し、全ゴール未完了です。nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合、容量/長時間/全変種認証も残ります。計算処理の効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 pendingを共通Actor着弾へ接続しMetal878・CUDA37で実証

計算source6bd7ab48095984d76ebdd5b291f56e0c99a5032e・private ABI83/mode9で、B3 pendingを128Actorの共通着弾helperへ接続しました。通常skillとpendingは同じ選択・世代検査・HP/counter/lifestealを使い、既存のソフトウェアbinary64・reference・後続buff除外・全数量を先に捕捉する二段階を保持します。pendingだけ同フレームで着弾し、full_burst_startやcounter子が作った通常skillは次フレームまで通常queueに残ります。明示normal_attack式よりB3 plain bonus pendingが優先するnative契約を共通packerへ反映しました。

Metal878＝native26実戦＋不正11＋旧841（833＋8）全524288word一致が初回成功しました。Apple M5でcommand completed、GPU 0.924025秒、全input/readbackを保存済み。CPU399検査、旧11entryのCUDA/MSL生成物厳密一致、保存raw/Git source/native/着弾trace/実際のpending容器から観測したenqueued・fired・countのGPU禁止監査にも成功。128対象、7rank、reference欠落/0/2、名前付き3hits、buff順序、counterが変える前の一括数量、add死亡、回復を含みます。通常画面の全キャラ認証ではありません。

直接skill入口はActor着弾本体の共通helperへの切り出しで生成コードが変わりました。これを旧12entry厳密一致と誤記しないでください。旧11entryは厳密一致、直接skillを含む旧841は全出力word保持です。生成測定はportable-world-pending-refactor-generation.json、実証と監査はportable-world-pending-validation.jsonとseal-world-pending-metal.pyです。CUDA/Metal別実装やCPU計算済み数量の入力はありません。GPU計1回、同一source/input retry0。

Windows v95は固定ea1eccc0e23d22f7cfede3437fd76dedf6dec0fe（15ファイル297084bytes）で成功しました。CPU48検査・GPU禁止37入力/native26・source SHA74照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、109.304244秒・exit0。保存3JSON計76674bytesだけを取得し、全input/output/native/trace/generated fingerprint・API50phase・元HEAD/status/service保持・残存0・retry0・旧841以下/通常4682再実行0を共通監査器で確認しました。portable-world-v95-cuda-validation.json、seal-world-v95-cuda.py。turn01a15bf5-799c-7bb1-a476-b5948bbaf2f6はcompleted、cursor164、idle。再実行依頼は不要です。

次のDoTはCPU11実戦を固定しました。通常timer tickはBM更新で作成され同フレームのqueue drainへ入り、射撃counterで適用したimmediate DoTは次のtimer更新で初めて生成されます（作成0→次フレーム着弾の通常skillとは数量捕捉時刻も異なる）。後続buffをその最初のtickが読む対照も保存しました。適用時の対象membershipは後から出現したwaveを含まず、tickごとに現在の数値を読み、refresh/own stacks/expiryを保持します。portable-world-dot-skill-native-contract.jsonと初回CPU観測を参照。初回は観測値の生成時刻を通常skillと同一視したassertが不正で、実測を残して修正しました。DoTのGPU受付は未接続のままです。

次は既存periodic timer/stack/数量計算を使い、8bitのperiodic対象maskを128Actorの捕捉membership・世代へ接続する必要があります。liveなlate-routingの直接skillと混同しないでください。timers→通常queue drain→burst/射撃のnative順序を保持し、DoTだから常に即時着弾とする別経路は作りません。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPEN、全ゴール未完了を維持します。DoT/source攻撃/interrupt・skill追加part到達、動的操作/復活、全効果組合せ、容量/長時間/全変種認証、nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合が残ります。計算処理の効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 auto_damageの数値契約をMetal8・CUDA8で実証

計算sourceef12e0940259d64bb48ed252ef1836b52ef4bfa7で、world入力のauto_damageは明示normal_attack式がある場合だけ通常攻撃計算を使うよう共通packerを修正しました。通常攻撃専用damage/critical補正と全攻撃critical補正、1hit/3hitsをnative8実戦で区別し、Metal8のbattle・着弾traceが完全一致しました。default242、normal専用damage50でも242、明示normal式なら363、全攻撃critical50なら298です。CPU393検査に成功し、従来のnon-world auto契約は保持します。

GPU shader73ファイルと生成CUDA/MSLは不変です。旧833の全保存input/readback SHAを確認し、旧40native中39は全入力word一致＋全native/trace再監査、変更したauto1入力は新8の先頭で実GPU検証しました。不正10入力も同一、旧783は保存済みsealed出力を保持します。同じ入力の再実行を避け、Metalは新8だけ1回、旧833再実行0、retry0。共通計算本体を別実装へ置き換えていません。portable-world-skill-formula-validation.json、seal-world-skill-formulas-metal.py、portable-world-auto-formula-finding.jsonを参照してください。旧v93は固定2498e1e worktreeでもMetal/CUDAをCPUだけで再監査済みです。

Windows v94は固定05a763db1d988ad9c82e5b14fcf4a49aa16430a0（6ファイル89510bytes）で成功しました。CPU42検査・GPU禁止8入力/native8・source SHA73照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、103.169556秒・exit0。保存3JSON計58579bytesだけを取得し、全input/output/native/trace/generated fingerprintとAPI50phase、元HEAD/status/service保持、残存0、retry0、旧833以下/通常4682の再実行0を共通監査器で確認しました。portable-world-v94-cuda-validation.json、seal-world-v94-cuda.py。Windows turn01a15be6-06de-7443-81e8-0c77c918612bはcompleted、cursor159、idle。再実行依頼は不要です。

次のpendingを完全native9実戦で固定しました。B3 bonus_damageは約0.583333秒のfull burst進入フレームで作成・着弾し、通常skillの次フレームqueueとは異なります。後続cast buffは除外し、先行buffは適用し、2pending分の数量は最初のcounter子fieldが変化させる前に一括捕捉します。all3対象、normal専用補正の除外、0係数も確認。B3 plain bonusのpending処理は明示normal_attack式より優先し、その補正を使わないことも固定しました。登録をliteral fixtureへ差し替える観測器ではchar_effects検索にも同じliteral一覧が必要でした。opt-in observe_authored_effect_lookupを追加し、元catalogによる誤った後続buff包含748と、正しい354のCPU対照を保存しました。portable-world-pending-skill-native-contract.jsonと初回native報告を参照してください。pendingはGPU未接続で、現private受付でも拒否します。

次は、既存pendingの「全数量を計算してから着弾」の二段階とreference/後続buff除外を保持し、direct queueの128Actor着弾本体を共通helperにしてpendingから同フレームで呼ぶ必要があります。通常queue全体を途中でdrainするとB3中の通常skillまで早く着弾するため不可です。pendingが明示normal式より先に処理されるnative優先順位も保持してください。新しいprivate入口を固定して、旧直接skillの全出力・拒否契約を保持しながら検証します。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPEN、全ゴール未完了を維持します。pending/DoT/source攻撃/interrupt・skill追加part到達、動的操作/復活、全効果組合せ、容量/長時間/全変種認証が残ります。nativeの永続条件付き味方HP/防御、hit-only max-HP rankの不整合も未解消。必要な検証後に計算処理を効率化します。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 direct skillの遅延着弾をMetal833で実証

計算source761e362・private ABI82/mode7で、counter子を含む直接skillを既存の共通damage計算・LandingReceiptキュー・128Actor selector・HP/counter/lifestealへ接続しました。作成時にbodyの明示query scopeで数量・hit数を捕捉し、次フレームまたは終了時にlive targetを選びます。捕捉したcompletion Actorへ敵fieldを付ける処理とは別のnative契約です。named hit_count wire49はcompletion targetを継承します。カウンターなし編成にも合成counterを挿入しません。

Metal833＝完全native40実戦＋不正10＋旧783全524288word一致、CPU390検査、旧11entry CUDA/MSL生成物厳密一致、保存input/readback/Git source/native/着弾traceのGPU禁止監査が成功しました。12直接damage系統、7rank selector、128対象分配と丸めで0damageでもcredit1、作成後に出現したadd、同じdrain中に追加される子damage、作成後buffで変わらないmulti-hit数量を確認しました。ソフトウェアbinary64、整数丸め、選択、状態、イベント、counterをCUDA/Metalで共用し、実装・fixture・比較器を分岐させていません。

nativeの空enemy field資源に依存したbody query scopeを修正しました。中立field0の有無で変わった242/511は両方511、旧11中10辞書と過去381完全native辞書を保持しています。証拠はportable-world-query-scope-regression.jsonとportable-world-counter-damage-queue-native-contract.jsonです。

初回のcore_damage分類差、通常攻撃式の許可bit256漏れ、入力packerの式指定漏れをそれぞれ保存しました。canonical CPUのcore_damageはWEAPON、normal_attack式はnormal_skill/SKILLです。単なるskill起源で分類しません。最終ケースはnormal_atk_dmg_pct50で式指定の数値も検査します。4つの固定source snapshotでMetal計4回、最終2回はGPU shader共通でauthored inputが異なり、同一source/input retry0。全失敗raw・全出力を保持しています。portable-world-skill-finding.jsonと初回/formula-admission/formula-packing-metal.jsonを参照してください。

Windows v93は固定9c34a5f1a4542811385ac3f6160087c3ef39b29e（23ファイル356917bytes）で新規50入力/native40に成功しました。CPU39検査・GPU禁止50入力照合・source SHA73を先行し、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、105.142319秒・exit0。保存3JSON計65960bytesだけを取得し、source/name/bytes/SHA・全input/output/native/着弾trace/generated fingerprint・50 API phase・旧783/通常4682以下の再実行0・元HEAD/status/service保持・残存0・retry0を共通監査器で照合しました。portable-world-v93-cuda-validation.jsonとseal-world-v93-cuda.pyを参照。再実行不要です。

次の数値組合せで、auto_damageのnativeは明示damage_formulaがない限りnormal_atk_dmg_pctを受けない一方、既存portable packerはauto_damageを常にdamageNormal1にする差をCPUで確認しました（native242→242、明示normal_attackなら363）。今回の既定値40実戦は一致していますが、auto_damage＋通常攻撃専用補正の組合せは未認証です。world入力の追加検証・修正が必要で、legacy normal生成物を変更しないでください。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPENを維持します。pending/DoT/source攻撃/interrupt・skillの追加part到達、動的操作/復活、全効果組合せ、容量/長時間/全変種の認証は未完了です。hit-only max-HP rankと永続条件付き味方HP/防御のnative不整合も残ります。明示normal_attack式はworld入力だけの追加受付です。全ゴール完了ではありません。効率化は必要検証後、GitHub共有はゴール達成まで利用者許可済みです。

# 対象別命中カウンターの共通実行器への接続

## 現在の状態

共通Slangのcounter resource/event、実着弾、完了子の対象条件と敵field受取先をprivate ABI81へ接続し、Metal783で実証しました。CPU379・旧10entry生成物・旧721全出力保持が成功しています。前段CUDA58も監査済みです。今回のCUDA62も保存3JSONのMac監査まで成功しました。typed damage queue/skill/pending/DoTは未接続で、先にnative body query scopeの不整合を解消する必要があります。通常画面CPU、world公開無効、全変種認証0/203を維持します。以下は段階別の履歴です。

## 参照する定義と実装

- `app/target_counter_specs.py`: CounterSpec、threshold、ActorHandle、family/outcome mask、refresh、on_death、attacker、world_scopeを唯一の定義として使います。
- `app/target_counter_runtime.py`: 実際のUID/epoch/credit/lifetime、収集・ラッチ・子通知・終了処理の順序です。
- `app/impact_specs.py` と `app/impact_runtime.py`: Actor、credit、family/outcome、body/part/addへの接続と着弾順です。
- `scripts/target_counter_cases.py` と `tests/test_target_counter_runtime.py`: 同じcase tableをCPUとGPUに使います。独立したCUDA/Metal用caseコピーを作りません。

カウンターのcarrierは敵sentinelに付く一方、数えるActorは設定にある正確なkind/identity/generationです。carrierの受領者と、resourceが参照するActorを混同しません。未知のActorをbodyへ読み替えません。値はstackではなく別resourceのcreditです。同じ所有者・名前のcounter定義はActor/credit policyが同じであることを検査し、その名前を通常のstack操作で変更する定義は拒否します。

thresholdは有限・正・最大1e12、creditはImpactの独立した非負binary64値です。damage、弾薬、core確率からcreditを推測しません。進捗は既存binary64加算とminを使い、整数へ丸めません。UIDとrefresh epochには別の容量・桁あふれ検査が必要です。

## ライフサイクルと同期再入

refresh時はepochを進め、preserve指定・同じActor・未完了・期限内の場合だけ旧creditを引き継ぎます。全ready siblingを先にdoneへラッチしてから子を同期実行します。完了した古いmarkerは完了子が動く間も見えます。子がmarkerをrefresh/置換した場合、古いcompletionが新epochを消してはいけません。

完了後は、resourceが同じrecord/epochのままの場合だけcarrier/resourceを除去します。実際にcarrierが残っていた場合だけstate_endを通知します。death policyはcompleteとcancelを区別します。dead Actor集合は正確な世代を持ち、現在のnative上限512を検査します。source期限切れと着弾による死亡を、根拠なく同じresource死亡へ読み替えません。

## 着弾側の接続点

実CPUの観測とinstalled ASTでは、body/partもlifestealより前に `publish_landing` と同期完了子を実行します。addは `BossScript.hit_add` のreceiptから `publish_impact`、続いてkilledなら `target_death` を呼び、その後にlifestealします。致死着弾も死亡登録より先にcreditを集計します。以前の「body/partはlifesteal後」という記録は誤りでした。`portable-world-target-counter-landing-order-finding.json` と実戦23ケースを基準にしてください。

nativeの実着弾bridgeが発行するoutcomeはDAMAGINGです。明示ImpactのBLOCKED policyを、worldの遮断時に勝手に発火する規則へ変えません。ゼロdamageでも正のcreditを持てます。武器モードやnormal-labelled skillはダメージ式の種類とHitFamilyが必ずしも一致しません。分類はcanonicalなタグ/impact規則に従い、既存のnormal/skill判定を検証して使います。

## 保持領域と入力

既存512 resident、128対象のgeneration付き受領者、4096件の遅延通知を活用します。counter用のstatic policyはGPU入力の専用領域へ、progress/epoch/done/completion/dead ActorはGPU所有領域へ置きます。refresh中の古いcompletionには、読み替わらないActor/credit/epoch snapshotを持たせます。

`detail_gpu.py`、`engine_worker.py`、`effect_spec.py`、`engine_compat.py` とlegacy CUDA本体は変更しません。portable adapterとcanonicalなCounterSpecから記述子を生成し、通常ABIのcounter受付やevent58を検証前に開きません。新しいprivate entryから共通のstate/event/impact処理へ接続し、CUDA/Metalで同じ計算・定義・比較器を使います。

## 必要な検証

まず既存tableの全caseをliteral stimulusとしてGPUへ渡し、nativeのcredit/epoch/complete/death/refresh/子の再入を照合します。CPUで生成した途中状態や完了列を入力しません。その後、実武器・複数pellet・weapon mode・0damage・部位・召喚・世代・fatal hit・遮断の完全native戦闘を共通fixtureへ追加します。skill/pending/DoTや新Actor種のworld接続が未完了なら、その範囲を完了扱いにしません。

入力/queue/epochの境界と負例、旧入力の全出力保持、通常/既存private entryの生成物厳密一致を確認します。Macで成功後、Windowsは新規入力だけをCPU事前検査→低優先度・独立180秒上限の1回で確認します。効率化は必要な検証と全変種の認証を終えた後です。

## 2026-10-21 入力契約と実CPU基準（GPU接続前）

`app/portable_target_counter_specs.py` に、共通のCounterSpec/Impactをそのまま検査して入力へ符号化する独立sidecarを追加しました。これはprivate executorへ接続する前段で、compile_programの受付、event58の受付、現在の実験ABI7D、GPUソースは変更していません。通常画面CPU・world公開無効・全変種認証0/203です。

WC01/version1のsidecarは5,128 wordsです。8-word header、256定義×16 words、64 literal action×16 wordsを持ち、元の92,336-word入力へ接続した場合は97,464 wordsとなります。まだその結合入力をGPUへ渡していません。policyにはActorの型/ID/世代、binary64 threshold、family/outcome mask、refresh/death/owner/single-body flag、共通compilerのowner/name ID、literal durationを保存します。actionは時刻とactivate/refresh/Impact/deathだけで、damageとcreditは別々のbinary64です。未使用領域は0、時刻は0..180秒・非減少、名前IDは重複しない0..255です。現在のliteral tableのattack_idは0のみで、一般的なImpact入力APIの完成とは数えません。

同じ所有者/名前の異なるCounterSpec、counter名への6種類のstack操作、不正なActor/量/時刻/名前/容量をCPUで拒否します。未知のActor IDも型と世代を保持し、bodyへ変換しません。carrierはtargetの敵sentinelに限定しています。他のselector、外部squad名、一般的なscript受付は未接続です。CPUのprogress/完了列/途中状態はpack関数の入力にありません。

`research/characterize-world-target-counters.py` は既存tableの10ケース・48段階を実BuffManager/target_counter_runtimeで実行し、全段階の期待値、credit/epoch/UIDの同一性/Actor/dead集合/完了snapshot、全ready siblingのlatch、子から戻った文脈を保存します。UIDはCPUのprocess-global番号ではなく、同一性を保持するケース内ordinalで観測します。共通detail compilerの11 policy row・owner/name IDも独立に照合しています。入力のSHAとnative観測は別々で、native観測をGPU入力にしません。証拠は`research/portable-world-target-counter-native-contract.json`です。

追加の実CPU witnessでは、最初のevent:marker子でepoch1・credit0・done=falseのresourceが既に存在し、その子のdamage0/credit1の着弾だけで完了しました。`effect_runtime.ActivationPreparation`は新carrierのappend直後、refreshのtrigger_count更新直後にprepareを挿入します。したがってSlangのprepareをadvanceBuffActivationの終了側へ置くと遅すぎます。carrierの登録/expiry更新後、named/stack子frameをpushする前に準備する必要があります。旧expiryを別resourceに保持してpreserveを判定し、全readyをlatchしてから子を回す設計を維持します。

portable CPU363検査が成功しました。最初のsandbox内検査は終了確認のpsだけがPermissionErrorで失敗したため、process確認を許可した環境で全検査を再実行しています。今回GPU実行0、Windows追加依頼0です。次はこのsidecarを新private entryへ結合し、resource/epoch/dead registry/immutable ready queueと共通event58の継続frameを実装します。実武器/部位/召喚の着弾とlifestealの通知順、skill/pending/DoT、新Actor種、全変種認証は未完了です。

## 2026-10-21 private resource/event phase:Metal622

固定98427c0、private ABI7Eで、既存resident登録の直後へprepareを置き、GPU所有のcredit/UID/refresh epoch/expiry/done、正確なActor死亡集合、immutable ready queue、同期event58継続frameを接続しました。全readyを先にラッチし、子から戻った時にUID/epochが同じ場合だけ旧carrierを終了します。計算は既存binary64 add/min、状態登録/expiry/名前merge/通知queue/子イベントは既存実行器を使います。CUDA/Metalで別実装を持ちません。

入力97,464 words、出力524,288 words。資源512×16、ready4096×20、死亡Actor512×3、完了trace128×24を未使用領域413,712以後に配置しました。epochとentry UIDの桁あふれ、queue/traceの容量を検査します。literal actionはop43から既存tick→既存dispatchへ渡し、自律world/武器を進めません。counterのpolicy/作用時刻を全てGPU側でも検査し、disabled sidecarは全word 0を要求します。

Metal622は正常10ケース・48段階のlive数/credit/epoch/UID同一性と完了snapshot、不正22入力、以前の590入力の全出力word保持で成功しました。名前付き完了子による自己refresh、siblingsの先行latch、期限境界、fractional credit、death/cancel、owner限定、blocked明示policyを含みます。per-step resource観測はこのtableの最大2 carrierを比較するものです。全キャラ/全物理Actor/全特殊効果の認証ではありません。

初回a27f308は旧590保持とraw22拒否に成功し、新10入力は自律world rootのop24完了条件で全て受付拒否でした。失敗raw/reportを保存し、CPUで原因を確認後、counter sidecar付き・全op43・時刻範囲内のliteral rootを明示するprivate providerを追加しました。修正版で検証し、物理実行は別ソースで各1回、同一ソース/入力の再試行0です。7つの旧entryのCUDA/MSL生成物が厳密一致し、共通portable CPU364件が成功しています。CPU単体revisionはa27f308、root修正後の生成物比較と実Metal検証が最終ソースに対応します。

`research/seal-world-target-counter-metal.py` が保存入力/出力、Git source blob、全48段階、ready snapshot、旧590の全wordをGPUなしで再監査します。証拠はportable-world-target-counter-validation.json、初回失敗はportable-world-target-counter-initial-metal.json、根因はportable-world-target-counter-root-finding.jsonです。Windowsは保存Metalの先頭32入力だけを共通short driverで検証し、下記v89で成功しました。旧590/通常4682の再実行は0です。

実物理着弾、lifesteal前後/致死着弾、通常武器/散弾/部位/召喚、skill/pending/DoT、型付きtarget条件とdamage子のcontextはまだ未接続です。counter有効入力では、この段階で未接続のdamage子、runtime条件、通常enemy field子をGPU側で拒否します。通常画面CPU・world公開無効・全変種認証0/203を維持し、効率化は必要検証後です。

Windows v89は固定61c7a884の共通short driverで新規32入力（native10/raw22）に成功しました。CPU13検査とGPU禁止の入力/native照合後、BelowNormal・JobObject/start gate・独立180秒・cleanup5秒のCUDA1回で92.359秒、exit0。input/output/native/generated fingerprintと50 API phaseがMetal基準に一致し、元checkout/service保持、GPU retry0、残存0、旧590/通常4682/旧各suite再実行0を確認しました。保存3JSON計50,092bytesをカプセルで取得し、bytes/SHA・固定Git source・CPU事前結果・全fingerprint・phaseを共通監査器で検査しました。証拠はportable-world-v89-cuda-validation.json、監査器seal-world-v89-cuda.pyです。

この10ケースのcounter bindingは固定body0/gen1です。不一致Actor/family/outcome/genの無視、明示blocked credit、death登録は検証しましたが、他Actorにbindしたcounterと実Actor poolによる着弾/死亡は今後の検証です。入力encoderの最大ID/世代テストを、全ActorのGPU動作証明には読み替えません。

実戦測定により、body/partもaddもcounter通知・同期完了子がその着弾のlifestealより先に動くことを確認しました。元のAST visit_Exprは[通知statement,元の_apply_lifesteal node]の順で挿入しており、以前の静的な読み取りが誤っていました。一方、body/partは元event.damage、addはreceiptのclipped tookをImpactに持ちます。body Impact→body lifesteal→到達part集合の全HP/死亡更新→各partのImpact/death/lifesteal、という複合順は保持する必要があります。

## 2026-10-21 実着弾のCPU契約23ケース（物理GPU接続前）

`world_target_counter_battle_cases.py` の同一fixtureを、元のfull native simulateと次のprivate入力adapterで使います。新観測器はopt-inで実際のpublish_impact、同期complete、heal_received、UID作成順、credit/expiry/dead Actorを観測します。旧53 native辞書は全て完全一致し、既存32 literal入力/native10のfingerprintも保持しました。GPUソースの変更/実行、Windows追加依頼はありません。

23実戦にはbody/add/part、HP/命中HP召喚、死亡完了/報酬なし取消、owner以外の致死着弾、期限切れ、未知ID/古い世代、遮断、散弾、skill_damage武器変更を含みます。完了子でlifestealを10%→50%へ変えるケースでは、body/addともHP500から同じ着弾で984へ回復します。bodyのImpactは968、HP50 addは50、hit-HP addは1を持ちます。部位HP50へのImpactは超過分を含む968で、body回復後のHP596.8でpart完了子が動き、part回復で1000になります。基礎攻撃0でもnative物理ダメージの下限は1です。遮断はBLOCKED Impactを発行しません。

`skill_damage`武器変更でも物理HitEventのtagはnormal/pellet/full_chargeで、canonical classify_hitのfamilyはWEAPONです。単発modeのSKILL-only counterはcredit0、WEAPON-only counterは完了します。これは式のnormal/skillや既存worldPhysicalNormal（skill_nameによる分類）と別の契約です。後者をcounter familyの代用にしてはいけません。standalone damage handlerのnormal_skill tagは別途SKILLなので、skill/pending/DoT接続時にそのcanonical分類を使います。

召喚が存在する実戦でtarget selectorは実際のaddを返すため、counter carrierがenemy sentinelを要求するnative prepareで拒否されます。実戦fixtureはtarget=bossを明記し、数えるActorはCounterSpecのadd/part等をそのまま持ちます。`portable_target_counter_program.py` は全定義のevent58とcounter carrierを共通compilerへ写像し、元のstat identityを保持します。`pack_battle` はboss sentinelを要求し、mode1 sidecarへ元の128 bindingのpart reachだけを追加します。CPU観測を入力には渡しません。

`compile-world-target-counter-battles.py` は全23入力をpending ABI7Fとして生成します。既存literal ABI7Eはmode1を拒否し、新しい物理entryはまだありません。`characterize-world-target-counter-landings.py` とnative-contract.jsonが実戦結果とliteral入力SHAを保存します。共通portable CPU368検査が成功しています。これはGPU実装済みという証拠ではありません。

次の実装は新private entryで開始し、以下を共通Slangへ接続します。
- GPU poolの着弾receiptから正確なkind/ID/gen、took/killedを捕捉し、再aimで死亡対象を読み替えないこと。
- 既存collect/latch/frame26/event58を共用し、credit→同期子→死亡登録/完了→lifestealの順を守ること。body/partは元damage、addはclipped took、武器creditは1・family WEAPONです。
- part damage/reachは射撃のcallback前に既存damageValueから捕捉し、body lifestealの後に到達part全件のHP/死亡を先に更新してから個別part callbackを回すこと。partのcore寄与は0、critとnormal/skill式は元packetのものを使います。
- 旧8entryの生成物と旧622の全出力を保持し、事前CPU検査・source固定・input/readback/evidence保存の後にMetalへ進むこと。必要な新規CUDAだけを短く検証します。

型付き子context、damage子、skill/pending/DoT、source攻撃、操作/復活、容量/長時間と全203変種認証は未完了で、public world false・通常CPU・全変種0/203を維持します。

観測器ON/OFFでも23ケース全ての戦闘出力（追加したcounter観測欄以外）が完全一致しました。致死receiptではActor poolのaliveが既にfalseでも着弾creditを配る必要があります。counterのdead Actor集合への登録はImpactと同期完了子の後です。

## 2026-10-21 実武器・部位・召喚のcounterをMetal663で実証

計算source e758630、private ABI7Fの共通Slangで、実際のActor着弾receiptから既存counter collect/latch/frame26/event58へ接続しました。body/partは元damage、addはclipped took、致死着弾も捕捉したkind/ID/generationを保持し、credit→同期完了子→死亡登録→lifestealの順で動きます。武器変更のskill式もcredit familyはWEAPONです。part damage/reachを射撃callback前に捕捉し、body回復後に全partのHP/死亡を更新してから個別callbackを回します。

Metal663入力＝完全native26実戦＋不正15＋旧622全524288word保持が成功しました。散弾・武器変更・召喚・部位・致死・世代・expiry・遮断、body+127partsを含みます。partのdirect hits/landedとextra hits/dealtを分け、unbreakable partのHP damage0とextra damage968、再出現gen3のextraリセットも一致しました。CPU369検査、旧8entryのCUDA/MSL生成物厳密一致、保存raw/Git source/全nativeのGPU禁止監査も成功しました。

初回0ae8c2dはcurrent_hp_reduceのkind8受付漏れで23実戦を拒否、次の1f07dbdは21/23一致でpartのdirect/extra会計だけ差がありました。各失敗rawを保持し、CPUで根因確認後に別ソースへ修正しています。異なるソースのMetal実行3回、同一ソース/入力retry0です。証拠はportable-world-counter-landing-validation.json、監査器seal-world-counter-landing-metal.py。新規41入力だけのMetal fingerprintとCPU26実戦照合を固定し、Windows v90を03383d90d5eda28c4eb8c15529365b33add0190e（21ファイル310092bytes）で依頼済みです。CPU18検査後、BelowNormal/JobObject/start gate/180秒/cleanup5秒で1回、通常4682と旧622の再実行0を指定しました。結果はまだ未照合です。

Windows v90のCPU18検査・41入力/native26・全67 source SHA照合とGPU呼び出し0はremote commentaryで確認しました（turn01a15b9e-ae4f-7693-9f09-9263cc3a83e0、cursor133）。CUDA実行依頼後にremote hostがunavailableとなり、実行結果と3JSONは未取得・未監査です。成功/失敗を推測しません。接続復帰後は既存検証の保存済み3JSONだけを取得し、再実行は依頼しないでください。seal-world-v90-cuda.pyとfingerprint/source manifestは保存済みです。

型付きtarget/Impact子context・runtime条件・damage子、skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全203変種認証は未完了です。未接続のcounter子はprivate受付でも拒否します。通常画面CPU・public world false・全変種認証0/203・legacy unexplained Metal14c8e2e OPEN、効率化は必要検証後です。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 counter完了子の対象条件をMetal721で実証

計算source6348577・private ABI80/context mode3で、immutable ready rowのActor型/ID/世代を完了子のイベント文脈へ接続しました。target_is_boss/add、target_state/not_target_state/target_stack、self_state/not_self_state/self_stackは既存の共通条件評価器を使います。致死addの再aim後も元addを判定し、death completionはimpactなしでもcompletion.actorを保持します。generic named子イベントは対象を継承せず、現在のaimへ戻ります。有限条件は発動時にlatch、永続条件はcounter終了後の吸血照会で再評価し、同じものにしません。敵sentinelのcounterはself_stateに含まれず、ownerのself_stackには含まれるnative契約を保持しました。

完全native49実戦＋不正9＋旧663全524288word保持＝Metal721入力が成功しました。単体374、旧9entryのCUDA/MSL生成物厳密一致、保存入力/readback/source/nativeのGPU禁止監査も成功しました。contextは既存ready bankへのpointerを32 dispatch×32 frameのGPU所有bank1096words（511080以後）へ保持し、終了時は全word 0へ復元します。数値・resident・同期子実行器の別コピーはありません。新しい共有compiler adapterは既存target_stack placeholder/name allocationを使い、旧41 literal入力はSHA完全一致です。

初回db568d3は新49/不正9成功・旧662保持でしたが、旧「unknown mode2」負例1件が新mode2と衝突しました。失敗rawを保持し、CPU診断後、mode3へ移して旧mode2拒否を保持しました。異なるソース/入力でMetal2回、同一条件retry0です。証拠はportable-world-counter-context-validation.json、監査器seal-world-counter-context-metal.py、mode-finding.jsonです。

前段Windows v90は接続復帰後に保存済み3JSON計55749bytesだけを取得し、CUDA41/native26・CPU18・source67・50 API phase・94.982143秒/実行1回・残存0・元checkout/service保持まで監査しました。v90の再実行0です。Windows v91は固定a9bb64216cce80e813a4a18e524f8b178ba6cc2c、16ファイル250508bytesの共通short driverで新規58入力/native49に成功しました。CPU23検査・GPU禁止58入力照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、100.699126秒・exit0です。保存3JSON計71270bytesだけを取得し、source/name/bytes/SHA、全input/output/native/generated fingerprint、50 API phase、元checkout/status/service保持、残存0、retry0、通常4682/旧663以下の再実行0を共通監査器で確認しました。証拠はportable-world-v91-cuda-validation.json、監査器seal-world-v91-cuda.pyです。Windows turn01a15bad-07d9-7460-8418-eb95ddd467e3はcompleted、cursor143、idle。再実行依頼は不要です。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPENを維持します。damage子/任意の敵field子、typed skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合も未解消です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 counter完了子の敵fieldをMetal783で実証

計算source4fc576c・private ABI81/mode5で、counter完了子の敵効果を既存Actor selector/resident/merge/条件/同期子へ接続しました。current selectorだけ捕捉Actorの型/ID/世代を使い、致死addから別addへ再aimしても元の死亡世代へ付与します。partの論理受取先はbodyです。generic named子とranked/nearest selectorは現在のaimを使います。def_pct・def_caster_based_pct・received_dmg_pct、current/boss/all/7種rank、同epoch refresh、有限/永続条件、expiry、part damage事前捕捉、128受取先とmarkerが見える間の128同期子を完全native52実戦で確認しました。全特殊効果の組合せ認証ではありません。

Metal783＝新52実戦＋不正10＋旧721全524288word保持が成功し、CPU379検査、旧10entry CUDA/MSL生成物厳密一致、保存input/readback/Git source/nativeのGPU禁止監査も成功しました。共通数値・stack・状態・子イベントを複製していません。case fixtureと比較器はCUDA/Metalで共用です。

初回bf9a60bは旧721/不正10を保持し、31実戦一致でした。body-only native観測にmembershipが無かったため、実際のtarget_charsの観測をopt-inで追加し、同じ保存rawをCPU再監査して51一致を確認しました。項目を無視してはいません。残る128受取先の正当な同期子列は旧4096 work上限でstatus4でした。mode5だけ512carriers×32depth＝16384の有限上限とGPU所有workカウンター（512176以後8words）を追加し、最大4106・合計4833・dispatch691・guard exit0を実測しました。旧モードの4096上限は生成物/全出力で保持しています。異なるソースでMetal2回、同一ソース/入力retry0、失敗raw保持です。

証拠はportable-world-counter-field-validation.json、監査器seal-world-counter-fields-metal.py、初回/membership-replay/finding.jsonです。Windows v92は固定9152a2a52b89cb8d3b77a94a619101a31d6942e8・15ファイル234843bytesの共通short driverで新規62入力/native52に成功しました。CPU28検査とGPU禁止62入力照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、98.870483秒・exit0でした。保存3JSON計74574bytesだけを取得し、source/name/bytes/SHA、全input/output/native/generated fingerprint、50 API phase、workカウンター、元checkout/status/service保持、残存0、retry0、通常4682/旧721以下の再実行0まで共通監査器で確認しました。証拠はportable-world-v92-cuda-validation.json、監査器seal-world-v92-cuda.pyです。Windows turn01a15bbc-c577-7da3-a1f3-f73de12eefcdはcompleted、cursor145、idle。再実行依頼は不要です。

次のtyped damage queueはGPU未接続です。CPU11実戦で、counter子は作成時に式を一度計算し、次フレーム（DT=1/60）か終了時drainで実着弾すること、致死addの子skillが後のbody aimへ着弾すること、named hit_count子（compiler wire49）が元completion targetを継承することを確認しました。ダメージの遅い対象解決と、敵fieldの捕捉対象解決を混同しないでください。

CPU11には新たなnative query scope不整合も保存しました。中立の敵field0があるだけで、body明示照会の味方runtime条件がparent completionのadd文脈からbodyへ変わり、同じchild skillが242→511になります。enemy_recipient_runtime.buffsの非empty field resource条件付きquery scopeを、typed skill受付前に解消・検証する必要があります。portable-world-counter-damage-queue-native-contract.jsonを参照。既知の永続味方HP/防御条件、hit-only max-HP rankの不整合も残っています。

通常画面CPU・public world false・全203変種認証0・legacy unexplained Metal14c8e2e OPENを維持します。typed damage/skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。
