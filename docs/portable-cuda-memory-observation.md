## 2026-11-02 module-checkへ関数属性とlifecycle観測を追加

既存の`module-check --observe-cuda-resources`で、バッファ確保／コピー／kernel実行なしのcache-only PTX検査へ観測を付けられる。2GiB・最大60秒・BelowNormalの所有Job、sealed package、厳密なcache／生成baseline、1回claimとcleanup監査を維持する。指定なしは追加query0。[実装・CPU108検査・限界](../research/product-cuda-resource-observer-v2.json)。

context作成・module読込・関数取得・関数属性照会・context破棄の前後で、自分／実parent／Jobとdevice推定空き容量を分けて記録する。context作成前、作成失敗後、破棄後はcurrent contextを仮定せずdevice query0。`cuFuncGetAttribute`のenum0..6から、threads/block、shared／constant bytes、local bytes/thread、registers/thread、PTX／binary versionを取得する。失敗や欠落はunknownで0へ補完せず、handleの数値を記録しない。属性照会自体の前後も観測するため、lazy loadingの影響をlaunchの影響と混同しない。

[NVIDIAの関数属性仕様](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__EXEC.html)のlocal sizeは1threadあたりであり、総GPU予約量でもhost commit増分でもない。属性値から1.6GiB増加の原因を断定しない。現段階はMac上のfake driver／Windows ABI／module allowlistのCPU検査で、Windows実driverでの新観測はまだ0。`memory_observation_complete`は従来のallocation／launchを対象とし、moduleの別`lifecycle_snapshots`／`function_resources`を計算成功へ昇格しない。module監査はrequested、runtime flag、実記録、全境界順を別々に照合する。

元の生成shader・計算backend・CPU正本・input／output wire・数値規約・goldenは全byte維持。標準266profile／203キャラの計算証拠は前のsealed owner5751e24c…から保持する。Windowsへは保存成果物のパス／SHA確認だけを依頼し、同じ戦闘を再実行していない。以下は過去記録。

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

固定164a2455…で82群861制御検査成功（MacではWindows cleanup1skip）。Mac実CLIの合成ログ正常系/誤SHA/Windows専用host gateも検査済み。GPU計算・protected CPU・goldenは不変。

## WindowsのCPU実証と保存PTXによる次の改善対象

同じ固定packageで5群53検査が成功（30.577秒）。host-memoryは4.575秒で、自分と親のprivate commit／working set／過去peak、親handle解放、Jobの2GiB上限を実Windowsで取得した。Windows x64の実host ABIは確認済み。ただしこれは失敗時の値ではなく、実device samplingは未実証のまま。

保存済み181,311byteのjournalを外部SHAで検証し、CPU要約が4.609秒で成功した。元のallocation3回成功／launch戻り値2／context destroy成功を保持した。旧journalには要求byte・launch形状・memory snapshotが無く、取得済みhost値で埋めない。全3段階は終了後Job空／元136file不変／新GPU claim無し。serviceが未知のため環境保全はfalse。

既存ptx-stats --callgraphも8.374秒で成功。元のPTX・CUBIN・compile receiptと一致し、entryから271定義すべてに直接到達する。未解決・外部・間接call・cycleは0。宣言local上位はdispatch 9,784byte、quantityTotals 5,192byte、tick 2,584byte。ただしPTXの宣言量は物理register／最終peak stack／失敗原因ではない。元136fileとcache証跡5fileの計141fileも不変だった。

次は既存のresident dispatch frame storageをmoving-groupへ接続し、全15入力／native3／拒否12と全出力比較を保持してMetalで検証する。quantityTotalsのseen配列とflagsの統合は別候補。追加の時計・計算式・効果実行器を作らず、資源削減は新しい生成物の測定後だけ認定する。

今回のWindows追加GPU／driver／compile／link／native battleはすべて0。消費済み失敗試行は再実行していない。公開要約4ファイルの全byte・外部SHA照合と判断は `research/portable-prepared-memory-and-ptx-peer-v1.json`。旧ローカル実装checkpointの未実証値は当時の記録として保持する。
