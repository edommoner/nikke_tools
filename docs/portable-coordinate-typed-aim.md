# 型付き対象の照準契約

共通CLI `reference --suite coordinate-typed-aim-common --out UNIQUE.json` は、元の完全5人編成・効果・武器・成長を保持したCPU契約7件を実行する。正例6件と、実際の未対応を拒否する1件。GPUパッキング・コンパイル・実行は行わない。既存 `coordinate-typed-weapon` のMetal46入力の証拠を自動照準の証拠へ流用しない。

明示指定 `typed_aim_policy={"mode":"typed-before-body-v1"}` の場合だけ、canonicalの名前付き対象／ADDが選ばれないBODY fallbackに型付き対象を追加する。ゲーム内の敵弾優先度を確定したものではない。通常の手動優先度・カメラ・フルバースト追従は元の調停器を通す。候補はframe開始時に生存世代と中心を固定し、同frameの先行射撃による破壊後も照準は固定、次frameで再選択する。射撃packetの生存snapshotは既存の射撃単位のまま。

`coordinate_typed_geometry_runtime.live_rows` を照準と物理射撃で共用する。照準proxyが追加するのは名前付きのcenter/kindのみで、ordinary skillのtargets/shapes/landing cacheはcanonicalのものを保持する。手動typed名の初期検査は所有worldの宣言namespaceを照合し、canonical `target_kinds` へ追加しない。core／canonical名との衝突、未宣言名を拒否する。canonicalがframe途中でgeometryを交換した場合、次frameに古いgeometryへ戻さない。

検証はfallback／期限切れ、散弾内破壊後の次frame選択、手動canonical、手動typed、ADD優先、元の実フルバースト追従。元Reiの `enemies_nearest_in_range` は現在照準先を論理enemy recipientへ変換する規則が未接続なので、全定義を保持して最初のframe前に拒否する。効果削除やBODYへの置換で通さない。登録時には既存の元定義・所有者・順序の完全一致検査も通る。

## 共有GPU wireの条件

入力compilerは既定ではtyped aim指定を `Typed automatic aim requires a new shared GPU wire and consumer` として拒否する。CPUだけ照準を変えて古いGPUへ送ることを防ぐ。sealed `coordinate-typed-aim` だけが `coordinate_typed_aim=True` を明示して専用consumerへ接続する。

共有CUDA／Metal consumerは、BODY=0、canonical=1..127、core=128を保持し、typed128slotへ129..256を割り当てる。既存focusのowner別8bit packingは256を表せないため、専用profileで9bit×5ownerへ変更し、読み手・書き手・入力検査・CPU比較を一緒に更新する。ターゲット容量を減らしたり、最後のslotをBODY/coreへaliasしたりしない。旧profileのbyte契約は保持する。

frame候補の固定は実world同期直後、照準調停は元と同じ時点に置く。timed skillによるframe途中の変化と射撃時snapshotを混同しない。前frame照準を参照するskill、現在対象recipient、手動名のwire検証も独立して維持する。未接続selectorは閉じたままとし、共有consumerの実Metal出力とfresh native監査が一致してからMetal対応を記録する。

証拠は `research/typed-aim-evidence/` と `research/portable-coordinate-typed-aim-checkpoint.json`。CPU契約の成功は全キャラ／ゲーム規則／公開GPU受付の認定ではない。UI CPU、全キャラ認定0、分類 `reference_model_gap` を維持する。


## 共通GPU consumerの開発経路

sealed suite `coordinate-typed-aim` は旧46をすべて含む59入力（native36／拒否23）。`package --suite coordinate-typed-aim` から不変packageを作る。新 `world_coordinate_typed_aim_entry.slang` が既存の座標射撃入口へframe照準hookを合成し、数値処理・射撃・物理着弾・効果dispatcherは共用する。typed header14=1の明示profileだけで、手動129..256を許す。ADDは内部専用257（手動wireでは拒否）に分け、BODY0／canonical1..127／core128と区別する。

候補snapshotはtyped tailの220224..220767（544word）に置く。32word headerと128×4word（ID／世代／node／identity）、全frameを既存と同じ二重64bit digestで検査する。旧物理history／overflow領域は保持し、新ownerを全件検査してから既存の物理比較へ投影する。115680入力／2032000出力word、Runtime138952byteは不変。`arena-check --profile coordinate-typed-aim-v1` で所有と重複を検査できる。

初Metal全59は58一致・ADD優先1不一致。focusを有効にすると旧座標のADD sentinel0がBODY0と衝突していたため、専用257と着弾先decoderを同時更新した。失敗raw／claimを保持し、旧46の全373888000byte保持も確認。修正版は境界対象を終了時にも生存させ、最終focusの非ゼロID256を実出力で比較する。修正版はM5で全59一致、別GPU禁止childのfresh独立監査172.056秒でも全59一致。実GPU3.877秒、新PSO93.968秒、実行時の生成cache必須hit／Slang0。現在CUDAの実行は未取得。

実readbackの候補世代・candidate ID・候補stream digest・9bit focus・未使用tail・全照準frame digestの6破損を拒否。最終focus ID256を非ゼロで実確認した。論理BODY／ADD名をtyped labelへ流用する入力もCPU reference／compilerで拒否する。最終化では数値／Slang／transportを変更せず、追加した拒否guardだけを除くと実行版のCPU producerと全byte一致することを検査し、別の最終CPU-only全59回帰137.954秒も成功した。関連78／制御488検査成功（Windows専用1skip）。最終パッケージ36acee7f…、証拠は `research/typed-aim-gpu-evidence/` と `research/portable-coordinate-typed-aim-gpu-checkpoint.json`。
