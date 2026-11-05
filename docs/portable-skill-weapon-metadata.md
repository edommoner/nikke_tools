# 自動スキルの武器注記と実編成の受付拒否

`auto_damage` の `weapon_type` は、現在の正本では効果固有の武器変更命令として使われない。
`timeline.py:_handle_damage_eff` は `cs.weapon` と `cs.base_weapon_type` を読む。
このhandlerのsourceと読取箇所を `portable_skill_weapon_contract.py` で固定し、
観測器で実際の計算器引数・命中属性・結果を追加照会なしに記録した。
単に出力差がないことだけから「意味がない」と推定していない。

共通入力検査は、`normal_attack` 型の `auto_damage` について、既知の武器種であり、
キャラの基礎武器metadataに一致する注記だけを許可する。
元の効果定義から欄を削除しない。異なる武器種、未知の種別、別のdamage familyやformula、
private combat world以外は、この拡張で受付しない。
これは現在の正本に一致する限定的なmetadata受付であり、独立武器overrideのGPU実装や
ゲーム内での意味を認定するものではない。矛盾する注記の6契約はmodel gapとして残す。

## 正本契約

合成14契約で42回の実際の計算器呼出を確認した。
AR／RL／SRの各基礎武器について、注記なし・AR・RL・SRを比較する。
注記だけを変えても元のbattleとtraceはすべて一致し、爆発倍率は基礎武器RLの場合だけ使われる。
AR→RL、RL→SRの武器モード中も記録した。モードは実際に入退出しているが、
周期スキルのhandlerが呼ばれる時点では、通常射撃のために一時変更した `cs.weapon` は復元済みである。
「モード中だから常にモード武器を使う」という別の解釈も追加していない。
get_buffs／値読取／calc_damage／random.sampleの呼出数と、元の全battle・traceを保持した。

アニス：スターを含む全83定義の実編成では、3秒で2回、30秒で77回の自動スキル計算を
正本で観測した。RL注記・RL基礎武器・RL実引数、normal／explosion属性、係数40.01を確認した。
短時間でも実際に発火している。元の注記を含む定義を削って小さな編成へ置き換えていない。

## Metal結果と未完了の原因

新10入力をMetalで実行した結果、合成8入力は既存比較器で一致したが、実編成2入力は
status64で拒否された。suite全体は `passed=false`／`calculation_verified=false` のまま。
新しいgoldenは作成・登録していない。合成一致を全10入力やキャラ全体の認定へ拡大しない。
通常実行はGPU0.0438秒、生成cache必須hit・追加Slang0。

既存の `PORTABLE_WORLD_PROJECTILE_DIAGNOSTIC` だけを別の不変packageへ有効化し、
3秒入力1件を追加観測した。通常ソースとCLI registryはpackage作成後に復元した。
診断結果はstage8000、定義index1、`스타 폴 2` の名前付き解除と
`no_burst1_ally`（wire `[32,0,0,0]`）を指した。
元の失敗・readback・claimは残し、診断を成功した計算証拠へ数えていない。

原因は `gpu/world_actor_fields.slang:actorFieldsDefinitionValid` の条件受付漏れ。
共通 `basicConditions` と正本 `_condition_ok` は、caster自身を除き、現在のburst stageを
使ってB1味方の有無を判定する。一方、actor-field tierはこの条件を許可していない。
静的packingの可否と、実際のGPU受付を別の分類として記録した。
30秒入力も拒否され、同じ定義・条件を持つが、追加診断は3秒だけである。

次の接続には、`has_burst1_ally`／`no_burst1_ally` の専用native契約を先に追加する。
自分の除外、生死とstage保持、動的stage overrideと期限切れ、条件順を確認し、
name／argumentが0であることを検査する共通受付を実装してから実編成を再検証する。
今回は期待値や条件受付を緩めていない。

## 保持と検査

最終不変packageの新規CPU5群37検査（skip0）が成功した。
単体合計6.781秒、native事前比較1.806秒。
別の不変packageで既存9群81検査も成功した。両群には重複があるため、足して固有件数としない。

通常の全GPUソース・算術・Runtime・stride・normalizer・正本CPU・旧CUDA・Windows wrapperは不変。
既存95入力（native72／拒否23）は共通CLI replayで保存結果を再利用し、独立sealも成功した。
298,844,160 bytesのraw／input／native／生成物を照合し、GPU再実行0。
新規合成の一致は、実編成の拒否と区別して残した。

静的packingは235→236／266（base176／203）、観測分類は43→42。
既存235入力SHAを全保持し、アニス：スターが新たにpacking可能になった。
これはGPU受付の成功を意味しない。上記の実行時blockerは別記録に残り、
全キャラ認定0・UI CPU・development_only・全目標未達を維持する。

主な操作は、共通CLIの `reference --suite skill-weapon`／`skill-weapon-rosters`、
`package --suite skill-weapon --develop`、`generation --develop`、`run`、`replay`、`seal`。
診断recipeは `research/skill-weapon-evidence/diagnostic-recipe.json`、
全記録は同ディレクトリと `research/portable-skill-weapon-checkpoint.json` に保存した。
Windows操作は今回0。現在sourceのCUDA実機検証、全保持、全カタログ対応は残件。
以前の7プロセス終了は原因unknown、保全確認falseのまま。
