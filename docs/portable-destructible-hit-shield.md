# hit盾を既存の選択・着弾Frameへ接続

後続の通常武器のnative CPU契約22件は[武器の盾接続設計](portable-destructible-weapon-shield-native.md)を参照。武器GPUは未接続で、以下はskill向けMetal111の記録。

共通CLIのsealed `destructible-hit-shield`を追加した。HP盾と同じ実戦scheduler・選択・Frame・receipt・counter continuationでhit盾を処理し、Apple M5のMetal111入力（native76・拒否35）が全件一致した。GPU実行は1回で成功し、保存出力の独立sealもGPU0で成功した。通常武器・貫通・ADD owner・全プロフィール・ゲーム規則・CUDA実機の認定は未完了。

## HP量とhit creditの分離

明示V2 policyは、owner kind/identity/generationがboss handleと一致する生存HP盾/hit盾を同じbinding slot順で1つ選ぶ。従来V1はHP盾だけを選び、hit盾を通り越す規則を維持する。混在順は宣言モデルであり、ゲーム内優先順位を確認したものではない。

plain boss skillの1 packetはcredit1を持つ。hit盾の残数はこのcreditだけを消費し、HPダメージ・crit期待値・係数・盾ダメージ補正で残数を増減しない。通常scalarの解決量をImpactの診断/counterへ保持するが、HP盾専用factorは適用しない。ActorKindはHIT_SHIELDのままで、BODYへ種別を置き換えて保存しない。HP盾を選んだ発は従来どおりHP専用factorを使う。

`destructible_shield_battle_entry.slang`の選択providerとscalar providerだけを拡張した。`destructible_frame_runtime.slang`、typed quantity core、`dwLand`、counterの同期子、gauge/完了通知は変更しない。新しい実行器・時計・ダメージ式・credit数式は作らない。量の消費は既存coreのkind4→credit、kind3→HPという分岐を再利用する。

source rowごとにV1 route3とV2 route4を区別する。HSI1 headerは従来のflag0を要求し、HSI2だけがflag1/route4を許可する。magicとflagを片方だけ変えた入力、未知route、予約word、非整数のhit容量を拒否する。input110112/output1048576word、Runtime全field/offset/stride138952byte、binary64・strict normalizer・保護CPU/compilerは不変。CUDA/Metalは同じソース・表・比較器を使う。

## 18契約の結果

|条件|Impactの解決量|消費した量/残数|
|---|---|---|
|容量2へ2発|968/968|各credit1、残0|
|容量1を破壊|968|credit1だけ消費、次発body968|
|hit容量1→HP容量5000|968/1451|credit1→HP1451、残0/3549|
|HP容量500→hit容量2|1451/968|HP500→credit1、残0/1|
|HP補正900%／投射物補正50%|968/968|各credit1のまま|
|係数100000|967500/967500|各credit1のまま|
|named係数150|1451/1451|各credit1のまま|
|named子／閾値counter子|親968・子484|別packetのcredit1ずつ|
|破壊counter子|盾へ968|子484と次発968はbodyへ|
|3回再出現|各世代へ968|世代1/2/3へcredit1ずつ|
|他owner／古いowner世代|迎撃なし|残数を維持|
|0.15秒でworld終了|初発盾968|次発はbody、credit追加なし|
|HP盾だけを選ぶV1|迎撃なし|hit盾の容量2を維持|
|元係数0|packetなし|credit0、残数2を維持|

body fallback、破壊した発のoverflowなし、子ごとの再選択、context解放はHP盾と共通のまま。通常物理は今回も元のbody経路であり、武器迎撃の完成ではない。

`reference --suite destructible-hit-shield --out NEW.json`は同じ18 CPU契約をpacking/build/execute禁止下で実行できる。18件全てをreference_model_gapに保ち、canonical positive0として記録する。新しいnormal admissionを有効にしていない。

## 保存結果と効率

producer package `8fd9e953d6d0b9fc776e5f1bab91b3f9c7f1a0dbda1e95c098539db5414641a2`で111入力を実行した。旧88は元の入力順を維持し、共通CLI `readback-retain`で旧/新comparisonのSHAとraw全ファイルを再検査した。旧88の全input/native指紋と全raw369098752byteが完全一致、欠落/変更0。歴史sourceのgoldenやrawを更新して通したものではない。厳密なentry全ファイルinverseは履歴fixtureのsource検査だけに使う。

GPU0.068622秒、library1.572529秒、pipeline65.071439秒、transport全体68.209232秒。実runはgeneration cache必須hit・Slang0。初回CUDA/Metalの生成2回はGPU0のgeneration段階で行った。最終sealed packageから両生成のstrict指紋/reflectionをcache必須hit・追加Slang0/GPU0で照合した。新GPU1・同一claim再試行0・Windows追加実行0。今回CUDA cache/JITの速度改善や実機成功は主張しない。

最終sealed package `bb01ce510b5a68e047f368c607de137652bd87ba4d9722853b9a7e83fa7e1153`をfresh unpackし、CPU22群191検査（skip0、39.557秒）とnative76の基準照合が成功した。

実GPU8blockのfixtureで、7正例のstatus・世代・残数・owner・source・係数・delivered・tookの56改変と拒否結果改変1を検出した。独立sealは保存111入力全体を再比較したものなので、fixture8件だけを全111入力の代わりにしていない。

容量ガードが最初に不足を検出したため、GPU claim前に終了済みrawを既存`sparsify-raw`で疎ファイル化した。旧88と旧damage-battle460の全byte/SHA/inodeを保持し、合計1307639808byteを回収、raw削除0。新input48889732＋output465567744byteと1GiB予約は、input前/claim前の両方で通過した。ケース数を減らしていない。

## 現在の入口と残件

現在のsealed入口は111入力の`destructible-hit-shield`を使う。旧88の専用goldenは履歴sourceのままで、開発checkoutではstaleとして実行を拒否する。旧固定package・raw・全fingerprintは保持する。HP盾V1は新111でも旧88の一部として実行し、全byte保持を確認済み。

全266profile・245packing/base185・issue/順位/残20model gap・全キャラ認定0・UI CPUを維持し、shield分類へplain skillのhit-credit限定実証metadataだけを追加する。Windowsは今回は再観測も実行もしておらず、直近の接続状態は利用不可。CUBIN O0検証、現CUDA実機、7プロセス終了の原因と環境保全は未確認のまま。

次は通常武器・散弾・charge/武器変更・貫通を同じ選択/着弾へ接続する。nativeにはCharState._fire/_charge_fireのcaster/manager context、GPUには既存weapon Frameの量確定とlanding continuationが必要で、HitEvent後だけの付け替えではHP補正やpellet単位の再選択を再現できない。ADD owner・対象別DEF/敵debuff・元プロフィール全体も残る。証拠は`research/destructible-hit-shield-evidence/manifest.json`、checkpointは`research/portable-destructible-hit-shield-checkpoint.json`。
