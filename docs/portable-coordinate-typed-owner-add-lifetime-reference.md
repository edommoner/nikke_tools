# ADD所有者の退場・再出現とfield寿命のCPU契約

`reference --suite coordinate-typed-owner-add-lifetime-common --out NEW.json` は、元Primの完全5人・71定義・武器／成長を保持する8秒の4契約です。別宣言counter markerと子fieldだけを追加し、実射撃からのcounter完了、物理kind/id/generation、宣言ADD所有者、固定されたfield世代を検査します。GPU／packingを禁止したCPU契約の実行と、別の共有wire packing検査を区別しています。

| ケース | 宣言所有者 | 観測内容 |
| --- | --- | --- |
| 発動前に退場 | ADD1/gen1 | 0.5秒でgraph終了、1.25秒に一度だけarmし、死後同世代の子fieldは非表示 |
| 発動後に退場 | ADD1/gen1 | 生存中に子fieldを生成し、1秒のgraph終了後に非表示 |
| 再出現へ非継承 | ADD1/gen1 | 無制限再出現でgen9が生存していても、旧gen1 fieldは非表示・被ダメージ倍率0 |
| 第2世代へ発動 | ADD1/gen2 | 1.25秒の一度のarm後にgen2へ発動、後続の生存gen9へ継承しない |

全ケースで実counter完了1件、物理targetのid10/gen1を保持します。子fieldは宣言したADDの世代を保持し、最終のBODY／ADD0／ADD1 received_dmg_pctは0／0／0です。再出現2ケースは最終ADDがgen9で生存中であることも検査するため、単に死んでいるから0となる検査ではありません。

観測器は既存OwnerQueries.projectとDestructibleWorld.synchronizeの受動wrapperです。既存managerのcarrier・immutable recipient key・current actor・visible判定を読み、値の変化だけを記録します。スケジューラや攻撃、RNG、数値buff queryを追加しません。観測器なし／ありの完全native結果とtraceが一致する検査を含みます。

初版は「発動前に退場」のcounterを早くarmしてしまい、退場前に実完了して契約が失敗しました。原本と失敗記録を保持し、入力だけを0.5秒退場→1.25秒に1回armへ修正しました。実行器や比較条件は緩和していません。v2の4契約成功後、再出現ケースを無制限反復へ強化し、生存中の新世代への非継承を直接確認しました。

不変CPU v3で強い4契約が40.211833秒で成功。最終v4（package ID `2f6e0c5f9048206911d07c942fe6a4b5b778ed50207ea1866f6196831b9238dd`）との差分はreadiness、CLIのテスト登録、packing単体テストの3fileのみ。全CLI関数AST・native producer／比較器は保持し、最終版で新4件のnative再生成は行っていません。最終関連120／制御517検査成功（Win専用1skip）。共有wireは全4件で完全73定義・115680wordのままpackingでき、generation必須hit・Slang0を確認しました。

旧ADD所有者3ケースも新しくCPU実行し、過去のinput/native/trace指紋をすべて保持しました。CPU共通契約のpolicy報告が後段でBODY名へ上書きされていた箇所を修正し、実入力どおりlogical-owned-current-fields-v1と報告します。過去の記録は書き換えません。

GPU・正本・数値・upstream・backend・CUDA compile cache・normalizerは全byte保持、旧99のgoldenも不変です。今回のGPU／Windows実行は0。退場はgraph終了によるもので、HPダメージによるADD死亡は未検証です。新4件のMetal/CUDA、ゲーム仕様、公開consumer、全キャラも未完。旧Metal captureの未回収状態も変わっていません。

成果は `.portable-recovery/proofs/owner-add-lifetime-20261027/` に保持し、小さな記録は `research/typed-owner-add-lifetime-reference-evidence/` と `research/portable-coordinate-typed-owner-add-lifetime-reference-checkpoint.json` にあります。次は同じ共有entryへdata-onlyで4入力を追加し、旧99を保持する新103入力のGPU検証へ接続します。これは新しい寿命契約の検証であり、失われた旧rawの再作成や旧captureへの証拠の追加は行いません。全キャラ認定0／UI CPU／目標未達です。
