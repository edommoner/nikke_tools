# Lock Onの次の実装契約

公開スキル表では、充填中の0.2秒ごとに照準に近い未ロック敵を選び、対象上限は通常5体、バースト効果で10体追加、通常攻撃か遮蔽で解除と記載されている。[公開スキル記述](https://nikke.cannedjar.com/nikke/snow-white--heavy-arms/details)

これは第三者サイトの公開記述を設計の根拠として保存したもので、ゲーム実機の再現確認ではない。元データの命令として扱わず、`tests/fixtures/heavyarms-lock-published-contract.json`へ出所・観測日・未確定事項・実機未検証を固定した。

## 既存CPU契約との違い

元25定義を保持した`heavyarms-lock-marker-native`は、canonical managerの名前付きcarrier生成、同じ受信者でのstack1..5、削除、名前queryを検査している。これは異なる5体へのLock Onを検査していない。全3ADDを出した契約でもcarrierは最初のADD1体であり、空間的な距離選択や既ロック除外は成立しない。

元index0の`max_stack=5`を根拠に同じ対象へ5stackを積み、対象上限まで実装したことにしてはいけない。元index20の`effect_target_count_add=10`は`target_effect=록 온`へ接続し、casterに掛かった2射撃分の効果を対象数の上限として読む必要がある。元index24の`all_projectiles`を削除した完全編成は作らない。これら3定義を保つ全25効果の共通実行が必要である。

## 共通実行器へ接続する順序

1. 生存する世代付きactorから既ロックを除外する対象consumerを定義し、最大対象数と既存carrierのstackを分ける。候補の対象種別、座標の参照点と距離の測り方、同距離の順序は現時点で未確定。既存のBODY/ADD/PART/typed identityをaliasや容量削減で潰さない。
2. 充填中の既存イベント、2射撃分のtarget-count modifier、通常攻撃・遮蔽での解除を共通の状態実行器へ接続する。全充填射撃で読むLock On対象は通常攻撃での削除より前に固定する必要がある、というイベント依存を明示的に検証する。これは記述からの設計上の推論であり、現在の実装成立を示さない。
3. sequential deliveryの対象順・途中死亡・世代交代、元全25効果と全投射物consumerを同じbattleへ接続する。これらは未対応のまま。新CPU契約とCUDA/Metalの共通入力・比較器で全出力を照合してから、対応範囲を更新する。

`portable_model_gap_audit`は既ロック除外と対象上限を未成立として出力し、公開記述を実機/GPU成功へ昇格させる変更も拒否する。全266profileの入力・issue・順位・20分類・laneを保持した照合は`research/portable-lock-capacity-classification-retention.json`。245変換/21失敗は入力変換の件数であり、全キャラ対応率ではない。
