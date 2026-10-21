# entry_reloadのCPU正本契約

武器変更のentry_reloadは未対応です。既存のentry_delay実行器へ接続する前に、pinned CPUの照会順序を確認しました。GPU計算・packingは追加していません。

calculator/timeline.pyの_tick_weapon_changeは、明示entry_delayがなければentry_reload有効時に_reload_durationを呼びます。この照会は新セッションの初回だけでなく、待機中・待機後の各モードtickでも実行されます。待機終了時刻自体は初回に確定し、後の照会値で再設定しません。後続照会を省略しても同等だと仮定せず、lazy buff等への影響をfull-native observerで確認する必要があります。

_reload_durationを呼ぶ時点ではモード武器への一時差替え前なので、元武器のreload_timeを読みます。fixed reloadがあればそれを優先し、なければ元時間×max(0,1-reload_speed_pct/100)です。明示entry_delayは0でも優先し、このreload-duration照会を行いません。charge開始は待機終了後です。

既存mode_entry_nativeとliteral factoryを再利用し、元武器0.5秒／モード0.9秒、明示delayなし／0／0.1秒をCPUで対照しました。0〜0.2秒の13tickで、delayなしは毎回0.5秒を読み、2回目以降も確定済み終了時刻0.5を観測しました。明示delayありは照会0回でした。小さな原probeはresearch/portable-entry-reload-native-probe.jsonです。

再利用可能なCPU契約はtests/test_portable_entry_reload_reference.pyにあり、owner0／4・auto／charge・delay3種の12条件を検査します。portable packingとGPU build／executeは禁止しています。このobserverは単独CharStateの検査で、full-world比較やGPU対応の証明ではありません。

full-world契約への接続結果は以下を参照してください。GPU側は既存MODE entry policyを拡張する候補ですが、共有reload計算の再利用と正本の毎tick照会を両立できることを先に確認します。CPU時刻をGPU入力へ埋め込まず、未対応の動的magazine／skill-mode等の拒否は維持します。

## full-world契約と共通CLIへの接続

`reference --suite entry-reload --out <新規JSON>`を追加しました。既存のfull native projectile→reload→control→team→frame observerを再利用し、32 literalケースで実際のモードtick、_reload_duration呼出、begin_weapon_sessionの前後を記録します。追加のstat照会は行いません。速度負値／50／100／150％／合算、固定0／正／負／最大値／速度無視、補正の途中到着と失効、明示delay0／0.17、auto／charge、owner4、有限終了、3回再入、遅延発動、元charge／reload中、cover gate、名前付き子イベントを含みます。

負の固定値はクランプされず、初回時刻0ではentry_until=-0.2のまま即時射撃します。通常の速度補正のmax(0,...)と混同しません。既存アプリのweapon_mode_runtime.begin_sessionは元charge／reloadをモードtickの前にresetするため、観測はreset前も記録します。pinned upstreamだけを直接読むのでは足りません。

Macの全CPU回帰743件中742成功・Windows専用1skip・失敗0です。32ケース全件の契約、観測あり／なしの全戦闘field・skill trace一致、latch破壊／元武器誤読／照会欠落／早期射撃の故障注入を4 CPUテストで検査しました。CLI実行は約1.81秒、GPU0／packing0です。source identityにapp内のPython互換層とportable_*contracts.pyを含め、実行中変更を検出します。既存のrevive契約も保持しました。構造化証拠はresearch/portable-entry-reload-reference-checkpoint.jsonです。GPU対応数・静的packing数は増えていません。

## カバー中の補正変更を追加した35ケース

カバー中に速度補正が失効、固定時間が到着、実測entry_delayを使用する3ケースを追加しました。nativeのsession resetはt=0ですが、最初の実mode tickはt=0.21666666666666665です。速度50％がt=0.1までに失効するケースの初回照会は元武器の0.6秒、固定0.2秒がt=0.1に到着するケースは0.2秒です。実測0.17秒のケースはreload-duration照会0回で、カバー解除後のmode tickから待ちます。

したがって、GPUへ接続する際にlogical modeの発動やsession resetと待機開始を同一視できません。既存selectWeaponの物理状態初期化、control gate、実際のmode tickでの照会・初回latchを区別する必要があります。実測entry_delayとカバーの組合せも同じ境界で比較します。負の固定値と待機完了済みを単一の負値sentinelだけで区別しようとせず、必要な状態を明示する方針です。

35ケース全native契約と観測透過性の4検査が成功し、以前の32ケースは全入力・native・trace・契約レコードが完全一致しました。構造化証拠はresearch/portable-entry-reload-covered-checkpoint.jsonです。この追加ではGPU build／execute／packingはすべて0。以前の全CPU回帰743件は履歴として保持し、今回全体を再実行したとは扱いません。entry_reloadのGPU対応は引き続き未完了です。
