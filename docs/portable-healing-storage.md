# 回復貯蔵と実編成の受付接続

共通stat74 `heal_overcharge_store`をprotection kind9として実装しました。CUDA／Metalで同じSlangと入力・比較器を使います。今回の実機証拠はApple M5のMetalです。新版CUDAの数値一致はまだ未確認です。

## 数値・状態の契約

容量は発動時のcasterの最終maxHP×効果値÷100、0未満を0とします。maxHP／現在HP／HP比率条件は貯蔵量によって増えません。通常の身体回復とlifestealの超過分だけを貯蔵し、身体へ届く被ダメージ・正のcurrentHP drainが先に消費します。無敵は消費せず、shield／decoyの処理後、不死・致死判定前に適用します。cover修復・復活・maxHP付与は貯蔵を満たしません。

失効で貯蔵量を失い、失効前の再付与は新しい容量まで以前の量を保持します。複数のcarrierは新しい発動を優先し、同時発動はresident順を保ちます。lazy対象は既存queryに接続します。protectionの共通object poolとscratchを再利用し、入出力strideは増やしません。

これらは`app/healing_storage_compat.py`に記載済みのCPUモデルとの一致です。全ゲーム内相互作用の独立した実証ではありません。ATK由来の貯蔵・放出・heal_splitは別の未対応機能です。負のcurrentHP drainで上限を超える既存CPU動作は、既存の静的reference health同期方針を使って保持します。binary64・integer／pow・厳密normalizer・protected参照4ファイルは変更していません。

## 受付と回帰

AnchorのC_STATIC編成条件は既存`basicConditions`で評価できましたが、actor-fieldの追加条件受付にありませんでした。固定booleanを0/1に限定して受け付けます。Soraのkind26解除はcounter admissionに状態系の受付規則を渡していなかったため拒否されていました。actor-fieldと同じ`WORLD_STATUS_KIND`を再利用し、既存status／recipient／scope検査を通します。新しい別の解除実行器は作っていません。

回復貯蔵51入力は正例39＋raw拒否12。周期回復・固定条件の真偽・refresh、解除の対象／件数・beneficial貯蔵の保持、上限超過HPと回復、lazy＋lifesteal、policyとmetaを同時に欠く負例も含みます。元36ケースに追加しています。

共通regression235はreadiness81＋stun46＋実編成32＋skill cooldown25＋回復貯蔵51です。native188正例とraw拒否47がすべてMetalで期待どおりでした。修正前184の4拒否と診断captureは保存し、期待値を拒否へ変えていません。旧210入力のinput／全raw output／native指紋は同一です。`portable-storage-regression-retention.json`を参照してください。

成功した固定packageから明示sealした新goldenは`research/portable-world-storage-regression-short-expected.json`です。個別の開発suiteは過去goldenの不一致を自動更新せず、必要な開発実行に限定します。通常の検証入口はsealed regressionです。

## CUDA診断

`compiler-stats`は保存した生成CUDAを原byteと証拠SHAで照合し、関数の字数・分岐等を集計します。`ptx-stats`は保存PTXキャッシュのidentity/key、原byte、既存compile receiptを照合して仮想register宣言とlocal宣言量を数えます。実レジスタ数、compilerメモリの原因、GPU性能や数値一致は証明しません。

旧Windows解析器は`%`のないregister名を拒否していました。PTXの変数宣言では`%`は必須ではありません（[NVIDIA PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/#variable-declarations)）。新しい共通解析器はこの宣言・parameterized名・nested scope・prototypeをCPUテストし、未対応構文は部分推測を返さず失敗させます。元の解析失敗は保持します。重いcompileを繰り返さず、保存済みPTXのCPU解析から次の比較仮説を決めます。
