<!-- native-query-observation-current -->
共通Slangへログsnapshot・初回/変化HP同期・期限切れログのlazy確定を接続。ログ有効/無効、満HP初回回復、終了通知から同効果再発動を含む25入力が同121sourceのMetalで全一致し独立seal成功。リリー30秒は4550抽選の全semantic順序・最終MT・原文battle/全射撃履歴まで一致。正本6編成の元指紋保持、CPU/数値/normalizer不変。読み取り専用census/windowをCLIへ追加し、診断領域以外の全byte保持を確認。旧1330＋新25の1355回帰も同121sourceでMetal全一致・独立fresh seal、CPU91群482検査成功。旧1326件のraw全4,171,235,328Bと新25件は全byte一致、既記録のselector25修正4件だけ各2B変化、旧1330のnative指紋は全保持。GPU11.14889秒/生成cache必須hit/追加Slang0。初回は旧散弾のno-op故障注入でGPU前停止し、監査層へprojectして確実に変異させるテストへ修正。Windows追加操作0/7終了原因unknown/保全false、全キャラ認定0/UI CPU/ゴール未達。詳細docs/portable-native-query-observation.mdと対応checkpoint。以下は履歴です。
<!-- /native-query-observation-current -->

# 全選択順の履歴方式と実編成の残差分

共通CUDA/Metalに`ordered_history_runtime.slang`を接続した。先頭128件の生履歴を保持し、129件目から64wordの追加bankを使って全recordのsemantic atomをSHA-256へ順次投入する。計算を128件で止めず、生履歴を省略した件数も明示する。最大1,048,576件でerror64、version/件数/finalization/予約wordも検査する。

追加bankは781792..781856。既存numeric-query bankの直後で、診断末尾786416より前。出力stride786432word、Runtime field追加0。128件以下では追加bankを一切書き換えない。通常の旧経路は今まで通り128件上限を維持し、native numeric readerを有効にしたprivate経路だけが拡張を使う。

semantic atomは8wordのLE列。sampleはowner/selector/人数/pool/順序/MTの前後index、revivalはevent/owner/HP/ammoを含む。sampleの時刻word6/7、revivalの時刻word2/3は明示的に0としてhashする。**このSHAは時刻を証明しない。** 戦闘・physical shot/skill traceの時刻は既存の全比較で引き続き検査する。輸送normalizerやbinary64/int/powは変更していない。

## 完了した単体検証とCLI

`ordered-history`は0/1/2/127/128/129/130/255/4550/8192件の10正例と、hard cap/拡張無効/未知kindの3拒否。混在したrecordから独立hashlib oracleを作り、順序・全semantic hash・padding・最終state・予約word・領域外書込を検査する。prefix/suffix値/suffix順序/header/最終状態等の故障も拒否する。

不変packet `/tmp/nikke-ordered-history-probe-v2`、id `f523eceb48ab61633734c1edadf8662a064c1e55ec494e637642c120a1bdb7c9`。Apple M5で13入力成功・fresh独立seal成功。実goldenを保存し、この**単体suiteのみ**通常CLIへ登録した。通常packet `/tmp/nikke-ordered-history-probe-release-v1`はCPU6検査成功。`package --suite ordered-history --out <new.zip>`で利用できる。これはbattle/full-character認定ではない。

最初のprobeはresident専用のgeneration cache指定により、Slang/GPU前に停止した。CLIはこの不適合をCPU事前計算やcapture/claim取得前に拒否するよう修正し、2CPUテストで固定した。旧失敗capture/claimは保持。独立probeでは`--generation-cache`を付けない。本体のpaired resident生成cacheは従来通り利用する。

## 実編成から修正した二つのconsumer

1. 正本`_LAZY_RESOLVE_PREFIXES`に`allies_broken_cover_random:`は含まれず、発動時に確定する。GPUがlazy対象にして空poolを数値照会のたびに再抽選していたため、pack時のselector25 lazy groupだけを0へ修正した。他group IDは保持し、GPUもselector19はlazy必須/25はlazy禁止として検査する。旧30入力のうち4件だけ、recipient flagの21→5が各1word変わる。`portable_eager_cover_migration`は記録した差分を戻し、全30入力・各caseを旧goldenのSHAへ完全復元する。旧goldenや正本CPUを差し替えていない。
2. 正本landingの吸血処理は率0でも`get_buffs`を呼ぶ。これを省いたため命中後buff更新で必要な再抽選が欠落した。既存の吸血continuationを再利用して数値照会を接続し、post-hit mutationを独立6番目のCPU契約へ追加。248照会/155hit/93抽選を固定し、既存5契約の期待値は保持した。

クールダウン補正0でも正本が数値照会する入口、チャージ終了・初回charge命中・full burst切替のcache破棄と照会順も接続した。旧経路の省略は維持し、native numeric reader有効時だけ必要な照会を追加する。

## 現在の結果：戦闘はまだ未完了

`ordered-history-battles`は短例13（native6/拒否7）＋原文全定義の実3編成×3秒/30秒6＝19入力。同じ119sourceで、**18件一致、リリー30秒だけ失敗**。`/tmp/nikke-ordered-history-battles-v2-metal`を保持している。battle成功goldenやsealは作っていない。

リリー30秒の抽選は正本4550対GPU4542、8回不足。先頭128件の選択/MT位置と、そのうち時刻を観測できる126照会は一致するが、physical shot205（0始まり、3.9666666666666575秒）からdamage差分がある。原文6入力の全native battleとfull traceは、最初の失敗packetの6指紋を全て保持した。CPUをGPUへ合わせた修正はない。

最終不変packet `/tmp/nikke-ordered-history-release-v1`はCPU55検査成功、`reference --suite late-attack-random`の6契約もGPU/packing0で成功。元の実編成失敗・本体v1/v2・probe初回停止等のpacket/raw/claimは保持、GPUの同一再試行なし。

次は3.85..4.0秒前後のGPU辞書照会owner/target/除外/epoch/hit/missを、計算に影響しない診断経路で保存し、正本の同じ照会と対照する。先頭128sampleの外で始まる不足を直接観測してから修正する。readerを一律に増やして帳尻を合わせない。

`ordered-history-retention`（旧1330＋新19＝1349、native1066/拒否283）は登録したが未実行。リリー差分の解消後、同じsourceで一括保持検証する。selector25の旧4入力だけは明示的migrationで監査し、無関係な入力/出力の変更を許さない。旧1330や旧native-query12の証拠は以前のsourceのまま保持する。

容量確保のため、成功済み旧raw1個をCPU-onlyでゼロ領域回収した。2,670,723,072Bの長さ/path/inode/全SHAを維持して1,898,971,136Bの割当を回収、raw削除0。容量回収は計算証明に加算しない。

Windows操作/CUDA実行0、NVRTC cache hit未検証、7プロセス終了原因unknown・環境保全falseを維持。全キャラ認定0、通常UI CPU、全目標未達。SHA/packet/失敗・保存記録は`research/portable-ordered-history-checkpoint.json`。
