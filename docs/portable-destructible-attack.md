# 生存弾一覧から既存実行器への一斉攻撃

`app/destructible_attack_runtime.py` と `gpu/destructible_attack_runtime.slang` は、typed worldの生存PROJECTILEだけを選び、選択時のslot・種類・ID・世代を固定して既存の着弾/counter/同期子イベント実行器へ渡す。CUDA/Metalは同一Slang本体を使用する。対象別creditや完了ループを作り直さず、`dwLand` と `dwPublishImpact` を呼ぶ。倍率やダメージ式を別実装しない。

これは `all_projectiles` に必要なlive集合選択・複数着弾のproducerである。CPU側は同じtyped worldと既存`deliver`を使用し、同期子イベントによる世代交代時は固定された古いhandleを持つ後続着弾が拒否される。フレーム時刻が子イベント中に変化した場合は停止し、再試行・巻戻しをしない。GPUの通常子イベントはworld時計を進めず、GPUでの子によるworld世代変更自体を実証したとは数えない。

共通CLI `destructible-attack` の15入力（宣言正例9・raw拒否6）をApple M5で1回実行。混在集合で盾を除外、弾0件、遅延生成、世代2、128対象/slot127、miss/blocked、分数credit、元attack_idと子atk_pctを検証した。既存BossScript時計・全128slotの状態・全counter完了trace・credit/epoch/dead・子ATKをCPUと比較し、保存readback全件一致。GPU約0.039299秒、readback47,185,920バイト、Runtime163528バイト。通常戦闘Runtime138952・旧147shader、旧counter/world/coreのソースは変更していない。

最初の比較はreaderへ`effects`を渡し忘れてKeyErrorとなった。実行自体は正常終了。reader修正後の固定packageへ保存結果をreplayし、独立seal成功。GPU再実行0、元失敗結果・claimを保持。保存5blockの故障注入テストは選択件数・世代・残量・子ATK・counter epoch・拒否statusの破損を検出する。GPU出力を期待値の代わりに使わず、全正例をCPU比較した後にsealした。

package v1 `2fbf1c377f5d3f5eee01e77d327195677bd4cea5b8e63e70de3f929f42b17915`、実capture `/tmp/nikke-da-metal15-v1`。reader修正v2 `1a1f20409cea537ce727f7404d6e6e629c9d7f6239b6b3a4b7d15fde937f7bde`、replay `/tmp/nikke-da-replay15-v2`。新runtimeのWindows実行は依頼していない。旧counter18のPTX必須cache実行1回は生成hit/Slang0/NVRTC0まで成功したが、driver module loadが内側60秒でtimeout、launch/readback0、CUDA数値は未検証。終了後の両Jobは空/missing0、service未確認なので環境保全false。旧claim保持・再実行0。Windowsの入力再利用は0.027634秒と測定できたが、これで全体時間の問題が解決したとはしない。

全inventoryを前回と完全比較し、266記録・245packing・20未対応分類/順位も不変。通常戦闘の効果定義から係数/倍率を解決してこのproducerへ入れる接続、敵弾の戦闘生成元、盾迎撃、破壊固有效果、attack group完了はまだ残る。通常の`all_projectiles`受付は拒否のまま、静的packingを全キャラ対応と数えない。次は既存のdamage query/Frameからtyped producerへ渡す契約と、CUDAのmodule/JIT費用の保存記録による切分け。数値/normalizer/正本を変更して通すことはしない。

証拠は `research/destructible-attack-evidence/`。失敗を含む各resultのscopeとpackage IDを区別して読む。全キャラ認定0、通常UI CPU、全目標未達。
