# 共通移動/typed/groupの短いWindows準備とコンパイル

## 現sourceのPTX cache hit（2026-10-29）

固定54c70a1d…/`moving-group-current`でpaired generationを1回準備し、sealed normalized pairへ一致。新source keyのためSlang2回・25.772秒だったが、生成CUDA/MSLの実bytesも元producerと一致した。続く共通`probe-ptx-cache`はexact PTX hit、auditor本体0.142秒/外stage10.511秒。generation/cache必須のPTX producerは内14.315秒/外25.969秒、Slang/NVRTC0・compiler_verified trueだった。

元PTXと同じ13,556,055byte/SHA `e6d83bf98e727ee989aaca68364c632ebbf9e26c259dd71161462a90184a104e`、同じcompile key `ded5292f9aa24aee1d01b79b04df40f46a9472a9d16bba8fdeb1751f9f61525e`。両sourceの識別は保持し、新しいsource receiptを作ったのであって旧成功記録の書換えではない。

全stageは2GiB/BelowNormal/gate、Job後0/欠落0/timeout・観測cleanup error無しの報告。サービス未識別は保全/overall false、compile stageのchild exit2/wrapper1。GPU/battle/ptxas/object/link/retry0。固定report dee9d4f2…の小要約4869byte＋manifest623byteを原CRLF/SHAで取得し、現Metal sourceと元生成物へ照合した。原PTX/全JobはWindows保存でMac独立原本監査ではない。`research/portable-moving-group-current-cache-peer-v2.json`。

次は旧object/CUBINと**現producer**のraw PTX・完全compiler identityを両方再監査する明示的な再利用受付。normalized一致だけでは受け付けず、元artifactのold source表示を保持する。現CUDA戦闘計算は未確認で、ここからobject/link/GPUを自動実行しない。以下は元sourceの履歴。

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

## PTX工程の結果

WindowsはNVRTC1回35.541301秒/code0でPTX13,556,055byteを保存した。SHA256 `e6d83bf98e727ee989aaca68364c632ebbf9e26c259dd71161462a90184a104e`、PTX cache key `ded5292f9aa24aee1d01b79b04df40f46a9472a9d16bba8fdeb1751f9f61525e`。artifact cache miss、既存paired generation必須hit/Slang0。inner51.799秒/peak289,640,448byte、outer65.379秒/peak324,009,984byte、各Job/gate/低優先度/2GiBを確認した報告。終了後Job/process欠落0、観測/cleanup/Job inspection error無し、両timeout false。service未識別によりpreservation/overall false、outer child exit2/wrapper exit1を成功へ書き換えない。

固定report commit `edc2c550a29384910c02b8dcdf7839a9c32d3c4a`の要約2703byte/manifest519byteを元CRLF bytes/SHAのまま取り込み、前回準備のraw生成SHA/normalized pair/generation keyと、固定M5 sealed normalized基準へ一致させた。PTX/全Job/phase本体はWindows保存で、Macの独立原本監査ではない。小証跡`research/portable-moving-group-ptx-checkpoint-v1.json`。

PTX生成がCUBIN assemblyを通さず成立した証拠であり、全工程メモリ改善やCUBIN/driver/GPU/計算一致ではない。追加ptxas/driver/GPU/native/旧CUBIN再試行0。次は保存PTXのversion/targetと固定外部toolを読み取り検査し、元producerを既存監査器で検証する別assembler工程を計画する。NVRTC再生成や自動fallbackは行わない。
