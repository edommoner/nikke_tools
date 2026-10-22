後続の共通GPU接続・Metal実証は [GPU実装記録](portable-manual-swap-gpu.md) を参照。以下の明示拒否・実装候補という説明はCPU契約段階の履歴です。

# 手動モード移行の正本契約

`weapon_mode_swap` の実行経路を調べ、共通CLIに `reference --suite manual-swap`
（24契約）と `reference --suite manual-swap-rosters`（全定義の実編成2契約）を追加しました。
GPUの本体・受付・golden・数値は変更しておらず、これはGPU移植前の比較基準です。

## 確認した正本の処理

`CharState.tick` は現在のweapon_change処理、無限弾薬によるreload取消、過剰装弾の補正の後、
一般のclick／cover操作より前に手動モード条件を確認します。
フラグがtrue、通常reloadとpost-reload待機がともに非正、かつ `manual_swap_ready` がtrueなら、
既存 `_start_reload` を呼び、そのtickの射撃を行わずreturnします。
装弾が満タンでも開始でき、既存のチャージは中断します。

`manual_swap_ready` は当人の `event:full_reload` 通知索引から、weapon_changeかつ
条件が空でない効果を原文順に確認します。成立した最初の効果でtrueを返します。
既にweapon_change状態ならfalseです。ここでは効果の発動上限を検査しません。
リロード完了通知時には通常dispatcherが改めて条件と発動上限を処理します。
そのため、開始時にあった条件が完了前に失効すればモードに入らず、
上限到達後も条件が残れば手動reloadを再度試みます。移植時にこの順序を変えません。

24契約はフラグ有無、別owner、空条件／偽条件／別通知／非weapon効果、条件の遅延成立と失効、
候補の順序、speedとfixed時間、チャージ中断、既にモード中、再突入、発動上限、
cover sequenceとの順序、原武器とchargeモード、重複通知descriptorを含みます。
正本が0秒／負のreload時間で複数フレーム開始を繰り返す挙動も、そのまま記録しています。
ゲーム内の正しさを認定したものではありません。
合計34開始・17完了・主対象139射。時間は固定の丸め値へ置換せず、実際の累積frameで
期限に到達した最初のtickと照合します。

観測器はリテラルのキャラ入力をnative constructorへ渡し、実際に呼ばれたready／条件／tickを読みます。
追加の条件判定・バフ照会・CPU tick・ターゲット解決を行いません。
全24ケースで観測あり／なしの全battle項目、skill trace、get_buffs呼出数が一致しました。
契約の件数・owner・latch・tick・装弾・条件を壊した負例も拒否します。

## 実キャラの自然な経路

シンデレラ：クリスタルウェーブの全定義を保ち、既存の `weapon_mode_swap=True` を指定しました。
3秒では条件が未成立で、ready成功0・弾消費相当効果0・全隊物理履歴112件です。
30秒では約16.483333秒でreadyが1回成立し、原文 `저격 모드 탄 소비 집계` が
値40で8回dispatchされ、全隊物理履歴は1425件です。
観測あり／なしの全native結果と物理traceが一致しています。
このCPU実証により、以前のフラグfalseの非発火対照だけでは見えなかった経路を確認できました。
GPUの自然なSR進入完了を意味しません。

## 静かに指定が落ちる問題の修正

従来の `normalize_static_weapon` はこのフラグをprivateの武器入力へ移さず、
trueでも通常の武器として静的準備できました。
GPU実行器への接続前は、trueまたは不正な型を
`UnsupportedPortable(reason='control', fields=['weapon_mode_swap'])` として明示的に拒否します。
false／省略の既存入力は保持します。正本CPUと既存CUDAのファイルは変更していません。

実APIの `_portable_static_inputs=True` でも、既存prepared入力を後から渡した場合でも拒否を検査します。
通常のCPU戦闘経路はこのprivate静的武器正規化を使わないため、フラグの正本機能を無効にしません。
未対応分類は、この具体的なprogram blockerをconsumer確認済み・26契約のGPU実装候補として案内します。
分類器の `gpu_supported`／`gpu_admission_verified`／`runtime_validation_performed` はfalseです。

## 再実行と次の実装

固定パッケージをfresh展開し、そのCLIから次を実行します。出力は未使用のパスを指定してください。

```sh
python scripts/nikke_gpu.py reference --suite manual-swap --out /tmp/manual-swap-new.json
python scripts/nikke_gpu.py reference --suite manual-swap-rosters --out /tmp/manual-swap-rosters-new.json
```

両コマンドはpackingとGPUを禁止し、入力／source identity、native／trace指紋と原データを保存します。
元出力の上書きは拒否されます。共通GPUのCPU事前検査にも新しい7検査を登録しました。
最終固定packageのCPU検査は9群61件、既存46入力の29 native指紋も一致しました。
分類器・compiler certificate・実入力の別32検査も成功しています。
単独CLI起動の初回にはnative依存の初期化不足があり、失敗記録を保持した別packageで修正確認しました。
完成記録は `research/portable-manual-swap-reference-checkpoint.json` を参照してください。

次はowner別の静的フラグを共通reload adapterへ運び、GPU内で条件付きfull_reload候補を判定して
既存beginReloadへ接続します。正本の並び、再判定とbudgetの境界、mode再突入を保持し、
24契約・実編成・旧1137入力の出力保持をMetalで検証してから受付を開きます。
GPU source／Runtime／binary64／整数変換／pow／normalizerは本段階で変更0。
CUDA cacheの新たな実機証明はなく、既存の両生成cacheを維持しています。
Windows追加操作0、7プロセス終了はunknown・環境保全false・サービス未確認で停止継続。
全キャラ認定0／通常UI CPU／全ゴール未達です。
