# 名前付き周期スキルの秒数補正

`effect_interval`と`skill_cooldown`を、既存の共通周期時計へ接続しました。割合補正・一回限りの残り時間短縮・秒数補正は別の演算として扱い、CUDA／Metalの本体・定義・fixture・native比較器を共有します。private combat worldのみで受け付けます。

## 数値・状態・lowering

参照はpinned `BuffManager.tick`のevery処理です。対象の効果名に一致し、そのcasterへ適用されるresidentを、effect_intervalのstat index、次にskill_cooldownのstat indexの順で合計します。グローバル発動順へ置き換えません。合計は既存のPython3.12に対応する補償加算を使います。1e308の相殺を含むfixtureは、順序を誤ると有限の結果がoverflowになることを検査します。

計算順序は`max(0, base + flat) * max(0, 1 + percent / 100)`、最後に元の`base * 0.05`を下限とします。途中の付与・失効時は既存時計が残り時間を新旧周期比で調整します。条件付き永続効果は既存runtime条件評価器を呼び、有限効果は発動時の条件を保持します。まだ対象未解決のresidentについて、通常のbuff queryを呼んで対象を決め直すことはしません。

canonical compilerのkind4/stat0とrow220〜222の演算種別／名前ID／名前有無を保持します。MODEの6〜9語にtagged payloadを置き、quantity flag512で識別します。既存trigger reducerのflag256とは排他的です。GPUでkind/stat/flag/tag/値/対象名/unused語を検査し、従来のstack・recipient・actor-field検査も通します。numeric damage statのベクトルへ紛れ込ませません。

効果名・target_effectが空または未指定なら周期変更は起きません。割合補正のtarget_effectがフィルタではない点と区別します。複数casterで同じ名前を持つ時計は、実際のrecipient集合で選択します。コードはshared Slangだけにあり、backend別の周期計算を増やしていません。

## 受付の整理と発見した不足

WORLD_TEAM_KIND／WORLD_TEAM_CONDITION／WORLD_SKILL_KINDは、呼出側の自由変数だったrowを明示引数へ変更しました。

初回415入力では414件が一致し、ally_hp_belowを持つflat効果1件がactor-field受付でstatus64になりました。条件評価器は既にC34を処理しますが、team additional-conditionの許可集合にありませんでした。C34を既存の0〜100のHP条件検査へ接続し、query casterのHPが条件を満たす正例、満たさない正例、不正name／NaN／範囲外の4拒否を追加しました。期待値は変更していません。

初回package・claim・raw・比較失敗を保持し、修正版は別source/inputで420入力を実行しました。同一source/inputの再試行は0です。保持監査は、comparisonの成功行だけの連番ではなく、manifestにある元のcase indexでrawへ戻って照合します。

## 実証

- flat個別57入力：native40＋raw拒否17。正負・下限・途中付与/失効・割合との併用・stack・同名merge・対象名/recipient・runtime条件・values・加算順序・trigger reducer/stack操作との併用を含みます。
- nativeは独立した実戦結果・全skill trace・実際の_next_fireを観測します。新しい期待値式は作らず、割合補正の既存比較器を再利用しました。
- 実`에이다`の全効果を含む3秒／30秒を追加し、実編成群は44入力です。効果・武器・成長値を検証用に差し替えていません。
- regression420（native334＋raw拒否86）はApple M5 Metalで全一致。GPU7.696943秒、library1.077211秒、pipeline9.915337秒、bounded51.706852秒。異なる入力群の時間なので速度改善の証明にはしません。
- 旧361ケース、初回415の成功414ケースはinput・全raw output・native指紋が同一です。この2集合は重複するため合算しません。
- 修正版を既存CLIでGPU禁止監査・明示sealし、通常regressionをportable-world-skill-flat-regression-short-expected.jsonへ切り替えました。CPU684検査は1skip・失敗0です。

静的packing193/266、基本キャラ134/203、未対応分類110。packingはGPU受付や全キャラ実戦認定ではありません。通常画面CPU、全キャラ実戦認定0、最終目標未完了、新版CUDA数値一致は未確認です。

## CLI制御確認の効率化

Windowsの子テストとJobはcapture/temporaryをTEMP／TMP／TMPDIRへ設定します。親環境は変更しません。`run --smoke`は固定packageの全ファイルを検査した後、制御用CPU29検査とGPU0のfresh Jobだけを実行し、全編成のnative battleやnumeric suiteの再実行を省きます。通常GPU実行とCPU-only検証の全native preflightは維持します。

制御テストでは「smokeからnative preflightを呼べない」「子プロセスが専用TEMPを実際に使う」を検査します。Windows実機の制御smokeはMac検証後の短いCPU確認として扱い、NVRTC／driver／kernelは起動しません。CUDA初回コンパイルのメモリ不足は別の未解決事項です。
