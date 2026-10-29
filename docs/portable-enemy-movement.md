# 敵移動の宣言モデルと共通GPU接続

移動停止・強制移動にはcanonical consumerが無い。元のduration carrierを既存ADDコライダーの位置へ接続するCPU契約・共通Slang核・元5戦闘のMetal接続を検証した。明示した移動モデルでの戦闘等価性と、ゲーム規則の認定は区別する。

## CPUの実戦闘契約

```text
python scripts/nikke_gpu.py reference --suite enemy-movement-common --out NEW.json
```

ユニ元編成69定義、ヤン元編成71定義、同時使用する混合編成69定義の全effect/owner/武器/育成/config/seedを保持する。停止、強制移動、再出現、重複時の2つの明示優先順位の計5ケース。移動元は原文の`BDG 2`（5秒）/`일확천금 2`（2秒）の本物のcarrierであり、発動時刻や射撃を入力へ焼き込まない。既存WorldSchedule・ActorRegistry・generation-aware enemy fields・LogicalGeometry・sampled shot/landing/ダメージを使う。HP/弾/効果タイマーや別の射撃実行器は作らない。

入力で全ADDの速度、強制移動先の画面座標、重複優先順位、recipient近似を必須にする。位置は同じ生存世代だけに積分し、新世代は宣言初期位置へ戻す。native frame間にあるactivated_at/expires_atで区切り、左閉右開で既存`_live`/enemy field visibilityを照会する。新時計は進めず、同一frameの二重呼出しも進めない。実際のshapeを次のshot snapshotへ渡し、元の命中/着弾処理へ届ける。停止consumerだけを外す故障注入で、同一の元定義のまま実packetとADDダメージが変わることを確認した。

位置更新の位相は元`boss.begin_frame`後、`bm.tick`/スキル通知/射撃前。frame途中に新しく付いたcarrierは次のframe開始時の移動更新から反映する。強制移動もこの移動tickでsnapする宣言で、スキル発動と同時に全着弾より先へ割り込むゲーム規則を仮定しない。GPU接続でもこの位相を合わせる必要がある。

`force_policy=snap-to-declared-center`は宣言モデルで、ゲームの引き寄せ速度/軌跡ではない。`recipient_policy=canonical-all-in-range`は正本の「全員が範囲内」近似を明示したもの。空間的な範囲選択を実装済みとしない。BODY/PART/typed projectileの位置、奥行き移動、実機の優先順位も未接続。混合編成では両carrierの実重複を観測するが、現在の配置では先にヤンが中心へ移すため両優先順位の位置履歴は一致する。異なる初期位置での同時入力分岐は別の数値検査で区別し、ゲーム実証へ読み替えない。

## 共通CUDA/Metal演算

```text
python scripts/nikke_gpu.py package --suite enemy-movement-math --out NEW.zip
```

`gpu/enemy_movement_math.slang`の`enemyMovementStep`は既存のsoftware binary64を使い、各軸を`position + velocity * dt`の順で計算する。native double/FMAは使わない。停止/強制移動の明示優先順位、signed zero、相殺、subnormal、overflowを全wordで照合する。43入力はnative契約34（うちoverflow16の2件）とraw拒否9。小さな数値wireであり、actor/field/frameのGPU接続を証明するものではない。

M5でGPU実行1回、全readback2752byteを取得。GPU約0.0000236秒、MSL library約0.0464秒、PSO約0.0308秒。最初の起動指定はstandaloneへresident generation-cacheを渡してclaim前に拒否され、ログを保持。初回GPUはoverflowを正しくstatus16で返したが、従来監査器の「native正例は0のみ」で比較が失敗した。

`portable_native_status`で、このsourceの`movement-step-overflow-v1`だけにCPU oracleの整数status0/16を要求する。旧battleの既定status0は変更せず、他source/未知status/bool値は拒否する。GPU値を期待値へ採用したりstatusを64へ変更して通していない。新immutable controllerで元raw/生成物/native期待を全保持してreplayし、さらにfresh GPU禁止childの独立seal（約0.508秒）が成功した。元capture/claim/失敗は保持し、GPU再実行0。証跡`tests/fixtures/enemy-movement-math-metal-v1.json`とsealed golden`research/portable-enemy-movement-math-v1-expected.json`。

standaloneのため`--generation-cache`は使わない。通常のMetal pipeline cacheは利用できる。初回のMetal実証時にはCUDAを実行していなかった。その後の43入力のCUDA数値検証は下記の別証拠へ記録する。既存439 GPUファイル、保護CPU4ファイル、strict normalizerは全byte不変で、旧source証明書を書き換えない。

## 接続方針

別の移動実行器を作らず、既存Runtimeのalive/end・actorFieldMember・source clockから同じ位置更新を呼ぶ。LogicalGeometryの固定x/y読取りを世代付き動的位置へ接続し、元5戦闘の全履歴/状態/物理着弾をMetalで比較する。専用wireと出力bankの所有権・容量・raw拒否も同時に検査する。数値probeのgoldenを戦闘の認定へ流用しない。canonical不足5件、全キャラ認定0、UI CPU、公開GPU受付falseは継続する。


## 元戦闘を使う共通GPU接続の開発経路

`enemy-movement` は元5戦闘をそのまま使うsealed suite。`package --suite enemy-movement --out NEW.zip`から通常のunpack/runを使う。静的入力は既存logical geometry prefixと、元定義との対応tag・ADDの速度・移動先・明示優先順位だけを持つ。CPUで計算した位置・発動時刻・世代・命中対象は入力しない。元effect辞書は変更せず、私有packing copyで元duration carrierへloweringし、tag付きconsumerが既存alive/end・actorFieldMember・world frameを読む。LogicalGeometryの命中判定は同じ世代の動的位置を読む。

専用入力117476word、既存出力2032000word。未使用tailへ128slotの最終状態、全4096frame行・全4096区間行を分離して置き、容量超過は拒否する。検査は位置だけでなく、既存の全battle/skill/射撃/group/packet履歴へ続ける。比較済みの移動領域だけを旧比較用viewでzeroにし、未比較領域を消して通さない。raw拒否10条件も含む計15入力。旧compiler/default admissionは閉じたまま。

初回CPU基準固定・run前の全native再計算・fresh独立sealを別々に行う。run内だけ既存ParentOraclesを使い、GPU終了後の二度目の同一native生成を減らす。独立sealは再利用しない。共有GPU hookとhost stride guardは小さなhunkの正確な逆投影で旧sourceを保持するが、旧goldenやstrict normalizerを書き換えず、current-source再認定とは区別する。

## 2026-10-29 Metal実戦・独立監査

固定package `2074f8e1…`の全15入力はApple M5 Metalで計算一致。GPU実行1回、再実行0。5つの30秒実編成は元全69/71定義と全履歴を保持する。各3,602frame、3,598〜3,608区間と最終世代/位置/全paddingを全word比較した後、既存の全battle/skill/group/packet/命中/着弾/ダメージ比較を通した。入力7,048,564byte、出力121,920,000byteを保持。計算済み位置・発動時刻の入力0、保護CPU4ファイルとstrict normalizer変更0。

CPU基準生成約292秒、run前native再計算301.701秒、GPU2.926秒、MSL library1.976秒、初回PSO61.397秒。PSO archiveは保存済み。run内のParentOraclesは5native/5観測contextを再利用し、比較時のfresh native0。別のGPU禁止child8群による独立sealは348.617秒、各群180秒以内・15入力を一度ずつ照合し、live-parent再利用0/GPU0で成功した。独立監査を省くためのcacheではない。

最初のsandbox起動はMetal device不可視でGPU claim前に停止し、`metal-v1`に保存。通常の承認経路の`metal-v2`だけが実GPUを実行した。同claimの削除/再実行は無い。失敗とsource snapshot、raw、生成物、全比較、group監査を `.portable-recovery/proofs/enemy-movement-battle-20261029` に保持する。共有する小さな証跡は `tests/fixtures/enemy-movement-battle-metal-v1.json`、通常goldenは `research/portable-enemy-movement-battle-v1-expected.json`。

既存logical actor/敵弾薬自爆の2入口は、正確な逆投影前後のCUDA/MSL生成物がraw/strict normalizedとも全byte一致（生成のみ、追加GPU0）。旧証明書を書き換えてcurrent-source GPU成功としない。旧combined wireの検査は、この場合にsource-baselineがstaleとして拒否することも検査する。関連120 CPUテストが成功。生成保持と今回の新機能の計算証明は別である。

現CUDA実機、ゲーム内の引き寄せ軌跡/速度/優先順位、真の空間recipient、BODY/PART/typed projectile、他機能との合成は未検証。Windowsへの追加依頼は0。canonical不足5件・全キャラ認定0・UI CPU・公開GPU受付falseは継続。次はこのconsumerを既存typed対象/worldと合成し、意味のある短い共通CUDA検証単位を選ぶ。


## 2026-10-29 移動演算43入力の短いCUDA実証

固定commit `f20b276b`、packet `149d1634…76707`の`enemy-movement-math`だけをWindowsで実行した。全30秒戦闘は実行しない。Mac/Windowsのpacket IDと、packet自身のCUBIN/O1・2GiB・60秒compile-planが一致。compile1回、run1回、native34（overflow status16の2件を含む）/raw拒否9、全688wordが元sealed Metal出力と一致した。通常CPU11検査も成功。

Windows GPU dispatch0.003763秒。compile内側12.388秒/外側24.811秒、run内側12.187秒/外側50.135秒。runはCUBIN必須cache hitでNVRTC0（compile段階はNVRTC1）。開始gate/Job残存0、timeout0、既存process欠落0。compile/run内側は終了0だが、外側runnerはいずれも終了2。既知service未識別によりpreservation/overallはFalseであり、計算/containment成功へ畳み込まない。Windowsの計算成功から全battleや環境保全を認定しない。

Windows reportの固定commit `557e18400e47c7eec653f5d5d9293e043acf4782`（branch `codex/cuda-enemy-movement-math-v1-report`）から、scalar要約2,603byteと43×16数値JSON5,756byteだけを取り込んだ。ファイルSHAを照合し、Macの固定packet自身のnative status契約・全row比較器・readback stream検査をGPU禁止で再利用して全43入力をfresh比較、元Metal raw全2,752byteとの完全一致も確認（約0.169秒、GPU0）。原CUDAのcache/Job/claim/envelopeをMacで再監査した証明ではなく、source-host common CLI auditの報告とMacの独立した数値比較を区別する。

小証跡`tests/fixtures/enemy-movement-math-cuda-v1.json`は全wordとentry指紋・source-host要約・出所を保持し、`test_enemy_movement_cuda_words.py`で通常のCPU検査から再照合できる。数学部品の`cuda_verified`だけを更新し、宣言実戦5ケースのCUDAはFalseのまま。旧Metal証跡/golden/保護CPU/strict normalizer/GPU sourceは変更しない。ローカルproof `.portable-recovery/proofs/movement-cuda-math-20261029` に固定packet、compile-plan、原JSON、取り込んだbyte、監査script/resultを保持。Windowsの追加実行依頼は終了し、同claimの再実行や追加benchmarkは無い。

最終登録は関連115 CPU検査と、固定normal packet自身のunit-check13検査が成功。後者はunitだけで全native/GPU/独立sealを再実行していない。GPU source・保護CPU・normalizer・既存goldenは全byte不変で、今回の実GPUはWindowsの数値probe1回だけ。
