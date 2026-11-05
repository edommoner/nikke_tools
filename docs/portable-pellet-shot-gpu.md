# 1射内の散弾命中数を共通GPUへ接続

`pellet_hit_in_shot:N` をCUDA／Metal共通Slangへ接続しました。正本CPU、既存CUDA、
binary64／整数変換／pow、normalizerを変更せず、Runtimeの追加fieldもありません。
原文別の静的IDとsigned32閾値を既存8word descriptorへ格納し、GPUで実際の射数を判定します。
CPUの計算結果をGPU入力にしていません。Runtime strideは138952、CUDA定数は48Bです。

## 実装と契約

- 原文別IDを所有者ごとに割り当て、数値→原文の順で通知します。`5`／`05`／`+5`／空白／Unicode数字を区別します。IDは静的な文字列identityで、正本の戦闘状態ではありません。
- hostとGPUの両方でsigned32範囲を検査。GPUはmode、reserved payload、IDの範囲・連続性、同じIDの閾値一致、数値順も検査します。
- 正本で有効な0・負の閾値は、既存CUDAコンパイラへ渡す静的中間表現だけ1へ変換し、portable descriptorへ元の値を復元します。正本と既存CUDAのファイルは変更していません。
- auto／auto_warmupの全pellet callbackが終わった後、gauge計算／on_attack／銃口hit_countより前に通知します。発射時に確定したpellet×muzzlesを使用し、途中の散弾数変更で当該射を数え直しません。chargeでは通知しません。
- 同じ原文を一度だけ通知し、効果内の重複descriptorによる複数発動は共通dispatcherの既存multiplicityへ委譲します。条件、発動上限、期限、対象は既存処理を再利用します。
- 射手別の既存quantityMask bitで未使用の射手を即returnし、旧ケースで毎射の全definition走査を追加しません。

旧監査fixtureのhashは変更せず、4つのhookと新helperの完全一致を別ledgerへ固定しました。
definition-viewの入口でこのdeltaだけを元へ戻してから旧HP／武器／物理監査を実行します。
standalone監査にも同じ層を接続し、hook除去・並び変更・範囲拡大・数値変更の故障注入を拒否します。

## 検証記録

共通CLIの入口は `pellet-shot`、`pellet-shot-rosters`、`pellet-shot-retention` です。
正本CPU21契約、Metal36入力（正例21／拒否15）、実キャラ全定義3秒／30秒2入力、
旧1050入力（正例847／拒否203）を同じ116-source本体で実行しました。
合計1088入力（正例870／拒否218）のnative比較が一致しています。
CPU回帰61群362検査は88.802秒で成功。前回79秒に新検査分が加わるため当該CPU枠だけ120秒とし、
GPU実行枠・旧検査群・比較項目は縮小していません。3検証とも独立seal済み。旧1050の全input/native/output entriesとraw3,303,014,400Bを全byte保持しました。
完了記録は `research/portable-pellet-shot-gpu-checkpoint.json` です。最終sealed packageのCPU62検査と
CPU専用reference21契約も成功し、GPU claimは消費していません。前段CPU20契約のnative／trace指紋も保持しました。

MetalのGPU時間は主36が0.044465秒、実2が1.670554秒、旧1050が10.649943秒です。
最初の生成はSlang2回、その後3検証は生成cache必須・追加Slang0回。
commands入口も同じソースからCUDA／Metalの両生成をCPUで確認しました。
これは実NVRTC cache hit、CUDA compile／link／battleの証明ではありません。

実フリバティ：アンカインドメイドで1射10発の閾値通知を3秒5回／30秒43回、
正のreload speed照会を433回／4133回、最大20.88%として観測しました。
追加buff照会0で、元のnative指紋を保持。物理履歴は85／770件、省略0です。
旧キロ／レム／ギロチンの既存履歴省略は保持したままで、解消したという意味ではありません。

初回v1のcharge対照は、fixtureが引き継いだ `min_cycle=10` と正本入力の不一致で
CPU2射／GPU1射となりました。原失敗package・claim・raw・診断を保持し、正本の0.1秒へ
テスト入力を修正した別v2で全件成功しました。GPU source再変更・同一claimの再実行は0です。
独立sealの最初の開始が比較完了より早かったCPU-only失敗もあり、実行完了を確認してから監査しています。

静的準備は224/266（base164/203）、未対応分類71です。packingはGPU認定ではありません。
全キャラ認定0／通常UI CPU／全ゴール未達を維持します。Windowsの追加照会・native・compile・GPUは0。
7プロセス終了は原因unknown、環境保全false、サービス未識別で、新規検証停止を継続します。

次は正本consumerを確認済みの `squad_ammo_consume_as` の通知数・装弾非消費・小数／負値・
再帰／発動上限のCPU契約を優先します。projectile／shield系は正本consumer未確認のまま受付しません。
