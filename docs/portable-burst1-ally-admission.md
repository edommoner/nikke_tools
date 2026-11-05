# B1味方条件を共通のactor-field受付へ接続

`has_burst1_ally`／`no_burst1_ally` を、CUDA／Metal共通のactor-field受付へ接続した。
前回のアニス：スター実編成は、通常の条件実行器が対応しているにもかかわらず、
`actorFieldsDefinitionValid` がこの条件を拒否していた。

新しいprivate flag `PORTABLE_BURST1_ALLY` の内側で、combatが有効であり、
conditionのnameと引数が0であることを検査し、既存 `basicConditions` へ渡す。
`world_actor_fields.slang` の受付4行とprivate入口のflag1行だけをGPUへ追加した。
条件の計算式、状態更新、software binary64、整数変換、pow、normalizerは変更していない。
正本CPU・旧CUDA・Windows wrapperも不変。

## 正本の判定

caster自身は対象から除く。一方、戦闘不能者のstageも判定に残る。
基礎stageに固定せず、現在の `burst_stages` を読むため、一時的なstage overrideと
期限切れがそのまま判定へ反映される。これを正本12契約・実際の条件呼出36回で固定した。

契約はhas／noそれぞれの、自己だけB1、他者B1、B1不在、他者B1の戦闘不能、
他者の一時overrideと失効、自己overrideの除外を含む。
instant回復を数値witnessにし、成立回数がHPへ反映されることを検査する。
観測前後の全battle・trace・get_buffs／条件判定／値読取／random.sample呼出数は一致した。

wire負例8件は両conditionのname非0、引数1、NaNと、combat／world欠落。
単なる条件成立／不成立と、不正入力のstatus64を混同しない。
受付のname・引数・combat検査や自己除外を変える故障は既存監査と新テストで拒否する。

## Metalでの検証

共通CLI `burst1-ally-retention` の125入力（native94／拒否31）がApple M5で成功し、
独立sealも完了した。新B1入力20、武器注記・実編成10、既存95を、既存のstride検査付き
combinerと元のnative比較器へ接続している。入力を小さな代替編成へ置換していない。

前回拒否されたアニス：スターの全83定義を含む3／30秒の2入力も、同じ入力SHAと
同じnative期待値のまま成功した。正本の自動スキル計算は2／77回。
これはこの実編成・期間での一致であり、全キャラや全設定の認定ではない。
元の失敗・診断・raw・claimも保存した。

GPU時間4.333秒。事前に共通CLI `generation --develop` で両targetを生成し、
実行時は生成cache必須hit・追加Slang0を確認した。
CPU12群108検査（skip0）が成功し、単体合計11.322秒、native事前比較9.956秒。
独立監査中のGPU呼出は0。

既存95の出力298,844,160 bytesと、前回一致していた合成8の25,165,824 bytesは、
いずれも旧readbackと全byte一致した。旧10入力すべての入力／native fingerprintも不変であり、
実編成の旧status64を新しい期待値へ書き換えて通したものではない。
Runtime反射とstride138,952 bytes、入力104,400／出力786,432 wordsも不変。

入出力445,416,004 bytesと予備14GiBを実行前に確保した。
このcheckoutにない `storage-check` コマンドは使わず、`shutil.disk_usage` で確認した。
rawの削除・再構成・圧縮率の仮定は使っていない。

## 範囲と残件

静的packing236／266（base176／203）、観測分類42は前回と同じ。
全プロフィールの旧入力SHAと拒否理由を保持した。
今回は静的分類に現れなかった実行時blockerを、12契約と2実編成の範囲で解消した。
`reference_readiness` は専用native契約と今回のscoped Metal証拠へ案内するが、
汎用の `gpu_supported` や全キャラ認定へ昇格させない。

異なるcaster位置、さらに広いstage／復活／通知混在、全1,612入力の新入口保持、
全カタログの実戦、現在sourceのCUDA実機検証は残る。
通常UIはCPU、development_only、全キャラ認定0、全目標未達を維持する。
Windows操作は今回0。以前の7プロセス終了は原因unknown、保全確認falseのまま。

実行packageは `9e7a432e4a59529b2f3203d142b3df221042ac5000ad55d220987b63a556b87b`。
検証・source差分・保持比較・解消したblockerへの参照は
`research/burst1-ally-gpu-evidence/`、現在の境界は
`research/portable-burst1-ally-gpu-checkpoint.json` に記録した。
次はこの記録を起点に、残る高優先の対象指定・着弾時点などの正本consumerを検証する。
