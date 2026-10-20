# 対象別命中カウンターの共通実行器への接続

## 現在の状態

共有スタック/免疫/解除は別途検証済みですが、`target_hit_counter` と完了通知の共通Slang接続はまだありません。通常画面CPU、world公開無効、全変種認証0/203を維持します。この文書は移植前に実装上の契約を固定するもので、GPU対応の証拠ではありません。

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
