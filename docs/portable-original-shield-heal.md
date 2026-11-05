# 元編成のシールド回復とCPU観測

`coordinate-original-shield`はラプンツェル：ピュアグレイス全73、モリ全72、キロ全74定義を元の5人編成・武器・成長・設定のまま保持する9ケースです。各6秒で、満タン、実被弾による損傷と回復後の再被弾、破壊の3状態を使います。ラプンツェルは公開bodyの`shooting_policy=character`を使い、元のhold操作を保持します。CPUが計算した発射／発火スケジュールをGPU入力へ渡しません。

既存の共通kind27 `shield_heal_pct`をCPU／Slang共通の受付宣言へ接続します。回復は既存シールドの空き容量だけを埋め、新しいシールドや容量を作りません。native observerは実際の`_dispatch_instant`、`heal_shield`呼出し前後の保存状態を読み、対象の再解決やstat再照会を行いません。元row・owner、全最終シールドの対象／stack／activation／期限／容量／現在量、定義別発火数と反復instant timerの位相を読み取ります。無期限は実wireのbinary64 infinityと有限1e30を区別します。従来のbattle／packet／RNG／手動操作／healing比較もすべて実行します。

反復instant効果は登録時には回復せず、次回tickから元の条件を再評価します。ラプンツェルは破壊後の条件不成立、モリは消費によるcarrier終了、キロは破壊後の別定義による再生成を保持します。kind受付だけを全キャラGPU認定として扱いません。

## 観測経路の高速化

CPU基準は複数の`sys.setprofile`観測器を重ねるため、観測対象外のC関数通知も各段へ伝わっていました。`native_python_profile.python_observers_only`は明示opt-in時だけ、Pythonのcall／returnを元の順番で全段へ渡し、C通知の伝播を外側で止めます。計算、Python観測、比較項目、ケース数、期間、180秒上限は保持します。正本のtimeline／BuffManagerや数値実装は変更しません。

外部／不明callback、明示的なC通知consumerは拒否し、例外時にも元profilerを復元します。旧ケースの既定値はFalseです。新しいケースで有効にする前には、そのケースの全native観測が非filter版と一致することを確認してください。C通知を使う新観測器には適用できません。

凍結パッケージの損傷ケースを各1回ずつ比較した結果、ラプンツェル28.490→3.897秒、モリ54.184→5.871秒、キロ71.885→7.069秒で、各全native観測のSHA256は一致しました。これはCPU観測の測定で、GPU速度やCUDA cacheの証明ではありません。観測器ごとのsource SHAと通知数を小さな記録へ保存します。

初版のM5実行はモリ／キロ6ケースが一致、ラプンツェル3ケースはstatus64でした。診断のstage8000／row1は、回復の前に「シールド中」条件付き味方buffのactor-field受付で止まったことを示します。実条件評価は既存`hasProtection`を使います。新入口だけで引数なし・戦闘中の`C_SHIELD`を検証して接続しました。条件を削除したりCPUで結果を固定したものではありません。初版と修正版の全9入力／native指紋は保持しています。旧reload入口は修正版でもCUDA／Metal原生成物を全byte保持し、元sourceへの厳密inverseを追加しました。初版のclaim／raw／失敗記録は残し、同じclaimを再実行しません。

修正版v2はM5 Metalで9ケースすべて一致し、独立fresh監査60.446秒でも全件一致しました。先に一致した6ケースの全42,476,544byteを保持しています。実GPUは計2回（初版失敗1・修正版成功1）、同claim retry0です。修正版はCPU事前比較56.256秒、初回pipeline生成93.108秒、GPU計算1.289189秒でした。

共通CLIにはsealed suiteとして登録済みです。`package --suite coordinate-original-shield --compact --out /tmp/new-shield.zip`から使います。最終パッケージは関連20／共通制御476検査成功（Windows専用1skip）、generation cache必須hit・Slang0でsealed生成物を確認しました。全1971payloadのSHA／checkout全byteと、GPU source・input・native・outputの一致を検査しています。終了済みreaderのrawは全byte／SHA／size／inodeを保持して疎化し、削除0です。

全266の静的inventoryはpacking247、kind理由の拒否10（旧13）です。237をGPU対応キャラ数へ変換しません。現CUDA実行／warm cache、公開GPU・全キャラ認定は未達、通常UIはCPUです。次は元ビスケット／リリのkind30 `cover_revive`を優先候補とします。Windowsへの新規実行依頼0です。
