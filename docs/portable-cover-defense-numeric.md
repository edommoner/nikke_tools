# 遮蔽物防御：独立した基礎量と共通数値部品

`cover_def_pct` は現在のCPU正本でSCOPED_INERTであり、元ソルジャーO.W.の入力変換を阻む。今回追加したのは、独立した基礎DEFを宣言する数値部品と、既存carrierから倍率を読むCPU関数。遮蔽物層・元戦闘・通常UIへの接続ではない。元statの拒否とreference_model_gapは維持する。

## 公開実測から分かること・分からないこと

[NIKKE Synergyの著者による物体比較](https://nikke-synergy.com/arena-guide_en)は、遮蔽物のHP/DEFはレベル依存で、本人のHP/DEF増加を継承しないと報告している。[元の検証画像](https://images.nikke-synergy.com/information/verify/cover.jpg)もブラウザで視認した。ただしarenaでの著者の報告であり、正確なレベル曲線やPvE全条件を証明する資料ではない。画像の非クリティカル表示31,612、クリティカル表示47,419に対し、著者の注記は31,612×1.5=47,418となっている。未丸め内部量が不明なので、これから精密な丸め規約や基礎DEFを逆算しない。

[吟味.netの攻撃側DEF検証](https://ginmy.net/nikke_def_test)は筆者の実測だが、遮蔽物への被ダメージや基礎量の検証ではない。遮蔽物の曲線を決める根拠には使わない。今回の数値式は、既存incomingの演算形を使った明示モデルとして扱う。

## 数値契約

`B`を明示した遮蔽物基礎DEF、`p`をcover_def_pctの順序付き合計とする。

```
effective_cover_defense = B * (1 + p / 100)
amount = max(attack - defense, 0) * coefficient / 100
amount = amount * max(0, 1 + received / 100)
damage = max(amount, 1)
```

同じ`incomingDefendedQuantity`を、明示したcover DEFとbody DEFの比較に使う。CUDA/Metalは同じSlangとsoftware binary64を使用。乗算と除算をまとめず、native double・FMA・途中の整数変換を加えない。例の771.43は、`×100÷100`を省略した771.4300000000001と異なる。初期unitの省略した期待式は失敗し、その記録を保持して順序を訂正した。

入力は有限binary64、attack/coefficient/cover baseは非負。割合とbody effective DEFは符号付きの明示数量。入力不正はtransport64、有限入力からの非有限結果はtransport0/numeric16、成功は両status0とする。結果の全wordと予約領域を比較する。負のDEFやreceived補正も宣言した数値領域の検査であり、ゲーム中の全補正規則を認定しない。receivedを本人から遮蔽物へ継承する実機仕様も、この部品からは導けない。

`cover_defense_model.live_defense`は既存`_live_sum(name,'cover_def_pct',t)`を使う。元倍率・元上位ATK3人・遅延対象確定・5秒の半開失効をCPU unitで確認した。これは元carrierを明示時刻10秒にactivateした読取検査で、元の周期schedulerによる実戦発火の証拠ではない。本人のbody DEFを基礎量へ流用しない。基礎量を与えるレベル曲線は未実装。

## 実証

固定83be1329/package `0c6a3d09d6b01f4ca95c67424cd8d6a0e1a3ca3ff7e5d49c62960f226d1bdee1` をM5 Metalで1回実行。562数値入力（元10段階倍率、ULP、極小値、overflow、128固定乱数vector）と不正wire10件の全572入力が一致した。数値成功558、numeric16が4、不正wire64が10。GPU0.000273秒、初回pipeline0.034186秒、library0.045703秒。新sourceなのでpipeline missを正しく記録し、warm測定へ読み替えない。

別fresh GPU禁止childの全562 native/572入力の独立照合は1.172452秒で成功。親結果再利用0/GPU0。goldenは `research/portable-cover-defense-numeric-v1-expected.json`、receiptは `tests/fixtures/cover-defense-numeric-independent-v1.json`、小証跡は `tests/fixtures/cover-defense-numeric-metal-v1.json`。

最初の起動指定はstandaloneにresident専用generation cacheを付けてしまい、capture/claim作成前に拒否された。そのログを保持し、正しい指定の別captureで実GPUを1回実行した。同claim retry0/GPU失敗0。数値unit初期のimport初期化、1ULP期待式、未解決対象を即時listと仮定した失敗も保存。比較を緩めていない。

最終c2ab073c/cache-only packet `95d02b205329745e0598ea1e3e93d98bc4c68ae4ad6616d0752a1f5b8111ce3e` は16unit成功、分類41unit成功。CUBIN/O1/2GiB/60秒compile-planはpolicyのみ成功。fresh model-checkとentry-inventoryも成功し、元266profileのpacking254・失敗12/13分類・全キャラ未認定を維持する。新Slang2ファイル以外の既存GPU fileと保護CPU4/normalizerは変更0。旧residentの273 source閉包も一致しており、旧戦闘のGPU再実行は重ねない。

入力corpusの生成にあったホストのpowを排除するため、実行済み128乱数vectorを入力だけのhex binary64表へ固定した。`research/cover-defense-random-inputs-v1.json` は結果を含まず、元の全36,612byte入力と完全一致する。native数値oracleとadapterの全byteも元packetと同一。GPU数値sourceは変更せず、元証跡の出所を新packetへ付替えない。

固定入力版f3820a6c/packet `40a8e62b05b81b764b7446b2718614b8dee21bacf2b0d5660c9394f58b1b6865` は自身のCLIで17unitとfresh native562/572入力の基準指紋一致に成功（CPU 0.806435秒/GPU0）。CUBIN/O1/2GiB/60秒compile-planもpolicy成功。旧GPU/独立監査のpackage IDは保持し、新packetでGPUを再実行したとは扱わない。最終静的監査・model-checkも成功し、254/266・未対応12を維持する。

## 共通CLI・次の接続

`package --suite cover-defense-numeric --out NEW.zip` → `unpack` → 固定packet自身の`run`。standaloneなので`--generation-cache`と`--require-generation-cache`は指定しない。Metal pipeline cacheは通常の共通optionを使える。`cover-defense-numeric-cache-only`は同じ数値/入力/golden/比較器のCUBIN/O1必須cache hit入口で、residentのpaired generationを要求しない。full-source compiler certificateをこのprobeへ流用しない。現CUDA実機未検証/Windows追加依頼0（既存hostへのread-only確認はunavailable）。

次は、5人の独立した基礎量のwire、元cover statのprivate lowering、既存incoming/protectionのcover段階への接続、shield callback前後のsnapshot/再query規則、均等分配との関係を明示する。body/cover量を同じ計算済み値で代用せず、元ソルジャーの周期・選択・失効・実cover破壊/復活を全戦闘で比較してから受付を広げる。レベル曲線・実機layer規則・全キャラ・公開GPU受付は残件。proof stemは `.portable-recovery/proofs/cover-defense-numeric*20261030*`。
