# 元編成のB1条件と明示バースト順

`original-catalogue-roles`は元Rapi RHとRed Hoodの30秒4条件を、既存の共通compiler/状態・イベント実行器へ渡すsealed suite。キャラ固有shader、damage計算、時計、発動scheduleを追加しない。BODY-owned HP shield1個を置く宣言worldであり、任意の実ゲームworldの認定ではない。

| 条件 | 元編成の全定義 | 実発動の確認 | 全skill履歴 |
|---|---:|---|---:|
| Rapi no B1 | 90 | 他B1を含まない実編成でRapiがB1、Dora B2、Drake B3 | 31 |
| Rapi with B1 | 91 | CentiをMirandaへ替えた対照で、Miranda B1、Rapi B3 | 38 |
| Red Hood 123 | 81 | 明示した初回cycleで本人がB1→B2→B3 | 6 |
| Red Hood 12 | 81 | 明示した初回cycleで本人B1→B2、Drake B3 | 6 |

Rapiの2編成は先頭4人が同じで、元bodyの5人目だけが異なる。元effect/owner順/実武器/育成を検査してから元条件がlive stageを変える。元B1側source0/2/3/14/15/16のGPU counterが発火し、対照ではB3側source1/4/5/17/18/19/20が発火した。これらのcounterはGPU実行の活動記録であり、独立CPU handler呼出し数の認定ではない。

Red Hoodは元のlogical Aを保つ。canonicalの自動候補順はB3のままであり、明示sequenceがB1/B2を選ぶ。新しい`portable_declared_burst_sequence.apply`は元config/編成/武器のidentity検査後にliteral操作をcopyして適用するだけ。既存176word burst wire、packの上限/名前/stage/重複検査と、元stage適格性を使い、既存sequenceの上書きを拒否する。元bodyには操作を混ぜず、identityへ`original_controls_preserved=False`と適用済みflagを記録する。sequence終了後は元の自動動作に戻るため、12ケースでも後のcycleに本人のB3が発動し得る。

比較は元の全状態、実武器・着弾・乱数・通知・回復、全skill履歴と全post-tick burst stateを既存比較器で照合する。さらに実burst receiptから必要なowner/stageを必須検査し、発動しないケースが一致しただけでは成功としない。物理履歴は従来の全順序semantic SHAと保持prefixで、個別全行を保持したとの主張はしない。

固定8c3a1706/package acc12615…のM5実GPU1回が全4成功。19群174unit、CPU照合100.11秒、GPU4.47774秒、独立fresh GPU禁止監査115.38秒でseal。live-parent再利用は独立監査ではFalse。生成・Metal pipelineは必須cache hit、Slang0/追加archive compile0。CUDA/MSLと両reflectionの全byteは前のburst cohortと同一。input115680/output2032000word、Runtime138952byteは不変。CPU正本4ファイル・GPU source・数値・effect定義・normalizerの変更はない。

初版の検査はRed Hoodの自動候補順を4と誤って期待し、CPU基準作成で停止した。検査を元のB3順へ修正し、B1/B2の実発動は独立したreceipt条件で保持した。GPU未起動であり、失敗を成功へ書換えずprivate診断に残す。

使い方は`package --suite original-catalogue-roles --out NEW.zip`→新規unpack→固定packet自身の`run`。`original-catalogue-roles-cache-only`は同じsource/入力/golden/比較器にCUBIN/O1必須・paired generation必須を適用する。現CUDA実機/実CUBIN hitは未確認。Windows旧transactionはhost unavailableで終端不明、追加run/再送0。

任意選択catalogueは元1,064名に実role操作4名を追加して1,068名。元266profileのinventoryを増やしたのではなく、全キャラ/全特殊効果・公開GPU受付は未達。次はRed Hood B2/decoyの実被弾、異なる論理敵/PART/typed混成、未実証元profileを優先する。未知のLock On距離を既存順位で埋めない。出所と範囲は`research/target-count-query-evidence/metal-original-catalogue-roles-v1.json`。
