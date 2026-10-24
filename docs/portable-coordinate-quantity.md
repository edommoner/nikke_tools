# 座標物理の整数参照量とキャッシュ保持

共通resident実行器のfull-charge通知へ、実際に展開する物理packetの参照量を接続した。CUDA／Metalは同じSlang・定義・native比較器を使う。M5 Metalで`packet-integer`305入力（正例294／拒否11）と`coordinate-quantity`31入力（共通CPU25／拒否6）を全word照合し、保存rawから独立sealした。現在のCUDA実行は未取得。公開GPU受付・UIのCPU方針は変更しておらず、全キャラ認証0／モデルgap20／全体目標は未達。

## 整数設計と実行器

`gpu/packet_integer_sum.slang`のuint64二語で128bit整数を保持する。非負・有限・整数・signed63bit変換可能な各packetを検査し、加算→pellet数の乗算→binary64 nearest/evenの順に一度だけ丸める。128項×signed63bit×1024でも80bit以内。実武器のpellet受付上限は64で、1024は独立数値probeの境界。先に浮動小数へ丸めてから乗算する方式は採らない。既存binary64・pow・整数変換本体は変更していない。

銃口数ぶん均一に複製したpacket総量を銃口数で割る正本の値は、template整数和×pellet数として計算できる。body・parts・private interruptの和をowner別bank+14へ保存し、full-charge通知のFrame.notifyDealtから読む。部位貫通2000＋3000＋3000なら親8000、25%固定子2000、総量10000。直接固定子にはゼロ初期化したbody-only座標receiptを渡し、共通着弾queueと現在世代解決を使う。

初版29入力では、追加したdrainが子の着弾を生成時刻.05へ早め、5件のskill traceが失敗した。正本は生成.05、着弾1/15。追加drainを取り除いて既存の次frame処理を保持し、時刻・順序・owner・世代・未使用trace末尾も比較した。失敗capture・source・rawを保存し、正本や旧goldenの期待値を変更して回避していない。

31入力は旧23の全input/native/output entryを保持する。追加8件は貫通参照量、7pellet×2銃口、大整数、interrupt、0係数、正の小数から0への切捨て、owner4、2射手。25共通CPU worldは87論理pellet／214着弾packet／11full-charge通知。passive observerは既存profileを連鎖し、例外時もprofileとnotifyを復元する。CPU-only再計算した全native SHAもsealと一致した。

## 実際に省けた処理

散布式を同じ生成statementからmacro展開し、通常経路には従来の関数本体を保つ。旧81／97の生成CUDAとMSLがpre132保存物と全byte一致した。normalizerの除外・キャッシュkeyの緩和・期待値の自動追従は追加していない。厳密なCUDAキャッシュのsource再利用条件を復元したが、Windowsでの実cache hitや計算成功を意味しない。

旧81／97は現sourceで各1回Metal実行し、独立seal、全input/native/output entry保持を確認。生成cacheとpipeline cacheを必須hitにしてSlang再生成を省いた。shared executeは81が15.199秒、97が3.914秒。31の初回新PSOはshared execute96.244秒で、主な待ち時間はpipelineコンパイル。詳細はcheckpointのtimingとcaptureのtransportを参照。

## 蓄積の分類

`reference --suite coordinate-accumulation-policy`の3worldでCPU正本の実consumerを観測した。target-onlyはpool0、本体2000＋部位ダメージがある場合もcollectは本体2000の1回だけ。正本のtarget着弾consumerは蓄積callbackを持たない。そのため「追加のpart蓄積がGPU欠落」という前回の分類を`native_reference_exclusion`へ訂正した。ゲーム仕様としての正しさは未確認で、GPU対応認証は増やさない。座標profileで蓄積ダメージを放出するbody-only receipt接続は依然未完了で、次の優先項目。

## 検査・保存・次作業

最終のimmutable compact packageでCPU37件、制御416件（Windows専用1skip）、model-checkを通過。full3006→compact1683の全残存recordとbyteが一致し、保護7sourceも一致。新GPU呼出5回（成功4／初版比較失敗1）、同claim再試行0。旧97はstorage guardがGPU前・claim作成前に止めたため、証拠を全byte／SHA／inode保持で疎化してから新captureで1回実行した。4rawの回収1086881792byte、raw削除0、入力数・容量削減0。

Windows API再試行は`Cannot steer conversation ... without an active turn id`で拒否。接続先idleを確認したが新しい実行開始は確認できず、Windows GPU負荷は追加していない。次は蓄積放出、live core、丸めGeometry cache key、manual aim、RNG、group混在、全元定義の受付を進める。

集約は`research/portable-coordinate-quantity-checkpoint.json`、保存結果・失敗・seal・storage・旧byte保持は`research/coordinate-quantity-v1-evidence/`。raw／compiler配布物／個人設定はGitHub共有対象に含めない。
