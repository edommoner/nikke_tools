# 混在consumerの共通GPU検証

照準キャッシュと後段ATKの数値辞書を同時に有効にし、回復共有・部位スキルを組み合わせる6ケースを共通CLIへ追加した。`mixed-query` が通常実行、`mixed-query-diagnostic` が同じ入力の回復診断である。CUDA/Metal別の計算実装やテスト期待値は追加していない。

CPUの固定契約は本人照準・他人照準・照準なし・回復共有・部位・回復共有と部位の組み合わせ。各248/257照会、90/93抽選を観測する。回復を挟むと数値辞書の破棄で乱数消費が変わり、本人照準の3発は7200/7200/7200から7200/6600/6600へ変化する。回復共有後の5人のHPは5600である。この正本挙動をGPU向けに変更していない。

観測器は既存の照準・回復・数値照会観測を合成し、全native結果・全skill trace・`get_buffs`/`has_live_stat`/`random.sample`呼び出し回数が無観測実行と一致することを検査する。乱数状態、cache hit、lazy分類、HP、ダメージ、回復イベント、部位、カメラの故障を契約が拒否する。

## 実証

固定パッケージからMetalで通常6件と診断6件が成功し、独立子プロセスのGPU禁止再監査から両goldenをsealした。CPUは通常4群13検査、診断5群16検査が成功。golden登録後の通常不変packageでもCPU13検査を成功し、GPUの再実行は0。GPU時間はそれぞれ0.050217秒、0.050356秒。通常は生成cache hit・追加Slang0。診断は新しいentryの生成cache missでCUDA/MSLを2回生成した。これはCUDA実行の証拠ではない。

全battle項目・skill trace・最終照準・全抽選順序と最終MT状態を照合した。診断では実際の回復共有呼び出し順を追加比較した。さらに両rawの入力・native指紋と、診断bank `[771072,781320)` word以外の18,628,416 byteが全一致し、診断による計算変化がないことを確認した。再利用用のCPU監査器は `research/verify-mixed-query-diagnostic-neutrality.py`。

通常の122 GPU sourceは前回の1,355入力検証と完全同一であり、全体の再GPU実行は行っていない。共通算術・整数変換・pow・normalizer・出力stride・Runtime容量は不変。今回追加したのは混在ケースと比較経路で、未対応機能の受付を広げる変更ではない。

証拠: `research/portable-mixed-query-metal-evidence.json` と `research/portable-mixed-query-checkpoint.json`。rawと消費済みclaimは/tmpの元captureへ保持し、GitHub共有には含めない。

## 次の未対応

private kind6の物理interrupt着弾橋はCPU試作段階で、正規ActorKindのPROJECTILE=2とは区別し、受付は引き続き閉じている。正本consumerの契約を先に固める。全キャラ認定0、UIはCPU、全目標は未達。

Windowsの追加操作は0。7プロセス終了について、ユーザーはアプリや端末の終了・Codex再接続・Windows再起動を操作していないと回答し、ゲーム・動画利用の可能性を伝えた。利用状況だけから原因を推定しない。原因unknown・環境保全falseを維持し、Windowsでの追加検証は保留する。
