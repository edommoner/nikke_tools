後続の手動モード移行調査と正本26契約は [CPU契約記録](portable-manual-swap-reference.md) を参照。以下は弾消費通知のGPU接続時点の記録です。

# 弾消費相当通知を共通GPUへ接続

`squad_ammo_consume_as` をCUDA／Metal共通Slangのkind37へ接続しました。
`max(0, int(value or 0)-1)` 回の追加通知を既存の同期continuationで順次処理します。
実弾を追加消費せず、通知ごとの条件・発動上限・再帰・tick順序を既存dispatcherへ委譲します。
リテラル小数を入力に保持し、既存binary64整数変換でGPUがtruncateします。
self・有限±4096・private combatの範囲をhostとGPU双方で検査し、scaling等は拒否します。

Runtimeの追加fieldは0、stride138952、CUDA定数48Bです。正本CPU、既存CUDA、
binary64／整数変換／pow、strict normalizerは変更していません。
再コンパイル時に同じ静的geometryを渡し、actor poolにも既存のcore／optimal-range条件契約を接続しました。
CPUで計算した戦闘結果をGPUへ渡していません。
旧監査fixtureを変更せず、5 GPUファイルの有限deltaを別ledgerで逆投影して既存監査を再利用します。

## 検証と再利用

共通CLIのsealed入口は次の4つです。各成功結果を別プロセスで独立sealしました。

| suite | 入力 | 正本比較 | 拒否 |
|---|---:|---:|---:|
| ammo-equivalent | 46 | 29 | 17 |
| ammo-equivalent-catalogue | 1 | 1 | 0 |
| ammo-equivalent-rosters | 2 | 2 | 0 |
| ammo-equivalent-retention | 1088 | 870 | 218 |
| 合計 | 1137 | 902 | 235 |

旧1088の全input/native/output entriesとraw **3,422,552,064B** は全byte同一です。
旧nested suiteの指紋も保持し、source certificateだけを実証済みsourceへ更新しました。
full116／commands117の生成certificate14検査が成功しています。
CPU-only referenceは基本25、geometry4、原文効果1契約。packing／GPUは禁止です。
最終sealed packageでも8群54件のCPU検査が成功し、GPU claimは消費していません。
件数・package／seal指紋・時刻別の検査数は `research/portable-ammo-equivalent-gpu-checkpoint.json` を参照してください。

基本契約は小数・負値・0／1・4096、auto／charge順序、全体counterとowner別buff、
無限弾薬、重複descriptor、max_trigger付き再帰、periodic登録と後続tickを含みます。
geometry4契約はcore／rangeの成立・不成立を両側で検査します。
シンデレラ：クリスタルウェーブの原文効果を変更せず明示的なチャージ武器へ適用した1入力で、
2射・80通知・2dispatch・装弾8・ダメージ6000／12000まで正本と一致しました。
これは自然な実編成のモード遷移完了を意味しません。

全定義の実編成3秒／30秒は既定MG方針で、対象効果のdispatchは0です。
正本指紋を再確認した非発火対照であり、正例として数えません。
SR進入に必要な手動reloadの制御経路は未対応です。
この実編成の物理履歴は112／2048件、30秒では32件省略を明示して保持しています。
旧キロ／レム／ギロチンの履歴省略も解消していません。

## 時間と診断の改善

旧1088では正本CPU preflight62.609秒、CPU回帰64群376検査102.090秒、GPU10.670990秒でした。
主46のGPUは0.122608秒、実2は2.993574秒、原文効果1は0.045157秒です。
主46の初回Slang生成は2回、その後の成功3検証は生成cache必須・追加Slang0回でした。
commandsのCUDA／Metal両生成もCPUで確認済みです。実NVRTC cache hitやCUDA戦闘一致は未証明です。

初期の実編成失敗では、actor poolがadmissionと同じ診断stage4を上書きし、失敗箇所を誤読しました。
Claude Codeの読み取り専用レビューで重複を指摘され、sourceで確認しました。
実原因はactor-field受付にcore／range契約が欠けていたことです。
poolをstage8000へ分離し、段階番号の一意性・呼出箇所・一時controlコード除去の検査を追加しました。
途中のstatus変更・atomic診断・早期return実験は本体から除去し、失敗package／claim／rawは保持しています。
Claudeの確認はsourceの批評であり、tmp成果物の独立GPU監査ではありません。

静的packing225/266（base165/203）、未対応70分類はGPU対応率ではありません。
全キャラ認定0、通常UI CPU、全ゴール未達です。
Windowsは追加照会・native・compile・GPUとも0。7プロセス終了の原因unknown、環境保全false、
サービス未確認を維持し、新規検証を停止しています。ゲーム／動画との因果関係は未確認です。

次は未対応分類と正本consumerを照合し、手動reload／武器制御等の実行経路を契約化します。
CPU参照の再利用はsource/input全一致と独立監査を維持した設計が必要で、現時点では未実装です。
projectile／shield等をconsumer未確認のまま受付しません。
