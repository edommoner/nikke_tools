# 決定的な着弾確率とGPU内の形状準備

共通の形状・円弧を半径方向のGauss–Legendre積分へ接続し、前後遮蔽を含む`front`、growによる`reach`、`core_open`、`core_under`を実装した。sealed `coordinate-landing`40入力（共通CPU26／拒否14）はM5 Metalの全word一致と独立sealに成功した。元のCPU正本は変更しておらず、新しい共通数値profileの参照結果である。resident戦闘の物理packet callerへは未接続。

## 共通powと積分定数

旧`coreProbability`は指数2.55専用なので、逆指数にも使える`coordinate-unit-power-v1`を追加した。既存のQ128区間演算と同じ演算本体から可変指数版を生成し、旧source SHAを固定している。対象は有限の`0<=x<=1`、binary64指数`2^-64<=y<=2^16`。指数の全bitをQ128へ正確に格納し、最大指数でも収まる二分探索幅を使う。上下限が同じbinary64へ丸まる場合だけ返し、未確定は拒否する。一般の全域powや全入力での無拒否は主張しない。

`coordinate-power`909入力（共通CPU898／拒否11）がMetal一致・独立seal。独立MPFR256の下向き／上向き比較2,434入力も0 ULPだった。旧`core_probability.slang`・binary64を変更していない。

GL10のnode/weightはDecimal160桁のNewton法で作成し、最終根で導関数を再計算してbinary64へ固定する。CPU／Slangを同じ定義から生成し、host cosによる初期化に依存しない。有理数のLegendre多項式で隣接floatの根の挟み込みを検査し、19次までの全単項式の積分誤差を1e-15未満へ確認した。

```sh
python scripts/nikke_gpu.py numeric-audit --profile coordinate-unit-power-v1 --samples 2048 --out /tmp/new-power-audit.json
python scripts/nikke_gpu.py package --suite coordinate-landing --compact --out /tmp/new-landing.zip
```

## 計算順と保持する出力

対象の距離によるnear選択、中心coreだけの直接pow、通常・grow付き区切り半径のpow変換、分割幅1e-15の条件、各区間の10点積分、前から順の被覆の差と和、最終clipを保持した。growは積分分割自体も変えるので、front確率も微小に変わり得る。これを同一値へ強制しない。

共通sceneの容量から127対象＋core行を導出し、分割点容量は`127*(16+24)+16+2=5098`、区間容量は1024を確保する。全分割点と全確率、未使用word、GPUで準備した各形状の24wordもCPU参照と比較する。入力2064wordは位置・寸法・角度・照準・radius/grow/kだけで、CPUの確率や戦闘traceを詰めない。出力13796word。kは逆指数もpowのdomainへ収まる`2^-16..2^16`とし、非有限の中間値・容量超過・未確定の区間丸めは拒否する。

CPU参照は新profileとして分離し、旧正本は保持する。26幾何ケースでは旧CPU正本との確率差を絶対1e-12未満へ検査した。これはhost間のbit一致や真の積分への全域誤差保証ではない。GPUの合格判定は共通CPU参照との全word一致で、許容誤差を使わない。

## 容量を保ったスタック修正と最適化

初版はMetal pipeline作成時にstack space超過で失敗し、kernel実行0。失敗package／claim／診断を保存した。分割点を既存の出力arenaへ置き、区間の差とmeasureを参照渡しへ特殊化して、同じ容量で実証した。

その版はGPU17.129972秒だった。次に回転・局所座標・頂点距離をGPU内で一度だけ準備し、各積分点で再利用した。既存の交差・shiftも同じ演算本体から参照渡し版を生成し、active prefixだけを移した。元の1,715,840byteを新出力各行のprefixとして全byte保持し、GPUで作った準備データも新しく照合・独立sealした。

同じ40入力の単一測定対でGPU0.423690秒（約40.4倍）、shared execute全体18.813→2.167秒。これはこのprobeの測定で、全戦闘の速度比ではない。新規kernelはpow1＋landing2、pipeline失敗1、同じclaimの再試行0。準備のみのv3 packageは実行していない。

最終CPU17件、関連・制御462件（Windows専用1skip）成功。full2969→compact1636で全残存record・byte・golden一致。旧主要7suiteのGPU閉包と保護7ファイルは不変で再GPU実行0。予備容量検査の停止後、終了済みraw 4,419,747,840byteを4KiB単位で疎化し1,096,093,696byte回収。全SHA／byte／inodeを検証し、raw削除0。

## 次の接続とWindows

次はこの確率から物理pelletのbody/front/reach packetを作り、共通resident実行器のdamage・通知・吸血へ接続する。sampling RNG、manual aim、cache key丸め、元の全キャラ定義・公開受付は未完了。全キャラ認証0、20分類のgap、UI CPU・目標未達を保持する。

新しいCUDA実機結果は未取得。既存Windowsチャットの依頼送信APIはactive turn ID不在で拒否され、待機中のjobとは扱わない。UI送信の可否も確認したが、Computer UseはCodexアプリを安全制約で利用できず、代替のUI自動操作は試していない。Windowsの新しい実行依頼0・GPU0。

詳細は`research/portable-coordinate-landing-v1-checkpoint.json`と`research/coordinate-landing-v1-evidence/`。rawはローカルcaptureへ保持し、GitHubへ送らない。

ユーザーの「もう一度試せますか？」を受け、idle/revision78を再確認して固定07e1d178のlanding40依頼を1回送信したが、同じactive turn IDエラーで拒否された。計算の再実行は依頼していない。送信を開始するにはWindows既存チャットを人が1通のメッセージで開始する必要がある。記録は`windows-message-retry.json`。Macで再現したWindows用package IDは`9856b8681e48c72aa3b9451b71a2401c174a147dcefe8b94535e4304d3cdf6b4`。
