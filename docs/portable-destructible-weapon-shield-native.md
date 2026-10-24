# 通常武器の盾接続：nativeの発射snapshotを保持

共通CLI `reference --suite destructible-weapon-shield`へ22 CPU契約を追加した。実際のCharState._fire/_charge_fireとBossScript時計からHP盾/hit盾へ接続し、auto・散弾・charge・tap・武器変更・複数総口・複数射手を確認した。今回の新GPU実行は0で、武器のMetal/CUDA接続・ゲーム規則・全キャラ認定は未完了。

## 発射中のcontextを接続する

`typed_battle(..., modifier_model=True, shield_owner=BOSS, hit_shields=True, weapon_shields=True)`で明示したscopeだけが有効。既定falseで既存のplain skill/投射物経路を維持する。追加の`WeaponShots`はnativeの2発射methodを一時wrapし、caster・manager・world・timeを把握する。発射・武器状態更新・reload・係数分割・弾数・通知・gaugeは元のmethodへ任せ、別simulatorや時計は作らない。

各scalar呼出しでlive盾を選び、nativeが実際に渡したbase ATK/buffs/weapon/hit_type/DEF/expectedをそのまま共有scalar adapterへ渡す。係数Noneはその時点の実weapon.damage_coeffを採取し、charge/normal/core/explosion/武器変更のcontextを維持する。HP盾にはHP補正、hit盾には通常scalarと独立credit1を使い、既存deliver/counterへ実packetを渡す。そのpacketの元body landingだけを省く。

nativeは発射時にbuff辞書を採取し、pelletループで同じ辞書を使う。子counterが途中でATKを増やしても、残りpelletは元の辞書を使う。一方、盾の破壊状態は次pelletで再選択する。これにより同じ散弾内のHP盾→hit盾→bodyを、buffの再採取なしで扱う。scalarとHitEventのcaster/timeを照合し、次のscalarまでにpacketが届かない投影を拒否する。pendingを子の発動前に消費するため、同期子のskillは別contextで解決する。

scope終了・scalar/packet失敗時にnative method・constructor・scalar・simulate alias・BuffManagerを復元する。座標、部位/interrupt到達、明示stage aim、piercingは独自規則が未実装なので、盾なしのときも黙ってbodyへ代用しない。lifesteal/ダメージ蓄積の着弾後規則も未宣言のため、該当する登録効果を最初の1走査で拒否し、pelletごとの効果走査は増やさない。通常RLの単一body向けexplosion factorは元scalarのcontextとして検査したが、範囲選択の完成ではない。

## 22契約の主要結果

|条件|確認した結果|
|---|---|
|auto HP50%|1451×4、残4196、body0、ammo996、gauge1|
|hit容量2／HP容量500|次発bodyへ復帰、破壊した発はoverflowしない|
|3pellet HP|484×12、残4192、発射4・ammo消費4・gauge3|
|散弾のHP→hit→body|最初のHP484から300消費、次pelletはcredit1、以降body323|
|散弾のhit→HP|初pelletはcredit1、後11pelletはHP484|
|初pelletのcounter子でATK100%|同じ発は484×3を維持、次発から1021×9|
|counterのskill子|weapon family0の323とskill family1の484が別creditを消費|
|full charge／charge散弾|2902×2／968×6、通常と同じ最終残量|
|tap|full-charge factorを付けず、3発・ammo997・gauge0.75|
|通常/skill式の武器変更|normal buffの適用を元hit_typeへ従わせ、終了後は通常武器へ復帰|
|core／RL explosion charge|元contextを維持して2801／4838を解決|
|2総口|8packetでも発射/弾数は4、hit容量3で後の5packetはbodyへ|
|slot4／2射手|実casterごとの係数・buff・ammoを保持|
|ownerなし／world失効／V1 HP-only|対象がない発は元body経路と残数を維持|

22件全てをreference_model_gap、canonical positive0として記録する。packing/build/executeは禁止した参照検査であり、CPUイベント列をGPU入力へ変換しない。

```sh
python scripts/nikke_gpu.py reference --suite destructible-weapon-shield --out NEW_REFERENCE.json
```

## 固定パッケージと保持検査

package `72dcbebdadd6282975aaf9f29641e73a2ebc0071fe6ae5939efac871d992f7b5`をfresh unpackし、CPU23群198検査（skip0、41.601秒）、既存111入力/native76の基準照合が成功した。22参照契約は1.996秒。scalar/packet故障からの復元、未対応part/piercing、二重scalar投影の拒否、既定offのbody3872も検査した。

Slang153 sourceは全て不変。旧Metal111の保存fixture・goldenを再利用し、両生成のstrict指紋/reflectionはgeneration cache必須hit・追加Slang0/GPU0で保持を確認した。binary64・strict normalizer・保護CPU/compiler変更0、raw削除0。新しい武器GPU成功やCUDA実機/cache速度を主張しない。

全inventoryを前段と完全比較し、266プロフィール・245packing/base185・全issue/順位・残20分類・全キャラ認定0・通常UI CPUが全field同一。Windowsは今回も新しい観測/実行0で、直近接続不可・CUBIN O0未実施・7終了原因不明/保全falseは維持する。

## 次の共有GPU接続

既存captureWeaponShotは発射前に量を1回採取し、landWeaponPelletsの通知後、weaponFrame末尾でbody landingを処理している。HitEvent後だけの対象付け替えでは、途中の盾破壊・counter子・HP補正を再現できない。

次は同じsampleDamageFactorsの採取結果から通常量/HP盾量を確定し、nativeと同じpellet位置でtyped選択と既存receipt/counterを実行する。終了後のbody landingでは盾が受けたpelletを除き、発射/弾数/gauge/shot snapshotは既存weapon Frameへ任せる。将来のpart/interrupt、piercing、ADD owner、lifesteal/蓄積なども明示契約が必要。Frameや数値式を複製しない。

証拠は`research/destructible-weapon-shield-native-evidence/manifest.json`、checkpointは`research/portable-destructible-weapon-shield-native-checkpoint.json`。現在のMetal検証入口は引き続きsealed `destructible-hit-shield`の111入力で、武器の接続済みとは扱わない。
