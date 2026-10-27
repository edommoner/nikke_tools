# 元のバースト・付着弾・ゲージ・HP連動を同じ実行器へ接続

`original-catalogue-burst` は元4編成の30秒を同じ選択adapter/typed owner/共有CUDA・Metal実行器で検証したsealed群。効果・owner順・実武器・育成・configを保ち、模擬damageやキャラ固有shaderを追加していない。元の既定5人編成に、明示したBODY-owned HP shield1個・seed4301を置く宣言worldである。

| 元profile | 編成の全定義 | 全スキル着弾行 | 実物理receipt | 発火した処理の例 |
|---|---:|---:|---:|---|
| ラピ：レッドフード | 87 | 29 | 2,457 | 付着16・蓄積起爆1・即時起爆9・burst bonus1 |
| 紅蓮：ブラックシャドウ | 76 | 22 | 1,141 | ゲージ段階別damage7/7/6・consume6・弾薬補充 |
| レッドフード | 81 | 7 | 1,561 | 武器係数69.04→51.46→69.04・charge速度/overflow |
| シンデレラ | 74 | 102 | 1,185 | HP由来ATK・最大HP更新9・追加攻撃80・連続10＋同対象bonus10 |

スキル160行は全行を厳密な既存decoderと実creation receiptで比較。物理6,344件は従来どおり全順序semantic SHAと保持prefixを検査し、実typed状態・全battle/武器/通知/乱数/回復/最終状態も照合した。Rapiの物理raw保持は先頭2,048件で、以降409件は全件SHAへ含む。このraw保持範囲を個別全行比較と呼ばない。表のbuff等の発火数はGPU timer counterであり、独立したCPU handler呼出しcoverageではない。スキル着弾数はnativeと一致した実行記録である。

## 独立監査で見つかった観測器の未対応

初回のM5実行は137unit/CPU全4/全GPU比較に成功したが、fresh独立監査では`Every native legacy packet needs its real hit-loop receipt`が発生した。外側のcreation observerがtyped scalar hookの設置前の関数codeを固定し、実際のlegacy呼出し境界を見逃す問題だった。Pythonが例外でprofilerを解除した後にcleanup guardが発火し、旧CLIはその表面の`Native profiler changed during simulation`だけを報告していた。

修正は`world_coordinate_sampled_skill_native.creation_indices`の観測境界だけ。実legacy callerを先に確認し、その時点の`timeline.calc_damage`のreturnを観測する。無関係なhook teardownの途中で消えるattributeを読まない。全packet数・hit順・量・時刻・owner/sourceのassertは維持し、後のlandingから欠落receiptを推測しない。profiler guardやC-event filter、CPU正本、GPU・数値・効果定義・strict normalizerは不変。

5秒の実Rapi編成を使う回帰テストは、修正前の失敗を再現し、修正後は外側の観測器を重ねてもnative payload全体が同一で、4.6秒の実burst/起爆を含む全creation receiptが一致することを確認した。この短いtestは元30秒の実証を置き換えない。既存の保留burst12・filter4・seal11・group15・CLI49・replay6検査も成功した。

共通CLIはnested exception chain、独立監査のfirst difference/実比較結果を保持する。単一childの失敗・timeoutではcaptureの隣に一意の`nikke-independent-audit-failure-*`を作り、stdout/stderrと失敗JSONを保存する。成功条件や比較の例外除外を増やさず、再実行せずに原因を確認できる。grouped auditは従来のログ保持を使うため、TMPDIRを永続proof directoryへ設定する。

## 保存結果を再利用した実証

元packet e78d2c17…/source24c4d918の実GPU1回はApple M5で4.036秒。生成・pipelineの両必須cacheが実hit、Slang0、PSO0.00327秒。前回の同じkernelの初回PSO62.16秒を再度支払っていない。これはコンパイル部分の短縮で、CPU参照/独立監査を含む開発全体の速度比ではない。

修正99b20b7c/packet e5e6e9e0…で元4入力とnative指紋、GPU source closureの全一致を確認。既存のstrict replay経路で32,512,000byteの入力対応readbackを再利用し、全4比較成功。その保存結果を別fresh GPU禁止childで再度全照合してsealした（101.22秒、live-parent再利用なし、GPU0）。goldenはこの独立監査の出力をそのまま登録した。GPU再計算/claim再利用は0、初版の失敗と各診断は保持する。

`package --suite original-catalogue-burst --out NEW.zip` → `unpack` → 固定packet自身の`run`を使う。`original-catalogue-burst-cache-only`は同じsource/script/4入力/goldenに既存CUBIN/O1・compile cache必須とpaired generation必須を適用する。前のinitial群と生成CUDA/MSLの全byteが同じため、正しい同一keyのCUBINを全編成ごとに作り直す必要はない。現CUDAの実cache hit/計算は未確認、Windows新依頼0。旧Windows transactionはhost unavailableで終端不明のため再送していない。

## 次に残る条件

元定義が入力にあることと、条件分岐が実際に発火したことを区別する。Rapiの「他のB1がいない」編成側、Red HoodのB1/B2側は今回未観測。incoming attack/decoyの被弾処理、複数論理敵・PART/混在typed world、favorite variantもこの4入力で認定しない。次はこれら未観測の元条件を実編成・実操作へ接続し、既存の専用実証と照合して優先する。全キャラ・全特殊効果・公開GPU受付は未達。

出所と各元effectの発火/未観測行は `research/target-count-query-evidence/metal-original-catalogue-burst-v1.json`。未観測をGPU未実装と断定せず、今回の停止は`independent_reference_observer_gap`として記録する。
