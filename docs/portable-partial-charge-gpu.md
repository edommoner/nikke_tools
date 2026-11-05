# 短押し・非フルチャージの共通実行器

`gpu/world_partial_charge_entry.slang` は既存のresident実行器へ
`PORTABLE_PARTIAL_CHARGE` を加える開発専用入口。計算本体・効果定義・正本比較は
CUDA/Metal共通で、公開入口は従来どおりtap wire2とevent40を拒否する。
全キャラ認定、UI GPU化、現在のソースのCUDA実機検証は未達。

## 状態と通知

静的なtapのhold/charge/release/post/full_intervalだけを入力とし、発射時刻・結果を
CPUから渡さない。制御wire2のowner maskを厳密に検査し、charge開始時に論理行1..8と
周期的full指定を保持する。バッチ位置に依存する絶対入力アドレスは状態へ保存しない。
許可するwindowはalways/burst_charge/own_full_burstのみ。

発射時にfull判定と武器倍率をsnapshotし、partialではfull通知・charge倍率・full用
ゲージ倍率を適用しない。event40はon_attackの後、hit_countの前に発行する。
tapの次射時計はreleaseとpostを正本の順序で加算する。reload、2銃口、武器変更callback、
チャージ速度の追加・失効、fullへの自然到達と周期的fullを比較対象に含める。
Runtimeのサイズ138952byte、入出力stride、既存容量は変更しない。

## 整数設計

非フル発射回数の基準は原文と符号付き32bitを保持する。正本の判定は
`max(1, base - int(ordered_reducer_sum))`。先にbaseを1へ丸めてはいけない。
非正のbaseはwireの閾値1とpayload flag1、符号付きtagで表し、正のbaseは従来経路を使う。
legacyコンパイラーには静的な中間値1を渡し、original effectからwireを復元する。
CPU正本、既存compiler、binary64・整数変換・powプリミティブは変更しない。
共有reducerでは非正baseの差を安全なint64で計算してから最小1を適用する。
512×1e8の既存reducer上限の範囲内であり、正のbaseの経路は維持する。

## 再現と境界

共通CLIの `partial-charge` は45入力（正本23/拒否22）、
`partial-charge-extended` は14、`partial-charge-rosters` は全77定義のクロスト4、
`partial-charge-reduction` は11（正本7/拒否4）。
`partial-charge-retention` は旧1442を含む1516（正本1192/拒否324）。
いずれも `package --suite NAME --develop` → fresh `unpack` → bounded Metal `run` →
GPU禁止の独立 `seal` を使用する。実際の成否・指紋はcheckpoint/evidenceに保存する。

実編成の物理traceは容量770と省略数を保持する。全packet・全skill個別traceの証明ではない。
lazy/random数値readerとtapの混在は[数値参照・抽選順](portable-partial-query-gpu.md)の17契約で
開始時／待機時参照・回復live走査・mode終了cacheの実差分を修正し、全1533入力で保持検証した。
広いカタログ、追加stat・武器・制御interleaving、現CUDAは残件で、全consumer一致とはしない。

初期extended v1はcamera設定とDOWN_Charge fixtureの時計不整合で失敗しraw/claimを保持。
入力を正本の静的条件へ直した別packageで検証した。絶対行→論理行の移行は
`research/audit-partial-charge-state.py` でソース3置換、入力・native不変、
1505入力のraw中33wordだけの変化と他4734320508byte保持を監査した。
この表現移行監査は整数修正後の差分を許可するためには流用しない。

Windowsの7プロセス終了は原因unknown・保全falseを維持する。利用者は当時の終了・
再起動等を否定し、ゲーム・動画利用の可能性を回答したが因果関係は未確認。
この区間でWindowsの追加実行は行わない。
