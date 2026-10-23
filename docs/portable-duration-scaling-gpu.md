# 持続時間の重複倍率を共通GPUへ接続

`duration_scaling: stack_count` をCUDA／Metal共通Slangの開発専用入口
`gpu/world_duration_scaling_entry.slang` へ接続した。値の倍率と独立した静的参照を使い、
参照数の取得・時間の乗算・時刻への加算はGPU側で行う。CPU正本・binary64 primitive・
整数変換・pow・generated-code normalizerは変更していない。

## 参照と順序

既存REFERENCEの第4wordをタグ付きunionとして使う。bit31が持続時間参照、
下位9bitがresource key+1、次の8bitがstate nameであり、空名はkey/nameとも0である。
従来の武器capacity参照は既存の表現を保つ。Runtimeのfield、stride138,952 bytes、
入力104,400 words、出力786,432 words、既存容量は増やしていない。

失効時刻は、recipientの変更や同名carrierへの合流、自身のstack増加より前に計算する。
適用元定義のdurationと参照を使うので、同名aliasに別の参照や時間があっても混同しない。
None／-1だけが無限で、この場合は参照を読まない。有限値は負でも乗算してから時刻に加える。
参照なしは0倍である。既存のreferenceCountを使い、ゲージ（0も有効）→生存召喚体数→
同じcasterの名前付き状態の順を保持し、召喚体の時刻を適用時刻へ合わせる。

条件付き有限passiveの延長もこの計算を使う。一方、正本のbuff_max_stack_addは
元のdurationで更新するため、その経路を倍率へ置き換えていない。
追加入力ではそのハンドラーが3回動き、初回にstack1→2、expiry0.15→0.05へ変わることを確認した。
最初のCPU刺激はinstant型でハンドラー0回だったため、正本が使うbuff型の刺激へ訂正した。
元の未発火記録を保存し、未発火を機能検証へ数えない。

## 検証

共通CLIの `duration-scaling` は47入力（native40／拒否7）。元の31契約と、
passive・参照の失効・召喚体減少・0の優先順位・caster分離・重複操作・コロン付き名前の
混在9入力を比較する。レイブル全80定義の通常／シールド破壊3／30秒も含む。
通常47と旧入口拒否1はMetal一致・独立seal済みである。

診断入口は既存の排他的な4,112-word bankへ、適用元定義・owner・読取有無・参照値・
基礎時間・時刻・expiryを記録する。40正例の160評価／154参照読取が正本と一致した。
時刻・基礎時間・参照値・expiryはbinary64の生ビットで比較し、符号付き0の故障も拒否する。
領域外147,076,160 bytesは通常出力と全byte一致した。容量256で、今回の省略は0である。

初回通常38の比較器には回復貯蔵decodeの接続漏れがあった。保存rawは修正比較器で全38一致した。
診断47の初回比較はarrayとlistの直接比較で停止した。コンテナ型と故障を検査する単体テストを加え、
同一source／input／native／輸送の不変packageを作り、共通CLI `replay` で保存結果を再比較した。
独立sealも成功し、この修復によるGPU再実行は0。元の失敗・raw・claimは保持している。

全1,612入力（native1,276／拒否336）がApple M5のMetalで成功し、独立sealも完了した。
旧1,565入力の4,923,064,320 bytesと新47入力の147,849,216 bytesを、それぞれ以前の出力と全byte一致で保持した。
CPU95群500検査175.582秒、正本事前93.154秒、GPU計算10.954秒、最終5群27検査12.517秒である。
全体の生成cacheは必須hitで追加Slang起動0。親比較はnative1,192再利用／84再計算で、独立sealは再利用しない。

静的packingは234/266・base174/203・47分類へ進み、旧233の全入力記録と残る拒否32記録、
残る分類code順序は保持した。実行前に入力＋出力5,744,084,740 bytesと予備14GiBを確認した。
rawの内容・SHA・path・inodeを保ち、ゼロ領域の割当6,898,712,576 bytesだけを回収した。
raw／claimの削除はない。Windows追加操作は0で、以前の7プロセス終了の原因unknown／環境保全falseを維持する。

保持結果・package識別子・時間は `research/portable-duration-scaling-gpu-checkpoint.json` に記録した。
従来の入口ではタグ付き参照を明示的に拒否し、開発専用の範囲を維持する。
全キャラ実戦認定0、通常画面CPU、現ソースのCUDA実機検証未完了である。
空／免疫／lazy recipient、復活や対象世代との広い混在と、全カタログ実戦の検証は続ける。
