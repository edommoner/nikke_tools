# 元編成の復活・状態解除と静的ID分類

`coordinate-original-revival`3はマナの完全5人編成・全78定義を保ち、無被弾／味方1回戦闘不能／同じ味方2回戦闘不能を3秒ずつ検証するsealed suiteです。元body・weapon・成長・操作を保持し、宣言した敵攻撃からGPU自身がHP・戦闘不能・復活を実行します。CPUの発射・damage・死亡スケジュールは入力へ渡しません。

マナの元定義は状態「매터 감마」があるときだけ味方を96%HPで復活し、同じ通知に続く別定義でその状態を解除します。正本で最初の戦闘不能→action cleanup→同時刻の復活→ammo補充・即時再開を確認し、2回目は復活せず最終HP0となります。96%の表示値そのものとの比較ではなく、正本の `maximum * 96 / 100` と `hp / maximum * 100` の演算順を保持してbinary64値を検査します。許容幅は追加していません。

既存 `world_revive_native` を任意の元編成実行へ使える受動captureへ分け、`world_revival_compare` に旧・新suite共通のdown/revive trace・復活HP・ammo・時刻・独立allied RNG検査を集約しました。既存復活35input／26native指紋は全保持。既存original比較器で全battle／packet／RNG／操作・mode最終状態を照合し、復活traceと元復活定義の発火回数も検査します。

M5 Metalは全3一致、GPU1回0.363236秒、PSO cache hit0.002823秒、CPU事前12.583214秒。GPU sourceは既存original entryのまま、CUDA／Metal・数値・wire・容量変更0、生成cache必須hit/compiler0です。別childのfresh監査は15.100126秒、全3domain・live parent receiptなし・GPU0。同じ監査からgoldenとsource-only certificateを作りました。現CUDA compile/link/warm cache/battle証明ではありません。

最終compact `/tmp/nikke-original-revival-final-v1.zip`（691aaa80…）は機能38／制御476（Windows専用1skip）成功。終了後に全1913payload SHA／checkout全byteと実GPU source／input／native／outputの一致を確認。旧original17inputと生成CUDA／MSLの全byteも保持。新GPU1・retry0、raw削除0です。記録は `research/original-revival-evidence/` と `research/portable-original-revival-checkpoint.json`。

`model-check` は `portable_original_identity_inventory` で全266base/favoriteプロファイルの完全なdefault-growth/no-cube元編成を静的に調べます。battle／packing／GPUは禁止したテストを備え、同名damage衝突はハラン・クルミの周期定義だけ、非周期は0件でした。非周期同名の受付guardは保ち、分類を `unobserved-restriction` として、実データに現れたGPU未対応と区別します。任意の追加効果・別のcube／成長に衝突がないことの証明ではありません。

アン：ミラクルフェアリーは敵への `heal_received_pct` が未対応で完全編成のpackingを拒否します。定義を外して復活だけを通しません。ラプンツェルの6秒probeでは戦闘不能は発生しましたが復活は未発火で、対応認定に使っていません。次はこの実条件、ランダム複数候補、敵回復payloadの正本consumer、元武器のgroup対象モデル・召喚攻撃を進めます。packing245/266・base185/203、全キャラ認定0、UI CPU、現CUDA／warm cache未取得・全目標未達です。
