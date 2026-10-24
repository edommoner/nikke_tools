# 盾混在時のbody吸血を共通実行器へ接続

HSI5の明示 `body_lifesteal=True` で、元ミルクの味方吸血16.16%を既存のbody着弾後処理へ接続しました。盾に吸収されたpacketはbodyへ渡さず、body吸血もしません。bodyへ届いたpacketだけが、従来どおり着弾→吸血→後続処理へ進みます。敵盾のゲーム仕様を推測した受付拡張ではなく、既存の宣言単一boss盾モデルに対する契約です。

新しい吸血式・時計・CPUイベント列はありません。Slangの既存 `applyLifestealState` と `storageBodyHeal`、武器pelletのbody抑止、skill Frameのbody fallbackを共用。CPUは既存 `_land` のbody抑止と、正本のbody着弾・吸血を共用します。旧HSI1〜4の吸血受付は閉じたままで、body policyなし・不正値・旧headerとの混在は拒否します。

元ノワール8・ミルク4・ドラー8・レイ7・ミサト5のskill定義と装備を含む全77定義を維持。3/30秒を、HP盾・hit盾・破壊後body・失効後body・owner世代違いの5条件で検証します。盾窓はBossScriptの2.8→3.2秒（失効対照は2.85秒）で、前の被ダメージから回復する条件を含みます。3秒のHP/hitでは吸血発動後もbodyへ届かず、盾の破壊/失効後と30秒側ではbody回復が生じます。

native observerは関数localsとHP変化を読むだけで、追加numeric queryやヒットを発生させません。例外時にはprofile・simulate・scalar・HitEvent・weapon scopeを復元します。GPUと照合する範囲は全battle/武器/HP/弾薬/gauge/trace、typed receiptと最終累積実回復量です。nativeの個々の吸血callback全履歴をGPUが個別出力しているという意味ではありません。

## 比較器の穴も保存rawで修正

実Metal13入力（native10・拒否3）は全件一致し、独立seal成功。実GPU3.313153秒、初回PSO65.182秒、library1.586秒、Runtime stride138952です。実行はrequired generation cache hit/追加Slang0でした。

その後、実raw3blockに対する破損注入で、従来比較器が累積healing欄を照合していないことを発見しました。31入力の実行はCPUで停止し、GPU claimは消費していません。比較器へnativeの実HP増加receiptの順序和と、GPUのquery/最終healing欄の厳密照合を追加。HP・healing・statusの12破損を全て検出し、保存済み13入力をGPU0のreplayと別process sealで再監査しました。全input/native/output/goldenは変更していません。このreceipt監査は現在の共有回復なし編成を対象とし、heal_splitは別の受益者receiptが必要です。

## 既存経路と回帰

変更は3既存shaderの限定header/admission分岐と新entryのみです。元HSI4のAoE18入力/native指紋は同一。新しいsourceから生成した旧経路のCUDA/MSLは、正規化前の全byteまで旧保存生成と一致しました。normalizer・binary64・量core・Runtime field・保護CPU4ファイル・pinned upstreamを変更していません。厳密な3source逆変換は過去fixtureの監査専用で、数値比較や現在のgoldenへ適用しません。

独立した単独suite `destructible-body-lifesteal`13と、旧AoE18を合わせる `destructible-body-lifesteal-retention`31がMetal一致・各独立sealに成功しました。現在の入口は後者です。旧AoE18は全75,497,472 byteが一致。吸血13は7ケースが全raw一致、残る6ケースは配置indexが18増えたため、scratchの絶対出力アドレスword941074だけが18×1048576増加しました。全wordを読み直して差分を固定し、元raw・厳密な保持検査の失敗・全input/native指紋を保持します。計算欄の差分はなく、normalizerや計算比較に除外を追加していません。最終固定版はCPU53検査を77.752秒、native26の事前照合を19.262秒で成功。31入力のGPU計算は9.804687秒、cached PSO0.002960秒です。共通制御372検査は371成功/Windows専用1skip。各SHAは `research/portable-destructible-body-lifesteal-checkpoint.json` を参照してください。

旧AoE・skill各goldenは旧sourceの履歴として保持し、新checkoutでsource staleになっても自動追従させません。元の固定package/captureは引き続き監査可能です。現在sourceの検証は上記の新entryを使います。

## 残件

ダメージ蓄積は引き続き拒否します。正本はbody着弾・吸血後に蓄積し、放出は既存poolからtake→split倍率→整数化→landing queueへ進みます。盾選択に対応する放出quantityの継続処理、共有回復・貫通・parts/coords/ADD混在が次の対象です。

全キャラ認定0・通常UI CPU・残20 model gapを維持。Windows追加実行0、現full battle CUDAの実機計算・cache性能は未確認です。旧7プロセス終了原因unknown/環境保全falseも変わりません。終了済みrawのゼロ領域だけを疎化して検証容量を確保し、元byte/SHA/inode・失敗・claimは保持、raw削除0です。
