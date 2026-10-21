# 実編成から共通world実行器への入力

`app/portable_world_roster_input.py` は `engine_worker.evaluate(... _portable_static_inputs=True)` の実準備結果を受け取り、全効果・実レベル・装備由来の基礎値・武器・カメラ・敵パターン・操作方針を共通の各sidecarへ接続します。研究用の効果差替え、武器変更、基礎値固定、効果フィルタは使いません。CPUでは静的CharStateの正規化だけを行い、戦闘・射撃時刻・数量・対象選択・生死は入力へ供給しません。

専用入口 `gpu/world_roster_entry.slang` は再装填入口を継承します。ABI0x5045568c、mode23、input104400word/output786432wordです。CUDA/Metalは同じSlang本体と入力・CPU基準・テストを使用します。public受付・通常画面はまだCPUです。

通常のkind5〜8（バースト待機短縮・回復・遮蔽物回復・HP減少）と既に実装済みのHP/確率/full/charging条件を共通の既存演算子へ接続しました。未実装の効果や操作は拒否します。canonical compiler/CPU referenceは変更していません。

## 保存実証

- 5aea8cc：初回6入力は3秒1件だけ一致。長い5件はteam1024/fraction2048の診断履歴上限でstatus64停止。raw・初回報告を保持。
- 903fc97：履歴上限後も実累積・counter・dispatchを継続し、省略件数を明示。6入力がCPUと完全一致。
- 76dc4de：旧入口の生成結果も保持する共通macroへ整理し、専用入口の不正4件を追加。最終Metal10＝実編成6＋拒否4が成功。6件全出力wordは903fc97の保存結果と同一。

実編成はMiranda/Dora/N102/Mary/Drakeの3・30・180秒と180秒成長変更、最後をBridに替えた30秒の通常/成長変更です。各編成70〜91効果、実成長・装備・スキルレベルを保持し、CPUの全員damage・HP/maxHP/def・遮蔽物・弾薬・射撃回数・reload/charge/fire待機・burst phase/gauge/cooldown・burst履歴と完全一致しました。全203キャラの認証や全効果組合せの証明ではありません。

最終M5のGPU command完了とinput/readbackのSHAは `portable-world-roster-metal.json` に保存しています。GPUの判定前にrawを保存し、`seal-world-roster-metal.py` がraw・Git固定source・CPU native6・保存指紋・旧20入口の生成完全一致をGPU禁止で再監査します。CPU531＋監査故障注入2＝最終533検査も成功。旧65/1063/通常4682のGPU再実行はしていません。

## 診断履歴と計算の区別

実編成専用入口では、team head+5、fraction head+3に省略件数を記録します。head+1は保存件数で上限に達したままです。上限後もイベント発火・累積・部隊counter・子効果を計算します。180秒ケースのteam履歴は1024保存＋7965省略、fraction履歴は2048保存＋15930省略です。全通知履歴を保存したとは主張しません。旧入口は従来どおり容量超過をエラーとして扱います。

## 全カタログの入力監査

`audit-world-roster-input.py` は全203キャラ＋21お気に入りの段階1/2/3、計266プロファイルを、明示した実5人編成で30秒入力へ変換します。CPU battle/tick/GPU build/executeを禁止し、全呼出し0を確認します。部隊効果を含む全入力変換はbase108、全152が成功しました。own定義だけの事前検査148とは別の尺度で、GPU admissionや戦闘認証ではありません。失敗114件も `portable-world-roster-input-readiness.json` に残しています。

未対応のbuff/selector、scaling/copy、source攻撃・interrupt・明示parts/操作、復活、全変種・長時間・容量・組合せ検証、legacy Metal14c8e2eの未解明差分と最終効率化は残ります。full_character_verified=0、full_goal_complete=falseを維持します。

## Windows v103

Windows v103は固定767f4f4274b5840da44cc48687572580f030d07a、codex/cuda-world-v103-source（12ファイル238622bytes）で計算検証に成功しました。CPU17・10入力/native6のGPU禁止照合、実base Python再照合とCPU Job smoke0.110550秒の後、BelowNormal/JobObject/start gate/180秒＋cleanup5でCUDA1回・176.942747秒。保存3JSON194699bytesをSHA一致で取得し、全input/output/native/generated指紋、API50段階PID22056/親39616、作成時刻、pre所属[22056]/post空、残留0/retry0、元HEAD/status保持を共通監査で確認しました。旧65/1063以下/通常4682再実行0。既存14プロセスの欠落とサービス識別未確定は残り、原因unknown、検証Job所属外・本番子より前の作成を確認。calculation_verified=true、preservation_verified=false、総合passed=falseを維持し、v102の既存7件も解消扱いにしません。GPU再実行は不要、turn01a15d03-a9b4-7ba1-92f2-1db1d530ba9f completed/idle、cursor223。詳細portable-world-v103-cuda-validation.jsonとseal-world-v103-cuda.py。上限まで約3秒しか余裕がなかったため、次回Windowsは変更対象の最小入力に限定します。GitHub共有は利用者からゴール達成まで許可済みです。
