# 共通規約の範囲スキル回転行列

`coordinate-matrix`は選択済みの`coordinate-binary64-v1`を範囲スキルの静的回転係数へ接続する。既存の共通Slang Geometry-cache実行器をそのまま使い、CUDA／Metal別の戦闘実装は追加しない。M5 Metalで151入力（共通CPU136／拒否15）が一致し、保存rawからGPU禁止の独立監査を行ってsealした。全キャラ認証0／モデルgap20／公開GPU閉鎖／UI CPU／全体目標未達。

従来のarea compilerはhost `math.radians/cos/sin`から係数を作る。新しい明示プロファイル`coordinate-area-matrix-common-v1`は既存numeric IRの正確な度数remainder、nearest90度縮約と共通多項式から係数を作る。単なる静的loweringで、CPU戦闘・距離・選択・着弾確率を入力へ埋め込まない。circleは(1,0)、rectangleは共通cos/sinを既存matrix ABIへ格納する。host sin/cos/radiansとbattle/distを禁止した全151入力packing検査も通る。

共通CPU参照ではShape.distだけをscope付きで差し替え、同じ係数と既存の整数hypot比較規約を使う。canonical CPUのファイルや旧area compilerは変更しない。contextは例外時にも復元し、同じprocess内で並列使用しない。物理着弾は既存の共通landing、damage／通知／queue／世代管理は既存battleのまま。旧host規約と共通規約の差を黙って同一視しない。

新18worldは±0、30/45度、±90/180度、90度の隣接float、-180度の隣接float、360度、±720.25度、1e20、最大有限角度と、直角矩形のtouch境界2件。全worldで実skill producerと物理producerを通す。境界外の隣接floatでは旧host CPUが本体2000＋部位3000、共通規約が本体2000のみとなることを保持し、Metalが後者と一致した。touch内側では部位3000も保持する。

旧133の全input SHAと全output SHAを保持した。さらに保存rawの先頭697303040byteを直接比較して一致を確認した。native結果には新しいarea policyの識別を付け、旧native指紋を新規約として付け替えない。拒否15件も継承し、全戦闘／fraction通知／順序付きpacket／Geometry cacheのtable・entry・代表署名・tail検査を再利用する。

GPU source、生成CUDA/MSLと両reflection、generation identityは前のcache profileから全byte／指紋を保持し、Slang呼出し0、generation cache必須hit。Metal pipeline cacheも必須hit。151入力のGPU3.713139秒、pipeline0.002616秒、shared execute7.534787秒。これは単一実行の観測であり、異なるworkload間の速度倍率は主張しない。Windowsの新規CUDA実行と現CUDA compile cache実hitは未取得。

最終compactは1738file、fullは3047file。全残存fileの実byte一致と、実証済みGPU source identityを確認。CPU78件／control416件（Windows専用1skip）とmodel-checkを検査する。初版unitの差分witnessを30度から90度へ変更した履歴を保持する（30度は両方式が偶然同一）。新GPU1回／retry0／Windows実行依頼0。rawは全SHA・byte・inode保持の疎化で563281920byte回収し、削除しない。

```sh
python scripts/nikke_gpu.py package --suite coordinate-matrix --compact --out /tmp/new-matrix.zip
# 新規展開したpackageをcwdにして実行する。
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-matrix-cpu
```

次はmanual coordinate aim／camera layer2 arbitrationを実射撃と範囲スキルへ接続し、その後sampling RNG、物理group・ADD共有、sceneのattack／buff／move／shield混在、全元定義と公開受付へ進む。証拠は`research/coordinate-matrix-v1-evidence/`、集約は`research/portable-coordinate-matrix-checkpoint.json`。
