# 元の投射物定義と所有者別スキルレベルの実戦接続

`destructible-original-battle`を共通CLIのsealed suiteとして追加した。スノーホワイト：ヘビーアームズの元定義index24（`all_projectiles`、`burst_cast`、レベル別values）を変更せず、実際の戦闘scheduler・バースト通知・共有Frame・投射物producerへ渡す。CUDA/Metalは同じ入力生成・GPUソース・比較器を使う。この元定義8入力はApple M5のMetal/nativeで全件一致し、保存出力の独立sealも成功した。

## 共通レベル入力

従来の実戦検証器は全員の全スキルを10に固定していた。`research/world_authored_roster.py:skill_levels`をnative observerとframe/team/counter/controlの各入力経路から共用し、caseの`skill_levels`で5スロットそれぞれの1/2/3を指定できるようにした。未指定の既存caseは10を維持する。明示指定は全5人・全3キー・整数1〜10を必須とし、bool・float・欠落・範囲外を拒否する。callerのmapを変更せず、係数やCPUイベント列をこのhelperで計算しない。

```python
case['skill_levels'] = [
    {'1': 2, '2': 7, '3': 1},
    {'1': 10, '2': 10, '3': 10},
    {'1': 10, '2': 10, '3': 10},
    {'1': 10, '2': 10, '3': 10},
    {'1': 10, '2': 10, '3': 10},
]
```

投射物receiptの比較器も固定値だけの想定を外し、実際の所有者・sourceのスキルレベルを既存`coefficient`で選ぶ。バーストを使うのは同じ戦闘controllerであり、CPUで作ったバースト時刻をGPUへ渡してはいない。元のtrigger/name/source/valuesは保持する。通常UI・canonical CPU/compiler・ソフトウェアbinary64・normalizer・GPUソースは変更していない。

## 実GPUで確認した8入力

全正例のバースト発動は約0.2秒。敵DEF100と宣言した戦闘条件での結果は次のとおり。

|条件|投射物ダメージ|追加観測|
|---|---:|---|
|スキル3レベル1、元係数24.76%|240|所有者のスキル1/2は2/7|
|レベル5、元係数32.38%|313|レベル10へ固定されない|
|レベル10、元係数41.9%|405|通常bodyへの重複着弾なし|
|レベル10・敵DEF0|450|既存scalar式を使用|
|レベル10・攻撃力+50%|631|発動時のlive buffを使用|
|元の名前付き完了通知の子|405|通常bodyへの子ダメージ484|
|投射物がまだ出現しない|着弾0件|通常bodyへの代替着弾なし|
|元キャラがスロット4・レベル1|240|スロット0のレベルを参照しない|

実証world・武器・周囲の効果は宣言fixtureであり、このキャラの元25定義全体を検証したものではない。投射物の専用倍率、投射物別DEF、盾迎撃、logical enemy owner policyも未対応のままである。

Metal package `7f7c13bd5efea8f2d9b8b01c7f02aa2130d032ddcd58abbb453ead00144d54a7`、GPU0.056033秒、pipeline0.016868秒、出力33554432byte、Runtime stride138952byte。新GPUは追加8入力の1回だけ、同一claim retry0。生成cache必須hitで追加Slang0。これはwarm経路の観測であり、CUDA実機や恒久pipeline cacheの性能証明ではない。

初回packageはCPUテストが必要とする通常492のgoldenを梱包しておらず、GPU前に停止した。support_filesへその参照を明示し、別の固定packageで解消した。元のCPU失敗・captureを保持する。スキルレベルの取り扱いをテストのために緩和していない。

独立seal後にgoldenを登録し、最終package `3b5cc5463d5cb4ff266e9cf9b80fe42e0041476a8d5fd481dc198d000f3ca0a7`をfresh unpackしてCPU145検査（skip0）/native8成功。実GPU8blockを入力・全raw SHA付きで固定し、係数・所有者・量・receiptと空集合の改変を検出する。sealed生成baselineは必須cache hit、追加Slang0/GPU0で照合した。

## 既存経路の保持と使い方

旧`destructible-battle`44入力の全入力とnative指紋を保持した。通常`projectile-chain-retention`492入力は別の固定packageでCPU288検査（skip0）・native378の全指紋が成功。両GPU source closureと正規化前のCUDA/MSL byteは変更前と完全同一であり、旧44/通常492をGPUで再実行していない。原rawは削除していない。ホスト経路を変えたためCPUの保持検査は実施した。

```sh
python scripts/nikke_gpu.py package --suite destructible-original-battle --out /tmp/original-battle.zip
python scripts/nikke_gpu.py unpack --archive /tmp/original-battle.zip --dest /tmp/original-battle
# 展開先をcwdにし、CPU-only / run / audit / sealは既存CLI契約を使う。
```

全266profile・packing245/base185・残20分類のissue/順位は不変。readinessにはこの1元定義・8入力・レベル1/5/10・実バースト通知の限定実証だけを追記した。全キャラ認定0・UI CPU・全目標未達。Windowsは接続観測不可、新run依頼0、CUDA実機は未確認、準備済みCUBIN O0実験は未実施。

証拠は`research/destructible-original-battle-evidence/manifest.json`、checkpointは`research/portable-destructible-original-battle-checkpoint.json`。次は元25定義全体を妨げるconsumerと投射物の専用補正・対象モデルを詰め、既存の通常ダメージ計算と共通Frameへ接続する。短いCUDA実証は接続復旧後に保存済み/準備済み成果物から再開し、巨大コンパイルの同条件再試行を避ける。
