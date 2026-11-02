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

**製品APIの例外とCPU fallbackの整理（Pythonのみ）。状態：方針確定、実装未開始、変更後レビュー未実施。**

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
