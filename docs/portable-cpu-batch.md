# 共通CLIのCPUテストまとめ実行

run/cpu-only/smokeは、登録順の全テスト群を新しい1個のCPU workerで実行します。毎群のPython再起動/importを除きます。既存のcpu-tests.jsonとpattern別stdout/stderrを維持し、tests/failures/errors/skipped/runner_pidを追加。batch全体のstdout/stderrとcpu-batch.jsonに上限・経過時間・終了値・選択patternを保存します。上限は既定60秒で、immutable registryに明記したsuiteだけ`cpu_test_timeout`を使用します（厳密な整数1..180秒、不正値は子起動前に拒否）。GPU/Jobの実行枠とは別です。native subprocessから継承された出力はbatchログに残します。

`skill-hp-basis-retention`は既存8群971入力を、元の入力・native比較器のまま1バッチへ結合します。入力の全byte SHAと元のラベルを検査し、各比較器へ元domainを渡します。最初の60秒検査は330件成功後に上限へ到達し、GPU claimなしで停止・保存しました。このsuiteだけCPU枠90秒とした別packageで55群340検査が66.540秒で成功しました。検査の省略・再利用した成功receipt・GPU枠の延長はありません。これは単発の観測で、速度ベンチマークではありません。

大きな保存結果の独立CPU監査は`seal --timeout 90`を明示できます（既定60秒、整数1..180秒）。正本の再比較・原source/入力/出所検査は変えず、元GPUを再実行しません。無効な値は子起動やファイル操作前に拒否します。

workerは元と同じunittest discovery/runnerを使い、すべてのpattern/fileを開始前に検査します。重複・不正path・欠落、zero discovery、import/test失敗、receipt欠落/不完全/順序違い、timeoutを成功扱いせず、GPU claim/Jobより前に止めます。失敗した群で停止し、それ以降の群は実行しません。workerのsys.pathは終了時に復元します。検査の省略やCPU oracle cacheは導入していません。internal _testsはimmutable package検査を経て起動され、GPU設定や実行を行いません。

7件の故障注入は実際の小さいfixture moduleのdiscoveryと同じPID/全選択群/ログ、失敗後の停止、zero/import error、path事前検査、receipt改変、親のGPU停止/timeout保存を確認。fresh packageの全834件は833成功・Windows専用1skip・失敗0（56.089秒）。

さらにCPU-onlyの実entry-reload-regressionを通し、全796入力/native633と既存input/native SHAを保持しました。旧Metal captureに保存された37群245テストの件数を各群で照合してすべて同じ、新しい7件を加え38群252テストが同じworker PIDで完了。旧各群process起動合計50.087秒に対し、候補batchは34.783秒でした。各1回の観測で、候補は別CPU回帰との一部並行もあり、速度ベンチマークではありません。CPU事前native照合は42.561秒、GPU呼び出し0。source/GPU/native計算・転送・比較を変更せず、追加GPU実行は行っていません。

Windowsの実転送v131は、この変更前の固定438d357で4入力成功した証拠です。CPU worker変更をWindowsで実行した証拠とは区別し、次の必要なWindows検証時にCPU smokeも確認します。full796 CUDA compiler/moduleの失敗、全キャラGPU認定0、UI CPUは未解決です。
