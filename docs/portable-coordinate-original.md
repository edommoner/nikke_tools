# 元の完全編成と座標実行器

開発中の `coordinate-original` は、公開bodyの静的準備から全効果・owner・元武器情報・base stats・設定を保持して、既存の共通座標実行器へ接続する入口です。新しいCUDA専用／Metal専用計算は追加せず、`world_coordinate_healing_entry.slang` と既存の比較器を使います。GPU認定・公開受付・全キャラ対応は未完了です。

マルチャーナとデルタ：ニンジャシーフの各完全編成、および4枠目をノアにした編成について、3秒と30秒の計8入力を用意しました。元の効果数は68・70・79・81で、定義を抜かず全source indexの結合を検査します。座標worldは明示したidle patternであり、元の公開APIに座標受付が実装済みとは扱いません。

CPU正本は元bodyを `engine_worker.evaluate` に渡します。静的準備済みのchars・config・seed・scalar enemy・weapon metadataと実際のrunの一致、登録された全効果の内容・owner・順序を検査した後、宣言済み座標worldと選択済み共通数値／物理乱数規約の下で実行します。authored fixtureのmetadata・stat・delay置換は使いません。入力生成はCPU戦闘を実行しません。

観測ラベルの追加前に登録済み効果とmanager内のordered lookupを同じdeepcopy memoで隔離し、通知indexを再構築します。元の共有parsed definitionsへラベルを残さず、ordered lookupとdispatch間のeffect identityを保持します。既存非座標経路の4入力は変更前の完全bodyとSHAを固定してバイト一致を回帰検査します。

残る受付境界は明示して拒否します。multi_hit groupには完全なgroup bindingが必要です。同名damageはownerを含む観測identityが未接続のため拒否します。未受付のconfigも既存規則で拒否します。これらの静的拒否をGPU計算成功へ数えません。

`python scripts/nikke_gpu.py package --suite coordinate-original --develop --compact --out /tmp/coordinate-original.zip` で固定基準を作成します。実GPUと独立fresh監査が終わるまではdevelopment-onlyを維持します。

初回の固定8入力 `ab4b3b25…` をM5 Metalで実行しました。カーネル・同期・読み戻しは成功、GPU 2.496秒、PSO cache hitで生成約0.003秒でした。全8入力の計算比較は失敗で、sealしていません。元の失敗・claim・rawは `/tmp/nikke-coordinate-original-metal-v2` に保存しています。

マルチャーナの短いケースは全戦闘フィールドが一致しましたが、入力のtraceがburst-onlyだったためスキル履歴がありませんでした。元編成入口だけfullへ変更し、8入力とも変更がword5の2→1だけであることを確認しました。再GPUはまだです。

30秒ではfractional historyの保持2048・省略1822が既存decoderで拒否されていました。元編成正本に実fractional通知の観測を追加し、共通history viewで保持件数と省略件数を厳密に検査します。prefixだけを旧decoderへ渡し、最終accumulator・状態・damageは全実行を比較します。保存済みのマルチャーナ30秒ではnative3870件＝2048＋1822、team3870件＝1024＋2846で、全戦闘フィールドが一致しました。履歴の省略は認定範囲に明記し、全履歴保持とは扱いません。

デルタは元定義7のkind1「名前指定の効果解除」がsampled入口で拒否されました。元効果を除いたり値を変更したりせず、既存共通handlerへの受付接続が次の優先作業です。同名damageとmulti_hit groupの境界も残ります。全キャラ認定0、公開UIはCPU、現CUDA実行とwarm CUDA性能は未確認です。

元編成観測器は共有parsed definitionsを汚染しないこと、元input4件のbyte保持、全効果packing、seed不一致の事前拒否を検査しています。旧340入力／291nativeの指紋は全件保持し、共通比較器6経路の旧GPU blockとの一致も確認しました。CPU profilerの対象外関数で不要なlocals取得を避け、CLIの基準作成にケース別時間を出すようにしています。検証記録は `research/coordinate-original-evidence/` を参照してください。
