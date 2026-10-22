# 現行戦闘本体のcompiler-only package

`compiler-full`は`heal-share-regression`と同じfull entryを、既存のcompiler-only経路へ渡す。追加wrapper、GPU計算本文の変更、生成コードの正規化変更はない。現在のMetal849実証に保存した全110 source SHAとCUDA/Metalの両generated_normalizedを、そのまま別のsource-only証明書へ固定する。新しいMetalやCUDAの実行結果を作ったとは扱わない。

```sh
python scripts/nikke_gpu.py package --suite compiler-full --out /path/to/new.zip
python scripts/nikke_gpu.py unpack --archive /path/to/new.zip --dest /path/to/new-package
```

source-only証明書のentriesは空、calculation_verifiedとexecutable_battle_verifiedはfalse。既存`compile`のPTX限定・2GiB・60秒とdriver拒否、保存compile auditとcache checkを再利用する。通常battle、module check、development/case指定は拒否する。CPU preflightとcompiler-only成功から戦闘計算成功へ昇格させない。

`compiler-commands`のsource closureは基準closureにcommands wrapperを1個追加したもの。`compiler-full`は基準closureと完全同一で、full entryを比較から除外しない。fullでは生成指紋も基準と完全一致が必要。選択はCLIの登録suiteから行い、証明書の任意フィールドや大小関係から推測しない。historical auditは元のimmutable証明書と基準を使う。

まず保存旧commands objectのlink実験を終え、その結果を評価する。fullの実コンパイルを自動開始したり、旧commands CUBINをfullのcacheに代用したりしない。次に必要な独立実験を固定packageで実施し、object、link、driverと小さな実編成の数値比較を段階ごとに区別する。現時点ではfull CUDA計算と全キャラ・全特殊効果対応は未完了。

## d1594d9 現行full PTX実証

別compiler-full package `a247319b8676029b05d317ca37d2b88d79576447e2bfdf594335d166b08915b2`をWindowsでも全2020files/table一致で固定。直前commands packetと同じcontroller/testsは全byte一致のため、CPU248/native gateの再実行は省略した。NVRTC compile1回は14.953秒で成功、PTX7,099,843B／SHA `c9a35121db6842b207741e8ae3b3820865145ec486c27defcae617b8dc57756a`、peak506,089,472B／2GiB／post空／cleanup正常／欠落0。source110と両生成指紋は基準一致、既存23,526file保持。保存CPU audit1回もcompiler_verified。service未識別のpreservationfalseと計算falseを維持。Macはpeer summaryまででraw独立監査ではない。記録は`research/portable-full-ptx-peer-report.json`。

現行full PTXからmodule-object1回→成功時のみJITlink1回を別claim/captureで依頼した。NVRTC／CPU248／native smokeの再実行や、旧commands CUBINの流用は不要。最終linkの共通CPU監査から元compiler/objectの全chainを再利用し、別の重複auditは増やさない。

## 本体へのCUBIN再利用接続条件

通常NVRTC cacheと区別した明示providerを使う。現行full証明書と全source、生成CUDAの全byte、prelude、NVRTC/ptxas/nvJitLinkの実binary SHAとoptions、元PTX/object/linked CUBIN、producer→object→linkのclaim/Job/receiptを結ぶ。古いcommands originやnormalized一致だけでは受け付けない。生成元のpath差があっても既存normalizerの除外を増やさず、raw CUDA全byteが一致しなければ拒否する。

live compilerを自動fallbackで呼ばず、共通`_cuda_module`のCUBIN load／既存params48B／既存実行・readbackを再利用する。数値本文・state/effects・input/output ABIは変更しない。compile receiptをNVRTC hitに偽装せず、専用artifact-admission eventとprovider identityをtransport/独立監査へ接続する。失敗origin、欠落、tool/header/source変更、old commands混入を負例として閉じる。

この接続後にだけ、既にMetalで保存済みのheal-share-rosters4をCUDAで短く1回比較する。リンクやmodule load成功は計算成功と区別し、readback/native/Metal保存結果の一致を必要とする。全キャラ・全特殊効果の認定とparts GPU実装はその後も残る。

## 現行full object／CUBIN実証

同じ固定full packetから保存PTXの全byteを使い、ptxas12.4.131のmodule-object1回とnvJitLink12.4.127のlink1回が成功した。ptxasは6.483811秒／return0／peak267,169,792B、object4,141,360B／SHA `b658a7f41034b55b9f81c99b00513d1768c193a917cdbc88332ea8d6e40ed2e8`。JIT providerは0.210278秒／全API9return0／Destroy成立／peak84,570,112B、CUBIN3,877,904B／SHA `91aacb335dc3355d72b652736bcd5c1bbca20798bdd8d661962c577793a45578`／params48B。driver moduleは3観測ともfalse。

両Jobは実2GiB／post空／cleanup正常／欠落0。元25,589file・object/claim・親環境を保持。最終CPU audit1回も元compiler/object chainからlink/containmentを認定した。追加NVRTC／driver／GPU0、retry0。service未識別のpreservationfalse、計算false／全キャラ認定0を維持。Macはpeer summaryまで。記録は`research/portable-full-object-link-peer-report.json`。これで現行本体のPTX→object→CUBINは実証でき、次は上記の明示providerと通常実行／独立監査への接続、実編成4ケースのGPU数値比較である。

## 明示保存CUBIN providerを実装（実GPUは未検証）

共通CLI `run --backend cuda --timeout 60 --linked-package <full-package> --linked-capture <full-link> --slang-root <existing-root> --original-workspace <original> --capture <fresh>`で選択する。NVRTC/cache設定との併用、Metal、smoke、cpu-only、development、compiler-onlyを拒否する。親/子/事後の監査は既存compiler→object→linkを再利用し、元package内の専用claimを照合する。source110／両生成指紋／full producer／生成CUDA全byte／prelude／CUBINを結んだ`provider=saved-module-jit-cubin`を専用receiptへ固定する。

通常backend・共有数値本文・state/effect・ABI・strict normalizerは変更しない。CLIが既存compile source境界を一時的に置き換え、検証済みimageを返す。NVRTC関数は明示禁止、自動fallbackはない。read→receiptは1回だけで、元CUBINを変更しない。既存CUDA module／execute／stream readbackを使う。cache reuseとNVRTC hitを別stageにし、ordered native traceと独立readback監査でも専用origin/receiptを要求する。`cache-check`もこのproviderではNVRTC cache環境不要・CPU-onlyで再照合できる。

新13故障注入を含むfresh controller CPU261中260成功／Windows1skip。4入力の既存CPU/native指紋と関連19検査も成功、両packetのコードbyte一致。数値sourceが同一なのでMetal849+実4は再実行しない。記録は`research/portable-linked-provider-checkpoint.json`。次は固定clean sourceでWindows CPU/Job smoke1回後、現行CUBINを再利用する実編成4だけをGPU1回。既存NVRTC/ptxas/JITlinkは再実行しない。計算／全キャラ認定は実結果が揃うまで未完了。

## ab5c17b 実CUDA起動と未解決のraw差分

Windows CPU261とnative gate成功後、保存CUBINの通常run1回を実施。RTX3070TiでcuModuleLoadData／Launch／Sync／readback2回を含むdriver19戻り値0、source/生成CUDA/prelude/保存CUBIN一致、追加NVRTC／ptxas／JITlink0を確認した。Job45.666311秒／peak1,667,842,048B／2GiB／post空／cleanup正常／欠落0、元25,637file不変。service未識別のpreservationfalseは維持。

ただし4入力ともGPU出力指紋がMetal goldenと異なり、calculation_verified=false。保存comparisonのCPU-only確認では4件すべてadapter.compareが例外なく完了し、name/input/native指紋は一致、output指紋だけ不一致と判別した。nativeの検査範囲は通過したが、未比較領域を含む全rawの一致は未証明である。差分を除外／許容せず、再GPUを行わずに調査する。peer記録は`research/portable-linked-rosters-peer-report.json`と`portable-linked-rosters-hash-fields.json`。

共通CLIのCPU-only `readback-index`／`readback-compare`は、記録済み全raw SHAと固定786432 words/caseを要求し、4096B単位の全block SHAを比較する。二度目のsample読みでも全blockと全SHAを再検査し、診断sampleは最大8block、元bufferはread-only、出力上書きは禁止。独立stdlib moduleとしても同じmainを呼べる。5故障注入と既存CLI39検査成功。保存Metal実4の12,582,912Bは元golden SHA f83a45b0...に一致し、`research/portable-heal-rosters-metal-block-index.json`へ3072 blockの指紋のみを保存した。raw本体は共有しない。次はWindows保存CUDAをこのindexとCPU照合し、相違wordの意味を調べる。

## 全raw差分の位置とscope snapshot生成の問題

CPU block比較で3072中6blockのみ不一致、全6blockをsampleしてMac rawと全1024wordずつ比較した。差は合計8word：全4caseの253955（actor query scope）がCUDA1/Metal0、ナユタ30秒の86024/86025（removal queue packed metadata）と512176/512178（counter-field work count/total）の4word。その他3066blockは全SHA一致。sampleと厳密word比較は`research/portable-linked-rosters-block-samples.json`／`portable-linked-rosters-word-differences.json`へ保存した。sample取得もGPU/compile0。

保存生成CUDAの`actorStatePushQuery_0`は、旧値をuintとして読み取らず同じresults要素へのuint*を保持し、新scopeを書いた後`return *old_pointer`を実行している。生成Metalは`uint previous = results[at]`をstore前に保存し、それを返す。共通Slangの`uint at=...,previous=results[at];results[at]=...;return previous;`が、CUDAで旧scopeを返さない生成になっている。bodyの差は4case共通scope差を説明する。ナユタ30秒の残る4wordが同じ原因から派生するかは未証明。

次は共通Slangでsnapshotを明示的なnoinline value-return helperへ分離する等、旧値がstore前に実値として評価される形へ修正し、両生成物を直接確認する。生成CUDAだけのパッチ、normalizer除外、末尾上書きは行わない。sourceが変わるためMetal849+実4の保持／独立sealと新source certificateを経てから、必要な新full compile/object/linkと短いCUDA比較を行う。旧失敗run・claims・元rawは保存する。

Windowsの実GPU入力generated.cu（1,861,674B／SHA `548a1cc63fbb26f4be5694f704606e8a98bf73c59c4c434db42798fd95461a3a`）も記録SHAと一致し、同じfunction bodyを保存ファイルだけで確認した。`research/portable-linked-scope-cuda-source-peer.json`に保持した。

## 共通snapshot修正候補

`actorStateQueryScopeSnapshot(uint at)`をnoinlineのuint返却helperとして共有Slangへ分離し、push側はcall結果をuintとして保持してからscopeを書き、保存値を返す。pinned Mac Slangの両生成物でcall→store→saved uint returnを確認。CUDA helperには`__noinline__`があり、生成監査はpointer reload／post-store snapshot／誤return／helper内storeを拒否する4負例を持つ。共通resident buildでもこの監査を実行し、対象CUDA/Metalの不正生成を公開前に拒否する。既存resident transport3検査も成功。記録は`research/portable-scope-snapshot-codegen-checkpoint.json`。

候補のGPU実行・計算保持はまだ未検証。GPU sourceはworld_actor_stateの1fileだけ変更し、closure110/ABI/数値式/strict normalizerは不変。旧sealed goldenとcompiler certificateは意図的に未更新である。次はdevelopmentからMetal実4／849の全raw保持と独立sealを確認して新source certificateを作り、必要な短いCUDA検証へ進む。古い成功sourceへ新SHAを貼るだけの認定はしない。

## 修正候補のMetal実4保持と境界ledger

専用Swift cache修正後のdevelopment packet edc6b6e4...でApple M5実4が成功。GPU3.104149秒、全12,582,912byteが旧保存rawと一致し、独立sealもGPU0で成功した。scope修正は旧Metal結果を保持している。旧Swift失敗packet/claimは維持した。

849候補はCPUで歴史的な「6注釈のみ」guardがworld_actor_stateの意図した修正を拒否し、GPU前で止まった。元token ledgerのhashは更新しない。guardにhelper/call/store/returnの完全一致deltaを明示し、その差分だけを旧形へ逆変換した上で、他の全tokenを元hashへ検査する。返すoriginal_file_tokens_preservedはfalse、explicit_scope_snapshot_deltaとunmodified_tokens_preservedはtrueと区別する。helper改変・call引数改変・noinline削除も拒否する5検査が成功。これはCPU source-change ledgerであり、GPUコードのnormalizer除外やrawの差分許容ではない。
