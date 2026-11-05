# ラピの付着弾・handler終了通知の正本契約

次のGPU接続対象はラピ：レッドフードの`projectile_attachment_damage`、`weapon_hit:<名前>`、buff型の`buff_stack_add`。元のCPU正本を変更せず、共通CLIで26合成契約と元87定義の3/30秒を固定した。GPU入力変換・build・実行は禁止した段階であり、新しいGPU受付はまだ開かない。

## 実測した区別

- `weapon_hit`はhandler終了時に1回。3 hitなら3 packetと3 named-hitの後に1通知。子handlerから戻って親の終了通知が続く。
- hit数0・負数でもhandlerを終えて通知する。元係数0、空の名前、蓄積放出・親固定ダメージ・未実装all_projectilesの早期returnは同じ扱いではない。元係数0と、名前倍率-100%で後から係数0になる場合も違う。後者のpacketは正本の最低ダメージ1を保ち、通知する。
- 通知は名前の空白・Unicode・コロンを含む完全一致で、別casterの同名listenerを起動しない。per-hit childのATK更新は親の既に計算したpacketを変えず、終了通知から作る子packetには反映する（900/900→1900）。
- buff型の`buff_stack_add`は通常のnamed carrierとしてstackが1→2となる。instant型は既存carrierへのstack操作で1→3となる。buffをinstantへ書き換えてはいけない。敵carrierのstack_reachも実際に発火する。
- normal_attackの付着弾は通常射撃系のpacket tagと付着弾倍率を同時に持つ。`weapon_type`注釈ではなくactorの武器を読むことを既存のpinned handler監査で確認した。元ラピの注釈MGとbase MGは一致する。矛盾するRL注釈を効果ローカルの武器変更として扱う根拠はなく、model gapとして残す。

元30秒では付着弾16 handler、即時爆発9、フルバースト開始爆発1を確認した。最終敵carrier「유탄」はstack6。B3の保留bonus packetはhandlerの通常終了通知を発生させない。3秒の元ラピにはskill handler発火がなく、30秒の対照が必要だった。観測なしの全battle/projectile、合成の全battle/trace/RNGと一致し、追加のsemantic queryは0。

26中24が既存の宣言モデルに基づく契約、2は矛盾した武器注釈と未実装projectile世界のmodel gap。既存の正本がreturnすることをGPUのno-op対応完了へ読み替えない。

## 再利用するCLI

```sh
python scripts/nikke_gpu.py package --suite projectile-chain-reference --develop --out /tmp/new-chain.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-chain.zip --dest /tmp/new-chain
cd /tmp/new-chain
python scripts/nikke_gpu.py reference --suite projectile-chain --out /tmp/new-chain-native.json
python scripts/nikke_gpu.py reference --suite projectile-chain-rosters --out /tmp/new-chain-original.json
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-chain-cpu
```

このpackageのGPU基準入力は既存の蓄積62を保持している。新しい26をMetalで実行したpackageではない。factories・observer・literal contract・fault injection・source監査を今後の共通Slang比較器へ接続する。旧62の入力/native/source baseline、既存146 shader source、全266 profile記録/244入力SHAと23分類の順序は同一であり、Metal460証拠を再利用する。

分類はGPU lowering候補2、native extension1、model gap10、review10へ更新した。static244/266・base184/203と通常UI CPU、全キャラ認定0は変わらない。

## 共通実行器へ落とす際の残件

Frame10の全per-hit子処理とgauge処理が終わった後に、caster/nameを持つ終了continuationを置く。Gaugeがgateで止まっても、handlerが通常終了した通知は止めない。元係数0、名前なし、特殊早期return、B3 bonus保留、full-burst landingで再度呼ばれるhandlerを区別する。負hit数を黙って0へ変換せず、gaugeが既にある場合のsigned寄与を追加契約で確認する。

compilerへのprivate静的projectionはordinary carrierの名前・stack・対象・寿命を保持する。既存instant stack操作と分離し、matching base-weapon注釈だけをbindingで許可する。正本compiler・保護4ファイル・pinned upstream・binary64・normalizerを変更して合わせない。共有Slangへ接続後は新ケース、旧460全byte保持、元ラピ87をMetalで比較し、必要なCUDAだけを別途短く検証する。

記録は`research/portable-projectile-chain-reference-checkpoint.json`と`research/projectile-chain-reference-evidence/`。full native reportは記録された`/tmp`パスに残し、Gitにはhashとcompact契約を保存する。
