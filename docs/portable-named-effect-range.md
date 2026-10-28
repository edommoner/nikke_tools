# 効果名別の範囲倍率と幾何選択

`named-effect-range` は未実装stat `effect_range_pct` を既存のcarrier/event executorへ接続する明示モデル。元マリの `섬멸 지원 5`（500%、9秒、`allies_with_buff:섬멸 태세`、参照名 `섬멸 태세 추가 효과`）をそのまま使う5条件と、派生した小数・負値・加算順・解除・refresh・ゼロ半径の7条件、raw拒否9条件。元キャラ全編成/全定義のbattle認定とは別。

範囲契約はordered percent sum → `1 + sum/100` → declared base radius × factor。名の異なるcarrierを混ぜず、既存の受け手と寿命/条件/stackを使う。native queryは既存target-count readerのstat引数だけを共通化し、nativeの計画・数値reader・順序を再利用する。managerのactive/cache/global stat mapは変更しない。遅延recipientは新たな寿命契約が必要なため拒否する。実際の円/矩形への選択は既存の決定的な二進64 geometryと1e-9接触規約を使う。

新entryは旧event entryを別名でincludeし、同じinitialize/command/serializer関数を順に呼ぶ。そのfinal checkpointの実Runtimeから範囲を読み、同じGPUでcolliderを選ぶ。新しいevent loop、時計、HP、damage計算はない。既存GPUファイルの変更は0。literal tail ERG1/version1は32header＋8×16word、input86,176/output159,744。CPUで計算済みpercent・倍率・距離・選択集合はwireに入れない。標準query0を保持し、元の未使用query63の32wordへ結果を書く。今回のconsumerは明示collider選択までであり、対象へのdamage配送、実worldの世代/生死/順位、元Asukaとのbattle合成は次の工程。

基準半径の実ゲーム値、500%が実ゲームで半径/面積のどちらへ作用するかの実測は未認定。ここでは明示radial growthモデルとして分離し、canonical default/公開GPU受付を変更しない。CPU15検査成功、初版の通知owner誤指定2assert失敗は正本の実結果に従って入力producerを修正した（native計算の変更なし）。固定packetでCUDA/MSL生成→M5 Metal1回→fresh独立監査を行うまではGPU成功としない。
