# 型付き128対象の免疫・共有スタックの接続設計

## 2026-10-21 128対象・共有バフのスタック操作をMetalへ接続

実験ABI7D・計算source50522a9で、buff_stack_add/remove/init、buff_max_stack_add、debuff_stack_add/removeを共通実行器へ接続しました。対象集合と世代・免疫だけを拡張し、整数変換・符号・ゼロの既定値・有限/無限上限・期限更新・遅延通知は既存stack_runtime/stack_numericを共用します。共有バフは65対象への操作でも1個のstackだけを1回更新し、対象ごとへ分割しません。共有バフに一部免疫があっても、nativeと同じ共有stackへの影響を保持します。

Metal590入力はnative53件・拒否8件・旧529入力の全524288出力word保持で成功しました。単体356件と、通常/fields/state/mutation/recipient/statusのCUDA・MSL生成物厳密一致を確認しました。小数・正負ゼロ・正負巨大値、named/unnamedの0/1下限、無限上限、2147483647の最終許容値、参照stack、所有者の違い、共有対象・免疫・再出現、期限更新とstack_reach子通知を含みます。31bit保持域を超える結果はstatus2で拒否し、許容範囲と混同しません。GPU実行1回・再試行0です。

証拠はportable-world-actor-stack-validation.json、CPU監査器はseal-world-actor-stacks-metal.py。新規61入力/53 native参照の全fingerprintを保存し、GPU関数禁止のCPU照合も成功しました。Windowsではこの61入力だけを低優先度・180秒上限で1回確認します。通常4682・旧529全件は再実行しません。target_hit_counterと完了/死亡/refresh epoch、skill/pending/DoT、mixed target、source攻撃/interrupt、操作/復活、容量/全203認証は未完了で、通常画面CPU・world公開無効・全変種認証0/203・効率化未開始を維持します。


## 2026-10-21 128対象の免疫・回数プール・解除をMetalへ接続

計算source0873bd9・実験ABI7Cで、既存status_runtimeの免疫走査・容量最大・使用数加算・再補充・解除順を共用し、対象参照と保存先を128対象へ拡張しました。通常/名前指定免疫は捕捉世代と生存を照合します。回数免疫はnativeのtarget_chars契約に従い、再出現通知中の旧世代でも実際に対象一覧から除かれるまで容量を参照します。この差は完全CPUの通知トレース3件で実測して保存しました。容量を整数へ丸めず、0.5/1.5の防御回数も一致します。

Metal529入力はnative37件・不正入力8件・旧484入力の全524288出力word保持で成功し、単体348件と通常/fields/state/mutation/recipientの生成CUDA・MSL厳密一致も確認しました。128個別プール、同名最大・別名独立、再補充、named免疫、irremovable、65対象、共有バフの部分解除、無通知での最後の受領者解除、再出現を含みます。初期コンパイラ比較はCUDAの空行1個で失敗し、読み取り式のproviderへ移して正規化を広げず回復しました。その修正までGPU実行0で、最終GPUは1回・再試行0です。

証拠はportable-world-actor-status-validation.json、CPU監査器はseal-world-actor-status-metal.py。共有受領者の新23入力と今回の45入力をまとめた68入力/56 native参照の全fingerprintを保存し、GPU関数を禁止したCPU事前照合も成功しました。Windows v87は固定f988d15の共通driverで68入力/56 native参照を94.93秒、BelowNormal・180秒上限の1回で成功しました。CPU21検査・GPU禁止事前照合、NVRTC/launch/同期/readbackの50記録、全input/output/native/generated SHAをMacで監査しました。元checkout/サービス保持・残存0・retry0です。保存済み3JSON 70,487bytesだけを取得してSHA照合し、GPU再実行0です。summaryにold484のカウンターが無いため、明示receiptの0・固定68入力command・実測launch1回から確認し、欠落や矛盾を許さないCPU負例5件と旧v83〜v86監査結果保持も確認しました。証拠はportable-world-v87-cuda-validation.jsonです。旧461/484・通常4682を全件再実行していません。スタック操作/target counter、skill/pending/DoT、mixed target、source攻撃/interrupt、操作/復活、容量/全203認証は残っており、通常画面CPU・world公開無効・全変種認証0/203・効率化未開始を維持します。


## 2026-10-21 長寿命共有受領者をMetalへ接続

実験ABI7B・計算source e7585b8で、512 residentそれぞれの128bit可変membership・捕捉generation・対象順を追加しました。単一受領者と共有受領者が同じ照会・世代照合を使い、buff_stack_initは1/65/128対象を1個のstack/期限で保持します。部分解除・全解除・死亡によるmembership解除・再出現・有限期限通知を共通実行器へ接続しています。

Metal484入力は完全native19件・不正入力4件・旧461入力の全262144出力word保持と拡張領域zeroで成功しました。CPU340件、通常／fields／state／mutationのCUDA・MSL生成物が厳密一致しました。M5のmaxBufferLength 14,302,248,960 bytesを実測し、新出力524288 words/ケース・実行全体1,015,021,568 bytesが上限内であることを確認しました。入力92336 wordsは増やしていません。GPU実行1回・再試行0です。元nativeの共有受領者も全辞書で照合しています。

保存結果のCPU監査器はseal-world-actor-recipients-metal.py、証拠はportable-world-actor-recipient-validation.json。新規23入力の全input/output/native/generated基準を保存しました。Windowsは未実行で、次の128対象免疫/解除とまとめて新規入力だけを短く検証する予定です。回数免疫用の拡張領域は確保済みですが、計算接続はまだ未実施です。通常画面CPU・world公開無効・全変種認証0/203・旧Metal差分OPEN・効率化未開始を維持します。


## 実測した契約

`research/characterize-world-actor-status.py` は元の完全なCPU simulateを17ケース実行します。入力は128対象の召喚・定義・通常武器だけで、途中状態はGPUへ渡しません。結果は `research/portable-world-actor-status-native-contract.json` です。通常画面CPU・world公開無効・全変種認証0/203を維持します。この段階のGPU実行は0です。

通常／名前指定免疫は対象ごとに作用します。127体の召喚＋bodyの128対象に対し、65対象だけの免疫は残る63対象への有害バフを妨げません。回数免疫は「対象ラベル・バフ名」の使用数を持ちます。同名の別所有者の容量は合計せず最大値、別名は独立です。容量0.5は1回、1.5は2回を防ぎます。使用数を容量より小さい間に1ずつ増やすCPU規則であり、容量を事前に整数へ丸めません。再付与は該当対象・名前の使用数を0に戻します。harmful_irremovableは免疫と回数消費を迂回します。

スタック初期化の1/65/128対象ケースは、**1つのcarrierが全対象を共有し、stack=3を1個保持**します。通常の敵バフのように受領者ごとへ分割すると、スタック変化・状態終了通知・残対象の関係を変えてしまいます。現在の4語の単一Actor keyをそのまま使い、対象ごとにcarrierを増やす実装は採用しません。

## 必要な共通保持領域

現在の通常ABI73、fields ABI78、state ABI79、名前指定解除ABI7Aの生成物・入力・出力を保持したまま、新しい実験entryに共有受領者領域を追加します。既存の単一受領者も同じ照会窓口を使い、同じ世代・生存規則で値を読みます。

1. residentごとに128bitの可変membership、128対象の捕捉generation、対象順、共有／単一のタグを持ちます。入力のbinding slotは固定であり、世代はGPUのスケジューラーから捕捉します。
2. 発動中のowned setと、carrierの寿命を通して残る共有対象を区別します。既存の32個の一時集合を長寿命carrierが占有する構造にはしません。512 carrierの上限に見合う領域を確保します。
3. 通常の敵バフは従来どおり受領者ごとのcarrier、初期化された共有バフは1個のstackと終了時刻を持ちます。部分解除はmembershipだけを減らし、最後の受領者が消えたときに1回だけ終了通知を出します。
4. mutationとvalue queryは既存のCPU generation-aware窓口に合わせます。空carrierの保持・通知は削除理由に依存します。死亡時のtarget_chars解除と、名前指定解除によるcarrier終了を混同しません。
5. 回数免疫の使用数は128対象×256名前×binary64の領域で持ちます。世代が変わっただけではラベル・名前のプールを勝手に初期化せず、nativeと同じ再付与経路でリセットします。
6. 出力上限を増やす場合、Metalの実デバイスのbuffer上限とCUDAのbyte寸法を実測し、必要なら同じソース・同じ入力を安全な分割で実行します。受付の上限を理由なく広げず、確保不能・領域超過は書き込み前に拒否します。

計算は既存の `stackIntegerDelta`、`checkedStackChange`、`setCarrierStack`、`refreshStackDuration`、`queueCarrierEnd`、`queueStackNotice` を共有します。別のCUDA/Metal算術やCPU事前計算を追加しません。必要検証後の効率化はまだ開始しません。

## 次の実証

共有受領者の1/65/128対象、部分解除・旧世代・再出現、免疫容量0/0.5/1/1.5/2、同名最大・別名独立、再補充、初期化の0／負数／小数・上限、named／unnamed stack変更と免疫、通知からの再付与、512 carrier／対象領域超過を共通fixtureで照合します。Metalで全比較と旧出力保持が通るまではWindowsへ依頼しません。Windowsは新規入力だけをCPU事前検査後に低優先度・180秒以内で1回確認します。
