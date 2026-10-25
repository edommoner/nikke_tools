# 元の完全編成と座標実行器

`coordinate-original`10はM5 Metalの保存結果照合と、別プロセスのfresh監査に成功し、共通CLIへsealed登録済みです。元の完全編成を検証した限定ケースであり、全キャラ認定・公開受付・現CUDA実行は未完了です。

マルチャーナ／デルタ：ニンジャシーフ、それぞれ4枠目をノアにした完全5人編成の3秒・30秒に、デルタの実被弾2ケースを加えています。全68／70／79／81定義・owner・元weapon/control/config/base-stat hooksを保持します。宣言済み座標worldと選択済み共通数値／物理乱数規約の下で、元bodyをengine_workerへ渡したCPU実行を比較し、authored metadata/stat/delay置換は使いません。入力生成はCPU戦闘を実行しません。

`world_coordinate_original_entry.slang` は既存の座標・回復入口をincludeし、kind1の受付を追加するだけです。名前指定解除・recipient snapshot・通知・state_endは既存の共通handlerを使います。ノア編成では実際の被弾1.0秒でステルスが1→0となり、その後1.1／1.2秒にも解除が通知され、GPUのactivation3・残存carrier0と一致しました。元効果の削除や短縮はありません。

固定GPU packet `/tmp/nikke-coordinate-original-removal-develop-v1`（0d8be0bb…）とcapture `/tmp/nikke-coordinate-original-removal-metal-v1` は初回8/10一致でした。GPU実行4.390秒、初回PSO92.884秒、CPU事前212.835秒。デルタ30秒2件は、legacy projectile historyの上限2048に対する省略55／59件を旧decoderが拒否していました。GPU・入力・native値を変更せず、保持した全射撃のowner・時刻・実メソッド由来mode・pellets／muzzles・予約領域と省略件数を検査するviewを追加しました。全ダメージ・RNG・packet履歴と最終状態は別途比較します。team1024・fractional2048の上限と省略も明示したままです。

共通CLIの `package --develop --compact --baseline-package OLD --reference-migration coordinate-original-projectile-history-v1` は、この固定source-bound比較器訂正だけに使います。計算・reference・GPU・transport・入力と、レビュー済み差分以外の全byteを保持し、全10inputを再pack／hashしてnative指紋10件を保持します。新しいnative計算0、保存結果の全fresh比較が必須、新GPUは禁止です。任意の実装差分を持ち込む機構ではありません。

訂正packet `/tmp/nikke-coordinate-original-removal-develop-v2`（80575ac3…）のGPU禁止replay `/tmp/nikke-coordinate-original-removal-replay-v2` は全10一致。続く独立監査は238.653837秒、別child・live parent receiptなし・全10native domain fresh・GPU0で成功しました。同じ監査からgoldenとfull-source証明を作り、独立監査の二重実行を避けました。原失敗・claim・rawは保持し、新shaderのGPU1回、同claim retry0、訂正後GPU0です。

旧入口は追加macroを定義しないため、CUDA／Metal双方の生成コードが既存healing基準と一致しました。正規化規則は変更していません。これは現CUDAコンパイル／実行／warm cacheの証明にはしません。生成cacheは共通CLIで再利用します。

最終配布 `/tmp/nikke-coordinate-original-final-v2.zip`（68e3a051…）は機能53・制御476（Windows専用1skip）成功。全1904payloadのSHAとcheckout全byte一致を確認し、最終配布でnativeを再計算していません。全reader終了後、原rawとreplay rawはsize・SHA・inodeを保持して疎化し、各67,231,744byteを回収しました。raw削除0です。

対応状況の監査器は、private coordinate=False既定・literal bool guardと、公開engine_workerの座標拒否を別々に検査します。private bridgeと公開GPU認定を混同しません。inventoryは245/266 packing、base185/203、未対応21profiles／20model-gap分類、全キャラ認定0／UI CPUを維持します。記録は `research/coordinate-original-removal-evidence/` と `research/portable-coordinate-original-checkpoint.json` を参照してください。

次は、240秒監査へ余裕を作るCPU observerの対象外locals取得削減、元編成のmulti_hit完全group binding・同名damageのowner-aware観測、down／復活・callback session合成です。Windowsは既存チャットrev78 idleを1回確認しただけで、依頼・追加GPU0。開始できない送信APIへ重複依頼しません。
