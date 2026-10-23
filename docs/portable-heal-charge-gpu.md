# 回復蓄積・容量補正・放出の共通GPU接続

共通CLIの開発入口`heal-charge`37入力と`heal-charge-retention`386入力へ接続した。計算は`gpu/heal_charge_runtime.slang`でCUDA/Metal共通、効果の静的policyは`app/portable_heal_charge_specs.py`と既存protection metadataを使う。正本`heal_charge_compat`、protected canonical/compiler、software binary64、厳密normalizerは変更していない。通常UIはCPU、全キャラ認定0、ゴール未達。

## 実装と観測

既存protection allocatorのkind10を1carrier当たり1個のscalar poolとして使う。current/base容量、owner/name、既存entryOrder/slotとdone/ended/reservedで世代を区別する。1024 objectの上限とRuntimeの全field・stride138952を維持し、per-recipientの過剰回復buffer(kind9)と混同しない。pool生成を同期named/stack子処理の後へ接続し、その時の付与者ATKをsnapshotする。body healのHP clamp前で正の割当量を集め、live容量bonusを読む。明示state_endでは消費前poolを残し、名前で一度だけtakeしてから元の重複対象順に既存の倍率・身体回復・同期・通知を使う。

観測bank771072に先頭512件のbuild/deposit/takeを最大20wordずつ記録する。金額はGPUで計算し、入力へCPUのpool量を注入しない。正本観測器もcapacityの実returnとrecord fieldを読むだけで、追加の意味照会を行わない。満HPでHP差が0でも量を比較できる。観測超過はtotalに記録し、現比較器は512件超を未検証として拒否する。heal-share/native-query診断とのbank併用は禁止する。

## 実証と失敗の保持

不変package f7949544...のMetal386（native290、拒否96）をApple M5で実行。GPU4.445386秒、library1.499秒、pipeline11.777秒。CPU33群231検査78.087秒、native事前25.563秒。生成は両backendを事前生成し、実runはgeneration cache必須hit/Slang0。CUDA生成成功はCUDA compiler/driver/計算の実証ではない。

最初のCPU失敗はテストのtuple/list比較、次のMetal37失敗はkind32のActor-pool受付漏れ。修正版386では戦闘・skill trace・量観測が全件一致したが、比較器が返す正本から観測欄をpopして指紋を変えてしまった。元の失敗は保持し、比較対象の辞書だけをコピーして修正。比較器が正本を変更しない検査と量・順・欠落への故障注入を含む8検査が成功した。

最終host変更はfresh package e7bf940c...で4群30検査・native29が成功（CPU8.009秒）。最終CLIのgenerationも必須キーと同じcacheでhit/Slang0/GPU0、CUDA/MSL/両reflection全byteを実Metalの保存物と一致確認した。

修正後package57b16e2d...へ保存rawをreplayし、GPU再実行0で386全件成功。fresh子による独立sealも成功。登録goldenはこの独立sealで、単独37はseal済み386の末尾37入力・rawを全hash一致で射影したもの。元raw/claim/失敗packageは残している。旧349の全input/native/output指紋、入力145742400B、raw1097859072Bが完全一致。両reflectionの全Runtime layoutも同一。

静的inventoryは242/266、base182/203、残30分類（以前241/base181/残33）。旧241の入力SHAと全266profileを保持した。新しく入力を作れるデルタ：ニンジャシーフは79定義で、実編成3/30秒の検証はまだ行っていない。

## 次に必須の境界

今回の29契約は宣言モデルの部分検証である。終了済みpoolを保持した後のdown→復活では、現在のsweepがbuild/collect/take時だけなので、復活後までowner破棄が遅れる恐れがある。次はdown直後の確定破棄を接続し、保持済みpool→down→復活→放出を直接比較する。これを現29件のdown単独検査で実証済みとは扱わない。1024 object上限、512観測超過、lazy/回復分配/親callback混在、元デルタ79定義の実編成も未検証である。

Windows追加操作0。過去7プロセス終了は原因unknown/環境保全falseのまま。今回の共通関数境界はgenerated CUDAで247 noinline/843関数として確認したが、実compilerの展開量・資源・cache速度改善の証明ではない。追加Windows検証の前に、有用な修正checkpointの独立Metal sealからcompiler packetを固定する。

## 再利用するCLI

```sh
python scripts/nikke_gpu.py package --suite heal-charge-retention --develop --out /tmp/new-heal-charge.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-heal-charge.zip --dest /tmp/new-heal-charge
# 展開先をcwdとし、その中のCLIで実行する。
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-heal-charge-cpu
python scripts/nikke_gpu.py generation --develop --out /tmp/new-heal-charge-generation --generation-cache /tmp/nikke-slang-generation-cache-v1 --slang-root /absolute/slang-root
# GPU実行では同じgeneration-cacheと--require-generation-cacheを指定する。
```

development_onlyを維持する。証拠は`research/heal-charge-gpu-evidence/`、最新要約は`research/portable-heal-charge-gpu-checkpoint.json`。rawはGitHubへ含めない。
