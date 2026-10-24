# 元レイ編成のskill盾接続：native契約

共通CLI `reference --suite destructible-skill-rosters`へ、元レイ7スキル＋装備・ミランダ・ドラー・N102・メアリーを含む全73定義の4契約を追加した。HP盾、hit盾、盾破壊後のbody fallback、発動前の短時間をactual native simulateで実行する。新しいGPU入口・GPU対応認定はまだない。

## 元の対象名を保つ理由

従来の盾skill入口はplainなbossスキルだけを扱っていた。全体/近距離/順位指定をbossへ置き換えるだけでは、対象名に依存するburst family flagを失う。ドラーの元「R&D 샷」は`enemies_top_def:1`なので単体burstであり、bossに書き換えると`is_single_burst`がfalseになる。

`typed_battle`の新しい明示`skill_shields=True`では元のeffect辞書・対象名をそのまま既存handlerへ渡す。既存handlerがskill level、live named倍率、burst/crit/family、HitEvent、named hit、gaugeを作り、現在の盾選択/量/receipt/counterがそのpacketを受ける。独自のskillダメージ式・再通知・発射時計は作らない。元のeffect/sourceの条件を削らない。

新policyはmodifier_modelとboss ownerを必須とし、単一boss・directな1hitのdamage/burst_damageに限定する。既存`damage_plan`で元selectorを検査し、既存係数契約でtable/levelを検査する。multi-hit、deferred/DoT、HP換算、normal formula、random/current target、part/interrupt/座標/ADD、post-landing吸血/蓄積を今回の対応と数えない。未知field・不正値・条件は拒否する。従来のkeyword既定値はfalseで、旧plain skill・武器のみの処理は維持する。

native観測器は現在の実編成観測器を共用し、opt-in時だけskill source indexと実際のfamily flagを記録する。元のcalcに入ったbuff辞書・hit_typeと戻り値を読むだけで、get_buffsや対象選択を追加呼出ししない。旧ミサト観測の返り値は同一。エラー時の全native関数・manager/回復method復元も検査する。

## 4ケースの固定値

3秒は0.5秒、30秒は4秒に、元のworld clockで0.3秒だけ盾を生成する。敵の攻撃で味方HPも減らす。実行時のCPUイベント一覧からGPU入力を作る経路はない。今回はそもそも新4ケースのGPU packingを行っていない。

|条件|typed着弾|含まれるskill|盾の残量|
|---|---:|---:|---:|
|3秒・早期HP|17|0|999999549032|
|30秒・HP|38|3|999943001161|
|30秒・hit容量50|38|3|12 credit|
|30秒・HP容量500|1|0|0、以降body|

HP/hitケースでは、元のドラーとレイの3skillを確認した。

|元のskill|時刻|HP盾の解決量|hit盾の診断量|
|---|---:|---:|---:|
|ドラー R&D 샷|4.116666666666657|748299|748299|
|レイ 선두 제압 2|4.133333333333324|4727897|590618|
|レイ 섬멸용 고폭탄 3|4.216666666666657|44161247|7703705|

レイ本人の元盾補正700.5%はHP側factor5へ入り、hit盾では加えずcredit1を消費する。ドラーの解決時点の盾補正は0。ドラーはburst=true/single=true/aoe=false。レイのB3は元定義が`damage`であり、sourceが「スキル3」だからといってburst familyへ変更しない。この区別をliteral contractで固定した。

## 共通CLIと保持確認

```sh
python scripts/nikke_gpu.py reference --suite destructible-skill-rosters --out NEW_REFERENCE.json
```

不変package `39c1188eb05de20d847fcf07fb85c58cd6d38fef7e08d2e5c8a84a490ee4f8f3`をfresh unpackしてreference4が成功した。canonical positive0/model gap4、packing/build/execute0を維持する。既存sealed `destructible-weapon-rosters`のCPU群へ新8検査を加え、CPU32/skip0（12.424秒）・旧native2（1.023秒）も成功した。新reference4は1.996秒だった。

旧ミサト2件の全golden entryと武器141件のinput/native指紋を再検査した。155GPU source・CUDA/Metal両生成・Runtime138952・保護CPU/compiler・binary64・strict normalizerは変わらない。generation必須hit/追加Slang0/GPU0。旧Metal実証を保ち、新レイ4件の実証へ流用しない。

inventory全fieldを前回と比較して完全一致を確認した。全266profile/245packing/base185/残20model gap/順位・全キャラ0/UI CPUを維持する。Windowsの新依頼・観測0。現CUDA実機/cache速度/CUBIN O0・過去7終了cause unknown/環境保全falseは未確認のまま。

## 次のGPU接続

現在の共通`destructible_frame_runtime`とshield entryはdamageRoute=1、plain flagsに限定されている。新契約をGPUへ接続するには、元のroute/countとburst/AoE/single flagを保持し、共通の敵選択・factor sampling・既存Frame continuationを拡張する必要がある。

新しい明示policyで旧HSI1/2/3入力を維持し、未知flagを既存入口で黙って受けない。selectorをbossへ置き換えず、共通selectorで解決した単一bossの盾へ渡す。HP/hit補正以外のdamage factorsと丸め、skill単位のcounter family1、gauge、named completion、盾なしの通常着弾を保つ。GPUからsource/family/係数も記録し、上表のnative packetと比較する。旧141とミサト2の保持回帰・新レイ4のMetal実行・保存sealが成功してから、新入口を実証済みとして登録する。

証拠: `research/destructible-skill-rosters-native-evidence/manifest.json`。checkpoint: `research/portable-destructible-skill-rosters-native-checkpoint.json`。最終目標は未達。
