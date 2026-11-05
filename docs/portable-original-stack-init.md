# 元スタック初期化と後続の消費・再加算

`coordinate-original-init` はソーダ：トゥインクルバニーの元定義全77行・完全5人編成・武器・成長・autoを保持する3入力です。スキル1のレベルだけを1／4／10に設定し、元の値表から40／45／50を初期化します。各8秒、seed3701、宣言idle worldを使用。効果の書換え、CPUが算出した発火時刻のGPU入力はありません。

初期化だけで終了せず、実バーストで17を消費し、その後の通常攻撃で3回加算されるところまで比較します。初期作成時にはstack_reach通知を合成せず、その後の実再加算では通知します。無期限の実wire bitsと最終stack・所属・activation時刻、全battle／packet／RNG／control／healthも既存比較器で検査します。

GPUは既存の固定 `gpu/world_coordinate_original_shared_entry.slang` を使います。今回のデータ追加でSlang本体・kind受付・Runtime・wire・数値規約は変更していません。既存stack observerとreaderを共用し、発火数を検査するoperation引数だけを追加しました。旧呼出しの既定範囲は同じです。

共通CLI `source-reuse` は6入力の旧shared packageから新3入力へのデータ変更を認識し、CUDA/MSLと両reflection、生成identity・consumerの完全一致と追加Slangコンパイル0を確認しました。この検査は実CUDAのcache/launchを証明しません。

このケース群は全キャラ認定ではありません。敵stack加減20/21、蓄積放出34、feather35、弾消費37、19入力変換失敗、モデル／variantの不足と現在のCUDA実検証・公開GPU統合が残ります。

M5 Metalで全3入力がstatus0・CPU一致。実GPU計1回、retry0、GPU0.734364秒、Metal pipeline必須hit0.002836秒、Slang追加コンパイル0でした。保存readbackを別のGPU禁止childで全3fresh再計算し、41.951534秒・live parent receiptなしでseal。CUDAの実計算・compiler cacheの証明へ流用しません。

正式packetは `/tmp/nikke-original-init-final-v1.zip`（d5274558…、1989files）。全payloadのSHAとcheckout byte、実GPU source／input／native／outputの一致を確認しています。reader終了後に21,238,272byteのrawをSHA・size・inode保持で疎化し、15,794,176byteの割当を回収、削除0。機能検査・制御検査の結果と実行失敗の有無は `research/portable-original-stack-init-checkpoint.json` に記録します。
