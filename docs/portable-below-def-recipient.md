# 最終防御力が自分より低い味方の共通選択

`allies_below_def` を開発専用のCUDA／Metal共通入口
`gpu/world_below_def_entry.slang` へ接続した。既存selector14を使い、
候補の選択はGPUで行う。CPUの選択結果や戦闘traceを入力へ埋めていない。

正本 `BuffManager._effective_def` と同じく、解決済みresidentを登録順に読み、
`base_def * (1 + def_pct / 100) + caster_based_flat` を計算する。
後者の各加算は付与元の基礎防御力と、付与元を引数に取得した倍率を使う。
pendingの対象を解決したり、runtime条件をもう一度判定したりしない。
比較は厳密な「未満」で、同値の味方と自分は選ばない。比較後に戦闘不能者を除外する。
数値演算は既存software binary64を使い、整数変換・pow・normalizerは変更していない。

文字列だけのbuff対象指定は、既存lazy cacheを通じて最初の数値消費時に解決する。
対象リスト内では正本と同様に即時解決する。これらを同じ時刻へ寄せていない。
新しいhelperとprivate gateは厳密なsource ledgerで検査し、従来の監査へ逆投影する。
Runtime反射は旧74入力と完全一致し、stride138,952 bytes／入力104,400 words／
出力786,432 wordsを保持した。正本CPU・旧CUDA・Windows wrapperも変更していない。

## 検証

正本13契約で39回の対象解決と234回の実際の防御力読取を観測した。
同値、binary64隣接値、補正後の負値と0、付与元の防御力からの加算、乗算後加算、
味方の途中死亡、リスト内即時解決、instant回復、補正の期限切れを含む。
負の基礎防御力は既存入力guardが拒否するため、負の最終値は有効な基礎値＋debuffで作った。
観測前後のbattle・trace・get_buffs／effective_def／random.sample呼出数は一致する。
誤選択が数値差として現れるよう、効果が有効な間に敵の全体攻撃を与えている。

Metal95入力（正本72／拒否23）がApple M5で成功した。新21入力と旧74入力を、
既存のstride検査付きcombiner・native比較器へ接続した。
GPU時間4.294秒、生成cache必須hit、検証中の追加Slang起動0。
旧74の入力30,902,400 bytesと出力232,783,872 bytesは全byte一致。
拒否例はdomain=Noneのまま引き継ぎ、成功例として扱わないこともCPU検査する。

最終不変packageのCPU9群81検査（skip0）が成功した。
単体合計7.320秒、native事前比較8.112秒。Metal95の保存出力も独立seal済み。
最終CPU用packageと監査済みreplay用packageの差は、CLIテストの環境復元だけであり、
全GPU／入力／native baselineは同一である。

静的分類は44→43。既存235プロフィールのpacking入力SHAはすべて保持した。
アニス：スターは対象指定の問題が解消しても、`auto_damage` の `weapon_type: RL` が残るため、
まだ全編成をpacking／GPU実行できない。残る単独blockerとなったため、既存の優先順位計算が
この分類を上へ移している。順位を以前へ固定したり、キャラ対応済みと数えたりしない。
実編成全体・現在sourceのCUDA実機・新入口の全1,612保持検証は未完了。
UIはCPU、全キャラ認定0、development_onlyのまま。

## 生成だけの事前検査

初回は未定義の `S_def_pct` がSlangで拒否され、GPU dispatchへ到達しなかった。
正しい既存wire表現 `alliedFlags` を使うよう修正し、元の失敗とclaimを保存した。
修正版はSlangだけの事前検査を行い、CUDA／Metal両生成とRuntime反射を確認してから、
別の固定packageでMetalを実行した。GPUの同条件retryは0。

この作業を共通化するため、既存CLIに明示的な開発モードを追加した。
不変packageを作成・展開し、そのrootをcwdとして実行する。

```sh
python scripts/nikke_gpu.py generation --develop \
  --out /tmp/unique-generation-capture \
  --generation-cache /tmp/nikke-slang-generation-cache-v1 \
  --slang-root /path/to/slang
```

既存cacheを確認する場合は `--require-generation-cache` を加える。
今回の実packageではcache hit／追加Slang0を確認した。
出力はsource基準・paired generation receiptの検査であり、
`calculation_verified=false`、`sealed_generated_baseline_verified=false` と明示する。
GPU実行・NVRTC・driver JITは行わない。既存sealed用の生成hash照合は維持し、
`--develop` なしで未封印packageを通したり、sourceの不一致を許容したりしない。
Windowsは従来どおりbounded compile/run経路が必要。

新CLIの引数テストには、環境変数を後続のCPU群へ残す不備があった。
単一processの81検査で検出し、テスト内で元の環境を復元するよう修正した。
この失敗も保存し、修復後のCPU検査は別captureで行った。計算・GPUコードの変更はない。

記録は `research/below-def-gpu-evidence/` と
`research/portable-below-def-gpu-checkpoint.json`。
Windows操作は今回0。以前の7プロセス終了は原因unknown、保全確認falseのまま。
次は残るauto_damage武器指定の正本契約と、pending防御バフ／参照値／復活等の混在、
全保持と全カタログ実戦を進める。
