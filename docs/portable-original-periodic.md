# 元編成の同名DoTと共通group binding

`coordinate-original-periodic`4はハラン／クルミの完全5人編成、3秒・30秒をM5 Metalと別processのfresh監査で照合しsealed登録済みです。全72／70元定義・武器・成長・操作を保持し、表示名が同じDoTを登録時の元定義IDとownerへ結び付けます。GPU入力へCPUのdamage／packet／shot scheduleを渡しません。

元のparsed effectsには、ハランの「바이러스 전이」、クルミの「해킹」がそれぞれ別triggerで2定義あります。従来の表示名→最終rowのlookupは区別できませんでした。実登録を元prepared定義・owner・順序と照合した後の `_portable_observer_row` を実際の生成／landing観測に使い、名前・ownerの不一致、欠けたID、同owner・同名でcreation IDのないeventは拒否します。非周期damageの同名は引き続き受付を拒否します。

30秒ケースではDoTが実際に発火し、先頭定義のrow0を同名のrow1へ取り違えずに比較できています。これは両方のtriggerがあらゆる組合せで発火する証明ではなく、enemy deathによるspread、同時refresh等は次の残件です。全キャラ認定・公開受付・現CUDA実行は未完了です。

固定packet `/tmp/nikke-original-periodic-develop-v1`（60a60b66…）、capture `/tmp/nikke-original-periodic-metal-v1` は4全件一致。GPU2.361383秒、PSO cache hit0.003104秒、CPU事前82.305819秒。生成cacheとMetal pipeline cacheを両方必須にし、既存共通shaderを再利用しました。shader／transport／numeric source変更0、GPU1・retry0です。

独立fresh監査は91.144139秒、全4native domain、live parent receiptなし、GPU0で一致。同じ監査からgoldenとfull-source certificateを作成しました。証明書はsource-onlyであり、現CUDA compile／link／warm cache／battleの成功には流用しません。

最終配布 `/tmp/nikke-original-periodic-final-v2.zip`（519c3343…）は機能32・制御476（Windows専用1skip）成功。全1911payloadのSHAとcheckout全byte一致を終了後に確認し、最終配布でnativeを再作成していません。全reader終了後にrawのSHA／size／inodeを保持して4KiB疎化し27,000,832byteを回収、削除0です。

CPU観測器ではmanual observerの対象codeを先に判定し、対象外returnのlocals生成を避けました。元編成10の指紋保持検査は200.573231秒、旧healing340入力／291nativeの全指紋も148.908552秒で保持。後者は現observerの回帰検査であり、新GPU証明ではありません。計測経路が異なるため、これを独立監査全体の速度比較とは扱いません。

multi_hitのliteral lowering／owner mask／event62結合を `portable_group_binding` へ共通化し、通常group入力と座標元編成が同じ処理を使うようにしました。既存group53と元編成10のinputは全byte保持。ベロータ71定義／ニヒリスター73定義も、元効果を削らず静的に結合できます。ただし実nativeのalive／1HP ADDの4world観測は1group1対象・通知0・子damage0で、必要な4／2対象を満たしませんでした。これは元のsingle-packet routing／対象モデルの不足として残し、静的packingや未発火ケースからGPU対応・全キャラ対応を認定しません。ルーティングをall-enemiesへ置換していません。

現在のmodel-checkは同名周期入口のproof/source matchを示し、公開GPU／全キャラ認定はfalseです。Windowsへの新依頼／GPU0。次は実enemy-death spread／同時refresh、必要なnonperiodic source identity、down／復活とcallback sessionを進めます。240秒監査上限と元case長を維持してください。記録は `research/original-periodic-evidence/`、`research/portable-original-periodic-checkpoint.json` を参照してください。
