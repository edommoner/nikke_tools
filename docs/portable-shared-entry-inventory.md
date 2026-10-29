# 保存した未対応一覧から次の作業を選ぶ（2026-10-29）

`entry-plan`は既存`entry-inventory`の保存JSONから、同じoperatorの複数targetに現れるprofileを重複除去して優先順を出す。profile準備・packing・battle・compiler・GPUを再実行しない。

```sh
python scripts/nikke_gpu.py entry-inventory --suite original-shield-weapons --out NEW_INVENTORY.json
python scripts/nikke_gpu.py entry-plan --inventory NEW_INVENTORY.json --out NEW_PLAN.json
```

stdoutは件数・operator・target・scoped suite ID・公開証跡だけの短い一覧。outには元profile段階/全定義SHA・既存のscoped Metal/CUDA flag・未完了要件を保持する。全266profileは254 packing成功・12失敗、11operator系統。最大はベイ4段階。同じ4段階のall_allies/self_coverを8件と数えず、別operator間の重複も全体へ足さない。packing数はGPU対応数ではない。

成功した静的監査・禁止呼出し0・元profile identity・件数を検査し、重複ID、壊れた定義SHA、boolの偽counter、矛盾したruntime/admission claimを拒否する。出力は新規pathだけで元reportを変更しない。新しいsource監査ではないため`current_source_revalidated=false`を明記し、過去のscoped Metalを現在のCUDA/defaultへ昇格しない。部分選択のscopeも引き継ぐ。

ベイには公開比率候補と不一致を分類へ追加したが、canonical consumer/GPU拒否は維持する。[資料と数値境界](portable-bay-allocation.md)。実CLIで元266行・全入力hash・GPU sourceを保持し、約693KBの元reportからstdout5650byteの一覧を作った。これは出力量の記録で、計算速度倍率ではない。新規7＋既存監査/CLI等の116テスト成功。[小記録](../research/portable-entry-plan-v1.json)。以下は従来の監査と選択経路。

# 対象profileを準備前に選択する（2026-10-28）

同じ未対応の再調査を避けるため、共通CLIの既存監査へ`--character`と`--favorite-stage`を追加した。指定しなければ従来の全266profile監査と同じ。キャラ名は繰り返し指定でき、favorite未指定ならそのキャラの元全段階、favoriteだけならその段階を持つ元profileを選ぶ。

```sh
python scripts/nikke_gpu.py entry-inventory --suite original-shield-weapons \
  --character '앤 : 미라클 페어리' --character '벨벳' --favorite-stage 0 \
  --out NEW_SELECTED.json
```

選択は元metadataで全件検証してからprepareへ渡す。未知名、重複、空選択、bool/範囲外stage、指定キャラに存在しない段階を拒否し、既知名だけを部分実行しない。元のmetadata順を保つ。favoriteごとのbodyはyield時にdeepcopyし、後の段階による共有defaultの更新を混入させない。元body/effect/武器・育成を変更する選択機構ではない。

選択報告は`profile_selection.all_profiles=False`と`applied_before_preparation=True`を持ち、部分結果を全体のinventoryと扱わない。`profile_explanations`は元source行、owner、name、元effect SHAと全定義SHAへ既存の`reference_readiness`を結合する。whole-program失敗、定義のfirst failure、kind拒否をそのまま区別し、新しい分類器やGPU受付を作らない。未知の後続要件や、1件を修正すればprofile全体が通るという予測はしない。元owner/名前/行の不一致は監査自体を失敗させる。

実CLIでAnn/Velvetの2profileだけを準備し、元本人の敵向け`heal_received_pct`/`ammo_charge_pct`が既存の`reference_model_gap`であることを0.87秒で出力した。Cinderellaだけの受理対照は0.82秒。全266監査は4.53秒で、以前の全profile行・入力hash・元定義identity・kind依存・未対応順位と完全一致した。選択した3行も全体対照の同じ行と完全一致。単発測定であり一般的な速度倍率は主張しない。監査コマンドのbattle/GPU/compiler呼出しは0。

source closureは履歴の古い静的報告ではなく、直前に固定したincoming packetの全GPU source byteと照合した。今回の変更にGPU/数値/計算/packing/比較/goldenは含まれないため、計算証明の再実行はしない。専用7＋既存inventory11/readiness15/semantics22検査が成功。Windows status取得はhost unavailableで終端不明、run再送0。詳細は`research/target-count-query-evidence/selected-original-entry-inventory-v1.json`。

この監査を使って既存の専用実証も先に確認し、未対応の元operatorを選択してからcatalogueのbounded開発packetへ進む。Ann/Velvetの敵数量、cover_def_pctの正本inert、未知のLock On距離をally選択やno-opで置換しない。全キャラ/全特殊効果/公開GPU受付は未達。最終f096e7fc/package10bb432e…は固定packet自身で選択監査成功、24群216unit/CUBIN O1・2GiB・60秒compile-plan policy成功。直前packetとの差は既存3ファイルの監査/CLI変更と新test1ファイルのみ。既存identityの全関数、全calculation/packing/native/比較ソースとgoldenは保持し、CLIはmain以外・inventoryはrun以外の既存関数/class ASTを保持する。native全sweep/GPU再実行0。最終記録`selected-entry-final-checks-v1.json`。

以下は従来の全件監査の説明。

# 実際の共通入口で未対応項目を調べる

開発の優先順位は、使用する入口の`entry-inventory`から決める。従来の`inventory`はlegacy world compilerの分類であり、共通座標入力やtyped modifier loweringの受理範囲とは異なる。いずれも静的変換で、GPU受付・計算・全キャラ認定を表さない。

```sh
python scripts/nikke_gpu.py entry-inventory --suite coordinate-original-owned --out NEW_ORIGINAL.json
python scripts/nikke_gpu.py entry-inventory --suite original-projectile-weapons --out NEW_PROJECTILE.json
python scripts/nikke_gpu.py entry-inventory --suite original-shield-weapons --out NEW_SHIELD.json
```

元のprofile準備、KindAdmission、元source行への逆対応、診断分類、GPU禁止contextを再利用する。後ろ2つは実際の`compile_coordinate_typed`を使い、kind2/3の1対象、明示BODY owner、固定の宣言形状、自動照準/現在敵field policyを記録する。模擬damageを追加せず、元effect/ownerを変更しない。これは既存13/15入力suiteの全ケースを再実行するコマンドではなく、同じcompilerへの全profile静的調査である。

入力変換失敗には、選択した入口と同じ既存group/target-modifier loweringを使う定義単位の診断を添える。エラーのidentity/stat/targetは変換前の元行を保持する。validatorの最初の失敗しか分からない範囲、全programの失敗、definition-kind拒否を分け、後続要件を解決済みと予測しない。未知policy/別sourceの組合せ、壊れたaxis/source対応、battle/GPU呼出し、出力上書きは拒否する。

現在の観測では全266profile中、legacy worldは245、元共通座標は247、宣言した発射体/敵シールド入口は254が変換できる。247からの差はSakura/Anchor/Clay/Asuka/Rei/Mari/Misatoの7profile。元266件の定義identityは同一で、GPU source/計算実装の追加ではない。残る12profileの失敗を13の元stat/target分類で保持する。全キャラ認定0・通常UI CPU・公開GPU受付Falseは変えない。

これは選択入口の失敗一覧で、全入口での未実装一覧ではない。特にHeavyarmsは別の専用entryで元25効果の限定合成実証が既にある。新規probeを作る前に、12件を既存専用entry/実証のscopeとも照合する。

`multi_hit:2/4`はNihilister/Belortaの元定義のまま共通入力へ下ろせ、実際のgroup owner maskも存在する。既に単体/実射撃/長時間/混成の限定実証があり、同じprobeを作り直す優先度は低い。一方、現在の座標modelで複数の論理敵へ同時に当てる経路や、既定CPUのproducerとは別問題である。PARTをBODY/ADDと同じ敵数へ置き換えたり、単体typed shieldを敵数として数えたりしない。変換成功からthreshold発火を推定しない。

次はこの一覧をruntimeの未実証条件と照合し、受理される元profileの選択・固定・bounded実行をCLIで反復できる経路を優先する。12件のmodel gapは別に残し、既存の実証や単なる変換を全効果対応へ昇格しない。今回の変更は監査/診断/CLI routingだけで、Metal/CUDA計算とWindows実行の追加はない。

固定93919181/package d389bd5d…で14群143検査（11.62秒）と3入口の実監査が成功。全input SHA/元定義identityを保持し、以前のsealed packetとの差分は監査/診断/CLI/testの5ファイルのみ。GPU/計算/packing/native/比較器とgoldenは不変で、全CLI関数はmainの本command解析・dispatch以外AST同一。GPU再実行はしない。CUBIN/O1/2GiB/60秒のcompile-planもpolicy検査だけ成功（compiler/GPU0）。証跡 `research/target-count-query-evidence/shared-entry-inventory-v1.json`。

旧診断testのmanifestにsuiteが欠けた2件は、実在projectile suiteを指定するfixtureへ修正した。prepare_entries/run_capture/wire guardを緩めていない。今回のsuite packetはglobal model-check用のpinned IMPL-STATUS.mdを含まない（以前のpacketも同じ）。全体のmodel-checkは必要資料が揃う開発checkoutで成功し、packet内の未実行/失敗を成功へ読み替えない。unit-checkは専用の小さなCPU reference testを含み得るが、全native sweep/GPU認定を実行したとは記録しない。
