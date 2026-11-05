# ナユタ・レムの全定義を含む実編成検証

`heal-share-rosters`4入力をMetalで1回実行し、全件一致・独立GPU0 sealを確認した。既存の実編成準備・native oracle・binding・戦闘結果比較器を再利用し、効果を間引かず、CPUで作った戦闘状態をGPU入力へ渡さない。共通GPU sourceとCUDA／Metal両生成指紋は、既存Metal849と完全一致。849のGPU再実行はしていない。

| 対象 | 時間 | 準備／binding定義 | CPU物理履歴 | GPU記録 | 省略 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ナユタ | 3秒 | 81／81 | 155 | 155 | 0 |
| ナユタ | 30秒 | 81／81 | 1,081 | 1,081 | 0 |
| レム | 3秒 | 70／70 | 115 | 115 | 0 |
| レム | 30秒 | 70／70 | 2,103 | 2,048 | 55 |

両編成の支援はミランダ・ドレイク・N102・メアリー。全prepared source indexがbindingへ現れ、欠落0を保存結果のnative指紋へ結んで確認した。戦闘結果・既存skill traceと、物理履歴の記録prefix／省略数を既存比較器で検査する。レム30秒の未記録55packetの個別内容・順序まで一致したとは主張しない。全キャラ認定0を維持する。

登録後の通常packetはCPU preflightとbinding／healing6検査に成功。readiness22検査も成功し、静的全266 profileの入力・失敗と80分類の順位は前回と同一。`hits_parts`だけの未対応3分類はCPU sourceのconsumerを確認したためnative_contract_extensionへ移したが、独立reference0件／runtime検証falseで、受付・GPU対応率は増やさない。次の契約は[parts skill設計](portable-parts-skill-next.md)を参照。

GPU実行約3.140秒は単一観測で、性能測定ではない。GPU再実行0、Windows追加0。本体CUDAは未成立、通常UIはCPU。最終目標未完了。記録は`research/portable-heal-share-real-rosters-checkpoint.json`、goldenは`research/portable-world-heal-share-rosters-short-expected.json`。通常CLIでは`package --suite heal-share-rosters --out <new.zip>`を使いfresh展開する。

次のGPU source変更時は、従来849に加えこの4実編成の保持も検査する。既存の容量制限と過去の省略は保持し、将来の詳細履歴拡張は別の観測契約として扱う。rawや失敗の再生成を目的に同じGPU実行を繰り返さない。
