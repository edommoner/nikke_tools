# 元編成のスタック操作

`coordinate-original-stacks`4はペッパー／ルピー／マルチャーナ：マリンスタディの完全元5人編成を使用します。元定義・weapon・成長・操作を保持し、6／10／6／6秒のworldを比較します。マリンスタディの1worldには0.5秒から6体の高HP ADD、3秒で終了する宣言patternを追加します。CPUで計算した発火・射撃・対象スケジュールは入力へ渡しません。

新入口 `gpu/world_coordinate_original_stack_entry.slang` は既存共通kind16（自身が受ける名前指定スタック追加）、17（同消費）、19（対象の有利な現在スタック増加）をsampled受付へ接続します。19の元stat名 `buff_max_stack_add` は上限変更を意味しません。CPU／Slangのkind条件は同じ宣言から生成し、旧ammo入口は新3kindを引き続き拒否します。binary64・wire・Runtime容量は変更しません。

元ペッパーはバーストで19が発火しますが、このworldでは対象stack carrierがなく無変更です。正の増加実証に数えません。元ルピーは100hit通知の19でマイレージ3→4、元15秒durationを更新し、後続の通常付与で最終5になります。マリンスタディは開始時16でホイッスル1→5、idle worldの5秒追加は上限で5のまま。ADD worldは17が実3回発火して5→4→3→2、ADD退出後5秒の16で2→3へ回復します。

受動observerは実 `_dispatch_instant`／`_apply_buff_max_stack_add` を元row・owner・nameで照合し、既存active carrierのfieldsだけをコピーします。対象解決やstat再照会を行いません。元通知・partial_skipsも記録します。GPU比較は既存全battle／packet／RNG／最終ammo／resourceに、元定義別の実発火数と全最終stack carrierの数・source・membership・stack・activation・expirationを追加します。今回の実stack carrierは味方だけであり、敵stack操作20／21や初期化18の認定には広げません。partial shared-recipient skipの正例も未検証です。

旧ammo入口は新stack macro未定義時のCUDA／MSL原生成物が全byte一致。strict source／transport inverseと祖先projectionを保持し、normalizerや旧goldenは変更しません。共有fragmentのraw hash変更により旧source readinessがfalseになることは隠しません。

静的entry-inventoryは全266profile／247入力変換、kind拒否30（旧ammo46）。残りをGPU対応済みとして数えません。次の候補は解除26（11profile）、名前指定持続時間延長15、残るstack18／20／21などです。敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cacheと公開GPU／全キャラ認定も残ります。

## 実証の経路

初回GPU packet `/tmp/nikke-original-stacks-develop-v1`（3f448b6e…）、capture `/tmp/nikke-original-stacks-metal-v1` は全4status0。GPU1回0.956482秒／初PSO92.513740秒／CPU事前40.028685秒、生成cache必須hit・compiler0。同claim retry0です。最初の比較は2/4一致で、マリンスタディ2件の無期限endをnativeのNoneと既存display decoderの1e30で比較したhost側の失敗でした。元失敗・claim・rawを保存しています。

比較器は無期限を実wireの正の無限大bitsから判定するよう訂正し、有限1e30が無限大にならないテストを追加しました。GPU source／全input／native基準を完全保持したpacket v2 `/tmp/nikke-original-stacks-develop-v2`（070d292e…）へ固定。GPU禁止replay `/tmp/nikke-original-stacks-replay-v2` はfresh native全4と一致。shader・数値規約・normalizer・正本は変更していません。訂正後GPU実行0です。

独立fresh監査は別child・全4native・live parent receiptなし、44.644305秒／GPU0で成功。同じ監査からgoldenとsource-only certificateを作成しました。現CUDA compile/link/cache/battleの認定ではありません。

最終compact `/tmp/nikke-original-stacks-final-v1.zip`（4eb6f0ce…）は関連22／制御476検査（Windows専用1skip）成功。終了後に全1945payload SHA／checkout全byteとGPU source・全input／native／output指紋を確認。全reader終了後に原とreplayのrawをSHA／size／inode保持で疎化し、それぞれ27,148,288byte回収、削除0。記録は `research/original-stack-evidence/`／`research/portable-original-stacks-checkpoint.json`。

全キャラ認定0／公開UI CPU／全目標未達。Windowsはrev78 idleを確認し、新規実行依頼0。現CUDA／warm cacheは未取得です。
