# ダメージ蓄積の共有状態本体とMetal検証

`gpu/damage_accum_core.slang` に、scalar pool・率・名前archive・放出の状態操作を実装した。`damage-accum-core` は共通CLIのsealed suiteで、34正例/7拒否の41入力を同じSlang、入力、CPU比較器でCUDA/Metalへ渡す。これは状態操作の単体検証で、戦闘GPU受付は閉じたままである。既存52戦闘契約のMetal接続、全キャラ・全特殊効果のGPU対応は未完了。

## 実装

既存protection allocatorと同じ24word object形式を使い、型13/dealt、16/received、15/rate、14/名前archiveを分離した。名前archiveはownerに属さず、carrierのretirementとは別に残る。pool初期化は名前archiveを0にし、takeは最初の同名active carrierをdone/0にする。doneの0量poolも後続を隠す。active不在時だけarchiveを取り、archiveを常に0へ戻す。

active順の双方向リストはrecord7/8にobject+1のリンクを持つ。初期化時に明示orderで挿入し、収集と率照会はリストを順に読む。poolごとに全容量から次のorderを探す重複scanを除いた。名前archiveの検索/空き探索はまだ線形であり、実編成での性能は未測定。速度向上を計測済みとは扱わない。

head/tailの2wordは明示header引数で渡す。arena直前に暗黙配置すると既存shield selectionに衝突するため、production adapterは別の監査済み領域を割り当てる必要がある。pool/rateは予約bitを保持し、retireがリンクを外して解放する。既存allocatorのcarrier世代・生存状態との同期はまだ実装していない。

率の値field存在、名前参照の有無、stack倍率、lost-HP倍率を別bitとして保持する。基礎と名前加算を別々にactive順で計算し、基礎なし100/明示0の違いを保持する。query時のowner HPはdaUpdateOwnerHPから更新する。収集はdealt→received、software binary64の乗算→除算→加算→cap比較の順で、cap-1e-9のdone判定を使う。通知列はcaller所有の領域へ全更新後の順で出力し、配送自体はbattle adapterのcontinuationが担当する。

放出整数は既存f64ToI64のtruncationを使う。正の量だけをemit対象とし、split倍率後の整数が0または負でもpacket資格を保持する。防御・ATK・criticalは再適用しない。非有限値やint64範囲外は元のerror16を返す。

## 検証の範囲

state-operation probeは初期容量、固定credit、rate定義、HP更新、take/retireを入力に持つ。CPUが実戦闘で計算した着弾量やtraceをGPUへ与える経路ではない。入力の容量/creditは単体検査用の著作された値であり、実戦闘のATK snapshotや着弾計算を実証しない。

CPU oracleは実際のBuffManager/ActiveBuffと、未変更のaccumulate_damage、_accum_rate、accum_discharge、_get_valueを使う。初期化/retirementはテストdriverが行い、full通知を記録して既存notifyへ渡す。split整数の期待値はtimelineと同じ式で計算するが、full timeline handlerの実行証明ではない。

34契約は、同/別owner、率なし/0/名前指定/大値の順序加算、負率、負/0/端数容量、epsilon、archive、refresh、dealt/received順、重複名、失ったHP41%とlive HP更新、stack、別poolへのcredit、split端数、正量から0への切捨て、負packet、0/負credit、slot再利用を含む。7拒否は不正policy/owner、archive容量不足、不明op、NaN credit、無限rate、整数overflow。共通CLIの拒否header64に対し、本体の正確なerror16/64をword2へ保持し両方を照合する。

Apple M5 Metalの41入力が成功し、fresh childによる保存rawの独立sealも成功した。GPU時間0.000189秒、raw128974848B。連結順・逆リンク・最終pool/archive・各take/率/通知/整数を比較した。保存Metal6ブロックは疎形式から全byteを復元してSHAを確認し、量/通知名/整数/リンクcycle/内部errorへの故障注入を検出する。

最終sealed package47a3e486...は2592ファイル、6509450B。CPU2群14検査が成功し、旧52戦闘契約とproduction143source SHAを保持した。登録goldenは独立監査済みv8と完全一致。最終生成はcache必須hit、Slang呼び出し0、CUDA/MSL/両reflectionを厳密照合した。生成CUDA46301B/36関数、MSL48927B。これは生成cacheの証明で、WindowsのNVRTC cacheや計算速度の証明ではない。

probeのresident Runtimeは実際のactivation順counterだけを持つ8Bで、production Runtime138952Bは変更していない。キャッシュのためにreflection規則やnormalizerを緩めていない。

## 使用

```sh
python scripts/nikke_gpu.py package --suite damage-accum-core --out /tmp/damage-core.zip
python scripts/nikke_gpu.py unpack --archive /tmp/damage-core.zip --dest /tmp/damage-core-package
# 以後、展開先をcwdとする。CPU確認はGPU0。
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/damage-core-cpu --timeout 90
```

sealed packageでgenerationを行い、cache必須hitを確認してから新しいcaptureへ1回だけ実行する。使ったpackage/backendのclaimを消さない。Windowsはこの41入力だけを短く検証する候補で、full-entry compilerや旧398入力の実行を必要条件にしない。CUDA coreの後続結果は末尾に記録した。full battleのCUDA実機は未検証。

## 保持した失敗と限界

最初のCPU packageは必要な旧goldenがsupport_filesにないため停止した。非resident probeでgeneration cacheを使った試みもGPU前に拒否された。実際の順序counterをresident bufferへ移し、既存paired-reflection経路を使った。初回Metalのreaderはnormalizer参照が不足し、reader修正後のGPU0 replayでは34正例一致/数値負例3件のheader差を検出した。元raw/claimを保持したまま、明示headerと内部errorを残す別sourceで2回目のMetalを実証した。reader修正だけのGPU再実行はない。

sealed最終packageへdevelopment captureを直接replayする試みは既存CLIのdevelopment限定条件で拒否された。規則を緩めず、既存の独立seal・完全一致golden・最終CPU/生成cache検査を根拠にしている。成功rawのゼロ領域のみ126287872B回収し、全byte/SHA/path/inodeを保持した。

probeはarena最大32、通知8の範囲である。production1024枠、複数通知の再入、carrier世代、実際のATK/着弾/吸血時機、aimed/部位/adds、実キャラの全定義は未認定。静的242/266・base182/203・未対応30分類、全キャラ認定0、UI CPU、全目標未達のままである。

## 次のbattle adapter

1. 共通coreをprivate world entryへincludeし、arena/header/通知scratchの非重複配置を監査する。既存shield/decoy/healing objectとの1024枠共存をfail closedにする。
2. 実carrierのentryOrder/世代/refresh/終了/解除/downをcoreのinitialize/retireへ同期する。容量はGPU内で正本順のfinal ATK×値/100を計算し、負容量を保持する。archiveはcarrier終了から独立させる。
3. rateのraw値・存在bit・stack・live HPを共有量読取へ接続する。値がない率と明示0、基礎/名前和の順序を変えない。
4. bossへの実packetだけを、実creditと吸血の後でcollectする。全pool更新後のevent50列は再入しても壊れない所有期間で保持し、既存Frame continuationから配送する。adds/aimed経路へ無条件に接続しない。
5. kind34放出を1回take→split倍率→共通整数変換→既存receiptへ結ぶ。private admissionのstat81/82/83、event50、quantity presenceと拒否を共通化する。
6. 正本52戦闘契約、旧Metal398全byte保持、元ドロシー/トロニーの全定義/実編成をMetalで検証する。保存old source証明は明示delta逆変換で保持し、正本・binary64・normalizerを変更しない。

証拠はresearch/damage-accum-core-evidence/、checkpointはresearch/portable-damage-accum-core-checkpoint.json。

## Windows配布とbattle配置候補の追記

Windowsへはroot commit5dfc0d6...の専用branchから6.5MBの同一packageと出所JSONだけを配布し、開発履歴転送を避けた。package ID/SHA確認後、補助helperが中断されCPU captureはpreflight/4検査成功までの記録で止まっている。CPU完了やCUDA開始は未確認、GPU実行0。保存runner PIDだけをliveness証拠にせず、既存実行だけの読み取り回収を依頼した。追加CPU/GPUや再起動は依頼していない。

既存scratch ownership監査の全5モードに候補を追加してCPU確認したところ、header260666..260668、通知scratch260668..261692（512件）が衝突せず入る。元の未所有区間は260666..262128で残り436word。これは実行layoutへの割当やGPU証明ではなく、次のadapterが実際に初期化順・再入時所有期間とともに実装する候補である。

## Windows準備経路の修正

読み取り回収で、旧helperの準備が過去34046ファイル/1167617324Bの列挙・SHA読取だったと報告された。元CPU runnerへはOpenProcessがerror87でlive handleを取得できず、CPU完了は未認定のまま保存した。旧7プロセスの終了原因とは結び付けない。

この個別helperを再利用せず、scripts/run-gpu-packet.pyでCPU事前検査を含む全stageを既存Job/start gate/cleanupの所有下へ置く。準備ではmanifest headerだけを読み、全member検査もgate後の予算内に含める。Macの対象CPU20検査とcontroller smoke323（Windows専用1skip）が成功。詳細docs/portable-packet-stage.md。

実adapterでは、coreのrate record21がstack、既存protectionObjectのrecord21がcarrier slotである点を分ける必要がある。coreのlogical slotはword6に置き、typed bindingで読む。allocateProtectionは先頭20wordを消すため、再利用前にactiveリンクを外さなければならない。入力policyの高位bitをcoreのactive/owner flagsへそのままコピーしない。これらは既存ソースの直接接続前に解決する条件で、現在の単体probeはproduction bindingを認定しない。

## CUDA coreの実機報告

修正版Windows smoke324件(skip9)/失敗0、対象CPU21件/失敗0の後、RTX3070Tiで41入力(native方法34/拒否7)が一致した。共有CLIの報告するinput SHA5018e811...、全128974848B readback SHA1c9b7b50...はMetal登録goldenと同じである。cold NVRTCは1回1.453秒、host dispatch0.004975秒（MetalのGPU秒とは別の計測）。file-only warm cacheはhit/0.085秒、追加compile/GPU0。GPUは1回のみ。

内側Jobで欠落0だが、全stageの前後観測では7件欠落/サービス識別不明で環境保全false、原因unknownを保持する。数値一致/containmentと保全を分離する。追加Windows実験は依頼せず、保存済み小レポートと時点集計だけを取得中である。現在の記録はWindows共通CLIの完了報告であり、MacでCUDA rawを独立再監査したものではない。battle adapter/全キャラ認定の証明にはしない。
