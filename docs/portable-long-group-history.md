# 64射を超える実射撃groupの完全記録

sealed suite `attack-group-long` は60入力（native48／拒否12）で、旧53入力と180秒の新6入力、未知履歴flag拒否1件を含む。Apple M5 Metalで全件一致し、別processのGPU禁止独立sealも成功した。新6入力は全927group・209通知を記録し、65射目以降も全対象・世代・順序・時刻・packet数をCPU正本へ照合する。

|180秒入力|routing|全group|通知|
|---|---|---:|---:|
|元ニヒリスター|native|119|0|
|元ベロータ|native|90|0|
|元ニヒリスター|全論理敵の宣言モデル|119|119|
|元ベロータ|全論理敵の宣言モデル|90|90|
|元ノワール＋宣言listener|native|262|0|
|元ツバイ＋宣言listener|native|247|0|

Ni／Velのnative2件は、groupを導入していない正本のbattle全体・全物理shot値と一致する。SG2件は元の散弾packetを使い、元からmulti_hitを持つという認定には使わない。全論理敵2件は従来と同じ明示比較モデルで、ゲームの爆発範囲・散弾分布の認定ではない。

## 実行状態と履歴の分離

live group32slot・128typed対象・1射1024packet・既存DFS／queue／damage formulaは変更しない。`compile_battle(..., group_history='compact')` がAGS1の予約word3を1にする。従来の `fixed64`／word3=0は入力byteと境界動作を保つ。

compactは1groupを `24+4×実対象数` wordsで、sealした順に連続記録する。先頭24wordsと各typed対象tupleは従来logと同じで、通知数も同じrecordへ反映する。先頭64件の従来logも保持する。rolling hashや履歴切り捨てでgroupを省略しない。headの総group数・使用words・prefix数と、全recordの終端・対象数・prefix一致を比較器で検査する。

開始位置はGPU／hostとも `PACKETS + schema LANDINGS` から導出する。LANDINGSは2048、開始862048、残186528wordsで、出力1,048,576wordsとRuntime138952byteを保つ。arenaが尽きた場合はstatus64で停止する。容量無制限の認定はしていない。

既存の物理shot観測は先頭2048件と省略数を使う。新6件の物理shotは4404～4631件で、このprefixと省略数を既存比較器で照合する。今回の完全記録は全927groupに対するもの。CPU契約は子着弾1254件を観測し、GPUの子効果は既存battle全体・ADD別数量／hit／世代・caster別総量・global overkill・参照解放で照合する。

## 検証と失敗の保持

初版は開始861000を指定し、着弾参照bankを512と誤認していた。実際は860000～862047を使うため履歴が重なり、新6件の参照bank検査が失敗した。hardware実行は完了していたが、そのcaptureを成功扱いせず保持した。GPU／hostの開始位置と境界テストを共通schemaへ接続して修正し、同じ全60入力を別の固定packageで実行した。過去文書の「512key bank」も実2048へ訂正した。

修正版はCPU31検査・native48事前照合・Metal全60一致・独立sealが成功した。65射目の世代、最終groupの時刻、末尾の余分なword、着弾bank最終wordの4改変を、同じ保存readbackの共通比較器で検出した。原本は変更せず、正常値のexpected hashやstrict normalizerも緩めていない。

旧53入力の全222,298,112byte、入力・native指紋を保持した。旧53／32goldenは独立sealのprefixへ全entry一致を検証し、source／生成物IDだけを更新した。新60のrawは251,658,240byte、GPU11.181300秒、cold pipeline90.851237秒。実runのSlang新規起動0、Runtime reflectionも一致する。制御380検査（Windows専用1skip）が成功した。

最終packageは `4c2a5371aa787162aadd3ae5afdfbc0f0e30aaf33716acad609ef213f56e3235`。実行済みv2との差は検証scope metadata、新golden、CLIのsealed登録だけで、最終packageからCPU31＋native48と必須generation cache hitを再確認した。全payload SHAもcheckout／新規展開へ一致する。証拠は `research/long-group-history-evidence` と `research/portable-long-group-history-checkpoint.json`。失敗／成功rawは全byte・SHA・inodeを保って疎ファイル化し、原本削除0で約656MBの割当を回収した。

旧body-heal-share61経路は今回GPU再実行していない。共通生成器で、groupコードが非activeなその経路のCUDA／Metal／両reflectionが前回と全byte同一であることだけを確認し、以前のsource-bound goldenとcaptureは履歴として保持する。新sourceへのrebindや新61入力の計算成功とは扱わない。

静的245/266・base185/203・20model gap、全profile／issue／laneは保持し、全キャラ認定0、通常UIはCPUである。Windows操作0、実GPU試行2（修正前失敗／修正後成功）を記録した。arena境界・広いmixed-owner、部位／座標／盾、通常producer導入、現CUDA本体compile/cacheと短いWindows計算証明は残件。全体目標は継続中である。
