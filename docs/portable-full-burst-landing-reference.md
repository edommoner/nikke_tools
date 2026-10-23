# フルバースト開始後の着弾契約

`land_in_full_burst` を次の共有実行器への接続対象とし、共通CLIへ合成13契約と元イレグ：ブーム＆ショック3/30秒の2契約を追加した。GPUの受付と本体は変更していない。既存のB3 `bonus_damage` を示す保留フラグをそのまま流用すると、値を読む時点とキューの意味が違うため誤る。

発動条件・budgetはcast時に確定し、その後に条件用の印が消えてもlandingで条件をやり直さない。参照hit数もcast時に固定する。正本はlandingで通常の参照読取を一度実行してから `_latched_hit_count` へ戻す。契約ではcast-countが1→2と増えるが、実際の攻撃は1回である。この2回の読取を「不要」として消さない。読取は既存 `reference_count_runtime.live_reference` から実際に返る値をprofileで記録し、追加照会しない。

通常の即時スキルは次の1/60秒フレームへ着弾する。フルバースト保留分は開始フレーム内で作成・着弾する。合成ではcast0.2秒、full-burst landing35/60秒で、stage2即時はcast0.1秒から次フレームへ進む。フラグfalseとstage2の対照を含む。

着弾ではentry buffを読み、同じcasterの後続burst_cast buffを除外する。攻撃力、倍率を前後に置いた対照を固定した。親は3150、倍率が先なら6300、後なら3150で、即時の対照は1075になる。従来B3 bonus1575は新しい親より先に着弾する。親3発の各3150は維持され、子のATK更新を伴う子攻撃は1260/1323/1386になる。名前付き子通知と、その後の通常キュー実行を混同しない。

合成は1/3/13hit、0と負のhit数、参照1の固定とlive2の読取、未所持参照、flag無効、stage2、従来bonusとの混在、前後の倍率、親子順を含む。合成handler24回・親通知36回・全packet40件を確認した。元イレグ3秒は発火0、30秒は「13 고스트」の6hitが1回発火し、handler2回・通知6回を確認した。元13hit条件の分岐は今回の実編成では未発火で、13hitは合成契約だけである。

観測器は既存のprofile呼び出しを連鎖し、元profileを復元する。全battle/skill trace/最終RNGと、get_buffs/ref_count/_by_name/notify/sampleの呼び出し回数を合成13と実編成2の観測前後で照合した。回数固定値、除外scope、full flag、時刻、owner、通知、参照読取の削除とpacket金額の故障を拒否する。

固定package `bb35b29375e449839dcaac2c2d1e1199617de6259137c68e235c4ddd60b591ff` でreference13+2、CPU5群27検査(skip0)15.365秒、旧230入力のnative事前照合12.532秒が成功した。最終の等価性検査を実編成2にも広げた単体5検査も5.864秒で成功した（テストだけの拡張で旧230を再計算していない）。GPU source133ファイル、旧230 input/native期待値は不変で、前回のMetal230の証拠を元のscopeで保持する。Slang、NVRTC、GPU build/execute、Windowsの追加実行は全て0である。

全266profile記録、239入力SHA、27拒否、37分類のcodeと順位を保持した。`sequential_damage:6/13`・`enemies_random`・fieldsがland_in_full_burstだけの2分類を、記録済みの正本契約から共有loweringへ案内するlaneに移した。これは受付追加やGPU実行の証拠ではない。他の未確認fieldsを持つ定義は元のreviewへ残す。

## 共有実装への接続方針

1. 既存の `attack_timing_specs.full_burst_landing` とlegacyの静的planを使い、privateの別モードとして詰める。現在のdamagePending真偽値の受付を無条件に広げない。署名・型・stage・cast timing・count boundsと参照名を検査する。
2. 既存のpending配列とrow identityを再利用できるか確認し、modeごとに読む値を分ける。従来bonusはcast時の係数を保持する。新modeはcastの条件とhit数を保持し、landingで通常のdamage計算を行う。cast時に計算した暫定係数の照会も正本では実行され、結果だけが再利用されない。値が0の早期return、HP basis、倍率、乱数を伴う値の読取は追加契約で固定する。
3. 符号付きの0/負hit数を正の巨大uintへ変換しない。既存配列へ符号付きbitを保持する場合も、実行回数への変換は明示的に0へclampする。参照値の欠落と0を数値設計上区別し、landingの実読取と固定値への復帰を両方保持する。
4. 正本の `_pending_burst_dmg` と `_pending_landing_dmg` の二つのキュー順を保持する。共有配列へ入れる場合でも、従来bonus全件→新landingの順に処理する。既存のpending観測counterは従来キューの意味を持つため、新modeの件数を加算してはいけない。mixed fixtureでは旧pending counterと新着弾を別々に照合する。
5. 除外scopeは親だけへ適用し、通常の子へ持ち越さない。新landingは通常のtyped receipt経路へ接続し、フルバースト内の親の同フレーム着弾と、子の通常キューを保持する。Runtime増大を前提にせず、queue上限・overflow拒否・旧230と元実編成の保持を検査する。
6. 追加契約を整えた後、固定package・生成のみの事前検査・生成cache必須・短いMetal実証・保存結果sealを行う。前回と同じ入力をGPUの回復手段として繰り返さず、比較器修正なら保存結果をreplayする。現CUDAは必要な小さな検証だけにする。

これらは次の実装方針であり、GPU実装済みとは数えない。全キャラ認定0、通常UI CPU、現CUDA未検証、全体目標未達を維持する。根拠は `research/portable-full-burst-landing-reference-checkpoint.json` と `research/full-burst-landing-reference-evidence/`。CLIの正本入口は `reference --suite full-burst-landing` / `full-burst-landing-rosters`。`full-burst-landing-reference` packageはCPU準備suiteで、新機能のGPU suiteではない。
