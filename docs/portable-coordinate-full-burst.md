# 座標を伴う全バースト保留弾

`land_in_full_burst`のopt-in保留弾を、既存の共通保留キュー・座標選択・着弾実行器へ接続した。旧形式B3 `bonus_damage`の本体だけの経路も保持する。CUDA／Metal別の計算本体、時計、効果定義、入力fixtureは作らない。

## 接続内容

新入口は既存座標pending入口をincludeし、既存`PORTABLE_FULL_BURST_LANDING`と座標側の受付を有効にする。発動条件と参照ヒット数はcast時に確定し、ダメージ係数・バフ・座標集合は既存full-burst生成処理から取得する。部位・阻止対象・深さ順・世代番号は同じ座標snapshotとして各receiptへ保存する。

`moveFullBurstReceipt`は、従来のscalar part値とperiodic／interrupt tupleに加え、座標側の68word snapshotを同じindex間で移動する。これにより、保留弾が生んだ通常子スキルを次フレームへ残す際に、row／対象slot／世代番号が古いreceiptへ取り残されない。コピー関数は既存arenaを使い、Runtime配列や入出力ABIを増やさない。境界・B3 stage・descriptor・pending kindの検査は維持する。

## 実証と保持

`coordinate-full-burst`76入力（native63／拒否13）がApple M5のMetalで一致し、独立監査でsealした。追加13正例は全部位、貫通・爆発範囲、多段、0hit、cast時の参照count固定、後続castバフ除外、開始バフ、部位出生・消滅、部位／阻止対象の子receipt tail、旧形式保留との共存。追加3負例はdescriptor、pending kind、B3 stageの破損を拒否する。子の世代・選択集合・対象slot・cast件数の保存結果4改変も検出した。

初回は入口の共通full-burstフラグ不足で新正例がstatus64となった。初回package／失敗／raw／claimは保持し、フラグ接続後の別packageで成功した。同一packageのGPU再試行はない。旧60入力の全入力と251,658,240byteのraw、全sealed entryは修正版でも完全一致した。

共有helperのsource変更に対し、本体`attack-group-mixed`81も現ソースでMetal実行・独立sealした。旧81の入力、339,738,624byteのraw、生成CUDAとMSLがすべてbyte一致し、goldenの差はsource closureだけ。元golden／source証明書を別名保存し、共通CLIから現sourceのcompiler証明書を独立作成した。旧81はMetal pipeline cache hitで、raw CUDA SHAは`44ed50919f8e92db7da1fcab5ba58bc5842a901989c510f7561c418d42e3c838`のまま。Windowsの現source cache hitは未検証で、旧producer ownerを再ラベルしない。

GPU実行は失敗76・修正版76・本体81の3回。修正版のGPU時間0.021444秒、Slang2.181秒、cold pipeline7.150秒。本体81はGPU11.922680秒、pipeline cache hit0.002558秒。81の最初のcaptureは容量guardでclaim前に停止しており、実行には数えない。入力数や1GiB reserveは減らさず、終了済みの旧4.73GBバッファ1件を疎化して1.16GB回収した。今回の終了済みraw3件も疎化し、計2,097,152,000byte回収。全byte／SHA／inode／過去証拠を保持、削除0。

定義ビューの制御検査は、新しいフックが既存source監査表に未登録であることを検出した。失敗は保持し、過去の監査表を変更せず、今回の3ファイルの全SHAと一意なliteral差分を照合する監査層を追加した。旧sourceへ正確に戻せることもSHAで検査し、新入口の全SHAも固定する。5種類の追加source改変を拒否し、監査報告には今回の対象を明示する。生成コードnormalizerや数値基準は変更しない。

最終固定packageは`ab67bf3f359452e27b06d4898d46cdf177274898b5beeb649b97adb60a7e5377`。full2905→compact1611の全残存record／byte／goldenを照合している。最終CPU検査はcheckpointと対応receiptを参照。

## 残る項目

手動aim、座標物理弾、frameを跨ぐ世代交代、元定義の混合world、公開受付が残る。Mac／Windowsのhost trig数値方針は回答待ち。新76のCUDA実行、保存objectの回収／JIT linkも未完了。全キャラ認定0・20gap分類・UI CPUを保持する。以前の座標入口の証明書は履歴として残し、現supersetには新76証明書を使う。
