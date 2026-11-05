# native子のファイル出力をCPUで確認する

78121d4では一時出力suffixを`.cubin`へ変えても、nvlinkは約0.073秒／ret1で出力作成に失敗した。入力・tool不変、native gate／2GiB／cleanupは成立。前回job/linkのexecはpeer履歴上どちらも`require_escalated`だったため、単に昇格して同じlinkをやり直す計画にはしない。

既存Windows `run --smoke`の即終了native子を、`portable_native_output_probe.py`に置き換える。同じPython／停止起動adapter／Job／cap／PID確認を使い、kernel32の`CreateFileW`でfresh capture内の固定名`native-smoke.probe.partial.cubin`だけをCREATE_NEWする。20byte固定markerを書き、FlushFileBuffers／CloseHandleまで確認する。既存ファイルの上書き、ACL／保護設定の変更、任意出力先、compiler／driver／GPUはない。

成功も失敗も子stdoutへ小さいJSONを出す。失敗API、直後のGetLastError、実際の書込みbyte数、flush／close結果を記録し、失敗時はexit71。親はnative returnとJSONを成功判定前に`native-smoke.json`へ保存し、失敗をmarker欠落だけへ縮めない。成功時は親が実ファイル20byteも照合する。probeだけの成功はnvlinkの出力成功やGPU計算の証明ではない。

- ファイル作成／書込みに失敗した場合：実際のWindowsエラーとJob証拠に基づき次を選び、linkは実行しない。
- 成功した場合：そのnative Python子の出力API成立まで。nvlink固有の実行環境・runtime・アプリ別権限は未確定なので、自動link再試行や保護設定変更へ進まない。

Windows実証は固定packageのCPUテスト＋smoke1回だけ。今回の診断はcompile／link／driver／GPUを起動しない。元失敗・claim・raw sourceは保持する。

APIの引数・失敗値はMicrosoftの[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)、[WriteFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-writefile)、[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)に基づく。疑似APIだけのCPU成功とWindows実機の出力成功を区別する。
