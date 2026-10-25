# 元ミハラの敵DoTスタック加算

`coordinate-original-enemy-stack` はミハラ：ボンディングチェーンの元定義を保持する4入力です。対照4秒・命中上限11秒・実戦闘不能4秒・元burstの引継ぎ8秒、seed3801。完全5人編成・武器・成長・autoを使い、効果書換えやCPU算出の発火予定の入力はありません。

対照／戦闘不能／引継ぎは全77定義の既定編成、命中ケースはドレイク／ミランダ／ドラー／ミハラ／メアリーの全78定義です。ドレイクを先頭B3候補に置き、ミハラ自身のburstによる元DoT解除を待たず、フルバースト中の実命中による10→…→20加算と、上限での再発火を検証。戦闘不能時は10＋20を20へ制限します。射撃・発火時刻は共有実行器が導出します。

既存 `world_original_stack_native.capture` に明示的なselected_rowsを追加し、既存source observerのcarrier／DoT時計読取りを再利用。既定のbuff観測範囲は不変。`compare_source_state` はfield／operation引数を追加し、旧source操作の既定比較を保持します。最終stack・所属・activation／期限・次tick、各元効果の発火数・ゲージ・全battle／packet／RNG／control／healthを検査します。

最初のCPU baselineは、4秒の対照が既にburst引継ぎ済みという誤った観測仮説を拒否しました。元の4秒ケースを初期DoT保持の対照として検査し、8秒の元引継ぎケースを別に追加。元失敗logを保持し、GPU実行前に修正しています。

## 検出した実装漏れと修正

初回Metalは全status0、有限DoT引継ぎだけが一致。加算対象を通常のactor-recipient領域だけで判定していたため、専用snapshotに対象を持つDoTが取り残され、命中／戦闘不能とも最終10のままでした。既存共通stack loopの対象照合へ `worldPeriodicNamedMember` を接続。周期領域には論理slot、通常recipientにはtag付き参照を渡します。数値変換・上限・lifetime・通知は既存共通処理を継続し、CPU正本・binary64・wire・Runtime138952byteは不変です。

この修正は固定shared入口のmacroだけで有効です。厳密なsource inverseを追加し、旧cover入口のCUDA/MSL原生成物は全byte一致を確認。新コードは正しくcache identityを変えます。初期のデータ追加ではSlang0でしたが、実装修正にはpaired Slang生成2回と新Metal pipeline93.950324秒が必要でした。source-reuseはこの変更を拒否し、key/normalizerを緩めません。最終登録packetは同じ修正版の生成cache必須hit・Slang0。pipelineのファイル検査は成功しましたが、新コードの実warm loadやCUDA実機cacheの証明へ数えません。

別のhost reader漏れとして、DoTの無限期限を表示用1e30と比較していました。元wire doubleを読み、正の無限大と有限1e30を区別する回帰検査を追加しています。

## 検証と残件

修正版M5 Metalは全4status0・CPU一致、GPU1.499809秒。全4input/native指紋を保持し、変更のない対照と引継ぎの全14,158,848byteも保持。実GPU計2回（比較失敗1保存・修正版1成功）、同claim retry0。独立GPU禁止childで全4fresh再計算48.621108秒・live parent receiptなしでsealしました。

最終packetは `/tmp/nikke-original-enemy-stack-final-v1.zip`（9dd7761e…、1997files）。検査・全payload byte検査・raw保持の記録は `research/portable-original-enemy-stacks-checkpoint.json`、証拠は `research/original-enemy-stack-evidence/` を参照してください。過去sourceのgoldenを今回の結果で書き換えません。旧不変packet・失敗・claimを保持しています。

アンカー：イノセントメイドの減算21は別の未完項目です。元編成の46秒／別編成64秒調査で正の発火は未確認。実notify観測では、64秒でもFB開始は4.316667／44.316667秒の2回、先頭B2マスト・B3ドレイクを40秒待っていました。発火0を対応証明へ数えません。次は宣言したburst rulesの交互選択で3回目へ届くかを調べ、既定autoの86秒ケースも候補として残します。いずれも未検証の予測です。filtered observerの64秒調査は正本との同条件比較が未実施であり、認定goldenではありません。

ADD対象・世代を含むこの修正の元キャラ実戦ケース、kind21/34/35/37、19入力変換失敗、モデル／variant、現在のCUDA・公開GPU・全キャラ認定も残ります。全キャラ0／通常UI CPU／ゴール未達です。
