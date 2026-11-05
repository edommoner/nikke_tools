# ダメージ蓄積を共通の戦闘実行器へ接続

`damage-accum-battle`、`damage-accum-retention`、`damage-accum-rosters` は独立監査済みの共通CLI suite。CUDA/Metalは同じSlang・入力定義・正本比較器を使う。実戦入口は `gpu/world_damage_accum_entry.slang`。通常UIはCPU、全キャラ認定は0のまま。

| Metal検証 | 入力 | 正本比較 | 拒否 | GPU時間 |
|---|---:|---:|---:|---:|
| 新しい戦闘契約 | 62 | 52 | 10 | 0.065秒 |
| 旧398を含む回帰 | 460 | 354 | 106 | 4.511秒 |
| 元ドロシー・トロニー3/30秒 | 4 | 4 | 0 | 2.387秒 |

全てApple M5で実行し、保存出力の独立sealも成功。旧398の入力・正本指紋・全raw 1,251,999,744バイト、新62の195,035,136バイトが一致した。Runtimeは全フィールド・offset・配列長・stride138952を保持する。CPUは回帰39群268検査、実編成23検査が成功。

## 接続内容

既存の `damage_accum_core.slang` を変更せず、戦闘アダプターが実carrierの生成/refresh/退役、付与時の最終ATKによる上限、query時の率・caster HP・stackを渡す。蓄積は吸血処理後のboss着弾へ接続し、add/照準対象とbody由来の部位複製を区別する。名前archiveはcarrier消失後も残る。

満タンになる全poolを更新してからevent50を配送する。再入時に親の通知を上書きしないよう、scratch一覧を予約済みのtyped notice objectへ移す。放出は最初のactive instance、なければ名前archiveから取り出し、split倍率と既存の共通整数変換だけを適用する。攻撃力・防御力・crit・gaugeを重ねて計算しない。

既存24-word objectを再利用し、型13/15/16のcarrier bindingだけword6を使う。rateのword21はstackであり、slotと混同しない。archive14・notice17はcarrierとして扱わない。header260666とqueue260668..261692は既存5モードの所有領域と非衝突であることを既存監査器で検査する。容量を超えた場合は拒否し、通知を切り捨てない。

正本compilerは変更していない。同名poolを拒否するlegacy compilerにはprivate静的projectionを渡し、名前・値・対象・triggerを維持してwire上のstat81/82を復元する。元定義の不変性・duplicate instance・順序・archiveを検査した。protected4ファイル、pinned upstream、software binary64、strict normalizerは変更していない。

## 証拠の範囲

戦闘52ケースでは既存の全battle/trace/RNG比較と最終pool/archiveを照合する。全ての途中状態をGPUから個別に観測したという意味ではない。率・整数・active順序などの詳細な状態操作は別のcore41証拠にある。

元ドロシー73定義、トロニー74定義は効果や時刻を省略していない。30秒の正本ではドロシーのsnapshot2・放出1、トロニーのsnapshot7・放出4を確認し、その実戦結果と最終蓄積がMetalと一致する。観測用タグは終了時に復元し、観測なしのbattle/projectileと完全一致を検査する。未発火の分岐まで全キャラ認定したものではない。

静的packingは244/266、base184/203。旧242の全入力SHAと記録は同じ。未対応は23分類（reference model gap10、reference review13）。静的packingと実GPU認定は別であり、全キャラ・全特殊効果の目標は未達。

## 時間と今後の検証

今回の新sourceの初回Metal pipeline生成は約65秒、62入力の計算自体は約0.065秒だった。sourceが同じ回帰ではpipeline生成約0.003秒、実編成約0.007秒となった。生成cache必須hitで実runの追加Slang呼出しは0。readerの切り分けと独立sealは保存出力を使い、GPUを再実行しない。

初回の梱包・preprocessor・sandboxの失敗、敵受付/付与continuationの接続漏れ、観測タグの復元漏れは元記録を保持した。次は軽量なadmission-only経路で受付の切り分けを先に行えるようにし、巨大pipelineの生成回数を減らす。

Windowsの追加GPU・compile・CPUテスト実行は0。既存core CUDAの成功報告はfull battleのCUDA証明ではない。7プロセス欠落の原因はunknown、環境保持はfalseのまま。前のexport RPCがcanceledで終了したため、保存済み小成果物と既存JSON件数だけの再依頼が受付済み。GPU再実行は依頼しない。残り分類の比較モデル整備、aimed partとの混在、空/遅延recipient、split後0/負packet、通知/容量境界、現CUDAは残件。

詳細なpackage/capture identityは `research/portable-damage-accum-battle-checkpoint.json`、小さな検証結果は `research/damage-accum-battle-evidence/` に保存した。rawと個人設定はGitHub共有へ含めない。
