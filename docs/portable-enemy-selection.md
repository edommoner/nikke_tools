# 共通の敵random／code選択と受付契約

共通SlangのActor集合選択へroute10を追加しました。CPUは静的な定義とseedだけをpackingし、抽選・RNG消費・対象世代・効果実行はGPUが担当します。CUDA／Metalに別の抽選器や効果実装はありません。Metalのsoftware binary64、整数変換、用途限定pow、strict normalizer、protected referenceは変更していません。

## 参照仕様と共有実行器

- CPython3.12のsampleと同じpool／selected-setの切替を整数で求め、既存MT19937とrandbelowを使います。敵攻撃のvictim選択とRNG状態を共有し、全624語、draw／reject／sample数を正本と比較します。128体の既存集合配列を使い、新しいRuntime配列は追加していません。抽選後はbody→add出生順へ戻します。
- add不在では抽選しません。正本モデルはbodyを退場させず、code selectorは属性を問わずbody1体を返します。このモデル制限に合わせています。実ゲームの属性別add選択まで対応したという意味ではありません。
- 多段ダメージは各landingの現在の生存集合から選び直します。buffとmutationは既存の集合capture／共通状態・イベント実行器を使います。
- DoTは登録時の対象を保持します。refresh時には正本と同じ抽選を消費して破棄し、同名aliasではincomingの対象union→canonical定義の破棄抽選の順を守ります。carrier失効後の最終tickは、正本で固定対象tupleがなくなるためlandingで再選択します。
- max_triggerは、枠が尽きていれば抽選せず、残っていれば実行前の対象probeを消費します。元係数0でもこのprobeは行います。
- 敵向け期間延長は、選択集合と一つでも交差する既存resident全体の期限を変え、DoT timerも同期します。数値演算・stack更新・期限・通知を別バックエンドへ複製しません。

## レビューを反映した検査と効率化

`actorSetCapture`から外れていたnoinline属性を戻しました。既存compiler-statsで保存generated CUDAの規模と属性を調べます。字句量はcompilerメモリや改善率へ換算しません。

敵instantの予約recipient語へprivate counter patchがstat keyを書いていた不具合を修正しました。値を無視するようGPU受付を緩めず、予約語をゼロに保ちます。期間延長はActor側とcounter側の両受付を同じ契約へ接続しました。

`research/portable_input_aliases.py`は同一packed入力を一度だけGPUへ投入し、元表記ごとの独立native oracleと比較をすべて保持します。alias間の正本結果が異なれば失敗します。61正例を51入力へまとめ、負例9入力と合わせて60入力です。10入力分のraw（31,457,280byte）を削減します。原ケースのCPUテストは保持しています。

診断suiteは9負例についてstatus64に加え、受付stageを検査します。stageは複数条件をまとめるため、正確な個別理由の証明とは区別します。各負例は同じ有効seedの単一語変異で、対応する正例も含みます。通常入口に診断tailを混ぜません。

```sh
.venv/bin/python scripts/nikke_gpu.py package --suite enemy-selection-diagnostic --develop --out /tmp/new-diagnostic.zip
.venv/bin/python scripts/nikke_gpu.py package --suite regression --develop --out /tmp/new-regression.zip
```

既存CLIのunpack→CPU preflight→bounded Metal→保存raw監査→明示sealを使います。失敗package／rawを上書きせず、sourceを修正した新しいpackageで検証します。

## 実編成で見つかった接続漏れ

入力変換が可能になった8キャラの全定義を各3秒／30秒で追加しました。ブリッド：サイレントトラック、ユリア（宝物3）、ミハラ：ボンディングチェーン、ソーダ、マルチャーナ：マリンスタディ、ヘルム：アクアマリン、アイン、シンデレラです。

初回集約662は656一致・6拒否でした。ミハラ／マルチャーナのC_CAST条件と、アインの周期source（kind35）が既存実行器へ接続されている一方で、Actor入口に未受付でした。既存の条件判定・source descriptor検査へ接続し、3秒各1件の追加診断は全件一致しました。元の失敗は保存しています。単に受付を外して全キャラ対応とする方法は使いません。

ミハラ30秒ではさらに、Actor側の名前付き解除がresidentだけを終了し、DoT clockを止めていない不具合を特定しました。倍率再解決だけでは再付与の位相差が残るため、従来経路とActor経路を`retireNamedCarrier`へ揃えました。0.27秒で再付与する独立fixtureを追加し、通常の0.1秒tick格子と区別します。診断専用入口でowner0の51スキルを記録し、作成時刻・着弾時刻・ダメージが正本とすべて一致しました。通常入口の履歴容量や比較器は変更していません。

新規ミハラ30秒の物理履歴は2048件を記録し32件を省略しています。新規の他15実編成は省略0ですが、過去persona等の省略制約も残ります。省略packet個別一致の認定ではありません。

## 検証状況

最終664入力（native526／拒否138）はMetal全件一致し、独立監査を1回使うGPU0の明示sealが成功しました。旧588の全input／raw／native、途中662の成功661の全raw、独立60の診断tail16語以外の全raw、全664のlazy bankゼロを確認しました。CPU719成功・Windows専用1skip・失敗0。詳細はdevelopment checkpointとretention記録を参照してください。初回62の6不一致、修正68の2不一致、scope58の1拒否はそれぞれ保存し、duration58で全件一致し、解除／再付与境界を含む60入力も全件一致しました。未対応項目を削ったり比較項目を省いたりして合格にしていません。

静的packingは209/266、base149/203、未対応87分類です。分類は各定義の最初の観測失敗で、完全な下流要件一覧ではありません。projectile_dmg_pct／shield_dmg_pctは正本consumer未確認のため無効果として受け付けません。次候補は参照consumerを確認できるatk_buff_mag_pct（79）です。

Windowsの追加実行は0です。以前のv117 cache／controller CPU53成功と、本体v115 cold compilerのallocation failureは別の証拠です。新版CUDA数値一致・通常UIのGPU化・全キャラ認定は未完了で、最終目標は達成していません。

保存generated CUDAはbaseline比13,619byte・10関数・noinline2増です。Runtimeの全宣言fieldは同一で、推定138,928byteを維持しています。これはcompilerメモリ改善ではありません。途中の約2.08GB rawは全展開SHAを確認した約5.85MBのgzipへ退避し、復元CLIとreceiptを残しています。
