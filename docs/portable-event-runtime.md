# 共通の状態・イベント実行器とMetal接続

## 接続済みの経路

`POST /api/portable-events` → `engine_worker.dispatch(evaluate_portable_events)` → `portable_runtime` → 共通Slang → Metal／CUDAアダプター、という外部イベント入力の経路を追加しました。Apple M5でHTTPから実Metal実行・読み戻しまで確認しています。CPUで計算した状態や発射時刻は渡しません。

これは通常画面の180秒自律戦闘、武器／バースト運用、全キャラ対応の接続ではありません。通常画面の詳細計算は引き続きCPUを使用します。APIは対応する効果定義と外部から与えられる刺激を実行する開発用の入口です。`application_event_runtime_connected: true` と `autonomous_battle_connected: false` を別々に返します。

実際の状態更新と計算は `gpu/event_runtime.slang`、数値は `binary64.slang` と `core_probability.slang` に一度だけ書きます。Metal／CUDAのソースを同じSlangから生成します。`app/portable_backend.py` は生成・起動・転送・読み戻しだけを担当し、CPUフォールバックはありません。並行リクエストの生成物は一時ファイルからatomic renameで公開し、入力・出力ファイルはリクエストごとに分けます。

効果の分類・ID・イベント記述・強制スキルの選択は、既存の `detail_gpu.compile_effects` と `effect_spec.py` を再利用します。Mac用のキャラ名分岐や効果定義のコピーは追加していません。旧CUDA本体は比較用に維持し、本体全体の切替はまだ行いません。

## 現在受け付ける範囲

- 5人の異なるキャラ、最大32効果、最大64外部コマンド。時刻は有限の0〜180秒で単調非減少。
- 自分／味方全体への攻撃割合、クリティカル率、クリティカルダメージのバフ。
- 本体1対象への係数ダメージ、周期ダメージ、周期自動攻撃。
- 同じ発動者の名前指定解除と、既存コンパイラーの選択マスクによるスキル強制実行。
- 条件なし・1種類のbattle_start、on_attack、hit_count、名前付きhit_count通知。閾値ごとの剰余カウントとmax_trigger。
- 外部入力の通常命中。係数と静的な射程／コア比率を入力し、GPUで命中ダメージを算出してhit_countを同期通知する。on_attackが必要な刺激では呼出側が別の外部通知を与える。自動射撃時刻の計算ではない。

未移植のHP効果、敵・味方の動的対象選択、条件、複数タイミング、同名の複数キャリア定義、召喚／部位／シールド、通常射撃の全通知等は入力時に拒否します。効果を黙って無視する受付はありません。全キャラ受付数は増やしていません。

## 状態とイベントの規約

通知は最大32段の明示スタックで、親の探索位置を確定してから子を実行します。子通知が完了するまで親は再開しません。1回のdispatchは最大4,096ステップ、ダメージ発動記録は最大128件です。上限超過は結果の切り詰めではなくエラーです。

各タイマーパスの先頭で登録順とepochを捕捉します。実行直前にも生存とepochを確認します。DOTの再付与は位相を維持し、自動攻撃・解除後の再生成はepochを更新します。次回期限は子通知より前に加算するため、子の再登録を親が後から上書きしません。damage→期限切れ→instantの順序と、即時／遅延初回の終了境界を既存の時計規約から移しています。

時刻・累積・補償和も共通binary64を使います。通常命中はクランプ済みのコア確率、既存と同じ順序の各binary64演算、int64最近接・偶数丸め、最低1ダメージを経由します。係数スキル・DOTはコア確率を適用しません。負のゼロのdurationを永続とは判定しません。

外部wireはlittle-endianのuint32列で、binary64は下位／上位の2語です。ホストからSlang内部の構造体を直接コピーしないので、Metal／CUDAの構造体paddingに依存しません。`portable_specs.py` が幅・上限・offsetを定義し、`portable_schema.slang` を生成します。入力梱包時に生成物の一致を確認し、GPU出力の次回期限・epoch・登録順・通知時刻・合計を読み戻します。

## 検証と再実行

```sh
.venv/bin/python -m pip install -r requirements-validation.txt
.venv/bin/python scripts/verify-portable-numeric.py --backend metal
.venv/bin/python scripts/verify-portable-events.py --backend metal
# 別ターミナルで ./Start-NikkeTools.command を起動しておく
.venv/bin/python scripts/verify-portable-api.py --backend metal
.venv/bin/python -m unittest discover -s tests -p 'test_portable*.py'
```

数値34,874ケースがMPFR／有理数等の独立期待値とbit一致しました。状態・イベントは既存の `timer_registry_cases.py` の8ケースをそのまま利用し、手書きの累積ダメージと一致。CPUの発動順はGPU実行後に独立して取得し、追加の回帰比較だけに使います。新しい共通fixtureには、通常命中のpow→丸め→同期子バフ、1.5／2.5の偶数丸め、負のゼロ、最終ダメージ丸めの前／一致／後、味方全体と発動者の分離、スタック上限の8ケースを一度だけ記述しています。合計16ケースがApple M5で成功しました。

さらに強制スキルの循環がスタック上限エラー1、ダメージのint64超過が数値エラー16になることを実GPUで確認しました。HTTPの対応入力は200、未移植効果は400を確認しています。記録は `research/portable-events-metal.json`、`portable-api-metal.json`、`portable-numeric-metal.json` です。これらは本体全体の性能測定ではありません。

CUDAでも同じ検証コマンドの `--backend cuda` を使い、入力・期待値・比較・実行器は変更しません。Windowsアダプターは固定Slangが生成したCUDAをNVRTCでコンパイルし、Driver APIで一回だけ実行します。SlangのStructuredBuffer用constant領域は実際のシンボルサイズを照合してから書き込みます。出力初期化もMetalと共通のゼロ規約です。

今回Windows PCは使用しておらず、CUDAのNVRTCコンパイル／GPU実行は未確認です。CodexのWindows接続は確認済みです。Windows側チャットへの送信が承認されました。短い入力検証だけを実施し、長時間の負荷測定・常時テスト・本体のフルビルドは行いません。必要な初回候補は次の2コマンドです。

```sh
python scripts/verify-portable-numeric.py --backend cuda --random-count 0 --report-suffix short
python scripts/verify-portable-events.py --backend cuda --short
```

## 次の接続

全キャラの自律戦闘へ進むには、実行器へ武器・バーストの状態機械、対象世代を伴う敵世界、HP／回復／シールド、残りの効果・条件を順に移す必要があります。現在のAPIでは実部隊の通常計算をMetal対応済みとして受け付けません。対応範囲を広げるたびに既存の仕様ケースを同じ入力へ接続し、未対応を拒否する境界も残します。
