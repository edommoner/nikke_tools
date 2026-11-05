# 座標physical packetと共通GPU射撃groupの接続

sealed `coordinate-group`225（決定的共通CPU正例199／拒否26）をApple M5の実Metalで検証した。旧control206へ、座標弾とgroupの正本17ケースおよび拒否2ケースを追加する。CUDA／Metalは同じSlang入口・定義・比較器・テストを使い、現在のCUDA実機計算は未取得。

## 実行経路と所有権

通常groupと座標groupが同じallocation／seal／履歴／通知コードを使うよう、元の処理を `attack_group_open.slang` と `attack_group_seal.slang` へ切り出した。式・容量・通知順を再実装せずincludeを共有する。通常入口の生成物は保持する。

新しい `PORTABLE_COORDINATE_GROUPS` 入口だけ、compaction186528wordを1310720から1497248へ移し、完全な出力strideを1507328wordとする。物理scratch19840word・aim160word・Geometry cache128576wordとの3重複を解消する。CP初期化のclearはAG_COMPACTより前で止め、world初期化・packetアドレスの除算／剰余・host両transport・Swift・readbackツールも新strideを使う。入力109528wordとRuntime物理stride138952byteは維持。

BODY packetは既存のnative Actor選択器でBODY／ADDへ配送し、各packetのreceiptをgroupへ収集してから同期counter childを実行する。次pelletはchildの終了後に対象を選び直す。PART／INTERRUPTは座標対象へ直接着弾し、敵数へ含めない。全packetの後で集合を閉じ、同じ既存group通知を実行する。従来の等量pellet配送を重ねて呼ばない。

座標descriptorとActor poolは同じ本物のslotを参照する。ADDが間に入る場合もpattern id／PART・INTERRUPT identityを維持し、shapeや確率・射撃scheduleをhostで計算しない。ここでのADD共有は共通Actor poolと閉じたgroup handleの共有を指す。割合によるdamage配分、RNG、追加の混在sceneを検証済みとは扱わない。

## 検証

新17ケースの112group／186展開physical packet／134receipt／111通知を比較した。部位のみの空集合、scatterと2銃口のdedup、0damageの命中receipt、ADD途中破壊と次pelletの再選択、死んだADDを含む閉集合の子効果、2射手、91射撃の全履歴を含む。先頭64件のlegacy logと、64件目以降も保持するcompactionを照合する。全225入力では正例199の8060frameを検査し、拒否入力の途中frameは除く。

全battle・skill trace・packet順と量／対象／世代、group identity／epoch／対象集合／通知数、照準の2種digest・frame数・最終bankを比較した。旧206の全inputと正例182のnative指紋は保持。旧readback1080033280byteを全照合し、151ケースは全byte一致、55ケースの差165wordは全lease解除済みActor選択器の作業領域 `[227352,243992)` のみ。他領域は全byte一致。旧goldenを新しいscratch内容へ追従させていない。

旧mixed81／composed97／core120／cache133／aim190／control206の生成CUDAとMSLは6ペアすべて全byte一致。normalizer・CUDA cache key規則・binary64／pow／core probability・保護したCPU正本は不変。実CUDA cache hitや両reflectionのbyte保持までは主張しない。新入口のpaired生成は確認し、実行時はgeneration cache必須hit・Slang0。新しいpipelineは初回生成で、warm速度比較ではない。

M5の計算3.717515秒、初回pipeline91.530805秒、shared execute103.212540秒。実dispatchは1回。calculationの独立検証とcontainmentを確認したが、環境保持はnullで、成功へ読み替えない。

## 失敗とGPU禁止replay

初回v1はSwiftのwire guardが旧strideのままでdispatch前に停止した。readbackなし・dispatch0。新strideを受付へ追加し、wire監査でもSwift consumerを検査するよう修正した。

v2で実dispatchとreadbackが完了したが、比較器4ケースが停止した。healing storage decoderが展開された定義行を元effectの添字として扱っていたためsource index／binding ownerへ対応付けた。またADD同居時の論理敵名 `__enemy__:*` は幾何的な自動照準0として比較し、実際のBODY／ADD選択は別にreceipt／packetで照合する。

v3はGPU本体・transport・正本・全入力／native baselineがv2と同一であることを既存replay gateで検査し、保存readbackを全byte保持して比較器だけを更新した。GPU禁止replayで225件が一致し、さらに独立sealが成功。元の失敗capture／claimは保持し、同claim再試行0、GPUの再計算0。

制御系では旧証明書のinclude graph、MAX_OUTPUT_WORDS改変負例、新旧clear分岐の改変検出を更新した。旧証明書の監査はexact inverseで復元したinclude graphを既存collectorで辿る。新しいsnippetを手動除外して現sourceへ証明を流用しない。NVRTC／driver／公開受付の条件も緩めない。失敗記録は証拠に含める。

## 再利用と残件

```sh
python scripts/nikke_gpu.py package --suite coordinate-group --compact --out /tmp/new-group.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-group.zip --dest /tmp/new-group
# 以降のcwdは展開先。保存captureは元のimmutable packageで監査する。
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-group-cpu
python scripts/nikke_gpu.py model-check --out /tmp/new-group-model.json
```

readback系CLIの `--case-words 1507328` も登録した。固定source／入力が同じなら保存結果を利用し、GPUを繰り返さない。CPU140検査とcontrol416検査（Windows専用1 skip）を最終パッケージで行う。rawは削除せず、全byte SHA・サイズ・inodeを保持して疎化する。

新しいWindows依頼は0。次はRNG・未検証の混在scene／割合配分・元キャラ全定義の接続と認定、必要な短い現CUDA実行。全キャラ認定0、native model gap20、UI CPU、公開GPU受付falseで、目標は未達。

[checkpoint](../research/portable-coordinate-group-gpu-checkpoint.json)に固定package／source／件数／容量／時間を記録する。[証拠inventory](../research/coordinate-group-gpu-v1-evidence/inventory.json)から成功・失敗・replay・監査・保持検査の元サイズとSHAを確認できる。
