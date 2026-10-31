# 固定パッケージのコンパイル計画

Windowsへ送る前に、不変パッケージ自身のCLIとcwdで以下を実行します。

```sh
python scripts/nikke_gpu.py compile-plan --artifact-kind cubin --ptxas-level 1 \
  --memory-limit-mb 2048 --timeout 60 --out NEW_PLAN.json
```

`passed`とpackage IDを照合してから、同じ引数で`compile`を依頼します。`compile`のbackendはCUDA固定で、`--backend`はありません。既存CLIのsealed戦闘パッケージはCUBIN用コンパイルを受け付けます。`compiler-full--...`の診断パッケージはPTX・2GiB・ptxas level指定なしに固定されており、その制約を維持します。artifactの自動fallbackはありません。

計画はパッケージの全file/source/goldenを検査したうえで、artifact・予算・purposeの互換性だけを判定します。GPU、Slang、NVRTC、Job、claim、cacheへの書込みは行いません。SDKや依存の存在、コンパイラ成功、Windows containment／preservation、計算一致は別のゲートです。計画JSONを既存の成功証拠へ読み替えません。

現在のCLIは同じpacketの`compile-claimed-cuda.json`の存在も読み取り確認し、`execution_claim_available`へ記録します。消費済みならartifactを変えても`passed=false`です。壊れたsymlinkも存在として拒否し、元claim/captureを変更しません。これは計画時点の観測で、実行時の排他的claim作成は引き続き必須です。過去の固定packetにはこの追加検査はなく、変更して後付けしません。

失敗したCUBINを別rootで再試行する手順ではありません。moving-groupでは元CUBIN失敗を保持し、**別工程として明示したPTX単独生成**に限って元不変ZIPを新規rootへ展開します。同じsource/goldenを保ち、既存生成cacheを必須hitにし、2GiB/child60秒/outer180秒を維持します。PTX成功だけで後段assemblerやGPU実行へ自動移行しません。

PTX診断パッケージへCUBINを依頼した失敗は、Windowsの`resident-compile-v1-preflight`に保存しています。実コンパイル・claimは0でした。修正後はsealed `coordinate-resident-arc`を使います。親・child・監査・計画は同じ`compiler_diagnostic_policy`を呼び、旧PTX制約を共有します。互換性、旧制約、budget、development拒否を含む11検査を通しました。

Windows v3ではdevice検査は成功しましたが、共通smokeのSwift修復fixtureが`write_text`でLFをCRLFへ変換し、固定SHA検査に拒否されました。v4ではfixtureをUTF-8 bytesで書き、実ファイルSHAも検査します。CRLF候補を拒否する負例を追加し、実運用の修復SHA／normalizerは変更していません。Macの共通60群581検査が成功し、計算コードと106goldenはv3と同一です。旧失敗は保存したまま新規packetのみを使います。


## 共通packetのO1経路

`run-gpu-packet.py --stage compile-cubin-o1 --backend cuda --capture NEW --timeout 180 --original-workspace ORIGINAL` は、既存の共通CLI `compile --artifact-kind cubin --ptxas-level 1 --memory-limit-mb 2048 --timeout 60` へ渡します。外側全工程180秒と内側コンパイルchild60秒を分け、既存O0／PTXと同じJob・claim・監査を使います。コンパイルchildの60秒にNVRTC単体60秒を保証する意味はなく、内部の検査・生成もその予算内です。CPUの固定argv・30/60/180秒境界・Metal拒否・original workspace必須・偽driver/GPU成功拒否を含む20検査が成功しました。新O1 stageの実Windows確認はまだ行っていません。

v4の保存報告（Windows report commit `a0844950`）では、個別driverの外側60秒が先に切れました。開始から最初のpackage検査等11.573秒、inner observation2.119秒、child package検査11.283秒、Slang9.754秒を経て、35.007秒時点でNVRTC entered。約24.995秒の未完了区間後に親timeoutであり、NVRTC所要時間や内部の失敗原因は断定できません。親peak645,595,136byte／cleanup後メンバー0、内側終了観測とpreservationは未確認、CUBIN／完成cacheなし。compile／cache claimを保持しています。

今回のclaimは再使用しません。次の候補は、保存生成物・cacheのidentityを確認して生成を省けるかと、既存PTX-only→object/link経路による工程の分離です。共有計算を削る、上限を拡大する、同条件のNVRTCを単純に再試行する判断には使いません。

## 2026-10-31 CUDA module-objectの同一gate内検証重複を解消

CLIのmodule-objectが同じsealed producer自身を処理する場合、親でverify_package済みの直後と子でverify_package済みの直後に、assembly_originが同じ全file検証を再実行していた。fresh mと同一root・同一manifestに限りその2重複だけを省き、全file検証は親1／子1／独立post1の計3回を維持する（外側wrapperは別）。foreign/historical producerは既存全検証のまま。引数は内部呼出し専用でrequest/CLIで再利用tokenを受け付けず、metadata/stat cacheや過去receiptの代用ではない。PTX producerの全artifact／Job／生成数値baseline監査は不変。post auditorはfast pathを使わず全package再検査する。実行後改変も拒否する。

既存compiler18群202テスト成功。親/子dispatchの実flag、同rootで1回のfresh検証、別root/manifest変化/実行後変化の拒否、post audit維持を回帰検査。PTXAS O1/fmad、60秒/2GiB、Job/pre/post観測、排他claim、旧失敗の扱いは不変。preparation journalにoriginとpost auditの実測区間を追加し、既存厳密phases列は変えない。GPU/数値code変更0、実SDK/GPU/新Metal/CUDA製品profile0。Windowsでの短縮は未測定。

旧owner2195のptxas15.021秒／outer62.406秒、object未admit、missing14原因不明／preservation=falseを保持する。修正は旧claimの再実行許可ではない。続いてd73ca08dのnormal開発ownerf3deae04…を固定し、own100unit／202 SDK模擬／fresh native1／実M5／GPU禁止独立sealが成功。旧accumulateのinput/output/native entriesは全一致だが、Mac生成CUDA/MSLは旧2195と異なりreflection2fileだけ一致した。旧PTXcache再利用はadmitしない。旧v9を保持したv10でaccumulateのsource/generated identityだけを実証済み現行版へ更新し、他24memberは不変。次は最終sealed current ownerでWindows preflight後、新コードの短いcompileを1回だけ計画する。証跡research/product-cuda-origin-gates-v1.json。

## コンパイル専用の事前検査と戦闘起動の事前検査

`compile` / `compile-ptx` / `module-object` / `jit-link-object` はコンパイル・保存artifactの検査だけを行い、戦闘のnative計算や全選択unit群を暗黙には実行しない。
sealed Metal基準・全package byte・現在source・生成CUDA/MSL・compiler options・artifact出所・Job/観測をそれぞれの既存gateで検査する。
生成段階を先に一度だけ完了し、後段はpaired generation cacheを必須にしてSlangの重複生成を防ぐ。
コンパイルだけを調べるWindows依頼に全戦闘テストやnative戦闘計算を前置きする必要はない。
これはGPU起動の免除ではなく、`run`/`staged-run`の全登録テストとnative admission、製品APIのGPU後fresh CPU全応答比較は従来どおり。

CLI childの実dispatchをfake NVRTCへ接続し、cpu_test_groups/open_suite/prepare_entries/native_value/compare_readbackを呼ばないことを回帰検査した。
実driver/GPU禁止、計算認定false、GPU claim未消費を検査し、既存compiler/module/object/link/Job/packetの計113検査も維持した。
SDK childは60秒・2GiB、外側wrapperは既存の最大180秒。複数のnative工程を依頼する場合も合計予算を別に明示し、欠落process・timeout・未admit artifactがあれば停止する。
サービス未識別とprocess欠落0を混同せず、過去の失敗・claimは保持する。
