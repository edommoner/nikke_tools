# 起動前fresh検査を分割する固定transaction

全106入力はnative63件の参照計算が約410秒を要し、Windowsの外側180秒制限へ収まらない。`preflight-begin` → `preflight-native-group` → `staged-run` は同じsealed package・入力・実行環境の一度だけのGPU検証を段階化する。通常の`run`とそのfresh preflightは変更しない。

各群は参照計算をfreshに実行し、保存するのは名前・入力SHA・native SHA・実行記録のみ。nativeの値、状態、観測contextをファイルへ保存したりGPUへ渡したりしない。別transactionの検証結果や、古いCPU値を読むcacheではない。

## CPU段階

```sh
python scripts/nikke_gpu.py preflight-begin --backend metal \
  --capture /new/begin --gpu-capture /new/gpu --group-size 10
python scripts/nikke_gpu.py preflight-native-group \
  --transaction /new/begin --capture /new/group0 --group-index 0
# 全群をindex順に、一度ずつ実行する
python scripts/nikke_gpu.py staged-preflight-check --backend metal \
  --transaction /new/begin --gpu-capture /new/gpu --out /new/admission.json
```

beginは容量検査、全選択CPUテスト、全静的入力を検査し、package manifest・入力・hostの指紋、nonce、全caseの分割、native所属、未来のGPU captureを固定する。共通の`gpu-claimed-BACKEND.json`をbeginで消費するため、同packetの通常runとの重複実行も成立しない。

各群は別fresh childで実行する。GPU直前ゲートは全群の完了、指紋、入力、unique PID、case順・件数、拒否caseも含む全coverage、元manifestとhost、各群のclaimを再検査する。途中で失敗した群や消費済みclaimを消して再実行しない。

Windowsは共通wrapperの以下のstageを使う。各requestの正確なキーは次の通り。

| stage | request |
|---|---|
| `preflight-begin` | `gpu_capture`（未来のGPU stageのproof絶対path）、`group_size`（十進文字列） |
| `preflight-native-group` | `transaction`（begin stageのproof絶対path）、`group_index`（十進文字列） |
| `staged-gpu-linked` | `transaction`、`linked_package`、`linked_capture`（絶対path） |

```sh
python scripts/run-gpu-packet.py --stage preflight-begin --backend cuda \
  --capture /new/begin-stage --timeout 180 --original-workspace /original --request /new/begin-request.json
```

native群も同じ形で1回1群、BelowNormal・2GiB・fresh Job／開始gate・外側180秒以内に限定する。GPU直前には各CPU stageのterminal exit0、Job終了後の空membership、PIDと時刻の対応、監視／cleanup errorなし、既存process欠落0も検査する。サービス未識別を成功へ変更しない。

## GPU段階と独立監査

```sh
python scripts/nikke_gpu.py staged-run --backend metal --transaction /new/begin \
  --capture /new/gpu --timeout 60 --slang-root /pinned/slang \
  --generation-cache /pinned/generation-cache --require-generation-cache
```

CUDAは`staged-gpu-linked` stageから既存の監査済みCUBINを使用する。mandatoryなpaired generation cacheを要求し、live NVRTCへのfallbackはない。GPU子は既存60秒上限、全stageは180秒上限を維持する。

静的入力をGPU直前に再生成して全指紋を照合し、専用`staged-prepared-v1` protocolで渡す。通常runの`cpu.json`は後付けしない。GPU実行claimも一度だけ作成する。

GPU後は`pending_native_audit=true`、`calculation_verified=false`、runは`awaiting-native-audit`となる。完了したdispatchとsealed readback SHAの一致は記録するが、計算成功や全キャラ対応へ昇格しない。生成物・raw・標準artifactsを保存した後、[共通fresh分割監査](portable-shared-native-groups.md)を全群実行・集約して初めて計算一致を判定する。GPUの再実行は不要。

CUDAのサービス保全が未確認なら計算一致後も環境保全／全体passedはfalse。transaction、CPU群、元の失敗とclaims、GPU rawと監査原本は保持する。
