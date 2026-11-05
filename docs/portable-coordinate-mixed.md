# 座標戦闘とworld処理の共通実行器

`coordinate-mixed` は、既存の座標弾・group・Actor poolに、有効な `split_damage` と buff／shield／vanish／move／groggy／直接boss attackを接続するprivate profile。CUDAとMetalは同じSlang入口、静的入力、CPU正本、比較器を使う。全キャラ認定、公開GPU受付、sampling RNGは別の未完了項目。

## 正本と範囲

旧225入力をそのまま含み、19の混在worldを追加する。合計244入力、共通CPU正本218、拒否26。入力109528／出力1507328 word、既存のgroup履歴186528 wordと全容量を維持する。基準はユーザー選択の `deterministic-common-cpu`。現行native parserが拒否する旧 `share` 設定は `native_reference_exclusion`、有効な `split_damage` は別のGPU移植対象として監査する。これはゲーム仕様として旧shareを除外する判断ではない。

19ケースには、BODYとADDの均等配分、ADD途中消滅、HP順位／seed付き対象選択、nearest-evenの奇数／偶数tieとゼロ丸め、shield／vanishの期間、順序付きbuff、距離モードの切替と失効、武器mask、直接敵攻撃と吸血、groggy、core移動、部位への別packetと配分スキルの同居を含む。入力packingでnative battleや着弾予定表を作らない。

実際のnative `_apply_lifesteal` 呼び出しを受動観測し、既にrouting・丸めを終えたpacketの対象・量・世代・時刻を取得する。既存group／照準observerと併用し、observer有無で全battleとtraceが一致することを検査する。GPUは同じworld refresh／recipient selection／damage／group executorを通す。部位への直接skill packetの論理traceはnativeのBODY slotを記録し、実座標packetには実PART slotを保持する。

## 修正と履歴の保全

初回の60秒CPU batchは旧140検査の後で停止し、GPU claim／dispatchは0。新suiteの既存CPU設定を90秒とし、GPU／Windowsの180秒上限は維持した。

修正前のv3はCPU148に成功し、Metal dispatch1回で244中242一致。失敗は、base distanceなしからmoveで距離モードを開始する入力のstatus64と、別PART packetのskill診断traceへのBODY／ADD集合流用。元の失敗・claim・rawを保持し、比較器や正本を弱めず共通GPUコードを修正した。

`PORTABLE_COORDINATE_MIXED_NODES` を定義する別入口だけで距離モード切替を受付け、既存のordered refreshを使う。別PARTの論理traceも既存loggerの引数として指定する。旧入口の生成CUDA／MSLは7ペアすべて以前と全byte一致。変更3ファイルとbackendの厳密な逆変換をliteral内容／SHAで監査し、未知変更を拒否する。生成normalizerへの除外追加、cache keyの緩和、古いproofのcurrent sourceへの付け替えは行わない。

## 実行経路

固定packageを新規フォルダーへ展開してから既存CLIを使う。

```sh
python scripts/nikke_gpu.py package --suite coordinate-mixed --compact --out /tmp/new-mixed.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-mixed.zip --dest /tmp/new-mixed
cd /tmp/new-mixed
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-mixed-cpu
```

実GPU前に必要保存量と1GiB reserveを検査する。生成cache、Metal pipeline cache、Windowsのbounded Jobは共通CLIの既存経路を使う。新sourceの初回PSOと、同sourceのwarm hitを混同しない。Windowsの現在のCUDA実行証明は未取得。直接boss attackの今回範囲から、summon attack／debuff payloadの対応を推定しない。

## 確認結果

M5 Metalで244入力すべて一致し、GPU禁止の独立監査でsealした。正例218入力の8,484 frame、旧225入力の全1,356,595,200 byteを保持。CPU149検査と制御416検査（Windows専用1件skip）が成功。GPU実計算は3.724秒、修正版PSO初回91.484秒。v3の同一旧sourceではpipeline cache必須hitが0.002612秒で成功しており、cacheが効く条件と初回source変更のコストを区別する。

この作業でのGPU dispatchは修正前v3と修正版v4の計2回。同claimのretry、旧7系統の別GPU再実行は0。CUDA／Metalのペア生成は共通Slangから行い、現Windows CUDA実行や現CUDA cache hitの証明とは区別する。Windows側の既存チャットはidleで送信APIがactive turn ID不在を返したため、今回新規検証は開始していない。

保存失敗v3と既存の完了captureを疎化し、全byte／SHA／inodeを保持して空き領域を確保した。rawを削除せず、現失敗を成功として書き換えない。選択した証拠と保存先・hashは `research/portable-coordinate-mixed-checkpoint.json` と `research/coordinate-mixed-v1-evidence/inventory.json` にまとめる。

次の優先項目はphysical sampling RNGと、そのdraw順序・角度必要条件・front／reach routingの共通化。召喚攻撃・debuff payload、全キャラ／全効果の元定義認定と公開受付も残る。全キャラ認定0／model gap20／UI CPU／public GPU closed／最終目標未達を維持する。
