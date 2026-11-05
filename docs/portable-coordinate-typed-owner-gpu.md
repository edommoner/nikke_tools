# BODY所有の型付き対象と現在対象fieldの共通GPU接続

sealed suite `coordinate-typed-owner` は80入力（native45／拒否35）です。旧 `coordinate-typed-actor`67をすべて保持し、元Primの完全5人・71定義・武器／成長を維持した5ケースと、入力不整合の拒否8件を追加しました。`package --suite coordinate-typed-owner` と既存の共通実行経路を使います。

## 共通の実行規則

新しい `world_coordinate_typed_owner_entry.slang` は既存actor／aim／weapon Runtimeを含みます。BODY所有を明示するpolicy `body-owned-current-fields-v1` はtyped header12=1・15=2を要求します。weapon13／aim14／live11も必要で、旧67に含まれる不正flag15=2を新policyとして誤受付しません。binding kind2/3とowner[0,0,1]を必須にします。

counterの物理kind/id/generationは保持します。敵fieldと対象条件の論理問い合わせだけ、同一世代のDT stateから宣言BODYへ投影します。実装はCUDA／Metal共通Slangです。通常current damageは既存のcanonical caster aim選択を維持し、物理counter対象へ置き換えません。Runtime138952byte、入力115680／出力2032000word、既存arena／history／RNGは不変です。

CPU private compilerは明示owner bindingのあるcounterについて、論理条件を検査する一時的なviewだけをBODYへ投影します。実際のコンパイル行は変更しません。正本の `detail_gpu.py` とその通常guardは不変で、scope終了・例外時にvalidatorを復元します。元の定義を削除／改変しません。source監査は既知full-hashのinverseだけを追加し、数値／normalizer／CUDA compile cache本体は変更していません。

## 実GPUとfresh監査

実行package `cf44aa64…`、capture `/tmp/nikke-typed-owner-metal-v2`。CPU事前検査80／native45は223.683332秒。Apple M5の実GPU1回は4.041898秒、library1.930172秒、初回pipeline93.763491秒でした。実行時はgeneration cache必須hit・追加Slang0、GPU retry0です。

初回比較は既存67＋新拒否8が成功、新規5件がenemy_fieldsで不一致でした。保存readbackを調べると、field値／recipient／counter子fieldはすべて一致し、CPU側だけに空の `nonzero_immunity_used` 観測がありませんでした。CPUへその観測を追加し、5件を再観測しました。追加キーを除く全native値のhashが元と完全一致すること、全入力・GPU／transport／正本の不変を固定した専用migrationだけで保存出力を引き継ぎました。比較器の項目削除やnormalizerの緩和はしていません。

修正版package `4754c201…` の共通replayによるfresh独立監査は全80／native45／拒否35が成功しました。24／24／24／8入力を別のGPU禁止childで比較し、78.245／73.308／135.965／4.863秒、各180秒内、全体294.003520秒です。ライブ親oracleの再利用0。goldenは、この同じfresh grouped auditの結果から登録しました。sealコマンドを再実行して同じnativeを重複計算したものではありません。

元Primのcurrent field数は対照／BODY／ADD／手動typed／counterで0／1／1／1／1。counterケースには原本の後へ別宣言の監査効果2件だけを追加しています。実HPシールド命中→実counter完了→子fieldの経路で、cameraがADDを狙っていてもBODYのreceived_dmg_pctは17、両ADDは0でした。物理impact・attack ID・世代・量、fieldの受け手、通常射撃とskill trace・RNGも共通比較器で照合しています。

旧67の全input/nativeと544576000byteのGPU出力を保存結果へ完全一致させました。失敗結果とclaimは保持し、GPU再実行0です。全reader終了後、元rawのSHA/size/inodeを保つ疎化で525991936byteの割当を回収しました。修正版replayは `--reuse-source-bytes` で同一filesystemの保存input/readback/evidence/generatedファイルをhardlink共有し、複製容量を避けました。どちらのcaptureも編集せず、各監査が全バイトを再hashします。

最終package `93ea25a5…` の差分はseal登録・golden追加・scoped readinessだけです。全CLI関数AST、native producer／比較器／tests、GPU sourceと全80goldenは実証版と一致します。最終関連100／制御507検査に成功（Windows専用1skip）、旧replay6件も成功。最終generation必須hit・Slang0。最終packageで新しいfresh native preflightを行ったという主張はしません。

## 使い方と残件

観測migrationは固定source packageと厳密な変更表に限定されます。履歴を再監査するときは不変 `/tmp/nikke-typed-owner-gpu-replay-v4` のCLIを使います。現在checkoutの追加変更をそのmigrationへ混ぜることは拒否します。詳細記録は `research/typed-owner-gpu-evidence/` と `research/portable-coordinate-typed-owner-gpu-checkpoint.json`。

共通CLIの `replay --reuse-source-bytes` は明示opt-inです。同一filesystemでregular file／同一inode／全hashを確認し、異なるfilesystemでのlink失敗を無予算のcopyへ切り替えません。部分共有失敗は失敗captureへ保存します。通常copy経路も維持しています。共有元／先を編集しないでください。

今回の実証は明示BODY所有のHPシールドを使うfield処理です。kind2の入力受付をprojectile fieldの実戦実証へ数えません。次は同じ固定entryへprojectile所有・破壊後／再登場世代のdata-only契約を追加し、生成／pipelineを必須cacheで再利用します。新shaderのwarm Metal load、現在CUDAのcompile/cache/launch、ADD所有・移動形状・他caller／variant、19packing失敗と残るモデル、同一現sourceへの旧suite集約、公開GPU／全キャラ認定は未完です。Windows追加依頼0、全キャラ0／UI CPU／目標未達を維持します。
