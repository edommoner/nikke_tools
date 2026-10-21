# 共通GPU実行器の追加レビュー（ddfadc3＋作業差分）

Claude Codeの回答を取得し、Codexが該当コードを照合した記録です。以前のレビューは `docs/claude-architecture-review-2026-10-21.md`。今回は現在のstaged差分と、共通実行器・入力検査・回復貯蔵・保存計測の関連抜粋を渡しました。Claudeのツールを無効にした限定レビューであり、全リポジトリの探索完了を意味しません。計算コードは変更していません。

## 判断

数値・状態・イベントの本体を共通Slangへ置き、CUDA／Metalから同じ定義とテスト入力を実行する方向は維持します。全面的な書き直しを支持する具体的な根拠は今回も得られませんでした。改善の優先対象は、実装済みの動作と複数の入力受付条件のずれ、回帰群への検証の統合、CUDAコンパイルの切り分けです。

静的packing187/266、基本キャラ130/203は対応認定数ではありません。全キャラ実戦認定0、通常画面CPU、新しい作業差分のCUDA数値一致は未確認です。回復貯蔵36ケースの先行Metal成功とは別に、拡張実編成回帰184件には4件の受付失敗が残っています。

## 確認した改善点と次の順序

1. **中：受付条件と共通実行器の接続を揃える。** `gpu/world_actor_fields.slang:26`、`gpu/event_runtime.slang:248`、`gpu/counter_landing_runtime.slang:16`などに受付知識が分散しています。AnchorとSoraの3秒／30秒、計4入力が現に拒否されています。保存診断はAnchorがactor pool内の定義検査、Soraがtarget counter内の定義検査へ到達したことを示します。Anchorの行にはC_STATIC条件があり、`teamAdditionalCondition`などの追加受付にC_STATICがありません。kind6の周期回復だけを原因と断定しません。Soraのkind26はcounterの既存kind集合に含まれません。まずこの2定義を正負の独立fixtureで再現し、既存共通処理の意味を確認してから受付を拡張します。4件を除外したり期待値を拒否へ変えたりしません。長期的にはkind・必要能力・検査箇所・テストを結ぶ小さな対応表と整合検査が有効です。
2. **中：回復貯蔵を通常回帰へ昇格させるまでが機能追加。** `research/verify-world-regression-short.py:17`のADAPTERSに回復貯蔵はまだありません。現状は開発中として妥当ですが、共有経路を変える機能を個別36ケースの成功だけで完了させないようにします。4件の拒否修正後、成功した新ソースの証拠を明示sealし、golden・suite件数・共通回帰を同時に揃えます。現goldenのstale状態を自動更新で隠しません。
3. **中：境界条件の独立fixtureを補う。** stat74のpolicyとmetaを同時に0へ改変する負例、負のHP drainで上限超過した後にstorage→healする順序、lazy対象選択＋lifestealの組合せが候補です。これは確認済み誤計算の報告ではなく、検証の不足です。native状態の観測を比較元とし、GPUの計算式を期待値として複製しません。
4. **中：CUDAは保存記録を解析してから、仮説を1つずつ測る。** 最新の保存結果はNVRTC呼出し約30.109秒でptxas allocation failure、GPU呼出し0です。静的な関数サイズはコンパイラのメモリ原因を証明しません。まず保存済みPTXの解析器を正し、コードの分割や有効機能の絞り込みについて具体的な比較仮説を立てます。Claude提案の複数サブシステムを外す5種類のWindows実験は、そのまま一括実行しません。実行する場合も必要な1比較だけを既存の短時間・メモリ制限内で行い、数値一致とコンパイル成功を別々に扱います。

## 照合して採用しなかった指摘

- **「mode5の回復もstorageへ入れる」：不採用。** `gpu/event_runtime.slang:1225`と`:1780`のmode5はmaxHP buffのHP付与です。モデルはmaxHP付与を貯蔵対象にしません。通常回復はmode3、lifestealはmode17です。すべてのHP書込みを同じ回復関数へ集約する提案は、意味の異なる付与・同期・復活まで変えるため採用しません。
- **「stat74が64要素の配列を越える」：現コードでは防止。** `gpu/event_runtime.slang:934`が`d.stat >= 64`を除外しています。
- **「入れ子queryを無条件に終了する」：現コードでは防止。** `gpu/lazy_runtime.slang:92`は既存query中にfalseを返し、呼出側は自分で開始した場合だけqueryActiveを0に戻します。
- **「policyとmetaが両方0なら検査が実行されない」：不成立。** `gpu/event_runtime.slang:2167`は`validProtection`をmeta値で省略せず呼び、`:275`付近でkind0/stat74＋policy0を拒否します。独立負例の追加自体は有用です。
- **「storageを常にincludeするため全entryのptxas負荷が増える」：未測定。** includeされた未使用関数がすべて同じ最終コンパイル負荷になるとは限りません。新storageより前のソースでもallocation failureは発生していました。機能別defineは共通実装を保った比較実験の候補に留めます。
- 診断末尾16wordの衝突は今回未立証です。必要ならschemaの使用領域と予約末尾の整合検査を追加します。未立証の衝突をバグとは報告しません。

## 今回の確認範囲

Claude Codeはexit0で回答。Codexは上記のコード経路を読み、CPUの回復貯蔵6テストとコンパイル統計2テストを実行して全8件成功。GPU・Windows実行、NVRTC、golden更新、計算コード修正は0です。過去のportable653件成功を今回再実行したとは主張しません。全ツリーのテストには既知の失敗があり、全リポジトリ成功とは扱いません。

外部レビュー原文はローカル `/tmp/nikke-claude-ddfadc3-review.txt` に保持しています。原文は未照合の指摘を含み、本書が照合後の判断です。

- reviewed HEAD: `ddfadc3a1fe3285f7a4c95bebe3ef2daaae7f7e5`
- staged diff SHA256: `0c2b372e87c6b24980e2d3908922a2f23b246bc84b521edf9c9e83cbaa1dfe5e`
- Claude raw SHA256: `ebf388b0ca4ff25ba6460710be896ef973455ee1caa8377969b2a87e473356a4`
