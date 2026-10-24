# 投射物・HP盾補正の共有scalar GPU実証

共通CLI `destructible-modifier`をsealed suiteへ登録した。先行CPU設計と同じ20ケースを、共有Slangのresident carrier・数値query・7因子・最終丸めへ接続した。Apple M5のMetal29入力（native20・拒否9）が全件一致し、保存rawの独立sealも成功。CUDA/MSLは同じSlangから生成・厳密照合する。現在のCUDA実機、実戦producer/Frameへの補正接続、ゲーム規則の認定は未完了である。

## 共通計算とprivate入力

新しい`gpu/destructible_modifier_runtime.slang`は、既存の`queryRecipient`、`scalarValue`/`recipientValue`で対象味方・期限・条件・stackを読み、元のactive順序で補正を合計する。`sampleDamageFactors`が採取した第5因子へ対象種別の補正を加え、`damageFromFactors`へ渡す。既存の7因子の積・丸めを複製せず、software binary64を使う。PROJECTILE/HP_SHIELD/bodyを明示し、他種別向け補正を混ぜない。

source/tableをlowerするのは専用adapterだけであり、通常の`portable_runtime`はこの2statを引き続き拒否する。既存コンパイラで数値value/stack/recipient/conditionをencodeした後、privateなkind4/stat0 markerへ数値payloadを保持する。別添の256行axis表がprojectile/HP-shieldの意味を指定する。通常numeric stats集計はkind4を読まないため、ATKや他のダメージstatへの代用にはならない。probeはaxis付き行のkind/stat/flagsを検査し、型が異なる入力を拒否する。

独立probe `gpu/destructible_modifier_probe.slang`は共通dispatcherでauthoredなbattle_start通知を実行してから、宣言時刻にscalar queryを行う。CPUシミュレーションから作った通知列・補正値・ダメージ値は入力しない。一方、今回は通常戦闘schedulerが自律生成する攻撃ではなく、同じ20ケースのscalar契約の実証である。

入力は通常86016word＋DMQ1 header32word＋axis256word＝86304word、出力は通常coreのstride159744wordを維持する。private診断は末尾32wordに置き、damage/factor5/projectile sum/shield sumを比較する。実戦用1048576wordのstrideを流用して内部住所計算と食い違わせない。Runtimeの実reflection strideは163528byte。

## 実測と失敗の保持

閾値・寿命の前段ではなく、今回比較したのはscalar補正である。投射物/HP盾の+50%=1350、body/別種別への非適用900、通常ATKダメージ+40%との加算1710、別carrier20%+30%、-50%=450、-100%の最低1、期限境界、別味方self/分隊贈与、条件不成立、2stack、丸め前境界2がCPUモデルと一致した。9負例はmagic、hit盾、attacker、reserved、NaN時刻、負係数、未知axis、未使用行axis、数値stat行へのaxisを拒否する。

最初の固定packageでは、空statが通常compilerで非数値markerへ変換されてvalueを落とし、GPUの型ガードが補正入力を拒否した。2番目では数値stat0をprivate領域と誤認し、ATK%へ補正が混入して1350のはずが2100になった。通常statsの意味や正本を変えず、kind4 markerのpayloadとして値を保存して解消した。元の失敗2capture/raw/claimとimmutable sourceを保持する。異なるsource/inputの固定packageを各1回実行し、新GPU合計3回、同一claimの再試行0。

成功packageは`a3cf6af59b8a0063e652d60ccee61e4191b05718b24d9d311ccdda2c2034c13f`。GPU0.004544秒、library0.858294秒、pipeline2.488622秒、readback18530304byte。実runは必須generation cache hit/追加Slang0。sourceの異なる2回の生成-only準備でCUDA/MSLを各1回（計4 compiler呼出し）生成した。これをCUDAコンパイルcacheやdriver JITの改善測定とは扱わない。

独立seal後にgoldenを登録した。最終package `933ca534aa266aefff29c3973b10bbc3ebe242186044986bbd4e521b5cdaf737`をfresh unpackし、CPU37検査（skip0）・native20が成功。実GPU29blockを全input/raw SHA付きの疎なfixtureへ保存し、20正例の4 scalar値をbinary64 bit列まで比較する。status/kind/量/第5因子/補正和/未使用tailの140改変を検出した。拒否9blockのstatusも確認する。sealed生成baselineは必須cache hit/追加Slang0/GPU0で照合した。最終packageでのGPU再実行はしていない。

```sh
python scripts/nikke_gpu.py package --suite destructible-modifier --out /tmp/modifier.zip
python scripts/nikke_gpu.py unpack --archive /tmp/modifier.zip --dest /tmp/modifier
# 展開先をcwdにして、既存のrun/cpu-only/auditを使う。
```

## 残件と既存経路

今回のsourceは新規2 Slangファイルだけで、通常147・実戦typed152のsource closureはそのまま。旧Metal44、元定義8、通常492のGPUは再実行していない。保護CPU/compiler、binary64、strict normalizerは変更していない。全266プロフィールの全行・packing245/base185・残20分類のissue/順位も完全同一。readinessにprivate Metal scalarの29/20だけを追記し、public GPU admissionと全キャラ認定には昇格させていない。

次はこのqueryを既存の実戦Frameへ接続する。対象kindとaxis表を明示するdescriptorを使い、親攻撃の量を採取してから兄弟着弾を進める。同期子のbuff更新で親の残り着弾量が変わらないこと、body/typedの混在と値固定を既存receipt比較へ組み込む。HP盾の実戦選択/迎撃、対象別DEF、logical owner policy、元プロフィール全体はさらに必要である。

Windowsの状態取得は今回も失敗した。新run依頼0、CUDA実機未検証、準備済みCUBIN O0実験は未実施。小さい新probeのCUDA確認ができても、従来のfull Frame/module load問題が解消したとは主張しない。全キャラ認定0・UI CPU・全目標未達。

証拠は`research/destructible-modifier-gpu-evidence/manifest.json`、checkpointは`research/portable-destructible-modifier-gpu-checkpoint.json`。個人設定・rawバイナリ・toolchainは共有しない。
