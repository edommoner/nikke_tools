# wire登録と保存結果の監査

`portable_wire_layout.py` がPython transportとSwift guardの共通上限を定義します。`run --backend metal` はSDK存在確認後、CPUテスト／native戦闘・device照会・実行claimより前にSwift guardを厳密検査します。許可表が不一致なら停止し、`metal-wire-preflight.json` は一致した場合だけ作ります。新しい大きなwireは、さらに専用entryと入力／出力寸法・領域所有権の登録が必要です。上限表の追加だけで他のentryを受付しません。

resident arc初回はSwiftに2,064,786語の登録がなく、device作成前に停止しました。原失敗とclaimを保持しています。`refresh-metal-wire` はこの特定のレビュー済みSwift SHAでの失敗だけに使うCPU専用修復器です。新しい不変ZIPを作り、Swiftの許可表1行と、そのbefore/afterを記録する監査JSONの1項目だけを変更します。計算・入力・CPU正本・テストPython・CLI・goldenは全byte保持。原claimを削除・再利用しません。修復後も通常の全native事前検査と独立sealが必要です。任意のSwift変更、別の失敗、dispatchやreadbackがあるcaptureには使えません。

```sh
python scripts/nikke_gpu.py refresh-metal-wire --source-package OLD_PACKET \
  --source-capture OLD_FAILED_CAPTURE --out NEW.zip
```

出力strideが変わるとcaseごとの絶対アドレスも変わります。`resident-arc-retain` は旧106入力と新106入力を全byte監査し、typed DFS scratchの既存writerが記録するtrace参照1fieldだけを、実record indexと新旧case baseの両方へ照合します。その他のprefix全byteと追加scratch全byteも検査。fieldを無視するmaskやGPU生成物normalizerは追加しません。源writer・binding3ファイルのSHA一致とinput/readback全SHAを要求し、計算の独立証明とは分けます。

```sh
python scripts/nikke_gpu.py resident-arc-retain --reference-capture OLD \
  --candidate-capture NEW --reference-evidence-sha256 OLD_EVIDENCE_SHA \
  --candidate-evidence-sha256 NEW_EVIDENCE_SHA --out NEW_RETENTION.json
```

M5の新106出力ではtraceアドレス20語がcase stride差だけ移動し、実trace recordとの整合を確認しました。それ以外の旧領域861,567,920 byteは一致し、新tail13,901,264 byteも全0。raw自体は同一ではなく、新goldenは移動後のアドレスを含む全byteのhashを保持します。新しいnative監査は別途実行します。生rawと元失敗は保存し、retention監査を計算成功の代用にしません。

WindowsのCIM照会はsandbox内でCimException/native code2でした。Microsoftの[MI_Result定義](https://learn.microsoft.com/en-us/windows/win32/api/mi/ne-mi-mi_result)ではアクセス拒否です。同じ固定queryを正規の`require_escalated`経路で1回実行するとsnapshot取得に成功しました。実行境界で結果が変わったことを示すもので、OS側の根本原因やサービスpreservation成功は主張しません。WMI／ACL／サービス／セキュリティ設定は変更していません。今後の短いWindows検証は、この確認済みの実行権限contextでbounded Jobを使います。
