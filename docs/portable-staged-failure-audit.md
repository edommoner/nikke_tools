# 保存済みstaged CUDA失敗の監査

対象は、保存CUBIN出所確認後、Slang generation identityでValueErrorとなった既知の失敗。claim消費をGPU到達の証拠とはせず、CUDA marker不在だけでも未実行と判断しない。`staged-failure-check` は既存のpackage owner検証、Job timeline、process snapshot比較、入力全row指紋検査を再利用するCPU専用監査。原本・transaction・claimを編集しない。

確認するものは元package ID、実行/生成/observerの厳密なAST関数一致、7件の順序付きphaseとValueError、inner/outer terminal、両Jobの2GiB/post0、監視processの保持、元inputとclaim/nonce/transactionの結合。readback/partial/result/evidence等がある、未知のphaseが混じる、原本が途中で変わる場合は拒否する。生成normalizerは変更しない。サービス帰属が不明なら保全も未確認のまま出す。

直接利用:

```text
python scripts/nikke_gpu.py staged-failure-check --package-root ORIGINAL_PACKET --capture FAILED_OUTER_CAPTURE --expected-package-id EXACT_SHA256 --out NEW_REPORT.json
```

Windowsでは固定packetの `scripts/run-gpu-packet.py --stage audit-staged-failure --backend cuda --capture NEW_CAPTURE --original-workspace ORIGINAL_WORKSPACE --timeout 180 --request REQUEST.json` を使う。requestはsource_package/source_capture/expected_package_idの3キー。既存のBelowNormal/fresh Job/start gate/2GiB/監視をそのまま使い、GPU/driver/compiler/native再計算を起動しない。source_captureはouter captureを指す。

passedはこの失敗の診断成立だけ。`execution_permitted`/`native_admission_revalidated`/`linked_artifact_revalidated`/`host_revalidated`/`calculation_verified`は全てFalse。消費済みclaimの削除・再使用、失敗packetの編集、再実行を許可する仕組みではない。次の実行には、元106入力/native63の全証拠とCUBIN出所を保持する、別途レビューされたimmutable recovery protocolが必要。

## 明示的な生成設定

`staged-gpu-linked` は `--slang-root ABSOLUTE_SDK --generation-cache ABSOLUTE_CACHE` をペアで受け取る。両方をrecipeへ固定し、bounded childの環境とも一致することをstart gate前に検査する。親環境を変更せず、従来の引数なし環境指定は保持する。partial/relative指定と別stageへの適用は拒否。compiler/cache identityと実cache hitの本検査は省略しない。旧packetは引数追加のために編集しない。

Windows保存phaseの小さなprojectionを回帰fixtureへ保存した。projectionは元journal全体やJob検証の代わりにはならず、full_capture_audited=Falseを保持する。実データでの監査は別の固定stage報告へ記録する。

## Windows原本での実行

固定ソースpacket `ebe7d2db…` はMacで90unitを実行した `754fcea8…` と全file recordが同一。GitHubのsource専用branchから13,029,265byteのZIPだけを取得し、3875fileを検証してからCPU監査を1回実行した。元04515f96の106入力・制御フロー・Job・監視・claim検査が成功し、stage終了0。GPU/compiler/native再計算、unit/smoke再実行は0。サービス識別は未確認のためenvironment preservation=Falseを保持する。

元Windows JSONはproof storageにbytes/SHA付きで保持し、公開fixtureはJSONをcanonicalな改行で保存する。stageのproof_resultと診断結果の一致、再実行/native/cache/host認定がFalseであることを回帰検査する。監査成功後も旧execution claimは消費済みである。

## 次の実行経路に残る要件

### 元事前検査のCPU専用再監査

`staged-origin-check --package-root ORIGINAL_PACKET --capture FAILED_OUTER_CAPTURE --expected-package-id EXACT_SHA256 --out NEW_DIRECTORY` は、失敗監査後に元packet自身の `staged-preflight-check` を別Pythonで実行する。現在のregistry/moduleを旧packetへ注入せず、全native指紋・unit receipts・Job・continuationを元実装で再監査する。battle/native oracleの計算は呼ばない。元receiptとの完全一致、host/nonce/input/件数を確認する。

元package、transaction、continuation親、各unit/native stageと元timeoutのcaptureを明示参照から列挙し、全ファイル名/bytes/SHAを再監査の前後で照合する。リンク、special file、追加ファイル、変更を拒否し、original workspace全体を探索しない。新directoryへfailure-audit.json/admission.json/owner-output.json/origin-inventory.json/result.jsonを排他的に保存する。失敗も保存し、同じdirectoryを上書きしない。

Windowsは固定packetのwrapperで `--stage audit-staged-origin --backend cuda --timeout 180` を使う。requestは失敗監査と同じ3キー。既存のBelowNormal/fresh Job/2GiB/監視を使い、旧CLI子120秒は全stage180秒に内包される。unit/native/GPU/compileを再実行しない。Mac fixtureで検査済みだが、実Windowsの元106/native63に対する実行は未確認。

成功時にnative_admission_revalidated/host_revalidatedだけがTrueになる。execution_permitted/recovery_admission_verified/linked_artifact_revalidated/calculation_verifiedはFalseを維持する。inventoryは監査対象の固定記録であり、それだけを将来のGPU admissionに使用してよいという証明ではない。新ownerへの一意な引き継ぎ、CUBIN/cache再検証、GPU後の独立監査は必要。

新しいrecovery capsuleは元packetのnative/GPU/data/test byteとsuite/goldenを保持し、変更をcontrollerの必要部分へ限定する必要がある。失敗の判定だけでなく、元106/native63の全事前検査、host、保存CUBINとpaired generationを再検証し、元claimを触らず新しいowner/nonce/captureへ結合する。旧read/prepare/claim/finishの境界を維持し、SDK設定不足は重い再監査より前に拒否する。

これは未実装の要件であり、現在の監査stageからGPUへ進む分岐は存在しない。新controllerを作る際も、正本変更、古い失敗の成功扱い、GPU前の全native再計算、上限拡大、自動retryで代替しない。GPU後の独立計算監査は別に必要で、Macでの実行を優先する。
