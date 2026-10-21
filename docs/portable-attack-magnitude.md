# 名前付きATK倍率の共通実行器

canonical79 `atk_buff_mag_pct`を共通Slangへ接続しました。CUDA／Metalで同じ数値・効果・native比較を使います。GPUで新たに検証した範囲はMetalであり、最新版CUDA数値一致や全キャラ認定を意味しません。

## 数値と対象の契約

正本の`get_buffs`は、名前が一致する`atk_caster_based_pct`の基礎ATK加算だけに倍率を掛けます。各base carrierの有効性・対象・runtime条件を調べた後、対応する倍率carrierを有効な登録順に足し、`(baseAtk * (baseValue / 100)) * factor`を既存software binary64で計算します。倍率の所有者一致やruntime条件の再検査、保留ダメージの除外は行いません。通常ATK％、HP由来ATK、ATKコピー、味方ATK順位、敵被弾のflat ATK計算へは倍率を流しません。

倍率の未解決対象は毎回freshに選び、永続的なlazy対象を確定しません。base側のlazy対象は別の規約です。正本の`enemy_atk_down_flat`は味方／敵所属を調べる前に、liveなstat26のlazy対象を解決する副作用があります。GPUも同じ順に合わせました。最終観測だけでなく、実際の敵被弾が順位反転前に対象を固定する境界も追加しています。Runtime配列は増やしていません。

## 受付と検証

型付き数値stat表と既存protection定義から、raw buffの受付bitsetを生成します。不明な数値statを黙って無効果にせず、既存初期化stage24の後のstage25で拒否します。保護効果のshield／split／cover-disable／decoyを含み、実編成80入力の全kind0定義が表に含まれることをGPU禁止のCPU契約で確認します。

独立52入力（native42／拒否10）は、負値・ゼロ・加算順・異owner・対象・stack・gear・scaled reference・期限・子イベント・解除・B3保留・敵carrier・lazy queryを確認します。イヴの全定義実編成3秒／30秒も集約へ追加しました。入力の作成時はnative戦闘／GPU実行を禁止し、期待値の注入を検査します。

旧664のうち`named-magnitude/reject/named-mag-unported-atk-magnitude`は、今回対応した79を拒否していた旧負例です。旧goldenを保持し、新suiteでは未知statの拒否へ明示移行します。この1件を除く663入力の保持と、新独立52入力の全input／nativeと専用診断tail16語を除くraw保持を別々に記録します。

初回51のlazy対象1不一致と、初回集約718のprotection受付漏れ13拒否は失敗のまま保存しました。修正に合わせて期待値や比較項目を緩めていません。コンパイラ配置指定漏れでGPU前に停止した起動記録も保持し、明示Slang rootでの実行と区別します。共通CLIは同じ配置ミスをCPU参照計算・GPU claim前に拒否します。

## 次の未対応

静的packingは210/266、base150/203、86分類です。これは実戦のGPU認定数ではありません。次の候補は`revive`です。正本には永続passive再付与、HP再同期、満弾・即時行動再開、down通知後の再入があり、単なるdown bit解除では足りません。`projectile_dmg_pct`／`shield_dmg_pct`／`heal_split`はpinned正本内のconsumer未確認で、無効果受付は行いません。

CUDA cache／controllerの以前のWindows v117 CPU53成功と、v115 cold compiler allocation failureを区別します。今回Windows実行は0です。同じcompiler条件の再試行や上限拡大はせず、生成CUDAのRuntime・属性・関数規模を記録します。通常UI CPU・全キャラGPU認定0・最終目標未完了を維持します。

## 確定した実証

Metal718入力（native570／拒否148）は全件一致し、GPU0の独立sealが成功しました。旧663の全raw保持、独立52の診断tail以外のraw保持、全718のlazy bankゼロを確認しました。イヴ3秒は物理116件、30秒は1063件で、どちらも履歴省略0です。以前のミハラ／persona等の履歴上限は残ります。最終CPUは723件中722成功・Windows専用1skip・失敗0、CLI28件も成功です。

生成CUDAは5,044byte・3関数増、noinline数と全Runtime fieldは同一、推定138,928byteです。これは実CUDA ABI・compiler peak・速度の測定ではありません。詳細は`research/portable-attack-magnitude-development-checkpoint.json`、`portable-attack-magnitude-retention.json`、`portable-attack-magnitude-compiler-delta.json`を参照してください。
