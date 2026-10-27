# 元のB2・回復・デコイを実被弾へ接続

`original-catalogue-incoming`は元Red Hood/Cinderellaの30秒4条件を、既存catalogue/compiler/共通CUDA・Metal実行器へ渡すsealed suite。元の全effect/owner順/実武器/育成と5人編成を保ち、BODY-owned HP shield1個の宣言worldへliteralな敵攻撃を追加する。damage計算、防御・回復・デコイ、対象選択、時計、元バーストの実装は複製しない。

| 条件 | 元編成の全定義 | 必須の実行確認 | 全skill履歴 |
|---|---:|---|---:|
| Red Hood B2 | 81 | 1/4/14秒のslot3攻撃が、効果中の4秒だけ本人へ転送。実被弾後に吸血回復 | 6 |
| Red Hood auto | 81 | 同じ編成・敵攻撃で、元オートは3回ともslot3へ着弾 | 7 |
| Cinderella chipped | 74 | 4/4.1/5秒の3発ともデコイが吸収、HP被弾なし | 102 |
| Cinderella broken | 74 | 4秒にデコイを破壊、4.1秒にHP被弾、元burstで復帰したデコイが5秒の攻撃を吸収 | 102 |

Red Hood B2の操作は前のrole suiteと同じliteral B1→B2→B3指定。元input identityを検査した後にcopyして適用し、`original_controls_preserved=False`を記録する。対照は元オート操作。発動/失効、被弾対象、回復量はCPU/GPUが実際に計算する。CPU側の必須条件は実hit owner/HP/吸血returnから判定し、そのnative全指紋とGPUの全状態/実traceを既存比較器で照合する。GPU全post-tick burst stateと実cast owner/stageも既存契約を使う。

デコイの正本規約は、吸収した一発全体を止め、余剰を同じ一発のHPへ流さない。破壊の証明は「元decoy容量を超える一発」「同一発のHP0」「次弾はdecoy0/HP正」「元burst後はdecoy正/HP0」の組合せ。元の4.233秒のburstは変更しない。これはCPU正本との一致であり、デコイ/遮蔽物の層規則自体のゲーム実機認定ではない。4秒〜4.233秒の不在期間には3秒周期のmaxHP条件判定が無いため、そのFalse分岐の認定でもない。

初版は同一発の余剰がHPへ抜けるという検査側の誤りでCPU停止。次版は5秒にもデコイが無いと誤って要求し、元burstによる復帰でCPU停止した。元の保存GPU記録からburst時刻を確認し、破壊と復帰の間のliteral4.1秒攻撃を追加した。元effectやburstを抑止せず、5秒の攻撃も復帰確認として保持した。GPU前の失敗2件はprivate診断と小さな公開証跡に保存し、成功へ書換えない。

固定05cc2d69/package854ea3ad…は20群178unit、CPU照合81.73秒、M5 GPU3.82519秒、fresh GPU禁止独立監査94.51秒で全4成功。独立監査はlive-parent再利用False、GPU追加0。実GPU1回/retry0、生成/Metal必須cache hit、Slang0/追加archive compile0、PSO0.00311秒。生成CUDA/MSLと両reflectionは前role cohortと全byte同一。input115680/output2032000word、Runtime138952byte、全履歴容量は不変。全skill217行を厳密比較し、物理履歴は従来の全順序semantic SHAと保持prefixを使う。未保持後半を個別全行比較とは呼ばない。

`package --suite original-catalogue-incoming --out NEW.zip`→新規unpack→固定packet自身の`run`を使う。`original-catalogue-incoming-cache-only`は同じ計算/入力/golden/比較器へ既存CUBIN/O1・paired generation必須を適用する。CUDA実機/実CUBIN hitは未確認。Windows新run/再送0、旧transaction終端不明の扱いを保持する。

未対応分類の追加確認では、AnnとVelvetの失敗は元本人の敵向けoperatorであり、味方rank selectorの欠落とは異なる。前者は`heal_received_pct/all_enemies`、後者は`ammo_charge_pct/all_enemies`。敵側consumerを確認する前にallyへ読み替えない。`cover_def_pct`は元正本のSCOPED_INERTに含まれるため、対象上位3人の受付だけで対応済みにしない。出所は`original-entry-next-blocker-triage-v1.json`。静的分類をGPU実証件数へ加えず、元inventoryの母数は不変。

任意選択は元1,064＋role4＋incoming4の1,072名。別のprofileを追加した数ではない。混成BODY/PART/ADD/typed world、元周期条件のFalse側、他のprofile/育成、canonical不足、全キャラ/全特殊効果/公開GPU受付は未達。証跡は`research/target-count-query-evidence/metal-original-catalogue-incoming-v1.json`。
