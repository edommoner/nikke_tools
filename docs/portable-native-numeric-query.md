# 後段ATKのdirect randomと共通数値キャッシュ

共通Slangの`native_numeric_query_runtime.slang`を本体へ接続した。`atk_from_hp_pct`/`atk_caster_based_pct`と`allies_random:N`の組合せにprivate metadata `RECIPIENT_META+5=0x4e515231`を付ける。GPUも定義から必要性を確認し、欠落・不正・不要なtagを拒否する。通常mapped statの遅延対象をこのreaderへ流用しない。

caster ATKをHP由来ATKの有無に依存せず後段passへ接続し、未確定の対象を直接読む。数値辞書はowner/target/除外/time/状態epochごとに64要素の全binary64結果を保持し、cache hitは再抽選しない。弾数・チャージ・無限弾薬・plain scalarの照会を同じ入口へ接続。初回通常命中とチャージ開始のcache破棄、既存の効果追加・終了・stack/HP更新経路の破棄も接続した。

scratchは既存focus bank直後の773056..781792（8736word、同時刻64context、各136word＋header32）。診断末尾786416より前で、既存bankとの重複なし。上限はerror64、epoch overflowはerror2。Runtime field追加0、構造体の数値ABIは変更していない。metaのない旧経路ではcacheへのアクセスも初期化も行わない。追加の全reader/全mutation/全編成を認定するものではない。

## 実証と終了時観測

共通CLIの`late-attack-random`を追加した。native5＝caster ATK、HP後段混在、HP由来ATK、mapped対照、同対象mapped sibling。拒否7＝tag欠落/不正/不要、allied tag欠落、予約word、combatなし、過大recipient count。5例は各248CPU照会/158hit、通常mapped1抽選対late90抽選の契約を維持する。

`/tmp/nikke-native-query-v5`（id `f29d1656093dbf0a912afb0a4340fc9e71443fc97d1ee317ec9c9f0c9f82c7f0`）をfresh展開し、CPU27検査後、Apple M5で12入力すべて一致した。戦闘全項目/skill traceだけでなく、抽選pool・人数・順序・MT消費位置・最後の全MT stateを照合する。保存rawからの独立fresh CPU sealも成功、GPU再実行0。実sealを`portable-world-late-attack-random-short-expected.json`へ保存したが、suiteはdevelopment_onlyのまま。

既存の正本観測器には、終了時の敵ATK→Actor数値読取がある。敵ATK読取は味方caster-ATKの保留対象も解決するため、GPUも同じ順序で既存処理を呼ぶ。Actor数値の実get_buffsは共通cacheを通す。一方、generic診断用のATK%表示だけのcollectorはlate passの抽選を起こさない。CPUの計算や期待値を変更せず、観測の副作用も含め一致させた。

v1は古いsource-delta故障テストの適用位置が新しい層と重なりCPU段階停止。各監査を新層→旧層の順で厳密に投影し、旧差分テストは投影後、最新差分テストは実sourceに故障注入するよう整理した。v2は初回命中/charge開始破棄不足とgeneric出力の追加照会、v3はActor数値照会不足、v4は終了時reader順で停止。全packet・raw・claimを保持し、同じ失敗の再実行・claim削除はしていない。

武器フェーズ・query boundaryの既存監査にも新しい厳密source層を接続した。既存baselineのSHAを変更せず、11sourceの明示差分だけを巻き戻す。消えたboundaryを含む故障は新source層で先に拒否し、旧算術/コールバック/早期returnの検査は保持する。

## 未完了と次のbatch

1. リリー30秒の4550抽選に対し、既存sample traceは128件でerror64。全選択を証明できる明示的な履歴/容量プロトコルが必要。黙った切り捨てやerror無効化はしない。次にこの方式を実装し、前回失敗した実6入力へ戻る。
2. chargeの実射撃/終了、focusing混在、他target/数値readerと全mutationのcache契約を拡張する。今回のchargeケースは待機で、実射撃の証明ではない。
3. 変更前sourceのsealed1330は歴史的証拠として保持する。今回118sourceでの全保持検証は未実行。履歴方式の変更後に同じsourceへまとめ、raw予算を確認して全入力/全rawを検証する。旧golden群・本体compiler証明のpromotionは保留。
4. 現sourceのCUDA/NVRTC cache hitは未検証。今回はSlangのCUDA/Metal両生成とMetal実行まで。Windows操作0、7プロセス終了原因unknown/環境保全falseを維持する。

最終検査用の不変packetは`/tmp/nikke-native-query-release-v1`。実Metal版とsource/input/全native指紋を保ち、CPU10群44検査と`reference --suite late-attack-random`の5契約が成功した。GPU再実行はない。standalone生成cache確認はdevelopment packageのsealed-source要件で生成前に拒否され、追加コンパイラ/GPU0。細部は`research/portable-native-numeric-query-checkpoint.json`。全キャラ認定0、通常UI CPU、全目標未達。
