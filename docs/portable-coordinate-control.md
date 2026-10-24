# 座標照準と武器・リロード・操作制御の合成

`coordinate-control` は共通Slangのprivate complete executorで、既存の照準190入力に武器・操作16入力を追加する。206入力（決定的共通CPU正例182／拒否24）がApple M5のMetal実行で一致し、保存rawをGPU禁止の独立監査で再照合してsealした。CUDA／Metalは同じ効果入力・Slang本体・native比較器を使う。今回のCUDA実行は未取得で、公開受付・全キャラ認定は進めていない。

## 実装と正本の読み取り順

`world_coordinate_control_entry.slang` が既存aim executorをincludeし、`PORTABLE_COORDINATE_CONTROL_COMPOSED` で新しい制御照会規約を選ぶ。通常のaim profileは旧生成物の全byteを保持する。

正本の武器変更は射撃中だけ `CharState.weapon` を一時的に置き換えて戻す。そのため射撃外の操作調停がリロード時間を読むときはbase武器時間を使う。modeの短い／長いリロード時間をここで使う旧helperを新profileで修正した。またbase clip_countが1でも、live reload_ratio_pctが負なら分割リロードになる。clip_countだけによる早期returnをやめ、正本どおりの照会順に合わせた。

順序はreloadDuration→live fraction／ratio照会→fractionが1以上またはmode中なら単一時間→必要な場合だけfullCapacity→半切上げの装填数→不足弾数に対する整数ceil→時間乗算。mode中もratio照会を保持する。CPU正本・共通binary64・既存normalizer・CUDA cache key規則は変更していない。

新16入力はmodeの短／長時間、途中開始／終了、base単一clipの負ratio、固定時間、31弾の丸め、容量buff、7pellet×2銃口、通知付き散弾、mode散弾とfraction通知、aim＋tap、aim＋自身のhold、別ownerの優先holdからの遷移を実際の戦闘で検査する。tap rate／新しい射手のmuzzle指定不足によるCPU準備失敗は記録を保存し、fixtureを補完した。ケース削除はしていない。

## 検証範囲と実測

正例182入力の7878frameを照準の二種64bit digest・件数・最終point bank、既存の全battle／physical packet／cache比較で検査した。拒否入力の途中frameはこの件数から除く。旧190入力の全input entry・正例166のnative指紋・readback全996147200byteが一致した。元aimの4window／5anchor・前回点を読むskillと今回点を読むphysicalは保持される。

入力109528word／出力1310720word、Runtime物理stride138952byteは従来どおり。今回のGPUは修正版v2の1回のみ、失敗0／retry0。v1はCPU／生成だけでGPU実行0。計算3.738755秒、初回pipeline90.527556秒、shared execute100.592714秒。生成cache必須hitで実行時Slang0。これはwarm cacheの速度比較ではない。calculationとcontainmentはtrue、環境保持はnullで成功と混同しない。

最終sealed compactのCPU95成功、control416成功（Windows専用1 skip）。full3072からcompact1763へ残す全recordと全byteが一致した。旧attack-group-mixed81／coordinate-composed97／core120／cache133／aim190の生成CUDAとMSL全byteを保持し、別GPU再実行0。両reflectionのbyte保持やWindows実cache hitまでは主張しない。新sourceのcompiler certificateは保存結果の独立監査によるsource証明で、NVRTC／driverの実証ではない。

rawを削除せず、全byte SHA・サイズ・inodeを維持した疎化で計2024034304byteの割当を回収した。今回成功raw1080033280byteと初期容量guard／回復記録を保持する。

## group統合の残件を共通CLIで監査

`model-check` は `portable_coordinate_group_frontier.verify` を呼ぶ。現在のgroup compaction writerはphysical scratch19840word・aim state160word・Geometry cache128576wordと重なる。座標物理profileのgroup受付拒否を維持し、この監査のpassedを統合成功と解釈しない。

容量186528wordを保った移設案はcompactionを1310720から1497248へ置き、出力strideを1507328wordとする。静的address planは成立するが、実アドレス・読み書き・transport登録は未実装。初期化がCP_BASEからP_OUTPUT_WORDSまでclearするcaller、physicalのgroup拒否guard、typed-pellet／body suppression hook、実deliverAttackGroupShot、hostのstride whitelistをsource hashとliteralで監査する。

次は実reader／writerの移設とclear上限、その後heterogeneous物理packetからgroup producerへのreceipt、ADD／actor共有と通知を接続する。領域移設だけではgroup対応にならない。RNG・混合scene・全元定義も残る。全キャラ認定0、native model gap20、UI CPU、公開GPU受付false、目標未達。

## 再利用

```sh
python scripts/nikke_gpu.py package --suite coordinate-control --compact --out /tmp/new-control.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-control.zip --dest /tmp/new-control
# 以降のcwdは展開先
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-control-cpu
python scripts/nikke_gpu.py model-check --out /tmp/new-control-model.json
```

検証済みcapture／claimを再実行しない。現在のWindows依頼APIはidleチャットを開始できず、新しいGPU検証は開始していない。再接続だけでは解消しないため、重複runを送らずMacの実装を進める。

固定package ID・source保護hash・残件は[checkpoint](../research/portable-coordinate-control-checkpoint.json)、保存ログ／比較／容量guard／失敗とSHA一覧は[証拠inventory](../research/coordinate-control-v1-evidence/inventory.json)を参照。
