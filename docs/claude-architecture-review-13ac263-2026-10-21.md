# 共通GPU移植の方針・効率レビュー（13ac263）

対象HEAD: `13ac26305ea843829e7c84bb1b9a3afc88e199ca`。
Claude Codeの外部レビューを取得し、Codexが関連ソースとCPU再現で照合しました。結論は、数値・状態・イベントを共通Slangへ置く方針を維持し、受付の整合検査とCUDAコンパイルの診断を優先することです。全面的な実行器の書き直しを支持する根拠は得られませんでした。

## 現状と効率の判断

- 共通CLIのregressionは327入力（native正例262、raw拒否65）。readiness、stun、実編成40、skill cooldown、回復貯蔵、発動回数減少、skill criticalの既存比較器を再利用しています。過去の「実編成がCLI外」「新機能の個別検証だけ」という指摘を現在のまま再報告しません。
- 最新Metalでは全327入力が期待どおりで、直前版の全input／raw outputも維持されています。ただしCUDA新版の計算一致は未確認です。静的packing191/266、基本キャラ132/203は実戦認定数ではありません。通常画面CPU、全キャラ実戦認定0、最終目標未完了を維持します。
- 保存されたv110はNVRTC約30.109秒でptxas allocation failure、kernel実行0でした。CUDA側の障害は検証入力数を減らすだけでは解消しない可能性があります。最新の単一noinline候補も、Metal一致と生成CUDAの属性1行差分までは確認済みですが、compiler時間・メモリ改善は未証明です。
- このレビューではGPU・Windows実行を追加していません。別途依頼済みの検証を再送していません。

## 照合した改善点

### 中：受付の知識が分散し、追加機能の接続漏れを生みやすい

`gpu/event_runtime.slang:252`のWORLD_TEAM_KINDと次行のWORLD_TEAM_CONDITIONは、引数にない`row`を呼出側から読みます。`gpu/world_actor_fields.slang:29`や`gpu/counter_landing_runtime.slang:21`の現呼出経路では正しいrowがあります。誤った行で計算した実例は今回確認していませんが、マクロの入れ子と暗黙の引数は変更時の保守リスクです。

まずrowを明示する小さな整理と、kind／condition・必要能力・受付箇所・正負fixtureを結ぶ対応表が有効です。特にPythonでpackingできた定義がGPU側の対象別検査で拒否される差を、実編成の受付診断で早く検出できるようにします。ゲーム処理全体を汎用レジストリへ書き直す必要はありません。整理時も生成byteと既存rawを確認し、normalizerの許容範囲を広げません。

### 中：CUDAの仮説検証には停止条件を固定する必要がある

noinlineを付けたhelperは生成CUDAで約125行ですが、旧v105のweaponFrameBodyはPTX約47,688行です。異なるソース・言語段階の行数から効果量は推定できません。「小さいので無効」「rawが同じなので性能上も無害」のどちらも未証明です。

既に依頼した単一候補の保存結果を先に回収し、compiler成功、数値一致、環境保持を分けて判断します。失敗時に次のhelperへ機械的にnoinlineを追加する連続試行は避けます。最新PTXの取得や状態配置の変更は、既存結果から比較仮説と必要性を定めてから検討します。コンパイル成功時も、同じartifactを使うrequired-cache実行とnative比較が必要です。

### 低：未対応分類には診断文依存の経路が残る

`app/portable_readiness.py:15`以降はreasonがない例外を部分文字列で分類します。CPU再現では`Invalid max_trigger`と`Invalid named event audience`はいずれもtrigger、`Lost HP defense requires combat and self recipient`はrecipientになりました。これらは異なる制約です。ただしsignatureにはkind／stat／target等もあり、現在の実inventory順位が誤っていることまでは立証していません。

新規・修正するvalidatorから構造化reasonを返し、文言フォールバック件数を可視化するのが妥当です。すべてのvalidatorを一度に書き換えるより、上位の未対応項目に必要な箇所から進めます。

### 低：実編成adapterの段階別定数と記録の現在値を分かりやすくする

`app/portable_world_roster_input.py:127`のABIとmodeは直書きです。projectile側では`app/portable_projectile_specs.py:finalize_program`が次段階のABI／modeへ更新します。現在の不一致は確認していません。各段階の定数を所有する小さな定義から参照し、adapter最終値を検査すると保守しやすくなります。現在のLIMITSに既存ABI／MODE定数があるというClaudeの提案は、そのまま適用できません。

過去機能の文書が当時のgolden名や235件を記録している一方、現在のCLIはcharge-boundary版327件です。過去の証拠を上書きせず、現在の入口と履歴の区別を明記すると調査時間を減らせます。

## 採用しなかった指摘

- **「compile-onlyにはJob peak memoryもNVRTC時間もなく、次回失敗しても何も分からない」：不成立。** `research/windows_validation_observer.py:109`はpeak_jobを読み、job_peak_memory_bytesと上限を保存します。v110記録にも最大2,148,089,856byteがあります。`research/portable_phase_audit.py:15`はmonotonic時刻を付け、実NVRTC境界を観測しています。ptxas単独の内部時間はこれとは別で、未観測です。既存計測を再実装する理由にはしません。
- **「charge_hold_maskのキャラ名判定を一般的なeffectフィールドへ変更すべき」：現段階では不採用。** pinned nativeの`calculator/timeline.py:2110`も同じキャラ名で特殊処理を分岐します。GPU adapterだけ一般化すると参照との意味が変わり得ます。現時点の未対応バグとは扱いません。
- **「boundの行番号とdefinition行の対応が疑わしい」：現在の経路では既存保証あり。** `app/portable_team_hit_specs.py:bind_compiled`はcompilerのsource_rowsを走査し、indexとlen(bound)の一致を検査します。bound_effectsはそのsource／owner対応を使います。prepared件数とbound件数が異なること自体は、team展開の仕様であり不具合ではありません。

## 次の作業順序

1. 依頼済みcompiler-onlyの保存結果を回収し、同条件の再実行なしで診断する。成功ならrequired-cacheでCUDA数値検証、失敗なら次の仮説を先に固定する。
2. 受付能力とfixtureの対応検査、rowを明示するマクロ整理、adapter段階定数の集約を小さく進める。数値・状態・イベント本体は共有を維持する。
3. 未対応一覧から参照動作が確認できる優先operatorを選び、独立fixture→実編成→共通回帰へ接続する。packing数だけを成果指標にしない。

## 実行範囲と証拠

Claude Codeはツールを無効にして関連ソースの行番号付き抜粋をレビューし、約114.08秒、exit0で回答しました。全リポジトリをClaudeが探索完了したレビューではありません。認証情報・session設定・raw GPUバイナリを渡していません。

Codexは指摘箇所と省略された関連実装を読み、分類をCPU再現しました。今回実行したテストはreadiness12、regression adapter2、compile CLI7の計21件で全成功。過去の671件やMetal327件を今回再実行したとは主張しません。計算コードは変更していません。

- prompt SHA256: `2cf309b363f625862909a533e7dd8dfee7e78ae14563f9a0983de2e0ec8abc3f`
- Claude原回答SHA256: `09dce7073928a6c87c413d421c28fcde7af5291a5563909cef6a55e0e76e7c90`
- ローカル原回答: `/tmp/nikke-review-current.txt`
- ローカル実行記録: `/tmp/nikke-review-current-run.json`

外部レビューに使ったスキル: `/Users/edo/.codex/skills/claude-code-reviewer/SKILL.md`。
