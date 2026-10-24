<!-- shared-readback-current -->
元のレベル別投射物定義にはsealed `destructible-original-battle`（8入力/native8、Metal/独立seal済み）を追加した。5人×スキル1/2/3の明示levelsを共通native/入力経路へ渡し、既存caseはlevel10を維持する。レベル1/5/10とowner4、実burst通知・完了子を検証。元1定義の限定実証であり全プロフィール認定ではない。詳細は docs/portable-destructible-original-battle.md。

現在の型付き実戦入口はsealed `destructible-battle`（44入力/native31・拒否13、Metal/独立seal済み）。通常`projectile-chain-retention`の492入力もsealed経路を使える。詳細は docs/portable-destructible-counter-battle.md。以下は既存経路を含む履歴であり、最新の件数/source readinessはCLI `list`と固定packageを参照する。

保存出力の既存監査器を拡張した。`readback-index --case-words 1048576`は型付き実戦の4MiB/caseを明示し、省略時は従来の786432word。`readback-compare`はSHAで固定したindexの幅を使う。ファイル長から幅を推測しない。`readback-retain`は並べ替え/追加のあるcapture間で元ケースの保持を調べる。2つのcomparison.jsonのSHAを必須とし、成功comparison・一意なcase名・件数・全readback SHA・実caseごとのoutput SHAを読み直してから、元caseのinput/native/output指紋を照合する。

```sh
python scripts/nikke_gpu.py readback-retain \
  --reference-capture OLD_CAPTURE --reference-comparison-sha256 OLD_COMPARISON_SHA256 \
  --candidate-capture NEW_CAPTURE --candidate-comparison-sha256 NEW_COMPARISON_SHA256 \
  --case-words 1048576 --out NEW_RETENTION_REPORT.json
```

大文字の値は実path/SHAへ置き換える。元raw/comparisonと既存出力は上書きしない。不一致は診断JSONを保存してexit2、anchor不正やraw改変も停止する。GPU/build/compileは呼ばない。成功comparisonのflagだけを信頼した数値証明ではなく、結果は常に `calculation_verified=false` / `gpu_calls=0`。追加native oracleやGPU計算は既存のrun/audit/sealが担当する。
raw退避済みなら既存の`restore-raw`で元byteを復元してから監査し、GPU再実行で作り直さない。
<!-- /shared-readback-current -->

<!-- packet-preparation-current -->
Windows core46はCPU37/24state preflight成功後に全stage90秒timeout。Slang2回は合計.608秒、CPU batch33.685秒/native.033秒、NVRTC/GPU/readback未観測。外側2GiB/peak340,103,168B/post空/cleanup正常、inner after未完・missing7/unknown/保全false。保存7JSON11,614Bを全SHA検査、再実行/cache-check0。CLI再importと同一processの重複全件検証を除き、共有run_captureのgate前検証、CPU worker/GPU childの検証は維持。既存Journalへ準備/監視/各検証/CPU/inner jobを追加しstatusもstage対応。最終固定packet 9fb5ca76...でCPU37＋controller335(334成功/Win1skip)、改変/gate故障注入9＋CLI41成功。旧Metal46は保存replay＋独立sealで全golden/raw保持・追加GPU0。Windows改善実測は未実施、次はCPU-only準備計測、時間枠拡大やGPU再試行はしていない。source147/245SHA保持・残20model gap・typed target coreはbattle未接続。全キャラ0/UI CPU/目標未達。再利用停止の直接差分は追加したIMPL-STATUS文書だけで、ActorRegistry由来との説明を訂正した。詳細docs/portable-destructible-target-core.mdとcheckpoint。以下は履歴。
<!-- /packet-preparation-current -->

<!-- destructible-target-core-current -->
残20分類の未監査10件をsource監査し、20model gap/review0へ。移動/lock/range/対象数のconsumer欠如、敵弾薬のallied filterとnamed通知、nearbyの1対象fallbackをCLI consumer-auditへ追加し、source変更注入で停止。単なる受付追加を避け、projectile/HP盾/hit盾の共有Slang状態部品＋CPU ActorRegistry bridgeを実装。Metal46（宣言モデル24/拒否22）＋独立seal、CPU5群37成功、GPU.002794秒/cached pipeline.000774秒、CUDA生成29,512B。型/identity固定・世代/失効・HPとhitcredit・slot127選択を検証、保存5blockの故障注入付き。probe Runtime8B、production Runtime138952/147source/全266記録/245SHA/20code順位不変、旧Metal492＋実ラピ2を保持。battleの生成/着弾/破壊通知とall_projectiles/倍率は未接続で、状態coreを全機能対応と数えない。CUDA実機はこれから必要な46入力だけを短く検証する候補、full battle未検証/旧7終了unknown/保全falseを維持。通常UI CPU/全キャラ0/目標未達。詳細docs/portable-destructible-target-core.mdとresearch/portable-destructible-target-core-checkpoint.json。以下は履歴。
<!-- /destructible-target-core-current -->

<!-- projectile-chain-reference-current -->

<!-- projectile-chain-gpu-current -->
名前付きスキル終了weapon_hitを既存damage Frame完了後のevent51へ、buff型buff_stack_addを非数値carrier stat92へ接続。CUDA/MetalのSlang・入力・native比較を共通化、Runtime全field/offset/stride138952とbinary64/正本/normalizer不変。Metal32(native24/拒否8)、元ラピ：レッドフード全87定義3/30sの2入力、旧460込み492(native378/拒否114)が全件一致・各独立seal成功。旧460 raw1,447,034,880B/新32 raw100,663,296Bと全指紋保持。CPU41群281件skip0、95.366秒＋native事前38.076秒、GPU4.549秒。初回pipeline66.165秒、同source後続.002690秒、実run generation cache必須hit/Slang0。旧descriptor sentinelのhost変換失敗と旧負例のCPU失敗を保持して修正。raw削除0、疎化で1.107GB回収。静的245/266/base185/203/残20分類、旧244SHA全保持。Windows追加実行・観測0、ゲーム/動画利用可能性の申告は因果根拠でなく7終了unknown/保全false、現full-battle CUDA未検証。通常UI CPU/全キャラ認定0/目標未達。詳細docs/portable-projectile-chain-gpu.mdとresearch/portable-projectile-chain-gpu-checkpoint.json。次は残20分類のcanonical consumer調査とfull-burst混在契約。以下は履歴。
<!-- /projectile-chain-gpu-current -->

次のラピ：レッドフードの付着弾/weapon_hit/buff型stack carrierを正本26契約＋元87定義3/30sで固定。native handler終了通知はper-packetではなくcast終了で1回、0/負hit・元係数0・名前倍率0・nested child・buff/instantの違いを実測。new GPU受付は閉じたまま、既存146 shader/旧62 source-input-native/全266記録・244 SHA/23分類code順保持、Metal460証拠を再利用。分類はGPU候補2/native extension1/model gap10/review10。Windows保存v4の26files201729Bを回収し、共通CLI saved-core-report-auditで41指紋と両生成strict指紋・cache identityを照合。cold1.453s/warm file-only.085s、CUDA raw/CUBIN独立監査やfull battle CUDAではない。7欠落はinner before/afterに0・旧7と同一identity0、role/cause unknown・環境保持falseを維持。追加GPU/Slang/NVRTC/Windows観測0。次は共有Frameのhandler終了continuation、ordinary carrier projection、matching base weapon guardとMetal/旧460/元ラピ。全キャラ0/UI CPU/未達。詳細docs/portable-projectile-chain-reference.md、docs/portable-saved-core-report-audit.mdとcheckpoint。以下は履歴。
<!-- /projectile-chain-reference-current -->

<!-- damage-accum-battle-current -->
ダメージ蓄積4種を共有scalar coreから実carrier・吸血後boss着弾・所有付きevent50 continuationへ接続。Metal62(native52/拒否10)、旧398込み460(native354/拒否106)、元ドロシー73定義/トロニー74定義3/30sの4入力が一致し、各独立seal成功。旧398 raw1251999744Bと新62 raw195035136B、全Runtime field/stride138952を保持。回帰CPU39群268、実編成23検査成功。初回pipeline約65秒/計算.065秒、同一source回帰pipeline.003秒/計算4.511秒、実編成計算2.387秒。実run生成cache必須hit/Slang0。観測タグは復元し正本battle/projectile不変。静的244/266/base184/203/残23(gap10/review13)、旧242記録/SHA保持。途中の全GPU状態履歴ではなく全battle/trace/RNG＋最終pool/archiveの比較で、scalar詳細証拠は別。Windows追加GPU/compile0/保存export再依頼受付/7欠落unknown/環境保持false/現full-battle CUDA未検証。全キャラ0/UI CPU/目標未達。次は残23分類、軽量admission切り分け、aimed/容量mixed、保存CUDA回収。詳細docs/portable-damage-accum-battle.mdとcheckpoint。以下は履歴。
<!-- /damage-accum-battle-current -->

<!-- damage-accum-core-current -->
追記：RTX3070Tiの同じcore41(native34/拒否7)も共通CLIで数値一致との完了報告。cold NVRTC1回1.453秒、warm file-only hit/追加compile・GPU0。報告input/output SHAはMetal goldenと同一。内側欠落0/全stage欠落7・保全false/原因unknown。小さい保存結果の共有依頼cell6939応答待ち、追加実験なし。CUDA rawのMac独立再監査やbattle/全キャラ認定ではない。
ダメージ蓄積の共有scalar状態本体を実装し、共通CLI damage-accum-coreをsealed登録。Metal41(native状態契約34/拒否7)＋独立seal成功、量/率/順序/名前archive/放出整数/activeリンク一致。旧52戦闘契約とproduction143source/Runtime138952不変、battleのGPU受付は未接続。active連結リストで順序再探索を除去、head/tailは明示別領域。probeのみresident順序counter8B。最終package47a3e486.../2592files/6509450B、CPU14成功・故障注入付き保存raw6ブロック、生成cache必須hit/Slang0/CUDA46301B。full battleのCUDA実機/速度は未確認。初回reader/拒否header差等を保持、計2source各1Metal・readerのみのGPU再実行0。成功rawのゼロ領域126287872B回収・削除0。静的242/base182/残30/全キャラ0/UI CPU/未達。Windowsへ同一packet6.5MBを履歴なしbranchで配布。旧helperが過去34046files/1.17GBを走査して中断、CPU4のみ/完了未確認/GPU0、runnerはOpenProcess87でlive handleなし。個別helperを廃し全stage所有launcherを追加、Mac CPU21とsmoke324(Win1skip)成功、Windows外側Jobは単独/2GiB/57秒/終了空/既存欠落0を確認したが、CPU193中Mac専用endpointテスト1件で停止/GPU0。production guard不変でテストだけOS条件を修正、Mac324成功、修正版Winは未実施。過去7終了unknown/保全false。全5mode非衝突のheader260666/queue260668は候補のみ。次はこのcoreを実carrier・吸血後boss着弾・再入安全なevent50 continuationへ接続→52＋旧398＋実編成をMetal検証。詳細docs/portable-damage-accum-core.mdとcheckpoint。以下は履歴。
<!-- /damage-accum-core-current -->

<!-- damage-accum-reference-current -->
次の未対応ダメージ蓄積4種を共通CLI reference damage-accumの正本52契約へ固定。dealt→received走査、基礎/名前率の別順序和、None/明示0、ATK snapshot、吸血後boss収集、全pool更新後通知、owner非依存first-active/名前archive、splitのみ倍率/intを確認。fresh不変package9a6e80f1...で52契約9.827秒＋10検査10.367秒、旧family通常CLI31検査成功。未移植敵carrierのreader分類修正は旧Metal398保存replay＋独立sealで全指紋/143source/raw1251999744B保持、GPU追加0。新蓄積系のGPU受付は拒否のまま。全266profile/242SHA保持、静的242/base182/残30・contract6/gap10/review14。失敗/元refresh/散弾/adds対照を保持、ゼロ領域のみ1271791616B回収・raw削除0。Windows追加0/7終了unknown/保全false/現CUDA未確認。全キャラ0/UI CPU/未達。次はscalar carrier＋global名前archive、吸血後continuation/遅延event50を共通Slangへ接続しMetal実証。詳細docs/portable-damage-accum-reference.mdとcheckpoint。以下は履歴。
<!-- /damage-accum-reference-current -->

<!-- heal-charge-lifetime-current -->
回復poolのdown破棄を共通retirementへ接続。正本activeのpersistent/共有carrierは保持し、終了/消失recordは復活通知前に破棄する12契約がMetal398(native302/拒否96)・独立seal成功。旧386 input/native保持、385raw1211105280B完全一致、down1入力のみstale量/型2wordを意図して0へ修正し差分明示。標準デルタ79定義に防御型がなく蓄積0だった失敗を保持し、対照＋ノア入り81定義を各3/30s、4入力全定義/順序・Metal/独立seal成功。発動30sは生成7/take2/正の放出2、全1272量/順序/時計を先頭512raw＋SHA256連鎖/最終poolで一致。共通SHA圧縮器を再利用し旧history13/8192記録もMetal成功・全旧raw指紋保持。全Runtime/stride138952不変。CPU36群248/85.079秒・native28.240秒/GPU4.561秒、実編成GPU3.434秒。最終通常CLI31成功、compiler-full--heal-charge-lifetime-retentionの143source証明/固定packet771f4aa1...、CPU323中322/Win1skip、生成cache必須hit/Slang0/GPU0/両生成・reflection全byte保持。静的242/base182/残30と全266/242SHA保持。Windows追加0/現CUDA実機未確認/7終了unknown/保全false、全キャラ0/UI CPU/未達。次は容量境界・広い混在・未対応30分類・有用な短いCUDA。詳細docs/portable-heal-charge-lifetime.mdとcheckpoint。以下は履歴。
<!-- /heal-charge-lifetime-current -->

<!-- heal-charge-gpu-current -->
回復蓄積/容量boost/放出を共通Slangのscalar kind10・既存pool lifetime/同期continuationへ接続。Metal386(native290/拒否96)の29新契約が一致し、decoder-only修正後に保存raw replay/独立seal成功、GPU追加0。元CPU型比較・kind32 Actor-pool受付・指紋popの失敗を保持。旧349 input/native/output/raw1097859072B、全Runtime field/stride138952、旧241input SHA/全266profile保持。CPU33群231/78.087秒＋比較器故障8成功、GPU4.445秒、生成必須hit/Slang0。静的242/266/base182/203/残30、元デルタ79定義はpackingのみ。次は終了pool→down→復活の即時破棄（現sweep時機に不足の恐れ）、上限/回復分配mixed、元デルタ実編成。CUDA生成のみで実compiler/cache速度/計算未検証、Windows追加0/7終了unknown/保全false。全キャラ0/UI CPU/development_only/目標未達。詳細docs/portable-heal-charge-gpu.mdとcheckpoint。以下は履歴。
<!-- /heal-charge-gpu-current -->

<!-- compiler-certificate-current -->
共通CLI compiler-certificateで保存Metalをfresh childから独立再監査し、登録world suiteごとのcompiler-full--suite source-only証明書を発行。Metal349/139sourceから発行成功、固定compiler packet ca71d9c0.../2556filesを作成。共通CPU32群323中322成功/Windows1skip・4.941秒、seal5成功。required generation cache hit/Slang0/GPU0・CUDA/Metal/reflection全byte保持。独立seal済みmax-ammo3 suiteを通常sealed package可能にし、実編成2もCPU3群16/native2で経路確認。旧weapon/query監査の追加差分接続漏れをCPUで検出、厳密逆変換を接続し元token/hashと失敗を保持。旧compiler-full/commands/historical、raw CUDA/prelude/toolchain/claim/Jobと保存CUBIN専用identityは維持。GPU数値/正本/ABI/normalizer変更0、Windows追加0・現CUDA compile/計算未確認・全キャラ0/UI CPU/目標未達。次は回復蓄積29の共有GPU接続と有用な固定checkpointでの短いCUDA。詳細docs/portable-compiler-certificate.mdとcheckpoint。以下は履歴。
<!-- /compiler-certificate-current -->

<!-- heal-charge-reference-current -->
共通CLI reference --suite heal-chargeへ受けた回復量の蓄積/容量boost/放出の正本29契約を追加。scalar pool・ATK snapshot・満HP前clamp・state_end retention/cleanse/down discard・consume後の重複対象順・owner順を固定。fresh不変packageで5.963秒/関連4群27検査(skip0)成功、追加照会0・全native/trace/RNG保持。harmful指定ずれとowner順をCPUで検出、失敗保持・同時刻反例を残し別ケース追加。GPU受付拒否のまま、Slang/数値/正本変更0・GPU/Windows commands0。全266profile/241input SHA/拒否理由/Metal349 source保持、静的241/266/base181/203/残33・modelgap10/contractextension3/review20。保存CUDA2.068MB/833fn/241noinlineをCPU構造分析、既存compiler-full sourceに追加23/変更38（cache hit/性能証明ではない）。次は共有pool lifetime/放出continuation接続と最新Metal seal由来compiler package経路。全キャラ0/UI CPU/現CUDA未検証/7終了unknown/保全false/未達。詳細docs/portable-heal-charge-reference.mdとcheckpoint。以下は履歴。
<!-- /heal-charge-reference-current -->

<!-- max-ammo-scaling-gpu-current -->
max_ammo_countのcharge_dmg_pctを共通Slangへ接続。Metal349(native261/拒否88)＋元エミリア全73定義3/30sの2入力が一致、両独立seal成功。live本人容量/stack後倍率/整数丸め/mode memoを再利用、Runtime全layout/stride138952不変・旧321 input/native/raw1009778688B保持。CPU31群217/71.663秒・native20.732秒・GPU4.426秒、実編成CPU3群16/GPU1.817秒、実run生成cache必須hit/追加Slang0。初回generationの静的再帰はGPU0で検出し非再帰容量読取＋共通整数変換へ修正、import/テスト形状もGPU前に修正し失敗を保持。静的241/266/base181/203/残33・旧240記録/SHA保持。Windows追加0/現CUDA未検証/7終了unknown/保全false、全キャラ0/UI CPU/development_only/未達。次は残33分類consumer、late-query/mode遷移混在、CUDAcache。詳細docs/portable-max-ammo-scaling-gpu.mdとcheckpoint。以下は履歴。
<!-- /max-ammo-scaling-gpu-current -->

<!-- max-ammo-scaling-reference-current -->
共通CLI reference --suite max-ammo-scalingへ正本20契約を追加。live recipient容量、半端割合グループ0.5切上げ/flat偶数丸め、1発効果、mode memo/再装填/失効、再帰Noneを固定。外側1349/内側1170、観測追加照会0・全native/trace/RNG保持。fresh不変packageでreference1.796秒と5群37検査(skip0)成功。GPU受付は拒否のまま、Slang/正本/数値/normalizer変更0・GPU/Windows追加0。前回Metal321の全sourceと全266profile/240input SHA/拒否理由を保持。静的240/266/base180/203/残34、全キャラ0/UI CPU/目標未達。次は量源を共通lookupへ接続し、再帰/query scope/cacheを検証→Metal20＋旧321保持・元エミリア実編成。詳細docs/portable-max-ammo-scaling-reference.mdとcheckpoint。以下は履歴。
<!-- /max-ammo-scaling-reference-current -->

<!-- parent-fixed-current -->
親通知のdealt_fixed_damageを共有Slangへ接続。Metal321(native241/拒否80)＋独立seal成功、旧291 input/native/raw915406848B保持、Runtime全layout/stride138952不変。23新契約は散弾/複数muzzle/端数0packet/通知欠如/再入/吸血/大整数を含む。CPU29群203/67.906秒、native19.685秒、GPU4.451秒、生成cache必須hit/実run追加Slang0。初回package欠落はGPU0、初回Metal差分はfixture待機0→正本.215の入力修正で解消し失敗を保持、GPUsourceと全正本期待値不変。consumer-auditで実consumer欠如を明示分類、静的240/266/base180/203/残34。次はmax_ammo_countのlive対象容量scaling（source確認のみ/契約0）と広い親context/現CUDA。Windows追加0/7終了unknown/環境保全false、全キャラ0/UI CPU/development_only/未達。詳細docs/portable-parent-fixed.md、checkpointとevidence。以下は履歴。
<!-- /parent-fixed-current -->

<!-- full-burst-query-current -->
保留pending2の0hit query-only・現在参照数の読取後に固定countを使用・HP換算を共有Slangへ接続。専用diagnostic19でbuff/ref/HP41戻り値の順・bit値・時刻が正本一致、通常とのbank外59456320B保持。Metal291(native218/拒否73)と両独立seal成功、旧272 input/nativeと855638016B保持・Runtime全layout/stride138952不変。巨大係数0hit5・現在1024でも固定1hit2・両HP方式/部位/子HPを含む新19。初回HP除外2差分は不変parent maskをHP基準へ渡して修正、初回診断のarray/listとcache無効時初期化も修正。保存replay GPU0で初期化漏れを検出、失敗/raw/claim保持・新source別package実証。通常291 input/native同一、他289raw909115392B保持。CPU27群190(skip0)66.850秒/native18.697秒/GPU4.416秒、診断CPU3群15/GPU0.053秒、実run生成cache必須hit/追加Slang0。分類追記後19検査成功、静的240/266/base180/203/残35・旧266全記録と240SHA保持。次は優先35分類の実consumer（projectile_dmg_pct等）、低marker周期移動/zero係数/対象混在/広い実編成/現CUDA。Windows追加0/7終了unknown/保全false、全キャラ0/UI CPU/development_only/未達。詳細docs/portable-full-burst-query.mdとcheckpoint。以下は履歴。
<!-- /full-burst-query-current -->

<!-- full-burst-capacity-current -->
full-burst待機列512境界と着弾後の次回mode2残存を実証。既存出力word3＋旧形式優先512entryで新形式件数/owner/name/hitsを公開し、正本の実controller終了列と照合。Metal272(native199/旧拒否72/実行時容量超過1)と独立seal成功、旧267 input/nativeと全839909376B保持・Runtime全layout/stride138952不変。親1＋子511で514packetとdamage654278、着弾後追加1項目が次回へ残る。513はnative515packetで有限/GPU status64、入力差はBUDGET511→512の1word。summaryは履歴のみ省略し全処理/総packet数/公開battle状態/RNG/最終列を比較、個別GPU514traceではない。CPU25群180(skip0)63.867秒/上限90秒/native17.885秒/GPU4.410秒、生成cache必須hit/実行時Slang0。次は0hit query-only・HP basis照会順/保留組合せ・周期snapshot移動・現CUDA/全キャラ。Windows追加0/7終了unknown/保全false、全キャラ0/UI CPU/development_only/未達。詳細docs/portable-full-burst-capacity.mdとcheckpoint。以下は履歴。
<!-- /full-burst-capacity-current -->

<!-- full-burst-queue-current -->
フルバースト着弾のlive再入とtyped receipt tail所有情報を共通Slangへ修正。子・孫を同回生成、旧bonus追加分だけ次回へ残し、既存出力bankに旧batchを一時保存して着弾前に枠解放。tailの本体8/部位2/周期・迎撃snapshot38wordとslot参照を移動。Metal267(native195/拒否72)と独立seal成功、旧260 input/nativeと全817889280B保持・Runtime全layout/stride138952不変。CPU24群174(skip0)52.754秒/native15.774秒/GPU4.399秒、生成cache必須hit/実行時Slang0。追加7はlive/孫/初期混在/旧tail/部位/迎撃/周期共存。周期低markerの移動は未実証、512枠境界・着弾後mode2の直接観測・0hit query-only/HP basis順・現CUDA/全キャラは残件。Windows追加0、利用者の終了/再起動操作なし回答を記録、ゲーム/動画原因は未確定・7終了unknown/保全false。全キャラ0/UI CPU/development_only/未達。詳細docs/portable-full-burst-queue.mdとcheckpoint。以下は履歴。
<!-- /full-burst-queue-current -->

<!-- full-burst-landing-gpu-current -->
フルバースト開始後の着弾を共有Slang private mode2へ接続。FBL1を非weapon MODE17..19へ格納し既存pending配列/Frame10/typed receiptを再利用、旧pending counter意味・通常queue prefix/tailを保持。Metal258(native186/拒否72)と独立seal、元イレグ全76定義3/30sの実編成2と独立sealが成功。cast1→live2読取の固定1回、同frame親子、0/負/13hit等を合成で検証、元13hit branchは未発火。旧232 input/native/output・729808896B保持、Runtime全layout/stride138952/数値/normalizer/正本不変。初回の倍率除外1件は生成MSLで消えた一時状態代入を不変row mask読取へ修正、失敗/raw/claim保持・別package成功、同一入力の他257 raw808452096B保持。元counterは宣言済single_body＋binding1の入力route/policyだけbodyへ正規化し、原定義と他世界拒否を保持。CPU23群169(skip0)47.733秒/native13.616秒/GPU4.340秒、実編成CPU2群10/GPU2.978秒、生成cache必須hit/実行時Slang0。静的240/266・base180/203・残35分類、旧239記録/SHA保持。次はlive再入queue/capacity、0hit query-onlyとHP basis照会順、RNG/部位/他実編成/現CUDA。新queue生成中の再入tailは現時点で正本と未一致、全キャラ0/UI CPU/未達。Windows操作0/7終了unknown/保全false。詳細docs/portable-full-burst-landing-gpu.mdとcheckpoint。以下は履歴。
<!-- /full-burst-landing-gpu-current -->

<!-- full-burst-landing-reference-current -->
次の未対応land_in_full_burstを共通CLI referenceへ合成13＋元イレグBoom&Shock3/30sの2契約として固定。cast条件/count固定、landingでlive参照1→2を実読取した後に固定1へ戻す順、後続cast buff除外、通常は次frame/保留はfullburst同frame、旧B3bonus先行・親子3150/1260/1323/1386を検証。合成handler24/親通知36/全packet40、元30sは6hit branchのhandler2/通知6、13hit原分岐未発火（合成で13hit検証）。fixed package reference15＋CPU5群27(skip0)/旧230native成功。GPU source133/input/native230不変により旧Metal証拠を保持、新build/Slang/GPU/Windows0。全266記録/239SHA/27拒否/37code順位保持、2分類をnative_contract_extensionへ。GPU受付は拒否のまま。設計は二つの正本queue順・旧pending counter意味・cast暫定係数の照会・signed count・除外scopeと通常receipt再利用を明記。次はzero係数/HP/RNG/capacity契約と共有別mode接続→Metal。現CUDA/全カタログ未完、全キャラ0/UI CPU/未達。詳細docs/portable-full-burst-landing-reference.mdとcheckpoint。以下は履歴。
<!-- /full-burst-landing-reference-current -->

<!-- named-enemy-removal-current -->
名前付き敵へのremove_named_buffを既存の共有解除本体へ接続。target scopeは名前route、default/globalはtarget未消費・descriptor未追加を区別。正本16契約48dispatch/33rank/33recipient/504所持、通知時の残存所属と全battle/trace/RNG/照会回数を確認。Metal230(native171/拒否59)と独立seal成功、旧207 input/native/output・651165696B保持。別の実編成2入力は元アスカWILLE全80定義3/30sがMetal＋独立seal一致、解除0/1回・state_end0/1回を観測。GPU差分は受付1式、Runtime/stride138952/数値/normalizer/正本不変。CPU20群156(skip0)35.914秒/native12.550秒/GPU4.337秒、実編成CPU2群7/GPU2.934秒、生成cache必須hit/実行時Slang0。旧テストの既対応random1拒否を容量外6へ訂正、CPU失敗保持/GPU起動0。静的239/266・base179/203・残37分類、旧238記録/SHA保持。周期/空の解除対象名/再入callback/seq/ref/scaling/budget/広い実編成/現CUDAは残件。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/目標未達。詳細docs/portable-named-enemy-removal.mdとcheckpoint。以下は履歴。
<!-- /named-enemy-removal-current -->

<!-- named-enemy-gpu-current -->
名前付き敵の対象選択を共有Slangのprivate入口へ接続。名前operandを非weapon MODE24..27へタグ付き格納し、既存の敵集合/所持状態/照会scope/世代を再利用。Metal207(native155/拒否52)・診断23の全69対象マスク・独立seal成功。旧175のinput/native/outputと550502400Bを保持、診断領域外72257444B同一。Runtime/stride138952/数値/normalizer/正本不変。初回の追加ダメージ4件status64は着弾の定義番号受け渡し漏れを修正、失敗/raw/claim保持・別packageで実証。CPU17群135(skip0)28.256秒/native12.033秒/GPU4.317秒、生成cache必須hit/実行時Slang0。静的238/266・base178/203・残39分類、旧237記録/SHA保持。名前付き敵remove_named_buffは未受付、seq/ref/scaling/budget/passive/実編成/現CUDA/全カタログは残件。Windows操作0/7終了unknown/保全false、全キャラ0/UI CPU/目標未達。詳細docs/portable-named-enemy-gpu.mdとcheckpoint。以下は履歴。
<!-- /named-enemy-gpu-current -->

<!-- named-enemy-reference-current -->
`reference --suite named-enemy --out <new.json>` はGPU/packing禁止の正本23契約。`named-enemy-reference` packageはそのCPU検査と旧175入力の保持を行う開発suiteで、新しい名前付き敵のGPU suiteではない。固定packageでreference23/CPU49/旧175nativeが成功、GPU0。対象解決/フォールバック/残件はdocs/portable-named-enemy-reference.md。
<!-- /named-enemy-reference-current -->

<!-- generation-boundary-current -->
`generation-boundary` は既存175入力で生成器/cache/CLIの11群116検査を行う開発suite。`run --cpu-only` と `generation --develop` で検証した。生成器を独立moduleへ抽出し、転送だけの編集でもcache必須hit/Slang0を維持する。旧cacheを新keyへ流用せず、旧receiptの監査を保持する。実測・限界はdocs/portable-generation-boundary.md。新GPU/Windows実行は0。
<!-- /generation-boundary-current -->

<!-- random-cleanse-gpu-current -->
private `random-cleanse-retention`175(native132/拒否43)がMetal保存replay＋独立seal成功。`package --suite random-cleanse-retention --develop` で固定する。`random-cleanse`単独は50(native38/拒否12)の開発suiteで別golden未登録。正本referenceは random-cleanse18 / random-cleanse-mixed12 / random-cleanse-budget6 / random-cleanse-rosters2。元175のowner不足による比較失敗はsource/input/native同一の新packageへreplayして修復、GPU再実行なし。詳しい実証範囲・残件はdocs/portable-random-cleanse-gpu.md。
<!-- /random-cleanse-gpu-current -->

<!-- random-cleanse-reference-current -->
`reference --suite random-cleanse --out <new.json>` はGPU/packing禁止の正本18契約。ランダム有害所持者の本人包含・解除不能の候補資格・抽選順と各人の所属解除を検査する。GPU接続前の契約であり受付は拒否のまま。詳細docs/portable-random-cleanse-reference.md、次はlive候補変化と共通実行器への接続。
<!-- /random-cleanse-reference-current -->

<!-- burst1-ally-gpu-current -->
has/no_burst1_allyをprivate actor-field受付へ接続。GPU変更はguard4行＋flag1行、既存basicConditions/数値/状態更新/Runtime/stride138952/normalizer/正本/旧CUDA/Windows wrapperは不変。正本12契約36判定で自己除外・戦闘不能者のstage保持・live override/失効を固定し、全battle/trace/照会回数保持。不正name/引数/NaN/combat/world8も拒否。Metal125(native94/拒否31)と独立seal成功、前回拒否のアニス全83定義3/30秒2入力も同じinput/native期待値で一致（正本auto calc2/77）。旧95の298844160Bと旧合成8の25165824Bを全byte保持、旧10 input/native fingerprintも不変、失敗/raw/claim保持。CPU12群108(skip0)11.322秒/native9.956秒/GPU4.333秒、生成事前検査→cache必須hit/追加Slang0、監査GPU0。静的236/266・base176/203・42分類は全profileSHA/拒否理由とも不変。既知runtime blockerはこの12契約/2実編成範囲で解消しroutingへscoped証拠を記録、全キャラ0/UI CPU/development_only/全目標未達。caster他位置/広いstage・復活混在/新private全1612/全catalog/現CUDAが残件。Windows操作0/原因unknown/保全false。詳細docs/portable-burst1-ally-admission.mdとresearch/portable-burst1-ally-gpu-checkpoint.json。以下は履歴。
<!-- /burst1-ally-gpu-current -->

<!-- skill-weapon-metadata-current -->
auto_damage武器欄は正本handlerが読まずactor武器を使うことをsource/実計算で固定。既知種別かつ基礎武器と一致するnormal_attack注記だけを共通hostで限定受付し、元定義を保持。不一致6はmodel gap、override実装とは数えない。合成14契約42calcとモード入退出、アニス全83定義3/30sで2/77calcを観測。新Metal10は合成8一致・実編成2がstatus64、suite未成功/未sealを維持。別不変packageへ既存診断flagだけ有効化し1入力を観測、stage8000/定義index1/스타 폴 2/no_burst1_ally[32,0,0,0]を特定。basicConditionsには有るがactorFieldsDefinitionValidでB1味方条件が未接続。通常source/registry復元済み、失敗/raw/claim保持。新CPU5群37(skip0)6.781秒/native1.806秒と旧9群81成功。全通常GPU/数値/normalizer/正本/旧CUDA/Windows wrapper不変のため旧95(native72/拒否23)を共通replay＋独立sealで再利用し298844160B保持・GPU再実行0。静的236/266・base176/203・42分類、旧235SHA保持だがアニスのGPU受付は未完。実行時blockerは静的分類と分離し次経路を記録。次はB1味方条件の自己除外/生死/stage override/失効の専用native契約→共通shape guard→実編成再検証。Windows操作0/現CUDA未検証/原因unknown/保全false、全キャラ0/UI CPU/development_only/全目標未達。詳細docs/portable-skill-weapon-metadata.mdとresearch/portable-skill-weapon-checkpoint.json。以下は履歴。
<!-- /skill-weapon-metadata-current -->

<!-- below-def-gpu-current -->
最終防御力比較selector14をCUDA/Metal共通private入口へ接続。解決済みresidentの割合→付与元flat、strict未満、down除外、文字列lazy/list即時を正本13契約39解決/234読取で固定。Metal95(native72/拒否23)と独立seal成功、旧74 input30902400B/output232783872B全byte保持。Runtime/stride138952/数値/normalizer/正本/Windows wrapper不変。GPU4.294秒、生成cache必須hit/追加Slang0。初回未定義シンボルはSlangで停止・GPU前失敗/claim保持し、既存alliedFlagsへ修正、生成だけの事前検査後に別packageで検証。共通CLI generation --developを追加し実packageでcache hit/Slang0/GPU0、sourceとpaired receiptを確認するが計算/封印生成基準認定false。既存sealed照合は維持。最終CPU9群81(skip0)7.320秒/native8.112秒、CLIテスト環境漏れは単一process検査で検出し復元、失敗保持。最終CPU packageとsealed replay差はテスト復元だけ、source/input/native同一。静的235/266・base175/203・43分類、旧235SHA保持。アニス：スターは別のauto_damage weapon_typeが残り、実編成GPU未検証。新private全1612/現CUDA/全カタログが残件。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/development_only/全目標未達。次はauto_damage武器指定の正本契約と防御lazy/参照/復活混在。詳細docs/portable-below-def-recipient.mdとresearch/portable-below-def-gpu-checkpoint.json。以下は履歴。
<!-- /below-def-gpu-current -->

<!-- leftmost-gpu-current -->
属性×武器種の左端生存者selector24をprivate CUDA/Metal共通Slangへ接続。生存filter後に人数制限、0〜5人、buff/instant、mask/flag/lazy不正拒否。Metal74(native59/拒否15)と独立seal成功、トリナ全76/78定義3編成3/30秒の6実編成を含む。新13契約/原正本22対象解決/実射2768、容量内traceと省略数を既存比較器で照合。旧47出力147849216B＋新21出力66060288B全byte保持。CPU8群41(skip0)4.838秒/native7.917秒/GPU4.338秒、生成cache hit/追加Slang0。初回21のstorage decode不足と初回74の拒否domain誤分類は失敗/raw/claim保持しreplayで修復、GPUretry0。後者は固定origin/adapterhash/15行だけの明示metadata migration、59正例とsource/input期待値は不変。旧入口生成CUDA/MSL全byte同一、Runtime/stride138952/数値/normalizer/正本/Windows wrapper不変。静的235/266・base175/203・44分類、旧234SHA/残分類順保持。旧1612の新private全再実行は未実施、全キャラ0/UI CPU/development_only/全目標未達。Windows操作0/現CUDA未検証/原因unknown/保全false。次はselector復活/list混在・新入口全保持と残るconsumer/対象分類。詳細docs/portable-leftmost-recipient.mdとresearch/portable-leftmost-gpu-checkpoint.json。以下は履歴。
<!-- /leftmost-gpu-current -->

<!-- cache-preflight-current -->
共通CLIへfile-only cache-probeとcache必須時の先行確認を追加。CUDAの両cache必須とMetal/CUDAの生成cache必須は、単体/native計算/実行claim前にmissを拒否。Slang/NVRTC/driver/子processを禁止したsnapshotで、hit後も既存検査・実行子の再確認は省略しない。旧schema1のkey/receipt/保存JSON全byte互換、未知claim保持、空/破損成果物をfail closed。初回Metalのlate生成missはhost consumer hash変更によるもの。旧失敗/claimを保持しSlangのみ2回2.692秒で刷新、CUDA/MSL/両reflection全byteを旧実証と一致確認しkey規則は不変。新版Metal47と独立seal成功、旧全entries/input19627204B/output147849216B保持。生成snapshot0.311秒。最終15群150検査14.002秒、Mac CPU-only smoke30群302(Windows専用1skip)成功。smoke初回の歴史compiler cert/current一致という誤前提を、保存基準一致＋現行流用拒否へ分離し旧証明は不変。テスト追加版へreplay＋独立sealしGPU追加0。GPU本体/数値/normalizer/Windowswrapper不変、既存1612は従前のbody証拠で新host全再実行なし。raw全byte/SHA/path/inode保持で3619946496B割当回収/削除0。skill-creator標準検査とrepo/installed Skill同期済み。Windows追加操作0、実cache-probe/新Job smoke/現CUDAは未検証、7終了unknown/保全false、全キャラ0/UI CPU/全目標未達。次は短い実Windows file-only確認/Job smokeの条件整理と、優先未対応consumerを続ける。詳細docs/portable-cache-preflight.mdとresearch/portable-cache-preflight-checkpoint.json。以下は履歴。
<!-- /cache-preflight-current -->

<!-- duration-scaling-gpu-current -->
持続時間のstack_count倍率をCUDA/Metal共通Slangのprivate入口へ接続。Metal1612(native1276/拒否336)と独立seal成功、通常47/native40・旧入口拒否1・診断47も独立監査。31既存＋passive/source/0優先/stack操作/コロン名9の40契約、全80定義レイブル通常/シールド破壊3/30sを含み物理49/38/455/444射を照合。診断160expiry/154refはbinary64生bit一致・省略0、領域外147076160B保持。比較器のstorage decode/array型失敗はraw/claim保持、診断は共通CLI replayで修復しGPU再実行0。未発火のinstant型刺激はhandler0を確認後buff型へ訂正しhandler3・raw時間更新を実測。適用元定義・stack増加前参照・乗算後加算・None/-1のみ無限、値倍率独立、passive再計算、既存stack操作の元duration更新を保持。REFERENCE4番目のタグunionのみ、Runtime/stride/容量/数値/normalizer不変。旧1565の4923064320Bと新47の147849216Bを全byte保持。CPU95群500検査175.582秒/事前93.154秒/GPU10.954秒/最終27検査12.517秒。cache必須hit/追加Slang0、親native1192再利用/84fresh/拒否336、sealはfresh。静的234/266・base174/203・47分類、旧233記録/32拒否/code順保持。入力出力5744084740B+14GiB確認、raw内容保持で6898712576B割当回収/削除0。Windows操作0/7終了unknown/保全false、現CUDA未検証、private/development_only/全キャラ0/UI CPU/未達。次は空/免疫/lazy recipientや復活・世代混在と、残るconsumer/全カタログ実戦を優先。詳細docs/portable-duration-scaling-gpu.mdとresearch/portable-duration-scaling-gpu-checkpoint.json。以下は履歴。
<!-- /duration-scaling-gpu-current -->

<!-- duration-scaling-reference-current -->
重複数に比例する持続時間を共通CLI reference duration-scalingへ31契約（合成27＋レイブル全80定義3/30sの通常/シールド破壊4）で固定。正本expiry93回/ref_count87回、通常入力0回と破壊刺激のstealth/stun各1回を区別。参照なし0・0ゲージ優先・整数化・caster単位・再付与の増加前読取・同名aliasの適用元定義・None/-1の読取省略・負の有限時間・値倍率との独立を確認。元battle/trace/全get_buffs/sample/expiry/ref読取の順と結果を保持、8故障拒否。不変packageのreference31とCPU5群26検査14.241秒成功。2分類をnative_contract_extensionへ移し、全266記録/233SHA/33拒否/49code順保持。GPU125sourceと既存32input/native同一によりMetal1565証拠を再利用し、今回GPU追加0。GPU受付は拒否のまま。正本/数値/normalizer変更0、Windows追加操作0/7終了unknown/保全false、全キャラ0/UI CPU/未達。次はstatic参照descriptorと適用前expiryを共有Slangへ接続し、passive/stack操作/召喚体の混在とMetal保持を検証。詳細docs/portable-duration-scaling-reference.mdとresearch/portable-duration-scaling-reference-checkpoint.json。以下は履歴。
<!-- /duration-scaling-reference-current -->

<!-- not-core-cli-current -->
現行の非コア検証は `not-core`32（native27/拒否5）、`not-core-legacy-reject`1、`not-core-retention`1565（native1236/拒否329）。共通Slangのprivate入口でMetal独立seal済み、development_onlyを維持。`package --suite not-core --develop` で固定し、`unpack`後は必ず展開先をcwdとして、そのpackageの `scripts/nikke_gpu.py run` を実行する。旧adapterには相対importがあるため、別checkoutをcwdにしない。保存結果の `seal` はpackage自身のcwd/importsを使う。実例と限界はdocs/portable-not-core-gpu.md。全体のCPU500検査約176秒/正本事前約90秒に対しGPU計算約11秒。以下は履歴。
<!-- /not-core-cli-current -->

<!-- not-core-reference-current -->
未対応not_coreを共通CLI referenceへ27契約（合成25＋冬ギロチン全79定義の実編成3/30s）で固定。正本条件評価160回/成立95回/instant39回、実ゲージhandler3/34回を観測。元battle/trace/全get_buffs/全sample保持、7種故障拒否。不変packageでreference27とCPU7群49検査成功。独立したeffect/caster累積キー、probとの独立、重複条件/descriptor、条件短絡とbudget後の評価、ペレット→銃口平均、発射snapshot、子通知の空contextと親復元、passive評価を明示。分類1件を正本接続待ちへ移動し、静的266記録/232SHA/34拒否/50code順序は保持。GPU123sourceと既存17 input/native指紋は同一のため、既存Metal1533の証拠を再利用。今回GPU build/execute/Windows0。GPUのnot_core受付は未開放・対応追加0、全キャラ0/UI CPU/未達。次は通知core_fracと独立状態・条件/budget順を共有Slangへ接続し、Metal合成/実編成/保持を検証。詳細[非コア条件の正本契約](portable-not-core-reference.md)とresearch/portable-not-core-reference-checkpoint.json。以下は履歴。
<!-- /not-core-reference-current -->

<!-- partial-query-current -->
短押し＋lazy/direct数値参照の17正本契約を共通CLIへ追加し、GPUの3実差分を修正：開始/待機中の余分な辞書照会、回復倍率の全辞書参照、mode終了の無効化不足。Metal1533(native1209/拒否324)と独立seal成功。診断2の0.2〜0.8秒の全missも一致し、診断bank外6258560B保持。新17の全4465抽選・順序・最終MTを検証。旧1516のinput/native全保持、1512raw全同一、4入力はcache hit回数1wordずつ（16B）だけ減少し正本回復呼出3/2/3/3回×2に一致。他4768923632Bと新17単独/全体rawを保持。CPU95群500検査176.060秒/正本事前88.790秒/GPU11.064秒/最終5群20検査11.253秒。全体v1の故障注入はGPU前停止を保持し、正しいlayout層へ投影して同じ故障を検査。入力/正本/ソース基準1533は修正前後同一。静的全266記録・232SHA・34拒否・50分類不変。数値primitive/normalizer/Runtime/stride/容量不変。生成cache必須hit・追加Slang0。Windows操作0/原因unknown/保全false/現CUDA未検証。development_only/全キャラ0/UI CPU/未達。次は追加consumer/制御混在と全カタログ実編成。詳細[短押しと数値参照](portable-partial-query-gpu.md)とresearch/portable-partial-query-checkpoint.json。以下は履歴。
<!-- /partial-query-current -->

<!-- partial-charge-current -->
短押し・非フルチャージをCUDA/Metal共通Slangの開発専用入口へ接続。Metal1516(native1192/拒否324)とGPU禁止の独立seal成功。追加74入力はpartial45・動的14・クロスト全77定義4・signed基準11。符号付きbaseから回数補正を引いてから最小1へclampし、signed32両端・負の小数補正・期限切れを固定。CPU95群500検査175.999秒、正本事前85.512秒、GPU11.219秒、最終12群93検査20.700秒。旧1505の全raw4734320640Bとnativeを保持し、入力変更は0/負base2件の静的header/tag/flagだけ。静的232/266・base172/203・50分類、旧231入力SHAと34拒否保持。数値primitive/normalizer/Runtime/stride/容量不変。生成cache必須hit・追加Slang0。Windows操作0/原因unknown/保全false/現CUDA未検証。public event40/tap2は未開放、development_only/全キャラ0/UI CPU/未達。次はtapとlazy/random数値readerの照会時点・混在制御の正本契約。詳細[短押しGPU接続](portable-partial-charge-gpu.md)とresearch/portable-partial-charge-checkpoint.json。以下は履歴。
<!-- /partial-charge-current -->

<!-- nonfull-charge-reference-current -->
共通CLI reference nonfull-chargeへ23の正本契約を追加。短押しpartial/full、周期的full、発射単位counter、重複/raw alias/軽減/budget、散弾2銃口、reload、通知callbackでauto武器へ変更・復帰を固定。全battle/trace/semantic read回数保持、7種故障拒否、fresh packageのreference23とCPU7群47検査成功。未対応4分類を正本確認済みnative_contract_extensionへ移動し、全266profile・231入力SHA・35拒否・54分類code順序を保持。GPU122sourceは既存1442と同一、追加GPU/Windows0。tapはstatic層で未受付、GPUはchargeならfull通知するためevent40だけ開放しない。次はpartial chargeの状態・tap制御・damage/core/ゲージsnapshotを共有実装し、混在/全定義クロストとMetalで検証。GPU対応追加0・全キャラ0/UI CPU/development_only/未達。詳細[非フルチャージの正本契約](portable-nonfull-charge-reference.md)とresearch/portable-nonfull-charge-checkpoint.json。以下は履歴。
<!-- /nonfull-charge-reference-current -->

<!-- squad-stage-current -->
段階別squad_burst_cast:1/2/3を共有Slangへ接続。Metal1442(native1144/拒否298)と独立seal成功。16native契約＋14拒否、全81定義のレッドフード7実編成で自動B3/明示A/live/期限切れを検証。旧1405の4419747840Bと追加37の個別結果を全保持。既存論理6/callback20/実編成12も変更後Metal一致・全raw保持。CPU95群500検査176.226秒、native事前80.025秒、GPU10.771秒。数値/normalizer/容量/Runtime不変。静的231/266・base171/203・54分類、旧230入力SHAと35拒否保持。Windows追加0/原因unknown/保全false/現CUDA実機未検証。development_only/全キャラ0/UI CPU/未達。詳細[段階別通知](portable-squad-stage.md)とresearch/portable-squad-stage-checkpoint.json。次は未対応consumer確認と対象/制御契約の拡張。以下は履歴。
<!-- /squad-stage-current -->

<!-- aimed-real-world-current -->
全定義の実編成3profile×部位/interrupt×3/30s=12をprivate明示受付へ接続。Mermaidの2入力で名前付き状態/解除の論理対象不整合を検出し、共通Slang2ファイル4箇所でpart/private6→本体の敵効果scopeへ修正。正本/期待値不変、修正版Metal12と論理6/直接private28receipt成功・独立seal。正本6624射/11870returned packet/3532private着弾/9102RNG、実GPU比較は状態/武器時計/burst/全pool会計/ordered RNG/最終MT。射撃trace容量770・省略1354保持、全packet/全skill列traceではない。旧1405の全4419747840Bとcallback20の62914560Bを全byte保持・独立seal。CPU回帰95群498検査175.984秒＋最終7群71検査。CLIは単体検査→native→GPUへ変更し故障注入11成功、実callback実行でも順序確認。default266の旧230packing入力SHA/拒否理由を全保持（base170）。sparsifyはSHA/path/inode保持で6941179904B回収・削除0。Windows追加0/原因unknown/保全false、現CUDA実行未確認。development_only/全キャラ0/UI CPU/未達。次は対象worldのカタログ拡張と未対応consumer/制御。詳細docs/portable-aimed-real-worlds.mdとcheckpoint。以下は履歴。
<!-- /aimed-real-world-current -->

<!-- aimed-callback-current -->
GPU本体変更なしでbody/partカウンター子のATK/吸血を共通20ケースへ追加。正本104射/440returned packet/20完了をCPU固定し、追加観測器のsemantic read/trace保持。Metal20の全battle/HP/pool/counter/named/trace/会計と直接private184行一致・独立seal。440行GPU個別traceではない。CPU4群17検査18.356秒＋最終5群21検査18.508秒、GPU0.05524秒、生成cache hit/追加Slang0。通常122/診断123 sourceが旧sealed1405/診断12と全同一なので旧1405保持証拠を再利用し全体再実行0。初期テストのcanonical通知無効化とcharge時刻0の誤認はGPU前に修正、数値期待値/正本変更なし。Windows追加0/原因unknown/保全false、現CUDA未検証。development_only/全キャラ0/UI CPU/未達。次は全定義実編成のtarget worldと広いcallback。詳細docs/portable-aimed-callbacks.mdとcheckpoint。以下は履歴。
<!-- /aimed-callback-current -->

<!-- aimed-area-current -->
共有Slangへ狙った部位／interruptの貫通・爆発body→target配信、対象重複除外・発射時倍率snapshotを接続。Metal全1405(native1121/拒否284)＋診断12/直接private74receipt成功。正本60射/172returned packetはCPU固定（全172のGPU個別traceではない）。旧1393 input/native保持、1387raw全byte一致、混在6はNQR cache hit数各3減だけ。他のbyteと診断bank外37551360B保持。診断容量16→128を排他bankで拡張、Runtime/stride/数値/normalizer不変。CPU95群498検査175.857秒。full v1のCPU故障注入失敗は保持、上位層逆投影の検査修正後v2成功・GPU同条件retry0。Windows追加0/原因unknown/保全false、現CUDA未検証。development_only/全キャラ0/UI CPU/未達。次は混在callbackと全定義実編成のtarget world。詳細docs/portable-aimed-area.mdとcheckpoint。以下は履歴です。
<!-- /aimed-area-current -->

<!-- aimed-packets-current -->
正本の物理split/hit_countと全returned HitEventを別観測する共通reference aimed-packets16契約を追加（86射/178packet/88private着弾）。旧24native/trace/receiptsとsemantic read回数保持。共有Slang1ファイルで狙ったpart/interruptのno-coreと直接対象倍率を接続。Metal全1393(native1109/拒否284)＋倍率診断8/34receiptが一致・独立seal。CPU95群498検査175.5653秒＋最終6群28検査、GPU10.5420秒。旧1385 input/native全保持、1361raw全byte一致、24件はcore memo72wordだけで旧4,356,832,992B保持。診断bank外25,148,928Bも全一致。共通CLI aimed-factor-compareでsource遷移/全raw/hashをGPU0で再監査。数値ライブラリ/normalizer/Runtime/容量変更0。Windows0/原因unknown/保全false、全キャラ0/UI CPU/未達。次はarea8の本体+対象packet/aimed重複除外を共有continuationへ接続。36private着弾を含むので診断容量16へケースを縮めず排他領域を拡張。development_only維持。詳細docs/portable-aimed-packets.mdと対応checkpoint。以下は履歴です。
<!-- /aimed-packets-current -->

<!-- interrupt-aim-gpu-current -->
private kind6の直接着弾を共有actor pool/吸血/通知へ接続。Metal通常1385(native1101/拒否284)＋診断24/98receiptが一致・独立seal。CPU95群498検査175.6899秒、GPU10.7289秒、normal122source/診断123。旧1355のinput/native全保持、1354raw全byte一致、負例1だけcharge制御不整合の拒否位置変更657wordを固定し両方64。混在6の18,874,368B、診断bank外75,446,784Bも全保持。normalizer/数値/Runtime/既存容量変更0。通常v1の零率通知差・診断v2の初期化順序失敗raw/claim保持。sparsifyはbyte/SHA/path/inode保持で6,898,974,720Bのzero割当回収・削除0。Windows0/原因unknown/保全false、静的230/266・62分類、全キャラ0/UI CPU/未達。24例はcore0/intercept追加なしの直接packet範囲。次は狙った対象のno-core/intercept倍率、複数packet native観測、貫通/爆発の本体+対象/aimed重複除外。development_onlyを維持し広いpromotionをしない。詳細docs/portable-interrupt-aim-gpu.mdと対応checkpoint。以下は履歴です。
<!-- /interrupt-aim-gpu-current -->

<!-- interrupt-aim-reference-current -->
共通CLI reference interrupt-aimへprivate物理着弾24契約を追加。正本hit_target前後98receipt、通常合計外会計・吸血・dead同フレーム・generation1→2・charge・散弾/2銃口・gateを固定。canonical ActorKind2はPROJECTILE、private6にhit creditを付けない。context内だけのCPU橋で通常CPU/default typed橋/GPU受付は不変。native/全trace/semantic read回数保持、偽receipt/二重/非物理/世代/容量/6故障を拒否。fresh不変packageのreference24とCPU23群140検査成功、batch28.4414秒。GPU/Windows0・共通GPU source/数値/normalizer変更0。全キャラ0/UI CPU/未達。次は共有landing continuationへprivate種別を接続し、Metal full battle/receiptと保持回帰後に受付。詳細docs/portable-interrupt-aim-reference.mdと対応checkpoint。以下は履歴です。
<!-- /interrupt-aim-reference-current -->

<!-- mixed-query-current -->
照準＋数値辞書＋回復共有＋部位の混在6ケースを共通CLI mixed-query/mixed-query-diagnosticへ追加。正本観測の計算・trace・semantic read回数保持、8種の故障検出。Metal通常6＋診断6が全項目/全抽選順序/最終MT/照準/回復順一致し、独立seal成功。診断bank外18,628,416byte全保持。CPU13/16検査成功、GPU各約0.050秒。通常122sourceは既存1355と完全同一で全体再実行0、通常Slang0・診断両生成2。GPU本体/数値/normalizer変更0。Windows追加操作0、ユーザーは終了/再起動操作なし・ゲーム/動画の可能性を回答、因果はunknown/保全falseのまま。全キャラ0/UI CPU/未達、次はprivate物理interrupt橋のCPU契約と接続。詳細docs/portable-mixed-query.mdと対応checkpoint。以下は履歴です。
<!-- /mixed-query-current -->

<!-- scratch-layout-current -->
旧scratch配置に部位スキル/割り込み集計/回復診断との重複を発見し、最大容量を保って分離。出力786432word/Runtime138952B/数値cache64/照準cache256/部位receipt2048は不変。NQRはpadding二bank、headerと履歴は割り込み集計後へ移動。排他的な二つの診断entryだけは領域共有し、同時macroを実Slangで拒否。共通CLI layout-check/layout-compareと読み書き幅・容量縮小・計算改変の故障検査を追加。Metal最大容量probe8＋実window1＋同122sourceの1355(native1071/拒否284)が全成功・独立fresh seal。CPU全92群487検査と最終小CLI10検査成功。GPU11.3868秒、normalizer/正本/算術不変。旧1302件は全byte一致、移動53件のcache/履歴と移動外4,260,934,400Bも保持。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/未達。次は混在consumer契約とprivate kind6の物理interrupt橋。18CPUケースが終了する試作は/tmp/nikke-private-interrupt-runtime-draft-v1.pyに保持し受付未開放。詳細docs/portable-scratch-layout.mdと対応checkpoint。以下は履歴です。
<!-- /scratch-layout-current -->

<!-- native-query-observation-current -->
共通Slangへログsnapshot・初回/変化HP同期・期限切れログのlazy確定を接続。ログ有効/無効、満HP初回回復、終了通知から同効果再発動を含む25入力が同121sourceのMetalで全一致し独立seal成功。リリー30秒は4550抽選の全semantic順序・最終MT・原文battle/全射撃履歴まで一致。正本6編成の元指紋保持、CPU/数値/normalizer不変。読み取り専用census/windowをCLIへ追加し、診断領域以外の全byte保持を確認。旧1330＋新25の1355回帰も同121sourceでMetal全一致・独立fresh seal、CPU91群482検査成功。旧1326件のraw全4,171,235,328Bと新25件は全byte一致、既記録のselector25修正4件だけ各2B変化、旧1330のnative指紋は全保持。GPU11.14889秒/生成cache必須hit/追加Slang0。初回は旧散弾のno-op故障注入でGPU前停止し、監査層へprojectして確実に変異させるテストへ修正。Windows追加操作0/7終了原因unknown/保全false、全キャラ認定0/UI CPU/ゴール未達。詳細docs/portable-native-query-observation.mdと対応checkpoint。以下は履歴です。
<!-- /native-query-observation-current -->

<!-- ordered-history-current -->
共通履歴を先頭128生record＋全semantic順序SHA-256へ拡張。追加bank64word(781792..781856)、stride/Runtime field不変。時刻はhash対象外でbattle/trace比較を保持。単体ordered-history13入力がMetal成功・独立seal、実goldenで通常CLIへ登録し通常CPU6成功。resident専用generation cacheの不適合指定はCPU/capture/claim前に拒否するCLI検査を追加。実編成でselector25のeager確定（旧4入力は1word21→5のみ、旧SHAへ全復元）と率0のlanding数値照会を修正、post-hit CPU契約を追加。119sourceのbattle19は18一致、リリー30秒のみ正本4550/GPU4542抽選で8不足・205発目からdamage差分。全6native/trace元指紋保持、失敗raw/claim保持、最終CPU55＋reference6成功。次は3.85..4.0秒のGPU辞書照会owner/target/epoch/hitを直接観測し欠落を特定。旧1330＋新19の1349suiteは登録のみで、差分解消後に一括検証。旧rawの全bytes/SHA/path/inodeを保って割当1.899GB回収、削除0。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/ゴール未達。詳細docs/portable-ordered-history.mdと対応checkpoint。以下は履歴です。
<!-- /ordered-history-current -->

<!-- native-numeric-query-current -->
後段ATK＋allies_randomのdirect読取と数値辞書cacheを共有Slangへ接続。meta+5の厳密tag/64context/8736word(773056..781792)、Runtime field追加0。初回命中/charge開始と既存mutationの破棄、数値reader入口、終了時の敵ATK→Actor数値読取順を保持。Metal native5＋拒否7が全項目・抽選pool/order/MT位置/最終全state一致し独立fresh seal、実golden保存・development_only維持。v1-v4の停止/失敗raw/claimは保持。CPU/数値/normalizer不変、厳密11source差分で旧監査層と算術/exit/boundary故障検査を維持。リリー実30秒の4550抽選は128履歴上限の拡張待ちで未検証。次は履歴方式とcharge実射撃/混在readerを検証し、実6＋旧1330を同じsourceで全保持検証。旧1330は変更前sourceの歴史的証拠で今回sourceでは未実行、広いpromotion保留。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/ゴール未達。詳細docs/portable-native-numeric-query.mdと対応checkpoint。以下は履歴です。
<!-- /native-numeric-query-current -->

<!-- late-attack-random-current -->
全定義3編成を共通CLI state-focus-rostersへ追加しMetal6入力を検証。5一致、リリー30秒は122差分で失敗・raw/claim保持/再実行0。原因は後段ATKのdirect random読取とdictionary cache境界：正本4550抽選に対しGPU4。CPU契約5をreference late-attack-randomへ追加し、各248照会/158hit・mapped1対late90抽選・5故障拒否・元native/trace/照会数保持を確認。分類器はこの組合せをreader/cache/history拡張へ修正。GPU source117は前回と同一、生成cache必須hit/Slang0、Apple M5 GPU2.745459秒。新suiteは未seal/development_onlyで、sealed範囲1330を維持。次は共有dictionary-query入口/後段direct読取/128超履歴を接続して実6と旧1330を保持検証。Windows操作0/原因unknown/保全false、全キャラ0/UI CPU/ゴール未達。詳細docs/portable-late-attack-random.mdと対応checkpoint。以下は履歴です。
<!-- /late-attack-random-current -->

<!-- state-focus-current -->
共有cover/camera条件39/30、focus_fire存在stat91、フレーム照準とtyped部位着弾/通知を接続。Metal新66(native54/拒否12)＋旧1264(native1000/拒否264)が同117sourceで成功・各独立seal。計1330、旧全entriesとraw3,976,200,192Bを全byte保持。条件30＋照準24、初期数値cacheとlive markerの違い・更新破棄・部位同フレーム破壊を照合。新Runtime field0/stride138952/CUDA定数48B、専用bank770976..773056/cache256。旧CPU455成功/GPU10.696秒/生成cache必須hit/Slang0。静的230/266・base170/203・62分類はGPU認定でない。追加stat reader/cache invalidation、typed interrupt橋、revival/random混在、実編成と広いpromotion、現CUDA実行が残件。旧golden/本体compiler証明は保留、suiteはdevelopment_only。失敗v1-v3/claim保持・正本CPU/数値/normalizer不変。Windows操作0/7終了unknown/保全false、全キャラ0/UI CPU/ゴール未達。詳細docs/portable-state-focus.mdと対応checkpoint。次は新規packing3編成の全定義3/30秒を優先し、readerとtyped interrupt橋を検証。以下は履歴です。
<!-- /state-focus-current -->

<!-- ally-random-gpu-current -->
味方random selector19/25を既存allied MT・遅延cache・順序付きrecipientへ接続。Metal新30(native20/拒否10)＋旧1234(native980/拒否254)が同じ116sourceで成功・各独立seal。旧全entriesとraw3,881,828,352Bを全byte保持、計1264/正例1000。旧保持CPU449成功、生成cache必須hit/追加Slang0、GPU10.3185秒。CPU契約18は不変、追加GPU契約は人数0と発動上限。新しいRuntime field0/stride138952、正本CPU/数値/MT/normalizer不変。味方だけでは復活を有効化しない。cover_breakログとcover_revive受付も既存処理へ接続。混在revive/random、random buff list、debuff型、cover/camera条件とfocus_fire marker/aim、現sourceのCUDA実行は未検証。実証goldenは保存したがsuiteはdevelopment_only、旧golden/本体compiler証明の一括promotionは保留。Windows操作0/7終了unknown/保全false、全キャラ認定0/UI CPU/ゴール未達。次は混在契約と共有cover/camera/marker接続をまとめ、次のsource batchで保持検証。詳細docs/portable-ally-random-gpu.mdとresearch/portable-ally-random-gpu-checkpoint.json。以下は履歴です。
<!-- /ally-random-gpu-current -->

<!-- state-prerequisites-current -->
次のまとめ移植に向け、共通CLI referenceへstate-predicates30＋ally-random18のCPU契約を追加。不変packageで48成功、CPU-only20群124検査24.533秒。生存者のみのcover判定（本人含む）、破壊/復旧/死亡、casterカメラ・有限/無限・同時刻の順序、独立した味方global RNGと敵RNG、空/1人/全員選択の消費、source欄を跨ぐ遅延対象cache、即時修復後の候補変化を固定。100条件/204cover/326runtime照会、50sample/50resolve/52選択。native全項目/trace/元照会回数/乱数stateを保持。focus_fireは条件だけでなくmarker＋aim consumerが未接続。not_coreは期待値累積でbool反転不可。静的227/266・68分類は不変、契約拡張6/consumer研究4/gap3/review55。GPU本体/受付/golden/正本CPU/数値/normalizer不変、GPU実行/claim0、既存Metal1234を新規証明へ加算しない。Windows操作0/原因unknown/保全false、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-state-prerequisites.mdと対応checkpoint。次は共有状態/marker/aim/味方recipientを同一batchで接続しMetal新例＋旧1234を検証。以下は履歴です。
<!-- /state-prerequisites-current -->

<!-- undying-predicate-current -->
不屈条件self_undyingを既存共有liveMarkerへ接続。値/名前でなく生存statを照会、Runtime追加field0/stride138952、明示発動/private worldのみ。CPU22＋原文全定義マキマ3（致死刺激あり）契約、Metal主28(native22/拒否6)＋実3＋旧1203が同一sourceで一致・独立seal、計1234(native980/拒否254)。旧全entries/raw3784310784Bを全byte保持。CPU事前67.249秒＋回帰75群433検査141.520秒、GPU10.966637秒、後続生成cache必須hit/Slang0。親再利用871/fresh84/拒否248、独立sealはfresh。full116/commands117 certificate14検査と正式CPU111検査成功、3suiteを通常経路へ昇格。2件のGPU前停止は保存し、監査区切りと古い拒否fixtureだけを修正。実履歴155/1398/1398、省略0、旧省略は残る。静的227/266・base167/203・68分類はGPU認定でない。接続済み条件の旧診断は未実装候補でなく文脈確認へ。rawゼロ領域回収で全byte/SHA/path/inodeを保持し、今回7360544768Bの割当を回収、削除0。正本CPU/数値/normalizer不変、Windows追加操作0/原因unknown/保全false、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-undying-predicate.mdと対応checkpoint。次は共有状態の未対応条件をまとめて契約/保持検証。以下は履歴です。
<!-- /undying-predicate-current -->

<!-- accuracy-retention-current -->
命中率条件の全保持検証完了。新34と旧1169が同一共有sourceでMetal一致・独立seal、合計1203(native955/拒否248)。旧全entriesとraw3677356032Bを全byte保持。CPU事前66.177秒＋回帰72群423検査129.281秒、GPU10.694823秒、生成cache必須hit/Slang0、親再利用843/fresh84/拒否242、独立監査はfresh。full116/commands117 certificate14検査と正式package CPU102成功、3suiteを通常経路へ昇格。共通CLIにMac sparsify-rawを追加し実APFS9検査成功、4rawの内容/長さ/path/inode/SHAを維持して7543914496Bのゼロ領域を回収、raw/claims削除0。歴史artifact metadataも不変、4.17GB入力出力＋14GiB予備を実空きで確認してからGPU実行。静的226/266・base166/203・69分類はGPU認定ではない。Windows追加操作0/原因unknown/保全false、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-accuracy-predicate-gpu.md、docs/portable-sparse-raw.mdと対応checkpoint。次は正本consumerのある未対応効果の契約と共有実装を継続。以下は履歴です。
<!-- /accuracy-retention-current -->

<!-- accuracy-predicate-gpu-current -->
命中率条件を既存共有stat読取/binary64比較へ接続。通常/actor-field受付を同一のstat whitelist＋有限値guardへ統一。Metal主32(native26/拒否6)＋原文全定義実モダニア2が同一到達sourceで成功し独立seal。CPU各102検査、GPU0.043992秒/3.645644秒、後者生成cache必須hit。物理履歴112/0省略と2048/295省略を照合。初回受付失敗・診断・GPU前監査失敗を保持し、入力/native期待値は不変。静的226/266・base166/203・69分類はGPU認定ではない。旧1169は変更前sourceの証拠で、今回sourceの全保持検証は容量不足で未開始（input約0.49GB＋output3.68GB＋予備14GiB必要）。development_only維持、全体promotion/証明更新は保留。raw/claims削除0、正本CPU/数値/normalizer不変、Windows追加操作0/原因unknown/保全false、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-accuracy-predicate-gpu.mdとresearch/portable-accuracy-predicate-gpu-checkpoint.json。以下は履歴です。
<!-- /accuracy-predicate-gpu-current -->

<!-- accuracy-predicate-reference-current -->
命中率条件の正本CPU26契約＋実モダニア全定義2入力を共通CLI referenceへ登録。不変packageで28契約成功、CPU-only14群99検査成功。実30秒は8判定が全成立、値は14%×5→5.44%×3で固定bool化不可。CPU物理履歴2343件はGPU容量超過のため後続比較で省略を明示する。差等被ダメ分配の2分類はpinned仕様未定の証拠を固定してmodel gapへ移動、均等分配への別名化なし。静的225/266・70分類は不変、candidate1/consumer研究4/gap3/review62。GPU受付は拒否継続、新GPU実行/claim0、正本CPU/GPU/数値/normalizer/golden不変。Metal既存1169範囲維持、Windows操作0/終了原因unknown/保全false、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-accuracy-predicate-reference.mdとresearch/portable-accuracy-predicate-reference-checkpoint.json。次は容量予算を確保して共有条件受付・Metal短例・旧1169保持へ進む。以下は履歴です。
<!-- /accuracy-predicate-reference-current -->

<!-- parent-oracles-current -->
共通CLIに同一親プロセスの事前CPU結果の再利用を実装。現在のmanual-swap/実編成/保持suiteで自動利用し、既存比較器のGPU decode/全項目比較/拒否/全raw/SHA/生成code/輸送監査は維持。package/capture/PID/thread/引数/値の同一性を検査、一度だけ消費してclose、値を子や保存cacheへ渡さない。独立audit/seal/replayとCPU-onlyは再利用なし。旧Metal1137のCPU読取比較で818正例を再利用/84再計算/235拒否、親比較68.414秒→11.833秒（56.581秒削減）、全項目/全entries/元保存JSON一致。preflight64.800秒とCPU回帰/独立監査は残す。新旧両比較を含む測定peakRSS6140461056Bは増分/Windowsメモリ証明ではない。正式30入力を新通常経路でMetal一致（再利用23/拒否7）、生成cache追加Slang0/GPU0.054426秒、CPU13群90成功、その保存結果の独立fresh auditも成功。故障注入13を含む関連97検査成功。GPU本体/golden/正本CPU/数値/normalizer変更0、既存Metal1169の範囲を維持。Windows追加操作0/7終了unknown/preservationfalse停止、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-parent-oracles.mdとresearch/portable-parent-oracles-checkpoint.json。次はこのCLIを使って未対応制御/効果の共通GPU接続を継続。以下は履歴です。
<!-- /parent-oracles-current -->

<!-- manual-swap-gpu-current -->
weapon_mode_swapを共通reloadへ接続。owner別5bit＋tagを既存headerへ格納し、GPUで条件付きfull_reload候補を判定、既存beginReload/完了dispatcherへ委譲。満弾開始・charge中断・0/負reload・条件失効・budget到達後の再試行・再突入を保持。Metal主30(native23/拒否7)＋自然な全定義実2＋旧1137が同116sourceで一致・独立seal。計1169(native927/拒否242)、旧全entriesとraw3576692736Bを全byte保持。実30秒は約16.483333秒に移行し原文値40が8dispatch、物理履歴112/1425、省略0。cover sequenceとのCPU1契約はhost拒否継続。Runtime追加field0/stride138952/CUDA定数48B、正本CPU/既存CUDA/数値/normalizer不変。初回kind取り違えの失敗raw/claim保持、input/nativeを変えずkind2修正v2で成功。full116/commands117 certificate14検査、最終sealed CPU78検査とreference26契約成功。旧1137はCPU preflight64.373秒＋回帰67群389検査117.387秒（worker117.703秒）＋親比較68.299秒、GPU10.748800秒。後続実2/旧1137は生成cache必須Slang0。静的225/266・base165/203・70分類はGPU認定ではない。Windows追加操作0/7終了unknown/preservationfalse停止、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-manual-swap-gpu.mdとresearch/portable-manual-swap-gpu-checkpoint.json。次は未対応制御/効果の契約と、独立sealを維持する親CPU事前照合結果の再利用設計。以下は履歴です。
<!-- /manual-swap-gpu-current -->

<!-- manual-swap-reference-current -->
weapon_mode_swapの正本経路を確認し、共通CLI referenceへmanual-swap24＋全定義manual-swap-rosters2契約を追加。full_reload候補の条件・原文順・budget非再検査、満弾開始、charge中断、再突入、0/負reload、cover前の判定を固定。24契約は34開始/17完了/主対象139射、全native/trace/get_buffs呼出数を保持。実シンデレラ30秒で約16.483333秒のready1回＋値40の原文効果8dispatchを正本で観測、3秒は未発火対照。trueフラグがprivate正規化で落ちる問題を、接続までreason=control/fields=weapon_mode_swapの明示拒否へ修正（false/省略保持）。consumer確認済み26契約のprogram blocker候補として分類、GPU支持はfalse。fresh packageのCLI26契約＋既存46入力/29native指紋一致、9群61検査14.104秒と別32検査成功。単独起動の依存初期化失敗は保存し、fresh child検査で修正確認。GPU本体/受付/golden/Runtime/数値/正本CPU/既存CUDA/normalizer変更0、GPU実行0/claimなし。既存Metal1137の範囲を維持し新GPU認定は加算しない。Windows追加操作0/7終了unknown/preservationfalse停止、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-manual-swap-reference.mdとresearch/portable-manual-swap-reference-checkpoint.json。次は静的ownerフラグと条件付きreload判定を共通GPUへ接続し、実編成と旧1137の保持をMetal検証。以下は履歴です。
<!-- /manual-swap-reference-current -->

<!-- ammo-equivalent-gpu-current -->
squad_ammo_consume_asを共通Slang kind37へ接続。リテラルtruncate後N-1通知を同期continuationで処理し、実弾の追加消費なし。Metal主46(native29/拒否17)＋原文効果の明示charge1＋全定義の実2＋旧1088を独立seal、計1137(native902/拒否235)。旧全entriesとraw3422552064Bを全byte保持。実2は既定MGで対象dispatch0の対照で、自然なSR進入／手動reloadは未対応。原文効果1は2射80通知・装弾8・6000/12000一致。静的geometry再コンパイルとactor core/range受付を修正。診断stage重複をClaudeのsourceレビューで特定し、pool8000へ分離・再発検査追加、一時実験コード除去、失敗raw/claims保持。旧1088はCPU preflight62.609秒＋回帰64群376検査102.090秒、GPU10.670990秒。full116/commands117 certificate14成功、Runtime追加field0/stride138952/CUDA定数48B、数値/正本CPU/既存CUDA/normalizer不変。静的225/266・base165/203・70分類はGPU認定ではない。実30秒物理履歴32省略と旧省略を維持。Windows追加操作0・7終了unknown/preservationfalse停止、全キャラ認定0/UI CPU/全目標未達。詳細docs/portable-ammo-equivalent-gpu.mdとresearch/portable-ammo-equivalent-gpu-checkpoint.json。次は正本consumerのある未対応制御経路を優先。以下は履歴です。
<!-- /ammo-equivalent-gpu-current -->

<!-- ammo-equivalent-reference-current -->
共通CLI `reference --suite ammo-equivalent` に正本CPU25契約を追加。fresh不変packageで71射・4426通知・64dispatch成功、旧散弾／共通reference負例／分類器を含む4群30検査成功（10.442秒）。小数truncate、N-1追加通知、実弾の追加消費なし、auto/charge順序、全体counter、4096、無限弾薬、max_trigger再帰、periodic登録とtickを固定。wrapperをunwrapして正本valを読み、追加buff照会0・native/trace全保持。シンデレラ：クリスタルウェーブのconsumerを確認、通常self/literalだけをGPU実装候補へ分類。静的224/266・base164/203・71分類不変、candidate1/review65。GPU本体／受付／golden／数値変更0・GPU実行0・claimなし。Windows追加操作0、7終了unknown/preservationfalse停止。詳細docs/portable-ammo-equivalent-reference.mdとresearch/portable-ammo-equivalent-reference-checkpoint.json。次は同期continuationへkind37を接続し、Metal短例・実定義・旧1088保持。全キャラ認定0／UI CPU／ゴール未達。以下は履歴です。
<!-- /ammo-equivalent-reference-current -->

<!-- pellet-shot-gpu-current -->
1射内pellet_hit_in_shot:NをCUDA／Metal共通Slangへ接続。原文別ID・signed32、0/負値の静的loweringと復元、captured pellet×muzzles、auto/warmupの通知順・重複descriptorを保持。CPU21契約、Metal36(native21/拒否15)＋メイドプリバティ全定義3秒/30秒2＋旧1050が同116sourceで一致・独立seal。旧全entriesとraw3303014400Bを全byte保持し、計1088(native870/拒否218)。CPU回帰61群362検査88.802秒、GPU10.649943秒、成功3検証の追加Slang0。full116/commands117 certificate14検査成功、最終sealed package CPU62検査・claimなし。実30秒で閾値通知43回・正reload speed照会4133回、最大20.88%、native指紋保持。物理履歴85/770・省略0、旧既知省略は維持。v1はfixtureのmin_cycle10混入でcharge1射差分、原失敗保持・正本入力0.1秒へ修正した別v2で成功、GPU source再変更なし。静的224/266・base164/203・71分類はGPU認定ではない。Windows追加操作0・7終了unknown/preservationfalse停止、全キャラ認定0/UI CPU/ゴール未達。詳細docs/portable-pellet-shot-gpu.mdとresearch/portable-pellet-shot-gpu-checkpoint.json。次は正本consumer確認済みsquad_ammo_consume_asのCPU契約。以下は履歴です。
<!-- /pellet-shot-gpu-current -->

<!-- pellet-shot-reference-current -->
共通CLI `reference --suite pellet-shot` に正本CPU20契約を追加。fresh不変packageで59射・62通知が成功し、旧失HP／共通reference負例を含む3群18検査成功。raw閾値aliasの区別、数値→原文順、重複descriptorの複数発動、captured pellet×muzzles、auto/warmupのみの通知、gauge/attack前の順序を固定。観測器の追加buff照会0・native/trace全保持。GPU本体／受付／golden／数値／ABI変更0・GPU実行0で、未実装のCPU準備段階です。Windowsのゲーム／動画併用は原因証拠ではなく、7終了unknown・環境保全false・追加検証停止を維持。詳細docs/portable-pellet-shot-reference.mdとresearch/portable-pellet-shot-reference-checkpoint.json。次は原文別ID＋共通Slang通知、Metal短例・実編成・旧1050保持。全キャラ認定0／UI CPU／ゴール未達。以下は履歴です。
<!-- /pellet-shot-reference-current -->

<!-- lost-hp-attack-current -->
失HP ATKを既存共有Slang scalarへ接続。GPUはreference受付1箇所だけで、数値・Runtime・正本CPU/既存CUDA/normalizerは不変。CPU21＋復活3契約、Metal主29(native21/拒否8)＋復活3＋ギロチン全定義3秒/30秒2、旧1016が同115sourceで一致・独立seal。旧全entriesとraw3196059648Bを全byte保持、計1050(native847/拒否203)。CPU回帰58群350検査が79.062秒、GPU10.416秒、生成cache追加Slang0。full115/commands116 certificate14検査成功、commands両生成の原byteも旧版と同一（NVRTC実hit証明ではない）。ギロチン30秒で正scalar714回、最小HP50.1209%・最大倍率47.8839を観測しnative指紋保持。物理履歴30秒32省略・旧省略は残す。静的223/266・base163/203・72分類はGPU認定ではない。Windows追加実行0、7終了unknown/preservationfalse停止、UI CPU/全キャラ認定0/ゴール未達。詳細docs/portable-lost-hp-attack.mdとresearch/portable-lost-hp-attack-checkpoint.json。次はpellet_hit_in_shot:5の正本契約。以下は履歴です。
<!-- /lost-hp-attack-current -->

<!-- skill-hp-basis-current -->
最大HP由来のスキルATK加算／置換を共通Slangへ接続。damage_basis_specsを共有し、GPUで最大HPを取得、演算順序・親子snapshot・部位・吸血を保持。HP37(native26/拒否11)＋保護回復4＋メイデン／キロ全定義3秒/30秒4、旧8群971を同115sourceでMetal一致・独立seal。旧971の全entriesとraw3054501888Bを全byte保持、計1016(native821/拒否195)。CPU回帰340成功、full115/commands116 certificate14検査成功。共通CLIで8群を1バッチへ統合し、初回60秒CPU停止を保持、当該suiteだけ90秒で66.540秒成功。GPU10.387秒、生成cache追加Slang0、GPU枠は不変。保留B3のHP換算欠落はホスト／GPUで拒否。キロ30秒の物理履歴32省略と旧省略を明示。静的222/266・base162/203・73分類はGPU認定ではない。Windows追加native/compile/GPU0、7終了unknown/preservationfalseの停止を維持。UI CPU/全キャラ認定0/ゴール未達。詳細docs/portable-skill-hp-basis.mdとresearch/portable-skill-hp-basis-checkpoint.json。次はatk_pct+lost_hp_pct等の正本consumerを先に契約化。以下は履歴です。
<!-- /skill-hp-basis-current -->

<!-- mode-capacity-current -->
武器変更max_ammo_scaling_refを共通Slangへ接続。None/0、ゲージ→召喚体→stackの優先順位、整数倍率、進入/再進入/再装填snapshot、弾薬即時操作、容量0と無限弾薬、散弾/2銃口/charge/sentinelのCPU29契約を固定。sealed mode-capacity32(native26/拒否6)＋追加instant3＋E.H.全定義3秒/30秒2入力がMetal一致・独立seal。旧849/部位63/実4/味方通知16/ルピー2も同sourceで全一致・独立seal、計971、旧934の全entriesとraw2938109952Bを全byte保持。CPU回帰330成功。Runtime追加field0/stride138952、CUDA定数48B、full114/commands115 certificate更新。sealのCWD混在を修正し、異なる2checkoutの実子プロセス検査4件を通過、保存32のCPU監査結果がpackage自身からのsealと完全一致。初回query guard3失敗はGPU前/claimなしで保持し、元fixtureを換えず有限deltaを接続。E.H.履歴152/1388・省略0、30秒で容量1/モード1packetの実行を正本でも観測。静的220/266・base160/203・75分類はGPU認定ではない。Windows追加GPU/native/compile0・既存7終了unknown/環境保全falseで停止維持。通常UI CPU/全キャラ認定0/ゴール未達。詳細docs/portable-mode-capacity.mdとresearch/portable-mode-capacity-checkpoint.json。次も正本consumerのある未対応項目を優先し、未確認projectile/shieldをnoop受付しない。以下は履歴です。
<!-- /mode-capacity-current -->

現在のsealed suiteに`ally-burst`16（native15／拒否1）と`ally-burst-rosters`2を追加しました。味方バースト使用通知を共通Slangへ接続し、本人を含む編成順・条件・発動上限・down・再突入・重複descriptorをMetal実証。ルピー：ウィンターショッパーの全定義3秒／30秒と旧849／実4／部位63も全一致・独立sealし、旧916入力のentriesと全rawを保持。`reference --suite ally-burst`はGPU／packing禁止のCPU15契約です。静的219/266・base159/203はGPU認定ではなく、全キャラ認定0／通常UI CPU／Windows新規検証停止を維持します。詳細[味方バースト通知](portable-ally-burst.md)。以下は履歴です。

物理武器のinterrupt追加着弾を共通Slangへ接続しました。現在`parts-skill-world`63（native59／拒否4）がMetal成功・独立seal済み。スキルと同じgroup HP・総ダメージ外計上・吸血を使い、散弾・2銃口・生成後buff変更・射程境界・コア／critical分離・破壊／gate／add対象を検証しました。既存849・実4も全一致・独立seal、旧45入力・849全raw約2.67GB・実4全rawを保持。全実行は生成cache必須・Slang0回です。座標・deferred・random最終tick・実CUDA／環境保全・全キャラ認定は未完了、Windows新規実行0。詳細は[物理interrupt](portable-physical-interrupt.md)。以下は履歴です。

Slangの両生成cacheを共通CLIへ追加しました。`generation --generation-cache <dir>`でsealed sourceをCPU準備し、`--require-generation-cache`でコンパイラ起動を禁止した再利用を指定します。`run`／`compile`／`module-check`にも同じ2オプションがあります。Mac本体114sourceの実測は初回4.09秒・Slang2回→hit0.47秒・0回、別packageでMetal実4も全一致・独立監査済み。これはNVRTC cacheとは別の前段で、Windowsの速度・実CUDA一致・環境保全の証明ではありません。Windowsのstandalone生成は拒否し、追加検証停止を維持します。詳細は[生成cache](portable-generation-cache.md)。以下は履歴です。

共通Slangへ非座標skillのpierce／explosion到達、生成値・reach receipt、interrupt群のHP／総ダメージ外計上・吸血を接続しました。現在`parts-skill-world`46（native41／拒否5）がMetal成功・独立seal済み。生成後buff変更・複数破壊・壊れない対象・周期3tick・共有吸血を含みます。最終849と実4もMetal成功、旧849全raw約2.67GB・実4全raw・従来26入力を保持。物理interrupt・座標・deferred・実CUDA照合・CUDA生成cache改善は未完了、全キャラ認定0、Windows新規実行0です。詳細は[到達処理](portable-interrupt-reach.md)。以下は履歴です。

`interrupt-packet-codec`は7bit・38wordの版付きinterrupt packetを独立検査するsealed suiteです（154入力、正例140／拒否14）。共通CUDA／Metal生成・Metal実行・独立seal済み。本体の到達ダメージ接続やCUDA実行を認定しません。詳細は[packet設計](portable-interrupt-packets-next.md)。

interruptのprivate kind6／source3を共通world poolへ接続し、出現・世代・再出現・期限終了をMetalで検証しました。現在のsealed入口は`parts-skill-world`40（native30・拒否10）。既存849と実編成4も独立sealし、旧全rawと以前の26入力を保持しています。到達ダメージ・吸血・座標・deferred・修正版CUDA照合は未完了、全キャラ認定0です。Windowsの新規実行は停止中。詳細は[interrupt接続](portable-interrupt-source.md)、次の実装は[packet設計](portable-interrupt-packets-next.md)。以下は履歴です。

新しいsealed suiteは`parts-skill-world`26（native25・deferred拒否1）と`skill-part-codec`4です。共通Frame・部位receipt bank・群着弾を接続し、既存849＋実4も同じ最終ソースで保持・独立sealしました。interrupt入力7件はhost拒否で別集計、座標・deferred・実CUDA照合は未完了です。[部位スキル](portable-parts-skill-gpu.md)を参照してください。通常replayの同一基準規約を保ち、CPUのcleared観測1項目の修正だけを、指定ソースSHA・他全項目一致を要求する明示的な`--reference-migration parts-cleared-v1`で監査できます。

追加のsealed suite `heal-share-rosters`はナユタ/レムの全定義3秒/30秒の4入力。GPU本文を変更せずMetal一致・独立seal、レム30秒の物理履歴55件省略は明示して保持します。基準の849と併せて次の変更時に検査してください。詳細は[実編成検証](portable-heal-share-real-rosters.md)。

現在のsealed入口は`heal-share-regression`849(native676/拒否173)、診断は`heal-share-diagnostic`53です。回復分配43契約を共通DFSへ接続し、Metal全一致・旧796全raw保持・独立seal済み。`package --suite heal-share-regression`で固定しfresh展開して既存runを使用します。全キャラ認定0・本体CUDA未成立・UI CPUです。最新範囲と制限は[回復分配GPU接続](portable-heal-share-gpu.md)、以下は過去の接続記録です。

<!-- phase-diagnostic-current -->
共有フェーズのコンパイル範囲は`phase-codegen --out <fresh-directory> --slang-root <compiler-root>`でCPU調査できます。検証済みpackageから実行し、同じSlangのinit/commands/write各入口のCUDA／Metal生成物を保存します。NVRTC／driver／GPUは0、戦闘やABI成立の認定ではありません。回復分配の独立CPU契約は`reference --suite heal-share --out <new-file.json>`。詳細は[フェーズ診断](portable-phase-codegen.md)と[回復分配](portable-heal-share.md)を参照してください。
<!-- /phase-diagnostic-current -->

<!-- parent-audit-current -->
共通CLIのGPU子プロセスはraw保存までとし、親の独立監査へCPU比較を一本化しました。親の計測はaudit-phases.jsonl、子のCUDA API traceは従来のphases.jsonlです。独立audit／sealと失敗保持は維持します。詳細は[親監査の変更](portable-parent-audit.md)を参照してください。
<!-- /parent-audit-current -->

<!-- revival-notify-current -->
## seedと通知規約を反映した蘇生の共通実行器とMetal759

現在のsealed CLIはregression759（native602／拒否157）、goldenはportable-world-revival-notify-regression-short-expected.jsonです。reviveの永続definition保持、数値／markerパッシブの復元、persist、共有carrier対象の再追加、HP同期・満弾行動resetと自己蘇生後の通知を共通Slangへ接続しました。味方class randomは敵RNGと別のMT bankを使い、budget前照会で捨てる抽選も含め正本の全stateと位置を一致させています。Runtime配列は追加していません。

独立31（native22／拒否9）に加え、seed0／42で抽選を発火する2入力と、共有再追加／新規再生成の通知対照2入力を集約へ追加しました。実編成のRunPlan.seedもstatic preparationで保持してMODEへ渡します。初期755では実編成6入力が抽選0回だったためfixture既定19の転送漏れを検出できず、成功結果とseed findingを保持しました。実ディーゼル：ウィンタースイーツ／ラプンツェル／マナの全定義3秒／30秒を含む最終759全件一致・GPU0 sealを確認済みです。

旧718全input／raw／nativeはarchive全展開SHAも確認して保持。独立31は診断tailとpeak／total work2語の明示的減少を除くrawと全759のlazy bankゼロも一致。新規6実編成の物理履歴省略は0、既存ミハラ／persona等の省略制約は残ります。途中の対象packing漏れ、対象順／ログ出力、破壊ログkind5衝突、charge最低周期／global RNG事前照会の失敗も保持しています。CPUの旧revive未対応負例は未知instantへ移行。最終CPU731件中730成功・Windows専用1skip・失敗0です。

静的packing213/266・base153/203・83分類、通常UI CPU・全キャラGPU認定0・新版CUDA数値一致未確認・最終目標未完了。Windows追加実行0。共有carrierへの再追加は名前付き通知を再発火せず、新規再生成だけが通常のactivation通知を行う対照2ケースも追加しました。生成CUDA差分は記録を参照。Runtime全field同一・推定138,928byteで、compiler改善ではありません。HP条件付きpassiveの一部でpinned CPUが復帰中None比較のTypeErrorになる参照制約は残し、26fixtureで全組合せを認定したとは扱いません。次は正本consumerがあるentry_reload／damage HP basis等を検討します。詳細docs/portable-revival.mdとdevelopment checkpoint。以下は履歴です。
<!-- /revival-notify-current -->

<!-- attack-magnitude-current -->
## 名前付きATK倍率79とMetal718

現在のsealed CLIはregression718（native570／拒否148）、goldenはportable-world-attack-magnitude-regression-short-expected.jsonです。atk_buff_mag_pctを共通Slangのcaster基礎ATK加算へ接続し、独立52入力とイヴ全定義の実編成3秒／30秒を追加しました。正本の加算順・対象・owner／runtime条件の非再検査・lazy fresh readを保持し、通常ATK％／HP由来／ATKコピー／順位は増幅しません。

初回51のlazy対象1差分、初回718の保護stat受付漏れ13拒否は保存し、修正版718全件一致・GPU0の独立sealを確認しました。旧664のうち79未対応を前提にした旧負例1件だけを未知stat負例へ明示移行し、残る663の全input／raw／native、独立52の専用診断tail以外の全raw、全718のlazy bankゼロを保持。イヴの物理履歴は3秒116件／30秒1063件・省略0です。既存ミハラ／persona等の省略制約は残ります。

最終CPU723件中722成功・Windows専用1skip・失敗0、CLI28件成功。Metalコンパイラ配置の欠落を重いCPU参照／GPU claim前に拒否するCLI検査を追加しました。指定漏れでGPU前に止まった原記録は保持しています。生成CUDAは5,044byte・3関数増、Runtime全field同一・推定138,928byte。compilerメモリ改善ではありません。

静的packing210/266・base150/203・86分類、通常UI CPU・全キャラGPU認定0・新版CUDA数値一致未確認・最終目標未完了。Windows追加実行0。次はreviveの永続passive再付与／HP同期／満弾行動再開／通知再入を接続する予定です。consumer未確認のprojectile_dmg_pct／shield_dmg_pct／heal_splitは無効果受付しません。CUDA cold compiler失敗の同条件再試行や上限拡大もしません。詳細docs/portable-attack-magnitude.md、docs/portable-revive-next.mdとdevelopment checkpoint。以下は履歴です。
<!-- /attack-magnitude-current -->

<!-- enemy-selection-current -->
## 共通random／code対象・DoT終了契約とMetal664

現在のsealed CLIはregression664（native526／拒否138）、goldenはportable-world-enemy-selection-regression-short-expected.jsonです。共通MT19937のrandom選択、codeの正本body規約、budget probe、DoT refresh／最終tick、敵stack／解除／期間延長を共有実行器へ接続しました。独立60入力は61正例を51 GPU入力へまとめ、各aliasの正本比較と9拒否stageを保持しています。新規8プロファイルの全定義実編成を各3秒／30秒で追加しました。

Actor側のnamed解除にDoT clockの終了漏れがあり、従来経路と同じretireNamedCarrierへ統合しました。0.27秒再付与の境界とミハラ30秒の全51スキルも正本一致。途中62／68／58／662の失敗を保持し、最終664全件一致、旧588の全input／raw／native、途中662の成功661の全raw、独立60の診断tail以外の全raw、全664のlazy bankゼロを確認してGPU0の独立sealを行いました。CPU719成功・Windows専用1skip・失敗0です。

新規ミハラ30秒の物理履歴は2048記録＋32省略で、prefix・省略数・全戦闘状態の一致までです。新規の他15実編成は省略0。過去persona等の省略制約も残ります。診断専用のowner0スキル51件と、通常の物理履歴の省略は別の範囲です。

共通CLIにarchive-raw／restore-raw（GPU0）を追加しました。固定evidenceの元サイズ／SHAと全展開byteを検査し、明示remove-original時だけ非圧縮コピーを除きます。実capture約2.08GBを約5.85MBへ無損失退避し、既存の失敗JSONは保持。監査前には復元してください。生成CUDAのRuntime宣言は138,928byteで据え置き、actorSetCaptureのnoinlineも復帰を確認しました。compiler peak／速度改善は未証明です。

静的packing209/266・base149/203・87分類、通常UI CPU・全キャラGPU認定0・新版CUDA数値一致未確認・最終目標未完了。Windows追加実行0です。v117 CPU53のcache/controller確認とv115 cold compiler allocation failureは区別し、同条件の再実行や上限拡大はしません。次候補は参照consumerを確認できるatk_buff_mag_pct（79）。projectile_dmg_pct／shield_dmg_pctはconsumer未確認のため無効果受付しません。詳細portable-enemy-selection.md、development checkpoint、retention、compiler-deltaを参照してください。以下は履歴です。
<!-- /enemy-selection-current -->

# 共通GPU検証CLI

現在のsealed入口は`regression`588（native459＋拒否129）、goldenは`portable-world-named-magnitude-regression-short-expected.json`です。名前付き係数／被ダメージ倍率の独立54入力と、全定義の実編成4入力を追加し、旧530の全input／raw／native保持を確認しました。保留カウンタ観測は既存read関数へ共通化し、比較項目を省いていません。`docs/portable-named-magnitude.md`を参照してください。以下は以前の接続時の履歴です。

最新のsealed入口は`regression`530（native412＋拒否118）、goldenは`portable-world-persona-regression-short-expected.json`です。persona marker／selector18と対象code受付を接続し、旧481等の全raw保持と独立監査でsealしました。物理履歴の省略は`docs/portable-persona.md`を参照してください。`run --smoke`は全編成nativeを実行せず、制御・cache・artifactのCPU53件とfresh Jobのみです。必要test欠落はJob前に拒否します。Windows v117でCPU53件とfresh Jobのpost空を確認しました。既存process欠落7・service未識別は残り、環境保持成功ではありません。現行本体compiler失敗は未解決で、このCPU smokeからCUDA計算一致を主張しません。以下の件数は履歴です。

最新のsealed入口は`regression`481（native379＋拒否102）、goldenは`portable-world-base-copy-regression-short-expected.json`です。基礎ATK／HPコピー47と全定義の実編成6を追加し、旧428の全input／raw／native保持を確認しました。sealは独立監査内の新しい比較結果を使い、二度目のnative比較を省きます。監査・全raw検査・元比較器は維持し、比較0回や複数回、失敗は拒否します。`docs/portable-base-copy.md`を参照してください。以下は履歴を含みます。

2026-10-22現在のsealed入口は`regression`428（native341＋拒否87）で、goldenは`portable-world-lazy-bank-regression-short-expected.json`です。旧420へlazy-bank境界8入力を追加し、同じ実行器・比較器へ接続しました。以下の420等の件数は以前の機能接続時の説明です。詳細は`docs/portable-lazy-bank-storage.md`、現在の件数・source readinessはCLIの`list`を参照してください。

`python scripts/nikke_gpu.py --help`。Python標準ライブラリで制御し、既存のshort検証器の`prepare`/native/`compare`、`portable_typed_cuda_proof_audit.verify_cpu_gpu_calls`、厳密な生成コードnormalizer、`portable_phase_audit`、`run-world-bounded.WindowsJob`、`windows_validation_observer`を再利用します。現在のソースに対するsealed suiteは`regression`420です。旧projectile/readiness/stun/roster/skill-cooldown等のgoldenはその時点の履歴として残し、sourceの違うpackageは拒否します。`list`はgolden_source_readyも表示します。新しいsourceは`--develop`でnative比較後に明示sealします。期待値を自動追従させません。別のスイートは同じadapter契約で登録します。全効果の自動対応やテスト範囲の自動推論は行いません。

## パッケージ作成とCPU検証

開発checkoutで、必要なPython依存・pinned upstreamを用意します。

```sh
.venv/bin/python scripts/nikke_gpu.py list
.venv/bin/python scripts/nikke_gpu.py package --suite regression --out /tmp/nikke-regression.zip
.venv/bin/python scripts/nikke_gpu.py unpack --archive /tmp/nikke-regression.zip --dest /tmp/nikke-regression
.venv/bin/python /tmp/nikke-regression/scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/nikke-regression-cpu
```

パッケージはGit追跡済みのPython/Slang/Swift、公開data JSON、選択したgoldenと、ローカルpinned upstreamのcalculator/runner/scraper/dataのPython/JSON・LICENSEを含みます。dirtyな開発コードも実byteで固定し、基準HEADとdirty flagを記録します。設定・session・既存巨大レポート・raw・コンパイラ・venvは含みません。全byte/サイズ/SHAとgoldenを`gpu-package.json`に記録し、GPU sourceとgoldenの不一致は作成時に拒否します。アーカイブSHAは転送前後で照合してください。ハッシュは署名や送信元認証ではありません。

既存検証器がscratchを書き込むため、展開先を作業領域として使います。CPU preflightは入力全体と各入力・native指紋を照合し、GPU build/executeを禁止します。続いて登録された限定CPUテストを実行します。書き出したcaptureは上書きできません。

## Metal実行

```sh
.venv/bin/python /tmp/nikke-regression/scripts/nikke_gpu.py run --backend metal \
  --slang-root /absolute/path/to/.tools/slang-2026.20-Darwin-arm64 \
  --capture /tmp/nikke-regression-metal
```

`--slang-root`はbin/slangcを含むインストール済みSlangルートです。指定しない場合は従来のcheckout内`.tools`配置を使います。共通transportはCUDA/Metal双方を生成し、既存の厳密normalizerで両生成物を照合します。ゲート前観測と検証子のコンパイル/実行には共通の最大180秒予算を使い、後始末は5秒、終了後観測は別枠で最大20秒です。CPU事前検査はこの予算の前に実行します。timeoutを増やして短時間検証の制約を回避しません。

パッケージ内の`gpu-claimed-metal.json`または`gpu-claimed-cuda.json`をGPU前に排他的作成します。切断・失敗後も残し、同じ展開先からの重複実行を拒否します。別の場所へ再展開すれば機械的な禁止は跨げるため、同じpackage/source/inputをやり直す用途に使わないでください。これは全PC共通のキャッシュではありません。

## Windows検証パッケージ

アーカイブをWindowsへ渡し、Windows側の既存Python依存とSlang/CUDAを使います。共有・別チャットへの依頼はそのセッションの利用者承認の範囲で行います。

```powershell
$py = 'C:\absolute\path\to\existing\.venv\Scripts\python.exe'
& $py scripts/nikke_gpu.py unpack --archive C:/proof/projectile.zip --dest C:/proof/projectile
# 制御系を変えたときのCPU Job smoke（GPU0）
& $py C:/proof/projectile/scripts/nikke_gpu.py run --backend cuda --smoke `
  --original-workspace C:/original/nikke_tools --capture C:/proof/job-smoke
# 必要な場合だけ実GPUを1回
& $py C:/proof/projectile/scripts/nikke_gpu.py run --backend cuda `
  --original-workspace C:/original/nikke_tools `
  --slang-root C:/tools/slang-2026.20-Windows-AMD64 --capture C:/proof/cuda-run
```

親はvenvのbase Pythonを選び、venv site-packagesを子のPYTHONPATHに渡して`__PYVENV_LAUNCHER__`を除きます。新しい検証子だけをBelowNormalで起動し、fresh Job所属を観測してからstart gateを解放します。既存プロセスをJobへ割り当てず、サービスの再起動も行いません。

外部ラッパーは`finally`で検証子を後始末した直後にafter snapshotを採取します。モデルの応答再開を待ちません。観測エラーもexecution.jsonへ保存し、cleanupを飛ばしません。観測自体には既存observerの20秒上限があり、終了から30秒を超えたsnapshotは環境保持の成功に使いません。

計算一致、containment、環境保持を個別に記録します。Windowsでサービス識別がunverifiedなら、計算が一致しても環境保持はfalseです。終了コードは0＝成功またはCPU/smoke成功、1＝計算/制御失敗、2＝計算成功・環境保持未成功です。after snapshot失敗が計算結果の不一致を意味するわけではありません。これらはrun/auditの終了コードで、audit-legacyは元監査器の従来の終了規約を保持します。

## 接続断後の回収とGPU禁止監査

```powershell
& $py C:/proof/projectile/scripts/nikke_gpu.py status --capture C:/proof/cuda-run
& $py C:/proof/projectile/scripts/nikke_gpu.py export --capture C:/proof/cuda-run --out C:/proof/cuda-results.zip
```

`run`を再送せず、保存先に対してstatus/exportを実行します。結果ZIPにはJSON/JSONL/logだけを入れ、input/readbackのrawや生成物はWindowsのcaptureに残します。JSONには診断に必要なプロセスID・実行パスが含まれますが、observerはコマンドラインを保存しません。

```sh
.venv/bin/python scripts/nikke_gpu.py import --archive /tmp/cuda-results.zip --dest /tmp/cuda-results
.venv/bin/python /tmp/nikke-projectile/scripts/nikke_gpu.py audit --capture /path/to/full/capture
```

importは原byte・サイズ・SHAを確認し、新規宛先だけへ展開します。回収された小さな結果だけからはrawの独立再照合を主張しません。`audit`はinput/readback/generatedを残した完全captureに対して、同じpackageから実行します。既存native比較をGPU禁止で再実行し、全readback/各入力/native/生成コード、CUDA API成功とJob PID/作成時刻を確認します。

`collect --capture ... --out ...`は進行中/失敗captureからも小さなartifact一覧を生成します。完了後に初めてexportしてください。原報告を書き換えてから再collectし、失敗を成功へ見せる用途には使いません。

履歴v102/103/104の固定JSONは従来の監査器をそのまま呼べます。

```sh
.venv/bin/python scripts/nikke_gpu.py audit-legacy --version 104
```

これは既存監査器の従来の出力先へ派生監査JSONを書きます。原Windows JSONは変更しません。過去の環境保持失敗は失敗のままです。

## 拡張と時間計測

登録先は`SUITES`。現在のadapter契約は`prepare() -> (entries, packed)`、`suite.INPUT`、`suite.inspect_native(case)`、`compare(block, domain)`、`cross.digest/normalized`です。複合domainを持つadapterは`native_reference(domain)`を明示でき、同じnative値全体を返します。`regression`はこの契約でreadiness81・stun46・全定義の実編成44・skill cooldown25・回復貯蔵51・発動回数減少48・skill critical36・周期割合補正32・周期秒数補正57をまとめ、各スイートの元の比較器へ委譲します。入力headerと各rowのstride/byte一致を合成前に検査し、一つのshader起動で420入力を処理します。計算本体やnative oracleを複製しません。

`cpu.json`、`cpu-tests.json`、`execution.json`、`phases.jsonl`、`evidence.json`に時間を分けて残します。executionのelapsedはゲート前観測と終了後観測も含みます。API phase/transport時間からコンパイルとGPU処理を区別します。パッケージ作成・転送時間の自動集計、全PC共通の結果キャッシュ、変更ファイルからの検証範囲自動選択は今後の拡張です。

## 未対応分類と新機能の開発

```sh
.venv/bin/python scripts/nikke_gpu.py inventory --out /tmp/nikke-readiness.json
.venv/bin/python scripts/nikke_gpu.py package --suite projectile --develop \
  --out /tmp/nikke-development.zip
# 必要な場合は --case development/lost-hp-defense-1-1--1 で入力を限定
.venv/bin/python scripts/nikke_gpu.py unpack --archive /tmp/nikke-development.zip \
  --dest /tmp/nikke-development
.venv/bin/python /tmp/nikke-development/scripts/nikke_gpu.py run --backend metal \
  --slang-root "$PWD/.tools/slang-2026.20-Darwin-arm64" --capture /tmp/nikke-development-metal
```

`inventory`は全266プロファイルを静的準備し、既存と同じlowering・効果validatorを各定義へ独立に適用します。`priorities`はカテゴリ・効果種別・stat・target・scaling・未対応フィールドで分類します。未対応triggerはvalidatorが返す`operator.domain`（timing/condition）と`operator.descriptor`を保持し、別の演算を同じcodeへ混同しません。同じcodeの診断文は`messages`へすべて保持します。影響プロファイル数と「観測された分類が1つだけ」の件数を出しますが、効果内の最初の失敗より先は未検査なので、件数は対応完了予測ではありません。元定義を変更せず、全プログラムのpackingも別途実施します。packing・GPU受付・実戦一致の認定は分けたままです。

`--develop`は出力goldenがない新機能向けです。入力・CPU基準・GPUソース・パッケージ全ファイルを固定し、同じbounded実行・native比較・全trace比較・保存結果監査を利用します。projectile adapterには新機能のdevelopment入力が追加されます。`--case`はこのパッケージだけに使用でき、未知・重複した名前は拒否します。開発パッケージの実行はMetal限定で、結果は`sealed: false`です。生成CUDA/MSLと全readbackの指紋は記録しますが、過去のgoldenの出力指紋を期待値にはしません。入力/native基準の変化は引き続き拒否します。正式goldenの自動更新やCUDAへの未確定入力送信は行いません。

## CUDAコンパイルキャッシュ

Windowsの既定はSM86向けCUBINです。NVRTCへ`--gpu-architecture=sm_86`・`--fmad=false`を渡し、`nvrtcGetCUBINSize`/`nvrtcGetCUBIN`でバイナリーを取得します。実行時にdeviceのcompute capabilityを照合します。APIは[NVIDIA NVRTC 11.3公式文書](https://docs.nvidia.com/cuda/archive/11.3.0/nvrtc/index.html)に基づき、Windowsの11.3 DLLでもexportをCPU0-GPUの能力検査で確認しました。`NIKKE_CUDA_ARTIFACT=ptx`は診断用の明示選択です。API不在やSM不一致からの自動切替はありません。数値・効果のSlang本体は共通です。

`NIKKE_CUDA_COMPILE_CACHE`を専用ローカルディレクトリへ指定した場合だけ、生成物を保存・再利用します。キーは形式(cubin/ptx)、生成CUDAの原byte、全オプション、NVRTC DLLと引用includeされたSlang prelude/headerの原byte SHAです。破損・identity不一致は失敗させ、normalizerはキーに使用しません。hitでもCUDA launch/synchronize/readback・CPU比較は必須です。`cuda_compile_cache`の観測と、`compiled.cubin`または`compiled.ptx`をcaptureに残します。rawバイナリーは結果ZIP・GitHub payloadへ含めません。

Slangは`-fp-mode precise -line-directive-mode none`で生成し、コンパイラールートをresolveします。Macで独立した2ルートのCUDA/MSL全byte一致を確認しました。改行配置も変わるため、既存normalizerを維持して新たにMetal75を実行・sealし、旧75の全input/output/native指紋との一致を確認しました。v3時点の`readiness`は累積75(native60＋拒否15)です。後続のv4は末尾の更新記録を参照してください。

`cases --suite readiness`は入力名をCPUで一覧にします。開発成功後は`seal --package-root /tmp/nikke-development --capture /tmp/nikke-development-metal --out /tmp/new-golden.json`で、元パッケージの独立プロセスによるGPU禁止監査・native再比較からgoldenを明示作成できます。失敗・非Metal・非development・現行GPUソース不一致を拒否し、既存ファイルを上書きしません。作成物をsuiteへ登録してからsealed packageでCUDAを検証します。`lost-hp-roster`は実編成用、`lost-hp-diagnostic`は既存診断入口用で、どちらもdevelopment限定です。

CUDAのcold実行後は、同じpackageの`cache-check --capture <cold-capture> --out <new-report.json>`で、保存バイナリーと同じcacheへのhitをGPU/NVRTCコンパイル0で確認します。`NIKKE_CUDA_COMPILE_CACHE`と`CUDA_PATH`をcold時と同じ場所へ設定します。コンパイル成功後のmodule load失敗でも、回収された生成物とphase receiptが揃えば検査できます。これはキャッシュ検査であり、計算成功・暖機後のGPU時間測定ではありません。`calculation_verified=false`を明記します。

v105のPTX方式は、コンパイル44.609秒後にmodule loadが返らず180秒で終了しました。kernel launch0、同条件retry0です。missing0/後続残留0/元HEAD・status保持も、失敗したcontainment・サービス識別未確定を成功へ変えません。v106のCUBIN方式もNVRTC内で180秒の予算を消費し、artifact作成・module load・kernelへ到達していません。missing14の原因は不明です。CUBINの実機速度・数値一致と暖機効果は未証明で、時間枠を増やして再試行しません。詳細原本はWindowsローカルに保持し、Macには個人情報を除いた集計を取得しました。

## 保存Metal出力からのデコーダー検証

```sh
# 新しいデコーダーを含むdevelopment packageを作り、別フォルダーに展開する
.venv/bin/python /tmp/new-package/scripts/nikke_gpu.py replay \
  --source-package /tmp/original-package --source-capture /tmp/original-metal \
  --capture /tmp/new-replay
```

元と新しいパッケージのsuite・GPU source・入力・native基準を一致させ、GPU transport・normalizer・canonical参照・新旧の全GPU/upstreamファイルを検査します。元のGPU dispatchが完了していれば、比較だけが失敗したcaptureも再評価できます。timeout・cleanup失敗・未完了dispatchは拒否します。元のraw/generated/evidenceをそのまま読み、元のexecutionは`source-execution.json`として保存します。新しいGPU実行を装うexecution.jsonは生成しません。原package/captureは監査時にも必要なので保持してください。出所はSHA検査であり署名ではありません。

`replay`の`gpu_calls: 0`、`source_gpu_dispatches: 1`、元の`source_execution_passed: false`を区別します。元の失敗を成功へ書き換えません。CPU比較の診断ディレクトリもCLIが準備します。正常入力のGPU statusが0以外の場合は、decodeより先に拒否statusを報告します。

2026-10-21のrecipient6では、元のMetal rawに保存された順序と重複を読み取るデコーダー修正をこの経路で確認し、GPU再実行0で6/6一致から明示sealしました。

## レビュー反映後の範囲

`readiness`の現行goldenはv5で81入力（native60＋拒否21）です。v4で旧75の指紋と全readback byteを維持し、再突入の不正入力6件を追加しました。v5はstun接続後にも全81の入力/native/output指紋とrawを維持しています。`burst-recipients`の13入力は再突入・instant対象の過去ソースでMetal/nativeが一致した記録です。新しいCUDA実機照合は未完了です。古いsuiteがsource不一致を示す場合、そのgoldenを自動追従させません。

`burst_reentry/all_allies`は、発動者に一度だけ再突入要求を記録するnative規約を共通world受付へ接続しています。5人への要求複製はしません。入力のcombat・stat・値・対象をGPUでも検査します。新たな味方対象にはinstant回復も含め、実在名の不在、コロン付き名、対象リストの重複、B3発動前後を共通fixtureで確認しました。

未対応statとrecipientには構造化したreasonを使い、文面だけでrecipientに混同しないようにしました。静的packingは173/266（base122/203）です。これはGPU実戦認定ではなく、通常画面はCPU、全キャラ認定0を維持します。

Windowsの終了処理は所有Jobを明示終了し、子とJob全体が終了した後、handleを保持したまま`post_wait`を採取して閉じます。cleanupは合計5秒で、待機失敗に同じ予算をもう一度与えません。Jobピークメモリも観測します。Macでは状態連動のCPU故障注入を通過しました。Windows専用のGPU0テストは、子孫を持つ2秒timeoutを使い実際の空Jobとピークメモリを検査します。実Windowsでの修正版確認までは、制御修正の実機成功を主張しません。失敗した過去のcontainment/環境保持の判定は維持します。

CUBINはELF形式を確認してからキャッシュへ公開します。不正な生成物は保存せず、既存の破損エントリは引き続き失敗として扱います。キャッシュhitのCPU検査と、実CUDAの計算・性能検査は別です。

### 新スイートの受け渡し

v105で、旧CLIが未知のsuiteを展開後に拒否するbootstrap問題を確認しました。現在の`unpack`はschema・member一覧・重複・原byte SHAを検査して転送し、suite登録の照合は展開先CLIの`verify_package`/`run`で行います。展開中にpayloadのPythonは実行しません。未知schemaは宛先作成前に拒否します。旧CLIの場合は、ZIP全体のSHAとmanifestを確認して取り出した現行CLIで、新しい宛先へunpackしてください。途中の展開失敗はGPU実行とは数えず、元の失敗記録を残します。

### Windows制御検査v108

v107はCPU81/native60の後、テスト用の子起動直後に失敗し、smoke未到達でした。原失敗を保持しています。テスト起動をCLIと同じbase Python・launcher環境除去へ合わせ、wrapper診断を残したv108は単独3件とCLIのCPU69件が成功しました。実Windowsの子孫付き2秒timeout検査と外側smokeで、終了後の空Job・peak memory取得を確認しました。smoke4.841秒、missing0、元HEAD/status保持、NVRTC/driver load/GPU0です。サービス識別unverifiedのため環境保持全体は未認定です。新機能のCUDA計算・coldコンパイル・速度は未検証のままで、次は資源と生成/最適化設定の切り分けです。詳細は`research/portable-world-v107-control-sanitized.json`、`research/portable-world-v108-control-sanitized.json`を参照してください。

## stun・免疫・対象条件

`stun`は共通の36正例＋10不正入力です。状態は解決済みのcarrier対象と生存から読み、条件・期限を独自に進めたり、遅延対象を数値バフとして消費したりしません。免疫はcanonical compilerの既存quantity bit2を使い、wire幅は変えていません。射撃停止・チャージ再開、B1/B2の既定候補を保持した待機、バースト再開、`target_stunned`と`self_stun_immune`を同じSlangで実行します。typed敵の参照条件は現在の敵文脈と世代を使います。敵stunを被ダメージ倍率へ加算しません。

Metal46はnative完全一致し、値0/負値でもpresenceが有効なこと、免疫の付与順・期限・他発動者、未解決rank、子通知中のstun、再出現世代、128対象を検査しました。CPUの外部イベントAPIへはstunを開放せず、private combat worldだけで受け付けます。静的packingは180/266、base126/203で、全キャラ実戦認定ではありません。

## コンパイルだけの短時間診断

```powershell
& $py C:/proof/package/scripts/nikke_gpu.py compile `
  --original-workspace C:/original/nikke_tools --capture C:/proof/compile-cubin-o1 `
  --compile-cache C:/proof/cuda-cache --artifact-kind cubin --ptxas-level 1 `
  --memory-limit-mb 2048 --timeout 60 --slang-root C:/tools/slang-2026.20-Windows-AMD64
```

これはsealed Metal packageのGPUソースと生成CUDA/MSL指紋を検査してから、通常実行と同じ`compile_cuda_source`/NVRTC/cacheだけを使います。ゲームのnative再シミュレーションは行いません。CUDA driverのDLLロード・context・kernelを禁止します。fresh Job/BelowNormal/start gateは共通で、コンパイルの最大予算は60秒、cleanupは5秒です。Jobのメモリ上限は既定2GiB、指定可能範囲は64〜4096MiBで、実際のpre/post上限とpeakを監査します。timeoutを別枠で足して古い失敗を継続しません。`compile-claimed-cuda.json`を排他的に保存し、同じパッケージの再送を拒否します。

`compiler_verified`・`calculation_verified`・環境保持は別です。成功しても計算はfalseです。`compiler.json`、生成物、compiled artifact、phase、Job/環境観測を残し、`audit`/`status`/`collect`/`export`を再利用します。途中失敗のartifactがあっても、完了したAPI/phase/Jobの証拠なしにコンパイル成功へ昇格しません。サービス識別unverifiedも成功へ変えません。compile/auditの終了コードは1＝compiler未確認、2＝compiler確認済み・環境保持未確認です。

ptxasレベルは明示指定したCUBINの0〜3だけを許可し、既定の計算方式・数値規約・FMA無効は維持します。異なるオプションは異なるcache keyです。NVRTC11.3の`--ptxas-options`とptxasの`--opt-level`は[NVIDIA NVRTC文書](https://docs.nvidia.com/cuda/archive/11.3.0/nvrtc/index.html#group__options)・[compiler driver文書](https://docs.nvidia.com/cuda/archive/11.3.0/cuda-compiler-driver-nvcc/index.html#ptxas-options)に基づきます。指定できることと、実機で速く正確に動くことは別で、低最適化版のCUDA数値・速度は未検証です。

v109の実NVRTC11.3は結合形式`--ptxas-options=-O1`をreturn5で拒否しました。固定tiny kernelによる15秒上限のGPU0診断では、`["--ptxas-options", "-O1"]`と`["-Xptxas", "-O1"]`の別引数形式は各1回成功しました。共通コンパイラは前者を使い、オプション配列そのものをcache keyへ含めます。本体のO1コンパイル成功や数値一致は、このtiny診断では認定しません。保存報告は`research/portable-world-v109-option-syntax-sanitized.json`です。

## 実編成の共通回帰

`roster-regression`は9つの公開キャラprofileを各3秒／30秒で準備する18入力です。stunで新しくpacking可能になったD、プリバティの全4段階、マスト：ロマンチックメイド、タキナと、比較用のペオニー・ミランダを含みます。既存の`compile_projectile_battle`、binding proof、native戦闘比較、物理射撃trace比較をそのまま使い、キャラ効果を選別・除外しません。

```sh
.venv/bin/python scripts/nikke_gpu.py cases --suite roster-regression
.venv/bin/python scripts/nikke_gpu.py package --suite roster-regression --out /tmp/nikke-real.zip
# 新しい効果／新しいGPUソースを検証する場合は --develop を明示する。
```

18入力はMetal/native完全一致後に明示sealしました。別ソースへ進んだ場合は、従来どおりstale goldenを拒否します。この代表編成群は全キャラ・全装備・全操作・全敵世界の認定ではなく、通常画面もCPUです。

後続のskill cooldown対応ではセンチの2profile×2期間を追加し、実編成は22入力です。現在は`regression`149の一部としてMetal/native一致を確認しました。旧145入力（readiness81/stun46/実編成18）は入力・全raw出力ともbyte一致です。新機能25入力と149入力は同じ新Slang sourceで検証し、それぞれ明示sealしました。個別の古いgoldenを集約結果で書き換えず、履歴と現行suiteを区別します。

v110の修正版argvは実NVRTCで受け付けられましたが、本体O1コンパイルは約41.20秒（NVRTC約30.11秒）で失敗し、保存stderrの先頭に`ptxas fatal: Memory allocation failure`がありました。Jobは2GiB、終了後空、missing0、GPU0、完成artifact0です。サービス識別はunverifiedで、上限との因果も未確定です。期限延長・メモリ増量・O0への自動再試行は行っていません。キャッシュの実機性能と新機能のCUDA数値検証は未完了です。

成功artifactがある場合のcache hitは、同じpackageの`cache-check`でNVRTC/GPU0の検査をします。cacheディレクトリはcold時と同じ`NIKKE_CUDA_COMPILE_CACHE`へ設定してください。

```powershell
& $py C:/proof/package/scripts/nikke_gpu.py run --backend cuda `
  --original-workspace C:/original/nikke_tools --capture C:/proof/warm-cuda `
  --compile-cache C:/proof/cuda-cache --artifact-kind cubin --ptxas-level 1 --require-cache
```

後続の実CUDA検証を行う場合に使う指定です。`--require-cache`（環境変数`NIKKE_CUDA_CACHE_REQUIRED=1`）では、missはNVRTC program作成前に失敗し、CUDA driverへ進みません。オプションの変化・破損・compiler/headerの変化は自動再コンパイルで隠しません。

## 保存済みコンパイル結果のCPU解析

```sh
.venv/bin/python scripts/nikke_gpu.py compiler-stats --capture /path/to/full/capture --out /tmp/cuda-source-stats.json
.venv/bin/python scripts/nikke_gpu.py ptx-stats --cache-entry /path/to/cache/KEY.json \
  --phases /path/to/original/capture/phases.jsonl --out /tmp/ptx-stats.json
```

両方ともNVRTC／driver／GPU呼び出し0。原ファイルを変更せず、新規出力先だけへ結果を保存します。前者は保存したgenerated.cuをartifact／evidenceで照合し、後者はキャッシュidentityのkeyと原PTX byteを既存のverified compile receiptと照合します。読み取った宣言の集計であり、実レジスタ・compilerメモリの原因・計算一致を認定しません。PTXの未対応宣言は部分推測を返さず停止します。Windowsの保存結果解析も低優先度・短いCPU上限内で実行し、解析のためにcompileを再実行しません。

`compiler-stats`へ任意の`--caller weaponFrameBody_0`を渡すと、既知のgenerated CUDA関数の呼出関係を最大3段・200関数まで集計します。noinline先は列挙してそこで止まり、同名overloadの曖昧さと打切りを明示します。関数名を解決できない場合は失敗します。これは静的な字句上の呼出しであり、実際のbackend inliningやcompilerメモリ原因の測定ではありません。

## 周期割合補正とcache読込みの更新

`skill-interval`はprivate worldの持続的割合補正32入力（native28）。`regression`361へ統合し、参照の実`_next_fire`時計も比較します。分類の`diagnostic_sources`は定義とprogramのstructured reason／文言fallbackを別集計します。CUDA cacheのhit／必須miss／破損はDLLをロードせず判定します。原byte identityと既存receipt、GPU計算比較は維持します。詳細はportable-skill-interval.mdを参照してください。

## 名前付き周期秒数補正と制御smoke

通常regressionは420入力（native334＋拒否86）。effect_interval／skill_cooldownの57入力を、既存の時計・trace比較器で統合します。詳細はportable-skill-interval-flat.md。Windowsの子プロセスはcapture/temporaryを専用TEMP／TMP／TMPDIRへ使います。`run --smoke`はpackage検査後、制御CPU29件とfresh Jobだけを実行し、native全編成とnumeric test群を省きます。GPU／NVRTC／driverは0です。通常GPU実行・CPU-onlyのnative照合とnumeric test群は維持します。

## readbackの無損失退避と復元（GPU0）

`archive-raw`は既存artifacts/evidenceに固定されたreadbackのサイズ・SHAを検査し、gzipへ保存して全展開byteを再検査します。receiptと圧縮archiveはcapture外へ保存します。既定は原ファイルを保持し、明示`--remove-original`の場合だけ検証後に非圧縮コピーを除きます。captureの既存JSON／失敗記録は変更しません。計算成功を認定するコマンドではありません。

```sh
.venv/bin/python scripts/nikke_gpu.py archive-raw --capture /tmp/old-capture \
  --archive /tmp/old-readback.bin.gz --remove-original
.venv/bin/python scripts/nikke_gpu.py restore-raw --capture /tmp/old-capture \
  --archive /tmp/old-readback.bin.gz
```

復元は既存readbackを上書きせず、receipt・圧縮byte・元evidence・展開後のサイズ／SHAをすべて確認してから公開します。原byteの退避先は`.gz`と隣接`.gz.json`の組です。非圧縮ファイルがない状態では従来の監査器は実行できないため、監査前に復元します。Linux／Macは除去前にarchive親directoryもfsyncし、Windowsはそのdirectory fsyncを行いません。停電耐性の認定ではありません。

Macの実capture2,082,471,936byteは5,849,675byteへ圧縮でき、全展開byteの元SHA一致を確認しました。復元・破損拒否・出力上書き拒否・検証失敗時の原ファイル保持はCPU4テストで検査します。rawや圧縮rawをGitHubへ含めません。

## GPU接続前のCPU正本契約

`reference --suite revive --out /tmp/revive-reference.json`は、未実装機能の正本consumerを短く確認する経路です。26のliteral fixtureと既存full-native observerを使い、packing／GPU build／executeを禁止します。`run --cpu-only`のようなGPU入力・goldenの事前検査とは別の段階で、GPU対応率へ加算しません。ソース・literal入力の変更、未検証契約、失敗後の同名出力上書きを拒否し、失敗を保存します。

詳細native状態はローカル出力に保存します。小さなcheckpointには入力／native／traceのSHAと契約結果を共有でき、詳細native状態を都度転送する必要はありません。成功しても`gpu_supported=false`／`calculation_verified=false`です。次に同じfixtureを共通Slangへ接続し、immutable packageのMetal検証・既存集約の保持・独立sealを行います。既存suiteの比較項目やstrict normalizerは変更しません。具体的な蘇生の契約と未完了部分は`docs/portable-revive-next.md`を参照してください。

## 保存PTXからの独立アセンブル

`assemble`は成功済みPTX producerと固定12.4.131 componentを再検査し、既存fresh Job・2GiB/60秒で一度だけアセンブルします。NVRTC/driver/GPU0、上限変更・fallback・自動再試行なし。詳細は[独立アセンブル](portable-offline-assembly.md)。

## CPU群のまとめ実行

run/cpu-only/smokeは全登録群を1個のfresh CPU workerへ渡します。群別ログ/receiptを保ち、欠落・zero tests・途中失敗・不完全receipt・CPU timeout（既定60秒／明示した統合suiteは90秒）はGPU前に停止。詳細[CPUまとめ実行](portable-cpu-batch.md)。通常run childの出力は明示file modeで固定8MiBずつ保存し、全件監査を維持します。詳細[共通file転送](portable-file-transfer.md)。
