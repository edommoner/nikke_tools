# 敵世界overlayの接続契約

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
