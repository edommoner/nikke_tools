# Metal可視性の事前検査

共通CLIの `metal-device-probe --out NEW_PATH` は同じ実行権限下でMetal deviceを列挙します。20秒上限でSwiftの専用probeを実行し、device名・registry ID・最大buffer長・終了コード・probe source SHA・標準出力／エラーを記録します。Metalのlibrary／pipeline／buffer／command queueは作らず、カーネル実行は0です。計算成功や次のGPU子processの可視性を保証するものではありません。

```sh
python scripts/nikke_gpu.py metal-device-probe --out /tmp/new-metal-device.json
```

通常の `run --backend metal` は、容量と必須cacheの事前検査後、CPU test・入力準備・native計算より前にこの検査を行います。未検出、Swift不足、timeout、不正な応答、実行中のprobe source変化は失敗として記録し、GPU claimを消費しません。CPU-only・smoke・Windows CUDA経路では呼びません。実GPU子は従来通り自分のMetal deviceと実行結果を検査します。

今回のsandbox内では未検出、権限を分けた実行ではApple M5を検出しました。実パッケージの `packet-ratio` で未検出時にCPU準備／test／GPU claimのない停止を確認しました。大きい313入力packetで先に発生した容量検査停止も保存しています。これらはGPU計算の失敗・成功ではありません。

専用8検査は正常・未検出・不正payload・失敗終了・timeout・source変化・OS／cache pathと、CPU前停止／CPU-only・smokeの除外を確認。既存の必須cache境界9検査は本物のbattle packetを持たないfixtureなので、容量／device検査を分離し、元のcache miss／hit・GPU禁止・claim前停止のassertを保持しています。この9検査も共通制御groupへ登録しました。
