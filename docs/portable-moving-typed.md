# 移動とtyped対象の共有実行経路

元ユニ69/ヤン71定義、混合69定義の30秒戦闘を保持し、既存ADD移動とtyped projectile/HP shieldの物理選択を合成する。停止・強制移動・重複優先順位2条件・再出現・所有者死亡の6条件。新しいdamage効果や射撃予定は追加しない。BODY所有の固定typed対象も同じworldに残す。

## 共通モデルとCPU境界

`reference --suite moving-typed-common --out NEW.json`。`visible-with-moving-owner-v1`を明示し、元bindingのADD所有者と同じ世代が生存中だけshapeを並進する。位置は `literal + (owner_position - owner_initial)` の順。新世代を古い所有者に読み替えず、typed HP/寿命/owner自体は変更しない。BODY所有のshapeは固定。ゲーム内の付属物/移動規則を認定するモデルではない。

`EnemyMovement.advance`は進め終えた既存clockを読む。typed aimのframe snapshotより先に同じ位置更新を呼び、従来の外側frame入口の重複更新を避ける。typed aimの中心はframeで固定し、同じframeの先行着弾で所有者が死亡した場合、次の物理shotの可視性だけが変わる。frame開始時のaliveとshot時のaliveを混同しない。

論理・typed双方のshapeを同じ順位へmergeし、canonical `_coord_pellet`を1回だけ実行する。既存のscalar、RNG、typed landing、論理直接landing、group観測器を再利用する。2つのpellet wrapperやclock/HPモデルを重ねない。元の定義にgroup consumerが無い条件ではgroup履歴は空だが、全group観測フィールドを保持する。

## wireとGPU実装

入力123188wordはcoordinate109968、typed5712、logical collider5712、motion1796の分離bank。CPUで計算した位置・世代・発動時刻・命中対象は含めない。motionは既存carrierのalive/end/actor field、typedは元のDT/owner bindingを読む。

出力2165136wordを専用幅としてPython/Swiftへ登録する。元typed出力2032000wordを維持し、weapon-onlyで空いているreceipt領域を既存の2048行skill historyと論理shot scratchへ割り当てる。その後ろへ4096行frame/区間・128slot最終状態、512wordのframe固定aim中心を分離配置する。元容量を削らず、超過は拒否する。typed packet履歴の先頭2048件と全stream hashという既存比較範囲は維持し、全件個別保持に読み替えない。

`moving-typed`はsealed suite。通常の`package --suite moving-typed --out NEW.zip`から使う。固定18入力（native6/raw拒否12）はM5 Metal/独立seal済み、現CUDA実機は未確認。旧sourceは13ファイルのexact hunk inverseで戻し、strict normalizerや旧goldenを書き換えない。保護CPU4ファイルは変更しない。

## CPU確認と回収点

`.portable-recovery/proofs/moving-typed-20261029`にCPU source snapshotと原native/reportを保持する。最初の事前条件は元rosterに無いgroup発動を必須にして拒否されたため、producerのplan gateを確認し、空の全観測行を保持する正しい契約へ修正した。次は死亡がframe内に起こる時のalive観測の違いを検出し、frame位置とquery時の元ActorRegistryのaliveを分離して記録した。計算や元の効果は削っていない。v3のGPU禁止referenceで全6条件/全native/packing0/GPU0、145.693秒で成功。停止・強制移動・重複・再出現の旧5 CPU指紋も保持する。

GPU生成snapshotはcompiler-onlyであり、実行/計算証明とは区別する。現CUDA短検証と、真の空間recipient/ゲーム規則/default/全キャラは引き続き残る。


## 2026-10-29 M5 Metalとfresh独立seal

固定packet `f757ad6a…`の18入力はGPU実行1回で全一致。GPU3.094098秒、MSL library2.108秒、cold PSO63.432秒。入力8,869,540byte/出力155,889,792byteをそのまま保持。run前native162.230秒、比較では同じ親の6native/6contextだけを再利用した。別のGPU禁止child9群によるfresh sealは234.284秒、全18を1回ずつ照合し、native再利用0/GPU0、各群180秒以内だった。

全6戦闘で各3,602行の移動frameと全区間・最終世代/位置/全paddingを全word比較する。typed aimは全frameのmembership/generation streamをhash比較し、追加512wordで最後の固定中心とpaddingを比較する。過去の全中心を新bankへ全行serializeした証拠ではない。typed packetの全件は既存のprefix2048＋全順序SHA規約で比較する。6条件ではtyped着弾20〜94件、論理packet930〜1,583件が存在し、元戦闘/射撃/RNG/skill/group/typed target状態と両配送を既存比較器へ通した。CPUのshape query診断そのものをGPU全件traceにしたとは主張しない。

小証跡 `tests/fixtures/moving-typed-metal-v1.json`、golden `research/portable-moving-typed-v1-expected.json`。旧移動単独・typed論理所有者の2entryは、exact inverse前後のCUDA/MSL生成byteが一致（生成のみ、旧entryのcurrent-source GPU再認定ではない）。旧5CPU移動native指紋も保持。raw/失敗/capture/claim/CPU snapshot/生成snapshot/独立監査はローカルproof rootへ保存し、同claim retry0。Windowsの追加依頼/GPUは0。

新しいwidthは必要な所有bankの分だけ増やし、キャラ/定義/既存容量/30秒を減らしていない。今回の検証は2ADDの6条件であり、127ADDの30秒履歴を4,096行に収めた認定ではない。より多いactor、実group consumerとの合成、PART/BODY移動、他typed種別や他キャラ、ゲームの物理規則、公開admissionは未完了。Windowsへ進める際はこのMacでもnativeだけで162秒かかるため、180秒コマンドへfull runを無条件に依頼せず、既存staged preflight/保存native groupの小単位を先に選ぶ。

## 配布CLIとCUDAキャッシュ必須経路

関連118テスト成功。source監査初版は旧typed weapon依存のraw SHAを直接読んで拒否した。新しいexact inverse後の全byteを既存SHAで検査するよう修正し、projection外はraw byteの検査を維持した。改変改行の負例も拒否し、`model-check` v3は成功。失敗記録を保持し、GPU計算を変更していないため再実行していない。

通常配布packet `58ee24b3…` 自身のunit-checkは26テスト成功。`moving-typed-cache-only`は同じ入力/CPU/GPU/golden/比較器に既存CUBIN/O1必須・paired generation必須・NVRTCロード禁止を適用する。固定packet `011db4de…` 自身で54テスト成功、CUBIN/O1・2GiB・60秒のcompile-planも成功。両packetの差はCLI登録1ファイルだけで、計算payloadは全byte同一。cache miss時のcold fallbackを許可せず、Windowsの実cache hit/計算成功とは区別する。今回Windows依頼・追加GPU・compiler実行0。小証跡は `research/portable-moving-typed-cli-v1.json`。
