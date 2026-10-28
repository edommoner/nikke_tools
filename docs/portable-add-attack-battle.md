# 実actor poolから共通被ダメージ実行器へのADD射撃

旧v1最終登録4542661bの通常/キャッシュ専用固定packageはunit-check35/44成功。関連82検査成功、sealed生成の必須cache hit/Slang0、現source-baseline一致、CUBIN/O1・2GiB・60秒compile-planも成功した。追加GPU/実CUDA compileは0。Windows既存chatのstatus取得はhost unavailable/durableで、新run/再送なし。証跡`target-count-query-evidence/add-attack-battle-final-cli-v1.json`。

旧v1固定17入力のM5実行は全一致（GPU0.692924秒、冷PSO58.330511秒、readback138,176,000byte）。34unitとfresh CPU6編成の事前照合、必須生成cache hit/Slang追加0、Swift/reflectionの実stride138,952byteも検査した。fresh GPU禁止childによる全17入力の独立sealも106.091323秒で成功した。計284発と1,120被弾の全履歴を既存比較器で照合し、通常登録goldenをこの独立結果から作成した。証跡`target-count-query-evidence/add-attack-battle-metal-v1.json`、監査`tests/fixtures/add-attack-battle-independent-v1.json`。

旧v1作成時、既存敵回復入口を当時のsourceで再生成したCUDA/MSLは、過去の実GPUcaptureから全raw byteが同一。新機能guardが無効な計算の保持を確認したが、旧goldenを新raw source hashへ書換えず、現source再認定とCUDA compile/cache実機証明は別に残す。

`add-attack-battle`は既存`nextWorldAddAttack`へ実actor poolのgeneration/alive/bornを渡し、元のworld incoming実行器へ接続する開発入口。単独componentで使ったclear-mask刺激を本体へ持ち込まない。HP撃破、元のsource graph、同名ADDの新世代は既存poolと`wsBegin`が所有する。

元スケジューラが作ったBODY射撃を一度数え、同じframeのnode順でBODY/ADDを既存WS_LOGへ並べ直す。別の時計や被ダメージ式を追加しない。実slot/取得時generationは並行する明示mapへ保持し、ADD用descriptorは専用bankから既存`incomingCommandAddress`へ供給する。対象選択、乱数、通常/貫通、shield/cover/HP、被弾通知は既存のまま。元CPUはADDの攻撃力低下を適用しないため、その制約も維持する。元CPUはframeでqueue済みの攻撃を途中のHP死亡で自動削除しない。新しい発射試行だけがframe先頭の実生存状態に従う。

入力はlogical prefix115,680word＋静的ADD descriptor784wordで116,464word。出力は既存2,032,000wordの未所有tailにheader/一時BODY集計/128slot×2word cursor/2,048ログ×slot・generationを割り当てる。Runtime構造体は拡張しない。元のeffects/育成/実武器を変更せず、既存host packerがまだ拒否するattack欄だけを別bankへlowerする。既定graph/actor compilerの拒否は残す。self-destructの退場順、攻撃付随debuff、敵弾薬はこの入口へ含めていない。

元ニヒリスター全70定義を保持した6編成は、生存、実HP撃破、時刻による再出現、BODY/ADD混在、random2人、slot2/4＋貫通。元AttackHitのnode/slot/generation/index/timeと全incoming HP履歴を既存の全戦闘比較へ追加する。raw11拒否を加えた17入力を固定44a543f8/package52b7150c…へ梱包した。元CPU6編成の観測と関連34検査、CUDA/Metalのコード生成、M5戦闘実証と独立sealが成功。固定packetの必須paired generation-cache hitも確認（Slang追加0）。

`add-attack-battle-cache-only`は同じ17入力/source/golden/比較器に既存CUBIN/O1必須・NVRTC禁止・paired generation必須を適用する。敵弾薬の資源状態や全キャラの受付を開く登録ではない。現CUDA実機、実CUBIN cache命中、self-destruct、攻撃付随debuff、全キャラの認定は残る。

共有4shaderとbackend stride登録の変更は、`PORTABLE_ADD_ATTACK_BATTLE`でguardした正確なbefore/after ledgerに記録した。既存source監査はその逆変換を検査してから過去の監査へ進む。生成code normalizerや保護CPU4ファイルは変更していない。逆変換は過去sourceが現raw closureと一致することや、新しいCUDA/Metal計算成功の代わりにはならない。旧registered source/goldenの現状再認定は別作業として残し、履歴goldenを一括で書換えない。

## 共有数値・resource hook変更後の現source再認定

固定a1881e09 / packete9ce00dcの元17入力をM5 Metalで1回実行し、fresh GPU禁止childで全出力を再照合した。元ニヒリスター全70定義/6編成、284発/1,120被弾と11拒否を維持。全旧input/native/各entry/readbackの138,176,000byteが完全一致し、Runtime138,952byte不変。unit35成功。実GPU0.6943365秒、cold pipeline58.155649秒、独立監査104.990122秒。実行時required generation hit/Slang0。新しいv2 goldenとfull-source certificateは同じjoint sealで作成し、旧v1は不変で保持。通常/cache-only登録と未対応分類の証跡参照をv2へ更新した。現在のCUDA実機は未確認、Windows新依頼0。

次の未対応self-destructについて、共通CLI reference --suite add-self-destruct-nativeで正本4条件を観測できるようにした。最終射撃をqueueした同じbegin_frameで退場/死亡event/敵数更新が起きるため、退場後の生存判定でqueue済み射撃を消してはいけない。これはCPU部品契約で、GPU/全戦闘/ゲーム仕様の認定ではない。詳細portable-add-self-destruct.md。再認定の証跡はtarget-count-query-evidence/add-attack-battle-current-recert-v2.json。
