# cover／reload方針の共通実行器

`coordinate-policy` は、既存 `coordinate-manual` の169入力を保持し、方針20worldとwire拒否7入力を追加する入口。共通CPU正本の判定を読み取り、静的descriptorをCUDA／Metal共通Slangへ渡す。公開GPU受付・全キャラ認定は別途必要で、通常画面はCPUのまま。

`own_full_burst` のcoverと、reloadの `before_fb_end`、`into_fb`、`finish_by_fb_end`、`finish_by_own_buff_end` を扱う。記述された `combat_start`／`fb_end`／`own_fb_end`／`next_fb_start`／`own_buff_end`、offset、reload_total差引き、stage-user gate、if_dry、duration、priorityを静的に変換する。CPUで方針の開始時刻・終了時刻・射撃時刻を作らない。次full burstの予測と装填総時間には既存照準実行器の時計・計算を再利用する。本人が発動した有限の名前付き効果の満了を見る際も、対象を先にresolveしない。

カメラ所有権の要求は、明示sequence、開いているcover／hold、その後に方針の順。物理処理では既存click時刻の判定後にsequence／方針を適用する。方針内ではburst coverをreload coverより先に判定する。カメラ所有権は既存の調停器、coverの物理処理は `enterManualCover` と同じreload／charge／被弾処理を使う。カメラpreempt時のアンカー復元は同じ種類・値につき一度だけ。武器変更中は方針を開始しない。方針の進入時にchargingの可視状態と数値cacheも更新する。

wireは入力109656word（旧109528＋128）、出力1769856word（旧1769472＋384）。Runtimeは増やさない。追加入力はheader8＋5人×24word。追加出力はheader16＋5人×64word＋padding48、各人のreentry履歴上限16。方針なしの既存入力は固定の空descriptorを追加し、新しい出力tailをゼロのまま保持する。上限超過は明示拒否し、既存のhold／sequence／pending容量を借用しない。

```sh
python scripts/nikke_gpu.py package --suite coordinate-policy --compact --out /tmp/UNIQUE.zip
python scripts/nikke_gpu.py unpack --archive /tmp/UNIQUE.zip --dest /tmp/UNIQUE
```

展開先をcwdにし、既存generation→run→保存結果監査→独立sealを使う。Windowsでは必要な短いsubsetと既存の低優先度・2GiB・180秒上限だけを使う。Bの予測を短くするためにCPUで未来の時刻を注入しない。元のburst cooldownと矛盾するliteralは準備段階で拒否する。

新しい出力幅は1024wordブロック境界と一致しない。共通readback検査器は境界をまたぐcase hashを分割計算し、末尾の短いブロックも全byte照合する。`readback-retain --input-extension coordinate-policy-v1 --reference-case-words 1769472 --case-words 1769856` は、両input全体・全caseのSHAと旧prefix／固定空descriptorを照合した場合だけ、追加入力を同等と認める。native SHAと出力prefix／新tailゼロの検査は維持する。汎用の「input差分を無視」optionではない。

残件はcover_all、他のsequence action、武器変更／状態異常／actor・回復保存との追加合成、元定義・CUDA実行・公開受付。20worldからすべての組合せの互換性を推定しない。

196入力（native171／wire拒否25）がApple M5のMetalで全件一致し、GPUを禁止した独立sealも成功。新規20worldに加え、旧169入力の全1,196,163,072byteとnative指紋を保持した。実GPU計算0.644926秒、初回pipeline構築91.377002秒。生成cache必須の別検査はcompiler0でCUDA／Metalの生成物を再利用した。現CUDAの実行成功・warm cache性能の証明には使わない。復旧点は`research/portable-coordinate-policy-checkpoint.json`。
