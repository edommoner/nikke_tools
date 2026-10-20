# 対象別命中カウンターの共通実行器への接続

## 現在の状態

共有スタック/免疫/解除は別途検証済みですが、`target_hit_counter` と完了通知をprivate literal入力から共通Slangへ接続し、Metal622で検証しました。実着弾bridge・型付き対象条件を持つ子は未接続です。通常画面CPU、world公開無効、全変種認証0/203を維持します。この文書には契約と段階別の検証を記録します。literal resource/eventの成功は、実着弾bridgeや全キャラの認証を意味しません。

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

現nativeのbody/partはlifesteal処理の後に `publish_landing`、addは `BossScript.hit_add` のreceiptから `publish_impact`、続いてkilledなら `target_death` を呼びます。致死着弾も死亡登録より先にcreditを集計します。既存Slangのland/actorPoolLandだけでbody/part/addの前後関係が同一とは仮定せず、各呼出元の実測を追加します。

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

portable CPU363検査が成功しました。最初のsandbox内検査は終了確認のpsだけがPermissionErrorで失敗したため、process確認を許可した環境で全検査を再実行しています。今回GPU実行0、Windows追加依頼0です。次はこのsidecarを新private entryへ結合し、resource/epoch/dead registry/immutable ready queueと共通event58の継続frameを実装します。実武器/部位/召喚の着弾順、lifesteal後の通知、skill/pending/DoT、新Actor種、全変種認証は未完了です。

## 2026-10-21 private resource/event phase:Metal622

固定98427c0、private ABI7Eで、既存resident登録の直後へprepareを置き、GPU所有のcredit/UID/refresh epoch/expiry/done、正確なActor死亡集合、immutable ready queue、同期event58継続frameを接続しました。全readyを先にラッチし、子から戻った時にUID/epochが同じ場合だけ旧carrierを終了します。計算は既存binary64 add/min、状態登録/expiry/名前merge/通知queue/子イベントは既存実行器を使います。CUDA/Metalで別実装を持ちません。

入力97,464 words、出力524,288 words。資源512×16、ready4096×20、死亡Actor512×3、完了trace128×24を未使用領域413,712以後に配置しました。epochとentry UIDの桁あふれ、queue/traceの容量を検査します。literal actionはop43から既存tick→既存dispatchへ渡し、自律world/武器を進めません。counterのpolicy/作用時刻を全てGPU側でも検査し、disabled sidecarは全word 0を要求します。

Metal622は正常10ケース・48段階のlive数/credit/epoch/UID同一性と完了snapshot、不正22入力、以前の590入力の全出力word保持で成功しました。名前付き完了子による自己refresh、siblingsの先行latch、期限境界、fractional credit、death/cancel、owner限定、blocked明示policyを含みます。per-step resource観測はこのtableの最大2 carrierを比較するものです。全キャラ/全物理Actor/全特殊効果の認証ではありません。

初回a27f308は旧590保持とraw22拒否に成功し、新10入力は自律world rootのop24完了条件で全て受付拒否でした。失敗raw/reportを保存し、CPUで原因を確認後、counter sidecar付き・全op43・時刻範囲内のliteral rootを明示するprivate providerを追加しました。修正版で検証し、物理実行は別ソースで各1回、同一ソース/入力の再試行0です。7つの旧entryのCUDA/MSL生成物が厳密一致し、共通portable CPU364件が成功しています。CPU単体revisionはa27f308、root修正後の生成物比較と実Metal検証が最終ソースに対応します。

`research/seal-world-target-counter-metal.py` が保存入力/出力、Git source blob、全48段階、ready snapshot、旧590の全wordをGPUなしで再監査します。証拠はportable-world-target-counter-validation.json、初回失敗はportable-world-target-counter-initial-metal.json、根因はportable-world-target-counter-root-finding.jsonです。Windowsは保存Metalの先頭32入力だけを共通short driverで検証し、下記v89で成功しました。旧590/通常4682の再実行は0です。

実物理着弾、lifesteal前後/致死着弾、通常武器/散弾/部位/召喚、skill/pending/DoT、型付きtarget条件とdamage子のcontextはまだ未接続です。counter有効入力では、この段階で未接続のdamage子、runtime条件、通常enemy field子をGPU側で拒否します。通常画面CPU・world公開無効・全変種認証0/203を維持し、効率化は必要検証後です。

Windows v89は固定61c7a884の共通short driverで新規32入力（native10/raw22）に成功しました。CPU13検査とGPU禁止の入力/native照合後、BelowNormal・JobObject/start gate・独立180秒・cleanup5秒のCUDA1回で92.359秒、exit0。input/output/native/generated fingerprintと50 API phaseがMetal基準に一致し、元checkout/service保持、GPU retry0、残存0、旧590/通常4682/旧各suite再実行0を確認しました。保存3JSON計50,092bytesをカプセルで取得し、bytes/SHA・固定Git source・CPU事前結果・全fingerprint・phaseを共通監査器で検査しました。証拠はportable-world-v89-cuda-validation.json、監査器seal-world-v89-cuda.pyです。

この10ケースのcounter bindingは固定body0/gen1です。不一致Actor/family/outcome/genの無視、明示blocked credit、death登録は検証しましたが、他Actorにbindしたcounterと実Actor poolによる着弾/死亡は今後の検証です。入力encoderの最大ID/世代テストを、全ActorのGPU動作証明には読み替えません。

次の着弾bridgeでは順序を分ける必要があります。実CPUソースの_land_boss/_land_targetはlifesteal直後にpublish_landingを挿入します。一方、addはBossScript.hit_add内のreceipt callbackでpublish_impact/deathを通知し、その呼出しが返った後に_landがlifestealします。addのcounter完了子は同じ着弾のlifestealより先に動きます。body/partは元event.damage、addはreceiptのclipped tookをImpactに持つため、共通landの一律な後処理へ接続するだけでは一致しません。次のCPU実戦witnessとGPU fixtureでこの差を固定してください。
