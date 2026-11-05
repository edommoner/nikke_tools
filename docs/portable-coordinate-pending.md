# 座標worldと旧形式B3保留の接続

共通Slangの既存pending executorから、座標worldの本体着弾・typed counter・吸血へ接続した。新入口は既存area入口をincludeするだけで、別のCUDA／Metal計算器、保留時計、金額計算、ターゲット選択を作らない。

## 正本の2経路を区別

元`calculator/timeline.py`では、B3の`bonus_damage`は`_pending_burst_dmg`へ入り、全バースト開始後に本体HitEventを生成する。この経路には`_coord_skill_hits`、部位・阻止対象選択、部位倍率がない。`land_in_full_burst`のopt-in効果は別の`_pending_landing_dmg`から通常のスキル着弾へ入り、座標選択を伴う。両者は同じ保留フラグとして処理しない。

新入口`world_coordinate_pending_entry.slang`は前者を許可し、既存の`landWorldPending`と`landWorldSkillReceipt`で本体を処理した後、座標snapshotのない旧形式receiptだけ追加座標配送を終了する。通常の即時／DoTは従来どおりsnapshotを必須とする。既存のpending定義検査（B3・flag・count等）、容量guard、公開coordinate受付は保持。後者のpending=2は拒否したまま。

## 実証

新suite`coordinate-pending`は既存area52入力を全て先頭に保持し、正本50＋拒否10の計60入力。追加8契約は旧形式B3の本体750、係数0、先行ATKバフ1500、後続ATKバフを除外して750、全バースト開始ATKバフ1500、部位出生・消滅と独立な本体着弾、部位分を含まない吸血でHP5075。正本fixtureのauthored effect lookupを維持し、原キャラの効果一覧と混同しない。

Apple M5のMetalで60入力が全word一致し、保存原本の独立CPU監査でsealした。GPUは1回のみ、実GPU時間0.027555秒、Slang2.425秒、cold pipeline7.191秒。旧52入力の約218MBの全raw、約22.6MBの入力、全sealed entryが完全一致。保存rawへの4種類のメモリ内改変（本体金額、対象kind、余分な選択、選択word数）を全て検出し、原本は変更していない。

最終固定packageは`fca106d7348f561652bdb1b3fdb3bc56fd7a85a3ff9a8a5d5598b4402c166bf8`。full2899→compact1605の全残存record／byte／goldenを照合。選択suite CPU33件と制御404件（Windows専用1skip）が成功。終了した新rawは4KiB単位でゼロ領域のみ疎化し、全byte／SHA／inodeを保持して242,868,224byteを回収した。削除・GPU再実行は0。

`world_attack_group_entry.slang`の旧81入力が使うsource closure、保護対象のCPU／binary64／厳密normalizerは変更していない。保存CUDA PTX／objectの出所はその旧81本体のままで、新しい座標pending入口のCUDA実証と混同しない。旧area入口のsource hashは今回の共通helper追加で変わるため、以前のarea52証明書は履歴として保持し、現在のsupersetには新60証明書を使う。

## 残る作業

座標選択を伴うopt-in保留は、既存queueのreceipt移動時に座標snapshotも移動する接続が必要。手動aim、座標物理弾、frameを跨ぐ世代交代、元定義の混合world、公開受付も残る。host trigのMac／Windows差は別の数値方針gapで回答待ち。新60のCUDA検証は未実施、WindowsのCPU監査回収依頼も送達未確認。全キャラ認定0、20gap分類、UI CPUを維持し、全対応完了とは扱わない。
