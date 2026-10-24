# 座標物理の蓄積ダメージ放出

共通resident実行器の蓄積放出を座標物理profileへ接続した。M5 Metalで新`coordinate-accum-emission`84入力（共通CPU78／拒否6）が全word一致・保存rawから独立seal。旧31の全input/native/output entryを保持した。全78worldの観測は622論理pellet／1845着弾packet／46蓄積放出。全キャラ認証0／モデルgap20／公開GPU閉鎖／UI CPUは維持し、全体目標は未達。

## 実装

既存`releaseDamageAccum`のtake→split照会→整数化→queueという計算と寿命管理をそのまま使い、`PORTABLE_COORDINATE_PHYSICAL`時だけbody-only座標receiptを初期化する。receipt depthはcast snapshot indexより1大きいため、depth==0を拒否してdepth-1へ保存する。容量・row・magic・ゼロ選択を共通helperで検査し、既存landing queueと現在世代解決へ渡す。CUDA／Metalに別の計算本体やeffect定義を追加していない。

比較器も前回のworld decoder・完全packet trace・末尾ゼロ・蓄積final pool/archive比較を再利用する。親参照量を必要とする旧full-charge入力には従来どおりbank bitsを検査する。蓄積だけの新入力はその消費者を持たず、bank値の一致を要求しない。入力packingはliteral shapesと効果・寿命だけを含み、CPU計算量・確率・packetを供給しない。passive蓄積observerとpacket observerはネストし、失敗時もprofile／notify／HitEventを復元する。

## 実証範囲

既存蓄積52worldのうち49を座標化し、完全遮蔽・interrupt・部位破壊・2射手の4worldを加えた。残る3worldはADD共有2件と敵攻撃によるdown1件で、現coordinate scene schemaが受付外。原suiteは保持し、座標対応済みとは扱わない。

期限切れ、active/archiveの消費一回、refresh、名前付き削除、同名pool、別owner、受ダメ蓄積、同時full通知、rateの省略と明示0、named係数、順序付き大数相殺、cap snapshot、整数切捨て、散弾×2銃口、放出が別poolへ入る処理を比較した。例としてdealt900／received4500、baseline50＋named25は675、split25.19は1126、別pool連鎖900→9900、順序付き相殺後9。完全遮蔽は0damage本体を持つが放出なし。

期限.4のpoolは実frame .41666666666666663で失効し、放出の生成・着弾もその時刻。これは前回full-charge子の生成.05→着弾1/15とは別の既存queue順序であり、どちらも正本の時刻を保持する。最初のCPUテストの.4という推測は実観測へ訂正し、正本を変更していない。target着弾の蓄積除外は従来どおりで、ゲーム仕様の正当性は未確認。

## キャッシュと監査

新GPU実行は1回、同claim再試行0。GPUは約.243秒、初回PSO compile91.803秒、bounded shared execute約96秒。Slangはgeneration-onlyで事前作成し、実行時は生成cache必須hit・再コンパイル0。Windows追加依頼0／現CUDA実行とcache hitは未取得。

既存のpaired generatorをimmutable package上で使い、通常81／97のCUDA・MSLが以前の保存物と全byte同一と確認した。旧GPU再実行0、CUDAコンパイル0。normalizerやcache keyを緩めない。raw一致はキャッシュ再利用条件の証拠であり、CUDA計算成功を示さない。

旧81の証明書は新しいprivate分岐を含む現source closureとは異なる。最終control v1で、この旧proofを常に現行とするテストが失敗した。既存のexact source inverseを再利用して履歴全closureを照合し、実際の現sourceを入れたmanifestが変更していない受付gateで拒否される負例を加えた。旧golden／旧証明書を現行へ書き換えていない。新84のsource証明書は別途保存rawを独立監査して作成し、compiler/cache/battle実行成功とは分けている。

## 最終確認と引き継ぎ

修正版immutable final-v2でCPU53件、control416件（Windows専用1skip）とmodel-checkが成功。full3013→compact1704の全残存record／byteが一致、保護7sourceも保持。最初のcontrol失敗と準備時のsource変更guard等は保存し、GPUをやり直していない。metadataとテストの変更後も実証済みGPU source identityは同一。

実行前の空き容量検査が一度止めたため、過去のraw2件と今回rawを全byte／SHA／inode保持で疎化し、計649306112byte回収。raw削除0、容量・入力削減0、実行時1GiB reserve保持。旧失敗rawも内容を残す。

次優先はlive core pattern nodes。その後はGeometry cache keyの丸め、manual aim、sampling RNG、物理group／ADD共有、座標sceneの敵攻撃、全元定義と公開受付。集約は`research/portable-coordinate-accum-emission-checkpoint.json`、保存証拠は`research/coordinate-accum-emission-v1-evidence/`。
