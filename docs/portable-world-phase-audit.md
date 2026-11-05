# world検証の段階記録と実行上限

v79の通常4,682入力は両GPUで全出力とCPU比較項目が一致した。後続world49入力は全体180秒上限で終了し、readbackがなく、NVRTC／GPU起動のどこまで進んだか分からなかった。この失敗記録を保持し、通常4,682入力と元の連続実行は繰り返さない。

`research/run-world-bounded.py` は既存の `verify-world-suite.py` をそのまま1回呼ぶ。CUDA／Metalとも49入力・共通Slang・golden・全byte比較は同じ。計算本体、コンパイラ引数、ABI、入力、GPUバッファを変更しない。

```
python research/run-world-bounded.py --backend metal --capture research/portable-build/world-phase-unique --timeout 180
```

Windowsでは `--backend cuda` を指定する。通常4,682入力を前置せずworldだけに独立した180秒上限を与える。BelowNormalで開始し、Job ObjectのKILL_ON_JOB_CLOSEを設定してから開始ゲートを開く。設定に失敗するとGPU検証は始まらない。終了・タイムアウトでは検証専用Jobを閉じる。Macでは新規プロセスグループを終了する。stdout／stderrはファイルへ直接保存し、子孫が持つpipeの終了待ちを避ける。終了後の親プロセスwait上限は5秒で、cleanup失敗も記録する。

`portable_phase_audit.py` はSlangビルドとWindowsの実際のNVRTC／CUDA APIを包み、呼び出し直前・戻り値をJSONLへflush／fsyncする。署名と呼び出し引数をそのまま転送し、バッファ内容は記録しない。0以外の戻り値を成功へ変換しない。`cuLaunchKernel`のenteredだけではGPU投入成功とせず、returnedかつコード0だけをAPI成功とする。同期・readbackは別に記録する。API成功だけで数値検証成功とは扱わず、共通suiteの全49出力比較が必要。

captureにはphases.jsonl、stdout.log、stderr.log、execution.jsonと、成功時のworld-report.jsonを保存する。元の共通suiteが作るinput／readback／evidenceも保持する。タイムアウトの正確な停止位置は最後に実測した境界の範囲内だけで述べ、未記録の段階を推定しない。

CPU故障注入では、ネイティブ署名・引数・戻り値の保持、起動エラーを成功扱いしないこと、同期未完了の区別、末尾書き込み中断、例外後の観測器解除、開始ゲート、タイムアウト後の経過時間・段階記録・子孫終了を検査する。Windows固有のJob ObjectはWindowsで同じCPUテストを通してからGPUを使う。新しいworld-only検証を行う場合もGPU再試行ループは設けない。
