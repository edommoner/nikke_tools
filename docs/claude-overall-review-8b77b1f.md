# Claude Codeによる現在の方針と共通実行器のレビュー

対象はGPU開発用worktreeのHEAD `8b77b1f33f3dc2e97ea509d6875bd3025b1a8f94`と作業中の部位攻撃CPU契約。main checkoutの別作業である保存領域変更は対象外。Claudeの回答をコードと追加のCPU検査で照合した。

共通Slangの数値・効果・状態／イベント実行器と、薄いCUDA／Metalバックエンドは継続する。全面書き直しを支持する証拠はない。ただしCUDA本体がコンパイルできない状態でMetal本文だけを増やす順序は改め、CPU契約の不足を埋めながら、保存PTXからCUDAの成立経路を調べることを優先する。今回のレビューではGPU本文を変更していない。

## 確認できた問題

1. **高：CUDA本体のassemblyが未成立のまま、機能追加が進んでいる。** `research/portable-world-v135-definition-view-compiler-sanitized.json`ではptxas約30.69秒、timeout=false、Memory allocation failure、Job peak約2GiBを記録。Metalでの意味保持は証明できても、CUDAで同じ実行器が成立したとは言えない。時間上限に達していない事実と、2GiB上限が内部失敗の直接原因か未確定である点は分ける。今後の機能追加が必ずメモリ消費を増すという断定もできない。
2. **高：部位吸血のテストがHP上限で飽和する。** `research/portable_parts_skill_cases.py:36`の吸血100%ではmain2000＋near3000だけでHP5000→10000となるため、far3000の吸血欠落・重複を最終HPでは検出できない。CPU正本を変更せずfixtureだけ吸血10%にした独立確認ではHP5800となった。非飽和ケースとinterrupt／回復分配との組合せが必要。
3. **高：interrupt拒否・snapshot・着弾境界の契約が不足する。** `research/portable_parts_skill_contracts.py`は基本ケースのinterrupt集計、通常packetの時刻／reach等を照合していない。parts-and-interruptのnativeへinterrupt credit9999、packet time/reach999を注入してもverified=trueとなることを確認。破壊後の次回攻撃はあるが、生成から着弾までの状態変化、再出現generation、子イベントで変わる状態、追加packetによるgaugeの非増加は十分に検査されていない。現在の22ケースをGPU接続の完成条件にしない。
4. **中：契約のassertが最適化Pythonで消える。** `research/portable_parts_skill_contracts.py`の判定はassertに依存し、`app/portable_reference.py`にoptimize拒否はない。fresh展開先で`python -O`からdamage=[]／events=[]の不正nativeを渡してもverified=trueを返すことを再現。通常モードのテスト成功とは別の検査器の欠陥。明示例外または最適化モード拒否を共通入口へ実装する候補とする。
5. **中：契約の成功とモデル制限、現在値と履歴が機械的に分離されていない。** deferred burstの制限はcase contractとreadinessには明記されているが、reference全体のcase_countには通常ケースと一緒に入る。成功した正本再現と、意図した機能の成立を別集計する。件数の直書きとケース名によるイベント順序分岐もfixtureのliteral契約へ結び付ける。CLI文書は冒頭で過去記録と明記しているので「現在値を誤っている」とは断定しないが、過去の『現在』記述が多く、再開時の読み取り負担はある。

## 採用しない実装提案と未確認事項

- **receiptのat+7は空きではない。** Claudeは予約語へのpart slot/generation格納を提案したが、`gpu/world_skill_runtime.slang:25`の後で`WORLD_PERIODIC_STORE`が呼ばれ、`gpu/world_periodic_runtime.slang:86`が周期snapshotのindex+1を格納している。無条件再利用は周期処理を壊すため採用しない。target/orderもworld receiptの保存形式では保持されず、構造体の項目が存在するだけでは使えない。
- **part子を通常receiptへ積むだけで同値とは限らない。** 生成時の同じstats snapshot、nativeの部位群へのdamage適用順、子通知、lifesteal、容量と寿命を確認してから設計する。既存のphysical部位処理と共通化できる境界を調べる。
- **関数stub化をそのまま次のWindows試験にしない。** 意味を変えた診断は計算証明にならず、現行assemblerの元PTX保持契約にも合わない。保存PTXの関数／呼出閉包とtool/link対応を調べ、原因を区別できる明示的な実験契約を先に用意する。RDCやlinkを自動fallbackにしない。
- **『記録・文書が全体時間の主因』は未証明。** 同じ実行での工程別・待ち時間を含む総所要時間がない。保存された単一観測はMetal849のGPU約10.3秒、CPU全893検査約66秒。認証・Windows往復・監査・転送・文書更新を含む削減率は出せない。
- **『証跡が全て/tmpだけ』は断定しない。** tracked checkpoint、golden、共有済み記録がある。一方、今回のテストlogなど未永続化の証拠もあるため、出所SHAを維持して保存状態を整理する価値はある。
- **coverageの区別は妥当。** 静的packing216/266、Metal849＋実編成4入力、全キャラGPU認定0を分け、レム30秒の物理履歴55件省略も記録している。いずれもCUDA本体成立や全効果対応の証明にはしない。

## 次の実装順序

1. GPU本文を増やす前に、CPU契約のfail-openを塞ぎ、非飽和吸血・interrupt creditゼロ・生成／着弾snapshot・通知／gaugeの境界を追加する。モデル制限ケースは別集計する。
2. 保存済みPTXと既存compiler監査器を使い、最大関数とmodule全体の負荷を区別する実験をMacで設計する。Windowsは合法性・tool・容量・出所が確定した必要最小限の1試行に限定する。同条件再試行や上限拡大はしない。
3. その結果を踏まえてpart snapshot／receiptの共通実装へ進む。新しいparts suiteと既存849＋実編成4の保持を確認し、独立audit／sealを維持する。既存CLI・観測器を再利用し別runnerを増やさない。

## 今回の確認と出所

- Claude Code実行成功：107.615秒。safe-mode、ツール／MCP／session保存無効。明示抜粋126,025byte。認証情報・個人設定・rawバイナリは送信していない。
- fresh package `040390f69d5945bf01ac1e84d409a69c306fd98c5eb3a76a20b782f58928ffc5`から、部位CPU契約8テスト成功（1.382秒）、readiness8テスト成功（0.807秒）。22はfixture数で、テストメソッド数とは別。
- 追加のCPU故障注入／吸血確認のみ。GPU・Windows実行0。全portableテストを今回再実行したとは主張しない。
- レビュー原回答：[research/claude-review-8b77b1f-response.txt](../research/claude-review-8b77b1f-response.txt)
- 実行receipt：[research/claude-review-8b77b1f-run.json](../research/claude-review-8b77b1f-run.json)
- 送信ファイルとSHA：[research/claude-review-8b77b1f-manifest.json](../research/claude-review-8b77b1f-manifest.json)
- テストlog：`/tmp/nikke-review-parts-cpu-040390f6-tests.log`、`/tmp/nikke-review-parts-cpu-040390f6-readiness.log`。

実装の修正はこのレビューには含めない。全キャラ・全特殊効果GPU対応は未完了。
