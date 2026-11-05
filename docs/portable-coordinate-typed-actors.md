# 型付き照準から現在対象ダメージへの接続

`coordinate-typed-actor-common` は元Reiの完全5人編成・全73定義・武器・成長を保持するCPU契約4件。追加スキルや射撃scheduleを作らず、元 `선두 제압 2` の `hit_count:100`／`enemies_nearest_in_range` を実発動させる。1秒対照は0回、12秒のBODY／ADD／手動typed＋ADDは各5回。実着弾packetと元skill traceの時刻・量・件数を照合し、ADDの実選択も受動観測する。単体BODY戦は選択関数を呼ばず直接着弾するため、関数呼び出し回数を発動証拠の代用にしない。

宣言 `typed_actor_policy={"mode":"canonical-current-damage-v1"}` がある場合だけ、通常の現在対象damageを元のcanonical敵選択器へ渡す。型付き形状は物理迎撃先であり、通常スキルの論理敵IDとは分ける。typed名を狙うと元の `_aim_enemy` はBODYを返し、ADDの自動照準では実際の先頭生存ADDを返す。型付き対象に新たなゲーム上の所有者を仮定する規則ではない。ゲーム規則／全キャラ認定は別に残る。

policy無しの旧CPU gap契約は維持する。現在対象の敵buff／状態変更／所有権継承は新policyでも拒否し、元定義を削って通さない。型付きevent内のtarget条件にも既存の未対応guardを残す。別caller・世代・移動形状・typed skill interception等の全variantをこの4件で認定しない。

## 共通GPU経路

sealed suite `coordinate-typed-actor` は旧59を全保持し、新4正例と4入力拒否を加えた67入力（native40／拒否27）。CUDA／Metalで同じ `world_coordinate_typed_actor_entry.slang` と比較器を使う。typed header15=1を明示し、13=weapon、14=frame aim、11=live aimを要求する。入力115680／出力2032000word、Runtime138952byteとarena所有は変更しない。

通常のcurrent damageが型付き命中／破壊通知から実行される場合、物理handleを敵recipientへ流用せず、既存のcaster aimによる論理敵を読む。物理counterの種別・世代は保持する。前frameのBODY照準中にADDが現れた場合も元の現在敵選択へ追従する。既存BODY／canonical／core／typed／ADDの9bit照準namespaceはそのまま使う。

CPU compilerとnative登録時に同じpolicy validatorを使う。共有Slangにも現在対象の敵fieldを未対応として拒否する検査を置く。旧source監査はfull hashの既知inverseだけを追加し、数値正本・binary64・strict normalizer・CUDA compile cache本体は変更しない。新sourceの生成cacheとPSOは別identityで検査し、旧cache成功を流用しない。

M5で全67入力が一致し、別GPU禁止childの全40 native再計算を含むfresh独立監査223.096秒でも一致した。実GPU4.069825秒／新PSO94.331620秒、生成cache必須hit・実行時Slang0。GPU実行1回、retry0。旧59全479552000byteと入力／native指紋を保持した。現CUDA実行・新shaderのwarm PSOは未取得。

最終パッケージ `/tmp/nikke-typed-actor-final-v1.zip`（959199e6…）はseal登録とscoped分類だけの変更。全native producer・テスト・データ・GPU／数値／transportのbyteと全67入力を実行版へ固定し、同じfresh独立監査を再利用した。最終版を再計算したCPU preflightとは主張しない。関連84／制御488成功（Windows専用1skip）、最終生成cache必須hit・Slang0。正しいADDのアドレスへ着弾先を差し替える負例、量／着弾時刻の1ULP差、source row改変もすべて拒否した。証拠は `research/typed-actor-evidence/` と `research/portable-coordinate-typed-actor-checkpoint.json`。
