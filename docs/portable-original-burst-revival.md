# 元B1復活と共通スキル待機時間短縮

`coordinate-original-burst-revival`4はラプンツェルの完全元編成を6秒ずつ検証するsealed suiteです。無戦闘不能／唯一のB3戦闘不能／N102戦闘不能／センチ編成の味方2人戦闘不能を扱い、全元定義・weapon・操作・成長を保ちます。宣言した敵攻撃以外にCPUのdamage・射撃・死亡スケジュールはGPUへ渡しません。

無対象でもB1から元のrevive定義は実行されるため、受動observerで `_dispatch_instant` の実試行と実復活を分けます。元row・owner・表示名の整合性を確認し、GPUの定義別発火数と照合します。N102ケースは3.8167秒、2候補ケースは4.0333秒に元81.67%HPの復活、ammo補充・即時再開を確認。候補2人が実際に同時に倒れた状態から1人だけを選びます。既存の共有revival trace・HP・ammo・時刻・全battle／packet／RNG・操作／mode比較を再利用します。

**未発火の原因を取り違えないこと。** 唯一のB3が倒れた6秒ケースは、直接native観測した最終ゲージが96.39999999999999%で、B1試行0です。当初の「B3不在で開始不可」という推測は誤りでした。正本はゲージ満タンでB1へ入ります。倒れたB3をB1で復活できないという仕様・モデル制限の証明には使いません。

初回GPU packet v1は先頭3件が一致し、センチ編成だけstatus64で拒否されました。元センチの `skill_cooldown_reduce_pct`（kind22）がsampled入口で未接続だったためです。元効果を削らず、新しい `gpu/world_coordinate_original_clock_entry.slang` で既存共通 `reduceSkillCooldown` を受け付けます。処理本体・CUDA／Metalの数値設計・wire・容量は不変です。元の次発動期限が本当に前倒しされること、発火回数・全periodic deadline／intervalをnativeと照合します。

新macro未定義の旧入口はCUDA／MSL原生成物が変更前と全byte一致し、厳密なsource／transport inverseと負例検査も追加しました。共有sourceの原byteは変わるため旧goldenのraw-source一致はfalseです。旧goldenを自動追従させず、旧生成物保持と新入口の独立証明を区別します。normalizer・共通binary64本体は変更していません。

修正版packet `/tmp/nikke-original-burst-revival-develop-v2`（2b3247aa…）／capture `/tmp/nikke-original-burst-revival-metal-v2` は全4一致。先頭3件の全21,238,272byte保持、全4inputと追加clock観測前のnative値の指紋保持を確認。実GPU計2回（初回拒否とsource変更後）、同claim retry0、失敗・rawは保存しています。新GPU計算0.621067秒／初PSO92.846710秒／CPU事前96.088091秒。生成cache必須hit・compiler0です。

独立fresh監査103.516777秒、別child・live parent receiptなし・全4native fresh／GPU0。同じ監査からgoldenとsource-only certificateを作りsealed登録。現CUDA compile/link/warm cache/battleの証明ではありません。最終compact `/tmp/nikke-original-burst-revival-final-v1.zip`（55d35cc9…）は機能39／制御476（Win1skip）成功、全1923payload SHA／checkout全byteと実GPU source・input・native・outputを終了後に再検査しました。

## CPU専用の元編成入口調査

開発checkoutまたはfull packageで `python scripts/nikke_gpu.py entry-inventory --out UNIQUE.json` を実行します。compactではコマンドを明示拒否します。既存ID監査と同じ元profile準備を使い、全266base/favoriteの元定義を保った座標入力を静的構築します。CPU battle／GPUは禁止し、失敗レポートを保持し、上書きを拒否します。全定義の元ID coverage・入力hash・元定義hash・compiler／data／GPU source hashと実kind一覧を記録します。GPU受付・計算・全キャラ認定は常にfalseです。

現結果は247/266の入力変換、3.71秒、禁止呼出し0。従来world入口の245/266とは入口が違い、group結合2件が増えることをGPU対応率へ加算しません。次はkind9 `gauge_charge` の15キャラ、kind10 `gauge_consume` の12キャラ候補を優先し、sourceの受付・実発火・最終resourceと後続通知を確認します。この一覧自体は当該kindのGPU対応を証明しません。可能なら受付差分を共有schemaからCPU事前検査にも接続し、今回のようなGPU開始後のstatus64検出を減らします。

アンの敵 `heal_received_pct`、他の未受付kind、元武器group対象モデル・召喚攻撃、現CUDAと公開GPU／全キャラ認定は残ります。UI CPU／全キャラ認定0／全目標未達、Windows新依頼0です。証跡は `research/original-burst-revival-evidence/` と `research/portable-original-burst-revival-checkpoint.json`。
