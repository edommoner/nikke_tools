# 有害効果を持つ味方のランダム解除

現在のGPU接続と追加契約は[共通GPU接続記録](portable-random-cleanse-gpu.md)を参照。以下は、最初の正本18契約を作成した時点の記録である。

共通CLI `reference --suite random-cleanse --out <new.json>` へ、正本の戦闘を実行する18契約を追加した。これはGPU実装前の意味の固定であり、GPU受付は引き続き拒否する。

正本 `calculator/buff_manager.py` の `_resolve_target_raw` は `allies_random_with_debuff:2` の候補を編成順の生存者から作り、`_has_harmful` が真の者を抽出して `random.sample` する。通常の `allies_random` と異なり本人を除外しない。`harmful_irremovable` も有害効果の所持判定に含まれるので、抽選されても解除が起こらない場合がある。

`_dispatch_instant` の解除上限は各人に適用し、付与が古い `harmful` から除く。同じ効果を複数人が共有している場合は選ばれた人の所属だけを除き、残る対象の効果を保持する。`harmful_irremovable` と beneficial は保持する。0・負数は全解除、正数は整数化するが、0より大きく1未満では最初の1件を除いてから停止する。これはpinned正本の挙動を記録したもので、ゲームの全仕様を認定するものではない。

18契約は空候補、本人、他者、解除不能のみ、混在、共有所属の部分解除、各人の古い順、上限0・負数・正の小数・2・2直前・最小正数・巨大有限値、seed0、末尾casterを含む。抽選の候補・順序・選択・MT位置、解除前後の全carrier所属をliteral期待値と比較する。観測器は実dispatchとsampleを1回ずつ呼び、追加の有害判定・数値照会を行わない。元の全battle・trace・random最終状態と、sample/対象解決/get_buffs/有害判定の回数を保持する。候補・本人除外・乱数・上限・共有所属・解除不能保持等の故障を拒否する。

固定package `74aa89b7226c1539e94e73169429ab412b679d157742f7ee5c9035b12029a1b3` でreference18とCPU4群26テスト（skip0）が成功した。初回のCPU契約は5人候補の抽選後MT位置を5としたため失敗し、独立したPython `Random(19).sample` で6と確認して訂正した。元失敗を保持し、正本・GPU期待値の変更やGPU再実行はない。

GPU source closureと既存125入力のinput/native全期待値は前回の成功packageと完全一致。GPUコード・数値・Runtime・normalizer・canonical CPU・CUDA compiler/cache・Windows wrapperは変更していない。今回Slang/NVRTC/driver/GPU/Windows操作は0。静的全266profileの入力SHA・拒否理由・42分類の順位/codeを保持し、packing236/base176は不変。

次は期限切れ・戦闘不能・復活・繰り返し抽選による候補変化を正本契約へ追加し、既存の共通RNG・carrier所属解除を再利用して共有Slangへ接続する。全定義の実編成、他の人数指定、現CUDA、全キャラは未検証。通常UI CPU・development_only・全キャラ認定0・全目標未達を維持する。根拠は `research/portable-random-cleanse-reference-checkpoint.json`。
