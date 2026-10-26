# HPダメージによるADD死亡の共通CPU契約

`reference --suite coordinate-typed-owner-hp-death-common` は、元Prim全71定義・完全5人・武器/成長・8秒を保持し、別宣言counter2効果だけを足した3契約です。同一攻撃内の子field発動後死亡、遅い子field発動前の死亡、fieldがframe境界で有効になった後の死亡を分けます。HP1または1000000のADDを既存攻撃で倒し、graphノードは死亡時もactive、世代1を保ちます。hit-count消費やgraph終了による退場ではありません。

既存BossScript.hit_addの前後へ受動observerを追加し、HP/dealt/aliveとgraph状態を読むだけです。ダメージ・clock・RNG・正本は変更しません。既存の所有者visibility observerを再利用し、観測なし/ありの完全native・trace一致を確認。graph_activeを偽造して退場と混同する負例は契約で拒否します。

全3契約は固定package50336fab…で27.509402秒、GPU/packing0で成功。同一攻撃ケースの死亡とcounter完了はともに0秒、遅い発動は死亡0秒→完了1.333333秒、field先行は完了0秒→死亡1.333333秒。浮動小数時刻が等しいケースはframe単位の可視期間を主張せず、所有者query時のaliveと攻撃前後のHP証拠を分けます。最終fieldのowner=[5,1,1]、現在ADD死亡、received値0。

最終package742c8a98…との差分はreadiness分類と負例unitの2fileだけで、全native producer/comparator/CLI/GPUを保持。最終22検査（新3＋分類19）/制御517成功（Win1skip）。生成cache必須hit/Slang0は50336fab…で確認、最終でもGPUとconsumer bytesは同じです。最終版で全3nativeを再生成したとは主張しません。

compiler-only packetで別suiteの全関連テストを強制した初回harnessは、宣言されていない旧golden2ファイルの不足で失敗しました。失敗は保存し、別suiteの全関連検査成功とは扱いません。正しい範囲の新unitと制御検査へ戻し、旧Metal103の関連120検査は以前の独立した証跡として保持しています。

永続proofは `.portable-recovery/proofs/owner-hp-death-20261027/`、小さな証跡とSHAは `research/typed-owner-hp-death-reference-evidence/` と対応checkpoint。新3件のMetal/CUDA・公開consumer・ゲーム仕様は未実証です。次は旧103を保持した106入力へdata-onlyで追加し、同じ固定Slang entryと既存比較器で検証します。CPU死亡witnessはGPU履歴の直接証明へ読み替えません。
