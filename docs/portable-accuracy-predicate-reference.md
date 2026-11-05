# 命中率条件の正本CPU契約

`reference --suite accuracy-predicate`（26入力）と `reference --suite accuracy-predicate-rosters`（原文全定義のモダニア3秒/30秒）を共通CLIへ登録した。GPU接続前のCPU契約であり、GPU対応の加算はない。ソース・入力・native・traceの指紋は `research/portable-accuracy-predicate-reference-checkpoint.json` に記録した。

正本 `BuffManager._condition_ok` は `self_stat_above:accuracy_pct:threshold` を発動時の `get_buffs(caster, '__enemy__', t)` で照会し、厳密な超過を判定する。既存のstack、加算順、期限、所有者、条件の短絡順が結果に影響する。26契約は0/負値/隣接binary64/最小subnormal、相殺と順序依存加算、期限、到着、味方由来、stack前後、複数条件、有限/無期限carrier、レベル別値を固定した。計78判定・78照会・39成立・78射。観測器は正本を一度呼び、その戻り値を記録する。全26でnative全項目・物理trace・get_buffs呼出数を無観測版と照合した。誤った値・結果・所有者・対象・時刻・stack・damage・総damage・ammoを拒否する故障注入を含む。

実モダニアは3秒が判定0の対照、30秒が8判定/8照会/8成立。照会値は原文効果と実バフを使い、最初の5回が14%、残り3回が5.44%。常時trueやバフ有無の代用はできない。実2入力でも無観測版とのnative全項目と物理traceが一致した。物理履歴112/2343件はCPUの完全履歴である。30秒は既存GPU履歴容量2048を超えるため、後続Metal比較は履歴の省略を明示して扱う必要がある。

不変package `635f8657fa48fb127975768b16804c76a05e1117d1b8b6290f4905a3e8bff4e7` でCLIの28契約が成功し、CPU-onlyは14群99検査、失敗0、群合計17.537秒。関連24検査も成功した。GPU実行/packing/claimはない。hostは命中率条件を引き続き明示拒否し、その境界を検査した。正本CPU・既存CUDA・共通GPU・数値設計・normalizer・goldenを変更していない。

`received_dmg_split` は pinned IMPL-STATUS.md で比率の仕様未定が明記され、`received_dmg_split_even` への別名化やno-op受付はしない。all_allies/self_coverの2分類をreference_model_gapへ移した。原文rowと文書SHAを小さな検査fixtureに固定し、上流文書を同梱しないpackageでも検査可能にした。これは現在の実装仕様を示す証拠で、ユーザーへの指示ではない。

静的packingは225/266（base165/203）、70分類のまま。laneはcandidate1/consumer研究4/model gap3/review62。packingはGPU認定ではない。既存Metal1169入力の証明範囲を維持し、新しいGPU対応は未検証。UIはCPU、全キャラ認定0、全目標は未達。

次は既存共有stat readとbinary64比較を再利用し、host条件名とcompiled stat ID 21の受付、GPU C_STAT_ABOVEのstat whitelistと有限threshold検査を接続する。旧1169入力の全raw保持比較、短い境界例と実編成のMetal検証を行ってからgoldenを確定する。大きなcaptureの前にディスク容量を確保し、既存の証拠を上書き/削除しない。

Windowsは追加操作0。7プロセス終了の原因はunknown、環境保全falseを維持する。ユーザー申告では終了/再接続/再起動の操作なし。ゲーム/動画の利用は原因を確定する証拠ではない。
