# 共通GPU検証CLI

`python scripts/nikke_gpu.py --help`。Python標準ライブラリで制御し、既存のshort検証器の`prepare`/native/`compare`、`portable_typed_cuda_proof_audit.verify_cpu_gpu_calls`、厳密な生成コードnormalizer、`portable_phase_audit`、`run-world-bounded.WindowsJob`、`windows_validation_observer`を再利用します。現段階ではprojectile/reloadのshortスイートを登録しています。`list`はgolden_source_readyも表示します。現行checkoutのreloadは過去goldenとGPU source hashが異なるためpackageを拒否します。検証済みソースのcheckoutで使うか、保存実証から厳密生成一致を確認してgoldenを明示更新してから利用します。期待値を自動追従させません。別のスイートは同じadapter契約で登録します。全効果の自動対応やテスト範囲の自動推論は行いません。

## パッケージ作成とCPU検証

開発checkoutで、必要なPython依存・pinned upstreamを用意します。

```sh
.venv/bin/python scripts/nikke_gpu.py list
.venv/bin/python scripts/nikke_gpu.py package --suite projectile --out /tmp/nikke-projectile.zip
.venv/bin/python scripts/nikke_gpu.py unpack --archive /tmp/nikke-projectile.zip --dest /tmp/nikke-projectile
.venv/bin/python /tmp/nikke-projectile/scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/nikke-projectile-cpu
```

パッケージはGit追跡済みのPython/Slang/Swift、公開data JSON、選択したgoldenと、ローカルpinned upstreamのcalculator/runner/scraper/dataのPython/JSON・LICENSEを含みます。dirtyな開発コードも実byteで固定し、基準HEADとdirty flagを記録します。設定・session・既存巨大レポート・raw・コンパイラ・venvは含みません。全byte/サイズ/SHAとgoldenを`gpu-package.json`に記録し、GPU sourceとgoldenの不一致は作成時に拒否します。アーカイブSHAは転送前後で照合してください。ハッシュは署名や送信元認証ではありません。

既存検証器がscratchを書き込むため、展開先を作業領域として使います。CPU preflightは入力全体と各入力・native指紋を照合し、GPU build/executeを禁止します。続いて登録された限定CPUテストを実行します。書き出したcaptureは上書きできません。

## Metal実行

```sh
.venv/bin/python /tmp/nikke-projectile/scripts/nikke_gpu.py run --backend metal \
  --slang-root /absolute/path/to/.tools/slang-2026.20-Darwin-arm64 \
  --capture /tmp/nikke-projectile-metal
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

登録先は`SUITES`。現在のadapter契約は`prepare() -> (entries, packed)`、`suite.INPUT`、`suite.inspect_native(case)`、`compare(block, domain)`、`cross.digest/normalized`です。source/golden/入力数/native数/限定CPUテストを登録します。契約が異なるスイートは薄いadapterを用意し、計算本体やnative oracleを複製しません。

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

`inventory`は全266プロファイルを静的準備し、既存と同じlowering・効果validatorを各定義へ独立に適用します。`priorities`はカテゴリ・効果種別・stat・target・scaling・未対応フィールドで分類し、影響プロファイル数と「観測された分類が1つだけ」の件数を出します。効果内の最初の失敗より先は未検査なので、件数は対応完了予測ではありません。元定義を変更せず、全プログラムのpackingも別途実施します。packing・GPU受付・実戦一致の認定は分けたままです。

`--develop`は出力goldenがない新機能向けです。入力・CPU基準・GPUソース・パッケージ全ファイルを固定し、同じbounded実行・native比較・全trace比較・保存結果監査を利用します。projectile adapterには新機能のdevelopment入力が追加されます。`--case`はこのパッケージだけに使用でき、未知・重複した名前は拒否します。開発パッケージの実行はMetal限定で、結果は`sealed: false`です。生成CUDA/MSLと全readbackの指紋は記録しますが、過去のgoldenの出力指紋を期待値にはしません。入力/native基準の変化は引き続き拒否します。正式goldenの自動更新やCUDAへの未確定入力送信は行いません。

## CUDAコンパイルキャッシュ

Windowsで`NIKKE_CUDA_COMPILE_CACHE`に専用ローカルディレクトリを指定した場合だけ、NVRTCのPTX生成物を再利用します。キーは生成CUDAの**原byte**、全コンパイルオプション、`nvrtc*.dll`と引用includeされたSlang prelude/headerの原byte SHAです。厳密normalizerはキー作成に使いません。破損・identity不一致は再コンパイルで隠さず失敗させます。無指定なら従来どおり毎回コンパイルします。

キャッシュhitはNVRTC実行成功として記録せず、独立した`cuda_compile_cache`観測に記録します。`compiled.ptx`をcaptureに残し、generated CUDA・キー・出力byte・phase receiptを監査します。CUDA launch/synchronize/readbackとnativeの検査はhitでも必須です。PTXは結果ZIPやGitHub共有payloadに含めません。この変更で削減できる候補はNVRTC区間です。モジュール読み込みの約83秒の削減や、Windows実測での高速化は未証明です。

`cases --suite readiness`はCPU静的梱包だけで入力名を一覧にします。開発成功後は`seal --package-root /tmp/nikke-development --capture /tmp/nikke-development-metal --out /tmp/new-golden.json`で、元パッケージの独立プロセスによるGPU禁止監査とnative再比較を行い、明示的にgoldenを作成できます。失敗・非Metal・非development・現行GPUソース不一致は拒否し、既存ファイルは上書きしません。作成物を対応するsuiteへ登録してから、通常のsealed packageでCUDAを検証します。`readiness`は今回の累積75入力（native60＋拒否15）の正式スイートです。`lost-hp-roster`は実編成検証用、`lost-hp-diagnostic`は既存の診断専用入口を使うもので、いずれもdevelopment限定です。

CUDAのcold検証後、同じパッケージの`cache-check --capture <cold-capture> --out <new-report.json>`で、保存compiled.ptxと同じキャッシュへhitすることをGPU/NVRTCコンパイル0で検査できます。`NIKKE_CUDA_COMPILE_CACHE`と`CUDA_PATH`をcold時と同じ場所へ設定します。キー不一致・missはコンパイルせず拒否します。これは暖機後のGPU所要時間測定ではありません。

キャッシュキーは`#line`のパスも含む原byteです。別の展開先で生成パスが変わるとmissになります。同じ生成物の再利用は確認できますが、展開先を跨ぐhit率の改善は今後の作業です。既存normalizerでパスを除外したSHAを、コンパイルキャッシュのキーへ流用しません。
