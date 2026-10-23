# 非コア条件の共通GPU接続

`not_core` をCUDA／Metal共通Slangの開発専用入口
`gpu/world_not_core_entry.slang` へ接続した。共通CLIの `not-core` は正例27＋拒否5、
`not-core-legacy-reject` は旧入口の拒否1、`not-core-retention` は旧1,533＋新32を扱う。
通常画面はCPU、全キャラ実戦認定は0、現ソースのCUDA実機検証は未完了である。

## 状態と通知

物理着弾後、callback前にペレットのcore値を既存の補償和とbinary64除算で平均し、
発射者ごとに固定する。既存FrameのhitCritのbit0を保ったままbit8〜10へ所有者タグを載せる。
物理hit_countだけがタグを持ち、子の通常通知は空、継続する親handlerでは元のタグを復元する。
on_attack／last_bullet等のコンテキストなしではcore=0を使う。

各定義×casterの1,280累積値を既存出力padding内へ保持する。prob用のbankとは独立し、
seen bitも検査する。条件順、重複評価、短絡、条件評価後の発動budgetを保つ。
Runtimeのfield、138,952-byte stride、出力786,432 words、既存容量、数値primitiveは変更していない。
全診断modeのscratch所有範囲を検査する。専用入口以外は明示的に拒否する。

## 正本比較と初回差分

正例は既存の正本27契約を変更せず使う。冬ギロチンの原文全79定義を含む3／30秒、
ゲージhandler3／34回、合成25例の独立累積・散弾・複数銃口・短押し・親子通知・passiveを含む。
既存battle／skill trace／物理着弾比較を残し、全1,280セルの状態比較を加える。

初回Metal実行の失敗はrawとclaimを保存した。比較アダプターの回復貯蔵decode不足と、
短押し入力の散布界が全員20→10pxに固定されていた不整合を修正した。
新規ケースに限り同じ静的武器メタデータから実際の散布界を入力へ渡す。
CPUの期待値・正本シミュレーター・GPU数値計算はこの修正で変更していない。
入力準備中のtick、get_buffs、GPU実行を禁止する検査もある。

修正版32例と旧入口拒否1はMetalで成功し、GPU禁止の独立sealも成功した。
全1,565入力（native1,236／拒否329）もApple M5のMetalで成功し、独立seal済み。
旧1,533入力の4,822,401,024 bytesと新32入力の100,663,296 bytesが、それぞれ以前の出力と全byte一致した。
CPU回帰95群500検査175.635秒、正本事前89.709秒、GPU計算11.063秒、
追加26検査も成功。生成cache必須hitで追加Slang起動0。
親の正本比較を1,152例で再利用し、84例は再計算、独立sealでは再利用しない。
証拠の識別子は `research/portable-not-core-gpu-checkpoint.json` に記録した。
ソース逆投影はレビューした差分と追加helperのSHAを固定し、既存normalizerは緩めていない。

保持検査の初回はGPU前に、過去の故障注入文字列が現ソースに合わず停止した。
対象履歴層へ投影した後、置換が一意に成立し実際に変化したことを確認して同じ故障を検査する。
追加CPU確認の初回はエージェントの起動cwdが旧checkoutを指したため停止した。
展開したpackageをcwdにしたCPU-only確認は成功し、原失敗を保持した。
全体実行時の作業treeとpackageの全2,397 payloadファイルもbyte一致を確認し、
独立sealはpackage自身のcwd／importsで再比較している。

静的packingは233/266、base173/203、49分類。旧232入力SHAと残る拒否33記録、
残る分類code順序は保持した。追加された冬ギロチンのpackingは実戦認定を意味しない。
実行前には入力＋出力5,576,608,324 bytesと予備14GiBの容量を検査した。
成功済みrawのゼロ領域だけを疎化し、全byte／SHA／path／inodeを保って6,910,836,736 bytesの
ディスク割当を回収した。raw／claimの削除はない。

## 残る範囲

今回のpassive契約はcoreコンテキストなしの数値参照である。通知開始時のHP同期とpassive maxHP、
probとの複合passive、広いteam alias／consumer混在は追加の正本契約が必要である。
これらの全対応や、全キャラのGPU対応を32例から認定しない。

Windowsでは今回追加操作を行っていない。以前の7プロセス終了について、利用者は終了・再起動等の
操作をしておらず、ゲームや動画を利用していた可能性があると回答した。
その利用と終了の因果を示す証拠はなく、原因unknown、環境保全falseを維持する。
