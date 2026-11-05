# 盾混在時のbody蓄積と固定量放出

HSI6は `body_accumulation=True` と既存のbody吸血policyを明示した単一bossモデルです。bodyへ届いた攻撃だけが正本と同じ着弾→吸血→蓄積へ進みます。放出は既存のpool take・split倍率・整数化・landing queueを共用し、着弾時点の盾へ固定量を渡します。放出量へATK・DEF・crit・盾倍率を再適用しません。正のpoolが整数化後0になってもhit盾の1命中を消費します。

物理攻撃と放出は同じ `destructibleNotifyShieldReceipt` で対象命中・破壊通知を実行します。放出専用の一時packetは既存Frameと武器bankの間に配置し、128攻撃の上限に従い、同期子通知の帰還後に消去します。CPUからヒット列・数量を入力せず、SlangのCUDA／Metal実装は同一です。ソフトウェアbinary64・量core・strict normalizer・保護CPU4ファイル・pinned upstreamを変更しません。

検証入力は元トロニーを含む全定義実編成の3／30秒×HP盾・hit盾・破壊後bodyの6編成と、明示したpoolの正量／整数化後0×HP／hit×3／30秒の8編成です。後者は宣言効果の検証であり、実キャラ全定義への対応認定には使いません。元ドロシーは貫通付与も含むため全定義を維持したまま拒否します。旧HSI1〜5へ蓄積受付を開放しません。

最初のCPU事前検査は全14編成を単体テスト内でも重複計算して90秒で停止しました。失敗capture `/tmp/nikke-body-accum-cpu-v3` とGPU未実行を保持します。単体テストを短い正量／整数化後0の観測器検査へ整理し、独立した全14編成のnative照合はpackage／runの必須工程に残しました。修正版の単体6件は約6.9秒で成功しました。時間上限は増やしていません。

## 実GPUと観測器

開発18入力はApple M5で全件Metal／native一致しました。GPU4.661352秒、初回pipeline65.796364秒、library1.580384秒です。初回のnative事前照合は153.024467秒かかりました。全Python call／returnを監視する観測器が、大きなcode objectを毎回辞書キーとしてhashしていたためです。監視する4関数のcodeを強参照で保持し、そのidentityによる検索へ変更しました。追加のnumeric query・callback・演算変更はありません。全14編成のnative指紋は固定した変更前パッケージと一致し、変更後の入力準備＋14編成照合は21.366225秒でした。工程と実行負荷が異なるため、厳密な速度倍率とは扱いません。新版単体6件は1.659秒、保存raw検査を加えた7件は6.036秒で成功しました。既存蓄積参照10検査も3.343秒で成功しています。

実raw4blockのstatus・累積healing・固定量・metadata・delivered credit・実消費量・pool／archiveへ24通りの破損を注入し、全て検出しました。宣言正量の盾放出は1,001,318、整数化後0のHP／hit放出は0です。全定義トロニーの30秒側ではpool snapshot7回、full通知・take・放出は各4回で、bodyへ届きました。この実編成で盾への放出まで実証したという意味ではなく、盾への固定量放出は別の宣言入力で検証しています。新しい共有sourceから生成した旧HSI5 entryのCUDA／Metalは、正規化前の全byteも前回保存生成と一致しました。

## 保持と独立seal

現在の共通CLI入口は `destructible-body-accum-retention` 49入力（native40／拒否9）です。旧31入力を同じindexへ保持して新18入力を末尾へ追加しました。全49入力がMetal／native一致し、別processのGPU0監査で独立sealしました。旧31は全input／native指紋と全130,023,424byteのrawが一致し、アドレス移動の除外も加えていません。CPU60件は82.357998秒で90秒枠内に成功、native40の事前照合は40.434799秒、GPU10.080716秒、cached pipeline0.003000秒です。最終小型packageでもCPU60件83.570秒・native40件40.598秒、制御372件（Windows専用1skip）が成功し、1576 payload全SHAを再確認しました。全SHAと保存根拠は `research/portable-destructible-body-accum-checkpoint.json` を参照してください。

```sh
python scripts/nikke_gpu.py package --suite destructible-body-accum-retention --compact --out /tmp/accum49.zip
```

単独18入力は開発用のままです。旧goldenは旧sourceの履歴として保持し、自動更新しません。現CUDA実機、共有回復・貫通・parts／coords／ADD混在、同期子放出の追加境界は未検証です。全キャラ認定0、通常UI CPU、全目標未達を維持します。Windows追加実行は0で、過去7プロセス終了の原因unknown／環境保全falseも維持します。ユーザーは終了・再接続・再起動を否定し、ゲーム／動画利用の可能性を報告していますが、原因の証拠にはしません。
