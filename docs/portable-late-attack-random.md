# 実編成から確認した後段ATKとrandom対象の差分

`state-focus-rosters`を共通CLIへ追加した。ビスケット、リトルマーメイド、リリーの全定義（70/79/68効果、favorite0）、元の装備と支援キャラを維持し、各3秒/30秒の6入力を使う。効果の削除やCPU結果からのGPUスケジュール生成はない。suiteはdevelopment_onlyで、成功goldenは未作成。

## 実行結果

不変package `c7c9346272563e27c93195da3a1a4d0269e0fc6346d89553cc4135dfc06ab133`をfresh展開し、CPU19検査成功後、Apple M5で実行した。生成cacheは必須hit、Slang追加0、GPU2.745459秒。117 GPU sourceは前回のstate-focusと同一。

5入力は全比較一致したが、リリー30秒は122差分で失敗した。最初の物理差分は191番（0始まり）、3.683333333333325秒、owner1、GPU30424/CPU42896。失敗全体のcapture `/tmp/nikke-state-focus-rosters-v1-metal`、raw・claim・元packageは保持し、再実行していない。5件一致をsuite成功や全キャラ認定として数えず、前回のsealed1330入力の範囲を維持する。

## 原因と正本契約

正本`BuffManager.get_buffs`は通常のmapped statを遅延対象として解決する一方、`atk_from_hp_pct`と`atk_caster_based_pct`は後段ループで読む。`target_chars is None`なら直接`_resolve_target`し、遅延対象を確定しない。同時刻の同じcaster/target/除外/active版/value版のdictionary cache hitでは、後段も再実行せず抽選を消費しない。

現GPUはcaster由来ATKだけでは後段passを有効化せず、generic `queryRecipient`が未確定対象を1回で固定する。既存`lateAttackRecipient`が有効な場合でも、数値照会の入口全体と正本dictionary cacheの呼び出し規約の対応確認が必要。通常の味方random20例の成功だけでは、このreaderを証明できない。

リリー30秒の正本観測はget_buffs26670回、cache hit17588回、sample4550回（direct4548/lazy2、query外9）。cache hit内のsampleは0。GPU保存履歴はsample4回。seedを含む最初の非空sampleは一致し、以降の消費契約が異なる。生の抽選実装やseedだけを変える修正では解決しない。

`world_late_attack_random_native.py`は元のget_buffs/sample/_resolve_lazyを各1回呼び、照会key・hit・抽選の所属・全MT状態hashを観測する。追加の数値照会0。6実編成全ての観測後native結果が観測前の全結果と完全一致することを確認した。

`reference --suite late-attack-random`は独立した5CPU契約：caster ATK、HP後段との混在、HP由来ATK、通常mapped対照、同対象mapped sibling。各248照会/158hit。通常mappedは1抽選、後段は90抽選。mapped siblingが先に1抽選を共有しても、後段の直接照会はそのlazy結果へ固定されない。順序・query所属・MT状態・damageを固定し、cache hit/sample/state/lazy/damageの5故障を拒否する。GPU支持はfalseのまま。

分類器もこの組合せを`native_contract_extension`へ訂正した。一般recipient成功からの支持推定やCPUモデル不足への分類を避け、reader/cache/history拡張を明示する。

## 次の共有実装

1. 全get_buffs consumerを共通dictionary-query入口へ対応させ、時刻/target/owner/除外/active/value版のcache境界を固定する。camera eligibilityの既存cacheだけを数値結果cacheとみなさない。
2. caster ATKをHP由来ATKの有無に依存せず正本の後段順序へ接続し、direct recipient readとlazy readを区別する。query missだけで抽選し、正本のquery外消費も保持する。
3. 現sample trace128件はリリーの4550件に不足する。状態計算と履歴保存を分けた明示的な容量/省略プロトコルを設計し、黙った切り捨てやerror無効化をしない。全乱数state・順序・計算結果の検査を保持する。
4. 新5契約と実6、既存1330の保持を同じ共有CUDA/Metal sourceで検証する。修正版で新しい不変packageを作成し、旧失敗rawやclaimを上書きしない。

最終CPU不変packageは`/tmp/nikke-late-attack-random-reference-v2`。`reference --suite late-attack-random --out <new.json>`と`run --backend metal --cpu-only --capture <fresh>`で再利用できる。詳細id/SHA/結果は`research/portable-late-attack-random-checkpoint.json`。

Windows操作・追加CUDA実行0。前回の7プロセス終了の原因unknown/環境保全falseは維持。全キャラ認定0、通常UI CPU、全目標は未達。
