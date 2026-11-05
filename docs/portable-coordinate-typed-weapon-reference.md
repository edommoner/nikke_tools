# 座標通常射撃から型付き対象へのCPU契約

共通CLIのCPU専用入口は `coordinate-typed-weapon-common`。現在は7契約で、同じ契約を使うMetal消費側は[sealed46入力](portable-coordinate-typed-weapon.md)として独立監査済み。現CUDAとゲーム仕様の認定は別に残る。

```sh
python scripts/nikke_gpu.py reference \
  --suite coordinate-typed-weapon-common --out /tmp/new-typed-weapon-reference.json
```

不変full package内で実行する。`package --suite coordinate-typed-weapon` から作成でき、referenceは常に7契約を実行する。別suiteの小packageは必要なsupport JSONを含まないため、型付き回帰検査の代用にしない。

元サクラ・マルチャーナ・レイを含む5人編成の全効果・武器・育成設定を保持する。追加damage probeを作らず、正本の `_coord_pellet` が実着弾点、critical、整数damage、packet順を生成する。型付き対象の円／回転矩形と生存世代をGeometryへ明示的に加え、型付きrecipientのfactor5だけへ既存v1 modifierを加える。正本ファイルは変更しない。

対象は射撃開始時に固定する。同じ散弾内で先頭対象が壊れても後続ペレットは旧handleを保持し、次射撃で再選択する。型付きdamageはHitEvent生成時に適用せず、実 `_land` の境界まで保留する。全ペレット量→full_charge_hit通知→着弾の順序を保持し、型付きpacketをBODY/PARTの吸血・蓄積・通常receiptへ混入させない。skillのboss selectorも維持する。

最初の6契約は大きな敵弾、全miss、散弾内破壊と再選択、HPシールド、BODY/typed reach混在、手前のcanonical PART。追加の30秒契約は2048件を超えるhistoryを検査する。元のcharge/RL、critical再利用、親量、全624語のMT状態、元modifierの寄与を確認する。入力生成時にCPU射撃scheduleを作らない。

CPU契約を作成した段階の6件は2.923秒、関連64／制御488検査成功（Windows専用1skip）、GPU／Windows実行0だった。この歴史的記録は `research/typed-weapon-reference-evidence/` に保持する。現在のMetal46入力・関連74検査・観測filter高速化・readback全件監査は `research/typed-weapon-evidence/` と新checkpointに記録する。

このCPUコマンド単独はGPU認定を行わない。明示された私有v1数値・対象モデルの契約であり、canonicalの敵弾／shieldのゲーム規則、typed auto aim候補、移動形状、hit-credit shield、別owner、公開GPU受付、全キャラを認定しない。classificationは `reference_model_gap`、全キャラ認定0、UI CPUを保持する。
