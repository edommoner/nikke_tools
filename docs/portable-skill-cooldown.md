# 共通の残りスキルクールタイム短縮

`skill_cooldown_reduce_pct`は既存canonical compilerのkind22を使うinstantです。発動時点で対象キャラが所有する初期化済み`every:Ns`の時計だけを変更します。CPUの途中状態・発動予定表は入力へ渡しません。CUDA／Metalの実装は`gpu/skill_clock_runtime.slang`一つです。

計算順序は`factor = max(0, 1 - value / 100)`、`next = t + max(0, next - t) * factor`です。`periodPrevious`や元のintervalを変えず、以後の発火・条件確認・再予約は既存の共通tickへ戻します。未初期化の時計は作りません。値0は対象queryを行わず、100%以上はfactor0、負値は残り時間を増やします。`target_effect`はnativeと同様にフィルターではありません。

対象は既存の味方recipient計画から選び、配列の重複はsetとして一度だけ適用します。literal名、別owner、all_allies、rank、編成にいない名前を共通fixtureで検査しました。通常の外部イベントAPIでは受付を開かず、private combat worldだけで扱います。

## 時計の数値境界

量のraw入力には有限値を要求します。一方、繰り返しの巨大な負値で将来時刻がInfへoverflowし、その後factor0との積でNaNになる場合、nativeの時計はその値を保持します。この時計固有の状態をダメージや整数変換へ流用しません。

周期発火の判定を、有限値を仮定した`!(now < next)`から、順序付きの`next < now || next == now`へ変更しました。NaNなら発火せず、後から別の短縮が来るとnativeと同じ引数順の`max(0, next-t)`で0を選び、時計が復帰できます。既存のソフトウェアbinary64とNaN正規化は変更していません。rawのNaN量は引き続きstatus64で拒否します。

初回23入力では巨大負値の反復だけがstatus16となりnativeと不一致でした。原captureを保持し、入力を除外せず時計の設計を修正しました。追加したInf×0の非発火・NaNからの復帰を含む21正例＋4不正入力は、修正版Metalでnative完全一致です。一度の短縮後に元の周期へ戻ること、同一時刻の定義順、短縮自身も周期効果である場合、条件不成立の時計も含みます。

## 実編成と回帰

センチの通常／favorite1が新たに静的packing可能となり、182/266profile、基本キャラ127/203です。各3秒／30秒の4実編成入力も、全定義を保持してnative比較しました。集約回帰149はnative118＋拒否31で成功し、旧145入力のinput/readbackは全byte一致です。新機能25入力と同じGPU sourceから実行しました。

共通CPUテスト645件成功、Windows専用1件はMacでskipです。Windows v110は一つ前の固定ソースのcompiler-only確認で、O1のargvは通りましたがptxasのメモリ確保失敗でartifact未完成、GPU0です。新しいkind22のCUDA数値一致、全キャラ実戦認定、通常画面接続は未完了です。
