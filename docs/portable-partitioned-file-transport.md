# 全入力を維持する分割・ファイル出力

Windowsの旧106入力は875,469,264byteの出力を一括確保し、cuMemAlloc3回は成功したがcuLaunchKernelがcode2で失敗した。Job commitとVRAMのどちらが原因かは未確定。今回の変更は上限を増やさず、既存sequence adapterを使って一度に保持する明示バッファを小さくする。

`portable_partitioned_transport.execute` はCUDA/Metal共通の入力分割、source/生成物/完全input hash検査、file metadata検査、順序付き結合、完全output hash検査を持つ。Slang/GPU計算本体と厳密normalizerは変更しない。CUDAは既存execute_cuda_batchesのoutput_paths、Metalは既存Swift --batchesを使い、context/pipelineと最大batch分の3バッファを再利用する。

元inputのrow byteを変更せず、headerの件数だけを各batchに合わせる。全体件数、最終短batch、拒否statusを含む全word、順序を保持する。行の独立性を推測で認定せず、通常のflat profileは元sealed baselineと全raw output SHAが一致しなければ完成ファイルを公開しない。明示address profileは下記の別の論理viewを検査する。partial/parts/失敗記録は保持し、同じ出力先を再使用しない。通常のbackend.executeや公開GPU admissionは変更していない。

## バッファと保存量

106入力を16/16/16/16/16/16/10に分ける場合、期待される最大明示bufferは以下。これをJob全体のcommitや実VRAM量へ読み替えない。

| buffer | 一括106 | 最大16 |
| --- | ---: | ---: |
| input | 49,048,324 | 7,403,524 |
| output | 875,469,264 | 132,146,304 |
| runtime（stride143,048） | 15,163,088 | 2,288,768 |

全875,469,264byteを削らず結合する。出力を丸ごとPython bytesへ読まず、既存8MiBのfile chunk単位で結合・hashする。各batchのinput/outputを証拠として保存するため、結合出力との2コピー分をstorage preflightへ計上する。既存rawや失敗captureを削って空きを作らない。

## immutable Metal診断

```text
python scripts/nikke_gpu.py partitioned-file-package --source-package OLD_SEALED_PACKET --out NEW.zip
```

元coordinate-resident-frames ownerの計算、data、test、registry、goldenを保持し、CLIのmain dispatcherだけを追加する。新packet自身で13個の分割・故障注入テストと5個のaddress viewテストを実行する。通常run/旧preflight経路を新dispatcherで拒否する。

```text
python scripts/nikke_gpu.py partitioned-run --capture NEW_CAPTURE --batch-size 16 --timeout 180 --slang-root SDK --generation-cache CACHE --metal-pipeline-cache METAL_CACHE --swift-module-cache SWIFT_CACHE
```

新packet cwdで実行する。Python/Swift wire、保存容量、必須generation hitを検査してから、元全106入力/native63をfresh CPU比較する。その後、新しいexclusive claimと既存run_jobの開始gate/時間制限を使ってM5実行する。GPU子はprepared input/CPU receipt/claim/sourceを再検査する。既存のnormalizer/sourceHash、Metal pipeline cacheの必須hitは緩めない。

これはMetal-onlyの診断controller。共通transportのCUDA経路は同じtestsで検査するが、Windowsで消費済みのclaim/ledgerを再利用する経路は開けていない。Metalの全出力一致を確認後、CUDA sequence trace・保存結果の独立比較・新しい正当な実行ownerへの接続が必要。診断のcalculation_verifiedはFalseで、公開受付/全キャラ認定へ昇格しない。

## 明示address profileと実行結果

実M5では全106/native63のfresh CPU照合が391.97秒、7 GPU dispatchが合計11.22秒で完了し、キャッシュは全hitだった。最大出力buffer132,146,304byteを確認した。flat連結はraw SHAが異なり旧stageを失敗として保存した。

差分は5row各1wordだけ。DFS作業領域の+530には`destructibleBattleCapture`がresults配列内の参照先word indexを保存する。分割ではバッファ先頭が変わるため、同じreceiptへの参照でも物理buffer内indexが変わる。これを値の誤差として無視しない。`resident-frames-dfs-receipt-address-v1`は4つのSlang source SHAとwire寸法を固定し、32slotすべてのreference/receipt ID/bounds/対象headerを検査する。

rawファイルはそのまま保存し、1row分のRAM view上で参照indexだけを論理全体の位置へ移す。全20参照を検査し5つが移り、106すべてのrow SHAと論理全体SHAが旧baselineへ一致した。raw SHA `0a737874…` とlogical SHA `4ecc755e…` は別々に記録する。数値・damage・statusのwordは変更しない。生成normalizer、期待hash、旧失敗判定も変更しない。派生readbackファイルは作らない。

共通CLIの`partitioned-address-audit --source-package PACKET --capture FAILED_FLAT_CAPTURE --out NEW.json`は保存データだけを監査する。GPU/compiler/native追加0、原本anchorsと既存Metal cache監査を再利用する。旧stageはFalseを保持する。現在のtransport/診断controllerはpacket metadataでprofileを明示し、rawとlogicalの区別に対応する。`output_sha256`はrawのまま、`address_view.logical_view_sha256`を別記する。legacy flatの`sealed_output_fingerprint_matches`はrawが異なる限りFalseのままにし、profileの論理一致は別flagで判定する。失敗時の終了codeも1にした。新統合はunit/source contract確認までで、GPUをもう一度実行した証拠ではない。独立post-GPU native監査とCUDA sequence trace/admissionは次の段階。

このprofileは観測した5箇所だけを特別扱いしない。全32slot×全106rowについて、sourceで宣言されたreference/receipt IDの組を検査し、全数値・status・参照先を含む全row hashと全体hashを照合する。rawファイルは付替えない。現69f25d90 packetの13＋5unitが成功し、plan/splitとCUDA/Metalのsequence呼出しASTが実行済み旧packetと同一であることを確認した。Windows追加実行0。


## 保存結果の独立native監査

新しいimmutable診断packet自身のcwdから実行する。旧packet・raw・失敗stageを変更しない。

```text
python scripts/nikke_gpu.py partitioned-native-audit --source-package EXECUTED_PACKET --capture FAILED_FLAT_CAPTURE --out NEW_AUDIT_DIR --timeout 240 --group-size 16
```

独立packetは全goldenと元のnative/GPU/data/test payloadを保持し、既存CLI関数のAST一致も検査する。最初に既存address監査・Metal pipeline cache監査で実dispatchとrawを確認する。その後、既存のpartition/selection/validate_factsを使って全入力を重複・欠落なく分割し、各群をfresh GPU禁止childで比較する。各childは全inputを元adapterで再構築し、元のsemantic compare/rejection/stage validator、native指紋、全row指紋、全体logical指紋とpaired strict generated指紋を検査する。live parent/native結果の持越しはしない。rawは毎群boundedに読むが、比較対象はその群だけ。群単位の成功はcalculation_verified=Falseで、全群のexact coverage・異なるPID・上限・同一raw/論理viewを検査した集約だけが全corpusの独立計算監査となる。

初版051dc854 packetの一括CPU比較は240秒でtimeoutし、v6-native-auditの失敗とwire監査を保持した。GPU/compiler追加0。上限を増やさず、d2197957 packetで16件ずつの分割へ変更した。CPU段階と各native比較のjournalを追加し、時間の内訳を追えるようにした。失敗した旧stageを成功へ変更する処理はない。全キャラ・公開受付の認定とは別である。

## CUDA sequence traceの別プロトコル

`portable_partitioned_cuda_trace.verify`はCPU-onlyの新しい監査器。legacy `verify_cuda_trace`の一回launch規則を変更せず、同じcontext内の全batchについてcache-only CUBIN receipt、全driver境界の順序と成功return、各出力zero、launch/sync、全chunkのdevice address/bytes、file receipt、最後のcontext destroyを照合する。後続batchの失敗・不足・余分なAPI・別PID・壊れたstreamを故障注入で拒否する。旧observerが記録しないgrid/blockやallocationの実byte数は認定しない。Windows実行許可や計算証拠ではなく、新しいbounded実行ownerへの接続は未完了。


2026-10-29結果：固定d2197957 packetの分割独立監査は全106/native63で成功した。別々の7 fresh child、16/16/16/16/16/16/10入力、各240秒以内（最大120.13秒）、集約506.70秒。入力再構築30.82秒、元semantic/native比較466.04秒。全row/input/native/生成code指紋が旧goldenへ一致し、raw SHAは元capture、logical SHAは旧goldenにそれぞれ一致した。全20参照を毎群検査した。GPU/compiler/Windows追加0、旧raw・失敗stage・golden変更0。新しい独立計算監査だけcalculation_verified=Trueで、旧stageはFalseのまま。v7 native controllerは現在の開発sourceと全byte同一。own packet26 unitと開発checkoutの関連108 unit成功。証跡 `research/target-count-query-evidence/partitioned-saved-native-v1.json`。これは旧固定106 corpusの認定であり、全キャラ・全特殊効果・現在すべてのsuite・公開GPU・CUDA成功の認定ではない。


## 実CUDA引数の観測とGPU禁止の出所再監査

`portable_partitioned_cuda_observer.observe` は既存 `portable_phase_audit.observe` の内側で動く。元のNativeFunctionへ同じ引数objectを一度だけ渡す。3 allocationの実要求byte数と返されたdevice address、各input upload、48byteのSlang定数ABI（input/output/runtime pointerと容量）、全launchの実grid/block/shared/streamを検査・記録する。誤ったサイズ・ABI・後続gridは該当driver呼出しの前に拒否する。DLLは同じjournalの既存NativeLibraryを要求し、NVRTC等のfallback DLLはロード前に拒否する。driver queryや計算コードを追加しない。

共通transportの `cuda_argument_journal=journal` で接続し、実観測を欠くbackendは完成readbackを公開できない。`portable_partitioned_cuda_trace.verify(..., require_arguments=True)` は追加receiptと元API境界の入れ子・順序を照合し、割当pointerと実readback/全ABI/各geometryを結び付ける。flag省略時の旧sequence規則とlegacy一回launch監査は保持する。これらの実引数検査は現在CPU fault injectionで検査済みであり、実CUDAの寸法を測定した証拠にはしない。

Windowsの旧66c50b92失敗には元own CLIのadmitをboundedに再評価する入口がなかった。このため新しいCPU-only入口を追加した。新claim/ledger/実行許可を発行しない。immutable packet cwdで次を実行する。

```text
python scripts/nikke_gpu.py partitioned-origin-smoke --capture NEW_SMOKE --original-workspace ORIGINAL --timeout 30
python scripts/nikke_gpu.py partitioned-origin-audit --source-package FAILED_OWNER --source-capture FAILED_OUTER --capture NEW_CPU_AUDIT --original-workspace ORIGINAL --slang-root SDK --generation-cache CACHE --timeout 180
```

smokeは元run_job/start gate/低優先度/2GiBと、Windowsでは既存native出力probeを再利用する。smoke成功後だけ後者へ進む。後者のJob全体は180秒以下、元CLIを読む子は150秒以下である。元package ID/全file hash/全goldenを検査してから元CLIをimportし、そのままadmitとsaved_linked_admissionをGPU/compile/DLL禁止下で再評価する。元の3alloc成功→launch code2→context destroy成功という全32境界、元inner/outer Jobとprocess snapshot、元claim/ledgerを前後検査する。source/claimの変更・compiler・未知のdriver境界・readbackのある別失敗は拒否する。サービス未識別を環境保持成功へ置換しない。新GPU ownerへの接続は引き続き未完了。

固定97e9477e/2161file packetは元2147fileの全byte・既存CLI関数・goldenを保持し、own42 unitとMac CPU smokeが成功。source archiveは9,635,447byte、SHA `5fff13fb57b3d8af87967caf4d0d48270a57e771c76a3b59d4053c2e7b588ed1`。GitHub `codex/cuda-partitioned-origin-v1-source` の固定11b1719eで共有。WindowsにはCPU smokeと出所監査だけを依頼した。GPU/compile/native戦闘の再実行は依頼していない。


Windows結果：CPU smoke11.202秒、origin audit155.448秒で双方成功（GPU/compile/native戦闘0）。readonly元admit/CUBIN再評価そのものは127.033秒で、Job全体180秒/子150秒以内。元106/native63、同じCUBIN6,636,880byte/SHA70fff521…、全32API境界、旧claim/ledger保持を確認した。process保持True、サービス未識別でenvironment=Falseを維持する。report固定cc75ccefの15file/166606byteをMacへ輸送し、同じJob監査器とlinked receipt key/元失敗sequence/goldenを再検査した。環境raw snapshotは未転送である。新しいGPU許可はまだFalse。次の実行ownerはこの固定CPU receiptを保持し、GPU子ではsource/header/CUBIN/imageと小さなreceipt anchorsを再検査する設計が必要。元producer chainの127秒を60秒GPU budgetへ重複投入しない。証跡 `partitioned-cuda-origin-v1.json`。


## 固定CPU受付を使う単発CUDA実行

`partitioned-cuda-package --source-package OLD_SEALED --metal-reference SAVED_NATIVE_RESULT --out NEW.zip` は、独立監査済みMetal/native全106の参照を固定した専用packetを作る。既存Metal-only packetの許可を変更せず、新packetにのみCUDA ownerを登録する。次はすべて新packet自身のcwdで実行する。

```text
python scripts/nikke_gpu.py partitioned-cuda-smoke --capture SMOKE --original-workspace ORIGINAL --timeout 30
python scripts/nikke_gpu.py partitioned-cuda-prepare --capture PREPARED --gpu-capture GPU_CAPTURE --auditor-root ORIGIN_PACKET --auditor-capture ORIGIN_AUDIT --original-workspace ORIGINAL --slang-root SDK --generation-cache CACHE --timeout 180
python scripts/nikke_gpu.py partitioned-cuda-run --capture GPU_CAPTURE --prepared PREPARED --original-workspace ORIGINAL --timeout 60
```

各段階の成功後だけ次へ進む。CPU準備は新packetの全inputを再構築し、全row SHAを元goldenへ照合する。成功済み97e9477eのorigin SHA c1367040…、元のJobと受付、元claim/ledgerを検査し、元のread_verifiedでCUDA source/header/CUBIN本体も照合する。source-hostのnative値やPythonオブジェクトは持ち越さず、fingerprint receiptだけを使う。状態はhost/新package/nonce/予定GPU保存先へ結合する。

GPU起動時には元失敗とconsumed claimのhashから安定した新ledgerを作り、新ownerのexclusive claimへ結合する。別copyの同一packetからも重複実行できない。旧claimは変更しない。失敗したGPU保存先やclaim/ledgerを削除して再送しない。GPU子は小さなreceipt anchors・元claim・全input・source/generation・source/header/CUBIN imageを再検査する。約127秒の元producer全体監査は繰り返さず、NVRTC/Slang fallbackを禁止する。CUDA driver cacheも無効化する。

同じ共通transport/同じSlangから全106を16×6＋10に分け、実allocation/48byte ABI/grid/block/全streamを監査する。logical SHAだけでなく、保存した分割Metalの全875469264byteのraw SHAとも一致させる。新段階はcalculation_verified=Falseを維持し、まずshared_metal_wire_equivalence_verifiedを明示する。fresh independent native比較や全char認定をしたとは扱わない。GPU jobはBelowNormal/2GiB/60秒以下、prepareはCPUだけ180秒以下。環境保持と計算は別flagで、サービス未確認を成功へ置換しない。

初版固定e2f6470d/2166fileはown52＋checkout129テストとMac CPU smokeが成功。元2147file・既存CLI関数・全goldenを保持し、shader/正本/normalizer変更0。source branch codex/cuda-partitioned-v1-source 固定24c11faaで共有した。Windowsには3段階を順番に各1回、失敗時停止の条件で依頼した。実CUDAの結果は別receiptに記録する。


Windows実行結果：固定e2f6470dはsmoke8.246秒、prepare42.079秒、GPU27.561秒、全Job post0/timeout0。7launch/7sync/106 chunk readbackは全return0で完了し、旧code2は今回発生しなかった。全106のrawはbc59f8bb…、論理viewもsealed baselineと不一致のため元stage/計算はFalseのまま。全875MBのpartialと7batchを保持し、再実行0。report固定d48d5050から38file/360328byteを取得し、Macでは末尾の既知のpost-readback failureを明示したAPI-prefix projectionだけを同じ監査器で検査した。全traceは失敗のままで、計算成功へ置換しない。source/code/claimsを維持して保存データのCPU差分調査へ進む。今後のtransportは計算済みaddress-view JSONを不一致判定前に保存するが、既存captureはbackfillしない。現checkoutの関連130テスト成功、実行済みpacketのown52テスト成功。証跡 `partitioned-cuda-single-attempt-v1.json`。


## 保存済みCUDAの行・ページ・数値差分（CPUのみ）

`partitioned-saved-index` は固定e2f6470dの失敗captureを変更せず、全raw SHA・元artifact anchors・input/plan/ABIを前後検査し、行SHAと64KiBページSHAを新しいcaptureへ保存する。source-pinned typed address viewをRAM内だけに適用する。既存のreadback-block hash helper、Job/start gate/BelowNormal/2GiBを再利用し、最大180秒、GPU/driver/Slang/native禁止。`passed=True`は診断完了だけであり、元計算はFalseのまま。

```text
python scripts/nikke_gpu.py partitioned-saved-index --source-package FAILED_PACKAGE --source-capture FAILED_GPU --capture NEW_INDEX --original-workspace ORIGINAL --raw-sha256 RECORDED_RAW_SHA --timeout 180
```

任意の`--details REQUEST.json --details-sha256 SHA`は、参照の4KiB block hashesを固定する。差分block一覧と、最初の異なる8ケースから各1block、計8192 uint32以下だけを出力する。raw再生成やGPU再送はしない。

Mac側の比較は以下。`--reference-raw`を付けると参照全体と各row SHAをストリーム検証し、輸送した全sample hash/参照block/範囲/重複/整数型を確認して、実際に異なるwordを出す。ここではraw SHAと論理SHAが同一の参照だけを許可する。address viewが必要なrawをそのまま参照にしない。

```text
python scripts/nikke_gpu.py partitioned-index-compare --reference METAL_INDEX.json --candidate CUDA_INDEX.json --reference-raw METAL_RAW --out NEW_COMPARISON.json
```

比較コマンドは不一致でも診断完了としてexit0を返す。`all_logical_rows_equal`と`changed_cases`を読むこと。`calculation_verified`は常にFalseで、この結果をsealやGPU受付へ流用しない。出力はexclusiveで旧診断を上書きしない。

2026-10-29：保存CUDA全106の83rowは論理全byte一致、23row/191ページ/315個の4KiB blockが異なる。全statusはMetalと同じ0:63/64:43。Windows最初のindex15.582秒、詳細index13.713秒で完了し、GPU/compile/native追加0。詳細report固定a2a2a2e1の10file/1296393byteを取得。Macの全875469264byte参照検査と8sample比較が成功した。ミサトの最初のHP照会にはhealing 283571/282542/282456/281928/280623対CUDAの全0があり、addsケースのcarrier pass49/50ではslot71/72だけが入れ替わる。owner/body等ではtotal damageの差もある。slot差を正規化・除外せず、数値差を丸めと断定しない。根本原因・修正・CUDA計算の再認定は未完了。元失敗/capture/claims/goldenは不変。


## Resident scalar snapshotのCUDA生成差

保存済みCUDAソースの厳密正規化SHA `2380f6f3…` は旧失敗ownerの生成基準と同じである。通常回復の`before = s.hp[owner]`がCUDA生成後には更新後HPの再読になり、累積回復量へ`HP-HP`を加算していた。`findCarrier`の`slot = s.carrierCount++`も、CUDAでは増加後countで定義を書き、同じ増加後countを返していた。Metalには両方の更新前scalarが残る。旧rawの回復0とslot差に対応する生成差であり、ドライバーや丸めの問題と説明しない。

共通Slangに読み取り専用のnoinline scalar境界`bodyHPBeforeHeal`と`carrierCountBeforeAllocate`を設け、更新前の値を明示的に保持する。CPU正本・wire・初期化shader・厳密normalizerは変更しない。`portable_scope_snapshot_audit.audit_resident_scalars`は生成CUDA/MSLのsnapshot→更新→利用順を確認し、キャッシュのpair再検査にも接続する。古い生成物を正規化で通す修正ではなく、新sourceには新しい生成/CUBIN identityが必要。

新しいpublic fixtureは`git add`で共通CLIのtracked-file whitelistへ登録してからpackageする。未追跡fixtureを後からimmutable packetへコピーしない。CPU groupの外部fixtureは`portable_cpu_tests.AUDIT_FILES`へ登録し、梱包漏れをnative/device前に止める。今回の監査fixture2件も明示依存にした。

源泉の診断は `resident-scalar-snapshot-root-causes-v1.json`。この生成検査はGPU計算成功を意味しない。新sourceのM5/nativeとCUDA実機は別々に認定し、旧106 CUDA失敗・raw・claims・goldenを保持する。


この修正の固定v5/8c87f24bは現sourceの選択3入力でMetal＋独立fresh native照合成功（28群179検査、GPU2.317秒、冷PSO62.332秒、独立45.438秒）。旧Metalの対応3行もtyped address viewで全word一致。ただし追加監査で、同じ生成CUDAのmarkEntryにはenemyBuffRows/infiniteRowsのpost-increment index問題が残る。2つのsnapshot guardだけで全生成物を認定せず、この追加修正前にWindowsへcompile/runを依頼しない。元全106/current全suite/全キャラは未完了。
