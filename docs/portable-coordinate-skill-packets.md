# 即時の全部位スキルを共通Frameへ接続

共通CLIのsealed `coordinate-skills` を追加した。宣言モデル・期待値モードの19正本battleと5拒否入力、計24入力が実M5 Metalで一致し、保存結果をGPU再実行なしで独立sealした。通常／貫通／爆発の `hits_parts=true`、marker absent／falseの通常bonus、depth反転、破壊／不壊、同castの後続packet、吸血の子スキル、typed counterのrefreshと死亡を比較した。これは即時スキルの私的実証経路であり、通常UIや全キャラ認定の解放ではない。

## 固定するタイミング

正本はフレーム先頭で作ったGeometryをスキルへ渡す。途中で部位が壊れても、そのフレームのGeometryには残る。castの途中だけでなく、破壊後に吸血から生まれた子スキルもその部位を選ぶ。live poolを発動のたびに再選択する実装では、この正本規約を保てない。

共通world frameの境界で、前段階のselectorからGeometry相当の順序集合を作る。cast Frameのcursor0でその集合を固定し、enqueue時にpacket専用領域へコピーする。各68word snapshotは、順序付き最大127slotと32patternの完全な32bit世代を保持する。世代はbit圧縮しない。casterや子Frameが戻って同じ作業領域を再利用しても、発行済みpacketは変わらない。

ダメージの数量は既存の `sampleDamageFactorsForReach` と `damageFromFactors` を使い、body／part量をsampleしてから子通知へ進む。実着弾は同じ `land`／Actor pool、typed receipt、吸血dispatchを使う。新しいRuntime fieldは0。LandingReceiptのprivate profile限定local field1個と、既存1Mword出力の余白を使う。32cast frame、2048queued packet、4096着弾trace、65536word選択logの上限を超えればstatus64で拒否し、記録を切り捨てない。

## 消滅済み対象と子処理

正本 `hit_target` は消滅済み対象でもkindを返す。part総量と吸血は後続packetも処理し、poolのhits／dealt／landedは生存中だけ増える。この違いを共通着弾でも保持した。座標の対象packetを、非座標reach経路のextra hitに置き換えていない。部位packetごとにgateを通し、typed receiptと吸血をその順で実行する。座標targetでは非座標partのdamage accumulator加算を追加しない。

新しいCPU契約26番目では、HP54%条件を満たした吸血の子が、既に壊れたnearをGeometryから選ぶ。全量8800／HP5880、pool hit差分1,1,0,0を確認した。さらにGPU専用witnessでは、最初の部位hitでカウンタ閾値が発火し、その子がmarkerをrefreshした後、死亡が新epochを処理する。理由threshold→death、epoch1→2、credit1→0で、stale後続は二重発火しない。

native observerは正本の選択と実着弾を読むだけで、追加routeやgeometry再計算を入力へ供給しない。従来のbody skill traceが座標targetをBODYとして扱わないよう、この新profileだけbody traceと対象packet traceを分けた。全battleの既存比較に加え、選択時の順序付きtyped key・世代、着弾順／数量／owner、未使用log末尾を独立比較する。

## 入口と保持検査

```sh
python scripts/nikke_gpu.py package --suite coordinate-skills --compact --out NEW_PACKAGE.zip
```

入力は元効果とliteral座標。既存static graph compilerへ渡す形状表現だけをreach表現へloweringし、新しいcoordinate executorではreach選択を使わない。元のcoord付きcaseを正本で比較し、CPU trace・計算済み数量・選択済みリストはGPUへ渡さない。新kernelは同じSlangからCUDAとMetalを生成する。今回のCUDA実行は未確認である。

初回23入力も成功し、typed counter witnessを加えた最終24ではpipeline必須hit、GPU約0.01957秒。先行18正本入力の全entryとraw75497472byteを保持した。保存rawのkey世代、着弾damage／順序、末尾の4改変も拒否した。原rawは変更していない。

新hookはprofileのpreprocessor条件内に置き、旧16とmixed81も現在sourceで再検証・独立sealした。合計406847488byteのraw、入力、生成CUDA／Metalを全byte保持し、mixed81の両reflectionも全byte保持した。履歴source監査は正確な逆差分を登録し、任意編集の拒否を維持する。compiler-full--attack-group-mixedの証明書も共通CLIで独立更新した。生成CUDAが同一であることは保持したが、今回CUDA compile／cache hitの成功を主張しない。

final full2872→compact1581の残存全recordと全payload SHAを確認した。実行snapshotからの差はprojectionと証明書・golden更新で、GPU sourceと比較器は同一。最終compact CPU20件／24入力native19、共通制御392件（Windows専用1skip）、旧81 CPU52件が成功した。binary64・正本CPU・strict normalizerは変更0。4dispatchは新23、旧16、旧81、新24で、同一packageのretryは0。Windowsへの追加依頼は0。

## 残件

距離による通常範囲選択、Shape.dist/contains、通常武器の座標確率とRNG、保留／DoT、フレームを跨ぐ同名対象の世代規約、実キャラ全定義との組合せは未対応。新経路で物理着弾が発生すればstatus64とし、単一対象へのfallbackをしない。フレーム跨ぎで保存世代と一致しないpacketも拒否する。公開coord guard、全キャラ認定0、残20分類、通常UI CPU、ゴール未達を維持する。

証拠はresearch/coordinate-skill-packet-evidence/、固定値と次段階はresearch/portable-coordinate-skill-packet-checkpoint.json。Windowsの以前のPTX結果はunknownで、今回は接続を再観測せず、GPUの再依頼もしていない。保存領域の不足は、完了済み3captureのゼロ領域疎化で合計1567010816byteを回収して解消した。全byte／SHA／inodeを保持し、原本削除は0である。
