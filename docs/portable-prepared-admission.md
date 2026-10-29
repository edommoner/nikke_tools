# 監査済み入力の受け渡し：次の実装要件

これは未実装の設計境界。現CUDAの計算証明や受付経路ではない。

Windows固定1e54383d…で、実戦3/拒否12の全群完了後に既存APIをそのままCPU計測した。staged admit34.451秒、保存link admit67.181秒、入力read/hash0.012秒、合計101.644秒。後者単独でもGPU子の60秒上限を超える。外側の180秒は守れたが、この経路でGPUを起動すると準備だけで子予算を消費する。GPU execution claimを消費せず停止した。

次は監査を省略するcacheではなく、CPU準備・GPU実行・独立監査を明示的に分離する。

1. CPU準備段階は元の全staged/link/PTX/object/compiler/Job/source/golden監査を実行し、渡すartifact・入力・出所・証拠の完全なbytes/SHAを固定する。native計算値/contextを保存・再利用せず、既存の指紋と証拠を使う。
2. GPU段階は準備済み証拠と実行所有claimを束縛した新しい明示protocolだけで受け取り、渡された入力・CUBIN・生成CUDA/source・証拠snapshotの全byte整合性を検査してから既存の共通GPU実行器を呼ぶ。mutableな元pathや単なるsuccess flagだけを信用しない。古いrun/staged-runのガードは保持する。
3. 準備側/実行側のpackage ID、元計算owner、transaction nonce、未来のcapture、完全なgolden/input、旧/現producerとreceipt keyを別々に束縛する。同じ未実行GPU試行のappend-only所有を維持し、claimの消去・再試行をしない。
4. GPU子60秒、各stage180秒、Job2GiB/低優先度/gate/終了後即時観測を維持する。時間短縮は実測で確認し、上限の変更で解決しない。
5. 実行後の完全な出所・artifact・入力/出力・共有native比較を独立CPU段階で行い、完了前はcalculation_verified=falseのままにする。保存監査済みwitnessを使う場合も全input/output/native/source一致と元のscopeが必要で、既存106入力用joinの固定pinを緩めない。

実装前/実装後に、入力/CUBIN/source/proof/claim/nonce/ownerの改変、未完了準備、異なるgolden、同一試行の再実行を拒否する検査を用意する。計算・効果定義・数値演算・strict normalizerを複製/変更せず、transport glueを既存実行器へ接続する。元の失敗/claims/rawを保持する。

今回のsource-host CPU計測は`research/portable-admission-budget-peer-v1.json`。Macは小要約とmanifestの元bytes/SHA、期待input/receipt、bounded sourceを照合した範囲で、Windows原rawや診断script全体のMac独立監査ではない。Windowsはidle、GPU未実行。
