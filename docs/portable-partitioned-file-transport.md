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
