# 共通GPU実行器の全体レビュー

対象は `18b93b8`。Claude Codeによる外部レビューをCodexがコード・保存計測・CPU再現で照合した記録です。レビュー中にGPU検証・Windows検証・計算コードの変更は行っていません。

## 結論

共通Slangに数値・状態・イベント処理を置き、CUDA／Metalを薄い実行アダプターにする方向は維持します。全面的な実行器の書き直しを支持する根拠はありません。ただし、現在の進捗を全キャラ対応へつなぐには、未対応分類の精度と、実編成検証を共通CLIへ載せる作業を優先すべきです。

静的packingは180/266プロファイル（基本キャラ126/203）。全キャラ実戦認定0、通常画面CPU、新版CUDA数値一致未確認です。packingの増加を実戦認定へ換算しません。

## 確認した改善点

### 中：別の未対応トリガーが同じ分類へ集約される

`app/portable_readiness.py:22` のsignatureはkind/stat/target/scalingを持ちますが、未対応のtiming／conditionを識別しません。現在のinventoryでも、同じcodeに次の異なるメッセージが含まれます。

- `multi_hit:2` と `multi_hit:4`
- `non_full_charge_fire_count:3` と `squad_burst_cast:1`
- `squad_burst_cast:1` と `squad_burst_cast:2`
- `self_undying` と `squad_burst_cast:2`

標準ライブラリだけのCPU再現でも、同じ効果座標にある`trigger_hit_crit`と`not_core`のcodeが一致しました。`summarize`のsampleは後勝ちなので、代表メッセージだけでは他の不足が見えません。

修正方針は、validatorから未対応operatorの構造化した識別子を返し、timingとconditionを区別して集約し、診断メッセージ集合も保存することです。全triggerの文字列をそのままキーへ加えて、同じ演算を不要に細分化することは避けます。現在のinventoryには「同一profile内の単独codeが異なるメッセージを隠す」例はありませんでした。単独ブロッカー件数が既に過大という断定はしません。

### 中：小規模の機能検証と実編成回帰の経路が分かれている

`app/portable_world_roster_input.py:17`と`app/portable_projectile_roster_input.py:7`に、全定義を渡す実編成のコンパイル経路があります。しかし、`research/verify-world-projectile-rosters.py:16`の実編成群と、共通CLIの`SUITES`、`research/verify-world-readiness-short.py:11`のliteralな回帰群は別管理です。

ゲーム処理が全く接続されていないという意味ではありません。現在の共通CLIで、未対応効果追加→実編成の準備→native比較→Metal実行→同じ入力のCUDA比較を一貫して扱う部分が不足しています。

既存の実編成compiler・binding proof・native comparatorをadapterとして再利用し、少数の代表編成を共通CLIへ登録します。旧goldenを自動更新せず、新しい版の入力・出力・差分を保持します。全キャラの一括GPU検証を先行させる必要はありません。

### 中：効果追加時の整合確認が複数箇所に分散する

受付は`app/portable_runtime.py:40`、stat集合は`app/portable_damage_specs.py`、raw入力の検査は`gpu/admission_runtime.slang`、実行は各Slang runtimeにあります。stat IDはcanonical定義を再利用していますが、受付条件・必要なworld能力・対象範囲・検査ケースとの対応は個別の分岐です。

これは今回確認した新しい誤計算ではなく、追加時の保守リスクです。IDと能力要件、validator／packer、対応テストを結ぶ小さなレジストリと整合検査を段階的に追加します。ゲームロジックのすべてを汎用レジストリへ書き直す案は採用しません。

### 低：CUDA終了処理の例外が本来の失敗を隠す

`app/portable_backend.py:249`では、`finally`内の`cuCtxDestroy_v2`も例外を投げる`call`を使います。実行失敗とcontext破棄失敗が同時に起きると、表に出る例外が終了処理のものになります。元の失敗とcleanup失敗を両方保持するよう改善できます。

これは実機で同時失敗を観測した報告ではありません。制御フローから確認した診断上の問題です。fake driverによるCPU故障注入で検査できます。

## Claudeの提案をそのまま採用しなかった点

- **展開先を変えると必ずCUDA cache missになる：不成立。** headerの絶対パスはtoolchainの場所です。固定toolchainを共有し、同一生成byteを別package rootへ置いたCPU再現は同じkeyでhitし、コンパイル関数は呼ばれませんでした。toolchainの移動時にはmissし得ますが、`original_workspace`指定がcache問題を回避するわけではありません。exact-byteのcache keyを単純に相対パスへ変更しません。
- **stun終了時刻を次回burst時刻に入れないため再開しない：未確認。** `gpu/combat_runtime.slang:389`はGPU内部の60Hz frameごとにtick→squadFrame→burstFrameを実行します。時刻を直接予約するだけの実行器ではありません。既存stunテストにも、先頭B1候補を保持して期限後に再開するケースがあります。より細かな非整列境界テストは候補ですが、現状を不具合とは認定しません。
- **効率の問題はCUDAコンパイルだけ：根拠不足。** 実編成への接続、未対応分類、検証経路の分散にも作業コストがあります。実戦のGPU性能は未計測です。
- **O1失敗後にO0も続けて試す：自動では行わない。** 保存結果を診断して次の仮説を決めます。今回のレビューではWindows実行を追加しません。
- **ptxasのインライン化が主因：仮説。** 巨大な生成コードとコンパイル／module loadでのtimeoutは整合しますが、主因の測定はありません。`noinline`追加や実行器分割は、生成コードと計測で判断します。

## 時間の根拠と次の順序

保存済みMetal記録では、stun46のlibrary作成1.020秒＋pipeline作成11.069秒に対し、GPU実行0.162秒でした。同一ソースの後続readiness81は作成合計約0.0032秒、GPU実行0.039秒です。毎回cold compileとみなして独自cacheを優先する根拠にはなりません。実編成の速度へも一般化しません。

Windows旧版のPTXはNVRTC約44.6秒の後にmodule loadで上限到達、CUBIN O3はNVRTC中に上限到達し、いずれもkernel実行0でした。新版のcompiler-only CLI、60秒・Job 2GiB・required-cacheは切り分けの方向として妥当ですが、実機性能や新版のCUDA数値一致を証明するものではありません。

1. 未対応operatorの分類を修正し、既存監査器から優先順位を再生成する。同時に、代表実編成adapterを共通CLIへ登録して機能追加後の確認経路を揃える。
2. 既存の短時間Windowsコンパイル依頼の保存結果を確認する。成功時もcache hitと実CUDA数値一致は別に判定する。失敗時は同条件の再実行や期限延長をしない。
3. 未対応機能を少数ずつ、独立fixtureと実編成回帰の両方へ接続する。現inventory上位の`heal_overcharge_store`（5profile）、`skill_cooldown_reduce_pct`（4）、`projectile_dmg_pct`（3）、`trigger_count_reduce`（3）、`trigger_hit_crit`（3）などを、依存関係と実装範囲も見て選ぶ。人数は解放予測や認定数ではない。

## 外部レビューの実行範囲

Claude Codeの認証を通常のmacOS環境で確認しました。読み取り専用のリポジトリ探索付きレビューは480秒で最終出力が得られず、timeoutとして保持しています。その後、関連コードの行番号付き抜粋と保存計測を渡し、ツールを無効にした限定レビューはexit0で回答を取得しました。従って、全リポジトリをClaudeが調査完了したという主張はしません。

Claudeの原回答はローカルの`/tmp/nikke-claude-review-18b93b8-focused.txt`、上記はCodexが照合・選別した結果です。今回の再現は分類キーとcacheだけのCPU処理で、NVRTC・driver・GPU呼び出しは0です。ソフトウェアbinary64と出力比較基準は変更していません。
