> 続き: 即時全部位のproducerと着弾接続を[座標skill packet](portable-coordinate-skill-packets.md)へ記録した。以下はpool読取り段階の履歴。

# 座標selectorから共通戦闘poolへの直接接続

共通Slangの座標selectorが、既存戦闘実行器の16word actor poolを直接読むようにした。新しい `coordinate-world-pool` 16入力（正本battle11、不正入力5）が実M5 Metalで成功し、GPU再実行なしで独立sealした。専用poolへのコピーや新しいRuntime状態は追加していない。既存の8word component viewも同じselectorを使い、旧21入力の全出力を保持した。

## 今回の証明範囲

実行するbattleは既存の非座標reach経路である。座標は別のliteral descriptorとして入力し、battle実行後・終了処理でpoolを閉じる直前に、その実poolのlive／generation／出生時刻を読む。CPU側は実正本battleをそのまま走らせ、finish直前の状態を別オブジェクトへ読み取り投影し、正本 `_apply_geom` で順序を決める。元BossScriptの状態や正本計算を変更しない。期待する対象リストやbattle traceをGPU入力へ供給しない。

つまり、**状態の読み取り接続は成立したが、座標集合をskill packetの生成・着弾へ渡す接続は未完了**。座標battle全体や実キャラの全効果対応を証明したものではない。公開coord guardと20未対応分類、全キャラ認定0、通常UI CPUは維持する。

部位とprivate interrupt、破壊後の空集合、不壊、2hit、再出現後の世代2、出生時刻による順序、同patternのordinal、depth反転を比較した。descriptorのkind／ordinal／HP／個数／slotが実bindingと違えばbattle前に拒否する。pool viewはdescriptorのworld slotから `actorPoolAt` と同じ領域を読み、出生時刻offset8を使う。BODYはdescriptorへ含めない。実際の戦闘全体の既存decoder比較と、追加の262144word領域の全word比較を両方行う。

最終16入力はGPU約0.01845秒、pipeline必須hit、library読込約0.00234秒だった。初版13入力も成功したが、birth／generation境界を加えた16を最終基準とする。保存rawのactor世代、座標slot／世代、末尾の4改変は全て拒否し、原raw SHAは不変だった。

## 旧profileとCUDA準備の保持

新profileの出力は既存上限の1048576wordを使う。初案の2倍strideは既存guardがGPU前に拒否したので、guardを緩和せず、generated schemaへ新profile用の条件1個を追加した。履歴source監査の固定逆差分もこの1条件だけを登録し、任意の未レビュー編集の拒否テストを保持した。

schemaは共通sourceであるため、mixed81を現在のsourceで再検証し独立sealした。以前の入力、全81のnative／output指紋、raw339738624byte、生成CUDA／Metalと両reflectionの全byteが一致した。pipeline必須hit、GPU約11.656秒。既存goldenはsource identityのみ更新した。旧21も全input／native／rawを保持して独立sealした。binary64、正本CPU、strict normalizerは変更していない。

全ソースcompiler基準は、最新の独立監査済みmixed81から共通CLIで作成した `compiler-full--attack-group-mixed` を使う。旧 `compiler-full--attack-group-long` 証明書はschema追加前の履歴として保持し、現在のsourceへ流用しない。新証明書はsource identityだけを証明し、CUDA compile／cache hit／実行成功を意味しない。生成CUDAの全byteが旧実証と同じなので、保存cacheの内容は引き続き既存の厳密keyで照合できるが、今回のWindows cache hitは未確認である。

## 再利用可能な入口と残件

```sh
python scripts/nikke_gpu.py package --suite coordinate-world-pool --compact --out NEW_PACKAGE.zip
python scripts/nikke_gpu.py package --suite compiler-full--attack-group-mixed --out NEW_COMPILER_PACKAGE.zip
```

final full2866／compact1575の残存全recordと全payload SHAを検査した。実行packageからの差はCLI・projection・監査fixture・compiler証明書テストと証明書登録で、GPU source、input、native、比較器は同じ。最終compactでCPU16と正本11／16入力、共通制御392（Windows専用1skip）が成功した。旧mixed81はCPU52成功。初回のstride、source監査、古いcompiler証明書の停止も保存した。既存ファイルのゼロ領域疎化で1206886400byteを回収し、全byte／SHA／inode／証拠を保持、原本削除0。

次は座標正本の選択タイミングで部位集合を固定し、Frameのpacketへ渡す。正本は同cast内の先行packetで対象が消滅してもkindを返してpart総量へ計上し、消滅poolのdealt／hitsは増やさない。この違いと通知・吸血順を保持する必要がある。今回の終了直前snapshotでは、そのproducer／着弾契約を検証していない。形状距離やhypot／三角関数も未実装のままである。

Windowsの保存PTX結果は接続利用不可のためunknown。今回の新規依頼・再実行は0。4回の新Metal dispatch（13、16、旧21、旧81）は別packageの検証で、同一packageのretryは0。検証記録はresearch/coordinate-world-pool-evidence/、固定値と残件はresearch/portable-coordinate-world-pool-checkpoint.jsonを参照。
