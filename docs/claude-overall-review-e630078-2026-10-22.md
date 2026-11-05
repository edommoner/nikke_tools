# 共通GPU方針の全体レビュー：e630078

利用者の依頼により、ログイン済みClaude Codeで全体レビューを実施し、Codexが指摘を実ソース・保存記録へ照合した。対象は隔離worktreeのe630078800caa29779ba277a4f258fdab7eb7d25と、未コミットのheal-share CPU契約。主checkoutの別作業は変更していない。

## 結論と優先順序

数値・状態・イベントを共通Slangへ落とし、CUDA／Metalは起動・転送を分ける方針は維持する。全面的な書き直しを支持する証拠はない。ただし、Metalの機能追加を続けるだけでは、最新版CUDA本体がコンパイルできない問題を解消しない。

1. **保存済みv132の診断を先に読む。** assemblyのstdout、起動までの時刻、取得済みメモリ情報を確認する。GPU／compilerの再実行は不要。取得していないメモリを過去の測定値として補わない。
2. **コンパイル対象を切り分ける設計を先に作る。** 既存initializePortableProgram／executePortableCommands／writePortableProgramを同じ本文の診断entryから呼ぶ案は検討に値する。Macで生成関数の到達範囲と規模を調べ、commands側にほぼ全閉包が残るなら、分割だけで改善すると期待しない。Windows試行は設計・事前検査・停止条件を確定してから、必要な候補だけを各60秒／2GiB以内で実施する。今回のレビューでは追加試行していない。
3. **未対応効果は独立CPU契約を完成させる。** heal_splitには確認済みのCPU消費経路がある。20提案中18成功、隣接HP通知の期待値不整合と入れ子ケースが未完了。共通実行器へのGPU追加はCUDA診断用の固定基準と混在させず、CPU契約、共通実装、Metal／CUDA一致をそれぞれ完了条件とする。

## 確認できた効率上の課題

**CUDAコンパイルが現在の主要な成立障害。** Windows v132の構造化報告では、PTXは8,757,024→6,721,321byte、最大関数virtual宣言は10,927→5,931へ減少した。しかし独立ptxasは1回失敗し、CUBINはない。NVRTC14.531秒、ptxas38.061秒、Job55.276秒、peak2,147,631,104byte／上限2,147,483,648byte。stderr診断なしで原因未確定。上限付近のpeakやvirtual宣言から必要メモリ・改善率を算出しない。Macで原captureを独立監査した結果ではなく、Windows側要約の確認である。

**assemblyの親・子に同じ重い監査がある。** scripts/nikke_gpu.pyのassemble_captureとassemble_childは双方でassembly_originを呼ぶ。前者の検証を後者で単に省略すると、間の改変を見逃す。親で確定した不変入力と証明へ束縛し、子では必要な再照合だけにできるか、故障注入を含む設計が必要。Job全体とptxasの差約17秒を全てこの重複の時間とは断定しない。ハーネスのメモリ削減でコンパイルが成立するとも未証明。

**検証の時間はGPU以外にもかかる。** 直近の保存Metal796ではGPU計算13.844秒、CPU preflight41.754秒、登録CPUテストbatch33.942秒、親の独立照合44.714秒。GPUを含むchild処理は27.391秒で、GPU時間と重複するため加算しない。既にchildのnative二重照合、全長ホスト転送・監査buffer、CPU各群の別process起動は整理済み。これらを未修正の課題として繰り返さない。preflight参照cacheは将来案で、入力・実行時依存関係・oracle source closure・破損時の拒否を設計するまで導入しない。audit／sealの独立再計算は維持する。

**履歴と現状の表示が混在。** docs/portable-resident-runtime.md等には246field／stride138,928時点の記録が残り、現行247／138,952と異なる。履歴自体は保存し、現状を示す小さな構造化checkpointへの入口を明確にする。各文書へ同じ最新数値を転記する運用を増やさない。

## 提案をそのまま採用しない点

- フェーズ別entry、複数kernel、機能別specialization、RDC／device-linkは**仮説**。Runtimeが常駐しているだけで分割が安全・有効とは証明できない。初期化、ready、queries、早期拒否、出力、実行順、ABI、共通数値を保持する契約が必要。診断entryを本番実装完成として扱わない。
- CPU出力がstat変更で不変でも「意味定義が存在しない」とは判定できない。条件・対象・発動経路を通っていない可能性がある。projectile_dmg_pct／shield_dmg_pctは消費経路未確認を維持し、条件を成立させた差分プローブとソース追跡の補助証拠を集める。no-op受付を対応件数へ加えない。
- heal-shareの通知8対2は、件数を8へ合わせるだけでは解決しない。実際のportion区間と隣接通知先を照合して契約を直し、観測器なしのnative／trace同一性、既存profile hookの連鎖・復元・例外時復元を検査する。CPU正本を期待値へ合わせて変更しない。
- 「Metal認定を0より増やす」という提案は、両backend対応という最終目標とは別の中間証拠。packing214/266やtiny CUDA4を全キャラ・本体CUDAの認定へ昇格させない。

最初の明確な到達点は、最新版本体のCUBIN成立と、既存全796入力の独立native比較・CUDA／Metal照合・seal。次に未対応効果を同じ経路へ追加する。通常画面CPU、全キャラGPU認定0、全目標未完了を維持する。

## レビューの実施記録

レビュー後、優先順序1の保存記録確認を実施。Windows保存stdout95byteにはMemory allocation failureがあり、当初のstderr0だけによる原因未確定報告を補正した。原報告と追補をともに保持する。origin verified→ptxas enteredは0.032秒で、起動前の全時間の内訳や直前harness memoryは未取得。詳細はresearch/portable-world-v132-saved-diagnostic.json。追加compiler／GPU実行0。

Claude Codeはsafe-mode、tools／MCP無効、session保存無効で、選択したコード・文書・検証要約だけを読んだ。129,895byte、159.221秒、exit0。認証情報・個人session設定・raw GPUバイナリは渡していない。レビューのためのGPU／Windows実行は0。指摘は抜粋範囲内の評価であり、リポジトリ全体を実行した監査ではない。

- prompt／送信元SHA一覧：`/tmp/nikke-overall-e630-review.manifest.json`
- prompt：`/tmp/nikke-overall-e630-review.prompt.txt`
- 原回答：`/tmp/nikke-overall-e630-review.response.txt`
- 原回答SHA256：`7fd059d47c9b90619974c015fb94cf13f5fb958ce3d1a595100255bd3351d246`
- 実行記録：`/tmp/nikke-overall-e630-review.run.json`
- 使用スキル：`/Users/edo/.codex/skills/claude-code-reviewer/SKILL.md`
