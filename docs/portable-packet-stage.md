# 固定GPU packetの全stage起動

`scripts/run-gpu-packet.py` は、共通CLIのCPU事前検査から全stageを既存bounded runnerで所有する入口である。GPU本体・Job実装・observerを作り直していない。Windowsで使われた個別helperが過去34046ファイル/1167617324Bの列挙・SHA読取を準備に含め、停止時にCPU runnerの所有情報を回収できなかった問題への対処である。旧記録はpreflight/4検査のみでCUDA0、計算成功や終了原因は認定しない。

親はpackage manifest headerのidentityだけを読む。full member/source検査とCPU preflightは、start gate後の所有childで実行する。準備のために元workspace・過去capture・SDK全体を新たに列挙/再hashしない。Slang/CUDA childの既存toolchain/cache identity検査は維持する。

既存run-world-boundedのfresh unnamed Job、BelowNormal、start gate、所有treeのcleanupと、windows_validation_observerのpre/post観測を再利用する。全stage上限は1〜180秒（cleanupは既存の別5秒）、内側GPU予算は最大60秒、Job上限2GiB。packageの外のfresh captureへrecipe・直接base Pythonのargv・child PID/PPID・Job identity/creation・stdout/stderr・execution・stage-resultを記録する。PIDやファイルだけをlive handleの代用にしない。Windowsは呼出元venvのsite-packagesだけをPYTHONPATHへ渡し、base Pythonを使う。

stageごとにpackage内へ排他的なclaimを作る。既存claimを削除して再実行しない。結果がない場合は元captureと所有handleを回収する。timeoutや観測切れだけを再実行の根拠にしない。各stageの計算/CPU検査、containment、process/service保全は別fieldで返し、不明serviceを保全成功へ昇格しない。

```sh
# 必ずunpack済みpackageをcwdにする。別の個別launcherを作らない。
python scripts/run-gpu-packet.py --stage cpu --backend metal --capture /tmp/packet-cpu --timeout 90
python scripts/run-gpu-packet.py --stage smoke --backend metal --capture /tmp/packet-smoke --timeout 90
```

Windowsではabsolute base Pythonから次の2stageを使う。`NIKKE_SLANG_ROOT`、`NIKKE_SLANG_GENERATION_CACHE`、`NIKKE_CUDA_COMPILE_CACHE`はその呼出しの環境にだけ指定する。smokeは既存controller CPU検査とCPU-only native Job probeで、compiler/GPUを呼ばない。

```text
python scripts/run-gpu-packet.py --stage smoke --backend cuda --capture <fresh-smoke> --timeout 90 --original-workspace <original>
python scripts/run-gpu-packet.py --stage gpu --backend cuda --capture <fresh-gpu> --timeout 180 --original-workspace <original>
```

gpu stageの内側の通常runが、選択suiteの全CPU tests/native preflightを完了した場合だけGPUへ進む。別のCPU stageを先に重ねて実行する必要はない。stageに失敗したら既存結果だけを取得し、手動Ctrl-Cや追加helperで継続しない。

Macでは全stage経路で対象CPU20検査成功。gate内へのfull verification移動後のcontroller smoke32群323検査（Windows専用1skip）もGPU0で成功した。これはWindows Job実機の新しい証明ではない。Windowsでは最初に上記smokeを確認してから、必要な短いsuiteだけを1回実行する。ダメージ蓄積coreのGPU source/41入力goldenは変更していない。
