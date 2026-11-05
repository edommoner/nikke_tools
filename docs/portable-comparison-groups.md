# 全ケースを保持する独立CPU監査の分割

共通CLIの `seal --comparison-group-size N` と `replay --comparison-group-size N` は、全入力を順序どおりのグループへ分け、グループごとに新しいGPU禁止のPythonプロセスで比較します。従来の未指定経路は維持します。CUDA／Metalの共通比較器を再利用し、GPU計算本体・数値規約・正本・normalizer・compile cacheは変更しません。現段階の保存capture入口は従来どおりMetalです。

```sh
python scripts/nikke_gpu.py seal \
  --package-root IMMUTABLE_DEVELOPMENT_PACKAGE \
  --capture SAVED_CAPTURE --out NEW_GOLDEN.json \
  --comparison-group-size 24 --timeout 180 \
  --audit-receipt NEW_AUDIT.json
```

保存出力を新しいdevelopment packageへ移す場合は、既存の `replay` に `--comparison-group-size 24 --audit-timeout 180` を追加できます。元と新packageの入力・native基準・GPU sourceが同じこと、元captureの実GPU境界とclaim、保存結果の完全性を既存replay検査で確認します。package／captureを後から書き換えて合わせません。

各childは不変packageとcaptureを検査し、入力・readback全体をハッシュ照合した上で担当nativeだけを再計算します。未担当部分のrawもハッシュ対象です。部分結果は `calculation_verified=False` のままです。集約は、全入力indexの順序・重複・欠落、拒否ケース、ケース別input/native/output指紋、全体input/output／生成コード指紋、transport、package/controller/captureの不変性を検査します。ライブ親oracleや保存native値は使いません。

`--timeout`／`--audit-timeout` は各childの上限です（1〜240秒）。総時間の上限や高速化を意味しません。逐次実行し、失敗・timeout後は次groupへ進まず成功goldenを出しません。最終版は `/tmp/nikke-independent-groups-*` にplan・各groupのstdout/stderrと部分JSON・failureまたはaggregateを保存し、成功時は返り値の `group_capture` に場所を記録します。失敗時の例外にも場所を残します。

## 実測と範囲

不変development package `22d968b4…` と保存Metal captureの全67入力／native40／拒否27を24・24・19に分割しました。新GPU呼び出し0、childは76.032／72.987／89.328秒、各180秒上限内、総239.598秒でした。旧単一childの223.096秒より総時間は増えていますが、ケースを減らさずに追加ケースを監査できるようになります。

全67のinput/native/outputとCUDA/MSL生成指紋を含むgoldenは旧sealed67と完全一致し、全544,576,000byteの出力を保持しました。グループ間のライブoracle再利用は0です。rawは全reader終了後にSHA・size・inodeを保った疎化を行い439,025,664byteの割当を回収、削除0でした。

最終package `b58926cf…` の変更はgroupログ／失敗記録と追加テストだけです。CLIの変更関数は `audit_saved_metal_groups` のみで、全native producer／比較器と他のCLI関数ASTは実測版と一致します。実測は開発版で行ったもので、最終版で全nativeを再生成したという主張はしません。最終版は実fresh子プロセス・途中失敗・timeout・部分結果・集約・seal receiptを含む新12件、既存seal8件、関連84件、制御500件に成功しました（Windows専用1件skip）。既存生成cache必須hit・Slang0も確認しました。

記録は `research/comparison-groups-evidence/` と `research/portable-comparison-groups-checkpoint.json`。この監査経路の完成を型付き所有者fieldのGPU対応、現在CUDA／warm cache実証、ゲーム仕様や全キャラ認定へ数えません。次はCPUで固定したowner規則を共通Slangへ接続し、旧67を保持して新counter／fieldケースをMetalで検証します。
