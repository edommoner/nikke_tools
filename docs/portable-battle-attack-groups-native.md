# 実射撃からの複数敵命中group: CPU契約

共通CLI `reference --suite attack-group-battle --out NEW_REFERENCE.json` に22契約を追加した。固定full packageから実行し、packing・GPU build・executeを禁止する既存reference経路で照合する。通常UI／既定battle／GPU受付は変更しない。

`battle_attack_groups(routing="all-logical-enemies")` は、plain BODY／ADDだけの明示的な比較モデルである。実際の `_fire`／`_charge_fire` の返却packetを射撃単位で所有し、既存Boss routerで全論理敵へ配る。計算式は既存CPUを通り、実着弾receiptだけにgroup IDを付け、全packet終了後に既存attack group runtimeをsealする。pellet数やdamage量を敵数として扱わない。最大pending32射／1射1024packet・既存typed-target容量を守る。Parts／座標／vanish／盾／敵攻撃／skill-damage武器をこのモデルへ暗黙導入しない。

ニヒリスターとベロータは元の全スキル・装備・同伴定義を保持し、3／30秒、敵0／1／3／5体、破壊、子効果前の同名敵再出現を20入力で確認した。14入力で非zero発動し、158射・102通知・428子着弾となる。ニヒリスターの元射撃は1packetであり、複数packetと仮定した初回unit assertionは失敗した。データを変更せずテスト前提を修正し、元ノワール／ツバイに宣言listenerだけを追加した2入力で実際の10packet射撃を確認した。これらは元キャラがmulti_hitスキルを持つという主張ではない。全22入力は168射／168group／112通知／448子着弾、16入力が非zeroである。

sealed matched setは子効果の対象selectorへ渡し、queued damageに敵世代を固定する。同名で再出現した世代2へ世代1の子を付け替えず、dead／expiredを除外する。子着弾のgroup IDとtyped handleを元集合ごとに照合する。ベロータの防御減少fieldは命中した全対象に付く。例外・不正token・入れ子scopeを拒否し、class／function alias・handler・event／impact／group資源を復元する。単一boss2入力は既存CPUのbattle全体とprojectile shotsに一致する。

固定package `c261067753be1bbd016cf7c19b558fe8a5b5c0fc7b60c18670b4f3648b6caa3d` で22契約4.193336秒、登録CPU93件93.076853秒／120秒枠、既存61入力のnative52事前照合72.114391秒が成功した。別途既存group foundation9件とparent-fixed10件も成功した。実行後の全2833 payload SHAはpackage／checkout双方と一致し、保護CPU・共通GPU・数値core・normalizer・goldenは不変である。GPU実行／Slang新規起動は0。

全22入力は `reference_model_gap` のままで、CLIの `positive_contract_cases=0` はその分類を表す。非zero発動数は各契約の `positive_children` に別記する。「全論理敵へ当てる」はゲームの射程／爆発半径／散弾分布を検証したものではない。Slangへの自律group生成・matched-set frameの接続、Metal実証、現在ソースのCUDA実機照合は未完了で、GPU対応数／全キャラ認定へ加算しない。

Windows接続は読み取りsnapshotで復旧を確認した。既存チャットはidle／前のturn completedのまま、新CUBINコンパイル・CUDA実行・検証再依頼0。次はこの契約の射撃境界・所有権・子対象scopeを共通Slangへ接続し、Metal短例と旧出力保持を確認する。全体目標は未達である。実行指紋・CPU回帰・失敗履歴は `research/portable-battle-attack-group-checkpoint.json` を参照する。
