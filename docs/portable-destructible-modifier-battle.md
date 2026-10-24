# 投射物補正を実戦Frameの量確定へ接続

後続の共有Frame/Metal88接続は[HP盾GPU実証](portable-destructible-shield-gpu.md)を参照。以下は当該段階の記録。

sealed共通CLI `destructible-modifier-battle`を追加した。先行scalarと同じ補正queryを、実際のbattle schedulerが所有する既存Frameへ接続する。Metal18入力（native12・拒否6）が保存replayで全件一致し、独立sealも成功。GPU実行は1回だけで、reader修正後のreplay/監査はGPU0で行った。現在のCUDA実機、HP盾への実戦対象選択・迎撃、ゲーム規則・元全プロフィールの認定は未完了である。

## 計算・状態の共用

`gpu/destructible_modifier_battle_entry.slang`は通常world entry、型付きworld、既存の`destructible_frame_runtime.slang`を含む。Frame本体を複製・変更せず、その量確定呼出しだけをproviderで共有`destructibleModifierDamage`へ接続した。通常物理/通常skillの計算は元の`damageValue`を使う。補正の合計・f5への加算・7因子/最終丸めは前段の共有Slangと同じ関数である。

DBT1の1 plain skillという前提を維持し、named coefficient/completion以外のflags、normal/physical、HP-basis modeなど、ここで意味を持たないscalar contextを明示拒否する。named係数はFrameが既に採取した`healthValue`を受け取る。補正を含む量は兄弟着弾前にFrameへ固定し、元のreceipt、同期counter子、再入depth/scratch、handler完了通知、gaugeへ戻す。新しいdispatcherやCPUイベント列は作らない。

入力は既存109536wordの後ろへDMB1 header32word＋axis256wordを加えた109824word。出力1048576word、Runtime138952byte、既存DBT1 descriptor/binding/receipt位置は維持する。source153ファイルのうち、新規入口が追加された分だけが既存経路と異なる。既存Frame・共有modifier query・binary64・strict normalizerのsourceは変更していない。

native側もopt-in `typed_battle(..., modifier_model=True)`だけに接続する。local BuffManager subtypeで既存carrier/queryを使い、通常handlerが実際に採取したbuff/coeff/weapon/defense/hit contextへ同じ宣言f5補正を加える。scope内のconstructor/scalar hookは終了・例外時に戻し、base class/mapや保護CPU/compilerファイルを変更しない。通常bodyのnested childは独自のordinary contextへ戻る。

## 実戦で確認した12正例

|条件|typed攻撃量|通常bodyの観測|
|---|---|---|
|投射物補正+50%と物理の混在|1451/1451|3872のまま|
|HP盾補正だけを投射物へ|968/968|3872のまま|
|補正期限0.15秒|1451/968|3872のまま|
|別味方self／分隊への贈与|968/968／1451/1451|3872のまま|
|普通のATKダメージ40%との加算|1838/1838|5416|
|50%の2stack|1935/1935|3872のまま|
|名前付き完了通知のbody子|1451|子484|
|named係数50%も付与|2177/2177|3872のまま|
|同producerへの親・子・孫|968/1451/1935|probe968|
|補正-100%／対象未出現|最低1/1／着弾0|通常bodyは元の規則|

親・子・孫はそれぞれ確定量を維持し、両typed対象の最終残量5646、親の遅い兄弟receipt量968が一致した。子がmodifierを更新しても親の残り量へ混入しない。graph状態/履歴、damage、allies、covers、shots/ammo、敵hit/log、RNG/gauge、typed世代/量/攻撃/receipt、counter状態と解放済みcontextを既存比較器で比較した。

6負例はDMB1 magic、reserved、未知axis、未使用行のaxis、skill行へのaxis、ATKへ混入し得るnumeric carrier型を拒否する。HP盾buffが投射物に影響しないという正例は、HP盾自体の選択・迎撃を証明するものではない。

## 保存結果からのreader修正

最初の実GPUは完了し、named倍率の1件だけreadback readerが停止した。旧readerは定義の係数100だけを期待していたが、handler/Frameは倍率後の150を採取し、正しい量2177を作っていた。native scalar callbackで実際の採取係数を観測し、shared decoderがそのbit列を照合するよう拡張した。採取前の100へ期待値を合わせたり、係数検査を省いたりしていない。係数観測のためにnative battleを二重実行もしない。

旧producer package `a32b395a945cdee7cbb0b6c4d46349374d82f5ab69de2ed658766e000b96a937`のsource/input/native基準・transport・normalizer・canonical参照を厳密確認し、reader package `29334f25744750c47970aa2f30d47f2ee69edfec3e76a3fc22040103a2a86478`から保存replayと独立sealを実行した。原comparison失敗/raw/claimを保持する。source executionは成功、最初のcalculation判定は失敗、修正readerのcalculationは成功を区別する。同一claim再試行0、GPU追加0。

元GPUの実測はGPU0.053815秒、library1.533835秒、pipeline64.655194秒。実行時間約67秒の大半はpipeline作成だった。実runは必須generation cache hit/追加Slang0。Metal pipelineやCUDA cacheの恒久改善を主張しない。raw75497472byteを再実行で作り直していない。

最終sealed package `30b09f59ae7b139400ff00ffed9cb8efdc9f929546f7b1b7f5a47b5bd8c02e1a`をfresh unpackし、CPU173検査（skip0）/native12成功。実GPU4blockから係数/owner/量/receiptの19改変を検出し、2177の量を保ったまま係数だけ100へ戻す不正も拒否した。sealed生成baselineは必須cache hit/追加Slang0/GPU0で照合した。

## 旧証拠・残件

通常147、typed152、scalar119のsource closureは不変で、旧44/元8/scalar29/通常492のGPU再実行は0。CPU173には既存の全44入力/native保持と元定義・scalarの実GPU保存fixture検査も含む。容量は既存の`sparsify-raw`を終了済み42/44 rawへ再利用して267124736byte回収し、論理byte・全SHA・inodeを保持した。raw削除は0。通常runの1GiB予約とinput前/claim前の容量検査も通過した。

全266プロフィール・packing245/base185・残20分類のissue/順位は完全同一。投射物だけに`typed_modifier_battle_validation`を追記し、HP盾や公開受付へは広げない。次はHP盾の実戦選択/迎撃、対象別DEF/owner policy、元プロフィール全体の接続が必要である。Windows状態取得は今回も失敗、新run依頼0/CUDA実機・CUBIN O0未実施。全キャラ認定0/UI CPU/全目標未達。

証拠は`research/destructible-modifier-battle-evidence/manifest.json`、checkpointは`research/portable-destructible-modifier-battle-checkpoint.json`。個人設定・rawバイナリ・toolchainは共有しない。
