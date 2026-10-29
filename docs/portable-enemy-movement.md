# 敵移動の宣言モデルと共通数値核

移動停止・強制移動にはcanonical consumerが無い。今回追加したのは、元のduration carrierを既存ADDコライダーの位置へ接続するCPU契約と、その演算部分の共通Slang核。元戦闘全体のGPU移植やゲーム規則の認定とは区別する。

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

standaloneのため`--generation-cache`は使わない。通常のMetal pipeline cacheは利用できる。CUDAは同じSlang/入力/比較器を使うが今回未実行。既存439 GPUファイル、保護CPU4ファイル、strict normalizerは全byte不変で、旧source証明書を書き換えない。

## 次の接続

次は別の移動実行器を作らず、既存Runtimeのalive/end・actorFieldMember・source clockから同じ位置更新を呼ぶ。LogicalGeometryの固定x/y読取りを世代付き動的位置へ接続し、元5戦闘の全履歴/状態/物理着弾をMetalで比較する。専用wireと出力bankの所有権・容量・raw拒否も同時に検査する。数値probeのgoldenを戦闘の認定へ流用しない。canonical不足5件、全キャラ認定0、UI CPU、公開GPU受付falseは継続する。
