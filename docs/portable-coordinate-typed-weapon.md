# 座標通常射撃の型付き対象接続

共通CLIのsealed suite `coordinate-typed-weapon` は46入力（native29／拒否17）。元の射撃・効果・武器・育成設定を保持し、実着弾点とcriticalを使って敵弾／HPシールドへ着弾する。CUDA／Metalは同じSlang実装、同じ入力とnative比較器を使用する。M5 Metalで全件一致し、GPU禁止のfresh独立監査131.445秒でも全件一致した。現CUDAの実行は未確認。

```sh
python scripts/nikke_gpu.py package --suite coordinate-typed-weapon --out /tmp/new.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new.zip --dest /tmp/new-package
```

共通CLIの通常run／audit／seal／generation-cache手順を使う。compactは未登録なので指定しない。入力115680／出力2032000word、Runtime138952byteを保持し、追加Runtime容量は0。

## 計算と着弾

元武器の射撃スナップショットへ型付き対象の生存世代を固定する。canonical対象とtyped対象を奥行き・出生時刻・node・ordinal/slot順で統合する。着弾点とcriticalは既存の共有MT抽選を各ペレットにつき一度だけ使う。貫通／爆発の型付き追加packetも同じcriticalを継承する。対象種別の倍率は既存のv1契約に従いfactor5へ加え、共通binary64・整数丸めを使う。

packet生成と着弾を分け、全ペレットの親量→射撃／命中通知→実着弾を保持する。同じ散弾内で壊れた対象も後続packetは旧handleを保持し、次射撃で再選択する。typed packetをBODY/PARTのdamage、吸血、蓄積、BODY/ADD groupへ混入させない。original skillのboss指定も維持する。

入力のtyped header13が1の場合だけweapon-only。live aimモードとauthored grow=0、skill sourceのsentinel、全skill route=0を要求し、普通の武器のgrowを使用する。旧スキルのDFS scratchはこの場合だけ物理snapshotへ再利用する。`arena-check --profile coordinate-typed-weapon-v1 --out UNIQUE.json` はこの排他条件とbank配置を監査する。

typed outputの170976word以降を物理historyに割り当てた。先頭2048件を24word/packetで保持し、保持外も全件SHA-256へ入れる。24bit attack IDの範囲で全件数を保持し、2048件到達で計算を打ち切らない。入力数・ターゲット数・shot上限は従来の共通guardを保持し、canonical127＋typed128＋BODYの最大262144 packet/shotを明示的なcoordinate typed groupだけに許す。

## 検証と効率

旧35をすべて残し、大きな敵弾、全miss、散弾内破壊・次射撃再選択、HPシールド、BODY/typed reach混在、手前のcanonical PART、30秒のhistory超過を追加した。新7契約のCPU入口は `reference --suite coordinate-typed-weapon-common`。

観測対象外のC関数通知を各Python observerへ繰り返し伝える処理が重かったため、既存の `native_python_profile.python_observers_only` をこのsuiteへ明示opt-inした。全46入力・source・native指紋の一致を確認し、基準作成269.180→104.266秒（約2.58倍）。計算・Python call/return・ケース・期間・比較項目は省略しない。外部／対応外callbackと明示的なC-event consumerは既存guardで拒否する。

runは73 CPU検査と29 nativeを事前検証し、live-parentの29 native／creation contextをその同じrunの比較だけに再利用した。独立監査には再利用しない。生成cache必須hit・追加Slang0、初回Metal pipeline93.762秒、GPU3.861秒、実GPU1／retry0。旧35の全入力・nativeと284480000byteを保持した。保存rawのdamage・generation・critical・全stream SHA・HP・未使用tailの6改変をすべて拒否した。

## 残りの範囲

静的な私有v1形状モデルへの通常射撃接続である。typed対象を自動照準の候補へ入れる処理、移動するtyped形状、hit-credit shield、別owner、canonicalの敵弾／敵shieldのゲーム規則、現CUDA、公開GPU受付は未完了。元全効果を保持したfixtureの成功を全キャラ認定へ変換しない。classificationはゲーム仕様の `reference_model_gap`、全キャラ認定0、UI CPUを維持する。

証拠は `research/typed-weapon-evidence/` と `research/portable-coordinate-typed-weapon-checkpoint.json`。次はtyped auto aim候補と、回転形状／手動aim／counter／weapon-modeの追加caller契約を同じ共有経路へ接続する。Windowsはsealedコードに必要な短い検証だけを行う。
