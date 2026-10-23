# 物理interrupt照準の正本契約

共通CLI `reference --suite interrupt-aim` に24のliteral契約を追加した。正本の物理射撃・対象決定・`BossScript.hit_target`・吸血処理をそのまま実行し、実際の着弾前後の状態をprivate receiptとして記録する。追加のダメージ計算・buff照会・照準照会・RNG消費はない。

`app/portable_interrupt_runtime.py` は明示context内だけで有効になる比較用の橋で、通常CPUの起動やGPU受付は変更しない。canonical ActorKindは0..5のまま、PROJECTILE=2である。interruptはprivate kind6のidentity/generationを持ち、部位やprojectileへ別名化しない。正本ではinterrupt着弾は通常ダメージ合計外・吸血あり・命中トリガーとゲージなしであるため、canonical Impactのcreditを付与しない。元の型付きpublisherにはbody/part/addを従来どおり渡す。

## 固定した契約

本人/他人/共有/空カメラ、markerの0/負数/欠落/同名別stat、runtime条件/有限snapshot、期限切れ/途中出現、interrupt期限、同フレーム破壊、penalty part対照、吸血、散弾と2銃口、再出現generation1→2、chargeと吸血、vanish gateを含む。

24ケースで98件のprivate着弾を記録した。同フレーム破壊後は通常合計外の集計と吸血は残る一方、対象のhits/dealt/landedは増えない。死亡後散弾では12着弾中11がこの経路を通る。再出現では旧handleのexact lookupを拒否する。

記録はnative hit_targetの直後、既存publish_landing hookで同じevent objectから一度だけ消費し、続く吸血通知より先に確定する。別event/未発行/二重使用/非物理/容量超過/nested contextを拒否し、例外後も元のメソッドへ戻る。private記録をcanonical hit creditへ変換しない。

## 検証と証拠の範囲

固定package `877b39ede2ce998e3434c15f464b0e89e30220beb0263e0189569bafe76b3222`、archive SHA `5065a44690ab8c9c920bd1c713a4224883db2f65d7b9084c24544d9a1c560a1e`。fresh展開からreference24と既存state-focus開発入口のCPU23群140検査が成功した。batchは28.4414秒、GPU build/execute/packingはreferenceで全0、Windows操作0。

無観測baselineでは、interruptを表現できない追加の型付きpublish_landing hookだけを無効化し、正本の着弾・会計・吸血・ライフサイクルを実行する。このbaselineとbridgeは全native結果・全skill trace、およびget_buffs/has_live_stat/random.sample呼び出し回数が一致する。これはdefault typed CPU橋がinterrupt対応したという主張ではない。defaultのUnknown world actorとGPU host拒否が残ることも既存検査で確認する。

identity/generation、credit、hits、会計、HP、damageの故障をliteral契約が拒否する。canonical ActorKindの変更、正本CPUや既存CUDA、共通GPUの算術/数値設計/normalizerの変更はない。共有GPU sourceは前回と同一で、GPU再実行0。GPU対応件数には加算しない。

詳細は `research/portable-interrupt-aim-reference-evidence.json` と `research/portable-interrupt-aim-reference-checkpoint.json`。詳細native本文は元/tmp結果に保持し、共有証拠には入力/native/trace指紋と契約結果を保存する。

## 次の接続

共有 `actorPhysicalGate` は現在のkind6 error64を維持している。次はhost/GPUの受付を対で更新し、private種別の通常合計外会計・対象世代・dead同フレーム規約・吸血を既存landing continuationへ接続する。新しい算術実行器やcanonical creditを作らない。24契約をfull battleとprivate receiptへ対応させ、変更sourceのMetal実証と独立seal、保持回帰後に受付を昇格する。全キャラ認定0・UI CPU・目標未達。
