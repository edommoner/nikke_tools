# 保存CUBIN戦闘の全stage制限

## 実PTX同一性による再利用監査

`linked-reuse-audit --linked-package OLD_LINK_OWNER --linked-capture OLD_LINK_PROOF --producer-package CURRENT_PTX_OWNER --producer-capture CURRENT_PTX_PROOF --out NEW.json` は、旧object/linkの全chainと現sealed producerを別々に再監査する。旧・現の**実PTX全bytes**とsize/SHA/version/target、完全compiler identity/key/headers/options/DLLを照合し、現producerの全native goldenと実行側goldenの完全一致を要求する。現compile claimもpackage ID/capture/PTXに束縛する。旧link identity/sourceは保持し、追加receiptの`exact_ptx_reuse`へ旧・現producerを分けて記録する。normalized一致だけでは受け付けない。

共通Windows wrapperは`--stage audit-linked-reuse --backend cuda --capture NEW --timeout 180 --original-workspace ORIGINAL --request REQUEST.json`。requestの4キーは絶対pathの`linked_package`/`linked_capture`/`producer_package`/`producer_capture`。既存Job/gate/BelowNormal/2GiB、専用stage claim/観測/collectを使う。監査だけでcompiler/GPU/native battleは0、出力は元入力外の新JSONのみ。再コンパイル、再リンク、原claim変更、GPU実行のfallbackはない。

開発/固定24870e4d…自身209検査と前後payload検査が成功。bytes/metadata/compiler options/receipt/claim/native基準改変とforged scopeを拒否し、旧cold/current cache-hitの違いはidentityと混同しない。`research/portable-exact-ptx-linked-reuse-v1.json`。

現時点ではread-only admission監査の接続まで。`run`/`staged-run`のCLIは従来の2-path linked requestを作るため、現producer pairをfresh transactionへ渡す接続と実CUDA計算は残る。監査成功だけを計算/全キャラ成功にしない。

## sealed producerとlink controllerを分ける（2026-10-29）

従来のfull compiler ownerからの受付は保持する。新しい明示経路では、link controllerはsealed packet、計算の元producerは別の独立sealed world battle packetとして全payload/source/goldenを検証する。実行側・controller・元producerは全てsealed/非選択。元producerのgoldenは実行側の**全goldenと完全一致**し、entries/input/output指紋も必須。controllerの別goldenを元計算の証明に使わない。

元producer package ID/manifest SHA、controller package ID/link receipt key、receipt内のobject→producer chainを別々に束縛する。従来のsource closure/normalized pair/CUDA元SHA/header/toolchainの照合、元PTX/object/link/Job/観測監査、live NVRTC拒否を維持する。正規化済み生成物が同じという理由だけで異なるsource closureやnative基準を受け付けない。UI/default admissionを開ける変更ではない。

開発側125検査と固定3443f8bf…自身125検査、前後payload検査に成功。元controllerと元sourceを区別した正例、改変native指紋/partial/owner/manifest/receipt/object chainの拒否、実source manifestを読み取るCLIを検査した。実WindowsのCUBIN admission/計算は未確認。小記録`research/portable-sealed-linked-admission-v1.json`。今回この追加packetはMacに保持し、GPU実行は依頼していない。

共通Windows wrapperの`gpu-linked`は、既存`nikke_gpu.py run --linked-package --linked-capture`へ接続する。CPU事前検査・元object/link監査からdriver/kernelまでを同じfresh Job、BelowNormal、2GiB、外側最大180秒・内側最大60秒で囲む。計算本体・効果定義・CUDA/Metal shader・数値契約・厳密normalizerは変更しない。

```sh
# request.json: linked_package と linked_capture の2キー、絶対パスのみ
python scripts/run-gpu-packet.py --stage gpu-linked --backend cuda \
  --capture /absolute/new-stage --timeout 90 \
  --original-workspace /absolute/original --request /absolute/request.json
```

sealed戦闘packageで実行し、requestのpackageはfull compiler packageまたは上記のsealed controller、captureは保存JIT-linkのproofを指す。元PTX/object/linkの全出所・byte・Jobと、現戦闘source closure／生成CUDA元SHA／headerを既存admissionで照合する。live NVRTCは拒否される。計算一致と環境保全／stage成功は分離し、wrapper専用claimに加えて既存戦闘のbackend claimも保持する。リンク・生成・GPUの自動fallbackや再実行はない。

今回の変更は固定package `7fb9a15f011b353d6c96a5f47e1c1603131ad1b847b4712909df61dedabcf8e2`でCPU制御39group／397件（Windows専用1skip、wrapper19件を含む）が成功。選択suiteのCPU10group／53件とnative68入力／全81入力も成功し、旧Metal81のgoldenとinput SHAを保持した。Windowsでこの新stageのJob smokeと実GPU実行はまだ行っていない。

## 現full sourceの保存object

現compiler owner `9bf571abcd56509f0e1feb0b308f35d53dbbd18b3a0ada016c329ed30ef0b9b5`の元PTX 9,554,090byteから、固定ptxas12.4.131／sm86／O1／FMAfalse／compile-onlyを1回実行。ptxasは20.5452815秒／ret0、5,452,464byteのET_REL objectを保存した。SHAは`ea9e1484a30fe69864a515cafdba87569079e93a924c55f44b82016762e48cb8`。分割・元PTX書換え・Slang/NVRTC/driver/GPU/linkは0。

内側Jobは59.4140873秒／exit0、しかし外側は後続監査の途中で90秒上限へ達し、93.6340647秒で終了処理した。package検証は6.8996383秒、9.9543165秒、内側13.5328837秒、最後の再監査は未完了。全stage/object_verifiedはfalseを保持する。両Jobは2GiB／BelowNormal／gate確認／post空、peak396,890,112／357,236,736byte、cleanup・観測errorなし／missing0、service未確認のため環境保全false。

元proofにはobject／全9phase／inner executionがあるが、outer終了でrun.statusはprocessingのまま、artifacts.json／result.json／failure.jsonはない。これを成功runへ書き換えたり、元captureへ後付けartifactsを作らない。claimは消費済みで再コンパイル・上限増加・リンクへは進まない。別のCPU監査receiptで出所を回収する共通経路は[object回収](portable-object-recovery.md)を参照。元失敗・欠けた記録を明示して保持する。

現状はWindows接続内peer reportまでで、Mac独立原本監査ではない。CUDA本体計算、全キャラ／全特殊効果の完成証明でもない。座標host trigの数値方針は回答待ち、公開受付とUIはCPUのまま。
