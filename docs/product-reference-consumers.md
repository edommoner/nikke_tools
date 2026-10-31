# 製品CPU参照consumerの接続

2026-10-31、ユーザーは残11profileのCPUモデル拡張を許可した。対象はアンの敵回復、ユニ／ヤンの移動、ソルジャーO.W.の遮蔽DEF、ベルベットの敵弾倉、スノーホワイトHeavy ArmsのLock On、ベイ4段階の配分、レイの対象数。pinned upstreamを変更せず、専用adapterと回帰テストで進める。未確定仕様は宣言モデルとする。この範囲について再確認を待つ必要はない。

最初の接続は `product_reference_models` の敵回復。通常評価要求に次の任意項目を渡す。

```json
{"reference_models":{"enemy_healing":[{"node":"heal-source","targets":["__enemy__:wave#1"],"amount":1000}]}}
```

sourceは既存idle node、対象は実際の有限HPを持つADDに限る。回復量は元のheal_received_pct、世代別field可視性、現在のdealtを使い、既存のHPへ適用する。hit数と累積damage creditを巻き戻さない。生存・世代・満HPでのclampは既存EnemyHealingを再利用する。receiptは1024件を超えた時点でエラーにし、履歴を切り捨てない。

通常CPU結果の `reference_models` に宣言、実回復receipt、最終ADD状態を返し、未確認の実ゲーム規則と区別する警告も返す。未指定要求は元の計算のまま。失敗時もsimulateの両aliasを復元する。元アンの全69定義を保持した通常評価で、回復倍率の低下と実HP回復を回帰テストした。既存の敵回復12テストも通過した。

**この変更は製品Metal対応の完了ではない。** 共通GPU製品wireをまだ接続していないため、宣言がある場合はGPU前に明示拒否する。static準備には宣言値だけを保持し、CPU receipt・HP・時刻をGPU入力へ渡さない。legacy GPUにも黙ってモデルを省略させない。過去の専用enemy-healing Metal実証を、今回の通常API GPU実証へ付け替えない。

次は既存enemy_healing wire／共有consumerの製品入口とreadback変換を接続する。残るモデルも同じ境界を守る。移動優先規則、独立したcover基礎DEF、敵弾倉、Lock Onの不明な距離式を暗黙値で補わない。

# バースト周期指定

元の `mast3`／解決済みpatternを既存の共通BurstControlPolicyへ接続した。優先順位を変える規約であり、非該当周期の使用を禁止するフィルタではない。GPUが完了full-burst数を数え、候補選択を行う。CPUの選択結果や予定時刻は入力しない。

既存weapon-stage wordの未使用上位bitへliteralを格納し、input/output strideを増やしていない。every:Nは1〜524287、cycle listは1〜19、nullの存在と空listも区別する。容量を超える指定、未接続のdelay/wait/sequenceは明示拒否する。

M5の通常HTTP6条件は、固定／蓄積、オート対照、B2の配置変更、代替候補なしのすべてで全CPU payloadと一致した。指定ありでは3周期目と6周期目にMastが選ばれ、指定なしの結果とも実際に変わった。代替候補なしでは非該当周期にもMastが発動した。保存raw再投影も一致し、追加GPU／nativeは0。普通のaccumulate基準1入力も実MetalとGPU禁止の独立sealを通し、旧入力・出力・native指紋を保持した新v2へ登録した。旧v1は保存した。他programの基準を未検証のまま更新していない。

添付設定はMac内だけで検証し、周期指定の接続後は実GPUまで到達した。burst履歴はCPU一致だが、1人のdamageとtotalに差があり、GPU結果を拒否してCPUへ戻している。許容差は緩めていない。詳細な個人設定、結果、hash、rawは共有しない。公開の集約証跡は `research/product-burst-pattern-v1.json`。

Windowsの前版はown70成功後にfake SDK検査で停止した。テストの環境コピーに並列化設定が抜け、cache identityが変わったことが原因。fixtureを修正し、Macでthreads=2の模擬45テストを確認した。Windowsの実SDK／driver／GPUへは到達しておらず、今回のCUDA成功とは数えない。以前のtimeoutとclaimも保持する。次の固定sourceで必要な短い検証だけを依頼する。
