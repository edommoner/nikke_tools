# 元の対象指定・burst判定を共通GPUの盾着弾へ接続

共通CLIのsealed `destructible-skill-retention`157入力（native102・拒否55）と、`destructible-skill-misato-retention`2入力を登録した。Apple M5のMetalで両方が一致し、それぞれ保存readbackの独立sealも成功した。元レイ7スキル＋装備/同伴の全73定義を、元の対象名・family flag・量・時計のまま接続した宣言単一bossモデルの実証である。全キャラ/全world/ゲーム規則/CUDA実機の認定ではない。

## 既存処理を共用する入口

新HSI4だけが元selectorを持つskillを有効にする。HSI1/2/3の既存分岐を維持し、旧入力を黙って拡張しない。source descriptorは武器のみと同じsentinelを維持し、skillはsource rowごとのroute表で指定する。

static compilerは既存の実編成preparation/world compilerを使う。全73定義の順序・owner・名前・条件・倍率表を保ち、元のdamageRoute/count/damageFlagsのwordを変更しない。`all_enemies`のcount128は既存world compilerの正規化を使う。CPUの発射イベント一覧や架空のskillをGPU入力へ加えない。

共通`actorSetCapture`で元selectorを解決し、単一bossのslot/generationを確認する。worksetは同期子の前に解放する。既存Frameへrouteと選択のproviderを加え、元のflagsを`sampleDamageFactorsForReach`へ渡す。HP盾補正だけを既存factor5へ加え、既存`damageFromFactors`で同じ順序・丸めを行う。hit盾は診断量とcredit1を分ける。量・counter family1・named hit・gauge・終了通知は既存のtyped Frame/collector/continuationを使う。盾がなければ元の通常skill Frameへ戻る。

型付きtraceはsource・係数に加え、family1・policy marker・元route/count・burst/AoE/single bitsを記録し、nativeが実際にsampleしたhit_typeと照合する。従来のskill/weapon traceの予約word規則は維持した。unknown route/flag、random/current selector、multi-hit、normal formula、deferred/periodic、post-landing吸血/蓄積、ADD/部位/座標を今回の対応と数えない。

4既存shaderと2新shaderでsource closureは155→157。Runtime全field/offset/stride138952byte、typed quantity core、modifier scalar core、保護CPU/compiler、binary64、strict normalizerは維持する。CUDA/Metalでsource・入力・比較器・テストが共通である。4ファイルの厳密inverseは過去fixtureのsource照合だけに使い、数値や生成コードを正規化して差分を隠す処理ではない。

## 元レイ4ケース

native契約は前段の保存値から変えていない。3秒の早期HP盾は17packet、30秒のHP/hit盾は各38packet、容量500の破壊後bodyは1packetを迎撃する。HP/hitの各ケースで元の3skillをGPUが処理した。

|元のskill|時刻|HP盾の解決量|hit盾の診断量|
|---|---:|---:|---:|
|ドラー R&D 샷|4.116666666666657|748299|748299|
|レイ 선두 제압 2|4.133333333333324|4727897|590618|
|レイ 섬멸용 고폭탄 3|4.216666666666657|44161247|7703705|

レイの700.5%をHP盾だけに加え、hit盾は38creditを消費して50→12となる。ドラーは元`enemies_top_def:1`によりburst/singleがtrue。レイの元B3はstatがdamageなのでburst=falseを保持した。sourceが「スキル3」であることだけでfamilyを変えない。AoE burst=trueの正例はこの4ケースにはなく、その組合せの実機実証済みとは扱わない。

最終HP・弾数・weapon gate・burst状態/trace・body damage・物理shot履歴、全typed packetのsource/係数/時刻/量/対象/receiptがnativeと一致した。旧ミサトの元71定義も同じ新sourceで再検証し、回復を含む結果を保持した。

## 独立監査と保持

157 producer package `e90050d4e7d1aa3b74b3a403c450a081c2e1cae7d622db45aae18fbc940f1d4e`、ミサト2 producer `aeab1203b4e50f3226851fc8b01822e9f0061998a98ce30db79c7e7d8b7848ad`を各1回実行した。初回から両方が成功し、同一claimの再試行0。独立sealはGPU0で保存全出力を再比較した。

共通`readback-retain`で旧141の全input/native指紋とraw591396864byte、旧ミサト2の全input/native指紋とraw8388608byteが完全一致した。旧141はdispatch indexも維持しており、pointer wordを変換して通したものではない。元native4の全値も前段referenceと一致する。保存GPUの新4正例＋拒否1例のfixtureでは、最終HP/弾数、source/係数、Dola/Reiのfamily/route/count、着弾/receipt/statusへの61改変を検出した。

最終sealed package `b00d2fcdb0fa045b33aa4b5b29b7b799041deab5eede57c87658b8b45d676f1b`をfresh unpackし、CPU43/skip0（48.872秒）とnative102（8.273秒）が成功した。保存出力検査を加えた新suiteのCPU上限は90秒、実行全体の上限は180秒。ケースを減らして時間や容量へ合わせてはいない。

157入力のGPU実計算3.110215秒、library1.582443秒、pipeline65.163974秒、child全体71.481398秒。同じsourceのミサト2はGPU1.760292秒、pipeline0.005851秒、child2.554456秒。初回のCUDA/Metal生成2回はGPU0のgeneration段階で行い、両実runとfinal generationはcache必須hit・Slang0だった。Metalのwarm結果をCUDAのcache改善と混同しない。

入力69150340＋出力658505728byteと1GiB予備をinput前/GPU前で確認した。終了済み旧codec2rawの全byte/長さ/SHA/inodeを維持し、疎化で958595072byteの割当を回収した。raw・失敗・claim削除0。

## WindowsのO0診断

接続復旧を確認し、既に共有済みのfixed O0 package `21ba977a8c6d7518ad448c9e1c8d5852eabfd76d06d8d64eb2b7e52ea71ad639`を使う短いCPU/compile診断を各1回依頼した。新レイ157やfull492はWindowsへ実行依頼していない。

Windows報告では、CPU63/native17が成功し、既存プロセスの欠落0・Job終了後空を確認した。O0 CUBIN stageは外側82.825秒で終了し、内側60秒の制限でtimeoutした。NVRTCは進入1/return0、CUBIN/完成compile cacheはなく、driverロード/GPU kernel/再試行0。両Jobはgate・BelowNormal・2GiB・終了後空を確認、欠落0。サービスを特定できず、環境保全はfalseを維持する。過去7終了の原因もunknownのまま。

内側のchild検証17.456秒、Slang generation10.512秒（cold miss、2 compiler calls）が時間枠を使った。NVRTC進入→wait完了の29.376秒は観測間隔で、コンパイル完了時間ではない。O0のコンパイラ所要時間や改善を確認できたとは扱わない。各工程は入れ子なので単純合算しない。

報告のinput SHAはMacの固定Frame26/native17 baselineと一致した。結果はremoteの保存結果要約として記録し、Windowsのraw artifactをMacで独立監査したものではない。旧CUBIN claimと今回O0 claimを保持した。

同じfixed packetのmanifestには2702 filesがあり、research1339、tests562、scripts332、app231、gpu233、data5である。このinventoryだけでどのファイルを除けるかは断定しない。次の効率化はsuite依存関係に基づくpayloadの縮小と、検証・生成・NVRTCの時間内訳の分離を優先する。検査を省いたりtimeoutだけを増やしたりして成功扱いにしない。

## 現在のCLIと残件

```sh
python scripts/nikke_gpu.py package --suite destructible-skill-retention --out NEW_PACKAGE.zip
python scripts/nikke_gpu.py package --suite destructible-skill-misato-retention --out NEW_MISATO_PACKAGE.zip
python scripts/nikke_gpu.py reference --suite destructible-skill-rosters --out NEW_REFERENCE.json
```

fresh unpack先をcwdとして実行する。157とミサト2が新sourceのsealed入口である。standalone16の`destructible-skill-rosters`は別dispatchのgoldenを登録していないためdevelopment_onlyを維持する。旧141/旧ミサト2の専用goldenは歴史sourceとして保持し、現在のcheckoutでは上記の新入口を使う。

全266profile・245packing/base185・残20model gap・issue/順位は限定readiness metadata以外を保持した。通常UIはCPU、全キャラ認定0、最終目標未達。次はAoE burst正例と広いskill混在、元アスカ/マリの貫通と吸血/蓄積、部位/座標/ADDを同じ実行器へ接続する。現CUDAの計算/compile cache改善は未完了である。

証拠: `research/destructible-skill-rosters-gpu-evidence/manifest.json`。checkpoint: `research/portable-destructible-skill-rosters-gpu-checkpoint.json`。
