# 名前付きスキル命中のクリティカル条件

共通predicate28 `trigger_hit_crit`を追加しました。既存の期待値モードに合わせ、名前付きスキルの命中通知が持つ判定を読みます。通常攻撃のクリティカル通知や、その時点のクリ率を代わりに使いません。計算・状態・テスト入力はCUDA／Metal共通ですが、新版CUDAの実行一致は未確認です。

## 状態と数値

native `_notify_frac`と同じcaster・スキル名の組で、software binary64の小数累積を持ちます。0以下／1以上の確率は累積キーを新規作成したり、以前の余りを消したりしません。多段スキルは発動時のダメージ計算で得たクリ率をsnapshotし、途中の子バフで残りの段を再計算しません。通常攻撃式のスキルはその式のnormal用クリ率を使います。

新しい通知はcontextを空にし、命中判定を明示的に受け取った名前付き通知だけがtrueになり得ます。継続処理のFrameは親contextを保持し、入れ子dispatchから復帰すると以前のcontextへ戻します。兄弟の発動やbuff通知、強制スキル使用が別の命中の判定を読むことを防ぎます。deferred B3 bonusはnativeが名前付き命中を通知しない経路なので、そのまま分けています。

GPU状態は既存projectile traceの後の未使用領域へ置き、入力／出力strideは維持しました。raw入力ではprivate world／native landing、条件operand、静的policyと名前付きpacket markerの対応、名前ID範囲を検査します。predicateがない旧プログラムには新しい累積状態を書きません。数値本体・integer／pow・厳密normalizer・protected参照は変更していません。

## 実編成で見つけた強制使用の接続不足

最初のregression320では、ユリアの愛用品1・2段階（各3秒／30秒）だけが受付拒否になりました。保存した3秒の診断は、actor poolのrow6、kind33 `force_skill_use`を示しました。クリティカル判定の計算差分とは分けています。

既存の共通強制使用実行器をworld受付へ接続し、maskの範囲・caster・自己参照を検査しました。また、強制先へ進む前に既存の条件評価器を呼ぶようにし、nativeと同じく現在の命中contextで一度だけ条件を検査します。強制使用は元のevery時計の格子をリセットしません。literal oracleでは既存のauthored-effect lookup観測を使い、別キャラの元データを強制先として参照しないようにしています。

## 検証

- 個別36入力：native26＋raw拒否10。確率0／1／小数、独立した名前とcaster、多段snapshot、兄弟・子・新規通知のcontext、通常攻撃式、周期スキル、ゼロ係数、空名、deferred B3、強制使用の条件と時計を含みます。累積はnativeの実際の`rng_acc`辞書から読み、GPU側の式を期待値へ複製していません。
- regression327：readiness81・stun46・実編成40・skill cooldown25・回復貯蔵51・発動回数減少48・skill critical36。native262正例とraw拒否65がMetalで全件期待どおりでした。
- 旧287、および最初の320で一致した316は、input／全raw output／native指紋が同一。2集合は重複するため合算しません。最初の4拒否・診断・claim・readbackは保持しています。
- CPU回帰671件、Windows専用1skip、失敗0。通常CLIの新goldenは`research/portable-world-critical-regression-short-expected.json`へ明示sealしました。

静的packing191/266、基本キャラ132/203、分類113。これは実戦認定ではなく、通常画面CPU・全キャラ実戦認定0を維持します。ユリア愛用品3段階には別の未対応selectorが残っています。

## CUDAコンパイルの診断

`compiler-stats --caller weaponFrameBody_0`を共通CLIへ追加しました。保存した生成byteを証拠SHAへ照合し、既知の関数呼出しを最大3段、noinline境界まで列挙します。実際のbackend inliningやメモリ原因とは区別します。

保存済み最新生成コードでは、`effectiveCharge`へ直接、およびstart／wait helper経由の呼出経路があり、その先の`rawEffectiveCharge`はnoinline未指定です。次の比較候補はこの1関数の共通境界で、数値とcallback順序を保持してMetal327の全rawを比較してから、必要なcompiler-only検証1回を検討します。旧v110との性能差を、この1変更だけの因果として扱いません。今回はWindowsの再コンパイル・GPU実行は0です。

根拠は`research/portable-skill-critical-development-checkpoint.json`と同prefixの原失敗・retention・Metal記録、および`research/portable-weapon-query-call-graph.json`です。
