# 元の移動停止・強制移動・グループ効果を同じ編成で実行

`moving-overlap`はユニ・ヤン・ドレイク・ニヒリスター・メアリーの元72定義、実武器・育成・seedと30秒を保持する。既存overlap編成のN102だけを元ニヒリスターprofileへ置き換え、停止・強制移動と実multi_hit通知/子攻撃を同じ戦闘で検査する。効果を追加・削除・短縮せず、位置や命中結果を入力へ保存しない。

新しいshader、時計、状態handler、damage式は作らない。既存moving-typed/groupの同一Slang entry・packer・native observer・全出力比較器を利用する。2つのworldは`disable-before-force`と`force-before-disable`を明示し、実際に両carrierが重なる生存区間と、その区間の位置・typed付属物・物理攻撃・distinct group通知・元子攻撃の着弾まで検査する。どちらがゲームの規則かを推定するものではない。recipientは既存`canonical-all-in-range`近似、force先は宣言中心、typed付属物も既存明示モデルを維持する。

固定開発packet1056fb2f…のM5実GPU1回で全14入力（実戦2/拒否12）が一致。GPU2.286507秒、pipeline0.003019秒、fresh CPU48.771816秒。generation/PSOは必須hit、Slang compiler0、再試行0。全72定義の元入力identity、全battle/skill/group/typed/移動履歴/最終状態を比較する。別fresh GPU禁止7群の独立sealも91.457493秒で成功、親native再利用0・GPU0。入力6,898,532byte・出力121,247,616byteと失敗log/claimsを永続proofへ保持した。

旧current-groupの生成CUDA/MSLは正規化前の全bytesも一致し、12拒否入力/native指紋も保持。既存GPU payload全体と保護CPU4ファイルはbyte不変。元group15のCUDA準備とは別packet/別入力であり、そのWindows成果を今回の計算証明へ付替えない。

通常は`python scripts/nikke_gpu.py package --suite moving-overlap --out NEW.zip`から固定packetへ展開して使う。現在のCUDA実行、実ゲームの距離・優先順・付属物規則、公開GPU受付、全キャラ認定は未完了。分類には両operatorの限定的な`current_overlap_validation`を追加し、元拒否理由や公開受付を維持する。小証跡は`tests/fixtures/moving-overlap-metal-v1.json`、期待値は`research/portable-moving-overlap-v1-expected.json`。
