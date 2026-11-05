# 親プロセスの事前CPU照合結果を再利用

共通CLIの `manual-swap`／`manual-swap-rosters`／`manual-swap-retention` は、通常のGPU実行時に
同じ親プロセスの事前照合結果を再利用します。GPU本体・golden・正本CPU・native観測器・数値・normalizerは変更していません。
CUDA／Metalで共通のPython経路ですが、今回の実機確認はMacのMetalだけです。

## 再利用するものと比較の境界

事前照合では従来どおり全入力とnative指紋をgoldenへ照合します。その成功値を親のメモリ内だけへ複製し、
GPU子プロセスの終了後、既存比較器の正本取得口へ渡します。GPUのデコード、全項目比較、
拒否例ごとの検査、全readbackのサイズ／SHA、厳密な生成コード・CUDA API／artifact／containment／環境観測は維持します。
子プロセスへ正本の値を渡さず、GPU入力の作り方も変えません。

既知の `native_reference`、`suite.inspect_native`、実編成の `real.native_reference` という取得口だけを対象にし、
一時的な差し替えは比較終了・例外時に復元します。取得口を確認できない複合adapter等は従来どおり再計算します。
対応を推測して正本検査を省くことはありません。

この再利用は、保存した比較JSONを読むキャッシュではありません。CLIの独立 `audit`／`seal`／`replay` は
再利用オブジェクトを受け取らず、引き続き正本を再計算します。既存の `comparison.json` が成功でも信用しません。
通常の `run --cpu-only` とsmokeも、この再利用オブジェクトを作りません。

## 同一性と改変の検出

- package ID・golden・capture絶対パス・親PID・threadの同一性を要求します。入力ファイルのSHAとケース別SHAをストリームで再検査します。
- package全ファイルをGPU claim前と親比較前に再検証します。別package、変更されたsourceや入力、閉じたオブジェクト、二度目の比較には使えません。
- 各正本値の指紋をgoldenへ再照合し、戻り値をdeepcopyします。比較器による変更が次の値へ伝わりません。
- 取得口の関数identity、引数objectと内容を確認します。変更された引数・別の呼び方・比較中の入力変更は失敗になります。
- 入力fingerprintのpickleはメモリ内のhash算出だけに使い、deserializeやpickleファイルの取り込みは行いません。一つでもdomainを安全にfingerprintできなければ、その実行の再利用を無効にし、全体を従来のfresh prepare／比較へ戻します。
- 再利用オブジェクトは一度の親比較だけで消費し、成功・失敗どちらでもcloseします。値をartifactへ保存する形式や読込コマンドはありません。

最上位の大きなワード配列と全入力bytesは保持せず、比較に必要なdomain／metadataと正本値を保持します。
metadataが必要とする一部の入力列は残ります。メモリ上限を新たに保証したものではありません。

## 測定と検証

保存済みMetal1137入力（native902／拒否235）の全readbackを、再利用あり／なしで比較しました。
818正例を再利用し、84正例を再計算、235拒否例を検査しました。
全比較項目・全entries・output SHAが完全一致し、元captureのJSON／JSONLも全byte不変でした。GPU／NVRTCは0です。

| 処理 | 秒 |
|---|---:|
| 必須の事前CPU照合 | 64.800 |
| 再利用ありの親比較 | 11.833 |
| 再利用なしの親比較 | 68.414 |

親比較だけで56.581秒、約83%の短縮です。回帰検査・事前照合・独立audit／sealの費用は残るため、
開発全体が83%速くなったという意味ではありません。このCPU測定プロセスのpeak RSSは6,140,461,056Bで、
新旧比較の両方を含む値です。再利用による増分メモリやWindowsのメモリ実測ではありません。

通常実行経路は正式goldenの短い30入力でMetal検証しました。23正例を再利用し、拒否7例を検査、
全結果が一致しています。追加Slang0、GPU0.054426秒、CPU回帰13群90件成功。
その後、同じ保存結果を再利用なしの独立auditで再計算し成功しました。元の保存記録は変更していません。

新しい故障注入13検査と既存CLI／replay／stream／seal／batch／compile／linked-provider検査の計97件が成功しています。
正本値・domain・取得口・source・rawの変更、不意の呼出、別PID／thread／capture、再使用、
比較器例外、輸送失敗後のcloseとclaim保持、独立監査の再計算を検査します。
記録は `research/portable-parent-oracles-checkpoint.json` を参照してください。

初期のunit検査でsmoke／早期失敗時の初期化漏れを検出し、共通runの入口で初期化して修正しました。
その後の97検査と実Metal経路で確認しています。GPU実行の失敗や同一claimの再実行はありません。

比較receiptは `comparison.json` の `parent_oracles` にあります。`reused_native_cases`／`fresh_native_cases`／
`rejection_cases` を確認できます。この件数だけでは計算成功の証明にならず、通常の `calculation_verified` と独立監査を確認します。

CUDAのSlang生成cacheは維持していますが、これはNVRTC cacheとは別です。
今回のWindows追加操作は0、既存7プロセス終了はunknown・環境保全false・サービス未確認で停止継続です。
既存Metal1169の機能範囲を維持し、全キャラ認定0／通常UI CPU／全ゴール未達です。
次はこの経路を使い、未対応の制御・効果を共通実行器へ接続します。
