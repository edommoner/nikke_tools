# 武器のfactor snapshotと盾へのpellet着弾

共通CLIのsealed `destructible-weapon-shield`を登録した。Apple M5のMetalで141入力（native98・拒否43）が一致し、保存readbackの独立sealも成功した。通常武器の22宣言契約を、既存の発射・時計・damage factors・typed着弾・counterへ接続した範囲の証拠である。ゲーム内の盾規則、全プロフィール、CUDA実機の認定ではない。

## 共通実行器への接続

`captureWeaponShot`の元の物理・normal/skill・core・charge・optimal contextで`sampleDamageFactorsForReach`を1度だけ呼ぶ。既存の9factorとHP盾modifierを射手別bankに保存し、`damageFromFactors`で実際に選択した種別の量だけを丸める。未使用のbody/HP量を先に計算してoverflowを起こさない。binary64・整数変換・damage式を別実装していない。

各pelletの通知前にliveなHP/hit盾をbinding順で再選択する。同じ発でHP→hit→bodyへ遷移してもfactor snapshotを維持する。HP量とhit creditは既存`dwLand`で消費し、counterを同じcollector/Frame continuationへ渡す。typedで受けたpelletは末尾のbody着弾から除外する。bodyへ進んだpelletは従来の着弾を使う。counter子のATK変更は次の発から反映する。

新HSI3 opt-inだけが武器providerを有効にする。旧HSI1/HSI2は既存処理のままである。武器のみの入力ではdescriptorのsource rowを`0xffffffff`とし、架空のskill定義やCPUの発射予定表を挿入しない。typed traceも武器source sentinel・mode flag・実係数を比較する。同期子のskill traceとは区別する。

CUDAとMetalは同じSlang・入力・native比較器・テストを使う。4既存shaderと2新shaderを変更し、Runtime全field/offset/stride138952byteを維持した。strict生成normalizer、保護CPU/compiler、binary64、typed quantity/Frame/target coreを変更していない。4ファイルの厳密inverseは旧fixtureの歴史source照合だけで使用し、新しい計算証拠の代用にしない。共通weapon/combatファイルは変更したため、通常147/scalar119のsourceが不変とは扱わない。通常492の追加実機回帰は今回行っていない。

## 検証結果

新22件はauto・散弾・charge・tap・武器変更（normal/skill formula両方）・core・RL・2銃口・slot4・2射手・world終了を含む。HP補正、HP/hit/body再選択、counter子、弾数、shot数、gaugeまでnativeと比較した。

|条件|確認結果|
|---|---|
|散弾HP→hit→body|最初の484でHP300、次の323でcredit1、その後body3230|
|同じ発のcounter ATK変更|最初の発484×3を保持、次発から1021×9|
|counter skillの追加着弾|武器323とskill484を別creditとして処理、body3553・gauge3.25|
|full charge|2902×2、時刻0.11666666666666665/0.44999999999999996|
|charge散弾/RL|968×6/4838×2、残HP4192/324|
|武器変更skill formula|1451,1451,2902,2902、元武器弾数998|
|2射手|body2904/3872、各4射、gauge2|

141件全体の独立sealはGPU0で全native/trace/readbackを再監査した。旧111は全input/native指紋とraw465567744byteを共通`readback-retain`で再hashし、全バイト一致した。保存実GPU10blockのfixtureでは、9正例へ各10改変と拒否結果1改変の計91改変を検出した。fixture10件だけで141全件の証明を代替していない。

最終不変package `328abf81064b73db4d481cee6c38ed4358284315d743d3756df4763e63bcb1cf`をfresh unpackし、CPU24群204検査（skip0、54.799秒）とnative98比較（6.943秒）に成功した。CPU限定reference22も成功し、22件すべてmodel gap/canonical positive0を維持する。final hostは未宣言座標policyのpacking拒否を加えているが、実証producerとの全141 input/native・155GPU source・両生成指紋は同一。

## 初回差分と時間

初回のGPU実行は完了したが、charge系3件の第2発時刻がGPU0.31666666666666665/native0.44999999999999996となり比較に失敗した。ダメージ・残数・弾数・gaugeは一致していた。fixtureをautoからchargeへ変更した際にpost-fire静的値0が残り、nativeのmetadata fallback0.215と食い違ったことが原因である。

5ケースの静的metadataを、既存`normalize_static_clock`とnative constructor metadataから補正した。実戦イベント時刻から逆算していないことを、simulate禁止のCPUテストで確認した。全141 native指紋とGPU sourceは不変。補正後の新package/claimで141件が成功し、rawが変化したのは上記3件のみだった。初回失敗・raw・claimは保持している。同一claimの再試行0、計2GPU実行（初回比較失敗1・補正成功1）。

成功時の実計算0.0691575秒、library作成0.001940秒、pipeline作成0.002857秒、GPU child実行・転送全体2.191777秒。初回はpipeline作成を含む全体68.966296秒であり、GPU計算自体が68秒かかったものではない。初期のCUDA/Metal生成2回はGPU0のgenerationで実施した。両実runとfinal generationはcache必須hit・追加Slang0で、finalはstrict生成指紋とreflectionを照合した。Metalのwarm結果をCUDAのcache/JIT改善とは扱わない。

終了済み旧111と初回失敗141のrawは、既存`sparsify-raw`で内容・長さ・SHA・inodeを保持したまま合計788332544byteの割当を回収した。raw/claim削除0。各runでinput62103172＋output591396864byteと1GiB予約を確認し、ケース数を減らしていない。

## 使用と残件

```sh
python scripts/nikke_gpu.py package --suite destructible-weapon-shield --out NEW_PACKAGE.zip
python scripts/nikke_gpu.py reference --suite destructible-weapon-shield --out NEW_REFERENCE.json
```

実行はfresh unpack先をcwdとする。旧111専用goldenは歴史sourceのまま保持し、現在の入口では141を使う。旧固定package・rawは保持する。

単一boss、宣言owner、明示policyのみ。座標・part・aim・貫通・ADD owner・対象ごとのDEF/debuff・武器着弾の吸血/蓄積混在・元プロフィール全体は未検証/受付拒否を維持する。次はこれらの混在と全カタログへの接続をnative契約で固定する。全266profile/245packing/base185/残20model gap/順位は、限定readiness metadata以外を保持した。全キャラ認定0、通常UIはCPU、最終目標は未達。

Windowsはstatus取得を試みたがremote hostを利用できず、新メッセージ・新実行依頼0。現CUDA実機/CUBIN O0/cache速度・7プロセス終了の原因は未確認。ユーザーは該当時刻の終了・再起動等を否定しゲーム/動画の可能性を挙げたが、因果の証拠ではないためcause unknown/環境保全falseを維持する。

証拠は`research/destructible-weapon-shield-gpu-evidence/manifest.json`、checkpointは`research/portable-destructible-weapon-shield-gpu-checkpoint.json`。
