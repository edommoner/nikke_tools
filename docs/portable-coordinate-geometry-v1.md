# 共通数値による形状・円弧

`coordinate-binary64-v1`を使い、GPUが authored degree から回転係数を生成して距離・contains・円弧・積分区切り半径を計算する経路を追加した。`coordinate-geometry`は1,224入力（共通CPU参照1,209／拒否15）でM5 Metalの全word一致と独立sealに成功した。新GPU実行1回、再試行0。CPUがsin/cosの結果を入力へ詰める旧shape/area経路と、その歴史的なhost差の証拠は保持する。

## 接続した計算

共通Slangの`coordinate_geometry_v1.slang`が既存の整数binary64 hypot、区間集合、wrap/shift、補償付きmeasure、新しいsin/cos・atan2・acosを再利用する。CPU参照は`coordinate_geometry_reference.py`に新profileとして明示し、元の`calculator.aim.Shape`を変更していない。

- 円の距離、円周の被覆arc、内包／外接／内接の分岐。
- 半平面の被覆arcと、4半平面の交差による矩形arc。
- 回転矩形、growによる2矩形＋4頂点円の合成と画面角度へのshift。
- 円の2個、矩形の16個、grow付き矩形の24個の区切り半径。順序・重複を保持する。

degreeは共通数値規約で360剰余へ縮約する。shiftにも同じ縮約済みdegreeをπ/180倍した値を使う。例えば450度は90度と同じ回転であり、旧host libmとの完全一致を主張するprofileではない。

入力24wordには形状の種類と位置・寸法・角度・照準位置・rho・growだけを渡す。出力4,160wordには距離・contains・回転係数・measure・最大1,024区間・最大24個の区切り半径を保存し、未使用wordも比較する。丸めを消す式変形はしない。円のwrapで、数学的な端点と演算順を保持した端点に3 ULP差がある具体例も固定テストにした。

有限な形状入力、非負rho/grow、正の寸法を要求する。計算途中の非有限値や円arcの分母のゼロへのunderflowはstatus64で拒否する。overflow／underflowの負例3件も検査した。これらは数値domainの制限として残り、無制限の幾何計算の認証ではない。区間を切り詰めず、overflowも明示拒否する。

## 検証と実行費用

```sh
python scripts/nikke_gpu.py package --suite coordinate-geometry --compact --out /tmp/new-coordinate-geometry.zip
```

新規展開先をcwdにして既存CLIのCPU／bounded run／sealを使う。standalone probeにresident専用generation cacheを指定しない。Metalでは既存の`NIKKE_METAL_MODULE_CACHE`とpipeline cacheを使える。

正例は静的形状1,080、乱数seed固定の128、旧sin45境界1を含む。新profileと旧正本の数値方針が変わらない288入力では距離と区切り半径を旧正本へ直接照合した。さらに共通hypotやarc生成を使わないDecimalの二乗距離判定で、乱数形状の円弧内部と隙間を200点超検査した。これは標本検査であり、全幾何の形式的な誤差保証ではない。

最終CPU18件、関連・制御445件（Windows専用1skip）成功。固定full2,950→compact1,621は全残存record・byte・golden一致。旧numeric2783／scalar640／arcs135／composed97／generation88／mixed81はGPU sourceが不変で、再GPU実行0。保護された正本7ファイルとcache規約もSHA一致を保持した。

M5 GPU時間0.188791秒、入力117,508byte／出力20,367,360byte。Swift module cacheを明示し、`shared_gpu_execute`全体は1.722503秒だった。別probeとの速度比は計算していない。rawはローカルcaptureへ保持しGitHubへ送らない。

## 次の接続

この関数群は共通Slangの幾何部品であり、まだ半径方向の積分やresident戦闘の物理弾callerへ接続していない。次はpowとGauss–Legendreのnode/weightを共通規約へ固定し、前後遮蔽を含むlanding確率、物理packet展開、RNG経路へ進める。手動aim・元の全キャラ定義・公開受付も未完了。全キャラ認証0、gap20分類、UI CPU・目標未達を保持する。

CUDA／Metalのコード・fixture・比較器は共通だが、この追加部分のCUDA実機結果は未取得。直前の数値probe依頼はCodex APIのactive turn IDエラーで未送達であり、実行待ちとは扱わず重複依頼していない。

記録は`research/portable-coordinate-geometry-v1-checkpoint.json`と`research/coordinate-geometry-v1-evidence/`。
