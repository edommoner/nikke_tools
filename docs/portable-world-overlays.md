# 敵世界overlayの接続契約

## 2026-10-21 共通208入力のCUDA／Metal一致

固定db8f4c8の共通実行器で、skill_damage武器モードとHeavyarms charge holdを含む208入力がCUDA／Metalで一致しました。全入力・全出力byte、125完全native／actual辞書、共有GPUソース、両生成コードのfingerprintを照合しています。WindowsはCPU11検査（終了処理5＋literal入力6）、GPU関数を禁止した全208入力生成とSHA一致の後、BelowNormal・180秒上限の実GPU1回で68.656秒、exit0でした。NVRTC・起動・同期・readbackの成功を50実測イベントで確認しました。

3JSON計96,679バイトを既存接続で取得し、各bytes／SHA、固定Git blob、事前検査、全208fingerprintとイベント順をMacで再監査しました。通常4682の再実行・GPU再試行0、元Windows作業／サービスを保持し、検証プロセス残存0です。Windowsのチャットは完了・待機状態です。共有したのはコード・ケース・小さな基準20ファイル331,359バイトだけで、rawと巨大詳細は各PCに保持します。

証拠は `research/portable-world-v82-cuda-validation.json`、`research/windows-portable-world-v82-summary.json`、`research/portable-cross-v82-receipt.json`。`research/portable_cuda_proof_audit.py` が共通のCPU証拠監査を行い、固定設定の `research/seal-world-v82-cuda.py` からGPUなしで再検証できます。通常受付CPU・全変種認証0/203を維持します。次は128枠の識別・世代・親参照を含むActorモデルと既存8対象の共通実行器の差を解消し、部位・阻止・召喚・HP／hit制HP・対象集合を接続します。混在selector、dynamic control・復活、全変種認証、必要な全検証後の効率化も未完了です。以下は段階ごとの記録です。

## 2026-10-21 Heavyarms holdのMetal208

共通実行器へHeavyarmsのvanish時charge holdを接続しました。静的な実在rosterからpolicyだけを入力にし、vanishの終了時刻・2秒上限・charge完成と期限はGPUが計算します。固定終了・終了不明・2秒の隣接値・複数vanish・再開・非camera・速度バフ失効・保持中の武器変更と再chargeの26条件を、元のHeavyarmsを含む完全native simulateと比較しました。完成後はcharge速度バフが失効してもfull latchを維持し、mode取消で完成chargeを解除します。状態領域と上限は共通schemaに集約しました。

初回206入力では、非cameraの1fixtureにcamera用ゲージ倍率300を残していた誤りを検出し、rawを保存しました。native123辞書を変えずGPU入力を100へ修正し、GPUソースと205入力の完全一致を確認して保存出力を再利用、変更1入力だけを実GPUで検証しました。その後、武器変更中の2スナップショットと共通状態schemaを追加した固定4bd848bで208入力を新規実行し、完全native125件・raw拒否34件・旧world49全出力が成功しました。旧179と途中206の全入力・全出力byte、99／123 native／actual完全辞書を保持しています。通常CUDA／MSL生成コードはv79と厳密同一、portable単体299件・旧native17辞書も成功しました。

証拠は `research/portable-world-charge-hold-validation.json`、`research/portable-world-overlay-charge-hold-metal.json`、`research/portable-world-charge-hold-expected.json`。Windowsは新規skill modeとholdを合わせた共通208入力を短く1回検証する準備中です。rawと巨大詳細は各PCのローカル保持です。通常受付CPU・全変種認証0/203を維持します。複合ally/enemy selector、Actor、dynamic control・復活、全変種認証と必要な検証後の効率化は引き続き未完了です。

## 2026-10-21 skill_damage武器モードのMetal179

実験ABI75の明示skill_damageモードを、同じダメージ式のnormal倍率・skill crit・core確率、着弾ゲート、ゲージ、弾数バフ消費へ接続しました。物理射撃の種類はcallbackによるモード終了前にGPUが保持します。初回175入力で2差分を検出し、rawを残して調査しました。元nativeの分類は、名前付き単発をスキル、pellet/core:pelletタグを名前にかかわらず通常着弾とするため、この着弾分類をスキル式・ゲージ・弾数消費から独立させました。これは現在のnative規約の保持であり、一律に全散弾をスキル扱いへ変更したものではありません。もう1件はカメラ中のcharge武器モードでfullChargeMultをゲージへ反映して解消しました。

修正版c953d3bのMetal新規179入力は全成功です。完全native simulate99件（従来70＋武器モード29）、不正入力31件、旧world49全出力を確認しました。前回CUDAまで確認済み146入力とその全出力byte、70件の完全native／actual辞書を、今回の成功・失敗両readbackから再監査して保持を確認しています。通常CUDA／MSL生成コードもv79と厳密同一、CPU状態を入力へ混入させない新規hostテスト4件を含む共通portable単体297件が成功しました。

証拠は `research/portable-world-skill-mode-validation.json`、`research/portable-world-overlay-skill-modes-metal.json`、`research/portable-world-skill-mode-expected.json`。`research/seal-world-skill-mode-metal.py` はGPUなしで固定ソースと全byteを再監査します。この29条件の新規CUDA実行はまだ行っていません。次の必要な短い検証へまとめます。Windows146の成功は保持し、元Windowsは待機中です。

Heavyarms固有のcharge hold、複合ally/enemy selector、Actor、dynamic control・復活、全変種認証は未完了です。通常受付CPU・全変種認証0/203を維持し、効率化は未着手です。

## 2026-10-21 CUDA／Metal146の全出力一致

固定6c8aaa5の共通overlay・shield／vanish・敵バフ解除146入力は、Windows CUDAとMac Metalの全入力・全出力byte、完全native／actual辞書、計算ソース、生成コードのfingerprintが一致しました。WindowsはCPU故障注入5件・Job Object子孫終了と、GPU呼び出しを禁止した全146入力生成／SHA照合後、BelowNormal・180秒上限のGPU実行1回で70.930秒、exit0でした。NVRTC・launch・同期・readbackの戻り値0を実測50イベントで確認しました。通常4682の再実行・GPU再試行は0、元作業・サービス保持、残存プロセス0です。

3つの結果JSON計73,073バイトを既存接続で取得し、個々のbytes／SHAと固定Git blob、CPU事前検査、全146fingerprintをMacで再監査しました。rawと巨大詳細は各PCに保持します。証拠は `research/portable-world-v81-cuda-validation.json`、`research/windows-portable-world-v81-summary.json`、`research/portable-cross-v81-receipt.json`。通常受付CPU・全変種認証0/203を維持し、次はskill_damage武器変更モードへ進みます。以下は段階ごとの履歴です。

## 2026-10-21 敵バフ解除・整数変換の共通接続

実験ABI75の本体1体に対し、enemy_buff_cleanseを既存のtyped instantと対象解決器へ接続しました。元の値をbinary64のまま保持し、nativeの `int(value or 1)` と同じゼロ既定値・ゼロ方向切り捨てを使います。32以上は最大ノード数32へ制限して巨大値の整数overflowを避けます。負数は解除なし、irremovableは飛ばし、開始時刻と宣言順の逆順で解除します。解除直後のsnapshotは維持し、次の別フレームで反映します。再開時の世代リセット、解除ログ、累積解除数も接続しました。既存debuff_cleanseとは別の明示フラグで区別しています。

初回144入力で整数直前の2条件が不一致となり、呼び出し側が最近接丸めmode0を指定していたと判明しました。失敗rawと比較を保存し、mode1の切り捨てへ修正しました。1.5／2.5の32ノード条件も追加し、修正版4057d19はMetalの新規1セッション146入力すべてで成功しました。native完全simulate70件（従来35＋敵解除35）、raw拒否27件、旧world49の全出力byte保持です。通常CUDA／MSLの限定正規化後の厳密同一性と旧native17辞書も保持しました。portable単体293件は初期実装3247e71で成功し、変更は解除呼び出しの丸めmodeと研究fixtureのみです。

証拠は `research/portable-world-overlay-cleanse-metal.json`、コンパクト全byte照合は `research/portable-world-cleanse-expected.json`、失敗原因は `research/portable-world-cleanse-integer-finding.json`。Windowsは新しい146入力だけを低優先度・180秒上限で1回実行する準備中です。通常4682の再実行は不要です。rawと巨大Metal詳細はMacに保持し、Windowsへは共有コード・共通fixture・小さなfingerprintだけを渡します。

skill_damage武器変更モード、Heavyarms固有charge hold、複合ally/enemy selector、Actor、dynamic control・復活、全変種認証は未完了です。通常受付CPU・全変種認証0/203を維持します。

## 2026-10-21 shield／vanishの着弾・ゲージ接続

共通計算ソースfe684eeで、shield／vanishを通常射撃、通常攻撃式を含む名前付きスキル、保留B3、lifestealの入口へ接続しました。遮断分は最初のノードだけに計上します。shieldは全てへの優越を要求し、基底コードとelement_code_overrideの現在のpresenceを使います。vanishは通常攻撃を先に遮断し、通常ゲージを止めます。shieldは通常ゲージを通し、遮断されたスキルのゲージを止めます。

静的cameraを入力へ追加し、非camera自動射撃の休止・射撃借金の廃棄・部分弾倉の再装填・MGの実停止時間に基づく冷却も接続しました。dynamic controlとHeavyarms固有のcharge hold、skill_damage武器変更モードは今回の認証に含めません。通常武器変更モードとcharge射撃は検証しました。

Metalの全100入力は、元CPU完全simulateとの35正例、raw拒否16件、旧world49の全出力保持です。初期の追加charge2件では、nativeのcharge.2秒＋待機.2秒に対しGPU入力の周期を.2秒にしていたfixtureの不整合を検出しました。元CPU35辞書を一切変えず、GPU周期を.4秒へ修正しました。GPUソースと98入力のbyte一致を確認して保存readbackを保持し、変わった2入力だけを新規実行しています。合成readbackの全100件について、各byteのGPU由来をCPU auditで追跡しました。失敗rawも保持しています。

通常CUDA／MSLは従来の限定正規化後にv79と厳密一致、共通portable単体293件と旧native17辞書も成功しました。証拠は `research/portable-world-gate-validation.json` と `research/portable-world-overlay-gates-metal.json`。`research/seal-world-gate-metal.py` はGPUなしで固定ソース・入力・全readback・CPU比較・合成の由来を再監査します。

enemy_buff_cleanse、skill_damageモード、Actor、dynamic control・復活、全変種の認証は引き続き未完了です。新gateのCUDA検証は、残るoverlay接続とMetal検証後に短くまとめて行います。通常受付CPU・全変種認証0/203を維持します。

## 2026-10-21 実験ABI75の本体接続

固定計算ソースa0e936a、入力89,376／出力225,280 words。GPUフレームで開閉したworldノードを開始時刻と宣言順で合成し、共通ダメージ本体の防御・core・適正距離へ渡しました。boss由来のreceived_dmg_pctはキャラ所有者を作らず、既存carrierと同じentryClockで挿入順にmergeします。キャラ敵バフを間に挟む1e16の相殺も元CPUと一致します。

Metalの1セッション74入力で、完全native simulateとの9正例、raw descriptor拒否16件、旧world49入力の全出力byte保持が成功しました。最初の9入力の全入力・全出力byteも初期版から維持しています。通常版の生成CUDA／MSLは従来の限定正規化だけで認証済みv79と厳密一致し、既存packing定数とcompiler5ファイルも維持しました。共通portable単体293件も成功しています。証拠は `research/portable-world-overlay-body-metal.json`、`research/portable-world-overlay-default-generated-parity.json`、`research/portable-world-overlay-default-packing-contract.json`、`research/portable-world-overlay-work-state.json` です。

これは防御・core・move・boss敵効果の開始／終了を接続した段階です。対象は本体1体に限定し、shield／vanishのlanding・ゲージ、enemy_buff_cleanse、Actor接続は未実装として拒否します。実験ABI75は通常受付へ開いておらず、CUDAでの新規overlay検証も未実施です。全変種認証0/203を維持し、次に残る共通処理とテストを接続します。通常版生成物の空行差分は比較基準を広げず、provider配置を直して解消しました。

これは元CPUの規約を固定した接続前の記録です。GPUのoverlay受付・対応済みキャラ・効率改善を主張しません。承認待ちv80の固定ソースと別の管理worktreeで開発します。

`characterize-world-overlays.py` は14契約と7つの完全なsimulateを検査します。元BossScriptと既存の元simulateを実行し、CPUで作った遷移表や中間状態をGPU入力へ使いません。防御・core・適正距離・vanish・shieldが実際の射撃ダメージを変える7条件では、武器spreadと適正距離も静的な明示入力へ固定します。既存17条件の完全なCPU結果辞書を再照合し、追加した任意のenemy／weapon入力が従来経路を変えないことも確認します。

## 数値と順序

- 開いているノードを `(start_t, declaration_index)` で安定順序に並べ、毎フレーム基底値から再構成します。宣言順だけで合成すると、後から開く先行宣言のバフで結果が変わります。
- 防御はノードごとにbinary64の乗算を丸めてから加算を丸めます。FMAは禁止です。負の途中値を0へ丸めません。防御低下等を含む既存ダメージ本体で初めて既存の下限処理を行います。
- coreは基底と生存対象を含む最大値です。開いているcoreの数値を変更するだけでなく、`core_hit`条件、通常射撃・通常攻撃式スキル、動的な確率とキャッシュキーを同時に接続する必要があります。
- moveは開始が後のものを優先し、閉じたら残るノードから再構成し、最後は基底へ戻ります。distanceと武器群一覧の両方式を混在させません。距離の閉区間とbinary64 EPS=1e-9を保持し、武器変更中の適正距離も既存の共通判定へ渡します。

## バフの寿命

敵buffの `received_dmg_pct` はenemy対象・pattern IDに束縛された効果です。仮のキャラ所有者へ付与して済ませません。開始で既存の敵効果管理へ入り、閉じたpatternの解除を新規付与より先に処理します。

敵バフ解除は `(start_t,index)` の逆順で、irremovableと既に解除済みのノードを飛ばします。スキル中の解除直後は同じフレームの防御・効果を変えず、次フレーム先頭で反映します。ノード自体の終了条件は維持します。繰り返しの再入場はdispelledをリセットし、前世代の効果解除と新世代の再付与を区別します。

## ゲートとフレーム

worldの確定はbattle_startより前、各フレームのtickより前です。条件・武器・バースト・攻撃対象順位が同じsnapshotを見るようにします。通知は既存のworldと同じくtick後です。

vanishは通常攻撃だけを止めます。名前付き武器変更スキルを通常タグだけで通常攻撃と判定してはいけません。shieldは全てに優越する必要があり、最初に止めたノードだけへblocked damageを計上します。vanishはshieldより先に判定します。ダメージだけでなく、通常射撃／スキルの異なるバーストゲージ規約と、固定終了のみ分かるvanish_return_atも接続します。

parts／interrupt／座標付き対象の生存・HP・世代・core・has_partsは別のActor接続が必要です。手動cleared maskを本体へ持ち込まず、GPUが所有するHP／世代から求めます。全overlayの本体接続と共通の正例・負例、旧4682入力・world49入力の保持、Metal／CUDAを確認するまで通常受付を開きません。
