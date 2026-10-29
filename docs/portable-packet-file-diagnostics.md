# 保存物検査を共通Jobへ通す

Windowsの保存PTX統計とcompile cache照合は、`run-gpu-packet.py`の`ptx-stats`／`cache-check`を使う。既存のfresh Job・2GiB・BelowNormal・start gate・終了直後観測・最大180秒を再利用する。独自のCPU wrapperへJob設定を手渡ししない。新経路の実Windows確認はまだ行っていない。

要求JSONは新規ファイルへ保存する。ptx-statsは次の2フィールドだけを受け付ける。

```json
{"cache_entry":"C:/absolute/cache/EXACT_KEY.json","phases":"C:/absolute/saved-proof/phases.jsonl"}
```

cache-checkは1フィールドだけを受け付ける。

```json
{"source_capture":"C:/absolute/saved-compile-proof"}
```

同じ不変packet自身のcwdとbase Pythonで実行する。

```sh
python scripts/run-gpu-packet.py --stage ptx-stats --backend cuda \
  --capture NEW_STATS_STAGE --request STATS_REQUEST.json \
  --original-workspace ORIGINAL_WORKSPACE --timeout 180
python scripts/run-gpu-packet.py --stage cache-check --backend cuda \
  --capture NEW_CACHE_STAGE --request CACHE_REQUEST.json \
  --original-workspace ORIGINAL_WORKSPACE --timeout 180
```

要求内のパスは絶対パスで、余分なfield・改行・NUL・相対パスを拒否する。出力captureは不変packetと元workspaceの外側。controllerのstage claimは1回限りで、失敗も削除しない。cache-checkのsource_captureは同じpacketが所有するcaptureに限り、既存coreの所有検査を維持する。古いpacketやowner IDを書き換えてこの経路へ合わせない。

ptx-statsは既存`ptx_statistics`をtop12／callgraph有効で呼ぶ。元cache-entryとcompile receiptへの固定、全解析の成功、graphのPTX SHA一致を検査する。間接call等によるgraphの不完全性はそのまま報告し、完全graphへ変換しない。controller package IDをPTXの計算所有証明に使わない。

cache-checkは既存`check_compile_cache`をそのまま呼び、同じ`NIKKE_CUDA_COMPILE_CACHE`／`CUDA_PATH`を使う。厳密hit・key・artifact hash・同一ownerを確認し、missは失敗として保持する。NVRTC callbackはcoreが禁止しており、このstageからcompileやGPUへ進まない。core自身の完全package検査を重複して追加しない。

両方とも`forbid_gpu`下でfile-only監査を実行し、`proof/detail.json`とscope付き`proof/result.json`、そのartifact hashを保存する。外側は2GiB設定を強制し、環境の値が0でも上書きする。結果のcompiler／calculation認定は常にfalse。型がboolの偽0 counterや別PTX graph、cache miss、不完全なreceiptは拒否する。元の実行counterと今回のfile-only counterを混同しない。

新規6検査は実PTX parser/graphへの合成入力、guard下の既存監査器呼出し、失敗時の部分記録保持、ambient上限0の上書き、偽counter等を含む。関連105検査と固定de42d2db…自身22群238検査が成功した。これはWindowsのJob動作や元のGPU計算の実証ではない。記録は`research/portable-packet-file-diagnostics-v1.json`。
