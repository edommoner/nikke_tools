# 次の未対応機能：hits_parts

数値基盤の最初の接続は`portable-damage-factors.md`に記録しました。既存damageValueを因子取得と順次積へ分離し、Metal849＋実4の全raw保持・独立seal、積の専用16ケースを確認済みです。二値入口damageValueWithPartの実戦呼出し、Frame／receipt保存と部位landingは未接続です。以下の設計全体を実装済みと扱わないでください。

現在の静的inventoryで、armor_break_burst_damage／burst_damage／damageの`hits_parts`が未対応。対象はベスティ：タクティカルアップ、レイヴン、シンデレラ：クリスタルウェーブの各profileに現れる。解除数の予測やGPU対応認定はしない。共通CLIのCPU参照契約は32件（通常契約31＋legacy deferred burstのモデル制限1）まで確認済み。GPU受付は閉じたまま。

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

## 生成値と着弾順序の追加7契約

`reference --suite parts-skill-lifecycle`を既存のCPU参照入口へ追加した。名前付き子通知によるpart倍率の増加／削除、部位期限終了、同名部位の再出現、吸血子通知中の倍率変更、部位群の破壊が各子回復に先行する順序、同時生成2発の先行破壊を検査する。観測器は実nativeのopen／close／destroy／part_hits返却へprofileを連鎖し、追加queryやsimulationを行わない。既存state／trace透明性、親hook復元、誤再計算・世代混同・順序変更の故障注入を含む影響25検査が成功。

同時2発では両方の生成metadataにpart_damage=3000が残るが、1発目で部位が壊れると2発目のpart_hits返却は空となる。対象名だけで生成時に子packetを固定すると誤る。一方、1発のpart_hitsが返す全対象は既にdamage適用済みで、その後に子packetの吸血・通知が走る。再出現は同名でもopen ordinal1と2を区別する。この検査はinter-frame投射体のtarget binding証明には拡張しない。

旧25の全input／native／trace／contract指紋を保持。GPU source閉包は既存849と同一、GPU／Windows追加0。記録は`research/portable-parts-lifecycle-reference-checkpoint.json`。

## 共通実行器へ接続する実装境界

1. `damage_runtime.slang:damageValue`のstats取得と7因子計算を分離し、同じ取得済みstatsからmainとpartの値を作る。part値をmainとの比から逆算せず、coreを外したpart判定で元の演算順を使う。`WORLD_FRACTION_SAMPLE`等の副作用を二重に呼ばない。物理攻撃とスキルの既存条件は維持する。
2. `dispatch_phases.slang:advanceSkillDamageFrame`のlanding branch／cursor0で両値を取得し、複数hitが同じ値を使うようFrameへ保持する。現在coefficient用のhealthValueはcursor0後に用途がなくなるが、他mode・pending経路との寿命を実装時に検査する。
3. `landing_runtime.slang:enqueueLanding`とworld codecに、生成済みpart値をGPU所有receiptへ保存する経路を接続する。at+7は周期packet snapshot使用済みなので使わない。並列bank案を採る場合も、全diagnostic領域との非重複、2048容量、再使用／初期化、未使用時の旧raw不変を検査してから確定する。
4. `world_skill_runtime.slang:landWorldSkillReceipt`の本体着弾／吸血後にlive reach部位を選び、`counter_landing_runtime.slang:deliverCounterParts`のgroup適用→packet/callbackという既存構造を共通化する。単に通常の敵selectorへ部位を追加しない。part分をchar totalへ、interruptをtotal外へ計上する境界は維持する。
5. 既存hostの座標／interrupt制約とlegacy deferred model gapは明示し、無効果受付しない。新しいsource候補はCPU契約、CUDA／Metal両生成、Metal新parts＋849＋実編成4の保持・独立sealを経る。CUDAの成立経路を判別する保存PTX分析・実験設計を先行させ、同条件のWindows再試行を増やさない。

これは上記接続の設計であり、共有GPU本文への実装・新しいGPU機能認定は未完了。
