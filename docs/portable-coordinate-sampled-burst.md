# 乱数保留バーストの共通実行器

`coordinate-sampled-burst` は、乱数物理射撃・通常damageへ旧B3と `land_in_full_burst` の保留queueを合成するprivate profile。共通Slang、効果IR、CPU正本観測器、比較器をCUDA／Metalで使う。固定89入力（CPU正本83／拒否6）がApple M5 Metalで全一致し、保存出力の独立監査でも成功した。現在ソースのCUDA実行は未確認で、全キャラ認定・公開GPU受付は未完了。

## 二つの保留queue

旧B3は保留entryごとにbuffを一度取得し、hitごとにcriticalを抽選する。全legacy amountを生成してからopt-inの解決と着弾へ進み、named-hit通知を発生しない。旧経路の基礎ATKを保ち、後からcastされたbuffの除外maskを適用する。乱数用の元rowを明示し、HP基準の計算へ置き換えない。

opt-inはcast時のhit countを保持し、full burst entryでbuffと倍率を取得し直す。後からcastされたbuffは除外し、entry時に加わったbuffは適用する。hitごとのcriticalとnamed-hitの子queueは通常damageと同じ実行器を使う。PART／INTERRUPTは本体の抽選を再利用する。両queueの出生順、実計算順、対象generation、全MT状態、実packetと総計を照合する。

各amountを正確なbinary64で保持するため、既存512entry×256hitの全address容量を明示したbankを出力末尾に追加した。入力109528word、Runtime138952byteは不変。出力1507328→1769472word、追加1MiB／入力であり、既存の着弾queueへ容量を押し込まない。これはaddress容量の保持であり、今回の24世界が全entry同時満杯を実行したという意味ではない。batch headerは物理shotで消去されるMETAから分離した。

## 差分と検証

新24世界は単発／多段／重複entry、係数0、critical 0%／100%、前後・entry buff、通常damageとの順序、latched count、parts出生／消滅、貫通／爆発、mixed queue、critical条件の子を含む。拒否3入力を追加し、旧62入力の受付／拒否を変更しない。

最初のMetal実行は87/89一致。legacy-later-buffは1packetだけ750→1500となり、MT状態は一致した。生成CUDA／MSLでは、新helperを跨ぐcallerの除外setterが消え、helper内のdamage queryに渡らなかった。最初のqueryを共通callerのsetter直後に戻し、helperは保存と後続hit再抽選だけにした。もう1件は参照count marker（既存kind4）の受付漏れで、新profileだけに明示受付を追加した。修正前のGPU出力・比較・claimを保存し、新しい固定source/packageで1回実行した。生成コードの正規化や期待値許容は変更しない。

修正版89/89一致、GPU実行0.485997秒、初回Metal PSO92.568059秒、子プロセス97.946240秒。生成cache hitでSlang呼出0、PSOは新sourceの初回miss。実GPU計2／同claim retry0。成功出力をGPU禁止で独立sealし、compiler source証明書も保存した。証明書はCUDAコンパイル成功やcache hitを意味しない。

旧62入力の入力・native fingerprintと旧出力prefix全373817344byteが一致し、追加bankは旧入力で全zero。従来11系統のCUDA／MSL生成ペアも全byte一致した。readback-retainに異なるstrideのprefix照合を追加し、全file／case hash、prefix digest、追加tailのzeroを必須とした。改変・anchor・tailの負例を検査し、旧同strideの検査も保持する。

## 共通CLIと残件

`package --suite coordinate-sampled-burst --compact`、`reference --suite coordinate-sampled-burst-common` を登録した。referenceはpacking／GPU禁止で実CPU24契約を検査するためfull packageで実行する。compactでreferenceを呼んだguard停止も記録し、制限は緩和しない。CPU55検査・制御421検査（Windows専用1件skip）が成功した。全体分類の `coordinate_sampled_bursts` は証拠の有無／現在source一致と未対応項目を分ける。

独立した整数ratio probeは4sourceすべて不変で、以前の14045入力Metal証拠を再利用しGPU再計算しない。保護7sourceとcore probabilityは不変。raw削除0。失敗を含む完了captureの疎化は全byte／SHA／inodeを保ち、receiptを保存する。Windows新依頼0、現在CUDA／CUDA cacheは未確認。

次は乱数戦闘への武器変更・heal、sampled group ownerと混合効果、全キャラ元定義の認定を進める。全キャラ認定0／20model gap／UI CPU／public GPU closed／full goal falseを維持する。記録は `research/portable-coordinate-sampled-burst-checkpoint.json` と `research/coordinate-sampled-burst-v1-evidence/inventory.json`。
