# 座標弾の実packetと射撃groupのCPU比較基準

`reference --suite coordinate-group-common` が、座標物理弾と実射撃groupのCPU契約17ケースを検査する。決定的共通着弾規約の実際の `_coord_pellet`／`_fire` の戻り値を使い、対象や射撃時刻を組み立て直さない。これはGPU接続前の比較基準であり、公開GPU対応や現在のGPU group計算を証明しない。

## 既存の観測器を拡張する理由と境界

従来の `battle_attack_groups(routing=...)` は同量の通常BODY／ADD packet専用で、`target`付きPART／INTERRUPT packetや範囲の追加packetを拒否していた。`coordinate_packets=True` を明示したときだけ、native routingのまま展開済みpacketを受け取る。既定値false、従来の拒否条件、default battleへの非導入を維持する。all-logical-enemiesとの併用とbool以外は拒否する。

元のCollector／seal／同期dispatchを再利用し、実packetオブジェクトのidentityを射撃の完了まで保持する。BODY／ADDの実着弾が発行するtyped impactだけにattack IDを付け、既存のBODY／ADD policyが集合を決める。PART／INTERRUPTは敵数へ加算しない。記録するreceiptは実際のimpactであり、ダメージ量や確率から敵を推測しない。32 live group／24bit identityは維持し、展開packetには最大1024論理pellet×128packetの保持枠を用意する。全キャラ・全sceneの容量認定ではない。

17ケースは計112group／186展開packet／134receipt／111通知を実行した。3pellet×2銃口は12packetを返すが、BODY6receiptが重複排除され敵1体になる。部位のみ・interruptのみなら空集合。貫通／charge、同射撃snapshot、部位破壊、ADD生存／途中破壊、2射手、91射撃の履歴を含む。0damageのBODY packetにも正本の命中receiptがあり、敵1体として残す。

子効果は閉じた集合を参照する。ADD2体を射撃中に壊した場合、集合はADD0→ADD1→BODYの順で固定され、子の実着弾は生存BODYだけとなる。死んだADDの配分をBODYへ付け替えない。group buffが次の射撃へ反映するケースもあり、全ケースを単なる観測透明性として扱わない。no-listenerでは全battle／packet／traceがbaselineと一致し、0%の観測用buffがある場合はそのnamed stateの有効化以外の全battle field・packet・traceを比較する。

## CLIと監査

```sh
# full immutable packageを新しいフォルダーへ展開し、そのcwdで実行
python scripts/nikke_gpu.py reference --suite coordinate-group-common --out /tmp/new-coordinate-groups.json
python scripts/nikke_gpu.py model-check --out /tmp/new-coordinate-group-model.json
python scripts/nikke_gpu.py consumer-audit --out /tmp/new-coordinate-group-consumers.json
```

referenceはGPU build／executeとportable packingを禁止する。詳細reportは約1.3MBで、元source identity・全native・trace・契約を残す。snapshotの成功を現在の別sourceへ付け替えない。新8テストと既存group31テストを `coordinate-control` の共通CPUゲートへ登録し、合計134件とcontrol416件（Windows専用1 skip）を検査する。

初期CPUテストのno-op named buff差分、0係数でも正本が最小damage1を返すworld、30弾のreloadにより長時間caseが64射撃を超えなかった診断を保持した。0damageは半径8.9の実確率丸めで実現し、長時間caseは容量300で91射撃を実行する。ケース削除や比較値の追従ではない。既存source改変テストが2分岐の片方の変更を見逃した失敗、missing-consumer監査の旧kwonly引数前提の失敗も保存し、両分岐とopt-in既定値／native-only policyを個別に監査するよう修正した。

## GPUへの残りの接続

`model-check` のcoordinate-shot-groups分類はadapter_gapからgpu_port_gapへ進む。native adapter利用可能と、GPU物理group receipt接続falseを別々に記録する。GPU shader／入力wire／旧golden／数値本体／cache規則は今回は変更しない。`coordinate-control`206の正例182のnative指紋を再照合し、旧Metal証明を保持する。新GPU0／Windows新依頼0。現CUDAの計算／cache実hitの検証は未取得。

次は共有group begin／collect／sealを、異なる量・対象を持つ座標physical packetへ接続する。group compactionは旧186528wordを保持して末尾へ移し、clear上限・実reader／writer・host strideを合わせる。BODY packetのnative ADD routingと、PART／INTERRUPTの直接着弾を分離して、receipt発行順と同期child後の次pellet再選択を守る必要がある。座標sceneの `count+1==actorPoolCount` 前提もADDとの同居に対応させる。これらを実装・Metal照合するまでは受付拒否を維持する。

[checkpoint](../research/portable-coordinate-group-reference-checkpoint.json)と[証拠inventory](../research/coordinate-group-reference-v1-evidence/inventory.json)を参照。全キャラ認定0／残model gap20／UI CPU／公開GPU受付falseで、目標は未達。
