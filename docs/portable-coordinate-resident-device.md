# 共通本体の短い実機確認

`coordinate-resident-device` は、既存 `coordinate-resident-arc` の全106入力の先頭4入力を、そのまま使う実機接続確認です。独立した4キャラ全機能認定ではありません。元定義Marciana controlと、サクラ・アンカー・クレイのmodifier probeを含みます。

計算source、115680入力word、2064786出力word、ソフトウェアbinary64、状態・イベント実行器、全末尾出力の比較器は全106と共通です。入力名・全入力SHA・元のnative domainを固定し、順序変更・欠落・domain消失・入力改変を拒否します。全106の登録とgoldenは残します。

全106のfresh native比較はMacでも約411秒かかります。最初のWindows実機接続を180秒以内で確認するため、この4入力の独立したsealed suiteを追加しました。通常runは4件ともfresh native比較を行い、保存CPU結果の再利用や比較省略はしません。全106のCUDA一致を証明するものではありません。

## Metal実証

Apple M5で4件を実際にGPU実行し、計算一致に成功しました。GPU時間0.419713秒。別のGPU実行を伴わないfresh childで4件を再計算し、15.297366秒で独立監査に成功。live parent receiptは使いませんでした。33,036,576byteの全readbackは、保存済みMetal106の先頭4入力のraw全byteと一致しました。source closureと生成正規化SHAも同一です。

最初のsandbox実行はdevice未検出でGPU前に停止しました。その失敗は保存し、deviceへアクセス可能な承認済み実行で新captureを作りました。

## パッケージと保存CUBIN

```sh
python scripts/nikke_gpu.py package --suite coordinate-resident-device --compact --out /absolute/new.zip
```

compactは3559→2129ファイル。除いた1430ファイルは選択外research/testsのPythonだけで、全保持ファイルのbyte、GPU、upstream、fixtures、goldenはfull packageと同一です。固定package IDは配布JSONを参照してください。

Windowsでは共通 `run-gpu-packet.py --stage gpu-linked` を使い、対応sourceの保存済みcompiler packageとJIT-link proofを2キーrequestで指定します。出所・全byte・生成source一致の既存監査を通し、新しいSlang/NVRTC/ptxas/linkは行いません。fresh CPU事前検査、BelowNormal、2GiB、全stage180秒、GPU child60秒、claimと終了処理は既存経路です。失敗時の自動再実行やcompile fallbackはありません。

このprofileのCUDA計算実証は未完了です。計算一致、実行containment、サービス保全を別々に記録します。未対応分類、全キャラ・全特殊効果、公開consumer/UIへの接続は引き続き未完了です。
