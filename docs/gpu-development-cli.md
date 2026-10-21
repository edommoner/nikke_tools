# 共通GPU検証CLI

`python scripts/nikke_gpu.py --help`。Python標準ライブラリで制御し、既存のshort検証器の`prepare`/native/`compare`、`portable_typed_cuda_proof_audit.verify_cpu_gpu_calls`、厳密な生成コードnormalizer、`portable_phase_audit`、`run-world-bounded.WindowsJob`、`windows_validation_observer`を再利用します。現在のソースに対するsealed suiteは`regression`235です。旧projectile/readiness/stun/roster/skill-cooldown等のgoldenはその時点の履歴として残し、sourceの違うpackageは拒否します。`list`はgolden_source_readyも表示します。新しいsourceは`--develop`でnative比較後に明示sealします。期待値を自動追従させません。別のスイートは同じadapter契約で登録します。全効果の自動対応やテスト範囲の自動推論は行いません。

## パッケージ作成とCPU検証

開発checkoutで、必要なPython依存・pinned upstreamを用意します。

```sh
.venv/bin/python scripts/nikke_gpu.py list
.venv/bin/python scripts/nikke_gpu.py package --suite regression --out /tmp/nikke-regression.zip
.venv/bin/python scripts/nikke_gpu.py unpack --archive /tmp/nikke-regression.zip --dest /tmp/nikke-regression
.venv/bin/python /tmp/nikke-regression/scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/nikke-regression-cpu
```

パッケージはGit追跡済みのPython/Slang/Swift、公開data JSON、選択したgoldenと、ローカルpinned upstreamのcalculator/runner/scraper/dataのPython/JSON・LICENSEを含みます。dirtyな開発コードも実byteで固定し、基準HEADとdirty flagを記録します。設定・session・既存巨大レポート・raw・コンパイラ・venvは含みません。全byte/サイズ/SHAとgoldenを`gpu-package.json`に記録し、GPU sourceとgoldenの不一致は作成時に拒否します。アーカイブSHAは転送前後で照合してください。ハッシュは署名や送信元認証ではありません。

既存検証器がscratchを書き込むため、展開先を作業領域として使います。CPU preflightは入力全体と各入力・native指紋を照合し、GPU build/executeを禁止します。続いて登録された限定CPUテストを実行します。書き出したcaptureは上書きできません。

## Metal実行

```sh
.venv/bin/python /tmp/nikke-regression/scripts/nikke_gpu.py run --backend metal \
  --slang-root /absolute/path/to/.tools/slang-2026.20-Darwin-arm64 \
  --capture /tmp/nikke-regression-metal
```

`--slang-root`はbin/slangcを含むインストール済みSlangルートです。指定しない場合は従来のcheckout内`.tools`配置を使います。共通transportはCUDA/Metal双方を生成し、既存の厳密normalizerで両生成物を照合します。ゲート前観測と検証子のコンパイル/実行には共通の最大180秒予算を使い、後始末は5秒、終了後観測は別枠で最大20秒です。CPU事前検査はこの予算の前に実行します。timeoutを増やして短時間検証の制約を回避しません。

パッケージ内の`gpu-claimed-metal.json`または`gpu-claimed-cuda.json`をGPU前に排他的作成します。切断・失敗後も残し、同じ展開先からの重複実行を拒否します。別の場所へ再展開すれば機械的な禁止は跨げるため、同じpackage/source/inputをやり直す用途に使わないでください。これは全PC共通のキャッシュではありません。

## Windows検証パッケージ

アーカイブをWindowsへ渡し、Windows側の既存Python依存とSlang/CUDAを使います。共有・別チャットへの依頼はそのセッションの利用者承認の範囲で行います。

```powershell
$py = 'C:\absolute\path\to\existing\.venv\Scripts\python.exe'
& $py scripts/nikke_gpu.py unpack --archive C:/proof/projectile.zip --dest C:/proof/projectile
# 制御系を変えたときのCPU Job smoke（GPU0）
& $py C:/proof/projectile/scripts/nikke_gpu.py run --backend cuda --smoke `
  --original-workspace C:/original/nikke_tools --capture C:/proof/job-smoke
# 必要な場合だけ実GPUを1回
& $py C:/proof/projectile/scripts/nikke_gpu.py run --backend cuda `
  --original-workspace C:/original/nikke_tools `
  --slang-root C:/tools/slang-2026.20-Windows-AMD64 --capture C:/proof/cuda-run
```

親はvenvのbase Pythonを選び、venv site-packagesを子のPYTHONPATHに渡して`__PYVENV_LAUNCHER__`を除きます。新しい検証子だけをBelowNormalで起動し、fresh Job所属を観測してからstart gateを解放します。既存プロセスをJobへ割り当てず、サービスの再起動も行いません。

外部ラッパーは`finally`で検証子を後始末した直後にafter snapshotを採取します。モデルの応答再開を待ちません。観測エラーもexecution.jsonへ保存し、cleanupを飛ばしません。観測自体には既存observerの20秒上限があり、終了から30秒を超えたsnapshotは環境保持の成功に使いません。

計算一致、containment、環境保持を個別に記録します。Windowsでサービス識別がunverifiedなら、計算が一致しても環境保持はfalseです。終了コードは0＝成功またはCPU/smoke成功、1＝計算/制御失敗、2＝計算成功・環境保持未成功です。after snapshot失敗が計算結果の不一致を意味するわけではありません。これらはrun/auditの終了コードで、audit-legacyは元監査器の従来の終了規約を保持します。

## 接続断後の回収とGPU禁止監査

```powershell
& $py C:/proof/projectile/scripts/nikke_gpu.py status --capture C:/proof/cuda-run
& $py C:/proof/projectile/scripts/nikke_gpu.py export --capture C:/proof/cuda-run --out C:/proof/cuda-results.zip
```

`run`を再送せず、保存先に対してstatus/exportを実行します。結果ZIPにはJSON/JSONL/logだけを入れ、input/readbackのrawや生成物はWindowsのcaptureに残します。JSONには診断に必要なプロセスID・実行パスが含まれますが、observerはコマンドラインを保存しません。

```sh
.venv/bin/python scripts/nikke_gpu.py import --archive /tmp/cuda-results.zip --dest /tmp/cuda-results
.venv/bin/python /tmp/nikke-projectile/scripts/nikke_gpu.py audit --capture /path/to/full/capture
```

importは原byte・サイズ・SHAを確認し、新規宛先だけへ展開します。回収された小さな結果だけからはrawの独立再照合を主張しません。`audit`はinput/readback/generatedを残した完全captureに対して、同じpackageから実行します。既存native比較をGPU禁止で再実行し、全readback/各入力/native/生成コード、CUDA API成功とJob PID/作成時刻を確認します。

`collect --capture ... --out ...`は進行中/失敗captureからも小さなartifact一覧を生成します。完了後に初めてexportしてください。原報告を書き換えてから再collectし、失敗を成功へ見せる用途には使いません。

履歴v102/103/104の固定JSONは従来の監査器をそのまま呼べます。

```sh
.venv/bin/python scripts/nikke_gpu.py audit-legacy --version 104
```

これは既存監査器の従来の出力先へ派生監査JSONを書きます。原Windows JSONは変更しません。過去の環境保持失敗は失敗のままです。

## 拡張と時間計測

登録先は`SUITES`。現在のadapter契約は`prepare() -> (entries, packed)`、`suite.INPUT`、`suite.inspect_native(case)`、`compare(block, domain)`、`cross.digest/normalized`です。複合domainを持つadapterは`native_reference(domain)`を明示でき、同じnative値全体を返します。`regression`はこの契約でreadiness81・stun46・全定義の実編成32・skill cooldown25・回復貯蔵51をまとめ、各スイートの元の比較器へ委譲します。入力headerと各rowのstride/byte一致を合成前に検査し、一つのshader起動で235入力を処理します。計算本体やnative oracleを複製しません。

`cpu.json`、`cpu-tests.json`、`execution.json`、`phases.jsonl`、`evidence.json`に時間を分けて残します。executionのelapsedはゲート前観測と終了後観測も含みます。API phase/transport時間からコンパイルとGPU処理を区別します。パッケージ作成・転送時間の自動集計、全PC共通の結果キャッシュ、変更ファイルからの検証範囲自動選択は今後の拡張です。

## 未対応分類と新機能の開発

```sh
.venv/bin/python scripts/nikke_gpu.py inventory --out /tmp/nikke-readiness.json
.venv/bin/python scripts/nikke_gpu.py package --suite projectile --develop \
  --out /tmp/nikke-development.zip
# 必要な場合は --case development/lost-hp-defense-1-1--1 で入力を限定
.venv/bin/python scripts/nikke_gpu.py unpack --archive /tmp/nikke-development.zip \
  --dest /tmp/nikke-development
.venv/bin/python /tmp/nikke-development/scripts/nikke_gpu.py run --backend metal \
  --slang-root "$PWD/.tools/slang-2026.20-Darwin-arm64" --capture /tmp/nikke-development-metal
```

`inventory`は全266プロファイルを静的準備し、既存と同じlowering・効果validatorを各定義へ独立に適用します。`priorities`はカテゴリ・効果種別・stat・target・scaling・未対応フィールドで分類します。未対応triggerはvalidatorが返す`operator.domain`（timing/condition）と`operator.descriptor`を保持し、別の演算を同じcodeへ混同しません。同じcodeの診断文は`messages`へすべて保持します。影響プロファイル数と「観測された分類が1つだけ」の件数を出しますが、効果内の最初の失敗より先は未検査なので、件数は対応完了予測ではありません。元定義を変更せず、全プログラムのpackingも別途実施します。packing・GPU受付・実戦一致の認定は分けたままです。

`--develop`は出力goldenがない新機能向けです。入力・CPU基準・GPUソース・パッケージ全ファイルを固定し、同じbounded実行・native比較・全trace比較・保存結果監査を利用します。projectile adapterには新機能のdevelopment入力が追加されます。`--case`はこのパッケージだけに使用でき、未知・重複した名前は拒否します。開発パッケージの実行はMetal限定で、結果は`sealed: false`です。生成CUDA/MSLと全readbackの指紋は記録しますが、過去のgoldenの出力指紋を期待値にはしません。入力/native基準の変化は引き続き拒否します。正式goldenの自動更新やCUDAへの未確定入力送信は行いません。

## CUDAコンパイルキャッシュ

Windowsの既定はSM86向けCUBINです。NVRTCへ`--gpu-architecture=sm_86`・`--fmad=false`を渡し、`nvrtcGetCUBINSize`/`nvrtcGetCUBIN`でバイナリーを取得します。実行時にdeviceのcompute capabilityを照合します。APIは[NVIDIA NVRTC 11.3公式文書](https://docs.nvidia.com/cuda/archive/11.3.0/nvrtc/index.html)に基づき、Windowsの11.3 DLLでもexportをCPU0-GPUの能力検査で確認しました。`NIKKE_CUDA_ARTIFACT=ptx`は診断用の明示選択です。API不在やSM不一致からの自動切替はありません。数値・効果のSlang本体は共通です。

`NIKKE_CUDA_COMPILE_CACHE`を専用ローカルディレクトリへ指定した場合だけ、生成物を保存・再利用します。キーは形式(cubin/ptx)、生成CUDAの原byte、全オプション、NVRTC DLLと引用includeされたSlang prelude/headerの原byte SHAです。破損・identity不一致は失敗させ、normalizerはキーに使用しません。hitでもCUDA launch/synchronize/readback・CPU比較は必須です。`cuda_compile_cache`の観測と、`compiled.cubin`または`compiled.ptx`をcaptureに残します。rawバイナリーは結果ZIP・GitHub payloadへ含めません。

Slangは`-fp-mode precise -line-directive-mode none`で生成し、コンパイラールートをresolveします。Macで独立した2ルートのCUDA/MSL全byte一致を確認しました。改行配置も変わるため、既存normalizerを維持して新たにMetal75を実行・sealし、旧75の全input/output/native指紋との一致を確認しました。v3時点の`readiness`は累積75(native60＋拒否15)です。後続のv4は末尾の更新記録を参照してください。

`cases --suite readiness`は入力名をCPUで一覧にします。開発成功後は`seal --package-root /tmp/nikke-development --capture /tmp/nikke-development-metal --out /tmp/new-golden.json`で、元パッケージの独立プロセスによるGPU禁止監査・native再比較からgoldenを明示作成できます。失敗・非Metal・非development・現行GPUソース不一致を拒否し、既存ファイルを上書きしません。作成物をsuiteへ登録してからsealed packageでCUDAを検証します。`lost-hp-roster`は実編成用、`lost-hp-diagnostic`は既存診断入口用で、どちらもdevelopment限定です。

CUDAのcold実行後は、同じpackageの`cache-check --capture <cold-capture> --out <new-report.json>`で、保存バイナリーと同じcacheへのhitをGPU/NVRTCコンパイル0で確認します。`NIKKE_CUDA_COMPILE_CACHE`と`CUDA_PATH`をcold時と同じ場所へ設定します。コンパイル成功後のmodule load失敗でも、回収された生成物とphase receiptが揃えば検査できます。これはキャッシュ検査であり、計算成功・暖機後のGPU時間測定ではありません。`calculation_verified=false`を明記します。

v105のPTX方式は、コンパイル44.609秒後にmodule loadが返らず180秒で終了しました。kernel launch0、同条件retry0です。missing0/後続残留0/元HEAD・status保持も、失敗したcontainment・サービス識別未確定を成功へ変えません。v106のCUBIN方式もNVRTC内で180秒の予算を消費し、artifact作成・module load・kernelへ到達していません。missing14の原因は不明です。CUBINの実機速度・数値一致と暖機効果は未証明で、時間枠を増やして再試行しません。詳細原本はWindowsローカルに保持し、Macには個人情報を除いた集計を取得しました。

## 保存Metal出力からのデコーダー検証

```sh
# 新しいデコーダーを含むdevelopment packageを作り、別フォルダーに展開する
.venv/bin/python /tmp/new-package/scripts/nikke_gpu.py replay \
  --source-package /tmp/original-package --source-capture /tmp/original-metal \
  --capture /tmp/new-replay
```

元と新しいパッケージのsuite・GPU source・入力・native基準を一致させ、GPU transport・normalizer・canonical参照・新旧の全GPU/upstreamファイルを検査します。元のGPU dispatchが完了していれば、比較だけが失敗したcaptureも再評価できます。timeout・cleanup失敗・未完了dispatchは拒否します。元のraw/generated/evidenceをそのまま読み、元のexecutionは`source-execution.json`として保存します。新しいGPU実行を装うexecution.jsonは生成しません。原package/captureは監査時にも必要なので保持してください。出所はSHA検査であり署名ではありません。

`replay`の`gpu_calls: 0`、`source_gpu_dispatches: 1`、元の`source_execution_passed: false`を区別します。元の失敗を成功へ書き換えません。CPU比較の診断ディレクトリもCLIが準備します。正常入力のGPU statusが0以外の場合は、decodeより先に拒否statusを報告します。

2026-10-21のrecipient6では、元のMetal rawに保存された順序と重複を読み取るデコーダー修正をこの経路で確認し、GPU再実行0で6/6一致から明示sealしました。

## レビュー反映後の範囲

`readiness`の現行goldenはv5で81入力（native60＋拒否21）です。v4で旧75の指紋と全readback byteを維持し、再突入の不正入力6件を追加しました。v5はstun接続後にも全81の入力/native/output指紋とrawを維持しています。`burst-recipients`の13入力は再突入・instant対象の過去ソースでMetal/nativeが一致した記録です。新しいCUDA実機照合は未完了です。古いsuiteがsource不一致を示す場合、そのgoldenを自動追従させません。

`burst_reentry/all_allies`は、発動者に一度だけ再突入要求を記録するnative規約を共通world受付へ接続しています。5人への要求複製はしません。入力のcombat・stat・値・対象をGPUでも検査します。新たな味方対象にはinstant回復も含め、実在名の不在、コロン付き名、対象リストの重複、B3発動前後を共通fixtureで確認しました。

未対応statとrecipientには構造化したreasonを使い、文面だけでrecipientに混同しないようにしました。静的packingは173/266（base122/203）です。これはGPU実戦認定ではなく、通常画面はCPU、全キャラ認定0を維持します。

Windowsの終了処理は所有Jobを明示終了し、子とJob全体が終了した後、handleを保持したまま`post_wait`を採取して閉じます。cleanupは合計5秒で、待機失敗に同じ予算をもう一度与えません。Jobピークメモリも観測します。Macでは状態連動のCPU故障注入を通過しました。Windows専用のGPU0テストは、子孫を持つ2秒timeoutを使い実際の空Jobとピークメモリを検査します。実Windowsでの修正版確認までは、制御修正の実機成功を主張しません。失敗した過去のcontainment/環境保持の判定は維持します。

CUBINはELF形式を確認してからキャッシュへ公開します。不正な生成物は保存せず、既存の破損エントリは引き続き失敗として扱います。キャッシュhitのCPU検査と、実CUDAの計算・性能検査は別です。

### 新スイートの受け渡し

v105で、旧CLIが未知のsuiteを展開後に拒否するbootstrap問題を確認しました。現在の`unpack`はschema・member一覧・重複・原byte SHAを検査して転送し、suite登録の照合は展開先CLIの`verify_package`/`run`で行います。展開中にpayloadのPythonは実行しません。未知schemaは宛先作成前に拒否します。旧CLIの場合は、ZIP全体のSHAとmanifestを確認して取り出した現行CLIで、新しい宛先へunpackしてください。途中の展開失敗はGPU実行とは数えず、元の失敗記録を残します。

### Windows制御検査v108

v107はCPU81/native60の後、テスト用の子起動直後に失敗し、smoke未到達でした。原失敗を保持しています。テスト起動をCLIと同じbase Python・launcher環境除去へ合わせ、wrapper診断を残したv108は単独3件とCLIのCPU69件が成功しました。実Windowsの子孫付き2秒timeout検査と外側smokeで、終了後の空Job・peak memory取得を確認しました。smoke4.841秒、missing0、元HEAD/status保持、NVRTC/driver load/GPU0です。サービス識別unverifiedのため環境保持全体は未認定です。新機能のCUDA計算・coldコンパイル・速度は未検証のままで、次は資源と生成/最適化設定の切り分けです。詳細は`research/portable-world-v107-control-sanitized.json`、`research/portable-world-v108-control-sanitized.json`を参照してください。

## stun・免疫・対象条件

`stun`は共通の36正例＋10不正入力です。状態は解決済みのcarrier対象と生存から読み、条件・期限を独自に進めたり、遅延対象を数値バフとして消費したりしません。免疫はcanonical compilerの既存quantity bit2を使い、wire幅は変えていません。射撃停止・チャージ再開、B1/B2の既定候補を保持した待機、バースト再開、`target_stunned`と`self_stun_immune`を同じSlangで実行します。typed敵の参照条件は現在の敵文脈と世代を使います。敵stunを被ダメージ倍率へ加算しません。

Metal46はnative完全一致し、値0/負値でもpresenceが有効なこと、免疫の付与順・期限・他発動者、未解決rank、子通知中のstun、再出現世代、128対象を検査しました。CPUの外部イベントAPIへはstunを開放せず、private combat worldだけで受け付けます。静的packingは180/266、base126/203で、全キャラ実戦認定ではありません。

## コンパイルだけの短時間診断

```powershell
& $py C:/proof/package/scripts/nikke_gpu.py compile `
  --original-workspace C:/original/nikke_tools --capture C:/proof/compile-cubin-o1 `
  --compile-cache C:/proof/cuda-cache --artifact-kind cubin --ptxas-level 1 `
  --memory-limit-mb 2048 --timeout 60 --slang-root C:/tools/slang-2026.20-Windows-AMD64
```

これはsealed Metal packageのGPUソースと生成CUDA/MSL指紋を検査してから、通常実行と同じ`compile_cuda_source`/NVRTC/cacheだけを使います。ゲームのnative再シミュレーションは行いません。CUDA driverのDLLロード・context・kernelを禁止します。fresh Job/BelowNormal/start gateは共通で、コンパイルの最大予算は60秒、cleanupは5秒です。Jobのメモリ上限は既定2GiB、指定可能範囲は64〜4096MiBで、実際のpre/post上限とpeakを監査します。timeoutを別枠で足して古い失敗を継続しません。`compile-claimed-cuda.json`を排他的に保存し、同じパッケージの再送を拒否します。

`compiler_verified`・`calculation_verified`・環境保持は別です。成功しても計算はfalseです。`compiler.json`、生成物、compiled artifact、phase、Job/環境観測を残し、`audit`/`status`/`collect`/`export`を再利用します。途中失敗のartifactがあっても、完了したAPI/phase/Jobの証拠なしにコンパイル成功へ昇格しません。サービス識別unverifiedも成功へ変えません。compile/auditの終了コードは1＝compiler未確認、2＝compiler確認済み・環境保持未確認です。

ptxasレベルは明示指定したCUBINの0〜3だけを許可し、既定の計算方式・数値規約・FMA無効は維持します。異なるオプションは異なるcache keyです。NVRTC11.3の`--ptxas-options`とptxasの`--opt-level`は[NVIDIA NVRTC文書](https://docs.nvidia.com/cuda/archive/11.3.0/nvrtc/index.html#group__options)・[compiler driver文書](https://docs.nvidia.com/cuda/archive/11.3.0/cuda-compiler-driver-nvcc/index.html#ptxas-options)に基づきます。指定できることと、実機で速く正確に動くことは別で、低最適化版のCUDA数値・速度は未検証です。

v109の実NVRTC11.3は結合形式`--ptxas-options=-O1`をreturn5で拒否しました。固定tiny kernelによる15秒上限のGPU0診断では、`["--ptxas-options", "-O1"]`と`["-Xptxas", "-O1"]`の別引数形式は各1回成功しました。共通コンパイラは前者を使い、オプション配列そのものをcache keyへ含めます。本体のO1コンパイル成功や数値一致は、このtiny診断では認定しません。保存報告は`research/portable-world-v109-option-syntax-sanitized.json`です。

## 実編成の共通回帰

`roster-regression`は9つの公開キャラprofileを各3秒／30秒で準備する18入力です。stunで新しくpacking可能になったD、プリバティの全4段階、マスト：ロマンチックメイド、タキナと、比較用のペオニー・ミランダを含みます。既存の`compile_projectile_battle`、binding proof、native戦闘比較、物理射撃trace比較をそのまま使い、キャラ効果を選別・除外しません。

```sh
.venv/bin/python scripts/nikke_gpu.py cases --suite roster-regression
.venv/bin/python scripts/nikke_gpu.py package --suite roster-regression --out /tmp/nikke-real.zip
# 新しい効果／新しいGPUソースを検証する場合は --develop を明示する。
```

18入力はMetal/native完全一致後に明示sealしました。別ソースへ進んだ場合は、従来どおりstale goldenを拒否します。この代表編成群は全キャラ・全装備・全操作・全敵世界の認定ではなく、通常画面もCPUです。

後続のskill cooldown対応ではセンチの2profile×2期間を追加し、実編成は22入力です。現在は`regression`149の一部としてMetal/native一致を確認しました。旧145入力（readiness81/stun46/実編成18）は入力・全raw出力ともbyte一致です。新機能25入力と149入力は同じ新Slang sourceで検証し、それぞれ明示sealしました。個別の古いgoldenを集約結果で書き換えず、履歴と現行suiteを区別します。

v110の修正版argvは実NVRTCで受け付けられましたが、本体O1コンパイルは約41.20秒（NVRTC約30.11秒）で失敗し、保存stderrの先頭に`ptxas fatal: Memory allocation failure`がありました。Jobは2GiB、終了後空、missing0、GPU0、完成artifact0です。サービス識別はunverifiedで、上限との因果も未確定です。期限延長・メモリ増量・O0への自動再試行は行っていません。キャッシュの実機性能と新機能のCUDA数値検証は未完了です。

成功artifactがある場合のcache hitは、同じpackageの`cache-check`でNVRTC/GPU0の検査をします。cacheディレクトリはcold時と同じ`NIKKE_CUDA_COMPILE_CACHE`へ設定してください。

```powershell
& $py C:/proof/package/scripts/nikke_gpu.py run --backend cuda `
  --original-workspace C:/original/nikke_tools --capture C:/proof/warm-cuda `
  --compile-cache C:/proof/cuda-cache --artifact-kind cubin --ptxas-level 1 --require-cache
```

後続の実CUDA検証を行う場合に使う指定です。`--require-cache`（環境変数`NIKKE_CUDA_CACHE_REQUIRED=1`）では、missはNVRTC program作成前に失敗し、CUDA driverへ進みません。オプションの変化・破損・compiler/headerの変化は自動再コンパイルで隠しません。

## 保存済みコンパイル結果のCPU解析

```sh
.venv/bin/python scripts/nikke_gpu.py compiler-stats --capture /path/to/full/capture --out /tmp/cuda-source-stats.json
.venv/bin/python scripts/nikke_gpu.py ptx-stats --cache-entry /path/to/cache/KEY.json \
  --phases /path/to/original/capture/phases.jsonl --out /tmp/ptx-stats.json
```

両方ともNVRTC／driver／GPU呼び出し0。原ファイルを変更せず、新規出力先だけへ結果を保存します。前者は保存したgenerated.cuをartifact／evidenceで照合し、後者はキャッシュidentityのkeyと原PTX byteを既存のverified compile receiptと照合します。読み取った宣言の集計であり、実レジスタ・compilerメモリの原因・計算一致を認定しません。PTXの未対応宣言は部分推測を返さず停止します。Windowsの保存結果解析も低優先度・短いCPU上限内で実行し、解析のためにcompileを再実行しません。
