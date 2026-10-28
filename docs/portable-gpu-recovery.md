# 保存済み事前検査から新しいGPU ownerへの引き継ぎ

対象は、既存staged-failure-checkで認定したSlang identity不足によるGPU前失敗だけ。旧claimと失敗captureは消費済みのまま保持する。旧ownerへ引数を足して再実行する方法ではない。

## 計算を保存するcapsule

```text
python scripts/nikke_gpu.py gpu-recovery-package --base-package OLD_SEALED_PACKET --origin-auditor VERIFIED_ORIGIN_AUDITOR --out NEW.zip
```

元packet自身のregistry/golden/native/GPU/data/test全byteを保持する。置換はCLI、stage wrapper、staged preflightの3ファイルだけ。CLIの全既存関数と元main本体を保持し、mainにrecovery dispatcherを追加する。preflightはcontextの空group分岐とadmitのbridgeだけをASTで差し込む。host/outside/static_input/exclusive/terminal_cpu_stage/prepare_gpu_input/claim_execution/read_gpu_input/finish_gpuと元native loopのASTを既存guardでも検査する。これはcontroller編集であり、生成GPUコードのnormalizerは変更しない。

元compact projectionのomissions/rootsは保持し、追加した明示helper/testのfile inventoryだけを更新する。再帰的なrecovery capsuleは拒否。通常runや元preflightのやり直しを新dispatcherで拒否する。GPU childはstaged-prepared-v1だけを受ける。

## CPUだけの引き継ぎ

新packetのwrapperを `--stage preflight-recover --backend cuda --timeout 180` で1回実行する。requestは以下9キーの絶対path。

- source_package/source_capture: 元sealed ownerと元GPU前失敗outer capture。
- origin_package/origin_capture: 成功したstaged-origin-checkの固定auditorとouter capture。
- gpu_capture: 新しいstaged GPU proof directory。後のstaged-gpu-linked outer/proofと一致させる。
- linked_package/linked_capture: 元失敗が参照した保存CUBIN producer/capture。
- slang_root/generation_cache: 元Slang SDKと既存paired cache。

Slang/cacheペアはrequestからrecipeとbounded child環境へ固定する。SDK/cacheの安価な実在検査、必須generation hit（compiler/library禁止）、元完全監査、静的入力の同一性、元CUBIN出所の順に検査する。重いnative/unit再実行は行わない。Jobは既存BelowNormal/start gate/2GiB/180秒を使う。

元監査のsource ownerをcapsule metadataで固定し、成功stageのrecipe/terminal/Job/observer、元failure report、native admission、完全inventoryを再検査する。34root/4916fileという過去の件数だけを受け入れ条件にせず、元auditorが検査した全path/name/bytes/SHAを照合する。サービスが未識別ならenvironment preservationを成功へ変えない。

新nonce/transaction/GPU capture/input/native membership/環境/出所を、元失敗outerの隣の `.gpu-recovery-claims` ledgerへ排他的に結合する。ledger名は元package IDと消費済みexecution claimのbyte hashから決定し、callerが任意keyを選べない。同じ元失敗から複数ownerを作れない。途中失敗でもledgerやclaimを削除・再使用しない。

## 既存GPU経路への接続

CPU引き継ぎ成功後、同じpacketのstaged-gpu-linkedを新しいGPU captureへ1回だけ実行する。Slang/cacheの同じ明示ペアを使う。GPU子60秒・outer180秒・2GiBを維持し、既存saved_linked_providerがCUBINと厳密CUDA sourceを再検査する。admit bridgeは元完全inventoryと新CPU stage/ledger/入力を各境界で照合する。native値を保存してGPUへ供給しない。

引き継ぎCPU成功は計算成功ではない。staged GPU終了後も元finish_gpuのpending_native_audit/calculation=Falseを保持し、別fresh saved-result native監査が必要。Macのcache hitやcontroller testsから、実Windows GPU、全キャラ、公開default受付を認定しない。
