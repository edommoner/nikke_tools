# 共通GPU開発の全体レビュー：309e305

利用者の依頼により、ログイン済みClaude Codeへ最新の関連コード・設計・保存検証記録を渡し、Codexが指摘を実ソースへ照合しました。対象HEADは309e305f4d07c36c1b2a9dd7dd3cc5c19da0bedaです。共通Slangで数値・状態・イベントを計算し、CUDA／Metalで転送・起動だけを分ける方針は維持します。ただし、CUDAのコンパイル成立よりMetalの機能追加を先行させ続ける順序は見直す必要があります。全面的な実行器の書き直しを支持する証拠はありません。

## 確認した課題

### CUDAのコンパイル成立を優先する

v115はCUBIN O1の生成中にptxas Memory allocation failureで終了し、artifact・driver・kernelは0です。その後のMetal759一致は最新版CUDAの成立を証明しません。生成CUDAの関数数・Runtime宣言量もcompiler peakの改善を証明しません。

次の機能はentry_reload等の独立CPU正本契約を先に固め、Slangの追加統合より、CUDAの失敗を改善できる具体的な仮説・候補・成功条件の整理を優先します。ClaudeのPTX-only試験案は候補です。既存のPTX／CUBIN証拠を確認し、追加実行で何が新しく分かるかを明示してから選びます。PTX生成だけではCUBIN生成やdriver JIT・計算一致は証明できないため、案をそのままWindowsへ実行依頼していません。60秒／2GiB等の既存上限、同条件再試行禁止を維持します。

### CPU参照の重複は実測でき、整理する価値がある

scripts/nikke_gpu.pyはCPU preflight、childのcompare_readback、親のaudit_captureでnativeを計算します。明示sealでも新しい独立比較を行います。seal内部の二重比較は既に解消済みで、今回の新しい改善候補はchildと親の重複です。

最終759保存captureのphases.jsonlでは、childのshared_native_compareは48.188651秒、shared_gpu_executeは35.573616秒です。GPU実処理15.880739秒と後者は包含関係にあり、単純加算しません。CPU preflightは45.938302秒、bounded child全体は91.146991秒でした。raw/evidenceはchild比較前に保存されます。

childをraw保存までにし、独立親監査で判定する案を検討します。ただし、現在の失敗記録・containment終了判定・artifact収集・比較回数の契約を維持する設計と故障注入テストが必要です。単に比較を削除して保証が同じと断定しません。今回はレビューのみで実行経路を変更していません。

### 抽選0回のglobal RNG初期状態にも検査の余地がある

research/verify-world-revive-short.pyのcompareは、実際のclass random対象照会がある場合だけMT全624語と位置を比較します。seed0／42の抽選対照と実RunPlan.seed転送検査は既にありますが、抽選しない個別入力のbank初期値はこの比較の対象外です。

次の検査拡張では、蘇生有効・抽選0回も独立したnative初期状態と比較する価値があります。GPUのseed式を期待値へ転用しません。初期755の見逃しは、実seed転送漏れと抽選0回fixtureの組合せでした。今回の指摘だけを単独原因とは扱いません。既存成功記録は当時の範囲のまま保存します。

### 拒否stageの保証範囲を区別する

集約regressionのvalidate_rejectionはadapterの同名hookに委譲します。reviveが提供するvalidate_rejection_stageはこの経路では呼ばれず、通常集約はstatus64を検査します。診断専用entryはPORTABLE_WORLD_PROJECTILE_DIAGNOSTICを定義し、独立revive-diagnosticはstage26／403を検査します。通常entryには診断stage出力の前提がありません。

したがって、通常759へstage hookを無条件追加するClaude案は採用しません。既存の独立診断と通常集約の役割を分け、将来は新しい拒否を診断suiteへ接続したことをCPU契約で追跡する方が小さい変更です。通常集約のstatusだけで拒否理由まで認定しません。

## 誤検出・将来の保守課題

- **kind12とkind4の不整合という指摘は不採用。** app/portable_runtime.pyのcompact化でlegacy kind12をKIND4へ変換した後にrevival metadataを付けます。pack側のrowsはlegacy表現、GPU側はcompact表現です。提示抜粋に変換が含まれず、Claudeが異なる表現を同一視しました。現在の受付不具合を示す証拠ではありません。
- **lost領域の現時点の越境という疑いは確認できません。** LIMITS.CARRIERSと生成P_CARRIERSはともに512で、5×512の配置と一致しています。ただしportable_revival_specs.pyの512とLIMITSの対応を明示assertする小さな保守改善は有効です。現時点の不具合とは区別します。
- rawのblock単位重複排除は設計候補に留めます。既存の無損失gzip退避を再利用し、別の保存形式を先に増やしません。docsの状態・件数は構造化checkpointを正本に寄せ、履歴の全文転記を増やさない方向が適切です。

## 次の順序

1. CUDA compiler成立の次の仮説を既存証拠から絞る。同時にentry_reloadのCPU正本契約を作る。
2. child／親の比較重複を、失敗・監査契約を維持して共通CLIで整理する。追加GPU実行前にCPU故障注入で確認する。
3. 拒否診断の登録、抽選0回RNG、領域定数の契約を補強し、その後に新機能を共通実行器へ統合する。

通常UI CPU、全キャラGPU認定0、静的packing213/266、最新版CUDA数値一致未確認、最終目標未完了を維持します。レビューでGPU・Windowsを追加実行していません。

## 実施記録

Claude Codeはツール無効・MCP無効・session保存無効・safe-modeで提供抜粋だけをレビューしました。117.845秒、exit0、送信prompt107,735byte。個人session設定・認証情報・raw GPUバイナリは渡していません。全リポジトリ探索や新しい性能測定ではありません。数値は既存保存記録の確認です。

- prompt SHA256: 33bda6e9bbf4ab55c04caf46b62a6b0d52702ea1889c1877e2b278a5ae629a27
- 送信file SHA: /tmp/nikke-review-current-309e305.manifest.json
- 原回答: /tmp/nikke-review-current-309e305.response.txt
- 回答SHA256: a1eb8a8334cc54a76bedd9617dc9df4cd61918eb06ca1ffb1c5da397427f32ec
- 実行記録: /tmp/nikke-review-current-309e305.run.json
- 使用スキル: /Users/edo/.codex/skills/claude-code-reviewer/SKILL.md
