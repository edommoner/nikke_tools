# 現ソース用の全106入力CUDA owner

実証packet `b873a58c48c76438c23c2b8fc7119d601793f702d8668a435ab74eefb437abcc`はWindowsで全106入力のwire一致に成功した。smoke47検査15.70秒、prepare41.20秒、GPU stage28.92秒、compiler/link0、launch/sync7、readback106。固定要約は`tests/fixtures/resident-current-cuda-v2-summary.json`。サービス保全とfresh独立native監査は未完了で、calculation/overall/public受付をtrueへ変更しない。原captureはWindowsに保持し、MacのMetal同一byte witnessをCUDA原captureとして扱わない。

`partitioned-current-package`は旧失敗の回収ownerを変更せず、現ソースのMetal sealと保存CUBINへ結び付ける別versionのownerを作る。GPU計算・効果定義・保護CPU正本・厳密normalizer・全goldenは保持し、既存の分割transport、CUDA trace/ABI監査、linked artifact admission、Job/start gateを再利用する。

```text
python scripts/nikke_gpu.py partitioned-current-package --source-package CURRENT_SEALED --metal-reference tests/fixtures/partitioned-physical-reference-v1.json --current-reference tests/fixtures/resident-append-full106-metal-v1.json --out NEW.zip
```

現ソースの参照は`portable_resident_validation`がpinする独立Metal/native sealの全byte SHAで検査する。全106/native63、input/output、完全golden fileへのanchorが一致しなければ作れない。元のphysical参照は別にpinする。今回、現Metalの全entry/input/output/native指紋と元参照が同一で、address ABIの4sourceも不変だったため、このphysical参照を再利用できる。古いGPU sourceを現ソースの実行証拠へ付け替える処理ではない。

すでにhelperを含むnormal packetから作る場合は、明示したcontroller/test/dataだけを更新し、main以外の既存CLI関数を保持する。unknown source/referenceや、旧ownerへ新linked受付を渡すことは拒否する。旧v1の固定origin/claim/ledgerはそのまま。

## 3段階

新しいpacket自身のcwdで、すべて実在する絶対パスを使う。

```text
python scripts/nikke_gpu.py partitioned-cuda-smoke --capture NEW_SMOKE --original-workspace ORIGINAL --timeout 60
python scripts/nikke_gpu.py partitioned-cuda-prepare --capture PREPARED --gpu-capture GPU --linked-root COMPILER_PACKET --linked-capture JIT_LINK_PROOF --original-workspace ORIGINAL --slang-root SDK --generation-cache CACHE --timeout 180
python scripts/nikke_gpu.py partitioned-cuda-run --capture GPU --prepared PREPARED --original-workspace ORIGINAL --timeout 60
```

smokeはWindowsの既存native Job probeと固定7群のCPU controller検査を同じJobで行い、全群receiptを親でも確認する。現在のpacketは47検査。CPU準備は全inputを再構築し、全row/全体SHAと必須paired generation hitを確認する。既存`saved_linked_admission`で元PTX/object/link・Job・欠落0を一度再監査し、`read_verified`でsource/header/CUBINを照合する。Windowsのnative戦闘を再計算したとは主張しない。固定するのは既に独立監査済みの現Metal/nativeの指紋で、native値やPython状態を持ち越さない。

prepared contextはhost、package、nonce、予定GPU保存先、設定と小さなreceipt anchorsへbindする。GPU直前は元manifest/link claim/receipt等のanchorと全input、source/header/CUBIN bytesを再検査し、重いproducer chain監査を繰り返さない。コンパイラーfallbackは拒否する。

新しいledgerは元linked sourceの保存場所でCUBIN receiptと完全goldenへ結び付ける。同じpacketのcopyでも重複実行できない。GPU前の保存容量不足はledger/claimを作る前に拒否する。失敗claim、partial、過去ownerは削除・変更しない。

## 範囲と上限

全106入力を16×6＋10へ分け、全875,469,264byteを保存する。最大明示output bufferは132,146,304byte。2コピーの出力、全batch input、original input、64MiBの余裕と1GiB reserveをbudgetに入れる（今回のrequired 1,916,144,064byte＋reserve）。Job全体は2GiB/BelowNormal、GPU stage60秒以内。Slang/NVRTC/ptxas/linkは起動しない。

rawは元physical wire SHAと比較し、source-pinnedのaddress viewで全row/論理全体も比較する。数値/statusの除外はない。`passed`/`stage_protocol_verified`はこのprivate stageのprotocol成立を示す。`overall_stage_passed`は環境保持も成立した場合だけtrueで、service未識別を成功へ変えない。GPU wire一致も`calculation_verified=false`と`pending_independent_native_audit=true`を維持する。全キャラ、canonical model、公開受付は別の未完了事項。
