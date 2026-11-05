# 型付き対象と既存world実行器

共通CLI `destructible-world` は、既存 `world_schedule.slang` のノード遷移へ弾・HP盾・回数盾の状態を接続する短い検証である。CPU側では固定済み正本の `BossScript` を実際に動かす。時刻、世代、生成・失効、全対象破壊からの遷移を照合する。新しい時間管理やCPU生成のスポーン予定表は導入しない。

## 実装範囲

入力は最大32ノード、128対象の静的binding、32操作。HPとhit creditの量は呼び出し元が解決済みとして渡す。対象の生死からGPUがclearedを求め、既存ノードのactive/generationに合わせて共有target coreを生成・退役する。node寿命には既存の1e-9秒許容を使い、別の失効時計を重ねない。同一時刻の再入はノード遷移を進めず、破壊による遷移は次の異なる時刻で処理する。

CPUのprivate時計へは全対象破壊のbooleanを表す集約proxyを置く。proxyのHPを実対象のHPや周辺幾何として計算には使わない。所有者は記述だけで、自動的な敵死亡や所有者死亡へ変換しない。破壊結果には世代付き対象・所有者・時刻のreceiptを保持するが、戦闘の効果dispatcherにはまだ接続していない。

## 検証

固定package `6033d41f…` を新規展開し、CPU16検査とnative事前検査を経てApple M5のMetalで33入力を1回実行。正例21・raw拒否12が一致し、独立sealも成功。GPU計算0.012810秒、pipeline構築0.182481秒。実行時の生成cacheは必須hitで追加Slang呼び出し0。別の事前生成では共通ソースからCUDAとMetalを生成した。CUDA実機の今回の検証は未実施。

繰り返し世代、同時刻再入、複数対象の全破壊、cleared > followed > expired、遅延生成、finish、slot127、owner、分数hit credit、epsilon境界、蓄積／有理フレーム時刻を検査した。保存5ブロックの小さなfixtureで、世代・時計・履歴・破壊receiptの改変を検出する検査を追加し、最終CPU17検査が成功した。保存出力は `/tmp/nikke-dw-metal33-v1`、全103,809,024バイトのSHAはgoldenに記録。監査のためのGPU再実行はない。

## 残件と保持

productionの147ソース、Runtime138952、既存binary64・world scheduler・target coreは不変。旧戦闘とtarget coreの証拠は保持する。静的packingの対応増加や全キャラ対応とは数えない。戦闘の生成元、対象選択・着弾、盾の迎撃／倍率、所有付き破壊イベントの効果実行、`all_projectiles` の受付は未接続である。

Windowsの追加実行は0。前回の7プロセス欠落は原因不明、環境保持成功とは扱わない。ユーザーは当該時間のアプリ／ターミナル終了、再接続、再起動を否定し、ゲーム・動画利用の可能性を回答したが、終了原因を示す独立証拠ではない。次のCUDA実行前にCPUだけの準備時間測定と保存されたcache claimの確認が必要。
