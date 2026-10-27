# パッケージ全byte検査のI/O並列化

Windowsのimmutable package検査は、128ファイル以上の場合に最大4threadで各ファイルを読みます。Macと小パッケージは従来の逐次処理です。実装は同じ `check_records` で、各pathの安全性・重複、regular file、全byteのSHA、sizeを照合します。毎回読み直し、mtime・inode・保存checksumによる再利用はしません。実行gate、CPU正本比較、元PTX/object/linkの監査は省略しません。

回帰テストでは全128ファイルが1回ずつ読まれ、同時readerが最大4であることを検査します。同じ長さへの書換え、消失、directory化、重複、unsafe pathを拒否し、失敗が別threadから呼出元へ伝わることを確認します。

```sh
python research/benchmark-package-byte-check.py --package /absolute/immutable-package --out /absolute/new-result.json
```

このCPU診断は逐次→最大4並列の順で各1回、既存監査器で全byteを読みます。headerと実行source SHAも記録します。順序が固定でOS cache・負荷の影響があるため、時間差だけで一般的な速度向上を主張しません。full packageの意味・出所・GPU計算の検証ではありません。Windowsでは既存のBelowNormal／fresh Job／2GiB／短い上限で囲みます。compiler・GPU・native battleは0です。

Macの2066ファイル／57,514,680byte測定は逐次0.094秒／並列0.102秒でした。このためMacの標準経路は逐次を保持します。Windowsの時間短縮と全stage完走は別途確認が必要です。
