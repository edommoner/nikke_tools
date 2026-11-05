# 乱数射撃の親参照量と整数総計

`coordinate-sampled-parent` は乱数物理射撃と `dealt_fixed_damage` を同じresident実行器へ接続したprivate profile。CUDA／Metalは同じSlang・効果定義・入力・比較器を使う。M5 Metalで39入力（共通CPU36／拒否3）が全一致し、GPU禁止の独立監査にも成功した。通常damageスキルの乱数、武器変更・healとの合成、sampled group owner、全キャラ元定義の認定は残る。

## 数値と接続

物理射撃が実際に生成した整数packetを既存の `PacketIntegerSum` で128ビット加算し、muzzle数で割った値をfull-charge通知へ渡す。BODY／PART／INTERRUPTを含む生成量と、実際に戦闘へ計上された量を混同しない。既存の通知Frame・`parent_fixed_runtime.slang`・子packet queue・BODY着弾処理を再利用する。固定damageの子packetはcritical乱数を消費しない。

新しい `packetIntegerRatio` は128ビット整数を32ビット4桁で長除算し、商と余りからbinary64へ最後に一度だけnearest-even丸めする。先に整数全体をdoubleへ変換しない。分母1〜1024、分子0〜2^128−1を扱う。例として35000000000000007÷3は1.1666666666666668e16が正しく、先に分子をdoubleへ変換すると1.166666666666667e16へずれる。既存のbinary64・pow・整数変換本体は変更していない。

実戦の大整数ケースでは、親量と全114packetは一致した一方、既存のdouble逐次加算による戦闘総計に差が見つかった。CPUの整数総計260714285714285742はbinary64に正確には収まらない。そこでBODY／PARTの実計上箇所へ、射手別の永続128ビット総計と件数を追加した。元のdouble総計も保持し、実packetから独立に再現した順序付きdouble加算と比較する。新decoderはheader・予約領域・整数総計・件数を検査して整数総計を読む。CPU正本や期待値を丸めて一致させていない。

ADDのHP上限付きscoreとINTERRUPTはこのmain総計へ含めず、既存処理を保持する。新領域は物理MT直後の未使用tail919704から29wordを再利用する。入力109528／出力1507328word、Runtime138952byteを維持し、容量追加は0。旧buff-only入力では親量maskが無効なためtailは0のまま。

## 実証と保持

新16契約は奇数muzzle3／5／7、貫通、0／負値／正値から0への整数化、重複timing、1回budget、隔回通知、親量のないtiming、大整数、2射手、後続ATK buff、INTERRUPTを含む。全物理MT状態・消費数、実packetの量・順序・対象・generation、最後の親量bitと整数和、全battle状態・skill traceを比較した。

- 戦闘39入力と数値probe14045入力が現在ソースのM5実GPUで全一致・独立seal。
- 数値正例14040は全1024分母、128ビット境界・丸め境界・seed固定乱数。Fraction／CPython整数除算と別のDecimal高精度計算を使用。負例5も検査。
- 最終CPU28検査、共通制御416検査（Windows専用1件skip）、数値CPU4検査、packing／GPU禁止の共通正本16契約が成功。
- 旧23入力・native fingerprint・全138674176byte readbackを完全保持。旧9系統のCUDA／MSL生成コードも全byte保持。旧goldenを新sourceへ付け替えない。
- full3113→compact1768の全残存record・byteを保持。保護7source、core probability、厳密normalizer、CUDA cache規約は不変。

今回のmilestoneは実Metal4回（親量初版1／総計修正版1、数値初版1／共有source更新後1）、同claimのGPU再実行0。親量初版の38/39成功・総計不一致の出力も保存する。容量ゲートで止まった2回はGPU0。終了済みrawの全byte・SHA・inodeを保つ疎化で790458368byteを回収し、原本削除は0。

修正版戦闘GPU0.464257秒、初回パイプライン作成92.692870秒。現在数値probeのGPU0.002363秒、Metalパイプラインcache命中・PSO0.000225秒。共有Slang生成cacheを使い、cache keyやguardを緩和していない。現在CUDA計算／CUDA cache hitは未取得。Windowsの新実行依頼0。

## 共通CLI

```sh
python scripts/nikke_gpu.py package --suite coordinate-sampled-parent --compact --out /tmp/new-parent.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-parent.zip --dest /tmp/new-parent
cd /tmp/new-parent
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-parent-cpu
```

通常のgeneration→CPUゲート→bounded実行→保存結果の独立sealを使う。数値単体は `--suite packet-ratio`。`reference --suite coordinate-sampled-parent-common --out /tmp/new-reference.json` はfull不変パッケージから共通CPU16契約だけを実行する。compiler source証明書も登録済みで、CUDA計算証明とは区別する。

`model-check` は作業ツリーの上流設計文書も参照する。実行用fullパッケージでは上流docsを配布しないため、今回full packageでのmodel監査は文書欠落で停止した。その失敗を保持し、文書を持つ作業ツリーで読取専用監査が成功した。実行パッケージや過去証拠へ文書を後付けしていない。

次は通常damageスキルのcritical乱数・queue、武器変更／heal、sampled group ownerを順に接続する。全キャラ認定0／20model gap／UI CPU／public GPU closed／full goal falseを維持する。証拠一覧は `research/coordinate-sampled-parent-v1-evidence/inventory.json`、集約は `research/portable-coordinate-sampled-parent-checkpoint.json`。巨大な比較詳細は原本の場所とSHAを記録した要約を共有し、元レポートをローカルに保持する。
