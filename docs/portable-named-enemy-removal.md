# 名前付き敵の効果解除

名前付き効果を持つ敵への `remove_named_buff` を、既存の共有解除本体へ接続した。CUDA/Metal共通Slangの変更はprivate名前operandの受付条件1式で、敵集合・世代・所属の解除・タイマー破棄・通知の処理は既存のまま使う。Runtime、stride138952、入出力容量、binary64/整数/pow、normalizer、正本計算器は変更していない。

正本には2経路がある。`remove_scope: target` は名前付き敵の集合を先に解決し、そこに属する同名インスタンスを解除する。default/globalはtarget文字列を消費せず同名インスタンスを全体解除する。globalではselector用の名前やdescriptorを追加しない。どちらも元の効果定義のtarget文字列を保持し、CPUで対象や通知を先取りしない。

敵の効果は敵ごとのインスタンスである。例えばボスと3addに同名効果があり、1addだけ選んだ場合は、その1インスタンスが終了し、他の3インスタンスは残る。残存全体があるから通知0という味方共有インスタンスの契約と混同しない。終了通知は選ばれたインスタンスを全て除いた後で発行され、通知時にも残存所属を観測した。

共通CLI `reference --suite named-enemy-removal` の16契約は、target/global各4通りの印（なし/ボス/add/全敵）、opaque/空文字selector、自分を選ぶ印の解除、他casterのpayload、同名caster union、128敵を含む。正本dispatch48、rank33、recipient33、実所持判定504回を確認した。全battle/trace/RNGとget_buffs/_by_name/resolve/rank/notify/dispatchの呼び出し回数を観測前後で保持し、所属・選択・通知・時刻・ownerの故障を拒否する。空文字selectorと空文字の解除対象名は別の契約で、後者の広い混在検証は残件である。

固定package `66a3ff7880bb538bf4a5761e8d4cbcb393a65852c62c4443846d45abefcfec57` のMetal230と独立sealに成功した。native171・拒否59、新規はnative16と不正7。旧207のinput/native/output全指紋を保持し、旧出力651,165,696バイトのSHAも一致した。global行へのdescriptor混入、globalへ変えたまま名前routeを使う入力、名前容量・人数・combat/world/state不正を拒否する。

別package `36e9c99d711c43855a6a2c24c2fc7fe6ee560341ecf6aa95804ce36429e59764` では、元のアスカ：WILLE全80定義を3秒/30秒でMetal比較・独立sealした。3秒は解除0回、30秒は1回発火し、ボスのアンチATフィールドの終了通知1回を確認した。default/globalのためtargetをフィルタへ渡さないことも正本で確認した。全射撃・状態・ダメージ・元定義を既存の実編成比較器で照合し、230入力は再実行していない。

CPU検査は20群156検査、skip0、35.914秒、native事前12.550秒、Metal4.337秒。実編成はCPU2群7検査8.730秒、native0.970秒、Metal2.934秒。両方は同じ生成CUDA/MSLを使い、生成cache必須hit・実行時Slang0。CPUテストだけの変更でも生成cacheを再利用でき、独立sealはGPU0で行った。

最初のCPU検査で、既存 `test_portable_removal.py` が対応済み `allies_random:1` を不正としていた。解除plannerがHEADと同じで既にその範囲を受付することを確認し、容量外 `allies_random:6` へ訂正した。旧失敗記録は保持し、GPUは起動していない。新規実編成テストのmetadata（effectsが名前リスト）誤読もGPU前に直した。

実行前は230件分の非圧縮input/readback＋14GiBを確認し、過去の完了済みrawのゼロ領域を全バイト/SHA/path/inode保持で疎化した。回収1,070,661,632バイトのreceiptを保存した。rawの削除はない。

静的受付239/266、base179/203、残分類37。旧238プロフィールの記録・入力SHAを全保持した。アスカ実編成2入力の実証を、全キャラ・全特殊効果の認定へ加算しない。周期timer、空の解除対象名、再入callback、sequential/ref/scaling/budget、他の世界・部位・全カタログと現CUDAの実計算は残る。Windows追加操作0、過去7終了の原因unknown・保全false、全キャラ認定0、通常UI CPU、全目標未達である。

CLI suiteは `named-enemy-removal-retention` と `named-enemy-removal-rosters`。固定packageを展開したcwdで `generation --develop`、生成cache必須の `run`、保存結果 `seal` を使う。`run` 自体がGPU前のCPU検査を行うため、実行する場合の同じCPU-only先行実行は重複させない。設計・結果の根拠は `research/portable-named-enemy-removal-checkpoint.json` と `research/named-enemy-removal-evidence/`、両suiteのexpected JSONにある。
