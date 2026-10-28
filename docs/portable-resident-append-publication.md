# Resident配列の追加位置とキャッシュ実行

共有Slangの`markEntry`と`initializeHPWatches`で、post-incrementを添字に使う3箇所を明示的な「格納→加算」へ変更した。旧生成CUDAは加算後のenemyBuffCount／infiniteRowCount／hpWatchCountを再読していた。旧MSLは加算前のscalarを保持しており、同じソースでも保存位置が違っていた。容量、Runtime field、数値式、保護CPU正本は変更しない。

既存の`portable_scope_snapshot_audit`へ生成CUDA/MSLの追加位置検査を追加し、生成時とpaired cacheの読み出し時に使う。旧CUDAの実生成断片を拒否し、旧MSLのscalar保存形と新しい格納順を許可する。この検査は計算認定ではない。既存source逆変換台帳は正確なbefore/afterとhashで更新し、normalizerは変更していない。

`resident-append`／`resident-append-cache-only`は実際の共有関数をincludeする9入力の小さいprobe。空、先頭、最終有効slot、refresh、owner別watch重複排除、全2048watch記述子を検査する。全3616出力wordとcanaryを独立したliteral list契約で比較し、架空の戦闘実行器は追加しない。これは記述子と保存位置の検証であり、canonical battleや全キャラ認定ではない。

M5の固定package `8ea059d2…`は9入力すべて一致。GPU0.339320秒、pipeline作成0.062737秒、fresh GPU禁止独立監査0.336597秒。初期2packageはentry衝突で生成前に停止し、GPU0、記録は保持した。全source生成でも旧scalar2箇所と今回append3箇所のguardがCUDA/MSL両方で成功した。

Windows v1はCUBIN O1の生成とfile-only cache hitまで成功した。最初のGPU段階はwrapperが`--cached-cuda-source`を渡さず、driver／launch／sync／readbackすべて0で停止。外側claimと失敗記録は保持した。service識別ができないため環境保全falseは維持し、計算・process保全と区別する。

## 共通wrapperの`gpu-cached`

sealedでpaired generation必須の`compile-cache-only-v1`だけが対象。新しい固定packetで次の4キーを持つJSONを`--request`へ渡す。値はすべて既存の絶対パス。

```json
{
  "cached_cuda_source": "C:/proof/compile/proof/generated.cu",
  "slang_root": "C:/tools/slang",
  "generation_cache": "C:/proof/generation-cache",
  "compile_cache": "C:/proof/cuda-cache"
}
```

```text
python scripts/run-gpu-packet.py --stage tests --backend cuda --capture NEW/tests --original-workspace ORIGINAL --timeout 60
python scripts/run-gpu-packet.py --stage gpu-cached --backend cuda --capture NEW/gpu --original-workspace ORIGINAL --request REQUEST.json --timeout 180
```

実際のNEW／ORIGINAL／REQUESTは絶対パスで指定する。既存のBelowNormal、fresh Job、2GiB、開始gate、外180秒／GPU子60秒を使い、CUBIN O1・compile cacheとpaired generationの必須hitを要求する。子で環境のずれを拒否し、compiler fallbackはしない。新stage固有のclaimを排他的に作成し、旧claimを消さない。登録外profile、不正request、環境改変、重複claim、計算成功でも環境保全falseになる結果の保持をCPU検査する。

v2packet `e65d79b7…`はv1と全golden／GPU source／入力が同一。変更は共通CLI、wrapper、wrapper testの3ファイルだけ。保存済みCUBINを再コンパイルせず検証する。CUDA実計算の結果は別receiptで確定する。全106のMetal再認定・独立監査も別証拠であり、この9入力から推定しない。

## CUDAとの照合結果

Windows v2は56検査成功後、保存CUBINで9入力を1回実行し、Macと全entryのinput/output/native指紋および正規化生成sourceが一致。launch／sync／readback各1、Slang／NVRTC0、paired generation／CUBINとも必須hit。host dispatch0.327625秒、GPU子11.218982秒、外側32.371456秒。Job残存0・timeoutなし・process保持true。service未識別のためpreservation／全体passed／transport_verifiedはfalseを保持する。旧GPU起動前失敗と区別し、CUDA全体成功へ読み替えない。固定report `7f2e988f…`、照合証拠 `research/target-count-query-evidence/resident-append-cross-gpu-v1.json`。
