# 短時間のnative子を起動前に観測する

共通object engineのlink profileは`SuspendedNativeProcess`を使い、一次threadを停止状態で起動する。従来のfocus/module profileと保存済み監査のidentityは保持する。Jobやtimeoutの別runnerを増やさず、既存の60秒／2GiB wrapper、Job queryと親子PID／creation timeの確認を使う。

[WindowsのCREATE_SUSPENDED](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)と[ResumeThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread)の仕様に従い、BelowNormalと停止flagだけで作成し、親と子のJob所属を確認してから一次threadを1回だけ再開する。戻ったsuspend countが1以外なら拒否。失敗した観測も保存し、子が速く終了したことを所属成功の代わりにしない。

CPython `_winapi.CreateProcess`を使い、通常のPopenが閉じる一次thread handleを保持する。stdioのduplicateだけをhandle_listへ指定し、追加handleやJob breakawayを渡さない。shellなし、stdinはDEVNULL、実行環境は親から継承。終了／失敗後は所有したhandleだけを閉じる。このAPI利用は[CPython subprocess実装](https://github.com/python/cpython/blob/3.13/Lib/subprocess.py)に合わせており、Windows実機のCPU smokeによる確認が必要。

既存`run --backend cuda --smoke`のWindows childが、同じlauncherと所属検査で`python -I -S -c ...`を起動する。固定文字列を出して即終了するだけで、コンパイラー・driver・GPUは使わない。Job上限は2GiBを明示し、元の環境へ復元。native-smokeのargv／gate／所属／終了値とstdout/stderrを確認してからsmoke成功とする。`--cpu-only --smoke`はAPI模擬テストだけで、実機native gate成立の証明ではない。

link receiptとjournalは`create-suspended-v1`と再開数を要求する。旧link失敗のsnapshot／戻り値を作り直さない。今回の改修は出力作成エラーの修正やlink成功を意味しない。入力拡張子・出力作成・環境アクセスの診断は別であり、WindowsではまずCPU smokeだけを検証する。

## native Job上限の取得

9115884の実Windows CPU217は全成功。停止起動・2PID所属・Resume count1・marker・return0・cleanupも成立したが、旧native観測器はmemory欄を取得せずnullを返すため最終smokeは拒否した。失敗と原本8083fileは保持する。外側の2GiBだけで欠けたnative snapshotを補完しない。

`portable_job_limits`へ従来のWindows x64拡張limit構造を移し、Job設定と観測で共通化する。[QueryInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject)のNULL handleは呼出元の直近のJobを指す。native観測でもclass9を読み、返された長さが144byteの完全な応答であることとJOB_MEMORY flagを確認する。未設定／照会拒否／短い応答を2GiB成功にしない。[構造の仕様](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)に基づき、共有ABIのsize／offsetとNULL Job観測をCPU検査する。既存の上限値・割当・cleanup方針は変えない。
