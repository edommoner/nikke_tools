# 武器変更中のキャラ状態とスクワッド操作

`coordinate-squad-mode` は `coordinate-squad`222入力を保持し、mode状態・装填進入・遮蔽方針24worldとversion拒否5入力を追加するprivate入口。入力109792／出力1769856word、Runtime138952byte・247fieldを維持する。実証範囲は固定worldで、全元定義・公開受付・全キャラ認定とは区別する。

CPU正本の `CharState._in_weapon_change` は、mode effectが満了・弾数終了・トグル解除された後も、そのキャラの次tickまで残る。down／stunの早期return時にも残る。新状態は5人分のbooleanとして既存squad出力bankへ保持し、生存・非気絶キャラのtick開始でlogical modeを読み、装填完了のcallbackからmodeへ入る際にも更新する。squadのcover_allと、カメラ調停前のcover/reload方針要求がこの同じbusy判定を使う。キャラtick内でmodeから戻った後、強制focusが所有権を保持していればそのフレームの方針進入は可能である。

復活で使うphysicalModeIndex=-2をmode中の判定へ流用しない。mode中と、baseから倒れて復活した場合を分けたnative witnessで確認する。既存の共通revival handler(kind29)をこのsourceのsampled実行へ接続し、CPU正本は変更しない。

装填完了がweapon_changeを発動した時、CPUはそのまま `_tick_weapon_change` へ入る。そのフレームは有効なcoverを再判定せず、進入待機をその時点から開始する。初版ではt=.31666666666666665のmode射撃と2通知が欠け、t=.41666666666666663のbase射撃だけが残った。修正は共通 `prepareWeaponFrame` でbase→modeのcallback進入を識別し、そのフレームの待機・shot limitとcover判定の順序を合わせる。shot-limit計算は1関数を両進入経路から使用する。

wire v2はsquad headerのversion=2／word5=0x4d535431。CPUはこの固定feature markerだけを追加し、実行時のmode flagやrecipientを入力しない。v1の旧222入力は保持する。出力bank1769808からのword16〜20へ5flag、24〜27へ全pumpの2本の64bit指紋、28へ観測数、29へmarkerを置く。指紋は実tのbinary64低高wordと全5人のflag maskを順序通りに処理する。全pump・最終flag・予約領域を照合し、親のsquad／policy／manual／全戦闘・RNG比較も残す。

同じliteral時刻でも、ボスpatternのdelay判定と操作の厳密時刻判定が異なるtickに達する場合がある。同一tickの復活witnessは実native時刻を確認して構成し、観測した時刻表をGPU入力へ渡さない。

検証は固定package `/tmp/nikke-squad-mode-develop-v1` でCPU125件成功・native209事前照合後にMetal実行し、247中246一致／装填進入1件の通知差分を保存。修正版 `/tmp/nikke-squad-mode-develop-v2` は、旧247全input／native指紋を保持し、4合成worldを追加する。CPU正本・通常のpackingコードは同一で、修正版ではmode／source guardsの8検査を選び、全213 nativeと全251 GPU出力を照合する。旧125検査と元raw・claimを保持する。変更したSlangは新packageで1回検証し、同じclaimは再試行しない。

```sh
python scripts/nikke_gpu.py package --suite coordinate-squad-mode --compact --out /tmp/UNIQUE.zip
python scripts/nikke_gpu.py unpack --archive /tmp/UNIQUE.zip --dest /tmp/UNIQUE
```

251入力がM5 Metal全件一致・独立seal済みで、通常入口へ切り替えた。残件はburst delay／wait_own_cooldown／patternと次FB予測、modeと個別sequence／post-delay／healing storage・actorの追加合成、元定義・CUDA実機・全キャラ認定。旧profileの通過から未検証の組合せを認定しない。

独立監査は`seal --compiler-certificate`を使い、同じfresh監査から戦闘goldenと専用full-source証明を作成した。旧222全1,571,632,128byte／input・nativeと、元失敗以外の246全1,741,538,304byteを保持。装填進入1件だけの出力変化を明示し、元失敗を成功へ書き換えていない。GPUは新sourceごと各1回の計2回、同claim retry0。CUDA実機・cache性能・全元定義の認定は未完了。復旧点は `research/portable-coordinate-squad-mode-checkpoint.json`。
