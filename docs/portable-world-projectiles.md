# 共通実行器の散弾数・範囲変更

`world_projectile_entry.slang` は実編成入口を継承するprivate ABI0x5045568d/mode24です。入力104400word、出力786432wordを保持します。CUDA/Metalは同じSlang本体・効果定義・入力・CPU基準・テストを使います。通常画面とpublic world受付はまだCPUです。

## 数値と実行順

`pellet_count` は基礎ペレット数へ加える量、`pellet_count_fixed` の合計が正なら固定値を優先します。先に全residentの値を既存の順序で合計し、ソフトウェアbinary64のties-to-evenで整数化して、最低1へ制限します。総口数は別の値のまま保持し、係数はペレット数だけで分割します。浮動小数点の整数丸めを済ませ、範囲を比較してからint64へ変換するため、巨大な負値でも不要な変換overflowを起こさず1へ制限できます。実効ペレット数が4096を超える入力はstatus64です。

一発のペレット数・係数・範囲は物理射撃のsnapshotです。自動射撃では最終弾通知と弾薬消費の子処理の後、チャージ射撃ではfull_charge通知後かつ弾薬消費前に捕捉します。途中のpellet通知が付ける変更は次の発射から適用します。modeの物理session・総口数・弾薬・burst gauge・通知は既存本体を使います。

座標なしのpart reachは、通常0、貫通1/2、爆発3/4です。100−1e−9以上なら次の段階へ届き、爆発と貫通の両方がある場合は爆発側を選びます。閾値直下のnextafterと一致点を元CPUで固定しました。`explosion_range` はidentity64なので64要素のdamage vectorへ添字として使わず、共通のordered scalar queryで読みます。座標geometry・interrupt・追加partへの直接skillはこの段階の認証に含みません。

部隊のpart/body通知は、元CPUと同じframe開始時点の`has_parts`を使います。初期の静的指定を残し、実在するpartの出現・期限・破壊をActor poolから捕捉します。同じframeで最後のpartが壊れても、そのframeの残りの通知では捕捉値を使います。

## 入力と既存演算子の接続

Neon: Vision EyeとArcana: Fortune Mateで使うgauge条件・消費、A2などの名前付き解除も既存の共通演算子へ接続しました。受付を追加しただけで、別の資源・解除処理は作っていません。元CPUの最終gauge value・cap・presenceも5戦闘35owner-resource項目で、保存済みGPU bankと直接一致しました。

引数なし`squad_ammo_consume`だけの効果は元CPUの部隊indexに入りません。回数指定を同じ効果に併記すると、そのindex登録数だけ全通知に反応します。元の効果・順番を残し、既存wireのnever-match形式と共通dispatchのslot選択へ静的にloweringします。個人`on_attack`等は保持します。

private counter入力変換器が、self/enemy向け名前付き解除の未使用recipient領域へstat keyを書いていた問題も修正しました。allied-scope以外は8wordをゼロのまま保ちます。canonical compiler/engine/referenceは変更していません。旧65入力は全bytesを保持します。

## 保存実証と診断

最終の共通63入力はnative52＋拒否11です。さらに新規11実プロファイルを各3/30秒、計22戦闘で全効果を省略せず検証しました。各69〜83効果、成長・装備・スキル・お気に入りを実準備から渡し、HP・damage・武器・burst状態と物理射撃の時刻/ペレット数/総口数/到達段階/一個のdamageまで元CPUと完全一致しました。固定パターン・期間の証拠であり、全キャラ・全変種の戦闘認証ではありません。

- 7b604ef：初回44実戦中25一致、拒否7成功。引数なし通知・動的part/body分類の不足と、検証入力のRL射撃後待機時間の誤りを保存。
- 3b66714：47中45一致。残る2件は、無効slotを通知多重度に数えた差分。初回rawは保持。
- 29280b8：native51＋拒否7成功。実22戦闘は16一致、資源条件/消費/解除を含む3プロファイルの6戦闘が受付拒否。
- 1421ea2：実22戦闘が全一致。共通52実戦は51一致、拒否10成功。残る複合1入力を診断し、予約語汚染を特定。
- e0e0ae3：別の受付診断入口でその1入力だけを観測し、admission第3定義(kind1)の拒否を確認。通常入口のCUDA/MSLは1421ea2と厳密生成一致。正規化は改変していません。
- aa147f7/6ce5351：入力変換修正後は変更した1入力＋予約語負例1だけを実GPU実行し、[0,64]とCPU一致を確認。検証器importの初回停止はGPU0で記録し、import確認を追加。

63入力の集約は、1421ea2の保存62ブロックから変更していない51実戦＋拒否10を取り、最後の2ブロックを上記追加実行から取りました。集約自体はGPU0です。両実行の入力・全readback・source/evidenceと対応表を保持し、通常入口の厳密生成一致を橋渡しの証拠とします。同じsource/inputの再試行は0。実22戦闘の初回に成功した16件も全output wordを保持しました。

`seal-world-projectile-metal.py`、`portable-world-projectile-validation.json`、`audit-world-projectile-resources.py`がGPU/build禁止で保存出力と元CPUを監査します。旧21入口のCUDA/MSLも厳密一致。CPU全548＋追加のGPU禁止import確認1＝549検査成功です。各失敗のraw・報告・専用診断・修正前後の結果は削除していません。

## 未完了の範囲

全203＋お気に入り込み266プロファイルの入力変換成功は152→163、base108→116です。新規11はNeon: Vision Eye、Vesti、Laplace通常＋お気に入り1/2/3、Dorothy: Serendipity、Leona、Arcana: Fortune Mate、Power、A2です。入力変換はGPU admissionや戦闘認証とは別の指標です。未対応103、他のbuff/selector・操作・復活・source攻撃・interrupt、全変種・組合せ・長時間/容量、legacy Metal14c8e2eの未解明差分と、その後の効率化が残ります。full_character_verified=0、full_goal_complete=falseを維持します。

Windows v104は固定def167197c840d63457ce139f5f6131ce78dc491（codex/cuda-world-v104-source、26ファイル390810bytes）で共通63入力だけをBelowNormal/JobObject/start gate/180秒＋cleanup5秒で1回実行し、127.617560秒で成功しました。事前CPU27検査、native52、全input/output/generated指紋、API50段階、PID107896のpre所属1/post空・残留0/retry0を保存3JSON404357bytesのSHA一致と独立監査で確認しました。実22・旧65/1063・通常4682の再実行は0です。

実行中のモデル容量エラー後も既存OSコマンドは終了0で完了しました。結果だけを取得する後続turnはGPU/build0です。ただし終了後snapshotはJob終了から401.9489005秒遅れ、GPU直前から約529.973秒の観測窓で既存28件の欠落を確認しています。欠落は検証Job外の既存プロセスですが、GPU実行中の終了もGPUとの因果も証明できません。原因unknown、サービス識別unverified、calculation_verified=true、preservation_verified=false、総合passed=falseを保持します。別のCPUのみ約37秒の対照観測では、自身のvenv観測launcher1件だけが欠落しMCP欠落0でした。過去の7/14件の原因も解消扱いにしません。次回の短いWindows検証では、外部bounded wrapperのfinally内でwait直後に完全なafter snapshotを採取し、モデルの次turnを待たない方式が必要です。今回の観測改善目的のGPU再実行は行いません。詳細はportable-world-v104-cuda-validation.json、portable-world-v104-collection-finding.json、seal-world-v104-cuda.py。
