# 敵弾薬の共通実行契約

前提producerは`add-attack-battle`として実actor poolと既存incoming damageまで接続し、元ニヒリスター70定義の17入力をM5/独立監査で実証した。敵弾薬の充填・消費・リロードをその実戦queueへ結ぶ作業は未完了。[接続済みの範囲](portable-add-attack-battle.md)。

GPU本体はADD自身の射撃をまだ拒否するため、その前提producerを`add-attack-schedule`として先に実装した。元graph時計とCUDA/Metal共通cursorで187発/19入力をM5＋fresh独立監査まで実証。死亡は部品用の明示刺激であり、本体actor pool/HP・弾薬消費との接続は未完了。[生成部品の境界と次の接続](portable-add-attack-schedule.md)。

`reference --suite enemy-ammo-common --out NEW.json` は、ヴェルヴェットの元76効果・実武器・育成・owner順を保持した6つのCPU契約を実行する。既存のlogical collider/world actor実行器を使い、元の敵攻撃関数へ実際に配送し、味方への被ダメージ・HP記録まで照合する。元データや既定CPU入口を変更するものではなく、GPUへの接続は未完了。

`app/enemy_ammo_model.py` はBODY/ADDの既存handle/generationに、明示した容量・初期残弾・リロード秒数を結び付ける。既存の`boss.begin_frame`を一度だけ呼び、そこで作られた攻撃オブジェクトと当時の世代を保持して、元の配送位置で残弾を消費する。ADDの`AttackHit.source`は表示名であり、world actorの`ADD_PREFIX`付きlabelへ変換する。未知のsource、失われたqueue identityをBODYへ代用しない。古い世代の発射は新しい同名ADDの弾を消費しない。

割合演算はnative `handle_ammo_charge_pct`のコード本体をそのまま使う。closureのうち対象解決と残弾状態だけを差し替え、コードidentityとfreevar集合を検査する。`round(capacity * (value / 100))`の除算→乗算→ties-to-even→加算→clamp、満装填時の元リロード中断、名前付き完了通知が受取対象loopの後に一度出る規則を保つ。空の受取集合でも名前があれば完了通知は出る。元のリロード中断関数は`full_reload`通知を発行しない。

今回の6契約は、Lv10/-5%とLv1/-2.95%（容量16でそれぞれ-1/0発）、遅延出現時の空集合、再出現、撃破後の空集合、BODY射撃。弾切れ後は次の元の射撃試行でリロードを開始し、期限以後の最初の元frameで全装填する。リロード中の元試行は消費せず配送しない。元の射撃予定やfired counterを動かさず、後へ再予約しない。この宣言モデルはゲーム中の敵リロード周期を確定するものではない。

容量固定以外の武器変更・容量バフ・flat充填・強制リロード、self-destruct敵の発射時刻規則は未対応として拒否する。取り込む割合効果の敵selectorは`all_enemies`に限定する。既定のcanonical敵状態、全キャラ、Metal/CUDA、公開GPU受付の対応へ読み替えない。未対応監査とreadinessにはこのopt-in CPU契約を別欄で示し、既定入口の不足flagは維持する。

次の共有GPU接続では、既存`applyAmmoInstant`のsoft-binary64数値演算を再利用し、既存world actor generationとframe/敵攻撃producerへ資源状態を接続する。別の敵scheduler・独自丸め・別GPU専用のスキル定義は作らない。wire/容量/履歴所有権の監査、CPU preflight、固定Metal実行、独立sealが必要。現Windowsの保存結果は接続エラーで取得できず、新しいCUDA実行や再送はしていない。

固定b8416750/package39a7382f…へ梱包し、別展開先をcwdにしたown CLIでもCPU6契約（2.641秒）と新規8検査が成功した。checkoutとの全input/native/trace/contract指紋が一致し、実行後にも全3,816 payload fileをown `verify_package`で検証した。元のenemy-healing計算suiteを梱包containerとして使っただけで、今回そのMetal14入力やCUDAを再実行したわけではない。小さな梱包証跡は`research/target-count-query-evidence/enemy-ammo-frozen-cli-receipt-v1.json`、完全reportとZIPは永続proofに保持する。
