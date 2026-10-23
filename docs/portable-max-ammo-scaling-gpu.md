# 現在の最大装弾数倍率の共有GPU接続

`scaling: max_ammo_count` のcharge_dmg_pctを共有Slangのprivate入口へ接続した。CUDA/Metalは同じ量源タグ・実行本体・検査表を使う。Apple M5で合成20＋不正8＋旧321の349入力と、原エミリア全73定義の3秒/30秒2入力が正本一致し、両方の保存結果を独立sealした。現ソースのCUDA実行、他のscaled numeric stat、広いlate-query/target/mode遷移混在、全キャラ認証は未完了。

## 実装

canonical compilerのMAX_AMMO_SCALE=-4を保持し、portable hostで意味が変わっていないことをassertした上でprivate Definition.flags4096へ変換する。名前付きstack/duration referenceとは独立。非combat/world、他stat、周期、named scaling_refは拒否する。新private Slang入口だけがflagを受付し、kind/stat/敵・HP・倍率flags/有限値等をGPUでも検査する。

collectStatsの通常の所属・条件判定、recipientValueによるstack計算後に、対象本人の現在の実効最大装弾数を掛ける。付与時snapshot・付与者容量・現在の残弾数ではない。通常武器はlive容量、武器変更は既存のmodeMagazine/modeCapacityEpochを再利用し、モード終了後は通常武器へ戻る。

容量計算の整数化をcapacityFromPartsへ抽出した。既存rawFullCapacityも新rawScaledFullCapacityも同じ変換・加算・範囲検査を使う。percentage groupごとの0.5切上げ、flatの偶数丸め、下限1を維持した。新読取は容量に必要なliveQuantityだけを読み、charge_dmg_pctを再評価しない。この限定された依存関係で正本の同recipient再帰省略を再現し、collectStats/ensureNativeNumericの再入と未完成dictionaryのcache公開を避ける。actor world query scopeをboss参照へ移し、終了時に戻す。Runtimeへのフィールド追加はない。

## 検証

共通suite `max-ammo-scaling` は正本20＋拒否8、`max-ammo-scaling-retention` は349(native261/拒否88)、`max-ammo-scaling-rosters` は元エミリア2。CPU31群217検査(skip0)、71.663秒、正本比較20.732秒、GPU4.426秒。実編成はCPU3群16検査、3.075秒、正本1.798秒、GPU1.817秒。cold Metal library1.496秒/pipeline9.199秒、実編成は両cacheがwarm。生成事前検査は新ソースでSlang2回、両実runは生成cache必須hit/追加Slang0。実編成のCUDA/Metal正規化生成hashは合成349と同じ。

旧321の全入力・native期待値・1009778688出力バイトが一致し、Runtime全layout/stride138952も同じ。短い28入力goldenは独立監査済み349の末尾から導出し、adapter入力・名称・raw全SHAを確認した（追加GPU0）。実編成は全73定義を保持し、1発持続の元scalingと親割合damageの両方を改変していない。実際の容量照会を3秒126/30秒1798回観測し、各同数の内側省略、base2.01×本人の容量を確認。全battle/physical traceを既存比較器で比較した。各親context戻り値を別bankで計測した実編成診断ではない。

静的受付は241/266、base181/203、残33分類。旧240profileの全記録/SHAは保持し、変化はエミリア1profileの拒否解消だけ。これはGPU全キャラ認証ではなく、全キャラ認定0/UI CPU/development_onlyを維持する。分類metadata追記後の29検査と依存graph検査5も成功した。

証拠はresearch/max-ammo-scaling-gpu-evidence/、要約はresearch/portable-max-ammo-scaling-gpu-checkpoint.json。raw/package/claimは元の/tmpパスに保持し、Gitへ含めない。過去4rawのゼロ領域をAPFS holeへ置換し、全バイトhash・inode・パスを保持したまま2459566080Bを確保した。削除は0。新規実行の領域と14GiB予備を確保してから開始した。

## 事前検査での修正

最初のgeneration-only検査はrawFullCapacity→plainQuantity→collectStatsの静的再帰をSlangが拒否した（GPU0）。flatだけをliveQuantityで読む容量経路と共通整数変換へ分けて修正した。失敗generation・不変packageを保持したまま別packageで成功した。

実編成のstandalone referenceは正本import初期化不足で一度失敗（GPU0）。importを初期化した別packageではreference2が成功。追加テストのprepared effectsをtupleとして読む誤りも、GPU前のCPU検査で検出・辞書形式へ修正した。最終packageで検査後に実編成GPUを1回だけ実行した。GPU失敗や期待値の都合のよい書換えはない。

Windows追加操作0。以前の7プロセス終了原因unknown/環境保全falseを維持する。現在のCUDAは未検証で、巨大compileや通常全件の再実行は行っていない。次は残33分類の実consumer整備と、容量倍率のlate-query/mode遷移混在、CUDA生成/compile cacheの成立条件を優先する。
