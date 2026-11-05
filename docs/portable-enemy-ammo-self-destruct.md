# 敵弾薬と自爆ADDを同じ実行器へ合成

固定packet `2d5ad371…` の全16入力がM5 Metalとfresh GPU禁止独立監査で一致した。元Velvet76定義を保持し、14自爆・26射撃試行・弾薬許可18発・実被弾90件を全比較。GPU0.803771秒、cold pipeline58.212479秒、独立監査144.576577秒。GPU dispatch1/retry0、独立GPU0。input7,528,452byte/readback130,048,000byte、Runtime stride138,952byteは不変。

通常入口と `enemy-ammo-self-destruct-cache-only` を登録した。後者は同じ計算/goldenのCUBIN/O1・NVRTC禁止・paired generation必須。CUDA/Metal生成とreflectionは対で成功し、実runではgeneration必須hit/Slang追加0。初回の生成専用準備はSlang2回であり、実CUDA compiler/driver/launchの認定ではない。

`enemy-ammo-self-destruct` は元ヴェルヴェット76定義、実武器・育成・owner順を維持する8条件と不正8入力。既存のADD時計、actor pool、退場・通知、割合弾薬演算、reload、incomingと全戦闘比較を共用する。ゲーム内の敵弾薬容量を確定するものではなく、固定容量を明示した私有モデル。既定のADD/敵弾薬入口による自爆の拒否は維持する。

入力117,632word・出力2,032,000wordは既存敵弾薬入口と同じ。ADD rowのself flag/attack_atとliteral magazine bankだけを下ろし、CPUの発射・退場・弾薬量の時系列は入力しない。Runtime構造体は変更しない。

出力は既存弾薬/全4096 resource履歴の直後1,943,776wordから、自爆header16＋2048×12wordを所有する。従来の自爆入口と異なる配置を専用schemaで宣言し、記録を相互上書きしない。比較器は自爆記録・未使用領域を全検査してからその所有領域だけを消去し、弾薬/リソース・既存全battle比較へ接続する。

元のscheduled attemptsを全てqueueしてから自爆する順序を維持する。退場済み射撃元を許可するのは、actorが同じgenerationのreason3退場、実WS_LOG射撃が同じnode/time、自分の同時刻自爆recordより前、shot indexが退場fired数未満、死亡通知配送済みの場合だけ。HP/time退場、別世代、別frameは許可しない。弾切れ・reload中でもscheduled counterと自爆時刻は変わらず、実incomingを生成するのは弾薬で許可した射撃だけ。ammo eventの旧reserved11に退場queue資格を記録し、既定decoderは引き続き非zeroを拒否する。

CPUの元8契約は全て確認した。通常unitで同じ8戦闘を再計算する重複は避け、wire/所有権/監査のunitと、固定packageのfresh native準備・実run前照合・独立sealを区別する。旧goldenや正本を新しいGPU出力へ合わせて書き換えない。共通hookの変更は別exact inverse台帳で既存監査へ接続し、履歴sourceを現source認定へ読み替えない。

新golden/独立receiptと、同じsealから作ったcompiler-source-only証明書を登録する。後者はsource/generatedとbaseline golden hashを結び、入力ごとの計算成立を単独で保証しない。実Metal計算の証拠はgolden/独立receiptへ分離する。

証跡は `research/target-count-query-evidence/enemy-ammo-self-destruct-metal-v1.json`、独立receiptは `tests/fixtures/enemy-ammo-self-destruct-independent-v1.json`。CUDA実機・公開default受付・全キャラ認定は未完了。元CPU4ファイル、pinned upstream、生成normalizerは変更しない。Windowsでは既存のGPU前失敗claimを維持し、この合成のための再コンパイル/再実行は依頼していない。新rawと固定packetをpersistent proofに保持し、GitHubへraw/バイナリを送らない。
