## 2026-11-03 混合場面の実ダウン・復活を通常Metal APIで確認

Claudeが選んだ36秒typed／Lock On／敵回復／手動遮蔽の混合1構成と対照が合格。元MirandaをRapunzelへ1名変更し、元Soldier O.W.が2.75秒down→3.833333秒に元B1の81.67%（1994253.9948HP）で復帰→4.75秒に再down。遮蔽HP2800を保持し、GPUの既存revival traceのowner／時刻／HPとboss履歴がCPU観測と完全一致。対照はdownのみ。[要求2件・全SHA・範囲・失敗保持](../research/product-mixed-revival-v1.json)。

CPU観測有無4実行の全native／公開payloadが一致。通常HTTP Metal2条件・2dispatchとfresh CPU2も完全一致、追加battleなしの独立保存監査2成功。Metal実行と監査は計15.27秒。新standard profile加算0、標準266の計算／packer／decoderは不変で再実行せず、受入済みCUDA専用host guard以外の全ソース一致を確認。共有コード／数値規約／正本／golden変更0、Windows接続を含め0。

初期fixtureの不成立2件・静的owner参照ミス・保存ログのoutcome/detail読み違いを保持。原HP・CPUログや期待値を書き換えず、最後の読取りミスは保存結果だけで解消した。実行はb3141d77のclean runtime-residentで、メインcheckoutの未commit storage作業は使っていないことも記録。CUDAと、他の混合構成での復活は未検証。次はClaude方針のCPU由来handler有限残件台帳。Windowsは明示再開まで確認・依頼しない。以下は過去記録。

## ユーザー指示：Windows再開の明示までMac開発を継続

現在のゴールと優先順位は[current-gpu-goal.md](current-gpu-goal.md)を参照。Windowsの接続確認・status取得・依頼・復旧質問・監視は行わない。準備済みCUDA1要求と固定consumerを保持し、Macの未対応範囲をClaude方針／Codex実装／Claudeチェックで進める。過去の「接続復旧待ち／復旧後に実行」という記述は自動再開の指示ではない。

# Claude主導の開発とレビュー

2026-11-02のユーザー指示により、基本の役割を次のとおり変更する。

- Claude：完成条件、残件の優先順位、次の実装単位と受け入れ条件を提案する。
- Codex：提案の事実をコードと記録で確認し、合意した単位を実装・検証する。
- Claude：固定した差分と検証結果を読み、受け入れ／修正要求／情報不足を判断する。

CodexはClaudeの指摘を無条件に正しいとは扱わない。誤認や制約との衝突は根拠を示してClaudeへ戻し、独自に別の大きな方針へ切り替えない。ユーザーの指示が常に優先する。

## 反復の境界

1. 次の実装前にClaudeの指示、変更対象、最小検査、終了条件を記録する。
2. Codexはその範囲を実装し、入力・コード・依存が一致する既存証拠を再利用する。
3. 固定commitの差分、実行結果、失敗、未確認事項をClaudeへ渡す。
4. 修正要求を解消し、Claudeの受け入れ判断とCodexの事実確認後に次の単位へ進む。

個人設定・認証情報・生GPUバッファはレビューへ渡さない。Claudeには原則、必要な抜粋と小さな検証記録だけを渡し、編集・実行ツールを無効にする。送信に承認上の停止があれば記録し、結果を捏造したり代替経路で迂回したりしない。

## 2026-11-02 方針レビュー完了

準備した14ファイルの抜粋・小JSON（119,395バイト）は、最初に自動承認レビューで送信が拒否された。その後ユーザーがこの具体的内容を明示許可し、Claude Codeによる読み取り専用レビューを実行した。追加の非公開コードを送らず、回答と事実確認だけで方針を再確認した。編集・実行ツール／MCP／セッション保存は無効。

元資料のSHA256：`0082288be50c760abf19b3af470556242a1c2b45d3966fc5864554c3d5eb823e`。対象commitは `9d34b136282f059acd108ae158ae5a0059db6747`。生回答と実行記録はローカル `proofs/claude-led-direction-v1-20261102` に保持する。

### 合意した完成条件

- 安全性：GPU一致または理由付きCPU fallbackで正本と同じ結果を返す。これは移行中の正しさであり、GPU対応完了ではない。
- GPU対応完了：CPU正本で意味を持つ効果・条件・依存相互作用から導出した有限台帳が、Metal／CUDAの両方で一致する。fallbackは残件として残し、完了へ数えない。
- 現在のnormalize許可集合だけで目標を狭めない。CPUが受理しnormalizeが拒否する範囲も残件に含める。
- 宣言モデルのCPU一致と、実ゲーム仕様の確認は別に記録する。
- 台帳の列挙方法自体が未確定なので、現時点で全目標完了は宣言しない。

### Claudeが選んだ次の実装単位

**製品APIの例外とCPU fallbackの整理（Pythonのみ）。状態：実装4155099d、Claude再レビューaccept、完了。**

対象は `app/portable_detail.py` と既存 `tests/test_portable_detail.py`。CPU正本4ファイル、Slang、成功時のdecode仕様、goldenは変更しない。

1. prepare／compile／transport／decodeの `Exception` を理由付きfallbackへ接続し、stage・error_type・tracebackを保存する。KeyboardInterrupt等のBaseExceptionは送出する。
2. CPU評価をGPU例外処理から分離し、要求ごとに1回だけ実行する。比較とfallbackで同じCPU結果を使う。
3. CPU例外はGPU未対応へ変換せず、cpu_errorを保存して同じ例外を送出する。再計算しない。
4. `product_ammo_cover` があるのに `product_enemy_ammo` がない異常metadataは、明示的に拒否する。通常生成経路にある欠陥とは主張しない。
5. 各段のAttributeError／IndexError／TimeoutExpired、CPU例外、KeyboardInterrupt、異常metadata、batchの1行だけ失敗、既存成功の不変を既存テストで確認する。新suiteや監査器は作らない。
6. 成功路の結果が変わる、または正本の変更が必要なら、範囲を広げずClaudeへ戻す。

Codexが確認した欠陥：現在はCPU評価がGPU用try内にあり、CPUのValueError等で再評価され得る。IndexError／AttributeError／TimeoutExpired等も現在の捕捉集合から漏れる。

Claudeのstride不一致懸念は、両INPUTが128124であり実Metal3件batchも成功していることを確認し、Claude自身が誤警報として撤回した。許可表の重複は構造課題だが、この単位では変更しない。

### 次へ進む条件

全差分、実行コマンド・出力（失敗を含む）、方針との相違、再利用証拠をClaudeへ渡す。ClaudeのacceptとCodexの事実確認がそろうまで、新しい効果合成や標準266の再実行を始めない。指摘が誤認なら根拠付きで返し、無条件に従わない。

後続予定は現source標準266の確認、CPU正本からの効果・条件・相互作用台帳、影響範囲の広い未対応の解消。CPU期待値の再利用は、入力・計算コード・依存の一致が確認できる範囲に限る。

### 依頼済みWindows結果

API1要求はCodexが `cuda_detail` を誤指定したため、既存guardが `cuda_shared_detail` の要求に合わないとしてGPU前に停止。POST／kernel／CPU戦闘は全て0。元要求・停止を保持した。修正と再送は上記単位に混ぜず後続へ回す。保存PTX／object／linked CUBINの成功、外側exit2／環境保全falseも変更しない。

Claudeが提案した外部実行前の確認は、ユーザーの既存の許可と実際の承認制約に照らして扱う。ユーザーは関連GitHub共有と必要な短いWindows検証を既に許可しているので、Claudeの提案だけを理由に同じ確認を繰り返さない。


## 例外処理単位の合格と次単位

Claude初回チェックはchanges_required。既存strict source ledger同期2ファイルへの最小拡張、batchのCPU例外テスト、ammo metadata正例経路の確認を指示した。4155099dで対応し、再チェックはaccept。製品テスト73、source ledger7成功、既存ammo8成功。旧互換失敗と旧ledger拒否も保存。Slang・正本・goldenは不変、追加GPU/Windows実行0。この合格はGPU対応profile数の増加ではない。

残件はcapture storage障害時の要求の扱い、CPU正本由来の被覆台帳、CUDA製品API、標準全件の現source確認。生成スクリプト本文は永続proofへ複製し、temporary-onlyにしない。

次単位は266要求のMetal通常製品経路。まずPhase0（読み取りのみ）で要求manifestの一意性・保存CPU対応・既存実行器・容量をClaudeへ報告し停止する。Phase1はClaudeの判断後に8件以下のpilot、続いて残り。runtime oracle cacheは導入せず、製品経路のGPU後CPU1回を使い、監査でCPU/GPUを再計算しない。全てgpu_match/fallback/mismatch/cpu_errorへ分類、fallback等を完成へ数えない。新しいCLIが必要かは、既存HTTP batch driverを優先してClaudeと判断する。


## 標準266 profileの最終チェック合格

4155099dの固定条件（180秒・期待値・seed0・core50・BODY1）で203キャラ／266 profile-stageを通常Metal APIで確認し、Claudeがacceptした。[全件と出所](../research/product-standard266-claude-accept-v1.json)。元条件のHTTP成功258と、sleep抑止条件を付けた別試行8の成功を選定した266件であり、original266成功とは表記しない。40物理dispatch／274実行case、成功payload266のCPU照合と独立保存監査、過去全rawとの一致。完了CPUファイルは既知271、元の完了不明3は不明のまま保持する。

旧timeout8、bind失敗、UTF8 scratch parser失敗、旧監査停止を保存。8の新試行は同じHTTP body・630秒・同じ415のままowned caffeinate -iを使用し、時計差0.519秒、元失敗rawとの直接比較も一致した。sleepとの相関は環境診断であり計算誤差へ付け替えない。historical3の当時dirty closure未証明ラベルとfull_payload_equal=falseは元記録のまま保持する。全266の旧CPUとの差分はevaluator stampだけで、除外も期待値更新もしていない。

公開CPU/GPU payload比較の除外はcomputeだけ。cache_hitはHTTP wrapper項目。既存監査器のoptional old_full_readback_anchor_verifiedは期待SHA未指定によりfalseのままで、別の全raw SHA照合266件の成功を明記した。今後は既存request envelopeへexpected_output_sha256を入れ、HTTP bodyや元要求を変えない。除外集合の拡大には別レビューが必要。

### Claudeが選んだ次の単位

保存linked CUBINがあるtyped-lock-healing36秒・index9のCUDA製品1要求。新bodyはcuda_detailをcuda_shared_detailへ直すだけで、Slang／selector／正本／数値規約は変えない。元のstatic停止を保持する。Metalのinput／全output SHA一致、fresh CPU一致、通常HTTP GPU成功、source／owner／全artifact admission、verify_phases、追加SDK0、独立保存監査を必須とする。CPU fallbackはCUDA成功に数えない。

WindowsはRAM4GiB一回確認、BelowNormal・fresh Job・2GiB・180秒・一回のみ。失敗は層を記録して停止し再試行しない。CUDA266／39dispatchを無条件に続けず、1件後はCPU由来coverage台帳と事前固定したsource-family代表deltaを優先する。fixed_battle_entryのCUBINは未成立なのでRapi等へtyped CUBINを転用しない。旧outer exit2／environment_preservation=falseは別境界で保持する。

ClaudeがCUBIN guardのpost-dispatch例外分類を指摘したため、その分離と故障注入を次単位で確認する。guardを変更した後のconsumerは新固定commitとし、Metal266の計算証拠は4155099dに固定して不要な再実行をしない。全特殊効果・任意場面・現在CUDA全件は未完了。


### CUBIN監査後の例外分類も合格

body_entered以降は本体・context終了時とも元の例外を保持し、verify_phasesを既存Journalでpost-dispatchとして記録。製品75検査、strict source ledger7成功、Claudeチェックaccept。[修正と検査](../research/product-cubin-post-dispatch-review-v1.json)。呼出側はGPU側Exceptionを捕捉してからCPUをtry外で1回評価し、GPU／compilerを再試行しないことを確認した。CUDA検証はCPU fallbackを失敗と数える。Slang・正本・decode・goldenは不変、追加GPU／SDK0。

verify_phases importの事前移動は非blockingの別unit候補として保持し、今回へ追加しない。Windows接続待ちには既存model-checkによるCPU由来coverageの読取りと欠落列挙だけを進める。完成条件・正本・goldenの変更や追加GPU実行は行わない。
