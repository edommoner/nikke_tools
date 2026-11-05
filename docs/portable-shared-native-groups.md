# CUDA／Metal共通のfresh分割監査

`saved-battle-audit` は保存戦闘captureを元immutable package自身の比較器で再検査するCPU専用CLI。Metalの既存分割sealを共通化し、CUDAも同じpartition、fresh child、全entry・input/output・生成物SHA、重複／欠落／parent-oracle拒否を使う。元の通常runやpreflightを短縮・省略する機能ではない。

```sh
python scripts/nikke_gpu.py saved-battle-audit --backend metal \
  --package-root /original/package --capture /original/capture \
  --group-size 20 --group-index 0 --timeout 180 --out /new/group0.json
```

groupごとに別のfreshプロセスで元参照計算を行い、結果値を保存するCPU cacheは作らない。receiptはcase指紋と原本anchorsだけを持つ。部分結果は`comparison_subset_verified=true`でも`calculation_verified=false`のまま。既存のMetal sealとそのschemaは維持する。

Windowsは1回1群だけ、既存のJob／BelowNormal／2GiB／開始gate／外側180秒以内で実行する。requestは絶対pathの`source_package`、`source_capture`と、ASCII十進文字列の`group_index`（0以上）、`group_size`（1以上）の4キー。

```sh
python scripts/run-gpu-packet.py --stage audit-native-group --backend cuda \
  --capture /new/group0-stage --timeout 180 \
  --original-workspace /original/workspace --request /new/request.json
```

各group indexに消費済みclaimを持ち、同じcontroller packetで別群は実行できるが、同じ群の再実行は拒否する。CUDA kernel／compiler／driverの追加起動はない。CPU群には外側180秒を使い、GPU子の60秒上限を増やすものではない。

```sh
python scripts/nikke_gpu.py aggregate-native-groups --backend cuda \
  --package-root /original/package --group-size 20 --timeout 180 \
  --receipt /saved/group0.json --receipt /saved/group1.json \
  --out /new/aggregate.json
```

集約は元packageと同じ固定controllerで、全群を順番に一度だけ指定する。全case、元manifest、capture全ファイルanchors、controller SHA、各群のfresh PIDと上限を検査する。原本byteを再読できない別hostでの集約は、source hostでのfresh監査とreceipt照合であり、remote rawのローカル再監査とは区別する。途中群や別capture／別controllerを混ぜて成功にしない。

CUDAの`calculation_verified`、Job／API traceの`transport_core_verified`、サービス保全を含む従来の`transport_verified`／`passed`を分ける。サービス未識別なら全case一致でも後者はfalse／exit2。Metalのtransport gateを弱める変更はない。

原本`artifacts.json`が存在する通常capture専用。outer timeoutで記録が欠けた原本に後付けinventoryは作らず、[readback回収](portable-readback-recovery.md)を使う。全106 CUDAの起動方法や、Heavyarmsの対象数・空間Lock Onモデルは、この監査CLIだけでは実装済みにならない。
