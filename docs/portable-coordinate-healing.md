# 座標戦闘の回復貯蔵・分配・放出

`coordinate-healing` は既存 `coordinate-auto-reload`322へ16の回復合成worldと2拒否を加える共通CUDA／Metal入口です。回復貯蔵・ATK由来の受療pool・分配・放出の計算本体を増やさず、既存の `heal_charge_runtime`／`healing_storage_runtime`／`heal_share_runtime` を使います。新入口だけがsampled座標戦闘にkind32の放出を受付け、damage skillのない放出だけの入力でも既存整数総計bankを初期化します。Runtime・wire・容量は不変です。

受動native観測は既存 `world_heal_charge_native.capture` と `world_frame_native` の貯蔵観測を使います。元のpool上限・収集・失効・take順序・放出先、実poolの最終状態、HP貯蔵の実容量／現在量を比較します。sampled packet・乱数・ダメージ・skill trace・回復・被弾の元比較器も維持します。CPUが貯蔵量・放出予定・対象の時刻表をGPUへ渡しません。同じ親の通常比較だけでParentOraclesとcreation receiptを再利用し、独立監査はfreshのままです。

16worldは空pool・容量到達・失効・HP貯蔵と受療poolの重複、回復分配・周期回復・吸血、live容量補正、mode散弾、cover修復非預入、一度だけのtake、手動cover、別caster最大HP、終了時active pool、追加の敵を含むdamage／lifestealを組み合わせます。拒否2件は放出名欠落とpool policy欠落です。これはauthored compositionの検査です。元キャラの全効果・本来のweapon/control metadataをそのまま使う完全編成の認定とは分けます。

新kind受付を専用defineで隔離し、旧ソースへの全text/SHA逆変換とbackend登録を検査します。古いgoldenを書き換えず、新しいMetal証拠を要求します。数値正本・software binary64・integer/pow・生成normalizer・CUDA cache keyは変更しません。

CPU専用5検査が成功し、literal packing時のsimulate禁止、実3000上限の一回take、active pool・cover修復、混在actorの着弾観測、厳密wireと未知source拒否を確認しました。fixture作成では親ケース群の同じ再構築を削除し、入力の値や順序を変えません。

新入口は保存Metal出力の全340一致・独立seal済みです。全キャラ認定・公開受付・現CUDA・warm cache性能は未確認のままです。


## 完全編成への次の接続境界

静的な元編成を既存engine preparationで抽出し、マルチャーナ編成68効果（本人14）とデルタ：ニンジャシーフ編成79効果（本人25）の全定義・元weapon metadata・config指紋を保存しました。CPU battle／GPUは実行していません。これは全編成GPU対応ではありません。

次の入力bridgeは `portable_world_roster_input.compile_world_battle` の全定義・owner・元CharState正規化を再利用し、座標・sampled・controlのsidecarへ接続します。authored observerはweapon metadata・reload/post-fire遅延・cover HP・操作設定を上書きするので、そのまま元編成の正本として使いません。元bodyを既存real native referenceへ渡し、user-selected共通座標mathだけを適用する経路と比較します。定義や不都合な武器・skillを抜いて68／79効果の認定にしません。元metadataと正本／compiled inputの同一性を検査してから、短い実編成をGPUへ投入します。


## 失敗と受動観測の移行

初回Metalは340中339一致で、混在actor1件が `Preserved ordered binary64 aggregate` で停止しました。実GPUとnative戦闘本体の総計は両方34,000、GPU exact bankも34,000／17件でした。旧観測器は `ev.target` が空の全敵skillについて、実 `_land` がrouteしたADDラベルを保存しておらず、10packet／20,000をBODYへ誤分類しました。計算本体や許容誤差は変えず、既存の実landing frame観測へ `sampled_routed_delivery` の明示opt-inを追加しました。他のfixtureの観測経路は不変です。

元の失敗case337は同じraw／同じinput全byteのまま元比較器で一致しました。専用migrationはobserver／fixtureの前後SHAを固定し、実ラベルから旧placeholderを戻したnative指紋が原基準に厳密一致することを要求します。放出量・ダメージ・時刻・owner・generation・他入力の変更、未知migrationを拒否します。`--baseline-package OLD --reference-migration coordinate-healing-routed-adds-v1` はこの既知修正だけに使えます。全340入力を再packして全SHA一致を要求し、339入力の基準指紋は保持、変わった観測domain1件だけを計算して新しいimmutable packetへ固定します。基準再作成の重複だけを削減し、全件freshのsaved replayと独立sealは維持します。

```sh
python scripts/nikke_gpu.py package --suite coordinate-healing --develop --compact \
  --baseline-package /tmp/original-packet \
  --reference-migration coordinate-healing-routed-adds-v1 --out /tmp/fixed-packet.zip
python scripts/nikke_gpu.py replay --source-package /tmp/original-packet \
  --source-capture /tmp/original-metal --capture /tmp/fresh-replay \
  --reference-migration coordinate-healing-routed-adds-v1
```

replayは修正版packet自身のCLI／cwdで実行します。原packet・claim・失敗は保持し、copy容量を省略せず事前検査します。再GPUは実行しません。専用7検査はラベル以外のnative変更、入力／GPU source／他の基準／未知observerを拒否し、変更domainだけを基準作成することを確認します。


最初の独立sealは既存の240秒上限で子を終了し、golden／証明書は作成していません。saved replayの全340一致は保持しています。二重に呼ばれる同じmigration guardの全入力再構築を減らすため、独立子process内だけで移行receiptを再利用する経路を追加しました。2回目には両immutable payloadの全file SHAとmanifest／replay／receipt／artifact anchorを再検査し、引数・source・receiptの変更は拒否します。これは戦闘基準のキャッシュではなく、全291 native domainの計算比較はfreshです。専用3検査と既存seal8検査を維持。CPU-only上限240秒、GPU／Windows上限180秒は変更しません。


## 最終独立監査

全340入力（native291／拒否49）のsaved replayが成功し、別processの独立監査も225.422417秒で成功しました。同じ子監査の中で静的入力をfreshに1回構築し、manifest・adapter・全入力／domain指紋と両payloadのSHAを検査して再使用します。native計算結果は使い回しません。移行guardはfresh1／同一子内receipt再利用1、入力構築fresh1／再利用1、live parent receiptなしを実測receiptに記録しました。先行2回の240秒timeoutと元失敗は保持しています。

同じ成功監査から新goldenと専用compiler source certificateを作成し、sealed suiteへ登録しました。実GPUは初回の1回のみ、GPU.755795秒／初回PSO93.081245秒、CPU事前200.755415秒／通常比較8.978930秒。通常比較は同じ親の291基準を再利用、独立監査は全291domainをfresh比較しています。旧322入力は全input／nativeと全2,279,574,528byteのrawを保持しました。

Slang generation cacheは必須hit／compiler0、CUDA・MSL生成物が元GPU captureと両方の全byte同一でした。CUDA実機計算・warm CUDA cache性能の成功にはしません。全rawと原失敗は削除せず、全reader終了後だけSHA／byte／inodeを保つ疎化を使います。


最終compact `a0f3be21…` は1890files／8,822,217byte。機能37・共通制御476（Windows1skip）成功、全payload SHA／checkout全byteと実GPU source/input・修正版native基準一致を確認しました。静的入力の監査内再利用は追加のdomain変異拒否等を含む専用6検査を共通制御へ登録しました。全キャラ認定0／UI CPU／全目標未達を維持します。
