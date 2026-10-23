# not_core の正本契約と接続要件

共通CLI `reference --suite not-core` へ27契約を追加した。
25合成入力と、冬ギロチンを含む全79定義の実編成3秒／30秒で、実際の条件評価160回、
成立95回、instant処理39回を観測する。実編成の `경험치 2` はゲージ処理へ3回／34回到達する。
これはCPU正本の準備段階であり、GPUの実装・受付・実行を追加した証明ではない。

## 確認した数値と状態

正本は `BuffManager._condition_ok` で `p = 1.0 - float(core_frac)` を評価し、
expectedモードでは `('not_core', effect identity, caster)` の累積値へ加算する。
1以上なら1を引いて成立する。0／1の端もキーが作られる。

- 通常／chargeの物理 `hit_count` が、その弾の `core_frac` を通知に載せる。
  `on_attack`、`battle_start`、`last_bullet` 等のこの契約のproducerには値がなく、既定値0なのでp=1。
  現在の幾何条件 `core_hit` や、最後に撃った弾の値で代用できない。
- `_bullet_core_fracs` はペレットの列を銃口ごとに分けて平均する。
  1発中のaccuracy変更後に再計算せず、発射時の列と正本のsum／除算を保持する必要がある。
- 同じ効果に `not_core` が2つあると同じキーを順に更新する。別の効果・別casterは独立。
  `prob` は別キーなので、その既存bankを共有してはならない。
- 先行条件がfalseならnot_coreへ到達せず、後続条件がfalseなら累積値の更新は残る。
  通知の重複descriptorも評価回数へ影響する。
- 発動上限が1でも3回の条件評価で累積値が進む入力がある。
  「条件成立2回・保持stack1」を固定し、budgetによる早期returnとの混同を防ぐ。
- 子の `event:heal_received` はcoreコンテキストを持たず、戻った後の兄弟条件には親の値が復元される。
  通知の開始／終了と、継続するhandler内の評価を区別する必要がある。
- passiveでは数値参照時の評価が存在する。この契約では17回・コンテキストなし。
  activation専用の経路だけを接続して全predicate対応とはしない。

## 観測・テスト

`world_not_core_native.py` は `_condition_ok`、`notify`、`_dispatch_instant` の元の処理を一度だけ呼ぶ。
追加の数値照会・対象解決・通知の注入を行わない。条件の前後で、累積キーの有無と値、
コンテキスト、順序、実carrier、実instant呼び出しを記録する。

`tests/fixtures/portable-not-core-native.json` はGPUを見る前に固定したCPU値。
最初の27契約の全フィールドを保持したままinstant観測2フィールドを追加した。
全27入力で観測器あり／なしの元battle・trace・全get_buffs照会・全random.sampleが一致する。
コンテキスト、成立結果、キー生成、累積値、carrier、traceの7種の故障を拒否する。

不変パッケージをfresh展開して `reference` とCPU検査を実施する。
パッケージのsuiteは既存 `partial-query` の17入力を固定する輸送用であり、
not-coreをGPU入力へloweringするsuiteではない。GPUの `run` をこの証拠の代わりに使わない。

## 残る実装

弾のスナップショットを通知コンテキストへ接続し、独立したeffect/caster状態と
条件・budgetの評価順を共通Slangへ実装する。新しい状態領域の所有・最大容量を監査し、
合成・実編成・旧1533入力とCUDAの短い検証まで進めてからGPU対応とする。
現時点ではportableは `not_core` を引き続き拒否する。全キャラ認定0／UI CPU／目標未達。

GPUソース123ファイルは既存Metal1533の証拠と同一。既存17入力のinput/native指紋も保持する。
今回のGPU build／execute／Windows操作は0。静的266記録・232入力SHA・34拒否・50分類コードを保持し、
not_coreの1分類だけを `reference_review` から `native_contract_extension` へ移す。
