# 共通GPU開発の全体レビュー：0e1f71b

利用者の依頼でログイン済みClaude Codeを実行し、現在の方針・共通実行器・検証工程をレビューした。対象は固定HEAD `0e1f71b2bff924fe9dfba881f3cdf9fa103fe260` と、作業中の保守的なreadiness分類。別チャットの保存領域変更は対象外。Claudeの回答をCodexが実ソースと照合し、以下へ整理した。

結論は、共通Slangの数値・効果・状態／イベント実行器と、薄いCUDA／Metalバックエンドを維持する。ただしMetalの新機能を積み重ねるより、CUDAコンパイルの障害を判別できる調査を先行させる。全面書き直しの根拠はない一方、Metal796入力／native633の一致から未対応機能やCUDA全体の健全性まで認定しない。

## 採用する指摘

- **高：次の試行は原因を区別できる設計にする。** v132本体、v134 commands単独、v135 Definition viewのassemblyはいずれもメモリ確保失敗。これで「フェーズを分けるだけで解消」「Definitionの宣言を小さくすれば解消」という候補には否定的な結果が得られた。ただし最大関数の負荷とモジュール全体の負荷はまだ判別できない。同種の表現変更や同条件再試行は増やさない。
- **中：Definition viewをCUDAメモリ改善と数えない。** 保存指標はPTX約5.46→5.66MB、最大virtual宣言5,328→5,865。`applyDefinitionFrame`の増加はgetter展開によるload／アドレス計算増加の仮説を調べる材料になる。compilerメモリの原因・悪化量・実レジスタ数は未証明。Metalの意味保持が検証済みであることと区別する。
- **中：変更のない保存PTX分析にはMetal全件再実行を要求しない。** 元producerの監査・SHA・tool・options・containmentとの結び付きを保持し、既存の保存結果監査を再利用する。計算本文を変更した候補のMetal証明や、最終CUDA数値比較は別途必要。既存source certificateを無条件に省く提案ではない。
- **中：新しい効果は実行器への接続単位を小さく設計する。** heal_splitのplan snapshot・cursor・weightsは入れ子を保持する必要がある。巨大なif連鎖への追加、Frame拡張、Runtime side tableのどれがcompilerに有利かは未測定。CPU契約を先に固め、配置案は比較して選ぶ。
- **低：readinessの記録件数を契約と結ぶ。** `recorded_cases=28`の直書きは、参照suite／checkpointとの整合性検査を追加すると保守しやすい。現時点で件数の不一致は確認していない。laneはGPU受付・計算対応率ではない。

## 誤検出と、採用しない断定

- **evidence.json欠落で成功するという疑いは不採用。** `scripts/nikke_gpu.py`の`compare_readback`はevidenceを必ず読み、`audit_capture`はその例外を失敗にする。実比較器を残したCPU故障注入で、欠落時に`FileNotFoundError`、`calculation_verified=false`、`passed=false`を確認した。GPU／Windows実行0。
- **「原因はcompile単位で、計算設計ではない」は断定しない。** 確認できたのはassembly段階の失敗まで。ソフトウェアbinary64や実行閉包を含む設計がcompiler負荷にどう寄与するかは未判別。
- **「RDCはmodule全体が原因の場合だけ有効」も確定事項にしない。** 独立関数でも失敗するなら、その分割方法では不十分という証拠にはなる。全ての分割・link方式の可否までは決められない。
- **PTX上位local宣言だけからRuntimeコピー不存在は認定しない。** 宣言統計は最適化後の物理配置を証明しない。
- **Runtime side tableを必須にはしない。** 深さ別のsnapshotと寿命を満たす設計候補であり、追加状態量とcompiler影響の確認が必要。
- preflightと実行後native比較は両方存在するが、前者は入力／正本の事前検査、後者は保存GPU結果との比較。既に削除したchild比較と混同しない。独立audit／sealを削らず、さらなる再利用は出所・入力・正本の固定契約と計測を伴って設計する。
- CUDA起動は現在1 thread/blockで、並列化の検討余地はある。しかし利用率や速度を1/32と決め付けず、compiler成立後に実測する。
- ptxas即時終了時の観測競合は将来の診断改善候補。現在のallocation failureの原因ではなく、安全側の停止を緩めない。

## 時間と開発順序

最新Metal796の単一観測はGPU約9.755秒、pipeline約6.450秒。親監査約47秒は以前の759保存結果であり、同一実行の時間として合算しない。CPU全検査870件は約61秒、選択検査のWindows158件は約26秒。Windows往復、認証／接続待ち、実装・検証全体の総所要時間は今回計測していないため、削減率は提示しない。

1. **Macで保存PTXを分析する。** SHAとproducerの出所を確認し、関数／呼出閉包、load／アドレス計算を調べる。GPU・NVRTC・ptxas追加実行0。統計をメモリ換算しない。
2. **判別可能なcompile実験を設計する。** 最大関数とモジュール全体を区別する仮説を固定する。PTX partition／relocatable assembly／linkは候補で、未実装。関数bodyの保持、linkageと外部関数ABI、global／constantの唯一の定義、対応tool版、失敗保持をCPUで検査する。既存のsource書換え禁止assemblerへ暗黙追加しない。合法性・対応tool・新しい監査契約を確立できなければ実行前に止める。
3. **必要なWindows検証だけを1回行う。** 新しい明示実験が準備できてから、既存の60秒／2GiB／BelowNormal Job／startgate／cleanupを再利用する。失敗時の自動fallback、上限拡大、同条件再試行はしない。compile／link成功後も、共通fixtureでCUDA数値比較を通すまでは本体CUDA成立と呼ばない。

未対応機能はheal_splitの未被覆対象・lifesteal等のCPU契約整備を進められるが、大きなGPU本文追加はcompilerの成立経路と両立させる。consumer未確認のprojectile／shield、CPUモデル上のcover防御を無効果として受付しない。共通CLI・比較器・保存結果監査を再利用し、別runnerは増やさない。

全キャラ・全特殊効果GPU対応は未完了。静的packing214/266は入力受付だけで、全キャラGPU認定0・通常UI CPU・最新版CUDA数値一致未確認を維持する。今回のレビュー自体はGPU／Windows実行0、実装変更0。

## レビューの出所

Claude Codeはsafe-mode、ツール無効、MCP無効、session保存無効で実行した。関連ソース・記録の明示抜粋137,787byte、176.652秒、exit0。個人設定・認証情報・raw GPUバイナリは送信していない。全リポジトリ探索や新しい性能測定ではない。

- prompt SHA256: `2a79ecf3aab665cc0a8b2201adbdd53e485b6d6f30a002ee7750c651c2adc17f`
- response SHA256: `ed6adbb3435e32b6eae32a9dbbc4ad12735b7fe95e21815d27d34f04114a62df`
- 原回答: `/tmp/nikke-overall-review-0e1f71b.response.txt`
- 送信ファイルmanifest: `/tmp/nikke-overall-review-0e1f71b.manifest.json`
- 実行記録: `/tmp/nikke-overall-review-0e1f71b.run.json`
- 使用スキル: `/Users/edo/.codex/skills/claude-code-reviewer/SKILL.md`
