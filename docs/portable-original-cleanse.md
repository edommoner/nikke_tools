# 元編成の解除と共有RNG

`coordinate-original-cleanse`4は元ココア71定義の対象なし6秒、ココア＋ベスティの完全75定義16秒、ミカ：スノーバディ＋ベスティ／ドレイクの完全77定義26秒、元ロザンナ76定義3秒を使います。元public body・成長・weapon・全効果を保持し、実在する元キャラ同士の編成でデメリットを発生させます。効果削除やCPUで計算した発火・射撃・対象スケジュールの入力はありません。

ココアは15秒の元スキルから、ベスティが5人へ付与した永続の有害fullburst-duration効果のうち実2人だけを解除します。seed3101ではドラー／ベスティが外れ、ココア／N102／メアリーの3人分を残します。ミカは最初のバーストでは無変更、後続バーストで5人分を解除。ロザンナは元10射撃通知の敵有利効果解除を発火し、宣言worldの通常buff2件を新しい順で解除し、解除不能1件を残します。ボス攻撃付随debuff payloadは依然別の未接続項目で、この実証へ混同しません。

新入口 `gpu/world_coordinate_original_cleanse_entry.slang` は既存の共通kind26をsampled受付へ接続します。CPU／Slangのkind条件は同じ宣言から生成。元 `debuff_cleanse` と `enemy_buff_cleanse` の既存flagを保持し、味方resident解除と敵world overlay解除を同じkindとして誤って混ぜません。受動observerは元row／owner／nameを検査し、実dispatch前後の有害carrierのfieldsをコピーします。対象解決やstat照会を追加しません。

## 整数抽選を含む一つの実行順

正例のCPU調査で、元random対象の `getrandbits` 消費が既存の座標観測器に無く、RNG再現検査が停止しました。`world_coordinate_sampling_native` はbattleのglobal Randomだけの実整数呼出しを記録し、point producer内は既存のpoint receiptで扱い、二重計数を防ぎます。契約検査は各呼出し前後のindex、実getrandbits値、消費word数、最終全624語を再現し、未知drawや改変値を拒否します。RNG値／丸め／正本のRandom実装は変更しません。旧マナ復活3ケースの全native指紋を保持しました。

GPU側の味方抽選は従来revival bank、座標射撃はCS bankを参照していたため、新入口だけで同じCS MTへ接続します。recipient計算・診断traceも同じ状態を読み、終了時に既存recipient出力へ全632語を写します。既存の整数sampleアルゴリズムと座標数値規約は変更しません。CPU/CUDA/Metalの計算・効果・検証を分けず、共有Slangと共通比較器を使います。wire／Runtime容量は不変です。

旧stack入口では新macro未定義のCUDA／MSL原生成物が変更前と全byte一致。source／transport inverseと祖先projectionは追加runtime差分も正確に戻し、normalizerや旧goldenを変更しません。旧raw source一致falseを隠さず、旧生成物保持と新入口の計算認定を分けます。

比較は既存全battle／packet／RNG／resourceに、元解除定義の発火数、全最終有害carrierのsource・membership・stack・activation・正確なexpiration、各world nodeの解除回数／解除不能状態を合成します。共有デメリットの未選択3人を削って成功にしません。

静的entry-inventoryは全266profile／247入力変換、kind拒否22（旧stack30）。残りをGPU対応数へ読み替えません。別のstack／resource操作、ボス攻撃debuff入力、敵回復、元武器group対象モデル・召喚攻撃、現CUDA／warm cache、公開GPU／全キャラ認定も残ります。

## 実証と訂正の記録

GPU前のpacket v1は未実行です。共有MTを接続したpacket v2 `/tmp/nikke-original-cleanse-develop-v2`（5ac7c508…）、capture `/tmp/nikke-original-cleanse-metal-v1` は全4status0、GPU1回2.614522秒／初PSO92.055633秒／CPU事前62.260447秒、生成cache必須hit／compiler0。同claim retry0。初回の計算比較は共通actor-poolデコーダがworld-nodeの追加解除fieldsを読んでおらず全4停止しました。原失敗・claim・rawを保持しています。

期待fieldsを削らず、`world_overlay_node_readback` を通常overlay／actor-pool／新比較器で共用しました。解除済みflag・回数を読み、破損flagを拒否するテストも追加。GPU source／全input／native基準を完全保持したpacket v3 `/tmp/nikke-original-cleanse-develop-v3`（89538b56…）のGPU禁止replay `/tmp/nikke-original-cleanse-replay-v3` は全4fresh一致。訂正後GPU0です。

独立fresh監査67.274981秒、別child・全4native再計算・live parent receiptなし／GPU0で成功。同じ監査からgoldenとsource-only certificateを作成しました。現CUDA compile/link/cache/battleの証明へ流用しません。

最終compact `/tmp/nikke-original-cleanse-final-v1.zip`（3f2da212…）は関連28／制御476検査（Windows専用1skip）成功。終了後に全1952payload SHA／checkout全byteとGPU source・全input／native／outputを検査。全reader終了後に原とreplay rawをSHA／size／inode保持で疎化し、各27,115,520byte回収、削除0。記録は `research/original-cleanse-evidence/`／`research/portable-original-cleanse-checkpoint.json`。

全キャラ認定0／公開UI CPU／全目標未達。Windowsの新規実行依頼0、現CUDA／warm cacheは未取得です。
