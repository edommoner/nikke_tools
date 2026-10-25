# バースト操作の共通候補producer

共通CLI `burst-control-policy` は、pinned `BurstController` の候補選択・押下待機・未観測時の次FB予測を、同一の Slang policy で照合する単体入口です。347正本ケースと34拒否ケースは Apple M5 Metal の実GPUで全一致し、保存結果を別プロセス・GPU禁止で監査してsealしました。全戦闘への接続は次工程です。従来のworld入口で `control.burst` の受付はまだ開きません。

`gpu/burst_control_policy.slang` は Runtime・入出力bufferに依存しません。実際の候補選択と次FB予測が `burstControlCandidates` を共有し、実押下だけが安定pattern順位を適用します。明示順序が存在する周期はその順序を優先し、欠けた段階は永久block、明示周期を使い終えた後は自動候補へ戻ります。自動B1/B2は再突入・明示段階・patternの存在がなければ先頭を予約します。空listは常に後順位、nullは順位1でもキーの存在が先頭予約を解除します。

`burstControlChoose` は次の正本演算順を保ちます。

- down/stun候補は待機判定より先に除外する。
- cooldown判定は `t < ready - 1e-9`。短い本人待機は `ready - t <= wait + 1e-9` で、候補1人のwait maskを返す。
- delayの押下時刻は `max(stage_open, ready) + delay`。後順位へ進まず、cooldown wait maskは0を返す。
- 全候補が使えない場合も、全候補のreadyから最小を求め、元のactionとのmaxと全候補maskを返す。候補なしは正の無限大。

次FB予測はfull-burst終了後、完了周期数を増やした状態から、tick冒頭の候補段階snapshotで使う契約です。実押下と同じdelay・明示順序・自動予約を使い、pattern順位・down/stun・本人waitによる候補除外は行いません。候補の `max(at, ready) + delay` の最小を段階ごとに求め、0.1秒・0.37秒を順に加算します。数値演算は既存の共通software binary64だけを使います。

## 静的descriptorと単体probe

`app/portable_burst_control_specs.py` は解決済みrunner configのliteralだけを176wordへpackします。名前付きpatternカタログの解決はrunnerの責務です。delayは有限0〜180秒、本人waitはfalseまたは0.5〜3秒。明示順序は16周期、明示patternは周期1〜512、every:Nは正のuint32という容量を明示し、超過は拒否します。受付容量を全キャラ認定と取り違えません。

| 領域 | word | 内容 |
| --- | --- | --- |
| descriptor header | 0〜7 | magic/version/enabled/明示周期数/5人/24word行/16mask word/予約0 |
| owner行×5 | 8〜127 | delay2、wait2、pattern種別、周期、512bit mask、存在flag、予約0 |
| 明示順序 | 128〜175 | 16周期×3段階、5候補を各3bit、0終端 |

probeだけがdescriptorの後に48wordの人工的な時刻・ready・段階・状態snapshotを入力します。これは正本の実メソッドの数値契約を調べるための単体境界であり、戦闘へCPUイベント・予測を渡す経路ではありません。実戦ではGPU常駐Runtimeと共有出力bankからこの状態を構成する必要があります。出力32wordの候補順・選択・wait mask・action・予測・予約領域すべてを正本と比較します。

ケースには120通りの候補順、A段階、再突入、明示段階、pattern fallback、delayとready/段階開始の前後、IEEE隣接値での3種類のepsilon境界、周期512前後、全員down/stun相当、無限action、192通りの固定seed混在条件を含みます。正本メソッドをそのまま呼び、effectful castと再突入callbackだけを観測用に置換しています。Runtime.tick全体、被弾・buff通知・cooldown減少との合成はこの証明の対象外です。

## 検証と残り

固定package `06f2b466…` のCPU事前347入力、専用3検査、共通制御smokeを実行しました。GPU 0.000918秒、初回pipeline 0.129766秒、共通transport全体0.953863秒です。単独probeにresident generation cacheを指定した初回起動はcapture/claim作成前に拒否され、指定修正後のGPU実行は1回、retry0です。巨大worldのcompile時間が短縮された証拠にはしません。生成CUDAとMetalは同じsourceから作成していますが、CUDA実機・CUDA cache性能は今回検証していません。Windows追加操作は0です。

次に同じhelperを `burstFrame` と `coordinateAimBurstEnd` へ接続します。段階開始時刻・完了周期数・tick冒頭の候補段階をGPU側で保持し、full-end通知前後、待機中のcooldown減少、再突入、reload into_fbとの合成を実戦正本観測で検証します。旧251入力の全指紋・rawを保持し、新規実証後にだけworldの受付を開きます。全キャラ認定0、通常UI CPU、20 reference-model-gap分類の解消とfull battle CUDAは引き続き未完了です。

根拠は `research/portable-burst-control-policy-checkpoint.json`、`research/burst-control-policy-v1-evidence/`、`research/portable-burst-control-policy-short-expected.json`。開発package `/tmp/nikke-burst-policy-develop-v1`、保存capture `/tmp/nikke-burst-policy-metal-v1`、独立seal `/tmp/nikke-burst-policy-sealed-v1.json` を保持します。
