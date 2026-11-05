# 通常対象選択を保つ射撃group

`reference --suite attack-group-native-route --out NEW.json` は、元のBossルーターを変更せず、実際に着弾したBODY／ADDだけから射撃groupを作るCPU契約20件を実行する。`battle_attack_groups(routing='native')` を明示したscopeだけで動き、通常UI・既定battleには導入しない。従来の `all-logical-enemies` は比較用の別ポリシーとして保持する。

正本 `BossScript._aim_enemy` は生存ADDの先頭を選び、同じ散弾射撃の途中でも破壊後の次の敵へ移る。新経路は `Boss.route` へ元eventをそのまま渡し、この再選択を保つ。実際の着弾receipt、射撃境界、既存group seal、世代付きqueued childの所有権は前段の実装を再利用する。ダメージ式や新しい対象判定式は追加しない。

元ニヒリスター／ベロータの全定義を保持した16件では、ADDが存在する場合も未導入の正本とbattle全体・全物理射撃履歴が一致する。通常1packet射撃は1対象だけに当たるため、敵が複数いるだけではmulti_hitは発動しない。宣言listener付きの元ノワール／ツバイ各2件では、耐久のあるADDでは非発動、HP1のADD3体では実10packetの途中でADD0→ADD1→ADD2→BODYへ移り、各1回だけ発動する。子は破壊済みADDへ再着弾せずBODYだけへ着弾し、元のunrouted overkill計上を維持する。これは宣言listenerの契約であり、両キャラが元からmulti_hitを持つという認定ではない。

不変package `bc5e11ad5eab7a18eb8f719333bb548ccb93bd87324988db8e0fdc289e43feb3` を新規展開し、20件・172group・2通知・2子着弾が6.154秒で成功した。登録CPU27検査、既存32入力（native22／拒否10）の全入力・native指紋保持も成功し、全2,832 payloadファイルのSHAはcheckoutと一致する。GPU source・保護CPU・binary64・strict normalizer・goldenは変更せず、GPU build／実行／Windows操作は0である。

最初のCPU検査は、監査器が旧ポリシー1種類のguardを厳密に要求して停止した。新しい2種類の明示guardと、全敵へのevent置換が旧ポリシー内だけにあることを監査するよう修正した。guardの無条件化・native側での全敵置換・異なる置換ルールの3改変を拒否する負例を加えた。失敗packageとcaptureを保持し、記録は `research/native-route-group-evidence` と `research/portable-native-route-group-checkpoint.json` にある。

次は同じGPU射撃group producerで、packetごとに既存 `actorPhysicalTarget` を選ぶ経路へ接続する。全敵集合への配布を通常対象選択へ読み替えない。20件のMetal実証、旧32／61の出力保持と独立sealが必要で、まだ実施していない。plain BODY／ADD以外のgeometry／parts／shield、長時間log64超、広いmixed-owner、現CUDA実機とcompile cache実測、全キャラ対応は未完了。通常UIはCPU、目標は継続中である。
