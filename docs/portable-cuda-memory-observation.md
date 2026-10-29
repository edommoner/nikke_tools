# CUDAメモリ観測と保存ログのCPU要約

失敗した実行を繰り返さず、記録済みの値と未取得の値を分ける。計算・allocationの可否・原因・環境保全の認定を行うツールではない。消費済みのclaimを消したり、既存captureへ観測を追記したりしない。

## CPUだけで読むコマンド

```sh
python scripts/nikke_gpu.py host-memory --out /existing-parent/new-host.json
python scripts/nikke_gpu.py cuda-resource-summary \
  --phases /saved/capture/phases.jsonl --expected-sha256 EXTERNAL_PHASE_SHA \
  --out /existing-parent/new-summary.json
```

出力は不変packageの外側の新規ファイルにする。host-memoryはWindows専用。自分と実parentだけのprivate commit、working set、別の過去peakを取得し、parent handleを閉じる。任意PIDの指定やprocess treeの列挙は無い。既存のJob extended-limit ABIで現在のJobのlimit/peakも読む。未参加・アクセス不能・取得失敗はunknownを保持し、0 bytesとしない。CUDA driverをロードせず、計算認定はfalse。

PrivateUsageは[MicrosoftのPROCESS_MEMORY_COUNTERS_EX](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex)が定義するprivate commit。過去peakを現在の使用量として足さず、親子の時点値もatomicなJob全体の使用量とは扱わない。別途取得したhost値を、過去のCUDA失敗時の値へ付替えない。

保存ログの要約は元artifact等で外部固定したSHAを渡す。全rawのSHAを読み取り前後に検査し、16MiBを超えるログは省略せず拒否する。allocation要求bytes、launchのgrid/block/dynamic shared、戻り値、記録済みsnapshotを取り出す。旧ログの未記録引数やdevice memoryはNone/unknownのまま。切断された最終appendはtruncated_final_event/incompleteとして残し、中間の破損は拒否する。stdoutは件数とnative引数等に限定し、全snapshotはoutに保存する。GPU/driverの新しい呼出しは0。

## 将来の未消費試行で記録するオプション

prepared-runへ`--observe-cuda-resources`を渡す。または共通Windows gpu-prepared requestへ`"observe_cuda_resources":"1"`を追加する。指定なし/`"0"`では追加memory queryは0。run.jsonのresource_observation_requested、子の環境、runtime.jsonのcuda_resource_observation_enabledを一致させる。

既存current context内のcuMemAlloc_v2/cuLaunchKernelの前後だけで、ホスト状態とcuMemGetInfo_v2を読む。contextの作成、allocation、compile、kernel launchは観測器に追加しない。新しいnativeログは、オプションにかかわらずallocation要求bytesとlaunch形状を実引数から記録し、これらのイベントにpointer値を追加しない。元の引数object、戻り値、例外を維持する。

デバイス空き容量は[NVIDIAのcuMemGetInfo仕様](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__MEM.html)に従うOSの時点推定値で、全量をallocationできる保証ではない。他のprocessと競合し得る。host/deviceの各読取も非atomicで、観測時間を含む実行のtimingを通常の純粋な演算時間へ読み替えない。取得に失敗した場合はunavailableを記録し、元のCUDA return codeへ上書きしない。

post監査はresource_observationのrequested/recorded/completeを区別する。completeには各allocation/launch前後の対応したsnapshot、利用可能なhost/parent/Jobとdevice値が必要。これだけでCUDA計算やmemory不足の原因を認定しない。元の全byte・Job・ordered API trace・fresh native比較の境界は保持する。

## ソース検査の重複削減

親のclaim直前にあったverify_packageを1回減らした。元のclaimが全consumer sourceとmanifestを再検査してから所有記録を作るため、その最後のbyte検査へ集約している。認証後のsource改変でGPU起動が止まることを実claim APIで検査する。最初の完全package検査、認証時検査、子自身の完全検査は残る。実行時間の短縮量は未測定。

固定164a2455…で82群861制御検査成功（MacではWindows cleanup1skip）。Windows x64 ABI・device memory getter・エラーは合成戻り値で検査し、実device samplingは未実証。Mac実CLIの合成ログ正常系/誤SHA/Windows専用host gateも検査済み。GPU計算・protected CPU・goldenは不変。実WindowsではCPU host読取と保存済み失敗ログの要約だけを次に確認する。
