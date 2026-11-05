# 座標距離の整数binary64 hypot

通常の座標貫通/爆発選択は正本 `Shape.dist` → `math.hypot` → `contains` で決まる。`coordinate-math` を共通CLIへ登録し、この距離数値処理をCUDA/Metal共通の `gpu/coordinate_math.slang` として実装した。既存binary64・正本CPU・normalizerは変更していない。実戦の座標選択callerへの接続、回転矩形のsin/cos、原キャラの全定義対応は次段階であり、全キャラ認定は0のまま。

## 数値設計

有限値の絶対値を指数と53bit整数へ分け、2乗和と中点比較を4個のuint64 limbで正確に計算する。整数候補の53bit探索後、2乗した中点との大小と偶奇でnearest/evenを決める。native float/double・近似sqrt・powは使わず、既存 `mulWide` / `f64Unpack` / `f64Pack` を再利用する。

指数差28以上なら小さい側による変化は大きい側の半ULP未満のため、その値を返す。差27以下は2乗和を省略せず計算する。和と丸め中点は256bit内に収まり、固定配列以外の確保はない。符号付きzeroは正のzeroへ、INFはNaNより優先し、その他のNaNは共通canonical NaNへ揃える。極大値のoverflowも明示INFになる。

初期CPU検査で数学的単一丸めとnativeが異なるsubnormalを発見した。入力bits `000c000000000000` / `0007000000000000` の単一丸めは `000de477359432dd`、nativeは `000de477359432dc`。正本に合わせ、正規化したnormを53bitへ丸めてから縮小する二段丸めを保持する。初期差分を許容誤差へ変えず、独立整数oracleの単一丸めと互換丸めを両方テストした。

CPythonの[vector_normソース](https://github.com/python/cpython/blob/v3.12.12/Modules/mathmodule.c)で正規化後の計算と最後の再scaleを確認した。実MacはPython3.12.15。この実装は独立の整数2乗/中点比較であり、CPythonの浮動補償計算法をコピーしていない。nativeとの一致証拠は以下の固定・乱数corpusに限り、全binary64入力についてのCPython/全platform同値を証明したという主張はしない。

## 検証

固定1024数値入力はzero/subnormal/normal境界/最大有限/INF/NaN・両符号、指数差26/27/28、sqrt(1+2^-52)近傍、近接指数256入力、決定的広域乱数を含む。入力packingはliteral bitsだけで、CPU計算した距離や選択集合を含めない。native `math.hypot` と別の任意精度整数isqrt oracleが一致することを確認してから、GPUの結果bitsと未使用wordを全比較する。4個のCPU検査ではさらに30000入力を照合し、packing時のoracle呼出しを禁止する。

固定development packageのMetal1回で1024数値＋2拒否の全word一致。別プロセスで保存rawを独立sealした。M5 GPU .000261秒、Slang .234602秒、pipeline .036313秒。subnormal二段丸め/半ULP近傍/INF優先/未使用tailの保存rawコピー4改変を検出し、原本全32832byteを保持。

最終compactのCPU4/1024nativeと共通制御392（Windows専用1skip）が成功。full2880→compact1574ファイル、残存record・全サイズ/SHA/byte・goldenが完全一致。既存coordinate35/24/16/mixed81の閉包は全て現sourceと一致しており、新しい数値helperを含まないため再GPU実行を省いた。

Windowsには新しい小normカーネルだけを固定2ファイルpackageで1回依頼した。source閉包は新2file＋既存binary64の計3file。既存wrapperのfresh Job/2GiB/BelowNormal・外180秒/内60秒・gate/cleanup/観測を維持し、別CPU stage・full battleビルド・再実行は行わない。Windowsでも計算・containmentが成功し、original比較JSON全1026entryのファイルサイズ/SHAが独立監査済みMetalの比較全文と一致した。source/input/output指紋も一致。CUDA compile .237171秒、dispatch .003335秒、stage全52.817556秒。監視process欠落0・Job終了後空だがservice未確認なので環境保全/stageはfalseのまま。

診断4ファイルの公開は自動承認レビューが具体的内容への個別許可不足として拒否したため停止。Windows原本は保持し、接続内の読み取りで照合した。詳細診断・entry指紋・compiler metadataは追加公開せず、照合結果はMacのローカル一時記録に保持。Windows rawの取得や新しい独立raw auditは行っておらず、原本比較JSONの指紋一致とWindowsでの既存共有比較器の計算成功を証拠とする。

## 利用と残件

`python scripts/nikke_gpu.py package --suite coordinate-math --compact --out PACKAGE.zip` で再利用可能。期待値・固定package ID・小さい監査結果は `research/portable-coordinate-math-short-expected.json`、`research/portable-coordinate-math-checkpoint.json`、`research/coordinate-math-evidence/`。rawとcompiler配布物は共有内容に含めない。

次は回転矩形の三角関数の互換性とshape距離/containsへの接続、aim/radius確定とinterruptを含む実packet連鎖。通常の座標物理、保留B3、跨frame同名世代交代、元全定義・公開受付も残る。20gap・UI CPU・全キャラ0を維持する。
