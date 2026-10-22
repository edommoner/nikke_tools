# 弾消費数として数えるinstant: 正本契約

共通CLIへ `reference --suite ammo-equivalent --out <新規JSON>` を追加しました。
`squad_ammo_consume_as` の正本CPU25契約を不変packageから検証します。
packing／GPU build／executeは禁止し、GPU受付・Slang本体はまだ変更していません。
正本consumerは `calculator/buff_manager.py:_dispatch_instant`、実定義は
シンデレラ：クリスタルウェーブの `저격 모드 탄 소비 집계`（full_charge_fire、値40）です。

## 数値と通知の契約

- 正本は `max(0,int(val or 0)-1)` 回の通知を順次追加します。装弾数を減らす処理ではありません。負値／0／1は追加0、小数はゼロ方向への整数化です。4.999999999999999は4として数えます。
- 既存 `weapon_mode_specs.extra_ammo_count` の有限入力領域±4096をGPU実装の境界として使う予定です。25契約では上端4096の実通知も確認しました。これは正本が4096で打ち切るという意味ではありません。
- 通常autoでは実弾消費通知がdamage計算より前、chargeではdamage計算より後です。同じ閾値buffでも最初のdamageが異なります。追加通知はそれぞれの子callbackを完了してから次へ進みます。
- 味方の弾消費counterは全体で共有します。射手と別の所有者のbuffも反応します。散弾数・銃口数を実消費通知回数へ掛けません。
- 無限弾薬では実消費通知がなくてもinstantの差分通知は発生します。指定数4なら追加3であり、総数を4へ補正しません。
- 重複descriptorの複数発動、max_trigger制限、条件false、通知自身による再帰発動を検査。発動権を子通知より前に消費するため、max_trigger付き再帰は有限に完了します。
- periodic instantは登録時には通知せず、後のtickだけで追加します。登録呼出しとtick呼出しも別に観測します。

25契約では71射・4426通知・64実dispatchを確認しました。上限、値のレベル選択、負値、
小数、battle_start、on_attack、auto／charge、散弾、複数銃口、所有者、無限弾薬、再帰、周期を含みます。
通知のframe別回数・順序・所有者・発生源、実dispatchの値・時刻・tick区分、最終stack、
packet damage・packet数・総damage・装弾数をliteral期待値と比較します。

## 観測・分類・再利用

観測器は実際のnotifyと正本instant dispatchのframeを読みます。互換wrapperを
`inspect.unwrap` でたどり、正本の `eff`／`val` を観測することで値の再計算を避けます。
追加buff照会0、元のnative全項目／trace保持、既存profileとの合成と例外時の復旧を検査。
NaN／Infinityの正本例外も成功へ読み替えません。検証開発中の最初の観測器はwrapperの変数名を
誤認して停止し、unwrapへ修正しました。計算本体や期待damageを合わせる変更はありません。

`portable_readiness_semantics` はこの25契約を参照し、通常のself／literal／追加fieldなしの
未対応instantを `gpu_lowering_candidate` に分類します。別対象・scaling・追加fieldは
`native_contract_extension`、別kind／program段階は従来のreviewを維持します。
`gpu_supported`／`gpu_admission_verified`／`runtime_validation_performed` はfalseです。
分類器の件数は登録literal suiteから検査し、分類がGPU受付を開かないことも確認します。

不変package最終版は `/tmp/nikke-ammo-equivalent-reference-v2.zip`、正本報告は
`/tmp/nikke-ammo-equivalent-reference-v2-report.json`。分類器を含む4群30検査も10.442秒で成功しました。結果とsource指紋は
`research/portable-ammo-equivalent-reference-checkpoint.json` に結びます。
GPU source／golden／数値プリミティブ変更0、GPU実行0・claimなし。
静的224/266・base164/203・71分類は不変で、実装候補1／review65へ分類だけ更新しました。

次はkind37の静的受付と有限数値検査、共通dispatcherの同期continuationへ接続します。
counterを一括加算する実装では途中の閾値・再帰・発動上限を再現できません。
CPU正負例から短いMetal、実定義、旧1088保持と独立sealへ進めます。
Windowsの追加操作0、7終了unknown／環境保全false／サービス未識別の停止を維持します。
全キャラ認定0・通常UI CPU・全ゴール未達です。
