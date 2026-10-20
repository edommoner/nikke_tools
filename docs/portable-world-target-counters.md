# 対象別命中カウンターの共通実行器への接続

## 現在の状態

共通Slangのtarget_hit_counter resource/event、実武器/body/part/addの着弾、完了子の型付き対象条件をprivate ABI80へ接続し、Metal721で実証しました。CPU374、旧9entry生成厳密一致、旧663全出力保持が成功しています。前段CUDA41も監査済みです。今回のCUDA58は依頼済みで結果待ちです。damage子/任意の敵field子とskill/pending/DoTは未接続です。通常画面CPU、world公開無効、全変種認証0/203を維持します。以下の段階別記録では、最新の実証範囲と過去の未実装状態を区別してください。

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

前段Windows v90は接続復帰後に保存済み3JSON計55749bytesだけを取得し、CUDA41/native26・CPU18・source67・50 API phase・94.982143秒/実行1回・残存0・元checkout/service保持まで監査しました。v90の再実行0です。今回のWindows v91は固定a9bb64216cce80e813a4a18e524f8b178ba6cc2c、16ファイル250508bytesで新規58入力/native49のみ依頼済みです。CPU23検査後、BelowNormal/JobObject/start gate/180秒/cleanup5秒の1回、通常4682と旧663以下の再実行0を指定しています。v91結果はまだ未照合です。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPENを維持します。damage子/任意の敵field子、typed skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合も未解消です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。
