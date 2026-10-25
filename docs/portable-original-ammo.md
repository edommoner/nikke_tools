# 元編成の弾薬操作とゲージ段階通知

`coordinate-original-ammo`は、ギロチン：ウィンタースレイヤー／ノワール／アルカナ：フォーチュンメイト／グレイブの元5人編成を使用します。全79／74／80／83定義と元weapon・成長・操作を保持し、6／6／6／16秒の実戦闘を照合します。効果の削除やCPUで計算した射撃・発火スケジュールの入力はありません。

新入口 `gpu/world_coordinate_original_ammo_entry.slang` は既存の共通割合補充kind13／固定補充kind14をsampled受付へ接続します。CPUとSlangのkind受付は同じ宣言から生成し、旧resource入口は引き続きこの2kindを拒否します。binary64・wire・Runtime容量は変更しません。

受動observerは実弾薬handlerの元row／owner／nameを確認し、呼出し前後の弾数・reload状態をコピーします。有効最大弾数はhandlerが実際に呼んだ `_effective_max_ammo` の戻り値を観測し、追加のstat照会は行いません。実対象とcapacity観測対象を一致させ、割合の丸め・上限・負の割合と固定量の変換を確認します。GPU比較は既存の全battle／packet／RNG／最終ammoに、元定義別の実発火数と全ゲージ状態／every_stack通知を合成します。

ギロチンは経験値10の正のevery_stack通知からレベル2と10.26%補充が実発火し、実cap141に対して90→104発。ノワールは全5人へ39.88%補充し、実上限による切り捨てを含みます。アルカナは実際に2発／6発を補充。グレイブは元の無限弾数状態の終了通知から−100%が発火し104→0発になります。各値は固定worldでの観測例で、任意編成への認定ではありません。

旧resource入口は新ammo macro未定義時のCUDA／MSL原生成物が両方全byte一致。source／transport inverseは厳密な差分とSHAを使い、祖先baselineに存在しなかった新fragmentを戻り値から除去します。normalizerを緩めず、旧goldenのsource hashも自動更新しません。

静的entry-inventoryは266profile／247入力変換、kind拒否46（前入口65）。入力変換・kind条件・実GPU計算は別段階であり、残り201を対応済みとは数えません。次の実在候補にはstack上限19、解除26、stack追加16等があります。敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cache、公開GPU／全キャラ認定も残ります。

## 実証

固定packet `/tmp/nikke-original-ammo-develop-v1`（ea73aa56…）、capture `/tmp/nikke-original-ammo-metal-v1` はApple M5で全4一致。実GPU1回1.706368秒、初PSO92.190548秒、CPU事前60.414598秒。生成cache必須hit／compiler0、同claim retry0。独立fresh監査64.316086秒、別child・全4native再計算・live parent receiptなし・GPU0で成功し、同じ監査からgoldenとsource-only certificateを作成しました。現CUDA compile/link/cache/battleの証明へは流用しません。

全キャラ認定0／公開UI CPU／全目標未達です。Windowsの新規実行依頼0、現CUDA／warm cache実測は未取得です。既存idleチャットを開始できない送信APIへの再試行も同じエラーで終わっており、検証の重複実行を依頼しません。

最終compact `/tmp/nikke-original-ammo-final-v1.zip`（b8fdecda…）は関連23検査・制御476検査（Windows専用1skip）成功。終了後に全1938payload SHAとcheckout全byte、GPU source／全input／native／output指紋を検査しました。全reader終了後のrawはSHA／size／inodeを維持して疎化し、27,058,176byteを回収、削除0。記録は `research/original-ammo-evidence/` と `research/portable-original-ammo-checkpoint.json`。
