# HP盾の実戦迎撃：共通CLIのCPU契約

投射物のMetal18実証に続き、通常native battle schedulerからHP盾へ攻撃を振り分ける明示モデルv1を追加した。共通CLI `reference --suite destructible-shield-battle`の15契約が成功した。これはCPU側の接続であり、Metal/CUDAの盾迎撃実証、ゲーム規則の認定、全キャラ対応ではない。

## 選択と量の確定

`typed_battle(..., modifier_model=True, shield_owner=BOSS)`を明示したscopeだけで有効になる。BOSSはBODY/identity0/generation1という実schedulerのboss handleで、文字列・暗黙のowner・ADD・別identity/世代は入口で拒否する。既存worldの生存HP盾から、ownerのkind/identity/generationが全て一致する最初のbinding slotを選ぶ。これはv1で宣言した優先順で、ゲーム内の重複盾の優先規則を実証したものではない。

対象は元のplain `target='boss'` damage skillだけである。通常handlerへ入る前に選択を固定し、そのhandlerが採取するbuff、named係数、weapon、DEF、crit/full-burst contextを使う。量は既存の共有CPU scalar adapterでHP_SHIELDを指定し、既存7因子・丸めにshield補正を加える。盾がない場合は元のbody scalar/landingへ戻り、盾補正をbodyへ混入させない。別owner・古いowner世代・ownerなし・投射物は迎撃対象にしない。

選択したhandleを既存`deliver`へ渡し、HP・破壊通知・target counter・同期子イベントを同じ時計で実行する。盾を破壊した発の余剰はbodyや次の盾へ流さず、次の発/子スキルが新しく選択する。bodyへの元landingはそのpacketだけ省く。新しいschedulerやCPUイベント列は作らない。scope終了・例外時にconstructor、scalar、handler、条件/target resolverを戻す。

## 固定した結果

|条件|盾へ解決した量|通常bodyの合計|
|---|---|---:|
|盾補正50%・通常物理との混在|1451/1451|3872|
|投射物補正だけ|968/968|3872|
|盾HP500・初発で破壊|初発1451から500消費、次発body968|4840|
|ownerなし/ADD owner/古いowner世代|迎撃なし|5808|
|盾HP500と5000の2つ|slot0へ500、次発slot1へ1451|3872|
|worldが0.15秒で終了|初発盾1451、次発body968|4840|
|named倍率50%|実採取係数150で2177/2177|3872|
|盾補正が0.15秒で失効|1451/968|3872|
|普通のATK damage40%との加算|1838/1838|5416|
|named完了の子スキル|親1451・子726も盾へ|0|
|破壊counterから子スキル|盾は500だけ消費、子484と次発968はbodyへ|5324|
|同じworld nodeの3回再出現|世代1/2/3へ各500消費|3872|

15契約の全件は`reference_model_gap=true`、canonical positive0、packing/build/execute0として記録する。入力に期待値やCPU攻撃列を追加していない。plain contract外のdamage_count等は、盾が不在でも拒否する。

```sh
python scripts/nikke_gpu.py reference --suite destructible-shield-battle --out NEW_REFERENCE.json
```

固定package `55bbea805a288149c0021629e8d1e217b34b88afebe0a1c4f7c7f639ccce7fb6`をfresh unpackしてCPU179検査（skip0、20群23.410秒）、既存modifier-battle18入力/native12を照合した。旧Metal保存fixtureの検査を含む。GPUソース・golden・保護CPU/compiler・binary64・strict normalizerは変更0。初期CPU開発時のpacket closure名取り違えによるNameErrorも証拠へ記録し、active contextのmanagerを使用する修正後に全検査した。

全inventoryを前段と比較し、全266profile・245packing/base185・残20分類・優先順位・全キャラ認定0・UI CPUが完全同一だった。新GPU dispatch0、Windows追加依頼0。CUDA cache/性能の改善を今回の結果から主張しない。

## 次の接続と未完了範囲

既存共有Frameの選択/量確定/receiptのproviderへ同じowner照合・slot選択・無spill・body fallbackを接続する。Frameを複製せず、旧投射物選択を既定として保持し、HP盾の新しいsource identityを明示してMetalで比較する必要がある。今回のCPU契約をGPU成功扱いにしない。

通常武器・hit盾・貫通・ADD所有盾・対象別DEF/敵debuff・元プロフィール全体・ゲーム内の重複盾優先規則は未対応。物理がbody3872のままという結果は今回のskill専用scopeを確認するもので、武器の盾迎撃が完成した証拠ではない。証拠は`research/destructible-shield-battle-evidence/manifest.json`、checkpointは`research/portable-destructible-shield-battle-native-checkpoint.json`。
