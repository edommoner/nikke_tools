# 乱数スキルのcritical・snapshot・queue

`coordinate-sampled-skill` は乱数物理射撃、通常damageスキル、`dealt_fixed_damage` を同じresident executorへ接続するprivate profile。CUDA／Metalは同じSlang・効果定義・入力・native比較器を使う。62入力（共通CPU59／拒否3）がM5 Metalの保存結果replay・独立sealで全一致した。保留バーストの乱数、武器変更／healとの合成、sampled group owner、全キャラ元定義認定・公開受付は残る。

## 実行規約

CPU正本はcast開始時にbuff・攻撃力・critical率・倍率を取得する。その後、hitごとにcriticalのuniformを1回消費し、named-hit通知の子スキルを実行してから親の次のhitへ進む。0%・100%でも抽選する。子がbuffを変更しても、現在castの計算因子は変更しない。別PART／INTERRUPT packetは本体のcriticalを再利用し、追加抽選しない。

この規約を既存の `sampleDamageFactorsForReach`、DFS frame、named-hit context、着弾queueへ接続した。最初のhitで計算因子を保存し、後続hitはその因子と新criticalから同じ順序のbinary64演算を実行する。深さ別の32slotを持ち、再入した子が親のsnapshotを上書きしない。slotは48wordで、sampled pellet領域とMETAの間の未使用1536word（914352〜915887）を再利用する。Runtime138952byte、入力109528／出力1507328wordを維持し、追加容量は0。

物理／スキル／条件の抽選は同じ既存MT列を順に使い、boss対象選択用MTとは分離したまま。固定親damageは既存経路を使い、criticalを引かない。main総計は前回のBODY／PART整数128bit sidecarを共用し、元の順序付きbinary64総計も引き続き検査する。

## 実証とtraceの修正

新22契約はcritical率、5段中のATK／率buff更新、子の2段攻撃、2射手、battle_start、係数0、periodic tick、core／armor-break／burst／attachment／sequential／split、通常攻撃式、PART／貫通／爆発、親量との混在を含む。22世界で物理91ペレット／121packet、スキル本体250回／target再利用72回、実着弾446packet、MT894wordを検査した。全戦闘状態・実packetの量／対象／順序／generation・物理MT全状態と消費数・named-hit子の条件を比較する。

最初の実GPUでは62中59入力が一致し、PART／貫通／爆発の3入力がskill traceのhit番号で停止した。3入力のbattle状態と総計は一致していた。既存CPU観測器は、実着弾packetを後から1,2,3と数えて番号を作っており、同じ親hitから出るBODY／PARTを別hitとして数えていた。GPUは親hit番号1を別PARTにも保持していた。

計算本体は変更せず、実CPUの `_coord_skill_hits` 呼出時に本体HitEvent、返却時にtarget HitEventと、外側の実hit-loop番号を受動記録した。着弾時に同じオブジェクトを追い、row／生成時刻／着弾時刻／amountが元traceと完全一致することを確認した上で番号viewを作る。最初の9packetは1,1,1,2,2,2,3,3,3となる。省略・別row・別amount・範囲外番号は拒否する。元native trace、native fingerprint、GPU raw、元失敗とclaimは保持し、期待値や生成コードの正規化は変更しない。

新しい固定host比較器で元readbackをGPU禁止replayし、62入力が全一致・独立sealした。通常パッケージでもCPU43検査、制御419検査（Windows専用1件skip）、packing／GPU禁止の共通CPU正本22契約が成功。実スキルGPUは1回のみ、比較修正版のGPU再計算0／同claim retry0。

旧39入力の全入力wordは同一。以前の `random-skill` 拒否1件だけを同じ入力の正例へ明示移行した。他の38入力はnative fingerprintと全229113856byte出力を完全保持し、旧10系統の生成CUDA／MSLも全byte保持した。一般の保持監査は旧負例1件の欠落を正しく報告するため、全39出力保持とは主張しない。

## source依存とcache

整数÷muzzleの独立probeが不要な戦闘本体までincludeしていたため、`binary64`・整数sum・整数ratio・probeの4ソースだけへ整理した。source閉包は125→4。無関係な戦闘効果の変更で数値probeの基準やcache identityを失効させず、必要な数値演算を変更した場合の厳密な失効は維持する。除外ルールやnormalizerの追加ではない。

4ソースの新固定パッケージで14045入力（正例14040／拒否5）が実Metal一致・独立seal。旧CUDA／MSL生成コードと全449440byte readbackも同一。数値GPU0.002343秒、既存Metalパイプラインcache命中・PSO0.000267秒。通常スキルの実GPU0.465029秒、初回PSO92.357225秒。現在のCUDA計算・CUDA cache命中は未取得で、Metalのcache命中をCUDA実証へ流用しない。今回の実GPUはスキル1＋独立数値1の計2回、Windows新依頼0。

## 共通CLIの監査経路

```sh
python scripts/nikke_gpu.py package --suite coordinate-sampled-skill --compact --out /tmp/new-skill.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-skill.zip --dest /tmp/new-skill
cd /tmp/new-skill
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-skill-cpu
python scripts/nikke_gpu.py model-check --out /tmp/new-skill-model.json
```

`reference --suite coordinate-sampled-skill-common --out /tmp/new-reference.json` はfull固定パッケージから実CPU22契約だけを実行する。既存の独立MT replay、実critical・target再利用、HitEvent生成番号を検査し、GPU／packingは0。compiler source証明書も登録した。full3124→compact1779の全残存record／byteは同一。

replay時、外部 `storage-check` のexit2を呼出側が無視してコピーへ進んだ。元の不合格receiptを保存し、完了後に全byte・SHA・inodeを維持した疎化で予備容量を回復した。再発防止としてreplay CLI自身にも、全コピーの非圧縮論理byte量＋1GiB予備の内部ゲートを追加した。不足時はrun失敗・storage・failure・artifactsを記録し、コピーと比較へ進まない。2件の故障注入を共通制御検査へ追加した。正常GPU起動の既存容量ゲートも維持する。

compiler証明書の初回準備では、最新のテスト登録で古いcompactを再解釈してguardに止まった。保存パッケージ自身の検証器を別のCPUプロセスで呼び、当時の厳密なregistry・全ファイルhashで検証するよう修正した。現在source一致と、保存Metalの独立再比較は引き続き必要で、古い証拠を現在へ付け替えない。改変時の拒否も検査した。分類テスト用の上流文書とarc基準を新suiteへ明示登録し、依存ガードを緩和せずpackage内のmodel-checkを利用可能にした。

今回のraw削除0、保護7source・core probability・数値本体・厳密normalizerは不変。元の失敗、容量不合格、監査停止、全raw／完全レポートはローカルに保持する。共有証拠は約594KBで、巨大な重複比較の完全版は場所とSHAを記録した要約を共有する。証拠一覧は `research/coordinate-sampled-skill-v1-evidence/inventory.json`、集約は `research/portable-coordinate-sampled-skill-checkpoint.json`。

次は保留バーストの抽選／queue、武器変更・heal、sampled group ownerと混合効果へ進む。全キャラ認定0／20model gap／UI CPU／public GPU closed／full goal falseを維持する。
