# 保存PTXの呼出グラフ：コンパイルを追加しない診断

既存の`ptx-stats`へ`--callgraph`を追加した。cache entryのidentity key・bytes/SHAを検査し、既存phases.jsonlのverified compile receiptとの一致を確認してから、同じ保存PTXをCPUで読む。元cache／capture／claimへ書き込まず、出力の上書きを拒否する。NVRTC・ptxas・driver・GPUは呼ばない。

```sh
python scripts/nikke_gpu.py ptx-stats \
  --cache-entry /absolute/path/to/cache/KEY.json \
  --phases /absolute/path/to/cold/phases.jsonl \
  --callgraph --out /absolute/path/to/new-report.json
```

従来の宣言統計の既定出力は維持する。追加モードでは全定義のSHA、宣言virtual register／local bytes、load/store opcode別の出現数、直接callの回数、entryから到達する定義、強連結成分を記録する。間接callはprototypeやcalltargetsがあっても未解決とし、外部／未宣言のsymbolも明示する。これらがあると`direct_graph_complete=false`になる。未知modifier・不正call・重複定義を部分成功にしない。

文法は[NVIDIA PTX ISA 8.4のcall仕様](https://docs.nvidia.com/cuda/archive/12.4.1/parallel-thread-execution/index.html#control-flow-instructions-call)を参照した。正規のPTX assemblerやABI検査器を実装したものではない。閉じた直接callグラフであってもglobal／constantの所有権・関数宣言／linkage・引数ABI・対応link toolは別途必要で、`partition_legal_verified=false`を維持する。宣言registerやload/store数は物理register・compiler memory・実行性能へ換算しない。

## 次の判断に使う範囲

保存v135の最大関数と、dispatchなどとの循環呼出群／entry閉包を確認する。単一関数を切り出せると先に決めず、強連結成分と外部依存を調べてから、意味保持した分割やcompiler専用実験の契約を設計する。この診断はPTXを書き換えず、assembly実験も追加しない。

Windowsへ依頼するのは保存済みcache＋phaseのCPU解析だけ。元PTX本体の公開が個別承認待ちである状態は変えず、別経路でのPTX転送は行わない。共有する候補は関数名・件数・hash等の小さな派生統計で、PTX本体／source抜粋／private path／cache内容は含めない。完全reportはWindowsに保存し、小さなsummaryからMacで次の調査を選ぶ。peer reportだけでMacの独立元PTX監査やCUDA計算成立を認定しない。

## 小さなCPU解析用の受渡し

`research/portable-ptx-callgraph-source-manifest.json`は、検証済み通常packageから抜き出す既存CLI／parser／reference registry／2テストの6ファイルをbytes/SHAで固定する。計約142KB。`git show <固定commit>:<path>`のbytesでfresh directoryへ復元し、manifestを照合してから`python -m unittest discover -s tests -p 'test_portable_ptx*.py'`を実行する。Macのfreshコピーで9検査が成功した。別runnerやcompilerを配布せず、通常CLIの`ptx-stats`だけを使う。これはCPU解析用のsource受渡しで、GPU実行packageや戦闘証明の代用にはしない。

WindowsのCPUテストを直接起動する場合も、先に書込み可能な新しいcaptureを作り、共通CLIの`validation_environment(capture)`が返すenvを`subprocess.run(..., env=env)`へ渡す。これは通常の`run_job`／`cpu_test_groups`と同じTEMP/TMP/TMPDIR設定で、親processの環境は変更しない。既定sandbox TEMPでは一時ファイルの作成・削除がPermissionErrorになることがある。失敗した出力は保持し、修正した環境の検査を別captureとして記録する。
