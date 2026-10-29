# 共通移動/typed/groupの短いWindows準備とコンパイル

固定package `76fbe7c3…e0557`（`moving-group-cache-only`）は、M5で独立監査済みの15入力/native3/拒否12を使う。最大127体用ではない。source packetはcommit `b93d1c87`、branch `codex/cuda-moving-group-v1-source`。元workspaceを変更せず、新規隔離root `C:/Users/owner/Documents/Codex/nikke-moving-group-cuda-v1`へ展開した。初めのturnはpackage検査後に別の過去の話題へ逸れたため、保存先/claim無し・実行process0を読み取ってから未実行stageだけを開始した。消費済みclaimの再送ではない。

## CPU準備

own wrapperのtestsは8群59件成功。batch22.374秒・外側35.371秒。generationは26.374秒でCUDA/MSLと両reflectionを生成し、sealed基準のstrict normalized SHAと一致した。初回generation missでSlang2回。両stageの内側exit0、BelowNormal・fresh Job・開始gate・2GiBを維持し、Job残存/process欠落/観測/cleanup errorは0。サービス未識別の環境保全とoverallはfalse。

準備時点のNVRTC/native全件/GPUは0。小さな元要約2231byteだけを取得し、元bytes/SHA・package ID・normalized pairをMacで照合した。Windowsの全Job/phase原本をMacへ取り込んで独立監査した証明ではない。source-host commit `5551b492` と `research/portable-moving-group-cuda-preparation-v1.json`、元要約は `research/cuda-preparation-evidence/moving-group-v1-peer-summary.json`。

## CUBIN1回の失敗を保持

packet自身のCUBIN/O1・2GiB・60秒compile-plan成功後、同じwrapperの`compile-cubin-o1`を1回だけ実行した。outer180秒・child60秒、generation必須hit・Slang0、NVRTC entered/returned1回でreturn6。NVRTC42.638秒、inner58.237秒、outer70.865秒。いずれもtimeoutではなく、CUBIN/cache artifactは無い。GPU/driver load/native全件は0。Job残存/process欠落/観測/cleanup errorも0、service未識別の保全falseを維持する。

保存stderrから`ptxas fatal : Memory allocation failure`が確認された。inner peak2112569344byte、outer2147676160byteと2GiB付近だが、Job上限・システム全体の空きメモリ・assembler内部のどれが直接原因かは断定しない。元要約の「原因未特定」は作成当時のまま保持し、後から読んだ具体的な診断を別excerptへ記録した。元ログの個人pathは送らず、元bytes/SHAをWindowsに残して診断行だけを共有した。

失敗共有commit `f7bd0a44`、小記録 `research/portable-moving-group-cuda-compile-failure-v1.json`。同claimの再試行、上限引上げ、代替artifactの追加compileは0。次は既存PTX-only/分離assembler経路の保存状態とメモリ計画を読む。生成cache成功をCUBIN成功やCUDA計算一致へ昇格しない。

## 次の明示工程：PTX単独生成（結果待ち）

既存`compile-ptx`と`assemble`を確認した。`assembly_origin`は元PTX producerのpackage/golden/compile receipt/Job/観測/bytesを再監査するため、過去の別kernelのPTXや失敗CUBINを代用品にしない。外部ptxasは固定12.4.131・sm86・O1・FMA無効、Job内で55秒＋cleanup5秒という既存規約。PTX成功後もまず元producerとtoolの適合を検査し、今回はassemblerを実行しない。

同じ固定ZIPの新規展開先`nikke-moving-group-ptx-v1/packet`で**別artifactのPTXだけ**を1回生成する依頼を送った。元CUBINを再試行せず、新rootでも同じCUBINを実行しない。Macの元packet自身でPTX/2GiB/60秒plan成功、Windowsのplan成功も確認。旧59CPU/paired生成の同payload証拠を再利用し、生成cache必須hit・Slang0を要求した。outer180秒/child60秒/2GiB/低優先度/Job/gateを保持し、GPU/driver/native/ptxasは0の計画。結果未取得で、PTX生成成功・assemblerのメモリ改善・CUDA計算一致はまだ認定しない。

新CLIは消費済みcompile claimを計画時に拒否するようになったが、今回の旧不変packetへ後付けしていない。詳細と現CLIの固定検査は`research/portable-compile-plan-claim-v1.json`。旧結果・cache・claimsを保持する。
