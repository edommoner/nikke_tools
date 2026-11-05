# 遮蔽物DEFを元の戦闘へ接続するCPU契約

`python scripts/nikke_gpu.py reference --suite cover-defense-common --out NEW.json`

5人分の独立した基礎遮蔽物DEFを明示し、元の完全編成・効果・武器・育成・seedを保つ専用モデル。正本の4ファイルは変更しない。既存simulateの保持ASTを構造検査して、既存の被弾・分配・シールド・遮蔽物破壊の実行順へ量だけを渡す。別の時計・HP bank・carrier実行器は追加しない。既定の入力変換・公開GPU受付は開かない。

元攻撃対象の受けるダメージ倍率を既存の照会位置で一度だけ取得し、元の有効攻撃力と係数とともに、元分配ループへlocalsで渡す。既存のシールド吸収とそのcallbackが完了した後、実際の遮蔽物フェーズで受け手の`cover_def_pct`を既存`_live_sum`から読む。独立DEFで計算した量を元の分配人数で割り、現在の遮蔽物HPを上限として、元の減算と破壊callbackへ返す。本体・シールド・デコイの数量は元のまま。受ける倍率のsnapshot位置と分配方針は明示モデルの選択であり、ゲーム実機仕様の認定ではない。

元ソルジャーO.W.の30秒編成で、倍率発動前・発動中・失効後、貫通、破壊後の本体被弾を検査する。元センチ／ジャッカル混成ではシールドと3人分配を実際に発生させる。元定義数は通常69／混成67。4ケースの実被弾行は15／15／13／33、遮蔽物減算receiptは15／15／5／16。破壊ケースの最後の2攻撃は対象が既に死亡しているため被弾行がないことを、先行する死亡行と照合する。分配の受け手には独立した被弾行がある。固定の「15行」で履歴を切らない。

ハイドは元の操作実行器が全員同時には開始しないため、5人の操作・攻撃を0.5秒ずつずらして宣言する。分配先がまだハイドしている場合の追加の遮蔽物減算も省かない。receiptの`hp_after`は即時減算直後で、後続callback後の最終HPではない。hitの`damage`列は従来の本体量を維持し、遮蔽物DEFによる別量はreceiptに記録する。両者に旧来の同一量の収支制約を課さない。

9つの短い検査で有限基礎値、所有者、分配人数、受ける倍率の単一照会、シールドcallback後のlive読み取り、貫通gate、破壊後非照会、破壊通知順、構造変更の拒否、例外後のalias復元、保存receiptの故障注入を確認する。保存fixtureは監査に必要な部分だけで、全native／trace／inputの指紋は別に保持する。これは全battleの保存GPU比較や独立sealではない。

次は5つの明示基礎DEFを共通wireで運び、既存protection runtimeのシールド終了後フェーズへ共通binary64 helperを接続する。攻撃・係数・受ける倍率・分配人数は元のincoming frameへ保存し、callback後に再計算しない。現GPUソース／旧goldenはこのCPU接続では変更していない。Metal戦闘照合と独立seal、短いCUDA検証、ゲームの基礎DEFレベル曲線は未完了。先行の572入力のMetal数値実証を、戦闘接続済みの証拠へ読み替えない。

## 共通GPU接続の開発版

`cover-defense-battle`をdevelopment-onlyで登録した。入力115704wordは元115680word＋24wordの明示基礎DEFだけで、CPUの動的なHP/倍率/時刻を輸送しない。出力2048912wordは旧2032000wordを保ち、32深さ×16wordのsnapshot scratchと512件×32wordのreceiptを末尾へ追加する。Runtime/Frameのレイアウトと履歴容量は変えず、snapshotは実GPUイベント内で取得し、8→22→23→20と8→20の元経路で渡す。シールドcallback後のevent3で独立遮蔽物量を読み、元の減算/破壊/通知へ返す。新entryのみstat93を受理し、CPU正本/通常packerの拒否は維持する。

CUDA/MSLのpaired生成が成功（4.214565秒、Runtime138952byte）。旧entryの現sourceを別生成し、既存strict normalized CUDA ea6efec5…／Metal 1a6baa15…が完全一致した（3.827160秒）。新entryの実GPU計算、旧entryの新sourceでのGPU再認定とは区別する。共通wire/既定拒否/全receipt word/未使用領域/旧source逆変換を検査する。新しい固定packageのCPU全件照合・Metal実行・独立sealを終えるまで、戦闘のGPU対応済みへ昇格しない。

初回M5試行d7565091…は実GPU2.479757秒で終了したが4戦闘とも不一致。snapshotを入力用`loadNumber`で読んでいたため、攻撃/係数が0、遮蔽物量が1になっていた。保存raw/claimを保持し、既存の出力用`protectionNumber`へ修正した別packageで検証する。CPU期待/全11入力は同一であり、比較の緩和は行わない。修正後の`check_schema`には、command読み取りを基礎DEFの2箇所に限定し、snapshot深さが共通Frame容量32と一致することを事前確認するguardも加えた。3つのscalarを個別に誤った入力読み取りへ戻す負例を含む7wire検査成功。元M5試行の判定を後から成功へ変更しない。

## M5戦闘比較と独立seal

修正版23dec48a／package3ed9914b…が全11入力（native4／拒否7）に成功した。実GPU2.477718秒、cold PSO61.963661秒、全CPU事前照合73.244085秒。Runtime138952byteを保持し、全90,152,128byteを保存した。別fresh GPU禁止childの全11監査も88.794047秒で成功し、親oracle receiptの利用なし。4ケースの全戦闘・物理・typed・2,048行スキル履歴・51件の独立cover receiptを比較した。元d7565091…の失敗は保持。成功GPU1／比較失敗GPU1／同claim retry0。

通常は `package --suite cover-defense-battle --out NEW.zip` → `unpack` → 固定packet自身の`run`を使う。`cover-defense-battle-cache-only`は同じ計算/入力/goldenへ既存CUBIN/O1とpaired生成必須を要求し、欠落時のfallback compileをしない。Windows新依頼0、実CUDA/CUBIN hitは未確認。full-source certificateは既に完了した同じfresh独立監査と全golden/source/input/output SHAを照合してpure factoryで直列化し、追加native/GPU実行0。これはCUDA compiler/driver/cacheの証明ではない。

旧entryを修正版sourceから別生成し、CUDA ea6efec5…／Metal 1a6baa15…の既存strict normalized SHAを保持した。新Metal実行を旧entryのGPU再認定へ拡大しない。先行数値572入力、今回の明示モデル戦闘4入力、既定の未対応分類は別の証明範囲。

残件：今回の実GPU receiptは受ける倍率0・係数100だけであり、非ゼロ倍率、変動係数、遮蔽物復活との合成は未検証。次は元の被ダメージ倍率を持つ実編成を選び、同じentry/キャッシュで追加分岐を検証する。基礎DEFのゲームレベル曲線、canonical/default admission、全キャラ/全特殊効果、実CUDAは未完了。

最終登録f81f1c96の通常package cf3013a3…自身でも5群27検査と全11入力/4nativeのfresh CPU事前照合が成功（73.945042秒）。固定goldenはM5独立seal版と完全一致し、追加GPU0。自身のcompile-planもCUBIN/O1・2048MiB・60秒で成功したがcompiler/driver/GPU/claim0。実CUDAキャッシュの成功とは扱わない。

## 元Noahの倍率と変動係数（開発中）

`cover-defense-modifiers`は同じGPU entryの追加2戦闘＋拒否7入力。元SOW/Noah/Drake/Jackal/Mary全69定義を保持し、Noahへの64回の微小被弾を元multi-hit nodeで宣言する。元row12のreceived_hit_count:1／prob:10／全員−8%・10秒は変更しない。固定seed4301では0.6／1.8／5.2秒に3回発動し、各16cover receipt中11件へ非ゼロ倍率が届いた。phaseの係数は33.33／137.5／250で、cover DEF上昇との同時適用もCPUで成立した。

既存の受動source観測器の選択だけをNoahへ向け、元の完全nativeから追加receiptを除いたcanonical JSON指紋が観測off版と同一であることを照合した。初回のPython tuple対JSON listの比較失敗を保持し、CLIと同じcanonical digestへ比較方法を揃えた。数値・入力・確率・許容誤差は変更していない。GPUでは同じ全比較に加えて元Noah rowの実activation数を照合する。現段階はCPU確認のみで、追加2ケースのMetal/CUDA認定はまだない。旧11入力と全GPU sourceは保持する。

## 共通被ダメージ集計の1ULP差と再検証

Noah追加版9ca192a3…は生成/PSOの両必須cache hit、GPU2.505108秒/PSO0.002931秒で終了。貫通は全一致し、非貫通のJackal累計だけ200757.09142740333対200757.09142740336（1ULP）だった。全HP hitと32cover receiptは一致した。元native観測器がhit列の`sum`を返すのに対し、GPUの累計が逐次加算だったことを、実際のHP term列と既存共通`addSum`で確認した。許容誤差や元CPUを変更しない。

全incoming receiverの累計を既存共通補償和へ接続し、correctionを5個のuint64状態に保持する（Runtime＋40byte、Frame/input/output幅は不変）。Noah専用のreadback修正ではなく、通常/分配/全世界共通の集計。元のHP減算/通知/各hit量は変更しない。source逆変換で旧証明を保持するが、旧生成SHAのcurrent-source一致は失われるため新sourceの認定は未完了として扱う。追加cohortは旧4戦闘も含む6戦闘＋拒否7の全13へ拡張し、全件を新sourceで検証する。先行Goldensと失敗claim/rawは変更しない。

## 共通補償和の現sourceを全13入力で独立seal

固定a6b99c55/package2873d961…は旧4＋Noah2の6nativeと拒否7、全13でM5一致。実GPU2.522692秒/冷PSO61.843307秒、CPU事前116.050422秒。別fresh GPU禁止childの独立監査も139.948001秒で成功し、同じ監査からsource-only certificateを作成した。Runtimeは138992byte（＋40byte）、Frame/input/output幅は不変。全83cover receiptsと270被弾、Noahの元10%条件各3発動、−8% snapshot計22件、係数33.33/100/137.5/250を全比較した。

共通readback-retainで旧11入力のinput/native/output fingerprintと全90,152,128byteを完全保持した。値/履歴/比較項目は削っていない。旧11対応のスキル・スイート名`cover-defense-battle`は、現在は保持ケースを含む全13へ拡張する。`cover-defense-modifiers`も同一dataset/entry/goldenの別名。両cache-only版は同じ13入力にCUBIN/O1・compile cache・paired生成必須を適用する。新sourceの実CUDAとCUBIN hitは未確認、Windows新依頼0。古い4ケースだけのv1証明書は歴史として残し、現sourceはv2証明書へ明示的に切り替える。

旧9入力の集計差分試行は保持。今回の補償和source成功GPU1/同claim retry0、独立監査と保持検査の追加GPU0。公開/既定admission・ゲームの基礎DEFレベル曲線・全キャラ/全効果は未完了。次は他の優先未対応項目を進めつつ、cover復活等との未検証合成と、必要な短いCUDA検証を残す。
