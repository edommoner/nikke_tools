# 保存PTXのCPU分割候補と再構成監査

共通CLIの`ptx-partition`は、既存cache entry／verified compile receiptへ元PTXを照合し、選択device functionだけの`focus.ptx`と残りの`remainder.ptx`を新しいdirectoryへ作る。省略時は最大virtual宣言の関数を選ぶ。最大がentryなら拒否し、黙って小さいdevice functionへ切り替えない。

```sh
python scripts/nikke_gpu.py ptx-partition \
  --cache-entry /path/to/cache/KEY.json --phases /path/to/cold/phases.jsonl \
  --out /path/to/new-candidate
python scripts/nikke_gpu.py ptx-partition --audit \
  --cache-entry /path/to/cache/KEY.json --phases /path/to/cold/phases.jsonl \
  --out /path/to/new-candidate
```

生成時は新directoryを排他的作成し、失敗も`plan.json`へ保存する。元PTX／cache／phase／claimは変更しない。監査は元キャッシュから候補全体を再構成して、planと両PTXの全byteを照合する。候補と候補側hashを一緒に書き換えても成功しない。上書きや失敗消去、コンパイラへの自動移行はない。

## 保持する契約

- 元の全function bodyは一意の所有側へ、`{`から`}`までの全byte／SHAを保持する。入力・戻り値のspace／alignment／type／array extentsを検査し、prototypeとdefinitionの引数名の違いだけをABI不一致にはしない。実bodyが参照するdefinition側の引数名を出力へ使う。
- 境界を跨ぐdevice functionは一つの`.visible`定義と対応する`.extern`宣言へ変換する。prototypeを先に置き、初期化tableがfunction addressを参照する場合にも宣言順を保持する。
- module-level global／constantの定義・初期値はremainderだけに置く。focusは同じ名前／type／alignment／array shapeのextern宣言で参照する。生成物も再parseし、唯一の定義・元初期値・version／target／address_sizeを照合する。
- 間接call／外部call／未宣言callee、未対応parameter属性、weak／common／既存extern state、未知module directiveなどは拒否する。debug section等を黙って落とさない。

externが参照するsymbolには一つのvisible/weak定義が必要という[NVIDIA PTX8.4のlinking仕様](https://docs.nvidia.com/cuda/archive/12.4.1/parallel-thread-execution/index.html#linking-directives-extern)を参照した。このtoolは対応する限定文法の構造検査で、assembler／linkerや全PTX文法の検証器ではない。

## 証明しないこと

`passed=true`はCPUでの生成・全body／parameter形状／状態所有権検査の成功だけを意味する。`partition_legal_verified`／`compiler_verified`／`calculation_verified`はfalse、NVRTC／ptxas／link／driver／GPU callsはすべて0。linkageは意図的に変わっているため、元definition全体がbyte不変とは呼ばない。推定compiler memoryや性能改善を認定しない。

既存`assemble`は元PTXを変更しない経路として維持する。新しい候補をそのartifact／cacheやbattle proofへ紛れ込ませない。実験用objectの生成には、別の明示的なmanifest／tool版／flags／Job監査が必要で、ここから自動的には起動しない。

## WindowsでのCPU確認

`research/portable-ptx-partition-source-manifest.json`の固定8ファイルだけをfresh directoryへbytesで復元し、全SHAを検査する。共通CLIの`validation_environment(capture)`を子processへ渡し、`test_portable_ptx*.py`の16件を15秒上限で実行する。成功時だけ、保存v135 cache＋phaseに対して生成1回・再構成監査1回をそれぞれ30秒上限・BelowNormalで行う。未知構文や失敗は保持して停止する。

元PTXと分割したPTX本体はWindowsに保存し、公開／転送しない。Macへ返すのは元SHA・定義数・焦点関数名・状態の名前／型／サイズ・生成物のbytes／SHA・検査結果の小さなsummaryだけとする。これは元PTXのMac独立監査やCUDA成立の代わりにはならない。

## 保存v135の実測結果

固定`f7e83cc2f287f44299dfeb66b0c3ac1477d7569b`の8ファイルをWindowsで照合し、16検査が2.1443秒で成功。候補生成4.4559秒、元cache／phaseからの再構成監査4.1026秒も成功した。191 bodyの所有はfocus1／remainder190、global／constant101定義はremainder単独。focusの`applyDefinitionFrame_0`は306,333byte、remainderは5,477,943byte。これらの大きさからコンパイラのメモリ改善は推定しない。

元PTX／cache／phaseと親環境は不変、NVRTC／ptxas／link／driver／GPU追加実行は0。結果は`research/portable-world-v135-partition-peer-report.json`へ出所付きで保存した。元PTX・候補・完全planはWindowsに残り、Mac独立原本監査ではない。

元PTX＋出所JSONのGitHub共有は人間が明示許可済みだが、Windowsの自動承認レビューが別チャットから取得した回答を認めずpushを再拒否した。push未実行で、別経路の転送や同一pushの再試行も行っていない。共有処理の停止をCPU監査の失敗や追加GPU実行の理由にはしない。
