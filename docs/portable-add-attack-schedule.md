# ADD射撃の共通生成部品

後続の`add-attack-battle`は同じcursorを本体の実actor poolへ接続し、元ニヒリスター70定義の17入力・284発・1,120被弾がM5と独立sealで一致した。単独componentの刺激モデルをHP実証へ読み替えたものではなく、別の実戦captureで検証している。[実戦接続と残件](portable-add-attack-battle.md)。

登録6fde3ca2の通常/キャッシュ専用固定packageはunit-check12/21成功。キャッシュ版のCUBIN/O1・2GiB・60秒compile-plan成功（compiler/GPU0、実コンパイル成立の証明ではない）。既存GPU421ファイルと保護CPU4ファイルのbyte保持、旧enemy-healingの登録sourceが現状と一致することも確認した。記録は`target-count-query-evidence/add-attack-registered-cli-checks-v1.json`。Windowsの既存保存結果statusはhost unavailable/durableで、追加run/再送なし。

敵弾薬の全6 CPU契約をGPUへ接続する前提として、ADD自身の射撃producerが不足していた。既存`compile_schedule`は`Summon attack lifecycle is not connected`として拒否する。本体の受付を開く前に、既存graph時計と元`BossScript`の実AttackHitを比較する`add-attack-schedule`を共通CLIへ登録した。

`gpu/world_add_attack_cursor.slang`の`nextWorldAddAttack`は、呼出し側から実generation/alive/bornを受け、2wordのgeneration/firedだけを所有する。元と同じ`born + index * interval`と既存`wsReached`を使う。新世代でindexを0へ戻し、生存中のdueだけを順に取り出す。Pythonで計算した発射リストや出現時刻はGPUへ渡さない。CUDA/Metalは同じSlangを使い、Runtime本体や旧GPUソースの変更はない。

部品検証の入力は既存graph＋静的なADD数/hits/interval。共有host packerは原パターンを保持し、まだ未接続のattack部分だけを別の明示bankへlowerする。デフォルトの`compile_schedule`を緩和しない。probeは既存`wsBegin`へframeを与え、node宣言順でBODYとADDを混在させたqueueを作る。死亡は明示clear-mask刺激であり、実戦のHP撃破や弾薬の影響を認定しない。self-destructは発射と退場の順序が別途必要なため現時点で拒否する。

8正例は敵弾薬world由来4graph、BODY/ADD混在とclear後の同frame再出現、疎なframeでの追いつき、rational時計、期限とdueの同時刻競合。元`BossScript.begin_frame`が作った187個のAttackHitから、発射元node/slot、世代、index、binary64時刻、全順序を独立して観測する。graphの最終状態・履歴・遷移順と未使用領域も比較。11 raw拒否を加えた19入力をM5 Metalで検証し、fresh GPU禁止childの独立監査でも全一致した。

固定39a1908b/package468ff5fb…はGPU0.008248秒、PSO0.115794秒、readback5,643,456byte、独立監査1.487986秒。初版は全発射queueが一致したが、finishが生存ADDを退場させた後のcleared診断1項目が不一致だった。caller側の終了時liveness処理を修正し、別packageで再検証した。初版失敗/claim/rawは保持。さらに初回のresident専用generation-cache指定は事前に拒否されcapture未作成だったため、standalone指定へ修正した。既存goldenや比較器の不足項目を除外して成功へ変えていない。

通常の`package --suite add-attack-schedule`はsealed期待を使う。`add-attack-schedule-cache-only`は同じsource/input/golden/比較器に既存CUBIN/O1必須・NVRTC禁止を適用する。standaloneなのでresident用`--generation-cache`/full-source certificateは付けない。現CUDA実機や実CUBIN cache hitは未確認で、Windowsへ新規実行依頼は出していない。

次は既存actor poolの実生存/世代をcursorの入力へ結び付け、既存world incoming damageへ発射元付きqueueを渡す。BODY/ADDを別pass配送して順序を変えない。元の弾薬CPU契約と同じく発射試行を後へ再予約しない。`applyAmmoInstant`の数値部分を共有したまま敵資源へ接続し、敵対象を味方5人maskへ代用しない。現本体のADD射撃・敵弾薬・公開受付・全キャラ対応は未完了。
