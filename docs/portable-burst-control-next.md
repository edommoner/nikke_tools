# 次のburst操作producerの移植契約

現入口は `control.burst` を明示拒否しており、この文書は対応済みの証明ではない。正本 `calculator/timeline.py` の `BurstController._try_stage` と `_predict_next_fb_start`、共通 `gpu/combat_runtime.slang` の `burstFrame`、`gpu/coordinate_aim_runtime.slang` の時計を接続対象とする。squad sequenceのfocus／cover_allとは別軸。

- delayは、候補が準備できていても段階全体を遅らせる。後順位の候補へcontinueしない。押下時刻は `max(stage_open_t, ready_at[owner]) + delay`。cooldown待機のmaskを設定すると後のcooldown低下によるmin更新でdelayが消えるため、両待機を区別する。
- wait_own_cooldownは本人の残cooldownが指定範囲以内の時にだけ、その候補で段階全体を待機する。正本の範囲0.5〜3秒とfalse、および時刻比較epsilonを数値契約へ固定する。down／stun候補は先に除外する。
- patternは候補削除ではなく周期ごとの後順位化。明示burst_sequenceがあればそちらが優先する。cycle index、再突入、A/B段階の選択と既存の明示候補flagを同じ共通候補実行器に載せる。
- 実際のburst候補・段階開始時計と、未観測時の次FB予測が同じdelay／順序契約を使う。観測済みのcycle外挿をCPUで入力しない。GPUがburst開始／終了の観測から自分で更新する。

比較ケースには、同段階の代替がreadyでも待つdelay、自分のcooldownが遅く解除されるcycle、境界直前直後のwait、cooldown減少、down／stun、明示順序、patternの代替fallback、再突入、reload into_fbの予測合成を含める。CPU正本のprotectedファイル・pinned upstreamをGPU都合で書き換えず、world native adapterのconfigへの静的literal受け渡しを明示監査する。元データと矛盾するweapon cooldown literalは現方針と同様に事前拒否する。

候補policy単体は `portable-burst-control-policy.md` の347正本＋34拒否で共通Slang/Metal実証・独立seal済みです。本書の戦闘接続要件は残り、現world入口は引き続きcontrol.burstを拒否します。次は実証済みhelperをRuntimeと時計へ接続してください。
