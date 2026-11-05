# ADD自爆と最終射撃の共通GPU接続

## 敵弾薬との合成：共通CPU契約

`reference --suite enemy-ammo-self-destruct-common --out NEW.json` は元ヴェルヴェット76定義の8条件を検査する。正本 `_retire(...,"자폭",...)` の時点で存在する実際のAttackHit objectを観測し、同じactor世代・同じframeでだけ退場後の弾倉へ配送する。HP撃破、時間切れ、別object、別世代、後続frameにはこの資格を与えない。既存EnemyAmmoのframe/attack/割合演算/完了通知/リロード処理を共用し、既定modelのself-destruct拒否は維持する。

単発0秒、間隔3発、同時3発、空弾倉、リロード中の最終射撃、until-cleared再出現、発射前HP撃破、時間切れを検査。弾薬で拒否されたattemptも元のscheduled counterを進め、自爆を延期しない。退場済み世代のreloadは完了しない。固定容量の明示モデルであり、ゲーム仕様の実測ではない。後続では出力所有権と退場後のqueue資格をSlangへ接続し、[専用合成入口のMetal実証](portable-enemy-ammo-self-destruct.md)に成功した。この節のCPU契約と、後続GPU実証の範囲を分けて保持する。

固定packetで8契約・新7unit成功。関連敵弾薬24検査・自爆wire8検査・readiness24検査も成功。旧goldenを変更せず、新CPU hookのexact inverseを既存監査へ合成。旧enemy-ammoのMetal証拠はself-destruct共有hook追加前の履歴であり、全現source一致という誤ったunit条件を、承認済みexact inverseによる全source保持検査へ修正した。現source再認定とは区別する。

初回参照のADD名二重prefixと、初回packetの未追跡module梱包漏れは失敗記録を保持し、別実行/別packetで修正した。共通CLIにはfull packetの全reference登録rootを梱包前に検査するguardを追加した。compact packetの全reference受付や動的import全closureを保証するものではない。

証跡 `research/target-count-query-evidence/enemy-ammo-self-destruct-native-contract-v1.json`。保護CPU4ファイル・GPU計算source変更0、この合成のMetal/CUDA認定とdefault受付は未完了。

専用CLI `add-self-destruct` の元実編成8条件＋不正6入力を、M5 Metalの保存出力とfresh GPU禁止独立監査で検証した。元ニヒリスター70定義、E.H.76定義を変更せず、18自爆/33射撃/165被弾の全戦闘・状態・通知を比較。通常/cache-onlyの14入力を登録した。実CUDA、敵弾薬との合成、公開default受付、全キャラ認定は含まない。

## 先に固定したCPU部品契約

共通CLI `python scripts/nikke_gpu.py reference --suite add-self-destruct-native --out NEW.json` は、固定されたcanonical BossScriptのbegin_frame/_add_attacks/_retireをそのまま呼ぶ。独自scheduler、CPU計算済みqueueをGPUへ渡す入力、正本の変更はない。単発、3発の間隔あり、同時3発、次frameで残り2発をまとめて回収する4条件を同じliteral factoryから実行し、入力と元メソッドの保持を検査する。

正本では最後のAttackHitをself.attacksへ入れた後、同じbegin_frame内でsourceを自爆退場させる。その呼出しが返る時点でsource.aliveはfalse、enemy_countはBODYのみの1、enemy_deathがeventsに存在し、最終射撃はqueueに残る。0秒の単発/同時3発ではspawnとdeathが同じ返り値に並ぶ。粗いframeでは残り複数発もqueueされたまま退場する。退場後のframeに余分な射撃や死亡eventは出ない。次frameでの被弾による破壊通知と同じ規則だと決めつけない。

GPU側では、現在のlive actor poolを読む既存ADD射撃cursor、WorldSchedule時計、既存死亡通知/敵数更新とincoming実行器を使う必要がある。最終射撃の生成を退場前に終え、その射撃のsource slot/generationは退場後も保持する。別世代へ再対象化したり、消えたsourceを理由に最後のqueue済み射撃を落としたりしない。until-cleared、HP撃破、再出現、同frameのbuff callbackとincomingの順序は、full battleのCPU契約を追加してからGPUで照合する。

このreference入口はCPU部品のみ。共通CLIのpacking/build/executeは0、full_battle_validation/gpu_supportedはfalse。既定ADD packerと敵弾薬モデルのself_destruct拒否は維持する。4unitには最終射撃削除/生存flag/死亡eventの改変負例、fresh CLI起動、canonical/observer source hashと未対応分類の結合検査がある。初回CLIはpinned calculator path初期化の不足で失敗し、その出力を保存。engine_worker経由で正規初期化する修正版で4条件が成功した。

証跡はresearch/target-count-query-evidence/add-self-destruct-native-contract-v1.json。Lock Onの未確定距離式を推測で埋めることなく、既存正本にconsumerがある次の実装候補として扱う。GPU受付・全キャラ対応数は増やさない。

## 共有actor/event実行器との接続

入力は既存ADD battleの116,464wordを使い、各rowの旧reserved4へself flag、5/6へliteral attack_at、7はreserved0を置く。新しい入口だけで許可し、既定入口の拒否を保つ。prefixを作る派生コピーからattack/self_destruct/attack_atを除いて別bankへ下ろし、元の静的atk順位も保持する。元case/効果/owner/武器/configは変更せず、CPUの発射時刻列・退場時刻列を入力へ持ち込まない。

既存nextWorldAddAttackへactual actor generation/alive/born+attack_atを渡す。最終射撃を全てqueueしてからpoolのalive/reason3を更新し、既存死亡数とenemy countを更新する。HP量を偽のdamageで0にする処理、別scheduler、別damage式は追加しない。全spawn/close通知後・incoming前にself死亡を配送し、既存actorStateDropGoneとincomingを通す。HP撃破用のdeferred通知数へ混ぜない。before-shot HP撃破と時間切れ退場では自爆を生成しない。

出力の既存ADD map末尾1872080からheader16＋2048×12wordの所有領域を使い、node/slot/generation/fired/time/WS_LOG record/notice配送を全件検査する。unused領域と他の全battle領域も既存比較器で検査。未発射でも生成済みのcursorはcanonical run.opens/_Add.firedと直接照合し、旧queue由来の仮定へ丸めない。共通比較器の追加fieldが無い旧caseの判定は維持する。Runtime stride138,952byteは不変。

元8条件は0秒単発、間隔3発、同時3発、until-cleared再出現、BODY混在、発射前HP撃破、時間切れ退場、E.H.死亡連動resource。E.H.では6件の死亡chargeを含む全dispatch、最終resource、timer発動回数を既存resource consumer/comparerへ接続し、最終scrap2/magazine2も一致した。元の全70/76定義を削らず、追加の合成効果も使わない。

## 実M5・失敗保持・保存結果の再照合

GPU source49a58f13のpacketd01a085dをM5で1回実行。unit38とCPU8基準の事前照合、required generation hit/Slang追加0の後、全正例status0・6不正status64。最初の比較はuint32 array sliceとlistの直接比較が原因で6caseを拒否した。失敗capture/claim/readbackを保持し、計算sourceや入力を変更して再実行していない。

比較器3998ad48はreceipt検査を分離し、実array/list両方と改変負例を追加した。新packetと元packetのgolden source/input/nativeが全一致し、既存replayがGPU/transport/canonical critical sourceと元claim/artifactを検査したうえで、入力/readback/generatedを同一filesystemのimmutable hardlinkで共有して14全件を再照合した。保存native値だけの診断ではcreation receiptが無いため既存guardが拒否し、fresh nativeで最初の全戦闘比較をやり直した診断も保持する。guardを緩めない。

replay captureをfresh GPU禁止childで独立sealし、同じ監査からfull-source certificateも生成。全14の計算が一致、GPU0.598816秒、cold pipeline58.053059秒、独立監査126.237991秒。GPU dispatch1/retry0/replay0-GPU/独立0-GPU。新しいnormal/cache CLIを登録し、source/receipt/golden/certificateを結ぶ検査を追加。台帳のUTF-8明示読取をCP932既定模擬の負例でも確認した。生成normalizerと保護CPUは変更しない。

## 次の範囲

敵magazineとの合成、攻撃付随debuff、全actor型/境界容量、現在のCUDA実機は未検証。既定GPU受付/UI CPUを変えず、全キャラ認定へ昇格しない。今回の一度だけの共有hook追加で旧ADD/敵弾薬等のraw source closureは変わったため、それらの現source再認定は別に残す。旧golden/成功記録は書き換えず、無差別な全履歴再実行もしない。以後の本体変更を新しいprivate runtimeへ置き、旧入口への不要なsource変更を避ける。Windows新実行依頼0。

証跡research/target-count-query-evidence/add-self-destruct-metal-v1.json、独立receipt tests/fixtures/add-self-destruct-independent-v1.json。raw/初回失敗/claim/両packetはpersistent proofsに保持し、GitHubへ送らない。
