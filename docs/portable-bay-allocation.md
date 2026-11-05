# ベイの偏差分配：公開比率と未確定の境界

既存のpinned正本は`received_dmg_split`と`self_cover`を規格未定として拒否する。元4段階の効果定義・target・noteは変更していない。今回の調査で公開比率の根拠は追加できたが、incoming実装や受付を解放したものではない。

[GameWithの人数別比率表](https://gamewith.jp/nikke/article/show/444593)は、遮蔽物無しの5人生存でベイ40%・他15%を掲載する。4/3/2人の表示も、重み「本人8・他3」を生存メンバーだけで正規化する候補と表示精度の範囲で一致する。これは表からの推論であり、HP/DEFを変える制御実験やゲーム内部定数を確認した結果ではない。

[Prydwenの著者解説](https://www.prydwen.gg/nikke/characters/bay)も5人の比率を掲載し、Skill2は本人の遮蔽物が対象だと説明する。英語skill本文のall allies記載と解説が区別する誤訳を混ぜない。死亡順や被撃通知をcanonical均等分配と同一とする根拠にはしない。リンク動画は今回視認していない。NIKKE.GGは検索索引だけ・直接取得403、公式技能紹介投稿も取得403として記録する。

## 数値契約へ直ちに昇格しない理由

遮蔽物ありの表には、本人8・他3に対して遮蔽物262という候補が近似的に合う。ただし1人時の表示はcover97.03%・本人2.96%。候補262/(262+8)を百分率の小数2桁へ最近接丸めすると97.04%であり、表示を正確なdouble仕様とは扱えない。不一致を表の書換えや丸め規約の変更で消さない。

追加で必要なのは、正確なcover重みと演算順、元carrierとcover receiverの結合、防御参照元と保護layer順、各メンバーの被撃通知、cover破壊/復活/再burst、本人死亡、均等分配との重複、favorite各段階の実証。均等版への別名化やno-opで静的失敗を減らさない。次は既存incoming/cover/group executorへ落とす明示契約を整える。

データは `tests/fixtures/bay-published-allocation-v1.json`。候補式・表の不一致・未対応flagの維持を3テストで検査する。GPU/Slang/NVRTC/native battle追加0。再調査は正確な定数・制御実験・layer/通知の新しい根拠が得られた時とし、同じ転載の再検索を重ねない。


## 2026-10-30 共通重み付き数値処理をM5で検証

保存済み全266profileのentry-planでも、偏差分配は4段階に影響する最優先未対応だった。`app/incoming_weighted_allocation.py`と`gpu/incoming_weighted_allocation.slang`を追加した。入力は量・生存body5bit・元caster slot・本人/他人/遮蔽物の正の有限重み・独立coverの有無。body slot0..4の後にcover slot5を加算した分母で、`amount * (weight / denominator)`を計算する明示規約。整数丸め、最低1、残差を特定recipientへ押し付ける補正は入れない。分母overflowはstatus16、死んだownerのcover指定/非有限値等はwire拒否。分配先と重みはfreezeした入力で、HPやキャリアからCPUがGPU結果を先取りするものではない。

重み8/3/262は入力例でありゲーム定数の確定ではない。別の明示重み・全31生存集合・5caster・cover有無・ゼロ/極小/最大量を含むnative1179と拒否13、全1192を同じSlangからCUDA/Metalへ生成した。固定689814a1/package59e9a503…でApple M5実GPU成功（0.000569958秒）、別fresh GPU禁止childで全1179 native/1192出力を0.386646秒で独立seal。元sandboxのdevice未取得はclaim前停止として保持し、通常権限の新captureで成功。raw/失敗を保持し、成功GPU1回、Windows依頼0。

共通CLIの`weighted-incoming`は通常package経路、`weighted-incoming-cache-only`は同計算のCUBIN/O1・compile cache必須経路。standalone数値entryなのでresident paired生成flagは要求しない。キャッシュ未作成をhitとせず、実CUDAは未検証。

証拠は`research/portable-weighted-incoming-v1-expected.json`、`tests/fixtures/weighted-incoming-metal-v1.json`、`tests/fixtures/weighted-incoming-independent-v1.json`、進捗`research/target-count-query-evidence/weighted-incoming-metal-v1.json`。これは数値処理の検証であり、元4段階の戦闘・実機比率・canonical consumer・公開GPU受付は未達。元拒否を維持し、分類へこの限定証拠を添付する。

### 次の実行器接続（数値probeを戦闘対応の代用にしない）

1. 元all_allies carrierとself_cover carrierを別recipientとして、元row/caster/発動時刻/失効/削除へ結ぶ。pinnedの`split_group`は均等版専用であり、偏差版をその別名にしない。`self_cover`には現在通常のbody target resolverがないため、body名への置換や元定義変更をしない。
2. 元`_boss_attack`の量確定後・`_land_squad`呼出し前と、共通`dispatch_phases.slang` incoming event0のgroup snapshot境界を対応させる。別のイベントclock・HP配列・通知ループを作らず、既存のmode22/23/20と保護層へ接続する。
3. cover slot5は「本人bodyの追加量」ではなく独立遮蔽物。cover破壊後の再正規化は次の被弾snapshotからとするか、同一被弾の残余を渡すかは明示model契約を定める。既存cover layerの余剰を渡さない規則と混同せず、実機規則へ昇格しない。
4. 通知は元の命中者と分配先を区別し、被弾中の死亡/復活/cover回復/reburst・均等版併存を含む元4段階のCPU契約と実Metal全戦闘比較を先に行う。その後だけ必要な短いWindows CUDA検証を依頼する。


## 2026-10-30 元carrierと既存native被弾実行器への接続

`reference --suite weighted-incoming-common --out NEW.json`を追加した。元ベイ4段階の全69/74/75/76定義を保持した30秒4戦闘、65秒の破壊/再burst、ベイ→ビスケット→ベイの明示burst候補による実cover復活/再burst、未発動3秒の完全透明対照、計7戦闘がCPU成功（2.932594秒、GPU/packing0）。元定義・owner・順序を実登録時に静的準備と全比較する。元skillや対象名/値/条件を変更せず、独立cover carrierの既存activated_at/expires_at/stackとcasterを読む。pinned resolverの空targetをbody名へ変更しない。

`weighted_incoming_battle_model`は元`_boss_attack`の量確定後・分配直前に生存/元recipientをfreezeする。身体shareはsquad順で元`_land_squad`へ渡し、最後に独立cover shareを適用。元cover減算/break/ログのASTを一つの共通nested helperへ移し、通常body-coverと独立coverの両経路が同じ更新を使う。元HP配列/clock/キャリア実行器を複製しない。被弾通知は元の命中者だけ、実cover消費は既存cover-hit通知。body shareが保護層で防がれる規則も維持する。この順序/最終攻撃量の参照元/余剰discard/重みは宣言モデルで、ゲーム仕様の確定ではない。

破壊直後は次snapshotからcoverを除き、同じ被弾を途中で再正規化しない。body callback中にcoverが失われた場合も元owner生存/coverHPを再検査し、消えた分を他人へ押し戻さない。元carrier再発動で時刻を更新し、owner死亡/cover破壊を独立に扱う。均等版併存・複数の偏差body carrier・未知条件/弾数寿命は明示policy待ちとして拒否。未対応を黙って均等化しない。

初版の「ベイのcover_heal_pctで破壊coverも復活する」という検査期待は失敗した。pinnedの元規則は回復と復活を区別するため、正本や実装を変えず、破壊を維持する対照と元ビスケットcover_reviveを実際に発動させる実編成を分けた。元失敗reportと追加診断を保持。証拠は`research/target-count-query-evidence/weighted-incoming-battle-cpu-v1.json`、全native/入力指紋/計算source指紋を`tests/fixtures/weighted-battle-cpu-v1.json`に保存。

今回の新native接続はCPU契約。Metalで成功済みなのは前節の数値配分1192入力のみであり、戦闘GPU・元4段階のCUDA・公開GPU受付は未完了。次はGPUの既存incoming frameに同じsnapshot/キャリア寿命/独立coverを下ろし、この7戦闘を同じ比較器で実証する。元self_coverを通常body recipientへ混同したwireや、knockDownでcover carrierを誤って消す実装を避ける。既存数値GPU source/goldenを変更していないので同じGPUを再実行しない。


## 2026-10-30 共通戦闘21入力をM5で独立seal

固定9bd06aad/package ef200b58…で、元ベイ4段階・破壊/再burst・元ビスケット復活・未発動対照の7戦闘と、元75定義の破壊cover条件付き自己回復1戦闘、不正入力13件を全比較した。Metal全21成功、GPU5.703300秒、初回pipeline59.370762秒、CPU事前164.984342秒。別fresh GPU禁止child6群が全21/8nativeを各1回比較し、213.119448秒で独立sealした。通常run内の比較は直前の生きたCPU事前結果8件を再利用、保存結果の代用や独立監査への流用は0。

元body/cover定義の固定行IDを明示weight bankへ格納し、既存presence carrierとmode22/23/20のincoming/protection/HP/通知を共用した。別stat番号、HP配列、clockを増設していない。self_cover carrierのmembershipは元どおり空集合を保ち、caster生存/coverHPから独立recipientの配送可否を読む。通常body-coverと独立coverは同じ消費helperを使う。Runtimeは138992byteで増分0。正例の元not_self_cover_alive自己回復は実HP増加2回をCPU/GPUで検査した。

途中の失敗を保持：監査binding用の生きた敵が元lifestealへ干渉したため、全戦闘中spawnしない監査nodeに修正し元7戦闘の全被弾を保存CPU契約と再照合した。self_coverをbody maskへ含めた旧結果はnamed-state差分で失敗。続く15入力では13件一致・favorite2/3がadmission status64で失敗し、既存診断のstage8000でactor field入力検査にcover条件の列挙漏れを特定した。既存条件評価を再利用しreserved/引数/戦闘contextを厳密検査、条件を無視して通さず正例と不正条件2例を追加した。失敗raw/claimを残し、同claim再試行0、許容差/normalizer/保護CPU4ファイル変更0。

通常CLI `weighted-battle` と `weighted-battle-cache-only` を登録。後者は同じ計算でCUBIN/O1・compile cache・paired generation必須。`weighted-battle-diagnostic`は開発専用のまま。証拠は `tests/fixtures/weighted-battle-metal-v1.json`、`weighted-battle-independent-v1.json`、`research/portable-weighted-battle-v1-expected.json`。compiler certificateはこのMetal battleのsource-only証拠で、実CUDAの成功ではない。

重み8/3/262は宣言モデル、正確なゲーム定数は未確定。canonical拒否/public admissionを維持する。均等分配との併存・複数weighted carrierのpolicy、owner死亡/復活のGPU合成、現CUDA、全キャラは未完了。旧cover-DEFの証拠は厳密source逆変換による履歴証拠として維持し、現source再認定とは分離した。次は対応表の残項目を再評価し、この限定範囲を超える合成ケースへ進む。Windowsの保存診断は共有承認待ちで、追加compile/GPU依頼0。
