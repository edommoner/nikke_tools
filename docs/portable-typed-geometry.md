# 型付き対象の形状と生存状態による選択

`coordinate-typed-geometry` は、元編成を保持した座標戦闘と型付き対象Frameの10入力へ、空間攻撃8入力・不正wire拒否10入力を追加する開発用suiteです。元サクラの敵弾補正と元レイのHPシールド補正を、明示した係数100・2秒ごとの攻撃で検査します。元の全効果・武器・成長・座標射撃は保持します。

入力の予約領域2,320wordへ固定の点、拡張幅、対象ごとの円／回転矩形と奥行きを格納します。入力115,680word・出力2,032,000word・Runtime138,952byteは増やしません。CPUで計算した生存状態や選択結果、射撃予定は入力しません。

GPUのselectorは既存の型付き対象状態とWorldScheduleを読み、生存している現在世代だけを選びます。包含判定には既存の共通binary64形状・三角関数を使い、奥行き、実生成時刻、node、binding順に比較します。選択した対象を既存DFSのscratchへ固定し、同じ攻撃Frameの補正計算とreceipt生成に使用します。対象が存在しない場合は攻撃を発生させません。CUDA／Metalで計算本体を分けません。

追加8ケースは、手前の破壊後の再選択、回転矩形の不命中、拡張幅による境界命中、同位置の生成時刻順、寿命切れ、同一identityの再出現、HPシールド、全対象への不命中です。共通CPU参照で期待handleと世代、damage、完了receiptを検査します。magic、version、個数、kind、拡張幅、予約領域、形状種別、半径の破損はGPU拒否ケースです。

これは明示した `typed_point` スキルのモデルです。通常武器の自動照準、移動する照準点、射線の遮蔽や貫通、ゲーム実機の敵弾・シールド規則は未対応です。全キャラ認定や正本の未対応分類を、このsuiteの受付・成功件数で置き換えません。公開UIはCPUのままです。

M5 Metal全28入力と、別GPU禁止プロセスによる全18native・拒否10入力の独立監査に成功しました。共通CLIの関連56検査・制御480検査も成功（Windows専用1skip）。GPU計算2.321770秒、初回pipeline92.863700秒、独立監査166.166623秒。実GPU1回、同claim再試行0回です。旧10入力の入力・native fingerprintと出力81,280,000byteをすべて保持し、旧型付き入口のCUDA／Metal生成コード・reflectionも全byte一致しました。数値normalizerの除外は増やしていません。

検証基準を独立監査結果から固定し、共通CLIへ登録しています。

```sh
python scripts/nikke_gpu.py package --suite coordinate-typed-geometry --compact --out /tmp/typed-geometry.zip
```

新しい実行が必要か判断する前に、保存結果とsource/input identityを確認してください。今回のgenerationは必須cache hit・追加Slang呼出0です。新pipelineのwarm hitとCUDA実機の証明にはしません。Windowsではこの段階の新規実行を依頼していません。証拠の出所は `research/portable-typed-geometry-checkpoint.json` に記録します。
