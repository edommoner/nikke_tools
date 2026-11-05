# mode中の明示操作と射撃後待機

`coordinate-mode-actions` は共通CUDA／Metal実行器へ、mode中の明示hold・coverと射撃後待機の合成を追加した共通検証入口です。旧 `coordinate-burst-control`293入力に20worldを追加し、313入力（native266／拒否47）を照合します。計算本体、定義、比較器をbackend別に複製しません。

## 正本の契約

正本の `CharState.tick` はmode中でもclick schedule→明示sequence→cover期限→装填完了→cover判定→一時武器交換の順です。明示holdとcoverのチャージ状態への作用は、交換前の元武器に従います。policy coverはmode中のこの入口では適用しません。

元武器がチャージ型なら、cover進入は充填だけでなく射撃後待機も取り消してreadyへ戻します。GPUの `enterManualCover` はこれまで充填状態だけを取り消し、未来の `nextShot` を残していました。共通実装で `nextShot=when` を設定し、姿勢・装填処理を経た後の再チャージを可能にします。元武器がautoの場合の待機保持は変えません。Runtime／入出力のサイズ追加はありません。

modeの射撃後待機は効果の静的値0.2秒、今回の元SRは正本の武器種既定値0.215秒です。これらを混同しません。新adapterは既存 `normalize_static_clock` を呼び、手書きのbase待機配列と不一致ならbattle／GPU実行前に拒否します。CPUで操作・射撃時刻表を計算してGPUへ渡しません。

## ケースと失敗の保持

holdのmode中消費、coverとの同時順序、期限前release／None、coverの有限／None／0、mode終了、auto mode、進入待機、射撃後自動装填、tap、元武器の周期下限をmodeへ継承しないこと、遮蔽禁止を含めます。新入口は元の全比較器と同じ親だけのParentOraclesを使い、独立監査はfreshです。

最初の16入力はsandboxの `No Metal device` によりカーネル前停止。M5の読み取り確認後、20入力で差分を採取しました。最初の入力は元武器SRの待機を0秒としており、CPU基準と矛盾していました。正規化値0.215秒への修正後も、20件全てのnative指紋は不変です。GPU側入力だけを正し、17件一致・cover中断3件の実装差を切り分けました。元の全失敗出力とclaimを保持しています。

313入力の準備で新入口のwire登録漏れと必要JSONの配布指定をCPU検査が検出しました。修正し、strict adapterのwire検査を入力生成・native再計算より前へ移しました。古い入口のsourceは、固定全文・SHAに束縛した逆変換で監査します。一般化した差分無視は加えません。

大きな旧結果の保持確認に先立ち、完了済みsource展開12件を全復元・全hash検査後にlossless圧縮しました。GPU rawは削除せず4KiB疎化で全byte／SHA／inodeを保持しています。

この入口の検査は全キャラ認定ではありません。全キャラ認定0、未対応21profiles／20分類、UI CPUを維持します。healing storage／混在actorの元定義、現CUDAの短い実行とwarm cache検証は残っています。

## 最終実証

M5 Metalで全313入力一致、別processのGPU禁止fresh監査と同じ監査からのsource certificate作成に成功しました。固定GPU packetは `/tmp/nikke-mode-actions-develop-v6`（55b8a8a3…）、captureは `/tmp/nikke-mode-actions-metal-v6`。GPU0.706120秒、初回pipeline93.681053秒、CPU事前186.553041秒、通常比較8.632057秒。通常比較はnative266件と実生成記録を同じ親だけで使い、追加native0件。独立監査へこの再利用を渡しません。

旧293のinput／nativeは全て不変。旧rawは287入力の全2,031,794,688byteが一致し、6入力だけ変更しました。差分はowner1〜4の10秒充填・未射撃charge武器の `nextShot` で、最後のcover進入時刻へ更新したものです。全変更wordを列挙して検査し、旧raw完全保持検査のfalseも保存しました。元失敗20のうち17成功入力は全120,350,208byteを保持し、変化したのは実際の失敗3入力だけ。全20のinput／native基準は不変です。

最終compact `9954d281…` は1856 files／ZIP 8,607,700byte。30選択検査と446制御検査（Windows専用1skip）、全payload SHA／checkout全byte一致、元capture全artifact hashが成功。ここでは186秒のnative事前照合を再び繰り返さず、実GPU packetとのsource／input／native一致を確認しました。sealed生成cacheはhit／compiler0でCUDA／Metalペアが原captureと全byte一致。Metal file cache probeもhitですが、warm GPU性能やCUDA実機の成功とはしません。

最終goldenは `research/portable-coordinate-mode-actions-short-expected.json`、checkpointは `research/portable-coordinate-mode-actions-checkpoint.json`。最初のNo Metal device停止、入力矛盾、元GPU失敗、途中の登録漏れを保持。v5の不要なCPU作成だけを登録漏れ修正のため明示中止し、GPUは実行していません。新GPUは失敗2＋修正版1の計3回、同claimの再試行0。Windowsはrev78 idleをread-only確認しただけで、新要求／GPU実行0です。
