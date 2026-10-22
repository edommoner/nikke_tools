# 次の未対応機能：hits_parts

現在の静的inventoryで、armor_break_burst_damage／burst_damage／damageの`hits_parts`が未対応。対象はベスティ：タクティカルアップ、レイヴン、シンデレラ：クリスタルウェーブの各profileに現れる。解除数の予測やGPU対応認定はしない。共通CLIのCPU参照契約は25件（通常契約24＋legacy deferred burstのモデル制限1）まで確認済み。GPU受付は閉じたまま。

## 確認した正本

- `app/detail_gpu.py:compile_effects`はboolだけを許可し、trueをflag65536へ写す。静的has_partsならさらにpart factorの1024を付ける。canonical compilerを修正する必要はない。
- pinned `calculator/timeline.py:_handle_damage_eff`は、main hitのpart判定を静的has_partsかつdynamic reach／geometryなしに限定する。dynamic partsがあればmainのpart判定を外し、子packet側でpart factorを計算する。actorが消えた後も静的has_partsが残る境界は別途検査する。
- `_reach_hit`は非座標モードのpartとinterruptの到達を分離する。parts_skillでpart reachを広げるが、interrupt reachはその指定を除いて計算する。pierce／explosionが併存するとinterruptへ別の理由で届く可能性がある。
- `_coord_skill_hits`は座標モードでlive geometryのpartsを対象に追加hitを生成する。part-inclusive指定でinterruptを選ばず、mainのcritical判定を保持する。追加hitはtrigger／gaugeを個別には出さない。
- `_land_boss`はpart hitをchar totalへ加え、part／interruptの双方でlifestealを処理する。interruptはtotal damageの外。通常hitの選択集合へpartsを単に足すだけでは、この順序とaccountingを保持できない。

## 現在のGPU境界

`gpu/world_skill_runtime.slang:validWorldSkillDefinition`はH_PART／65536を明示拒否する。`landWorldSkillReceipt`は現在、通常のtyped enemy集合を使う。hostの許可フィールドだけを広げたり、65536を消したりして受付してはならない。既存のActor generation／landed lifecycle／receipt／binary64計算／lifestealを共通化したまま、子part receiptの対象・生成時basis・着弾時生存判定を設計する。

## 残るCPU契約とGPU接続条件

1. markerなし／false／true、partなし、静的partだけ、dynamic partを対照にする。part factorをmainと子の両方へ二重適用しない。
2. 近／遠part、最初からdead、破壊／期限終了／再出現のgenerationを検査する。
3. interruptだけ、part＋interrupt、pierce／explosion併存を検査し、parts_skillだけでinterruptへ届かないことを確認する。
4. 複数hit、deferred burst／periodic、child-triggerで対象が消える順序を観測する。部分damageをCPUで合成したGPU入力にはしない。
5. part total、interrupt accounting、lifesteal、named-hit通知とgaugeを実nativeのpacketから読む。observerは既存profile hookへ連鎖し、追加queryやsimulationの二重実行で元挙動を変えない。

CPU fixture／観測透明性／故障注入を共通CLI referenceへ接続し、それから共有Slangへ移植する。GPU sourceを変える段階では旧849と新しい実編成4件の保持を検査する。既存の物理履歴は2048上限で、レム30秒の55件省略は現時点で残る。新たな計算差分を省略や許容差拡大で隠さない。

## レビューを反映したCPU契約

`reference --suite parts-skill`の15件と`reference --suite parts-skill-extended`の10件を再利用する。通知順序はfixtureのliteral、基本interrupt2件はcreditゼロ・packet reach/time・gaugeゼロを検査する。非飽和吸血10%では部位込みHP5800、interrupt込み6000、5人共有各5160を検査し、旧HP上限10000ケースを残したまま欠落・重複を判別する。

共通CLIは最適化Pythonをnative実行前に拒否し、失敗報告を保存・再使用を拒否する。parts検証器自体も明示例外で判定する。reportの`positive_contract_cases`と`reference_model_gap_cases`は別集計であり、どちらもGPU対応率ではない。

既存22件の全native既存field／traceは保持した（基本interrupt2件の追加観測accountingのみ除外して比較）。oracle追加によりinput指紋は意図的に変わっている。今回GPU sourceは既存849と全閉包SHA一致、GPU／Windows実行0。上記のsnapshot・再出現・子イベント境界は未完了で、receipt at+7も周期snapshotが使用済み。詳細は`research/portable-parts-skill-reference-checkpoint.json`と`docs/claude-overall-review-8b77b1f.md`。
