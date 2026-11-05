# 乱数射撃を共通戦闘実行器へ接続

`coordinate-sampled-battle` は、決定的な共通数値規約の着弾点producerを既存のresident武器実行器へ接続したprivate profile。CUDA／Metalは同じSlang、入力、native比較器を使う。現在の受付はbuff定義を伴う物理射撃。非buff効果・親参照量・全元定義の認定・公開GPU受付は未完了。

## 実行経路

既存のshot captureから各ペレットの着弾点→front／core／reach→criticalを順に抽選し、個別の整数damageを保存する。射撃中のbuff通知で、同じshotのdamage／spread snapshotを再照会しない。autoのペレット通知と、chargeのteam→bullet消費→critical→core通知順序を保持する。muzzleごとにcore平均を作り、`not_core` 条件へ渡す。追加の貫通packetは本体のcritical判定を再利用する。

物理／critical／条件抽選のMT状態は、boss対象選択のMT状態と別領域に保持する。同じ初期seedでも消費列を混ぜない。`prob:` は0%／100%でも抽選し、`not_core` は0<p<1のときだけ抽選する正本の規約を使う。期待値モードの条件累積器は変更せず、専用入口の条件分岐で切り替える。

領域は期待値専用の積分scratchを再利用する。個別保存は1024×12 word、共通shot metadataは768 word、永続MTは632 word。全127対象のslot／kind／generationをsnapshotする。Runtime stride138952 byte、入力109528／出力1507328 wordを維持し、Runtimeと出力の追加容量は0。共通のBODY／ADD receiptとPART／INTERRUPT着弾処理を使い、既存のgroup begin／collect／sealも再利用する。今回のgroup owner実例の認定は含めない。

## 検証

最終CPU18検査、制御416検査（Windows専用1件skip）、旧mixedの9検査と、full packageの正本20契約が成功。full3099→compact1755の全残存record／byteを保持した。

最終23入力（共通CPU20／拒否3）はM5 Metalの保存readbackをGPU禁止replayで再比較し、独立sealした。20ケースで1256ペレット／1397packet／5498 MT word、全物理MT状態と消費数、実packetの対象・順序・量、battle・critical／core／team通知を照合する。GPU計算0.448525秒、修正版初回PSO91.909787秒。

元の11実戦に加え、critical／core／pellet通知で更新されるbuffのsnapshot、muzzleごとの部分core確率、`prob:0／50／100`、127対象、1024ペレットを含む。1024ペレットは既存の受付に従いbase64ペレット×8 muzzleに `pellet_count_fixed=128` を適用し、容量を縮めていない。RNG無効・未接続random skill・非有限core距離を拒否する。非有限core距離はcriticalの追加抽選前に停止する。

初版11入力も実GPU一致・独立seal。拡張版では23中22入力一致の原本を保存し、残1件の比較器だけを修正した。計算本体の差ではなく、1024ペレットのteam履歴が既存roster上限へ達したことが原因だった。共通writerは先頭1024件を保持し、その後の1024件の省略数を記録する。新しい比較viewは保存件数・省略数・予約領域を正本と厳密に検査し、元readbackを変更しないコピーを旧decoderへ渡す。保存prefix、全イベント総数、全battle状態、全critical／core履歴、全packet、全MT状態の比較を維持する。省略されたteam個別履歴の後半を完全観測したとは主張しない。

GPU dispatch計2回／同claim retry0／修正版のGPU再計算0。旧11入力・元nativeの全実データと全66,322,432 byte rawを保持。追加のnative抽選ledgerとscope文言の変更は観測metadataとして明示し、古いnative proofを付け替えない。旧8系統の生成CUDA／MSLは各2版で全byte一致し、旧GPU再実行0。old goldenのsource hashを新sourceへ書き換えない。厳密なsource逆変換は未知変更を拒否する。

初回sealはROOT側のsource更新を検出して拒否された。固定パッケージ自身から別出力へCPU監査し、旧11の独立sealを保持した。replay初回も追加test rootによる旧compact package不整合を拒否した。追加2検査を既存bank検査ファイルへ統合し、projection guardを変更せず新packageでreplayした。失敗・claim・原本はすべて保存する。

現在のWindows CUDA計算／CUDA cache hitは未取得。新Windows依頼は0。generation cache・pipeline cache・コンパイラは既存の共通CLI経路を使い、cache key・normalizer・binary64／pow正本を緩和していない。

## 共通CLIと次の作業

```sh
python scripts/nikke_gpu.py package --suite coordinate-sampled-battle --compact --out /tmp/new-sampled.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-sampled.zip --dest /tmp/new-sampled
cd /tmp/new-sampled
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-sampled-cpu
```

`reference --suite coordinate-sampled-battle-common` はfull checkout／full packageから実CPU正本20契約だけを実行する。nativeの実uniform呼び出しと実sample点を受動記録し、独立CPython RNGで全列と最終状態を確認する。GPU／packingは0。既存のexpected observerの規約は変更しない。

次は非buff効果（武器変更・heal・damage／queue）の乱数対応、親参照量の正確な整数合計÷muzzleの数値設計、sampled group owner世界、全キャラ元定義の認定を進める。受付kindの制限と親参照量の拒否は明示したまま拡張する。全キャラ0／20 model gap／UI CPU／public GPU closed／full goal falseを維持する。

証拠の一覧とhashは `research/coordinate-sampled-battle-v1-evidence/inventory.json`、集約は `research/portable-coordinate-sampled-battle-checkpoint.json`。
