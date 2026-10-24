# 投射物・HP盾補正の宣言CPU契約と容量ガード

残る最優先の`projectile_dmg_pct`と`shield_dmg_pct`について、GPUへ接続する前の明示CPUモデルv1を実装した。共通CLI `reference --suite destructible-modifier`の20件が成功。これは既存CPU正本やゲーム仕様の完成ではなく、新しい対象モデルの計算契約である。全20件をreference_model_gapのまま報告し、GPU/battle接続・in-game認定はfalseに保つ。今回の新GPU dispatchは0。

## 数値・対象契約

`app/destructible_damage_policy.py`は、既存の7因子・積の順序・最終`round`・最低1の処理を再利用する。v1の設計選択として、PROJECTILEには`projectile_dmg_pct / 100`、HP_SHIELDには`shield_dmg_pct / 100`を第5因子へ最後に加える。他の種別向け補正は加えない。既存のpart/intercept/attachment/explosionとは別軸であり、それらのstatへ代用しない。第5因子内に置く選択は宣言したモデルであり、元CPUに存在しなかったゲーム規則を実証したものではない。

|契約|期待結果|
|---|---:|
|base ATK1000・DEF100・係数100%、crit0|900|
|投射物補正+50%をPROJECTILEへ|1350|
|HP盾補正+50%をHP_SHIELDへ|1350|
|同じ補正を通常bodyへ|900|
|ATKダメージ+40%と投射物補正+50%|1710（第5因子1.9）|
|投射物補正20%と30%を別carrierから|1350|
|補正-50%／-100%|450／最低1|
|ATK3・DEF0・係数50%・補正50%|2（丸め後に掛けると3になる境界）|

ほかに異なる味方へのself補正、分隊への贈与、期限境界、条件不成立、2stackを検査した。HIT_SHIELDはcreditを消費する量であり、このHPダメージqueryへ入れる操作を拒否する。現在のqueryはbody/projectile/HP shieldだけを受け付ける。scalarの係数0に対する最低1はnativeのscalar契約であり、実スキルの係数0で発動を早期終了する規則はcallerが引き続き所有する。

## 既存状態・queryの再利用

carrierの発動、受領者、value、stack、期限、条件、source除外、plan/cacheは既存BuffManagerを使う。managerのローカルsubclassでnumeric reader2個の関数namespaceだけをcloneし、そこへ2つのstatを追加する。導入済みの敵generation/query-context wrapperはclosureの子readerだけを置き換えて保持する。グローバルmap、既存manager、base class、canonical `_factor5`/`calc_damage`を変更しない。追加数式は第5因子の対象別加算だけで、7因子全体の式を複製しない。

未知のquery wrapper、将来canonicalに追加された同名consumer、非有限入力、暗黙のactor kind、敵へ付いたoutgoing modifierは拒否する。source除外はnativeの所有者・名前規則を再利用する。scalarでoverflowが起きてもグローバル関数が変わらず、その後の通常queryが動くことも検査した。

固定package `60ef5a229d0456e5ed6778b7276895e58e1dc6500892995c64ada95f1d942b6f`をfresh unpackし、CPU159検査（skip0）と既存元定義8件のnative指紋照合が成功。20件のreferenceは別途GPU禁止下で実行し、正例昇格0/model gap20と記録した。既存実Metal44/8の保存fixture比較はCPU群で維持する。GPU152/通常147のsource closureは不変、sealed生成も必須cache hit・追加Slang0/GPU0。

```sh
python scripts/nikke_gpu.py reference --suite destructible-modifier --out NEW_REFERENCE.json
```

case表は`research/destructible_modifier_cases.py`、native observerは`research/world_destructible_modifier_native.py`、literal検査は`research/portable_destructible_modifier_contracts.py`。次は同じ表を共有Slangへ接続し、resident carrierから対象別補正を採取して既存のfactor積へ渡す。親攻撃の値固定・同期子・別種別の混在は既存Frame/receipt契約へ接続して検証する。対象別DEF、実戦binder、public admission、元プロフィール全体は別途未完了である。

## 実行前の保存容量検査

この作業ブランチにはskillが参照する`storage-check`がなかったため、既存の保存モジュールにある同種のfree-space方式を再利用し、budget限定のCLIを追加した。archival integrity検査や削除を行うコマンドではない。

```sh
python scripts/nikke_gpu.py storage-check --required-bytes 37059588
```

既定reserveは1GiB。nonnegative整数byteを要求し、空き不足なら結果を表示してexit2。`--path`で対象volume、`--reserve-bytes`で手動の観測予算を指定できる。通常runは固定1GiBを使い、`4 + 件数 × input_words × 4 + 件数 × output_words × 4`を入力作成前に検査する。CPU-only/smokeはGPU出力を確保しない。CPUゲート後・GPU claim前にも、既に作ったinputのサイズを検査し、残るreadback＋reserveを再確認する。workloadや出力幅を減らして通過させない。

実環境のfree433860608byteでは追加8入力の必要37059588byte＋reserveを満たさず、`storage.json`と元failureを残してCPU群/input/GPU claim前に停止した。失敗したcaptureは保持し、同じ8入力のGPU再実行はしていない。

## rawを削除しない容量回収

既存の`sparsify-raw`を通常492の終了済みcaptureへ再利用した。planning後にゼロ領域だけをDarwin F_PUNCHHOLEで疎ファイル化し、原ファイルの全byte・size・inode・元evidence/raw artifact SHAを再検査した。raw自体の削除・圧縮形式への変更・GPU再実行は0。

- 論理rawサイズ: 1547698176byteを維持
- 原SHA: `81097426560613d9b76ab91e30bdec3e7a2d6747dd001554cb7158ec36d5af7b`を維持
- 物理割当: 1547698176 → 440926208byte
- 回収: 1106771968byte（約1.1GB）

回収後は同じ追加8入力のbudget検査がfree1526177792byteで成功した。これは保存容量の証拠であり新しい計算証明ではない。疎ファイルを別volumeへコピーするときは、論理サイズ分の空きが必要になり得る。

全266profile・packing245/base185・残20分類のissue/順位は完全同一。ヘビーアームズの元全25定義を妨げるindex0 lock_on、index20 effect_target_count_add、index24 all_projectilesもそのまま記録する。Windowsへの新run依頼0、今回は再観測しておらず直近は接続利用不可。CUDA計算/性能・CUBIN O0実験は未確認、全キャラ認定0/UI CPU/全目標未達。

証拠は`research/destructible-modifier-design-evidence/manifest.json`、checkpointは`research/portable-destructible-modifier-design-checkpoint.json`。raw/toolchain/個人設定はGitHub共有に含めない。
