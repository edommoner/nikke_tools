# 短押しと数値参照・抽選順

短押しと遅延数値参照の混在で、旧実装が正本より多く／少なくランダム抽選する差分を検出した。
計算・効果定義・比較器はCUDA/Metal共通。CPU正本と旧compiler、binary64・整数変換・pow、
生成コードのstrict normalizerを変更せず、共有Slangの参照順序を修正する。
公開入口はevent40/tap wire2を拒否し、UIはCPUのまま。開発専用の検証範囲である。

## 固定した契約

共通CLI `reference --suite partial-query` は実際の `_effective_charge_time`、`get_buffs`、
`random.sample` を観測する。追加の数値・対象照会を行わず、元のbattle・trace・入力を保持する。
`tests/fixtures/portable-partial-query-native.json` はGPUを見る前にCPUで固定した参照回数、
cache hit、全query・全抽選・通知・battle・trace指紋。最初の14契約の値を保持して3契約を追加した。

17入力はcaster由来／HP由来攻撃力のdirect random、mappedなチャージ速度・flat・fixed、
期限切れ、通知による値更新、周期的full、自然full、通常full、自動射撃、reload、ログ、
時間／弾数で終わる武器変更を含む。発射ごとのfull/partialだけでなく、全battle状態、
全skill trace、抽選のpool・owner・selector・順序・MT位置・最終624wordを比較する。
抽選履歴は先頭128生recordと全semantic順序SHAを併用し、省略を隠さない。

## 共有実行器の修正

- 非forced tapは、開始時のlast-bullet判定に必要な場合以外は追加の無限弾数照会を行わない。
  holdの終了までeffectiveChargeを照会せず、発射時に判定する。通常fullの経路は維持する。
- 回復倍率は正本の `_live_sum` と同じく、回復を受ける／与えるstatだけを走査する。
  `plainQuantity` の全数値辞書参照で無関係なdirect randomを再抽選しない。
  同じresident走査を `liveQuantity` へ分離し、加算・倍率の算術順序は変えない。
- `clearMode` は弾倉復元の後、名前付き終了callbackの前に数値cacheを無効化する。
  物理的な持ち替え前に終了する論理modeでも無効化する。正本のend_session→invalidate順に対応する。

## 診断の再利用

`partial-query-diagnostic` は元の更新／mode入力2件を一切変更せず、既存数値query診断器へ接続する。
0.2〜0.8秒の全cache missを256件の既存bankへ記録し、overflowは拒否する。
窓とmiss-onlyは診断入口のcompile-time設定で、従来の13.3〜13.37秒の診断と公開入口は維持する。
通常版と診断版の同じ入力は、診断bank以外の全byteが一致することを別のGPU0監査で確認する。
診断streamの一致は全battle認定ではない。

## 検証履歴と残件

v1は5/14一致、主な基準ケースは抽選320→324の過剰。
開始・待機照会修正後v2は12/14一致。通知後の更新は320→323、modeは304→303。
回復live走査修正後v3は13/14一致。診断でmode終了0.533秒の弾倉復元後のmiss不足を特定した。
終了時の無効化修正と3契約追加後v5は17/17一致。診断v4も元2入力の全missが一致した。
通常v4／診断v3のpackage作成は、新auto fixtureに残ったcharge用post-delayを静的validatorが拒否し、
GPU前に停止した。autoのpost-delayを0へ整合した後もCPU正本値17件は不変。
失敗capture・raw・claimを保持し、同一packageのGPU再実行は行わない。

旧1516を含む `partial-query-retention` は1533入力（native1209／拒否324）。
全体v1は92群489検査の時点で、旧layout故障注入テストが後段変換前の文を見つけられず停止した。
GPU claimは作成されていない。最上位の完全なsource projection検査を残し、
layout層へ投影した文へ同じ故障を注入する検査へ直した（5検査すべて成功）。
全体の成否、CPU検査、raw保持とcache観測は対応checkpoint・evidenceを正とする。
全体v2はMetal1533と独立sealに成功した。CPU95群500検査176.060秒、正本事前88.790秒、
GPU11.064秒、最終5群20検査11.253秒。生成cache必須hit・追加Slang0。
旧1516の全input/native指紋を保持し、1512入力は全rawが同一。
差分4入力は `NATIVE_QUERY_BASE+8` のcache hit回数だけで、減少数6/4/6/6が
実際の正本heal_received_mult呼び出し3/2/3/3回の2倍に一致することを追加観測した。
他4768923632byteは全保持。新17は全4465抽選の順序・最終MTを照合し、単独／全体rawも一致した。
詳細は `research/portable-partial-query-checkpoint.json` と `research/partial-query-evidence/`。
Runtime138952byte、strideと容量は維持する。Windows操作を追加せず、7プロセス終了は
原因unknown・環境保全false、現在のソースのCUDA実機確認は未完了のまま記録する。
全キャラ・全stat・全制御の混在を認定する契約ではなく、カタログ拡張と追加consumerの検証が残る。
