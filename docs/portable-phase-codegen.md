# 共有フェーズのコンパイル範囲を調べるCLI

`phase-codegen`は、検証済みimmutable packageの同じSlang本文を初期化／コマンド実行／出力の3つの診断entryから参照し、CUDA／Metal生成物とreflectionを保存する。GPU本体の本文、数値式、状態layout、既存goldenは変更しない。起動・NVRTC・driver・戦闘計算は行わない。

```sh
python /tmp/package/scripts/nikke_gpu.py phase-codegen \
  --slang-root /absolute/path/to/slang-2026.20-Darwin-arm64 \
  --out /tmp/new-phase-codegen
```

CLIは最初にpackage全fileを検査し、shared resident runtime closureだけを受け付ける。既存のentry名をwrapper内だけで変更し、診断entry名は`portablePhase`とする。wrapperには対象フェーズ呼出だけを記述し、共有関数のbodyをコピーしない。commands／writeは前段の状態がGPU bufferにある前提でコンパイル対象を残すための入口であり、単独実行できる戦闘ではない。ready・queriesの本番継続ABIを実装したわけでもない。

各Slang生成はprecise、既存line directive設定、60秒上限。CUDA／Metalの全6生成物・reflection・stdout/stderr・wrapper・元source SHA・compiler実行file SHA・時間・CUDA字句統計を新規directoryへ保存する。途中失敗・timeout・partial・診断ログも保存し、同じ出力先へ上書きしない。生成中の共有source変更とcompiler変更を拒否する。gpu_callsはGPU build/execute APIが0であることを示し、別項目slang_codegen_callsは生成試行数を示す。反射layout／実ABI／compiler memory／数値一致の認定ではない。

## Macで得られた範囲

正本は`research/portable-phase-codegen-checkpoint.json`。fresh package8470d38eで全6生成が成功、約3.89秒、NVRTC／driver／kernel0。全CPU852件中851成功・Windows専用1skip。本体生成CUDAは保存e630078の1,655,188byte／652関数。フェーズ別の件数・byteはcheckpointを参照する。

初期化ではcommands/write/dispatchの各関数が生成されず、出力側でもinit/commands/dispatchは生成されなかった。commandsではinit/writeは生成されなかったが、dispatchを含む573関数が残る。compiler対象の局所化は出来たが、主な実行閉包は残っている。字句上の縮小からptxasの必要メモリを換算しない。

## 次の判定と安全境界

v132本体PTXは保存stdoutにMemory allocation failureを確認済み。同条件の再実行はしない。次にWindowsで検証するなら、この固定基準から生成したcommands側だけを候補とする前に、source／生成指紋／compiler／options／entry／cache keyを束縛するcompiler専用package契約を設計する。既存full本体のgoldenへ診断出力を混ぜたり、正常戦闘の入口として登録したりしない。

新しい候補のNVRTC／ptxas各1回、60秒／2GiB、fresh Job／BelowNormal／startgate／cleanupを維持する。成功しても他フェーズや本体CUDA成立とは別。commands側も失敗するなら、phase分割で解消する証拠は得られないため、RDC等を自動追加せず次の構造仮説を選ぶ。今回のWindows実行は保存ログのCPU読取だけ。

複数kernelによる本番実装には、ready/queries・早期拒否・初期化・serializers・Runtime保持・子イベント順序・ABIを保持する別契約と、全796の独立比較／sealが必要。全キャラGPU認定0・UI CPU・full CUDA未成立は継続する。
