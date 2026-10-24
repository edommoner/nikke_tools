# 座標DoTと共通時計

`coordinate-dot` は既存 `coordinate-skills`24入力を先頭に保持し、DoT9正例と時計欠落/保留packetの2拒否を追加する。共通CLIの sealed 35入力（native28/拒否7）として登録し、CUDA/MSLを同じSlangから生成する。今回の実GPU計算証拠はApple M5 Metalのみ。原キャラ全定義の対応認定は0のまま。

## 実装

`validWorldSkillDefinition` の既存periodic時計検証を利用し、私有座標入口のDoT拒否だけを解除した。追加部位へのImpact familyも既存 `WORLD_PERIODIC_FAMILY` でDOTへ揃える。新しい時計、ダメージ計算式、Runtime状態は追加していない。正本CPU・binary64・pow・整数変換・厳密normalizerは変更していない。

CPU観測器は、座標target packetをbody traceから除外するときにもreturn時の観測rowを解放する。対象packetは別の順序付きtraceとして全て比較する。入力は静的効果とliteral形状だけで、native計算結果・選択集合・ダメージをGPU入力へ埋め込まない。

## 数値と寿命の契約

即時3tick、遅延2tick、tick間の部位消滅/破壊、再出現世代2、不壊とdepth逆順、DoT限定counterと吸血を比較する。最終tickはcreated .2099でも着弾frame .21666666666666665のGeometryを参照し、.21から存在する部位を含める。選択時刻をcreatedに置き換えない。

DoT+200%とpart+50%は正本の同じ数量層へ加算する。基礎2000ならbody6000、part7000、3tick合計60000。初期テストの乗算期待9000は正本の層定義に照らして訂正した。共有数値処理の変更はない。

## 検証と効率

固定development35パッケージを1回実行し、native28/拒否7に一致。保存結果を別プロセスで独立sealした。GPU .021773秒、Slang3.659秒、初回pipeline7.083秒。既存24も同じ現sourceで1回だけ実行・独立sealし、GPU .019816秒、必須pipeline cache hit .001846秒。旧24全100663296byte、入力全体、35先頭の出力が旧保存結果と完全一致。旧world-pool16/mixed81のGPU閉包は変更されておらず、再実行していない。

最終full/compact各CPU23、共通制御392（Windows専用1skip）が成功。full2875→compact1584ファイル、残存manifest recordと全payload byte、goldenが完全一致。保存rawコピーへの世代・最終tick量・counter元packet量・未使用tailの4改変を全て検出し、原本SHAは保持した。初期の非manifest走査は実行生成pycacheも比較したため停止し、manifest列挙全件のサイズ/SHA/byte照合で配布内容を確認した。raw原本は削除していない。

実行package ID、入力/output SHA、CPUログ要約、故障注入・保持検査は `research/coordinate-dot-evidence/` と `research/portable-coordinate-dot-checkpoint.json` に保存。再利用コマンドは `python scripts/nikke_gpu.py package --suite coordinate-dot --compact --out PACKAGE.zip`。

## Windows保存結果

接続復旧後は既存PTX結果のstatus/exportのみを依頼し、再実行はしていない。NVRTCは26.302秒で9554090byteのPTX生成に成功、Slang生成cache hit。全stage97.422秒のうち親package検査40.865秒、子package検査12.761秒、artifact compile26.534秒（入れ子の値は合算しない）。driver/link/GPU0。外側観測で9プロセス欠落・原因unknownのためstage/環境保全はfalseであり、compiler成功と分けて保持する。共有15ファイルへの個別承認を受け、固定commit `da8051535d135009e5a72e3e8cb19beb4a777ff1` をMacへ取得し、manifestを含む計9634581byteの全サイズ/SHAを照合した。正規化CUDA/MSLは現mixed81と一致するが、生成raw/source閉包identityは異なるため現packageへPTX cacheを再bindしてはならない。保存PTXは別branchに保持し本実装branchへ重複梱包しない。

## 残件

通常の距離/形状選択、座標物理、保留B3のnative packetモデル、跨frame同名世代交代、原キャラ全定義、公開受付は未完了。DoT宣言9例はこれらを完了扱いにしない。全キャラ0、20gap、UI CPUを維持する。
