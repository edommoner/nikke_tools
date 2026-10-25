# 座標戦闘の通常比較での事前計算再利用

`coordinate-burst-control` の通常実行を既存 `ParentOracles` へ接続しました。実戦の共通CUDA／Metalソース、入力、CPU正本、golden、元の全比較項目は変えていません。事前計算で実際に収集した生成イベント記録も、同じ親process・thread・package・capture・domainの通常比較で一度だけ使います。保存ファイルからnative値を読みません。

`native_comparison_adapter(domain)` は元の比較器が呼ぶleaf providerを明示します。`NATIVE_COMPARISON_CONTEXT` のcapture／validate／restoreは、既存 `creation_indices` 観測器の実記録を受け渡します。native値の指紋に加えてdomain・provider・補助記録・hookの同一性を検査し、元の `trace_view` と全比較器を実行します。例外時もproviderと観測器を復元します。未知の非直列化objectはfreshへ戻し、不完全な既知protocolや変異は拒否します。

別processのaudit／replay／sealは従来どおりfreshです。通常比較の高速化を独立監査の代用にしません。

## CPUのみの回帰確認

immutable packageを作成・展開し、そのルートで実行します。

```sh
python scripts/nikke_gpu.py coordinate-parent-check \
  --source-package /tmp/nikke-burst-control-develop-v3 \
  --source-capture /tmp/nikke-burst-control-metal-v3-ready-v1 \
  --out /tmp/nikke-coordinate-parent-check-new
```

原Metalの実行claim・成功記録・全artifact hashと、現packetの数値source／入力／native基準を検査します。実native事前計算、再利用比較、再利用を閉じたfresh比較の順に全293入力を検査し、比較結果の完全一致と実native呼出し数を確認します。rawは読み取り専用fixtureとして使用し、新しいGPU capture／claim／監査証明を作りません。終了時に原captureの全hashを再検査します。

## 実測

固定package `4012b0d0…` のCPU回帰確認は293入力（native246／拒否47）で成功しました。native事前計算178.002秒・通常比較8.661秒・fresh比較195.058秒。事前native246回、通常比較の追加native0回、fresh比較246回、補助記録再利用246件で全比較結果が一致しました。同一実行内の順次測定であり、独立した速度ベンチマークではありません。GPU追加実行は0回です。

Slangペア生成cacheはhit／compiler0で、CUDA・MSLの全byteが元Metal実行時と同じでした。Metal pipelineのfile probeもhitですが、現CUDA実行やwarm GPU性能の証明にはしません。

新しい実fixture4検査は全246domainのprovider経路、実生成hit記録、MT／保留burst量／stage-open破損の拒否、observer復元、source／入力／native admissionを確認します。既存ParentOraclesの所有者・順序・変異・fallback等20検査も保持します。

全キャラ認定0、未対応21profiles／20分類、UI CPUは変わりません。次はmode中の明示sequence・post-delayのnative契約と、healing storage／混在actorの元定義への接続です。
