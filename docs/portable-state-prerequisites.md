# 遮蔽物・フォーカス・味方選択のGPU移植前契約

共通CLI `reference --suite state-predicates`（30入力）と `reference --suite ally-random`（18入力）を追加した。これは正本CPUの意味を固定する準備であり、新しいGPU対応ではない。hostは未対応条件/対象選択を拒否し続ける。GPU本体/受付/golden/正本CPU/数値/normalizer変更0、GPU実行とclaim作成0。既存Metal1234入力の範囲を変更していない。

不変package `18ca1d4b33a732d85b46513ee69a239f692c53483e45e0d28868b2929bb91465` から全48契約が成功した。共通CLIのCPU-only20群124検査は失敗0、群合計24.533秒。新観測器はnative全項目・物理traceと既存のcondition/cover/runtime query/sample/resolve呼出数を無観測版と比較し、味方乱数の実行後stateも一致する。入力を作るためにCPU battle/packingを呼ばず、既存helperを一度だけ呼んで戻り値を記録する。sourceと指紋は対応checkpointに保存した。

## 遮蔽物とカメラの30契約

`no_broken_cover_ally` は `_alive()` の生存中の味方だけを隊列順に見て、本人も含む。遮蔽物HPが正なら生存扱い、0なら不成立。死亡した味方の壊れた遮蔽物は除外する。部分被害、破壊、復旧、破壊後の戦闘不能、本人の破壊、所有者、短絡順、重複条件、有限/永続witnessを固定した。刺激はliteralのreload/attack/reviveであり、結果のdown/cover状態をGPU入力として与えていない。

`focusing` は正本の `_runtime_condition_ok` がbuffのシェア先ではなくcasterの `state['camera']` を調べる。無期限passive、空/単独/共有カメラ、別所有者、all_allies、操作所有者の切替を含む。有限の離散buffでは発動時 `_condition_ok` がこの条件を調べず、期限中のruntime queryもない。今回の有限passive入力でも17回の条件評価が全true、runtime query0で、カメラが他人でも3射6600だった。この観測を無限buffのカメラ判定と混同しない。正本モデルの契約であり、ゲーム仕様の認定ではない。

動的カメラの入力はUP武器のhold区間をliteralで指定する。runtimeで見たmaskは1→16→2→1、所有者は4→1→なしとなり、本人の3射は6600/6000/6600。0秒の発射と所有者切替、stat照会の順序も保持する必要がある。単に最新maskを読むだけで同じ結果になるとは推測しない。合計100条件評価/204cover照会/326runtime照会/79成立/87射を固定した。

## 味方選択と乱数の18契約

`allies_random:N` は生存中の本人以外、`allies_broken_cover_random:N` は生存中かつ遮蔽物が壊れた味方（本人を含む）から、正本のmodule-global `random.sample` で選ぶ。空集合は消費0だが、候補1人や全員選択でも乱数を消費する。選択順はソートして消さない。seed19/0、1/2/飽和数、空/1人/戦闘不能、壊れた本人、buff/instant、敵の乱数攻撃との併存を固定した。

味方側はsimulateのseedで初期化するglobal stream、期待値モードの敵側は別の `random.Random(_EXPECTED_BOSS_SEED)` である。敵側だけを6word進めた対照でも味方の全sampleとstate hashは同一だった。同じ整数MT実装を再利用してもstate/seedを混ぜてはいけない。prepared inputsには `policies.seed` が既にあり、正本engineを変える必要はない。

遅延buff対象のcache keyは `(caster, activated_at, str(raw_target))`。effect名やスキル欄は含まず、異なるsourceの2効果でも対象を共有してsample1回になる。instantは即時に選び、cover_reviveが成功すると次回の候補集合が変わる。この差を同じ処理へ潰さない。計50sample/50resolve/52選択を固定し、before/afterのMT indexとJSONで正規化した全state hashも記録した。index差はmod624で集計し、一般的な乱数生成回数の計測とは主張しない。初期index624の空集合を誤集計したv1のsummaryを修正し、入力/native/traceの全指紋が同じv2を採用した。v1も保持した。

## 共通実行器へ接続する残作業

条件39と30のwire/受付/共通状態照会に加えて、射撃集中 `focus_fire` 自体のmarker定義と `_resolve_aims` の照準共有consumerが必要。focus_fireは現在STAT表にない。条件だけ受付し、markerをno-opや別の数値statへ置換しては完了にならない。既存liveMarkerの無敵/不屈用maskと、新しいmarkerの照会も区別する。次のGPU batchでcameraのquery順、markerのliveness、actor target、味方RNG、lazy cacheとinstant処理を接続する。

`not_core` も調べたが、期待値モードでは `(1-core_frac)` をeffect/caster別に累積する条件であり、core_hitのbool反転ではない。別の数値・イベントcontext契約が必要なので、今回の状態条件と混同しない。

分類は静的227/266（base167/203）、未対応68分類の件数を変えず、native契約拡張6/consumer研究4/model gap3/review55へ整理した。依存が残るものを即時GPU候補へ昇格していない。全キャラ認定0、UI CPU、全目標未達。Windows追加操作0、7終了原因unknown/環境保全falseの停止を維持する。次はこの共通batchの実装・短いMetal検証・旧1234保持を行う。
