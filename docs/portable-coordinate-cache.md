# Geometryの小数6桁キーと共有キャッシュ

private `coordinate-cache`を共通実行器へ接続した。M5 Metalで丸め`coordinate-round`9046入力（正例9039／拒否7）、実戦`coordinate-cache`133入力（共通CPU118／拒否15）が全word一致し、それぞれ保存rawから独立sealした。全キャラ認証0／モデルgap20／公開GPU閉鎖／UI CPU／全体目標未達。Windowsでの現CUDA実行・compile cache実hitは未取得。

## 数値規約

CPU正本の`Geometry.landing`は`(round(ax,6),round(ay,6),round(radius,6),round(grow,6))`でdictを引き、同じキーの最初の計算結果を返す。丸めた入力を再計算する方式や、直前の1件だけを保存する方式では再現できない。

`coordinateRoundSix`はbinary64の仮数を正確な整数として取り出し、共通uint128で5^6を乗算し、残る2の指数でnearest/even整数丸めする。結果整数は処理範囲で2^53未満なので正確にbinary64へ移せ、既存software binary64で1000000除算を一度行う。指数33以上はdecimal6の摂動が半ULP未満なので入力を返し、指数-22以下は符号付き0となる。NaN／Infは明示拒否。丸め結果の-0は保持し、dictキーでは+0へ正規化する。保護されたbinary64本体は変更しない。

独立Fractionによる有理数丸めとCPythonの`round(x,6)`を比較し、次にCUDA／MSL共通SlangをM5 Metalで検査した。半端値・隣接float、指数-25〜35、subnormal、最大有限値、ランダムbit、正負・signed zeroを含む。単純な`round(x*1e6)/1e6`と異なる実例もunitで保持する。

初版probeは数学正例9039件が一致したが、拒否コード1が共通transportの期待64と違い7件失敗した。外側の拒否コードだけを修正した別パッケージで全9046件をseal。失敗のcapture／raw／sourceは保持し、同claimは再実行していない。

## 共通実行器

全射手が同一Geometryのcacheを共有する。dormant group arenaの920000〜1048576wordへ置き、8192slotのopen addressingと完全な4キー照合を使う。hashだけで一致判定しない。entryはキー・core_open／core_under・front／reachのbinary64全bitを保持する。初回の実入力で積分し、hitでは保存した確率を使う。半径やgrowを丸め値に置き換えて積分しない。

Geometryの切替はworld frameのsnapshot境界で判定する。実際の対象順、core形状、既定照準が同じなら、graphの世代やcore選択nodeが変わってもcacheを保持する。対象名が一意な現private adapterでは、must_breakは生存対象集合と静的宣言から決まるため、その対象順が同じならmust_breakも同じ。重複labelは既存Actor binding／reference境界で拒否し、未認証の組合せを黙って扱わない。

Native Geometryは等しいGeometryの最初の実体を残すため、core／autoのsigned zero等も最初の代表値を保持する。coreはscriptの径ではなく実Shapeの半径を署名へ保存し、core無しはbase -0も含めNoneとして正規化する。Geometryが切り替わると使用entryとhash tableをclearする。queryがない間のGeometry切替も追跡する。

容量は対象0なら4096entry、対象127なら231entry。上限到達で明示拒否し、古い値の破棄や再計算でnative dictの意味を変えない。これは現在のprivate GPU容量であり、nativeの無制限dictと同一の受付範囲を主張するものではない。

## 実証と再利用

旧120入力をそのまま保持し、新12worldと容量拒否1を追加した。固定半径、同じ丸めキーの異なる半径、別射手の最初の値、grow0→正の微小値、同じ丸めキーでもcore移動によるGeometry切替、同径同中心でnodeだけ更新、同じ対象の再出生、同じ対象集合の順序変更、7散弾×2銃口、queryがないGeometryの隙間、base -0、127対象・容量近傍を比較する。正常な容量近傍ケースには179entryと55個の同一hash bucket衝突があり、全table／キー／値を検査した。30秒の負例は実際に231件を超え、GPUのoverflow旗と231件保持・拒否64を確認した。

passive observerは実際のGeometry生成・dict照会・最初のLanding object再利用・最終entryを読む。新しいlanding計算を追加しない。既存の全戦闘／fraction通知と残差／順序付きpacket比較に加え、cacheの完全な代表署名、全entry、hash table、未使用tailゼロを比較する。observerは例外時にも元のhooksへ戻る。

正例118件のnative Geometry照会は1024回。GPUの実照会878回はcache hit515／積分363で、元からある同一射撃template再利用146回とは分けた。負例の途中までの積分はこの正例集計に含まない。今回は同一workloadの非cache版との速度比較をしておらず、runtime倍率は主張しない。133入力全体のGPU3.681750秒には長い容量検査も含む。PSO compile90.407945秒、shared execute99.236430秒。生成cacheを必須hitにし実行時Slang0。

旧120の入力・元native指紋を保持した。実rawでは全戦闘／legacy領域、物理bank、coordinate packet領域の計559672320byteが旧保存物と一致。新しいcache arenaと積分の作業scratchは別profile状態なので、旧full raw同一とは扱わない。全出力は新しい明示sealの指紋で固定する。

## CLI・CUDA cache・残件

`package --suite coordinate-cache --compact`と`package --suite coordinate-round --compact`が正式な検証プロファイル。新規展開→CPU preflight→bounded GPU→保存結果監査の既存CLIを再利用する。literal spread IRとnative metadataの不一致もGPU前に拒否する。

通常81／97／core120のCUDA・MSLを同じpaired generatorで生成し、以前の保存物と全byte一致した。これらを別途GPUで再実行していない。normalizer・CUDA cache key・保護compile cache本体は変更していない。再利用可能な生成条件の証拠であり、Windowsの実cache hit／計算成功とは区別する。Windows既存chatはread-onlyでrevision78・idleのまま確認し、新規実行依頼0。

最終immutable packageはCPU72件、control416件（Windows専用1skip）、model-check成功。full3041→compact1732の全残存record／byteが一致し、実証GPU source identityも保持。保護7source保持。新GPU3回（丸め初版のstatus不一致1、丸め成功1、実行器成功1）、同claim retry0。cacheの初版CPU preflight失敗は、重複labelが既存の早いguardで拒否されたのにテストが後段messageを期待したもの。元のcaptureを保持し修正した。負例や入力を減らして通していない。

過去raw1件と今回rawを全byte／SHA／inode保持で疎化し、1724448768byte回収。raw削除0、実行時1GiB reserve保持。

次は`app/portable_coordinate_area_specs.py`に残るhost `math.cos/sin`の回転係数loweringを共通化し、両OSの入力規約を揃える。その後manual aim／layer2、sampling RNG、物理group・ADD共有、sceneのattack／buff／move／shield混在、全元定義と公開受付を進める。集約は`research/portable-coordinate-cache-checkpoint.json`、保存証拠は`research/coordinate-cache-v1-evidence/`。
