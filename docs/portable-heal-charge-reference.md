# 受けた回復量の蓄積と放出：共有GPU接続前の契約

共通CLI `reference --suite heal-charge --out <new.json>` に、既存CPU lifecycleの29契約を追加した。対象はheal_overcharge_store_atk_pct、accumulate_max_scale_pct、heal_overcharge_discharge。既存heal_charge_compat/effect_runtimeを正本として使い、正本やlegacy GPUを変更していない。GPU受付は拒否のまま。これは宣言モデルの一致を目指す段階で、ゲーム内の全相互作用を実証したものではない。

## 固定した挙動

各carrierは1個のscalar poolを持つ。過剰回復をダメージ軽減へ使う既存heal_overcharge_storeとは異なる。生成時の付与者final ATK×値/100が基礎容量で、再付与時は量を0へ戻す。受ける本人のHP上限へclampする前の正の割当済みbody healingを蓄積し、満HPの回復も入る。all_alliesのcarrierでも各人別poolではない。修復や負の回復は加算しない。

accumulate_max_scale_pctはpool付与者に有効な現在値を読み、target_effectありなら同名だけへ適用する。容量減少は既収集量を削らない。owner ATKの後日増加はsnapshot容量を変えない。放出はowner/nameで量を一度取り出し、current=0/done=trueにしてから、解決済み対象順で回復する。重複対象も保持し、現在のsource/recipient回復倍率を各回復へ適用する。別のlive poolは放出回復を受け取れる。

状態終了noticeは取り外されたpoolを放出用に残す。解除は保存せず、downも捨てる。downしたownerの放出effectは実行されない。状態終了でのretention、消費、通常after_dispatchでの回収の順を区別する。正本の同時刻battle_startはowner順なので、owner0からowner4への回復はowner4 pool生成前に発生し得る。別ownerの容量bonusも同じ順序の影響を受ける。

## 検証

fresh不変package d29dea53cefada2f27f6979f8bdb2aae57092e32366cf3820250383c3411cf90で29契約が5.963秒で成功。関連4群27検査(skip0)成功。空/満HP/被ダメージ/容量0・負/負回復/上限/名前の有無/bonus失効/ATK snapshot/二度放出/再付与/名前解除/cleanse/重複順/別pool/倍率/吸血/down/修復/共有scalar/別owner/owner順を含む。

観測器は既存callbackのcall/returnとrecord fieldだけを読み、余分なcapacity/final_atk/get_buffsを呼ばない。全native state・trace・RNGを無観測の正本と比較し、callback/照会数も保持。take・done・対象順・HPへの故障注入を拒否する。全29契約はGPU/packingを禁止した共通reference経路から実行した。CPU検査をGPU計算成功として数えない。

初回はcrit抑制field追加後のharmful指定先のずれを検出し、poolへ訂正した。次は別ownerの回復がpool生成前だったことを検出した。同時刻の反例を削らず、生成後のケースを追加して27→29にした。v2/v3の失敗report/packageを保持し、正本計算や期待値を都合よく変更していない。GPU実行claimはない。

静的241/266、base181/203、残33は同じ。全266profile記録/241input SHA/拒否理由とMetal349の全共有source SHAは保持した。3分類をreference_reviewからnative_contract_extensionへ移し、他はmodel gap10/review20。全キャラ認定0/UI CPU/目標未達。

## 共通実行器への設計

既存carrier identity・owner/name・generationと共有activation/retirement/health callbackを使い、scalar current/base-cap/done/endedを同じlifetimeへ結ぶ。既存のper-recipient excess-heal storageへ詰め替えない。再付与のreset、明示state_endでのretention、cleanse/downでのdiscardを区別する。放出は既存同期continuationで対象を先に解決し、takeを1回だけ行い、その後に既存の倍率/共有回復/通知を対象順に使う。CPU-produced pool amountを入力へ渡さない。

次はこの29表をCUDA/Metal共通入力へ接続し、容量・世代・不正量源の拒否、旧349出力保持、元デルタ実編成を確認する。GPUのstate領域と容量上限は接続時に設計・監査する。今回新しいGPU allocationや数値primitiveは追加していない。

## CUDAキャッシュ側の確認

Windowsの既存チャット履歴だけを1回読み、直近の調査が完了していることを確認した。新しいWindowsコマンド・compiler・GPUは0。過去7プロセス終了原因unknown/環境保全falseを維持する。

保存済みMetal349のgenerated CUDAを共通compiler-statsで全SHA検査後にCPU解析した。2,067,954B、833関数、noinline241。collectStats rootの既知call graphは字句解析で、実compilerの展開量・メモリ・速度を表さない。現在の共有sourceは既存compiler-full証明書に対して追加23/変更38で、同じcacheとして使えない。これはrepository証明書との比較であり、Windows raw artifactの独立監査ではない。

次のCUDA作業では、最新の独立Metal sealからfull compiler packageを固定する共通経路を先に整える。旧CUBIN/normalized hashの流用やcache key緩和は行わず、exact raw CUDA/prelude/toolchain/producer→object→linkを結ぶ。Windowsで再度重い試行を始める根拠は今回増えていない。

証拠はresearch/heal-charge-reference-evidence/、checkpointはresearch/portable-heal-charge-reference-checkpoint.json。
