# 味方のバースト使用通知を共通実行器へ接続

`event:ally_burst_cast`（canonical event42）を、成功した各バースト使用の直後にCUDA／Metal共通Slangから通知します。使用者本人の`burst_cast`処理が終わった後、使用者を含む5人へ編成順に通知し、通常のowner条件・対象選択・発動上限・戦闘不能抑止を共有DFSに委ねます。再突入でも通知します。段階への進入、使用待ち、フルバースト開始そのものを使用通知に置き換えません。別の`stage-specific squad_burst_cast:1..3`（event41）は今回もホストで拒否します。

CPU正本の`BurstController._cast`と`BuffManager._notify`を確認し、入力・観測・契約を分離しました。`reference --suite ally-burst`はpacking／GPUを禁止して15契約を実行します。通知・instant実行のprofile観測は追加のbuff照会を行わず、既存の全戦闘フィールドとskill traceを保持します。使用者／非使用者、自己／全員対象、発動上限、本人の使用効果が先に反映される順序、編成順、使用済み条件、不成立条件、戦闘不能、通常／通知由来の再突入、使用なし、重複descriptorを含みます。重複timingはCPUの通知indexに重複登録されるため2回発動し、既存共通実行器のmultiplicity処理も一致しました。

共通CLIのsealed suite `ally-burst`は16入力（native15／拒否1）、`ally-burst-rosters`はルピー：ウィンターショッパーの全定義を含む実編成3秒／30秒の2入力です。Apple M5の実Metalで全件一致し、GPU禁止の独立監査からsealしました。新実編成の物理履歴は49／471件、省略0です。保存readbackを再度CPUでdecodeし、30秒では「ショッピング」が全5人対象・4stack・activeとなる実発火も確認しました（3秒では当該carrierなし）。キャラ全体のあらゆる条件を網羅した認定ではありません。

同じ最終sourceで既存849入力、ナユタ／レムの実編成4入力、部位・阻止部位63入力も全件一致・独立sealしました。旧916入力のinput／native／output entriesと、出力2,881,486,848バイトは全バイト一致です。旧レム30秒の物理履歴55件省略など、既存の履歴容量制約は保持します。Runtimeのfield追加0・stride138952、CUDA定数48バイト。通知定義がない場合は追加dispatchを行いません。過去のsource guardは書き換えず、combat／admissionの2ファイルだけを有限の逆変換ledgerで旧SHAへ照合し、それ以外の変更を拒否します。

SlangのCUDA／Metal生成結果は既存キャッシュから再利用し、成功した5つのMetal検証は各Slang呼び出し0回です。full114／commands115 source certificateを実証と両生成に基づいて更新しました。CUDA compiler／link／実戦闘の成立を示す証明ではありません。Windowsの追加GPU・コンパイル・native戦闘は0、既存7プロセス終了の原因不明／環境保全falseを維持し、新規検証を止めています。

最初の14入力の試行はsandbox内で`No Metal device`となり、readbackなしで失敗しました。元package・capture・消費済みclaimを保存しています。その後、条件不成立・重複descriptorを追加した別packageを、実GPUにアクセス可能な権限で1回実行しました。CPU観測器の変数名修正、重複descriptorの当初の誤った単発想定、source-only生成の手動呼び出し修正もcheckpointへ記録しました。比較器・CPU正本・数値設計・strict normalizerの変更はありません。

静的packingは219/266（base159/203）、未対応分類は76。これをGPU対応率とは扱いません。通常UIはCPU、全キャラGPU認定0、最終ゴール未達です。次は正本consumerのある武器変更`max_ammo_scaling_ref`について、Noneの既定1／ゼロ容量／状態snapshot／reloadでの再取得／maxAmmoBuffの扱いを契約化してから共通化します。未確認consumerを持つprojectile／shield係数を無効果で受付しません。

実行例（Pythonは既存venv、出力先は新規パス）:

```sh
python scripts/nikke_gpu.py reference --suite ally-burst --out /tmp/ally-burst-reference.json
python scripts/nikke_gpu.py package --suite ally-burst --out /tmp/ally-burst.zip
python scripts/nikke_gpu.py unpack --archive /tmp/ally-burst.zip --dest /tmp/ally-burst
```

証拠の位置・hash・測定値・失敗と制限は`research/portable-ally-burst-checkpoint.json`に集約しました。
