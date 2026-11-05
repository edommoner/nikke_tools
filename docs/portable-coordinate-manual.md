# 明示cover／holdの共通実行器（Metal検証済みprivate profile）

`coordinate-manual` は `coordinate-sampled-delivery` の136入力を保持し、明示操作25worldとwire拒否8入力を追加するprivate suite。通常画面はCPUのまま。全キャラ・全特殊効果の認定にはならない。

入力は `control.sequence` の時刻・cover duration・hold untilという記述された値だけを変換する。CPUで射撃／再装填／cover終了時刻を計算して渡さない。条件付きcover/reload/burst policy、cover_all、未知のsequence actionはこのproducerの範囲外。

実行本体は `gpu/coordinate_manual_control_runtime.slang`。既存のカメラ調停、charge、武器変更、reload、HP・cover処理を呼び出し、同じSlangからCUDAとMetalを生成する。入力109528word、出力1769472word、Runtime容量は従来どおり。出力の未使用tail 919744から80wordを5人の状態へ割り当てる。旧入力version 1/2では全領域をゼロのまま保持する。version 3だけで追加状態を解釈し、それ以外の未使用領域は厳密なゼロ検査を維持する。

正本の状態遷移はパッシブobserverで観測する。時刻0・duration 0はraw end=0を保持し、正の時刻のduration 0は次frameで解除する。duration Noneは再装填完了まで、満弾なら進入の次frameまで。時限解除時に弾が残っていれば装填を中断し、空なら最初のclip取得後に中断する。中断は満装填通知を発生させない。元武器が連射・変更先がchargeの場合は、内部のcharge段階と通知・条件から見えるchargingを別に保持する。cover中の武器変更、禁止状態、カメラpreempt、後から予約されたhold、被弾を同じ比較経路で検査する。

cover／holdで全射撃を抑止するworldも正当な入力。点／pelletの対応、全乱数draw、MT全624wordとindexを照合し、ゼロ消費を検証する。射撃の有無だけで成功を決めない。

共通CLIのstrict adapterでは、登録sourceとadapter SOURCEが違う場合に入力準備前に停止する。親suiteから古い入口を継承した誤登録の再発を防ぐ。過去のsource監査は新しい逆差分を通して当時のinclude graphを復元し、既存のgoldenを書き換えない。

```sh
python scripts/nikke_gpu.py package --suite coordinate-manual --compact --out /tmp/UNIQUE.zip
python scripts/nikke_gpu.py unpack --archive /tmp/UNIQUE.zip --dest /tmp/UNIQUE
```

展開先をcwdにして既存のgeneration、run、保存結果監査、独立sealを使う。169入力（native151・拒否18）はM5 Metal照合と独立sealを完了した。CPU112件、制御428件（Windows専用1件skip）、旧136入力962,592,768byteの保持を確認した。GPU計算0.484183秒／初回PSO91.796496秒。最初のGPU出力では初期化順序とmode charge保持の差分を発見し、原出力を残した別sourceで修正した。実GPU計2回・同claim retry 0。新しいsource/inputを検証するときだけpackageへ `--develop` を付ける。CPU検査・paired生成だけではGPU計算の成功を意味しない。Windowsは既存の短い上限内の検証だけに使い、未送達の旧依頼を重複実行しない。

証跡は `research/portable-coordinate-manual-checkpoint.json` と `research/coordinate-manual-v1-evidence/`。成功・失敗のrawはローカルへ保持し、疎化前後の全SHA／byte／inodeを照合した。GitHub共有にはraw・compiler配布物・個人設定を含めない。次は条件付き方針producer、cover_all、post-delay／listenerなし／down・保存回復との合成、元定義・CUDA実行・公開受付を進める。今回の25worldから全操作の互換性を推定しない。
