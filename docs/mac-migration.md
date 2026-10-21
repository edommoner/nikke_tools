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

# MacBookへの開発環境の移行

## 2026-10-21 counter完了子の敵fieldをMetal783で実証

計算source4fc576c・private ABI81/mode5で、counter完了子の敵効果を既存Actor selector/resident/merge/条件/同期子へ接続しました。current selectorだけ捕捉Actorの型/ID/世代を使い、致死addから別addへ再aimしても元の死亡世代へ付与します。partの論理受取先はbodyです。generic named子とranked/nearest selectorは現在のaimを使います。def_pct・def_caster_based_pct・received_dmg_pct、current/boss/all/7種rank、同epoch refresh、有限/永続条件、expiry、part damage事前捕捉、128受取先とmarkerが見える間の128同期子を完全native52実戦で確認しました。全特殊効果の組合せ認証ではありません。

Metal783＝新52実戦＋不正10＋旧721全524288word保持が成功し、CPU379検査、旧10entry CUDA/MSL生成物厳密一致、保存input/readback/Git source/nativeのGPU禁止監査も成功しました。共通数値・stack・状態・子イベントを複製していません。case fixtureと比較器はCUDA/Metalで共用です。

初回bf9a60bは旧721/不正10を保持し、31実戦一致でした。body-only native観測にmembershipが無かったため、実際のtarget_charsの観測をopt-inで追加し、同じ保存rawをCPU再監査して51一致を確認しました。項目を無視してはいません。残る128受取先の正当な同期子列は旧4096 work上限でstatus4でした。mode5だけ512carriers×32depth＝16384の有限上限とGPU所有workカウンター（512176以後8words）を追加し、最大4106・合計4833・dispatch691・guard exit0を実測しました。旧モードの4096上限は生成物/全出力で保持しています。異なるソースでMetal2回、同一ソース/入力retry0、失敗raw保持です。

証拠はportable-world-counter-field-validation.json、監査器seal-world-counter-fields-metal.py、初回/membership-replay/finding.jsonです。Windows v92は固定9152a2a52b89cb8d3b77a94a619101a31d6942e8・15ファイル234843bytesの共通short driverで新規62入力/native52に成功しました。CPU28検査とGPU禁止62入力照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、98.870483秒・exit0でした。保存3JSON計74574bytesだけを取得し、source/name/bytes/SHA、全input/output/native/generated fingerprint、50 API phase、workカウンター、元checkout/status/service保持、残存0、retry0、通常4682/旧721以下の再実行0まで共通監査器で確認しました。証拠はportable-world-v92-cuda-validation.json、監査器seal-world-v92-cuda.pyです。Windows turn01a15bbc-c577-7da3-a1f3-f73de12eefcdはcompleted、cursor145、idle。再実行依頼は不要です。

次のtyped damage queueはGPU未接続です。CPU11実戦で、counter子は作成時に式を一度計算し、次フレーム（DT=1/60）か終了時drainで実着弾すること、致死addの子skillが後のbody aimへ着弾すること、named hit_count子（compiler wire49）が元completion targetを継承することを確認しました。ダメージの遅い対象解決と、敵fieldの捕捉対象解決を混同しないでください。

CPU11には新たなnative query scope不整合も保存しました。中立の敵field0があるだけで、body明示照会の味方runtime条件がparent completionのadd文脈からbodyへ変わり、同じchild skillが242→511になります。enemy_recipient_runtime.buffsの非empty field resource条件付きquery scopeを、typed skill受付前に解消・検証する必要があります。portable-world-counter-damage-queue-native-contract.jsonを参照。既知の永続味方HP/防御条件、hit-only max-HP rankの不整合も残っています。

通常画面CPU・public world false・全203変種認証0・legacy unexplained Metal14c8e2e OPENを維持します。typed damage/skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 counter完了子の対象条件をMetal721で実証

計算source6348577・private ABI80/context mode3で、immutable ready rowのActor型/ID/世代を完了子のイベント文脈へ接続しました。target_is_boss/add、target_state/not_target_state/target_stack、self_state/not_self_state/self_stackは既存の共通条件評価器を使います。致死addの再aim後も元addを判定し、death completionはimpactなしでもcompletion.actorを保持します。generic named子イベントは対象を継承せず、現在のaimへ戻ります。有限条件は発動時にlatch、永続条件はcounter終了後の吸血照会で再評価し、同じものにしません。敵sentinelのcounterはself_stateに含まれず、ownerのself_stackには含まれるnative契約を保持しました。

完全native49実戦＋不正9＋旧663全524288word保持＝Metal721入力が成功しました。単体374、旧9entryのCUDA/MSL生成物厳密一致、保存入力/readback/source/nativeのGPU禁止監査も成功しました。contextは既存ready bankへのpointerを32 dispatch×32 frameのGPU所有bank1096words（511080以後）へ保持し、終了時は全word 0へ復元します。数値・resident・同期子実行器の別コピーはありません。新しい共有compiler adapterは既存target_stack placeholder/name allocationを使い、旧41 literal入力はSHA完全一致です。

初回db568d3は新49/不正9成功・旧662保持でしたが、旧「unknown mode2」負例1件が新mode2と衝突しました。失敗rawを保持し、CPU診断後、mode3へ移して旧mode2拒否を保持しました。異なるソース/入力でMetal2回、同一条件retry0です。証拠はportable-world-counter-context-validation.json、監査器seal-world-counter-context-metal.py、mode-finding.jsonです。

前段Windows v90は接続復帰後に保存済み3JSON計55749bytesだけを取得し、CUDA41/native26・CPU18・source67・50 API phase・94.982143秒/実行1回・残存0・元checkout/service保持まで監査しました。v90の再実行0です。Windows v91は固定a9bb64216cce80e813a4a18e524f8b178ba6cc2c、16ファイル250508bytesの共通short driverで新規58入力/native49に成功しました。CPU23検査・GPU禁止58入力照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、100.699126秒・exit0です。保存3JSON計71270bytesだけを取得し、source/name/bytes/SHA、全input/output/native/generated fingerprint、50 API phase、元checkout/status/service保持、残存0、retry0、通常4682/旧663以下の再実行0を共通監査器で確認しました。証拠はportable-world-v91-cuda-validation.json、監査器seal-world-v91-cuda.pyです。Windows turn01a15bad-07d9-7460-8418-eb95ddd467e3はcompleted、cursor143、idle。再実行依頼は不要です。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPENを維持します。damage子/任意の敵field子、typed skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合も未解消です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 実武器・部位・召喚のcounterをMetal663で実証

計算source e758630、private ABI7Fの共通Slangで、実際のActor着弾receiptから既存counter collect/latch/frame26/event58へ接続しました。body/partは元damage、addはclipped took、致死着弾も捕捉したkind/ID/generationを保持し、credit→同期完了子→死亡登録→lifestealの順で動きます。武器変更のskill式もcredit familyはWEAPONです。part damage/reachを射撃callback前に捕捉し、body回復後に全partのHP/死亡を更新してから個別callbackを回します。

Metal663入力＝完全native26実戦＋不正15＋旧622全524288word保持が成功しました。散弾・武器変更・召喚・部位・致死・世代・expiry・遮断、body+127partsを含みます。partのdirect hits/landedとextra hits/dealtを分け、unbreakable partのHP damage0とextra damage968、再出現gen3のextraリセットも一致しました。CPU369検査、旧8entryのCUDA/MSL生成物厳密一致、保存raw/Git source/全nativeのGPU禁止監査も成功しました。

初回0ae8c2dはcurrent_hp_reduceのkind8受付漏れで23実戦を拒否、次の1f07dbdは21/23一致でpartのdirect/extra会計だけ差がありました。各失敗rawを保持し、CPUで根因確認後に別ソースへ修正しています。異なるソースのMetal実行3回、同一ソース/入力retry0です。証拠はportable-world-counter-landing-validation.json、監査器seal-world-counter-landing-metal.py。新規41入力だけのMetal fingerprintとCPU26実戦照合を固定し、Windows v90を03383d90d5eda28c4eb8c15529365b33add0190e（21ファイル310092bytes）で依頼済みです。CPU18検査後、BelowNormal/JobObject/start gate/180秒/cleanup5秒で1回、通常4682と旧622の再実行0を指定しました。結果はまだ未照合です。

Windows v90のCPU18検査・41入力/native26・全67 source SHA照合とGPU呼び出し0はremote commentaryで確認しました（turn01a15b9e-ae4f-7693-9f09-9263cc3a83e0、cursor133）。CUDA実行依頼後にremote hostがunavailableとなり、実行結果と3JSONは未取得・未監査です。成功/失敗を推測しません。接続復帰後は既存検証の保存済み3JSONだけを取得し、再実行は依頼しないでください。seal-world-v90-cuda.pyとfingerprint/source manifestは保存済みです。

型付きtarget/Impact子context・runtime条件・damage子、skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全203変種認証は未完了です。未接続のcounter子はprivate受付でも拒否します。通常画面CPU・public world false・全変種認証0/203・legacy unexplained Metal14c8e2e OPEN、効率化は必要検証後です。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 128対象・共有バフのスタック操作をMetalへ接続

実験ABI7D・計算source50522a9で、buff_stack_add/remove/init、buff_max_stack_add、debuff_stack_add/removeを共通実行器へ接続しました。対象集合と世代・免疫だけを拡張し、整数変換・符号・ゼロの既定値・有限/無限上限・期限更新・遅延通知は既存stack_runtime/stack_numericを共用します。共有バフは65対象への操作でも1個のstackだけを1回更新し、対象ごとへ分割しません。共有バフに一部免疫があっても、nativeと同じ共有stackへの影響を保持します。

Metal590入力はnative53件・拒否8件・旧529入力の全524288出力word保持で成功しました。単体356件と、通常/fields/state/mutation/recipient/statusのCUDA・MSL生成物厳密一致を確認しました。小数・正負ゼロ・正負巨大値、named/unnamedの0/1下限、無限上限、2147483647の最終許容値、参照stack、所有者の違い、共有対象・免疫・再出現、期限更新とstack_reach子通知を含みます。31bit保持域を超える結果はstatus2で拒否し、許容範囲と混同しません。GPU実行1回・再試行0です。

証拠はportable-world-actor-stack-validation.json、CPU監査器はseal-world-actor-stacks-metal.py。新規61入力/53 native参照の全fingerprintを保存し、GPU関数禁止のCPU照合も成功しました。Windows v88は固定a106e1eの共通driverで61入力/53 native参照を94.76秒、BelowNormal・180秒上限の1回で成功しました。CPU13検査・GPU禁止事前照合、全input/output/native/generated SHA、NVRTC/launch/同期/readbackの50記録をMacで監査しました。31bit超過のstatus2も一致しています。保存済み3JSON 66,312bytesを取得してbytes/SHAと固定Git sourceを照合し、元checkout/サービス保持・残存0・retry0を確認しました。証拠はportable-world-v88-cuda-validation.jsonです。通常4682・旧529全件の再実行はありません。target_hit_counterと完了/死亡/refresh epoch、skill/pending/DoT、mixed target、source攻撃/interrupt、操作/復活、容量/全203認証は未完了で、通常画面CPU・world公開無効・全変種認証0/203・効率化未開始を維持します。


## 2026-10-21 128対象の免疫・回数プール・解除をMetalへ接続

計算source0873bd9・実験ABI7Cで、既存status_runtimeの免疫走査・容量最大・使用数加算・再補充・解除順を共用し、対象参照と保存先を128対象へ拡張しました。通常/名前指定免疫は捕捉世代と生存を照合します。回数免疫はnativeのtarget_chars契約に従い、再出現通知中の旧世代でも実際に対象一覧から除かれるまで容量を参照します。この差は完全CPUの通知トレース3件で実測して保存しました。容量を整数へ丸めず、0.5/1.5の防御回数も一致します。

Metal529入力はnative37件・不正入力8件・旧484入力の全524288出力word保持で成功し、単体348件と通常/fields/state/mutation/recipientの生成CUDA・MSL厳密一致も確認しました。128個別プール、同名最大・別名独立、再補充、named免疫、irremovable、65対象、共有バフの部分解除、無通知での最後の受領者解除、再出現を含みます。初期コンパイラ比較はCUDAの空行1個で失敗し、読み取り式のproviderへ移して正規化を広げず回復しました。その修正までGPU実行0で、最終GPUは1回・再試行0です。

証拠はportable-world-actor-status-validation.json、CPU監査器はseal-world-actor-status-metal.py。共有受領者の新23入力と今回の45入力をまとめた68入力/56 native参照の全fingerprintを保存し、GPU関数を禁止したCPU事前照合も成功しました。Windows v87は固定f988d15の共通driverで68入力/56 native参照を94.93秒、BelowNormal・180秒上限の1回で成功しました。CPU21検査・GPU禁止事前照合、NVRTC/launch/同期/readbackの50記録、全input/output/native/generated SHAをMacで監査しました。元checkout/サービス保持・残存0・retry0です。保存済み3JSON 70,487bytesだけを取得してSHA照合し、GPU再実行0です。summaryにold484のカウンターが無いため、明示receiptの0・固定68入力command・実測launch1回から確認し、欠落や矛盾を許さないCPU負例5件と旧v83〜v86監査結果保持も確認しました。証拠はportable-world-v87-cuda-validation.jsonです。旧461/484・通常4682を全件再実行していません。スタック操作/target counter、skill/pending/DoT、mixed target、source攻撃/interrupt、操作/復活、容量/全203認証は残っており、通常画面CPU・world公開無効・全変種認証0/203・効率化未開始を維持します。


## 2026-10-21 長寿命共有受領者をMetalへ接続

実験ABI7B・計算source e7585b8で、512 residentそれぞれの128bit可変membership・捕捉generation・対象順を追加しました。単一受領者と共有受領者が同じ照会・世代照合を使い、buff_stack_initは1/65/128対象を1個のstack/期限で保持します。部分解除・全解除・死亡によるmembership解除・再出現・有限期限通知を共通実行器へ接続しています。

Metal484入力は完全native19件・不正入力4件・旧461入力の全262144出力word保持と拡張領域zeroで成功しました。CPU340件、通常／fields／state／mutationのCUDA・MSL生成物が厳密一致しました。M5のmaxBufferLength 14,302,248,960 bytesを実測し、新出力524288 words/ケース・実行全体1,015,021,568 bytesが上限内であることを確認しました。入力92336 wordsは増やしていません。GPU実行1回・再試行0です。元nativeの共有受領者も全辞書で照合しています。

保存結果のCPU監査器はseal-world-actor-recipients-metal.py、証拠はportable-world-actor-recipient-validation.json。新規23入力の全input/output/native/generated基準を保存しました。Windowsは未実行で、次の128対象免疫/解除とまとめて新規入力だけを短く検証する予定です。回数免疫用の拡張領域は確保済みですが、計算接続はまだ未実施です。通常画面CPU・world公開無効・全変種認証0/203・旧Metal差分OPEN・効率化未開始を維持します。


## 次の接続：共有受領者と免疫プール

128対象の完全native17ケースを実測し、回数免疫が対象・名前ごとの最大容量プール、buff_stack_initが1つのcarrierに1/65/128対象を共有する契約を確認しました。従来の単一受領者へ分割するとstack・通知の意味が変わるため、GPUの長寿命共有受領者領域を先に接続します。実装・Metal検証・Windows確認は未実施です。設計は `docs/portable-world-actor-status.md`、実測は `research/portable-world-actor-status-native-contract.json`。今回のGPU実行0、Windows待機中、通常CPU・全変種認証0/203を維持します。


## 2026-10-21 型付き128対象の名前指定解除（Metal／CUDA一致）

実験ABI7A・固定af7aae6で、共通resident解除処理に名前指定のglobal／味方scope／敵scopeを接続しました。敵scopeは既存128対象集合を一度だけ捕捉し、全対象の解除を終えてから既存の状態終了通知列を実行します。新しい同名バフを通知から再付与しても、終了した走査で再削除しません。世代の照合は既存actorFieldMemberを使います。効果計算の別コピーはありません。

Metal461入力で完全native30件・不正入力7件・旧424入力の全262144出力word保持が成功しました。初回は29/30件が一致し、再出現直後に旧世代の空carrierを誤って解除する差が1件ありました。失敗rawを保持し、実CPUのmutation_targetsで重複ラベル45件の旧世代除外を確認後、共通の世代照合を追加した別GPUソースで検証しています。同一ソース・入力の再試行はありません。CPU332件、通常／fields／stateのCUDA・MSL生成物が厳密一致しました。

Windows v86は固定4271202の共通driverで新規37入力（native30＋不正7）を78.29秒、BelowNormal・180秒上限の1回で成功しました。CPU事前13検査・GPU禁止37入力と30参照、NVRTC／launch／同期／readbackの50記録、全input/output/native/generated SHAをMacで監査しました。旧424・通常4682の再実行0・GPU retry0・残存検証0で元checkoutとサービスを保持しています。保存済み3JSON 56,848bytesだけを取得し、bytes／SHAと固定Git sourceを照合しました。証拠はportable-world-v86-cuda-validation.jsonです。通常画面CPU・world公開無効・全変種認証0/203です。条件付き永続味方HP/防御のCPU不整合、広域免疫/stack/counter、skill/pending/DoT、操作・復活・容量・全変種の認証と必要検証後の効率化は未完了です。証拠はportable-world-actor-mutation-validation.json、監査器はseal-world-actor-mutation-metal.pyです。


## 2026-10-21 型付き対象の名前付き状態条件（Metal／CUDA一致）

共通計算ソース8c5a09b、実験ABI79で、target_state／not_target_state／target_stack、self_state／not_self_state／self_stackを128対象のresidentへ接続しました。条件の評価対象は味方数値照会・イベント所有者・明示対象の文脈を保存復元し、死亡・期限切れの対象解除は通知の後に行います。空のenemy carrierも期限通知まで残します。通常受付CPU・world公開無効・全変種認証0/203を維持します。

Metal424入力はnative完全戦闘49件、不正入力18件、旧357入力の全262144出力word保持で成功しました。最初の実行では48/49件が一致し、1件は敵攻撃のliteral payloadが入力生成で欠落して初期拒否されました。失敗rawを保存し、共通入力packerを修正した3bf0881で変更された1入力だけ実行、同じ計算ソース・生成物・入力を持つ423blockを再利用しています。同一入力のGPU再試行0です。CPU単体324件、旧125 native辞書、通常版および前fields版のCUDA/MSL生成物の厳密一致を確認しました。

残課題として、元CPUが永続味方HP/防御効果のruntime条件を無視する実例を保存しました。今回の実験policyでは該当入力を拒否し、対応済みには数えません。旧Metal差分・広範な免疫/解除/カウンター、skill/pending/DoT、interrupt/source攻撃、操作/復活、容量と全203変種の統合も未完了です。効率化は必要な検証後です。

Windows v85は固定c9ecd4dの共通driverで新規67入力（native49＋不正18）を76.69秒、BelowNormal・180秒上限の1回で成功しました。CPU事前14検査・GPU禁止67入力と49参照、NVRTC／launch／同期／readbackの50記録、全input/output/native/generated SHAをMacで監査しました。旧357・通常4682入力の再実行0・GPU retry0・残存検証0で、元checkoutとサービスを保持しています。保存済み3JSON 61,096bytesだけを取得し、各bytes／SHAと固定Git sourceを照合しました。証拠はportable-world-v85-cuda-validation.jsonです。GitHub共有はゴール達成まで利用者が許可しています。個人設定・raw・巨大詳細は共有しません。証拠はportable-world-actor-state-validation.json、CPU監査器はseal-world-actor-state-metal.pyです。


## 2026-10-21 Metal357:128対象の敵バフと敵数条件

private ABI78の共通実行器へ、def_pct・def_caster_based_pct・received_dmg_pctの型/世代付き受取先と、敵数/target_is_boss/add条件を接続しました。発動条件と回数は1回だけ処理し、既存owned setで親の対象順・世代を固定して各受取先を既存resident executorへ渡します。計算式・保持領域・名前merge・expiry・同期子イベントは共用です。Metal357の新52実戦・raw20・旧285既存全出力保持が成功し、最終の各Actor modifierと保持領域の型/ID/世代/stack/時刻/順序までnative完全一致です。128対象・512 resident・死亡/再出現・有限latch/永続runtime敵数条件・武器変更/散弾を含み、通常CUDA/MSL生成コードの厳密一致、CPU315、旧125 native辞書保持も成功しました。

初回保持verifierは、初期化後のコマンド拒否6件でも新領域zeroを期待したため失敗しました。旧285の既存領域と新72は全成功しており、初回report/rawを残して、固定旧GPUのpool-ready markerに従う期待値へ修正し、同じ読み戻しをCPUで再監査しました。GPU retry0です。通常生成差もCPU段階で式/行位置を修正し、厳密一致と314件成功を確認後にGPUへ進みました。後続typed query入力テストを含む315件も成功しています。計算source c2425e5、証拠 `research/portable-world-actor-fields-validation.json` と各findingを参照。

Windows CUDA72も成功しました。最小18ファイル250,128 bytesを固定8be669d、`codex/cuda-world-v84-source`へ共有し、CPU11件＋GPU禁止の72入力/52 native事前照合後、BelowNormal・180秒上限の実GPU1回で72.631秒、exit0でした。全input/output/native・生成fingerprintがMetal保存基準と一致し、NVRTC/launch/sync/readbackを実測50eventsで確認しました。接続の一時失敗と別質問への応答でカプセルが未出力になりましたが、検証を再実行せず保存済み3JSON計53,844 bytesだけを取得し、固定Git blob・輸送SHA・CPU事前結果・全fingerprintをMacで再監査しました。旧285の専用countはreceiptに無いため、source固定の72-input command・transport cases72・実測kernel launch1回・actual execution1回とsummaryの0から非再実行を確認しています。旧208/通常4682/GPU retry0、残存0、元Windows作業/サービス保持、Windowsは待機中です。`research/portable-world-v84-cuda-validation.json` を参照。個人設定/raw/巨大詳細は共有せず、利用者のゴール達成までのGitHub共有許可を反映しています。

wide enemyのその他条件、immunity/cleanse/counter、skill/pending/DoT、mixed target、interrupt/source attacks、自動制御/復活、容量/長時間条件、全変種認証と必要検証後の効率化は未完了です。pure hit-HP召喚のmax-HP順位は元nativeでTypeErrorになることをCPU実証して保存し、この組み合わせはまだ受け付けません。通常画面CPU/public受付false/全変種0/203を維持します。

## 2026-10-21 Metal285: ActorのHP・命中・128対象集合

固定822c559のprivate ABI77で、召喚のHP/hit制HP・通常武器からの命中・死亡通知・GPU targets_cleared再出現、部位の超過ダメージ/score、128bitと順序/世代付き対象集合を共通landへ接続しました。Metal285は実戦native14・型付きpool/set10・raw拒否19・旧242全出力保持で成功、portable CPU309件、通常CUDA/MSL生成コードの厳密一致、保存rawと固定Git blobの再監査も成功しています。`research/portable-world-actor-pools-validation.json` を参照してください。

Windows CUDA77も成功しました。最小24ファイル301,900 bytesを固定ea1f8dd、`codex/cuda-world-v83-source`へ共有し、CPU15件・全77入力/36 native oracle/SHA事前照合後、BelowNormal・180秒上限の実GPU1回で72.917秒、exit0でした。全input/output byte・native・CUDA/MSL生成fingerprintがMetal保存出力と一致し、NVRTC/launch/sync/readbackを実測50eventsで確認しました。3JSON計56,595 bytesを既存接続で取得し、固定Git blob・全SHA・事前検査・イベント順をMacで再監査しました。通常4682/旧208再実行0、GPU retry0、残存0、元Windows作業/サービス保持、Windowsは待機中です。証拠は `research/portable-world-v83-cuda-validation.json`。利用者はこのゴール達成までのGitHub共有を許可済みで、個人設定/raw/巨大詳細は送っていません。

wide enemy効果・skill/pending/DoT・Actor-bound callback・interrupt・召喚自身の攻撃/自爆・dynamic control/復活・全変種認証・必要検証後の効率化は未完了です。通常画面CPU・public world受付false・全変種認証0/203を維持します。

## 2026-10-21 128枠Actor識別を共通フレームへ接続

実験ABI76でbody・parts・addsの型、設定内ID、出現世代、親参照を共通worldフレームの開始／終了へ接続しました。Metal242入力でnative BossScript/ActorRegistryとの12比較、不正入力22件、以前の208全出力byte保持が成功しました。128枠・全32node・未出現・再出現・古い世代・親rootを含みます。初回237の全blockも保持し、通常CUDA/MSL生成コードはv79と厳密同一、CPU portable303件が成功しました。

最初の通常生成比較ではActor分岐による空行1つを検出しました。shellの後続処理が続いて初回237実証が行われた事実を保存し、比較規則を広げず配置を修正しました。最終242は通常生成物とCPU検査成功を確認後に実行しました。証拠は `research/portable-world-actor-registry-validation.json` と `research/portable-world-actors-metal.json`、設計は [Actor接続](portable-world-actors.md) です。

このActor実証はlifecycle/識別の範囲です。HP・命中・敵数・対象集合・interruptはまだ未接続で、完全battleやキャラ対応として数えません。次に128枠を維持して共通HPと対象集合へ接続します。新ActorのCUDAは未依頼、Windowsは前回208成功後の待機状態です。通常受付CPU・全変種認証0/203を維持します。

## 2026-10-21 共通208入力のCUDA／Metal一致

固定db8f4c8の共通実行器で、skill_damage武器モードとHeavyarms charge holdを含む208入力がCUDA／Metalで一致しました。全入力・全出力byte、125完全native／actual辞書、共有GPUソース、両生成コードのfingerprintを照合しています。WindowsはCPU11検査（終了処理5＋literal入力6）、GPU関数を禁止した全208入力生成とSHA一致の後、BelowNormal・180秒上限の実GPU1回で68.656秒、exit0でした。NVRTC・起動・同期・readbackの成功を50実測イベントで確認しました。

3JSON計96,679バイトを既存接続で取得し、各bytes／SHA、固定Git blob、事前検査、全208fingerprintとイベント順をMacで再監査しました。通常4682の再実行・GPU再試行0、元Windows作業／サービスを保持し、検証プロセス残存0です。Windowsのチャットは完了・待機状態です。共有したのはコード・ケース・小さな基準20ファイル331,359バイトだけで、rawと巨大詳細は各PCに保持します。

証拠は `research/portable-world-v82-cuda-validation.json`、`research/windows-portable-world-v82-summary.json`、`research/portable-cross-v82-receipt.json`。`research/portable_cuda_proof_audit.py` が共通のCPU証拠監査を行い、固定設定の `research/seal-world-v82-cuda.py` からGPUなしで再検証できます。通常受付CPU・全変種認証0/203を維持します。次は128枠の識別・世代・親参照を含むActorモデルと既存8対象の共通実行器の差を解消し、部位・阻止・召喚・HP／hit制HP・対象集合を接続します。混在selector、dynamic control・復活、全変種認証、必要な全検証後の効率化も未完了です。以下は段階ごとの記録です。

## 2026-10-21 Heavyarms holdのMetal208

共通実行器へHeavyarmsのvanish時charge holdを接続しました。静的な実在rosterからpolicyだけを入力にし、vanishの終了時刻・2秒上限・charge完成と期限はGPUが計算します。固定終了・終了不明・2秒の隣接値・複数vanish・再開・非camera・速度バフ失効・保持中の武器変更と再chargeの26条件を、元のHeavyarmsを含む完全native simulateと比較しました。完成後はcharge速度バフが失効してもfull latchを維持し、mode取消で完成chargeを解除します。状態領域と上限は共通schemaに集約しました。

初回206入力では、非cameraの1fixtureにcamera用ゲージ倍率300を残していた誤りを検出し、rawを保存しました。native123辞書を変えずGPU入力を100へ修正し、GPUソースと205入力の完全一致を確認して保存出力を再利用、変更1入力だけを実GPUで検証しました。その後、武器変更中の2スナップショットと共通状態schemaを追加した固定4bd848bで208入力を新規実行し、完全native125件・raw拒否34件・旧world49全出力が成功しました。旧179と途中206の全入力・全出力byte、99／123 native／actual完全辞書を保持しています。通常CUDA／MSL生成コードはv79と厳密同一、portable単体299件・旧native17辞書も成功しました。

証拠は `research/portable-world-charge-hold-validation.json`、`research/portable-world-overlay-charge-hold-metal.json`、`research/portable-world-charge-hold-expected.json`。Windowsは新規skill modeとholdを合わせた共通208入力を短く1回検証する準備中です。rawと巨大詳細は各PCのローカル保持です。通常受付CPU・全変種認証0/203を維持します。複合ally/enemy selector、Actor、dynamic control・復活、全変種認証と必要な検証後の効率化は引き続き未完了です。

## 2026-10-21 skill_damage武器モードのMetal179

実験ABI75の明示skill_damageモードを、同じダメージ式のnormal倍率・skill crit・core確率、着弾ゲート、ゲージ、弾数バフ消費へ接続しました。物理射撃の種類はcallbackによるモード終了前にGPUが保持します。初回175入力で2差分を検出し、rawを残して調査しました。元nativeの分類は、名前付き単発をスキル、pellet/core:pelletタグを名前にかかわらず通常着弾とするため、この着弾分類をスキル式・ゲージ・弾数消費から独立させました。これは現在のnative規約の保持であり、一律に全散弾をスキル扱いへ変更したものではありません。もう1件はカメラ中のcharge武器モードでfullChargeMultをゲージへ反映して解消しました。

修正版c953d3bのMetal新規179入力は全成功です。完全native simulate99件（従来70＋武器モード29）、不正入力31件、旧world49全出力を確認しました。前回CUDAまで確認済み146入力とその全出力byte、70件の完全native／actual辞書を、今回の成功・失敗両readbackから再監査して保持を確認しています。通常CUDA／MSL生成コードもv79と厳密同一、CPU状態を入力へ混入させない新規hostテスト4件を含む共通portable単体297件が成功しました。

証拠は `research/portable-world-skill-mode-validation.json`、`research/portable-world-overlay-skill-modes-metal.json`、`research/portable-world-skill-mode-expected.json`。`research/seal-world-skill-mode-metal.py` はGPUなしで固定ソースと全byteを再監査します。この29条件の新規CUDA実行はまだ行っていません。次の必要な短い検証へまとめます。Windows146の成功は保持し、元Windowsは待機中です。

Heavyarms固有のcharge hold、複合ally/enemy selector、Actor、dynamic control・復活、全変種認証は未完了です。通常受付CPU・全変種認証0/203を維持し、効率化は未着手です。

## 2026-10-21 CUDA／Metal146の全出力一致

固定6c8aaa5の共通overlay・shield／vanish・敵バフ解除146入力は、Windows CUDAとMac Metalの全入力・全出力byte、完全native／actual辞書、計算ソース、生成コードのfingerprintが一致しました。WindowsはCPU故障注入5件・Job Object子孫終了と、GPU呼び出しを禁止した全146入力生成／SHA照合後、BelowNormal・180秒上限のGPU実行1回で70.930秒、exit0でした。NVRTC・launch・同期・readbackの戻り値0を実測50イベントで確認しました。通常4682の再実行・GPU再試行は0、元作業・サービス保持、残存プロセス0です。

3つの結果JSON計73,073バイトを既存接続で取得し、個々のbytes／SHAと固定Git blob、CPU事前検査、全146fingerprintをMacで再監査しました。rawと巨大詳細は各PCに保持します。証拠は `research/portable-world-v81-cuda-validation.json`、`research/windows-portable-world-v81-summary.json`、`research/portable-cross-v81-receipt.json`。通常受付CPU・全変種認証0/203を維持し、次はskill_damage武器変更モードへ進みます。以下は段階ごとの履歴です。

## 2026-10-21 Metal146・敵バフ解除の整数境界

実験ABI75で防御・core・move・敵効果、shield／vanishの着弾とゲージ、休止・reload・MG冷却、敵バフ解除を共通本体へ接続しました。Metalの146入力で、元の完全simulate70件、raw拒否27件、旧world49全出力が一致しています。敵解除の初回は整数直前の2条件で丸め指定の誤りを検出し、rawを保存してゼロ方向切り捨てへ修正しました。既存35ケースの全出力byteとnative辞書、通常CUDA／MSL生成コード、旧native17辞書、共通portable単体293件も維持しています。

コード・共通fixture・fingerprintだけの22ファイル299,196バイトを固定6c8aaa5として codex/cuda-world-v81-source へ共有済みです。ユーザーは「今後githubへの共有をこのゴールを達成するまで許可します」と明示承認しました。個人設定・raw・巨大詳細は含みません。WindowsにCPU事前検査後の146入力だけをBelowNormal・180秒上限で1回依頼し、結果待ちです。通常4682を再実行しません。新overlayのCUDA成功はまだ主張しません。

通常受付CPU・全変種認証0/203は維持します。skill_damage武器変更モード、Heavyarms固有charge hold、複合ally/enemy selector、Actor、dynamic control・復活、全変種認証は未完了です。[接続契約](portable-world-overlays.md)、`research/portable-world-cleanse-validation.json` と `research/portable-world-cleanse-expected.json` を参照してください。

## 2026-10-21 world49をWindows実GPUで照合

共通フレーム・敵攻撃・対象選択・パターン通知のworld49入力は、固定86f6685でCUDAとMetalの全出力・ソース・生成コードが一致しました。通常4682入力は実行済みv79の保存結果を再利用し、全入力・全出力・CPU比較項目も一致しています。通常コアのGPU再実行はありません。

WindowsはCPU一時領域の権限と隔離checkoutの参照不足をGPU起動前に検出し、失敗記録を保持して環境を修正しました。CPU故障注入5件・Job Object子孫終了・GPU関数を禁止した49入力生成と全SHA一致を先に確認後、worldだけをBelowNormal・独立180秒上限で1回実行し、61.139秒で成功しました。NVRTC・launch・同期・readbackの戻り値0を実測JSONLで確認し、結果8ファイルのbytes／SHAとMac基準を照合しました。元作業・既存サービスを保持、残存検証0です。

追加5ファイルの共有と現在のゴール中の共有・検証について利用者の包括承認を受けています。個人設定とrawは送信しません。通常画面CPU・全変種認証0/203を維持します。別worktreeの実験ABI75 overlayはこの認証に含めません。証拠は `research/portable-world-v80-cuda-validation.json` です。

## 2026-10-21 共通本体への統合とパターン通知

別コピーの実行器を廃止し、通常ABI73と実験world ABI74が同じevent／combat／protection／target計算を使う構成へ戻しました。計算ソース15bcbfeの0秒修正とパターン開始／終了通知を、検証後に元ツリーへ統合しました。通常受付と通常画面はCPUのままです。

通常版の固定ソース4c07f45はMac全52検査・単体286件・Node4件・実編成158条件を通過しました。通知接続版も通常4682入力をMetalで実行し、全出力・全CPU比較項目が一致しました。新しいworld版は38成功条件・2容量拒否・34不正入力、旧4682入力の全出力保持、単体288件を確認しました。初期0秒を二重に処理する追加境界差は失敗rawを保持し、別ソースで4回帰条件を通して解消しました。旧原因未特定Metal差分は未解決のままです。

Windowsの短い検証用に、個別実証済みworld49入力を同じ1セッションへまとめ、Metalで全byte一致を確認しました。通常4682入力とworld49入力の全出力・全CPU参照・ソース・生成コードを比較する基準は約44KBです。許可済みの最小42ファイルを固定6f54193としてGitHubへ共有し、Windows v79をBelowNormal・全体180秒上限で1回実行しました。通常4682入力は141.942秒で成功し、Macで全入力・全出力・CPU参照・共通ソース・生成コードのfingerprint一致を確認しました。続くworld49入力は全体上限で終了し、readbackとevidenceがありません。GPU投入段階は不明のためCUDA未検証を維持します。保存済み4ファイルを既存接続で取得してbyte数とSHAを照合し、GPU再実行0・残存検証0・元Windows作業とサービスの保持を確認しました。効率測定は未実施、worldを含む両GPUの完了版はまだありません。通常版の前回完了ソースは7357045です。`research/portable-cross-v79-partial-validation.json`を参照してください。

世界overlay・debuff／継続被弾・部位・召喚・操作・復活・通常画面・全変種の接続は未完了で、全変種認証0/203を維持します。[共通通知と証拠](portable-world-notices.md)、`research/portable-world-notices-validation.json` と `research/portable-world-provider-global-validation.json` を参照してください。以下は段階ごとの履歴です。

## 2026-10-21 共通フレームから敵攻撃への接続を別コピーで検証

GPUのフレーム時計→敵スケジューラー→既存の対象選択・保護・分配・HP・通知へ接続しました。20成功条件で元の完全なsimulateと全比較項目が一致し、別の2容量超過も拒否できました。72発・同時512発、624語を跨ぐ乱数、装填中の遮蔽物、戦闘不能での射撃停止、終了通知と順位選択の順序を含みます。旧4682入力の全出力ワードも保持し、新規不正入力25件・単体285件が成功しています。

本体はまだ7357045／ABI73で、別コピーの仮ABI74を通常受付へは開いていません。世界overlay・パターン通知・debuff／継続被弾・部位・召喚・操作・復活などの接続を続けます。Windowsと効率測定は未実施です。[接続順・失敗記録・証拠・残作業](portable-world-frame-design.md)を参照してください。通常画面CPU・全変種認証0/203を維持します。


## 2026-10-21 敵世界スケジューラーの共通部品をMetalで検証

最後の本体認証は下記の `7357045` です。次の共通スケジューラーは87グラフ・22不正入力をM5で検証し、元CPUの終了履歴・分岐消費・繰り返し・開始／終了／発射順・フレーム状態が一致しました。逆順32段の連鎖、終了理由の優先、同時1000発、EPSの隣接値、180秒時計、容量あふれを含みます。入力生成の単体4件も成功しました。入力・全readbackと最初の全展開JSONを保持し、同一GPUコードの保存出力で再照合しています。実GPU実行は1回です。

実編成の敵世界受付、共通フレームへの攻撃接続、overlay・効果・召喚体・操作・復活はまだ未完了です。cleared maskは部品検証の手動刺激で、本体ではGPUの対象HP／世代から求めます。Windowsと効率測定は本体接続と必要な全検証まで待ちます。[設計・証拠・次の接続点](portable-world-schedule-design.md)を参照してください。通常画面CPU・全変種認証0/203を維持します。


## 2026-10-21 敵対象選択・整数RNGと最適化を両GPUで照合

固定ソース `782a13c`、ABI `0x50455673`。挑発・ステルス・敵の対象選択（全員／指定枠／乱数／攻撃力順）とCPython整数seed互換MT19937を共通Slangへ接続しました。対象と順序はGPUで決め、既存の受撃・分配・通知へ渡します。対象選択は敵攻撃のsourceTimeとHP同期後に実行します。入力86016／出力159744 wordsは維持しています。seedはuint64整数または正規10進文字列を受け付け、HTTPで不正確な大整数JSON数値を拒否します。

Metal／CUDA全4,682入力（4,112正例・570拒否）の入力・全出力・展開結果・CPU回帰・限定正規化した生成CUDA／MSLが一致しました。旧4,070入力と導入時4,658入力も保持しています。敵対象のCPU回帰548件、同名武器変更と敵バフ24件、624語のRNG更新を跨ぐ2件を含みます。有限最大HPのCPU同期を直し、既知差分3件を完全一致の検査へ戻しました。

Mac全52検査・Python単体278件・Node4件・実編成158条件が成功しました。156条件は既存CPU観測項目と完全一致し、ベクハク2条件の従来HP差分だけを厳密に保持しています。旧136条件の観測結果と全158条件の入出力ブロックを保持しました。実射撃80件・条件付きHP20件と大整数seedのHTTP経路はMacでの追加検証です。

Windows v77はBelowNormal・180秒上限のGPU1回、145.904秒で成功しました。許可済み結果2ファイル（52,532,755 bytes）をGit `7f31876` から取得し、親・2パス・byte数・SHA・全出力を照合済みです。元の作業とサービスを保持し、残存検証0、転送目的のGPU再実行0です。

全検証と転送終了後、不要な定義展開を省く候補を別コピーで測定しました。7局所負荷×1024入力、交互順・warmup後3標本で乱数選択約7.6%・指定枠約4.5%の短縮を確認し、事前基準を満たしました。候補の4,682＋80＋20入力は全入出力一致です。採用版 `7357045` は新たなMetalコア4,682入力と実編成158条件で旧版と全入出力一致、Mac全52検査・単体278件・Node4件も成功しました。Windows v78もBelowNormal・180秒上限のGPU1回、145.193秒で成功しました。許可済み結果2ファイル（52,532,755 bytes）をGit `39fbfc4` から取得し、親・2パス・byte数・SHA・全入力・全出力・CPU回帰・限定正規化した生成CUDA／MSLを照合して採用を確定しました。元Windows作業とサービスを保持し、残存検証0、転送目的のGPU再実行0です。

事前検査79体、愛蔵品313/812条件・全4段階78体、未受付264効果です。全変種認証0/203・通常画面CPUを維持します。一般の敵世界スケジューラー、操作・復活、残る効果は未接続です。以前の原因未特定Metal差分も未解決です。最適化版の証拠は `research/portable-enemy-target-scalar-broad-validation.json`、`research/portable-enemy-target-scalar-transfer-completed.json`、`research/portable-enemy-target-scalar-adoption.json`。基準版の記録も保持しています。[対象選択の契約](portable-taunt-design.md)を参照してください。


## 2026-10-20 HP由来攻撃力・武器変更待機・保留バースト参照倍率

固定ソース `39bce8a`（計算本体 `f2e250c`）、ABI `0x50455672`。`atk_from_hp_pct`、条件付き武器変更の進入待機、保留B3の全バースト時の参照倍率を共通Slangへ接続しました。入力86016／出力159744 wordsを維持し、CPUの戦闘経過をGPUへ渡していません。

Metal／CUDAの全4070入力（3540正例・530拒否）が成功し、入力・全出力ワード・展開結果・CPU回帰と限定正規化した生成CUDA／MSLが一致しました。旧3539入力では有効ABI71→72だけを変更し、意図的な不正ABI70・他の入力・全出力・CPU回帰を保持しています。HP由来185正例・23拒否、待機400正例・11拒否、保留倍率120正例を共通テストへ収録しました。

Mac全47検査・単体263件・実編成136条件・既存HTTP APIが成功しました。旧134成功条件を保持し、以前拒否されたラプラスの通常／成長180秒も検証しました。134条件はCPU観測項目と完全一致、ベクハク2条件だけは従来のHP限定契約を固定値で検査します。別の実射撃80例・条件付きHP20例はMacで検証した範囲です。今回専用のAPIケースを追加したとは扱いません。

Windows v76はBelowNormal・150秒上限のGPU1回、133.46秒で成功しました。利用者が許可した結果2ファイル（42,173,583 bytes）をGit `8eee91b` から取得し、親・2パス・byte数・SHA・全出力を照合しました。元作業・既存サービスを保持、残存検証0、転送のGPU再実行0です。コードと前段記録も個別許可を受けて固定39bce8aまで共有しました。

全検証・Windows転送・残存検証0を確認後、HP基準値の再利用候補を別コピーで測定しました。基準・候補の4070＋実射撃80＋条件付きHP20入力は全入出力が一致しました。7負荷×1024入力、交互順・warmup後3標本では採用基準を満たさず、候補を不採用として検証済み本体を維持しました。CUDA速度・実編成全体・物理ピークメモリの改善は主張しません。以前からの原因未特定Metal差分は未解決のまま保持します。事前検査68体、愛蔵品269/812条件・全4段階67体、未受付294効果です。全変種認証0/203・通常画面CPUを維持します。

証拠は `research/portable-mode-entry-broad-validation.json` と `research/portable-mode-entry-transfer-completed.json`。数値設計は [HP由来攻撃力](portable-atk-from-hp-design.md)、物理時計と保留倍率は [武器変更待機](portable-mode-entry-delay-design.md) を参照してください。

## 2026-10-20 バースト充填速度・射撃中スキル係数を共通化

固定ソース `20e213b`、ABI `0x50455670`。`burst_charge_speed_pct` を共通Slangの射撃・スキル加算へ接続しました。付与者の元ゲージ基準値と初回通常命中を保持し、物理射撃内の同期スキルでは、その射撃中の武器係数を使います。スキルのゲージ用バフは名前付き通知前に取得した値を保持します。入力86016／出力159744 wordsを維持し、CPUの戦闘経過をGPUへ渡していません。

新310正例・71拒否を共通化し、Metal／CUDAの全3331入力（2835正例・496拒否）が成功しました。旧2950入力のABI以外の入力・全出力と、初期版3231入力の全出力を保持しています。Windows v75はBelowNormal・120秒上限の実GPU1回、110.52秒で終了。許可済み2ファイルをGit経由で取得し、親コミット・パス・byte数・SHA・全入力・全出力・展開結果・CPU回帰・限定正規化した生成CUDA／MSLを照合しました。元Windows作業とサービスを保持、残存検証0、転送のGPU再実行0です。旧版v74も短い1回を実行しましたが、修正版の認証根拠には使いません。

Mac全41ゲート・単体254件・実編成130条件・既存HTTP APIが成功しました。実編成128条件が既存CPU観測項目と完全一致、ベクハク2条件は従来のHP／最大HPだけの既知差分を固定値で検査します。条件付きHP20例は今回Macで実行しましたが、Windows v75の新規実行範囲は共通コア3331入力です。APIには今回専用の充填速度ケースを追加しておらず、既存経路の回帰検査です。

初期化器への履歴フィールド反映漏れと、武器変更の同期スキルがCPU28・Metal19となる未収録条件を別々に検出・修正しました。失敗入力とreadbackを保持し、後者は元simulateを使う40条件へ拡張して検証しています。以前の原因未特定Metal差分は未解決として保持し、今回の修正と混同しません。

全検証・Windows転送・プロセス終了後、ヒット数のbinary64変換を再利用する候補を別コピーで測定しました。基準・候補の3331＋HP20入力は全入出力一致です。局所5負荷×1024入力、交互順・warmup後3標本の結果と採否は `research/portable-burst-charge-efficiency-decision.json` に記録し、候補は不採用、検証済みソースを維持しました。CUDA速度・実編成全体・物理ピークメモリの改善を意味しません。

定義事前検査の候補65体、愛蔵品257/812条件・全4段階64体、未受付効果300件です。全変種認証0/203・通常画面CPUを維持します。証拠は `research/portable-burst-charge-validation.json`、[充填速度の契約](portable-burst-charge-speed-design.md)、[次のHP由来攻撃力設計](portable-atk-from-hp-design.md)を参照してください。後者はCPU基本60条件・混合順位60条件だけを調査し、GPU受付はまだ有効にしていません。

現在の確認範囲と未完了項目は[共通実行器の進捗](portable-combat-runtime.md)と `research/portable-combat-checkpoint.json` を参照してください。以下は移行開始時の手順・経緯を含み、共通Metal本体の全キャラ対応完了を示す文書ではありません。

2026-10-19にMacBook Air・Apple M5（GPU 10コア）・24GB・macOS 26.6.2 arm64を実機確認しました。CPU起動（203体）とMetal実証4ケースは成功し、`research/portable-probe-metal.json` に実GPUの結果を保存しています。移行開始時点では本体のGPU計算はCUDA専用でした。現在は共通Metal本体を部分接続しており、全キャラ対応は未完了です。MacでCPUを使う作業環境と、共通GPUコアの小さな実証を先行して整備しています。

現在の固定検証ソースは `7492d8b`、ABI `0x5045566F`。物理射撃の貫通・防御無視フラグを共通化しました。Metal全2950入力・Mac全37ゲート・単体251件・実編成126条件が成功し、2条件の既知CPU最大HP差分を別記しています。Windows v72は実GPU1回・106.87秒で全2950入力、v73は追加HP20入力だけを1回・50.30秒で確認しました。現ソースとv72の主GPU・検証ソース・入力の同一性を確認して保存結果を再利用し、全readbackも照合済みです。元Windows作業・サービスを保持し、結果共有は明示許可後に行いました。

全検証・転送後の効率化候補は散弾親子通知の負荷が約2.4%遅くなり、改善を確認できなかったため採用しません。段階0候補63体・全愛蔵品段階の候補62体、全変種認証0/203体・通常画面CPUです。初回の保存不備や原因未特定Metal差分も記録を維持しています。[最新の引き継ぎ](mac-handoff.md)と[物理フラグの規約](portable-attack-flags.md)を参照してください。

## 移行時の問題と対処

| 問題 | 現状と進め方 |
| --- | --- |
| 数値精度 | 本体はダメージ・時刻・ゲージ等に広く`double`を使用しています。Metalは`double`非対応なので、整数化・固定小数点化が妥当な部分と高精度演算が必要な部分を分類します。小さな整数の実証が通っても、本体の数値互換性の根拠にはしません。 |
| CUDA版の検証 | Macでソース生成はできますが、NVIDIA GPUでの実行確認にはWindows PCが必要です。Windowsは必要な差分だけ明示的に検証する補助環境にし、常時の自動ビルド・GPU検査は設定しません。 |
| Windowsの他作業への影響 | CUDAのコンパイルやPTXの初回JITもCPU時間を使います。低いプロセス優先度だけではGPUの他用途への無影響を保証できません。普段の編集・共通テスト・Metal開発はMacへ移し、CUDAは対象を絞った短い検証と、合意した空き時間の測定に分けます。 |
| 起動・コンパイラー | 従来の起動用`.cmd`、PowerShellセットアップ、NVRTCのWindows DLL指定はMacでそのまま使えません。計算エンジンの導入は共通Pythonへ移し、Mac/Linuxの起動時は`python3`を選びます。本体のCUDAビルド手順は依然Windows依存です。 |
| ARM64とバージョン | Apple Silicon用のPython・Node・Slangを使います。Windowsの数値比較環境はPython 3.12.14、Node 24.19.0です。Pythonはまず3.12系でそろえ、OS付属の実行環境やRosetta側と混在させないようにします。 |
| 個人データと過去版 | Gitにはブラウザー内の状態、`local-data/`、過去版の`research/ports/`等がありません。画面の「保存・書き出し」で`nikke-lab-session.json`を保存し、Macで読み込みます。保存したGPU設定はCPUに選び直します。過去版との比較が必要なら、Windows側の保存版を参照するか、必要な保存版だけ別途移します。BlaBlaLinkはMacのブラウザーでログインし直します。 |
| メモリと速度 | 現行CUDA状態は1部隊1,260,136バイトで、1,000候補の状態だけでも約1.26GBです。入力・出力・ホスト側のコピー等は別です。この配置をMetalにそのまま移すと仮定して性能や24GBでの上限を決めず、小さなバッチからMac実機で測定します。 |

## 共通実装の進め方

効果データ・命令仕様・状態管理・イベント実行・数値規約・期待値を共通にします。SlangからCUDA/MSLを生成し、GPU起動・バッファー配置・読み戻しだけをバックエンドへ分離する案を実証します。生成されたCUDA/MSLを手作業で別々に改修しません。現行のCUDA版は比較用の実装として保持します。

SlangのMetal側では型・ポインター等に制約があります。約2,700行のCUDA本体をそのまま変換できると仮定せず、グローバル状態の置き場、構造体の配置、子通知用の明示スタック、整数／高精度数値の操作を順に接続します。型の幅とバッファーの配置も、バックエンドごとの実測・反射情報で確認します。

最初の `gpu/portable_probe.slang` は次の4ケースだけを扱います。

- float32で整数を正確に表せる範囲を超えるダメージの整数演算
- 32bitを超える積と64bitの桁上がり
- 対象が再出現した後に旧世代へ向けた処理を適用しないこと
- 周期時計の再登録・解除・期限と、古い登録の拒否

入力と期待値は `tests/fixtures/portable-probe.json` に一度だけ書きます。`scripts/verify-portable-probe.py` が梱包と結果比較を共有し、Swift側にはMetalの起動・転送だけを置きます。現時点ではCUDA向けの生成確認までで、この実証のCUDA実行アダプター、本体のダメージ数式・float64規約・実編成は未接続です。Windowsで両方のソース生成と入力検査を確認しました。Metalのコンパイル・実GPU4ケースはApple M5で成功しました。本体の速度・メモリは未検証です。追加のbinary64共通コア候補と14,034ケースの実GPU検証は[数値規約](portable-numerics.md)を参照してください。

テストの記述は共通にしますが、機器固有の障害を検出するために各GPUで同じケースを実行することは必要です。CPU由来の途中状態や発射時刻をGPU入力に流用せず、仕様から作った期待値と既存の代表的な部隊検証を使います。

## Macでの最初の起動

以下はM5のMacで実行する手順です。Windows側で実行するコマンドではありません。最初にWindowsの画面の「保存・書き出し」で `nikke-lab-session.json` を保存し、Macへコピーしてください。このファイルは個人の所持・育成データを含むためGitへ追加しません。

### 1. Python・Node・Xcodeを準備

[Homebrew公式サイト](https://brew.sh/)の案内でHomebrewを導入します。すでに導入している場合は再導入不要です。M5ではApple Silicon用の`/opt/homebrew`を使います。ターミナルで次を実行します。

```sh
export PATH="/opt/homebrew/bin:$PATH"
brew install python@3.12 node@24
export PATH="/opt/homebrew/opt/node@24/bin:$PATH"
uname -m
python3.12 --version
node --version
```

`arm64`、`Python 3.12.x`、`v24.x`を確認します。Node 24はHomebrewのkeg-only formulaなのでPATHを明示します。新しいターミナルでも同じPATHが必要です。この手順ではシェルの設定ファイルを自動変更しません。

実機ではCommand Line ToolsのSwift 6.3.3と、`device.makeLibrary(source:)` による実行時コンパイルで両方のMetal実証が成功しました。`xcrun --find metal` は見つかりませんが、今回のソース実行には不要でした。オフラインのMetalコンパイルやXcodeでの解析が必要な段階では、Mac App Store等でXcodeを導入し、一度起動してライセンス確認と初期設定を完了します。通常のXcodeを`/Applications/Xcode.app`へ配置した場合、同じターミナルで次を実行します。

```sh
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodebuild -version
xcodebuild -downloadComponent metalToolchain
xcrun --find metal
swift --version
```

Xcodeを別名・別の場所に置いた場合は`DEVELOPER_DIR`をその場所に合わせます。Metal ToolchainはXcodeのSettings → Componentsからも導入できます。Xcode本体とMetal Toolchainの初期導入には時間・ディスク容量・ネットワークが必要です。

### 2. 移行用ブランチを取得

```sh
cd ~
git clone --branch codex/mac-portability https://github.com/edommoner/nikke_tools.git
cd nikke_tools
git branch --show-current
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python scripts/setup-engine.py
python scripts/check-migration.py --cpu-smoke
```

`codex/mac-portability`ブランチであることを確認します。変更はDraft PR #1にあり、mainへはまだマージしていません。プロジェクトのNode部分とPython部分は標準ライブラリーを使うため、この起動に追加の`npm install`や`pip install`は不要です。Slangのコンパイラーは次の段階で別途取得します。

起動確認のJSONは、`platform: Darwin`、`architecture: arm64`、`engine_present: true`、`cpu_catalog.passed: true`と`characters: 203`を目安にします。ここでの`passed`はCPU起動確認であり、GPU実行の成功ではありません。Metal ToolchainとSwiftの項目も確認します。

すでにMacでクローン済みなら、新たに同じ名前のフォルダーへクローンせず、そのフォルダーで`git fetch origin`、`git switch codex/mac-portability`、`git pull --ff-only`を実行します。未コミットの変更がある場合は先に内容を確認して保存します。

## 小さなMetal実証

```sh
python scripts/setup-slang.py
python scripts/build-portable-probe.py
python scripts/verify-portable-probe.py --validate-only
python scripts/verify-portable-probe.py --backend metal
```

同じターミナル・リポジトリ直下・仮想環境で順番に実行します。Slangは公式の2026.20を`.tools/`へ取得し、配布物のSHA-256を照合します。macOS arm64用とWindows用を分け、既存CUDAのインストールは更新しません。生成物は `research/portable-build/` に置き、各環境で作り直します。最後のコマンドだけがMac GPUを実行します。成功時も実証4ケースの検証であり、通常画面の詳細計算には接続されません。

`research/portable-probe-build.json` はソース生成、`portable-probe-fixtures.json` は入力の検査、`portable-probe-metal.json` はMacでの実行結果です。`gpu_execution_verified` と `production_runtime_connected` を分けて記録し、CPUフォールバックをGPU成功として扱いません。

最後の出力で`passed: true`、`gpu_execution_verified: true`、`backend: metal`、MacのGPU名、4ケースの一覧を確認します。`production_runtime_connected: false`はこの段階では正常です。`--validate-only`だけの成功はMetal実行の確認になりません。Swift／MSLが失敗した場合は診断を表示します。SwiftのキャッシュやGPUデバイスへのアクセスがサンドボックスで拒否される場合は、通常のMacターミナルで実行するか、その実行へのアクセス承認を利用します。入力検査だけへ置き換えて成功扱いにせず、実際の診断から修正します。

## 通常画面の起動と設定の復元

Metal実証を終えてから、同じターミナルで起動します。

```sh
NIKKE_PYTHON=python node server.mjs
```

ブラウザーで `http://127.0.0.1:4317` を開き、Windowsで書き出したJSONを読み込み、詳細計算はCPUを選びます。通常画面にはまだMetal詳細計算は接続されていません。サーバーはターミナルを使い続けるので、追加のコマンドは別のターミナルで実行するか、`Control+C`でサーバーを停止してから実行します。

新しいターミナルでは次の準備を行います。クローン先を変えた場合は`cd`のパスを置き換えます。

```sh
export PATH="/opt/homebrew/opt/node@24/bin:/opt/homebrew/bin:$PATH"
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
cd ~/nikke_tools
source .venv/bin/activate
```

## つまずいた場合

- `brew`・`node`・`python3.12`が見つからない：上記PATHと導入状況を確認します。
- `xcodebuild`がCommand Line Toolsを参照している：Xcodeの配置と`DEVELOPER_DIR`を確認し、Xcodeの初期設定を済ませます。
- Metal Toolchainがない：XcodeのComponentsか`xcodebuild -downloadComponent metalToolchain`で導入します。
- `Rebuild the changed portable probe first`：`python scripts/build-portable-probe.py`を再実行します。Windowsの生成物はコピーせずMacで生成します。
- Swift・MSLのエラー：ターミナルの診断と`research/migration-readiness.json`を確認します。初回実行はApple M5で成功していますが、環境ごとに診断を確認してください。
- ポート4317が使用中：既存サーバーを確認するか、`PORT=4318 NIKKE_PYTHON=python node server.mjs`として、ブラウザーも4318へ合わせます。

Macでの実行により`research/`のレポートJSONがMacの結果へ書き換わるのは正常です。個人のセッションJSON、`.venv/`、`.tools/`、キャッシュはGitへ追加しません。続きを開発する際は[引き継ぎ情報](mac-handoff.md)を先に確認してください。

## 参考

- [Slangの対応表（Metalのdouble制約を含む）](https://github.com/shader-slang/slang/blob/master/docs/target-compatibility.md)
- [Slangのポインター制約](https://docs.shader-slang.org/en/stable/external/slang/docs/language-reference/types-pointer.html)
- [公式Slang配布物](https://github.com/shader-slang/slang/releases/tag/v2026.20)
- [Apple：Xcodeの追加コンポーネント](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components)
- [Homebrew：Python 3.12](https://formulae.brew.sh/formula/python@3.12)
- [Homebrew：Node 24](https://formulae.brew.sh/formula/node@24)

## このMacでの再起動と復元済みデータ

`./Start-NikkeTools.command` でNode 24と`.venv`のPythonを選んで起動します。起動先は `http://127.0.0.1:4317` です。同じポートのサーバーを二重に起動しないでください。今回の元セッションとCPU選択・再計算後のセッションはGit対象外の `local-data/session-original.json` と `local-data/session-mac-cpu.json` に保存しました。後者を画面で読み込むと復元できます。育成データの自動永続保存は既存画面の仕様に含まれないため、再読み込み時はJSONを読み込んでください。

添付の5人・15秒設定で、CPUの現在育成は45,251,089、取り込み時育成は44,888,797でした。デモと記録された5人のセッションであり、全所持キャラのインポート件数ではありません。Pythonは3.12.15、Nodeは24.22.0で、Windowsの記録とパッチ版が異なります。
