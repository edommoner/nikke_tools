# 共通の乱数着弾点と実戦抽選の正本契約

着弾点producer `coordinate-sample-v1` をCUDA／Metal共通Slangへ実装した。既存の整数MT19937は変更せず、連続する2 wordの上位27／26 bitからCPython互換の53 bit一様乱数を作る。半径の `max(radius, 1e-9) * u ** (1/k)`、必要な場合だけ2個目の一様乱数を消費する角度、pow／sin／cosと加算順は、選択済みの決定的binary64規約を使う。

Metalのsealed `coordinate-sample` は107入力（共通CPU93／拒否14）、計1,296着弾点が一致し、GPU禁止の独立監査に成功した。全座標bitだけでなく、MT全624 word・index・消費数・拒否抽選数・後続critical用一様乱数・対象抽選・未使用出力を比較する。5 seed、1／2一様乱数と交互切替、624境界と2回のtwist、ゼロ／負／極小／大半径、指数境界、有限入力からのoverflowを含む。入力に抽選結果・着弾点・予定表は含まない。

CPU12検査、制御416検査（Windows専用1件skip）が成功。実GPU dispatch1回／同claim retry0。GPU0.018514秒、初回PSO0.278665秒、出力438,272 byte。旧10入口のsource閉包193ファイルと保護数値・正本・normalizer／CUDA cache本体は全byte保持し、既存mixed244のcurrent sealも保持した。旧GPU再実行0、Windows依頼0、現在のCUDA実行証明は未取得。

## 実戦の正本契約

共通CLIの `reference --suite coordinate-sampling-common` は、11の実CPU戦闘を動かし、63ペレット／77実packet／362 MT wordの消費順序と最終全状態を検査する。旧expected専用observerは変更せず、新private adapterだけがnativeの正規 `rng_mode='random'` と共通の着弾点／shape距離providerを使う。正本のdamage・critical・callback・target retirement・schedulerは実行し、caseの静的packingやGPUを呼ばない。

角度不要のbody／中心core、偏心core、前面PART／INTERRUPT、回転矩形、複数ペレット／muzzle、途中破壊、貫通／chargeを含む。各ペレットは着弾点抽選後にcriticalを1回抽選し、同じ貫通弾の追加packetはその判定を再利用する。観測の有無で全battleとpacketが一致し、patchとprocess全体の乱数状態も復元する。初版adapterの不正モード名はnativeが拒否したため正規値へ修正し、失敗ログを保存した。

これはユーザー選択の共通数値規約でのCPU契約であり、過去のhost libmとの完全一致やGPUの戦闘caller接続の証明ではない。

## 共通CLI

```sh
python scripts/nikke_gpu.py package --suite coordinate-sample --compact --out /tmp/new-sample.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-sample.zip --dest /tmp/new-sample
cd /tmp/new-sample
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-sample-cpu
```

`reference` はfull checkout／full packageから実行する。CPU-onlyのimmutable final packageでも12検査と全107入力のfingerprintを再確認した。fullとcompactの全残存record／byteの保持を検査している。

この小さい非resident primitiveにはresident向けgeneration cacheを指定しない。初回generation-onlyで既存のreflection必須guardが作動し、compiler／GPU開始前に停止した。その失敗は保持し、guardを緩和せず既存の非resident生成経路からCUDA／MSLを1ペア生成して実行した。Metal pipeline cacheは既存経路を使う。CUDA compile cacheのhit、現Windows計算、resident生成cache hitは今回未主張。

## 次の接続

既存のGPU物理経路は、shot templateを一度作ってペレット数だけ複製するexpected専用経路。着弾点helperの実証を、その経路全体の乱数対応として扱わない。次は以下を同じ共通executorに接続する。

- boss対象選択とは別のphysical／critical MT状態と、ペレット単位のdraw順序。
- core／front／reach判定、criticalの追加packetへの再利用、通知順序。
- 個別packetのsnapshot、1024 logical pelletと127対象の既存容量、parent参照量の整数合計。
- 既存group begin／receipt／sealと遅延deliveryへの接続。

全元定義の認定、召喚攻撃／debuff payload、公開GPU受付も未完了。全キャラ0／20 model gap／UI CPU／full goal falseを維持する。証拠は `research/portable-coordinate-sample-checkpoint.json` と `research/coordinate-sample-v1-evidence/inventory.json`。
