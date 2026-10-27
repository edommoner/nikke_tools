# 元武器と敵シールド補正

`original-shield-weapons`は、`shield_dmg_pct`を持つ元4キャラ（レイ・アスカ・マリ・ミサト）を、それぞれ実編成/実武器/元全効果のまま既存`world_coordinate_typed_owner_entry.slang`へ渡す共通CUDA/Metal suite。レイ/ミサトの従来のsingle-boss実証やレイの旧座標武器実証を、全キャラの実機認定として数え直さない。今回の対象は共通座標・自動照準・明示BODY-owned敵シールドと元条件の合成である。

正例10件は4キャラの3/30秒と、マリ12秒/ミサト22秒のハイド操作。kind3のHPシールド2個は物理handleとlogical BODY ownerを区別し、`typed-before-body-v1`と`body-owned-current-fields-v1`を使う。入力115680/output2032000word、常駐Runtime138952byteは既存のまま。射撃時計/照準/MT19937/形状/発射snapshot/着弾/補正/元の状態・回復処理/比較器を再利用し、追加damage probeやCPU計算済み発火scheduleは入れない。

意味契約はレイ本人700.5%、アスカ本人601.01%、マリの元full_charge_fire後の全体100.09%、ミサトの元射撃回数状態に連動する全体150%。固定seed/元育成での値であり、全skill levelを検査したという意味ではない。3秒ミサトは約2.52秒から一部の実着弾に補正が現れ、全員の発動後射撃は長時間caseで検査する。マリは2～8秒、ミサトは7～15秒に本人がハイドし、他の味方が撃ち続ける間に補正が失効し、本人の復帰後に元条件で再発動することを要求する。

操作は既存`portable_declared_manual_sequences.apply`を元input identity検査後に適用する。元effect/owner/武器/育成/configは保持するが、操作を変更したcaseの`original_controls_preserved`はFalseとして明示し、元操作を一切変えなかったとは記録しない。別timer/別buff処理/別target poolは作らない。

raw拒否5件はowner marker/actor policy/owner generation/無効modifier axis/未使用定義axis。全battle・乱数・照準stream・typed state・物理receipt・予約領域を既存比較器で比較する。レイ30秒は2,457実着弾を持ち、先頭2,048保持に加え全streamSHA256を比較する。live run内だけ既存ParentOraclesでnative値とcreation-index contextを再利用し、別fresh GPU禁止sealは全nativeを新たに計算する。

固定53ca72b3/packageaba59d6b…の15入力がApple M5 Metal全比較と別fresh GPU禁止sealに成功。86unit/CPU事前照合128.25秒/実GPU3.81635秒/必須cache hitのPSO0.00294秒/独立照合149.61秒。全9,237物理receiptを比較し、live run内のnative/creation-index context再利用は10件、比較時の追加native計算は0、独立sealは全件fresh。GPU1回/retry0、生成cacheは必須hit/Slang0。前回projectile suiteと生成CUDA/MSLの全byteが同じで、406 GPUファイルも前checkpointから不変。旧全suiteの現在source再認定とは区別する。証跡 `research/target-count-query-evidence/metal-original-shield-weapons-v1.json`。

通常の`package --suite original-shield-weapons`はsealed goldenを使う。`original-shield-weapons-cache-only`は同じscript/source/golden/input/nativeのCUBIN/O1必須＋paired generation必須経路。cache不在をcold compileへfallbackしない。Windows新規依頼/再送/追加pollは0で、前回のhost unavailableを終端扱いにしていない。実CUDA/CUBIN hitは未検証。4carrierという範囲はpinned parsed_skills.jsonを使うcatalog検査で固定し、この依存はpackage前のAUDIT_FILES検査にも登録する。

残る範囲はcanonical敵target-world、kind/owner/geometryの任意編成への受付、実機との一致、全分岐/全育成/全キャラ認定、公開GPU admission。宣言したシールドの等価実行と、これらの認定を分ける。
