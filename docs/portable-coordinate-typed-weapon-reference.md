# 座標通常射撃から型付き対象へのCPU契約

共通CLIのCPU専用経路へ `coordinate-typed-weapon-common` を追加した。不変full package内で次を実行する。

検証用full packageには既存型付きsuiteのsupport JSONも必要。開発checkoutで `package --suite coordinate-typed-live-aim --develop --case coordinate-typed/control/original-Marciana-3s --out UNIQUE.zip` を作り、freshな場所へunpackする。ここでのcase選択はpackage作成時の基準計算だけを限定し、下記referenceは常に6契約を実行する。別suiteの小packageは必要なsupport JSONを含まないため、型付き回帰検査の代用にしない。

```sh
python scripts/nikke_gpu.py reference \
  --suite coordinate-typed-weapon-common --out /tmp/new-typed-weapon-reference.json
```

元サクラ・マルチャーナ・レイを含む5人編成の全効果・武器・育成設定を保持する。元武器の射撃を実行し、追加ダメージprobeは作らない。正本の `_coord_pellet` が実着弾点、critical、整数damage、packet順を生成する。型付き対象の円／回転矩形と生存世代をGeometryへ明示的に加え、型付きrecipientのfactor5だけへ既存v1 modifierを加える。正本ファイルは変更しない。

対象は射撃開始時に固定する。同じ散弾内で先頭対象が壊れても後続ペレットは旧handleを保持し、次の射撃で再選択する。型付きdamageはHitEvent生成時に適用せず、実 `_land` の境界まで保留する。これにより全ペレット量→full_charge_hit通知→着弾の順序を保持する。型付きpacketをBODY/PARTの吸血・蓄積・通常receiptへ流さない。skillのboss selectorは従来どおりで、全skillの強制interceptionはしない。

6契約は、大きな敵弾、全miss、散弾内破壊と次射撃の再選択、HPシールド、BODYと型付きreachの混在、手前の正本PARTによる遮蔽を扱う。charge/RLを含むケースは3秒、散弾世代契約は1秒。実際の元RLが発射されたこと、貫通・爆発のcritical再利用、親量、全624語のMT状態、元modifierの寄与を検査する。入力生成時にCPU射撃scheduleは作らない。

これは明示された私有v1数値・対象モデルのCPU契約である。正本に欠ける敵弾／敵シールドのゲーム仕様、型付き対象へのauto aim候補、移動する型付き形状、hit-credit shield、公開GPU受付、全キャラ認定を確立しない。分類は `reference_model_gap` を維持し、Metal／CUDA／全キャラの認定はfalse。既存の実照準35 Metal suiteとは別の段階である。

次はこの同じpacket契約を共通Slangのsample・shot snapshot・deliveryへ接続する。物理packetの生成と着弾、親量、BODY/ADD group accountingを分け、canonical/typedの奥行き順序を統合する。CPUで作った対象列やdamageをGPU入力へ入れない。旧35の全入力／native／GPU出力を保持し、新しいMetal実行と独立fresh監査後にだけGPU認定を進める。Windowsは対応する短いCUDA検証だけを使う。

検証記録は `research/typed-weapon-reference-evidence/` とcheckpoint JSONに保存した。fresh packageのreferenceは2.923秒、関連64／制御488検査成功（Windows専用1skip）。旧35入力16,195,204byteと全356 Slangソース、保護8ファイルが同一。新GPU／Windows実行は0で、Metal対応は未完了。CLI制御・計算・GPUの認定を分けている。
