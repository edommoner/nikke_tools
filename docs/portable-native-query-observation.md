<!-- scratch-layout-current -->
旧scratch配置に部位スキル/割り込み集計/回復診断との重複を発見し、最大容量を保って分離。出力786432word/Runtime138952B/数値cache64/照準cache256/部位receipt2048は不変。NQRはpadding二bank、headerと履歴は割り込み集計後へ移動。排他的な二つの診断entryだけは領域共有し、同時macroを実Slangで拒否。共通CLI layout-check/layout-compareと読み書き幅・容量縮小・計算改変の故障検査を追加。Metal最大容量probe8＋実window1＋同122sourceの1355(native1071/拒否284)が全成功・独立fresh seal。CPU全92群487検査と最終小CLI10検査成功。GPU11.3868秒、normalizer/正本/算術不変。旧1302件は全byte一致、移動53件のcache/履歴と移動外4,260,934,400Bも保持。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/未達。次は混在consumer契約とprivate kind6の物理interrupt橋。18CPUケースが終了する試作は/tmp/nikke-private-interrupt-runtime-draft-v1.pyに保持し受付未開放。詳細docs/portable-scratch-layout.mdと対応checkpoint。以下は履歴です。
<!-- /scratch-layout-current -->

# 数値照会の観測とログ・HP同期consumer

共通Slangへ三つの正本consumerを接続した。正本CPU、保護対象のcompiler、binary64/int/pow、生成コードnormalizerは変更していない。CUDA/Metal別の効果処理は追加せず、同じSlangから両backendを生成する。今回の実GPU検証はApple M5のMetalだけである。

- フルバースト開始のログ用snapshotは、未確定の対象を各味方について直接選ぶ。通常の数値辞書照会でも対象のlazy確定でもない。CPUの実編成runnerはverbose=Trueなのでprivate compilerが明示的なログ方針を渡す。authored nativeは従来のverbose=Falseを保持し、有効・無効の両方を検証する。
- 明示的なHP同期は、満HPへの初回回復でも値のversionを更新する。private numeric cacheの予約headerへseen maskと5人のbinary64 HPを保存する。通常の派生HP計算と明示的な同期を区別し、reference-health方針では境界同期も観測する。Runtime fieldと出力strideは増やしていない。
- 期限切れログは、active集合から取り除き、state_endの子処理を終えてから未確定対象をlazy確定する。既存の終了通知continuationとlazy cacheを再利用する。ログ確定待ちのdead carrierは再利用を予約し、同じ定義が子処理で再発動しても古いsnapshotを上書きしない。

ログ方針はRECIPIENT_META+6のliteral boolean。+5のNQR1 tagがある場合だけ有効にでき、+7は予約0のまま。tagなしの有効化とboolean範囲外は拒否する。ログによる消費を全入力へ無条件に追加しない。

## 計算を変えない観測

共通CLIに二つのdevelopment-only診断を追加した。

```sh
python scripts/nikke_gpu.py package --suite native-query-diagnostic --develop --out <fresh.zip>
python scripts/nikke_gpu.py package --suite native-query-window --develop --out <fresh.zip>
```

両方とも元のリリー30秒入力をそのまま使う。診断entryだけがdisjoint bank 781856..785968（4112word）へ記録する。追加のget_buffs、対象選択、cache破棄、数値計算は行わない。通常entryでは観測関数の本体は空。CPU観測器も元の呼出回数、native結果と射撃履歴を保持する。

censusはowner0の各観測時刻で最初のmissを最大2048件、抽選累計とMT indexの2wordで記録する。中間の時刻はCPU側の順序上の文脈であり、個々のGPU時刻の証明ではない。windowは固定した短い時間窓内で最大256件のhit/miss、owner/target/exclusion/epoch/phase、binary64時刻・ATK・乱数位置を記録する。現在の窓は13.3..13.37秒。入力から診断結果をGPUへ戻す経路はない。

**診断はbattle認定ではない。** native-onlyのbattle指紋は文脈であり、診断comparatorが比較するのは観測streamだけである。censusはGPU側のprivate最終query（30.0秒）がCPUの最終frame（29.999999999999577秒）より1件多いことも省略せずに報告する。生の診断failureを成功へ書き換えていない。

13秒台のwindow診断v3とcensus診断v4は、通常版の同じ入力と診断領域以外の全バイトが一致した。v3は窓の開始時点で既に1回不足していることを示し、v4が最初の発生frameを絞った。`native-query-window-v1`がowner4のpost-heal missを直接特定した。その後のv5では期限切れ時のlazy抽選が次の不足箇所と判明した。失敗capture、raw、claimは保持している。

## Metalで成功した範囲

`ordered-history-battles`は、authored正例11、不正入力8、原文全定義の実編成6（ビスケット／リトルマーメイド／リリー各3秒・30秒）の25入力。

不変packet `/tmp/nikke-native-snapshot-battles-v4`、id `d63af63d578d73f16486b557150df9e049f5c4cc0e9bccc552331d752098fd43`。同じ121sourceで25入力すべて一致し、独立fresh sealも成功した。Metalの実GPU実行3.340834583秒。CPU事前検査55件成功。最新catalogでは新しい差分・診断の故障検査4件も追加した。

リリー30秒は4550抽選、先頭128生record、残る4422件を含む全semantic順序SHA、最終MT全stateが一致した。semantic SHAは`d535eb73d32c08670144e58222e1e25fcb7534b5b818490569698ec6bcf840b0`。時刻をhashへ混ぜておらず、戦闘・射撃時刻は既存の全battle比較で別途検査している。元の6編成のbattle/full trace指紋も全保持した。

保存した実goldenは`research/portable-world-ordered-history-battles-short-expected.json`。suiteはdevelopment_onlyを維持し、全キャラ対応や本体compilerへの一括promotionを意味しない。

`ordered-history-retention`は旧1330＋新25＝1355入力（native1071／拒否284）。不変packet `/tmp/nikke-native-snapshot-retention-v2`（id `2c05f378b91f3185008da793b87715ba99f6148ee11d49d38247f88a2faa3ffc`）でMetal全一致・独立fresh seal成功。CPU事前73.150秒、全91群482検査169.345秒成功、GPU11.148889750秒。生成cacheは必須hit、追加Slang0。旧1330のnative指紋は全保持し、記録済みselector25修正4件だけraw各2bytes変化、残る旧1326件の4,171,235,328bytesと新25件は全byte一致した。保持goldenは`research/portable-world-ordered-history-retention-short-expected.json`。旧goldenのSHAを変更して通したものではない。初回packetはCPUの旧散弾監査テストでGPU前に停止した。現行rawへ古い差分文字列を置換しても何も変わらない故障注入だったため、上位差分をprojectした歴史的監査層で各差分の出現を確認し、実際に変更したsourceを拒否するテストへ修正した。監査器、旧SHA、GPU sourceは変えていない。隔離CPU診断の残り32群123検査は成功した。

## 容量とWindows

全入力・readbackと14GiBの予備を事前に見積もった。検証済みの旧raw1本は、論理bytes、全SHA、path、inodeを維持したままゼロ領域の割当1,898,971,136 bytesを回収した。削除0、GPU再実行0。独立seal後の新1355入力rawも全SHA/path/inodeを保持したまま3,036,479,488 bytesの割当を回収し、合計回収4,935,450,624 bytes。

Windowsの追加操作は0。10月22日19:04:25 JSTの7プロセス終了原因はunknown、環境保全はfalseのまま。終了原因を特定する独立した証拠は得られていない。原因を切り分けるまで追加Windows実行を凍結する。

全キャラ認定は0、UIはCPU、全体ゴールは未達。現在sourceのCUDA実機検証、追加stat consumerと状態・対象の混在、typed interrupt橋、広いpromotionと全キャラ認定が残る。
