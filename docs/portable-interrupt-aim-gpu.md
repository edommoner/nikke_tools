# Private interrupt直接着弾の共有接続

通常合計外のinterrupt直接着弾を共有SlangのactorPoolLandへ接続した。生存中はnativeどおりhits/dealt/landedを加算し、同フレーム破壊後も外部会計と吸血を残す。対象の再出現世代を維持し、canonical counterへのImpactは発行しない。通常の武器発射イベントとゲージ処理を消す変更ではない。CUDA/Metalに別々の計算・効果定義・期待値は追加していない。

正規ActorKind2はPROJECTILEのまま、interruptはprivate6である。既存のactor pool、binary64、着弾continuation、吸血、味方通知を使う。Runtime138952B・出力786432word・既存cacheとreceipt容量・整数変換/pow/normalizer・正本CPUと既存CUDAは不変。診断は未使用だった `[785536,786064)` wordに16件×32word＋16word headerを置き、他の診断entryとの同時利用を拒否する。既存の最大容量を縮小していない。

## 現ソースの実証

- 通常全1,385入力＝旧1,355＋新interrupt24＋混在6、native1,101/拒否284。Metalで全項目/全skill traceが一致し、別子プロセスのGPU禁止監査から独立sealした。CPU95群498検査、175.6899秒。GPU10.7288665秒。normal122source、generation cacheは今回の新sourceでmiss、CUDA/MSL生成2回。現在のCUDA実行やNVRTC cache hitを証明するものではない。
- 診断24入力も同じ122source＋entry1で一致・独立seal。98着弾のidentity/generation、時刻、damage、alive/hits/dealt/landedの前後、通常合計外会計の前後、canonical credit0を順序まで完全比較した。診断GPU0.0498738秒、最大12記録/16容量で省略0。
- 通常と診断の24入力は、診断bank以外の75,446,784byteが全一致。混在6入力は旧raw18,874,368byteを全保持。
- 旧1,355件の入力/native指紋は全保持。1,354件のrawが全byte一致。残る負例1件は下記の明示的な拒否位置変更で、旧全raw中4,262,458,812byteが保持された。旧native1,071件の計算結果に差はない。

分類・監査器の依存JSONを含む最終不変packageもCPU7群36検査に成功した。GPUの再実行は0。

現full package `6b996fa158ddbcd960b83d297b7fed9bbceaa3871519d2bcbc2c41793f1168a7`、archive SHA `1a1d61536d97c6e6a5b27b38cc7872a7234c937bcde5c56eab4e1b1875110b3c`。診断package `4ab0135625e0b18f5b9bede7ad1731472211f2d5851d967a6fbbfc4fbecbd8d1`。実goldenは `portable-world-interrupt-aim-retention-short-expected.json` と `portable-world-interrupt-aim-diagnostic-short-expected.json`。通常単独v2の24成功は初期化位置変更前sourceの履歴であり、現sourceの24件はfull1,385内で検証した。未実行full v1 packageも保持し、現証拠へ混ぜない。

## 失敗と拒否位置

通常v1は21入力で味方命中通知の差を検出した。interrupt照準もpart0/body0の二つの観測を残す必要があり、既存の共有notifyWorldTeamへ接続して修正した。診断v2はactor recipientの全tail初期化が先に書いたheaderを消す問題を検出した。初期化を既存clear後のfocus初期化へ移し、順序監査を追加した。いずれも失敗raw/claimを保持し、CPU期待値やnormalizerは変更していない。

旧 `state-focus/reject/state-focus-physical-interrupt` は、charge fixtureのweapon modeだけをautoへ改変し、charge制御を残した不整合入力である。obsoleteなinterrupt一括拒否を外す一方、静的charge制御とbase武器modeの整合性を共有側で検査した。両版ともcommand実行前にerror64だが、後段で拒否するため657wordがzeroから初期状態へ変わった。この一件のinput/native/旧新output SHAと全変更wordを `research/portable-interrupt-aim-rejection-stage.json` に固定した。正常計算の差を除外するnormalizerではない。CPU監査器 `research/verify-interrupt-aim-retention.py` は他の差を認めず、実rawと全hashを照合する。

## 残る接続と運用

24契約の直接着弾はcore0・intercept追加倍率なしの範囲であり、**物理interrupt全体の完成ではない**。狙ったtargetのno-core/intercept倍率、貫通・爆発時の本体＋対象packetとreach対象からのaimed重複除外、複数packetを保持するnative shot観測器が次の接続対象。現在のprojectile観測器は一射のreturned packetが同一damageであることを前提としており、そのまま複数種packetへ流用しない。

`interrupt-aim` / `interrupt-aim-diagnostic` / `interrupt-aim-retention` はdevelopment_onlyを維持する。privateの入力生成・直接着弾試作経路を広く認定したとは扱わず、上記の倍率/複数packetを実装・検証するまでpromotionしない。default typed CPU橋は変更せず、通常UIはCPU。全キャラ認定0、目標未達。

Windows追加操作0、既存7プロセス終了の原因unknown/環境保全falseを維持。静的inventoryは230/266・base170/203・62分類でGPU認定ではない。過去raw2本と今回rawを全byte/SHA/path/inode保持でsparsifyし、計6,898,974,720byteのゼロ割当だけを回収した。削除0。大きい全体package作成でもnative照合の時間がかかるため、次回は短い通常/診断の成功後にfull packageを作成する。

詳細は `research/portable-interrupt-aim-gpu-evidence.json` と `research/portable-interrupt-aim-gpu-checkpoint.json`。
