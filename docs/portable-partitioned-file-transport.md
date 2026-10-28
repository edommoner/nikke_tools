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
