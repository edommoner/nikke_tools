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
| `staged-gpu-linked` | `transaction`、`linked_package`、`linked_capture`（絶対path）。現PTX producerで旧CUBINを再利用するときのみ、対の`producer_package`/`producer_capture`（絶対path）を追加 |

```sh
python scripts/run-gpu-packet.py --stage preflight-begin --backend cuda \
  --capture /new/begin-stage --timeout 180 --original-workspace /original --request /new/begin-request.json
```

native群も同じ形で1回1群、BelowNormal・2GiB・fresh Job／開始gate・外側180秒以内に限定する。GPU直前には各CPU stageのterminal exit0、Job終了後の空membership、PIDと時刻の対応、監視／cleanup errorなし、既存process欠落0も検査する。サービス未識別を成功へ変更しない。

## 選択テスト自体が180秒に収まらない場合

Windowsのfull106では、native参照計算より前の選択177テストも一括では180秒を超えた。失敗したbeginとclaimを保持し、以下の明示した別経路で新しいpacketを用いる。テスト数・元の登録順・assertion・拒否入力は変えない。

```sh
python scripts/nikke_gpu.py preflight-plan --backend metal \
  --capture /new/plan --gpu-capture /new/gpu --group-size 10 --test-group-size 2
python scripts/nikke_gpu.py preflight-test-group \
  --transaction /new/plan --capture /new/tests0 --group-index 0
# 元registryの全テスト群を、元の順で各群一度だけ実行する。
# 全群成功後に、同じtransactionで全native群を実行する。
```

`preflight-plan`は静的入力と登録テストの固定分割をtransactionへ保存し、GPU所有claimを消費するが、`cpu_tests_verified=false`である。各`preflight-test-group`は元の`portable_cpu_tests.run_groups`を使用する別fresh child。元のテスト・依存確認・全stdout/stderr・件数・runner PID・終了記録を保存する。native群の開始時とGPU直前に全登録テストの順序・coverage・全原本byte・nonce・unique PIDとWindows Job/監視を再検査する。欠落、失敗、同群のreplay、別transaction、ログをinventoryから削る変更は拒否する。一括の`cpu-tests.json`を後付けしない。

Windows wrapperのrequestは、`preflight-plan`が`gpu_capture`・`group_size`・`test_group_size`（数値はASCII十進文字列）、`preflight-test-group`が`transaction`・`group_index`。各段階を従来と同じBelowNormal/fresh Job/2GiB/180秒以内で実行する。GPU子の60秒上限は変えない。通常`run`と通常`preflight-begin`は引き続き全選択テストを一括実行する。

## GPU段階と独立監査

```sh
python scripts/nikke_gpu.py staged-run --backend metal --transaction /new/begin \
  --capture /new/gpu --timeout 60 --slang-root /pinned/slang \
  --generation-cache /pinned/generation-cache --require-generation-cache
```

CUDAは`staged-gpu-linked` stageから既存の監査済みCUBINを使用する。mandatoryなpaired generation cacheを要求し、live NVRTCへのfallbackはない。GPU子は既存60秒上限、全stageは180秒上限を維持する。

古いcompact compiler packageは、全payload byteを検査した後、その検証済みowner CLIの元registry／projection監査器で登録rootを検査する。現在のテスト一覧を古いpackageへ押し付けない。owner script・manifest・監査器のSHAを前後で照合し、追加のnative参照計算・Slang／NVRTC／assemblerを実行しない。これにより新しいCLIからも保存CUBINの出所監査を維持して再利用できる。

静的入力をGPU直前に再生成して全指紋を照合し、専用`staged-prepared-v1` protocolで渡す。通常runの`cpu.json`は後付けしない。GPU実行claimも一度だけ作成する。

GPU後は`pending_native_audit=true`、`calculation_verified=false`、runは`awaiting-native-audit`となる。完了したdispatchとsealed readback SHAの一致は記録するが、計算成功や全キャラ対応へ昇格しない。生成物・raw・標準artifactsを保存した後、[共通fresh分割監査](portable-shared-native-groups.md)を全群実行・集約して初めて計算一致を判定する。GPUの再実行は不要。

CUDAのサービス保全が未確認なら計算一致後も環境保全／全体passedはfalse。transaction、CPU群、元の失敗とclaims、GPU rawと監査原本は保持する。

## native群のtimeout後、同じ未実行GPU試行のtailだけを小分けで継続

`continuation-package --base-package /original/package --out /new/controller.zip`は、元sealed packetの全payloadを保持し、3つの制御ファイルと継続用helper/testだけを変更した固定capsuleを作る。新しいゲーム機能やnative/数値/データ/元のテストの変更は混入できない。CLIの既存計算/監査関数、静的input生成、fresh nativeループ、GPU入力/実行後gateのASTも保持する。元registryを元owner自身で検査し、最新のSMOKE一覧を元packetへ押し付けない。

```sh
python scripts/nikke_gpu.py continuation-package --base-package /original/package --out /new/controller.zip
# 新しく展開したcapsule自身のCLI/cwdで実行する
python scripts/nikke_gpu.py preflight-resume --backend metal \
  --parent-transaction /original/plan/proof --capture /new/resume \
  --group-size 5
```

既存の全選択テストと、失敗直前までの連続した成功native群を、同じhost/Python・元manifest・全入力・全原本anchors・Job/観測で再検査する。失敗はcleanなbounded timeoutだけを対象とし、未成功群やreturnedだけの部分結果を成功へ昇格しない。元のresult/artifactsが無い場所へ後付け記録を作らない。元のGPU captureとexecution claimが未使用であることを確認し、元packetへappend-onlyの継続所有claimを作る。

新transactionは元のGPU保存先を保ち、未完了caseだけを厳密に小さい群へ分割する。元の成功記録と失敗のbytes/SHAを`original-evidence.json`へ固定し、各tail群とGPU直前に再照合する。保存するのは指紋と検証記録のみで、native結果値・状態・contextのcacheではない。元の選択テストは同じ試行の記録として保持し、新しい制御ロジックはcapsuleのCPU-only Job smokeで別途検査する。

Windows wrapperは`--stage preflight-resume --backend cuda`、requestは`parent_transaction`（絶対path）と`group_size`（ASCII十進文字列）の正確な2キー。新capsuleの共通wrapperでCPU-only smoke成功後、resumeを1回実行する。その後、通常の`preflight-native-group`で新transactionのtail indexを各1回実行する。BelowNormal/fresh Job/start gate/2GiB/各stage180秒を維持する。元の失敗群をそのまま再送しない。初版は普通のsealed ownerからの一段の継続に限定し、追加失敗時は自動retryしない。

全入力を元prefix+fresh tailで検査した後も、GPU子60秒・CUDA保存CUBIN/生成cache必須・実行後の独立fresh native全件照合を維持する。元の失敗stageはfalseのままであり、継続後の計算成立と区別する。原本source/input/runtimeが変わった場合は継続を拒否する。

## 通常payloadの継続と、拒否入力だけのまとめ処理

通常packageは既に継続helperと元の継続テストを含む。`continuation-package`はこのownerを専用`controller-continuation-full-owner-v1`として扱い、3つの制御ファイルと2つの継続helperだけを置き換える。元テストを含む他の全payload byteと全goldenを保持し、追加は専用の制御テスト1ファイルのみ。全payloadを投影や削減せず、従来のcompact owner経路も保持する。計算/監査関数・native参照ループ・入力/transport関数のAST保持検査も従来通り。

`preflight-resume --group-size 1 --reject-group-size 12`は、同じ元transactionに記録されたnative所属を使って、native入力と拒否入力を別の連続群へ分ける。元15入力のnativeが0/1/2の場合は`[0] [1] [2] [3..14]`の4群となる。拒否ケースも元のfresh `native_value`と指紋照合を全件実行し、失敗・省略・順序変更を成功扱いにしない。`reject_group_size`とnative所属はtransactionへ束縛し、各群とGPU直前に同じ群計画を再生成して検査する。省略時は従来の等サイズ分割を維持する。

共通wrapperの`preflight-resume` requestも、従来の`parent_transaction`/`group_size`に任意の十進文字列`reject_group_size`を追加できる。各stage180秒・2GiB・低優先度・開始gate、同じ未実行GPU所有claimを維持し、テスト群の再実行や古いCPU値のcacheは行わない。

固定75ea07e1…自身と開発側の関連95検査、原ownerとの実lineage/全payload前後検査が成功。Windowsでの実resumeとtail完了は未確認。今回の修正・scope・旧失敗は`research/portable-continuation-tail-budget-v1.json`。

## 判明した制御検査の修正だけを明示して取り込む

`continuation-package --base-package ORIGINAL --repair-controls --out NEW.zip`は、既知の835c8dbd…ownerに対する固定の修正profileだけを適用する。ledger全体のSHA、既存3ファイルの元/現byte・SHA、追加2ファイルのbyte・SHA、元generation-extraction期待fixtureのSHAを要求する。任意のpathや新しい期待値の差替えには使えない。修正前3ファイルは`research/control-repair-originals/`へ全byte保存し、元ownerとも再照合する。

修正対象は偽SDKのPOSIX/Windows名、抽出監査の3行append-audit inverse、履歴監査へ既に復元された完全な入力を渡す処理。生成/transport/計算関数やGPU/native入力・全goldenは変えない。元の失敗stageとclaimsは保持し、新schema`controller-continuation-reviewed-controls-v1`でlineageを検査する。省略時は従来のcapsule経路を維持する。

固定1e54383d…自身で実元ownerとのlineage・保持した旧control bytes・関連97検査と、全69制御群719検査が成功。実Slang/GPU/nativeは0。Windowsの実smoke/resumeは別途必要であり、このCPU検査をCUDA計算成功へ昇格しない。小記録`research/portable-continuation-reviewed-controls-v1.json`。

### 単一ファイル内のテストID分割

登録ファイル全体が時間枠に収まらない場合は、`preflight-plan` に
`--test-group-size 1 --split-test-pattern test_product_reference_models.py --test-case-group-size 3`
を指定できる。packet wrapperのrequestには同名のsnake_caseキーを両方追加し、サイズは正規の十進文字列で渡す。
この指定は既存ファイルをunittestの発見順で分割する。fixture・テスト本文・比較値・実行時間上限は変更しない。
計画時には本文を実行せず、各段階のreceiptへ実行した元IDを保存する。
独立取り込みでは、登録ファイル・ID順序・各群の件数とreceiptを再検査し、元IDの欠落・重複・並び替えを拒否する。
全群が成功するまでnative/GPU段階へ進めない。従来のファイル単位計画はそのまま利用できる。
