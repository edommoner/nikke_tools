# 座標物理packetと常駐実行器

共通CLI `coordinate-physical` を追加した。単独の確率probeから進み、
GPU常駐Runtimeの実射撃・命中通知・対象HP更新へ共通着弾計算を接続した。
CUDA／Metalは同じSlang入口、効果定義、CPU比較器とfixtureを使う。
新入口はprivate profileであり、公開受付・全キャラ対応の認定ではない。

## 実証

`world_coordinate_physical_entry.slang` の23入力（実戦CPU17／拒否6）が
Apple M5 Metalで成功し、別processの保存結果監査からsealした。
17worldの52 logical pellet／100 expanded packetについて、既存の全戦闘decoderを通じて
ダメージ、HP、弾数、射撃時刻、gauge、各種fraction通知、counterとskill traceを照合し、
追加のpacket traceでowner・対象・kind・世代・時刻・量・extra・順序を照合した。
unused trace tailもゼロを要求し、全readbackのSHAを固定した。

対象は重なった部位、完全遮蔽、割込対象、2銃口×3散弾、破壊後の対象交代、
貫通、チャージ、部位命中閾値、回転矩形、クリティカル、精度buff、2射手、
不壊部位、同一射撃中の部位破壊、割込補正、スキルダメージ型武器変更である。
完全遮蔽の0damage本体packetと微小残差の違いは選択済みの共通数値規約を使い、
確率の丸め直しで吸収していない。最初の15入力は追加後も全entryのinput/native/output SHAを保持した。

旧本体81入力と旧座標・group97入力も現ソースで各1回Metal回帰検証・独立sealし、
旧入力・native指紋・全readback（339738624／508559360byte）のSHAが一致した。
生成CUDA/MSLはspread計算の関数抽出で変わったため、新しい生成指紋を監査後に登録した。
旧生成物の一致を主張せず、厳密normalizerにも例外を追加していない。

最終固定packageはCPU27件、control416件（Windows限定1skip）で失敗なし。
compact1663／full2986の全残存recordとbyte、保護7sourceの一致を検査した。
新GPU実行は初回15・追加23・旧97・旧81の4回、同claim再試行0。
Windows追加依頼0、現在のCUDA計算実証・CUDA compile cache改善は未完了。

## 接続と所有権

既存の武器Frame・scheduler・sampleDamageFactorsForReach・damageFromFactors・
Actorのland・fraction accumulator・counter collectorを使う。
射撃時に共通着弾計算をGPU内で実行し、確率と既に丸めたpacket templateを捕捉する。
全pelletの通知とfinishWeaponShotの後に、そのtemplateを元の順序で着弾させる。
通知の子buffや武器変更で同じ射撃の量を再取得しない。
部位名に対応するslotの世代は既存のcoordinateLandingGenerationで着弾時に解決する。
今回の物理traceの正例は世代1であり、物理弾の再出生世代まで認定した証拠ではない。

入力108648／出力1310720wordを維持し、127対象、5098cut、1024arc、128template、
4096packet traceの容量を減らしていない。scratchは900000–919840word。
AG_COMPACTの一部を使うため、group owner mask=0とgroupイベント定義なしをGPUで必須にし、
arena監査とbackendの入口・完全stride検査を追加した。旧group入口のbody-only guardは維持した。

着弾本体は既存coordinate_landing_v1.slangからinputのaddress spaceだけを機械的に変えて生成する。
算術・制御flowを再実装しておらず、CPU事前検査で元ソースとの全byte変換を要求する。
CPUで確率やpacketを計算してGPU入力へ詰める経路はない。

## 時間とcache

初回15入力はSlang生成約3.26秒、Metal pipeline約90.84秒、GPU約0.091秒だった。
同じshaderへの23入力は生成cacheとpipeline cacheを必須hitにして実行し、
Slang compiler呼出0、pipeline約0.0027秒、GPU約0.132秒、shared_gpu_execute約1.25秒。
入力数が異なるので、全体の同一workload速度比較ではない。
旧97／81も新しい生成指紋でpipeline作成が必要だった。
次のcache課題は通常経路の生成byteを維持するspread共通化と、必要な短いCUDA検証である。

終了済みraw3件を4KiB疎化し、計1896841216byteを回収した。
全byte・SHA・inodeを保持しており、raw削除や再GPU実行による作り直しはない。

## 監査と残り

controlが検出した武器phaseの未登録差分、旧compiler証明書のstale、transport監査差分は
それぞれ失敗logを保持した。歴史fixtureを上書きせず、exact source inverseと改変拒否を追加し、
旧81の新しい独立監査からcompiler証明書を作り直した。証明書だけではCUDA成功を認定しない。

次の優先項目は座標packet全体のフルチャージ参照量と部位ダメージ蓄積である。
現在の旧Frame式 `body_amount * pellets` は座標の追加packet量を含まない。
正本の `sum(all packet integer damage) / muzzles` の整数加算と最後のbinary64丸めを保持する必要がある。
追加CPU観測では貫通chargeの参照量8000／25%子damage2000／総damage10000を確認した。
現GPU式から得る参照量は2000であり、これはソースからの推定で、追加GPU失敗を実行観測した結果ではない。
literal caseと親通知の観測を `parent-quantity-gap.json` に保存した。
live core node、Geometryの6桁丸めcache key、手動aim／layer2、RNG、射撃groupとの同時使用、
原定義の混在も未完了。これらを未対応分類に残し、UIはCPU、全キャラ認証0／20gap／目標未達を維持する。

記録: `research/portable-coordinate-physical-gpu-checkpoint.json` と
`research/coordinate-physical-gpu-v1-evidence/`。
