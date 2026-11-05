# バースト操作と戦闘実行器の接続

`coordinate-burst-control` は、単体実証済みの `gpu/burst_control_policy.slang` を既存の `burstFrame` と `coordinateAimBurstEnd` へ接続するprivate world入口です。候補選択・実押下待機・次FB予測は同じproducerを使います。CUDA／Metalで効果・数値演算・テストを分岐しません。通常UIの公開GPU受付や全キャラ認定とは別です。

## GPUが保持する時計

`coordinate_burst_control_runtime.slang` が既存Runtimeのready・phase・down・stun・再突入状態と、出力bank内の段階開始時刻・完了周期数をpolicyに渡します。CPUからcast時刻・ready・予測・候補maskを入力しません。

- `burstFrame` 冒頭の有効候補段階を5人分cacheし、full-end通知でbuffが変わっても、そのtickの次FB予測ではこのsnapshotを使います。
- 初回stage1は現在時刻、段階切替と再突入は次のaction時刻でstage-openを更新します。本人cooldown待機・delay待機では更新しません。
- full-endで完了周期数を増やしてから未観測の次FBを予測します。観測済みの周期外挿は既存の共通時計を使います。
- cooldown待機maskの既存min更新と、maskを作らないdelay待機を区別します。共通のcooldown減少handler kind5は、この新descriptorが有効な場合だけ追加受付します。旧入力の受付範囲を広げません。

## 配置と保持

入力は旧109792wordの後に176wordの静的burst descriptorを加えた109968wordです。既存251入力には固定のdisabled descriptorだけを付け、旧prefixとnative値を保持します。GPU側はdisabled時も全176wordが既定literalと同じことを検証します。

出力は1769856word、Runtimeは既存の247field／138952byteのままです。squad bankの末尾18word（絶対1769838〜1769855）を新しいstateが所有します。

| bank相対word | 内容 |
| --- | --- |
| 0 | burst magic |
| 1 | 完了周期数 |
| 2〜3 | stage-open binary64 |
| 4〜8 | tick冒頭の5人の候補段階 |
| 9 | 予約0 |
| 10〜13 | 各tick終了状態の2種類のrolling hash |
| 14 | 実tick数 |
| 15〜17 | 予約0 |

毎tickのhashは、時刻、phase、再突入、action、stage-open、周期数、候補段階5人、cooldown wait mask、ready5人の全25wordを含みます。正本の実 `BurstController.tick` のreturnを受動観測し、同じ順に照合します。新領域を親比較器から射影する際も、新比較器がこの18wordの全てを検証します。

## 正本と静的literalの境界

`world_burst_control_native.resolve` はpinned runnerの `build_config` でcatalog pattern・delayと明示configの優先順位を解決し、CPU正本にも同じ静的configを渡します。`wait_own_cooldown` は正本どおりchar.controlから読みます。明示段階flagとA段階もGPUの静的weapon指定に対応させます。保護されたCPU実装・pinned upstreamを書き換えません。

既存のcover-policy packerには、新adapterがburst軸だけを除いた静的controlを渡します。正本simulateには元のcontrolを渡し、比較時のcover mask再計算にも同じ射影を使います。simulateや予測結果をpackすることはありません。observerは例外時も元のprofileを復元します。

33編成はdelayの3段階・遅いready・本人waitの範囲内外・false・空pattern・every/null・明示順序の終了後fallback・欠けた段階・A・明示段階・down/stun・待機中のcooldown減少・再突入・reload into_fb・cover/squad合成・full-end段階変更・隣接浮動小数値を含みます。旧251入力と不正wire9を加えた293入力が検証対象です。全キャラの元定義を実行した認定ではありません。

単体policyはbinary64の二重includeを避ける条件を加えた版でも、新しい固定packageから381入力を再実証・独立sealしました。旧単体の全input／raw／生成CUDA／MSLと全byte一致し、元のgoldenは残して `portable-burst-control-policy-shared-short-expected.json` を新規登録しています。

実行結果・独立監査・旧raw保持の到達点は `research/portable-coordinate-burst-control-checkpoint.json` を正とします。Windowsへの新しい実行依頼とCUDA cache性能の認定は、Macでの一致から推測しません。

CPU監査の全293比較は通常195.023秒かかったため、GPU禁止のseal／compiler-certificateだけ上限240秒を明示可能にしました。GPU・Windows・compile・CPU test群の180秒上限は変更しません。180秒で開始した初回CPU監査は既知の枠不足として子のみ中止し、GPUは再実行していません。上限分離・240秒受渡し・241秒拒否・GPU181秒拒否はCPU検査済みです。

共通CLIのGPU前native照合では `preparation.jsonl` にケース番号・名前・件数・nativeの有無・開始／正常終了／例外・所要時間を記録します。指紋が一致した後にだけ成功を記録し、全件完了前は入力を公開しません。正常・指紋不一致・正本例外を含む13検査を通しています。これは進捗記録で、processの生存や全体成功の証明ではありません。

遮蔽物破壊とdownの順序は、新入口が有効な場合だけ `worldCoverBreakLog` に既存hit履歴から数えた先行down数を記録し、復元器が正本どおりにinterleaveします。予約bitのmarkerで旧arg=0を区別します。全員cover→貫通5人、非貫通のcover破壊だけ、別queryで先行down、最後の対象のcover破壊の4編成を追加。v1の遮蔽物／HP計算自体は一致していたが、ログ順序が逆でした。旧251入力は従来の記録形式を維持します。

実証は293入力（native246／拒否47）の全件一致・別process独立seal済みです。旧251の全1,776,935,424byte、初版で成功した287の全2,031,794,688byteを保持。初版289全input／nativeは同一で、rawの差は記録済みの失敗2件だけです。正本の再突入は現在段階の候補を再選出し、各段階・周期で1回だけ開く契約を保持します。全キャラ認定・current CUDA・warm cache性能はこの実証に含みません。

最終compact package `c4de2a88…`（1846 files／ZIP 8,475,998byte／展開53,629,442byte）は専用12検査・全246 nativeのCPU再照合・共通制御446検査（Windows専用1skip）が成功し、終了後に全payload SHAとcheckout全byteの一致を検査済みです。最終captureは `/tmp/nikke-burst-control-final-cpu-v1` と `/tmp/nikke-burst-control-final-control-v1`、archiveは `/tmp/nikke-burst-control-final-v1.zip`。GPU追加実行はありません。
