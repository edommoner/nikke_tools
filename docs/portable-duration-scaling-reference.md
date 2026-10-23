後続のGPU接続と保持検証は [持続時間の共通GPU接続](portable-duration-scaling-gpu.md) を参照。以下はCPU準備段階の記録。

# 重複数に比例する持続時間の正本契約

共通CLI `reference --suite duration-scaling` に31入力を登録した。
合成27入力と、レイブルの原文全80定義を含む3／30秒の実編成各2入力で、
正本の持続時間評価93回と参照読取87回を固定した。GPUの実装・受付はまだ追加していない。

## 持続時間と値の倍率を分ける

正本 `BuffManager._expires_at` は、明示durationがNoneならduration_valuesを解決する。
`duration_scaling: stack_count` があり、解決後の時間がNone／-1でないときだけ
`ref_count(caster, duration_scaling_ref)` を一度読み、float(duration)×countを計算してから
時刻へ加える。参照が存在しなければcount=0になる。値の `scaling_ref` とは独立である。

- None／-1は無限であり、持続時間用の参照自体を読まない。
- 0秒でも参照を読み、0秒のexpiryを作る。有限の負時間-2は3重複なら-6秒になり、
  「負ならすべて無限」という既存の単純な判定を流用できない。
- ref_countはゲージを優先し、0のゲージが同名バフを隠す。2.9は整数化後の2を返す。
  その後に召喚体の生存数、同じcasterの最初の名前付き状態を調べる正本規約がある。
  今回はゲージと名前付き状態を実測した。召喚体の時刻・優先順位の混在は追加契約が必要。
- 再付与では自身のstackを増やす前に参照する。同じ時刻の自己参照3回はNone→1→2となる。
  兄弟の配列順によってNone→1→2と1→2→3が分かれる。
- 同名carrierへ合流しても、今回適用する定義のduration／duration_scaling_refを使う。
  合成例では同じcarrierへ3倍と1倍の定義を交互に適用する。
- 持続時間の参照はcaster単位であり、全員対象の効果でもrecipientの状態を読まない。

## 実際の状態終了を通す

通常のレイブル3／30秒では対象の持続時間処理は0回だった。
原文全80定義を保持し、1秒時点にslot1へATK1,600,000・係数100の単発攻撃を追加した。
シールドの終了通知から、カウンター「망상 파괴」が1へ増え、
ステルス「상상 실연」とスタン「망상 파괴 2」がそれぞれその1を読み、1秒後に失効する。
入力の時刻は累積時計の1.0000000000000013、expiryは2.0000000000000013だった。
3秒と30秒の両方で同じ2処理を確認した。通常入力で未発火だったことも契約として保持する。

観測器は既存の `_expires_at`／`ref_count` を各1回だけ呼ぶ。元のbattle、物理着弾、
skill trace、全get_buffs・random.sample・expiry・ref_countの順序と結果を比較し、
全31入力で観測追加前と一致した。expiry、参照値／所有者／名前、定義、carrier、trace等の
8種の故障を拒否する。入力と正本計算は観測のために変更していない。

## 実行と次の接続

不変package `3da37aa6c94ce59189eaf95cc290d5dd4c97b32d167086414173fbe6448df60d` の
展開先をcwdとして、共通CLI reference31と関連5群26検査が成功した。
packageは既存not-core32のsourceを凍結する輸送用であり、今回のGPU検証32例ではない。
reference段階ではportable packingとGPU build／executeを禁止している。

分類上はレイブルの2件をnative_contract_extensionへ移した。
静的全266記録、233入力SHA、拒否33記録、49分類のcode・メッセージ・順序は保持した。
共有GPU125ソースと旧32入力／native指紋が同じなので、既存Metal1,565の証拠を再利用する。
GPU再実行・Windows追加操作は0。数値primitive／normalizer／保護対象CPUは変更していない。

次は参照名／ゲージkeyを静的入力へ固定し、共有実行器が適用時刻に読むよう接続する。
carrier変更より前の計算、同名aliasの適用元定義、負の有限時間と無限の区別を保つ。
passive初期化・stack操作による再計算の呼出箇所も調べ、共有Slang・Metalの新例と旧保持を検証する。
現在のGPU受付は拒否を維持し、全キャラ実戦認定0・通常画面CPU・全ゴール未達とする。

証拠は `research/portable-duration-scaling-reference-checkpoint.json` と
`research/duration-scaling-reference-evidence/` に保存した。
