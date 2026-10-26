# 型付きスキルと実照準点の接続

`coordinate-typed-live-aim` は、型付き対象の選択点を、固定入力から正本と共通GPUの実照準bankへ切り替える開発用suiteです。既存の形状・生存世代・奥行き選択、補正、DFSとreceiptをそのまま使います。照準を解決し直したり、CPUで生成した照準予定を入力したりしません。

`point_source: "caster_aim"` ではliteral `point` を拒否します。既存入力の予約word11をmodeに使用し、元の固定点入力は全byte保持します。GPUは宣言した攻撃sourceのownerを読み、既存 `coordinateAimPoint` を呼びます。CPUは正本 `CharState._aim_point` と同じ実bank／auto fallbackを読みます。対象を選ぶ時点の照準を使うため、正本のtimerスキルが読む前フレームの照準を保ちます。

照準操作を試すケースは、育成専用profileへ操作を混入させません。元の編成・効果・武器・config・seedを照合した後に、名前を明示した `declared_aim_controls` を適用します。CPUとGPU入力は同じ操作overlayを使い、既存のburst等は保持します。overlayを使ったケースは `original_controls_preserved: false` と別記し、元操作の無変更を主張しません。

新規ケースはauto aim、スキル前に手動照準を切り替える場合、同フレームの切替前の照準を読む場合、HPシールドへの照準です。既存28入力へ4ケースと不正mode／live点へのliteral混入／予約領域の拒否3ケースを加える35入力です。CPU正本は22ケースです。

通常武器が型付き対象へ命中する処理、型付き対象をauto aim候補へ入れる処理、移動する対象、貫通・遮蔽とゲーム実機の規則は未対応です。この段階のconsumerは、明示した係数100・2秒周期のスキルです。全キャラ・正本の敵弾／shield consumer・公開GPU対応の認定は行いません。

M5 Metal全35入力・独立GPU禁止監査に成功し、その結果からgoldenを固定しました。GPU計算2.359530秒、初回pipeline92.611882秒、独立監査203.872149秒。関連60／制御480検査成功（Windows専用1skip）、実GPU1回・retry0です。旧28入力の全input/native fingerprintと出力227,584,000byteを保持しました。旧型付き入口の164依存sourceも全byte一致のため、旧入口の再コンパイル・再GPUは行いません。

```sh
python scripts/nikke_gpu.py package --suite coordinate-typed-live-aim --compact --out /tmp/typed-live-aim.zip
```

最後のパッケージ固定では計算producerと入力・出力・生成物の同一性を検査し、完了済み独立監査を結び付けます。GPUを再実行して最終パッケージを作り直すことはありません。新しいpipelineのwarm hit、CUDA実機、全キャラ認定は未取得です。出所は `research/portable-typed-live-aim-checkpoint.json` を参照してください。

現在の開発経路はpackage作成・run直前・独立sealでCPU参照を計算します。GPU数秒に対してCPU参照は各数分かかるため、作成とrunの重複計算を固定source・owner・監査境界を維持して統合する経路が次の効率化候補です。独立した最後の監査を省略する案ではありません。
