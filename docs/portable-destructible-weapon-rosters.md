# 元のミサト編成を共通武器・盾実行器へ接続

Current sealed entry: `destructible-skill-retention`157 / `destructible-skill-misato-retention`2. See [shared skill GPU proof](portable-destructible-skill-rosters-gpu.md). The following text records this earlier stage.

sealed共通CLI `destructible-weapon-rosters`を追加した。元ミサトの5スキル定義と、装備・ドラー・ドレイク・N102・メアリーを含む全71定義を保持し、元の実武器・成長設定・スキルレベルで3秒/30秒をMetal実行した。両入力がnativeと一致し、保存readbackの独立sealも成功した。

これは宣言された単一boss・武器だけの盾policyでの実編成検証であり、通常UIや全キャラ/全worldの認定ではない。盾の優先順位と補正factorは既存のprivate宣言モデルを維持する。

## 元の効果を残した静的入力

`portable_destructible_roster_input.compile_weapon_shield_roster`は既存の実編成preparationとworld compilerを使う。全定義の順序・owner・名前・条件・倍率表・継続時間を保持し、盾補正carrierを既存のkind4/axis3表現へlowerする。prepared入力を変更せず、効果の削除・架空のskill・CPUの発射予定表を加えない。

元5スキルはparsed_skillsの元データと全フィールド一致することをテストしている。prepared71/bound71を必須とし、単一bossのbody以外の座標/部位、未宣言の貫通・吸血・蓄積、boss/all_projectiles skillを静的に拒否する。通常の実編成compilerは前後ともshield_dmg_pctを拒否し、public admissionを変更していない。

HSI3の武器専用source sentinelと既存binding表だけを付加する。GPUは前回の武器141入力と同じ155sourceであり、Runtime138952byte、CUDA/Metal両生成、binary64、保護CPU/compiler、strict normalizerに追加変更はない。量・係数・pellet選択・receipt・counter・body除外は同じ実行器が処理する。

## 正の発動と回復

盾は元のBossScriptで0.1秒だけ存在するHP盾と宣言した。3秒ケースでは0.5秒後、30秒ケースでは4秒後に生成する。別のenemy attackで0.1秒後に全員へダメージを与え、回復を全快状態だけで検査しない。元のキャラ定義や武器を発動しやすい値へ書き換えてはいない。

|ケース|盾の着弾|元の盾補正|盾が受けた量|
|---|---:|---:|---:|
|3秒・発動前|ミサト3pellet|0%|9470×3|
|30秒・発動後|3射手の22pellet|150%|ミサト39998×2、ドレイク271001×10、メアリー101571×10|

30秒では元の60回攻撃条件で「사격 매뉴얼」が成立し、元のpassive「회복 보조」がall_alliesへ150%を与える。元の120回攻撃回復とburst回復も実行し、native観測では27回の回復配布中10回で実HPが増えた。最初の正の回復は4.383333333333323秒、各152939.23386192である。観測は既存の回復呼出しの前後HPを読むだけで、数値照会・回復通知を追加しない。

GPU比較は最終HP・弾数・weapon gate・burst状態/trace・body damage・物理shot履歴と、全25typed packetの係数・時刻・量・owner・世代・receiptを対象にした。回復27件のGPUイベント履歴を個別に比較した証拠ではない。回復を含む結果のHPはnativeと一致した。

## 保存監査と実行時間

producer package `aeb6742a8f319fc7146843f14e832d3324c879798c36b115e9660d31d8c745be`でGPU2入力を1回だけ実行した。GPU1.758617秒、library0.006169秒、pipeline0.007626秒、child全体2.645708秒。実runと最終generationはcache必須hit・追加Slang0だった。CUDA/Metalのstrict生成指紋は前回141と同一である。Windowsのcompile/GPU実行やCUDA cacheの速度改善を示すものではない。

readback8388608byteを独立sealがGPU0で再監査した。保存した両blockのfixtureでは、最終HP・弾数・body damage・typed時刻/量/receipt/statusの各9改変、合計18改変を比較器が検出する。旧141の全input/native指紋もCPUで再照合した。旧141のGPU実行は繰り返していない。

初回の実行要求は1GiB予備容量不足をclaim前に検出して停止した（GPU0/claim未消費）。終了済み旧141rawを既存`sparsify-raw`で疎化し、全591396864byte・SHA・inodeを保ったまま440991744byteの割当を回収した。raw/claim削除0。入力880900＋出力8388608byteと予備容量をinput前/GPU前で再確認してから、未消費packageのGPUを実行した。元の停止記録を保持している。

最終packageの初回CPU検査では旧141goldenのsupport_files梱包漏れを検出し、失敗を保持した。依存ファイルを明示した別final v3 `e95f1af29addb30acb57a024efcf5e2f7271ea1c689e1c9479f5f095eb2e24bf`から、CPU24検査（skip0、10.998秒）とnative2（1.027秒）が成功した。最終packageの全input/native/GPU sourceは実証producerと同一で、GPU再実行0。CPU-only reference2はcanonical positive0/model gap2を維持する。

## 継続方法と残件

```sh
python scripts/nikke_gpu.py package --suite destructible-weapon-rosters --out NEW_PACKAGE.zip
python scripts/nikke_gpu.py reference --suite destructible-weapon-rosters --out NEW_REFERENCE.json
```

fresh unpack先をcwdとして実行する。共通CLIのgeneration/seal/auditと既存Windows bounded packageを再利用できるが、現CUDA実機は未確認のまま。今回はWindowsへの新依頼・観測0。過去7プロセス終了はcause unknown/環境保全falseを維持する。

全266profile、245packing/base185、残20model gap、issueと順位は限定readiness metadata以外を維持した。全キャラ認定0、通常UI CPU、最終目標未達。次は他の盾補正キャラの全定義を同じ経路へ接続し、貫通・吸血/蓄積・skill route・部位/座標との混在を処理する。元アスカの貫通/吸血、マリの貫通などは現在のpolicyで明示拒否し、効果を削って対応済みとは数えない。

証拠: `research/destructible-weapon-rosters-evidence/manifest.json`。checkpoint: `research/portable-destructible-weapon-rosters-checkpoint.json`。
