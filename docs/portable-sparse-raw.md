# Macのrawゼロ領域回収

共通CLI `sparsify-raw` は、終了済みcaptureの `readback.bin` から完全にゼロである64KiB単位の領域だけをDarwin F_PUNCHHOLEで未割り当てにする。通常のrawファイルを同じパス・inode・論理長のまま保持し、読み取り値は全バイト不変。圧縮形式への置換、raw削除、claim削除、GPU再実行ではない。既存audit/replayは従来どおりrawを読める。

```sh
python scripts/nikke_gpu.py sparsify-raw --capture /tmp/CAPTURE --out /tmp/PLAN.json
python scripts/nikke_gpu.py sparsify-raw --capture /tmp/CAPTURE --out /tmp/APPLIED.json --apply
```

outはcaptureの外の新規ファイル。applyなしは計画のみ。Darwin専用で、run状態がfinishedのcaptureに限る。run=failedや未終了のcaptureは拒否する。evidenceのartifact SHAとoutput SHA/長さを検証し、rawをO_NOFOLLOWで開き、hardlinkを拒否、排他flockを取得する。全hash照合後のmetadata変化を拒否し、各ゼロ領域を処理直前に再読する。fsync後に全raw SHA、長さ、inode、path、evidenceを再照合する。成功/失敗receiptを外部に残す。領域回収量0は可能だが、内容不一致を成功へ変換しない。

古いartifacts.jsonがraw_included=falseでrawを除外している場合は、既存のhash検証済みevidence.output_sha256を使う。後付けのartifact記録を作らない。元のartifacts/evidence/claim/比較結果を変更しない。ファイル機能による保存容量の改善であり、数値計算・GPU対応・環境保全の証明ではない。

不変packageで実APFSファイルを使う9検査が成功。ゼロ領域回収、繰り返し、計画のみ、誤hash、未終了/失敗、symlink/hardlink、途中例外、並行変更、receiptのcapture内alias、旧raw除外ポリシーを検査した。7つの保存raw（論理合計21054357504B）から計14904459264Bを回収し、全SHA・同一inode・証拠を保持。詳細はresearch/portable-sparse-raw-checkpoint.json。

この機構も大きなGPU実行前の未圧縮input/output全量＋予備容量の予算を省略しない。今後ゼロ領域が増えると予想して実行を開始しない。容量回収完了後の実際の空きで予算を検査する。Mac以外は明示拒否する。
