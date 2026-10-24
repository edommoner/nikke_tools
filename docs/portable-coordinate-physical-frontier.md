# 座標物理弾の移植境界と共通区間演算

座標skillの距離containsと、通常物理弾の着弾確率は別の処理。物理弾は`CharState._coord_pellet`が`Geometry.landing`を呼び、前面遮蔽・core・reachの確率から複数HitEventを生成する。body-onlyの共通入口を部位poolへ開くだけでは対応しない。

## 既存監査を共通CLIへ接続

```sh
python scripts/nikke_gpu.py model-check --out /tmp/new-coordinate-frontier.json
```

新規の出力先を指定する。既存`portable_model_gap_audit.verify`とarena／composed source監査を再利用し、正本の実consumer、private body-only制限、公開受付の拒否、host数値方針gapを照合する。角度区間probeは独立seal済みgoldenのsource閉包とも照合する。source更新時は`requires_new_metal_proof=true`とし、旧証明を使わず新しい開発検証へ進める。`model-check`はnative戦闘・compiler・GPUを実行せず、結果を計算や公開対応の証明にしない。

依存項目は着弾確率、物理packet展開、座標shot group、正本観測器、RNG、手動座標aim、数値方針の7つ。正本観測器はexpected mode用のreference adapterとして実装済み。他は今回の区間演算だけから完成に変更しない。関係する正本仕様文書を対象suiteのpackageへ明示的に含める。監査を全suiteのsmokeへ強制せず、`coordinate-arcs`／`coordinate-composed`の対象CPU検査へ接続する。

## 正本物理packetを再計算なしで観測

既存`world_projectile_native`は、総銃口で割れるpacket数と、全packetの同一damageを要求する。`battle_attack_group_runtime`もBODY／ADDのみの世界とplain logical packetを要求する。両方の実際の拒否をCPUで確認し、既存observerを変更せず保持した。

新しい`world_coordinate_physical_native.observe`は既存のwhole battle／team／control observerを使い、正本`_coord_pellet`のreturnだけをpassive profileで記録する。確率・対象選択・ダメージ・丸めを複製しない。frameの幾何順、確率4種、各HitEventの全fieldとwhole battleを保持する。profileは終了時に元へ戻す。

8つの著者定義worldで15pellet／31packetを観測した。前面／後面の遮蔽、PARTとINTERRUPTの違い、3散弾×2銃口、破壊後の次frame、空scene、貫通reach、chargeを含む。3散弾×2銃口は6pelletだが12packetとなる。部位がほぼ完全に前面を覆う場合も、正本の積分結果には約4.44e-15のbody確率が残り、damage0の本体packetが実際に生成される。epsilonで消したり、pellet数をpacket数へ置き換えたりしない。この観測は全キャラやRNG modeの認証ではない。

## CUDA／Metalで共通の角度区間演算

`gpu/coordinate_arc_sets.slang`は、正本`aim._union`／`_intersect`／`_subtract`に対応する和・交差・差集合を実装する。入力は角度[0,2π]内の有限・整列済み・互いに離れた区間。和はstableな辞書順mergeで`sorted(a+b)`と同じ順序を保ち、交差と差は正本と同じ境界比較を使う。共有software binary64の比較とbit保持を使い、native float／doubleは使わない。

probeは各入力512区間・出力1024区間を確保し、overflowをstatus64で拒否する。未使用入力・非有限・逆転・重複・上限超過も拒否し、結果を切り詰めない。最大1024区間の和と差を検証した。ただし全geometryの必要容量を証明したものではなく、本体の既存対象数やarena容量も変更していない。積分へ接続する前に実生成arcの容量上限とscratch所有権を監査する。

`coordinate-arcs`135入力（native126／拒否9）がApple M5 Metal実GPUで全word一致し、保存rawを独立sealした。接触／1ULP／符号付きゼロ／空集合／wrap済み区間／乱数由来の静的区間と、未使用tailも比較する。GPUは1回、0.012983秒。Slang生成0.315124秒、Metal library0.055550秒、cold pipeline0.045464秒。CUDAは同じSlang・入力・正本helper・比較器を使うが、今回のCUDA実行証明はない。

このprobeは区間の長さのsum、arc生成のacos／atan2／sin／cos、半径方向のGauss–Legendre積分を含まない。Python3.12の`sum`には補償があり、後続のmeasure実装では既存の共通Sum規約と演算順を照合する。確率・条件付きcore・target別round・0damage packet保持・group収集・本体実行器への接続は次の作業。

## 記録と残件

固定package、source／input／output指紋、CPU検査、失敗とWindows送信の状態は`research/portable-coordinate-physical-frontier-checkpoint-v1.json`と`research/coordinate-physical-frontier-evidence-v1/`へ保存する。最初のpackageは出力stride登録不足で作成前に停止し、生成cacheを指定したstandalone runもclaim前に拒否された。修正後の初回dispatchをv2bへ保存し、同claimでのGPU再試行は0。最終v1のCPU制御検査は仕様文書のpackage漏れを検出し、対象suiteへ明示し、同梱依存をpackage作成時・CPU worker前の両方で検査する。合成suiteのarc golden漏れもCPUで検出して保持し、最終v4で再検証する。これらの失敗を消していない。

Windowsの保存object回収はCPUのみの初回依頼を送ったが、接続APIがactive turn不在として拒否した。新しい処理開始は確認できず、再送・compile・GPUは行っていない。保存objectがあったという前回のread-only結果を、回収成功へ読み替えない。host sin45の数値方針も回答待ち。

全キャラ認定0・20gap・UI CPUを維持する。物理着弾確率とpacket展開の本体接続、手動aim、元キャラ全定義の混合world、公開受付、Windowsの計算実証が残る。

最終v4は区間CPU8・合成CPU51・制御416（Windows専用1skip）が成功。full2932→compact1605の残存record／byte／goldenは完全一致。旧合成97と旧座標88・本体81のGPU閉包は既存goldenに一致し、GPU再実行0。CPU正本・共有binary64・strict normalizer・CUDA cache規約も不変。
