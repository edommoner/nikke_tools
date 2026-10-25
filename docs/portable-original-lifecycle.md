# 元編成DoTの別定義発火と再付与

`coordinate-original-lifecycle` はハランの敵死亡前後2world（12秒）と、クルミのバースト再付与（6秒）の完全5人編成を扱います。全72／70元定義・成長・武器・操作を保持し、元のpublic bodyから実engine_workerで準備します。CPUからdamage／発射・死亡スケジュールをGPU入力へ渡しません。敵の出現時刻・HPは宣言worldの入力です。

元の同名DoTには別triggerの2定義があります。元定義IDで実 `_activate` を受動観測し、呼出し前後のcarrier・期限・次tickを記録します。再付与元がrow1でも、実packetと保持timerは元のrow0です。これは新しいDoTを並走させず、tick位相を保って期限を延ばす正本の契約です。GPU比較は全battle／packet／RNG／最終周期状態に加え、両定義それぞれの実発火数とrow1が独立timerを持たないことを検査します。

ハランの負例では敵2体が0秒に倒れ、まだ感染がないためrow1は0回です。正例ではBODYに感染がある状態で10秒に出現するHP1のADD2体が実射撃で倒れ、次frameの死亡通知でrow1が2回発火します。クルミでは36hit由来のrow0を、実バースト由来のrow1が1回更新します。入力の武器やtriggerをこのために置換しません。

**正本の限界:** ハランの条件判定は死亡した敵のIDではなく「現在対象の状態」を参照しています。今回の正例はBODY感染中のADD死亡通知です。死亡敵自身の感染状態や生存ADDへの伝播先を証明するものではありません。召喚敵の攻撃・自爆payloadもschedulerとactor registryで未対応のまま拒否します。ルーティングや正本を変更してこの差を隠しません。

共有shaderは `gpu/world_coordinate_original_entry.slang` のままです。CUDA／Metalの実装・数値規約・wire・容量変更はありません。前の元編成14入力と、実生成CUDA／MSLの全byte保持を検査しました。Windowsでの現CUDA実行／warm cache性能・公開GPU・全キャラ認定は未完了です。

実行記録・独立監査・最終配布の識別子は `research/portable-original-lifecycle-checkpoint.json` と `research/original-lifecycle-evidence/` を参照してください。GPUの再実行はせず、比較器に発火数検査を追加した後は保存readbackのfresh再照合を使います。
