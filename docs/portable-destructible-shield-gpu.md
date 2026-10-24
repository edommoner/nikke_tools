# HP盾の実戦迎撃を共有Frameへ接続

共通CLIのsealed suite `destructible-shield-battle`を追加した。前段のCPU15契約を同じbattle scheduler・DFS Frame・共有modifier scalar・既存receipt/counterへ接続し、Apple M5のMetal88入力（native58・拒否30）が全件一致した。GPU実行は1回で成功し、保存出力の独立sealもGPU0で成功した。通常武器/hit盾/貫通の迎撃、ゲーム規則、全プロフィール、CUDA実機の認定は未完了。

## 共通実行器の変更

`destructible_frame_runtime.slang`の対象選択をprovider化した。既定は従来のall_projectilesで、新しい入口だけがrowごとのroute2/3を渡す。route3は生存HP盾のowner kind/identity/generationを明示boss handleと照合し、最初のbinding slotを選ぶ。1つ目を選んだ後は他の盾を同じ発へ追加しない。全量を既存Frameに固定し、兄弟/子イベントによる再計算や再選択はしない。

該当盾がなければFrameを変更せず通常のskill continuationへ戻る。body処理を始めたFrameには後から割り込まない。盾を破壊した発の余剰は本体や次の盾へ流さず、次発・named完了の子・破壊counterの子がそれぞれ新しく選択する。新しいdispatcher、時計、ダメージ式は作らない。

盾へ向かう量だけを、投射物にも使った同じ`destructibleModifierDamage`へkind3で接続する。通常bodyへのfallbackは元の`damageValue`を使い、盾補正を混入させない。Frame、量確定、着弾、同期counter continuation、完了通知/gaugeの流れは共通のまま。native observerも元のhandlerの実採取係数とsource行を観測し、共有decoderがそれぞれbit列/行番号を照合する。別CPU実行から採取した値やCPUイベント列をGPU入力へ渡していない。

入力110112wordは、旧109536word＋DMB1 header32＋modifier axis256＋route256＋owner header32。新owner headerはHSI1 magic、BODY/identity0/generation1と予約0を要求する。routeは0/2/3のみで、非damage行・未使用行・plain契約外の行を拒否する。既存DBT1 descriptor、typed出力/receipt配置は維持する。出力1048576word、Runtime全field/offset/stride138952byte、binary64・strict normalizer・保護CPU/compilerは不変。

## 実証範囲

|入力群|native|拒否|観測|
|---|---:|---:|---|
|旧destructible-battle44|31|13|旧dispatch位置、nativeとraw全バイト保持|
|旧modifier-battle18|12|6|native全指紋と同じ比較項目を保持|
|新HP盾15|15|0|CPU15契約と同じ実戦結果|
|新wire拒否11|0|11|axis/route/owner/magic/reserved|
|合計88|58|30|全件一致・独立seal成功|

HP盾15件は、補正50%で1451/1451、投射物補正の非混入968/968、HP500破壊後の次発body968、ownerなし/ADD owner/古い世代の除外、2盾のslot0→slot1、0.15秒のworld終了、named係数150で2177/2177、modifier失効、普通のATK damageとの加算1838/1838、named子726、破壊counter子のbody484、再出現世代1/2/3を確認した。通常物理は既存のbody経路のままであり、この点を武器迎撃の実証とは扱わない。

graph/時計、damage、allies/covers、shots/ammo、敵hit/log、RNG/gauge、typed状態/owner/世代/攻撃/receipt、counter状態、context解放を既存比較器で照合した。実raw7blockをfixtureとして保存し、6正例のstatus・owner・clock・source行・係数・量・delivered・tookの48改変と、拒否結果改変1件を検出した。

## 証拠と実行費用

producer packageは`c800e398c36d57beafbf9a7abc2f8f0f06362b124c831dfd10f493d07a5b9d03`。旧44ケースは新inputの先頭109536wordが元input SHAと一致し、native指紋も一致した。既存の`capture_fingerprints`で旧/新comparisonのSHAとraw全ファイルを再検査し、旧44の全raw184549376byteが新88の対応領域と完全一致した。追加wireまで同じinputと称していない。旧18はdispatch位置が変わるため、absolute scratch pointerを含むrawの全バイト保持は主張せず、native指紋と全意味項目の比較を記録する。

GPU0.068128秒、library1.559128秒、pipeline65.066406秒、transport全体68.096856秒だった。実runはgeneration cache必須hit・追加Slang0。CUDA/Metal生成の初回2コンパイルはgeneration-only段階で行い、sealed最終packageから両生成のstrict指紋/reflectionを必須cache hit・追加Slang0/GPU0で再確認した。CUDA cache/JITの恒久改善やCUDA実機成功をこの結果から主張しない。

最終sealed package `2b820131b02d9a2818f578bdfbee03a6a25baaf29b06df06b9ad78cae66ecdd3`をfresh unpackし、CPU21群184検査（skip0）とnative58の基準照合が成功。初期tableの旧modifier拒否6件の欠落、旧source assertionのinverse接続漏れによるCPU失敗を保持し、GPU実行前に修正した。入力順の修正もGPU前だけで行った。同一claim再試行0、GPU失敗/再実行0。

容量は既存`sparsify-raw`で終了済み旧492 rawのゼロ領域を回収した。論理1547698176byte・全SHA・inodeを保持し、割当1547698176→440926208byte、1106771968byte回収。raw削除0。新88のinput38759428＋output369098752byteと1GiB予約の検査をinput前/claim前に通過した。

## 現在の入口と残件

今後はこの88入力のsealed入口を使う。Frameのsource identityが変わったため、開発checkoutの旧frame/battle/original/modifier-battle専用goldenは履歴sourceのままで、CLIはstaleとして実行を拒否する。旧固定package・raw・goldenは保持する。厳密な全ファイルinverseは保存fixtureの履歴source検査だけに使い、新しいGPU計算証明やgoldenの自動更新へ転用しない。通常147sourceと専用scalar119sourceは変更していない。

全266profile・245packing/base185・issue/順位/20model gapは保持。shield_dmg_pctに限定実証metadataだけを追加し、公開GPU受付・全キャラ認定0・UI CPUは維持する。Windowsの状態取得は利用不可、新規run依頼0、CUBIN O0実証は未実施。7プロセス終了の原因不明・環境保全falseも維持する。

次は通常武器/hit盾/貫通を同じ選択/着弾実行器へ接続し、ADD owner・対象別DEF/敵debuff・元プロフィール全体を進める。boss handleとbinding slot優先、overflowなし、第5因子への補正というv1宣言をゲーム規則の確認済み事項にしない。証拠は`research/destructible-shield-gpu-evidence/manifest.json`、checkpointは`research/portable-destructible-shield-gpu-checkpoint.json`。
