# 元ニヒリスターの実2敵通知と共通GPU実行器

`logical-actor-rosters`は元5人編成/全70定義、SR武器、育成・操作・seedを保持し、既存の明示ADD幾何モデルで元`multi_hit:2`→`버닝 샷 3`を検証するsealed5条件。固定66df6953/package b38e3b9d…、M5 Metal1回とGPU禁止fresh独立監査で全出力比較が成功した。全キャラ認定、既定CPUとの幾何同値、ゲーム距離規則の認定ではない。

| 条件 | 実際に検査すること |
|---|---|
| BODY＋実ADD、3秒 | 元の2敵通知1回、子着弾2件 |
| ADDが範囲外、3秒 | 登録数ではなく実着弾で判定し、通知/子なし |
| 範囲外ADD＋実PART、3秒 | 初弾はPARTだけなので敵集合0、次弾はBODY1。PARTを2体目に数えない |
| 回転矩形ADD、3秒 | literal37度の矩形を既存共通shape判定で処理し、元通知/子を検査 |
| BODY＋実ADD、30秒 | 実group20、元通知19、子着弾38を全履歴比較 |

CPU reference `reference --suite logical-actor-rosters-common --out NEW.json`は上記5件をGPU/packing禁止で約2.01秒で検証する。最初のPART対照で「全groupは1敵」という観測assertが失敗し、保存nativeを確認すると初弾はPART単独で論理敵0だった。敵数は最大1、実BODY1のgroupも存在し、実PART着弾はあるが通知/子なし、という条件へ修正した。源effectや射撃時刻を変更していない。失敗とPART診断はprivateに保持。

GPUは前のベロータsuiteと**同じentry**で、CUDA/MSL/両reflection全byteが一致する。効果handler、HP、時計、sampler、damage式を追加していない。比較器も元の全battle/物理packet/RNG/group/2,048行skill履歴/解放tailの検査を共有する。native取得後の旧比較文すべてを抽出して共通関数へ移し、固定f4f4b7eeのASTと完全一致を検査する。旧13goldenと旧GPU出力は不変で、旧GPUケースの再実行は0。

実M5のGPU2.434174秒、library0.004075秒、pipeline0.002745秒。実archive必須hitとgeneration必須hit/Slang0を確認し、前の初回pipeline約58秒を繰り返さなかった。通常比較はlive ParentOraclesで5native/5context再利用・追加fresh native0。実run前71unit成功。独立監査はfresh子2群で全5入力を一度ずつ比較し、107.573248秒、GPU0、live parent再利用なし。同じ独立監査からgoldenとfull-source compiler証明を作成した。

`package --suite logical-actor-rosters --out NEW.zip`で固定し、own CLIを使う。`logical-actor-rosters-cache-only`は同じ計算/goldenへ既存CUBIN O1・compile cache必須・paired generation必須を適用する。現CUDA/CUBIN hitは未検証であり、旧Windows transaction終端不明の間は新runを送らない。未対応分類には2敵通知だけの元ニヒリスター証拠を別に追加し、既定producer未設置・reference_model_gap・公開GPU拒否・全キャラ未認定を維持する。

出所は `research/target-count-query-evidence/metal-logical-Nihilister-v1.json`、独立receiptは `tests/fixtures/logical-Nihilister-independent-v1.json`。大きなnative/readback/生成物はprivate proofに保持する。
