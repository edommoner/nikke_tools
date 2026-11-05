# 共通GPU実行器と開発効率の外部レビュー

対象はHEAD `a9366fb5ca1dd1737aab01a8445571113e29dd2b`と、作業中のlazy-cache storage変更です。利用者の依頼により、ログイン済みClaude Codeへ関連差分・設計・検証記録の抜粋を送り、Codexが回答をソースと照合しました。共通Slangで数値・状態・イベントを実行し、CUDA／Metalのtransportだけを分ける方針は維持します。今回の範囲では新しい動作不具合の確証は得ていません。

## 優先する判断

1. **CUDAコンパイルを、機能追加とは別の完了条件で管理する。** v112はNVRTC約30.344秒、compiler全体40.847秒でptxas allocation failureとなり、kernel実行0でした。Job上限付近のpeakは観測されていますが、原因の帰属は未証明です。Metalの対応件数だけ増やしても両GPU対応の障害は解消しません。現在の配列移動も、宣言上の状態量を24,576byte減らす候補であり、compilerメモリや速度の改善ではありません。
2. **storage候補の統合条件を機械判定する。** Metal428を一度実行し、native比較に加えて旧420入力の全raw一致、新8境界入力の一致、全428入力のbank領域ゼロを検査します。拒否入力も含めます。不一致時は比較器や許容範囲を緩めず、候補の採用を止めて原因を確認します。今回のレビューではMetal428を実行していません。
3. **領域と受付の接続漏れを小さな契約テストで防ぐ。** bank allocatorは直前のskill-critical領域と診断tailの間を検査しますが、entryの出力strideとの対応まで直接検査していません。現在の唯一の定義元はprojectile entryで、roster→reloadのincludeを通して786432語を選びます。現在の越境は確認していません。将来のentry追加に備え、出力専用の領域・stride・診断幅を明示して検査する価値があります。入力領域と出力領域が混在するLIMITSの全BASE/WORDSを単純収集する案は、そのままでは使えません。

## 共通実行器への落とし込み

新機能を別バックエンドへ複製する必要はありません。lowering、共有定義、受付、状態更新、イベント配送、対象処理、正負fixture、全定義の実編成を一組として追加し、既存のnative比較器と集約regressionへ接続します。

受付の分散は実際の保守課題です。直近のflat intervalでは、評価器が扱えるC34が受付から漏れ、初回415入力中1件が拒否されました。この既知問題は修正済みです。今後はkind／stat／conditionと受付経路・fixtureの対応を検査し、同種の漏れを早く見つける方が、実行器全体の汎用レジストリ化より小さく進められます。

Runtimeの宣言・初期化・access macroを完全生成する一般化は今は見送ります。現generatorは未知の宣言やguardを拒否します。別のbankが必要になった時点で重複を再評価し、仮説のない配列移動を連続して行いません。

## Claudeの提案から修正した点

- **baseline／候補のPTX生成をWindowsで各1回追加する案は、自動採用しません。** PTXのlocal宣言や仮想register数はptxasのpeak memoryを直接測りません。差が小さいことだけをstorage案の否定条件にもできません。追加2回のWindowsコンパイルを必須化せず、既存証拠で答えられない判断を先に明示し、Metal確認後に必要最小のcompiler-only検証を選びます。既定の時間・メモリ上限、再試行禁止を維持します。
- **早期returnによるbank残留は、現コードの確定不具合ではありません。** entryの早期returnは主コマンドループ前で、現候補はその前にbankをゼロ初期化します。ループ内のエラーはbreakし、最後のFINISHへ進みます。helper内returnとentryのreturnを混同して全体を書き換えません。全rawとbankゼロの検査で将来の退行を検出します。
- **動的配列は必ずlocalに置かれる、という説明は断定しません。** 最終配置・最適化はcompiler次第です。宣言byte、PTX宣言、物理register、compiler peak、実行時間を別指標として扱います。

## 時間の使い方

保存済みMetal420のCPU preflightは21.785秒、登録CPUテスト11群は計約19.76秒、bounded実行は51.707秒です。GPU処理自体は7.697秒で、library作成1.077秒、pipeline作成9.915秒でした。各時間は含む工程が異なり、単純加算して性能効果を推定しません。

CPU参照はpackage作成、preflight、readback比較、独立監査でそれぞれ使われます。preflightと独立監査は異なる保証を持つため、重複に見える処理を一括削除しません。改善するなら工程別の時間を集計し、不変な入力準備やプロセス内の再利用から始めます。GPU出力をCPU期待値へ流用するキャッシュは作りません。

現在のraw出力strideは1入力3,145,728byteで、420入力は約1.32GBです。件数だけを減らすより、保存結果を再利用する既存replay／監査を使い、同じGPU実行や転送を繰り返さない運用が有効です。

## 次の順序

1. 候補Metal428と保存baselineの保持検査を完了し、領域契約を確認する。
2. 必要なら固定候補のcompiler-onlyをWindowsで短く1回行う。失敗時に時間・メモリ上限を上げず、次の変更前に新しい仮説を記録する。成功してもCUDA計算一致は別に確認する。
3. 未対応一覧の上位から、参照動作を確認できるoperatorを独立fixture→実編成→集約regressionへ接続する。projectile_dmg_pct等、taxonomyにあっても参照consumerを確認できない機能を無効果として受け付けない。

静的packing193/266、基本キャラ134/203は実戦認定数ではありません。通常画面CPU、全キャラGPU認定0、新版CUDA数値一致未確認、最終目標未完了を維持します。

## 実施範囲と記録

Claudeはツール無効、MCP無効、session保存無効で提供された抜粋をレビューし、106.763秒、exit0で回答しました。全リポジトリを探索したレビューではありません。認証情報、個人session設定、raw GPUバイナリは渡していません。Windows／GPU実行の追加は0です。既存のCPU689件成功・1skipは候補作成時の保存ログを確認したもので、レビュー中に再実行した結果ではありません。

- prompt SHA256: `bc0c5a69b8c42d70c6bc73417b1e3b4288bd624f907a2b29f0412e9dbb002e2a`
- Claude回答SHA256: `9b490573b35687283578296bb503f56e2b6a87070886514e4d1488b6bcd433e3`
- ローカル原回答: `/tmp/nikke-architecture-review-claude.txt`
- ローカル実行記録: `/tmp/nikke-architecture-review-run.json`
- 使用スキル: `/Users/edo/.codex/skills/claude-code-reviewer/SKILL.md`

根拠: `scripts/nikke_gpu.py`のcpu_preflight／compare_readback／audit_capture、`app/portable_lazy_bank_specs.py`、`app/portable_runtime_layout.py`、`gpu/event_runtime.slang`、`gpu/world_projectile_entry.slang`、`app/portable_specs.py`、`research/portable-world-v112-compiler-sanitized.json`、`docs/portable-skill-interval-flat.md`。
