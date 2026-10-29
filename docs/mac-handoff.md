# 2026-10-30 歴史逆変換を共通化、保存物診断を共通2GiB Jobへ接続

portable_quantity_visited_source_contract.historical_hashesへ旧Frame/mixed証明書の数量逆変換を共通化。固定d04e5689…へ5hunk全byteを復元し、helper/source改変・依存欠落・baseline変更・演算式改変を拒否する。旧証明書を使う現source実行は引き続き拒否。最初の診断packet9f1661…のMac unit失敗は保存し、修正版f7337532…は21群232件とPTX plan成功、a2a87eb4で共有した。GPU計算sourceは前回Metal sealから不変。

保存物専用のptx-stats/cache-check stageをrun-gpu-packetへ追加。既存監査器を同じfresh Job/2GiB/BelowNormal/gate/終了直後観測へ通す。readonly CPU経路も独自wrapperで上限を省略できないようにした。current packetのowner検査、厳密cache hit、PTX receipt/graph hash、CPU-only counterを維持し、compiler/calculationを認定しない。関連105/固定de42d2db…22群238検査成功。新stageの実Windows確認は未実施。詳細portable-packet-file-diagnostics.md、記録research/portable-packet-file-diagnostics-v1.json。

Windowsの保存結果はまだMacへ取得できていない。共有の自動承認拒否に対して既存の人間の包括許可を示した再確認を依頼したが、接続が利用できず結果不明。元のPTX検証やCPU診断を再送せず、既存チャットの保存状態・共有審査結果の取得だけを行う。復旧確認はユーザーへasync質問済み。次は保存結果の全byte/SHA照合を完了してからCUDA物理資源/実計算へ進む。全目標は未達。以下は履歴。

# 2026-10-30 quantityTotalsの訪問管理を共通bitsetへ縮小、Metal3種類を独立seal

QuantityVisitedは256uintのseenを8uintへ置換（ソース上1024→32byte）。values/flags/order配列、初出順、フィルター、binary64加算・丸め、時計は不変。共通helperをCUDA/Metalへ生成。5hunk逆変換で旧quantity全文SHA d04e5689…を復元し、旧max-ammo baseline/normalizerを保持した。実PTX local／物理stack削減は未測定。

quantity-visited16（境界9/拒否7）/max-ammo-visited28（native20）/moving-visited15（native3）がM5成功し、全3を別fresh GPU禁止監査でseal。GPU .000414/.051732/2.227792秒、独立監査 .409858/2.438136/84.360426秒。max-ammoとmovingの旧全input/output/native指紋を保持し、moving全129908160byteのSHA3765a8c5…も同一。world2種に同じfresh golden由来source-only証明書、moving-visited-cache-onlyも登録。旧Frame証明書は厳密な歴史projectionで検査するが現source証明にはしない。新規実行にはvisited suiteを使用し、他の古いsource sealを昇格させない。

最終76検査、sealed moving packet fb2c7719…自身8群42検査成功（ZIP13669201byte/SHA98610c75…）。実GPU source不変の最終登録後にGPU再実行0。初版dd282090はmutating不足でGPU前停止、4d98341eは拒否domain誤分類でGPU後比較失敗。共通拒否経路へ修正したa6b39ff1の出力と4d98全rawは同一だが元失敗は保持。今回成功GPU3/比較失敗GPU1/GPU前失敗1/同claim retry0。Windows追加依頼0、既存チャットidle。記録research/portable-quantity-visited-metal-v1.json、詳細portable-quantity-visited.md。次は短いWindows PTX比較でquantityTotals5192byteの変化を測る。CUDA起動成功／全キャラ／全目標は未達。以下は履歴。

# 2026-10-30 Windows新PTX比較完了、公開残件と限定実装の分類を分離

固定3fc64fb2/compiler-full--moving-framesはWindows20群227件、paired生成29.770秒、PTX単独NVRTC1回39.477秒（内側55.185/60秒）成功。compile生成cache必須hit/Slang0。新PTX5fc6b522…は271関数／未解決等0。dispatch local9784→1848byte、virtual regs12572→13654。quantityTotals5192/tick2584は不変、PTX全体は112453byte増。物理stack/register・速度・起動error2の解消を認定しない。次はquantityTotals visited-group scratch削減、first-seen順と全binary64演算順を維持し、共通テスト/Metal後に短いPTX比較。

driver/kernel/native/ptxas/object/link0、全Job終了空/欠落0/error0、元139file不変。ただしNIKKEサービス未識別でpreservation false→compile CLI exit2→外側stage false→wrapper1を保持。保存結果の読取だけで理由を確認、再実行0。公開summary9499byte/manifest739byteを固定report eeb36b45…からSHA全照合し、CUDA/MSL strict正規化hashがMac独立seal基準と一致。Macでraw PTXを読んだ認定ではない。記録research/portable-moving-frames-ptx-peer-v1.json。

model-checkの依存表にprivate sampling/skill/parentのsuite・proof存在・現source一致を明示し、公開受付の残件と分離。mixed-world残件のscopeも限定。約3KBのCLI要約へ投影し、分類20/CLI51検査成功。5canonical不足／公開GPU false／全キャラ0は不変。記録research/portable-coordinate-gap-scope-classification-v1.json。コード共有d8bde117。Windows既存チャットはidle、cursor77f087d6-874c-42d4-a6aa-311d94ff8aa6:30、未処理依頼なし。全目標は未達。以下は履歴。

# 2026-10-30 moving-groupへ共通resident Frameを接続、Metal全15を独立seal

moving-framesは既存moving entryをincludeしてPORTABLE_RESIDENT_FRAME_STACKを有効化するだけ。既存277 GPU source／戦闘時計／全15 input/native契約／全出力比較は保持。固定3c72494eでM5実GPU1回2.233823秒／cold PSO63.780806秒。129,908,160byte全部が旧moving-groupのSHA3765a8c5…と一致。別fresh GPU禁止監査が全15/native3を84.244527秒でseal。CUDA/Metal反射はstride143048、Frame4096byte at138952、3資源／CUDA引数48byteで一致した。

sealed／cache-only入口、新goldenと同じfresh監査golden由来source-only証明書を登録。最終package dada18f3…（ZIP13,632,538byte/SHAa8a4c567…）自身7群40テストとCLI51テスト成功。旧全106証明書には変更前HEADの11GPU sourceとの不一致があり保持する。新15で旧106を認定しない。backendのexact inverse hunk追加は旧baselineを保持、汎用Frameテスト6件を再利用した。旧失敗packet945ddf7d…と全rawは保存。

PTX compile-planはsealed packet自身で2GiB／60秒／ptxas level無しのpolicy成功。180秒とPTXへのlevel指定を拒否した元planも保存。Windows追加依頼0／GPU再実行0。次は新sourceの短いWindows PTX生成と資源比較（既存CLIとbounded stage、旧消費済みclaimは再送しない）。CUDA物理stack削減／return2解消／実CUDA計算は未確認。quantityTotals5192byteは次の改善候補。証跡research/portable-moving-resident-frames-metal-v1.json、詳細portable-resident-dispatch-frames.md。全キャラ／全目標は未達。以下は履歴。

# 2026-10-30 Windows CPU53とhost ABI確認、保存PTXから改善箇所を特定

固定378bf9a0/package164a2455のWindows5群53件が成功。新host-memoryは実自分・親・Job上限2GiBの読取と親handle解放を確認。保存journal要約は元launch戻り値2を保持し、未記録のallocation byte／launch形状／失敗時memoryをunknownとした。実device samplingは未実証。各段階終了後Job空、元136file不変、新GPU claim無し。

同じsourceの既存ptx-stats --callgraphで、保存PTXとreceipt／CUBINの一致、271定義の完全な直接到達graphを確認。local宣言上位はdispatch9784／quantityTotals5192／tick2584byte。未解決・間接・外部call／cycle0。ただし物理register／peak stackやCUDA return2の原因を確定しない。元136＋cache証跡5file不変。Windows GPU／driver／compile／native battle追加0。

公開summary/manifest計4fileの外部SHA・bytes・数値・失敗境界をMacで照合した。checkpointはresearch/portable-prepared-memory-and-ptx-peer-v1.json。次は既存resident Frame保存をmoving-group全15/native3/reject12へ接続してMetal実証し、新sourceの資源を測る。距離モデル調査は同じスキル文の再探索を終了し、独立GPU対応を進める。CUDA計算／環境保全／全キャラ／目標は未達。以下は履歴。

# 2026-10-30 メモリ観測CLIを追加、最終claim検査を保って重複1回削減

host-memoryは自分と実parentのPrivateUsage/working set/別の過去peak、および既存Job ABIによるlimit/peakを読むWindows CPU専用CLI。任意PID指定/全process列挙/CUDA driver呼出しは無い。cuda-resource-summaryは外部SHAで固定した保存phaseからallocation要求byte・launch形状/戻り値・保存memory snapshotをまとめ、旧未記録値はunknown、最終append切断はincompleteとする。途中の破損/変わったSHA/偽のbool数値等を拒否する。いずれも計算認定false。

prepared-run --observe-cuda-resourcesとgpu-prepared requestのobserve_cuda_resources="1"だけが、既存current CUDA contextのcuMemGetInfoとown/parent host状態をallocation/launchの前後で取得する。デフォルト追加query0。native引数・戻り値/例外・buffers・計算は不変。flagをrun/env/runtimeへ束縛し、post監査はrequested/recorded/completeを分ける。数値は非atomicな時点観測で、空きVRAMの全量を確保できるという保証や原因判定にしない。実device samplingはまだ未実証。

親の直前verify_package1回は、同じ全source/manifestを再検査してから所有を記録する元claimへ集約した。最終byte検査そのものは残し、認証直後のsource改変もclaim前に止める回帰検査を追加。実時間の改善は未測定で、前の7.594秒をそのまま新しい短縮量として主張しない。

固定164a2455…自身82群861検査成功（Windows cleanup1skip）、payload/全golden/501計算・保護CPU・pinned source record保持。17 memory/observer合成検査、親13/子8/stage7/phase8を含むWindows候補5群53件はloaderで実数確認。実CLIの合成ログ正常/誤SHA/Mac host gateも成功。既存phase cleanupのps読取はsandbox拒否を維持して許可されたCPU環境で検査し、スキップしていない。source ZIP13,538,017byte/SHAc42185aa…、記録research/portable-prepared-memory-observation-v1.json。

次はWindowsで新CPU CLIの実host ABIと保存済み失敗ログだけを確認する。GPU/driver/context/module/compile/native battleを再実行しない。消費済みba760483のclaim/失敗と原136fileは保持。実CUDA計算/全キャラ/目標は未達。以下は履歴。

# 2026-10-30 保存binaryのCPU資源診断、link後のREG/stackを固定

WindowsのCPU診断は4.959秒/exit0、既存cuobjdump resource1回0.115秒と保存linkログがREG254/STACK24,960byte/LOCAL0/SHARED0で一致した。object entry単体REG24/stack/spill0とは別であり、前者を実CUBINの値として扱う。PTX entryのlocal depot宣言無しも呼出先stack無しの証拠にはしない。既存CUBIN0f140174…/PTXe6d83bf9…/CUDAf2d15deb…へ一致、原136file不変、追加GPU/driver/compiler/native/test0。Job終了空/欠落/観測cleanup error0、service/環境false。

保存phaseはallocation成功3回とlaunch return2/context destroy0を持つが、allocation要求byte数・launch形状の実値と失敗時VRAMは未記録でunknown。原因はGPU資源とJob内host圧迫を未切分け。次は共通CLIにこの不足観測を追加し、Job上限を上げたりゲームを止めたりする前提にせず、計測できるメモリ計画を作る。同じ消費済み試行を再実行しない。

公開ca9142e6…の小summary5328byte/manifest504byteだけを元bytes/SHAと同一binaryの既知anchorへ照合。Macは原rawの独立監査ではない。親のverify_packageが5回・合計50.308秒、子のown source検査7.778秒だったため、失敗したGPUの演算時間を待ち時間の主因としない。重複検査の削減は元の完全bytes/所有/claim境界を保持して設計する。記録research/portable-prepared-resource-peer-v1.json。Windowsはidle、実CUDA計算/全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 修正版は実launchへ到達、CUDA error2で停止・再実行禁止

Windows固定ba760483…は全4017file/指定3群の実数34検査（依頼42はMacのwildcard集計誤りで訂正）成功。必須paired生成cache hit/Slang0/NVRTC0、元snapshot/追補/完全認証成功後に元の一度だけのGPU claimを消費した。module load/メモリ確保は成功し、cuLaunchKernel1回がreturn2で停止。GPU子18.019秒/外側113.163秒、ともにexit1/timeout無し。context破棄成功、readback無し、native post未実行、計算false。GPU呼出し0とはせずgpu_calls nullと実launch attempt1を分離する。

Job設定2,147,483,648byte、子peak2,088,165,376/外側peak2,185,158,656byteは別観測値として保持。Job残存/既存process欠落/観測cleanup error0、元84file（79＋v1証拠5）不変、service/環境false。claim/失敗/captureを保持して同じstageやGPUを再送しない。公開61846f04…のsummary3986byte/manifest553byteだけ元bytes/SHA・packet/base snapshot/certへ照合した。Macは元Windows rawを独立監査していない。research/portable-prepared-parent-peer-v2.json。

NVIDIA公式のerror2はmemory/resources確保失敗。VRAM/local/stackとJob内host memory圧迫は未切分けで、ゲーム利用等を原因と断定しない。保存phase/ptxas log/同じPTX・CUBINのresourceを読むCPU-only診断を1回依頼済み。導入済みcuobjdumpがあればresource表示だけを使い、compile/driver/device query/GPU再実行はしない。数値が無ければunknownとする。4群のfresh native監査はreadbackが無いので実行しない。全キャラ/全特殊効果/目標は未完了。以下は履歴。

# 2026-10-30 v1は実GPU前で停止、専用cache guardを保持して修正

Windows8d72e81e…は完全4016file/指定30合成検査35.008秒/CPU Job smoke4.408秒が成功。gpu-preparedは11.391秒/exit1でrequired_generation_snapshotのcache readerを外側forbid_gpuが先に置換して停止。cache missではなくlaunch false/GPU0、元/新GPU execution claim/future capture無し。元79file不変、全stage gate/終了空/欠落0/観測cleanup error0、service/環境false。旧wrapper stage claimと失敗を保持。公開75351026…の小summary3814byte/manifest553byteだけ元bytes/SHAと既存anchorへ照合した。原rawのMac独立監査ではない。

修正はrequired_generation_snapshotをその関数自身のfile-only guardで呼び、その後の認証/claimを従来forbid_gpuで囲む。専用guardのcompiler/subprocess/native library/execute禁止は変更しない。元readerを保存する前に外側guardで破壊しない。実paired cache hitを親から読む回帰検査を追加し、compiler追加0で到達することを確認。

後続の共通native監査へ外部SHA付きcase-groups計画を接続。moving-groupは全15入力を[[0],[1],[2],[3..14]]の4群へ分け、重いnative3を個別に、拒否12をまとめる。比較/全raw/入力準備は省略せず、15 singleton群による準備の重複を減らす。順序/欠落/重複/bool/幅超過/異なる計画の集計を拒否し、既存uniform指定は保持。実fresh子＋既存aggregatorの全比較で検査。

固定ba760483…自身80群831制御検査成功（Windows限定cleanup1skip）、payload/全golden/501計算・保護CPU・pinned source保持。既存bounded/observer/Job ABI recordも8d72e81e…と同一。実CLIは計画SHA不一致をsource/native IO前に拒否。source ZIP13,528,926byte/SHA5433639c…、記録research/portable-prepared-parent-v2.json。旧試行のGPUは未消費なので、新sourceの修正版だけを次に確認する。実CUDA/full post/全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 GPU親処理と共通bounded stageを接続、実Windows前

prepared-runは必須paired生成cache hit/全byte CUDA・CUBIN一致/保存容量/元CPU準備認証の後だけappend-only claimを消費する。GPU子60秒/Job2GiB/BelowNormal/gate/終了直後観測は既存run_jobを再利用。親はnative battleを実行せず、成功時もsnapshot-gpu-pending-native-audit/calculation falseとして既存saved-battle-audit/audit-native-group/aggregate-native-groupsへ渡す。停止・partial claimは保持しretry不可。元run/staged-runのadmissionは不変。

共通run-gpu-packetへgpu-preparedを追加。外部snapshot/cert SHAと元準備/ローカルbinding/SDK/cache/必要時header descriptorを正確なrequestへ固定し、外側180秒/内側60秒/2GiBを維持。元129秒準備やcompileを繰り返さない。service未知の保全falseと部分計算falseを成功へ読み替えない。

固定8d72e81e…自身で72群749制御＋8群76 admission検査成功（Windows専用cleanup1skip）。実認証/claim/子/共有trace/Job parserの合成確認、失敗注入、実launch adapterのcommand/env/observer接続、stage schemaを検査。Mac実CLI負例は出力/claim無しで拒否。全golden/501計算・保護CPU・pinned source record保持。CLIはrun_job/mainだけ変更。source ZIP13,526,711byte/SHA46834653…、小記録research/portable-prepared-parent-v1.json。

次はWindowsの固定archive/短いCPU検査/Job smoke後、元未消費GPU試行を1回だけ確認する。full build/native再準備/compileは行わない。新実GPUとfresh native postは未実証で、全キャラ/特殊効果/目標も未達。以下は履歴。

# 2026-10-30 ヘッダー追補付きWindows認証成功、共通CLIのpost比較を接続

Windows固定49d90bfb…はヘッダー追補14.607秒/authority-check38.871秒が各1回成功。両方2GiB/BelowNormal/gate/終了空/欠落0、元79file不変、GPU claim/future capture無し、追加native/test/compiler/driver/GPU0。1header/44,459byteの追補とauthorityはWindowsローカルに保持する。公開328d4c28…の集計summary3089byte/manifest598byteだけMacで元bytes/SHA・元packet/base snapshot/certificateへ照合した。service未知による保全/overall falseは継続。原rawのMac独立監査ではない。拒否済みSDK path/nonce入り診断2fileは未公開。

新portable_prepared_auditを既存CLIのaudited_battle_comparison_groupへ接続し、saved-battle-audit/元audit-native-group stage/元aggregate-native-groupsを再利用する。claim三重mirror、元証拠、60秒/2GiB/ordered trace/正確なcommand/直後観測、paired生成cache hit/reflection、exact input/CUDA/CUBINを検査。部分native比較の全raw/row/strict normalizerは元compare_readbackのまま。link provenanceだけを凍結Handoffへ限定adapterし、監査前後のsource/capture/所有情報を再検査する。子は比較用input.binを元snapshotから排他的に保存する。

固定e9186899…で14群217制御検査成功、新監査15件を含む。全golden/501計算・保護CPU・pinned source record不変。CLIは分割dispatch関数以外の全関数AST不変。合成Job/transportによる検査で、実GPU/post実証ではない。小記録research/portable-prepared-native-post-v1.json。

次はpublic parentのcache/storage preflight・元準備認証・一度だけのclaim・60秒GPU子を接続し、既存bounded native群で完全独立post監査する。Windowsはidle、実GPU未消費。全キャラ/特殊効果/default受付/目標は未完了。以下は履歴。

# 2026-10-30 実snapshotでヘッダー未収録を検出、追補byte経路と子protocolを実装

Windows80c928f3…のauthority-checkは27.839秒/exit1でSDK headerのfrozen source absentとなり、CUBIN/input最終reader検査前に停止。Job2GiB/peak108,838,912byte/BelowNormal/gate/終了空・欠落0、元75file不変、authority/元とconsumerのGPU claim/future capture未作成、prepare/native/test/compile/GPU再実行0。公開済みff5ae130…のsanitized summary2415byte/manifest650byteのみ元bytes/SHAで取得。SDK絶対path/nonceを含む別診断2ファイルは自動承認レビューが具体的公開許可不足で拒否し、未公開・未取込のまま。保存manifest診断によるheader原文/同名/SHA/blob未収録の報告を修正根拠とし、原失敗を保持する。

新materialize-headersは元snapshot/certificateを変更せず、元receiptで期待されたSHAと一致するSDK headerだけを別archiveへ固定する。基底snapshot/cert SHAとexact missing header mapを束縛し、通常Handoffでもう一度全入力/CUBIN/出所を検査する。SDK資料はローカル保持で、元129秒準備/native/compile/GPUを繰り返さない。今後のprepareは既存read_verifiedでactual CUDA/header/CUBINをread set内で読む。authority/claim/内部childは追補archiveのSHAも保持・再検査する。

内部_prepared_childは元/consumer/authorityの3 claim mirror、外部claim SHA、host/source anchors/run bindingを検査し、2GiB kill-on-close Jobとstart gateで1回だけ共有executeを呼ぶ。既存file transport・SDK生成cache必須・saved CUBIN callback・native trace/stream verifierを再利用し、dispatch完了もcalculation false。再呼出しは既存journalへ追記する前に拒否。public GPU runnerと完全独立post監査は未接続、実GPUは未実行。

固定49d90bfb…自身で関連119検査（materials7/admission62/child7/stage43）と全69群719制御検査成功、Windows限定1skip。元CLI main以外全AST・全golden・455計算record/payload保持。実CLI負例は不完全storage archiveとMacでのCUDA childを拒否、claim無し。小記録research/portable-prepared-header-materials-v1.json、配布source ZIP13,509,867byte/SHA1059d613…はSDK/rawを含まない。次はWindows保存snapshotに追補を作りCPU認証だけを検証する。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 Windowsの完全CPU準備が成功、50.7MB snapshotを固定

前回printのJob制限/終了が確認済みだったため、その保全不合格を保持したまま、未実行だったcad4086f…のCPU準備だけを初めて1回実行した。既存保存staged15入力/native3とlink全chain/PTX実bytesを監査し、準備123.391秒/全stage129.006秒・exit0/timeout無しで成功。2GiB/peak290,951,168byte/BelowNormal/gate/終了空、欠落0/観測cleanup error無し。元69file不変、元GPU claim/future capture未作成、native/test/compile/driver/GPU/retry0。旧smokeのmissing1不合格は変更しない。service未知の保全/overall falseも維持する。

read set28,103＋証明書1＝28,104 inventory、unique blob4,210、snapshot50,729,955byte/SHA face629b215828058612b8bfdbbb29724ff20b8f4f9f7290f89721b76524a07f、certificate SHA72c08944af969905c76f7b514261912e87f4c0d612f826b17ed65fda29936e41。Windowsローカルnikke-prepared-admission-v1/prepare-v1/proofに保持。固定94624fdf…の小summary3337byte/manifest656byteだけ取得し、元bytes/SHA、local固定packetのmanifest/wrapper SHA、typed件数、既知input/CUBIN/receiptへ一致確認。Macはpeer summary照合までで原snapshotの独立監査ではない。research/portable-admission-preparation-peer-v2.json。

Windowsはidle。次はこの実snapshotを新reader/authority経路で検証し、元の未消費試行だけを新GPU子protocol/共有execute/独立post監査へ接続する。実行所有claimはまだ作っておらず、CPU準備成功を60秒GPU子や計算成功の証明へ昇格しない。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 元準備の認証と一度だけのclaim APIを実装

authority-checkは元Windows hostの成功済みCPU準備を既存wrapper recipe/Job/比較器で認証する。完全packet/全golden、command/base Python、子PID journal完了、2GiB/gate/終了空、欠落0/終了直後観測、元予約/transaction/nonce/外部snapshot/cert SHAを検査する。検査前後のmetadata保持も必須。サービス未知は保全falseのまま、CLIはpassive authority.jsonだけを作る。

ライブラリclaim APIは同じ認証呼出しからの一回限りhandleだけを受け、claim直前にconsumer全source/証拠/snapshot/hostを再検査する。元transaction・consumerへsnapshot-prepared-v1の新規所有記録を束縛する。書込み途中の失敗はpartialを保持しhandleを再利用しない。JSONのsuccess flagをhandleへ変換しない。実GPU runner/claim用CLIはまだ公開せず、元の実試行には触れていない。

固定80c928f3…自身で関連105検査（authority13を含むadmission62＋既存stage43）と全69群719制御検査成功、Windows限定1skip。全golden/455計算record/元CLI main以外全ASTとpayload保持。元の共通Job/観測parserで合成fixtureを検査し、実WindowsやGPUと扱わない。実CLIのMac負例はexit1/authority出力・claim無し。小記録research/portable-admission-authority-cli-v1.json、package/rawはlocalだけ。

Windows追加依頼0、前回smoke停止後の実試行を変更していない。本番準備/authority/claim/GPUは未証明。次は認証＋所有handleを新しいGPU子protocolから共有executeへ接続し、元の60秒/2GiB/gateを維持して完全独立post監査へ接続する。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 固定snapshotの検証読取と共有実行器用adapterを実装

Handoff/handoff-checkは外部archive/certificate SHA、元owner/準備controller/実行consumerの別ID、read-set全digest、完全source record/全golden、元transaction/nonce/host/input全row、CUDA原文/headerと既存static CUBIN検査を接続した。元Windows pathは開かずsnapshot bytesだけで検査する。既存compile callbackへ1回だけCUBINを渡すadapterを追加し、異なる生成CUDA・compiler fallback・二度目/無供給・途中失敗の成功化を拒否する。共有execute本体/transport/生成/効果/数値は不変。

固定dde31e0c…自身92関連検査（handoff16を含むadmission49＋既存stage43）と全69群719制御検査が成功（Windows限定1skip）、終了後payload/全golden/455計算record/元CLI main以外全AST保持。元ファイル削除後・Windows origin on Mac・共有execute＋CPU transport doubleを検査し、合成結果をGPU実証へ昇格しない。実CLI負例は既存storage-only archiveを証明書不足でexit1・成功出力無し・claim無しで拒否。小記録research/portable-admission-handoff-cli-v1.json、package/rawはlocalだけ。

Windowsは前回smoke停止のままidleで、今回の依頼/GPU0。次は完全準備と外部SHAを元の未消費試行の認証claimへ束縛し、新GPU子protocolから同じ実行器を呼び、完全な独立post監査へ接続する。reader成功は実行許可ではなく、実source-host snapshot/60秒子予算/計算一致は未証明。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 Windows短いCPU Jobは完了、保全不成立で本準備前に停止

cad4086f…のZIP/展開ID一致後、CPU printをfresh Jobで1回実行。4.956秒/exit0/10秒枠、BelowNormal/開始gate/終了空、peak7,835,648byte/2GiB、観測cleanup/inspection error無し。ただし無関係roleの既存process1件が前後で消失し原因unknown、service未識別。保全/overall false、smoke全体不合格で指示どおりprepare-admissionへ進まなかった。native/test/compile/driver/GPU/retry0、元69file不変、元GPU execution claim/future capture未作成、snapshot/certificate無し。Windowsはidleで未実行の準備を再送していない。

固定8bcc71cb…の小summary2120byteとmanifest589byteを元bytes/SHAで取り込み、local固定packetのmanifest SHA、typed件数と全scopeを照合した。Macはpeer summary照合まででWindows原Job/観測の独立監査ではない。小記録`research/portable-admission-prepared-stage-peer-v1.json`。旧smoke/元claim/失敗は保持する。Mac側で認証されたhandoff/consumerと独立post監査への接続を続け、Windowsを自動再実行しない。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 共通bounded CPU準備stageを接続、Windows実証前

prepare-admissionを既存run-gpu-packetへ接続し、正確な7field request、owner外部ID、元CPU transactionとlink/current producer対を固定。元の180秒/2GiB/BelowNormal/gate/即時観測を使い、GPU execution claimを作らない。親は証明書SHA、binding、元staged/nativeとlinked receipt、snapshot記録を照合し、GPU/compiler/native/driver非0やexecution/calculation trueを拒否。service未知を保全成功にしない。

固定cad4086f…自身76検査と全69群719制御検査が成功（Windows限定cleanup1件はMac対象外）、payload/全golden/455計算関連record保持。前版6cc80648…の実bounded負例は認証後のmissing transactionでexit1・0.739秒、失敗/専用stage claim保持、元GPU0。配布packetはresearch/windows-source-packets/prepared-admission-stage-v1.zip、13,482,329byte/SHA1548e7cf…、小記録research/portable-admission-prepared-stage-v1.json。

Windowsは既存保存証拠でCPU準備1回だけを次に依頼する。新しいnative/GPU/compileや元失敗の再実行は行わず、short CPU Job smoke成功後に元owner1e54383d…の未消費GPU試行からsnapshotを作る。実準備成功、認証claim/GPU consumer/独立post監査と102秒問題の解消はまだ未証明。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 完全なCPU監査からsnapshotを作る共通CLIを接続

`prepare-admission`は外部expected owner ID/全sourceを検査して元CLIを読み込み、元staged admitとsaved_linked_admissionをGPU禁止内でそのまま呼ぶ。同suite/全golden、cached helper同一bytes、元input receipt/実CUBIN size/SHA、全observed package closure、未消費execution claim/future captureを検査。完全receiptとread-set digestを証明書へ束縛し、既存freezeで全sourceを再検査したsnapshotを新規出力する。失敗/partialは保持し、実行所有やcaptureは作らない。準備成功もexecution_admitted/calculation false。

固定3eb93038…自身で関連29検査（準備protocol12＋readset8＋snapshot9）と既存69群719制御検査が失敗/error0（Windows限定cleanup1件はMac対象外）、終了後payloadも一致。実元owner1e54383d…の認証/import後、未存在transactionで止まるCLI負例とfailure保持も確認。元CLIのmain以外全関数AST、全golden、GPU/backend/generator/保護CPU記録は保持。小記録`research/portable-admission-prepare-cli-v1.json`。合成protocolテストはWindowsの元証拠による意味監査成功ではない。

次は準備CLIを共通bounded Windows stageへ接続して既存証拠で1回CPU検証し、そのsnapshotを認証済みclaim・共通GPU consumer・独立post監査へ接続する。60/180秒・2GiB/低優先度/gateは維持、旧claim/失敗を消さず再実行しない。Windows依頼/GPU0、102秒の準備問題はGPU段階での実測まで未解消、全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 監査の実read setを記録、固定owner全sourceを照合

`portable_admission_readset.ReadSet`は元CPU監査のPath bytes/textと既存streaming digestをそのまま実行し、消費したsize/SHA/pathだけを記録する。再読の変更・digest中の改変・captureの重複/再利用を拒否し、並列recordと例外時のreader復元を検査。元text encoding/errors/newlineを保持する。package closureは認証済みmanifestの全file記録を別検査し、任意open/subprocessを網羅したとは扱わない。native値/contextのcacheや意味監査の成功flagは作らない。

専用8+snapshot9の17検査成功。固定1e54383d…の実verify_packageと全check_recordsが元3,995file＋manifestの3,996記録へ一致し、既存snapshotへの受け渡し・作成前の改変拒否も検査。元の計算/保護CPU/GPU/golden/claimは変更0。研究小記録`research/portable-admission-readset-check-v1.json`。Windows依頼/GPU実行0。

次はこのread-setを元の完全なstaged/link admissionへ適用して、監査結果・owner・transaction・input/artifactへ束縛した証明書とinventoryを発行する。その後にsnapshot/一度だけのclaim/共通GPU consumer/独立post監査を接続する。現在はまだGPU受付・CUDA計算証明ではなく、102秒の準備問題は未解消。全キャラ/目標は未完了。以下は履歴。

# 2026-10-30 監査済み受け渡しの固定バイトストレージを共通CLIへ実装

admission-snapshot/checkをCPU専用で実装。全sourceを重複分も読んでsize/SHA検査し、content address blobをZIP保存する。受信側は外部anchor SHAで全archiveを検査し、選択payloadを展開後にもsize/SHA照合、reader終了時に全archive再検査。元Windows pathを受信Macで開かずopaque origin IDとして扱う。安全な相対path/正規manifest/完全member一覧/サイズ上限、symlink/改変/部分失敗保持を実装。metadata viewはコピーで内部bindingを変更できない。

固定633dcbb5…自身9検査＋全69群719制御検査に成功。2つの実immutable source package＋実入力7.39MB＋既存Metal archive9.91MBをCLIで往復。全7,997 sourceを4,000 blob/18,586,316byteへ保存し全byte一致。M5ストレージ検査+選択input/artifact readは0.083秒、CLI作成2.482秒/CLI検査0.209秒。これは合成transaction bindingによるストレージ試験だけで、Windowsの全admission/GPU起動時間ではない。元パッケージpayload/golden/全GPU/backend/generator/保護CPUを保持。

admission_verified/calculation_verifiedはfalse固定、GPU/compiler/native0。意味監査済みinventory生成・準備owner/transaction/claimの認証・実GPU consumer・完全な独立post監査への接続は未実装。Windowsはidleのまま、GPU execution claim未消費を保持。次は[受け渡しの接続要件](portable-prepared-admission.md)に従って、ストレージを既存監査と実行器へ接続する。小記録research/portable-admission-snapshot-cli-v1.json、raw/archiveは永続local proofのみ。目標は未完了。以下は履歴。

# 2026-10-29 起動前監査が101.644秒、60秒GPU子へは起動せず

固定1e54383d…のread-only CPU計測が全15入力/native3の最終staged admissionと保存link admissionに成功。verify6.893秒、staged34.451秒、link67.181秒、入力read/hash0.012秒、合計B+C+D101.644秒、post verify8.597秒。外側123.338秒/exit0/peak109,580,288byte・2GiB/低優先度/gate/post空/欠落0/観測cleanup error無し。全57監視ファイルは不変、GPU execution claim未消費・future capture未作成、GPU/compiler/native/test再実行0。service不明の保全/overall falseを維持する。

固定a138fa6c…の小summary2445byte/manifest444byteを元bytes/SHAで取得し、input SHA/15/native3、元exact PTX reuse receipt key、既存bounded source SHAを照合。staged final admissionはここで初めて成功したが、GPU子予算は失敗であり計算成功ではない。`research/portable-admission-budget-peer-v1.json`。

次は[監査済み受け渡しの実装要件](portable-prepared-admission.md)。全CPU準備・immutableなartifact/input/proof snapshot・GPU子・独立post監査を明示的に分離し、計算本体を共有したまま子側の繰返し監査負担を減らす。上限延長・監査省略・古いnative値cache・既存106用witness pin緩和で解決しない。新経路は未実装、Windowsはidle、GPU/CUDA計算/全キャラ/目標は未完了。旧失敗/claims/rawを保持する。以下は履歴。

# 2026-10-29 Windows全4 CPU群が成功、GPU前の監査時間を計測依頼

固定1e54383d…の残りnative1/2/3が各1回成功。全15入力（実戦3/拒否12）の群証拠が揃った。native1は112.897秒（参照53.727/静的15.797）、native2は110.275秒（参照52.624/静的15.515）、拒否群は56.770秒（静的15.529）。全Job2GiB/低優先度/gate/exit0/post空/欠落0/観測cleanup error無し。旧smoke/resume/native0の再実行、GPU/compile/native値cache/claims変更0。

固定a4349293…のsummary5354byte/manifest473byteを元bytes/SHAで取得。実戦0/1/2の全input/native指紋をsealed goldenへ一致確認し、元のGPU outputというfieldの誤称はnative_sha256へ明示訂正。件数もJSON整数で再報告し、旧summaryは保持。Macの原raw独立監査ではない。`research/portable-reviewed-controls-complete-tail-peer-v1.json`。全群完了と最終admissionは別であり、原all_native_preflight_verified=falseを保持する。

次のWindowsはimmutable packet外の小診断scriptから既存run_bounded/observe_job/observerを使い、2GiB/低優先度/gate/外180秒のread-only CPU計測1回のみ。packet自身verify_package、staged admit、保存link admission、入力read/hashをそれぞれ測る。GPU/native/Slang/compile0、GPU execution claim未消費・future GPU capture未作成・元claim不変を前後確認する。元の全監査を省略せず、60秒GPU子予算へ準備負担が収まるか調べる。GPUはまだ依頼せず、計算/保全/overall/目標は未完了。以下は履歴。

# 2026-10-29 Windowsの全制御gate・継続監査・単独native0が成功

Windows固定1e54383d…がsmoke69群719検査（142.286秒）、resume監査（62.572秒）、単独native0（116.391秒、計算55.088秒/静的入力15.846秒）で成功。全Job2GiB/BelowNormal/gate、exit0/post空/欠落0、観測cleanup error無し。全4群計画は[0]/[1]/[2]/[3..14]、元test31の証拠を保持し、旧timeout/partialを成功へ昇格しない。GPU/driver/Slang/NVRTC/native値cache/retry0、サービス未識別の保全/overall falseも維持。

固定9a27a9de…のsummary4017byte/manifest594byteを元bytes/SHAで取得し、case0のinputとnative指紋を元sealed goldenへ一致確認。peer field `native_case_0_output_sha256`はnative SHAでありGPU出力SHAではない（異なる値であることも検査）。smoke_control_testsはJSON float719.0として保持し、typed整数証明へ黙って変換しない。次のreportへ名称/型の訂正を依頼した。Macは小peer監査までで、Windows原rawの独立監査ではない。小記録`research/portable-reviewed-controls-first-native-peer-v1.json`。

同じcapsule/transactionで未実行tail1/2/3だけを各180秒以内・順番に依頼済み。GPUは未依頼。全CPU成功後も、staged admissionと保存link再監査のCPU所要時間を調べてから、60秒GPU子予算へ収まるか判断する。現在の116秒stageを60秒GPU予算の証明には使わない。元captures/claimsを保持し、計算一致/全キャラ/目標は未完了。以下は履歴。

# 2026-10-29 明示修正profile付き継続カプセルを固定

`continuation-package --repair-controls`は、SHA固定ledgerで既知owner835c8dbd…の制御監査/テスト3ファイルと追加2ファイルだけを受け付ける。元3ファイルの完全なコピーも新capsuleのresearch/control-repair-originalsへ保存し、lineageで旧ownerと照合する。任意のテスト変更を許可せず、元の全golden・GPU/native/transport/計算bytesは保持する。旧75ea…smoke失敗/元native timeout/claimsを削除・再送しない。

固定1e54383d…自身で実base lineage・旧controlコピー・関連97検査、全69群719制御検査と終了後payload一致が成功。native/Slang/GPU0。3979元ファイルは全bytes不変、3修正controlの元bytesも別保存。配布ZIP/bytes/SHA/schemaは`research/portable-continuation-reviewed-controls-v1.json`。次はWindows新rootでCPU Job smoke→resume監査→成功時のみ単独native0。reject budgetは12、計画4群、上限180秒/2GiB/低優先度/gateを維持する。Windowsの実resume/CUDA計算は未確認。以下は履歴。

# 2026-10-29 全制御gateで見つかった3件を修正、固定719検査成功

Windows75ea07e1…のsmokeは偽SDKにslangc.exeが無く、cache gate前のValueErrorで失敗。24群283件中282成功/1error、57.317秒/timeoutなし、2GiB/gate/終了空/欠落0/観測cleanup errorなし。resume/native/GPU/compile0、旧失敗とclaimを保持。固定9578c258…の小summary/manifestを元bytes/SHAで回収した。再送はしていない。

Macで同packetの全制御gateを検査すると、generation extraction監査にも2件の古い前提が残っていた。fd15fec6のappend audit3行を、全source SHAと8ca7c8ddの元sourceへ一致する明示inverseで復元してから元AST期待へ比較する。元の期待fixtureは書き換えない。またresident arcの完全なcurrent sourceが外側inverseから届いた場合だけ、同じcurrent文字列/hashとbaseline hashを検査して復元する。新しいlogical/movement inverseを二重適用しない。compiler flags/timeout/append audit変更を拒否する故障注入も追加。

偽SDKはslangc/slangc.exeを用意し、ローカルOS proxyで両方を実際に通してgate到達・native/test/Job/claim0を検査する。実OS/Metal device gateを広くmockして回避しない。計算本体・backend・Slang generator・保護CPU4ファイル・strict normalizer・全goldenは不変。

修正済み固定866522e7…自身で全69制御群719検査が成功（CPU-only smoke、native/実Slang/GPU0）、終了後payloadも一致。関連8+10検査も成功。修正3既存ファイル/2追加ファイルの元・現byte/SHAを`tests/fixtures/portable-control-fixture-repairs-v1.json`へ明示。小記録`research/portable-control-fixture-repairs-v1.json`。次はこの明示修正を新continuation capsuleへ取り込み、元計算/入力/golden/旧失敗を保持したまま全制御gateを確認する。現75ea…のsmokeを再送したり、テストを外してresumeへ進まない。Windowsは現在idle、GPU未実行。以下は履歴。

# 2026-10-29 通常ownerの同一未実行GPU用継続とnative予算を修正

既存continuation-packageは、通常payload内に元からあるhelper/testを「追加済み」として拒否した（初回失敗logを保持）。通常owner用schemaを追加し、元3controller＋2continuation helperのみ更新、元の全テストを含む他の全bytes/goldenを保持し、制御テスト1ファイルだけ追加する。compact旧経路、計算/監査関数・fresh nativeループ・入力/transport ASTの保持は変更しない。

preflight-resumeの任意`--reject-group-size`を共通wrapperにも接続。元native所属に従い実戦は1件ずつ、拒否は連続したまとまりに分ける。旧15入力はnative[0]/[1]/[2]＋拒否[3..14]の4群（全件・順序・指紋保持）、通常の1件分割15群を避ける。群計画とbudgetはtransactionへ束縛し、各stageとGPU直前に再検査。元のタイムアウト/partial returnsを成功へ昇格せず、元テスト31件の同一試行証拠を保持する。

開発/固定75ea07e1…自身各95検査、実base835c8dbd…とのlineageと前後payload保持が成功。packet/bytes/SHA/未完了は`research/portable-continuation-tail-budget-v1.json`。次のWindowsは新capsuleのCPU-only Job smoke→fresh resumeの実監査→成功時だけ最初の単独native群。GPU/compile/上限増加/旧群再送は0。以下は履歴。

# 2026-10-29 移動停止・強制移動・グループの元72定義を同時Metal検証

`moving-overlap`はユニ/ヤン/ドレイク/ニヒリスター/メアリーの元全72定義・実武器/育成/seed/30秒を保持し、同じmoving-typed/group entryへ接続した。新shader/時計/handler/ダメージ式/計算済み位置入力は0。実際に停止と強制移動が重なる区間を持つ2つの明示優先順で、typed付属物・物理命中・multi_hit通知・元子攻撃着弾まで既存全比較を行う。ゲーム規則への昇格ではない。

固定1056fb2f…のM5実GPU1回で全14入力（実戦2/拒否12）成功。GPU2.286507秒、pipeline0.003019秒、fresh CPU48.771816秒、unit32。generation/PSO必須hit、Slang0/retry0。fresh GPU禁止7群の独立seal91.457493秒成功、親native再利用/GPU0。旧current-group生成CUDA/MSL全bytes、旧拒否12入力/native指紋、既存GPU payload/保護CPU4ファイルを全保持した。raw/元失敗/claims/独立ログを永続proofへ保持。

通常sealed suiteへ登録し、両operatorの分類へ限定`current_overlap_validation`を追加。開発分類42検査、固定sealed1e2e50a3…自身7群33検査、model-check成功。公開受付/元拒否/ゲーム規則/全キャラは維持。詳細[元複合編成](portable-moving-overlap.md)、小記録`research/portable-moving-overlap-cli-v1.json`。

Windowsの旧group15は固定835c8dbd…でplanと全テスト3群31件が成功。native-group0（実戦3件を含む入力0–4）は外180秒でtimeout、183.465秒で終了しGPU0。native1/2へ進まず原proof/claimを保持する。保存ログと正式peer要約を取得してから、既存の同一未実行GPU用continuationでnative群を1入力ずつへ分割できるか検査する。再送/上限増加/再コンパイルはしない。これは新overlap14のCUDA証明でもない。以下は履歴。

# 2026-10-29 Windows実byte再利用監査成功、通常/段階実行へ出所対を接続

Windows固定24870e4d…の読み取り監査が76.435秒/exit0で成功。旧・現PTX13,556,055byteの全bytesと完全compiler identity/keyが一致し、既存CUBIN6,918,480byteを保存したまま現producerへ束縛できた。原claim変更/compiler/Slang/NVRTC/ptxas/link/driver/GPU/native/retry0。2GiB/BelowNormal/gate/終了空/欠落0、サービス保全不明は環境保全/overall false。固定93d6556d…のsummary3330byte/manifest615byteを元CRLF/SHAで取得。Mac原本chain独立監査ではない。

通常runとstaged-run、共通wrapperの両linked stageへ任意のcurrent producer対を接続し、起動前・子provider・実行後監査で同じ4-path requestを使う。freshテスト/native、transaction/claim/Job、live compiler排他は維持。開発126/固定835c8dbd…自身126検査と前後payload検査が成功。記録は`research/portable-exact-ptx-execution-pair-v1.json`。[CLI](portable-saved-linked-stage.md)。次は新固定packetでfresh staged preflight、成功後だけ短いCUDA1回とfresh独立比較。実CUDA計算/default/UI/全キャラ/目標は未完了。以下は履歴。

# 2026-10-29 旧CUBINと現PTXの実byte再利用監査を接続

新CLI `linked-reuse-audit`/共通bounded stage `audit-linked-reuse`を実装。旧object/JIT/PTXの全chainと、現sealed world producer/compile claim/Jobを別々に再監査し、実PTXの全byte・size/SHA/version/target・完全compiler identity/keyを要求する。現native全goldenとreceiver全goldenの一致も必須。旧source/link identityを保持し、追加receiptに旧/現producerを分ける。normalizedだけやhashだけの比較へ緩めず、GPU/compile/battle/fallback/原claim変更0。

開発209/固定24870e4d…自身209検査、前後payload検査が成功。Windowsでは2GiB/BelowNormal/gate/外180秒の読み取り監査1回だけを次に行う。packet/SHA/未完了は`research/portable-exact-ptx-linked-reuse-v1.json`。[監査CLI](portable-saved-linked-stage.md)。現CLIのrun/staged-runはまだcurrent producer pairをfresh transactionへ渡さないため、その接続・現CUDA実行/独立比較は未完了。default/UI/全キャラ/目標は未達。以下は履歴。

# 2026-10-29 現sourceでPTX cache再利用成功、移動停止の分類を更新

Windows固定54c70a1d…で現sourceのpaired generation25.772秒/Slang2回を準備。元生成物の実byte/normalized pairへ一致し、共通bounded PTX probeがhit（auditor0.142秒/外10.511秒）。cache/generation必須の現PTX producerも成功、内14.315秒/外25.969秒・Slang/NVRTC0。元PTX13,556,055byte/SHA e6d83bf9…/compile key ded5292f…を再利用した。全Job/gate/低優先度/2GiB/終了0/欠落0/timeout・観測cleanup error無し。service不明は保全/overall false、compile exit2/wrapper1。GPU/battle/ptxas/object/link/retry0。report固定dee9d4f2…を原bytes/SHAで取り込み、Macは小peer照合まで。`research/portable-moving-group-current-cache-peer-v2.json`。

分類にはユニの移動停止だけ`moving-group-current`の現Metal再認定を別字段で追加し、ヤンforce_moveを昇格させない。全266profile行・元定義/入力hash/拒否理由・GPU source・11系統の順位/profile/targetを保存reportと完全一致へ照合。254 packing/12失敗、canonical欠落5/default/全キャラ0は維持。開発74テストとmodel-check成功。初回固定packetは監査文書不足17error、次は旧期待JSON不足1errorで停止し、元失敗を保持。現suiteへIMPL-STATUS.mdと旧enemy-movement goldenを宣言した新b793cf12…自身で74全成功・前後payload一致。期待値/監査/テストを削っていない。`research/portable-current-movement-stop-classification-v1.json`。

次は保存object/CUBINと現producerの**実PTX bytes/全compiler identity**を監査して、再生成せず使う明示的受付を実装する。元artifact/source/claimは保存し、normalizedだけの一致やold sourceの再ラベルは禁止。現CUDA戦闘/全キャラは未完了。[cacheの範囲](portable-moving-group-cuda.md)。以下は履歴。

# 2026-10-29 PTXファイル点検を共通bounded packetへ接続

`probe-ptx-cache`は既存file-only cache-probeを全payload検査後に呼び、既存Windows Job/gate/BelowNormal/2GiB/外側180秒を再利用する。3 absolute pathの厳密request、専用stage claim、result/artifacts/観測を保持。missは有効なsnapshotでありhitとは別字段。Slang/NVRTC/driver/GPU/native battleや内側compiler Jobを起動せず、compiler/cache claimも変更しない。forged calculation/compile/GPU/cubin receiptとbool-as-int、request混同を拒否する4検査を追加。開発/固定packet自身201検査・前後payload/PTX plan/validation-deps成功。数値/GPU/旧CLI/golden変更0。

現sourceのsealed packet54c70a1d…、配布ZIP/bytes/SHA/境界は`research/portable-bounded-ptx-cache-probe-v1.json`。次のWindowsはpaired generation1回→共通bounded file-only PTX probe。元保存PTX cacheへexact hitの場合だけcache必須/NVRTC fallback禁止で現producer1回を作る。元76fbe7c3…の生成物を現sourceの成功へ再ラベルしない。object/link/GPU/native全件はこの依頼に含めない。[点検CLI](portable-cache-preflight.md)。以下は履歴。

# 2026-10-29 移動groupのJIT-link成功・現sourceのMetal再認定

Windows固定b418ed14…が元bb28af2e…の保存objectを再生成せずJIT-link成功。API0.058635秒、CUBIN6,918,480byte/SHA0f140174…、sm86/portableEvents/params48B、API9件全ret0/Destroy成功/log空。inner28.217秒/peak126,640,128byte、outer72.833秒/peak232,325,120byte、両Job2GiB/gate/低優先度/終了0/欠落0/timeout・観測cleanup error無し。nvcuda3観測未ロード、compile/GPU/battle/retry0。service未識別の保全/overall false、旧source/current equivalence falseを保持。小要約とmanifestを固定4003d701…から元CRLF/SHAで回収、Mac原本監査ではない。`research/portable-moving-group-jit-peer-v1.json`。

共通saved-linked受付は、sealed controllerと実sealed world producerを別々に監査・束縛する経路を追加。元producer全goldenと実行側全goldenの完全一致、source/generated/CUDA/header、producer manifest・controller receipt・object内producerを要求。従来full compiler経路・default/UIは保持。開発/固定3443f8bf…各125検査が成功、実Windows admissionは未確認。[受付](portable-saved-linked-stage.md)。

現GPU sourceを含む小entryも新規M5実GPU1回/全15成功、GPU2.281339秒、CPU69.944秒、generation必須hit/Slang0。Swift consumer変更で旧cacheを拒否し、新pipeline60.518秒。fresh GPU禁止8群の独立seal121.880秒成功、親native再利用/追加GPU0。旧input/output/entries/normalized pairを完全保持し、closureのみ2変更/1追加。元v1登録を監査用に保持し、`moving-group-current`/同cache-onlyを追加した。固定fa991605…自身185検査/前後payload/PTX plan成功。`research/portable-moving-group-current-metal-v2.json`。[現小entry](portable-moving-group.md)。

次は現sourceのWindows file-only PTX cache triageを先に行う。旧sourceのPTX/object/CUBINを現source成功へ再ラベルしない。現CUDA計算・実ゲーム空間規則/default/全キャラ/目標は未達。Windows全nativeを1stageへ詰めず、既存bounded groupの条件を保持する。rawと旧失敗/claimsは保存。以下は履歴。

# 2026-10-29 移動groupのWindows module-object生成に成功

新固定bb28af2e…でCPU55成功後、保存旧76fbe7c3…のPTX全13,556,055byteを分割/改変せずobject生成1回。ptxas14.446秒/code0、relocatable7,493,872byte/SHA2780dc69…、inner35.150秒/peak502,321,152byte・outer63.253秒/peak554,463,232byte。2GiB/低優先度/gate/Job後0/欠落0/観測cleanup error無し/timeout無しの報告。service未識別はpreservation/overall false、exit2/wrapper1を保持。Slang/NVRTC/driver/GPU/battle/JIT-link/直接CUBIN/retry0。

report固定7d1fd21f…の小JSON2個を元bytes/SHAで取り込み、元source packet・保存PTX識別へ一致。object/全Job原本はWindowsに保持し、Mac独立原本監査ではない。旧source由来のobject成功であり、現source/CUBIN/計算/default/全キャラは未認定。`research/portable-moving-group-module-peer-v1.json`。後段のsealed object owner→診断link接続も開発/固定b418ed14…各122検査済み、Windowsへは未依頼・追加packetはMac保持。次は保存objectからJIT-link、runtime admissionのsource/owner接続は別途必要。[経路と範囲](portable-module-object.md)。以下は履歴。

# 2026-10-29 保存sealed戦闘PTXを既存module-objectへ接続

Windows読み取りで保存PTX8.4/sm86/SHA・元producer compiler/containment・固定ptxas19,582,976byte/SHAを確認、追加compile/native tool/GPU0。過去のwhole-program直接assembly失敗とmodule-object成功を踏まえ、新しい直接assemble wrapperは増やさず、既存module-objectを使う。

共通CLIのassembly_origin/partition_object_originだけを変更し、独立sealed world battleの保存producerを専用の明示分岐で検証する。元ファイル/正本/生成物/cache/phase/Jobの監査を保持し、元compiler-only歴史検証・直接assembleの同golden条件は変更しない。新originはhistorical_sealed_battle_source=true/current_battle_equivalence_verified=false。旧compiler経路とsealed経路、不完全/非world/development・source mode混同の拒否を含む開発120/固定packet自身120検査が成功、payload前後一致。数値/GPU/golden/保護CPU変更0。

固定bb28af2e…のsource packet/出所は`research/portable-module-sealed-producer-v1.json`。現module-objectのWindows実行は未確認、JIT-linkのsealed owner接続・現CUDA計算/default/全キャラ/目標は未完了。[経路](portable-module-object.md)。以下は履歴。

# 2026-10-29 同じ移動group sourceのPTX単独生成がWindowsで成功

元固定76fbe7c3…の別PTX工程は成功。Windows小要約＋manifestを固定edc2c550…から取得し、元bytes/SHA/package ID・前回paired raw生成/hash/cache key・M5 sealed normalized生成との一致をMacで確認。PTX13,556,055byte（e6d83bf9…）、NVRTC1回35.541秒/code0、generation必須hit/Slang0。inner51.799秒/peak289,640,448byte、outer65.379秒/peak324,009,984byte、両方timeoutなし・2GiB/低優先度/gate/Job終了0/欠落0/観測cleanup error無しの報告。サービス未識別は保全false/overall false、外child exit2/wrapper exit1を保持する。

PTX/全Job原本はWindowsに保持し、Macの独立原本監査ではない。ptxas/driver/GPU/native/旧CUBIN再試行0。これでNVRTC frontendからPTXまでを分離できたが、別assemblerのメモリ改善・CUBIN/現在のCUDA計算・全目標は未証明。次は保存PTX8.4/sm86と固定assemblerの読み取り検査から進む。証跡`research/portable-moving-group-ptx-checkpoint-v1.json`、[共通経路と境界](portable-moving-group-cuda.md)。以下は履歴。

# 2026-10-29 消費済みcompile claimを計画時に検出し、別PTX工程へ

共通`compile-plan`は既存claim（壊れたsymlinkを含む）を読み取り確認し、`execution_claim_available=false`/`passed=false`で止める。artifact変更でも同じpacketのclaimを再使用しない。実行時の排他的claim/監査/数値/GPU/golden/保護CPU4fileは変更0、CLIの既存top-level定義変更はcompile_planだけ。開発側119検査、現source基準の固定fd7de6c1…自身compiler70検査とPTX/2GiB/60秒planが成功。旧small基準での固定はsource closure staleとして拒否され、goldenを書き換えず現moving-many基準で固定した。証跡`research/portable-compile-plan-claim-v1.json`。

Windowsへは別artifactのPTX単独生成を1回だけ依頼。元不変ZIP/package76fbe7c3…を新しいnikke-moving-group-ptx-v1へ展開し、旧CUBIN失敗/claimsを保持。既存paired generation必須hit/Slang0、2GiB/BelowNormal/fresh Job/gate/child60秒/outer180秒、native/driver/ptxas/GPU0。Macの元packet ownCLIでplan成功、Windows側もplan成功まで確認、実結果は待機中。NVRTC終了後の別assemblerでメモリを減らせるかは未検証で、後段への自動移行は依頼しない。全キャラ/default/全目標未達。

# 2026-10-29 未対応の優先順とWindowsのコンパイル失敗を保存

共通`entry-plan`は保存entry-inventoryを再準備せず、operator/複数target間の同じprofileを重複除去して影響数順に並べる。元266行/全入力hash/GPU sourceを保持、254 packing/12失敗/11系統。最大はベイ4段階で、all_allies/self_coverを8件に水増ししない。scoped Metal/CUDA記録は残し、current_source_revalidated/calculation/default/全キャラはfalse。約693KBの報告からstdout5650byteへ短縮。新規7含む116検査成功、固定f756da39…自身のCLIでも開発側と完全同じplan JSON、payload前後検査成功。旧CLIはmain以外の全function/class AST同一、数値/GPU/保護CPU4file/golden変更0。[次のoperator選択](portable-shared-entry-inventory.md)。

ベイの公開比率表は本人:他=8:3という候補を人数別に支持するが、cover262候補は1人時の表97.03%と最近接丸め97.04%が一致しない。元の規格未定/拒否は維持し、根拠無しから公開候補と未確定の分離へ分類を更新した。正確なcover演算・layer/通知・死亡/復活/再burst・favorite全段階が次の契約。[公開資料の境界](portable-bay-allocation.md)。

Windows固定76fbe7c3…では59テストとpaired CUDA/MSL生成が成功（35.371/26.374秒）。source/strict normalized pairはM5基準と一致。generation cacheを必須再利用したCUBIN/O1・2GiB/child60秒/outer180秒の1回は、NVRTC42.638秒・code6、ptxas Memory allocation failure。CUBIN無し、GPU/driver/native全件0、追加compile/再試行0、Job残存/既存process欠落/観測error0。Job capとsystem memoryの原因切分けは未確定。元claim/ログは保持し、個人pathを含む元stderrを共有せず、要約＋診断excerptだけ取得した。サービス未識別の保全/overall=false。[保存結果・出所・次の分離assembler計画](portable-moving-group-cuda.md)。以下は履歴。

# 2026-10-29 最大127ADD・30秒を同じ実行器でMetal検証

最新sealed `moving-many`は元ユニ＋ニヒリスター全71定義/元武器・育成/5人編成/30秒を保持し、BODY＋127ADDを処理する。2体を射線付近、125体を遠方に置き、全127体の元移動carrierと全228727frame/228854区間・最終状態・全paddingを比較する。同時127体命中の認定ではない。従来4096行では拒否された3体以上に対応するため、既存本体をincludeするだけの新entryと262144行ずつのframe/segment bankを追加。input123188wordは同じ、output10422672word。元のskill/typed/group/history容量は削らず、旧layoutの既定byteも保持する。

固定b44a5f39…のM5実GPU1回で全13入力（native1/拒否12）一致。GPU42.869923秒/初回PSO61.194543秒、generation必須hit/Slang0。別fresh GPU禁止child7群の独立sealは160.209秒、全群180秒以内で成功。元の実通知9回・子着弾27回・typed着弾50件と元全battle比較も保持。raw/CPU snapshot/claimsを永続proof rootへ保存。小証跡 `tests/fixtures/moving-many-metal-v1.json`。[容量・境界・共通CLI](portable-moving-many.md)。

`moving-many-cache-only`は同じ計算に既存CUBIN/O1とpaired generation必須を適用し、固定e5c5ce5b…のcompile-plan（2GiB/60秒）は成功。現CUDA/実ゲーム空間規則/同時多数命中/BODY・PART移動/default/全キャラは未認定。Windows新依頼0。共有7fileはexact inverseで旧sourceを保持し、旧小entryの生成CUDA/Metalは既存strict normalized hashと一致したが、旧suiteのcurrent-source GPU再認定とは区別する。以下は履歴。

# 2026-10-29 移動中の実グループconsumerを同じMetal実行器で検証

最新のsealed `moving-group`は元ユニ＋ニヒリスターを同じ元5人編成（全71定義・元武器/育成・30秒）へ接続する。移動/範囲外/再出現の3戦闘＋拒否12。各20group、元`multi_hit:2`→`버닝 샷 3`の通知9/0/17・子着弾27/0/51が実発動。CPUで移動fieldsだけを外すと通知9→5・子着弾27→15となる。GPU source276ファイルは直前のmoving-typedと全byte同一で、元全比較文をAST同一の共通関数へ抽出し、計算を複製していない。

固定b6729852…のM5実GPU1回で全15一致（GPU2.281622秒、PSO0.003021秒、generation/pipeline必須hit、Slang0）。別fresh GPU禁止child8群の独立sealも123.327秒で成功、全raw/旧失敗/claims保持。通常`moving-group`と同じ計算の`moving-group-cache-only`を登録し、現CUDAは未確認。小証跡は `tests/fixtures/moving-group-metal-v1.json`。[範囲・負例・次のCLI](portable-moving-group.md)。3ADD以上の30秒容量、他キャラ/全条件、PART/BODY移動、実ゲーム空間規則/default/全キャラは残る。Windows新依頼0。以下は履歴。

# 2026-10-29 移動するADDとtyped物理対象を共通実行器でMetal検証

最新はsealed `moving-typed`。元ユニ69/ヤン71/混合69定義・30秒を維持した6戦闘＋拒否12入力をM5 GPU1回（3.094098秒）とfresh独立sealで全比較。既存clock/actor世代/carrierと1つのcanonical pelletを共有し、宣言した所有者へのshape並進・死亡・再出現を処理する。全移動frame/区間、既存battle/typed/skill/group比較、最後のaim中心を検査する。実group consumerが無い元編成の空履歴を発動実証へ読み替えない。ゲーム実機の付属物モデル、空間recipient、default/全キャラは未認定。[設計・失敗保持・証跡](portable-moving-typed.md)。

関連118テスト、通常packet自身26テスト成功。`moving-typed-cache-only`も同じ計算payloadを保持し、既存CUBIN/O1・paired generation必須へ接続。固定011db4de…自身54テストと2GiB/60秒compile-plan成功、Windows追加依頼/GPU/コンパイル0。現CUDA統合検証は未完了。次は元group consumerとの合成とactor数拡張を優先し、Windowsの全件nativeはMacでも162秒なので既存staged groupで分割する。rawと旧失敗claimは永続proof rootへ保持。以下は履歴。

# 2026-10-29 未対応の敵移動へ着手：元5戦闘CPU契約とMetal数値核

移動停止/強制移動を、元ユニ69/ヤン71/混合69定義の全実編成を保持したCPU契約へ接続した。既存native frame、実duration carrier（5秒/2秒）、generation-aware enemy fields、ADDコライダー、元sampled shot/landing/ダメージを使う。期限内分割・世代再初期化・同時状態の明示優先順位・scope復元・overflowを9検査で確認。consumerだけを除く故障注入で、同じ元定義の実packet/ADDダメージが変わる。`reference --suite enemy-movement-common`は5ケースを約4.095秒で成功し、GPU/packing0。速度/強制移動先/優先順位は宣言値で、recipientは正本のall-in-range近似を必須明示する。ゲーム軌跡、真の空間recipient、BODY等、GPU戦闘consumerは未完了。

新しい共通`enemyMovementStep`はsoftware binary64の順序付き演算のみ。43入力（native34・raw拒否9、overflow status16 witness2件）はM5 GPU1回で全2752byteを取得。GPU0.0000236秒/MSL0.0464秒/PSO0.0308秒。初回はstandaloneにresident generation-cacheを指定してclaim前に拒否、ログ保持。正しい起動のGPU値は正しかったが、status16を従来native正例0固定の監査器が拒否した。source限定/契約名固定の`portable_native_status`を追加し、旧battle既定0・未知status/bool拒否を保持。数値/status/期待値を書き換えず、immutable ff646ff2で元captureをreplay、fresh独立seal0.508秒成功。元GPU claim/失敗/raw保持、追加GPU0。sealed goldenを通常`enemy-movement-math`へ登録。CUDA/Windows新依頼0。

証跡`tests/fixtures/enemy-movement-math-metal-v1.json`、raw/packet/全ログ/元CPU reportは永続`.portable-recovery/proofs/enemy-movement-20261029`。元439 GPUファイル/保護CPU4ファイル/strict normalizer全byte不変。既存106/appendの証拠やhashは更新しない。未対応分類は宣言CPU契約と数値核だけを別記し、canonical不足5/20model gap/全キャラ0/UI CPU/公開受付falseを維持する。次は既存Runtimeのalive/end/actorFieldMember/source clockと動的ADD位置・元5戦闘の全比較を結ぶ。数値核を戦闘GPU接続済みとしない。[敵移動の範囲と次段階](portable-enemy-movement.md)。以下は履歴。

# 2026-10-29 現CUDA全106入力をfresh native/wire envelopeで認定

共通CLI `partitioned-witness-join`を実装し、固定proof SHA・元own packet・context/plan/anchors・14fresh群・全106/native63/拒否43・全input/raw/logical/generated/native指紋と保持Metal rawを再検査した。immutable packet e38b399c自身の72検査とjoinが成功。source-hostで原CUDA出力を再読したenvelopeとMacのbyte-identical Metal witnessに対するfresh native比較が揃い、**固定106入力のcalculation=true**になった。原CUDA rawをMacで取得/再読したとは主張せず、peer受領の境界を結果に保存する。元中間capture/claim/失敗/pendingは変更0、追加GPU/compile/native再計算はjoin中0。証跡`tests/fixtures/resident-current-cuda-native-join-v1.json`/SHA6cf83185…。共通判定は[保存結果監査](portable-identical-wire-native-audit.md)。

Windowsの正常承認下で70検査8.115秒、validation-depsインストール0、原captureのCPU監査42.219秒で成功。7launch/106readback引数、exact CUBIN、全875MBとprepared/claim/ledger/processを検査。原GPU実行をやり直していない。固定report2d0d24e2094ab6b1bed518c7b1d41969cffa4128/codex/cuda-resident-envelope-v1-reportの非個人JSON1883byte/SHA6648e2c8…だけを取得。sandbox TEMP/hardlinkの旧2失敗は保持し、OS/ACL/テストの緩和なし。サービス未識別により原/監査の環境保全とoverallはfalseを維持する。

未対応分類と`model-check --summary`はhistorical frames/append/wireを保持し、別joined proofで106入力の計算true・native pending false・環境false・Mac原CUDA未読を表示する。5 canonical consumer/20model gap/全キャラ0/UI CPU/公開受付falseは継続。次は保存結果監査の再実行を重ねず、未対応の移動状態/物理producer等の不足モデルを優先する。Lock Onの距離式は公開情報で確定できず保留。以下は履歴。

# 2026-10-29 同一byte witnessの全106 fresh native監査成功

共通`portable_partitioned_native.compare_readback`へ既存native/rejection比較ループを抽出し、元Metal入口も同じ関数を使用。`partitioned-witness-native-audit`は元Metal captureを既存address auditorで全byte再監査し、現CUDAの固定要約と全raw/論理SHAを照合する。現source/golden/native/input/paired generationを維持し、現Metalのseal前development packetの期待は正確なinput/source/native projectionで検査する。出力欄を捏造してsealed扱いしない。新packet v2/9c2b84fd自身の67検査とvalidation-depsが成功、14個のfresh GPU禁止childで全106（native63/拒否43）を549.815秒で独立照合した。全元entry/native/出力を保持、追加GPU0。元875MBをコピー/書換えせず、raw/失敗/claimと全group logsは永続Bへ保持。証跡[Mac native witness](../research/target-count-query-evidence/resident-current-native-witness-v1.json)。v1 packetはgeneration元がdevelopmentであることを静的点検で検出し、監査未実行で保持。

`witness_calculation_verified=true`はMetal由来の同一byte witnessへのfresh native一致。CUDA原captureをMacで取得/独立再読したとは呼ばず、`calculation_verified=false`・原CUDA envelope監査pendingを維持。共通CLIのWindows専用`partitioned-current-envelope-audit`は、既存Job/BelowNormal/2GiB/180秒とGPU/compiler禁止guardで原source/paired generation/loaded CUBIN/input/ABI全trace/claims/process観測を再監査するCPU入口。native戦闘0、元GPU claim/ledger不変。両証拠のjoinはまだ未実装/未認定で、片方の結果を成功へ昇格しない。

60dc9d09で関連70/CLI51検査が成功し、source-only packet22762b5e（ZIP11,066,142byte/SHA002aa6ca…）を固定c50e17e2/codex/cuda-resident-envelope-v1-sourceへ共有。Windows事前70検査は最初sandbox TEMP拒否（0.474秒/93errors）、所有TEMPを固定した次は基本操作が成功したがhardlinkがsandbox拒否（約10.07秒）で停止。validation-deps/envelope/GPUは未実行。計算失敗や原CUDA claim消費と混同しない。元失敗を保持し、通常承認経路でCPU検査だけを行う依頼を送った。OS/ACL/guard/テストを緩めず、拒否時は停止する。Windows結果は未取得なので重複実行を依頼しない。

次はWindowsの既存依頼結果を取得し、原出力envelopeとMac fresh native witnessの全106/63・input/raw/logical/generated/sourceを共通joinで結ぶ。保全/overallと計算の認定を分離し、service未識別はfalseを維持。未対応5 canonical consumer/20model gap/全キャラ0/UI CPU/公開受付falseは継続。実装と証拠境界は[保存結果監査](portable-identical-wire-native-audit.md)。以下は履歴。

# 2026-10-29 現ソースCUDA全106入力のwire一致・共通CLIへ記録

`partitioned-current-package`を実装し、現Metal独立sealと元physical wire参照を別々にpinした。旧失敗回収ownerは保持し、既存の分割transport・linked artifact admission・Job・ABI観測を再利用。新ownerは元PTX/object/linkをCPU準備で一度監査し、実行直前には小さいreceipt anchorsと全input/source/header/CUBINを確認する。fallback compile/linkなし、source/goldenの除外なし。保存容量はGPU claim/ledger作成前に確認する。全106/native63、488 GPU/canonical/upstream/normalizerファイル、元CLIのmain以外のASTを保持した。詳細[現ソースCUDA owner](portable-current-source-cuda-owner.md)。

固定packet b873a58c（source806e01dc）のWindows実行は、smoke47検査15.70秒、全106入力のfresh静的準備41.20秒、GPU stage28.92秒で成功。launch/sync各7、readback106、driver失敗0。875,469,264byteの全rawとlogical SHAが参照と一致し、生成cache必須hit・compiler/link0。低優先度/2GiB/GPU60秒を保持し追加GPU実行は不要。元raw/claim/全receiptはWindowsに保持し、Macは固定b3c989d1の1637byte要約のみ取得。process保持true、service未識別のpreservation/overall false、calculation false・fresh独立native監査pendingを維持する。

Macでは保持済みMetal rawをsource-pinned address viewで全106行再照合し、Windows要約のraw SHAとも一致した（1.124秒、20参照/5アドレス移動）。これはMetal由来の同一byte witnessであり、CUDA原captureの取得/独立監査とは呼ばない。fresh native再計算0。次は元出力を再実行せず、共通native比較器の保存結果入口を現ownerへ接続し、全63 native＋43拒否を独立監査する。Windowsで長い正本計算を常駐させず、Macのbyte witnessとWindows原captureの証拠境界を保持する。

共通CLI `model-check --summary`と未対応分類へwire106成功/計算false/pendingを別字段で表示。partitioned63/readiness25/model-gap14/CLI51検査、model-check成功。5 canonical consumer/20model gap/全キャラ0/UI CPU/公開受付falseは未完了。証跡[checkpoint](../research/target-count-query-evidence/resident-current-cuda-v2-checkpoint.json)、固定Windows要約`tests/fixtures/resident-current-cuda-v2-summary.json`。Lock On公開調査は照準線基準までを採用し、中心/外形/2D/3D/tie/PARTは未確定のまま。他機能の開発を実機提供待ちで止めない。以下は履歴。

# 2026-10-29 現full PTX生成成功・未対応分類へstorage証拠を接続

compiler v2はsource stale負例テストのsynthetic inventoryにCPU audit fixtureが無く、Windows6群72検査の1失敗で停止。production guardは変更せず、そのunitだけCPU suite/smoke/native payload検証を隔離して本来のstale source拒否を検査した。v3/babcd09cはv2とtest1ファイルだけの差で、GPU/全golden/consumerは同一。packet自身の20群210検査がMac/Windowsで成功。元失敗/capture/claimは保持。

v3固定source3fca564fで現full CUDA/Metal生成がv2 certificateと一致し、PTX生成とcompiler検証が成功。NVRTC処理37.187秒（peer最終報告）、compile子50.899秒／外61.776秒、PTX12,934,766byte/SHA a50f1d53…。driver/GPU0。生成cacheはcompile時必須hit。環境保全・overallはservice未識別でfalseのまま。Windowsの34 metadataファイルはauto-reviewで共有拒否され、再送せず、path/PID/環境情報を除いた29key/1362byteの単一要約だけを別orphan branchへ共有した。固定615e1944/codex/cuda-resident-frames-v3-public-summary。拒否34fileとae599c8c/原PTXはWindows保持。Macではpackage/entry/厳密正規化生成hashの一致を確認したが、元34fileの独立監査とは主張しない。証跡resident-frames-current-ptx-v3.json。

保存PTX全体のmodule-objectは成功。固定ptxas12.4.131/--compile-only/O1/sm86/FMA無効、元12,934,766byteを保持し7,179,120byteのobjectを生成。native14.274秒/ret0、子29.834秒/外50.439秒、timeoutなし、object/containment true、preservation/overall/calculation false。Slang/NVRTC/driver/GPU0。単一要約7dc6ff2a/codex/cuda-resident-frames-v3-object-summaryを取得し、PTX SHA/bytes/packageが直前compiler要約と一致。元object/JobのMac独立監査とは呼ばない。証跡resident-frames-current-object-v3.json。

同じobjectからjit-link-objectも成功。固定nvJitLink12.4.127、API9回ret0/API計0.057221秒、CUBIN6,639,440byte/SHA43de2ec9…。子19.148秒／外49.471秒、link/containment true、preservation/overall/calculation false、compiler/driver/GPU0。通常cacheへは登録しない。固定要約e6707dc4/codex/cuda-resident-frames-v3-link-summaryを取得し、直前object要約とSHA/bytes/package一致。原CUBIN・全receipt・claimはWindowsのroot/jit-link/proofに保持。リンク済みCUBINの監査元packageは同root/package。証跡resident-frames-current-link-v3.json。

次は全106のfresh CPU準備と保存CUBIN admissionを通して、既存の低メモリ分割ファイル転送でCUDA全出力を照合する。CUBINを再compile/linkしない。normal sealed battle package ba3189a6（B/resident-frames-cuda-battle-v3.zip/-package、2463files、ZIP11,016,876byte/SHA55ceaf48…）をMacで準備し、packet自身のverifyと、全106のfresh Metal golden／PTX正規化基準との完全一致まで確認した。Windowsへは未配布・未実行、fresh CPU preflight未実行。v2作成はv2 source certificateの梱包依存漏れでdevice0停止し、frame本体/短縮profileのsupport_filesを同じCPU_AUDIT_FILESから取得する修正と9検査/CLI51で解消。生成/数値/保護CPU/normalizerは変更0。元失敗log保持。今後のGPU結果はまだ未認定なので、全キャラ/公開受付を開かない。

共通portable_resident_validationをmodel-gap監査とreference work laneへ接続し、Metal106とCUDA append9を別のpinned proofとして表示。model-check --summaryはappend計算trueとstage/環境保全false・full CUDA battle falseを同時に表示する。proof fixtureのSHAと全106/9のscope、両consumer一致を検査。readiness25/model-gap14/CPU batch19/CLI51/projection9成功。source closureは実監査済みframes v2と同一、追加GPU0。5 canonical consumer/20model gap/全キャラ0/UI CPU/公開受付falseは不変。証跡resident-storage-routing-v1.json。以下は履歴。

# 2026-10-29 Resident配列追加3箇所を修正・CUDA/Metal9契約一致・Metal全106独立一致

fd15fec6の共有markEntry／initializeHPWatchesを「格納→加算」へ変更。旧CUDAが加算後indexを再読する3箇所を修正し、既存生成器とpaired cache読込へ生成順guardを接続。空／最終512／refresh／owner重複／全2048watchを、実共有関数の9入力でCUDA/Metal全word一致。新gpu-cached wrapperは保存source・SDK・両cacheの4キーを固定し、CUBIN O1／必須hit／Job／2GiB／180秒・子60秒を保持する。

Windows固定report 7f2e988fのcalculation/containment true、process保持true・missing0。Slang/NVRTC0、launch/sync/readback各1、host dispatch0.328秒、GPU子11.219秒／外32.371秒。service未識別のpreservation／全体passed／transport_verified falseを保持する。元v1の引数欠落失敗とclaimは残し、GPU再実行ではなく新wrapperの初回実GPUだけを実施。全battle/全キャラのCUDA成功ではない。出所・全指紋はresident-append-cross-gpu-v1.json。

現sourceのcoordinate-resident-frames全106（native63／拒否43）もM5で1回成功、14個のfresh GPU禁止childの独立seal成功。全旧entry/input/output/native指紋を保持。GPU4.134秒／cold pipeline62.416秒、CPU正本430.231秒、unit114.828秒、独立監査582.646秒。約875MBの全raw、旧golden、失敗を保持。独立group logsは永続Bへ全byte照合して保存、元tempも削除していない。新v2 goldenと同じfresh監査から既存certificate helperで作成したsource-only証明書を登録し、旧v1は保持。証明書はCUDA compile/cache/実計算の認定ではない。証跡resident-append-full106-metal-v1.json、詳細portable-resident-append-publication.md。

現full sourceのcompiler-only packet20d328a5をb7ff2c64/codex/cuda-resident-frames-v2-sourceへ共有し、既存Windowsチャットへtests→generation→PTXのみ1回を依頼済み。新rootはC:/Users/owner/Documents/Codex/nikke-resident-frames-v2。内compile60秒／外180秒／2GiB、driver/GPU0、fallback/retry禁止。結果は未取得なので再送せず既存turnを確認する。own compile-planのPTX＋O1指定はpolicy拒否を保持し、O1指定なしの新receiptが成功。パッケージ/transport/要求範囲はresident-frame-current-compiler-packet-v2.json。

次は現full sourceのCUDA接続を既存の限定compiler段階で進め、保存済み旧106 CUDA失敗との差分を再評価する。大きい本体を無制限に再compileしない。今回の9probeとMetal106だけで未対応分類を消さない。5 canonical consumer欠落／20model gap／全キャラ0／UI CPU／公開受付falseを維持。Lock Onは公開記述を根拠に取得・解除を進め、距離式は未確定のまま、実機環境の回答待ちでは止めない。以下は履歴。

# 2026-10-29 CUDAの更新前scalar消失を2箇所修正・Metal3ケース独立一致

保存CUDAの厳密生成基準2380f6f3…と一致するコードで2つの具体的な差を確認した。通常回復のbefore HPがCUDAでは更新後HPの再読となり累積回復が0になる。findCarrierの後置incrementも更新後countを配列index/戻り値へ使う。Metalには更新前の値が残る。共通SlangのbodyHPBeforeHeal/carrierCountBeforeAllocateというnoinline scalar境界で修正した。本修正のGPU差分はevent_runtime/carrier_runtimeの2file。正本4file/厳密normalizer/wire/runtime_init shaderは変更0。現在の開発closureを使うので、旧凍結ownerとの全source一致は主張しない。

固定v5/8c87f24bの元ミサトHP・owner/body・owner/addsの3ケースがM5 Metalで成功し、別fresh GPU禁止sealも成功（45.438秒）。入力/全native期待は旧106の対応3件と完全一致。own28群179検査115.022秒、CPU全3照合39.586秒、実GPU2.317秒、冷pipeline62.332秒/library2.216秒、child84.573秒。generation必須hit/Slang0、pipelineを永続cacheへ保存。現在のapp/gpu/scripts全1222fileは実行済みpacketとbyte一致。root CLIテストだけ後からsynthetic data依存へ追従して51成功、計算codeは不変。

選択3件の全outputは既存source-pinned typed address viewで旧Metal基準と完全一致。ミサトだけcorpus位置9→0のDFS receipt参照1wordが変わり、既存4file ABI/receipt ID/boundsを検査したRAM内viewで全word一致した。rawは変更せず、最初のraw-only差分記録も保持。元875MB CUDA失敗・claims・goldenを変更/再実行しない。

生成時とgeneration cache pair再検査へ2箇所のsnapshot→更新→利用監査を接続し、実生成断片の負例テストを追加した。これは全生成codeが安全という認定ではない。追加静的確認で、v5 CUDAのmarkEntryにenemyBuffRows/infiniteRowsの後置incrementも更新後indexを使うことを発見した。Metal側は更新前indexを保持している。次はこの2つと他の更新前値の利用を監査・修正してからCUDA compile/runへ進むこと。v5をWindowsへ送らず、Windows新依頼0。現在の3件Metal成功をCUDAや全106/全キャラへ拡大しない。

v2はcompactで旧inverse接続が欠落、v3は未追跡の新fixtureがtracked whitelistに入らず、v4は共通initializer生成器が既存Lock用optional宣言を未認識で停止。すべて失敗/packetを保持しdevice0。厳密inverseをcompactでも必ず接続し、fixture2件をGit登録＋AUDIT_FILESへ明示した。既知optional宣言は専用initializeGenerationLocks/initializePhysicalLocksが全fieldを初期化することを確認して、共通generatorからexact blockだけを分離した。runtime_init全byte一致を保持し未知guardの拒否は維持する。最終v5のみdevice1回。

model-checkは成功。差分80pathはevent_runtime/carrier_runtimeのsource SHAだけで、5つの未実装canonical consumer/20model gap/全キャラ0/UI CPU/公開受付Falseは不変。証跡resident-scalar-snapshot-root-causes-v1.json、原本B/resident-scalar-snapshot-v5-metal、independent/sealed/logical-retentionも同proof root。以下は履歴。

# 2026-10-29 保存CUDA差分をCPUだけで23ケースへ限定

共通CLIに`partitioned-saved-index`と`partitioned-index-compare`を追加。既存hash helper/source-pinned address view/Job監査を再利用し、旧raw・失敗判定・claimsを変更しない。Windows index15.582秒、詳細13.713秒、GPU/compile/native追加0。固定report8c349c2cとa2a2a2e1からmetadataだけを取得した。全106statusはMetalと一致、83行は論理全byte一致、差分23行/191個64KiBページ/315個4KiB block。最大8ケースの8192uint32を輸送し、Macで全875MB参照/row/sample SHAを検査してword比較した。

最初のミサトHP照会の累積healingはMetal283571/282542/282456/281928/280623対CUDA全0。addsケースのcarrier pass49/50はslot71/72が入れ替わり、抽出範囲の他fieldは一致。owner/bodyなどにはtotal damageの差もある。これは一律ULP差ではないが、原因をcompiler/alias/初期化と断定できない。slot差を除外・正規化せず、厳密比較は失敗のまま。次はこの保存差分と共通health/carrier/typed owner経路を照合し、原因を限定した上で共有shader修正を設計すること。旧GPUの再送・再compile・上限増加は行わない。

診断完了は計算成功ではない。共通CLIの比較exit0でもall_logical_rows_equal=False/calculation_verified=Falseを読む。原本B/partitioned-details-windows-v1-report、CPU比較B/partitioned-index-word-comparison-v2.json。詳細[分割転送](portable-partitioned-file-transport.md)、記録partitioned-cuda-saved-word-diagnosis-v1.json。公開GPU/全キャラ/全特殊効果は未達。以下は履歴。

# 2026-10-29 CUDA全106の実API成功・出力差分を検出（再実行禁止）

固定e2f6470d/2166file、source固定24c11faaの単発CUDA ownerを実装。固定97e9477e CPU監査と独立Metal/native参照ca3c24a8を結合し、fresh静的input再構築とsource/header/CUBIN照合を維持する。約127秒の元producer監査をGPU子で繰り返さない。新しい専用claimと旧失敗・claimに結ぶ安定ledgerで重複実行を拒否。旧claim/ledgerは保持。元2147file/既存CLI関数/全goldenを保持し、shader/正本/厳密normalizer変更0。own52＋checkout129テスト、Mac CPU smoke成功。

Windows smoke8.246秒/prepare42.079秒/実GPU27.561秒、各1回・timeout0。GPUの全7launch/syncと106 chunk readback、context destroyは成功、全CUDA return0。実grid16×6＋10/block1、入力7403524/output132146304/runtime2288768byteを実引数で確認。GPU Job peak1874407424byte/2GiB以下・post0。旧code2は今回再発しなかったが原因の断定はしない。生成cache hit・Slang/NVRTC/native戦闘0。smokeで既存7process消失が観測され原因unknown、prepare/GPUはprocess保持True。サービス未確認で環境保持False。

一方、全875469264byteのCUDA raw SHA bc59f8bb…は分割Metal0a737874…と異なり、論理viewも旧4ecc755e…と不一致。共通transportはstrict検査で例外を出し、元stageはFalse・計算未認定のまま保存した。CUDA logical SHA自体は旧失敗controllerが保存しておらず未知。部分/全7batch/output/input/claim/ledgerを保持し、GPU再実行/再compile/上限増加は行わない。

Windows report固定d48d5050の38file/360328byteをMacへ取得。全phaseは末尾の出力検査RuntimeErrorで失敗のまま。同じ監査器で、明示的にそのenclosing failureを保持したAPI-prefix projectionだけを検査し、全7実引数/API/stream/cleanupを確認した。これはhardware completionの証拠であり、whole trace・計算検証の成功へ置換しない。詳細partitioned-cuda-single-attempt-v1.json、原本B/partitioned-cuda-windows-v1-report、API projectionはB/partitioned-cuda-v1-api-projection.json。

次は保存済みCUDAの全row/status/logical hashとMetalの差分をCPU-onlyで特定すること。GPUを再送しない。今後の共通transportには、失敗直前に既に計算済みのaddress-view JSONを保存する診断改善と負例testを追加したが、旧captureは編集しない。旧source固定106の比較であり、現全suite・全char/効果・公開GPUは未達。以下は履歴。

# 2026-10-29 実CUDA引数の共通観測・Windows元admit/CUBIN再監査成功

共通partitioned transportへ任意のcuda_argument_journalを接続。元NativeFunctionへ同じ引数objectを一度だけ渡し、3allocationの実byte/address、input/48byte定数ABI、各grid/block/shared/streamを検査する。NVRTC fallbackや元API観測なしのdriverを拒否し、実観測のないbackendは完成outputを公開しない。sequence traceのrequire_arguments=Trueが各receiptと実API境界を照合する。計算/Slang/正本/厳密normalizerは変更0。実CUDAでの引数認定はまだ行っていない。

元66c50b92のadmitをbounded再評価する入口がなく、最初のWindows読み取りはmetadataだけ取得して停止した。新CPU-only entry partitioned-origin-smoke/auditを追加し、既存run_job/start gate/BelowNormal/2GiB・旧admit/saved_linked_admission・Job/snapshot監査・native出力probeを再利用。新GPU claim/ledger/実行許可は発行0。

固定97e9477e/2161file、source branch codex/cuda-partitioned-origin-v1-source commit11b1719e。元2147file・既存CLI関数・全goldenを保持、own42＋checkout119テスト、Mac CPU smokeが成功。Windows smokeは11.202秒、元admit/CUBIN監査は155.448秒（子のreadonly再評価127.033秒）で成功。双方exit0/timeoutなし/Job post0/cleanup・観測error0、2GiBとstart gateを確認。CPU監査Job peak153800704byteはGPU実行時のmemory測定ではない。元106/native63のadmissionを再評価し、6,636,880byteの同じCUBIN（70fff521…）と旧phase172803byte/fc933ba9…、全32API境界、旧claim/ledgerの保持を確認した。GPU/compiler/native戦闘追加0。process保持True、service識別未確認でenvironment=Falseを維持する。

保存結果15file/166606byteをreport branch固定cc75ccefから取得。Macで同じJob監査器・元失敗sequence・linked receipt keyと全golden一致を再検査した。環境raw snapshotは転送せず、source-host結果を保持する。詳細portable-partitioned-file-transport.md、証跡partitioned-cuda-origin-v1.json、原本B/partitioned-origin-windows-v1-report。

次はこのCPU receiptを新しい単発のCUDA実行ownerへ結び、元claim/ledgerを再利用しないこと。保存CUBINを同じsource/header/imageで再検査し、7batch全106・全raw/logical fingerprint・実引数traceを検査する。元producer全体の約127秒の再監査をGPU子の60秒へ再投入しない。新ownerのCPU preflightと実行時artifact revalidationの境界を明示し、上限増加/SDK再compile/GPU再送で回避しない。実CUDA成功・現在の全suite・全char/効果・公開defaultは未達。以下は履歴。

# 2026-10-29 保存済み分割Metalの独立native監査・全106一致

`partitioned-native-audit`を共通CLI/immutable dispatcherへ追加した。実行済みv4の失敗rawと元sourceを変更せず、別packetのfresh GPU禁止childで元adapterのsemantic compare/rejection/stage validatorsを実行する。明示source-pinned address viewを使い、全input/output/native/strict generated指紋を保持する。既存partition/selection/validate_factsを再利用し、群単位のcalculationはFalse、全入力の重複・欠落なし集約だけTrueとする。

初版051dc854の一括CPU監査は240秒timeoutで失敗保存。上限を増やさず分割版d2197957へ移行し、全106/native63・7 fresh childが成功した。群の秒数73.62/28.63/57.84/92.32/50.68/120.13/81.04、集約506.70秒。入力再構築30.82秒、元native比較466.04秒で、時間の主体はCPU戦闘シミュレーション。各比較をjournalへ記録し、最も長いshield-stream-overflowは30.36秒だった。GPU/compiler/Windows追加0、raw/期待hash/旧失敗stage変更0。新独立監査のみcalculation_verified=True、旧stage=False・public=False・全goal=Falseを維持。v7 controllerと開発sourceはbyte同一、own packet26＋checkout関連108テスト成功。

別のCUDA sequence trace監査器を追加した。全7launch/sync/readback・cache-only CUBIN・zero/全chunk address/bytes/receipt・context destroyを検査し、後続失敗や欠落を拒否。legacy一回launch監査は変更0。旧observerが記録しない実launch寸法/allocation byteは未認定で、CPU故障5テストのみ・CUDA新ownerへの接続は未完。消費済みWindows claim/ledgerを再使用せず、新しいbounded owner、実引数観測、保存CUBIN再利用へ接続すること。上限増加/常駐テスト/GPU再送はしない。

全キャラ/全特殊効果/現在の全suite・公開受付は未達。旧固定106の独立計算認定と混同しない。詳細[分割転送](portable-partitioned-file-transport.md)、証跡 `partitioned-saved-native-v1.json`。以下は履歴。

# 2026-10-29 全106の共通分割file transport・M5論理wire一致

共通partitioned transportとprivate Metal CLIを実装。106を16×6＋10に分け、既存CUDA execute_cuda_batches(output_paths)／Swift --batchesの1context/pipeline・3bufferを再利用する。GPU計算/正本/厳密生成normalizer変更0。最大input7403524/output132146304/runtime2288768byte、全output875469264byteを保持。原本2148file中2147はbyte同一、CLIはmain dispatcherのみ追加、元registry/goldenを保持。

実行固定9a69d35dのfresh CPU全106/native63は391.973392秒で一致。M5全7dispatchは11.216289秒、必須generation/compiler0、Metal pipeline7hit。旧flat wire検査はRaw SHA 0a737874…対旧4ecc755e…で失敗し、child14.217147秒/exit1。旧親CLIはFalseを返しつつexit0だったため現codeでexit1へ修正。原本/partial/claimは保持しGPU再実行0。

保存raw比較で101rowは全byte一致、残るrow16/28/29/30/31も各1word、すべてDFS scratch depth1の+530（row word1924498）だった。destructibleBattleCaptureが保存するresults配列内の絶対word indexで、差は16×2064786。数値/state差ではない。source4file SHAを固定する明示address profileを実装し、全20参照のID・参照先・boundsを検査。rawを変えずRAM内の論理viewだけ5参照を付替え、全106のrow hashと全体4ecc755e…が一致。GPU原本raw0a737874…、期待hash、旧失敗判定は変更0。

現69f25d90 packetはsource-pinned profileを明示しraw SHAとlogical SHAを別記する。出力rawの付替え/数値正規化は行わない。source/call AST比較でplan/split/CUDA・Metal sequenceの引数は実行済みv4と同一。現packet自身13＋5unit成功、既存batch8/file15/stream4/CLI50成功。現profile統合の追加device実行ではなく、旧実GPU出力へのread-only監査とsource/unit証拠である。計算認定/独立post-GPU native監査/CUDA新owner・sequence traceは未完。Windows追加0、消費済み旧claim/ledgerを再使用しない。

model-checkはe061e679…で従来同一、未対応分類/公開default/全キャラ認定は維持。次はこの明示wire viewを使う保存結果の独立native監査と、共通sequence API trace・bounded CUDA実行経路への接続。詳細portable-partitioned-file-transport.md、証跡partitioned-file-transport-v1.json。

# 2026-10-29 immutable recovery接続・CUDA launchでcode2

元04515f96の計算/data/test/registry/goldenを保持するcapsuleを実装。CLI/flowの必要なbridgeだけをAST差込みし、9個の入力/claim/finish関数とnative loopを保持。新owner/nonce/transactionを安定した排他ledgerへ結合し、旧claimを触らない。固定66c50b92/commit18cde163のproduction codeは旧テスト成功版9d995acdと全byte同一（差は追加testのみ）。元28群177unit、新capsule9検査、関連stage31/preflight13/origin11/continuation10成功。Mac必須生成hit/compiler0は0.57秒。

Windows source2153file検証後のpreflight-recoverは59.477秒/exit0で成功。generation2.927秒・元証拠26.800秒・静的入力10.404秒・CUBIN出所12.409秒。元106/native63を再計算せず新transactionを作成。続くstaged GPUを同じ固定ownerで1回だけ実行したが、cuLaunchKernelがcode2。3回のcuMemAlloc/context/moduleは成功、sync/readback未到達。outer148.286秒/inner48.041秒、両exit1/timeoutなし、generation hit/Slang0。原本JSON4個をbytes/SHA照合し保存。後処理のevidence.json不足は副次エラーである。

新旧claimとledgerを保持し再実行0、両Job post0/monitor cleanup error0、process保持True/service未識別でenvironment=False。Job peakはouter2182651904/inner2023596032byte、上限2GiB。これだけでhost commit/VRAM不足を断定しない。全106の期待readbackは875469264byte。次は保存PTX/CUBIN/resource metadataの読取り依頼の結果を取得し、既存共通batch/streamingを用いて全入力を維持しながら一括出力割当を減らす設計を検証する。GPU再実行/claim削除/上限拡大で代替しない。

Windows taskのread-only metadataはcursor52a33edf-b45e-47e6-bdf6-6851a2c039ed:17で取得済み、idle。GPU/driver/SDK tool/compile/native/unit追加0。保存metadataではinput49048324/output875469264/scratch15163088byte（stride143048×106）。launch106block×1threadはソースからの導出でAPI引数記録ではない。既存CUBIN resource出力はREG254/STACK17056/LOCAL0/SHARED0、PTX entryはlocal0/virtual50。PTX全体のmax local宣言5192/max virtual15299を物理資源使用量へ読み替えない。元journal172803byte/SHA fc933ba9…はmetadataだけ取得、full bytesは未回収。3alloc成功→launch code2→context destroy成功、sync/readback無しを確認。未対応分類/model-checkのSHA e061e679は維持。現在の全106 CUDA計算成功・公開default・全キャラは未達。詳細portable-gpu-recovery.md、証跡cuda-gpu-recovery-v1.json。

# 2026-10-29 元preflightをown CLIで再監査するCPU経路

元04515f96の106/native63を再計算せず再監査するstaged-origin-check/audit-staged-originを実装。旧package自身のstaged-preflight-checkを別Pythonで呼び、当時の完全receiptとの一致とhost/nonce/input/countを確認する。元source/transaction/continuation親/各stage/timeoutの全file name・bytes・SHAを前後照合し、リンク/読取り失敗/追加/変更を拒否。workspace全体は探索しない。新ownerへのGPU admissionやCUBIN/cache検証は未実装で、execution/recovery/calculationはFalse。旧claimを触らず、GPU/compiler/native再計算0。

固定d754f360/commit928f3a33の9群101unitは10.454秒で成功。既存CLI50/stage31/failure7/preflight13も成功し、model-checkは従来と同じSHA e061e679…。source-only ZIP13,040,209byte/3879fileをartifact branch codex/staged-origin-controller-v1-source/0f524364で共有。Windowsも全byte一致後にCPU監査1回が78.906553秒/exit0で成功。106/native63を再計算せず再監査し34root/4916fileを固定、Job post0/cleanup監視error0。元結果2JSON計2467byteを回収しbytes/SHAとstage内reportの一致を照合。process保持True/service未識別でenvironment=False。native/host再監査Trueだがrecovery実行許可とCUBIN/cache検証はFalseを維持。元Slang/cacheの正確なpath/keyもmetadataから取得済み。次はこの完全証拠を保持するimmutable recovery owner/nonce/claimを実装し、保存CUBINと必須generation cacheを再検証して短いCUDA成立へ接続する。全キャラ/default/残consumerは未達。詳細portable-staged-failure-audit.md、記録staged-origin-controller-v1.json。

Windows原本のCPU監査は固定ebe7d2dbで終了0/30.154169秒、予算179.797秒・BelowNormal・stage_verified=True。元04515f96の106入力/AST/両Job/監視/消費済みclaimを確認。元結果2JSON計11,102byteを再実行せず回収しbytes/SHA一致を検証、fixturesへ保存した。execution metadataはscalar projectionだけを記録し、元1107byteのSHAも保持。GPU/compiler/native/旧unit/smokeの追加実行0、process保持True/service識別未確認なのでenvironment=False。execution_permitted/native/cache/host再認定はFalseのまま。元claimは消費済みで編集しない。実fixture追加後のfailure7検査とmodel-checkも成功。source-only ZIP13.03MB/3875fileの転送だけを使い、巨大履歴checkoutを避けた。記録staged-failure-windows-v1.json。次は既存事前検査とCUBINを保持するimmutable recovery protocolの実装。

# 2026-10-29 staged CUDA失敗監査と明示生成設定

元04515f96の消費済みexecution claimを再使用する既存経路はなく、その拒否を維持する。新CPU専用staged-failure-check / audit-staged-failureは、package owner・AST関数一致・7phase・両Job/監視・prepared全row/nonce/transaction/claimを既存監査器で検査する。passedでもexecution_permitted/native_admission_revalidated/linked_artifact_revalidated/host_revalidated/calculationはFalse。新しいimmutable recovery protocolは未実装であり、この診断でGPU再実行を許可しない。

staged-gpu-linkedのSlang/cacheはペアのCLI引数でも指定でき、recipeとbounded子環境に固定する。親環境を変更せず、partial/relative/子でのdriftを拒否。旧packet/claimを編集しない。固定754fcea8の8群90unit成功、明示設定31/failure6/既存CLI50/preflight13検査成功。GPU/Slang/CUDAの追加実行0、生成normalizer/保護CPU/Slang source変更0。Windowsでは保存metadataを読取済みでphase projectionだけfixture化した。実原本の新監査はまだ未実施で、下のWindows結果取得後に記録する。

詳細portable-staged-failure-audit.md、記録staged-failure-controller-v1.json。次はWindows原本をCPU専用・BelowNormal・2GiB・180秒で1回監査し、元106/native63と保存CUBINを保持する新controller移行を設計する。旧GPU/compile/native群を再実行しない。

最終330e9603/cache固定packet6b4d8009は6群53unit成功。sealed paired生成は必須hit/Slang0、source-baseline current、CUBIN/O1・2GiB・60秒compile-plan、model-checkも成功（追加GPU/実CUDA/Windows依頼0）。記録enemy-ammo-self-destruct-final-cli-v1.json。GPU実計算とfresh独立監査は先の固定2d5ad371の16入力証拠であり、このunit-checkをfresh全native実行と扱わない。

# 2026-10-29 敵弾薬と自爆を同じSlang実行器でMetal実証

固定2d5ad371の元Velvet76定義8world＋raw拒否8がM5/同出力のfresh GPU禁止独立sealで一致。14自爆/26試行/許可18発/実被弾90件、GPU0.803771秒/cold PSO58.212479秒/独立144.576577秒。unit43とfresh8 nativeの実行前照合、generation必須hit/Slang0、stride138952不変。CPU入力に計算済みschedule/弾薬/退場を入れず、入力117632word/出力2032000wordの幅を維持する。自爆記録をresource履歴の後1943776wordへ分離し、同世代・同時刻の実queueだけが退場後のmagazineを使える。empty/reloadも元scheduleで退場、HP/time退場は射撃なし。元時計/actor/割合演算/incoming/resource consumerと比較器を共用。

新golden/同sealのcompiler-source-only証明書/独立receiptを登録し、通常とcache-only入口へ接続した。compiler証明書自体のcalculationはFalseであり、実計算の根拠はgolden/receipt。新proof-binding5検査/readiness24検査と、旧ammo9/self8/CLI50の検査が成功。unitで8戦闘を繰り返す重複を除き、full nativeは固定package準備/実行前/独立sealで検査する。旧goldenは変更せず、新shared hookは別exact inverseで旧監査へ合成する。

現CUDA/公開default/全キャラは未達。Windowsは既存04515f96のGPU前失敗claimを保持し、今回の新規依頼0。次は通常/cache固定CLIの登録後確認、次の未対応consumerと既存CUDA preflight/cacheを保持するcontroller移行の設計。巨大な旧golden群を一括再実行しない。詳細portable-enemy-ammo-self-destruct.md、証跡enemy-ammo-self-destruct-metal-v1.json。

# 2026-10-28 敵弾薬と自爆のCPU合成契約・梱包漏れguard

元Velvet76定義のenemy-ammo-self-destruct-commonは固定packetで8契約/新7unit成功。関連敵弾薬24・自爆wire8・readiness24・CLI50・registry payload3検査が成功。実自爆時の既存AttackHit object/世代/frameを証拠に退場後の弾倉へ接続し、元scheduler/割合演算/被弾/完了通知を共用する。空弾倉/リロード中でも元scheduled countで退場、HP撃破/時間切れに射撃を生成しない。既定enemy-ammoは自爆拒否を維持。新CPU inverseを既存監査へ合成し、旧Metal goldenを改変しない。GPU source/保護CPU変更0、GPU合成は出力所有権とqueue資格のSlang接続が次。新契約の実Metal/CUDA/default/全キャラは未達。

初版packetは未追跡module漏れでreferenceのimport前後に失敗し保持。修正版を別展開して成功。full packageで全reference登録rootがtracked payloadへ入ることをZIP作成前に検査するguardを実装（動的import全closureの保証ではない）。小証跡enemy-ammo-self-destruct-native-contract-v1.json。先の自爆M5実証の最終d7d82948/cache packetは50unit/必須生成hit/Slang0/source current/compile plan/model-checkを確認し、add-self-destruct-final-cli-v1.jsonへ記録した。

Windowsは既存04515f96の保存事前検査177unit/106入力/native63成功と、保存PTX/object/CUBINを確認。再compile/事前検査再実行なしのstaged-gpu-linkedを1回だけ依頼し、設定行の失敗を報告した。GPU前にSlang compiler identity absentで終了。GPU子48.64秒/exit1、外181.59秒/timeout、driver/launch/sync/readback0、post0/消失0/監視cleanupエラー0。stage/サービス保全は未認定、旧claim保持/retry0。帰属不明を成功にしない。Mac共通runnerへ設定pathのpreclaim早期guardを追加し26検査成功。compiler/cacheの本検証は省略しない。証跡staged-cuda-environment-failure-v1.json。次は保存失敗metadataの回収と、元CPU事前検査/キャッシュを保持する新固定controllerへの正当な移行設計であり、旧claimの再使用はしない。

最終4883442aの敵回復normal/cache固定packetは107/135unit成功。sealed生成はrequired cache hit/Slang0、CUBIN/O1・2GiB・60秒plan成功（追加GPU/実CUDA compile0）。model-check成功、全source棚卸しの21 current/179 stale/2 unavailableを保持。現CUDA/公開受付/全キャラ未達。元32再認定の全run/sealは終了済みで再実行しない。新しいCUDA依頼0、Windowsstatusのみhost unavailable/durable。次は敵弾薬のCPU契約とCUDA成立経路の切分けを優先し、履歴goldenの一括再実行・巨大GPU本文の追加を先行しない。記録enemy-healing-named-admission-final-cli-v5.json。

# 2026-10-28 敵弾薬の元ハンドラ・実射撃をCPU契約へ接続

最終4542661bのADD実戦normal/cache固定packetは35/44unit成功、関連82検査成功。sealed生成必須hit/Slang0・新entryのregistered source current・CUBIN/O1/2GiB/60秒plan成功（追加GPU/実CUDA compile0）。保護CPU4ファイルはbyte不変。Windows既存statusはhost unavailable/durable、新runなし。次は敵弾薬6ケースのCPU契約をこの実戦queueに接続する。最終小証跡`target-count-query-evidence/add-attack-battle-final-cli-v1.json`。

後続`add-attack-battle`は実actor poolの世代/生存/bornを共通cursorに接続し、既存WS_LOGとincoming実行器を共用。固定44a543f8/package52b7150c…の元ニヒリスター70定義6編成＋拒否11、284発/1,120被弾の全戦闘がM5/独立seal成功。GPU0.692924秒・冷PSO58.330511秒・独立監査106.091323秒、readback138,176,000byte。34unit/fresh CPU6・必須生成cache hit/Slang0・stride138,952byteを確認。通常goldenとCUBIN/O1/NVRTC禁止/paired generation必須cache-onlyを登録。敵弾薬、self-destruct、攻撃debuff、現CUDA、default、全キャラは未完了。

旧敵回復入口の生成CUDA/MSLは以前の実GPUcaptureから全raw byte同一。guard付き共有sourceの正確な逆変換は過去監査で検査するが、旧goldenのraw source closureは別であり自動昇格しない。旧current suiteの再認定は、次の敵弾薬接続までsource変更をまとめてから行い、179履歴の一括実行は避ける。設計`portable-add-attack-battle.md`、小証跡`target-count-query-evidence/add-attack-battle-metal-v1.json`。新raw/claimは永続proofに保持。

ADD部品の登録6fde3ca2後も通常/キャッシュ専用固定packageで12/21unit成功、CUBIN/O1・2GiB・60秒plan成功（compiler/GPU0）。旧GPU421ファイル・保護CPU4ファイルの全byte保持、旧enemy-healing source-baseline currentを確認。追加GPU0。現Windows statusはhost unavailable/durable、既存結果取得のみ待ち、新runなし。小証跡`target-count-query-evidence/add-attack-registered-cli-checks-v1.json`。

後続：GPUの既存scheduleはADD射撃を拒否することを確認し、`add-attack-schedule`の共通cursorを先行実装。固定39a1908b/package468ff5fb…の8正例/11拒否（全187発）がM5/独立fresh GPU禁止監査で成功。GPU0.008248秒・監査1.487986秒。旧GPU本体source変更0。初版はfinish退場後のcleared診断1項目だけ失敗しraw/claim保持、別packageで修正。関連67検査成功。`add-attack-schedule-cache-only`は同じ計算のCUBIN/O1必須・NVRTC禁止、standaloneでresident生成cache指定不可。現CUDA/battle actor pool/弾薬未接続。詳細`portable-add-attack-schedule.md`と`target-count-query-evidence/add-attack-metal-component-v1.json`。

固定b8416750/package39a7382f…（3,816file/ZIP12,939,983byte）を別展開し、own CLIでも6契約2.641秒・新規8検査成功。全input/native/trace/contract指紋をcheckoutから保持し、実行後の全payloadも検証。container suiteのenemy-healing Metalは再実行0。梱包receiptは`target-count-query-evidence/enemy-ammo-frozen-cli-receipt-v1.json`。

`reference --suite enemy-ammo-common --out NEW.json`を追加。元ヴェルヴェット76効果・実武器・育成・owner順を維持した6worldで、割合演算は元handlerのcode identityを保持し、対象/状態closureだけを差し替える。既存BODY/ADD handle/generation、元frame、元attack callback/被ダメージHPへ接続。source表示名とADD_PREFIX付きregistry labelの不一致を修正。独自の敵clockやdamage計算は追加しない。共通CLIは6契約/2.550秒成功、関連61検査成功、model-check成功。証跡`target-count-query-evidence/enemy-ammo-cpu-contract-v1.json`。

固定容量・初期残弾・whole reloadを明示するopt-in CPUモデル。元scheduled attempts/counterを維持し、blocked shotの再予約はしない。Lv1/-2.95%とLv10/-5%の容量16での0/-1発差、空対象loop後の名前付き完了、reload期限/中断、世代reset/dead/staleを検査。武器変更/容量バフ/flat充填/force reload/self-destructは未対応。GPU本文/wire・過去golden・canonical CPU4ファイルは変更0。現Metal/CUDA/default/全キャラの認定ではない。設計は`portable-enemy-ammo.md`。

Windows既存chatのstatus取得は今回もhost unavailable/durable。追加run/再送なし。CUDA成立経路を先に切り分けるレビュー順を維持し、既存保存結果を取得できた時に次のbounded/cache検証を決める。Mac側はこのCPU契約を固定してから共通GPU資源状態へ接続する。以下は履歴。

# 2026-10-28 全登録source棚卸しを共通CLIへ追加・レビューの順序を維持

source-baseline --all-registeredを追加。source/golden組をde-duplicateしentryごとに一度hash、producer rootだけでcurrent/stale/unavailableを出す。全202組/224登録名/114source entryの結果は21 current・179 stale・2 unavailable（attack-magnitudeのgolden欠落）。source差分の多くは過去のschema/admission等も含むため、今回の32件だけで全登録を現source認定済みとしない。11 source-baseline境界検査が成功。数値/受付/正規化/過去goldenは変更していない。summaryはregistered-source-closure-inventory-v2-summary.json、全差分は共通CLIで再現する。

参照レビュー309e305/0e1f71bの方針を再確認：共通Slangと薄いbackendを維持し、巨大GPU本文の追加を続ける前にCUDA compiler/cache成立経路を確認する。独立監査を削らず、同条件Windows再試行・上限拡大はしない。179履歴を一括再実行する方向へ作業を広げず、現runtimeの証拠と未対応consumerのCPU契約を優先する。次は敵弾薬の世代付き状態/実shot/reload契約をCPUで固め、Windows既存transactionの保存状態が取得できた後に必要な短いCUDA検証を設計する。最新statusはhost unavailable/durable、追加runなし。以下は履歴。

# 2026-10-28 敵回復14も現sourceでM5・独立監査成功

固定5433f8e9/package343fa678…の敵回復14入力は100unit・fresh native6・M5 1回・fresh GPU禁止14群sealが成功。GPU4.863728秒、冷PSO59.320956秒、独立監査666.033136秒。input/全entry/native hashとreadback113,792,000byteを旧v1から保持した。新v2 golden/同一監査のcurrent source証明書を登録し、旧v1 golden/証明書を保存。旧18入力の再認定に続くこの14入力も完了したが、他の登録スイートの現source整合性・default consumer・現CUDA・全キャラ認定は別途確認が必要。

元Anne69定義・6worldの限定証拠を作業分類とsource監査へ更新。敵回復runtime6/readiness24検査が成功し、公開/正本受付は閉じたまま。記録enemy-healing-named-admission-recert-v3.json。次は登録後のnormal/cache固定packet検査・全登録goldenのsource整合性棚卸しと、敵弾薬の世代付きstate/shot/reload consumerへの接続。Windowsstatusはhost unavailable/durable、再依頼0。以下は履歴。

# 2026-10-28 次の未対応分類を元3編成のselected entry-inventoryで具体化

既存共通CLI entry-inventory --suite original-shield-weapons --character 유니 --character 얀 --character 벨벳 --favorite-stage 0 を再利用し、元69/71/76定義の3profileを全定義保持で静的監査。3packing失敗・各1観測カテゴリ、CPU battle/GPU0。Yuni row5のenemy_movement_disableはburst時5秒、Yan row4のforce_moveはburst時2秒で、数値量を持たない状態効果。Velvet row1はbattle_start/burst_enter:2のall_enemies ammo_charge_pct（level10 -5%）。新しい状態/射撃/リロードproviderが必要で、既存allied operatorのdivision→multiply→ties-even round→clampを共通規約として使える。名前付き完了は非空nameなら受信者loop後に一度、空loopでも発行する。

source監査と作業分類へ共通の敵弾薬前提を追加し、移動状態の空間/寿命依存を明示。24 readiness/14 model-gap検査が成功。再監査で全original definition SHAと拒否理由が従来と同一、受付は開けていない。次の優先候補は敵弾薬の世代付き状態と実shot/reload consumerであり、移動やLock Onの未確定空間規則を仮実装へ置換しない。選択3件だけの監査で全profileの優先順位/解除数を予測しない。記録selected-movement-ammo-prerequisites-v1.json。以下は履歴。

最終70f11e25のlogical/rosters通常・cache固定packetは76/95/104/123unit成功。通常2packetのsealed生成はrequired hit/Slang0、cache2packetのCUBIN/O1・2GiB・60秒planも成功（実compile/GPU/Windows0）。model-checkも成功し未対応canonical5種/公開受付/現CUDA/全体未達を保持。敵回復runは固定packetで継続中で、再依頼・再実行しない。記録logical-named-admission-final-cli-v4.json。

# 2026-10-28 共通source検査を固定packetで実証・旧18入力を現source再認定

固定5433f8e9のlogical13/元Nihilister5は75/94unit・fresh全native・M5各1回・fresh GPU禁止独立sealが成功。GPU2.509929/2.429060秒、独立監査147.150955/116.157589秒。後者は必須Metal pipeline cache hitでPSO0.002954秒。旧input全byte・全entry/native hash・readback計146,304,000byteを保持。新v3 goldenと同一監査のcurrent source証明書を登録し、v1/v2 golden/証明書は履歴として保持する。source-baselineは親logicalの全sourceが検証済みrosters development closureへ含まれることを実パッケージで検査し、登録source current=False/計算認定Falseと明示した。

新6境界検査に加え、現source/過去証明書pair・保持結果の5検査、既存CLI/rosters検査が成功。未対応分類は新source18件の限定証拠だけへ更新し、default/全キャラ/現CUDAを開けない。詳細証拠logical-named-admission-recert-v3.json。

敵回復14の同source固定packetもfresh native6の作成・14群100unit・必須paired生成hitが成功。own CLI runを開始し、まだfresh CPU照合中でGPU/独立sealは未完。PIDやcaptureの状態だけを成功証拠にしない。producer rootを変更しても実行中の固定packet rootは変更しない。Windows追加0、全目標未達。次は敵回復runの終了確認・同readbackの旧byte保持照合・fresh独立seal。以下は履歴。

# 2026-10-28 再認定用の共通source-baseline検査を実装

旧logical/rosters/healingのgolden/証明書は整合するが、現sourceとは異なる。全てを現sourceへ付替えず、共通CLI source-baselineで通常の厳密一致と検証済みdevelopment closureを区別する。親/peerを認めるのは要求sourceの全file/SHAがactive manifestのclosureに含まれる時だけ。登録source current/計算認定/GPU認定は別field。旧golden/証明書pairの検査とfresh native/Metal/sealを残す。選択suiteの個別test分岐も共通helperへ統合。6境界検査・既存範囲8検査と現登録範囲のCLI source-checkが成功。temp alias初版の失敗はtest root.resolveで修正し、Slang生成器は変更なし。次は固定packetで旧32入力（logical13/rosters5/healing14）を現source再認定。Windows追加0、全目標未達。以下は履歴。

最終358687dfの旧selection通常/cache固定packetは24/52unit成功。sealed paired生成はrequired hit/Slang0、CUBIN/O1・2GiB・60秒plan成功。最終model-checkも成功しcanonical consumer5種/公開受付/全目標未達を保持。追加GPU0/Windows0。記録named-range-final-cli-v7.json。

# 2026-10-28 範囲battle通常/cache検査・旧selection21の現source再認定が成功

登録aa4c32e1の通常/cache固定packetは7群53unit/9群81unit成功。sealed paired generationはrequired hit/Slang0、CUBIN/O1・2GiB・60秒compile-plan成功（実compile/GPU/Windows0）。結果はnamed-range-battle-registered-v6.json。

旧selection21はsource変更を正しく拒否した。development packet内だけ検証済みmanifestの新source基準を読むようテストを修正（5369e834）、通常goldenのcurrent一致は維持。固定f052572f…のM5全21とfresh独立seal（1.23757秒）が成功。GPU0.003406秒、旧input全byte/出力13,418,496byte/全entry/native hashを保持し、v1を残してv2 goldenへ登録。v3はCPU testでGPU前停止し失敗を保持。証拠named-effect-range-current-source-v4.json。

新battle16と旧selection21は別scope。旧logical13/rosters5/healing14の現共通source再認定はまだ必要。default正本consumer5種/公開数値受付/現CUDA/全キャラは未達のまま。Windowsstatusはhost unavailable durableで追加実行・再送0。以下は履歴。

# 2026-10-28 元範囲battle全16入力の保存再監査・独立seal成功

固定240a9788/package8b532626…の修正比較器で、保存v3出力全16入力をfresh16群で再監査成功（242.42秒）。続いて別fresh8群（2入力/群・各180秒上限）で独立seal成功（216.40秒）、同じ監査から期待値とfull-source compiler証明書を生成。元4worldの各54cast/実選択/元87定義の全battle比較とraw拒否12を含む。元失敗/claim/rawを保持、追加GPU0/Windows再実行0。通常named-range-battleと同じ計算のcache-onlyを登録し、CUBIN/O1・paired generation必須を継承。キャッシュ実hit/現CUDA/実ゲーム半径・最近傍/default consumer/全キャラは未認定。

モデル監査と作業分類は共通の証拠記述を使い、effect_range_pct/target_countの未対応分類を残したまま限定battle証拠を併記する。旧sourceのnamed-effect-range/旧logical/healingは共通stack admission変更による現source再認定が必要で、旧goldenのSHAを付替えない。旧範囲testのsource一致検査はこの未完を検出している。次は新normal/cache固定packetのunit/generation/compile-plan確認と旧範囲の現source再認定。証跡named-range-battle-sealed-v5.json、独立receipt named-range-battle-independent-v5.json。全目標未達。以下は履歴。

# 2026-10-28 範囲battle M5実行・命中番号比較器修正

固定628dd82d/package ee3ab93f…のown CLIが6群48unit/fresh native4（175.65秒）/required generation hitを通過しM5 Metalで16入力を1回実行。GPU2.29904秒、冷PSO58.4064秒。正例4件status0/各54cast recordは一致、raw拒否12件成立。ただし全selection比較は旧traceの仮hit1を使って停止。既存trace_viewで実HitEvent生成番号を厳密に結び、同一GPU保存出力のexpanded1件をfresh CPUで診断すると全既存battle比較が成功（41.44秒、102creation receipts）。全16の固定再監査と独立sealは未完、成功golden未登録。同claim再試行0/GPU追加0/Windows追加0。証拠named-range-battle-metal-v3.json。

共通source inverseの二重healing巻戻しと途中の検査済み依存dropを修正（f1de08fc）。新wire5/旧logical5/旧named6/元health-parts6検査が成功、改変sourceの拒否を維持。旧logical生成CUDA/MSLは今回の共通admission修正で変わり、旧goldenの現source再認定は未完。正規化器/保護CPU/旧証明書の書換えなし。次は修正版固定packetで保存v3出力を全件replay/独立sealし、現CUDAは引き続き未認定とする。全目標未達。以下は履歴。

# 2026-10-28 範囲battle初回Metalの初期化拒否を修正・再検証前

v2はM5実GPUが完了したが正例4件すべてstage15/status64で初期化拒否、raw拒否8件は成立。失敗/raw/claimを保持し同claim再実行0。元Asukaのnamed-enemy MODE24..27とstack演算の併存が原因。新entryへ既存PORTABLE_NAMED_ENEMYを接続し、既存named validatorが検査する4wordだけstack検査から委譲。不正tag/name/flags/reservedを拒否する4件追加（全16入力）。新wire3/旧logical source5検査とpaired CUDA/MSL生成成功。修正版Metalは未検証、全目標未達。証拠named-range-battle-admission-v2.json。以下は履歴。

# 2026-10-28 範囲battleの共通Slang実装・検証前

元4world＋raw拒否8の新named-range-battleを実装。NRB1/version1のliteral tail544word（input116224/output2032000）に元damage row/base count/base radius/BODY colliderだけを保持し、元range/count定義をprivate stat94/93へ対応付ける。対象数は既存namedTargetCountValue、範囲はordered software binary64、候補順は既存actorSetCaptureへ接続。共通CP cast/queueにADD世代とBODY ordinalを固定し、既存ActorPool/land/counter/healへ配送する。新ダメージ式/HP/時計なし。全54cast record/全selectionと既存full battle比較を追加。GPU未実行、goldenなし。

共有4ファイルのopt-in差分を厳密な全文SHA inverseで保持し、既存healing/logical source監査へ合成。新wire3検査・旧logical runtime5検査が成功。旧source証明書は履歴であり、変更後sourceへ付替えない。次は固定packetのfresh native・paired生成・M5 Metal1回・fresh独立seal。以下は履歴。

# 2026-10-28 元87定義battleの固定CPU契約・共通reader統合が成功

最終2f64d278/cache packet 7afe87dd…のown CLIで5群51unit、fresh全4world CPU reference（3.222秒）、model-checkが成功。重複していた対象数演算を既存共通queryへ統合し、4worldのinput/native/trace全指紋を保持した。default callerのrecipient受付は変更せず、静的なallies_with_buffを明示opt-inする。

既存selection-only21のsealed生成も必須cache hit/Slang0、CUBIN O1・2GiB・60秒plan成功。これは新battle4worldのGPU認定ではない。今回GPU/Windows新実行0、battle wire/Metalは未接続、全目標未達。packet v1のmodel-check依存不足は失敗を保持して既存arc goldenを明示同梱しv2/v3で解消。次は新battle cast/queue snapshot/landingを同じ共通Slangへ接続する。最終証跡named-range-battle-cpu-final-v3.json。以下は履歴。

固定CPU packet v1のown CLIで50unit・全4world fresh reference・旧sealed21のrequired generation hitが成功。追加のmodel-checkはarc golden未同梱でCPU停止。producer側auditとは区別し、必要な既存arc goldenを明示support_filesへ追加する。元失敗/packetは保持、計算sourceと旧Metal期待値の変更なし。

# 2026-10-28 範囲の元87定義battle CPU接続・出所訂正

前回範囲500%をマリと説明したが、実sourceは레이 (가칭)/index4。METAと定義11件が存在しis_preview=False。辞書や既存21 golden/input/rawは変更せず、元マリのキャラ認定へ使わない。旧case label original-Mariは履歴として保持。

新reference named-range-battle-commonはAsukaWILLE/Rei(가칭)/Miranda/Dora/Maryの全87定義・実武器/育成/config/seedを保持。cast時のnamed range/count queryと既存logical candidate順/geometry filterを接続し、同じHitEventと既存ActorRegistry/route/HP/landで配送。元worldの全54cast/landingで、初期2回の0%/2体→52回の500%/3体を確認。小基準半径・遅延spawn・死亡ADDの4worldが共通CLI fresh CPU契約に成功、約2.98秒、GPU/packing0。stale/dead frozen actorは除外し、次世代へ当てず振替もしない明示モデル。空間最近傍/ゲーム半径の認定とは別。

このbattleのGPU wire/Metalは未接続。既存sealed21のMetal証拠を今回へ付け替えない。既存GPUファイル変更0で旧source/goldenを保持。次はCP cast/queue snapshotとpacket hookへ接続し、literal versioned tail・cast/selection全出力比較を追加。詳細portable-named-effect-range.md、CPU証拠named-range-battle-cpu-v1.json。以下は履歴。

最終e47a74a7のimmutable cache packet bb8f984f…は通常の全検査を含む4群45unit成功。sealed paired generationは必須hit/Slang0、CUBIN O1・2GiB・60秒compile-planも成功（実compiler/GPU/claim0）。通常/cacheで計算/golden/sourceが同一であることも検査した。追加GPUなし。記録named-effect-range-final-cli-v1.json。次は`coordinate_area_runtime.slang`のcast時grow/snapshotを実actor setとqueueへ結び、既存世代付きcarrierとlandingを使う。基準半径は宣言値として保持し、ゲーム式の認定と混同しない。

# 2026-10-28 効果名別範囲を共通実行器の実状態→幾何選択へ接続

新named-effect-rangeは元レイ（データ上の名称「レイ（仮称）」）の500%/9秒/marker限定recipientを保持した5条件＋派生7＋raw拒否9。新entryは既存event初期化/command/serializerを再利用し、final checkpointの実carrierからordered percent→factor→declared radiusを読んで、既存決定的circle/rectangle選択へ渡す。既存GPU source変更0。stat引数だけを共通化したnative readerは旧target-count10検査も成功。

固定6b1369a0のM5実GPU1回（0.003541秒、冷PSO3.095670秒）はdecoder配列型で比較停止。失敗/claim/rawを保持。9415c8f0のdecoder修正だけを別固定packetへ作り、既存CLI replayの全source/input/native guardで保存readbackを再監査し全21成功、GPU追加0。fresh独立GPU禁止sealも1.305107秒で全一致。全world compiler証明書はscope guardが拒否、限定sealだけを作成した。通常/cache CLI登録済み。現CUDA/実world世代/生死/ダメージ配送/ゲーム半径規則/全キャラ/defaultは未認定。次はこのconsumerを実actor setと元Asuka/Reiのbattleへ接続する。Windows旧transaction statusはhost unavailable durable、終端未取得・再送なし。証跡named-effect-range-metal-v2.json、詳細portable-named-effect-range.md。以下は履歴。

# 2026-10-28 敵回復の最終normal/cache packet検査成功

最終2842d83dの通常4cdb20da…/cache-only5ba6bd36…を固定。own CLIの15群122unitが成功、sealed paired生成は必須hit/Slang0。CUBIN O1・2GiB・60秒compile-planも成功（実compile/GPU/claim0）。元Metal14件/独立監査の計算source/全期待値を保持。v1の証明書同梱漏れはGPU前CPU gateで検出し、失敗packet/rawを保持してv2で修正した。Windows新依頼0。現CUDA/全キャラは未完。最終証跡enemy-healing-final-cli-v2.json。以下は履歴。

最終packet v1のCPU unit gateは新source証明書の同梱漏れを検出（GPU/claim0）。producerの明示support_filesへ追加し、検査を維持して別v2へ固定する。失敗packetとログを保持し、元Metal/golden/source bytesは変更しない。

# 2026-10-28 敵回復14入力のfresh独立監査が成功・通常CLIへ登録

固定688de06e/package80c86ed0…のM5全14入力を、別fresh GPU禁止14群（元native6/拒否8、各180秒上限、計667.090秒）で全比較した。親oracle再利用0・追加GPU0。同じsealのgolden/source証明書を登録し、通常enemy-healingと同じ計算のenemy-healing-cache-onlyを追加。後者はCUBIN/O1とpaired generation必須。旧CPU契約とdefault gapは保持し、別の限定Metal証拠を分類へ追記。現CUDA/公開admission/全キャラは未認定。v4失敗とraw/claimは保持。小さな最終証跡enemy-healing-metal-sealed-v5.json。以下は履歴。

# 2026-10-28 修正版敵回復14入力がM5 Metal全一致（fresh独立監査中）

固定688de06e/package80c86ed0…のown CLIが90unit・fresh CPU6件・必須paired生成cache hitを通過し、M5 Metalで14入力全比較に成功。GPU4.886496秒、冷PSO58.768053秒。親のfresh native6件/creation context6件を再利用し、追加native0。前回失敗deadはraw overkill498896へ一致。他13入力の全readback byteは保持し、deadの差分4wordはquery/最終/全体overkillと着弾試行数2833→2839だけだった。比較を弱めていない。v4の失敗/claim/rawを保持し、v5は別sourceで1回/retry0。

同じproducer rootのown CLI `seal` をgroup-size1/各180秒・GPU禁止fresh14群で開始した。現在その完了とsource証明書/independent receipt待ち。未確認のまま通常goldenへ登録しない。実行中rootを変更しない。小さな一次結果 `research/target-count-query-evidence/enemy-healing-metal-live-parent-v5.json`。旧18入力は上記修正sourceで再認定/登録済み。Windows新依頼0、全目標未達。以下は履歴。

# 2026-10-28 共通配送修正後の旧18入力をMetal・独立監査で再認定

固定688de06eのlogical13/package4093b5b9…と元Nihilister5/packagebae48b53…は、own CLIの65/84unit・fresh全native・M5 Metal各1回・fresh GPU禁止独立sealが成功。GPU2.518804/2.435720秒、独立監査140.324/115.503秒。後者のpaired generation/pipelineは必須hitでPSO0.002840秒。全18入力・CPU指紋・全readback byteを旧保存結果から保持した。retirementの追加passive監査は正本結果の透明性、全ADD pool/score/global overkill、hit_addに帰属するowner別overkillも照合。ただし同ケースの同世代死亡後packetは0であり、Anne deadの回帰を代替しない。

通常logical geometry/rostersのCLIを新v2 goldenへ更新。旧v1 goldenと旧source証明書のbyteを別ファイルで保存し、fresh sealと同時生成したcurrent source証明書を登録した。分類にはfixed source688de06eの再認定だけを追記し、default/全キャラ/現CUDAは閉じたまま。継承test dataは登録golden名から参照するよう修正し、証明書/履歴の8JSONも明示同梱。新4検査・入口4/5検査が成功。小さな出所 `research/target-count-query-evidence/logical-dead-overkill-recertification-v1.json`。

Anne修正版v5/package80c86ed0…は14入力/全native期待指紋をv4から保持し、90unitとpaired生成が成功。own CLIのfresh CPU照合→新Metal1回を開始、完了/独立sealは未確認。v4消費済みclaimの再試行0。実行中rootを変更しない。Windows新依頼0。最終6b114364の通常32bf85b4…/cache-only6f199272…は固定own CLIで14群116unit、sealed paired生成必須hit/Slang0、CUBIN O1・2GiB・60秒compile-plan成功。追加GPU/Windows0。出所 `research/target-count-query-evidence/logical-delivery-final-cli-v1.json`。以下は履歴。

# 2026-10-28 敵回復M5実行13/14一致・死亡後overkillを修正

v4のfresh CPU6件（約580秒）/89unit/必須generation hitが成功し、M5 Metal1回で14入力を実行。5正例＋8拒否は全比較一致、dead1件のraw overkillがGPU85404/CPU498896。GPU4.8772秒・冷PSO58.8500秒。失敗/raw/消費済みclaimを保持し、同実行の再試行0。fresh保存group3監査でも同じ失敗を確認。計算全体はfalseのまま。

原因は回復ではなく、共通logical direct配送で同射撃内の死亡済み・同世代ADDをearly dropしていたこと。既存ActorPoolLandのoverkill-only経路へ渡す1条件の修正と回帰検査を追加し、stale世代拒否、命中/counter/group/trace抑止を保持した。新25検査＋旧logical source5検査が成功。比較器は項目/実値/期待値の説明だけ追加し、比較を弱めない。旧logical13/5の現source再認定も後続で必要。

次は修正版を別packetへ固定してMetal14件＋fresh独立seal。現在sourceでGPU成功未確認。Windows新依頼0。詳細[敵回復](portable-enemy-healing.md)、小さな失敗出所 `research/target-count-query-evidence/enemy-healing-first-metal-difference-v1.json`。以下は履歴。

# 2026-10-28 敵回復14入力の完全CPU基準とpaired生成が完了

固定4f56bc8e/package1581f245…の元6条件は完全観測で参照値を固定（1件約70〜104秒）。Anneにmulti_hit定義がないため欠けていたgroup空集合の観測を有効化し、旧v2のCPU作成は明示中断/GPU0・ログ保持。短い3秒診断で6種類の空group記録と実回復2件/元69定義を確認した。本来の6条件は短縮していない。

CUDA/MSLのpaired生成が成功。v3のunitは継承検査が使う旧logical goldenの同梱漏れを検出。共通CLIの限定 `supplement-test-golden` で、sealed donor1b700538…からgolden1ファイル32,392byteだけを加えたv4/package2d9216cb…を作り、元3,758ファイル・全入力/CPU期待指紋を完全保持した。own CLIの12群89検査成功、paired必須cache hit/Slang追加0。今後の通常packageのsupport_filesにも依存を登録し、新toolの7検査/入口5検査も成功。元失敗とパッケージは変更しない。

v4のown CLIでfresh CPU事前照合→Metal1回の実行を開始した。完了/独立sealはまだ確認していない。Windowsの既存statusはhost unavailable durable、再送/新実行0。実行中coordinator/rootを変更しない。小さな出所 `research/target-count-query-evidence/enemy-healing-predevice-v1.json`。以下は履歴。

# 2026-10-28 敵回復の共通wire・Slang consumerを実装（実機認定前）

EHL1/version1のliteral bankを既存logical prefixへ追加し、新入力120,048/出力2,032,000wordの明示entryを登録。既存pool同期後にsource-openを消費し、既存の世代付き敵carrierとbinary64 ADD HPを使う。hit/score/overkillを回復では変えず、raw小数creditと公開キャラ別roundを別に比較する。元6編成/69定義とraw拒否8件の開発専用 `enemy-healing` を共通CLIへ追加。新24検査・旧logical source5検査成功。初回旧source検査の戻りmap件数差を検出し、既存6件の返却契約を保持して修正。失敗は保存し、旧テスト期待値は変更しない。

次は固定packet自身のnative事前検査→paired生成→Metal1回→fresh GPU禁止seal。wire/Slang/登録の成立は実GPU成功ではない。Windows新依頼0、旧transactionの終端不明を維持。詳細[敵回復](portable-enemy-healing.md)。以下は履歴。

# 2026-10-28 敵回復consumerの元アンCPU契約を実装（GPU未接続）

`enemy-healing-common`は元アン全69定義、既存idle source/ADD HP/世代/回復倍率で6条件を検証。元Lv10約0.2107/Lv1約0.5659が実回復量へ反映。回復が実際の生存/累積得点へ影響する検査、上限/死亡拒否、未期限切れ旧世代の除外、二重t0とalias復元を含む。新時計/HP heap/効果の置換なし。

小数回復後の撃破ではraw score/overkillが小数になるが、公開SimResultは元からキャラ別round→合算だった。失敗診断を保持し、内部ledgerと公開roundを別々に検査する。GPUで途中int変換しないことが次の数値要件。専用11検査成功。既定consumer未設置/GPU wire/Metal/CUDA未接続、分類はreference_model_gap。次は[敵回復wire/phase/小数credit設計](portable-enemy-healing.md)に従い共通GPUへ接続する。固定5fb6a02c/package c8d95305…のown CLIで参照6件（7.11秒）・11群83unit・model-checkが成功。GPU追加0。出所 `research/target-count-query-evidence/enemy-healing-cpu-final-v1.json`。以下は履歴。

最終b390bad5の通常1b700538…/cache-only16917e53…を固定。own CLIの72unit/model-check/required generation sealed baseline hit・Slang0と、CUBIN O1・2GiB・60秒compile-plan/必須flag負例が成功。追加GPU0。出所logical-Nihilister-final-checks-v1.json、private継続点logical-Nihilister-sealed-continuation-v1.json。既知の元multi_hit2/4はこの明示幾何モデルで検証できたが、既定producer/残る5stat/敵quantity/現CUDA/全キャラは未完。次は未対応分類の新しい実戦consumerを優先し、同じ形状fixtureの反復だけへ縮小しない。

# 2026-10-28 元ニヒリスター70定義の実2敵通知をMetalで検証

`logical-actor-rosters` sealed5。元SR/全70定義のままBODY+ADD、範囲外、PART、37度矩形、30秒を検査。実group20/通知19/子着弾38の長時間も全比較。固定66df6953/package b38e3b9d…、M5 GPU2.434174秒、必須pipeline hit0.002745秒、generation必須hit/Slang0。旧GPU entry/CUDA/MSL/reflection全byteと旧13goldenを保持し、旧GPU再実行0。71unitとfresh独立監査5件107.573248秒が成功。共通比較器の旧全検査文は固定AST一致で保持する。

最初のPART対照assertはPART単独初弾の敵集合0を考慮していなかった。実native診断を保存し、最大1敵・実BODY1・実PART着弾・通知子なしを検査する形へ修正。源effect/武器/時刻は変更していない。通常/cached CLIを登録し、分類は明示モデルの元2敵通知だけを検証済みとし、既定gap/公開拒否/全キャラ未認定を維持。現CUDAは未検証、Windows新依頼0。詳細は[元ニヒリスター](portable-logical-actor-rosters.md)。以下は履歴。

最終e0e2b430の通常a254a809…/cache-only9f583a9b…を固定。通常own CLIの65unit/model-check/required generation sealed baseline hit・Slang0、cache側のCUBIN O1・2GiB・60秒compile-planと必須flag負例を確認。追加GPU0。model-check用固定文書とarc基準の同梱、共通receipt includeの厳密source監査も完了。Windows statusはhost unavailable durable、旧終端不明で新runなし。次は他の元キャラの実複数敵通知・武器/幾何/世代の組合せへ広げる。private継続点logical-actor-metal-sealed-continuation-v1.json。

# 2026-10-28 実ADD幾何をM5 Metal・独立sealで検証

`logical-actor-geometry` sealed13（元6＋拒否7）。固定5ed97fd4/package e4d6f280…のown CLIがCPU63検査・fresh native6・M5 Metal全比較に成功。GPU2.514622秒、初回PSO58.345348秒、事前CPU102.617612秒。比較はlive ParentOracles6件再利用/追加native0。独立GPU禁止fresh監査も全13件で成功（128.944960秒）。通常goldenとfull-source compiler証明を同じ監査で作成。実GPU1、retry0、Slang必須cache hit/Slang0。未対応分類には別の明示モデル証拠を追加し、既定戦闘のgapと全キャラ未認定を保つ。

次は通常sealed packetとcache-only packetのCPU/compile-planを確認し、他キャラ・複数形状・世代遷移など未認定の組合せへ広げる。新CUBIN/cache hit・現CUDAは未実証。旧Windows transactionの終端不明の間は新runを送らない。詳細は[実ADD幾何](portable-logical-actor-geometry.md)、出所はmetal-logical-actor-geometry-v1.json。以下は履歴。

# 2026-10-28 実ADD幾何の共通runtime配線・paired生成（Metal未実行）

新world_coordinate_logical_actor_entryは通常shot snapshotへ実ADDを合流し、元shape math/整数親量/landing/receipt/groupを共有する。Runtime138,952byte不変、新CUDA/MSL生成成功、旧history entryのCUDA/MSL/両reflection全byte保持。新required生成cache hit/Slang0。CPU契約6件の全nativeを保持、既存full native chainでも6件のgroup/子/point/draw/RNG等10項目を完全照合。関連43検査成功。初回観測self問題・逆順rewrite・旧arena逆投影の接続漏れの失敗を保存し修正。GPU/Windows新依頼0、公開受付/全キャラ認定は未完。

次はSwiftの新wire受付、共通CLIの開発suiteと既存全battle/group/history比較＋新scratch監査を登録し、固定packetでMetal1回＋fresh sealへ進む。新entryの実GPUはまだ0であり、生成成功を計算成功と扱わない。旧Windows transactionの終端不明の間は新runを送らない。詳細は[実ADD幾何](portable-logical-actor-geometry.md)、小さな出所はlogical-actor-runtime-generation-v1.json、private詳細はresident-frame-arena-20261027/logical-runtime-source-v1およびlogical-full-existing-native-six-v1.json。以下は履歴。

最終0175fe99…（27466a62）のown CLIはCPU契約6件2.34秒、25群226unit/compile-plan policy成功。旧GPU entryのgeneration必須hit/Slang0・CUDA/MSL/reflection全byte保持。新logical geometryのwire/Metalは未接続。private full native約5.35MB、公開は小さなSHA/件数/境界記録のみ。次はこのCPU契約を固定基準に共通wire/actor pool/Metalへ接続する。

# 2026-10-28 実ADD幾何と元RLの4敵通知をCPU契約へ接続

`logical-actor-geometry-common`は元ベロータ5人/全68定義を保持し、既存WorldSchedule/actor registry、sampled `_coord_pellet`、既存landing/groupでBODY＋実ADDを結ぶ新しい明示モデル。元multi_hit:4→敵def field/追加攻撃、3敵/範囲外/PART非算入、実死亡後の子対象、30秒を6条件へ固定する。元damage/sampler/HP/clockの複製なし。ADD前面はbody-hit creditを保持し、元PART/coreチャンネルと投影外fallbackを保つ。全aliasとevent復元、世代filter、元effect/owner/実武器/config/seed、全SimResultとpoint/draw/RNGを検査。既定CPU同値ではなくCPU reference/model gapのまま、GPU wire/Metal/CUDA未接続。既存typedoptin追加より古いaudit2引数期待を変更前HEAD同一sourceで確認し、3引数＋両False default＋型依存guardへ厳密修正。Windows新run0。次は共通wire/arena/source保持→同じ6条件でMetal接続。全体未達。[詳細](portable-logical-actor-geometry.md)。以下は履歴。

最終packet10bb432e…（f096e7fc）は選択監査実行/24群216unit/compile-plan policy成功。計算/packing/native/比較/goldenを保持し、native全sweep/GPU再実行0。詳細`target-count-query-evidence/selected-entry-final-checks-v1.json`。

# 2026-10-28 元profile選択監査を共通CLIへ接続

`entry-inventory`へ`--character`反復指定/`--favorite-stage`を追加。元metadataで全選択を検証後、指定profileだけprepareする。元owner/source行/name/effect SHAと既存reference_readinessを結合した`profile_explanations`を出し、部分結果に全体admissionを付けない。未知名/存在しないstage/重複は準備前拒否、failureも保存。favorite bodyの共有defaults混入をdeepcopyで防止する。実Ann/Velvet2件0.87秒/Cinderella1件0.82秒、全266対照4.53秒。旧全profile行/input SHA/定義identity/未対応順位を保持し、選択3行も全体行と一致。専用7/既存inventory11/readiness15/semantics22検査成功。元GPU/数値/正本/packing/比較/golden変更0、追加GPU/compile0、Windowsstatusはhost unavailable・再送0。既存model-gap調査を重ねず、敵向けconsumer不足とGPU lower不足をこの入口で確認してから次の変更を選ぶ。全体未達。[詳細と証跡](portable-shared-entry-inventory.md)。以下は履歴。

最終cache packetb9cf55d4…（a41de72f）は23群209unit/compile-plan policy成功。全計算/観測/比較・元input/native期待と独立goldenを保持し、最終登録によるnative/GPU再実行0。詳細`target-count-query-evidence/original-catalogue-incoming-final-checks-v1.json`。

# 2026-10-28 元B2・デコイの実被弾を共通実行器で独立seal

`original-catalogue-incoming`は元Red Hood B2/autoとCinderella chipped/broken各30秒の4入力、元81/81/74/74定義を保持。挑発中だけのvictim変更、実HP被弾後の吸血、デコイ一発全体吸収→次弾HP→元burst復帰を既存処理で全照合した。全skill217行、全battle/武器/通知/回復/乱数/全burst tickを比較。固定05cc2d69/package854ea3ad…、178unit/CPU81.73秒/M5 GPU3.82519秒/独立94.51秒、生成/PSO必須hit・Slang0/PSO.00311秒。GPU実行1/retry0、元GPU/数値/CPU正本/効果変更0。初版2件の誤った検査期待はGPU前に失敗保存、元burstを抑止せずliteral4.1秒攻撃を足して実分岐を確認。CUDA cache-onlyは同じ計算/golden、現CUDA実機未確認・Windows新run0。全キャラ/全特殊効果は未達。Ann/Velvetの失敗を本人の敵向けoperatorへ特定し、味方selector不足と混同しない。cover_def_pctの正本inertも保持。次は敵向けconsumer契約と混成world/周期False側などの残件。[詳細と証拠](portable-original-catalogue-incoming.md)。以下は履歴。

最終cache packet9fb47503…（7fdc2b26）は22群205unit/compile-plan policy成功。全計算/観測/比較と元input/native期待を保持し、最終登録によるnative/GPU再実行0。詳細`target-count-query-evidence/original-catalogue-roles-final-checks-v1.json`。

# 2026-10-28 元のB1条件と明示バースト順をMetalで独立seal

`original-catalogue-roles`はRapi no/with B1の実編成とRed Hood 123/12の明示操作、各30秒4入力を同じ共通実行器でseal。元90/91/81/81定義を保持し、全skill31/38/6/6行と全戦闘状態・全burst tickを比較した。実owner/stage receiptも必須検査する。明示burst操作は元identity検査後にcopyして適用し、元操作保持Falseを記録。初版の自動候補順の期待誤りはGPU前に修正し失敗を保持。固定8c3a1706/package acc12615…、174unit/CPU100.11秒/GPU4.47774秒/独立115.38秒。生成/Metal必須hit・Slang0、GPU実行1回/retry0。CUDA/MSL/reflection全byteは前burstと同一。既存cache-only経路へ同じ計算/goldenを登録するがCUDA現実機未確認。Windows新実行0、全キャラ/全特殊効果/公開受付は未達。次は実被弾/decoy、混成worldと他の未実証元profile。[設計と証拠](portable-original-catalogue-roles.md)。以下は履歴。

# 2026-10-28 元4編成のburst合成を独立seal・観測器の不足を修正

最終cache packet f7ca339e…（9cbcad76）は20群197unit/compile-plan policy成功。初版の比較golden同梱不足を既存support_files/AUDIT_FILESで修正。独立sealから全計算/観測/比較moduleを保持し、native/GPU全再実行0。最終検査の詳細は `research/target-count-query-evidence/original-catalogue-burst-final-checks-v1.json`。

`original-catalogue-burst`はRapi RH/SBS/Red Hood/Cinderellaの元30秒4編成を同じ共通実行器でseal。全318定義を保持し、付着/蓄積・即時起爆、gauge3段、武器変更、HP由来ATK/最大HP更新と連続攻撃を実行。全skill160行/物理6344receiptの既存全件SHA+保持prefix/全状態を比較。初回GPU比較は成功したが独立observerのstale scalar codeで失敗したため、実caller+現在のscalar returnへ観測を修正。元4入力/native/GPU source全保持のstrict replay・fresh GPU禁止監査101.22秒で成功した。GPU実行1回のみ4.036秒、generation/pipeline必須hit・Slang0/PSO.00327秒。canonical/GPU/数値/効果/normalizer変更0。単一監査failure/timeoutの詳細を共通CLIがcapture隣へ保存する。Rapi no-other-B1とRH B1/B2は未観測で、次に実入力へ接続する。CUDA cache-only入口は同じkernel/基準を使うが実CUDA未確認、Windows新依頼0・旧transaction再送なし。全キャラ/全特殊効果は未達。[設計・失敗・証拠・次の条件](portable-original-catalogue-burst.md)。以下は前段の履歴。

# 2026-10-28 共通スキル履歴1,618件をMetalで全照合・独立seal

`original-catalogue-initial`の元4入力を共通記録器の2,048件bankへ接続し、M5 Metal全一致・fresh GPU禁止監査でseal。入力/CPU指紋は旧4件全保持、旧成功3件の24,384,000byte完全一致。新entryは武器専用の未使用typed receipt領域へ128行以降を保存し、全行を既存decoderで比較した後に限り旧比較viewへ射影する。input115680/output2032000・Runtime138952byte/全field reflection不変、damage/時計/効果/正本/normalizer変更0。固定d90c5f9a/package3edf0819…、136unit/CPU77.54秒/GPU4.746秒/PSO62.16秒/独立89.35秒。通常sealed入口と同じ基準のCUBIN/O1+paired generation必須cache入口を登録。CUDA現実機未確認・Windows新依頼0・旧transaction再送なし。次は未実証元profile/他履歴bank/model gapを同じ選択CLIで進める。全キャラ/全特殊効果・公開GPU受付は未達。[設計・証跡・限界](portable-original-catalogue.md)。最終cache packet8a2bb6d4…は16群165unit/compile-plan policy成功、CLI関数AST/既存test/全計算source保持でnative再実行0。checkout model-checkも成功。以下は前段の履歴。

# 2026-10-28 元profile選択CLIと実履歴容量の未対応

`original-catalogue`で1,064名から1〜4件だけをprepare/compileする開発経路を実装。元266profileの全inventory recordを保持。固定4件は129unit/CPU全4成功、M5実GPU1回で3件一致、Modernia30秒はスキル履歴128件上限でstatus8。CPU実履歴1,618件が次の優先課題。係数変更と復帰は元定義から検査し、通常攻撃扱いの武器変更をskill damageと混同しない。最終guard15unitは超過をGPU前に拒否するが容量対応/全4認定は未完了。必須generation/pipeline hit・Slang0、Windows新依頼0。詳細は[元profile選択と未対応容量](portable-original-catalogue.md)。失敗packet3591b6f8…/captureは保持し再実行しない。全キャラ/全特殊効果・CUDA現実機・公開GPU受付は未達。

# Mac GPU開発引き継ぎ

2026-10-28追加：共通入口ごとの静的監査を既存`entry-inventory`へ接続。`--suite original-projectile-weapons`/`original-shield-weapons`は実`compile_coordinate_typed`、明示BODY owner、kind2/3・1対象の宣言worldを使う。元準備/KindAdmission/source逆対応/診断/禁止contextを再利用し、原effect/ownerを保つ。変換失敗は同じgroup/target-modifier lowering後の定義診断も持ち、変換前のstat/target/source identityを保持。未知policy/不一致source/axis provenance/CPU battle/GPU/上書きを拒否する。

監査は全266中、legacy world245/元座標247/宣言typed254で別の数。247との差は7carrierで、GPU対応数を増やしたのではない。12profileの失敗を13の元stat/target分類へ絞れた。multi_hit2/4のNihilister/Belortaは共通入力とgroup ownerを既に持ち、旧単体/実射撃/長時間/混成の限定証跡もある。複数論理敵への座標着弾と既定producerは別に残るため、PARTやtyped shieldを敵数へ読み替えない。次は現共通入口で受理される元profileを選択・固定・bounded実行するCLI経路を整備し、未実証条件を反復検証する。新しいprobeを既存証跡と重ねて作らない。[監査の使い方](portable-shared-entry-inventory.md)。

固定93919181/package d389bd5d…で14群143検査（11.62秒）と3入口の全監査成功。全266元定義identity/既存input SHAを保持。旧sealed packetとのpayload差分5ファイルは監査/診断/CLI/testのみで、全GPU/計算/packing/native/比較とgoldenは不変、mainの本command解析/dispatch以外の全CLI関数ASTも同じ。compiler/GPU/Windows追加0、full native sweep再実行0、compile-planはpolicyのみpassed。旧test manifestのsuite欠落2件をfixture修正し本体guardを保持した。

global model-checkは今回/旧suite packetともpinned IMPL-STATUS未同梱で実行できず、必要資料があるcheckoutで成功した。packetの成功とはしない。12profileはgeneric typed入口の失敗であり、Heavyarmsなど別専用entryの既存実証も必ず照合する。次はaccepted profileを明示選択して固定するcatalogue経路（現prepare_entriesは全prepare後にcase filterのため全profile混在では失敗候補も先にcompileする）を整備する。選択外profileを黙ってdrop/rejection成功へ置換しない。証跡 `shared-entry-inventory-v1.json`。

2026-10-28追加：`original-shield-weapons`をsealed15入力（native10/raw拒否5）に登録。shield_dmg_pctの元4carrier（レイ/アスカ/マリ/ミサト）を3/30秒の実編成/実武器/元全効果で共通座標typed owner実行器へ接続。マリ12秒/ミサト22秒は明示ハイド操作を元identity検査後に適用し、効果失効と元条件による再発動を検査する。元操作不変とは記録せず、操作overlayのcaseはoriginal_controls_preserved=False。元定義73/74/70/71、追加damage/timer/計算複製なし。全9,237着弾、最大2,457件は先頭2,048＋全streamSHAを比較する。

固定53ca72b3/packageaba59d6b…はM5 Metal＋独立fresh seal成功。86unit/CPU128.25秒/GPU3.81635秒/必須pipeline hit0.00294秒/独立149.61秒。live native/context10件再利用、独立GPU0、実GPU1/retry0。生成も必須hit/Slang0、前回projectileの生成CUDA/MSL全byteと同一、406 GPUファイル不変。未対応分類に元物理shieldのscopeを追記し、旧non-coordinate証跡の未検証範囲と新座標証跡を混同しない。`original-shield-weapons-cache-only`は同じ計算/goldenのCUBIN/O1必須＋paired generation必須。Windows追加0、実CUDA/cache hitは未確認。canonical target-world/任意world・混成/全分岐・育成/実機/公開受付/全キャラは未達。[元シールド補正](portable-original-shield-weapons.md)参照。

最終36b4304f/cache package fad27828…のunit-checkは12群117検査（6.16秒）成功。compile-plan CUBIN/O1/2GiB/60秒もpassed、実compile/GPU0。Metalとのpayload差分は依存登録/分類/CLI登録/test/goldenの5ファイルだけ。全計算・入力・native・比較ソースと全input/native期待、CLI/CPU batch関数ASTは不変のため、約128秒の全native sweepは再実行しない。fresh inventoryは266中245packing/21失敗、全キャラ0/UI CPUのまま新scopeをself/all_alliesへ記録。次は既存original-coordinate/attack-group証跡と現在のshared実行器の差分を確認し、混成/対象処理の未実行条件を優先する。同じprobeを再実装せず、未知のゲーム規則は保留を維持。最終証跡 `original-shield-weapons-final-checks-v1.json`。

2026-10-28追加：`original-projectile-weapons`をsealed13入力（native8/raw拒否5）として登録。元サクラ3/30秒、アンカー3/30秒、クレイ3/12/30秒、発射体未出現対照を、既存typed BODY owner/自動照準/元武器へ接続した。元全効果/owner/実武器/育成/configを保持し、模擬damageや別timerなし。サクラ全体7.74%、アンカー本人25.6%、クレイ全体45.05%の実条件発火と失効を意味契約にする。全5,367着弾、最大2,186件で先頭2,048件＋全streamSHAを既存比較器で検査。固定540142c4/package7fa83104…はM5 Metal＋fresh独立seal成功、58unit/CPU81.06秒/GPU3.04524秒/初回PSO62.10秒/独立97.21秒、実GPU1/retry0。406 GPUファイルは前checkpointからbyte不変、旧suite再認定とは別。

同じ計算/goldenの`original-projectile-weapons-cache-only`をCUBIN/O1必須＋paired generation必須へ登録。生成事前準備は2compiler/GPU0、実runは必須cache hit/Slang0。Metal archiveのCPU file snapshotも成功、実warm runやCUDA hitの認定にはしない。Windows既存statusはhost unavailable、新規依頼/再送0。未対応分類にprobe実証と元物理武器実証を区別して追加し、canonical target-world/Elegg nearby/実機/全キャラ/公開受付は未達のまま。次はshield_dmg_pctの元武器と現在敵fieldの未検証profileを優先し、Eleggのnearbyを削除して通さない。詳細 [元武器接続](portable-original-projectile-weapons.md)。

最終e704391d/cache package eff7ddd9…の`unit-check`10群91検査（3.87秒）とcompile-plan成功。実compile/GPU0。Metal packageとの全payload差分はreadiness/CLI登録/test/goldenの4ファイルだけで、全CLI関数AST/全計算・native・packing・比較ソース/全input/native期待は不変。fresh inventoryは266中245packing/21失敗、全キャラ0/UI CPUを維持し新しい元武器scopeを記録した。変更のない全native sweepは再計算しない。最終証跡 `original-projectile-weapons-final-checks-v1.json`。

2026-10-28ネット調査：ユーザーは実機提供ではなくネット情報での判断を指定。日英韓の公開情報を照合し、照準基準の未ロック取得/0.2秒/通常5/バースト+10/攻撃・ハイド解除を設計根拠として維持。中心vs外形vs3D、同距離順、PART候補、死亡時振替先の数値規則は得られず、現行の明示policyを実機仕様へ昇格しない。実機環境の回答待ちは解除し、他のGPU開発を継続する。新規制御実験/公式数値仕様が出るまで同じ転載の再探索は不要。計算/GPU/Windows追加0。詳細は [調査判断](portable-heavyarms-lock-selection.md) と `research/target-count-query-evidence/heavyarms-online-selection-decision-20261028.json`。

2026-10-28追加：`original-lock-health-parts` をsealed11入力（native7/raw拒否4）として登録。元Heavyarms25定義/実編成91定義を維持し、実PART2個への命中と破壊、負傷/CPR、メアリーを先に置く実編成のburst回復、回復後HP条件の真偽と5秒後の実被ダメージ、3秒後ADD出現との同居を共通実行器へ接続。静的has_partsはFalseのままでlive nodeが決める。原操作/育成/武器/configを維持し、編成変更は元bodyとして明示する。

固定338d2280/package66bef718…がM5 Metal全比較とfresh GPU禁止seal（136.12秒）に成功。11群95テスト、CPU事前照合132.43秒、実GPU2.21711秒/冷PSO9.61304秒、generation必須hit・Slang0。既存heal-share diagnosticの呼出し/配分/clamp/元heal_source/通知順204行を全比較。既存projectionはHP/adjacent_hpの観測専用通知をserializeしないため、それら全通知列の認定ではない。PARTをLock On候補へ入れる規則、距離/同距離順、死亡時振替、全分岐/他キャラ/公開受付は未達のまま。

初版718a776a…はCPU74/全11照合成功後、hostのentry登録漏れでGPU計算前に停止。消費済みclaim/失敗は保持しretry0。修正版は明示entryと完全wireを登録し、既存ガードとexact inverseを維持。共通CLIはpackage/runのCPU準備前にもexplicit wireを検査し、不明entry/幅違いを拒否する（関連79検査）。既存GPU405ファイルは前回f51bbe9eと全byte同じ、追加は既存回復logを有効化する3行のentryだけ。v1/v2の全golden/input/native期待と生成CUDA/MSL原byteも同一。

Windowsは既存status取得がhost unavailableで、再依頼/追加実行0。CUDA用`original-lock-health-parts-cache-only`は同じ計算/goldenのCUBIN/O1必須＋paired generation必須。実CUDA/CUBIN hitは未確認。追加した`unit-check`は固定packetの既存CPU unit群だけをbounded実行し、完全native事前検査/calculation/GPU認定はFalseのまま記録する。登録/監査器だけの変更確認に利用し、数値変更時のrun/sealを省かない。次は他の未対応分類/実編成を優先し、未知のLock On規則は保留を維持する。証跡 [Metal](../research/target-count-query-evidence/metal-original-health-parts-v2.json)、[HP条件](../research/target-count-query-evidence/original-mary-hp-condition-v1.json)。

登録77de10f7後の固定cache package8815c31b…を新unit-checkで13群111検査（約22.48秒）成功。CUBIN/O1/2GiB/60秒のcompile-planもpassedだが実compile/GPU0。元Metal packageとのdeltaはCLI登録/新unit command/監査分類/tests/goldenのみで、全numeric/native/packing/比較ソースと全input/native期待は不変。全native sweepは重ねない。最終証跡 `original-health-parts-final-checks-v1.json`。再inventoryは266中245packing、21失敗、全キャラ認定0を確認。次はprojectile_dmg_pctのSakura/Clay/Anchor（Eleggはnearbyも必要）を既存declared typed modifier/battleへ原定義で接続する。分類はcanonical reference gapのまま、no-op受付で成功にしない。

2026-10-28追加：`original-lock-controls` をsealed17入力（native9・raw拒否8）で登録。元全25効果/実編成91定義/実武器/育成/configを保持し、本人ハイド（取得前/充填中・本体/3ADD）、別キャラのハイド、30秒16ADDの15対象飽和を既存manual/lock/typed実行器へ接続した。ハイドは原入力identity検査後の明示操作overlayであり、元の操作を一切変えていないという主張ではない。source row2の0.35秒発火・実敵marker削除・state_end通知・再取得をCPU受動観測し、全native指紋も固定基準と一致。従来の24entryと合わせて元25entryの呼出しを観測できたが、全条件分岐/全キャラ認定ではない。

固定1754ba71、package2b01f589…がM5 Metal全比較と別fresh GPU禁止seal（94.64秒）に成功。元burstで15対象を2回snapshotし、その後5へ戻る。10群76テスト、fresh CPU事前検査90.96秒、GPU2.59235秒、warm PSO0.00227秒。生成cache/PSOは必須hit、Slang0、実GPU1/retry0、旧8caseの全input/nativeと全出力41943040byteを既存CLI `readback-retain` で保持。CUDA/MSL原byteも旧版と同一、wire/runtime不変。梱包漏れで止まったv2はCPU失敗/GPU0/claim0のまま保持し、既存AUDIT_FILESへ依存JSONを登録して梱包前停止へ改善（関連16テスト）。件数のためだけにfixture9を再生成したunitの重複を除き、同じ4テストは38.15秒で成功（以前85.91秒）。件数はCLI gate、旧8入力のbyte照合はunitと保持監査に残す。

`original-lock-controls-cache-only` は同じ計算/goldenにCUBIN/O1必須＋paired生成必須を適用する。CUDAハードウェア/実CUBIN hitは未検証。Windowsは既存transactionのstatusを1回確認したがhost unavailable、終端判定/再送/追加実行0。次は実編成のPART/負傷・回復条件を優先し、距離/同距離順と死亡時振替は未確定のまま保持。公開GPU受付・全キャラ認定0・UI CPU・20model gapは継続。証跡 [Metalと独立監査](../research/target-count-query-evidence/metal-original-lock-controls-v3.json)、[旧出力保持](../research/target-count-query-evidence/original-lock-controls-cli-retention-v1.json)、[元cover効果](../research/target-count-query-evidence/original-cover-source-activation-v1.json)。

登録bff94e61後の固定cache-only package08d237bc…でも、11群86テストと17入力/native9のfresh CPU照合が成功（GPU0）。CPU群67.18秒、元Metal計算/packing/native/比較器と全入力指紋は不変。モデル監査13検査も成功し全体未達を保持。最終証跡 `research/target-count-query-evidence/original-lock-controls-final-preflight-v1.json`。

2026-10-28更新：`original-lock-composition` を追加し、Heavyarms元全25定義、装備/共通込み本人34定義、実編成91定義を実武器・元configのまま3/30秒×本体/3ADDで実行。固定8fd51499、package0d4b4748…のnative4+拒否4がApple M5 Metalと独立GPU禁止sealに成功。9群71テスト、実GPU2.2474秒、冷PSO9.3935秒、fresh CPU比較49.34秒。13種類のnative履歴容量をclaim前に監査し、30秒の射撃742回/取得110回/配送190行/skill113行/端数通知2240行/team1120行を全行比較、省略0。既存wire内の未使用領域に5bankを割当て、旧bankゼロ・新全row/padding/tailを検査する。v1のmetadata/照会上限差分、v3の既定通知省略差分を保持、v2はGPU未実行。同claim再実行0。

CPU受動監査は各caseの全native fingerprintを固定goldenと一致させたまま、30秒で元25定義中24定義のactivation entryを観測した。未観測は元row2（cover）。entry呼出しはGPU全分岐認定ではない。次は実編成のcover入力を既存manual制御へ接続し、元row2を通す。実編成でのburst15対象飽和、parts/負傷/healのworld、距離/同距離順、死亡時振替、他キャラ/variant、CUDA実機、既存suiteのcurrent-source GPU再認定も残る。公開GPU受付・全キャラ認定0・UI CPU・20model gapは継続。

`original-lock-composition-cache-only` は同じSlang/入力/golden/比較器を使い、residentのpaired generationとCUBIN/O1のcompile cache両方の必須hitを要求する。今回のSlangは必須hit・compiler0、実CUBIN hitは未検証。旧7suite+本体106のCUDA/MSLは従来のstrict normalized SHAと全て同一。Windowsは旧transactionのstatusを1度読んだだけでhost unavailable、terminalと判断せず実行再送0。最後の旧thread/cursorはprivate continuation v31の値を保持する。詳細[合成](portable-heavyarms-lock-selection.md)、[Metal](../research/target-count-query-evidence/metal-original-lock-composition-v4.json)、[未発火条件](../research/target-count-query-evidence/original-lock-native-activation-coverage-v1.json)。登録7b31389c後の固定packetも通常72検査/cache profile81検査とnative4・入力8のfresh CPU事前検査に成功。最終証跡 `research/target-count-query-evidence/original-lock-final-preflight-v1.json`。以下は履歴。

2026-10-28更新：元の敵ロック定義を共通actor carrier実行器へ接続した `enemy-lock-carriers` を追加。元index0/1/2/6/20を保持し、自己向けmarkerへ置き換えず、敵への名前付き状態・被ダメージ増加・解除まで比較する。固定32630ddf、package eee19024…の7入力（native4・拒否3）はApple M5 Metalと独立GPU禁止sealに成功、53テスト、GPU0.05085秒、Metal PSO必須hit。死亡でrecipientが空になった実敵carrierの誤分類は、native観測器で保持済みのimmutable受け手IDを使い修正し、空carrierを含む全行を保持した。失敗5capture（診断wire拒否1はGPU未実行）も保存。Windows追加0、同claim再実行0。CUDA cache-only経路は同じgolden/実装を参照し、standaloneの既存CUBIN必須hit規約を使うが、実CUDA/CUBIN hitは未検証。

旧6スイートと本体106のCUDA/MSL生成は従来のstrict normalized SHAと同一。source inverseも完全一致ledgerで保持する。ただし共通sourceのcurrent-mapは変わったため、旧GPU goldenを新sourceへ黙って更新しない。新sourceでの旧GPU再認定は未完了。次はこの敵carrier接続を既存の順番攻撃/typed projectile合成へ適用し、元全25定義を実行する。候補は明示body/spawn-order providerであり、距離規則と死亡時振替の実機認定は未完了。公開admission・全キャラ認定0・UI CPU・20model gapの境界を維持する。詳細[Lock On接続](portable-heavyarms-lock-selection.md)、[Metal証跡](../research/target-count-query-evidence/metal-enemy-lock-carriers-v4.json)。登録後の固定953a3416では通常54検査・CUDA cache profile63検査とnative4がCPU事前検査成功。CLIモデル監査も成功し、全体未達を維持。最終証跡 `research/target-count-query-evidence/enemy-lock-final-preflight-v1.json`。以下は履歴。

保存結果のfresh分割監査をCUDA／Metalで共通化。`saved-battle-audit`、`aggregate-native-groups`、Windowsの1群限定`audit-native-group` stageを追加した。元own CLI／比較器を別fresh childで実行し、全case・全raw SHA・元manifest／capture／controller anchors、重複・欠落・bool整数混同を検査する。部分結果は全体成功にしない。Metalの旧gate/schemaを保ち、CUDAは計算transportとサービス保全を分離する。実装`1fdab95a`、境界強化`834a0fda`。固定v1で保存Metal4入力を2+2へ分け、各fresh比較約12.3／12.7秒・GPU追加0で全entry/input/output/生成物が独立sealed goldenと一致した。最終v2は選択62／共通604検査（Windows専用1skip）成功、GPU／保護CPU／golden不変。Windows新stageは未実行、現4入力CUDAを再実行しない。[共通監査](portable-shared-native-groups.md)、[Mac実証](../research/shared-native-group-evidence/metal-four-v1.json)。全106 CUDAの起動前native63を短いJobへ分けるtransactionは次段階で、通常preflightはまだ省略・変更していない。Heavyarms元25効果はLock On markerだけでなく対象数追加とtyped敵弾への攻撃を要する。対象数を無効statへ置換して全対応とせず、専用対象数／空間選択モデルを整える必要がある。全キャラ0／20model gap／UI CPU／全体未達は継続。以下は履歴。

共通CLIに`recover-readback`とWindowsの同名CPU stageを追加。保存CUBINの子が正常終了し、親が比較中にouter timeoutとなった場合に、元capture・消費済みclaim・欠落記録を保ったまま別監査へ回収する。元own CLIのfresh比較・出所・全raw・Job・観測を再利用し、再GPU／compilerはない。旧compactを新registryで検証した初版不具合は修正済みで、byte bootstrap後に旧own registryで完全検証する。固定v3の選択62検査と実旧e72パッケージ検証がMacで成功、共通制御はv2で598検査（Windows専用1skip）。GPU／保護CPU／golden不変。公開source packetは`research/windows-source-packets/readback-recovery-v3.*`、実装`09a9467a`、配布`f2099375`。[回収CLI](portable-readback-recovery.md)。Windowsの私的captureと結果はGitへ入れない。全106 CUDA認証・公開受付・全キャラ認定は未完、残20model gap／UI CPUを維持する。全106へ広げる際はfresh native63の予算とGPU実行を明示的に分ける設計が必要で、通常preflightの省略やCPU値cacheは導入しない。以下は履歴。

resident arc本体106はMetal独立認証済み、CUDA計算は未実証。PTX固定942b009e…はWindows共通tests207が成功しましたが、smokeはcompiler profileのCPU worker既定60秒で34/60群・354検査までで停止（実行済み群のfailure/error0、未完了）。generation／PTX compile未着手、同packetのclaimを保持。既知Windows smoke約84秒に合わせ、共通smokeのCPU予算を既存上限180秒内で明示分離した固定33415559…を準備。Mac共通tests207／smoke586成功、必須生成cacheはv1と同じkeyでhit・Slang0、PTX plan成功。Windowsでは新v2だけを次に確認します。compiler child60秒／2GiBと旧CUBIN claimsは不変。Macでは元25効果Lock Onをboss／3ADDの4CPU契約へ拡張し、自然named query0/0/88/820と元定義・全結果・射撃履歴を検査。旧2契約の結果と266profile入力／issue／順位を保持、245変換・20model gap・全キャラ認定0・UI CPUは継続。汎用markerは存在し、専用空間選択／対象数拡張／full25 typed GPUが未完という分類に明確化。[現在の契約](portable-coordinate-resident-arc.md)。以下は履歴。

共通resident arcの全106入力は修正版58daee47…でM5通常検証に成功しました。GPU4.240秒、子72.407秒、Runtime reflection不変。独立監査も536.437秒で全106入力に成功し、sealed登録しました（7群・fresh native63・追加GPU0）。旧prefixの差は既存trace参照20語のcase-base移動だけで、残り861,567,920byte一致・新tail全0を専用監査で確認しました。wire事前検査・狭い修復器・保持監査をCLI化し、共通制御580（Windows1skip）が成功。Windows CIMは正規承認contextで取得成功、新着弾40の固定通常／cache-only packetはCPU47／54検査成功。Windowsの着弾40/native26はCUBIN必須cacheで実launch／sync／readback成功、Metal保存golden全byte指紋と一致、NVRTC／compiler library要求0。STACK199352→2880byteをoffline確認。サービス識別は未確認のためCLI全体exit2／preservation未確認を保持し、本体106のCUDA成功とは区別します。計算一致／preservation／全キャラ認定は別の証拠として扱います。[wireと監査](portable-wire-preflight.md)。以下は履歴。

開発profile `coordinate-resident-arc` を共通戦闘実行器へ接続しました。既存全106入力（native63／拒否43）とCPU指紋を保持し、出力tail32,786語を追加、Runtime reflectionは旧版と完全一致。関連140／制御555成功、固定ae70b296…の通常Metal検証が進行中です（まだsealedではありません）。Windowsのprocess観測は既定／明示pwshとも失敗し、compiler/GPU0。有限operation/type/error-family IDのCPU診断を追加、制御559成功。raw／claims／旧失敗を保持。[接続と現在の検証範囲](portable-coordinate-resident-arc.md)。以下は履歴。

共通arc区間のresource view版を追加し、M5 Metalでarc140／着弾40を全word照合・fresh独立sealしました。旧arc135／着弾40のinput/nativeとlogical出力hashを全保持し、1024区間・127対象・5098cutを維持。Windows旧CUBINのSTACK199,352byteとcache-onlyでもlaunch code2の失敗を保存。次は新sourceの短いcompile-only／offline資源検査でstack量を確認し、その後にCUDA実行を判断します。現resident106本体・公開UI・全キャラ対応は今回変更していません。[配置と検証範囲](portable-coordinate-arc-arena.md)。以下は履歴。

通常の元武器による実射撃をtyped対象へ共通接続。sealed `coordinate-typed-weapon`46（native29／拒17）がM5 Metal・GPU禁止fresh監査131.445秒で全一致。散弾内handle固定／次射撃再選択、canonicalとの奥行きmerge、RL critical共有、親量と実着弾順、history2457件（保持2048＋全件SHA）を確認。旧35全284480000byte／input/native保持。既存Python観測filterで全46指紋を保ちCPU269.180→104.266秒（2.58倍）。関連74／制御488成功（Win1skip）、GPU1／retry0、GPU3.861秒／初回PSO93.762秒。生成必須cache hit・run追加Slang0、Runtime追加0。finalは配置監査・対応metadata・seal登録だけで計算／proof関数ASTを保持、再GPU0。raw全byte／SHA／inode保持の疎化で364113920byte回収。現CUDA／typed auto aim／canonicalゲーム仕様／全キャラ0／UI CPUは未達。[通常射撃のtyped接続](portable-coordinate-typed-weapon.md)。以下は履歴。

座標通常射撃→型付き対象のCPU契約を共通CLI `reference --suite coordinate-typed-weapon-common` へ追加。元の武器・効果を保持した6ケース、661実ペレット／666packet／typed278、散弾内世代固定・次射撃再選択・RL critical再利用・full_charge親量／通知後着弾・MT全624語を確認。fresh不変packageでCPU契約2.923秒、関連64／制御488成功（Win1skip）。旧35入力16,195,204byte・全356Slang・保護8file保持。GPU／Windows新実行0、型付き通常射撃のMetal接続は次段階。canonicalゲーム仕様／typed auto aim／全キャラ0／UI CPUは未達。[通常射撃CPU契約](portable-coordinate-typed-weapon-reference.md)。以下は履歴。

共通CLIに `package --develop --native-baseline-package PATH` を追加。CPU依存／入力／caseが完全一致する固定基準から期待hashだけを引き継ぎ、GPU sourceと検査済みSlang ledger current部の変更だけを受付。runtime値／旧GPU出力は引き継がず、fresh preflight／独立seal・Windows制約は不変。実35入力pack3.482秒（native基準関数禁止）、通常CLI同一ID、runで22nativeを177.031秒で再計算して一致。関連60／制御488成功（Win1skip）、新GPU0／Windows0。8負例・境界検査とスキル手順を追加。GPU本体は実照準35から変更なし。次は通常武器のtyped命中・型付きauto aim、現CUDA/cache検証。全キャラ0／UI CPU／未達。[CPU期待基準の再利用](portable-development-expectations.md)。以下は履歴。

固定pointに続き、正本の実照準bankを共通型付きスキルselectorへ接続。sealed `coordinate-typed-live-aim`35（native22／拒否13）がM5実GPU1回・独立GPU禁止監査203.872秒で一致。auto、スキル前／同フレームの照準切替、HPシールドを実証。照準操作は元編成の照合後に明示overlayし、元操作保持とは区別。旧28全227,585,000byte／input/native保持、旧164 shader source保持で旧compile/GPU0。関連60／制御480成功（Win1skip）、GPU2.360秒／初回PSO92.612秒、生成必須cache hit・Slang0。通常武器命中／型付きauto aim／移動・貫通・現CUDA・全キャラ0／UI CPUは未完。CPU基準のpackage/run重複計算が効率化候補。[実照準の接続](portable-typed-live-aim.md)。以下は履歴。

型付き対象の固定point／円・回転矩形selectorを共通DFSへ接続。`coordinate-typed-geometry`28（native18／拒否10）はM5実GPU1回と独立GPU禁止監査166.167秒で一致。生存・奥行き／生成順・破壊／期限／再出現世代・HPシールドを実選択してdamage/receiptへ渡す。既存10入力・nativeと81,280,000byte出力、旧型付き入口CUDA/MSL/reflection全byte保持。関連56／制御480成功（Win1skip）、生成必須cache hit・Slang0、GPU2.322秒／初回PSO92.864秒。wireとRuntime不変。通常武器auto aim／移動・射線・貫通、正本の敵弾／shieldルール、現CUDA、全キャラ0／UI CPUは未完。次は固定pointスキルから元武器とlive aim consumerへの接続。[形状と対象選択](portable-typed-geometry.md)。以下は履歴。

武器skill指定と乱数BODY／ADD receipt groupを共通実行器で実証。sealed coordinate-sampled-delivery136（CPU正本126／拒10）がGPU禁止replay・独立sealで全一致。新14契約、CPU95／制御428（Win1skip）、旧120全849346560byte保持。GPU／compiler／transport／数値ソース変更0、旧13 CUDA-MSLペアを保持し生成cache hit・Slang0。Metal実archive hitでPSO91.958→.002588秒、GPU.480秒／子3.491秒。実GPU1／host修正版再GPU0。観測hookのcode identityを修正し、metal-cache-probe、package前の監査データ検査、準備64MiBの容量余裕を追加。現CUDA未取得／Windows新依頼0。手動cover・追加武器／回復混合・全元定義は残る。全キャラ0／20gap／UI CPU／未達。[乱数groupとcache](portable-coordinate-sampled-delivery.md)。

乱数戦闘へ既存の武器変更／HP・遮蔽物回復／現在HP減少を接続。sealed coordinate-sampled-vital120（CPU正本112／拒8）がM5 Metal全一致・独立seal。新29契約、CPU63／制御421（Win1skip）、旧89全629932032byte・旧12 CUDA-MSLペア保持。実総口と初弾係数を受動観測し親量を検査、damageスキルなしの整数総計初期化漏れを修正。新GPU2／retry0、GPU.491秒／初回PSO91.958秒。容量追加0、通常run内のCPUゲートを使い事前CPUの重複を避ける。手動cover packing・追加武器flag／回復混合・sampled group・全元定義は残る。現CUDA未取得／Windows新依頼0、全キャラ0／20gap／UI CPU／未達。[武器変更と回復](portable-coordinate-sampled-vital.md)。

乱数保留バーストの旧B3／opt-inを共通residentへ接続。sealed coordinate-sampled-burst89（CPU正本83／拒6）がM5 Metal全一致・独立seal。新24契約、旧62全373817344byte prefix・追加zero、旧11 CUDA-MSLペア保持。CPU55／制御421（Win1skip）／正本24。512entry×256hit bankを明示し出力+1MiB、Runtime不変。旧B3のbuff除外setterとmarker受付を修正し、修正前失敗保存・新GPU2回／同claim retry0。GPU.486秒／初回PSO92.568秒。異strideのreadback-retainを共通CLIへ追加。現CUDA未取得／Windows新依頼0。武器変更／heal・sampled group・全元定義は残る。全キャラ0／20gap／UI CPU／未達。[保留バースト](portable-coordinate-sampled-burst.md)。

通常damageのhit別critical・cast snapshot・子queueを共通residentへ接続。sealed coordinate-sampled-skill62（共通CPU59／拒3）がM5保存結果replay・独立sealで全一致。実GPU1／比較修正版の再計算0。CPU43／制御419（Win1skip）／正本22、旧38全229113856byteと旧10 CUDA-MSLペアを保持し旧拒否1件を正例へ移行。数値probeは125→4ソースへ独立し14045入力実証、生成コード／全449440byte保持・Metal cache hit。replay容量ゲートと保存版registry監査をCLIへ追加。保留バースト・武器変更／heal・sampled groupと全元定義は残る。現CUDA未取得、全キャラ0／20gap／UI CPU／未達。[乱数スキルとCLI](portable-coordinate-sampled-skill.md)。

乱数物理射撃の親参照量を共通residentへ接続。sealed coordinate-sampled-parent39（共通CPU36／拒3）とpacket-ratio14045がM5 Metal全一致・独立seal。整数128bit÷muzzleを一度だけnearest-even丸めし、dealt_fixed_damageの既存通知／queueへ接続。大整数の旧double総計差も実計上の整数sidecarで解消し、従来double加算の検査を保持。CPU28／制御416（Win1skip）／正本16、旧23全138674176byteと旧9 CUDA-MSLペアを保持。容量追加0、実GPU計4／同claim retry0／raw削除0。戦闘GPU.464秒／初回PSO92.693秒、数値cache hit・GPU.002秒。現CUDA未取得／Windows新依頼0。通常damage RNG・武器変更／heal・sampled group owner・全元定義は残る。全キャラ0／20gap／UI CPU／未達。[親参照量・整数総計](portable-coordinate-sampled-parent.md)。

乱数物理射撃を共通resident executorへ接続。sealed coordinate-sampled-battle23（共通CPU20／拒3）がM5 MetalのGPU禁止replay・独立sealに成功。1256ペレット／1397packet／5498 MT word、127対象・1024ペレットを検査。物理MTとboss MTを分離し、shot snapshot・個別critical・auto／charge通知・muzzle core平均・not_core／prob条件抽選を接続。期待値scratch再利用でRuntime138952byte／入力109528／出力1507328word不変。GPU.448525秒／初回PSO91.909787秒。1024件のteam履歴省略を厳密検査する比較viewへ修正、実GPU計2／修正版再計算0／retry0。旧11raw全66322432byte・旧8 CUDA-MSLペア保持。現受付buffのみ、非buff・親量・sampled group ownerと全元定義は残る。現CUDA未取得／Windows新要求0。全キャラ0／20gap／UI CPU／未達。[乱数射撃の接続](portable-coordinate-sampled-battle.md)。

乱数着弾点の共通producer coordinate-sample-v1を既存MT19937へ接続。sealed coordinate-sample107（共通CPU93／拒14）、1296点がM5 Metal全bit一致・独立seal。MT全624状態／index／消費・拒否数／後続抽選を照合、GPU1回.018514秒／PSO.278665秒／retry0。実CPUのrandom経路11契約で63ペレット／77packet／362wordとcritical再利用を確認。最終CPU12／control416（Win1skip）、旧10閉包193sourceとmixed244 current seal保持、旧GPU再実行0／Windows0。非residentのgeneration cacheは既存reflection guardで開始前停止し、guard不変の通常生成を使用。GPU戦闘callerは未接続。次はphysical専用MT状態→per-pellet core／crit／通知→個別snapshotとgroup delivery。全キャラ0／20gap／UI CPU／未達。[乱数着弾点と正本契約](portable-coordinate-sampling.md)。

座標弾・groupへ有効なsplit_damageとbuff／shield／vanish／move／groggy／直接boss attackを合成。sealed coordinate-mixed244（共通CPU218／拒26）がM5 Metal全一致・独立seal、正例8484 frame、旧225全1356595200byte保持。均等配分・ADD途中消滅・対象順位／seed選択・tie偶数丸め／ゼロ丸めを含む新19契約。旧shareは現parserのnative_reference_exclusionとし、有効splitの移植と区別。距離モード切替と別PART packet診断traceを共通コードで修正し旧7 CUDA-MSLペア全byte保持。CPU149／control416（Win1skip）、修正版GPU3.724秒／初回PSO91.484秒。修正前旧sourceのwarm必須cache hitは.002612秒。CPU上限60停止はdispatch0、v3失敗／v4成功の実GPU計2／同claim retry0、原本保持。現CUDA未取得。次はsampling RNG・召喚攻撃／debuff payload・全元定義認定。全キャラ0／20gap／UI CPU／目標未達。[混在worldと割合配分](portable-coordinate-mixed.md)。

座標physical packetの実receiptを共通groupへ接続。sealed coordinate-group225（共通CPU199／拒26）がM5 Metal一致・GPU禁止replay・独立seal。旧206input／native182保持、8060正例frame、追加17の112group／186packet／134receipt／111通知を比較。allocation／sealは既存snippet共有、compact186528wordを1310720へ移設しoutput1507328word、全stride／clear／実slotを接続。BODY／ADD native再選択、PART／INTERRUPT除外、閉集合child／91射撃履歴を実証。旧readback全1080033280byte検査、差165wordは解除済みActor setだけ、他領域保持。旧6 CUDA-MSLペア全byte保持。初回Swift strideでdispatch前停止、v2 dispatch後decode4件停止を保存し比較器だけ修正、実dispatch1／GPU再計算0／同claim retry0。GPU3.718秒／初回PSO91.531秒／shared103.213秒、Slang0。最終CPU140／control416（Win1skip）、現CUDA未取得／Windows依頼0。次はRNG／割合配分・未検証混在scene／全元定義認定。全キャラ0／20gap／UI CPU／目標未達。[座標GPU group](portable-coordinate-group-gpu.md)。以下は履歴。

座標physicalの異量・複数対象packetを既存group observerへ明示opt-inで接続し、共通CPU17契約をCLIへ登録。112group／186packet／134receipt／111通知、BODYだけのdedup・PART／INTERRUPT除外・ADD途中破壊・閉じた集合のchild・2射手・91射撃履歴を確認。default false／native routing限定、正本不変。新8＋旧group31を共通CPUゲートへ登録（計134）、制御416（Win1skip）。source改変検出2分岐とmissing-consumer既定値監査の失敗を保存して修正。model-check分類はadapter_gap→gpu_port_gap。GPU shader／wire／旧golden／cache変更0、新GPU0／Windows依頼0。次はgroup begin／collect／sealを座標receiptへ接続、compaction移設とclear／host stride、BODYのADD routingとscene-pool同居。現GPUはgroup受付拒否、全キャラ0／20gap／UI CPU／未達。[group正本契約](portable-coordinate-group-reference.md)。以下は履歴。

武器変更・動的reload・散弾・tap／holdと照準を共通executorへ合成。sealed coordinate-control206（共通CPU182／拒24）がM5 Metal一致・独立seal、正例7878frameを検査。base武器reload時間とlive ratioによるclip分類／照会順を新profileで修正、正本不変。旧190input／native166／raw全996147200byte保持、旧5系統の生成CUDA-MSL全byte保持。新GPU1成功／retry0、GPU3.739秒／初回PSO90.528秒／shared100.593秒、Slang0。最終CPU95／control416（Win1skip）、full3072→compact1763全残存byte一致。raw削除0、全SHA-byte-inode保持で2024034304byte回収。model-checkでgroup writerの実3重複と容量保持の1507328word移設案を監査。移設・clear・physical group receipt・ADD共有・transport登録は未実装。Windows追加検証0／現CUDA未取得。次は実group writer/caller統合→RNG／混合scene／全元定義。全キャラ0／20gap／UI CPU／目標未達。[操作合成とgroup残件](portable-coordinate-control.md)。以下は履歴。

手動aim／camera調停を共通complete executorへ接続。新coordinate-aim190（共通CPU166／拒24）がM5 Metal一致・独立seal。要求合流／4window／5anchor／gate／動的reload／focus sequence／shared camera／前回点を読むskillと今回点を読むphysicalを実証。7059frameを2種digest＋数＋最終bank、全戦闘／packet／cacheを比較。input109528／output1310720、CF_END〜GC_BASEの160wordを実consumer監査、Runtime stride138952保持。旧151input prefix／native136／新領域を除く791578240byte保持。初版26差分（auto上書き／span欠落）を保存して修正、v2 CPUのみ、v3成功。GPU2／retry0、GPU3.699秒／PSO91.078秒／execute100.810秒、Slang0。旧81／97／120／133 CUDA-MSL全byte保持、現CUDA/cache実hit未取得。最終CPU90／control416（Win1skip）、full3062→compact1753全残存byte一致、model-check成功。raw byte-SHA-inode保持で2970705920byte回収／削除0。Windows snapshot rev78 idle・新依頼0。次は武器変更等との合成・group／ADD writer/caller統合→RNG／scene混在／全元定義。全キャラ0／20gap／UI CPU／目標未達。[共通GPU照準](portable-coordinate-aim-gpu.md)。以下は履歴。

手動照準の正本30契約を共通reference CLIへ追加。1652frame／実照会206、4window／5anchor／動的reload減算／gate／優先度edge／生存fallback／共有camera／実破壊／全バースト追従をCPU検査。定時skillが前回照準、調停後physicalが新照準を読む同frame差3件を保持。静的aim IRは元normalizerを再利用し、live default priority／全clock式／他操作軸を残す。GPU caller／clock接続は未完了・受付拒否を維持。最終CPU85／control416（Win1skip）、full3052→compact1743全残存byte保持、旧151input／golden／GPU source保持、生成cache必須hit／Slang0。新GPU0／Windows依頼0。詳細8.2MBはローカル保持・共有summaryと失敗履歴を保存。次は要求合流→照準bank→前半skill／後半physical caller接続。全キャラ0／20gap／UI CPU／目標未達。[照準接続契約](portable-coordinate-aim-contract.md)。以下は履歴。

範囲スキルのhost trig入力を共通数値IRへ接続。新coordinate-matrix151（共通CPU136／拒15）がM5 Metal一致・独立seal。旧cache133全input／全raw697303040byte保持、新18worldで軸／隣接float／負角／巨大角・命中境界を実戦比較。旧host本体2000＋部位3000→共通本体2000のみとなる境界を明示しcanonical CPUは不変。CUDA/MSL両reflectionとgeneration identity保持、Slang0・生成／Metal pipeline必須hit。GPU3.713秒／PSO.002616秒／execute7.535秒、速度倍率未主張。最終CPU78／control416（Win1skip）、full3047→compact1738全残存byte一致、model-check成功。GPU1／retry0／Windows追加0、raw SHA-byte-inode保持で563281920byte回収／削除0。現CUDA未実証。次はmanual aim／camera layer2→RNG／group・ADD／scene混在／全元定義。全キャラ0／20gap／UI CPU／目標未達。詳細[共通area matrix](portable-coordinate-matrix-common.md)とresearch/portable-coordinate-matrix-checkpoint.json。以下は履歴。

Geometry小数6桁key＋共有dictを共通実行器へ接続。coordinate-round9046（正9039／拒7）とcoordinate-cache133（共通CPU118／拒15）がM5 Metal一致・独立seal。uint128で正確decimal6丸め、signed-zero key正規化、最初の実Landing保持、全射手共有、Geometry変更時だけ切替。query無しの切替、世代のみ更新、同径core、完全hash照合／全entry／代表署名／tail検査。127対象は容量231、対象0は4096、超過は明示拒否しevictionしない。旧120入力／元native保持、戦闘・bank・packet全559672320byte一致（新cache／作業scratchは別profile）。正例GPU照会878＝hit515＋積分363、既存template再利用146は別。GPU全133で3.682秒／PSO90.408秒／execute99.236秒、速度倍率未測定。通常81／97／core120のCUDA/MSL全byte保持、別GPU再実行0／現CUDA/cache実hit未取得。CPU72／control416（Win1skip）／model-check成功、full3041→compact1732全残存byte一致、保護7維持。GPU3（丸めstatus不一致1／成功2）retry0、cache GPU1、CPU初版guard-message失敗は保持。raw2件をbyte-SHA-inode保持疎化、1724448768byte回収／削除0。Windows read-onlyでidle revision78、追加依頼0。次優先area matrixのhost math.cos/sin lowering共通化→manual aim／RNG／group・ADD／scene混在／全元定義。全キャラ0／20gap／UI CPU／目標未達。詳細[Geometry cache](portable-coordinate-cache.md)、research/portable-coordinate-cache-checkpoint.json。以下は履歴。

live coreを共通実行器へ接続。新coordinate-core120（共通CPU106／拒否14、追加core28＋IR拒否8）がM5 Metal一致・独立seal。world graphの開閉／再出現／startを再利用し、最大径→同径で新start→後宣言、base原点、既定照準core追従を実装。127対象＋core／32node、遮蔽・貫通・爆発・通知・親量・範囲skillを照合。入力108648＋静的144word=108792、出力1310720。旧84のinput prefix・native／raw全440401920byte保持。全720pellet／2037着弾。初版2差分（RL入力不整合／部位skill trace）を保存して修正、GPU2／retry0。修正版GPU.247秒・PSO90.561秒・execute95.164秒、Slang0。通常81／97のCUDA/MSL全byte保持・別GPU再実行0・現CUDA/cache実hit未取得。最終CPU59／control416（Win1skip）／model-check成功、full3024→compact1715全残存byte一致、保護7保持。raw3件をbyte-SHA-inode保持疎化、2294730752byte回収／削除0。Windows追加0。次優先Geometry丸めcache key、その後aim／RNG／group・ADD／scene混在／全元定義。保存結果の厳密再結合CLIは候補・未実装。全キャラ0／20gap／UI CPU／目標未達。詳細[live core](portable-coordinate-core.md)、research/portable-coordinate-core-checkpoint.json。以下は履歴。

座標物理の蓄積放出を既存take／split／整数化／queueへbody-only receiptで接続。新coordinate-accum-emission84（共通CPU78／拒否6）がM5 Metal一致・独立seal、旧31全input/native/output entry保持。既存49蓄積world＋新4geometry world、全622pellet／1845着弾／46放出。ADD共有2件・敵攻撃1件はscene受付外として未対応保持。GPU1／retry0／Windows追加0、GPU.243秒・PSO91.803秒・実行時Slang0。通常81／97生成CUDA/MSL全byte保持、旧GPU再実行0／CUDA実hit未取得。最終CPU53／control416（Win1skip）、model-check成功、full3013→compact1704全残存byte一致、保護7維持。旧81証明書のcurrent仮定によるcontrol失敗を保存、exact inverseで履歴監査＋現source拒否負例を追加し旧proofは昇格せず。raw3件をbyte-SHA-inode保持疎化、649306112byte回収／削除0。次優先live core、その後Geometry cache／aim／RNG／group・ADD／敵攻撃scene／全元定義。全キャラ0／20gap／UI CPU／目標未達。詳細[蓄積放出](portable-coordinate-accum-emission.md)、research/portable-coordinate-accum-emission-checkpoint.json。以下は履歴。

座標物理full-charge親参照量をuint128整数和→pellet乗算→binary64一度丸めで接続。M5 Metalでpacket-integer305（正294／拒11）、coordinate-quantity31（共通CPU25／拒6）一致・独立seal。旧23全entry保持、87pellet／214着弾packet／11通知。固定子body-only receiptと次frame着弾を接続。初版29の時刻誤り1captureは保持して修正。旧81／97もMetal・独立seal、全entry保持、生成CUDA/MSLをpre132全byteへ復元、生成cache＋PSO必須hit。CUDA cache実hit・現計算は未実証。最終CPU37／control416（Win1skip）、full3006→compact1683全残存byte一致、保護7維持。新GPU5（成功4／失敗1）／retry0、容量guard1はGPU前、raw4件をbyte-SHA-inode保持疎化で1086881792byte回収／削除0。Windows再送はAPI active turn不在で拒否・開始未確認。part蓄積はCPU正本にもconsumerなしと3world確認、native_reference_exclusionへ分類訂正（ゲーム仕様未確認）。次優先は座標蓄積放出body-only receipt、live core、Geometry cache／aim／RNG／group混在／全元定義。全キャラ0／20gap／UI CPU／目標未達。詳細[整数参照量とcache保持](portable-coordinate-quantity.md)、research/portable-coordinate-quantity-checkpoint.json。以下は履歴。

座標物理の共通着弾→packet捕捉→通知→着弾をresident実射撃へ接続。新coordinate-physical23（共通CPU17／拒否6）がM5 Metal成功・独立seal、52pellet／100packetの全戦闘decoderと順序付きtraceを照合。散弾・2銃口・貫通・charge・回転矩形・crit・accuracy・2射手・破壊・interrupt補正・武器変更を実証。旧97／81も現sourceでMetal／独立seal、input/native/raw全byte SHA保持。生成CUDA/MSLはspread抽出で変更、新指紋とfull compiler証明書を独立監査後に更新。GPU4／retry0、warm23は生成cache＋PSO必須hit・Slang0・GPU.132秒／execute1.25秒（初回PSO90.84秒）。最終CPU27／control416（Win1skip）、full2986→compact1663全残存byte一致、保護7source維持。監査3失敗を保持しexact inverse／証明書を修正。raw3件を全byte-SHA-inode保持で疎化、1896841216byte回収／削除0。Windows追加0／現CUDA未実証。次優先は全packet整数和のfull-charge参照量とparts蓄積、通常経路生成byte保持によるCUDA cache再利用。live core／丸めGeometry cache／aim／RNG／group同時／原定義混在は未完了。全キャラ0／20gap／UI CPU／目標未達。詳細[座標物理GPU接続](portable-coordinate-physical-gpu.md)とresearch/portable-coordinate-physical-gpu-checkpoint.json。以下は履歴。


共通CLI `reference --suite coordinate-physical-common` を追加。共通着弾規約を実際のCPU物理packet・通知・破壊へ接続し9world／27pellet／47packetを検査した。完全遮蔽の旧0damage本体packetとの差、別frameの正残差packet保持、同射撃snapshot固定（6×1000→次射撃6×7000、part通知11）を明示。旧CPU／passive観測器／GPU283source／保護7source不変。selected36／control416（Win1skip）、full2976→compact1643全残存byte一致、model-check成功。初回監査資料梱包漏れを保持し修正済み。新GPU0／Windows追加0／cache変更0。resident物理へのGPU packet・fraction通知・着弾接続は未完了、body-only制限／全キャラ0／20gap／UI CPU維持。詳細[共通規約の物理CPU比較](portable-coordinate-physical-common.md)とresearch/portable-coordinate-physical-common-checkpoint.json。以下は履歴。


共通の可変指数unit pow・GL10定数・形状arcをexpected landingへ接続。sealed `coordinate-power`909（共通CPU898／拒否11）と`coordinate-landing`40（共通CPU26／拒否14）がM5 Metal全word一致・独立seal、MPFR2434入力0 ULP。127対象／5098cut／1024arcを保持し、初版pipeline stack失敗を出力arenaと参照渡しで解消。形状準備をGPU内で一度だけ行い、旧全1715850byte保持・新準備データ照合、GPU17.130→.424秒（単一probe測定対約40.4倍）。最終CPU17／関連・制御462（Win1skip）、full2969→compact1636全byte一致。新kernel3／pipeline失敗1／同claim再試行0、旧主要7suite再GPU0。raw全SHA-byte-inode保持の疎化で1096093696byte回収。Windows新要求0、API active ID不在・CUA Codex安全制約で未送達。物理packet／resident戦闘caller／RNG／aim・cache key／全元定義と公開受付は未接続。全キャラ0／20gap／UI CPU／目標未達。詳細[共通着弾確率](portable-coordinate-landing-v1.md)とresearch/portable-coordinate-landing-v1-checkpoint.json。以下は履歴。


共通数値profileをGPU側の角度→回転係数→形状距離／contains／円・半平面・grow付き回転矩形arc／区切り半径へ接続。sealed `coordinate-geometry`1224（共通CPU1209／拒否15）がM5 Metal全word一致・独立seal。旧正本と方針不変の288入力を距離／breaks照合し、別方式Decimalの円弧内外200点超も成功。最終CPU18／関連・制御445（Win1skip）、full2950→compact1621全残存byte一致。GPU1／retry0／旧6suite再GPU0。GPU .188791秒、Swift module cache利用でexecute全体1.722503秒。Windows新要求0、直前の数値依頼はAPIエラーで未送達。積分／pow・GL定数規約／物理packet／resident戦闘caller／全元定義・公開受付は未完了。全キャラ0／20gap／UI CPU／目標未達。詳細[共通形状・円弧](portable-coordinate-geometry-v1.md)とresearch/portable-coordinate-geometry-v1-checkpoint.json。以下は履歴。

数値基準はユーザー明示回答で「決定的な共通規約」に選定。選択fixtureと監査をgpu_numeric_implementation_gapへ更新し、共通profile実装／公開受付は未完了として保持。共通Slangに正period剰余・arc wrap／shift／measureと生成被覆の差／交差を追加、既存Sum/addSumを直接再利用しevent_runtime本体不変。極小負剰余→2π、幅0区間→差集合2区間、補償1ULPを保持。640入力（native632／拒否8）がM5 Metal一致・独立seal、旧600input/nativeと9849600byte保持。各shift反復の1024区間コピー3回をactive挿入へ変更し全640raw10506240byte一致、今回GPU2.516秒→.036585秒（probe測定約68.8倍、CLI全体比ではない）。最終CPU18／制御416（Win1skip）、full2938→compact1611全record/byte保持。kernel4（成功3/失敗1）・容量guard1/同claim再試行0・Windows要求0。opcode5負例の衝突は失敗保持して8/9へ分離、CPU重複検査追加。過去raw2件をSHA/全byte/inode保持の疎化で2212257792byte回収、削除0。旧135/97/88/81閉包と保護7source/cache規約不変、再GPU0。次は共通三角関数・範囲縮約とCPU参照のversioned規約を定義し、幾何arc→積分→物理packet→resident本体へ接続。全キャラ0／20gap／UI CPU／目標未達。詳細[円弧数値演算](portable-coordinate-arc-scalar.md)、research/portable-coordinate-arc-scalar-checkpoint-v2.json。以下は履歴。

決定的な共通数値profile `coordinate-binary64-v1`のsin/cos・atan2・acos・整数sqrtを共通IRからCPU／Slangへ実装。sealed `coordinate-numeric`2783（共通CPU2771／拒否12）がM5 Metal全word一致・独立seal、独立Decimal10451入力は最大1/1/1/2/0 ULP。共通CLI `numeric-audit`追加、最終CPU9／関連・制御436（Win1skip）、full2944→compact1614全残存byte一致。新GPU1／retry0、旧5suite再実行0。CUDAの新規計算実証は未取得。回転caller・arc生成・積分・物理packet・共通resident戦闘への接続と公開受付は未完了。全キャラ0／20gap／UI CPU／目標未達。詳細[共通数値v1](portable-coordinate-numeric-v1.md)とresearch/portable-coordinate-numeric-v1-checkpoint.json。以下は履歴。


座標物理の移植境界をsource-bound model-checkへ整理し既存モデル／arena監査を再利用。物理は6pellet→12packet、ほぼ全遮蔽でも0damage本体packetが残ることを正本passive観測で確認。既存の均一packet／BODY-ADD group観測器は変更せず、expected専用の正本8world／15pellet／31packet oracleを追加。共通Slangの角度区間union／intersect／subtractを実装し、coordinate-arcs135（native126／拒否9）がM5 Metal一致・独立seal、最大1024区間／境界／符号zero／tail検証。GPU1回0.012983秒／同claim再試行0／Windows実行0。最終区間CPU8／合成CPU51／制御416（Win1skip）、full2932→compact1605全record／byte保持。監査データの同梱漏れ2件は失敗記録を保持しpackage作成時とCPU worker前に自動拒否。source更新時は旧proofをstale表示し開発検証を継続可。旧97／88／81のGPU閉包と保護7source不変、再GPU0。物理確率・三角関数／積分／measure／packet展開／group本体接続は未実装。数値方針の回答待ち。Windows保存objectのCPU回収依頼はAPIがactive turn不在として拒否、開始未確認／再送0。全キャラ0／20gap／UI CPU／目標未達。詳細[座標物理の移植境界](portable-coordinate-physical-frontier.md)、research/portable-coordinate-physical-frontier-checkpoint-v1.json。以下は履歴。

座標＋実射撃groupを共通GPU常駐Runtimeへ接続。private coordinate-composed97（native81／拒否16）がM5 Metal実GPU一致・独立seal。入力108648／出力1310720word、scene104408／area107592／CP1048576、全容量保持。owner0／3と1／3／6packetの同frame共存を検査。物理射撃はbody-onlyで部位poolを明示拒否、座標skillの部位・保留・世代交代は接続済み。旧81／88を最終sourceで再実証しinput／raw全byte／生成CUDA-MSL保持、新97内の旧88はworld＋座標一致・主入口admission16word差を全goldenへ固定。CPU42／制御415（Win1skip）、full2922→compact1628全record／byte保持。GPU5（成功4／比較失敗1）、実行前停止4／容量guard2、同claim再試行0。Windows保存objectは5452464byte／SHA ea9e1484…48cb8、proof結果JSONと回収receiptなし／関連active0をread-only確認、追加compile／GPU0。sin45数値方針は回答待ち。座標物理部位／手動aim／混合world原定義／公開受付が次優先。全キャラ認証0／20gap／UI CPU／目標未達。設計[合成実行器](portable-arena-composed-executor.md)、集約research/portable-arena-composed-executor-checkpoint-v1.json。以下は履歴。

主実行器統合に向け共通arena schemaとCLI arena-checkを実装。CP Python/AG host定数を共通schema化し旧Slang宣言byte保持・実consumerの入力/clear範囲を照合、既存resident監査再利用。combined-legacyは出力live235096word＋clear末尾4968wordに加え、AGでsceneが8word動きCA_BASE_INPUT固定のため入力107585–107592も重複し終了1。combined-v1はscene104408/area107592/CP1048576、入力108648/出力1310720word、全容量保持で重複0。ただしruntime_connected=false、backend最大1Mのままで合成battle未接続。次は合成入口・backend受付・decoder・storage budgetを同時接続。共通smokeに7検査追加、実宣言/入力/clear5改変拒否。固定packageで旧88(native75)+CPU37/本体81(native68)+CPU53/制御413(Win1skip)成功、両GPU閉包・入力/native指紋保持。full2913→compact1619全残存record/byte保持。GPU0/Windows0/数値変更0。全キャラ0/20gap/UI CPU/未達。詳細[arena合成](gpu-arena-composition.md)とresearch/portable-arena-composition-checkpoint-v1.json。以下は履歴。

座標スキルの世代交代を共通executorへ接続。選択snapshot固定・着弾時対象名→現在世代解決・期限切れ部位のimpact→閾値→死亡順と冪等性を保持。新coordinate-generation88(native75/拒否13)がM5 Metal一致・独立seal、追加12正例、旧76全318767104byte raw/33026560byte input/entry保持。本体81閉包不変で再実行0。GPU2(初回期限切れ死亡登録失敗1/修正版1)、retry0/Windows0。CPU37/制御406(Win1skip)、保存5改変/source5改変拒否。full2910→compact1616全record/byte一致、raw2件4KiB疎化で707969024byte回収、全byte-SHA-inode保持/削除0。主実行器のAGとCP arenaが同時有効時243608word重複する静的課題を発見、現別profileの衝突実証ではない。次は共通schema/CLI合成検査/合成profileを優先、世代固定ActorHandleは対象名解決と区別。許可済みWindows15fileはda805153/計9634581byte取得・照合済み、再送なし。数値基準回答待ち、全キャラ0/20gap/UI CPU/未達。詳細[世代交代](portable-coordinate-generation.md)、[arena合成](gpu-arena-composition.md)、research/portable-coordinate-generation-checkpoint.json。以下は履歴。

座標opt-in全バースト保留を共通executorへ接続。scalar/periodic/interrupt receiptと68word座標snapshotを同じqueue indexへ移動。新coordinate-full-burst76(native63/拒否13)がM5 Metal一致・独立seal、範囲/多段/参照count/出生消滅/子tail/旧形式共存13正例と3負例。旧60全251658240byteと旧81全339738624byte/input/生成CUDA-MSLを完全保持。旧81も現sourceでMetal一致・独立sealとcompiler source証明書更新。GPU3(初回flag不足失敗1/修正版1/旧81回帰1)、同package retry0。未登録source deltaで制御失敗したため過去ledgerを保持して今回の全SHA/一意literal差分監査と5改変拒否を追加。最終CPU35/制御405(Win1skip)、full2905→compact1611全record/byte一致。4K疎化で計2097152000byte回収、raw削除0/全byte-SHA-inode保持。数値/正本/厳密normalizer不変。Windows送達・数値方針回答待ち、手動aim/物理/世代交代/混合world/公開受付が残る。全キャラ0/20gap/UI CPU/未達。詳細[座標full-burst](portable-coordinate-full-burst.md)とresearch/portable-coordinate-full-burst-checkpoint.json。以下は履歴。

旧形式B3 bonus_damageの保留→共通本体着弾を座標worldへ接続。新coordinate-pending60(native50/拒否10)が実M5 Metal一致・独立seal、先行/後続ATK・全バーストbuff・部位出生/消滅・吸血8契約を追加。旧area52の全218103808byte raw／22597120byte入力／sealed entryを完全保持。GPU1/retry0、実GPU.027555秒、CPU33/制御404(Win1skip)、full2899→compact1605全record/byte一致。新raw全byte/SHA/inode保持の4KiB疎化で242868224byte回収。旧81本体source closureと保護CPU/数値/normalizerは不変、Windows新依頼送達は未確認で再送なし。座標opt-in保留のsidecar移動、手動aim/物理/世代交代/公開受付、host trig数値方針とCUDA回収が残る。全キャラ0/20gap/UI CPU/未達。詳細[座標B3保留](portable-coordinate-pending.md)とresearch/portable-coordinate-pending-checkpoint.json。以下は履歴。

Read-only module-object recovery is implemented in the shared CLI/wrapper. It anchors an external object SHA, validates the original terminal outer timeout and successful inner Job, reuses the object auditor with a separate before/after byte snapshot, and never backfills original artifacts/result. Fixed packet control404 (Win1skip), recovery7 included, compiler CPU191 passed. Distribution: codex/current-object-recovery-v2-source @811ca5ce; Windows dispatch has no acknowledgement, so execution is unconfirmed and must not be repeated without status. Recovery receipt is not yet connected to JIT-link admission. No new tool/GPU calls; original failure/claims retained. Goal incomplete, coordinate numeric policy pending. See [object recovery](portable-object-recovery.md) and research/portable-module-object-recovery-checkpoint.json. History follows.

現full PTXのmodule-objectをWindowsで1回だけ実行。ptxas20.545秒/ret0で5452464byteを保存したが、outer終了後監査中に90秒上限となり全stage/object_verified false。inner59.414秒/exit0・両Job2GiB/BelowNormal/post空/missing0/service未確認。元proofのartifacts/resultなし・status processingとclaim保持、再実行/上限増加/link0。次は別CPU監査receiptによる原本回収、元captureへの後付け禁止。保存CUBIN戦闘を共通wrapper gpu-linkedへ接続し固定package制御397件(Win1skip)/wrapper19成功、Windows新stage未検証。GPU/正本/数値/normalizer変更0。全キャラ0/20gap/UI CPU/未達、座標数値方針回答待ち。詳細[保存リンク実行](portable-saved-linked-stage.md)。以下は履歴。

<!-- coordinate-skill-packets-current -->
compiler-onlyのcompactを既存依存解決器へ接続し、full2892→compact1578の全残存record/byte/golden保持。CPU191/共通395(Win1skip)成功。Macの現full source生成cache必須hitでSlang/GPU0。Windows旧PTX file-probe hit.146秒、現package9bf571ab…のgenerationを明示1回（Slang2/9.099秒・sealed一致）後、両cache必須のcompile-ptx1回がSlang/NVRTC/ptxas/driver/GPU0で既存9554090byteを.122秒復元。現owner自身のproducer、旧owner再ラベル0/原本claim保持。全Job2GiB/BelowNormal/post空/timeoutなし/missing0、service未確認で保全/compile全stage false・計算falseを維持。cache key/厳密normalizer/GPU/数値/正本変更0。次は保存PTXからのmodule-object/JIT-link・短いCUDA実計算。座標の数値基準は回答待ち、全キャラ0/20gap/UI CPU/未達。詳細[compiler compact/cache](portable-compiler-compact-cache.md)とresearch/portable-compiler-compact-cache-checkpoint.json。以下は履歴。

円/回転矩形の距離選択→既存照準/範囲buff→PART/INTERRUPT packet着弾を共通Slangへ接続。area52(native42/拒否10)と同じshape関数のprobe158(native150/拒否8)がM5 Metal一致・独立seal。旧19全79691776byte/native保持、初回focus設定漏れを修正し他51block保持・失敗保持。新Metal3/retry0、旧35/24/16/81/hypot閉包不変で再実行0。最終CPU31/shape6/制御394(Win1skip)、full2893→compact1599全record/byte一致。input gateへ最大64rowの自動SHA診断を追加しGPU/oracle再実行なしでWindows差45行を検出。Windowsは小probeを1回だけ、CPU6後に入力差で停止/GPU0。sin45のhost 1ULP差が境界の命中/非命中も反転することを実証しreference_numeric_policy_gapへ分類、数値基準選択をユーザーへ依頼中。原本/guard/normalizerは変更せず、Windows失敗/claim/14欠落原因unknown保持。全キャラ0/20gap/UI CPU/未達。手動aim/座標物理/保留B3/世代交代/混合actor/全元定義/公開受付が残る。CLI guideの履歴を別fileへbyte保持移動し手順書を軽量化。詳細[座標area](portable-coordinate-area.md)とresearch/portable-coordinate-area-checkpoint.json。以下は履歴。

座標距離用の整数binary64 hypotを共通Slangへ実装。sealed coordinate-math1026(native1024/拒否2)がM5 Metal全word一致・独立seal、4CPUで追加30000入力一致。subnormal単一丸めと正本二段丸めの1ULP差を発見し、正本を変えず二段丸め契約を保持。4limb整数2乗/中点比較、近似sqrt/native float0。GPU .000261秒/new1/retry0、旧35/24/16/81閉包不変・再実行0。最終CPU4/制御392(Win1skip)、full2880→compact1574全record/byte保持。Windows小norm1026も1回で計算/containment成功、比較原本SHAがMetal全1026entryと一致。missing0/service未確認で保全/stage false。診断4file公開は自動審査拒否、接続内read-only照合・原本保持、full本体なし。shape/回転sin-cos/実callerは未接続、全キャラ0/20gap/UI CPU/未達。詳細[座標数値](portable-coordinate-math.md)とresearch/portable-coordinate-math-checkpoint.json。以下は履歴。

DoTの既存時計→frame Geometry→世代付き座標packet→PART着弾を共通Slangへ接続。sealed coordinate-dot35(native28/拒否7)がM5 Metal一致・独立seal。新9ケースで即時/遅延tick、消滅/破壊/世代2/不壊/depth、DoT限定counter/吸血、created .2099→landed .216666の新生部位、dot+part同一層加算を検査。旧24も現sourceでMetal一致・独立sealし全100663296byte/input保持、35先頭も完全一致。新GPU2/retry0、旧16/81閉包は不変で再実行0。最終full/compact CPU23各成功・制御392(Win1skip)、2875→1585全record/byte保持。Windows保存PTX生成成功26.302秒/全97.422秒/GPU0、outer missing9でstage false・原因unknown。再実行なし、承認済み15fileをMac取得・全サイズ/SHA一致。正規化生成一致だがraw/source IDは異なりcache再bind不可。全キャラ0/20gap/UI CPU/未達。距離形状/座標物理/保留B3/跨frame世代/元全定義/公開受付は未完了。詳細[座標DoT](portable-coordinate-dot.md)とresearch/portable-coordinate-dot-checkpoint.json。以下は履歴。

即時全部位スキルのframe Geometry→cast→世代付きpacket→Actor着弾を共通Slangへ接続。sealed coordinate-skills24(native19/拒否5)がM5 Metal一致・独立seal。宣言/期待値モデルでplain/pierce/explosionのhits_parts、depth反転、破壊/不壊、同cast stale、吸血子のframe残存near（8800/HP5880）、typed counter閾値→refresh→死亡（epoch1→2）を検査。全battle＋選択key/世代＋着弾順/量を比較。新Runtime0/local receipt uint1、容量超過status64。旧16/81も再検証・独立seal、全406847488byte/input/生成CUDA-MSL保持（81両reflectionも保持）、compiler mixed証明書更新。最終CPU20/旧81CPU52/制御392(Win1skip)、full2872→compact1581全SHA一致。新GPU4/retry0/Windows追加0。距離形状/座標物理/保留DoT/跨frame世代/原キャラ全定義/公開受付は未完了。全キャラ0/20gap/UI CPU/未達。詳細[座標skill packet](portable-coordinate-skill-packets.md)とresearch/portable-coordinate-skill-packet-checkpoint.json。以下は履歴。
<!-- /coordinate-skill-packets-current -->

<!-- coordinate-world-pool-current -->
座標selectorを共通戦闘の16word actor poolへ直接接続（状態コピー0／Runtime追加0）。sealed coordinate-world-pool16(native battle11/拒否5)がM5 Metal一致・独立seal、再出現世代2/出生順/ordinal/破壊/interrupt/depth反転を検査。既存非座標battle＋literal座標sidecarの終了前読取り検証で、座標packet producer／Frame着弾は未接続。旧21全byte保持、mixed81も現schemaで再検証・独立seal、全339738624byte/input/native/生成CUDA-MSL両reflection保持。新compiler-full--attack-group-mixedを共通CLIで独立監査登録、旧long証明書は履歴（現source stale）。最終CPU16/旧81CPU52/制御392(Win1skip)、full2866→compact1575全record/SHA一致。新GPU4/retry0/Windows新依頼0、保存PTXunknown。全キャラ0/20gap/UI CPU/未達。次は選択時の座標集合固定と実packet接続、stale accounting/通知吸血順。詳細[実pool直接接続](portable-coordinate-world-pool.md)とresearch/portable-coordinate-world-pool-checkpoint.json。以下は履歴。
<!-- /coordinate-world-pool-current -->

<!-- coordinate-scene-current -->
座標descriptor／depth・出生時刻順／live世代付き全部位集合を共通Slangへ追加。sealed coordinate-scene21(native10/拒否11)が実M5 Metal全word一致・独立seal、保存raw4改変検出。127対象/pattern31/不壊/再出現/signed-zero/subnormalを検査。CUDA/MSL共通生成、CUDA実行なし。明示primitive操作の部品検証で、戦闘Frame・範囲距離・公開受付は未接続。正本stale targetはkindを返し総量計上するため前記録を訂正、同cast後続packetのreference25を追加。最終CPU12/旧81native68+CPU52/制御392(Win1skip)、全package SHA/compact残存records一致。新GPU1/retry0、Windows追加依頼0・保存PTX結果unknown。全キャラ0/20gap/UI CPU/未達。次は共通Frame caller pool接続、形状数値primitive。詳細[座標GPU部品](portable-coordinate-scene.md)とresearch/portable-coordinate-scene-checkpoint.json。以下は履歴。
<!-- /coordinate-scene-current -->

<!-- coordinate-skill-reference-current -->
座標スキルの正本24契約を共通reference CLIへ追加しGPU/packing0で成功。全部位指定と通常貫通/爆発の距離選択・前後順・破壊/不壊・通知/packet順・別interrupt量を区別。CPU bridgeの無条件PART publishによるinterrupt誤分類を、native戻り値capture→元total後/吸血前の条件publishへ修正。hit_target1回・private kind6非alias・reserved local拒否を検査。観測透明性/既存profile連鎖/入力不変も成功。source監査は座標をnativeモデル有りのgpu_port_gapとし、GPU拒否guardと数値依存6math＋powを記録。固定package CPU49/旧81入力native68保持/制御392(Win1skip)、全残存full/compact records一致。正本/数値/GPU/旧golden変更0、新GPU0/Windows新依頼0。座標GPU未接続、全キャラ0/20gap/UI CPU/未達。次は共通descriptorと形状/数値primitive。詳細 [座標スキル正本契約](portable-coordinate-skill-reference.md) とresearch/portable-coordinate-skill-reference-checkpoint.json。
<!-- /coordinate-skill-reference-current -->

<!-- mixed-attack-group-current -->
実Ni/Velを同編成のslot0/1・3/4へ配置し元全効果を保つ混合owner20ケースを追加。sealed attack-group-mixed81(native68/拒否13)がMetal一致・独立seal、旧60の全251658240byte/input/native保持。新20は1116group/528通知、3/30/180秒・閾値2/4・両policy・65件目以降の両ownerを照合。GPU11.661秒/必須pipelinehit.002401秒/Slang0、保存4改変拒否。最終CPU34/制御392(Win1skip)、full2848→compact1567全残存record一致。共通テストfixture同梱漏れの失敗を保持して修正。容量guard停止後4KiB opt-in疎化を実装し2capture計1564307456byte回収、全byte/SHA/inode/証拠保持・削除0。共有計算/数値/正本/旧golden変更0、新GPU1/retry0。Windows新依頼0、既存PTX結果unknownで再依頼せず。全キャラ0/静的245/266/base185/203/20gap/UI CPU/未達。次はgeometry/parts/arena境界の正本契約、Windowsは復旧後に保存結果取得。詳細 [混合owner実射撃group](portable-mixed-attack-groups.md) とresearch/portable-mixed-attack-group-checkpoint.json。
<!-- /mixed-attack-group-current -->

<!-- current-full-compiler-packet -->
現在のMetal60をGPU0で独立再監査しcompiler-full--attack-group-longの全source証明書を登録。旧本体で成功したPTX→object→JITlinkを再利用する方針で、現全ソースPTX専用1回をWindowsへ依頼。接続不可のため実行状態・結果はunknown、再依頼0。共通packetへ既存module-object/JITlink CLIを固定request/外Job/内60外180秒/2GiBで接続し、CPU191＋制御391(Win1skip)成功。source/数値/golden変更0・新GPU0。v2へ移行する場合は成功済みPTX cache必須でNVRTC0のproducerを同ownerへ作り、providerのpackage ID条件を維持する。新stage実Windowsは未確認。全キャラ0/20gap/UI CPU/未達。詳細 [現在の全本体コンパイル経路](portable-current-full-compiler.md) とresearch/portable-current-full-compiler-checkpoint.json。
<!-- /current-full-compiler-packet -->

<!-- long-group-history-current -->

<!-- cuda-packet-preparation-current -->
CUDA準備を既存packet wrapperの生成専用stageへ分離し、実Job/2GiB/BelowNormal/gate確認付きでWindowsへ接続。Windows CPU32/native48/60入力成功後、生成v4も34.117秒でCUDA/MSL sealed指紋一致（Slang2、NVRTC/driver/GPU0、postJob空/missing0、service unverified）。最新3suiteをcompactへ追加し、残存全byte/goldenを保持。Windows相対path監査不具合をPOSIX表記で修正。Mac制御387(Win1skip)・生成stage成功、計算コード/数値/golden変更0・GPU再実行0。生成cache必須O0を1回だけ実施しcachehit/Slang0、NVRTC27.211秒でptxas Memory allocation failure/rc6/artifactなし、全58.300秒（timeoutなし）。内外Job後空/missing0、driver/GPU0・再試行/上限変更0。次はCPUのみで保存生成コードを解析しcompilerメモリ削減の共通分割候補を調べる。失敗・claimは保持。現CUDA計算未確認、全キャラ0/静的245/266/base185/203/20gap/UI CPU/未達。詳細 [CUDA packet準備](portable-cuda-packet-preparation.md) とresearch/portable-cuda-packet-preparation-checkpoint.json。以下は履歴。
<!-- /cuda-packet-preparation-current -->

sealed attack-group-long60(native48/拒否12)で、180秒の全927group/209通知をMetal一致・独立seal。live32slotと観測履歴を分離し、opt-in可変長24+4*対象wordsで全recordを保存、先頭64legacyも保持。schema LANDINGS2048から開始862048/arena186528wordsを導出、尽きれば明示status64。初版の512誤認/領域重複で新6件の参照bank検査が失敗したcapture/claimを保持し、同じ60入力で修正を検証。65射目/最終時刻/余分word/参照bank末尾の4改変を検出。旧53の全222298112byte/input/native保持、旧53/32のsource/生成IDだけ更新。CPU31/正本48/制御380(Win1skip)、GPU11.181秒/PSO90.851秒/run Slang0、最終package4c2a5371…全payload/CPU/generation照合済み。旧61は新GPU0/source再bind0、生成CUDA/Metal/両reflection全byte一致だけをCPU確認。原本削除0で約656MB割当回収。静的245/266/base185/203/20gapと全profile/issue/lane保持、全キャラ0/UI CPU/Windows0/未達。次はCUDA本体compile/cacheとmixed-owner/arena境界、geometry/盾/parts。詳細[完全な長時間group履歴](portable-long-group-history.md)とresearch/portable-long-group-history-checkpoint.json。以下は履歴。
<!-- /long-group-history-current -->

<!-- metal-pipeline-cache-current -->
共通CLIへopt-in Metal pipeline cacheと必須hitを追加。生成MSL/Swift consumerの全byte、GPU/OS/entry/stride/safe数値optionをkey化し、native failOnBinaryArchiveMissで再コンパイルfallbackを禁止。key lock内の2file読込・fsync/rename公開、破損/別kernel/必須miss拒否と公開途中待機を実機確認。最終v5の実53 cold/warmが全一致・独立監査、既存222298112byte/rawとcomparison全文を完全保持。PSO90.964848→.002401秒、GPU2.144520→2.108135秒（準備1pair実測）。v4も成功、公開競合のsource点検後v5修正を保持。制御380(Win1skip)、小nativeはv2/v4/v5各4GPU、実53はv4/v5各2GPU、計16dispatch/再試行0/Windows0。最終package037ef7aa…はreplay監査器差替拒否/負例だけを追加し全payload SHA照合。raw削除0で約1.63GB割当回収。CUDA既存cache/計算/Slang/normalizer/golden変更0、現CUDA実機・全キャラ0/UI CPU/残20gap/未達。次はCUDA本体compile/cacheと長時間group64・mixed-owner・geometry/盾/parts。詳細[Metal pipeline cache](portable-metal-pipeline-cache.md)とresearch/portable-metal-pipeline-cache-checkpoint.json。以下は履歴。
<!-- /metal-pipeline-cache-current -->

<!-- native-route-gpu-current -->
通常対象選択を既存共通actorSetCapture／actorPhysicalTargetへpacketごと接続。sealed attack-group-native-route53(native42/拒否11)がM5 Metal一致・独立seal、旧32の全134217728byte保持。新20は172group/2通知、SG途中ADD3破壊→BODY再選択、元Ni/Vel16全battle保持。全53は340group/114通知、保存出力4改変を共通比較器で拒否。旧61も現source一致・独立sealし全255852544byte、入力/native、両生成/両reflection全byte保持。CPU28＋旧93＋分類17、制御372(Win1skip)。実run Slang0/再試行0/Windows0。GPU53=2.028秒/PSO93.076秒、61=10.382秒/PSO67.185秒、永続PSO cacheは未実装。全byte/SHA/inode不変で約1.55GB割当回収、raw削除0。最終package53は7e38f81f…、61は6dbb436d…、payload全SHA照合済み。静的245/266/base185/203/20gapと全profile/issue/lane保持、通常UI CPU/全キャラ0/未達。次は長時間log64・mixed-ownerと準備cache、geometry/盾/parts、現CUDA。詳細[通常対象選択GPU](portable-native-route-gpu.md)とresearch/portable-native-route-gpu-checkpoint.json。以下は履歴。
<!-- /native-route-gpu-current -->

<!-- native-route-groups-current -->
実射撃groupに明示nativeポリシーを追加し、元Bossルーターを変更せず実着弾を収集するCPU20契約を共通CLI referenceへ登録。新規展開の固定packageで172group／2通知／2子着弾、元2プロフィール16件のbattle全体と全物理shotが未導入正本に一致。宣言listener付きSG2件では同一射撃中ADD3破壊→BODYへ実再選択し、各1回だけ発動。CPU27成功、旧32input/native22全保持、全2832payload SHA一致。旧policy専用source監査の初回失敗を保持し、明示二policyと置換禁止3負例で修正。GPU source／golden／数値／保護CPU変更0・GPU0・Windows操作0。新20はGPU未接続で全キャラ認定へ加算しない。次はpacketごと既存actorPhysicalTargetへ共通Slangを接続し、Metal20＋旧32/61保持・独立seal。詳細[通常対象選択の射撃group](portable-native-route-groups.md)とresearch/portable-native-route-group-checkpoint.json。全体目標未達、以下は履歴。
<!-- /native-route-groups-current -->

<!-- battle-attack-groups-gpu-current -->
実射撃group・queued childの世代付き対象・敵buff fanoutを共通Slangへ接続し、sealed `attack-group-battle`32（native22／拒否10）がApple M5 Metal一致・独立seal。元ニヒリスター／ベロータ20入力と宣言listenerを加えたSG2入力で168group／112通知、全物理snapshot・全ADD数量／hit／世代・global overkill・buff対象・所有参照解放を照合した。GPU1.950秒／cold PSO89.670秒、Runtime138952不変・run Slang0。旧61も同じ現共有sourceで一致・独立sealし、旧255852544byte rawと全input／native保持。旧goldenはsource／生成物identityだけを更新した。CPU23＋旧93、共通制御372（Win1skip）が成功。CLIへ出力割当一致guard、source履歴へexact逆差分を追加し、失敗・claim・rawを保持。明示all-logical-enemies/BODY/ADDモデルで、geometry／長時間log64超／mixed-owner広範囲／現CUDA／公開受付は未完了。静的245/266・base185/203・残20gap／全キャラ0／UI CPU／ゴール未達。Windows追加0。詳細 [実射撃group GPU接続](portable-battle-attack-groups-gpu.md) とresearch/portable-battle-attack-group-gpu-checkpoint.json。以下は履歴。
<!-- /battle-attack-groups-gpu-current -->

<!-- battle-attack-groups-native-current -->
共通CLI `reference --suite attack-group-battle` に実射撃のCPU22契約を追加。固定full packageで168射／168group／112通知／448子着弾が成功、16入力で非zero。元ニヒリスター／ベロータ20入力と、宣言listenerを加えた元ノワール／ツバイ10packet射撃2入力を区別する。実際のBODY/ADD receiptからdistinct集合をsealし、queued childの世代固定・例外復元・単boss全battle保持を検査。明示all-logical-enemiesモデルで、ゲーム内の範囲判定／Slang自律producer／Metal接続は未完了、22全てmodel gap・GPU加算0。前回のsealed Metal入口はdestructible-body-heal-share-retention61、親oracle52再利用とfresh独立監査を維持する。Windowsは接続復旧を読み取り確認、idleで新規CUBIN／CUDA依頼0。全キャラ0／通常UI CPU／ゴール未達。詳細 [実射撃group CPU契約](portable-battle-attack-groups-native.md) とresearch/portable-battle-attack-group-checkpoint.json。以下は履歴。
<!-- /battle-attack-groups-native-current -->

<!-- body-lifesteal-shield-current -->
HSI5で元ミルク吸血16.16%を既存body着弾後へ接続。盾で吸収したpacketはbody/吸血を抑止し、body到達だけ従来処理。元77定義・3/30秒の新13(native10/拒否3)、旧AoE18込み31(native26/拒否5)がMetal一致・各独立seal。累積healing未照合を保存raw破損で発見して厳密なnative receipt比較を追加し、GPU0 replay13/再seal・12破損検出。旧18全raw一致、新13の6件は配置変更に伴うscratch絶対アドレス1wordのみ、元raw/保持検査失敗/全差分を保持しnormalizer除外0。source158/Runtime138952/数値/保護CPU維持、旧経路の生成CUDA/MSL全byteも同一。現在sealed入口destructible-body-lifesteal-retention31、旧goldenはsource stale履歴を保つ。蓄積/共有回復/貫通は未対応、Windows追加0/全キャラ0/UI CPU/残20gap。詳細docs/portable-destructible-body-lifesteal.mdとcheckpoint。以下は履歴。
<!-- /body-lifesteal-shield-current -->

<!-- aoe-burst-shield-current -->
元ノワールAoEと元ミサト盾150%、元トリナAoE435.6%を既存共通FrameでMetal18(native16/拒否2)・独立seal。全78/83定義を保つ3/30秒実編成、HP/hit/slot順/破壊body/世代を照合、旧14全raw保持。GPU9.758秒/PSO.002491秒、source157/Runtime138952/正本/数値/normalizer不変・required generation hit/Slang0。sealed destructible-aoe-burst-rostersをcompactへ追加し比較器共通化、破損16検出は同一入力nativeをコピーし90秒上限を維持。Windows追加0/現CUDA未確認/20gap/全キャラ0/UI CPU。詳細docs/portable-destructible-aoe-burst-rosters.mdとcheckpoint。以下は履歴。
<!-- /aoe-burst-shield-current -->

# 共通CLIの軽量パッケージ

`docs/portable-compact-package.md` と `research/portable-package-projection-checkpoint.json` を参照。`package --compact` は現行skill157/Misato2に限定し、全GPU source・fixture/data・pinned upstream・指定CPU/全smokeを保持する。ファイル数2,795→1,550/ZIP8.46→6.39MB、Windows速度は未測定・今回追加実行0。共通制御372(Win1skip)、strict generation hit/Slang0、保存Metal2 replay成功。失敗と古いgeneration fixtureを保持し、歴史source auditだけ後続の明示stride差分へ対応。計算本体/normalizer/全キャラ認定0/残20model gapは変わらない。

<!-- shared-gpu-current -->
元selector/count/burst flagsを共通actorSetCapture・sampleDamageFactorsForReach・既存typed Frameへ接続。sealed destructible-skill-retention157(native102/拒否55)＋destructible-skill-misato-retention2がMetal一致・各独立seal。元レイ7＋全73定義の4契約でHP/hit各38packet内のskill3を確認、Dola burst/single=trueとRei B3 damageのburst=falseを保持。新HSI4だけで拡張、盾なしは元skill Frame、旧141全input/native/raw591396864Bとミサト2全8388608Bを保持、保存5block61改変検出。fixed b00d2fcd…CPU43/skip0・native102成功、4既存/2新shaderでsource157、Runtime138952/保護CPU/量core/binary64/normalizer維持。GPU157=3.110215秒/PSO65.163974秒、warmミサト=1.760292秒/PSO.005851秒、実run/final生成cache必須hit Slang0。GPU2回/再試行0、raw削除せず958595072B割当回収。Windows復旧、既共有O0 fixed21ba977a…だけCPU63/native17＋compile各1回。CPU成功/欠落0、O0内側60 timeout・NVRTC entered1/return0/CUBINなし/driver-GPU0、外側82.825秒・両BelowNormal/2GiB/post空/欠落0、service unknownで保全false・旧7終了unknown継続。child verify17.456s/generation10.512s cold2回、entered→wait29.376sは完了時間でない。remote reported summaryでMac raw独立監査なし、claim保持。既存packet2702filesの不要依存を検査しpayload縮小と工程分離が次の効率化。全266/245/base185/残20・issue/順位は限定metadata以外保持、全キャラ0/UI CPU/未達。standalone16はdevelopment_only、現入口は157とnewミサト2。次はAoE burst正例（今回true正例なし）、広いskill/貫通/吸血蓄積/parts/coords/ADD、現CUDA cache/計算。詳細 docs/portable-destructible-skill-rosters-gpu.md / research/portable-destructible-skill-rosters-gpu-checkpoint.json。

元レイ7スキル＋装備/同伴の全73定義を、元selectorを変えないskill_shields opt-inのnative契約4件へ接続。共通CLI reference destructible-skill-rostersがpacking/build/execute禁止で成功、HP/hit各38packet内に元skill3（ドラー単体burst748299、レイ4727897/44161247、hit側590618/7703705）を確認。盾補正700.5%・credit1を分離、元Dola single=trueと元Rei B3 damageのburst=falseを保持。3秒17packet/盾破壊後body、未知family/multi/deferred/ADD/parts/coords/吸血蓄積を拒否、全method例外復元。fixed39c1188e…CPU32/skip0・旧native2成功、旧ミサト2golden全entry/武器141 input-native保持。全155GPU source/Runtime/両生成/binary64/保護CPU/normalizer不変、generation必須hit/Slang0/新GPU0。新レイ4はGPU未接続で実証認定しない。inventory全266/245/base185/残20/全field完全一致、全キャラ0/UI CPU/未達。Windows観測/新依頼0、現CUDA/cache速度/CUBIN O0/7終了unknown・保全false継続。次は元route/count・burst/AoE/single flagを共通selector/factor/Frameへ接続し、旧141/ミサト2保持＋新レイ4のMetal/独立seal。詳細 docs/portable-destructible-skill-rosters-native.md / research/portable-destructible-skill-rosters-native-checkpoint.json。

元ミサト5スキル＋装備/同伴4人の全71定義を、実武器・元preparationのまま共通武器盾入口へ接続。sealed destructible-weapon-rosters2（3/30秒）がMetal/native一致・独立seal成功。3秒は補正0の3packet、30秒は元60回条件→passive盾補正150%の22packet、元回復27配布/10正回復の最終HP・弾数・burst/物理履歴まで一致。GPU回復全イベント列の個別照合ではない。155GPU source/Runtime138952/両生成/binary64/保護CPU/normalizer追加変更0、既存実行器を再利用。最終fixed e95f1af2…CPU24/skip0・native2成功、旧141全input/native保持、実GPU両block18改変検出。GPU1.758617秒/child2.645708秒/実runとfinal生成cache必須hit Slang0、GPU1回/再試行0/Windows依頼・観測0。容量不足はclaim前GPU0で停止、旧成功141rawの全byte/hash/inodeを保持し440991744B割当回収・raw削除0。final v2の旧141golden梱包漏れCPU失敗を保持しsupport_files修正、fresh v3成功/GPU再実行なし。全266/245packing/base185/残20gap・issue/順位は限定metadata以外保持、全キャラ0/UI CPU/目標未達。通常受付は拒否、宣言単一boss・武器専用policy。次は他の盾補正キャラ全定義、貫通・吸血/蓄積・skill route・部位/座標の混在。現CUDA/cache速度/CUBIN O0/7終了unknown・保全false継続。詳細 docs/portable-destructible-weapon-rosters.md / research/portable-destructible-weapon-rosters-checkpoint.json。

通常武器の盾接続を共通Slangへ実装し、sealed destructible-weapon-shield141(native98/拒否43)がMetal一致・独立seal成功。実shotの9factor/HP補正を1回保存し、pellet通知前のlive HP/hit/body選択・dwLand/counter子・body除外を共通化。auto/散弾/charge/tap/武器変更/core/RL/2銃口/slot4/2射手の22契約で、量/時刻/弾数/gauge一致。旧111全input/native/raw465567744B全保持、実GPU10block91改変検出、final fixed328abf81…CPU204(skip0)/native98/reference22成功。初回charge3件の時刻失敗はfixtureの静的postfire0をnative metadata fallback.215へ5入力補正して解消、全native/source保持・raw変更3件・初回失敗/claim保持、計2GPU/同claim再試行0。成功GPU.069158秒/child2.191777秒、初回pipeline込み68.966296秒、実run/final生成cache必須hit Slang0。4既存/2新shader、source155/Runtime138952/保護CPU/binary64/normalizer不変、通常147/scalar119は共通hook変更でsource不変とは扱わずfull492再実行なし。rawを削除せず割当788332544B回収。全266/245packing/base185/残20model gap・順位は限定metadata以外保持、全キャラ0/UI CPU/未達。Windows status取得不可/新依頼0、現CUDA/cache速度/CUBIN O0/7終了unknown・保全false継続。座標/parts/aim/貫通/ADD owner/吸血・蓄積混在/対象DEF・敵debuff/全profileが次の未対応。詳細 docs/portable-destructible-weapon-shield-gpu.md / research/portable-destructible-weapon-shield-gpu-checkpoint.json。以下は各時点の履歴。
<!-- /shared-gpu-current -->

<!-- destructible-frame-current -->
通常burst_cast通知→既存条件/発動権/係数確定/mode10 Frame→typed弾着弾をopt-inで接続。閾値全兄弟latch/子/破壊終了を同じFrame配列・work/depthでmode26継続、dispatch再帰なし・深さ別scratch。CPUはmanager scoped対象resolver/damage callbackでlive弾集合を返し、例外時も元callback/resolver復元。対象0なら発動権を消費しない既存契約を維持。Metal26(native宣言17/拒否9)＋独立seal、level1/10/fullburst/DEF0-100/zero/round/trigger未到来/2攻撃450→500/予算1/空予算/名前命中子450→595/128slot127/兄弟epoch1-2-3 ATK33/context解放が一致。GPU.033392秒/raw81,788,928B/Runtime163528、旧25 input/native/output/raw78,643,200B保持。初回23の子mode26終端未指定でcreditのみ溜まり完了しない差分を既存Frame valueへready終端を渡して修正・失敗保持。fixture8block故障注入、最終fixed a92d8469…CPU51/native17成功。通常492もfixed1a412068…CPU288/native378/Metal/独立seal成功、旧1,547,698,176B全byte・全492 input/native/output保持。通常経路はCUDA/MSL生成rawまで同一、Runtime138952不変、旧gold snapshot保持後actual sealで最新retention goldenを登録。共通2sourceのexact inverseは歴史source検査のみで、新実証の代用なし。通常GPU4.483秒/PSO65.213秒、Metal作成費は未解決。CUDA入力同一でもWindows新cachehit/数値は未測定、追加Windows0/claim操作0、remote最終turn01a16ab6…terminal/pending0のまま。全266/245packing/20分類順位保持、priority16へFrame限定証拠だけ追加しmodel gap/公開拒否維持。full battle scheduler/敵弾生成/個別DEF-debuff/倍率/盾迎撃/破壊固有/attack groupは残件、typed1行・driver root最大2で全キャラ認定0/UI CPU/全目標未達。次はscheduler worldと元profileのこの入口への接続、CUDA保存PTXの関数境界によるJIT費用削減。詳細docs/portable-destructible-frame.mdとcheckpoint/evidence。以下は履歴。
<!-- /destructible-frame-current -->

<!-- destructible-skill-current -->
原all_projectiles定義→既存係数選択/compiled Definition/damageValue→live弾producer/counter/同期子をCPU/共通Slangへ接続。元SnowWhite HeavyArms index24の1定義8入力＋合成0係数/丸め境界2のMetal18(native宣言10/拒否8)が全件一致・独立seal成功。GPU.026898秒/raw56,623,104B/Runtime163528/source128。level1 24.76%=266/level10 41.9%=450/fullburst660/DEF100=405を既存7段/roundで確認、同攻撃のchild ATK増後も2本目の量固定。callerが明示DEF/phaseを持ち、typed Actorは保持・sentinel carrierだけworld-skill route1、既存ABI/mode7/時計through条件へ正しく変換。初期5失敗（literal入口、clock未到達、診断、sentinel route、旧DEFと消えた一時phase代入）を保持、数値/正本/normalizerの緩和0。最終fixed d34d72ec…CPU46/native10成功、梱包漏れCPU v7も保持・support_files修正、GPU再実行なし。旧producer15全input/native/既存GPU source保持。inventory全266/245packing/20分類順位の全field保持、priority16へ限定typed_skill証拠だけ付記しmodel gap/公開拒否維持。通常battle自動Frame/生成元/弾個別DEF-debuff/倍率/盾迎撃/attack group完了は残件。Windows今回は旧cache PTX静的分析のみ既存bounded CPU1.402秒、全181関数reachable/582edges/1510sites/無循環・間接call0、JIT負荷候補だが因果未確定・物理register/stack証明なし。Slang/NVRTC/driver/GPU0/claim不変。remote turn01a16ab6-b5a5-73b2-a610-8ff4466ebd8a terminal/idle cursor b0ceb4a4-c8c1-428e-bc07-b30c38de2633:16/pending0。詳細docs/portable-destructible-skill.md、checkpoint/evidence。全キャラ0/UI CPU/全目標未達。次は通常skill Frameからtyped routeへの自動dispatch契約と対象context/倍率、保存PTXの共通関数境界によるcompile費用削減。以下は履歴。
<!-- /destructible-skill-current -->

<!-- destructible-attack-current -->
共通CPU/Slang producerがlive PROJECTILE一覧をGPU側で選択しslot/kind/id/generationを固定、既存dwLand/dwPublishImpact/counter/子dispatchへ複数着弾。盾除外/空集合/遅延/世代2/128対象slot127/miss/blocked/端数credit/元attackID/子ATKをMetal15(native宣言9/拒否6)で1回実行。GPU.039299秒/readback47,185,920B。初回reader effects渡し忘れKeyErrorを修正し新固定v2へ保存replay＋独立seal成功、GPU再実行0/元失敗・claim保持。saved5block改変検出、CPUの同期子世代交代はold handleを拒否。GPU子によるworld世代変更自体は未実証。旧counter/world/core/production147source・Runtime138952不変、新driver163528。inventory全266/245packing/20分類順位を完全保持。sealed最終v3 package45ed81bd…/最終CPU検証記録はresearch/destructible-attack-evidence/。旧counter18のWindows cache必須gpu1回は生成hit/Slang0/PTXhit/NVRTC0、child入力.027634秒、cuInit/context成功後cuModuleLoadData進入→inner60 timeout、launch/readback0/数値未検証。module進入後観測38.632秒は完了時間ではない。outer125.725秒/timeoutなし、両2GiB/BelowNormal/post空/missing0・service不明/環境保全false・旧claim保持/再試行0。remote turn01a16aac-39e6-72e0-8a15-a58b2a8cd063 terminal/idle、cursor b0ceb4a4-c8c1-428e-bc07-b30c38de2633:15/pending0。新producerのWindows実行は未依頼。通常battleの効果係数/倍率/typed生成元/盾迎撃/attack group完了は残り、all_projectiles通常受付は拒否。次は既存damage query/Frameからtyped producerへ接続する契約と保存PTXのmodule/JIT費用切分け。全キャラ0/UI CPU/残20model gap/全目標未達。詳細docs/portable-destructible-attack.md。以下は履歴。
<!-- /destructible-attack-current -->

<!-- prepared-transport-current -->
CPU成功後の入力をprepared-v1で公開し、子はpackage全件検証＋入力全体/行SHA/CPU receipt照合を維持してadapter再import/packingを省略。auditも同じ照合、欠落/改変は停止・legacy fallbackなし。Metal先行v2の18入力が全件一致、旧raw56,623,104B同一、子入力確認Mac.005087秒。最終v3固定5972500d…はMac/Windows CPU64/native13成功・関連146成功、最終v3 GPU再実行なし。既存packetにcompile-ptxを追加し同じJob/gate/2GiB/BelowNormal/inner60/outer180以下で既存compiler-only経路を呼ぶ。Windows CPU1回/PTX1回、生成cache hit/Slang0、NVRTC22.536秒でPTX4,952,590B完成・driver/GPU0・旧CUBIN未完claim元SHA保持/新PTX claimなし。両Job終了後空/missing0、service unverifiedなので環境保全false/全体stage exit2、compiler成功と区別。CPU全体62.747秒（package27.207/群26.804、worker14.395含む）、compile全体65.946秒（親verify15.140/子16.045/NVRTC22.536）、入れ子合算不可。過去7終了は操作なし/game-video可能性でもcause unknown。remote turn01a16aa6-3ecc-7b32-ae11-0f2126820c14 terminal/idle、cursor b0ceb4a4-c8c1-428e-bc07-b30c38de2633:12/pending0、再試行0。Windows報告metadataは取得済み/PTX本体独立audit未実施。詳細docs/portable-prepared-transport.md、証拠research/prepared-transport-evidence/。通常戦闘producer/選択/迎撃/倍率未接続、245packing/残20model gap/全キャラ0/UI CPU/目標未達。以下は履歴。
<!-- /prepared-transport-current -->

<!-- destructible-counter-current -->
宣言typed弾/HP盾/hit盾のresolved Impactを既存collector/DFS子イベントへ接続する共通CLI destructible-counterを追加。GPUで消費後、全兄弟latch→閾値子→壊れた正確な世代のcounter終了。body enemy_death/owner死亡へ変換しない。Metal18(正例13/拒否5)＋独立seal、ATK0/11/22/33/epoch/元Impact/old gen/子refresh/兄弟+破壊順が一致。旧16 input/native/raw50331648B全保持、最終Mac固定11a78f5c…CPU43/native13成功・保存5block故障注入、GPU.026794秒/cached PSO.001578秒/実run生成cache必須hit Slang0。初回ABI host不一致status64は保持し入力修正、追加case含む各固定package1回ずつ（v1入口拒否/v2成功16/v3成功18）。driver Runtime163528/123source、production147/Runtime138952/core/world source不変。inventory全266/245SHA/20code順保持、5分類へfoundation証拠だけ追加しmodel gap/受付拒否維持。Windows固定9b2d57fb…をroot642ab82で2file共有しCUDA18だけ1回。CPU42/native13/Slang build9.197秒成功、NVRTC entered後28.646秒の観測内で戻りなし→inner60 timeout/outer141.509秒exit1、GPU0/数値未確認。両2GiB/BelowNormal/post空/missing0・service unverified/保全false、生成cache完成/未完NVRTC claim保持・再実行0。remote GPU turn01a16a82-e29a-7501-ba5d-3a1ad1b86d72 terminal/idle、転送turn01a16a8c-0b6a-7340-9cd5-6157ca2d62f3もterminal、cursor b0ceb4a4-c8c1-428e-bc07-b30c38de2633:10/pending0。詳細16fileのsource/絶対path送信はauto-review拒否、縮小4JSON+manifestは審査拒否なしだがWin Git認証不足、認証を変えずCodex経由元bytes16276BをMacへ回収・manifest SHA53a777dc…/全4membersを検査、Mac認証で縮小版branch codex/cuda-destructible-counter-v1-sanitized-report commit45609afへ共有済み（source/path/PID/tokenなし）。strict normalized CUDA/Metal/input/normalizer SHAはMac一致。通常戦闘生成元/選択/倍率/破壊固有effectは未接続、全キャラ0/UI CPU/未達。次はCUDA内側予算のverify/pack/生成時間の削減（時間枠だけ増やさず、claim保持）と通常戦闘への接続。詳細docs/portable-destructible-counter.mdとcheckpoint。以下は履歴。
<!-- /destructible-counter-current -->

<!-- generation-timing-current -->
共通observerにgeneration各区間/関数elapsed/status timed_calls、cacheパス/key/entry/claim参照を追加。key/consumer/claim規則/全件SHA不変。Windows CPU-only v2はverify38.917秒＋cp932診断errorで12中11成功/残未到達・timeoutなし。診断UTF-8＋owned child UTF8/親不変、file metadata3→lstat1（旧2667records/40404440B全一致・改変/nonregular拒否）に修正。Windows v4固定4fe0ff04…はCPU38/native24成功、inputSHA旧Metal46同一。全stage64.580秒/verify26.163/CPU batch33.904(worker verify9.510含む)/観測2.198+1.999、単回なので改善率未認定。2GiB/BelowNormal/peak199839744/post空/missing0、service未確認・環境保持false、Slang/NVRTC/driver/GPU0。remote turn01a16a70-1a2a-74e1-91f6-499eba312ccd terminal/idle、cursor b0ceb4a4-c8c1-428e-bc07-b30c38de2633:2、pending0。旧timeout cause/旧claimともunknown。さらにoverlay cases()がデータ取得だけでnative7を走らせていた根因を分離しsimulation_cases()へ。変更前9cases/packed SHA全保持、packing時oracle禁止＋明示native7維持を確認。CLI core/smokeへ純粋性2検査を追加、最終Mac固定4e3cc51d…でCPU40/native24 stage成功、関連74成功。最新case分離はWindows未測定・追加Windows依頼なし。旧Metal33/46・production147source/Runtime138952保持、全目標未達。次はtyped着弾→既存counter/所有破壊dispatchの共通接続と必要時だけの短いCUDA。詳しくはdocs/portable-generation-timing.md。以下は履歴。
<!-- /generation-timing-current -->

<!-- destructible-world-current -->
型付き弾/HP盾/hit盾を既存world_scheduleへ接続する共通CLI destructible-worldを追加。GPUが生死からclearedを求め、既存active/generationで生成・退役する。別時計/CPUスポーン予定表なし、same-time再入/旧世代着弾/cleared優先/epsilon/slot127/owner/finishをBossScript正本時計＋宣言target状態と照合。Metal33(正例21/拒否12)一致＋独立seal、最終CPU17成功・保存5block故障注入、GPU.012810秒/PSO.182481秒/実run生成cache必須hit/Slang0。production147source/Runtime138952と旧core保持。戦闘生成元/dispatch/迎撃・倍率/all_projectilesは未接続、245packing/残20model gap/全キャラ0/UI CPU/未達。Windows追加0、7欠落は操作否定・game/video可能性の回答でもcause unknown/保全false、次CUDA前はCPU準備計測と保存claim監査。詳細docs/portable-destructible-world.mdとcheckpoint。以下は履歴。
<!-- /destructible-world-current -->

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
共通CLI reference named-enemyへ23正本契約。buff/bonus damage/duration extension、名前そのまま（colon/空白/空文字）、body先頭alive add誕生順、同名caster非依存、該当なしboss fallback、expiry/late wave/retire/同id再登場/解除/128敵を固定。実rank64/recipient57/所持628、全native/trace/RNG/6照会回数保持、故障拒否。旧native観測器が未対応敵selectorを味方に整形するValueErrorだけ修正、正本/GPU受付変更0。fixed package reference23＋CPU6群49(skip0)/旧175native成功、旧GPU/source/input/native175全同一。静的全266記録/237SHA/29拒否/41code順位保持、4分類をsource確認済みnative_contract_extensionへ。Slang/NVRTC/GPU/Windows追加0、全キャラ0/UI CPU/未達。次は共有名前operand/敵route/状態世代への接続、seq/ref/scaling/budget/文脈/実編成契約→Metal保持。詳細docs/portable-named-enemy-reference.mdとcheckpoint。以下は履歴。
<!-- /named-enemy-reference-current -->

<!-- generation-boundary-current -->
Slang source_hashes/build/resident生成を独立moduleへ抽出し、backendの転送/driver編集による不要な生成cache missを解消。元3関数はroot引数以外AST同一、他backend全module文/定数同一。cache keyは生成器全体/ABI/scope/tool/GPU閉包のhashを保持、新keyで旧cache流用0/旧receipt監査保持。新entryはCPU禁止・cache先行確認・replay保護へ接続。固定Aと転送chunk8→4MiBだけのBでGPU/input/native175全同一、cold2.766s/Slang2→B必須hit0.287s/Slang0、CUDA/MSL/両reflectionは前回Metal175と全byte同一。比較用chunk変更は復元済み。CPU11群116(skip0)/native175成功。初回CPUのps sandbox拒否は保持し同packageを別CPU-only captureで権限付き終了検査成功、skip0。新GPU/Windows execution0/現CUDA未検証、前回175の証拠は元scopeで保持。前回静的237/266・41分類、今回効果/入力変更0、全キャラ0/UI CPU/未達。次は名前付き敵対象等の未対応契約と、本体CUDAの保存object/linkから短い検証を選ぶ。詳細docs/portable-generation-boundary.mdとcheckpoint。以下は履歴。
<!-- /generation-boundary-current -->

<!-- random-cleanse-gpu-current -->
有害所持味方のrandom selector20をprivate CUDA/Metal共通Slangへ接続。基礎18/live12/budget6/ココア全71定義3/30sの2で正本38。本人包含・解除不能候補・expiry/down/復活・人数0..5・budgetの候補probe→dispatch二重抽選/上限後0を固定。Metal169成功後budget追加175を実行、ownerメタデータ不足の比較失敗を元raw/claim保持で修正し共通replay＋独立seal175(native132/拒否43)成功、GPU再実行0。全624語MT/初期0抽選/最終所属と既存battle/traceを比較。旧125raw393216000Bと旧169raw531628032B全byte保持。CPU15群125(skip0)＋最終8成功、GPU4.365s、cache必須hit/追加Slang0。Runtime/stride138952/数値/normalizer/正本/Windows wrapper不変。静的237/266・base177/203・41分類、旧236SHA/残拒否/code順保持。Windows0/原因unknown/保全false/現CUDA未検証、全キャラ0/UI CPU/development_only/未達。次はperiodic/免疫/別carrier混在、敵デバフ実編成、現CUDA/全カタログ。詳細docs/portable-random-cleanse-gpu.mdとcheckpoint。以下は履歴。
<!-- /random-cleanse-gpu-current -->

<!-- random-cleanse-reference-current -->
共通CLI reference random-cleanseへ18正本契約を追加。本人を含む有害所持者/解除不能も候補/編成順pool/ordered sample/各人の古い順/共有carrierの部分解除/小数上限を固定。fresh packageのreference18＋CPU4群26(skip0)成功、元battle/trace/RNG/全照会回数保持。GPU受付は拒否のまま、既存125のsource/input/native期待値全同一、追加GPU/Windows0。全266profileSHA/拒否理由/42順位code保持、236/base176不変。次はexpiry/down/revive/repeated候補変化→共通Slang→全定義実編成と現CUDA。全キャラ0/UI CPU/未達。詳細docs/portable-random-cleanse-reference.mdとresearch/portable-random-cleanse-reference-checkpoint.json。以下は履歴。
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

<!-- not-core-gpu-current -->
非コア条件not_coreをCUDA/Metal共通Slangの開発専用入口へ接続。Metal1565(native1236/拒否329)と独立seal成功、新32＋旧入口拒否1も独立検証。冬ギロチン全79定義3/30秒の実ゲージ3/34回を含む。発射core snapshot、定義×caster独立binary64累積1280セル、prob別bank、重複/短絡/条件後budget、子context空と親復元、passive限定例を固定。既存Frameタグ/paddingのみ、Runtime/stride/数値/normalizer不変。旧1533の4822401024Bと新32の100663296Bを全byte保持。CPU95群500検査175.635秒/事前89.709秒/GPU11.063秒/最終26検査成功。cache必須hit/追加Slang0、親native1152再利用/84fresh/拒否329、sealはfresh。初回decode/入力散布界、GPU前の旧故障注入不成立、CPU-onlyの起動cwd失敗は保持し、期待値変更0。静的233/266・base173/203・49分類、旧232SHA/残33拒否/分類順保持。容量予算+14GiB確認、raw内容保持で6910836736B割当回収/削除0。Windows操作0、7終了の操作なしとの回答、ゲーム/動画の因果証拠なし/unknown/保全false。現CUDA未検証、private/development_only/全キャラ0/UI CPU/未達。次は通知開始HP同期とpassive maxHP/prob複合等のconsumer混在契約と全カタログ実戦を優先。詳細docs/portable-not-core-gpu.mdとresearch/portable-not-core-gpu-checkpoint.json。以下は履歴。
<!-- /not-core-gpu-current -->

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

<!-- ally-burst-current -->
味方バースト使用通知event42を共通Slangへ接続。CPU15契約とsealed ally-burst16(native15/拒否1)、ルピー：ウィンターショッパー全定義の実編成3秒/30秒2入力がMetal全一致・独立seal。旧849＋実4＋部位63も同sourceで全一致・独立sealし、旧916の全entriesとraw2881486848Bを全byte保持。新実編成の物理履歴49/471件・省略0、旧レム30秒55件省略等は維持。Runtime追加field0/stride138952、CUDA定数48B、full114/commands115 certificate更新、成功5検証のSlang0。CPU回帰312成功、新feature検査21成功。静的219/266・base159/203・76分類はGPU認定ではない。event41別段階通知は拒否のまま。Windows追加GPU/native/compile0、既存7終了unknown/環境保全falseで新規検証停止維持。初回sandboxのMetal未取得失敗・claim等を保存。全キャラ認定0/UI CPU/ゴール未達。詳細docs/portable-ally-burst.mdとresearch/portable-ally-burst-checkpoint.json。次は武器変更max_ammo_scaling_refのNone/zero/snapshot/reload契約。以下は履歴です。
<!-- /ally-burst-current -->

<!-- windows-historical-log-current -->
Windowsの既存7プロセス終了（2026-10-22 19:04:25 JST）の追加切り分け。ユーザーから同時刻前後のアプリ／ターミナル終了・Codex再接続・Windows再起動なしとの回答があり、ゲーム／動画の併用は可能性として挙がっただけで因果関係は未確認です。±2分のSystem/Applicationログを30秒上限で読み取り照会し、両方UnauthorizedAccessExceptionで取得不能（1.824秒）。イベントが存在しなかったという証拠ではありません。権限昇格・範囲拡大・再現実験・追加GPU／コンパイルは0。原因unknown・環境保全false・サービス未識別を維持し、保存済み失敗／claimを保持。Windowsの新規native/GPU検証停止を継続し、Macの独立開発を進めます。根拠はresearch/portable-scope-windows-event-log-peer-report.json（peer要約、元ログの独立監査ではない）。
<!-- /windows-historical-log-current -->

物理武器のinterrupt追加着弾を共通Slangへ接続しました。現在`parts-skill-world`63（native59／拒否4）がMetal成功・独立seal済み。スキルと同じgroup HP・総ダメージ外計上・吸血を使い、散弾・2銃口・生成後buff変更・射程境界・コア／critical分離・破壊／gate／add対象を検証しました。既存849・実4も全一致・独立seal、旧45入力・849全raw約2.67GB・実4全rawを保持。全実行は生成cache必須・Slang0回です。座標・deferred・random最終tick・実CUDA／環境保全・全キャラ認定は未完了、Windows新規実行0。詳細は[物理interrupt](portable-physical-interrupt.md)。以下は履歴です。

Slangの両生成cacheを共通CLIへ追加しました。`generation --generation-cache <dir>`でsealed sourceをCPU準備し、`--require-generation-cache`でコンパイラ起動を禁止した再利用を指定します。`run`／`compile`／`module-check`にも同じ2オプションがあります。Mac本体114sourceの実測は初回4.09秒・Slang2回→hit0.47秒・0回、別packageでMetal実4も全一致・独立監査済み。これはNVRTC cacheとは別の前段で、Windowsの速度・実CUDA一致・環境保全の証明ではありません。Windowsのstandalone生成は拒否し、追加検証停止を維持します。詳細は[生成cache](portable-generation-cache.md)。以下は履歴です。

共通Slangへ非座標skillのpierce／explosion到達、生成値・reach receipt、interrupt群のHP／総ダメージ外計上・吸血を接続しました。現在`parts-skill-world`46（native41／拒否5）がMetal成功・独立seal済み。生成後buff変更・複数破壊・壊れない対象・周期3tick・共有吸血を含みます。最終849と実4もMetal成功、旧849全raw約2.67GB・実4全raw・従来26入力を保持。物理interrupt・座標・deferred・実CUDA照合・CUDA生成cache改善は未完了、全キャラ認定0、Windows新規実行0です。詳細は[到達処理](portable-interrupt-reach.md)。以下は履歴です。

interrupt packetの7bit codec単体を共通Slangで実装し、sealed suite `interrupt-packet-codec`154（正例140／拒否14）をMetal検証・独立sealしました。本体へのincludeはまだなく、既存849／40／実4のソースは維持。次はFrameに生成値／reachを保持し、codecをreceiptの保存・読出しへ接続してからkind6群着弾・計上・吸血を接続します。初回probeの256word stride誤りは原失敗を保持して786432wordへ修正済み。Windows新規実行0。

interruptのprivate kind6／source3を共通world poolへ接続し、出現・世代・再出現・期限終了をMetalで検証しました。現在のsealed入口は`parts-skill-world`40（native30・拒否10）。既存849と実編成4も独立sealし、旧全rawと以前の26入力を保持しています。到達ダメージ・吸血・座標・deferred・修正版CUDA照合は未完了、全キャラ認定0です。Windowsの新規実行は停止中。詳細は[interrupt接続](portable-interrupt-source.md)、次の実装は[packet設計](portable-interrupt-packets-next.md)。以下は履歴です。

<!-- parts-skill-world-current -->
hits_partsの生成時二値sample→Frame snapshot→2048件専用receipt bank→live部位群着弾を共通Slangへ接続しました。新sealed suite parts-skill-world26(native25/拒否1)、skill-part-codec4(正例3/拒否1)がMetal成功・独立seal済み。最終DoT部位familyも本体と共通化、part/DoT専用counter完了を実証。旧849＋実4は同じ最終sourceで全件一致・独立seal、全input/native/output entriesと旧raw計2683305984Bが完全一致、CPU集約308成功。full closure112/commands113/Runtime stride138952、goldens/certs登録。原25入力失敗はnative観測器の固定0だったclearedを実Runへ直し、明示的なparts-cleared-v1移行監査で1ケース1項目だけの修正・他全項目同一を要求して保存raw再監査/旧失敗保持/GPU再実行0。新26は別source/inputの実GPU証拠です。詳細 docs/portable-parts-skill-gpu.md / research/portable-parts-skill-gpu-checkpoint.json。次はinterrupt Actor入力7契約、interruptの部位と異なるaccounting/吸血、座標/deferredと詳細lifecycle証明、およびCUDA保存生成物キャッシュ改善。Windows追加実行0、既存7終了cause unknownは維持し、ユーザーへ10/22 19:04:25前後の終了操作の有無だけを確認中。静的218/266・base158/203はGPU認定ではなく、全キャラ0/通常UI CPU/ゴール未達。以下は履歴です。
<!-- /parts-skill-world-current -->

<!-- damage-factors-current -->
共通ダメージの因子取得／順次積を分離し、damageValueWithPartの入口を追加しました。CUDA／Metal共通Slang、binary64／整数／pow／normalizer／protected CPUは不変です。CLI damage-factors16はMetal全bit一致・独立seal、既存849(native676/拒否173)と実4も全件一致・独立seal、旧raw2670723072B/89afa4ed...と12582912B/f83a45b0...が全byte一致、全input/native/output entries保持。CPU集約307成功。source closure111/Runtime stride138952、full/commands証明書とgoldenを実証から登録しました。details docs/portable-damage-factors.md / research/portable-damage-factors-checkpoint.json。新しい二値入口は戦闘未接続でhits_partsの受付は閉じたまま。次は生成時の二値sample診断とFrame snapshot、周期snapshotと重ならないreceipt bank、live part group landingへの接続です。Windowsは以下の7終了の原因unknownで追加実行停止、全キャラ認定0/ゴール未達を維持します。
<!-- /damage-factors-current -->

# Windows scope検証の停止記録

固定ソース`5c4bfcd`のCPU272件、PTX生成、object生成、JIT CUBIN生成は成功しました。link後の既存プロセス7件の消失により、実編成4ケースのGPU実行は開始せず停止しています。CUDAの修正版数値一致は未検証です。MacではMetal849ケースと実編成4ケースの全raw保持・独立sealが完了しています。

接続復旧後、Windows側の保存記録のみを読み取りました。7件は今回の最初のsmoke検証より前から存在し、全件が終了コード1・signaledでした。CIMとnativeの作成時刻の差はマイクロ秒への切り捨てで説明され、PID再利用として扱いません。終了はlinkのbefore観測後、約5.19ミリ秒の区間に集中し、最後の子journalの約5.7秒前でした。後始末の開始時刻そのものは記録がなく、この順序だけで因果関係は断定できません。

保存PPIDはlink子・ラッパーのPIDと一致せず、ソースレビューでは検証用Popenと新規無名Job以外を明示的に終了する処理は見つかりませんでした。実行時の原因はunknownです。環境保全はfalse、サービス識別はunverifiedを維持します。保存記録と失敗判定を変更せず、Windowsの追加native/GPU実行を止めています。復旧後の調査でGPU・コンパイル・新しいプロセス照会は実行していません。

根拠は`research/portable-scope-windows-pipeline-peer-report.json`、`research/portable-scope-windows-exit-peer-report.json`、`research/portable-scope-windows-timing-peer-report.json`です。Windows側から取得した要約であり、Macで元の全ファイルを独立監査した証明ではありません。7件の原因調査と、将来の検証で終了処理の直前・直後を記録する設計が必要です。全キャラ・全特殊効果のGPU対応は未完了です。


<!-- scope-metal-sealed-current -->
scope snapshot修正がMetal全849＋実4で保持確認・両独立seal成功。849packet d8ae57ff.../capture /tmp/nikke-scope-regression-v3-metal、CPU306全成功、GPU10.377407s、旧raw2670723072B全byte一致/89afa4ed...。実4packet edc6b6e4.../GPU3.104149s、旧raw12582912B全byte一致/f83a45b0...。入力/native/outputの全entriesも旧golden一致、source変更はworld_actor_state1fileのみ/110 closure/Runtime stride138952不変。新sealed goldens2とcompiler-full/commands証明書を実証から更新、full110/commands111/両生成指紋固定。新fresh compiler-full controller272中271成功/Win1skip/失敗0。旧Swift/CPU guard失敗全保持、old native source fixtures/hashも保持。record research/portable-scope-regression-metal-checkpoint.json。次は固定clean source共有→Windows同code full/rosters packet→CPU272/native gate1回→PTX/object/JIT各1回/各2GiB60秒、成功時のみ新CUBIN実4を1回。古いab5失敗/claimを再実行しない。残Na30の4wordが修正で消えるかは未証明、tol/normalizer変更なし。Windows現在idle、ゴール未達/全キャラ認定0/parts CPU32/UI CPU維持。以下は履歴です。
<!-- /scope-metal-sealed-current -->

<!-- scope-ledger-reconciliation-current -->
849 v2 packet a5fe2bb3...もGPU前CPUでdefinition-viewの歴史的consumer rawhash guard1件のみ停止。scope以外の改変はなし。元fixture/hashは更新せず、query-boundaryにhelper/comment/call/store/returnのexact raw逆変換を追加し、definition-viewも同じdeltaだけを元rawへ戻して旧consumer SHAへ照合。unchanged flagはfalse/approved delta listを明示、外側source/数値/wire変更は拒否する。関連query5＋definition6成功、v2で未実行だった残5group22検査を元fresh packetでCPU-only実行して全成功、GPU0。v1/v2失敗capture/packet保持、いずれもGPUclaimなし。次はcorrected fresh full packetで849全CPU→Metal1回→全raw旧2.67GB比較→独立seal、new goldens/certificates→CUDA修正版検証。Metal実4の全raw保持/独立sealは済。GPU sourceはscope1fileだけ、normalizer不変、Windowsidle。以下は履歴です。
<!-- /scope-ledger-reconciliation-current -->

<!-- scope-rosters-retained-current -->
修正候補＋private Swift cacheのMetal実4がApple M5で成功（packet edc6b6e4...、GPU3.104149秒、Runtime stride138952不変）、旧raw12582912Bと全byte一致/f83a45b0...、独立seal成功/GPU0。record research/portable-scope-rosters-metal-checkpoint.json。849最初のdevelopment packet efa7767a...はCPU query-boundary guardの2失敗だけでGPU前停止、capture /tmp/nikke-scope-regression-v1-metal/原失敗保持、GPUclaimなし。旧6注釈のみのledgerがscope修正を拒否したため、元ledger hashは据え置き、helperとcall/store/returnの完全一致するレビュー済みdeltaだけを逆変換して残全tokenを検査するguardへ更新。original_file_tokens_preserved=false/explicit_scope_snapshot_delta=true/unmodified_tokens_preserved=trueを明記、任意差分や数値式変更は拒否、新改変負例含む5検査成功。GPU normalizer変更なし。次はcorrected fresh packetで849CPU/GPU保持→全2.67GB旧raw一致→独立seal、新source golden/両compiler証明書登録→新full pipeline/短いCUDA再検証。全goal未完了/Windows現在idle。以下は履歴です。
<!-- /scope-rosters-retained-current -->

<!-- private-swift-cache-current -->
scope修正候補9b87d1fのMetal実4初回はSwift module cache書込拒否でGPU前に停止。capture /tmp/nikke-scope-rosters-v1-metal、packet2da654bd.../claim/失敗ログ保持・readbackなし。CPU-only Swift -module-cache-path /tmp/nikke-scope-swift-module-cache-v1 -e import Foundationはexit0、SDK再install不要と確認。共通Metal launcherでprivate cache argvを指定し、CLI validation envはcapture専用cacheまたは明示タスクprivate cacheを保持、親env変更なし・絶対path必須。既存deadline/新cache7検査成功。次は修正版fresh packetで実4を1回、同SDKの既存task-private cacheを再利用してlibrary再コンパイルを抑制。旧packet/claimは再実行しない。shader candidateの共通snapshot生成監査は両target成功、Metal849保持/独立seal/new compiler certと修正版CUDA比較は未完了。Windowsidle/追加GPUなし。詳細research/portable-private-swift-cache-checkpoint.json。以下は履歴です。
<!-- /private-swift-cache-current -->

<!-- scope-snapshot-candidate-current -->
共通gpu/world_actor_state.slangにnoinline uint value-return snapshot helperを追加し、旧scopeの取得をstore前の実値へ固定する候補を実装。pinned Mac Slangで現行full両生成を実行し、CUDA/Metalともhelper call→buffer store→保存uint returnに修正されることを監査済み。CUDA helperは__noinline__。新4負例＋既存resident transport3検査成功、共通resident buildに両生成のsnapshot監査を接続。生成CUDAだけのpatch/normalizer変更/数値式変更/Runtime ABI変更なし。codegen記録research/portable-scope-snapshot-codegen-checkpoint.json（GPU0/計算false）。GPU sourceは1file変更・110 closure、旧sealed golden/source certificateはまだ更新していないので通常旧suiteはstaleとして閉じる。次はdevelopment packetでMetal実4と849の全raw保持/独立seal/new source certificateを実証し、それから新full pipeline/短いCUDA比較。Na30残4wordがscope修正で解消するかは未証明。旧ab5c17b実CUDA1回のraw/失敗claimは保持、Windows現在idle/新実行未依頼、compile/GPU再実行なし。全キャラ認定0/parts CPU32/UI CPU維持。以下は履歴です。
<!-- /scope-snapshot-candidate-current -->

<!-- scope-snapshot-diagnosis-current -->
749ba6b CPU照合完了：3072block中6不一致・全6sampleをMac preserved rawと厳密比較し8wordへ確定。全4case word253955（actorFieldHead+3 query scope）はCUDA1/Metal0、ナユタ30秒のみ86024/86025（removal queue packed metadata）と512176/512178（counter-field work count/total）の4word。残3066blockは全SHA一致、native4 fingerprint一致。generated CUDA actorStatePushQuery_0が旧値のuint snapshotでなくuint*を保持し、同addressへnewscopeを書いた後return *oldpointerを行う具体的誤生成を発見。Metalはstore前に旧uintを保持して返す。Windows saved generated.cu同functionもread-only確認済み（1861674B/SHA548a1cc6...、記録SHA一致、同じstore後loadパターン）、追加GPU/compile0。共通scope差の説明がつくがNa30残4wordとの因果は未断定。次はshared Slangでnoinline value-return snapshot helper等に分離し両生成を検査、生成物の直接patch/normalizer除外/末尾の無条件zeroは禁止。GPU source未変更のまま、まだ修正未実装。変更後はMetal849+実4保持/独立seal/new source certificate→新full pipeline→必要な短いCUDA比較。全キャラ認定0/parts CPU32/UI CPU維持。詳細docs/portable-full-compiler.md、research/portable-linked-rosters-block-samples.jsonとword-differences。以下は履歴です。
<!-- /scope-snapshot-diagnosis-current -->

<!-- linked-rosters-difference-current -->
ab5c17b Windowsで保存現行CUBINを使う通常CUDA4入力1回を実行。RTX3070Ti/cuModuleLoad・Launch・Sync・readback2回/driver全19ret0、追加compiler0、source/生成CUDA/prelude/CUBIN一致、Job45.666s/peak1667842048B/実2GiB/post空/cleanup正常/missing0/25637原本保持。だが4件output指紋不一致→calculationfalse。保存JSONのCPU確認で4件すべてnative compareは例外なし/name・input・native指紋一致、raw outputのみ不一致と判別。全raw同等とは扱わず、tolerance/normalizer除外追加なし、GPU/compile/audit再実行なし。Windows現在idle、失敗claim/raw/log保持。次は新stdlib CPUブロック照合器を既存CUDA rawにだけ使う。Mac保存Metal実4 raw12582912Bはgolden f83a45b0...一致、3072block指紋indexを研究記録へ生成（rawは未共有）。readback-index/compare共通CLI＋同modulemain、全raw/SHA・二度読SHA・最大8診断block/元読取専用/出力上書禁止、5負例＋既存CLI39成功。詳細docs/portable-full-compiler.md、research/portable-linked-rosters-peer-report.jsonとhash-fields。数値/Runtime/Metal849+実4/parts CPU32/全キャラ認定0/UI CPU維持。以下は履歴です。
<!-- /linked-rosters-difference-current -->

<!-- linked-provider-current -->
現行CUBIN再利用の明示run --linked-package/--linked-captureを共通CLIへ実装。保存compiler→object→linkの全出所/元claim、full source110/両生成指紋/生成CUDA全byte/prelude/CUBINを照合し、独立provider receipt/phaseで通常NVRTC cacheと区別。CLIのcompile境界だけ一時置換し、既存backend module/実行/stream readbackを再利用、live NVRTC/fallback禁止・2GiB/60秒・private driver cache、GPU数値/Runtime/strict normalizer不変。親と独立raw比較にも全admission/専用traceを接続。新13含むfresh CPU261中260成功/Win1skip、実4 CPU/native指紋と関連19検査成功、全code packet byte一致。実GPUはまだ0。次は固定clean source共有→Windows CPU/Job smoke1回→保存現行CUBINでMetal実編成4をCUDA1回、NVRTC/ptxas/link再実行なし。実行済みclaimは維持。現行保存CUBINはfull package a247319b...、Windows C:/Users/owner/Documents/Codex/nikke-full-object-link-d1594d9-diagnostic/link/jit-linked.cubin（3877904B/91aacb33...）。実行前にdocs/portable-full-compiler.md。Metal849+実4/parts CPU32/全キャラ認定0/UI CPU維持。以下は履歴です。
<!-- /linked-provider-current -->

<!-- full-cubin-success-current -->
固定d1594d9の現行full entryでPTX→object→メモリCUBINがWindows実証。full package a247319b.../2020files/Metal基準110source・両生成指紋一致。NVRTC14.953秒/PTX7099843B c9a35121.../peak506089472、ptxas--compile-only O1 fmadfalse6.483811秒/object4141360B b658a7f4.../peak267169792、JIT0.210278秒/CUBIN3877904B 91aacb33.../peak84570112/全9return0/Destroy/params48B/driver3観測false。各2GiB/60秒/startgate/BelowNormal/post空/cleanup正常/missing0、最終25589原本・全失敗/claims/親環境保持。最終link CPU audit1回から全chain認定、CPU248/native smoke再実行なし。service未識別preservationfalse/CLI exit2、計算/全キャラ認定0は維持。Macはpeer summaryまで・raw独立監査なし。Windows現在idle/未依頼実行なし、同package・消費済みclaimを再実行しない。次は保存現行CUBINの明示providerを共通backendと独立監査へ接続（NVRTC cache偽装/自動fallbackなし）、厳密raw CUDA/prelude/全source/toolchain照合後にMetal実編成4の短いCUDA比較。実行前にdocs/portable-full-compiler.mdの接続条件を読む。GPU数値本文/Runtime/strict normalizer不変、Metal849+実4/parts CPU32維持。詳細research/portable-full-ptx-peer-report.json、portable-full-object-link-peer-report.json。以下は履歴です。
<!-- /full-cubin-success-current -->

<!-- jit-link-success-current -->
d1594d9 Windows CPU248/native gate成功後、保存旧commands objectのnvJitLink1回が成功。provider0.245787秒/CUBIN3129744B・65963e8d.../API12.4全9return0/Destroy/ET_EXEC sm86 params48B。保存CPU audit link/containment true、Job2GiB/peak82231296/post空/missing0/16492fileとDLL・object保持。service未識別preservationfalse/CLI exit2、計算/現行full battlefalseを維持。Macはpeer summaryまで・raw独立監査なし。次に同固定d1594d9の別compiler-full package a247319b...で現行PTXだけを1回依頼済み、同controller CPU/Job再検査とNVRTC以外compiler/driver/GPU0。結果評価前にobject/link自動実行しない。通常cache provider未接続/Metal849+実4/parts CPU32/全キャラ認定0維持。詳細docs/portable-jit-link-next.md、research/portable-jit-link-peer-report.json。以下は履歴です。
<!-- /jit-link-success-current -->

<!-- jit-link-controller-current -->
Windows接続復旧後、64af5fbの保存結果を再取得。新実行なし、欠落7原因unknown/service未識別/preservationfalse維持。nvJitLink明示CLI jit-link-objectを共通object controller/bounded childへ接続し、元source全chain/専用claim/固定DLL前後SHA/実Job PID・2GiB/API journal・ELF/driver module観測を監査。新9を含むfresh CPU248中247成功/Win1skip、全source byte一致。実DLLロード/link/driver/GPUはまだ0。次は固定clean sourceを共有しCPU+Job smoke1回後に保存旧commands objectのメモリlink1回、nvlink.exe/ptxas/NVRTC再実行なし。成功でも現行full battleとは別、cache provider未接続/全キャラ認定0。Metal849+実4/parts CPU32維持。詳細docs/portable-jit-link-next.md、research/portable-jit-link-controller-checkpoint.json。以下は履歴です。
<!-- /jit-link-controller-current -->

<!-- jit-link-primitive-current -->
Windows64af5fb CPU230/native I/O成立（CreateFileW新規20B/write/flush/close/実SHA/2PID/2GiB/Resume1）、nvlink固有出力は未解決。欠落7はunrelated5/service_candidate2・原因unknown、service未識別/preservationfalseを維持。保存14393file不変、追加compile/link/driver/GPU0。原失敗raw/claims保持。次候補nvJitLink12.4.127公式archive/DLL/header/LICENSEをMac静的SHA/export確認、DLL実ロード0。CUBIN AddData→Complete→GetLinkedCubin/共通ELF/Destroy/ログ保持primitiveと9疑似API検査を実装。fresh CPU239中238成功/Windows1skip。CLI実行mode/Job/source origin/cache接続は未実装で返すorigin/containment/calculationはfalse、API自動fallbackなし。次は共通bounded child/専用claim/固定DLLと元object全chain/phase監査/driver module観測を接続してからWindows1試行を選ぶ。source only旧commandsと現行compiler-fullを区別。Metal849+実4/parts CPU32/全キャラ認定0維持。詳細docs/portable-jit-link-next.md、research/portable-jit-link-primitive-checkpoint.json、portable-nvjitlink-component-candidate.jsonとnative I/O peer report。以下は履歴です。
<!-- /jit-link-primitive-current -->

<!-- native-output-probe-current -->
78121d4保存全文とexec履歴を取得。job/linkは既にrequire_escalatedで、suffixだけの変更でも同じ出力エラーのため単純な再昇格/relinkは選ばない。既存Windows smokeのnative子を固定出力probe scriptへ接続し、CreateFileW/CREATE_NEW→WriteFile20B→Flush→CloseとWin32失敗番号をJSON保存、native returnも成功判定前に保持する実装。既存上書き/設定変更なし、parentは実20B照合。fresh CPU230中229成功/Windows1skip。次は固定新packageでCPU+native I/O smokeだけ1回、compiler/link/driver/GPU0。probe成功もnvlink個別権限や計算成功とは別。元raw/claims/失敗保持。詳細docs/portable-native-output-probe.md、research/portable-native-output-probe-checkpoint.json。Metal849+実4/parts CPU32/全キャラ認定0維持。以下は履歴です。
<!-- /native-output-probe-current -->

<!-- link-output-suffix-result-current -->
78121d4 Windows CPU223/native smoke成功、出力suffix変更でもnvlinkは0.072903秒ret1/Could not open output file継続、partial/CUBINなし。2PID/実測2GiB/Resume1/peak61820928B/post空/missing0/cleanup正常、元12275file不変。単なるsuffix仮説では解消しないため比較終了、retry/flags/cap変更なし。Macは小peer summaryまで・raw独立監査ではない。次は保存全文とexecのsandbox/昇格履歴をread-onlyで取得し、native子のファイル出力権限/APIを切り分ける。Macで固定nvlink PE importsにCreateFileA/W/WriteFile/GetLastErrorを確認したが失敗API/Win32番号は未確定。再link/GPU依頼はしない。取得RPCの一度の応答待ちだけを中止し、Windows新turn未生成を確認後、read-only取得を再依頼済み。全キャラ認定0/本体CUDA未成立/Metal849+実4/parts CPU32維持。詳細research/portable-link-output-suffix-peer-report.jsonとportable-nvlink-file-api-inventory.json。以下は履歴です。
<!-- /link-output-suffix-result-current -->

<!-- link-output-suffix-current -->
f604071 Windows CPU223全成功/native smoke成功。2PID所属/停止起動/Resume1/実測2GiB/marker/return0/cleanup確認。実nvlinkは.cubin入力を認識し202B gmem/48B cmem[3]/portableEvents統計を出すが0.070901秒ret1で旧partial出力作成失敗。native Job cap2GiB/peak62898176B/post空/missing0、元10162file不変。link/計算false。次の1変数診断は一時名のみlinked.partial.cubin（末尾.cubin）へ変更、input/tool/flags/cap/公開名/検査は同じ。vendor必須仕様の証明はなく互換性仮説。fresh CPU223中222成功/Win1skip。未実行の新packageでCPU/Job gate後に1回だけ選ぶ。追加NVRTC/ptxas/driver/GPU0、元claim/失敗保持。詳細docs/portable-device-link.md、research/portable-link-output-suffix-checkpoint.jsonとportable-device-link-native-gate-peer-report.json。Metal849+実4/parts CPU32/全キャラ認定0を維持。以下は履歴です。
<!-- /link-output-suffix-current -->

<!-- native-memory-current -->
9115884 Windows CPU217全成功、停止起動/2PID所属/Resume1/marker/return0/cleanup成立だが、native観測器のmemory欄が未取得nullで最終smoke拒否。原失敗/8083file保持。共有portable_job_limitsへ従来x64 ABIを移し、Job設定とnative/outer観測が同じclass9完全144byte応答を使う修正。NULL現在Jobから実際のcap/peakを取得、照会拒否/短応答/未設定は2GiBへ推定しない。旧上限/割当/cleanup方針不変。fresh CPU223中222成功/Win1skip、新API6検査含む。次は固定修正版でCPU223+native gate smoke1回、成功時のみ.cubin入力契約の保存object link1回。追加NVRTC/ptxas/driver/GPU0、元object再生成/同条件retry/cap増加なし。Metal849+実4/parts CPU32/全キャラ認定0を維持。詳細docs/portable-native-launch.md、research/portable-native-memory-checkpoint.jsonとWindows peer report。以下は履歴です。
<!-- /native-memory-current -->

<!-- raw-device-link-current -->
LLVM nvlink wrapperの生device ELF入力契約に合わせ、link用copy名をmodule.relocatable.cubinへ変更。元module.oのbyte/SHA/ET_RELを保持、rename/再生成なし。receipt input_container=raw-device-elf-cubin-v1、argvは新名を要求。出力名/固定tool/flags/2GiB/60秒は変更なし。fresh CPU217中216成功/Windows1skip。Windows9115884はnative gate専用CPU+Job smoke進行中、リンクはまだ再実行しない。元出力エラーの原因が入力拡張子と確定したわけではない。次はgate結果確認後、別packageで同じ保存objectのlink1回を選ぶ。追加compile/link/driver/GPU0、元失敗/claims/生object保持。全キャラ認定0/本体CUDA未成立/Metal849+実4/parts CPU32維持。詳細docs/portable-device-link.mdとresearch/portable-raw-device-link-checkpoint.json。以下は履歴です。
<!-- /raw-device-link-current -->

<!-- native-launch-current -->
link profileへCREATE_SUSPENDED/BelowNormal/stdio handle listの起動adapterを接続。共通Job親子/PID作成時刻を実行前に確認してからResumeThread1回（count1のみ）、所有handleのみcleanup。旧focus/module identity/通常assembler/数値/GPU本文不変。既存Windows smokeは同じadapterで即終了Python(-I -S)を確認し、2GiB/出力marker/所属/gate/returnを要求。別Job runnerなし。fresh CPU217中216成功/Windows1skip。初回freshの共通証明書fixture不足エラー保持、whitelistを修正。実Windows gate/リンクは未検証、次はCPU+Job smokeだけ1回。Windows保存CPU診断は原object全symbol定義あり/undefined0、両dir ACL同一/短path/原8083file不変。Defender限定event昇格readは0件で原因断定不可。出力作成エラーは未解決、raw PTX共有拒否継続。full compiler packageは準備済みだがnative再試行はしない。Metal849+実4/parts CPU32/全キャラ認定0維持。詳細docs/portable-native-launch.mdとresearch/portable-native-launch-checkpoint.json。以下は履歴です。
<!-- /native-launch-current -->

<!-- device-link-failed-current -->
Windows330b204のlink1回は失敗。package2010/tool/license/元object全byte/CPU origin gate一致、CPU202全成功・Job smoke成功。nvlinkは出力作成不可、続くnative子所属確認は不成立。native return/snapshot未保存・CUBINなし・link/計算false。外Job31.986572秒/peak62066688B/2GiB/timeoutなし/post空/missing0/cleanup観測errorなし、native子の証明とは別。service未識別はpreservation=false。原失敗claim保持、retry/出力先変更/追加compile/driver/GPU0。入力.oはLLVMの生ELF.cubin要求と相違するが出力エラー原因と断定しない。Windowsへ元ACL/path/ELF symbols/保存記録のCPU-only診断を依頼済み。Mac共通engineは所属拒否snapshot/観測可能returnを今後保存する修正、関連31成功。起動前native gateは未実装。full package b9434efは準備済みだが追加native試行は診断後。全キャラ認定0/本体CUDA未成立/Metal849+実4/parts CPU32維持。詳細docs/portable-device-link.mdとresearch/portable-world-v135-device-link-peer-report.json。以下は履歴です。
<!-- /device-link-failed-current -->

<!-- full-compiler-package-current -->
compiler-fullを既存compiler-only経路へ登録。Metal849と同一full entry/全110 source/両生成指紋をsource-only certificateへ固定し、追加wrapperやGPU数学/normalizer変更なし。commandsはwrapper1追加、fullはclosure完全同一と生成指紋一致を検査。historical/通常battle拒否と2GiB/60秒/PTX/driver禁止を保持。fresh package CPU205中204成功/Windows1skip、新しいcompile/link/driver/GPU0。Windowsは固定330b204の保存旧commands object linkを検証中で、その結果を評価してから現行full compileの独立packageを選ぶ。full CUDA計算/全キャラ認定0、Metal849+実4/parts CPU32は不変。詳細docs/portable-full-compiler.md、research/portable-full-compiler-checkpoint.json。以下は履歴です。
<!-- /full-compiler-package-current -->

<!-- device-link-current -->
保存単一module.oからのlink-object CLIを共通native engineへ追加。元compiler-source-only package/producer/全source/capture/Job/claimと独立object SHAを再監査し、nvlink12.4.131の公式archive/member SHA固定。-arch=sm_86/--ignore-host-info/verbose、2GiB/60秒/BelowNormal/gate/wait55+cleanup5、専用claim・mode・artifactで通常cacheと区別。ET_EXEC/EM_CUDA/sm86/64bit/全table範囲とportableEvents実行code・SLANG_globalParams48byteを静的検査。fresh CPU202中201成功/Windows1skip、新link9・既存focus/module21保持。GPU数学/legacy assemble不変。次は固定sourceと隔離toolをWindowsへ用意し、CPU/Job smoke1回後に保存objectのlink1回のみ。新ptxas/NVRTC/driver/GPU、fallback/retry/cap増大なし。link/実行/計算は現時点未認定、旧commands-onlyと現在のfull battleを混同しない。Metal849+実4/parts CPU32/全キャラ認定0を維持。詳細docs/portable-device-link.md、research/portable-device-link-development-checkpoint.json。以下は履歴です。
<!-- /device-link-current -->

<!-- module-object-verified -->
元v135全PTXの--compile-only object生成がWindowsで成功（固定e909395、input5666316byte全byte不変/分割0、193CPU全成功）。ptxas12.4.131/O1/FMA無効、5.500616秒/ret0、module.o3327472byte/SHA c92550d36a7bc5892ffcb9f002c297227b34f7184a74827394996c2afe44b79c、CUDA format124/755sections。共通audit object_verified/containment=true、Job26.855570秒/peak219258880byte/2GiB/BelowNormal/post空/missing0、service未識別はpreservation=false/exit2。原本/全失敗/partial/claims/回収receipt/親環境保持。追加ptxas1/NVRTC/link/driver/GPU0。Macはpeer summaryまでで独立原本監査ではない。次は同版nvlinkの保存単一object実験を共通CLIへ接続し、tool版/全source chain/ET_EXEC/Job監査を準備する。PTX分割を増やしたり元objectを再生成せず進める。commands-onlyは現在のfull battleと別で、link/計算/全キャラ認定0・parts GPU未接続は未完了、Metal849+実4とparts CPU32を維持。詳細docs/portable-module-object.md、research/portable-world-v135-module-object-peer-report.json。以下は履歴です。
<!-- /module-object-verified -->

<!-- module-object-current -->
元PTX全体の明示module-object CLIを実装。focusと同じobject engine/ELF/tool/Job/監査を再利用し、元producer/cache/phaseの全byte一致からだけmodule.ptxへコピー。source_partitioned=false、module専用purpose/provider/artifact/claim/child modeを区別し、候補分割入力は拒否。通常assemble/cache/GPU数値本文は不変。fresh CPU193中192成功/Windows1skip、元focus/recovery16保持、新module5成功。次は固定sourceで元v135全体を同じ--compile-only/O1/FMA無効の1回だけ比較（2GiB/60秒/BelowNormal、CPU/Job smoke重複なし）。新NVRTC/link/driver/GPU、自動fallback/再試行/cap拡大は追加しない。単独focusのret0だけからmodule負荷・RDC効果を断定しない。全キャラ認定0/本体CUDA未成立・parts GPU未接続、Metal849+実4とparts CPU32を維持。詳細docs/portable-module-object.md、research/portable-module-object-checkpoint.json。以下は履歴です。
<!-- /module-object-current -->

<!-- saved-object-recovery-complete -->
Windows保存focus partialのCPU回収が成功（998db4e/12file237020byte全SHA一致、18.734118秒）。元ptxas0.315660秒/ret0の145024byteはCUDA format124/14sections/外部記録SHA一致、元Job containment確認。4024file・原失敗/claim/inventory/親環境は不変、追加Job/compiler/link/driver/GPU0。saved_object_cpu_verified=trueと元実行passed=false/未公開を分離、service未識別のpreservation=false/exit2を保持。Macはpeer summaryまでで独立原本監査ではない。通常cache/CUBIN/計算への昇格なし。次は元v135 PTX全体を同じ--compile-only条件で比較する明示module-object実験を共通CLIへ設計し、分離とRDCの影響を区別する。対応nvlink候補はCPU指紋確認まで・link未実行。parts GPU接続・本体CUDA計算/全キャラ認定0は未完了、Metal849+実4/parts CPU32を維持。詳細docs/portable-partition-object.md、research/portable-world-v135-focus-object-recovery-peer-report.json。以下は履歴です。
<!-- /saved-object-recovery-complete -->

<!-- saved-object-recovery-current -->
Windows75dc851のfocus実ptxasは1回、0.315660秒/ret0/145024byte partial、Job peak148045824byte/post空/missing0。元CLIはCUDA e_version124をgeneric1へ誤限定して拒否し、object_verified=false/partial/claimを保持。CUDA ELF EI_VERSIONと非ゼロformat versionを区別する修正と、別receiptだけを作るCPU-only partition-object-recoverを追加。独立記録のpartial SHA必須、元producer/candidate全再構成・固定tool/argv/ret0/Job/metadata inventory/claimを再監査し、元失敗・partialを変更/rename/再コンパイルしない。collectの元metadata-only inventoryへraw recordを捏造追加しない。fresh CPU188中187成功/Win1skip。CPU回収用の既存CLI12file/237020byteを同packageから抽出しhash固定、WindowsはそのCPU検査のみを次に行う（追加compile/link/driver/GPU0）。サービス未識別・link/計算未認定、全キャラ認定0/本体CUDA未成立。詳細docs/portable-partition-object.md、research/portable-object-recovery-checkpoint.jsonとportable-world-v135-focus-object-format-peer-report.json。以下は履歴です。
<!-- /saved-object-recovery-current -->

<!-- historical-producer-current -->
Windows5801e81の保存結果を回収。CPU181全成功/Job smoke成功（post空/missing0/service未識別）、objectは旧producerに現行heal-share証明書を要求してnative compiler/実験Job/capture/claim前に停止。原失敗と全input保持、追加compile/GPU0。修正版は診断経路だけ元manifest/全records/唯一certificate/基準hash/source closureへ結び、古いproducerと現在のbattle基準を混同しない。通常assemble/current cacheの同一source条件は不変。fresh CPU185中184成功/Windows1skip、実保存compiler packet3種もread-only監査成功。事前失敗もfresh captureへ保存・audit false、claim消費前に停止。次は固定修正版でCPU/Job共通smokeを1回だけ行い、元v135上流監査成功時のみfocus object1試行。PTX公開拒否は迂回しない。全キャラ認定0/本体CUDA未成立・Metal849+実4/parts CPU32維持。詳細docs/portable-partition-object.md、research/portable-historical-producer-checkpoint.jsonとportable-world-v135-focus-object-preflight-peer-report.json。以下は履歴です。
<!-- /historical-producer-current -->

<!-- partition-object-current -->
共通CLI partition-objectへ保存candidateのfocus専用relocatable object実験経路を追加。元producerのcompile/Job監査＋cache/phaseからcandidate全体再構成＋producer SHA/key照合を親/子/事後で再利用。固定12.4.131・O1/fmad=falseに明示--compile-only、既存bounded Job2GiB/60秒/BelowNormal・専用claim/ELF ET_REL検査、失敗/partial保持。既存assemble/通常cache/数値/共通GPU本文は不変。fresh immutable CPU181中180成功/Windows1skip、新故障注入11成功。固定5801e81をWindowsへ依頼済み。package ID/2007file table完全一致とJob smoke成功のpeer報告後、接続が利用不能となり、実assemblerの開始/終端・object/最終containmentは未確認。同じturnの保存結果だけを回収し、再実行を依頼しない。詳細research/portable-world-v135-focus-object-pending.json。remainder/link/driver/GPUへ自動移行しない。Macで公式12.4.131 archive/nvlink memberのSHAとLICENSEを確認（tool実行/link互換性は未確認）。全キャラ認定0/本体CUDA未成立・Metal849+実4とparts CPU32維持。詳細docs/portable-partition-object.md、research/portable-partition-object-development-checkpoint.json。以下は履歴です。
<!-- /partition-object-current -->

<!-- ptx-partition-tool-current -->
共通CLI ptx-partitionの保存v135に対するWindows CPU確認が成功。固定f7e83ccの8ファイル照合・16検査2.1443秒、候補生成4.4559秒、元cache/phaseからの再構成監査4.1026秒。191 bodyをfocus1/remainder190へ保持、global/const101定義はremainder単独。focus applyDefinitionFrame_0は306333byte、remainder5477943byte。元PTX/cache/phaseと親環境は不変、compile/link/driver/GPU追加0。原本・候補・完全planはWindowsに残り、Macはpeer summary取得までで独立原本監査ではない。PTX＋出所JSONの明示共有許可は受領済みだが、Windows自動承認レビューが別チャットの回答を認めずpushを再拒否。別経路転送・再pushは行わずWindowsチャット側の承認解決待ち。次は独立object実験のtool/link/ABI・明示manifestを準備する。partition合法性/コンパイル/計算は未認定、本体CUDA未成立/認定0、Metal849+実4とparts CPU32を維持。詳細docs/portable-ptx-partition.md、research/portable-world-v135-partition-peer-report.json。以下は履歴です。
<!-- /ptx-partition-tool-current -->

<!-- v135-callgraph-analysis-current -->
Windows保存v135のcache/phaseを共通ptx-stats --callgraphでCPU解析成功。191定義すべてportableEventsから到達、SCC191個/循環0、間接/外部/未解決0。最大applyDefinitionFrame_0の5865virtual/10472行/local宣言56byteは物理memoryに換算しない。9テスト成功＋解析1.692秒/BelowNormal、追加compile/GPU0。最初のTEMP権限7pass/2errorは保持し、既存validation_environmentで別captureの環境設定だけ修正。完全261KBreportと元PTXはWindowsに残し、Macはpeer summaryのorigin/source fields照合まで（独立原本監査ではない）。次は共通CLIのCPU分割計画/ABI/global所有権検査を実装し、準備後に必要な新しいcompiler専用実験を選ぶ。単なるdead-function削除やcall循環対策は今回根拠なし。本体CUDA未成立/全キャラ認定0、Metal849+実4とparts CPU32を維持。詳細docs/portable-v135-callgraph-analysis.md、research/portable-world-v135-callgraph-peer-report.json。以下は履歴です。
<!-- /v135-callgraph-analysis-current -->

<!-- ptx-callgraph-tool-current -->
保存PTXのCPU-only ptx-stats --callgraphを追加。既存cache key/bytes/SHA/phase receipt照合を再利用、全直接call/entry閉包/SCC/宣言・loadstore統計を出す。間接/外部/未解決は明示しclosed判定false、PTX分割合法性とcompiler memoryの認定はfalse。fresh共通smoke163中162成功/Windows1skip、選択60成功、既存CLI6ファイル約142KBのCPU受渡し9検査成功。legacy PTX3つもread-only解析できたがv135ではない。次はWindowsの保存v135 cache/phaseだけをCPU解析し、小さな派生summaryを取得。NVRTC/ptxas/driver/GPU追加0、PTX本体公開は個別確認待ちのまま。詳細docs/portable-ptx-callgraph.mdとresearch/portable-ptx-callgraph-cpu-checkpoint.json。以下は履歴です。
<!-- /ptx-callgraph-tool-current -->

<!-- parts-lifecycle-current -->
parts-skill-lifecycle7の生成stats／着弾live部位／group破壊→子回復順序を共通reference CLIで検証。parts32＝通常31＋deferred gap1、影響25検査成功、旧25全input/native/trace/contract指紋保持。倍率を変更するnamed子の前に生成値を固定、同時2発の2発目は生成part値を保持しても先行破壊後の着弾part集合は空、同名再出現はopen ordinalで区別。GPU source閉包は旧849不変・追加GPU/Windows0・受付閉。次はdocs/portable-parts-skill-next.mdのcaptured stats/Frame/receipt/部位group接続を実装する条件を満たし、CUDA保存PTXで判別可能なcompiler実験を設計。本体CUDA未成立・全キャラ認定0/UI CPU。詳細research/portable-parts-lifecycle-reference-checkpoint.json。以下は履歴です。
<!-- /parts-lifecycle-current -->

<!-- parts-review-current -->
Claudeレビュー反映：共通reference CLIは最適化Pythonをnative前に拒否・失敗保持、parts検査は明示例外、positive/model-gap別集計。parts15＋extended10＝25CPU契約（24通常＋deferred gap1）、非飽和吸血/interrupt/sharedを追加。fresh影響38検査成功、旧22全native既存field/trace保持。oracle追加でinput指紋は意図変更。GPU source全閉包は旧849同一、追加GPU/Windows0・GPU受付閉。本体CUDA未成立/全キャラ認定0/UI CPU。次は生成時stats snapshotと着弾のgeneration/子イベント契約を補強し、保存PTXに基づく判別可能なCUDA実験を設計。at+7は周期処理使用済みなので再利用不可。詳細portable-parts-skill-reference-checkpoint.json、docs/claude-overall-review-8b77b1f.md。以下は履歴です。
<!-- /parts-review-current -->

<!-- heal-real-rosters-current -->
heal-share-rosters4（ナユタ/レムの全定義3秒/30秒）をMetal一致・GPU0 seal。定義81/70のbinding欠落0、source/両生成指紋は旧849と同一、849再実行0。レム30秒だけ物理履歴2103中2048記録/55省略、prefix+省略数と全戦闘結果までで未記録packet完全照合は未証明。最終CPU preflight/既存6検査/readiness22成功。全266入力と80順位保持、hits_parts3分類をsource確認済み・CPU契約0のlaneへ。次はdocs/portable-parts-skill-next.mdのCPU契約を作成し共通receiptへ移植。GPU source変更時は849＋実4を保持。本体CUDA未成立/認定0/UI CPU、Windows追加0、保存PTX共有は個別確認未回答。詳細docs/portable-heal-share-real-rosters.mdとresearch/portable-heal-share-real-rosters-checkpoint.json。以下は履歴です。
<!-- /heal-real-rosters-current -->

<!-- healing-share-gpu-current -->
現在はheal-share-regression849(native676/拒否173)をMetal全一致・GPU0独立seal。回復分配のmembership→既存Frame mode31→HP/storage/同期子イベント→元通知へ共通接続、normal stat75なしfast pathを保持。診断53も全一致（plan/portion/元通知を直接比較、HP notify profiler列は明示的対象外）。旧796全input/native/raw・2.50GB直接比較/lazyゼロ保持、Runtime247/138952不変。CPU893中892成功/Win1skip、最終compiler smoke158中157成功/Win1skip＋更新certificate9成功。静的packing216/base156で新ナユタ/レムは入力受付だけ。次は全定義の3秒/30秒実編成を検証。本体CUDA未成立・認定0・UI CPU、Windows追加0。保存PTXの個別共有確認は未回答・再実行しない。詳細docs/portable-heal-share-gpu.md、research/portable-heal-share-gpu-checkpoint.json。以下は履歴です。
<!-- /healing-share-gpu-current -->

<!-- heal-plan-current -->
回復分配のCPU参照は43（元34全input/native/trace/contract保持＋lifesteal9）、関連18成功。共通heal_share_plan.slangを実装し、独立Metal10入力（literal8＋拒否2）が一致、GPU0 seal、通常sealed CLI登録。planのみでmembership/HP/storage/DFS通知への接続は未実装・heal_split受付は閉じたまま。portable887は885成功/Win1skip/ps拒否1、同packageの観測5再確認成功。誤った広い1260 discoveryの失敗も保持。GPU実行1/Windows0。詳細research/portable-heal-share-plan-checkpoint.json、portable-heal-share-lifesteal-reference-checkpoint.json、接続計画docs/portable-heal-share-gpu-next.md。保存PTX共有の個別確認は未回答・再実行しない。以下は履歴です。
<!-- /heal-plan-current -->

<!-- heal-targets-current -->
共通CLI referenceへheal-share-targets6を追加、旧28の全input/native/trace/contract保持・関連15検査成功。self＋RL上位2／重複／RLなし／別carrier重み／同率／別ownerを検査。正本sync_hpの除算→乗算を反映しHP5500の55.00000000000001を厳密比較、55.0再結合は故障注入で拒否、元失敗保持。readiness記録34とfresh21検査成功。GPU source/受付変更・GPU/Windows追加実行0、lifesteal等と本体CUDA成立は未完了。詳細research/portable-heal-share-target-reference-checkpoint.json。以下は履歴です。
<!-- /heal-targets-current -->

<!-- reference-readiness-current -->
最新レビューはdocs/claude-overall-review-0e1f71b.md。未対応82分類へ保守的な作業laneを追加、全266 profile/input/issueと旧順位を保持。21検査とfresh inventory成功、GPU/CPU battle0、packing214/base154・認定0は不変。詳細research/portable-reference-readiness-checkpoint.json。v135はPTX生成/cache再読成功、commands assemblyはMemory allocation failure、post空/missing0だがservice未識別でpreservation=false。詳細research/portable-world-v135-definition-view-compiler-sanitized.json。単なるgetter/構造体縮小試行を追加せず、保存PTXの関数負荷とmodule負荷を区別できるCPU分析・明示実験契約を優先。PTX共有は自動承認拒否で個別許可待ち、再実行しない。heal_split composite対象とlifestealはCPU契約未被覆。以下は履歴です。
<!-- /reference-readiness-current -->

<!-- definition-view-current -->
現在の通常入口はentry-reload-regressionの新golden portable-world-definition-view-regression-short-expected.json。Definitionを55項目の一括値からwire input/row+ローカルoverride5uintへ変更し、getter/型/初期化/元全consumerを固定Gitに照合。Metal probe6はadapter戻り値だけを訂正して元GPU結果をG0 replay/seal、原失敗保持。full796/native633全一致・旧2.50GB全byte/input/native保持・独立G0 seal成功、GPU9.755秒は単一観測。全CPU870中869/Windows1skip、影響5/diagnostic9再確認、compiler packet smoke158成功。Runtime247/138952/48byte不変、CUDAmemory改善は未確認。次は固定sourceを共有し、commands-only PTX1回＋正常receipt/cache/containment時だけAOT1回(各60秒/2GiB)。v134欠落7はunknown/preservation=falseのまま、driver/kernelやfallbackは追加しない。詳細docs/portable-definition-view.md、research/portable-definition-view-checkpoint.json。回復分配28はCPU契約のみ・全キャラGPU認定0・UI CPU。以下は履歴です。
<!-- /definition-view-current -->

<!-- v134-and-definition-prototype-current -->
現在の根拠はresearch/portable-world-v134-commands-compiler-sanitized.json／portable-world-v134-saved-compiler-analysis.json。v133 fixtureのWin pathを88bce89で修正、v134はsmoke153全成功、commands PTX5.46MB/11.094秒と同key cache hit成功、独立assembly1回はMemory allocation failureで未成立。Job post空だが既存process7欠落・原因unknown、service unverifiedでpreservation=false。driver/module/kernel0。init/write追加やRDC等の自動fallbackはしない。追加CPU解析でPTX191関数/maxvirtual5328（basicConditions）を確認。Macの一時Definition wire-view案（55項目一括248byte推定→5uint20byte）はCUDA／Metal生成だけ成功し、生成CUDA量は増えておりメモリ改善未証明、本worktreeのGPU本文は未変更。次はsnapshot/override/55getter契約を確認してからMetal796候補へ。詳細docs/portable-definition-view-prototype.md。回復分配は元20完全保持＋追加8をCPU検証・関連11/通常smoke153成功、GPU接続は未完了。全キャラ認定0・UI CPU。以下は履歴です。
<!-- /v134-and-definition-prototype-current -->

<!-- compiler-diagnostic-current -->
現在はcompiler-commandsの固定compiler-diagnostic packageを追加し、既存compile/cache-check/assemble/監査/Jobを再利用。full796の共有本文は不変、診断入口1ファイルのみ追加。通常run/adapter/moduleとbattle認定を拒否、PTX/2GiB/60秒を子・親・保存監査で固定。fresh aaec8ca7で全CPU861中860成功/Windows1skip、smoke153、生成指紋/layout247/138952/48byte一致。次は固定コミット共有後、Windowsでこのcommands PTX1回＋成功時のみ独立assembly1回。通常fullを再実行せず、失敗時のinit/write・RDC等の自動追加も禁止。詳細docs/portable-compiler-diagnostic.md、research/portable-compiler-diagnostic-checkpoint.json。以下は履歴です。
<!-- /compiler-diagnostic-current -->

<!-- phase-codegen-current -->
次のcompiler調査用に共通CLI phase-codegenを追加。fresh package8470d38eで同Slang本文からinit/commands/write各CUDA／Metal全6生成、全CPU852中851成功/Windows1skip。CUDA生成量は本体1.66MB/652関数に対しinit543KB/170、commands1.20MB/573、write169KB/153。commands閉包は大きく残り、ptxasメモリ改善や本番複数kernelは未証明。詳細docs/portable-phase-codegen.md、research/portable-phase-codegen-checkpoint.json。新しいGPU/Windows実行0。次はcommands診断の固定source/生成物/compiler/cacheとbounded Jobを結ぶcompiler専用package契約を設計し、事前検査後の必要な1試行だけを検討。以下は履歴です。
<!-- /phase-codegen-current -->

<!-- heal-share-reference-current -->
現在の入口はdocs/claude-overall-review-e630078-2026-10-22.mdとdocs/portable-heal-share.md、状態はresearch/portable-heal-share-reference-checkpoint.json／portable-query-boundaries-checkpoint.json。heal-shareはCPU契約20・観測器透明性・入れ子snapshot・hook連鎖の7テスト成功、共通CLI reference登録済み、GPU受付未追加。fresh846検査はsandboxのps拒否1件を同packageの影響群5件で再確認して全成功、Windows専用1skip。既存796/native633のCPU全指紋も保持。Windows v132はPTX6.72MB/最大virtual5931へ減少したがassembly失敗。保存stdoutの再読でMemory allocation failureを確認（再実行0）、gate開放時刻／直前harness memoryは未取得。次は同共有本文のcompiler到達範囲の切り分けをMacで設計する。全キャラ認定0・full796 CUDA未成立・UI CPUを維持。以下は履歴です。
<!-- /heal-share-reference-current -->

<!-- query-boundaries-current -->
6個の既存query/actor command関数へnoinlineだけ追加、元5ファイルの全tokenを固定8fdaf47と同一に保持。fresh CPU839中838成功/Windows1skip、CUDA全6境界・uint Runtime handle確認、652関数/noinline226。Metal796/native633全一致、旧全input/raw/native指紋と2.50GB直接比較/lazy bankゼロ、GPU0独立seal成功。現sealed goldenはportable-world-query-boundaries-regression-short-expected.json。WindowsはPTX1回→保存v128とのCPU全関数max/size比較→事前gate成立時だけ独立assembly1回（各60秒/2GiB）を準備。driver/kernelは追加しません。全キャラ認定0/full796 CUDA未完了。詳細portable-query-boundaries.md/checkpoint。以下は履歴です。
<!-- /query-boundaries-current -->

<!-- cpu-batch-and-v131-current -->
共通CLIのCPUテストを1 fresh workerへまとめ、旧37群245件を全保持+故障注入7件で38群252件、単一観測50.087→34.783秒。fresh全CPU834中833成功/Windows1skip、全796/native633のCPU preflight成功、追加GPU0。Windows v131（固定438d357）はCPU129とtiny binding4 CUDAの実転送/12MiB全比較・Mac golden一致、8+4MiB copy/zero/1launch/sync/context破棄/48byteABI、2GiB Job peak406MB/post空/missing0を確認。service未識別はpreservation=false/exit2。CUBIN再読cache hitは追加NVRTC/driver/GPU0。新CPU workerのWindows確認は次の必要検証へ。full796 CUDA compiler/module・全キャラ認定0・UI CPUは未完了。次は保存PTX/callgraphに基づく限定的なcompiler境界改善を検討し、v130同条件再実行はしません。詳細portable-cpu-batch.md/file-transfer.md/checkpoints。以下は履歴です。
<!-- /cpu-batch-and-v131-current -->

<!-- file-transfer-current -->
共通CLIを8MiB file保存へ接続。CUDAのdevice zero/offset付き分割DtoH、Metalの分割write、exclusive final公開、unused child domains解放、全chunk/zero/context破棄のtrace監査を実装。fresh CPU827中826成功/Windows1skip、Metal796/native633/全input・output・旧comparison全一致（新実行1回）。小さいbinding4もMetal実行・GPU0独立seal、新専用goldenでWindowsの短い実転送を準備。通常bytes APIは維持。全796 CUDA compiler/module・全キャラ認定0は未完了。詳細portable-file-transfer.md/checkpoint。以下は履歴です。
<!-- /file-transfer-current -->

<!-- offline-assembly-v130-current -->
Windows v130のoffline assemblyは1回失敗で終了・idleです。正規承認経路でCPU107とsmoke/観測成功後、固定12.4.131 tool/元PTX SHAを照合。ptxas9.174秒/exit4294967295、2GiB Job peak2,147,573,760byte、stderr0、ELF/partial0。harness+assemblerの正確なJob所属と親/作成時刻、post空/missing0/cleanup・observation正常を確認。service未識別でpreservation=false、原因未確定、NVRTC/driver/kernel0。v129はsandbox snapshot失敗でgate前停止した原失敗を保持。再試行/上限拡大/fallbackなし。詳細portable-offline-assembly.mdとv130 sanitized。次はMacでbounded transfer/child保存と、証拠に基づくcompiler負荷削減へ。全キャラ認定0・新版CUDA計算未確認・目標未完了です。以下は履歴です。
<!-- /offline-assembly-v130-current -->

<!-- compact-input-current -->
共通regressionの796 word行をarray('I')へcompact化、各行の元wire照合とdomain identityは維持。保存Metal796/native633/全input・全output・comparison全一致、GPU0。Macのprepare最大RSS2,354,872,320→1,808,695,296byte、全監査1,812,381,696byte。全CPU812のlist型固定テスト1件を内容/domain/wire/array型の契約へ修正し、fresh関連5件成功（他810成功/Windows1skip）。GPU本体と比較器不変。CUDA transfer/child保存のstream接続は未完了。Windows v130は権限修正後smoke107成功/missing0/post空、offline assembly1回失敗、追加実行せず保存証拠取得中。詳細portable-compact-input.md/checkpoint。以下は履歴です。
<!-- /compact-input-current -->

<!-- stream-audit-current -->
共通CLIのartifact SHAと親readback監査を固定8MiB/1case読取りへ変更。fresh package CPU809中808成功・Windows1skip、保存Metal796/全2.50GBをnative633と再照合し旧comparison全一致（GPU0）。ただし最大RSS2,365,014,016byteで全体2GiB未達。次は入力準備peakとword表現、CUDA transfer/child保存のstream化が必要です。Windows v129はCPU107pass後、snapshot取得失敗でgate前停止。ptxas取得/assembly/driver/GPU0、再試行せずCPU観測診断中。詳細portable-stream-audit.md/checkpoint。以下は履歴です。
<!-- /stream-audit-current -->

<!-- offline-assembly-current -->
共通CLIへ保存PTX専用の `assemble` を追加しました。固定tool SHA、元producerの既存監査、fresh BelowNormal Job/start gate、2GiB/60秒、別claim、ELF/phase監査を再利用します。NVRTC/driver/kernel0、fallback/retryなし。Macではcomponentをdownloadしwheel/EXE SHAを確認、実行していません。fresh immutable packageのCPU805件は803成功・Windows1skip・sandboxのps拒否1件で、当該phase群5件はOS観測許可で全成功しました。GPU本体/adapter/transportは実行済みMetal796とbyte同一。Windows実assemblerは未実行、CUBIN cache接続/driver load/stream転送/新版CUDA計算は未完了。詳細docs/portable-offline-assembly.mdとdevelopment checkpoint。以下は履歴です。
<!-- /offline-assembly-current -->

<!-- weapon-phases-current -->
## 共通武器フレーム分割とMetal796

現在のsealed suiteはentry-reload-regression796（native633／拒否163）、goldenはportable-world-weapon-phases-regression-short-expected.jsonです。武器本体を共有5 helperへ分割し、2,287 tokenの処理文を再構成、引数・snapshot・早期returnを検査しました。CUDA生成にもnoinline5境界が存在します。Runtime247／138952byte／align8と入力は変更していません。

Metal796全件一致、分割前796の全input／raw／native、全lazy bankゼロを確認し、GPU禁止の独立sealが成功。SHA b9cd45185fb37568494df918a71d4b115b7853e26e8eba0b1af5d307f6d30637、2,503,999,488byte。CPU788中787成功・Windows専用1skip、その後signature guard5件も成功。詳細portable-weapon-phases.md、development checkpoint、retention、compiler-structureを参照してください。

通常UI CPU、全キャラ認定0、packing214/266は入力受付のみ、entry_reloadのcover4件・新版CUDA計算は未完了です。v126既定JITとv127明示JIT1は旧Runtime246のPTXに対するメモリ確保失敗でした。固定976fb99のWindows v128はsmoke91・PTX生成・新cache hit・normalized source一致まで成功しましたが、JIT1 moduleはCUDA218／メモリ確保失敗でした。context破棄0・post Job空・missing0・service未識別、kernel0／計算未確認。保存PTX最大virtual宣言はexecutePortableCommands10927、武器root70。単なるサイズ指標で原因とは扱いません。Claude限定レビューの指摘を実ソースへ照合し、追加GPU実行や盲目的な文分割を止め、offline assemblerの段階分離を優先候補にしました。既存Windows ptxasは11.3.58で、新PTX向けに12.4.131の隔離component metadataを選定済みですが、まだdownload／offline compileしていません。macro escape契約を7検査へ補強し、scratch memset推奨は初期化コードを確認して不採用にしました。詳細claude-cuda-followup-976fb99-2026-10-22.md。全796のCUDA転送には2.50GBの一括ホスト確保を抑える修正も必要です。以下は履歴です。
<!-- /weapon-phases-current -->

<!-- entry-reload-current -->
## 共通entry_reloadの現在地

独立37（native31／拒否6）と集約796（native633／拒否163）がMetalで一致しました。CPU35契約のうちcover操作4件は既存control adapterが拒否するため未対応です。毎実tickのreloadDuration照会、元武器時間、fixed負値、明示delay0、待機latch、弾倉・charge開始を共有実行器へ接続し、照会owner／時刻／値の全順序を独立CPUと比較しました。Runtimeは247 fields／138952byte／align8。詳細はdocs/portable-entry-reload-gpu.md、checkpointと保持検査を参照してください。以下の旧759は履歴です。

全portable CPU784件中783成功・Windows専用1skip・失敗0。静的packing214/266（base154）は入力受付で、全キャラGPU認定ではありません。通常UI CPU、全キャラ認定0、新版CUDA計算未確認、目標未完了です。接続復旧後にv126最終報告を取得し、既定JITのmodule失敗（CUDA218、メモリ確保失敗）・context破棄0・post Job空・missing0を記録しました。Macの原capture独立監査ではありません。明示JITレベル1の検証コードは固定6b1a15eにあり、新sourceで既存v125 cacheを照合したことにはしません。固定6b1a15eのv127はCPU smoke86・PTX hit・JIT level1実引数照合まで成功しましたがmodule loadがCUDA218／メモリ確保失敗でした。context破棄0・post Job空・missing0・service未識別、kernel0／計算未確認です。同条件再実行は行いません。
<!-- /entry-reload-current -->

<!-- entry-reference-nvrtc-current -->
entry_reloadを共通CLIのreferenceへ接続し、full-world32契約と全戦闘／traceの観測透明性を確認。GPU対応は未実装です。NVRTC12.4のv119依存ロード失敗を共通loaderで修正し、v120は両DLLロード成功後にCUBINのptxas allocation failure（42.402秒／2GiB付近）で終了。Windows追加試行は止めました。次はGPU常駐Runtime参照の構造仮説をMacで検討します。小さいコード生成4件は成功していますが本体は未変更です。詳細は[CPU契約](portable-entry-reload-next.md)と[Runtime検討](portable-runtime-storage-next.md)。通常UI CPU・全キャラ認定0・最終目標未完了。
<!-- /entry-reference-nvrtc-current -->

<!-- parent-audit-current -->
CLIのchild／親とreplayの重複CPU比較を整理しました。計算本体・goldenは変更せず、保存Metal759を新しい親監査器で再照合しています。詳細と検証記録は[親監査の変更](portable-parent-audit.md)を参照してください。次はCUDAのコンパイル成立の仮説とentry_reloadのCPU正本契約を優先します。
<!-- /parent-audit-current -->

<!-- revival-notify-current -->
## seedと通知規約を反映した蘇生の共通実行器とMetal759

現在のsealed CLIはregression759（native602／拒否157）、goldenはportable-world-revival-notify-regression-short-expected.jsonです。reviveの永続definition保持、数値／markerパッシブの復元、persist、共有carrier対象の再追加、HP同期・満弾行動resetと自己蘇生後の通知を共通Slangへ接続しました。味方class randomは敵RNGと別のMT bankを使い、budget前照会で捨てる抽選も含め正本の全stateと位置を一致させています。Runtime配列は追加していません。

独立31（native22／拒否9）に加え、seed0／42で抽選を発火する2入力と、共有再追加／新規再生成の通知対照2入力を集約へ追加しました。実編成のRunPlan.seedもstatic preparationで保持してMODEへ渡します。初期755では実編成6入力が抽選0回だったためfixture既定19の転送漏れを検出できず、成功結果とseed findingを保持しました。実ディーゼル：ウィンタースイーツ／ラプンツェル／マナの全定義3秒／30秒を含む最終759全件一致・GPU0 sealを確認済みです。

旧718全input／raw／nativeはarchive全展開SHAも確認して保持。独立31は診断tailとpeak／total work2語の明示的減少を除くrawと全759のlazy bankゼロも一致。新規6実編成の物理履歴省略は0、既存ミハラ／persona等の省略制約は残ります。途中の対象packing漏れ、対象順／ログ出力、破壊ログkind5衝突、charge最低周期／global RNG事前照会の失敗も保持しています。CPUの旧revive未対応負例は未知instantへ移行。最終CPU731件中730成功・Windows専用1skip・失敗0です。

静的packing213/266・base153/203・83分類、通常UI CPU・全キャラGPU認定0・新版CUDA数値一致未確認・最終目標未完了。Windows追加実行0。共有carrierへの再追加は名前付き通知を再発火せず、新規再生成だけが通常のactivation通知を行う対照2ケースも追加しました。生成CUDA差分は記録を参照。Runtime全field同一・推定138,928byteで、compiler改善ではありません。HP条件付きpassiveの一部でpinned CPUが復帰中None比較のTypeErrorになる参照制約は残し、26fixtureで全組合せを認定したとは扱いません。次は正本consumerがあるentry_reload／damage HP basis等を検討します。詳細docs/portable-revival.mdとdevelopment checkpoint。以下は履歴です。
<!-- /revival-notify-current -->

<!-- revive-reference-current -->
## 蘇生のCPU正本契約：GPU接続は未完了

共通CLIに`reference --suite revive --out /tmp/revive-reference.json`を追加しました。packing／GPUを禁止し、18 literalケースで23 down・15 reviveの実処理と共有carrier／HP／行動／通知／クラスrandomの契約を確認します。失敗も保存し、同名出力への再実行を拒否。GPU監査器と既存full-native observerを再利用し、GPU source／goldenは要求しません。native参照約1.4秒、専用CPU5検査と既存CLI28検査が成功しました。

全18の既存battle／skill traceは観測器の有無で一致。クラスrandomは敵専用RNGと別のPython global RNGで、空集合は無消費、1候補のsampleは消費します。GPU移植時は状態を混同しないでください。約1.9MBの詳細はローカル、小さな指紋・契約・source identityだけを共有します。

今回GPU source変更・GPU実行・Windows実行は0、sealed Metal718・静的210/266・通常UI CPU・全キャラGPU認定0のままです。次は失われた永続効果のdefinition順序を保持するledger、shared対象の再追加、復帰中HP同期抑止と満弾行動resetを通知DFSへ接続します。revive／persist／down-only selectorのGPU受付は未実装です。詳細docs/portable-revive-next.md、research/portable-revive-reference-checkpoint.json。以下は履歴です。
<!-- /revive-reference-current -->

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

<!-- named-magnitude-current -->
## 名前付き係数／被ダメージ倍率とMetal588

現在の通常CLIはregression588（native459／拒否129）、goldenはportable-world-named-magnitude-regression-short-expected.jsonです。canonical78／80を共通Slangへ接続し、独立54（正43／拒否11）とブレイディ／エマの全定義実編成3秒／30秒を追加しました。Metal588全件一致、旧530・独立54の全input／raw／native保持、全588のlazy scratchゼロ、GPU禁止sealを確認済みです。CPU711件・Windows専用1skip・失敗0。詳細docs/portable-named-magnitude.md、research/portable-named-magnitude-retention.json、development checkpoint。

初回52は48一致・4失敗で原captureを保持。倍率後0の通常スキルを最小1ダメージのヒットとして残し、保留0係数はbuff query後にスキップする正本の差を修正。保留3件はdecoder未接続のため、既存3カウンタreadを共有し、原rawでも全native一致を診断しました。原失敗は成功へ書き換えていません。追加実編成4件の物理履歴省略は0ですが、過去persona等の省略制約は残ります。

静的packing201/266・base142/203・104分類、通常UI CPU・全キャラGPU認定0・新版CUDA数値一致未確認・最終目標未完了。stat79のATK倍率、random／code対象（イブ等）は未対応です。CUDA v115 cold compilerのallocation failureは未解決で、今回の機能でWindowsの追加実行は0です。v117 CPU53件成功は以前のcache/controller検証であり、CUDA計算一致ではありません。次のcompiler変更には、同条件再試行でなく新しい仮説・計測・停止条件が必要です。以下は履歴です。
<!-- /named-magnitude-current -->

<!-- persona-current -->
## ペルソナ状態・B3対象とMetal530

現在の通常CLIはregression530（native412／拒否118）、goldenはportable-world-persona-regression-short-expected.jsonです。persona_state存在マーカーと本来のB3味方対象（selector18）を共通Slangへ接続し、独立41入力とクイーン／ユキコ／アイギスの実編成・3人同時編成を追加しました。Metal530全件一致、旧481・独立33・原522の成功518の全input／raw／native保持、全530のlazy scratchゼロ、GPU禁止sealを確認済みです。CPU708成功・Windows専用1skip・失敗0。

原522でクイーン／ユキコ4入力が拒否された失敗は保持しています。診断でTARGET_CODE44のactor-field追加条件受付漏れを特定し、既存共通評価器へ接続。不一致／不正codeと名前表の完全一致も検査します。物理履歴の2048件上限によりユキコ30秒32件・3人同時30秒2123件を省略しており、記録prefixと省略数・全戦闘状態の一致までの確認です。省略packet個別一致ではありません。詳細portable-persona.md、portable-persona-retention.json、portable-persona-development-checkpoint.json。

CUDA cacheは同一keyのmiss時に排他的claimを取得し、競合を即時拒否・取得後のhit再検査・自ownerのみ解放・異常終了claim保持を実装しました。実プロセスを使うCPU検査もfake compilerであり、NVRTC実行やcoldコンパイル改善の証明ではありません。共通CLIのsmokeはcleanup4＋CLI27＋cache12＋artifact10の53件とfresh Jobだけです。必要test欠落はJob前に拒否します。Windows v116はCPU43件中42成功・cache PID前提の1件失敗で停止、artifactとfresh smoke Jobは未到達。原失敗を保持し、テストchildをbase Pythonへ変更。Mac cache12＋CLI27＋artifact10成功後、固定d5ccaf5のWindows v117はCPU53件とfresh Job smoke成功（全体15.268秒／Job6.129秒、post空）。既存process欠落7・原因unknown・service未識別なので環境保持成功とはせず、新版CUDA数値一致も未確認です。原v116の原因は未確定のまま保持。本体cold compiler v115の失敗は未解決・同条件再試行しません。詳細portable-cuda-cache-claims.md。

次候補の名前付き倍率78／80は参照consumerを確認し、GPU禁止のdamage projection6件が成功しました。GPU受付は未実装で、enemy named-state observerも本対応が必要です。docs/portable-named-magnitude-next.mdを参照してください。

静的packing199/266・base140/203・106分類、通常画面CPU・全キャラGPU認定0・新版CUDA数値一致未確認・最終目標未完了を維持します。以下は履歴です。
<!-- /persona-current -->

<!-- base-copy-current -->
## 基礎ATK／HPコピーと集約481

通常CLIはregression481（native379／拒否102）、goldenはportable-world-base-copy-regression-short-expected.jsonへ明示seal済みです。stat85／86、MODE tagged union、carrier別basis／gift／source／generationを共通Slangへ接続しました。自己／味方、stack初期化、named子イベント、親削除→slot再利用、refresh、負値、失効のHP cap、source戦闘不能後の再選択を47入力で確認。ギルティ／シン／クエンシーの全定義実編成を各3秒／30秒で追加し、Metal481が全件一致しました。

旧428と新47は保存baselineと全input／raw／native同一。初期の受付・HP同期・policy受付の3失敗は元package／rawと別JSONへ保持。CPU695・Windows専用1skip・失敗0、その後のseal改善はCPU3＋CLI26成功と実481のGPU禁止sealで確認しています。sealは元packageの独立監査内の比較を1回だけ再利用し、同じnative全体の二度目の実行を省きます。

静的packing196/266、base137/203、108分類。通常画面CPU、全キャラ認定0、新版CUDA数値一致未確認、最終目標未完了。この機能でWindows実行は0です。v115のcold compiler失敗から同条件再試行しません。詳細はdocs/portable-base-copy.md、research/portable-base-copy-retention.jsonと開発checkpointを参照してください。以下は履歴です。

<!-- lazy-bank-current -->
Windows v115は終了済み・idleです。固定4312287、CPU21成功後のCUBIN O1は42.99秒／NVRTC30.422秒でMemory allocation failure、compiler改善未証明、artifact0、GPU0／retry0。Job post空、missing7／原因unknown／service未識別で環境保持falseを維持します。同条件を再依頼せず、次の変更仮説を先に固定してください。詳細はresearch/portable-world-v115-compiler-sanitized.json。

未知fieldを構造化し、全266profileのpacking・input hash・分類codeを保持したまま効果fallback44→25／program27→14へ削減しました（CPU14成功）。次の高優先機能は基礎HP／ATKコピーで、既存CPU参照8ケース25観測はGPU禁止で再確認済み、portable接続は未実装です。docs/portable-base-copy-next.mdを参照してください。

## 2026-10-22 private lazy cacheの作業領域とMetal428

現在の通常CLIはregression428（native341／拒否87）、goldenはportable-world-lazy-bank-regression-short-expected.jsonです。5配列24576byteをprojectile入口のprivate Runtimeから出力内scratchへ移し、共通アルゴリズムを保持。Metal428全件一致、旧420と追加8境界のinput／全raw／native同一、全bank語ゼロを確認して明示sealしました。原fixture失敗は保持しています。詳細はdocs/portable-lazy-bank-storage.mdとresearch/portable-lazy-bank-retention.json。

旧event／rosterの2入口ではCUDA／Metal生成byte不変。projectileのRuntime推定163504→138928byteは生成宣言の測定であり、compiler改善・実CUDA ABIではありません。新版CUDA数値一致は未確認です。次は固定packageでCUBIN O1・60秒／2GiB・driver/context/kernel0のcompiler-onlyを必要な1回だけ行います。失敗時に上限拡大・再試行しません。通常画面CPU、全キャラGPU認定0、静的193/266・base134/203、最終目標未完了です。

以下は過去の接続時の記録です。

<!-- skill-flat-current -->
## 2026-10-21 名前付き周期秒数補正と制御smokeの効率化

通常CLIはregression420（native334／拒否86）、goldenはportable-world-skill-flat-regression-short-expected.jsonです。effect_interval／skill_cooldownを共通時計へ接続し、個別57入力と実에이다3秒／30秒を追加。Metal420全一致、旧361と初回415の成功414のinput／全raw／native維持を確認して明示sealしました。初回1拒否はC34の対象別受付漏れで、原失敗を保持し、既存HP条件評価器へ接続。CPU684検査・1skip・失敗0です。

受付マクロのrowを明示引数にし、Windows子の専用TEMPを自動設定。run --smokeは制御CPU29件とfresh Jobだけでnative全編成を省きます。Windowsではこの制御確認だけを短く行い、失敗した本体コンパイルを再実行しません。静的packing193/266、base134/203、分類110。通常UI CPU・全キャラ実戦認定0・新版CUDA数値未確認・最終目標未完了です。詳細portable-skill-interval-flat.md、portable-skill-flat-development-checkpoint.json。GitHub共有はゴール中利用者許可済みです。

Windows v114は固定ee0756fで制御CPU29件とfresh Jobのsmoke成功。native_oracles0、全体11.219357秒、pre子1／post空、after2.433606秒、missing0／残留0、Slang／NVRTC／driver／GPU0、retry0。親TEMP保持・子temporary設定を確認。service未識別なので環境保持認定はせず、CUDA数値一致も未確認のままです。詳細portable-world-v114-controller-smoke-sanitized.json。
<!-- /skill-flat-current -->

<!-- skill-interval-current -->
## 2026-10-21 周期割合補正・分類の観測・NVRTC読込み省略

現在の通常CLIはregression361（native292／拒否69）、goldenはportable-world-skill-interval-regression-short-expected.jsonです。skill_cooldown_pctを共通時計へ接続し、28native＋4拒否と実イサベル3秒／30秒を追加。Metal361全一致、旧327のinput／全raw／native維持を確認し明示sealしました。静的packing192/266、base133/203、分類112。通常画面CPU・全キャラ実戦認定0・最終目標未完了です。

分類へstructured reason／文言fallback件数を追加し、既知の境界・audience・scalingを明示分類。CUDA cacheはexact identityを維持し、hit／必須miss／破損でNVRTC DLLを読まないCPU経路へ改善しました。Windows実測の高速化は未確認です。

依頼済みv112 compiler-onlyはallocation failure（NVRTC30.344秒、Job2GiB／60秒、kernel0／retry0）。保存結果だけを回収し再送0。noinlineの改善は未立証、環境保持もservice未識別でfalseを維持、新版CUDA数値一致は未確認です。次は保存結果からコンパイル仮説を絞る作業とflat周期変更等へ進みます。詳細portable-skill-interval.md、portable-skill-interval-development-checkpoint.json、portable-world-v112-compiler-sanitized.json。GitHub共有はゴール中利用者許可済みです。

Windows v113は3ソースのSHA一致後、fake NVRTCのCPU10検査成功。専用TEMPを指定しない初回の権限失敗ログも保持。実cache hitは元v105 generated.cu不在で未確認、再生成／DLL／NVRTC／GPU0です。今後CPUテストも専用TEMP/TMPを指定します。
<!-- /skill-interval-current -->

<!-- readiness-cli-development -->
## 2026-10-21 レビュー反映：未対応分類・開発CLI・失HP防御

`nikke_gpu.py inventory`で全266プロファイルの定義別拒否を分類し、全体packingも継続します。効果ごとに最初の失敗までの診断であり、未観測要件や対応完了予測ではありません。静的packingは163→167、base116→117。次は生成JSONのprioritiesを使い、未対応のstun、burst_reentry(all_allies)、heal_overcharge_store等を検討します。

共通CLIにMetal限定のdevelopment package、case選択、cases一覧、GPU禁止sealを追加。入力/native/source/全payloadを固定し、出力の自動期待値化をしません。`readiness`が新しい正式suiteで、共通75(native60＋拒否15)をM5で確認し、旧63入力/output/native指紋は完全保持。実Peony通常＋favorite1/2/3の4プロファイル×3/30秒の8戦闘も、全効果・被弾・物理履歴まで元CPUと一致しました。

共通Slangへlost_hp_pct防御を接続。直接HP/防御helperと通常buff照会のruntime predicate規約を分け、型付き敵対象の挑発を既存receiver集合へ接続。実編成では敵パターン有無から遮蔽物HP同期を選びます。保護されたCPU/compiler/referenceは変更していません。途中の拒否・差分・診断captureは保持しています。全キャラ/変種/容量/長時間の戦闘認証ではなく、public world=false、通常UI=CPU、full_goal_complete=falseを維持します。

Windows v105は共通75/native60とCPU検査・smokeが成功しましたが、NVRTC44.609秒後のPTX module load中に180秒で停止、kernel launch0、retry0です。missing0、後続残留0、元HEAD/status保持も、失敗したcontainment/サービス識別未確定を成功に変えません。個人情報を除いた集計はportable-world-v105-cuda-sanitized.json、詳細原本はWindowsローカルです。

修正版はSM86 CUBIN直接生成と形式別の原byte cacheへ変更。DLL/header/flags/sourceをkeyにし、破損拒否・途中失敗時artifact回収・GPU/NVRTC0のcache-checkを共通化しました。Slangのline directiveを生成時に無効化し、2展開先のCUDA/MSL全byte一致をCPUで確認。改行配置が変わるためnormalizerは維持し、Metal75を再実証・v3 goldenへseal、旧75全出力指紋を保持しました。CUBINのWindows実機確認はこれからで、180秒上限の修正版1回だけを使います。API能力はNVRTC11.3/GetCUBIN有りをCPUだけで確認済みです。

詳細：docs/gpu-development-cli.md、research/portable-readiness-development-validation.json。全ゴールと未対応項目は継続中です。
<!-- /readiness-cli-development -->

<!-- shared-gpu-cli -->
## 2026-10-21 共通検証CLI・Windowsパッケージ・開発スキル

今後の短時間検証はscripts/nikke_gpu.pyとdocs/gpu-development-cli.mdを使います。既存のnative比較、共通CPU/GPU監査、厳密normalizer、phase観測、WindowsJobとprocess observerを再利用。package→unpack→CPU preflight→限定テスト→bounded run→status/export/import→GPU禁止auditを共通化しました。固定SHAパッケージ、排他的な実行claim、失敗原記録、Job子のbase Python起動、finally内で終了直後にafter観測を保存します。計算/containment/環境保持は別判定です。

Mac関連44検査、隔離パッケージの63入力/native52と限定16、保存済みMetal63の全出力/native/生成一致、従来v104監査、結果ZIPの原byte回収が成功。Windows固定3c44b97はCPU32＋限定16、CPU-only Job smoke1回が成功し、子45800/親17312、pre[45800]/post[]、after約2.073秒、missing0、GPU/build0、元HEAD/status保持を確認。サービス識別はunverifiedであり、保持成功は主張しません。初回cadd96bは共有ブランチの監査器更新漏れでJob前に停止し、失敗記録を保持して修正。新GPU dispatchは0です。

スキルnikke-shared-gpu-developmentを~/.codex/skillsへインストールし、repoのskills/にも原本を保存しました。CLI listでgolden_source_readyを確認してください。現行reloadの旧goldenはsource hash差分により拒否します。期待値の自動書換えは行いません。全キャラ対応の状況・未解決差分は以下の実装記録を引き継ぎ、今回のツール整備を新しい戦闘認証に数えません。詳細research/portable-gpu-cli-validation.json。
<!-- /shared-gpu-cli -->

<!-- world-projectile-v104 -->
## 2026-10-21 散弾数・貫通/爆発範囲と実編成の資源条件を共通実行器へ接続

private ABI0x5045568d/mode24でpellet_count/pellet_count_fixed/pierce_range/explosion_range、frame開始時has_parts、元CPUの部隊弾薬通知indexを共通Slang本体へ接続しました。binary64の順序付き合計とties-to-even、最低1/上限4096、係数と総口数の区別、100−1e−9の到達閾値を検証しました。gauge条件/消費と名前付き解除は既存の共通演算子を利用し、self/enemy解除の未使用recipient予約語だけをprivate packerで修正。canonical engine/compiler/referenceは変更していません。

Metalは共通63（native52＋拒否11）と新規11実プロファイル×3/30秒＝22戦闘で、全効果・状態・物理射撃の時刻/ペレット/総口数/範囲/damageが元CPUと完全一致。最終63は保存62の不変61ブロックと修正後delta2の集約で、集約GPU0、対応表・元raw・厳密生成一致を監査しています。通常生成コードは1421ea2と一致し、診断専用入口だけを分離。計8実GPU呼出し（診断1を含む）、同一source/input retry0、失敗原報告を保持。CPU549、旧21入口CUDA/MSL厳密一致、旧65入力bytes保持、5戦闘35資源最終値のnative直接照合が成功しました。

全266プロファイルの静的入力変換は152→163、base108→116、未対応103です。入力変換はGPU admission/全キャラ戦闘認証ではありません。全203＋お気に入り、未接続buff/selector・操作・復活・source攻撃/interrupt・組合せ/長時間/容量と効率化が残ります。通常画面CPU、public world false、full_character_verified=0、full_goal_complete=false、legacy Metal14c8e2e OPENを維持。詳細はportable-world-projectiles.mdとportable-world-projectile-validation.json。

Windows v104は固定def167197c840d63457ce139f5f6131ce78dc491（codex/cuda-world-v104-source、26ファイル390810bytes）で共通63入力だけをBelowNormal/JobObject/start gate/180秒＋cleanup5秒で1回実行し、127.617560秒で成功しました。事前CPU27検査、native52、全input/output/generated指紋、API50段階、PID107896のpre所属1/post空・残留0/retry0を保存3JSON404357bytesのSHA一致と独立監査で確認しました。実22・旧65/1063・通常4682の再実行は0です。

実行中のモデル容量エラー後も既存OSコマンドは終了0で完了しました。結果だけを取得する後続turnはGPU/build0です。ただし終了後snapshotはJob終了から401.9489005秒遅れ、GPU直前から約529.973秒の観測窓で既存28件の欠落を確認しています。欠落は検証Job外の既存プロセスですが、GPU実行中の終了もGPUとの因果も証明できません。原因unknown、サービス識別unverified、calculation_verified=true、preservation_verified=false、総合passed=falseを保持します。別のCPUのみ約37秒の対照観測では、自身のvenv観測launcher1件だけが欠落しMCP欠落0でした。過去の7/14件の原因も解消扱いにしません。次回の短いWindows検証では、外部bounded wrapperのfinally内でwait直後に完全なafter snapshotを採取し、モデルの次turnを待たない方式が必要です。今回の観測改善目的のGPU再実行は行いません。詳細はportable-world-v104-cuda-validation.json、portable-world-v104-collection-finding.json、seal-world-v104-cuda.py。

GitHub共有は現在のゴール達成まで利用者許可済みです。
<!-- /world-projectile-v104 -->

<!-- world-real-roster-v103 -->
## 2026-10-21 実編成の全効果を共通world入力へ接続、Metal10実証

計算source76dc4de・private ABI0x5045568c/mode23で、実準備結果を最新の共通world実行器へ接続しました。app/portable_world_roster_input.pyが各編成70〜91の全効果、成長・装備・スキルレベル、武器・カメラ・敵パターン・操作方針を既存sidecarへ渡します。研究用の効果/武器/基礎値差替えや効果フィルタはありません。静的CharState以外のCPU計算済み射撃時刻・数量・対象・生死は入力しません。通常の回復・HP減少・遮蔽物回復・待機短縮と既存条件を共通演算子へ接続し、canonical compiler/referenceは変更していません。

Metal10＝実5人編成6＋拒否4が成功。3/30/180秒と実成長差分を含み、全員damage/HP/maxHP/def/遮蔽物/弾薬/射撃数/各待機/phase/gauge/cooldown/burst履歴が元CPUと完全一致しました。M5 command completed、GPU17.433928秒、library1.053856秒、pipeline0.004912秒、input4176004/readback31457280bytesを判定前に保存。CPU531＋監査故障注入2＝最終533検査、旧20入口CUDA/MSL厳密生成一致、保存raw・Git固定source・native6・以前の6全出力word保持のGPU禁止監査に成功。詳細portable-world-real-roster.md、portable-world-roster-validation.json、seal-world-roster-metal.py。

5aea8ccの初回6入力は1件だけ一致、5件はteam1024/fraction2048の診断履歴上限でstatus64停止。903fc97は全6成功。76dc4deは旧入口の生成物まで保持する共通macroへ整理し、不正4件を追加しました。実編成専用入口は履歴上限後も累積/counter/dispatchを継続し、team head+5/fraction head+3に省略数を記録します。180秒でteam7965/fraction15930件を省略し、全通知履歴は主張しません。旧入口の容量超過拒否は保持。計3固定source・GPU3回、同一source/input retry0。Swift sandbox初回停止はGPU実行前で、失敗記録も保持。正規化規則は拡張していません。

実203＋お気に入り込み266プロファイルを実5人編成の全入力としてCPU battle/tick/GPU build/execute禁止で検査しました。入力変換成功はbase108/全152、未対応114も理由を保持。own定義事前検査148とは別指標で、GPU admissionや全キャラ戦闘認証ではありません。通常画面CPU・public world false・全キャラ戦闘認証0・legacy Metal14c8e2e OPEN・全ゴール未完了。未接続buff/selector、source攻撃/interrupt、操作/復活、全変種・組合せ・容量/長時間、最後の効率化が残ります。

Windows v103は固定767f4f4274b5850da44cc48687572580f030d07a、codex/cuda-world-v103-source（12ファイル238622bytes）で計算検証に成功しました。CPU17・10入力/native6のGPU禁止照合、実base Python再照合とCPU Job smoke0.110550秒の後、BelowNormal/JobObject/start gate/180秒＋cleanup5でCUDA1回・176.942747秒。保存3JSON194699bytesをSHA一致で取得し、全input/output/native/generated指紋、API50段階PID22056/親39616、作成時刻、pre所属[22056]/post空、残留0/retry0、元HEAD/status保持を共通監査で確認しました。旧65/1063以下/通常4682再実行0。既存14プロセスの欠落とサービス識別未確定は残り、原因unknown、検証Job所属外・本番子より前の作成を確認。calculation_verified=true、preservation_verified=false、総合passed=falseを維持し、v102の既存7件も解消扱いにしません。GPU再実行は不要、turn01a15d03-a9b4-7ba1-92f2-1db1d530ba9f completed/idle、cursor223。詳細portable-world-v103-cuda-validation.jsonとseal-world-v103-cuda.py。上限まで約3秒しか余裕がなかったため、次回Windowsは変更対象の最小入力に限定します。GitHub共有は利用者からゴール達成まで許可済みです。
<!-- /world-real-roster-v103 -->

<!-- world-reload-v102 -->
## 2026-10-21 固定再装填時間と強制再装填を共通実行器へ接続、Metal65実証

計算source76344c05940db2c8059af149482bdf6802f5ddcf・private ABI0x5045568b/mode22で、reload_time_fixedとforce_reloadを共通carrier/recipient/weapon loopへ接続しました。固定値の最大値、値なしmarkerと0秒の区別、レベル別values、開始後の期限保持、nativeの直接active query、stack/alias、物理武器コールバックの文脈を保持します。強制再装填はreload_until>0なら何もせず、そうでなければ弾薬0と充填・保持の取消を共通beginReloadで行います。full_reloadの同期子処理、クリップ継続、再装填中のpost_delay、通常ammo percent/flatも同じ本体です。

Metal65＝full native46＋拒否19が成功しました。M5 command completed、GPU0.031416秒、library1.001秒、pipeline25.511秒。input27144004/readback204472320bytesを判定前に保存し、全battle/state/notice/skill queueとforce/start/finish traceを完全照合。CPU523（GPU source時点512＋Windows観測11）、旧19入口CUDA/MSL厳密生成一致、旧58/native31の入力・ネイティブ指紋保持、保存raw/Git/nativeの独立監査が成功しました。同じsource/inputのGPU再試行0です。実データのMilk Blooming Bunny/Jillの再装填2定義ずつも含みますが、全キャラ戦闘認証の数ではありません。

27216abはhostの出力上限検査でGPU前に停止、入力と失敗を保存しました。dff1086の初回GPU62は41/43 nativeと拒否19が一致し、再装填中のphase保持と通常ammoの許可不足2件を保存。76344c0で修正し、通常ammo3件を追加して全65成功。初回の変更対象以外41ケースと拒否19は最終全出力wordと一致しました。3計算コミット・GPU実行2回です。

入力104400word（旧104136＋WRL1 header8＋定義256flags）、出力786432wordです。655360にheader16と5人の最終reload_until、655376から4096×16wordの履歴、終端720912です。共有transportとMetal入口は新サイズだけを明示追加し、隙間サイズは拒否します。固定値は64要素damage vectorの外のidentity90で扱います。明示max_trigger:-1はネイティブでは発動しないため、共通packerでbudget0へ正規化し、キー欠落の無制限sentinelと区別しました。canonical compiler/CPU referenceは変更していません。詳細はportable-world-reload.md、portable-world-reload-validation.json、seal-world-reload-metal.pyを参照。

Windows v102は固定51aa3399961c408889a599e1a265057469ff1bb6（25ファイル432154bytes）、codex/cuda-world-v102-sourceで計算検証に成功しました。CPU137・GPU禁止65入力/native46・base Pythonでの再照合後、CPUだけの実Job smokeは0.106619秒/GPU0。本番はBelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・121.898908秒、全65入力/output/native/generated指紋とAPI50段階が一致しました。新しい観測器のSHA、PID77560/親2448、作成時刻、pre所属[77560]、post所属空、全50段階PID77560、残留0/retry0、元HEAD/status保持を独立監査済みです。保存3JSON180500bytesはSHA一致で取得しました。ただし既存MCP等7件の欠落とNIKKEサービス識別未確定は残り、原preservation flagと総合passedはfalse、calculation_verifiedはtrueです。欠落7件は本番子より前に作成され、検証Jobの所属に含まれませんでした。終了原因は不明のままです。通常4682・旧1063以下の再実行0。summaryの旧958件カウンタ名をold965と転記したミスも監査が検出し、元JSONを変えず、明示receiptのold958=0と固定65入力・単一dispatchから検証しました。今後のreporterは修正済み、故障注入2件を加えた最終CPU525が成功しています。portable-world-v102-cuda-validation.json、seal-world-v102-cuda.py、portable-world-v102-summary-counter-finding.jsonを参照。

実203＋21お気に入り段階1/2/3＝266プロファイルのPython own定義事前検査はbase105→107、全145→148（Milk/JillとExia favorite3）です。CPU battle/GPU呼出し0で、GPU admissionや全効果の戦闘認証の数ではありません。通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。tap/anchor/cover/reload/aim/burst/focus操作、他buff/selector、明示parts/interrupt/source攻撃、復活、全組合せ/容量/長時間/全変種認証、その後の効率化が残っています。GitHub共有はゴール達成まで利用者許可済みです。
<!-- /world-reload-v102 -->

<!-- world-charge-control-v101 -->
## 2026-10-21 手動チャージ保持を共通実行器へ接続、Metal58実証

計算source2a585cfab7b15bedc6a591433ee4bf3edbc49df6・private ABI0x5045568a/mode21で、charge_hold:N/count:M、手動hold、hold_until_close、hold_judge、明示holdシーケンスを共通実行器へ接続しました。完了を実観測時刻でラッチし、生の0.1/0.10を別通知として閾値順に処理、条件より前に一度消費します。カメラの優先度/新規要求/部隊順、先取り解除、同一burstアンカーの再入1回、本人full burstと終了後の判定、動的chain窓、戦闘不能、武器session復帰順を扱います。CUDA/Metal別の計算実装、CPU算出済み射撃・充填時刻・通知・所有者入力はありません。

Metal58＝native31実戦＋拒否27が成功しました。Apple M5 command completed、GPU0.089250秒、library1.028秒、pipeline11.503秒。input24159556/readback152043520bytesを判定前に保存し、全battle・状態・通知・小数・skill queueとカメラtraceを完全照合しました。CPU全488検査、旧18入口CUDA/MSL厳密生成一致、旧47入力/native29の指紋保持、保存raw/Git/nativeの独立監査も成功。同一source/inputのGPU再試行は0です。

a9b7c2aの初回Metalは28/31一致、弾薬kind13/14の許可不足2件と武器終了後の保持解除1件を保存しました。既存の共通弾薬演算子をcontrol通知の定義に限って許可。f077cbeは30/31一致でしたが、保持解除がカメラ判定より1フレーム早い差を保存しました。2a585cfで論理失効→カメラ判定→物理武器復帰のnative順へ接続し、全31成功。初回の変更対象以外28ケース、2回目の変更対象以外30ケースは最終全出力wordと一致しました。3固定ソース・GPU実行3回です。

CPU生成器が前段階のprivate teamEvent宣言を共通fieldとして解釈できなかった3件も発見・保存しました。正確な条件付き宣言だけを明示して扱い、共通initializerのbytesを変えず、未知のdirectiveは拒否します。専用入口のteamEvent初期化は従来どおりです。最終488件は成功しています。

入力は104136word（従来98000＋WCH1の6136）、出力655360wordです。653160からowner5×32、653320からheader16、653336から閾値1280bit、653376からowner5×16アンカー、653536から220×8trace、終端655296です。未使用/予約語、raw event名と秒数、有限値、DOWN_Charge制約などをGPUで検査します。trace/履歴容量超過は失敗扱いです。詳細はportable-world-charge-control.md、portable-world-charge-control-validation.json、seal-world-charge-control-metal.pyを参照。

Windows v101は固定784762d0f9cb809958107c040dcac7c219889c4c（22ファイル341461bytes）、codex/cuda-world-v101-sourceで計算検証に成功しました。CPU106・GPU禁止58入力/native31・全source SHA照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・118.622770秒。保存3JSON121370bytesのinput/output/native/generated指紋とAPI50段階は一致、元HEAD/status保持・residual0/retry0、通常4682・旧1005以下の再実行0です。ただし既存Node/Python7件（Codex cua_node3、Blender MCP2、generic uv Python2）のPID保持を確認できず、元receiptのexisting_gpu_service_preservedはfalseです。追加の読取専用調査12543bytesも取得しましたが、終了原因と元NIKKEサービスの同一性は不明です。検証JobObjectは新規子プロセスだけを割り当てる実装で、7件への直接割り当て記録はありません。GPU再実行・サービス操作は行っていません。strict監査は拒否したまま、全計算/API/source検査を最後まで行う診断ではcalculation_verified=true、preservation_verified=false、総合passed=falseです。4件の故障注入を含む最終CPU492が成功。次のWindows実行前にはサービスの明示識別と子PID/PPID/creation/Job所属のbaseline保存を改善します。portable-world-v101-cuda-validation.jsonとportable-world-v101-preservation-finding.jsonを参照。

実203＋21お気に入り段階1/2/3＝266プロファイルのPython own定義事前検査はbase102→105、全142→145（라푼젤 : 퓨어 그레이스、길티 : 마이티 바니、신 : 스위프트 바니）です。CPU battle/GPU呼出し0で、GPU admissionや全キャラ戦闘認証の数ではありません。通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。tap/anchor/cover/reload/aim/burst/focus操作、他buff/selector、明示parts/interrupt/source攻撃、復活、全組合せ/容量/長時間/全変種認証と、その後の効率化が残っています。GitHub共有はゴール達成まで利用者許可済みです。
<!-- /world-charge-control-v101 -->

<!-- world-team-v100 -->
## 2026-10-21 部隊part/body命中を共通実行器へ接続、Metal47実証

計算source725f020・private ABI0x50455689/mode19で、part_hit_count/body_hit_countを既存コンパイラの5人分bindingへ接続しました。条件は元のeffect owner、発動casterとtarget:self・caster-based数量は実attackerです。部隊のglobal count、max_trigger、確率accumulatorは攻撃者をまたいで共有します。scalar・carrier・recipient・health・gauge・damage子処理は共通dispatchを使用し、CUDA/Metalに別実装やCPU算出済みcredit入力はありません。通常のpellet通知とchargeの弾数buff期限前というnative順、1−coreのbinary64蓄積、source owner downを保持します。

Metal47＝native29実戦＋拒否18が成功しました。Apple M5 command completed、GPU0.036294秒、library 1.089秒、pipeline 8.318秒。input18424004/readback123207680bytesを保存し、全数量・状態・通知時刻・小数・実accumulator・skill queueを照合しました。共有budget/prob、3pellet×2muzzle、core0/小数/1、HP条件と戦闘不能、caster-based量、heal/gauge、child damage、normal/skill charge、add消滅とtarget state、重複timingのnative通知indexを含みます。CPU460検査・旧17入口CUDA/MSL生成厳密一致、保存raw/Git/nativeの独立監査が成功。同じsource/inputのGPU再試行0です。

29be064/f1465b2/373ad77はpipeline生成300秒でGPU実行前に停止し、各input・失敗を保存しました。専用入口でcounter marker/mode19をGPU上で先に検査して旧モード分岐を定数化し、pipeline生成を約8秒へ削減しました。旧入口の生成物の余白差も原型を保持して解消し、正規化は拡張していません。277af2bでの初回GPU47は46一致・gauge1拒否を保存。既存共通kind24がteam初期検査に無かったため追加し、725f020で全47成功。修正対象以外46入力の全出力wordも初回と一致しました。stage計5ソース、GPU実行2回です。

入力98000word（従来fraction97480＋WTH1 header8＋256binding×2）、出力655360wordです。644936から5×4wordの部隊小数、644956に12word head、644968に1024×8word traceを置きます。bindingのsource owner/shared budget/実attacker順と未使用語をGPU検査します。mixed/periodic/weapon-change team listenerは既存コンパイラで拒否します。詳細はportable-world-team-hits.md、portable-world-team-validation.json、seal-world-team-metal.pyを参照。

Windows v100は固定a61136f1db638b7cd16f5174b08fa13dffbe0bb1（23ファイル387656bytes）、codex/cuda-world-v100-sourceで成功しました。CPU78・GPU禁止47入力/native29・全source SHA照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・111.208852秒。保存3JSON計108231bytesのinput/output/native/generated全fingerprint・API50段階・元HEAD/status/service保持・residual0/retry0・旧958以下/通常4682再実行0を共通監査済みです。portable-world-v100-cuda-validation.json、seal-world-v100-cuda.pyを参照。

実203＋21お気に入り段階1/2/3＝266プロファイルのown定義Python事前検査はbase100→102、全140→142（D : 킬러 와이프、루마니）です。CPU battle/GPU build/execute禁止・呼出し0で、GPU kind admissionや全キャラ戦闘認証の数ではありません。通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。charge_holdの手動control・充填latch・一度判定、他buff/selector、明示parts/interrupt/source攻撃、動的操作/復活、全組合せ/容量/長時間/全変種認証を続けます。GitHub共有はゴール達成まで利用者許可済みです。
<!-- /world-team-v100 -->

## 2026-10-21 クリティカル・コア小数通知をMetal35・CUDA35で実証

計算source7cb937878bd642ccf448cd5f4c7b33feafe993a5・private ABI88/mode17で、crit_hit/core_hitと各countを共通実行器へ接続しました。物理damageValueから一発分の確率を捕捉し、既存binary64でowner別の小数を蓄積、1を超えたら共通dispatchを呼びます。確率0/1では新しいaccumulatorを作らず、既存の残り値を保持します。CUDA/Metal別実装やCPU算出済みcredit入力はありません。

通常射撃はpellet_hit→critical→coreを弾片ごと、チャージはon_attack/full_charge/hit_count等→弾数buff消費→全critical→全core→last_bulletというnative順を保持します。同じ散弾中のcallbackで確率を取り直しません。normal専用criticalはskill modeへ入れず、pinned nativeがaddへの最終routingでもcore確率を維持する契約も観測のまま保持します（明示parts/interrupt照準とは別です）。

Metal35＝native24実戦＋拒否11が成功しました。M5 command completed、GPU0.039672秒、input13647204bytes/readback91750400bytesを保存。0/1clamp、15%の7発目、unit率への変更時の残り値、3pellet×2muzzle、callback/charge/skill mode/normal限定補正/弾数期限/core出現変化/add経路を完全nativeの数量・状態・通知時刻・小数値・実accumulator keyで照合しました。CPU442検査、旧16入口CUDA/MSL生成物厳密一致、保存raw/Git source/nativeのGPU禁止監査も成功。旧923以下・通常4682のGPU再実行はありません。

初回ee14e40（ABI87/input97464）の29入力を保持しています。全24の数量・最終小数値は一致しましたが、charge6件の通知が1frame早い差を発見しました。literal base charge入力のinterval.4−charge.2が実native SRのpost_fire_delay.215を表しておらず、さらに一般にcharge+delayからdelayを復元してもbinary64値が保存されないため、独立したstatic時計入力へ接続しました。初回raw・initial-metal・findingを保存し、同一source/input retry0です。異なる固定source2種でMetal計2回。

新入口だけ入力を97480wordへ拡張し、97464から16word（WFC1/version1/5owner/予約0＋各post-fire delayのbinary64＋予約0）を追加しました。native静的CharStateから読み出すnormalize_static_clockと厳密packerを共通化し、CPU battleは禁止して検査。weapon modeは既存descriptorのraw post_fire_delayを直接読みます。NaN/負値/nonchargeへの非0/予約語をGPUで拒否。旧入口のinput幅と生成結果は保持します。出力655360wordは同じで、628504に5×8wordの小数/shot snapshot、628544に8word head、628552に2048×8wordの観測を置き、過去のbankと重なりません。

Windows v99は固定158e8b7a81e0af470af7cfe06e5d8809b48690ba（19ファイル293289bytes）、codex/cuda-world-v99-sourceで成功しました。CPU60検査・GPU禁止35入力/native24・source SHA82・input97480照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・116.380413秒・exit0。保存3JSON計71749bytesを取得し、全input/output/native/generated fingerprint・API50phase・元HEAD/status/service保持・residual0・retry0・旧923以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v99-cuda-validation.json、seal-world-v99-cuda.pyを参照。turn01a15c58-b163-7190-8fd9-bed75504179aはcompleted、cursor187、idleで、再依頼は不要です。

実203＋21お気に入り段階1/2/3＝266プロファイルの静的監査では、own定義のPython事前検査通過がbase97→100、全137→140になりました（K、루드밀라 : 윈터 오너、마스트）。CPU battle/GPU build/executeは禁止・呼出し0。これはGPU kind admission・real roster/world配線・容量・全キャラ戦闘認証を示す数字ではありません。

次のpart/body通知はnative6実戦を固定しました。条件はeffect owner、発動casterとtarget:selfは実attackerであり、team counterはattackers間で共有されます。owner4だけ被弾させる条件対照と、3pellet/2muzzleの全体N=3対照も確認。portable-world-team-hit-native-contract.json、characterize-world-team-hit-ownership.pyを参照。このGPU bridgeはまだ拒否します。charge_holdも手動control・充填完了のlatch・閾値ごとの一度判定・キャンセル/カメラの接続が必要です。

通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。部隊命中/保持・他buff/selector・source攻撃/interrupt・skill追加part到達・動的操作/復活・全効果組合せ・容量/長時間/全変種認証、nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合も残ります。効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 初期敵出現通知をMetal27・CUDA27で実証

計算sourcecb4400977032fdac69621c9f1fa5a6dff34e8c31・private ABI86/mode15で、event:enemy_spawn（元のevent5）をworld定義の受付と共通startupへ接続しました。全員のbattle_start→全員の初期enemy_spawn→初期magazineの順で一度だけ実行し、召喚敵1体ごとの既存通知は同じdispatchを使います。CUDA/Metalに別のイベント実行器・数量計算・効果定義は追加していません。new入口のevent5定義は旧mode13では拒否します。

Metal27＝native22実戦＋拒否5が初回成功しました。Apple M5 command completed、GPU0.063310秒、input10526116bytes/readback70778880bytesを保存。初期通知5回、即時/遅延2体、127体の計640通知とowner順序・binary64時刻、再出現、全5owner、別ownerのbattle_start状態、初期装弾、gauge、敵fieldのscope/stack、trigger budget、vanish、同フレームの敵攻撃、128対象への通常skill/DoTを完全nativeで照合しました。既存timer・queue・counter・Actor着弾順序を保持し、DoT初回は既存のt=0 timer passを使います。

CPU429検査、旧15入口CUDA/MSL生成物厳密一致、保存raw/Git source/nativeのGPU禁止監査に成功しました。出力は既存655360wordのまま、612112に8word head、612120から4096件×4wordの通知観測をGPUが記録します。128Actorの敵攻撃力・periodic packet bankと重ならず、容量超過はstatus64です。旧入口の生成結果を保持し、旧923以下・通常4682を再実行していません。Metal GPU1回・source1種・同一source/input retry0。

CPU初回の「0.2秒以上」という観測assertは、実native累積clockが0x1.9999999999999p-3だったため不正でした。浮動小数点sumのPython版による差も避け、nativeと同じ12回の逐次加算を厳密比較します。丸め/許容誤差は追加せず、初回native20件をportable-world-spawn-native-initial.jsonへ保持しました。旧生成物の空行1行差も空展開フックを既存行に置いて解消し、正規化規則は変更していません。失敗したCPU生成照合はportable-build/world-spawn-initial-generation.json/.logへ保持。

Windows v98は固定a7f4b777845dee039f9d873df7eea272d4debf07（17ファイル280180bytes）、codex/cuda-world-v98-sourceで成功しました。CPU47検査・GPU禁止27入力/native22・source SHA80照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・114.941192秒・exit0。保存3JSON計66029bytesを取得し、全input/output/native/generated fingerprint・API50phase・元HEAD/status/service保持・residual0・retry0・旧923以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v98-cuda-validation.json、seal-world-v98-cuda.pyを参照。turn01a15c43-0306-7782-94cc-7e37a28380aeはcompleted、cursor182、idleで、再依頼は不要です。

実203キャラ＋21お気に入りの段階1/2/3＝266プロファイルを静的再監査しました。own定義のPython事前検査通過はbase95→97、全133→137です。바이퍼（通常＋お気に入り1/2）と아크레인저 블랙の4プロファイルが増え、差分をportable-world-spawn-catalog-delta.jsonへ保存しました。CPU battle/GPU build/execute禁止・実呼出し0。GPU kind admission・容量・real roster/world配線・全キャラ戦闘認証を示す数字ではありません。

通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。次はcharge/part/crit判定、未接続buff/selector（explosion_range、effect_interval、trigger_count_reduce、stun等）、source攻撃/interrupt・skill追加part到達、動的操作/復活、周期gone/expiry/dispelを含む全組合せ、容量/長時間/全変種の認証を進めます。永続条件付き味方HP/防御とhit-only max-HP rankのnative不整合も残ります。効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 敵攻撃力fieldをMetal37・CUDA37で実証

計算source0395cad4130cadf32d560efa0df5551d374f7f10・private ABI85/mode13で、敵へのatk_pct/atk_caster_based_pctを既存のresident・stack・期限・Actor recipient・名前付き状態へ接続しました。CUDA/Metalは同じSlang本体と28実戦・不正9入力を使います。出力幅655360wordは前段階のまま、periodic snapshotの後611856から128Actor×2wordの実GPU queryを保存します。CPU計算済みの敵攻撃力や被害量は入力しません。

nativeのenemy_atk_down_flatは術者の基礎攻撃力×割合をresident順に合計し、ボス攻撃力へ加算して0以上に制限します。この値をtarget選択・5人への着弾より前に一発ごと捕捉し、途中のHP条件変化で残りの対象を再計算しません。敵へのatk_pctはnativeの被ダメージ式では読まれませんが、get_buffsの対象側分岐ではこちらの与ダメージのatk_pctに入るため、既存の順序付きcollectStatsへ接続しました。味方のrank/base-stat helperへは混ぜていません。nativeが召喚敵の発射元IDを復元できずflat補正を適用しない既知の制約も残ります。

修正版Metal37＝native28実戦＋拒否9はすべて一致しました。M5 command completed、GPU0.139797秒、input14424676bytes/readback96993280bytesを保存済み。基礎ATKと味方buffの区別、正負・0clamp、expiry、stack/refresh、複数owner/alias、HP runtime条件と有限条件のlatch、7rank、128対象、遅延spawn/再世代、全battle/field/名前付き状態を照合。CPU418検査、旧14入口のCUDA/MSL厳密一致、保存raw/Git source/nativeのGPU禁止監査にも成功しました。

初回22c8ca3の35入力は不一致を保持しています。既存status観測の有効化だけで保存出力をCPU再監査し22/28が一致、残るatk_pct与ダメージ3件とHP条件受付3件を共通処理へ修正しました。初回raw・initial-metal・observer-replay・findingを保持し、同一source/input GPU retry0です。今回のMetalは異なる固定source2種で計2回。旧入口は14生成物の厳密一致を確認して旧923以下と通常4682のGPU再実行をしていません。

skill/pendingの古いshort goldenはこの変更前のa51ea7dでも現行生成物と異なりました。この2入口は追跡ファイルのcleanな固定a51ea7d worktreeから生成して比較し、今回の変更後も厳密一致を確認しました。normal等の旧11とperiodicも従来基準に一致。正規化規則を追加して差を隠していません。portable-world-enemy-attack-generation-baseline.jsonに両方の値と固定source SHAを保持しています。

Windows v97は固定970aed0d7921de429c3808ec73a7115b0dcd2386、codex/cuda-world-v97-source（16ファイル252144bytes）で成功しました。指定CPU36検査・GPU禁止37入力/native28・source SHA78照合後、BelowNormal/JobObject/start gate/180秒＋cleanup5秒でCUDA1回・112.762323秒・exit0。保存3JSON計66976bytesを取得し、全input/output/native/generated fingerprint・API50phase・元HEAD/status/service保持・residual0・retry0・旧923以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v97-cuda-validation.json、seal-world-v97-cuda.pyを参照。turn01a15c33-bbcf-75e1-b3d9-08c4d7753dceはcompleted、cursor174、idleで、再依頼は不要です。

実203キャラ＋21お気に入り段階1/2/3＝266プロファイルを静的再監査し、own定義のPython事前検査通過がbase85→95、全121→133へ増えました。12の新規プロファイルをportable-world-enemy-attack-catalog-delta.jsonに保存。CPU battle/GPU build/executeは禁止して呼出し0です。これはGPU kind admission・容量・real roster/world配線・戦闘認証の証明ではありません。

通常画面CPU・public world false・全キャラ戦闘認証0・legacy unexplained Metal14c8e2e OPEN・全ゴール未完了です。敵対象の他field/selector、enemy_spawn通知、charge/part/crit、source攻撃/interrupt・skill追加part到達、動的操作/復活、周期gone/expiry/dispelの全組合せ、永続条件付き味方HP/防御とhit-only max-HP rankのnative不整合、容量/長時間/全変種認証を進めます。効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 DoT・一般周期ダメージをMetal923・CUDA45で実証

計算source1f059919037de30f722b121064cd4be819cc87e1・private ABI84/mode11で、DoT/一般周期ダメージを既存timer・stack・reference・binary64数量計算・共通Actor着弾へ接続しました。256定義と2048着弾パケットそれぞれに、128対象の順序/bitset/捕捉birth ordinalを38wordで保存します。既存のchecked monotonic add birth ordinalを使い、後から生まれた同slotの世代へ再結合しません。aliasによる対象unionでも、作成済みパケットは不変です。通常timer更新→queue drain→burst/射撃の順序を保持し、即時DoTを別の早着弾経路にしていません。

Metal923＝native32実戦＋不正13＋旧878が成功しました。全数量/着弾traceに加え、実際のnative timer・carrier・named predicate状態を一致検査しました。128対象、7rank、同名alias、再出現世代、own stack/refresh、参照stack、通常式、一般周期3hit、DOT credit/counter子、致死/生存addからの登録・回復を含みます。CPU408検査、旧11入口CUDA/MSL生成物厳密一致、保存raw/Git source/nativeのGPU禁止監査に成功。legacy UIの全キャラ対応を意味しません。

新入口だけ出力655360wordへ拡張し、不変snapshot領域を追加しました。従来の524288word prefixを旧878入力すべてで完全保持し、追加tailは0です。従来入口の出力幅は変更していません。共通backend/Metal transportは従来の範囲と新655360だけを許可し、未検証524289などはbuild前に拒否します。2GiB未満の互いに重ならない700件＋223件の2バッチで、各input/readback/evidenceを即保存しました。source2種・Metal計4 dispatch（初回2＋修正版2）、同一source/input retry0です。

初回7fffac4の全数量・packet traceと旧878 prefixは一致しました。finish後pool aliveでbefore_finishの捕捉membershipを削った観測差2件と、prepare hookを通らない実native periodic ActiveBuff UIDを数えなかったordinal差1件を、保存readbackのCPU再監査だけで解消し32実戦一致を確認しました。観測項目を無視・丸めてはいません。残るNaN intervalのstatus0は、共通周期判定を正の有限binary64 intervalへ修正し、NaN/Infinity/負値を実GPUで拒否しました。初回raw/observer-replay/findingを保持しています。portable-world-periodic-validation.json、seal-world-periodic-metal.pyを参照。

Windows v96は固定4554b0b61ce98375deee8aedeb262729915e3e0f（21ファイル346136bytes）で新45入力/native32だけを検証しました。CPU65検査・GPU禁止45入力・source SHA76照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、111.904949秒・exit0。保存3JSON計70803bytesだけを取得し、全input/output/native/trace/generated fingerprint、API50phase、元HEAD/status/service保持、残存0、retry0、旧878以下/通常4682再実行0を共通監査器で照合済みです。portable-world-v96-cuda-validation.json、seal-world-v96-cuda.py。turn01a15c1c-6a59-7803-bb5e-a9787bfd22fdはcompleted、cursor167、idle。再実行依頼は不要です。

実データを全203キャラ＋お気に入り21キャラの段階1/2/3、計266プロファイルで静的監査しました。own定義のPython事前検査通過はbase85/203、全プロファイル121/266です。全定義を実owned/growth準備から取得し、除外や架空効果を使っていません。CPU battle/GPU build/executeを禁止して呼出し0を実測しました。これはGPU kind admission・capacity・policy wiring・戦闘認証ではありません。portable-world-catalog-definition-readiness.jsonに全target/field/trigger/conditionと不受理理由を保存しています。

次はこの実キャラ一覧から、敵atk_pct/atk_caster_based_pct等の未接続numeric field・selector、event:enemy_spawn等の通知、charge/part/crit判定、source攻撃/interrupt・追加part到達、revive/controlへ進みます。DoTのmid-frame gone/expiry/dispelを含む全効果組合せとreal roster/world入力接続も引き続き認証が必要です。

通常画面CPU・public world false・全203変種の戦闘認証0、legacy unexplained Metal14c8e2e OPENを維持し、全ゴール未完了です。nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合、容量/長時間/全変種認証も残ります。計算処理の効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 pendingを共通Actor着弾へ接続しMetal878・CUDA37で実証

計算source6bd7ab48095984d76ebdd5b291f56e0c99a5032e・private ABI83/mode9で、B3 pendingを128Actorの共通着弾helperへ接続しました。通常skillとpendingは同じ選択・世代検査・HP/counter/lifestealを使い、既存のソフトウェアbinary64・reference・後続buff除外・全数量を先に捕捉する二段階を保持します。pendingだけ同フレームで着弾し、full_burst_startやcounter子が作った通常skillは次フレームまで通常queueに残ります。明示normal_attack式よりB3 plain bonus pendingが優先するnative契約を共通packerへ反映しました。

Metal878＝native26実戦＋不正11＋旧841（833＋8）全524288word一致が初回成功しました。Apple M5でcommand completed、GPU 0.924025秒、全input/readbackを保存済み。CPU399検査、旧11entryのCUDA/MSL生成物厳密一致、保存raw/Git source/native/着弾trace/実際のpending容器から観測したenqueued・fired・countのGPU禁止監査にも成功。128対象、7rank、reference欠落/0/2、名前付き3hits、buff順序、counterが変える前の一括数量、add死亡、回復を含みます。通常画面の全キャラ認証ではありません。

直接skill入口はActor着弾本体の共通helperへの切り出しで生成コードが変わりました。これを旧12entry厳密一致と誤記しないでください。旧11entryは厳密一致、直接skillを含む旧841は全出力word保持です。生成測定はportable-world-pending-refactor-generation.json、実証と監査はportable-world-pending-validation.jsonとseal-world-pending-metal.pyです。CUDA/Metal別実装やCPU計算済み数量の入力はありません。GPU計1回、同一source/input retry0。

Windows v95は固定ea1eccc0e23d22f7cfede3437fd76dedf6dec0fe（15ファイル297084bytes）で成功しました。CPU48検査・GPU禁止37入力/native26・source SHA74照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、109.304244秒・exit0。保存3JSON計76674bytesだけを取得し、全input/output/native/trace/generated fingerprint・API50phase・元HEAD/status/service保持・残存0・retry0・旧841以下/通常4682再実行0を共通監査器で確認しました。portable-world-v95-cuda-validation.json、seal-world-v95-cuda.py。turn01a15bf5-799c-7bb1-a476-b5948bbaf2f6はcompleted、cursor164、idle。再実行依頼は不要です。

次のDoTはCPU11実戦を固定しました。通常timer tickはBM更新で作成され同フレームのqueue drainへ入り、射撃counterで適用したimmediate DoTは次のtimer更新で初めて生成されます（作成0→次フレーム着弾の通常skillとは数量捕捉時刻も異なる）。後続buffをその最初のtickが読む対照も保存しました。適用時の対象membershipは後から出現したwaveを含まず、tickごとに現在の数値を読み、refresh/own stacks/expiryを保持します。portable-world-dot-skill-native-contract.jsonと初回CPU観測を参照。初回は観測値の生成時刻を通常skillと同一視したassertが不正で、実測を残して修正しました。DoTのGPU受付は未接続のままです。

次は既存periodic timer/stack/数量計算を使い、8bitのperiodic対象maskを128Actorの捕捉membership・世代へ接続する必要があります。liveなlate-routingの直接skillと混同しないでください。timers→通常queue drain→burst/射撃のnative順序を保持し、DoTだから常に即時着弾とする別経路は作りません。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPEN、全ゴール未完了を維持します。DoT/source攻撃/interrupt・skill追加part到達、動的操作/復活、全効果組合せ、容量/長時間/全変種認証、nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合が残ります。計算処理の効率化は必要な検証後。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 auto_damageの数値契約をMetal8・CUDA8で実証

計算sourceef12e0940259d64bb48ed252ef1836b52ef4bfa7で、world入力のauto_damageは明示normal_attack式がある場合だけ通常攻撃計算を使うよう共通packerを修正しました。通常攻撃専用damage/critical補正と全攻撃critical補正、1hit/3hitsをnative8実戦で区別し、Metal8のbattle・着弾traceが完全一致しました。default242、normal専用damage50でも242、明示normal式なら363、全攻撃critical50なら298です。CPU393検査に成功し、従来のnon-world auto契約は保持します。

GPU shader73ファイルと生成CUDA/MSLは不変です。旧833の全保存input/readback SHAを確認し、旧40native中39は全入力word一致＋全native/trace再監査、変更したauto1入力は新8の先頭で実GPU検証しました。不正10入力も同一、旧783は保存済みsealed出力を保持します。同じ入力の再実行を避け、Metalは新8だけ1回、旧833再実行0、retry0。共通計算本体を別実装へ置き換えていません。portable-world-skill-formula-validation.json、seal-world-skill-formulas-metal.py、portable-world-auto-formula-finding.jsonを参照してください。旧v93は固定2498e1e worktreeでもMetal/CUDAをCPUだけで再監査済みです。

Windows v94は固定05a763db1d988ad9c82e5b14fcf4a49aa16430a0（6ファイル89510bytes）で成功しました。CPU42検査・GPU禁止8入力/native8・source SHA73照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、103.169556秒・exit0。保存3JSON計58579bytesだけを取得し、全input/output/native/trace/generated fingerprintとAPI50phase、元HEAD/status/service保持、残存0、retry0、旧833以下/通常4682の再実行0を共通監査器で確認しました。portable-world-v94-cuda-validation.json、seal-world-v94-cuda.py。Windows turn01a15be6-06de-7443-81e8-0c77c918612bはcompleted、cursor159、idle。再実行依頼は不要です。

次のpendingを完全native9実戦で固定しました。B3 bonus_damageは約0.583333秒のfull burst進入フレームで作成・着弾し、通常skillの次フレームqueueとは異なります。後続cast buffは除外し、先行buffは適用し、2pending分の数量は最初のcounter子fieldが変化させる前に一括捕捉します。all3対象、normal専用補正の除外、0係数も確認。B3 plain bonusのpending処理は明示normal_attack式より優先し、その補正を使わないことも固定しました。登録をliteral fixtureへ差し替える観測器ではchar_effects検索にも同じliteral一覧が必要でした。opt-in observe_authored_effect_lookupを追加し、元catalogによる誤った後続buff包含748と、正しい354のCPU対照を保存しました。portable-world-pending-skill-native-contract.jsonと初回native報告を参照してください。pendingはGPU未接続で、現private受付でも拒否します。

次は、既存pendingの「全数量を計算してから着弾」の二段階とreference/後続buff除外を保持し、direct queueの128Actor着弾本体を共通helperにしてpendingから同フレームで呼ぶ必要があります。通常queue全体を途中でdrainするとB3中の通常skillまで早く着弾するため不可です。pendingが明示normal式より先に処理されるnative優先順位も保持してください。新しいprivate入口を固定して、旧直接skillの全出力・拒否契約を保持しながら検証します。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPEN、全ゴール未完了を維持します。pending/DoT/source攻撃/interrupt・skill追加part到達、動的操作/復活、全効果組合せ、容量/長時間/全変種認証が残ります。nativeの永続条件付き味方HP/防御、hit-only max-HP rankの不整合も未解消。必要な検証後に計算処理を効率化します。GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 direct skillの遅延着弾をMetal833で実証

計算source761e362・private ABI82/mode7で、counter子を含む直接skillを既存の共通damage計算・LandingReceiptキュー・128Actor selector・HP/counter/lifestealへ接続しました。作成時にbodyの明示query scopeで数量・hit数を捕捉し、次フレームまたは終了時にlive targetを選びます。捕捉したcompletion Actorへ敵fieldを付ける処理とは別のnative契約です。named hit_count wire49はcompletion targetを継承します。カウンターなし編成にも合成counterを挿入しません。

Metal833＝完全native40実戦＋不正10＋旧783全524288word一致、CPU390検査、旧11entry CUDA/MSL生成物厳密一致、保存input/readback/Git source/native/着弾traceのGPU禁止監査が成功しました。12直接damage系統、7rank selector、128対象分配と丸めで0damageでもcredit1、作成後に出現したadd、同じdrain中に追加される子damage、作成後buffで変わらないmulti-hit数量を確認しました。ソフトウェアbinary64、整数丸め、選択、状態、イベント、counterをCUDA/Metalで共用し、実装・fixture・比較器を分岐させていません。

nativeの空enemy field資源に依存したbody query scopeを修正しました。中立field0の有無で変わった242/511は両方511、旧11中10辞書と過去381完全native辞書を保持しています。証拠はportable-world-query-scope-regression.jsonとportable-world-counter-damage-queue-native-contract.jsonです。

初回のcore_damage分類差、通常攻撃式の許可bit256漏れ、入力packerの式指定漏れをそれぞれ保存しました。canonical CPUのcore_damageはWEAPON、normal_attack式はnormal_skill/SKILLです。単なるskill起源で分類しません。最終ケースはnormal_atk_dmg_pct50で式指定の数値も検査します。4つの固定source snapshotでMetal計4回、最終2回はGPU shader共通でauthored inputが異なり、同一source/input retry0。全失敗raw・全出力を保持しています。portable-world-skill-finding.jsonと初回/formula-admission/formula-packing-metal.jsonを参照してください。

Windows v93は固定9c34a5f1a4542811385ac3f6160087c3ef39b29e（23ファイル356917bytes）で新規50入力/native40に成功しました。CPU39検査・GPU禁止50入力照合・source SHA73を先行し、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、105.142319秒・exit0。保存3JSON計65960bytesだけを取得し、source/name/bytes/SHA・全input/output/native/着弾trace/generated fingerprint・50 API phase・旧783/通常4682以下の再実行0・元HEAD/status/service保持・残存0・retry0を共通監査器で照合しました。portable-world-v93-cuda-validation.jsonとseal-world-v93-cuda.pyを参照。再実行不要です。

次の数値組合せで、auto_damageのnativeは明示damage_formulaがない限りnormal_atk_dmg_pctを受けない一方、既存portable packerはauto_damageを常にdamageNormal1にする差をCPUで確認しました（native242→242、明示normal_attackなら363）。今回の既定値40実戦は一致していますが、auto_damage＋通常攻撃専用補正の組合せは未認証です。world入力の追加検証・修正が必要で、legacy normal生成物を変更しないでください。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPENを維持します。pending/DoT/source攻撃/interrupt・skillの追加part到達、動的操作/復活、全効果組合せ、容量/長時間/全変種の認証は未完了です。hit-only max-HP rankと永続条件付き味方HP/防御のnative不整合も残ります。明示normal_attack式はworld入力だけの追加受付です。全ゴール完了ではありません。効率化は必要検証後、GitHub共有はゴール達成まで利用者許可済みです。

## 2026-10-21 counter完了子の敵fieldをMetal783で実証

計算source4fc576c・private ABI81/mode5で、counter完了子の敵効果を既存Actor selector/resident/merge/条件/同期子へ接続しました。current selectorだけ捕捉Actorの型/ID/世代を使い、致死addから別addへ再aimしても元の死亡世代へ付与します。partの論理受取先はbodyです。generic named子とranked/nearest selectorは現在のaimを使います。def_pct・def_caster_based_pct・received_dmg_pct、current/boss/all/7種rank、同epoch refresh、有限/永続条件、expiry、part damage事前捕捉、128受取先とmarkerが見える間の128同期子を完全native52実戦で確認しました。全特殊効果の組合せ認証ではありません。

Metal783＝新52実戦＋不正10＋旧721全524288word保持が成功し、CPU379検査、旧10entry CUDA/MSL生成物厳密一致、保存input/readback/Git source/nativeのGPU禁止監査も成功しました。共通数値・stack・状態・子イベントを複製していません。case fixtureと比較器はCUDA/Metalで共用です。

初回bf9a60bは旧721/不正10を保持し、31実戦一致でした。body-only native観測にmembershipが無かったため、実際のtarget_charsの観測をopt-inで追加し、同じ保存rawをCPU再監査して51一致を確認しました。項目を無視してはいません。残る128受取先の正当な同期子列は旧4096 work上限でstatus4でした。mode5だけ512carriers×32depth＝16384の有限上限とGPU所有workカウンター（512176以後8words）を追加し、最大4106・合計4833・dispatch691・guard exit0を実測しました。旧モードの4096上限は生成物/全出力で保持しています。異なるソースでMetal2回、同一ソース/入力retry0、失敗raw保持です。

証拠はportable-world-counter-field-validation.json、監査器seal-world-counter-fields-metal.py、初回/membership-replay/finding.jsonです。Windows v92は固定9152a2a52b89cb8d3b77a94a619101a31d6942e8・15ファイル234843bytesの共通short driverで新規62入力/native52に成功しました。CPU28検査とGPU禁止62入力照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、98.870483秒・exit0でした。保存3JSON計74574bytesだけを取得し、source/name/bytes/SHA、全input/output/native/generated fingerprint、50 API phase、workカウンター、元checkout/status/service保持、残存0、retry0、通常4682/旧721以下の再実行0まで共通監査器で確認しました。証拠はportable-world-v92-cuda-validation.json、監査器seal-world-v92-cuda.pyです。Windows turn01a15bbc-c577-7da3-a1f3-f73de12eefcdはcompleted、cursor145、idle。再実行依頼は不要です。

次のtyped damage queueはGPU未接続です。CPU11実戦で、counter子は作成時に式を一度計算し、次フレーム（DT=1/60）か終了時drainで実着弾すること、致死addの子skillが後のbody aimへ着弾すること、named hit_count子（compiler wire49）が元completion targetを継承することを確認しました。ダメージの遅い対象解決と、敵fieldの捕捉対象解決を混同しないでください。

CPU11には新たなnative query scope不整合も保存しました。中立の敵field0があるだけで、body明示照会の味方runtime条件がparent completionのadd文脈からbodyへ変わり、同じchild skillが242→511になります。enemy_recipient_runtime.buffsの非empty field resource条件付きquery scopeを、typed skill受付前に解消・検証する必要があります。portable-world-counter-damage-queue-native-contract.jsonを参照。既知の永続味方HP/防御条件、hit-only max-HP rankの不整合も残っています。

通常画面CPU・public world false・全203変種認証0・legacy unexplained Metal14c8e2e OPENを維持します。typed damage/skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 counter完了子の対象条件をMetal721で実証

計算source6348577・private ABI80/context mode3で、immutable ready rowのActor型/ID/世代を完了子のイベント文脈へ接続しました。target_is_boss/add、target_state/not_target_state/target_stack、self_state/not_self_state/self_stackは既存の共通条件評価器を使います。致死addの再aim後も元addを判定し、death completionはimpactなしでもcompletion.actorを保持します。generic named子イベントは対象を継承せず、現在のaimへ戻ります。有限条件は発動時にlatch、永続条件はcounter終了後の吸血照会で再評価し、同じものにしません。敵sentinelのcounterはself_stateに含まれず、ownerのself_stackには含まれるnative契約を保持しました。

完全native49実戦＋不正9＋旧663全524288word保持＝Metal721入力が成功しました。単体374、旧9entryのCUDA/MSL生成物厳密一致、保存入力/readback/source/nativeのGPU禁止監査も成功しました。contextは既存ready bankへのpointerを32 dispatch×32 frameのGPU所有bank1096words（511080以後）へ保持し、終了時は全word 0へ復元します。数値・resident・同期子実行器の別コピーはありません。新しい共有compiler adapterは既存target_stack placeholder/name allocationを使い、旧41 literal入力はSHA完全一致です。

初回db568d3は新49/不正9成功・旧662保持でしたが、旧「unknown mode2」負例1件が新mode2と衝突しました。失敗rawを保持し、CPU診断後、mode3へ移して旧mode2拒否を保持しました。異なるソース/入力でMetal2回、同一条件retry0です。証拠はportable-world-counter-context-validation.json、監査器seal-world-counter-context-metal.py、mode-finding.jsonです。

前段Windows v90は接続復帰後に保存済み3JSON計55749bytesだけを取得し、CUDA41/native26・CPU18・source67・50 API phase・94.982143秒/実行1回・残存0・元checkout/service保持まで監査しました。v90の再実行0です。Windows v91は固定a9bb64216cce80e813a4a18e524f8b178ba6cc2c、16ファイル250508bytesの共通short driverで新規58入力/native49に成功しました。CPU23検査・GPU禁止58入力照合後、BelowNormal/JobObject/start gate/180秒/cleanup5秒でCUDA1回、100.699126秒・exit0です。保存3JSON計71270bytesだけを取得し、source/name/bytes/SHA、全input/output/native/generated fingerprint、50 API phase、元checkout/status/service保持、残存0、retry0、通常4682/旧663以下の再実行0を共通監査器で確認しました。証拠はportable-world-v91-cuda-validation.json、監査器seal-world-v91-cuda.pyです。Windows turn01a15bad-07d9-7460-8418-eb95ddd467e3はcompleted、cursor143、idle。再実行依頼は不要です。

通常画面CPU・public world false・全203変種認証0、legacy unexplained Metal14c8e2e OPENを維持します。damage子/任意の敵field子、typed skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全変種の認証は未完了です。nativeの永続条件付き味方HP/防御とhit-only max-HP rankの不整合も未解消です。効率化は必要検証後。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 実武器・部位・召喚のcounterをMetal663で実証

計算source e758630、private ABI7Fの共通Slangで、実際のActor着弾receiptから既存counter collect/latch/frame26/event58へ接続しました。body/partは元damage、addはclipped took、致死着弾も捕捉したkind/ID/generationを保持し、credit→同期完了子→死亡登録→lifestealの順で動きます。武器変更のskill式もcredit familyはWEAPONです。part damage/reachを射撃callback前に捕捉し、body回復後に全partのHP/死亡を更新してから個別callbackを回します。

Metal663入力＝完全native26実戦＋不正15＋旧622全524288word保持が成功しました。散弾・武器変更・召喚・部位・致死・世代・expiry・遮断、body+127partsを含みます。partのdirect hits/landedとextra hits/dealtを分け、unbreakable partのHP damage0とextra damage968、再出現gen3のextraリセットも一致しました。CPU369検査、旧8entryのCUDA/MSL生成物厳密一致、保存raw/Git source/全nativeのGPU禁止監査も成功しました。

初回0ae8c2dはcurrent_hp_reduceのkind8受付漏れで23実戦を拒否、次の1f07dbdは21/23一致でpartのdirect/extra会計だけ差がありました。各失敗rawを保持し、CPUで根因確認後に別ソースへ修正しています。異なるソースのMetal実行3回、同一ソース/入力retry0です。証拠はportable-world-counter-landing-validation.json、監査器seal-world-counter-landing-metal.py。新規41入力だけのMetal fingerprintとCPU26実戦照合を固定し、Windows v90を03383d90d5eda28c4eb8c15529365b33add0190e（21ファイル310092bytes）で依頼済みです。CPU18検査後、BelowNormal/JobObject/start gate/180秒/cleanup5秒で1回、通常4682と旧622の再実行0を指定しました。結果はまだ未照合です。

Windows v90のCPU18検査・41入力/native26・全67 source SHA照合とGPU呼び出し0はremote commentaryで確認しました（turn01a15b9e-ae4f-7693-9f09-9263cc3a83e0、cursor133）。CUDA実行依頼後にremote hostがunavailableとなり、実行結果と3JSONは未取得・未監査です。成功/失敗を推測しません。接続復帰後は既存検証の保存済み3JSONだけを取得し、再実行は依頼しないでください。seal-world-v90-cuda.pyとfingerprint/source manifestは保存済みです。

型付きtarget/Impact子context・runtime条件・damage子、skill/pending/DoT/source攻撃/interrupt、動的操作/復活、容量/長時間/全203変種認証は未完了です。未接続のcounter子はprivate受付でも拒否します。通常画面CPU・public world false・全変種認証0/203・legacy unexplained Metal14c8e2e OPEN、効率化は必要検証後です。GitHub共有は利用者がゴール達成まで許可しています。

## 2026-10-21 実着弾のCPU23実戦と共通入力adapter（物理GPU entry未実装）

前回の「body/partはlifesteal後」という引き継ぎは誤りでした。実CPUのイベント列とinstalled ASTを確認し、body/part/add全てでImpact→同期counter完了子→counterへの死亡登録→lifestealと訂正しました。23実戦でbody/addとも同じ着弾の吸血10%→50%変更が効き、HP500→984。body/partのImpactは元damage968、HP50 addはclipped50、hit-HP addは1です。partではbody回復後596.8でcounter子が動き、その後part回復で1000になります。part全件のHP/死亡を先に更新し、それから個別partのcallbackを回すnative順を維持してください。

skill_damage武器変更も物理tagはnormal/pellet/full_chargeで、CounterSpecのfamilyはWEAPONです。式のskill/normalやworldPhysicalNormalからcredit familyを推測しないでください。単発modeのSKILL-only counterは0、WEAPON-onlyは完了を実証しました。遮断はBLOCKED Impactを発行せず、基礎攻撃0でも物理damage下限1です。未知ID/古い世代をbodyへ読み替えません。実戦counter carrierはtarget=bossを明示し、数えるadd/part等はCounterSpecに保持します。target selectorは実addへ解決されてnative prepareに拒否されるため、この差を混同しないでください。

app/portable_target_counter_program.pyへcounterの非数値carrier/event58変換を共通化し、全定義のstat identityを保持しました。既存32入力/native10のSHA完全保持、旧53 native辞書完全一致、portable CPU368が成功しました。research/compile-world-target-counter-battles.pyは23実戦のliteral定義と128 bindingのpart reachをmode1 sidecar/pending ABI7Fへ符号化します。CPU途中状態を入力にせず、現literal ABI7Eはmode1を拒否します。GPUソース変更0・今回GPU実行0・Windows追加依頼0です。

次は新private entryで実際のActor receiptからcredit/死亡を既存collect/latch/frame26/event58へ渡し、lifesteal前に完了子を実行します。part damage/reachは射撃callback前に既存damageValueから捕捉し、body回復後にpart全HPを更新してから個別part callbackへ進みます。旧8entry生成物と旧622全出力を保持してからMetalで実証してください。詳細はdocs/portable-world-target-counters.md、CPU証拠はportable-world-target-counter-battle-native-contract.json/input-validation.json、訂正証拠はlanding-order-finding.jsonです。

前回Metal622/CUDA32は引き続き有効で、Windowsはv89完了・idle、cursor130です。通常画面CPU/public world false・全203変種認証0・legacy unexplained Metal14c8e2e finding OPEN。物理bridge、typed child context、skill/pending/DoT、操作/復活、容量/長時間、全変種対応と必要検証後の効率化は未完了です。

## 2026-10-21 対象別counterの共通resource/event:Metal622／CUDA32一致

計算source98427c0・private ABI7Eで、credit/UID/refresh epoch/expiry/dead Actor、immutable ready queue、全siblings先行latch、共通event58の同期子と同epochだけの終了処理を接続しました。正常10ケース・48段階のUID/epoch/credit/完了snapshot、不正22、旧590全524288word保持に成功し、保存rawのCPU再監査も成功しました。通常＋6旧private entryのCUDA/MSL生成物は厳密一致、portable CPU364（unit revision a27f308）も成功しています。

初回a27f308の10正常入力は自律worldのop24完了条件で全受付拒否でした（raw22拒否/旧590保持は成功）。失敗rawを保持し、CPUで根因を確認後、sidecarあり・全op43・範囲内時刻のliteral rootをprivate providerで区別しました。別ソース98427c0で成功し、物理GPU実行は異なるソースで各1回、同一ソース/入力の再試行0です。Macは現在GPU job0です。

source packet61c7a884c3d687c486017d71e84e560d6b0a46e9、codex/cuda-world-v89-source（13ファイル233071bytes）でWindows新32入力だけを検証し、Mac監査まで成功しました。CPU phase5＋target_counter8、GPU禁止の32入力/native10照合後、BelowNormal/JobObject/start gate/独立180秒/cleanup5秒でCUDA1回・92.3588146秒・exit0。3JSON計50092bytesのsource/name/bytes/SHA、全input/output/native/generated fingerprint、50 phase、元checkout/service保持・残存0を確認しました。旧590/通常4682/旧各suite再実行0、GPU retry0です。Windows turn01a15b67-4fba-7982-b0ad-033e5cf20c5aはcompleted、cursor130、idle。再実行依頼は不要です。GitHub共有はゴール達成まで許可済みです。

Mac証拠:portable-world-target-counter-validation.json、portable-world-target-counter-metal.json、初回失敗/root-finding、監査器seal-world-target-counter-metal.py。次は実武器/散弾/部位/召喚のImpact bridge（body/part/addはいずれもlifesteal前、addはclipped receipt callback、致死credit先行）、型付き対象条件/子context、skill/pending/DoTへ接続します。このphaseはliteral resource/eventのみで、未接続のdamage子/runtime条件/通常enemy field子をcounter有効時に拒否します。通常画面CPU・world公開無効・全変種認証0/203、効率化は必要検証後です。

## 2026-10-21 対象別カウンター：入力とnative基準を固定（GPU未接続）

前段のMetal590/CUDA61成功を保持し、CounterSpec/Impactを使う共通literal sidecarとCPU参照器を追加しました。既存10ケース・48段階、共通compilerの11 policy row、子イベント内のdamage0/credit1着弾で即完了する実CPU witnessが成功し、portable CPU363検査も成功しました。GPUソース・通常受付・実験ABI7Dは変更していません。今回GPU0・Windows追加依頼0、通常画面CPU・world公開無効・全変種認証0/203です。

重要な接続順として、counter prepareはcarrier登録/refresh直後、名前付き/stack子イベントの前に必要です。CPU AST挿入と実際の子でresourceが見えることを確認しました。入力は5,128 words（256定義/64 action）、native途中状態を含めません。`research/portable-world-target-counter-native-contract.json`と`docs/portable-world-target-counters.md`を参照し、次はprivate entryへresource/epoch/dead/ready queue/event58を接続してください。着弾bridge、Metal/CUDA照合、skill/pending/DoTと全変種対応はまだ未完了です。GitHub共有はゴール達成まで許可済みです。

# Mac側で開発を続けるための引き継ぎ

## 2026-10-21 128対象・共有バフのスタック操作をMetalへ接続

実験ABI7D・計算source50522a9で、buff_stack_add/remove/init、buff_max_stack_add、debuff_stack_add/removeを共通実行器へ接続しました。対象集合と世代・免疫だけを拡張し、整数変換・符号・ゼロの既定値・有限/無限上限・期限更新・遅延通知は既存stack_runtime/stack_numericを共用します。共有バフは65対象への操作でも1個のstackだけを1回更新し、対象ごとへ分割しません。共有バフに一部免疫があっても、nativeと同じ共有stackへの影響を保持します。

Metal590入力はnative53件・拒否8件・旧529入力の全524288出力word保持で成功しました。単体356件と、通常/fields/state/mutation/recipient/statusのCUDA・MSL生成物厳密一致を確認しました。小数・正負ゼロ・正負巨大値、named/unnamedの0/1下限、無限上限、2147483647の最終許容値、参照stack、所有者の違い、共有対象・免疫・再出現、期限更新とstack_reach子通知を含みます。31bit保持域を超える結果はstatus2で拒否し、許容範囲と混同しません。GPU実行1回・再試行0です。

証拠はportable-world-actor-stack-validation.json、CPU監査器はseal-world-actor-stacks-metal.py。新規61入力/53 native参照の全fingerprintを保存し、GPU関数禁止のCPU照合も成功しました。Windows v88は固定a106e1eの共通driverで61入力/53 native参照を94.76秒、BelowNormal・180秒上限の1回で成功しました。CPU13検査・GPU禁止事前照合、全input/output/native/generated SHA、NVRTC/launch/同期/readbackの50記録をMacで監査しました。31bit超過のstatus2も一致しています。保存済み3JSON 66,312bytesを取得してbytes/SHAと固定Git sourceを照合し、元checkout/サービス保持・残存0・retry0を確認しました。証拠はportable-world-v88-cuda-validation.jsonです。通常4682・旧529全件の再実行はありません。target_hit_counterと完了/死亡/refresh epoch、skill/pending/DoT、mixed target、source攻撃/interrupt、操作/復活、容量/全203認証は未完了で、通常画面CPU・world公開無効・全変種認証0/203・効率化未開始を維持します。


## 2026-10-21 128対象の免疫・回数プール・解除をMetalへ接続

計算source0873bd9・実験ABI7Cで、既存status_runtimeの免疫走査・容量最大・使用数加算・再補充・解除順を共用し、対象参照と保存先を128対象へ拡張しました。通常/名前指定免疫は捕捉世代と生存を照合します。回数免疫はnativeのtarget_chars契約に従い、再出現通知中の旧世代でも実際に対象一覧から除かれるまで容量を参照します。この差は完全CPUの通知トレース3件で実測して保存しました。容量を整数へ丸めず、0.5/1.5の防御回数も一致します。

Metal529入力はnative37件・不正入力8件・旧484入力の全524288出力word保持で成功し、単体348件と通常/fields/state/mutation/recipientの生成CUDA・MSL厳密一致も確認しました。128個別プール、同名最大・別名独立、再補充、named免疫、irremovable、65対象、共有バフの部分解除、無通知での最後の受領者解除、再出現を含みます。初期コンパイラ比較はCUDAの空行1個で失敗し、読み取り式のproviderへ移して正規化を広げず回復しました。その修正までGPU実行0で、最終GPUは1回・再試行0です。

証拠はportable-world-actor-status-validation.json、CPU監査器はseal-world-actor-status-metal.py。共有受領者の新23入力と今回の45入力をまとめた68入力/56 native参照の全fingerprintを保存し、GPU関数を禁止したCPU事前照合も成功しました。Windows v87は固定f988d15の共通driverで68入力/56 native参照を94.93秒、BelowNormal・180秒上限の1回で成功しました。CPU21検査・GPU禁止事前照合、NVRTC/launch/同期/readbackの50記録、全input/output/native/generated SHAをMacで監査しました。元checkout/サービス保持・残存0・retry0です。保存済み3JSON 70,487bytesだけを取得してSHA照合し、GPU再実行0です。summaryにold484のカウンターが無いため、明示receiptの0・固定68入力command・実測launch1回から確認し、欠落や矛盾を許さないCPU負例5件と旧v83〜v86監査結果保持も確認しました。証拠はportable-world-v87-cuda-validation.jsonです。旧461/484・通常4682を全件再実行していません。スタック操作/target counter、skill/pending/DoT、mixed target、source攻撃/interrupt、操作/復活、容量/全203認証は残っており、通常画面CPU・world公開無効・全変種認証0/203・効率化未開始を維持します。


## 2026-10-21 長寿命共有受領者をMetalへ接続

実験ABI7B・計算source e7585b8で、512 residentそれぞれの128bit可変membership・捕捉generation・対象順を追加しました。単一受領者と共有受領者が同じ照会・世代照合を使い、buff_stack_initは1/65/128対象を1個のstack/期限で保持します。部分解除・全解除・死亡によるmembership解除・再出現・有限期限通知を共通実行器へ接続しています。

Metal484入力は完全native19件・不正入力4件・旧461入力の全262144出力word保持と拡張領域zeroで成功しました。CPU340件、通常／fields／state／mutationのCUDA・MSL生成物が厳密一致しました。M5のmaxBufferLength 14,302,248,960 bytesを実測し、新出力524288 words/ケース・実行全体1,015,021,568 bytesが上限内であることを確認しました。入力92336 wordsは増やしていません。GPU実行1回・再試行0です。元nativeの共有受領者も全辞書で照合しています。

保存結果のCPU監査器はseal-world-actor-recipients-metal.py、証拠はportable-world-actor-recipient-validation.json。新規23入力の全input/output/native/generated基準を保存しました。Windowsは未実行で、次の128対象免疫/解除とまとめて新規入力だけを短く検証する予定です。回数免疫用の拡張領域は確保済みですが、計算接続はまだ未実施です。通常画面CPU・world公開無効・全変種認証0/203・旧Metal差分OPEN・効率化未開始を維持します。


## 次の接続：共有受領者と免疫プール

128対象の完全native17ケースを実測し、回数免疫が対象・名前ごとの最大容量プール、buff_stack_initが1つのcarrierに1/65/128対象を共有する契約を確認しました。従来の単一受領者へ分割するとstack・通知の意味が変わるため、GPUの長寿命共有受領者領域を先に接続します。実装・Metal検証・Windows確認は未実施です。設計は `docs/portable-world-actor-status.md`、実測は `research/portable-world-actor-status-native-contract.json`。今回のGPU実行0、Windows待機中、通常CPU・全変種認証0/203を維持します。


## 2026-10-21 型付き128対象の名前指定解除（Metal／CUDA一致）

実験ABI7A・固定af7aae6で、共通resident解除処理に名前指定のglobal／味方scope／敵scopeを接続しました。敵scopeは既存128対象集合を一度だけ捕捉し、全対象の解除を終えてから既存の状態終了通知列を実行します。新しい同名バフを通知から再付与しても、終了した走査で再削除しません。世代の照合は既存actorFieldMemberを使います。効果計算の別コピーはありません。

Metal461入力で完全native30件・不正入力7件・旧424入力の全262144出力word保持が成功しました。初回は29/30件が一致し、再出現直後に旧世代の空carrierを誤って解除する差が1件ありました。失敗rawを保持し、実CPUのmutation_targetsで重複ラベル45件の旧世代除外を確認後、共通の世代照合を追加した別GPUソースで検証しています。同一ソース・入力の再試行はありません。CPU332件、通常／fields／stateのCUDA・MSL生成物が厳密一致しました。

Windows v86は固定4271202の共通driverで新規37入力（native30＋不正7）を78.29秒、BelowNormal・180秒上限の1回で成功しました。CPU事前13検査・GPU禁止37入力と30参照、NVRTC／launch／同期／readbackの50記録、全input/output/native/generated SHAをMacで監査しました。旧424・通常4682の再実行0・GPU retry0・残存検証0で元checkoutとサービスを保持しています。保存済み3JSON 56,848bytesだけを取得し、bytes／SHAと固定Git sourceを照合しました。証拠はportable-world-v86-cuda-validation.jsonです。通常画面CPU・world公開無効・全変種認証0/203です。条件付き永続味方HP/防御のCPU不整合、広域免疫/stack/counter、skill/pending/DoT、操作・復活・容量・全変種の認証と必要検証後の効率化は未完了です。証拠はportable-world-actor-mutation-validation.json、監査器はseal-world-actor-mutation-metal.pyです。


## 2026-10-21 型付き対象の名前付き状態条件（Metal／CUDA一致）

共通計算ソース8c5a09b、実験ABI79で、target_state／not_target_state／target_stack、self_state／not_self_state／self_stackを128対象のresidentへ接続しました。条件の評価対象は味方数値照会・イベント所有者・明示対象の文脈を保存復元し、死亡・期限切れの対象解除は通知の後に行います。空のenemy carrierも期限通知まで残します。通常受付CPU・world公開無効・全変種認証0/203を維持します。

Metal424入力はnative完全戦闘49件、不正入力18件、旧357入力の全262144出力word保持で成功しました。最初の実行では48/49件が一致し、1件は敵攻撃のliteral payloadが入力生成で欠落して初期拒否されました。失敗rawを保存し、共通入力packerを修正した3bf0881で変更された1入力だけ実行、同じ計算ソース・生成物・入力を持つ423blockを再利用しています。同一入力のGPU再試行0です。CPU単体324件、旧125 native辞書、通常版および前fields版のCUDA/MSL生成物の厳密一致を確認しました。

残課題として、元CPUが永続味方HP/防御効果のruntime条件を無視する実例を保存しました。今回の実験policyでは該当入力を拒否し、対応済みには数えません。旧Metal差分・広範な免疫/解除/カウンター、skill/pending/DoT、interrupt/source攻撃、操作/復活、容量と全203変種の統合も未完了です。効率化は必要な検証後です。

Windows v85は固定c9ecd4dの共通driverで新規67入力（native49＋不正18）を76.69秒、BelowNormal・180秒上限の1回で成功しました。CPU事前14検査・GPU禁止67入力と49参照、NVRTC／launch／同期／readbackの50記録、全input/output/native/generated SHAをMacで監査しました。旧357・通常4682入力の再実行0・GPU retry0・残存検証0で、元checkoutとサービスを保持しています。保存済み3JSON 61,096bytesだけを取得し、各bytes／SHAと固定Git sourceを照合しました。証拠はportable-world-v85-cuda-validation.jsonです。GitHub共有はゴール達成まで利用者が許可しています。個人設定・raw・巨大詳細は共有しません。証拠はportable-world-actor-state-validation.json、CPU監査器はseal-world-actor-state-metal.pyです。


## 2026-10-21 Metal357:128対象の敵バフと敵数条件

private ABI78の共通実行器へ、def_pct・def_caster_based_pct・received_dmg_pctの型/世代付き受取先と、敵数/target_is_boss/add条件を接続しました。発動条件と回数は1回だけ処理し、既存owned setで親の対象順・世代を固定して各受取先を既存resident executorへ渡します。計算式・保持領域・名前merge・expiry・同期子イベントは共用です。Metal357の新52実戦・raw20・旧285既存全出力保持が成功し、最終の各Actor modifierと保持領域の型/ID/世代/stack/時刻/順序までnative完全一致です。128対象・512 resident・死亡/再出現・有限latch/永続runtime敵数条件・武器変更/散弾を含み、通常CUDA/MSL生成コードの厳密一致、CPU315、旧125 native辞書保持も成功しました。

初回保持verifierは、初期化後のコマンド拒否6件でも新領域zeroを期待したため失敗しました。旧285の既存領域と新72は全成功しており、初回report/rawを残して、固定旧GPUのpool-ready markerに従う期待値へ修正し、同じ読み戻しをCPUで再監査しました。GPU retry0です。通常生成差もCPU段階で式/行位置を修正し、厳密一致と314件成功を確認後にGPUへ進みました。後続typed query入力テストを含む315件も成功しています。計算source c2425e5、証拠 `research/portable-world-actor-fields-validation.json` と各findingを参照。

Windows CUDA72も成功しました。最小18ファイル250,128 bytesを固定8be669d、`codex/cuda-world-v84-source`へ共有し、CPU11件＋GPU禁止の72入力/52 native事前照合後、BelowNormal・180秒上限の実GPU1回で72.631秒、exit0でした。全input/output/native・生成fingerprintがMetal保存基準と一致し、NVRTC/launch/sync/readbackを実測50eventsで確認しました。接続の一時失敗と別質問への応答でカプセルが未出力になりましたが、検証を再実行せず保存済み3JSON計53,844 bytesだけを取得し、固定Git blob・輸送SHA・CPU事前結果・全fingerprintをMacで再監査しました。旧285の専用countはreceiptに無いため、source固定の72-input command・transport cases72・実測kernel launch1回・actual execution1回とsummaryの0から非再実行を確認しています。旧208/通常4682/GPU retry0、残存0、元Windows作業/サービス保持、Windowsは待機中です。`research/portable-world-v84-cuda-validation.json` を参照。個人設定/raw/巨大詳細は共有せず、利用者のゴール達成までのGitHub共有許可を反映しています。

wide enemyのその他条件、immunity/cleanse/counter、skill/pending/DoT、mixed target、interrupt/source attacks、自動制御/復活、容量/長時間条件、全変種認証と必要検証後の効率化は未完了です。pure hit-HP召喚のmax-HP順位は元nativeでTypeErrorになることをCPU実証して保存し、この組み合わせはまだ受け付けません。通常画面CPU/public受付false/全変種0/203を維持します。

## 2026-10-21 Metal285: ActorのHP・命中・128対象集合

固定822c559のprivate ABI77で、召喚のHP/hit制HP・通常武器からの命中・死亡通知・GPU targets_cleared再出現、部位の超過ダメージ/score、128bitと順序/世代付き対象集合を共通landへ接続しました。Metal285は実戦native14・型付きpool/set10・raw拒否19・旧242全出力保持で成功、portable CPU309件、通常CUDA/MSL生成コードの厳密一致、保存rawと固定Git blobの再監査も成功しています。`research/portable-world-actor-pools-validation.json` を参照してください。

Windows CUDA77も成功しました。最小24ファイル301,900 bytesを固定ea1f8dd、`codex/cuda-world-v83-source`へ共有し、CPU15件・全77入力/36 native oracle/SHA事前照合後、BelowNormal・180秒上限の実GPU1回で72.917秒、exit0でした。全input/output byte・native・CUDA/MSL生成fingerprintがMetal保存出力と一致し、NVRTC/launch/sync/readbackを実測50eventsで確認しました。3JSON計56,595 bytesを既存接続で取得し、固定Git blob・全SHA・事前検査・イベント順をMacで再監査しました。通常4682/旧208再実行0、GPU retry0、残存0、元Windows作業/サービス保持、Windowsは待機中です。証拠は `research/portable-world-v83-cuda-validation.json`。利用者はこのゴール達成までのGitHub共有を許可済みで、個人設定/raw/巨大詳細は送っていません。

wide enemy効果・skill/pending/DoT・Actor-bound callback・interrupt・召喚自身の攻撃/自爆・dynamic control/復活・全変種認証・必要検証後の効率化は未完了です。通常画面CPU・public world受付false・全変種認証0/203を維持します。

## 2026-10-21 128枠Actor識別を共通フレームへ接続

実験ABI76でbody・parts・addsの型、設定内ID、出現世代、親参照を共通worldフレームの開始／終了へ接続しました。Metal242入力でnative BossScript/ActorRegistryとの12比較、不正入力22件、以前の208全出力byte保持が成功しました。128枠・全32node・未出現・再出現・古い世代・親rootを含みます。初回237の全blockも保持し、通常CUDA/MSL生成コードはv79と厳密同一、CPU portable303件が成功しました。

最初の通常生成比較ではActor分岐による空行1つを検出しました。shellの後続処理が続いて初回237実証が行われた事実を保存し、比較規則を広げず配置を修正しました。最終242は通常生成物とCPU検査成功を確認後に実行しました。証拠は `research/portable-world-actor-registry-validation.json` と `research/portable-world-actors-metal.json`、設計は [Actor接続](portable-world-actors.md) です。

このActor実証はlifecycle/識別の範囲です。HP・命中・敵数・対象集合・interruptはまだ未接続で、完全battleやキャラ対応として数えません。次に128枠を維持して共通HPと対象集合へ接続します。新ActorのCUDAは未依頼、Windowsは前回208成功後の待機状態です。通常受付CPU・全変種認証0/203を維持します。

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

## 2026-10-21 Metal146・敵バフ解除の整数境界

実験ABI75で防御・core・move・敵効果、shield／vanishの着弾とゲージ、休止・reload・MG冷却、敵バフ解除を共通本体へ接続しました。Metalの146入力で、元の完全simulate70件、raw拒否27件、旧world49全出力が一致しています。敵解除の初回は整数直前の2条件で丸め指定の誤りを検出し、rawを保存してゼロ方向切り捨てへ修正しました。既存35ケースの全出力byteとnative辞書、通常CUDA／MSL生成コード、旧native17辞書、共通portable単体293件も維持しています。

コード・共通fixture・fingerprintだけの22ファイル299,196バイトを固定6c8aaa5として codex/cuda-world-v81-source へ共有済みです。ユーザーは「今後githubへの共有をこのゴールを達成するまで許可します」と明示承認しました。個人設定・raw・巨大詳細は含みません。WindowsにCPU事前検査後の146入力だけをBelowNormal・180秒上限で1回依頼し、結果待ちです。通常4682を再実行しません。新overlayのCUDA成功はまだ主張しません。

通常受付CPU・全変種認証0/203は維持します。skill_damage武器変更モード、Heavyarms固有charge hold、複合ally/enemy selector、Actor、dynamic control・復活、全変種認証は未完了です。[接続契約](portable-world-overlays.md)、`research/portable-world-cleanse-validation.json` と `research/portable-world-cleanse-expected.json` を参照してください。

## 2026-10-21 world49をWindows実GPUで照合

共通フレーム・敵攻撃・対象選択・パターン通知のworld49入力は、固定86f6685でCUDAとMetalの全出力・ソース・生成コードが一致しました。通常4682入力は実行済みv79の保存結果を再利用し、全入力・全出力・CPU比較項目も一致しています。通常コアのGPU再実行はありません。

WindowsはCPU一時領域の権限と隔離checkoutの参照不足をGPU起動前に検出し、失敗記録を保持して環境を修正しました。CPU故障注入5件・Job Object子孫終了・GPU関数を禁止した49入力生成と全SHA一致を先に確認後、worldだけをBelowNormal・独立180秒上限で1回実行し、61.139秒で成功しました。NVRTC・launch・同期・readbackの戻り値0を実測JSONLで確認し、結果8ファイルのbytes／SHAとMac基準を照合しました。元作業・既存サービスを保持、残存検証0です。

追加5ファイルの共有と現在のゴール中の共有・検証について利用者の包括承認を受けています。個人設定とrawは送信しません。通常画面CPU・全変種認証0/203を維持します。別worktreeの実験ABI75 overlayはこの認証に含めません。証拠は `research/portable-world-v80-cuda-validation.json` です。

## 2026-10-21 共通本体への統合とパターン通知

別コピーの実行器を廃止し、通常ABI73と実験world ABI74が同じevent／combat／protection／target計算を使う構成へ戻しました。計算ソース15bcbfeの0秒修正とパターン開始／終了通知を、検証後に元ツリーへ統合しました。通常受付と通常画面はCPUのままです。

通常版の固定ソース4c07f45はMac全52検査・単体286件・Node4件・実編成158条件を通過しました。通知接続版も通常4682入力をMetalで実行し、全出力・全CPU比較項目が一致しました。新しいworld版は38成功条件・2容量拒否・34不正入力、旧4682入力の全出力保持、単体288件を確認しました。初期0秒を二重に処理する追加境界差は失敗rawを保持し、別ソースで4回帰条件を通して解消しました。旧原因未特定Metal差分は未解決のままです。

Windowsの短い検証用に、個別実証済みworld49入力を同じ1セッションへまとめ、Metalで全byte一致を確認しました。通常4682入力とworld49入力の全出力・全CPU参照・ソース・生成コードを比較する基準は約44KBです。許可済みの最小42ファイルを固定6f54193としてGitHubへ共有し、Windows v79をBelowNormal・全体180秒上限で1回実行しました。通常4682入力は141.942秒で成功し、Macで全入力・全出力・CPU参照・共通ソース・生成コードのfingerprint一致を確認しました。続くworld49入力は全体上限で終了し、readbackとevidenceがありません。GPU投入段階は不明のためCUDA未検証を維持します。保存済み4ファイルを既存接続で取得してbyte数とSHAを照合し、GPU再実行0・残存検証0・元Windows作業とサービスの保持を確認しました。効率測定は未実施、worldを含む両GPUの完了版はまだありません。通常版の前回完了ソースは7357045です。`research/portable-cross-v79-partial-validation.json`を参照してください。

世界overlay・debuff／継続被弾・部位・召喚・操作・復活・通常画面・全変種の接続は未完了で、全変種認証0/203を維持します。[共通通知と証拠](portable-world-notices.md)、`research/portable-world-notices-validation.json` と `research/portable-world-provider-global-validation.json` を参照してください。以下は段階ごとの履歴です。

## 2026-10-21 共通フレームから敵攻撃への接続を別コピーで検証

GPUのフレーム時計→敵スケジューラー→既存の対象選択・保護・分配・HP・通知へ接続しました。20成功条件で元の完全なsimulateと全比較項目が一致し、別の2容量超過も拒否できました。72発・同時512発、624語を跨ぐ乱数、装填中の遮蔽物、戦闘不能での射撃停止、終了通知と順位選択の順序を含みます。旧4682入力の全出力ワードも保持し、新規不正入力25件・単体285件が成功しています。

本体はまだ7357045／ABI73で、別コピーの仮ABI74を通常受付へは開いていません。世界overlay・パターン通知・debuff／継続被弾・部位・召喚・操作・復活などの接続を続けます。Windowsと効率測定は未実施です。[接続順・失敗記録・証拠・残作業](portable-world-frame-design.md)を参照してください。通常画面CPU・全変種認証0/203を維持します。


## 2026-10-21 敵世界スケジューラーの共通部品をMetalで検証

最後の本体認証は下記の `7357045` です。次の共通スケジューラーは87グラフ・22不正入力をM5で検証し、元CPUの終了履歴・分岐消費・繰り返し・開始／終了／発射順・フレーム状態が一致しました。逆順32段の連鎖、終了理由の優先、同時1000発、EPSの隣接値、180秒時計、容量あふれを含みます。入力生成の単体4件も成功しました。入力・全readbackと最初の全展開JSONを保持し、同一GPUコードの保存出力で再照合しています。実GPU実行は1回です。

実編成の敵世界受付、共通フレームへの攻撃接続、overlay・効果・召喚体・操作・復活はまだ未完了です。cleared maskは部品検証の手動刺激で、本体ではGPUの対象HP／世代から求めます。Windowsと効率測定は本体接続と必要な全検証まで待ちます。[設計・証拠・次の接続点](portable-world-schedule-design.md)を参照してください。通常画面CPU・全変種認証0/203を維持します。


## 2026-10-21 敵対象選択・整数RNGと最適化を両GPUで照合

固定ソース `782a13c`、ABI `0x50455673`。挑発・ステルス・敵の対象選択（全員／指定枠／乱数／攻撃力順）とCPython整数seed互換MT19937を共通Slangへ接続しました。対象と順序はGPUで決め、既存の受撃・分配・通知へ渡します。対象選択は敵攻撃のsourceTimeとHP同期後に実行します。入力86016／出力159744 wordsは維持しています。seedはuint64整数または正規10進文字列を受け付け、HTTPで不正確な大整数JSON数値を拒否します。

Metal／CUDA全4,682入力（4,112正例・570拒否）の入力・全出力・展開結果・CPU回帰・限定正規化した生成CUDA／MSLが一致しました。旧4,070入力と導入時4,658入力も保持しています。敵対象のCPU回帰548件、同名武器変更と敵バフ24件、624語のRNG更新を跨ぐ2件を含みます。有限最大HPのCPU同期を直し、既知差分3件を完全一致の検査へ戻しました。

Mac全52検査・Python単体278件・Node4件・実編成158条件が成功しました。156条件は既存CPU観測項目と完全一致し、ベクハク2条件の従来HP差分だけを厳密に保持しています。旧136条件の観測結果と全158条件の入出力ブロックを保持しました。実射撃80件・条件付きHP20件と大整数seedのHTTP経路はMacでの追加検証です。

Windows v77はBelowNormal・180秒上限のGPU1回、145.904秒で成功しました。許可済み結果2ファイル（52,532,755 bytes）をGit `7f31876` から取得し、親・2パス・byte数・SHA・全出力を照合済みです。元の作業とサービスを保持し、残存検証0、転送目的のGPU再実行0です。

全検証と転送終了後、不要な定義展開を省く候補を別コピーで測定しました。7局所負荷×1024入力、交互順・warmup後3標本で乱数選択約7.6%・指定枠約4.5%の短縮を確認し、事前基準を満たしました。候補の4,682＋80＋20入力は全入出力一致です。採用版 `7357045` は新たなMetalコア4,682入力と実編成158条件で旧版と全入出力一致、Mac全52検査・単体278件・Node4件も成功しました。Windows v78もBelowNormal・180秒上限のGPU1回、145.193秒で成功しました。許可済み結果2ファイル（52,532,755 bytes）をGit `39fbfc4` から取得し、親・2パス・byte数・SHA・全入力・全出力・CPU回帰・限定正規化した生成CUDA／MSLを照合して採用を確定しました。元Windows作業とサービスを保持し、残存検証0、転送目的のGPU再実行0です。

事前検査79体、愛蔵品313/812条件・全4段階78体、未受付264効果です。全変種認証0/203・通常画面CPUを維持します。一般の敵世界スケジューラー、操作・復活、残る効果は未接続です。以前の原因未特定Metal差分も未解決です。最適化版の証拠は `research/portable-enemy-target-scalar-broad-validation.json`、`research/portable-enemy-target-scalar-transfer-completed.json`、`research/portable-enemy-target-scalar-adoption.json`。基準版の記録も保持しています。[対象選択の契約](portable-taunt-design.md)を参照してください。


## 2026-10-20 HP由来攻撃力・武器変更待機・保留バースト参照倍率

固定ソース `39bce8a`（計算本体 `f2e250c`）、ABI `0x50455672`。`atk_from_hp_pct`、条件付き武器変更の進入待機、保留B3の全バースト時の参照倍率を共通Slangへ接続しました。入力86016／出力159744 wordsを維持し、CPUの戦闘経過をGPUへ渡していません。

Metal／CUDAの全4070入力（3540正例・530拒否）が成功し、入力・全出力ワード・展開結果・CPU回帰と限定正規化した生成CUDA／MSLが一致しました。旧3539入力では有効ABI71→72だけを変更し、意図的な不正ABI70・他の入力・全出力・CPU回帰を保持しています。HP由来185正例・23拒否、待機400正例・11拒否、保留倍率120正例を共通テストへ収録しました。

Mac全47検査・単体263件・実編成136条件・既存HTTP APIが成功しました。旧134成功条件を保持し、以前拒否されたラプラスの通常／成長180秒も検証しました。134条件はCPU観測項目と完全一致、ベクハク2条件だけは従来のHP限定契約を固定値で検査します。別の実射撃80例・条件付きHP20例はMacで検証した範囲です。今回専用のAPIケースを追加したとは扱いません。

Windows v76はBelowNormal・150秒上限のGPU1回、133.46秒で成功しました。利用者が許可した結果2ファイル（42,173,583 bytes）をGit `8eee91b` から取得し、親・2パス・byte数・SHA・全出力を照合しました。元作業・既存サービスを保持、残存検証0、転送のGPU再実行0です。コードと前段記録も個別許可を受けて固定39bce8aまで共有しました。

全検証・Windows転送・残存検証0を確認後、HP基準値の再利用候補を別コピーで測定しました。基準・候補の4070＋実射撃80＋条件付きHP20入力は全入出力が一致しました。7負荷×1024入力、交互順・warmup後3標本では採用基準を満たさず、候補を不採用として検証済み本体を維持しました。CUDA速度・実編成全体・物理ピークメモリの改善は主張しません。以前からの原因未特定Metal差分は未解決のまま保持します。事前検査68体、愛蔵品269/812条件・全4段階67体、未受付294効果です。全変種認証0/203・通常画面CPUを維持します。

証拠は `research/portable-mode-entry-broad-validation.json` と `research/portable-mode-entry-transfer-completed.json`。数値設計は [HP由来攻撃力](portable-atk-from-hp-design.md)、物理時計と保留倍率は [武器変更待機](portable-mode-entry-delay-design.md) を参照してください。

## 2026-10-20 バースト充填速度・射撃中スキル係数を共通化

固定ソース `20e213b`、ABI `0x50455670`。`burst_charge_speed_pct` を共通Slangの射撃・スキル加算へ接続しました。付与者の元ゲージ基準値と初回通常命中を保持し、物理射撃内の同期スキルでは、その射撃中の武器係数を使います。スキルのゲージ用バフは名前付き通知前に取得した値を保持します。入力86016／出力159744 wordsを維持し、CPUの戦闘経過をGPUへ渡していません。

新310正例・71拒否を共通化し、Metal／CUDAの全3331入力（2835正例・496拒否）が成功しました。旧2950入力のABI以外の入力・全出力と、初期版3231入力の全出力を保持しています。Windows v75はBelowNormal・120秒上限の実GPU1回、110.52秒で終了。許可済み2ファイルをGit経由で取得し、親コミット・パス・byte数・SHA・全入力・全出力・展開結果・CPU回帰・限定正規化した生成CUDA／MSLを照合しました。元Windows作業とサービスを保持、残存検証0、転送のGPU再実行0です。旧版v74も短い1回を実行しましたが、修正版の認証根拠には使いません。

Mac全41ゲート・単体254件・実編成130条件・既存HTTP APIが成功しました。実編成128条件が既存CPU観測項目と完全一致、ベクハク2条件は従来のHP／最大HPだけの既知差分を固定値で検査します。条件付きHP20例は今回Macで実行しましたが、Windows v75の新規実行範囲は共通コア3331入力です。APIには今回専用の充填速度ケースを追加しておらず、既存経路の回帰検査です。

初期化器への履歴フィールド反映漏れと、武器変更の同期スキルがCPU28・Metal19となる未収録条件を別々に検出・修正しました。失敗入力とreadbackを保持し、後者は元simulateを使う40条件へ拡張して検証しています。以前の原因未特定Metal差分は未解決として保持し、今回の修正と混同しません。

全検証・Windows転送・プロセス終了後、ヒット数のbinary64変換を再利用する候補を別コピーで測定しました。基準・候補の3331＋HP20入力は全入出力一致です。局所5負荷×1024入力、交互順・warmup後3標本の結果と採否は `research/portable-burst-charge-efficiency-decision.json` に記録し、候補は不採用、検証済みソースを維持しました。CUDA速度・実編成全体・物理ピークメモリの改善を意味しません。

定義事前検査の候補65体、愛蔵品257/812条件・全4段階64体、未受付効果300件です。全変種認証0/203・通常画面CPUを維持します。証拠は `research/portable-burst-charge-validation.json`、[充填速度の契約](portable-burst-charge-speed-design.md)、[次のHP由来攻撃力設計](portable-atk-from-hp-design.md)を参照してください。後者はCPU基本60条件・混合順位60条件だけを調査し、GPU受付はまだ有効にしていません。

## 2026-10-20 物理攻撃の貫通・防御無視フラグを共通化

固定検証ソース `7492d8b`、ABI `0x5045566F`。`pierce_enabled`／`armor_break_enabled` を共通Slangの物理射撃へ接続しました。数量ではなく存在で判定し、既存64要素のstat領域を使います。武器変更中も適用し、通常型スキルや外部の通常ダメージ命令の分類と分けます。散弾は親パケットのダメージを共有します。

Metal全2950入力（2525正例・425拒否）が成功し、旧2754入力はABI番号以外の入力と全出力を保持しました。フラグ162例・不正入力34例・API新8例を両バックエンド共通で保持しています。Windows v72は低優先度・120秒上限の実GPU1回、106.87秒で全2950入力を確認しました。検証器だけを変えた現ソースはGPU計算・主入力・主検証ファイルがv72とbyte単位で同一なので、この保存結果を再利用しています。追加の条件付きHP20例はWindows v73で1回・50.30秒とMetalで実行し、全入力・readback・CPU側差分記録も一致しました。結果共有は版ごとの明示許可後に行い、元Windows作業とサービスを保持、残存検証0です。

Mac全37ゲート・単体251件・実編成126条件・203武器・203部隊の装備初期化・固定8編成・APIが成功しました。実編成は124条件が既存のCPU観測項目と完全一致し、ベクハク2条件は条件無効化後のHP／最大HPにだけ既知のCPU差分を記録します。CPUの最大HP集計は実行時条件を再検査していません。独立20例で契約を確認し、CPU戦闘やGPU本体は変えず、この2固定条件の10フィールドそれぞれを厳密に検査しました。初回と現行のGPU展開結果・元CPU観測結果は全126条件で同一です。全内部状態や受撃時の伝播までの認証ではありません。

初回の実編成検証は一時readbackを削除する設計だったため、失敗時の生readbackは未保存です。全展開結果と同一SHAの再構成入力を保持し、現行では全126条件の入力・生readbackを比較前に保存しています。診断fixtureの初回観測スロット重複と、計測器の単一バッチ上限による保存失敗も別記録に残し、GPU不一致と混同しません。以前の原因未特定Metal差分も未解決として保持します。

全検証・Windows転送・検証プロセス終了後、2つのstat比較を1つのmask比較にする候補を測定しました。基準・候補の2950＋HP20入力は全入出力が一致しましたが、散弾親子通知のGPU中央値が約2.4%増え、warmup後3標本の範囲も重なりませんでした。他7負荷は範囲が重なり、改善を確認できなかったため採用しません。現行の読みやすい比較を維持します。8局所負荷×1024入力のM5測定であり、実編成全体・CUDA速度・物理ピークメモリの改善は主張しません。

入力事前検査の候補63体、愛蔵品0～3段階は249/812条件・全4段階の候補62体です。未対応判定は345件から310件へ減りました。全変種認証0/203体・通常画面CPUを維持します。証拠は `research/portable-attack-flags-validation.json` と [物理フラグの規約](portable-attack-flags.md)。次のバーストゲージ充填速度はCPU45条件＋単発式24条件だけを調査し、GPU受付は未有効です。[次段階の設計](portable-burst-charge-speed-design.md)を参照してください。

## 2026-10-20 敵状態・対象スタック条件を両GPUで検証

固定ソース `795a9e5`、ABI `0x5045566E`。`target_state:`／`not_target_state:`／`target_stack_above:` を共通Slangへ接続しました。完全一致の名前を使い、生きている敵のいずれかに付いた状態を判定し、重複数は複数キャスター・対象の合計ではなく最大値を使います。状態の有無は無限効果の取得時にも再評価しますが、対象スタック閾値は発動時だけ判定します。Runtime配列・入力86016／出力159744 wordsは維持しています。

Mac全2754入力（2363正例・391拒否）が成功し、既存2503入力の全出力・展開結果・CPU回帰を保持しました。新233ケースには完全一致名、全5所有者、期限、複数敵、対象の死亡と再出現、継続ダメージ、除去、整数境界、同名効果の統合30件を含みます。Mac全35ゲート・単体249件・実編成108条件・203武器・203装備初期化・固定8編成・API新10件が成功し、旧104編成はCPU参照の実行時間以外すべて一致しました。

Windows v71はBelowNormal・120秒上限の実GPU1回、82.23秒で変更対象251入力（新233正例・拒否18）を検証しました。GPU計算ソース全46ファイルはv70からbyte単位で不変なので、旧2503入力は保存済みv70の入力・全出力・GPUソースを厳密照合して再利用しました。Macの全2754入力を251＋2503に分け、両方の入力・出力をCUDAと完全一致で照合しています。全2754入力をWindowsで新規GPU実行したという意味ではありません。元checkout・サービスを保持し、残存検証0です。利用者の明示許可後、結果2ファイル（約135KB）をGit `0eb87fb` から取得し、親commit・paths・byte数・SHA・限定正規化した生成CUDA／MSLも照合済みです。転送目的のGPU再実行はありません。

初回Metalでは新しい状態スキャンの期限確認漏れ11件を検出して修正しました。続く追加ケースでは、旧コンパイラーへ渡す仮条件がruntime/merge flagsを変え、同名atk10／20効果がGPU30・CPU20になる不具合を確認しました。元2724入力は両GPUで一致していましたが、そのMac全体検証を中止し、発動時だけの仮条件と別の名前登録に修正しました。両方の失敗入力・readbackを保持し、修正版で全2754入力を新たにMetal検証、変更233ケースをCUDA検証しました。記録は `portable-target-states-first-finding.json`、`portable-target-stack-alias-finding.json` と `portable-target-states-initial-gates-aborted.json` です。以前の原因未特定のMetal差分は別の未解決記録として保持します。

全35ゲート・Windows検証・結果転送・検証プロセス終了後、状態の存在判定を最初の一致で終了する候補を測定しました。全2754入力の入出力は基準版と一致しましたが、未存在の負荷はGPU時間中央値が約9.8%増え、warmup後3標本の範囲も重なりませんでした。残る5負荷の範囲は重なり、明確な改善を確認できなかったため採用を見送り、`795a9e5` を維持します。M5の6局所負荷の測定であり、全実編成・CUDA速度・物理ピークメモリの改善は主張しません。

段階0の受付候補54体、愛蔵品0～3段階の受付210/812条件・全4段階の候補52体で、全変種認証0/203体・通常画面CPUを維持します。全体証拠は `research/portable-target-states-validation.json`、直前の全体証拠はGit `3f6342f` です。次の貫通・防御無視フラグは、CPU102ケースで存在判定・期限・条件・AR/SR/RLの物理攻撃を観測しましたが、GPU受付はまだ無効です（導入前102例は `portable-attack-flags-native-study.json`、当時の原本はGit `13c9bdf`）。残る全キャラ・全特殊効果の対応と認証を続けます。

## 2026-10-20 コア・適正距離条件を両GPUで検証

固定ソース `17decef`、ABI `0x5045566D`。敵コア径・距離の有無・武器リスト・元武器と変更後武器の距離上下限を入力余白1592 wordsへ梱包し、共通Slangがbinary64で判定します。適正距離を広げるstat61/62は既存64要素のstat集計を使い、通常攻撃の距離ボーナスにも接続しました。条件の発動判定は元武器、射撃ダメージはその時点の変更後武器の範囲を使います。入力86016／出力159744 wordsとRuntimeの配列は維持しています。

全2503入力（正例2130・拒否373）をMetal／CUDAで実行し、全入力・全出力・ケース別結果・CPU回帰が一致しました。従来2280入力の全出力ワードを保持しています。新190件にはbinary64の境界、条件の記述順、武器変更の物理射撃8件、確率の0／100%に丸め残差が残る列を含みます。Mac全34ゲート・単体246件・実編成104条件・203武器・203装備初期化・固定8編成・API新8件が成功し、旧102編成もCPU参照の実行時間以外は全項目一致しました。

Windows v69はBelowNormal・120秒上限の実GPU1回、101.86秒で成功しました。元checkoutと既存サービスを保持し、残存検証0です。利用者の明示許可後にGit `6295626` から保存結果2ファイルを取得し、byte数・SHA・全入出力・生成CUDA／MSLをMacで照合済みです。転送のためのGPU再実行はありません。

初回の成分検証は武器変更4件のゲージ観測で失敗しました。検証器が射撃後に元武器へ戻った状態からゲージを再計算していたため、実際のBuffManagerのゲージを読むよう修正しました。初回の全入力・readbackを保持し、CPU-only再照合で190件が一致しています。その後、固定版の全2503入力を新たに実GPUで検証しました。以前の原因未特定のMetal差分は別の未解決記録として保持します。

全34ゲート・Windows実行・転送終了後、入力のゼロ領域検査をまとめる効率化候補を測定しました。候補と基準版の全2503入力・全出力は完全一致しましたが、5負荷すべてでwarmup後3標本の範囲が重なったため、改善は確認できず採用を見送りました。固定ソース `17decef` を維持します。判断は `research/portable-geometry-efficiency-decision.json` に記録しています。M5の局所測定であり、CUDA速度・全実編成・物理ピークメモリの改善は主張しません。

段階0の受付候補52体、愛蔵品0～3段階の受付202/812条件・全4段階の候補50体で、全変種認証0/203体・通常画面CPUを維持します。全体証拠は `research/portable-geometry-validation.json`、直前の証拠はGit `cd5762a` です。残る全キャラ・全特殊効果の対応を続けます。次の `not_core` は着弾文脈のコア確率を参照するため、敵コア径の判定とは別に接続が必要です。CPUで1120イベントと条件順4件を観測し、GPU受付はまだ無効です（`portable-not-core-native.json`）。

## 2026-10-20 条件helperの効率化を両GPU検証後に採用

固定ソース `2b89bab`、ABI `0x5045566C`。共通Slangの条件helperで必要なowner・duration・flags・conditionCountだけを読みます。測定した候補と採用版のhelperは同一です。数値演算・効果定義・Runtimeの配列、入力86016／出力159744 wordsは変更していません。

全2280入力（1940正例・340拒否）の全出力ワードが基準版 `27a3751` とMetal／CUDAで完全一致し、ケース別SHA・展開結果・CPU回帰・旧2182入力も保持しました。Mac全32ゲート・単体243件・実編成102条件・203武器・203装備・固定8編成・HTTP APIが成功し、従来102条件もCPU参照の実行時間以外は全項目一致しました。

Windows v68はBelowNormal・120秒上限の実GPU1回、99.71秒で成功しました。元checkoutと既存サービスを保持し、残存検証0です。結果2ファイルの共有は利用者の明示許可後にGit `4ab2a94` から取得し、byte数・SHA・全入力と出力・CPU回帰・限定正規化した生成CUDA／MSLをMacで照合しました。転送のためのGPU再実行はありません。

全基準検証・転送終了後の測定では、4096発負荷のGPU時間中央値が約2.7%短縮し、標本範囲は重なりませんでした。他の4負荷の範囲は重なります。今回の採用確認で新しい速度測定は行っておらず、実編成全体・CUDA速度・物理ピークメモリの改善は主張しません。

初回の新しい保存器は入力先頭の件数4バイトを記録し忘れて停止しました。実GPU入力・出力は基準版と一致し、rawを保存したうえで保存器を修正し、固定版の全検証をやり直しました。記録は `portable-probability-optimized-initial-harness-finding.json` です。前段の原因未特定のMetal差分は別の未解決記録として保持し、修正済みとは扱いません。

最新の証拠は `research/portable-probability-optimized-validation.json` と `research/portable-combat-checkpoint.json`、基準版の全体証拠はGit `988858f` です。愛蔵品0～3段階の受付監査は198/812条件・全段階の候補49体で、段階0だけの候補51体と区別します。プリムの対象スタック条件・ジュリアのクリティカル条件などが残ります。全変種認証0/203体・通常画面CPUを維持します。

次のコア／適正距離条件は、実CPUのbuff付き35条件と203体×6武器種の距離境界32,886条件を観測しました。入力余白へ武器ID・距離・元武器と変更後武器の範囲を保持する設計だけで、GPU受付はまだ無効です。残る全キャラ・全特殊効果の接続と認証を続けます。

## 2026-10-20 確率条件の両GPU検証と結果照合

ABI `0x5045566C`。期待値モードの `prob:` を共通Slangへ接続し、条件の記述順・binary64累積・元効果の識別を保持します。状態は既存出力余白2560 wordsへ置き、入力86016／出力159744 wordsとRuntime private配列を維持しました。Metal成分92件（4096回の物理射撃5件、複合受領者・遅延順位解決を含む）と単体243件が成功しています。

固定ソース `27a3751` の全2280入力では、旧2182入力の全出力・展開結果・全CPU回帰を保持しました。Mac全32ゲート・単体243件・実編成102条件・APIを確認済みです。Windowsは90.38秒で全2280入力が成功しました。利用者の明示許可を受け、保存結果2ファイルをGit `a14c02b` で取得し、byte数・SHA・全入力と出力・CPU回帰・生成ソースをMacで照合済みです。転送のためのGPU再実行はありません。全検証・転送終了後の効率測定では、条件helperの必要フィールドだけを読む候補が全2280入力で同一出力となり、4096発負荷で中央値約2.7%短縮しました。他の4負荷の標本範囲は重なります。候補は未採用で、採用には変更後ソースの両GPU検証が必要です。前段の全体検証済み証拠はGit `f2206ef`、今回の証拠は `research/portable-probability-validation.json` です。全キャラ・全変種認証0/203体・通常画面CPUを維持します。[確率条件の接続と検証状況](portable-probability-design.md)を参照してください。

## 2026-10-20 属性判定の最適化を両GPU検証後に採用

固定ソース `32653b0`、ABI `0x5045566B`。属性優位上書きの存在判定を、alive／対象所属で絞って既存のkind・stat・codeアクセサーを読む方式へ変更しました。実装は共通Slangの1か所です。数値演算・状態配置・入力86016／出力159744 wordsは変更していません。

最適化後も全2182入力の全出力ワードが、基準版 `14c8e2e` とMetal／CUDAの両方で完全一致しました。全ケース別SHA・旧2006入力・全CPU回帰も保持しています。Mac全31ゲート・単体237件・実編成86条件・203武器・203装備・固定8編成・HTTP APIが成功し、旧86条件の実行時間以外の全項目も一致しました。

Windowsの今回v66はBelowNormal・120秒上限の1回、93.48秒で成功しました。元checkoutとサービスを保持し、残存検証0です。結果JSONとreadback照合記録の2ファイルだけをartifactブランチへ保存し、MacでGit blobのbyte数・SHAと内容を照合しました。基準版v65の88.58秒の保存結果も取得済みで、接続復旧に伴う過去検証の再実行はしていません。

全基準検証・転送終了後の測定で選んだ候補と、採用したhelperのソースは同一です。その測定では通常負荷のGPU時間の中央値が約5.6%、末尾一致負荷で約1.3%改善し、標本範囲は重なりませんでした。残る3負荷は範囲が重なります。今回の採用確認は正しさの検証であり、実編成全体・CUDA速度・ピークメモリの新しい測定ではありません。

初回の未保存Metal出力差は原因未特定のまま、`portable-element-initial-core-finding.json` に保持します。現在の検証では再現していません。修正済みとは主張しません。出力不一致時の全readback・差分ケースの入力・ケース別SHAを保存して停止する比較器を維持しています。

最新証拠は `research/portable-element-optimized-validation.json` と `research/portable-combat-checkpoint.json`、基準版証拠はGit `80170c3` の `portable-element-baseline-validation.json` です。定義受付候補43体・未受付効果384件・全変種認証0/203体・通常画面CPUを継続します。次の確率条件は、スキル値・短絡順・所有者共有位相・4096イベントのbinary64状態をCPUで観測し、[接続設計](portable-probability-design.md)へ整理しました。GPU受付はまだ無効です。

## 2026-10-20 属性優位上書きの基準版検証と効率化候補

固定ソース `14c8e2e`、ABI `0x5045566B`。`element_code_override` を共通Slangへ接続し、元属性とORで属性優位を判定します。数値量やスタック量ではなく、有効キャリアの対象所属とコードIDを参照します。周期callbackが期限整理より先に動く順序、未解決の順位対象、同名・別定義更新で元コードを保持する規則、物理射撃による弾数寿命も元CPUと一致させました。Runtime・Definition・Frameのフィールドと入力86016／出力159744 wordsは増やしていません。

Metal／CUDA1848正例・334拒否（2182入力）、新規CPU参照156件・単体237件・出力記録付きMac全31ゲート・実編成86条件・API追加9条件が成功しました。旧2006入力のABI番号以外の全バイトと全出力ワード、旧86編成のCPU実行時間以外の全項目を保持しています。WindowsはBelowNormal・120秒上限の1回、88.58秒で成功し、元作業とGPUサービスを保持、残存検証0、全65分割の保存結果転送と復元SHAを確認しています。全入力・全出力・判定・展開結果・CPU回帰・検証ソース・限定正規化した生成CUDA／MSLが一致しました。

最初のMac全体実行で旧出力SHAの不一致を1回検出しましたが、そのreadbackを保存できておらず原因は未特定です。同じGPUソースで、隔離した旧2006入力・全2182入力比較・出力保存付き4回・CUDAでは差が再現しませんでした。比較器を変えず、比較前にケース別SHAと不一致時のreadbackを保存する方式へ進め、全31ゲートが成功しました。初回差分を修正済み・解明済みとは扱いません。記録は `research/portable-element-initial-core-finding.json` です。

全検証・転送終了後、必要な3フィールドだけを読む候補を測定しました。全2182入力の出力は完全一致し、今回の通常負荷で約5.6%、属性効果が末尾にある負荷で約1.3%改善しました。残る3負荷の標本範囲は重なります。状態追加を伴わない直接読み取りを採用候補に選び、最適化後の固定ソースを両GPUで確認します。実編成全体・CUDA速度・ピークメモリの測定ではありません。

基準版の証拠は `research/portable-element-baseline-validation.json` と `research/portable-combat-checkpoint.json`、詳細は[属性優位上書き](portable-element-overrides.md)を参照してください。定義受付候補43体・未受付効果384件・全変種認証0/203体・通常画面CPUです。ラピ：レッドフード／シュガの上書き定義を試験していますが、両キャラには他の未対応効果が残ります。次の確率条件は元CPUの規則だけを観測し、GPU受付はまだ有効にしていません。

## 2026-10-20 回帰を保持する共通GPU分割実行

固定ソース `ff9a10d`、ABI `0x5045566A`。全キャラ・全効果の回帰を追加し続けられるよう、一括上限2048を超える入力を順序どおり分割する共通経路を接続しました。CUDAはNVRTC・コンテキスト・モジュール、Metalはライブラリー・パイプラインを各1回生成し、最大分割に合わせた入力・出力バッファ2本をゼロ初期化して再利用します。数値・効果の共通Slang、入力86016／出力159744 words、GPUのRuntime・Definition・Frameは変更していません。

旧2006入力を削らず、先頭44入力を繰り返した2050入力を1024／1024／2で両GPU実行し、旧全出力・追加44入力の全バイトが一致しました。全体と各分割の入力・出力・status・検証ソース・限定正規化した生成CUDA／MSLも一致しています。WindowsはBelowNormal・120秒上限の1回、78.66秒で成功し、元作業とGPUサービスを保持、残存検証0、保存報告の全1分割転送と復元SHAを確認しました。

固定ソースのMac全31ゲート、共通コア2006入力・単体220件・実編成86条件・203武器・203装備・固定8編成・HTTP APIが成功しました。従来86編成の全比較項目をCPU実行時間以外保持しています。全検証と転送終了後の効率測定では、2050入力のGPU時間中央値が分割2048で0.527秒、1024で0.790秒、512で1.079秒でした。GPU標本範囲は重ならず、小さくするほど遅いため既定2048を維持します。ホスト実行時間の範囲は重なります。要求したwireバッファはそれぞれ約1.875／0.938／0.469GiBで、小さい明示サイズも利用できます。物理ピークメモリ・GPU私有領域・CUDA速度の測定ではありません。

最新証拠は `research/portable-dispatch-sequence-validation.json` と `research/portable-combat-checkpoint.json`、詳細は[共通分割実行](portable-dispatch-sequence.md)を参照してください。前段のreceiptは各証拠コミット時点の履歴です。定義受付候補43体・未受付効果385件・全変種認証0/203体・通常画面CPUを維持します。次の属性上書きはCPU60ケースで規則を観測しましたが、GPU受付はまだ有効にしていません。残る効果・敵世界処理と全キャラ・全変種の接続・認証を続けます。

## 2026-10-20 敵コード条件の共通化と両GPU検証

固定ソース `dd7d62b`、ABI `0x5045566A`。`target_code:` の完全一致条件を共通Slangへ接続しました。CPUでコード文字列をID化し、GPUが発動時・実行時の条件を比較します。未指定・空コードは元CPUどおり通し、追加敵への照準継承があっても部隊共通の敵コードを参照します。武器変更が終了時に有効な実編成は、実CPUの射撃方式・定義ID・発数・行動待機時計まで比較します。

Metal／CUDA1692正例・314拒否（2006入力）、追加CPU参照103件、単体212件、Mac全29ゲート・実編成86条件・コード一致／不一致／未指定の実編成6条件・203武器・203装備・固定8編成・HTTP APIが成功しました。旧1893入力はABI番号以外不変で全出力ワード一致、旧84編成はCPU実行時間以外の全項目を保持しています。

WindowsはBelowNormal・120秒上限の1回、80.35秒で成功しました。元作業とGPUサービスを保持し、残存検証プロセス0、保存結果の全9分割転送と復元SHAを確認しています。途中で途切れた転送は保存ファイルの再送だけで完了し、CUDAを再実行していません。全入力・全出力・status・CPU回帰・検証ソース・限定正規化した生成CUDA／MSLはMetalと一致します。

全検証・転送終了後、コード条件を数値引数の読み込みより先に判定する候補を測定しました。全2006入力の出力は一致しましたが、条件なし負荷の中央値が約32.4%悪化し、残る4負荷も標本範囲が重なるため不採用です。現行ソースを保持し、入力86016／出力159744 words、Runtime・Definition・Frameのフィールドは増やしていません。実編成全体・CUDA速度・ピークメモリの測定ではありません。

最新証拠は `research/portable-enemy-codes-validation.json` と `research/portable-combat-checkpoint.json`、詳細は[敵コード条件](portable-enemy-codes.md)を参照してください。定義受付候補43体、未受付効果385件、全変種認証0/203体・通常画面CPUです。効果本体の別フィールド `target_code`、残る効果・敵世界処理と全変種の接続・認証を続けます。現在2006入力／一括上限2048のため、今後は既存回帰を削らず共通検証の分割実行も検討します。

## 2026-10-20 名前付き状態・適用通知と元武器分類の両GPU検証

固定ソース `ed68e68`、ABI `0x50455669`。コロンを含む名前の状態条件・通知と、`dot_dmg_pct`／`split_dmg_pct` の適用通知を共通配送器へ接続しました。発動時の対象順・重複を保持し、遅延対象を解決した後の別定義更新でも元定義のフラグで通知を省きません。実編成で見つかったRLチャージ射撃の爆発分類漏れも、元武器情報を共通入力へ渡して修正しました。

Metal／CUDA1589正例・304拒否（1893入力）、追加CPU参照65件、単体195件、Mac全27ゲート・実編成84条件・203武器・203装備・固定8編成・HTTP APIが成功しました。旧1882入力はABI番号以外不変で全出力ワード一致、旧82編成もCPU実行時間以外の全項目を保持しています。元の失敗2成分・別定義更新2件・新規「민트」実編成2条件は履歴に残し、現在版は全効果を含む「민트」通常／成長180秒もCPU本体と一致します。

Windowsは初期版77.07秒、実証した差を修正した現在版76.23秒の必要な短い各1回です。BelowNormal・120秒上限、元作業とサービスを保持、残存検証プロセス0、全8／9分割の転送と復元SHAを確認済みです。全入力・全出力・status・CPU回帰・検証ソース・限定正規化した生成CUDA／MSLが両GPUで一致します。

全検証と転送終了後、通知先がない継続処理を省く候補を測定しました。全1893入力の出力は完全一致しましたが、全5負荷で標本範囲が重なり、遅延／空の対象負荷でも中央値が改善しないため不採用です。現行ソース・入出力86016／159744 wordsを維持し、Runtime・Definition・Frameのフィールドは増やしていません。実編成全体・CUDA速度・ピークメモリの測定ではありません。

最新証拠は `research/portable-named-states-validation.json` と `research/portable-combat-checkpoint.json`、詳細は[名前付き状態と適用通知](portable-named-states.md)を参照してください。定義受付候補42体、未受付効果395件、全変種認証0/203体・通常画面CPUです。次は敵コード条件など残る効果・敵世界処理を接続し、全キャラ・全変種の認証を続けます。

## 2026-10-20 Windows接続復旧・現在版の両GPU照合

固定ソース `60a10b6`、ABI `0x50455667`。Metal／CUDA1524正例・300拒否（1824入力）、instant配送CPU参照45件・分配46件・保護層57件、Mac全26ゲート・単体177件・実編成82条件が成功しました。旧1773入力の出力は全ワード一致です。全入力・全出力・status・全CPU回帰リスト・検証ソース、および限定正規化した生成CUDA／MSLを両GPUで照合しました。

接続復旧後、先行v59の保存結果をGPU再実行なしで回収しました。現在版v60はBelowNormal・120秒上限の1回で77.98秒、残存検証プロセス0、元のWindows作業とGPUサービスを保持しています。両報告とも全8分割の転送と復元SHAを確認済みです。

全検証と転送終了後、Frame.valueを32bitへ戻し、対象順序の上位bitを既存出力余白の32ワードへ置く候補をM5で比較しました。全1824入力の出力は完全一致しましたが、単一グループ・複合3対象・21回instant回復で中央値が約2.4〜3.5%悪化したため不採用です。21対象通知は標本範囲が重なり速度改善を確定できません。現行コード・ABI・strideを維持します。実編成全体・CUDA速度・ピークメモリの測定ではありません。

最新の証拠は `research/portable-instant-lists-validation.json` と `research/portable-combat-checkpoint.json`、契約と数値は[共通instant配送](portable-instant-lists.md)を参照してください。以前のMac単独receiptはコミット `c72b529` 時点の履歴です。全変種認証0/203体・通常画面CPUを継続し、残る効果・敵世界処理と全変種の接続・認証を進めます。

## 2026-10-20 複合instant配送のMac確認（CUDA結果取得待ち）

固定ソース `60a10b6`、ABI `0x50455667`。HP・遮蔽・保護膜・デコイ回復、現在HP減少、弾薬操作、クールタイム短縮の複合対象を共通の再開可能な配送器へ接続しました。最大21回の順序と重複を保持し、子通知後に次の量を評価します。部隊共有ゲージは1回だけ加算します。通常入力で21回の回復がHP310となり、前段のGPUが5回だけ処理する未完成経路を修正しました。

Metal1524正例・300拒否、新規CPU参照45件、単体177件、Mac全26ゲート・実編成82条件・API追加8条件が成功しました。旧1773入力の全出力ワード、直前82編成のCPU実行時間以外の全項目を保持しています。入力86016／出力159744 wordsとRuntime／Frame宣言は前段と同じです。

Windowsは先行v59（`d12b365`）の実行結果と転送終端が接続途絶で未確認です。同じ検証を再起動せず、保存結果の取得を待っています。現在の固定版でのCUDA検証はまだ依頼しておらず、先行実行の終端確認後に必要な短い検証だけを依頼します。効率化は未実行です。全変種認証0/203体・通常画面CPUを継続します。[契約・Mac証拠・残る作業](portable-instant-lists.md)、`research/portable-instant-lists-metal-validation.json` を参照してください。

## 2026-10-20 均等分配・複合バフ対象のMac確認（継続中）

固定ソース `d12b365`、ABI `0x50455666`。均等被ダメージ分配と、順序・重複を保持する最大21回の複合バフ対象を共通Slang実行器へ接続しました。Metal1479正例・294拒否、CPU分配46件＋既存保護層57件、単体166件、Mac全25ゲート・実編成82条件・API追加6条件が成功しています。旧1709入力の全出力ワードと新末尾のゼロ、旧74編成のCPU時間以外の全項目を保持しています。監査候補41体・全変種認証0/203体・通常画面CPUです。

Windows v59は依頼受領後に接続が失われ、実行結果と転送の終端が未確認です。再実行せず保存結果の取得を待っています。また、通常APIが拒否する複合instant対象のraw-wire診断で、21回の回復をGPUが5回だけ実行する未完成経路を確認しました。次にinstant配送を接続して境界を閉じます。効率化と段階全体の完了扱いは保留しています。[契約・未完了・Mac証拠](portable-split.md)、`research/portable-split-metal-validation.json` を参照してください。以下の保護層は直前の両GPU検証済み記録です。

## 2026-10-20 保護膜・デコイと被弾層の共通化

固定ソース `c411ddc`、ABI `0x50455665`。保護膜・共有保護膜・デコイの生成／消費／回復、次の保護膜の増幅、作成者基準の保護膜無敵、遮蔽無効、`during_shield` と適用／消費通知を共通Slang実行器へ接続しました。入力は81920／出力135168 wordsで、私有配列・Runtimeスカラー・Frameフィールドは追加していません。

Metal／CUDA1433正例・276拒否（1709入力）、保護層CPU参照57件・状態79件・スタック148件、単体155件が成功しました。最適化後のMac全24ゲート、実編成74条件・203武器・203装備・固定8編成・API保護層5条件も成功しています。旧1625入力はABI番号とゼロ拡張以外不変で、旧出力全ワードと新しい末尾のゼロを保持します。最適化前後の全1709入力の出力、および74実編成の全比較項目・CPU参照（CPU実行時間以外）も一致しています。

Windowsは初期版74.59秒・最適化後72.67秒の必要な短い2回です。各120秒上限・BelowNormal、元作業とサービス保持、残存検証プロセス0、全8分割の転送完了を確認しました。最終版は固定ソースの全1709入力を実際に一括CUDA実行した証拠で、差分の合成ではありません。生成CUDA／MSLも位置情報・標準include経路等を限定した正規化で一致します。

全検証と転送終了後に測定し、定義に存在しない保護膜無敵・遮蔽無効・増幅の探索を省く静的機能マスクを採用しました。M5の限定負荷中央値は32膜27.535→24.674ms（約10.4%短縮）、256膜332.400→283.381ms（約14.7%短縮）。1膜と機能が存在する対照負荷は範囲が重なり、変化を確定できません。実編成全体・CUDA速度・ピークメモリの測定ではありません。

監査候補は37体・全変種認証0/203体・通常画面CPUを継続します。対象／遮蔽マスクは手書きの機械条件であり、自動照準・ボス予定・均等分配などの世界処理は未接続です。残る保護系10項目と修飾・操作・敵世界・効果を接続します。[契約・CPU補正・測定範囲](portable-protection.md)、`research/portable-protection-validation.json` と最新checkpointを参照してください。

## 2026-10-20 デバフ解除・免疫・名前付き状態の共通化

固定ソース `d2ba01a`、ABI `0x50455663`。デバフ解除、無制限／名前指定／回数制免疫、statを持たない名前付き状態を共通Slang実行器へ接続しました。省略・null・空文字の状態統合、通知後の免疫残量リセット、共有敵世代、部分解除後のDoT対象と時計、最大HP解除後の比率を独立CPU参照で照合しています。

採用後のMetal／CUDA1376正例・249拒否、状態CPU参照79件、切り替え境界64／65プールの追加2件が成功しました。Mac全23ゲート、単体146件、64実編成・203武器・203装備・固定8編成・API追加5条件も成功しています。旧1528入力の出力差は、CPUでは有効だったlazy容量入力1件だけで、別の実際に容量を超える入力で拒否を維持しました。旧60実編成と直前64条件はCPU実行時間以外の全項目を保持しています。

Windowsは初期全体69.15秒、CPU入力／観測修正の差分2件45.74秒・1件45.38秒、GPU最適化後の全体＋境界2件115.90秒の4回だけです。各120秒上限・BelowNormalで終了し、元作業・サービス保持、残存検証プロセス0、全転送完了を確認しました。最終版は現ソースの全1625入力を一括CUDA実行しており、途中の差分合成証明と区別して保存しています。

全検証・Windows転送終了後に測定し、64以下の免疫プールだけ触れた名前を消去する方式を採用しました。限定負荷のM5中央値は1プール15.625→13.647ms（約12.7%短縮）、32プール35.850→35.157ms（約1.9%短縮）。255プールでは改善を判断できず、大きいプール数では従来の全消去を維持します。候補の全1625入力・全出力ワード一致と、採用後の両GPU・全ゲートを確認済みです。入力77824／出力102400 words、出力は32KiB増えますがRuntime配列・スカラーやFrameフィールドは増やしません。実編成全体の速度・CUDA速度・ピークメモリの主張ではありません。

定義監査候補32体・全変種認証0/203体・通常画面CPUを継続します。残るライフサイクル・敵世界・防御・操作・効果と全変種の認証を続けます。[契約・数値・測定範囲](portable-status.md)、`research/portable-status-validation.json` と最新checkpointを参照してください。

## 2026-10-20 スタック操作・初期化・変更免疫の両GPU確認

固定ソース `ba890da`、ABI `0x50455662`。6種類のスタック操作と変更免疫を共通実行器へ接続し、共有敵状態の世代・部分解除・終了通知、HP子通知順、対象別発数、初期化時の条件寿命を検証しました。Metal／CUDA1297正例・231拒否、スタックCPU参照148件が成功しています。旧1355入力はABIのみの変更、旧出力差は18ケースのDoT生成時刻だけで、全てCPU生成記録と一致します。他の全出力ワードは保持しています。

全22ゲート、単体138件、60実編成・203武器・203装備・固定8編成・HTTP追加4条件が成功しました。既存58編成の全比較項目・CPU参照も保持しています。Windowsは初期版68.78秒と修正版66.98秒の必要な短い2回で終了し、元作業・サービス保持、残存検証プロセス0、各7分割の転送完了を確認しました。全入出力・status・CPU参照・正規化生成コードは両GPUで一致しています。

全検証・転送終了後の検索効率2候補は、異名負荷を約8%短縮しましたが、同名負荷では改善を確認できず採用を見送りました。入力／出力サイズとRuntime／Frame宣言は前版と同一です。定義監査候補は30体、全変種認証0/203体・通常画面CPUを継続します。[実装・測定・残る範囲](portable-stack-operators.md)、`research/portable-stack-operators-validation.json` と最新checkpointを参照してください。

## 2026-10-20 スタック整数・保存通知と+1専用化の両GPU確認

固定ソース `6e28e63`、ABI `0x50455661`。整数化・ゼロ既定値・符号反転・上限処理と、更新時の値を保持する4096件の共有通知基盤を接続しました。既存の通常バフ・DoT・対象別発数スタックの増加も共通処理です。入力77824／出力94208 words、保存値のため出力は16KiB増えますが、私有配列・Runtimeスカラー・Frameフィールドは増やしません。

Metal／CUDA1149正例・206拒否、数値19908件・通知9件が成功し、採用前1355入力・全出力が正規化なしで一致しました。モードCPU参照41件・既知差分0、単体131件、58実編成・203武器・203装備・固定8編成・API追加4条件など、採用後の全22ゲートも成功しました。58実編成の全比較項目・CPU参照も保持しています。

全検証とWindows転送終了後、+1専用uint64候補を測定しました。32バフ×64イベント×64入力のGPU中央値53.946→47.470ms（約12.0%短縮）、各3標本の範囲は非重複です。実編成全体の速度やピークメモリの主張ではありません。採用後のWindowsは低優先度・120秒上限の1回、82.486秒で成功しました。基盤版の103.038秒と合わせて必要な短い検証2回で、各7分割の転送終了、元HEAD・作業・サービス保持、残存検証プロセス0です。

新しいstack add/remove/init/maxと変更免疫の効果種別はまだ受理していません。次の接続用に、整数/期限/通知/免疫53条件、初期化/0保持/共有対象11条件、敵世代22時点を独立CPU参照で確認しました。通常画面CPU・全変種認証0/203体を維持します。[数値・通知・次のCPU契約](portable-stack-foundation.md)、`research/portable-stack-increment-validation.json`、最新checkpointを参照してください。

## 2026-10-20 スタック整数・遅延通知の共通基盤

固定ソース `8516256`。整数化・ゼロ既定値・符号反転・上限処理を共通Slangへ接続し、Apple M5で19,908数値ケースと通知9ケースが成功しました。旧1355入力はABI番号だけの変更、旧出力90112 wordsは全バイト一致し、新末尾はゼロです。ABI `0x50455661`、入力77824／出力94208 words。更新時の値を保持する共有通知キューにより出力は16KiB増えますが、私有配列・Runtimeスカラー・Frameフィールドは増やしません。

Macの全22ゲートは成功し、58実編成の全比較項目・CPU参照も前版と一致しました。Windowsも低優先度・120秒上限の1回、103.038秒で全検証が成功しました。入力・出力・CPU参照・正規化生成コードが両GPUで一致し、7分割の転送と検証プロセスの終了を確認しました。この段階で新しいスタック操作・免疫の効果種別は受理していません。全変種認証0/203体・通常画面CPUを維持します。[数値・通知・次のCPU契約](portable-stack-foundation.md)、`research/portable-stack-foundation-global-gates.json` を参照してください。

## 2026-10-20 同フレームのセッション識別・終了通知の弾倉基準

固定ソース `2e1a265`。CPU互換層で論理セッションと物理入場を区別し、未解決の同フレーム再入／別モード置換2件と、既知の期限終了後の子再入1件を通常照合へ戻しました。モードCPU参照41件・既知モード差分0です。保持中の入力期間は維持し、親の射撃で新しい弾倉・発数・予約を上書きせず、実際に撃ったMGの蓄積と時計を保持します。元のCPUファイルは変更していません。

追加テストで、共通GPUの終了通知内の割合操作が旧射撃の容量を参照する差分も見つかりました。10発へ戻した後の50%除去が2発となる差を5発へ修正し、子の再入／取り消しと二重補充も検査しています。新しいGPU配列・スカラー・wire領域はありません。

Metal／CUDA1149正例・206拒否、単体131件・周期CPU15件・追加native10件、58実編成・203武器・203装備・固定8編成・HTTP追加4件・数値34874件・実証4件を含む全21ゲートが成功しました。Windowsは低優先度・120秒上限の1回、73.230秒で終了し、全入力・全出力・status・検証コード・全CPU参照・正規化生成コードが一致しました。旧1345入力と全出力は両GPUで全バイト一致、58実編成もCPU実行時間の記録だけを除いて全項目一致しています。元のWindows作業状態・サービスを保持、検証プロセス0、全22分割の転送も終了しています。

全検証と転送終了後、解除の重複を省く候補で1149正例の全出力ワード一致と順次測定を確認しました。64入力×3秒、各3標本のGPU中央値は終了1回17.287→17.236ms、毎フレーム終了22.678→22.481msですが、どちらも範囲が重なり未採用です。[契約・原因・数値・残る範囲](portable-session-identity.md)、`research/portable-session-identity-validation.json` と最新checkpointを参照してください。次はstack変更・初期化・免疫など残るライフサイクルと世界・操作・全効果の接続を続けます。全変種認証0/203体・通常画面CPUを維持します。

## 2026-10-20 通常武器復帰時計の修正

固定ソース `a7f4784`。通常武器の再開フレームで射撃時計を更新し、終了通知前に戻した弾倉を再補充せずに保持します。新しい状態配列・wire領域はありません。機械fixtureの変更武器が省略した装填時間を、CPU参照と同じ元武器から継承するよう入力準備も修正しました。未調査だった4ケースがCPU全比較フィールドと一致し、連続フレーム8条件を追加、モードCPU参照29件となりました。

Metal／CUDA1139正例・206拒否、単体128件・周期CPU15件、58実編成・203武器・203装備・固定8編成・API・数値34874件・実証4件を含む全18ゲートが成功しました。Windowsは低優先度・120秒上限の1回、61.989秒で終了し、全入力・全出力・status・全CPU参照・正規化生成コードが一致しました。元の作業状態とサービスを保持、残存プロセス0、22分割の転送も終了しています。旧1125ケースの全状態を維持し、変わった6件はquery内の射撃／装填時計だけです。58実編成もCPU参照の実行時間だけを除いて全項目一致しました。

全検証と転送終了後、復帰判定を既存分岐へまとめる候補で1139入力の全出力ワード一致を確認しました。64入力×3秒、各3標本の中央値は発数終了17.256→15.266ms、時間終了17.255→17.188msでしたが、両条件で範囲が重なり、前者はばらつきも大きいため未採用です。[原因・数値・比較範囲・残作業](portable-mode-return.md)、`research/portable-mode-return-validation.json` と最新checkpointを参照してください。残る同フレームの終了再入／別モード置換のCPU raw差分2件と、全効果・全変種の接続を続けます。通常画面CPU・全変種認証0/203体を維持します。

## 2026-10-20 Windows再確認・武器変更と再突入の証跡

固定版 `76e0c08` の既存共通実行器を再確認しました。Metal／CUDA1131正例・206拒否、portable単体127件が成功し、全入力・全出力・status・既存CPU参照はv45と一致しました。Windowsは低優先度の1回、65.348秒、120秒上限内で、元の作業状態とサービスを保持、検証プロセス0、報告も終了しています。武器変更・散弾・再突入の23fixtureを再監査し、再突入など7件を追加でCPU controllerの全比較フィールドへ照合しました。実装・定義・fixtureは従来どおり両GPUで共通です。

追加の未補正CPU observer調査では、旧武器変更8件中7件に残弾・発数・待機時計の差分があり、既知の契約差分1件と未調査6件を区別して記録しました。CPU完全一致や全キャラ認証とは扱いません。[再現方法・比較範囲・差分](portable-weapon-burst-recheck.md)、`research/portable-weapon-burst-recheck.json` とWindows v46 receiptを参照してください。通常画面CPU・全変種認証0/203体を維持します。

## 2026-10-20 名前付き持続時間延長と独立した敵状態

固定ソース `b0f1cf3`、ABI `0x50455660` でMetal／CUDA1131正例・206拒否が成功しました。名前付き持続時間延長39ケースを実CPUの対象・期限・時計・世代と照合しています。単体127件・CPU周期処理15件、29候補の通常／SR15の58実編成、203武器・203装備・固定8編成、API追加4件、数値34874件・実証4件も成功しました。旧1092ケースの全クエリと1028ケースの全読み戻しを保持しています。敵64ケースはresidentの分離・世代表示・実際のフレーム深度の変化を明示し、58実編成の既存の全項目とCPU参照も維持しました。

共有味方／DoTは一致した対象が一部でも共有期限を変えます。敵のバフは対象ごとに期限・スタック・世代を持ち、発動時の順序と世代を固定して子通知の終了後に次の受領者へ進みます。有限の1e30、無期限、再付与による期限種別の変化、正負のオーバーフローを区別し、内部はsoftware binary64の∞を保持します。stride77824／90112ワードとresident容量512を維持し、追加の私有配列は作りません。

基準版の全16ゲートとWindows転送終了後、対象1体でHP通知pending/dirtyがない場合だけ追加フレームを省く候補を測定しました。1131正例は実際の最大フレーム深度1ワードだけを別管理し、ほかの全出力ワードが一致しました。固定256入力×60回発動でGPU中央値26.642→24.351ms（約8.6%短縮）。3体は範囲が重なり明確な差を示しません。採用後も全16ゲートを再確認しています。

Windowsは基準版・最適化版を各1回、低優先度・120秒上限で67.483秒／65.985秒で実行しました。最適化版は最大フレーム深度も含め全出力・入力・status・CPU参照・正規化生成コードが一致しました。元の作業状態とサービスを保持し、残存検証プロセス0です。末尾7分割は保存済みの再送だけで、GPU再実行はありません。[契約・数値・測定範囲](portable-duration-extend.md)、`research/portable-duration-extend-validation.json` と最新checkpointを参照してください。通常画面CPU・全変種認証0/203体を維持し、残るライフサイクル・世界・効果群の接続を続けます。

## 2026-10-20 対象別除去・定義入力ビューの両GPU検証

固定ソース `9047790`、ABI `0x50455659` でMetal／CUDAの1092正例・195拒否が成功しました。対象別除去の28件と武器87件を実CPU参照と照合し、同名の旧1059ケースと58実編成の全読み戻し・CPU参照を保持しました。単体118件、29候補の通常／SR15の58実編成、203武器・203装備・固定8編成・API追加4件、数値34874件・実証4件も成功しています。旧期待を直した4件は名前と履歴を残し、変更武器のreload、チャージ待機時計、明示フレームの入力条件を整えました。

私有の256定義配列を廃止し、同じ共通入力wireのビューへ接続しました。大きなレコードはout引数、単項目参照は直接読み、入力検査76行を内容・順序を保って共通GPU関数へ分離しました。初期化と読み戻しの関数境界も明示した候補で全体コンパイルが成功しています。複数の変更を含むため、単一の原因を断定しません。strideは77824／90112ワードのままです。

Windowsは低優先度・120秒上限で1回、65.478秒で終了し、本体と55項目×1024行のcodecが成功しました。全入力・出力・status・CPU参照リスト・正規化生成コードが一致し、元の作業状態・サービスを保持、残存検証プロセス0です。全22分割の転送とMacの全15ゲート終了後に、比較版の1092正例の全出力ワード一致を確認しました。続く順次測定は256定義×32入力の名前付き除去で、全定義参照62.286→直接参照60.306ms（中央値、約3.2%短縮）です。比較範囲は新しい入力ビュー内の参照方法に限ります。私有テーブル63488バイトの保存を避けますが、ピークGPUメモリの実測値ではありません。

[契約・診断・測定範囲](portable-removal.md)、`research/portable-removal-validation.json` と最新checkpointを参照してください。全キャラ・全特殊効果の目標は継続中で、通常画面CPU・全変種認証0/203体です。残るライフサイクル・世界・効果群の接続を続けます。

## 2026-10-19 時点の未完了チェックポイント：対象別除去とコンパイラー障害

ABI `0x50455659` の作業版です。名前付き状態の対象別除去・最後の対象の終了通知・敵別の通知数を共通Slangへ接続し、独立した武器変更と周期instantを誤って止めていた旧期待4件を実CPU参照で修正しました。単体117件、29の除去fixture（28のCPU除去参照と発数寿命1件）、全1287入力のバイト列維持を確認しています。定義監査の未対応ライフサイクルは93→84件、入力候補は29体のままです。

**全体カーネルのMetal検証は未完了です。** 5候補ともGPU実行前のAppleコンパイラー内でLLVMのメモリ確保失敗となりました。本体と同じGPU所有の終了通知キュー関数を単独で実行する検査はApple M5で成功し、4096件格納・4097件目の拒否・16bitの両側を確認しましたが、全体実行器の認証へ読み替えません。Windowsの新しい検証と効率測定はまだ実行していません。

次は大きな私有定義配列と生成コードのライブ範囲を調べ、全体カーネルのコンパイルを解決します。[契約・診断・残作業](portable-removal.md)、`research/portable-removal-work-in-progress.json` を参照してください。最後の完全な両GPU認証は固定ソース `70f9018`、証跡コミット `272ed61` です。旧Metal報告は `research/portable-combat-v41-metal.json`、旧checkpointは `research/portable-combat-v41-checkpoint.json` に保持しています。通常画面CPU・全変種認証0/203体を維持します。


## 2026-10-19 着弾記録の共通圧縮と効率確認

固定ソース `70f9018`、ABI `0x50455658` で着弾記録を12→8ワードに圧縮しました。2048件の容量とbinary64の量・時刻を維持し、出力を98304→90112ワードへ削減しました。実際の出力バッファで1プログラム32KiB、約8.3%減です。同じ物理処理の12ワード制御版と、全1247入力の全出力ワード（使用済み着弾記録を含む）が表現の正規化後に一致しました。259境界正例・11拒否、未排出キューの読み戻しも成功しています。

Metal／CUDA1063正例・184拒否、単体106件・CPU周期処理15件、58実編成・203武器・203装備・固定8編成・API・数値34874件・実証4件が成功しました。旧1063ケースと58実編成の全読み戻し項目・CPU参照も保持しています。Windowsは低優先度・120秒上限で境界と本体だけを1回のラッパー、79.495秒で実行し、全入力・出力・status・CPU参照リスト・正規化生成コードが一致、残存検証プロセス0です。保存済み21分割の転送も終了しています。

全検証とWindows転送終了後の順次測定は、2着弾×64プログラムでGPU中央値8.661→8.470ms（約2.2%短縮）、2048着弾×16で23.377→23.202ms（約0.75%短縮）でした。後者は標本範囲が重なり、明確な速度改善とは扱いません。限定負荷で、デスクトップGPU活動は除外できません。[配置・測定範囲](portable-landing-compact.md)、`research/portable-landing-compact-validation.json` を参照してください。全変種認証0/203体・通常画面CPUは継続し、残る効果ライフサイクル・対象・世界モデルを共通実行器へ接続します。


## 2026-10-19 共通着弾キュー・吸血とWindows再検証

共通Slangの着弾キューに通常弾・スキル・周期／段階DoT・B3保留の回復を接続しました。発動時に量を捕捉し、次フレームの排出・排出中の子通知・回復で追加された次のB3保留を保持します。以前のHP150対CPU250の差は解消しました。ABI `0x50455657`、固定ソース `431d699` です。以下の通常弾試作は過去の記録です。

武器変更・散弾・バースト再突入を含むMetal／CUDA1063正例・184拒否、単体106件・CPU周期処理15件が成功しました。Windowsは低優先度・120秒上限で1回、80.582秒で終了し、全入力・出力・status・CPU参照リスト・正規化生成コードが一致しました。元のWindows作業状態とサービスを保持し、残存検証プロセス0です。検証と保存済み20分割の転送は終了しています。

定義監査候補は29体、通常／SR15の58実編成条件がCPU本体と一致しました。203武器・203装備・固定8編成・HTTP着弾追加4件・数値34874件・Metal実証4件も成功しています。旧1028正例と52実編成の既存読み戻し項目も維持しました。[着弾契約と残る範囲](portable-landings.md)、`research/portable-landings-validation.json` と最新checkpointを参照してください。今回の着弾記録は2048×12ワードで、圧縮・効率測定は次の作業です。世界・ライフサイクル・残る効果と全変種の認証は未完了で、通常画面CPU・全変種認証0/203体を維持します。


## 過去の記録：2026-10-19 吸血の通常弾試作と着弾順の未接続

吸血回復の共通binary64処理と、通常弾の射撃通知後の回復経路を試作しました。Apple M5で15ケースが元CPUの吸血関数・CharStateと一致し、既存1028正例・176拒否の全入力／出力バイトも維持しました。単体101件が成功しています。

吸血ファミリー全体は未完了です。実CPUタイムラインで通常弾＋攻撃時スキル2ヒットを実行すると総ダメージ3000・最終HP250ですが、現GPU試作は同じダメージでHP150です。スキルの次フレーム着弾時の回復が未接続で、公開ホスト受付は閉じています。差を `passed: false` のまま記録し、次は共通着弾キューへ接続します。[契約と残る実装](portable-lifesteal.md)、`research/portable-lifesteal-work-in-progress.json` を参照してください。この試作でWindowsは使っていません。以下の両GPU認証は以前の固定版 `21e03a0` の安定記録です。通常画面CPU・全変種認証0/203体という未完了範囲は維持しています。

## 2026-10-19 段階選択の索引と効率検証

段階適用を持つ定義だけを選ぶ静的索引を共通Slangへ接続しました。ABI `0x50455656`、既存余白の257ワードを使い、入出力stride・Runtimeの私有状態は増やしていません。最大254段階キャリアと不正索引5件を含むMetal／CUDA1028正例・176拒否、全走査版との全出力バイト一致、単体94件・CPU周期処理15件が成功しました。旧1027ケースと52実編成の全読み戻しも維持しています。

Windowsは固定版 `21e03a0` を低優先度・120秒上限で1回、66.976秒で成功しました。全入力・出力・status・全CPU参照リスト・正規化生成コードが一致し、元の作業状態・サービスを保持、残存検証プロセス0です。接続断後は保存済みの最後の1分割だけを再送し、GPUは再実行していません。52実編成・203武器・203装備・固定8編成・API追加4件・数値34874件・実証4件も成功しています。全検証と転送終了後の順次測定は、256定義でGPU中央値1036.069→1022.829ms（約1.3%短縮）。33定義は範囲が重なり明確な速度改善を示しません。限定負荷の結果であり、デスクトップGPU活動は除外できません。[設計・測定範囲](portable-staged-index.md)と `research/portable-staged-index-validation.json` を参照してください。通常画面CPU・全変種認証0/203体を維持し、世界・効果ライフサイクル・残る全キャラの接続を続けます。

## 2026-10-19 Windows再確認と段階適用

武器変更・散弾・バースト再突入を含む共通回帰をWindowsでも再確認しました。固定版 `8bc3c97` のRTX 3070 Tiは低優先度・120秒上限の1回、68.935秒で1027正例・171拒否が成功し、Metalと入力・全出力・全status・全CPU参照リスト・正規化生成コードが一致しました。元のWindows作業状態とサービスを保持し、残存検証プロセス0です。

same-targetの段階DoTを共通Slangへ追加しました。23ケース、登録世代・0〜64回・固定ダメージ用スタック・遅延フレーム・資源参照時刻を検証しました。単体93件とCPU周期処理15件、52実編成・203武器・203装備・固定8編成・API追加4件・数値34874件・実証4件が成功しています。旧1004ケースと52実編成の全状態も新しい空のフィールドを除いて維持しました。ABI `0x50455655`、配置strideの増加なしです。[規約と残る範囲](portable-staged.md)、`research/portable-staged-validation.json` と最新checkpointを参照してください。段階予定の選択は全走査で、高速化の測定は次段階です。通常画面CPU・全変種認証0/203体、全キャラ・全特殊効果の目標は未完了です。

## 2026-10-19 所有者付き周期資源とfeather

所有者付き周期資源とfeatherを共通Slangへ接続しました。寿命・生存数・人口依存の周期・登録順・子通知での再召喚、命中数／buff倍率／最大HPの参照をGPUが管理します。ABI `0x50455654`、追加29件を含むMetal／CUDA1004正例・159拒否、常時計数版との全出力一致、単体87件、52実編成・203武器・203装備・固定8編成・HTTP追加4件が成功しました。起動アダプターのstride変更後に数値34,874件・実証4件も実GPUで再検証しています。Windowsは固定版 `924279e` を低優先度で1回、71.189秒で実行し、全出力・全参照リストと正規化した生成コードが一致しました。既存975ケース・52実編成の状態は2つの空の新フィールドを除いて一致し、計数省略前の27ケースも同じ読み戻しを保持しました。同一時刻・再召喚世代で生存数を再利用する固定負荷は、全出力を保ってGPU中央値400.521→376.461ms、約6.0%短縮しました。[配置・数値規約・順序・測定範囲](portable-sources.md)を参照してください。全変種認証0/203体・通常画面CPUは維持し、same-target ramp・世界・残る全効果の接続を続けます。

## 2026-10-19 外部参照倍率と最大HP境界

外部参照buff倍率とDoT係数、保持／更新の順序、最大HPとHP率の境界同期を共通Slangへ接続しました。ABI `0x50455653`、追加40件を含むMetal／CUDA975正例・142拒否、毎回探索版との全出力一致、単体80件、52実編成・203武器・203装備・固定8編成・HTTP追加4件が成功しました。Windowsは固定版 `1f06043` を低優先度で1回、64.408秒で実行し、全出力・全参照リストと正規化した生成コードが一致しました。既存935ケース・52実編成の状態は、新しい参照保持値の空欄追加を除いて一致しています。CPUの自己参照名キャッシュと、最大HP参照変更後の古いHP率を互換層で修正し、pinnedソースは保持しています。探索省略の固定負荷は全出力を保って中央値24.653→24.357ms、約1.2%短縮しましたが、3標本の範囲が重なり、明確な速度向上とは扱いません。[数値規約・順序・検証範囲](portable-reference-scales.md)を参照してください。全変種認証0/203体・通常画面CPUを維持し、feather・世界・残る全効果へ接続を続けます。

現在の確認範囲と未完了項目は[共通実行器の進捗](portable-combat-runtime.md)と `research/portable-combat-checkpoint.json` を参照してください。以下は移行開始時の手順・経緯を含み、共通Metal本体の全キャラ対応完了を示す文書ではありません。

## 2026-10-19 大容量モード・無消費バフと補充の文脈

`max_ammo=-1` の999,999発モードと、弾を消費しない `infinite_ammo` バフを共通実行器で区別しました。射撃中／外の補充上限、チャージ途中の弾薬除去、装填取消の射撃時計、発数寿命・終了通知の子効果まで接続しています。ABI `0x50455648`、Metal649正例・69拒否、弾薬96件（追加45件）のCPU参照、単体40、HTTP API、固定8実編成と全17候補の34実編成が成功しました。203武器・203部隊の装備初期化も成功しています。[数値・文脈・実体索引・残る差異](portable-infinite-ammo.md)を参照してください。固定版 `83d9df3` はWindowsのRTX 3070 Tiでも低優先度・1回、35.580秒で649正例・69拒否が成功しました。共通ソース・入力・全出力・検証コード・全status・全CPU参照リストがMetalと一致し、生成CUDA/MSLも改行・位置情報・標準includeパスだけの正規化で一致しました。元のWindows作業状態を保持し、残存プロセス0です。無消費フラグの索引は、他の本チャットの検証を終えた単独の固定負荷でGPU時間中央値6.886秒→5.891秒、約14.5%短縮し、参照版と全出力が一致しました。同一フレームの失効→子モードでは既存のfresh-session期待値と元CPUの残弾引継ぎに未解決差があり、全変種認証0/203体・通常画面CPUを維持します。前段の両GPU一致は `research/portable-combat-v23-checkpoint.json` に保存しました。

## 2026-10-19 弾薬即時操作と名前付きイベント

割合補充・固定発数の増減、符号付き残弾、装填取消、変更武器の上限を共通Slangへ接続しました。割合の偶数丸め・固定発数の切捨て・負残弾からの部分装填・空の対象・子イベントを、元CPUハンドラーと照合します。進入前に参照した変更武器の上限は、実際の進入時に再計算する境界も追加しました。ABI `0x50455647`、Metalの604正例・69拒否と弾薬51件のCPU参照、単体38件が成功しています。ノワールを含む全17入力候補の通常／SR15・180秒、34実編成は修正版でもCPU本体と一致し、固定8条件・HTTP API・203武器・203部隊の装備初期化も成功しました。名前付きイベント処理の固定負荷は、他の検証終了後の単独測定で533.706ms→97.283ms、約81.8%短縮し全出力が一致しました。固定版 `a5822ad` はWindowsのRTX 3070 Tiでも低優先度・1回、32.740秒で604正例・69拒否が成功しました。共通ソース・入力・全出力・検証コード・全status・全CPU参照リストがMetalと一致し、生成CUDA/MSLも改行・位置情報・標準includeパスだけの正規化で一致しました。元のWindows作業状態を保持し、残存プロセス0です。[順序・丸め・数値範囲・残る範囲](portable-ammo-instants.md)を参照してください。全変種認証0/203体・通常画面CPUは未完了です。前段の両GPU一致は `research/portable-combat-v22-checkpoint.json` に保存しました。

## 2026-10-19 フルバースト期間と全入力候補の実編成

共通実行器に期間効果の加算・短縮・最短1秒・最終B3発動者と鮮度・source別重複を接続しました。開始通知より先に期間を固定し、再突入・発動回数条件もCPU本体の順序に合わせます。ABI `0x50455646`、Metalで553正例・62拒否、期間30件のCPU controller参照が成功しました。武器変更・散弾・再突入を含む既存回帰を維持しています。入力監査を通る全16候補について、全効果を含む通常／SR15育成180秒の32条件がCPU本体と一致しました。固定8条件とHTTP APIも成功しています。`trace='burst'` で計算を保ち全バースト時刻を照合し、512着弾でsummaryとの計算一致を確認します。[順序・境界・検証範囲](portable-burst-duration.md)を参照してください。固定版 `4342fe1` はWindowsのRTX 3070 Tiでも低優先度・1回、30.447秒で553正例・62拒否が成功しました。共通ソース・入力・全出力・検証コード・全status・全CPU参照リストがMetalと一致し、生成CUDA/MSLも改行・位置情報・標準includeパスだけの正規化で一致しました。元のWindows作業状態を保持し、残存プロセス0です。全変種認証0/203体・通常画面CPUは未完了です。前段の両GPU一致は `research/portable-combat-v21-checkpoint.json`、最新証跡は `research/portable-combat-checkpoint.json` です。

## 2026-10-19 B3予約ダメージとブリッド実編成

元のB3属性、予約時の条件・係数、後続の同発動者バフの除外、フルバースト開始後の計算・着弾を共通Slangへ接続しました。ABI `0x50455645`、522正例・51拒否と予約27件のCPU controller参照をMetalで確認しています。512予約の保持とflush、名前付き親の静的反復、再突入・周期再登録を含みます。ブリッド編成を追加した実編成8条件は、全定義を含めCPU本体と一致しました。入力監査では実験用static adapterの存在と通常画面の未接続を区別します。全変種認証0/203体・通常画面CPUは未完了です。[順序・数値・効率化と残る範囲](portable-pending-burst.md)、固定版 `51fe398` はWindowsのRTX 3070 Tiでも低優先度・1回、29.728秒で522正例・51拒否が成功しました。共通ソース・入力・全出力・検証コード・全status・全CPU参照リストがMetalと一致し、生成CUDA/MSLも改行・位置情報・標準includeパスだけの正規化で一致しました。元のWindows作業状態を保持し、残存プロセス0です。モデル混雑で中断した要約転送は既存ファイルから再開し、GPU計算を繰り返していません。 最新の照合は `research/portable-combat-checkpoint.json` を確認してください。前段495正例の両GPU一致は `portable-combat-v20-checkpoint.json` に保存しました。


## 2026-10-19 遮蔽物HPとSR15実編成

遮蔽物HPの加算率・発動者最大HP基準、通常回復・復活、残り比率による対象選択、生存条件と命中／回復通知を共通Slangへ接続しました。ABI `0x50455644`、495正例・41拒否と遮蔽物32件の独立CPU参照をMetalで確認しています。SR15育成を止めていた `cover_hp_pct` を省略せず計算する経路です。固定編成の3・30・180秒（71定義）とSR15育成180秒（91定義）は、遮蔽物状態も含めてCPU本体と4条件とも一致しました。通常画面・全変種認証0/203体は未完了です。[数値・状態・対象・残る範囲](portable-cover-runtime.md)、固定版 `78a59ee` はWindowsのRTX 3070 Tiでも低優先度・1回、27.698秒で495正例・41拒否が成功しました。共通ソース・入力・全出力・検証コード・全status・全CPU参照リストがMetalと一致し、生成CUDA/MSLも改行・位置情報・標準includeパスだけの正規化で一致しました。追加GPU実行はなく、元のWindows作業状態を維持し残存プロセス0です。 最新の照合は `research/portable-combat-checkpoint.json` を確認してください。前段463正例の両GPU一致は `portable-combat-v19-checkpoint.json` に保存しました。


## 2026-10-19 敵への分配と実編成入力

敵の対象順・複数ヒット・分配丸め、本体／ADD／過剰分の集計と、CPUと同じ加算時計を共通実行器へ接続しました。ABI `0x50455643`、Metalの463正例・36拒否、単体31件・API・34,874数値ケースが成功しています。武器変更・散弾・バースト再突入を含む共通回帰を維持しています。実B1/B2/B3編成の全71定義で3・30・180秒のCPU本体と一致しましたが、SR15育成は遮蔽物HPで拒否され、必須4条件の全体結果は未完了です。全変種を含む認証済み0/203体・通常画面CPUを維持します。[範囲・数値・残る課題](portable-enemy-damage.md)、WindowsのRTX 3070 Tiでも固定版 `372f85e` の499入力が26.841秒・低優先度の1回で成功し、ソース・入力・全出力・検証コード・全CPU参照が一致しました。証跡は `research/portable-combat-checkpoint.json` です。前段420正例の両GPU一致は `portable-combat-v18-checkpoint.json` に固定しました。


## 2026-10-19 バーストの短縮と共有ゲージ

クールダウンの使用時短縮・開始時の追加反映・待機再計算と、共有ゲージの即時加算を共通実行器へ接続しました。ABI `0x50455642`、追加31件の独立CPU参照、既存の武器変更・再突入との組み合わせを検証しています。[参照順・数値・残る範囲](portable-burst-resources.md)を確認してください。固定版 `ac5378d` はMetalの420正例・22拒否とWindowsのRTX 3070 Tiでも93.551秒・低優先度の1回で成功し、共通ソース・入力・全出力・検証コード・status・全CPU参照リストが一致しました。単体29・API・旧16＋2・203武器・203装備初期化も成功し、同じ全出力の固定負荷ではGPU中央値が132.321msから89.509msへ約32.4%短縮しました。最新証跡は `research/portable-combat-checkpoint.json`、前段389正例の両GPU一致は `portable-combat-v17-checkpoint.json` に保存しています。実定義の入力preflightは7体ですが、全効果込みの実編成GPU検証は0/203体です。

## 2026-10-19 受領者別の発数寿命

発数制バフの受領者別消費・再付与・stack、遅延対象、終了通知を共通実行器へ接続しました。ABI `0x50455641`、Metalの389正例・19拒否、発数寿命33件の独立CPU参照が成功しています。[消費順序・CPUとの差異・効率化](portable-bullet-runtime.md)を確認してください。固定版 `d8d0d79` はWindowsのRTX 3070 Tiでも通常条件・低優先度の1回、95.711秒で成功し、共通ソース・入力・全出力・検証コード・status・全CPU参照リストがMetalと一致しました。診断トレース付きの先行実行は120秒で打ち切り、失敗記録も保持しています。照合は `research/portable-combat-checkpoint.json`、前段353正例の両GPU一致は `portable-combat-v16-checkpoint.json` に保存しています。実編成GPU検証は0/203体、通常画面と全効果の接続は未完了です。

## 2026-10-19 遅延対象と共有スナップショット

順位指定の持続バフを最初の参照でGPU解決し、同じ発動者・時刻・生の対象指定の効果が結果を共有する経路を接続しました。ABI `0x50455640`、共有結果1,024枠。Metalの353正例・16拒否、追加26件の独立CPU参照、単体27・API・旧16＋2・203武器・203装備初期化が成功しています。GPU生成の1,201射撃で再利用しつつ、遅れて参照する回復効果の古い結果も保持しました。[解決順・数値差異・キャッシュと残る範囲](portable-lazy-runtime.md)を確認してください。同じ全出力を保つ固定負荷でGPU中央値を468.414msから288.114msへ短縮しています。本体性能の証明ではありません。固定版 `053faba` はWindowsのRTX 3070 Tiでも低優先度・1回、73.697秒で成功しました。353正例・16拒否の共通ソース・入力・全出力・検証コード・status、遅延対象を含むCPU参照はMetalと一致し、元のWindows作業状態を保持しています。Windows照合の記録は `research/portable-combat-checkpoint.json`、前段325正例の両GPU一致は `portable-combat-v15-checkpoint.json` に固定しています。実定義の入力preflightは6体ですが、全効果込みの実編成GPU検証は0/203体です。発数寿命・残る効果・実編成と通常画面への接続を続けます。

## 2026-10-19 定義と複数の効果実体

定義ごとの発動予算・時計から、対象／stack／期限／HP snapshotを持つ実体を分離しました。ABI `0x5045563F`、256定義・512実体、入力49,152語・出力32,768語です。持続バフの発動時状態・バースト対象、同名統合の規約、全発動者の名前付き削除と終了通知を接続し、Metalの325正例・12拒否、追加15件の独立CPU参照、API・単体27・203武器・203装備初期化が成功しています。[実体・通知・効率化と残る範囲](portable-carrier-runtime.md)を確認してください。全出力を保つ固定の実体探索負荷ではGPU中央値が870.332msから129.458msへ短縮しました。本体性能の証明ではありません。固定版 `7b86f88` はWindowsのRTX 3070 Tiでも低優先度・1回、67.788秒で成功しました。325正例・12拒否の共通ソース・入力・全出力・検証コード・status、実体を含むCPU参照はMetalと一致し、元のWindows作業状態を保持しています。Windows照合の記録は `research/portable-combat-checkpoint.json`、前段307正例の両GPU一致は `portable-combat-v14-checkpoint.json` に固定しています。遅延対象・発数寿命・残る効果・実編成／通常画面は未接続で、全効果込みの実編成GPU検証済みは0/203体です。

## 2026-10-19 味方対象選択と即時効果

共通Slangへ静的な武器種／属性／クラス／配置フィルターと、即時回復・HP減少の現在HP／攻撃力順位・バースト状態による対象選択を接続しました。順序と発動予算を含むMetalの307正例・11拒否条件、追加32件の独立CPU参照、単体27件が成功しています。ABIは `0x5045563E`、入力49,152語・出力28,672語です。固定版 `91303cc` はWindowsのRTX 3070 Tiでも、低優先度・1回、63.042秒で成功しました。307正例・11拒否の共通ソース・入力・全出力・検証コード・statusとCPU参照はMetalと一致し、元のWindows作業状態を保持しています。Windows照合の記録は `research/portable-combat-checkpoint.json`、前段271正例の両GPU一致は `portable-combat-v13-checkpoint.json` に固定しています。[対象選択の規約と未接続範囲](portable-recipient-runtime.md)を確認してください。対象が変わる持続バフ・一般の複数効果実体は受付を広げておらず、実編成のGPU検証済みは0/203体、通常画面と全効果への接続は未完了です。

## 2026-10-19 256定義と実装備の入力

共通定義容量を256へ拡張し、強制スキル・時計を8語maskへ接続しました。ABIは `0x5045563D`、入力45,056語・出力28,672語です。Metalの271正例・9拒否、API、単体24件、旧イベントと203武器の回帰が成功しました。通常の所持・育成準備から、203部隊の45装備定義を初期化する実Metal経路も追加しました。[wire・実データ段階・残る複数キャリアの制約](portable-capacity-runtime.md)を確認してください。固定版 `e1960cd` はWindowsのRTX 3070 Tiでも低優先度・1回、63.396秒で成功しました。271正例・9拒否の共通ソース・入力・全出力・検証コード・statusとCPU参照がMetalと一致し、元のWindows作業状態を保持しています。最新記録は `research/portable-combat-checkpoint.json`、前段258ケースの両GPU一致は `portable-combat-v12-checkpoint.json` です。実編成・通常画面・全キャラ対応は未完了で、実編成の検証済みは0体です。

## 2026-10-19 体力層への被弾とダウン

共通実行器へ攻撃力・係数・明示対象からの体力層ダメージ、無敵／不屈・致死通知、受領者単位のダウン片付けを追加しました。ABIは `0x5045563C`、単一バッチ上限512。Metalの258正例・8拒否、HPのCPU参照69ケース、API、単体22件、203体の武器回帰が成功しています。[体力層の規約・効率化・未接続範囲](portable-incoming-runtime.md)を確認してください。固定版 `e014b1b` はWindowsのRTX 3070 Tiでも低優先度・1回、50.340秒で成功しました。258正例・8拒否の共通ソース・入力・全出力・検証コード・statusと既知CPU差異がMetalと一致し、元のWindows作業状態を保持しています。最新記録は `research/portable-combat-checkpoint.json`、前段230ケースの両GPU一致は `portable-combat-v11-checkpoint.json` です。保護層・敵攻撃のスケジュール／照準・復活・実編成は未接続で、実編成のGPU検証済みは0体です。

## 2026-10-19 HP通過通知と同期順

共通実行器へ本人・部隊・隣接者のHP通過／満タン復帰通知、通算回数、同キーの重複除去、子によるHP再変化の抑制を追加しました。ABIは `0x5045563B`。Metalの230正例・7拒否、HP43ケースの独立CPU参照（失効時の既知差異2件を明示）、API、単体21件、203体の武器回帰が成功しました。[通知の数値規約・効率化・残る範囲](portable-health-runtime.md)を確認してください。固定版 `a55ab81` はWindowsのRTX 3070 Tiでも低優先度・1回、47.298秒で成功しました。230正例・7拒否の共通ソース・入力・全出力・検証コード・statusと既知CPU差異がMetalと一致し、元のWindows作業状態を保持しています。最新記録は `research/portable-combat-checkpoint.json`、前段212ケースの両GPU一致は `portable-combat-v10-checkpoint.json` に固定しました。実編成のGPU検証済みは0体、全キャラ・通常画面への接続は未完了です。

## 2026-10-19 味方HP・防御・回復

共通Slangへ味方の初期HP／防御、最大HP・スナップショット、回復倍率・回復通知と子の順序、HP条件を接続しました。ABIは `0x5045563A`。Metalの212正例・7拒否、25ケースの独立CPU参照（HP失効時の既知差異1件を明示）、API、単体19件、203体の武器回帰が成功しています。[規約・効率化・未接続範囲](portable-health-runtime.md)を確認してください。固定版 `37c2e36` はWindowsのRTX 3070 Tiでも低優先度・1回の検証が76.388秒で成功しました。212正例・7拒否の共通ソース・入力・全出力・検証コード・statusと既知CPU差異がMetalと一致し、元のWindows作業状態を保持しています。最新記録は `research/portable-combat-checkpoint.json`、前段187ケースの両GPU一致は `portable-combat-v9-checkpoint.json` へ固定しました。実編成・通常画面・全キャラ対応は未完了です。

## 2026-10-19 チャージ後の自動補充と全203武器

チャージ射撃後の補充予約・完了通知・モード変更時の破棄を共通実行器へ接続しました。ABIは `0x50455639`。Metalの187正例・5拒否、新しい12ケースの独立CPU参照、単体18件を確認しています。全203体の実武器データは効果を除く3秒間のMetal実行で射撃数・残弾・ダメージを照合し、入力preflightも203体です。[動作規約・効率化・未接続範囲](portable-weapon-runtime.md)を確認してください。固定版 `082509d` はWindowsでも低優先度で1回だけ検証し、187正例・5拒否が37.235秒で成功しました。共通ソース・入力・全出力・検証コードのハッシュと全statusがMetalと一致し、元のWindows作業状態を保持しています。最新記録は `research/portable-combat-checkpoint.json`、前段169ケースの両GPU一致は `portable-combat-v8-checkpoint.json` へ固定しました。実編成のGPU検証済み0体・通常画面・全特殊効果の接続は未完了です。

## 2026-10-19 ソース別の弾数・チャージ時間

共通実行器へ弾数／チャージ時間のソース別丸め、有限モードの弾倉、速度免疫、固定時間、超過分のダメージ変換を接続しました。ABIは `0x50455638`、Metalの169正例・5拒否と単体18件が成功しています。独立CPUの武器／量補正63ケースには、同名装備成分の早期統合に関する既知差異1件を明示して検証しています。[量補正の数値規約と検証](portable-quantity-runtime.md)を参照してください。固定版 `132461d` はWindowsのRTX 3070 Tiでも低優先度で1回だけ実行し、169正例・5拒否が36.299秒で成功しました。共通ソース・入力・全出力・検証コードのハッシュはMetalと一致し、元の作業状態を保持しています。最新照合記録は `research/portable-combat-checkpoint.json`、前段130ケースの両GPU一致は `portable-combat-v7-checkpoint.json` に保持しています。実編成のGPU検証済みは0体、通常画面と全キャラ・全特殊効果の接続は未完了です。

## 2026-10-19 ウォームアップ・拡散・分割装填

自動連射のウォームアップと冷却、可変拡散と精度、分割装填・装填後遅延、チャージ周期下限を共通実行器へ追加しました。Metalの130正例・3拒否、新しい24ケースの独立CPU武器比較、単体17件が成功しています。powは正確な比率が同じときだけ再利用し、状態・子通知を省かず評価回数を減らしています。[共通武器処理](portable-weapon-runtime.md)を確認してください。

実カタログではCPU戦闘を実行せず131体の武器入力を正規化・梱包できました。72体は未接続のチャージ後のカバー／自動装填を理由に拒否しています。全効果込みの実編成GPU検証は0体のままで、通常画面・全キャラ対応は未完了です。現在のABIは `0x50455637`。 固定版 `14f7bed` はWindowsのRTX 3070 Tiでも130正例・3拒否が21.204秒の低優先度1回で成功し、共通ソース・入力・出力・検証コードのハッシュがMetalと完全一致しました。元のWindows作業ツリーとHEADは保持しています。前段 `859aa65` の106正例・3拒否はWindowsでも17.948秒の低優先度1回で成功し、共通ソース・入力・出力・検証コードのハッシュがMetalと一致しました。その固定記録は `portable-combat-v6-checkpoint.json`、最新版は `portable-combat-checkpoint.json` です。

## 2026-10-19 単発ダメージ式と登録順集計

通常／スキル別の補正、ダメージ種別、基本チャージ倍率と加算・倍率補正、適正距離と属性を共通Slangへ接続しました。Metalは従来69ケースと新しい37ケース、拒否3ケースが成功しています。新規37ケースは手書き期待値とCPUの単発式にも一致し、登録順の1ケースは独立BuffManagerの状態でも確認しています。ABIは `0x50455636` です。CUDAの最新照合状態は `research/portable-combat-checkpoint.json` を参照してください。前段69ケースの両GPU一致は `portable-combat-v5-checkpoint.json` に固定しています。

登録順の保持と単回集計により、同一入力・出力を使う固定測定でGPU時間中央値が19.86msから14.60msへ短縮しました。本体全体の速度・全キャラ対応の証明ではありません。計算順、検証方法と未対応範囲は[共通ダメージ処理](portable-damage-runtime.md)へまとめています。実編成・通常画面・全特殊効果は引き続き未完了です。

## 2026-10-19 共通通知・条件とWindows再確認

共通Slangへ1効果あたり最大8通知・3条件、通知ごとのカウンター、同期した名前付き終了／スタック到達、passiveと周期時計を接続しました。武器変更・散弾・バースト再突入を含む従来53ケースに、16ケースを追加し、Metalで69正例・3拒否を確認しています。外部通知の14ケースは独立CPU参照とも照合しました。現在のABIは `0x50455635`、入力8,192語・出力16,384語です。WindowsのRTX 3070 Tiでも同じ固定版 `cfff376` を低優先度で1回だけ実行し、69正例・3拒否が13.193秒で成功しました。共通ソース・入力・出力・検証コードのハッシュはMetalと完全一致です。元のWindows作業ツリーとHEADは保持しています。照合記録は `research/portable-combat-checkpoint.json`、正確なWindows要約は `windows-portable-combat-v5.json` です。

Metalのコンパイル時間増大に対し、共通ソースの主要な関数へ `noinline` を付け、生成されたCUDAにも `__noinline__` が出ることを確認しました。Metalアダプターにはライブラリー生成・パイプライン生成・GPU投入の診断を追加しています。通常画面の実編成経路、全キャラ・全特殊効果のGPU対応は未完了です。

## 2026-10-19 GPU内フレーム進行と203体の監査

GPU内で1/60秒のフレームを生成し、180秒まで進める経路を接続しました。分割／一括の状態一致、明示フレームとの一致、長時間DOTとバーストを含め、53正例と3拒否例をMetalで検証しています。APIからの180秒進行も確認し、ABIは `0x50455634` です。この変更後のCUDA実機検証はまだ行っていません。前段43ケースの両GPU一致はABI v3の記録として保存しています。

203体の実定義を通常の育成準備から監査した記録は `research/portable-catalog-readiness.json`、全体の完了条件は `docs/portable-roadmap.md` です。実編成のGPU検証済みは0体で、通常画面・全キャラ・全特殊効果への接続と効率化は未完了です。次はpassive／周期通知、条件、残りの数値式と武器処理、実編成アダプターを進めます。

## 2026-10-19 武器変更・散弾・バースト再突入

共通実行器へ武器変更の時間／発射数／トグル終了と子からの再入、ペレット／銃口と実弾の分離、段階A・段階上書き・バースト再突入を接続しました。共通43ケースと拒否2ケースをMetalで検証しています。ABIは `0x50455633`、通常画面・全キャラ受付は未接続です。追加後の `5985f82` もWindowsで1回だけ検証し、43正例＋拒否2が105.337秒で完了しました。Metalと共通Slang・入力・出力のハッシュが完全一致しています。最新記録は `research/portable-combat-checkpoint.json` です。詳細は[共通戦闘実行器](portable-combat-runtime.md)を確認してください。

ユーザー依頼で以前の確定版 `3c34171` をWindowsのRTX 3070 Tiで再確認し、20正例・2拒否の単一バッチが26.718秒で成功しました。Metalと共通ソース・入力・出力のハッシュが一致しています。旧版の固定した証跡は `research/portable-combat-v2-checkpoint.json` に保存しています。

## 2026-10-19 武器・バースト・敵対象の追加接続

共通実行器へ固定連射／自動フルチャージ、弾倉・装填・待ち、基本の1→2→3バースト、ゲージ／クールダウン、本体・追加の敵のHP／照準／出現世代を接続しました。新しい20ケースと拒否2ケースをApple M5で確認し、旧イベント16ケースと拒否2ケース、HTTP APIの新しい戦闘入力も検証しています。計算とfixtureはCUDA／Metalで共通です。[受付範囲・入力規約・未完了項目](portable-combat-runtime.md)を先に読んでください。通常画面と全キャラ受付はまだCPU／既存の境界のままです。今回のCUDA比較は120秒で停止し、未確認として保存しました。Windowsでは再実行せず、次回の負担を減らす単一バッチ化をMetalで確認しています。照合状況は `research/portable-combat-checkpoint.json` と `windows-portable-combat-timeout.json` を参照してください。

以下の数値・イベントの検証は以前の到達点の履歴です。旧ABIのCUDA／Metal照合記録はその実行時コミットを指します。今回のwireはABI `0x50455632` へ更新しています。

## 2026-10-19 共通実行器の追加更新

整数変換・floorと、コア命中確率のclampされたpowを共通Slangへ追加しました。数値34,874ケース、状態・イベント16ケース、再入／数値あふれの拒否2ケースをApple M5で確認しています。アプリの `POST /api/portable-events` から実Metalまで接続済みです。通常画面の自律戦闘と全キャラ対応は未完了で、GPUの標準受付は増やしていません。[共通実行器の範囲と検証手順](portable-event-runtime.md)と[更新した数値規約](portable-numerics.md)を先に確認してください。WindowsのRTX 3070 Tiで短いCUDA検証を実施し、数値5,178ケース・状態14ケース・拒否2ケースが成功しました。GPUソース・入力・出力のハッシュがMetalと一致しています。Windowsの元の作業フォルダーと本体は変更せず、フルビルドや常時テストは行っていません。来歴は `research/portable-cross-gpu-checkpoint.json` を参照してください。

## 2026-10-19 Mac実機の初回記録（上記の追加更新より前）

- このMacの作業ブランチは `codex/mac-metal`、開始点は `origin/codex/mac-portability` の `61a43e9` です。以下のWindows時点の履歴は比較用として残します。
- M5・24GB・macOS 26.6.2 arm64、Python 3.12.15、Node 24.22.0でCPUカタログ203体を確認。元のMetal実証4/4ケースはApple M5のGPUで成功しました。
- binary64をuint64整数で計算する共通Slang候補を追加。四則演算・比較の14,034ケースがMetalでbit一致。CUDAは同じソースから生成までで、NVIDIAでの実行は未確認です。詳細と残作業は[数値規約](portable-numerics.md)を先に確認してください。
- SwiftはCommand Line Toolsで動作し、実証は実行時MSLコンパイルを使います。Xcode本体・オフラインmetalコンパイラーは未導入です。
- 添付セッションは画面へ取り込み、CPUを選択して15秒の5人部隊を再計算済み。元データとCPU用書き出しは `local-data/` 内だけに保存しています。再起動は `./Start-NikkeTools.command`。
- Nodeの既存テスト34件、Pythonの実証梱包1件・エンジン導入2件・時計3件を確認しました。
- 本体のMetal実行と全キャラ対応は未完了です。既存CUDA本体／ABI／定義は変更せず、Windows PCは使用していません。

## 作業の目的と現在の優先順位

最終目的は、NIKKEの所持・育成に基づく詳細計算、育成条件の探索、おすすめ部隊探索を支える全キャラ・全特殊効果のGPU対応です。新しいキャラ固有の分岐や同じテストの複製を増やさず、共通の効果・状態・イベント実行器へ接続します。CPUがゲーム仕様と異なる場合、その不具合へGPUを無理に合わせません。

現在は残りキャラのCUDA対応拡大に先立ち、CUDAとMacのMetalで計算本体・定義・テストを共用する設計を実証する段階です。共通GPUソースから両ターゲットへ出力し、バックエンド固有部分は起動・転送・メモリ配置・読み戻しに限定する方針です。Slangは候補であり、本体全体を移せるかと性能はまだ証明されていません。

最初に[移行手順](mac-migration.md)を実行してください。Macで本体のMetal計算が完成しているわけではありません。

## 環境と制約

- 主な開発環境：ユーザー申告のMacBook M5・24GB・macOS 26.6.2。Mac実機での初回確認はこれからです。
- 比較環境：Windows PC、RTX 3070 Ti（SM86）。既存のCUDAビルドはCUDA Toolkit 11.3のWindows NVRTCを使っています。
- Windows検証時のPythonは3.12.14、Nodeは24.19.0。MacもまずPython 3.12系・Node 24系で合わせます。
- Windows PCは常時起動してリモート利用可能ですが、他の作業への影響が出たことが移行理由です。編集・共通テスト・Metalの開発と測定はMacを主にします。
- Windowsで常時GPUテストや自動フルビルドを設定しません。CUDAに関係する差分のみ、必要な短いケースを明示的に実行します。大きなビルド、PTX初回JIT、長時間の性能測定は空き時間を確認します。CPUのプロセス優先度だけでGPU競合を解消できるとは扱いません。

## GitHubと保存範囲

- リポジトリ：`https://github.com/edommoner/nikke_tools`
- 作業ブランチ：`codex/mac-portability`
- Draft PR：`https://github.com/edommoner/nikke_tools/pull/1`。mainへは未マージです。
- 初回アップロード：`6f3f4f0`。最初のMac移行準備：`24e9d90`。この文書などの後続変更も同じブランチにあります。最新の状態はブランチHEADで確認してください。
- `research/upstream/`、`research/ports/`、`research/staging/`、CUDAキャッシュ、`.tools/`、`.venv/`、`local-data/`、認証情報はGit対象外です。
- 過去版の保存コピーはWindows側にあります。過去版を必要とする比較スクリプトは、GitHubからクローンしただけでは実行できないものがあります。必要な保存版だけ移すかWindows側を参照してください。
- 所持・育成・編成・計算履歴は画面の「保存・書き出し」でJSONへ保存して移します。セッションJSONは個人データとして扱い、Gitへ追加しません。Macで読み込んだ後は詳細計算をCPUへ選び直します。
- Macからコミット／pushするためのGitの名前・メール設定とGitHub認証はMac側で行います。公開リポジトリの取得とMetal実証だけなら書き込み認証は不要です。

## 確認済みのことと、まだ確認していないこと

Windowsで以下を確認しました。

- Nodeの軽いテスト34件、Pythonの新しいテスト3件。
- CPU側の起動と203体のカタログ取得。これはダメージや全キャラのGPU対応確認ではありません。
- 固定版のエンジンZIPのバージョン確認と、別環境に導入するセットアップ処理の検査。
- Slang 2026.20の同じソースからCUDAとMetalのソースを生成できること。
- 共通の実証入力4ケースの形式と期待値の梱包。

Macでの起動、Swift／Metalコンパイル、Metal GPUでの実証4ケースの実行、速度・メモリ使用量は未確認です。この小さな実証のCUDA実行アダプターも未実装です。今回のMac移行準備ではGPUを実行していません。

本体のCUDA版は別途、ABI `detail_timer_registry_v81` まで確認しています。状態領域は1部隊1,260,136バイト。共通の時計の検査はnative/PTX各8ケース、既存の周期処理17ケース・発動順25ケース・混成10部隊、軽い検査112件、通常APIの所持・装備・一時育成変更も確認済みです。標準条件のコンパイル受付は187/203体で、全キャラ・全装備・全条件の数値検証済み件数ではありません。

v81の時計の索引拡張案は、状態領域を1,016バイト減らしましたが通常8部隊のGPU中央値が約3.8%遅くなったため採用せず、機能確認版へ戻しています。記録は `research/timer-registry-checkpoint.json` と `research/timer-registry-index-experiment.json` です。

## 最初に読むファイル

| ファイル | 役割 |
| --- | --- |
| `gpu/portable_probe.slang` | 小さな共通GPUコア。整数演算、対象世代、時計の登録世代を扱う実証。 |
| `tests/fixtures/portable-probe.json` | 手書きの共通入力・期待値4ケース。CPU実行の途中状態をGPUへ渡していません。 |
| `scripts/build-portable-probe.py` | 同じソースからCUDA／MSLを生成。生成だけではGPU実行済みになりません。 |
| `scripts/verify-portable-probe.py` | 共通の梱包・結果比較。Metal実行は`--backend metal`で明示します。 |
| `scripts/run-metal-probe.swift` | Metalの起動・転送だけ。ゲーム計算ロジックは置きません。 |
| `scripts/setup-engine.py`・`setup-slang.py` | 別環境への固定版セットアップ。Slang配布物はSHA-256で照合します。 |
| `app/detail_effects.cu` | 現行本体のCUDA計算・状態・イベント実行器。共通GPU本体への切り出し元。 |
| `app/detail_gpu.py` | 詳細計算の命令生成、入力検査、CUDA実行と出力の復元。 |
| `app/effect_spec.py`・`lifecycle_specs.py` | 効果の分類と共通ライフサイクル。 |
| `app/timer_registry_runtime.py` | CPU参照側の共通時計。周期維持更新と再登録・再生成を区別。 |
| `docs/adding-effects.md`・`docs/timer-registry.md` | 新しい効果の追加方針と時計の規約。 |
| `docs/summon-source-next-steps.md` | 対象別の継続ダメージ、予約着弾、通常の敵対象処理への未接続事項。 |

## 次に進める順序

1. Macで環境確認とCPU起動を確認し、共通のMetal実証4ケースを実際に実行します。失敗ならSwift／MSLの診断から修正します。入力検査だけの成功へ置き換えません。
2. `research/portable-probe-metal.json` の`passed`・`gpu_execution_verified`・`backend`・GPU名と全4ケースの出力を確認します。`production_runtime_connected: false`はまだ正常です。
3. 本体の数値規約を整理します。約2,700行の現行CUDA本体は広く`double`を使用し、Metalは`double`非対応です。単純なfloat化や誤差判定の緩和で対応済みにしません。時刻・閾値・ゲージ・丸め・累積・指数計算を分け、整数／固定小数点／高精度演算の必要範囲を決めます。実証の整数演算成功はこの問題の解決を意味しません。
4. 共通コアへ実際の状態更新・イベント順・対象世代・時計を順に移し、同じ期待値を両GPUに使います。生成されたCUDA／MSLを手作業で別々に編集しません。共有状態とバッファー配置も確認します。
5. 小さな実証のCUDA実行部分を薄いアダプターとして用意し、Windowsが空いているときに必要なケースだけ比較します。大きな本体の再ビルドや全キャラの検査は、その前提が変わった場合に限定します。
6. 本体の実編成・装備・一時ステータス変更を含めた正しさと速度を測り、通常画面のMetal計算へ接続します。その後も残るキャラ・特殊効果・敵世界の対応を進め、全体の効率化を見直します。

現行の未完了項目には、受領者別の継続ダメージの時計、予約着弾の対象世代、通常の自動照準・召喚への攻撃経路、物理的な射撃単位の同時命中、残りキャラ・装備・効果の組み合わせがあります。標準条件で通ったことだけでこれらの受付を開きません。

## Mac側の作業開始時に渡す依頼文

```text
このリポジトリのdocs/mac-migration.mdとdocs/mac-handoff.mdを読み、MacBook M5・24GBで続きを進めてください。まず環境確認、CPU起動、共通SlangソースのMetal実証4ケースを実行し、実際にGPUで動いたことを確認してください。

最終目標は全キャラ・全特殊効果のGPU対応です。CUDA版とMetal版の計算本体・効果定義・テストを二重に実装せず、共通コアと薄いバックエンドへ分けてください。Metalのdouble制約への数値設計は未解決です。CPUの不具合へ無理に一致させず、発動順・対象世代・丸めを仕様に基づいて確認してください。

Windows PCは他作業に影響が出ているため、常時のCUDAテストや自動フルビルドは設定せず、必要な短い検証を明示的に実行してください。Metal実証の成功だけを、本体移植や全キャラ対応の完了として扱わないでください。
```

## 2026-10-21 v89完了追記

上記v89依頼は完了・Mac監査成功です。固定61c7a884のCUDA32はCPU13＋GPU禁止のnative10/48段階照合後、独立180秒/BelowNormalの1回で92.3588146秒、exit0。3JSON計50092bytesを取得し、source/name/bytes/SHAと共通監査器の全fingerprint・50 phase・元環境保持・残存0を確認しました。旧590/通常4682再実行0、GPU retry0です。Windows turn01a15b67-4fba-7982-b0ad-033e5cf20c5aはcompleted、cursor130、idle。再実行依頼は不要です。

現在の10ケースはbody0/gen1にcounterをbindするliteral resource/event検証です。他Actorへのbind、実着弾、target条件/child contextは次の段階で実証します。実戦測定ではbody/part/addの全てでcounter通知がlifesteal前でした。以前のbody/partをlifesteal後とした記録は誤りです。addのclipped damage、body/partの元damage、part全体のHP更新と個別callbackの順を検証してください。全変種0/203・通常CPU/public false・legacy unexplained Metal14c8e2e finding OPENを維持します。

## 2026-10-21 Claudeレビュー反映・再突入接続

最新の開発手順は`docs/gpu-development-cli.md`、根拠は`research/portable-review-development-checkpoint.json`を参照してください。共通CLIの開発package・保存Metal replay・sealを使用しています。recipient6は元のrawを再比較して成功（GPU再実行0、原失敗保持）、再突入/instant対象13は修正版Metalでnative完全一致、readiness v4は81（native60・拒否21）で成功しました。旧75のinput/native/output指紋と全raw byteも完全一致です。CPU共通テスト610件が成功しています。

味方全体表記のburst_reentryを発動者に一度だけ記録する規約でworld受付へ接続しました。literal名・B3発動済み対象のbuff/instantには、存在・不在・重複・コロン付き名・発動前後の共通ケースがあります。静的packingは173/266、base122/203へ進みましたが、全キャラ実戦認定0と通常画面CPUは維持します。未対応分類はstatとrecipientを構造化reasonで分離しました。

Windows v105はPTX生成後のmodule load、v106はCUBIN生成前のNVRTCで180秒に到達し、どちらもkernel0です。v106のmissing14の原因は不明で、元の失敗判定は変更しません。終了監査はJobを明示終了→子/子孫終了を5秒以内で待機→post観測→handle closeへ修正し、ピークメモリを記録します。Macの故障注入は成功していますが、実WindowsのGPU0 timeout/smoke検査が次です。追加の重いCUDAコンパイルは先行させません。CUBINはELF確認前にキャッシュへ書かないよう修正しました。coldコンパイルと実機キャッシュ効果は未解決です。

次は短いWindows制御検査、CUDA coldコンパイルの資源/設定切り分け、stun/target_stunned等の未対応効果、対応済み実編成の通常結果への接続です。全面的な実行器再実装や、時間枠を増やしたWindows再試行は行いません。

### Windows制御検査v108

v107はCPU81/native60の後、テスト用の子起動直後に失敗し、smoke未到達でした。原失敗を保持しています。テスト起動をCLIと同じbase Python・launcher環境除去へ合わせ、wrapper診断を残したv108は単独3件とCLIのCPU69件が成功しました。実Windowsの子孫付き2秒timeout検査と外側smokeで、終了後の空Job・peak memory取得を確認しました。smoke4.841秒、missing0、元HEAD/status保持、NVRTC/driver load/GPU0です。サービス識別unverifiedのため環境保持全体は未認定です。新機能のCUDA計算・coldコンパイル・速度は未検証のままで、次は資源と生成/最適化設定の切り分けです。詳細は`research/portable-world-v107-control-sanitized.json`、`research/portable-world-v108-control-sanitized.json`を参照してください。

## 2026-10-21 stunとコンパイル専用CLI

最新根拠は`research/portable-stun-cache-development-checkpoint.json`です。stun/免疫/対象条件の36正例＋拒否10は修正版Metalでnative完全一致。readiness v5の81も旧81と全input/native/output・raw一致です。CPU631件成功（Windows専用1件はMacでskip）。初回stun46ではrankの早期消費とenemy倍率への混入を発見し、原失敗を保持したまま、状態presenceを数値バフ集計から分離して解消しました。B1/B2の既定候補はstun中も保持して待機し、typed敵の条件は現在対象の文脈・世代を使います。既存canonical参照とbinary64/normalizerは変更していません。静的packing180/266、base126/203ですが通常CPU・全キャラ認定0です。

新しい`compile` CLIは同じNVRTC/compiler cacheを使い、sealed sourceと生成指紋を検査後、driver/kernelを禁止して最大60秒・既定2GiBのJob上限で実行します。異なるptxasレベルはcache keyを分け、後続`run --require-cache`はmissでNVRTC program作成前に停止します。CUBIN速度・実CUDA数値は未検証です。次のWindows依頼は、メモリ上限の実WinAPI CPUテストとcompiler/CLIのCPU故障注入を先に行い、成功時だけO1のGPU0コンパイルを1回に限ります。以前のv105/106/107の失敗は変更せず、同条件retryやtimeout延長は行いません。

## レビュー後の分類・実編成CLI・NVRTC引数

未対応triggerのvalidatorはtiming/conditionと不成立のdescriptorを構造化して返します。inventoryは117分類となり、旧113分類で混在した演算を分離しました。全266profileのpacking可否・入力SHAは以前と同じで、180/266、base126/203です。同じcodeの診断文集合も保持します。

共通CLIの`roster-regression`は実編成18入力を全定義のままMetal/native比較し、完全一致後にsealしました。初回のsandboxによるSwift module cache拒否はGPU起動前の原失敗として保持し、transport修正後の別package/captureで検証しています。通常画面CPU・全キャラ認定0は維持します。

Windows v109はCPU19件と実Jobメモリ上限検査に成功し、本体compilerは結合形式の`--ptxas-options=-O1`を受け付けず約9.95秒で終了、kernel0でした。実DLLの`nvrtcVersion`は11.3です。その後、tiny kernelで別文字列の長名/短名2構文を各1回だけ確認し、約4.74秒、driver/context/kernel0、missing0で成功しました。共通compilerは`["--ptxas-options","-O1"]`へ修正しました。本体O1の速度・CUDA数値一致は未確認です。CUDA context破棄失敗は、本来の実行失敗へnoteとして付け、原因を隠さないようにしました。詳細は`docs/claude-architecture-review-2026-10-21.md`と`research/portable-review-followup-checkpoint.json`を参照してください。

## 残りskill cooldownと集約回帰

`docs/portable-skill-cooldown.md`、`research/portable-skill-cooldown-development-checkpoint.json`を参照してください。共通kind22は残り時間だけを調整し、元のperiodを保持します。初回23の巨大負値反復で見つけた時計境界を修正し、Inf/NaNの非発火と復帰を含む25入力がMetal/native一致しました。ソフトウェアbinary64やnormalizerを緩めていません。GPU前のCPU参照で見つけた配列targetのhash検索例外は、`enemy_recipient_runtime`でnative resolverへの委譲を維持する型guardへ修正し、独立テストで確認しています。protected4ファイルとupstreamは変更していません。

`regression`149は既存readiness81・stun46・実編成22を元の比較器のまま集約します。全149入力がMetal/native一致し、旧145入力は入力・全raw出力とも完全一致、追加センチ4入力も成功しました。現在のsealed suiteはskill-cooldown25とregression149で、古い個別goldenは履歴としてsource staleを保持します。CPU645件成功（Windows専用1件skip）、静的182/266、base127/203、通常CPU・全キャラ認定0です。

Windows v110はCPU20件成功後、修正argvでO1 compilerを1回だけ実行し、全体41.20秒／NVRTC30.11秒、ptxas Memory allocation failureで終了しました。Job2GiB、post空、missing0、driver/context/kernel0、artifact0、再試行0です。サービス識別とメモリ上限との因果は未確定です。次はMac上の生成CUDA／保存PTXの構造とcompile資源の診断、残りのheal_overcharge_store・trigger_count_reduce・trigger_hit_crit等へ進みます。Windowsで同じ巨大compileを繰り返したり、メモリ上限や時間枠を自動で拡大しません。

## 回復貯蔵・実編成受付・保存コンパイル解析

`docs/portable-healing-storage.md`と`research/portable-healing-storage-development-checkpoint.json`を参照してください。共通stat74／protection kind9の回復貯蔵を追加し、既存の身体回復・lifesteal・被ダメージ・HP drainへ接続しました。maxHP付与は回復と区別します。初回実編成184のAnchor／Sora4拒否は原記録を保持し、C_STATIC条件と状態解除の受付接続を修正しました。拡張regression235（native188＋拒否47）はMetal全件一致、旧210の入力・全raw・nativeも一致、明示seal済みです。個別suiteの古いgoldenは自動追従させず、現在の通常入口はregression235です。CPU659件成功（Windows専用1skip）、静的187/266・base130/203、通常画面CPU・全キャラ認定0です。

共通CLIに`compiler-stats`と`ptx-stats`を追加しました。保存byte／既存receiptを検査するCPU解析で、NVRTC・GPU0。PTXの仮想register／local宣言を実レジスタ数やcompilerメモリ原因へ換算しません。旧Windows解析器が拒否した`%`なしregister名を含む正負例をCPU検査しました。原解析失敗は別JSONへ保持しています。新版CUDAの数値一致は未確認で、同じ巨大compileは再実行していません。次の未対応上位はprojectile_dmg_pct・trigger_count_reduce・trigger_hit_critです。

保存済みv105 PTXのWindows解析は共通CLIで成功しました。CPU3件成功、解析約1.16秒、BelowNormal・5秒上限、NVRTC／driver／context／GPU0、原PTX・cache・旧失敗保持。188関数の仮想宣言を集計し、entryのlocal宣言164,296byte、dispatch9,496byte、weaponFrameBodyは仮想register28,295でした。物理register／compilerメモリ原因の証明ではありません。`research/portable-v105-saved-ptx-stats-sanitized.json`はWindowsの構造化報告であり、Macへ原PTXを転送して独立監査したものではありません。次のCUDA比較仮説は武器frameの共通関数境界やRuntimeのprivate状態量を対象にし、同じ巨大compileの再実行はしません。

## 発動回数減少とregression287

`docs/portable-trigger-reduction.md`と`research/portable-trigger-reduction-development-checkpoint.json`を参照してください。buff版trigger_count_reduceはcanonical REDUCER_MASKの転置を使い、caster・生timingの一致と、resident順の固定値合計→整数化→閾値最小1を共通Slangで処理します。スタック／受益者／runtime条件による再フィルターを入れません。非武器MODEのtagged unionを使いstrideは維持、既存status／stack metadataとの共存も検査しています。

最初の287で見つけたフルチャージ2入力の時計不整合は、native静的正規化へ入力各3wordを合わせて修正しました。native全指紋・計算本体・比較器は不変、元失敗は保持。修正版287（native232＋拒否55）がMetal全件一致し、旧235と原失敗中の成功285は入力・全raw・native同一です。新goldenを明示sealし、現在の通常CLI入口はregression287です。新しい2キャラの全定義実編成を各3／30秒で追加。CPU665成功・Windows専用1skip、静的189/266・base132/203・分類114、通常CPU・全キャラ認定0。今回はWindows実行0で、CUDA数値一致は未確認です。次はtrigger_hit_crit等と、projectile_dmg_pctのCPU基準にも欠ける意味定義、および保存PTXに基づく共通関数境界のコンパイル診断を進めます。

## 名前付き命中context・強制スキル使用・regression327

`docs/portable-skill-critical.md`と`research/portable-skill-critical-development-checkpoint.json`を参照してください。predicate28は期待値のcaster/name別skill critical累積と、通知ごとのFrame contextへ接続しました。多段の率snapshot、入れ子・兄弟からの復帰、通常攻撃式、deferred B3の通知なし経路を区別します。nativeの実際のrng_acc辞書も比較します。

最初の320ではユリア愛用品1・2段階の計4実編成が拒否され、1件の診断でkind33 force_skill_useのactor-pool受付不足を確認。既存共通強制使用を受付へ接続し、maskの範囲／caster／自己参照と、強制先の条件を検査しました。every時計はresetしません。元の失敗と診断は保持。修正版327（native262＋拒否65）はMetal全件一致、旧287と元失敗中の成功316はinput／全raw／native同一。明示seal済みの通常CLI入口はregression327です。CPU671件（1skip）失敗0、静的191/266・base132/203・分類113、通常CPU・全キャラ認定0です。

保存生成コードを使うcompiler-statsに--callerを追加し、最大3段・noinlineで止まる字句上の呼出関係を出せます。現ソースでもeffectiveCharge→rawEffectiveChargeの未注釈境界を確認し、次のCUDA改善候補はrawEffectiveCharge一箇所です。共通境界変更をMetal327で数値・全raw検証してから、必要な60秒／2GiB compiler-only検証1回を検討します。現在は新版CUDA数値一致未確認、今回Windows0で、同じ冷コンパイルを再試行していません。

## rawEffectiveChargeの共通関数境界候補

rawEffectiveChargeへ共通noinline属性だけを追加しました。変更前1180f97と生成CUDAの差分は該当1属性だけで、厳密normalizerは変更していません。固定327入力のMetal/nativeは全件一致し、input／全raw outputも旧327と同一です。新しいsourceを明示sealし、現在のregression327はresearch/portable-world-charge-boundary-regression-short-expected.jsonを使います。CPU事前検査の登録9群も成功しました。旧671件全体のCPU回帰は1180f97の証拠で、今回再実行したという意味ではありません。

research/portable-charge-boundary-development-checkpoint.jsonが最新根拠です。生成CUDAの呼出関係上でrawEffectiveChargeがnoinlineになったことは確認しましたが、compilerメモリ／速度の改善はまだ未確認です。Windowsはsealed packageでCUBIN O1・60秒・Job2GiBのcompiler-onlyを1回だけ行う予定です。driver/context/kernelは使わず、再試行・上限拡大・自動fallbackはしません。過去v110との比較はsourceが違うため、この1属性だけの因果として扱いません。
# 2026-10-24 実戦時計の型付き投射物Metal実証

最新は`docs/portable-destructible-battle.md`/`research/portable-destructible-battle-checkpoint.json`。共通CLI `destructible-battle`がMetal20(native10/拒否10)・独立seal成功。通常と同じ最新entry/単一WorldSchedule/同じdamage Frameを使い、CPUイベント列なしで出現世代・物理攻撃混在・名前付き子・128弾・空対象budget保持を照合。GPU0.061秒/pipeline64.809秒、Runtime138952不変・新entryだけ出力1048576wordへ拡張し専用領域へ配置。最終不変package1ba39cad...はCPU119(skip0)/native10成功、実raw5blockの破損45通りを検出。通常492もCPU288/native378/Metal/独立seal成功し、旧1547698176byteを直接比較して全一致、生成CUDA/MSLも正規化前から同一。旧goldenは保持し、実証後だけ新golden登録。初回Swift guardのGPU前失敗、次の2回の名前付き子拒否（flag受付＋最新consumer入口の漏れ）、package中source編集の停止は保持/同一claim retry0。全266profile同一、packing245/base185/残20・全キャラ0/UI CPU/未達。Windows接続取得失敗で新run依頼0。次は実戦typed counter/子context・通常cleared node共存、元の全定義profile、個別DEF/投射物/盾倍率。CUBIN O0短時間実証は接続復旧後のみ。以下のCPU段階は履歴。

# 2026-10-24 実戦時計の型付き投射物CPU契約

最新の追加は`docs/portable-destructible-battle.md`と`research/portable-destructible-battle-cpu-checkpoint.json`。通常native simulate所有のBossScriptへ数量を接続し、別時計を作らず3世代再出現・普通の子/物理攻撃保持・再入ID・例外復旧をCPU9契約で確認。fresh共通CLI packageのCPU72(skip0)/既存native17成功、既存Metal golden保持、新GPU/Windows追加0。実schedulerのMetal接続は未完了。共通packetへCUBIN O0 compile-only stageを追加、同じ60/180秒・2GiB・BelowNormal/Job・driver/GPU0制約を保持。Windows実行は未依頼。7プロセス終了についてユーザーは手動終了/再接続/再起動なし・ゲーム/動画利用の可能性と回答。因果不明/保全失敗は維持し、利用状況から原因を断定しない。次はSlang world同期→既存FrameのMetal実証。全キャラ0/UI CPU/目標未達。
# 2026-10-24 body蓄積・固定量放出と観測器の高速化

最新は `docs/portable-destructible-body-accum.md` と `research/portable-destructible-body-accum-checkpoint.json`。共通CLIの `destructible-body-accum-retention` 49入力（native40／拒否9）がMetal全件一致・別process独立seal済み。旧31のinput／native／全130,023,424byte rawは同じ配置で完全一致しました。HSI6の明示policyだけで既存のbody着弾→吸血→蓄積と、pool take→整数化→landing queue→live盾への固定量放出を接続します。固定量へダメージ式・盾倍率を再適用しません。整数化後0もhit creditを消費します。元トロニー全定義はbody蓄積・body放出を実証し、盾への固定量放出は独立した宣言入力です。元ドロシーは貫通未対応として全定義のまま拒否を維持します。

native observerの全Python呼出し監視がcode objectをhashしていたため、監視対象codeの強参照を保ってidentity検索へ変更しました。変更前の14編成とnative全指紋は同一。初回事前照合153秒に対し、新版14編成の準備・照合は約21秒（工程・負荷差があるため厳密な速度倍率ではない）です。GPU4.66秒／初回PSO65.80秒と、回帰49のGPU10.08秒／cached PSO0.003秒を分けて記録します。保存raw4blockの破損24通りと既存蓄積CPU参照10検査も成功。旧HSI5の生成CUDA／Metalは正規化前の全byte一致。保護CPU4ファイル・pinned upstream・binary64・strict normalizerは不変です。

最終小型packageは1576 files／7,218,467byte。CPU60件83.570秒・native40件40.598秒、共通制御372件（Windows専用1skip）に成功し、実行後の全payload SHAとcheckoutとの一致も確認しました。旧golden／失敗／claim／rawは保持し、単独18は開発用のままです。次は共有回復の受益者receipt、貫通、parts／coords／ADD混在、同期子放出境界を優先します。packing245/266・base185/203・残20 model gap・全キャラ認定0・通常UI CPUは維持。Windows追加操作0、現full battle CUDA実機とcache性能は未確認。過去7プロセス終了はユーザー操作なし・game/video利用の可能性だけでは原因を確定できず、unknown／保全falseを維持します。

# 2026-10-24 共有回復の受益者監査・保持61

最新は `docs/portable-destructible-body-heal-share.md`／`research/portable-destructible-body-heal-share-checkpoint.json`。元レム・ミルク・RL2人と元ノワール／元トロニーの全73定義×3／30秒・HP／hit／破壊の12編成を追加。既存共通Slangの共有Frameを使い、recipientごとの実clamp前後HPを既存observerのcontext managerで観測します。初期1/3とburst後2/8対1/8、盾のbody吸血抑止、蓄積共存を検査。回復元のHP差へ誤帰属せず、5人のquery／最終累積healingを厳密比較します。実raw2blockへの24破損と誤帰属・audit省略を拒否。故障注入で見つけた最終HP欄の未照合も、同じnative最終queryへのHP／maxHP／HP%／DEF照合で修正しました。実body clamp内の例外後にprofile・simulate・damage/heal scopeが復元することも検査しています。

共通CLI `destructible-body-heal-share-retention` 61入力（native52／拒否9）がMetal全件一致・独立seal成功。旧49の全input／native指紋と全205,520,896byte rawが同一indexで一致。GPU sourceと生成CUDA／Metalは正規化前から前回と全byte同じで、Slang追加0、GPU10.170秒／cached PSO0.003秒。CPU71件87.796秒／90秒枠、native52事前照合72.304秒。独立sealのみ実測に基づくCPU90秒を明示（GPU／Windows枠変更なし）。最初の12入力は容量再検査でGPU前停止、rawをbyte/SHA/inode保持で疎化して未消費claimを使った別captureで実行。原失敗は保持しています。

最終compactは1583 files／7,275,395byte。CPU71件89.150秒、native52件72.096秒、共通制御372件（Windows専用1skip）成功、全payload SHAとcheckoutとの一致も確認済み。単独12は開発用、旧goldenは履歴のまま。Windows追加操作0、現full battle CUDA／cache実測は未確認、旧7プロセス終了原因unknown／保全falseを維持。packing245/266・base185/203・残20 model gap・全キャラ0・UI CPU・目標未達です。

次の効率化は、共通adapterのnative providerを既存ParentOraclesへ直結して同じ親processの事前値を通常比較で使うこと。現retentionのcompareは別adapterへ委譲するためprovider検出が通らず、事前計算と通常監査の約72秒ずつが重複しています。独立seal／保存結果監査をfreshに保ち、input/provider/valueのstampと全比較項目を維持したCPU故障注入・保存raw照合で進めてください。未対応20分類を見直し、貫通・元ドロシー／parts・coords・ADD混在と共通CUDA compile負荷も優先します。

# 2026-10-24 共通比較器の親process再利用と未対応20分類の再確認

最新は `docs/portable-destructible-parent-oracles.md`／`research/portable-destructible-parent-checkpoint.json`。共通body比較を1か所へまとめ、retention61のcompareからnative_referenceを直呼びすることで既存ParentOraclesへ接続。通常実行のCPU事前52編成を同じ親だけで再利用し、追加native0／拒否9／全61 Metal一致。通常比較2.051859秒（以前fresh約72秒）で、input/provider/valueのstamp・所有者・1回だけの利用・全数値比較は維持。別processのGPU禁止監査は実native52回・再利用0、75.438829秒で成功。旧61全255,852,544byteとinput/native/生成CUDA/MSLは同一、GPU/定義/core/normalizer/goldenは変更なし。今回GPU1回／Slang0／Windows0。

新しい実fixture再利用2検査と既存ParentOracles13検査を追加し、CPU86件91.286秒。既存71検査約89秒に追加分があるためsuiteのCPU枠だけ事前に120秒へ設定し、GPU/compiler/Windows枠は変更していません。終了故障注入のunitが実disk不足へ先に到達したため、この模擬testだけ容量成功と2回呼出しを検証して目的のtransport失敗へ到達させます。本番storage guardは不変。compact package b58be3b...は1585 files／7,281,453byte。GPU10.283秒・cached PSO0.003秒、事前native52は72.634秒。共通制御372件（Windows専用1skip）成功、全payload SHA/checkout一致も確認済み。

現sourceの共通CLI inventoryは266 profiles／packing245（base185）、未対応21 profiles／20分類、CPU戦闘/GPU0。20分類は全てreference_model_gapで、現在のtyped補正modelの通常入口への接続、受取damage splitの保留仕様、空間・cover・敵回復/弾薬等が残る。小さな全20分類・未対応profile一覧とfull report SHAをevidenceへ保存。次は既存attack_group_runtimeのopen/sealを実戦producerへ接続するmulti_hit:2/:4（니힐리스타／벨로타）のnative契約を優先。受付だけを開いたpacking増加を対応済みにしない。CUDA compile負荷と短いcached実機検証も未完。全キャラ0/UI CPU/全目標未達、旧Windows7プロセス終了原因unknown/保全falseは維持。

## 2026-10-25 明示cover／holdの共通GPU実行

`coordinate-manual`169（native151／拒否18）はM5 Metal照合・独立seal済み。旧136全962592768byte・input/native指紋を保持。新規25worldで有限／None／時刻0、部分装填取消、mode auto／charge、camera preempt、cover_disabled、被弾、後から予約したhold、ゼロ射撃・全MT保持を検査。初版GPUは23差分を保存、CF領域clear後の初期化とbase autoの内部phase／見えるchargingの分離で解消。実GPU計2／同claim retry0。CPU112／control428（Win1skip）、Runtime138952byte・247fieldと入出力容量不変。GPU.484183秒／初回PSO91.796496秒。共通CLIがstrict SOURCE不一致を準備前に拒否し、fixture base再利用で入力生成の重複を削減。保存済みMetal cacheのfile probeはhitだがwarm GPUは再実行していない。Windows新要求0・現CUDA未取得。

最新根拠は `research/portable-coordinate-manual-checkpoint.json`。現worktree `/private/tmp/nikke-runtime-resident`、branch `codex/runtime-resident`。復旧点は固定package `/tmp/nikke-manual-develop-v8` と成功capture `/tmp/nikke-manual-metal-v2`、失敗 `/tmp/nikke-manual-metal-v1`。rawは削除せず4KiB疎化で全byte/SHA/inode保持。次は条件付きcover/reload/burst policyとcover_all、post-delay中のcover・mode期限、named listenerなしの数値cache／reload速度条件、down／revival・healing storage合成を優先して契約→共通Slangへ進める。明示25worldから全入力・全元定義の対応を推定しない。元canonical7ファイル不変、全キャラ0／model gap20／UI CPU／目標未達。

## 2026-10-25 条件付きcover／reload方針の共通GPU実行

`coordinate-policy`196（native171／拒否25）はM5 Metal全件一致・独立seal済み。本人FB coverと4リロード方針、5種類のanchor、if_dry、stage gate、優先度、camera preempt時の一度だけのanchor復元を共通Slangへ接続。既存aimのanchor／装填総時間／次FB予測を共有し、CPUで操作時刻表を作らない。20新worldを追加し、旧169全1,196,163,072byteとnative／input prefixを保持。入力+128word／出力+384word、Runtime138952byte・247fieldは不変。共通readback器はcase境界をまたぐhashと短い末尾blockを照合する。静的burst cooldownの正本との矛盾は入力準備で拒否する。

固定package `/tmp/nikke-policy-develop-v2`、成功capture `/tmp/nikke-policy-metal-v2`、最終配布 `/tmp/nikke-policy-final-compact-v1.zip`。CPU116件141.626秒、native171事前98.824秒。GPU0.644926秒／初回PSO91.377002秒。初版 `/tmp/nikke-policy-metal-v1` は旧ソース逆変換のschema／Swiftの不足をCPUで検出し、GPU前停止。修正版だけGPU1回／claim retry0。sealとcompiler証明書は別processのGPU禁止監査。rawは全byte/SHA/inodeを保った4KiB疎化で約1.35GBを回収し、削除していない。生成cache必須検査はpaired CUDA／Metal出力をcompiler0で再利用したが、CUDA実行・warm cache性能は未証明。

詳細は `docs/portable-coordinate-cover-policy.md`／`research/portable-coordinate-policy-checkpoint.json`。現worktree `/private/tmp/nikke-runtime-resident`、branch `codex/runtime-resident`。旧manual169単独のcertificateは履歴としてexact inverseを維持。新方針の証明を旧入口の対応済み認定へ自動転記しない。次はcover_allと強制burst action producer、post-delay／zero-listener／knockdown・回復貯蔵の合成、mixed actor／元定義を優先する。Windowsは既存接続の送信APIがidleを開始できず、新規GPU要求0、現CUDA結果未取得。全キャラ認定0／20 model gap／UI CPU／目標未達を維持する。

最終compactは1,832 files（full3,173）で全選択byte一致・checkout SHA一致。共通制御433件成功（Windows専用1skip）、frontier5件と静的cooldown負例1件も成功。最新inventoryは245/266 packing・base185/203で、全キャラ戦闘認定0を保持。

## 2026-10-25 スクワッドfocus／全体遮蔽の共通GPU実行

最新は `coordinate-squad`222（native189／拒否33）、`docs/portable-coordinate-squad.md` と `research/portable-coordinate-squad-checkpoint.json`。focus／cover_allのauthored literalを共通Slangへ接続し、burst tick後・カメラ調停前に処理する。focus解除とcover_allが同時でも旧ctrl_ownerを除外する順序をCPUで確認。全体遮蔽はカメラ維持を要求しない。武器変更・遮蔽禁止・部分装填・個別sequence／方針との18worldを追加。Runtime138952byte・247field／出力1769856wordは不変、方針padding48wordへ明示状態を割当て、入力+136word。

固定GPU package `/tmp/nikke-squad-develop-v1`、元capture `/tmp/nikke-squad-metal-v1`。CPU121件151.241秒（batch151.537秒）／native189事前114.846秒。GPU0.661187秒／初回PSO92.310655秒。方針＋squad合成1件だけ旧host比較器の再packが拒否。原失敗は保持し、比較器を共通policy-state関数へ分離。修正版 `/tmp/nikke-squad-develop-v2` ではGPU source・全input・全native基準が厳密同一。`/tmp/nikke-squad-replay-v2` でGPU禁止replay全222一致、別processの独立sealも成功。元のstorage停止 `/tmp/nikke-squad-replay-v1` も保持。旧196全1,387,567,104byte／native／input prefixと固定の空拡張を保持し、実GPUは計1回・retry0。raw2本は全byte/SHA/inodeを維持した4KiB疎化で保持。13個の完了済みsource-package展開だけをtar.gzへ全復元テスト後に移し、receiptと元zipを残している。必要な古い展開はreceiptのtarを復元して再検証する。

最終compact `/tmp/nikke-squad-final-compact-v1.zip` はfull3181→1840 files、全選択byteとcheckout SHA一致。共通CLIとblock検査器の入力拡張契約一覧を1か所にまとめ、二重parserの不一致を回帰検査した。新profile専用compiler-source証明書と現CUDA実機は未作成／未検証で、親policyの証明を代用しない。生成cacheのrunはhit／compiler0だがCUDA cache性能実測とは区別する。Windows新要求0。全キャラ0・20 model gap・UI CPU・目標未達。

最優先の追加境界は、mode duration=.3とsquad t=.3が同じtickの操作。CPU観測ではpump前に `_in_weapon_change=True` でowner0を除外し、t=.5ではFalseで含む。現18worldにはこの同時境界を入れていない。`gpu/event_runtime.slang::clearMode` のlogical modeと、次char tickまで残るphysical状態を同一視しない。physicalModeIndex=-2はrevivalでも使うため一律判定へ置き換えず、native `_tick_weapon_change` の終了分岐を確認し、共通stateを保持・比較する。次にburst delay／wait_own_cooldown／patternと次FB予測への接続（`docs/portable-burst-control-next.md`）。効率化ではcoordinate adapterの比較を共通observed経路へまとめ、既存ParentOraclesの同じ親だけの再利用を検討する。独立auditはfreshのまま保つ。

## 2026-10-25 キャラmode状態・装填callbackからのmode進入

最新は `coordinate-squad-mode`251（native213／拒否38）、`docs/portable-coordinate-squad-mode.md`／`research/portable-coordinate-squad-mode-checkpoint.json`。mode effect満了・弾数終了・トグル解除後も次の生存・非気絶char tickまで残る `_in_weapon_change` を5flagで保持し、全体遮蔽と調停前のcover/reload要求で共有。強制focusのownerはchar tick内でmode終了後すぐ方針へ入れる。気絶・復活、装填完了からのmode進入・待機の24worldと全pumpの2×64bit指紋・最終flagsを比較する。既存revival handler29をこのsourceへ接続。Runtime138952byte・247field／入出力サイズは不変、wire v2の固定markerと既存出力bankを使い、CPU操作表を入力しない。

初版 `/tmp/nikke-squad-mode-develop-v1`／`/tmp/nikke-squad-mode-metal-v1` はCPU125検査159.353秒・native209事前122.209秒、247中246一致。装填完了callbackでmodeへ入る時、CPUはそのフレームのcover再判定を経ず `_tick_weapon_change` を開始するため、GPUにt=.31666666666666665のmode射撃とteam2通知が不足した。修正版は共通prepareWeaponFrameでこの経路を識別し、同じフレームの進入待機・shot limitを処理する。計算・正本の比較対象を削らず、4合成worldを追加。

修正版 `/tmp/nikke-squad-mode-develop-v2`／`/tmp/nikke-squad-mode-metal-v2` は251全件一致。CPU正本・packingの旧247全fingerprintは不変。差分8検査13.200秒に選択し、全213 native事前123.470秒・全251 GPU比較は維持。初版の固定125検査も保持。GPU.714553秒／初回PSO91.490106秒。旧222全1,571,632,128byteと、初版で成功した246全1,741,538,304byte／input・nativeを保持し、装填進入1件のraw変化を明示。新Slang各1回の実GPU計2／同claim retry0。raw2本は全byte/SHA/inodeを維持して4KiB疎化。16個の古いsource-package展開だけを全復元テスト後に圧縮し、元zipとreceiptを保持した。

`seal --compiler-certificate PATH` を追加し、同じGPU禁止fresh監査からgoldenと専用full-source証明を作成した（`docs/portable-joint-seal-certificate.md`）。既存pure certificate関数を再利用。filtered／probe、manifest変化、package・source・計算不一致、既存／同一出力を拒否し、従来の単独sealと既存certificate操作を保持する。23 CPU検査と実251入力で確認。新証明は専用compiler aliasを準備するが、CUDA compile/link/cache/GPU/resourceの成功にはしない。

最終 `/tmp/nikke-squad-mode-final-compact-v1.zip` はfull3189→1832 files、全選択byte／checkout SHA一致。最終control443（Windows専用1skip）、frontier5、追加の進入待機positive witness1も成功。Windowsはrev78 idleのままで新しい実行依頼0。生成cache hit／compiler0と、現CUDA実行・warm cache性能未確認を分ける。packing245/266・base185/203、未対応21 profiles／20 model gap分類、全キャラ0／UI CPU／全目標未達を維持。

次は未対応分類の現consumerを再確認し、burst delay／wait_own_cooldown／patternと予測時計（`docs/portable-burst-control-next.md`）、modeと個別sequence・post-delay・healing storage／actorの合成、元定義への接続を進める。coordinate ParentOraclesの再利用では、比較時だけ収集するcreation_indicesも事前観測へ含める必要がある。比較から単にnative呼出しを抜いてobserverの値を空にしない。独立監査はfreshを維持する。

## 2026-10-25 burst操作の共通policy単体実証

最新追加は `docs/portable-burst-control-policy.md` と `research/portable-burst-control-policy-checkpoint.json`。共通CLI `burst-control-policy` は347正本＋34拒否の381入力がM5 Metal全一致・別process/GPU禁止seal済み。候補producerをactual/予測で共有し、delay、本人wait、安定pattern順位、明示順序、再突入/A候補とepsilon境界を共通software binary64で検査。GPU1回、0.000918秒、pipeline0.129766秒。単独probeへresident generation cache指定した初回はcapture/claim前に拒否、指定修正後に実行。CPU3、共通制御443（Windows1skip）、保護8ファイル・旧world shaderは不変。実戦のcontrol.burst受付は未接続のまま。次は同じhelperをburstFrame/coordinateAimBurstEndへ接続し、stage_open/完了周期/tick冒頭候補をGPU保持、cooldown低下・full-end通知・reload into_fbを実戦照合し、旧251全raw保持後だけ受付を開く。固定package `/tmp/nikke-burst-policy-develop-v1`、capture `/tmp/nikke-burst-policy-metal-v1`、seal `/tmp/nikke-burst-policy-sealed-v1.json`。Windows追加0、現full battle CUDA/cache性能未取得。packing245/266・未対応21profiles/20分類・全キャラ0/UI CPU・全目標未達。

## 2026-10-25 burst操作を共通戦闘実行器へ接続

最新は `docs/portable-coordinate-burst-control.md`／`research/portable-coordinate-burst-control-checkpoint.json`。共通CLI `coordinate-burst-control` 293入力（native246／拒否47）がM5 Metal全一致・GPU禁止の別process監査＋同じ監査からのcompiler source certificateでseal済み。delay・本人wait・pattern・明示順序を共通candidate producerへ接続し、stage-open／完了周期／tick冒頭の候補段階をGPUが保持、次FB予測と同じ候補／delayを使います。既存Runtime247field/138952byte・出力1769856wordは不変、squad bank末尾18wordを所有。入力は固定176wordを足した109968wordです。旧251入力の全1776935424byte／input-prefix／nativeを保持。初版で一致した287入力の全2031794688byteも保持し、旧289全input/nativeが同じでrawが変わったのは実際の失敗2件だけ。初版のdown時boss_log逆順と再突入kind25の受付漏れを修正し、全員cover／先行down／最後の対象のcover等4編成を追加。原失敗とraw/claimは保持しています。

GPU.727458秒／初回PSO93.066173秒／CPU事前174.963130秒／通常全比較195.023022秒。初期CPU監査180秒は実測に対して不足と判断して子だけ中止、GPU禁止のsaved seal/certificateだけ上限240秒へ分離（GPU/Windows/compiler/CPU test枠180は維持）。上限分離24件、native進捗journalの成功／指紋不一致／例外13件をCPU検査。journalは実GPU前の各ケース名・番号・件数・開始／終了／例外・時間を記録し、全体の生存／成功と混同しません。単体policy381はinclude調整後も全input/raw/CUDA/MSLが旧版と全byte同じ、新goldenを別名で登録し旧golden保持。

固定package `/tmp/nikke-burst-control-develop-v3`（281dd15c…）、capture `/tmp/nikke-burst-control-metal-v3-ready-v1`、seal `/tmp/nikke-burst-control-sealed-v3.json`、certificate `/tmp/nikke-burst-control-source-certificate-v3.json`。v2準備は多重個別操作fixtureの誤った前提で中止、v3初回captureは容量検査でclaim/GPU前停止。元ソース展開16件を復元・全SHA検証付きでlossless圧縮して展開分だけ除去、全rawは削除せずSHA/inode/byte保持で4KiB疎化。

現inventoryは266/packing245・base203/185・未対応21profile/20reference-model-gap分類、全キャラ認定0/UI CPUで未達。Windowsは既存チャットを一度read-only確認しrev78/idleのまま、新メッセージ・新実行0、現CUDA／warm cache性能は未取得。次は明示mode-sequenceとpost-delay、healing storage／混在actorの元定義、共通CLIのParentOraclesに新adapterの通常比較をつなぐこと。独立監査はfreshのまま維持し、current-source CUDAは短い必要検証だけにします。

最終compact package `c4de2a88…`（1846 files／ZIP 8,475,998byte／展開53,629,442byte）は専用12検査・全246 nativeのCPU再照合・共通制御446検査（Windows専用1skip）が成功し、終了後に全payload SHAとcheckout全byteの一致を検査済みです。最終captureは `/tmp/nikke-burst-control-final-cpu-v1` と `/tmp/nikke-burst-control-final-control-v1`、archiveは `/tmp/nikke-burst-control-final-v1.zip`。GPU追加実行はありません。


## 2026-10-25 座標戦闘の通常比較での事前計算再利用

最新は `docs/portable-coordinate-parent-oracles.md`／`research/portable-coordinate-parent-oracles-checkpoint.json`。coordinate-burst-control293の元leaf比較器を既存ParentOraclesへ接続し、実native観測で得たcreation_indicesも同じ親・threadだけで一度再利用します。全入力のfresh比較との完全一致、実native事前246／通常比較追加0／fresh246回をCPU専用CLIで確認。事前178.002秒／再利用比較8.661秒／fresh比較195.058秒。同一実行の順次測定で、独立benchmarkではありません。独立audit/replay/sealのfresh境界と元比較関数を維持し、source/input/native/provider/補助記録/所有者のstamp・原observer復元を検査。GPU/core/正本/golden変更0／実GPU追加0。全原capture artifact hash29件を終了後も再検査しました。

CPU専用 `coordinate-parent-check` は原成功Metal293のread-only fixtureから新GPU claim/capture/certificateを作りません。固定実証packet `/tmp/nikke-coordinate-parent-develop-v2`、結果 `/tmp/nikke-coordinate-parent-check-v2`。最後に追加した原artifact再hash後条件は別の実29件再hashで検査し、fixture4件にはobserver復元assertを追加。Slangペアgeneration cache hit／compiler0・CUDA/MSL全byte原成功captureと同一、Metal file cache probe hit。現CUDA実行・warm GPU性能にはしません。Windowsへのcoordinate-landing40の送信を再試行したが、既存idleチャットを開始できない同じAPIエラーで未送信。再実行依頼の重複はしていません。

次はmode中の明示sequence・post-delayのnative契約、healing storage／混在actorの元定義、短いcurrent CUDA検証。packing245/266・base185/203、未対応21profiles/20分類、全キャラ認定0/UI CPU/目標未達を維持します。

最終compact `c325f597…`（1851 files／ZIP 8,530,451byte）は選択36件と共通制御446件（Windows専用1skip）が成功。終了後に全payload SHAとcheckout全byte一致を確認。archive `/tmp/nikke-coordinate-parent-final-v1.zip`、選択検査 `/tmp/nikke-coordinate-parent-final-tests-v1`、制御 `/tmp/nikke-coordinate-parent-final-control-v1`。GPU追加0。


## 2026-10-25 mode中の明示操作・射撃後待機

最新は `docs/portable-coordinate-mode-actions.md`／`research/portable-coordinate-mode-actions-checkpoint.json`。共通CLI `coordinate-mode-actions`313（native266／拒否47）がM5 Metal全一致・別process/GPU禁止fresh seal済み。mode中のhold／cover・同時順序・待機中cover・期限／auto／進入待機・自動装填／tap・元武器周期の非継承・遮蔽禁止を20worldで合成。正本は一時武器交換前のbase fire_modeで姿勢を処理するため、共通enterManualCoverでbase chargeのnextShotもcover時刻へリセット。Runtime138952byte/247field・入出力109968/1769856wordは不変。base SRの0.215秒とmode効果0.2秒を区別し、既存static normalizerとの不一致を新adapterで拒否。strict wire登録をopen_suiteでpacking/native前に検査し、必要監査JSONもpackage前に検査します。

初16入力はsandbox No Metal deviceでカーネル前停止、claim保持。M5デバイス読み取り確認後の20入力初版にはbase待機0秒の入力矛盾があり、修正後も全20native指紋は不変。正しい入力では17一致・3実装差となり、時計リセットで全313一致。途中v4はJSON依存不足、v5はwire登録漏れをCPUで検出し作成子だけ明示中止。全原失敗・rawを保持。現rawの旧293は287全2031794688byte保持、6件のみ未射撃10秒charge武器のnextShotをcover進入時刻へ更新。全変更wordの位置・値・owner・未射撃を確認し、旧raw保持検査falseも残す。元20の17成功全120350208byteは保持、変化は実失敗3件だけ。待機配列の誤りを正本に従って直した後、native正本と比較項目は変更していません。

固定GPU packet `/tmp/nikke-mode-actions-develop-v6`（55b8a8a3…）、capture `/tmp/nikke-mode-actions-metal-v6`、seal `/tmp/nikke-mode-actions-sealed-v6.json`、certificate `/tmp/nikke-mode-actions-source-certificate-v6.json`。GPU.706120秒／初回PSO93.681053秒／CPU事前186.553041秒／通常比較8.632057秒。親再利用266・追加native0、fresh監査へ再利用0。GPU実行は失敗2＋修正1、同claim retry0。共通CPU-only cache検査ではsealed Slangペアhit/compiler0・CUDA/MSL全byte原capture一致、Metal file probe hit。現CUDAとwarm GPU性能は未確認。

最終compact `/tmp/nikke-mode-actions-final-v1.zip`（9954d281…／1856 files／8607700byte）は選択30・制御446（Windows1skip）成功、全payload SHA／checkout全byte一致とGPU packet source/input/native同一を確認。最終配布だけで全266nativeを再実行しない。全reader終了後にrawをbyte/SHA/inode保持で4KiB疎化。完了済みsource展開12件も全復元・全SHA検査後にlossless圧縮し、receiptは `research/coordinate-mode-actions-evidence/nikke-mode-actions-staging-archived-v1.json`、実tar/全file一覧は `/tmp/nikke-mode-actions-staging-archives-v1`。raw削除0。

model-checkに最新入口の証明を追加しsource match true、inventoryは245/266 packing・base185/203・未対応21profiles/20 reference_model_gap分類を維持。全キャラ0／UI CPU／全目標未達。Windowsは既存チャットrev78 idleのままで、今回status確認1・新メッセージ/GPU0。次はmodeで中断したpending automatic reloadの通知とspeed effect期限の合成、zero-listener／healing storage／mixed actor元定義、短いcurrent CUDAとwarm cacheの検証を進めます。

このMacの今回のsandbox内ではMetal deviceを列挙できず、読み取り確認と実Metal実行はrequire_escalatedで成功しました。次回もデバイス可視性を先に確認し、同claimを再利用しないこと。共通CLIへGPU0のMetal可視性事前検査を加え、CPU準備後のNo Metal device停止を避けることも次の効率化項目です。


## 2026-10-25 保留自動装填・CPU前Metal確認・test-only更新

最新は `coordinate-auto-reload`322（native275／拒否47）、`docs/portable-coordinate-auto-reload.md` と `research/portable-coordinate-auto-reload-checkpoint.json`。共通weapon tickでpost-delay完了を扱い、遮蔽でreadyへ戻ったmode chargeだけ弾倉を補充、非適格な次shotでもpendingを保持します。mode開始／終了の既存pending破棄は保持。9worldで期限・cover取消・mode満了／交換・until_reload・zero-duration／listener・待機途中終了を実native観測し、通知の子damage／atk・最終ammo／pendingを比較。Runtime／wire／入出力容量と保護8ファイルは不変です。

固定 `/tmp/nikke-auto-reload-develop-v4`（6b24922b…）／`/tmp/nikke-auto-reload-metal-v4` は322全一致。GPU.697421秒／初回PSO93.756371秒／CPU事前192.452146秒／通常比較8.671853秒、事前275を再利用し追加native0。同じ親のreceiptを渡さないGPU禁止fresh子監査は210.929726秒、全322／275native domain一致。同じ監査でgolden・専用source certificate・実測時間receiptを作成。CUDA証明へ流用しません。旧313は入力／native全同一、312全raw保持、残る1件はfield work統計2wordのみ変化。初版成功321も316全raw保持、5件は同じwork統計だけ。失敗1件はammo0→1と統計。詳細全word差分・元失敗は保持し、全raw保持と偽りません。新sourceのGPU計3回、同claim retry0。

共通CLIにGPU0のMetal device可視性検査を追加。容量／必須cache後、CPU準備／test／claim前に20秒上限でdevice確認。sandbox未検出・権限別M5検出、実packetのCPU前停止を確認。CPU-only／smoke／CUDAは除外。`refresh-tests` は未claim・GPU未開始のfailed development packetだけ、既存test Pythonの明示変更を新ZIPへコピー。非test／golden／基準を原byteで保持し、全payload再hash・排他的公開・元capture維持。実322 packetのテスト期待値1件更新に利用し、CPU基準再作成だけを回避。通常native照合・独立監査は省略しません。機構7検査、可視性8、既存cache境界9を共通制御へ登録。CLIのimport scope失敗も既存復旧検査が検出・修正し元失敗を保存。

最終compact `/tmp/nikke-auto-reload-final-v2.zip`（85d28d12…／1871files／8,716,209byte）は選択33・制御470（Windows1skip）成功、終了後に全payload SHA／checkout全byte／実GPU source・input・native基準一致を確認。生成cache hit／compiler0、実GPU時のCUDA/MSL両生成物と全byte同一。追加GPU0。全reader終了後にrawを全byte/SHA/inode維持で4KiB疎化。完了source展開19件も全復元・全SHA検査後のlossless archiveへ移し、元ZIP・receiptを保持。raw削除0。

inventory再検査は245/266 packing・base185/203、未対応21profiles、全キャラ認定0／UI CPU／目標未達。未対応20 model-gap分類の解消をpackingだけで認定しません。Windowsの送信API再試行はidle chatを開始できず未送信で、追加実行0。接続復旧を繰り返し依頼せず、ユーザーが開始した場合だけ既存短い検証の結果を取得します。次はpending装填とdown／復活・callbackでのmode／容量変更、healing storage／混在actor元定義、短いcurrent CUDA／warm cache確認を優先します。


## 2026-10-25 sampled座標戦闘の回復貯蔵・分配・放出

最新は `coordinate-healing`340（native291／拒否49）、`docs/portable-coordinate-healing.md` と `research/portable-coordinate-healing-checkpoint.json`。既存のHP超過回復貯蔵・ATK由来受療pool・heal_split・放出の同じSlang handlerを使い、新入口だけsampled admissionへkind32と既存整数総計初期化を接続。16world＋拒否2で期限・capacity・periodic・lifesteal・mode散弾・手動cover・別caster・active pool・ADDへのskillを合成。計算本体／容量／Runtime／wire／保護8ファイルは不変です。

元GPU `/tmp/nikke-coordinate-healing-develop-v1`（ddd3ca4c…）／`/tmp/nikke-coordinate-healing-metal-v1` は339/340一致。1件は既存packet observerが空ev.targetをBODYと記録し、実 `_land` のADD routeを失ったため総計54,000を期待していました。GPU・native本体・exact bankは34,000／17件で一致。既存実landing observerを明示opt-inで再利用し、ADD2体への10packet／20,000のラベルだけを補正。旧nativeに投影すると原指紋に全一致する、source前後SHA固定migrationを追加しました。ダメージ／時刻／owner／generation・他入力・source変更は拒否。元失敗・claim・rawは保持しています。

修正版packet `/tmp/nikke-coordinate-healing-develop-v2`（d291c83f…）は全input／GPU source同一、339入力の基準指紋を保持し変更観測1件だけ再作成。`package --baseline-package OLD --reference-migration coordinate-healing-routed-adds-v1 --develop --compact` で全340inputを再pack／hashしてから固定します。続くGPU禁止saved replay `/tmp/nikke-coordinate-healing-replay-v2` は全340／291native fresh一致。新CLIではbaseline_migration付きpacketの新GPU実行も拒否し、saved replayへ限定します。最終sealed packetにこの制限markerは付きません。

独立sealの2回は240秒timeoutで終了・記録保持。重複migration guardとその全入力再構築を削減しました。成功したv4監査は225.422417秒、fresh guard1／同じ子内receipt再利用1、fresh静的入力構築1／再利用1、live parent receiptなし。静的入力はadapter・manifest・全domainのpickle stamp（deserializeなし）・両payload全SHA・receipt anchorsを再検査し、native値は再利用しません。全291native domainの計算比較はfreshです。同じ監査からgoldenと専用source certificateを作成しsealed登録。GPU／Windows180秒、CPU saved audit240秒は不変。

実GPU計1回、同claim retry0／observer修正後の再GPU0。GPU.755795秒／初回PSO93.081245秒／CPU事前200.755415秒／通常比較8.978930秒（同じ親291を再利用）。旧322は全input／native／全2,279,574,528byteのraw保持。Slangペアgenerationは必須cache hit/compiler0で、CUDA/MSL原生成物と両方全byte同一。現CUDA／warm CUDA cache性能へ流用しません。全reader終了後に原rawとreplay rawをbyte/SHA/inode維持で疎化。完了source展開16件は全復元／全SHA検証後にlossless archive、元ZIPとreceiptを保持しraw削除0です。

最終compact `/tmp/nikke-coordinate-healing-final-v1.zip`（a0f3be21…）は機能37・制御476（Windows専用1skip）成功。全1890filesの終了後payload SHA／checkout全byteと、実GPU source/input・修正版native基準との一致を確認。最終配布で全nativeを再作成しません。

次はauthored fixtureを増やす前に、元の完全編成input bridgeを優先します。既存static preparationからマルチャーナ編成68効果（本人14）、デルタ：ニンジャシーフ編成79効果（本人25）の全元定義・weapon/config SHAを抽出済み（`original-static-v1.json`、CPU battle/GPU0）。authored observerはweapon metadata／遅延／cover HP／操作を置換するため元編成正本に代用しません。`portable_world_roster_input` の全定義・owner・元正規化と座標sidecarを共通化し、real bodyを既存native reference＋user選択の共通座標mathだけで比較します。元の不都合な定義・武器を抜かないこと。down／復活・callback session合成と公開受付も残ります。

inventory再検査は245/266 packing、base185/203、未対応21profiles／20model-gap分類、全キャラ認定0／UI CPU／全目標未達。Windows新依頼0。既存idle chatを開始できない送信APIの制約に対して同じ依頼を重複送信せず、開始可能になった既存短いCUDA検証の保存結果だけを取得します。

## 2026-10-25 元の完全編成と座標実行器：開発途中

最新は `docs/portable-coordinate-original.md`／`research/portable-coordinate-original-checkpoint.json`。worktree `/private/tmp/nikke-runtime-resident` の `coordinate-original`8を追加しました。マルチャーナ／デルタ：ニンジャシーフ、それぞれ4枠目ノア版も含む完全5人編成、3／30秒。全68／70／79／81定義と元weapon/config/base-stat hooksを保持し、元public body→実engine_worker→宣言座標worldのnativeを比較します。authored metadata/stat/delay置換はせず、全registered effects/owner/orderとrun identityを検査。観測ラベルはmanagerローカルのeffect/cacheコピーへ隔離し、共有parsed definitionsの汚染を防ぎます。

固定packet `/tmp/nikke-coordinate-original-develop-v2`（ab4b3b25…）、capture `/tmp/nikke-coordinate-original-metal-v2`。M5 GPU実行2.496399秒・PSO cache hit0.003064秒・CPU事前202.573866秒。CUDA/MSL generation cache必須hit。実GPU1、retry0、全8の計算比較は失敗、sealなし。元失敗・claim・rawは保持。containment成功、preservationはnullのままです。

失敗原因は、(1)元world adapterのburst-only traceで短いケースのskill historyが空、(2)30秒のfractional履歴省略が旧decoder未対応、(3)Deltaの元定義7・kind1 named removeがsampled入口未対応。元効果を削らないこと。現checkoutは(1)だけ元編成入口をfullへ訂正し全8input差分がword5だけと検査、(2)は実fractional native観測＋typed prefix/omission検査を追加。保存Marciana30秒でfractional3870＝2048＋1822、team3870＝1024＋2846、最終accumulatorを含む全battle fieldsが一致しました。skill trace／Deltaを含む全体の成功へ読み替えません。訂正後GPU0、次のpacketはnative fingerprintも新規に固定する必要があります。

元経路4 inputの全byte保持、旧340input／291native指紋保持、共通比較器6経路の保存GPU block一致を確認。初期関連37検査、訂正後original/history8、最終共通制御476（Windows1skip）が成功。CPU観測の対象外関数でlocals取得を避け、CLIのdevelopment基準生成にケース別時間を出しました。途中package v1は作成中のtest修正をsource guardが拒否、最終制御v3は外側forbid_gpuがmocked transport検査まで遮断した検証wrapperの問題で、正規runner v4は全成功。原記録も保持しています。

次は既存named remove handlerを新しいoriginal入口のsampled admissionへ接続し、Deltaの実被弾で解除が発火する元編成worldも追加します。その後、訂正済み8＋実解除ケースを固定してMetal、全比較成功後だけfresh seal／source certificateへ進めること。全キャラ認定0／公開UI CPU、packing245/266・base185/203・未対応21profiles/20分類の認定は変更していません。同名damageのowner-aware観測、multi_hit完全group binding、公開受付、現CUDA／warm cacheは残ります。Windows新依頼0。既存チャットを開始できないAPIへ依頼を繰り返さないでください。


## 2026-10-25 元編成10入力・名前指定解除・履歴の厳密な再照合

最新 `docs/portable-coordinate-original.md`／`research/portable-coordinate-original-checkpoint.json`。`coordinate-original`10（全native）がM5全一致・独立fresh監査238.653837秒でsealed登録済みです。元の68／70／79／81全定義とweapon/control/config/base-stat hooksを保持し、3／30秒の完全編成8＋Deltaの実被弾2。新入口は既存共通named-removal handlerへkind1受付を追加するだけ。1.0秒に実stealth1→0、1.1／1.2秒も解除通知、GPU activation3／残存carrier0を確認しました。

GPU packet `/tmp/nikke-coordinate-original-removal-develop-v1`（0d8be0bb…）／capture `/tmp/nikke-coordinate-original-removal-metal-v1` は初8/10。Delta30秒の残2件はprojectile履歴2048の省略55／59を旧decoderが拒否。元raw／失敗／claimは保持。source-bound comparator訂正 packet v2（80575ac3…）へ入力・GPU・native指紋全10を保持し、新native基準計算0で再配布。GPU禁止saved replay v2が全10fresh一致。保持射撃全件のowner／時刻／実method由来mode／pellets／muzzles／予約0と省略件数を検査し、全damage／RNG／packet／最終状態を別途比較。team1024／fractional2048の省略も明示したままです。

新shader GPU1回・4.390048秒、初PSO92.883551秒、CPU事前212.834851秒。同claim retry0／host修正後GPU0。独立監査は別child・live parent receiptなし、全10native domain fresh／GPU0。同じ監査からgoldenとsource-only certificateを作成。現CUDA compile／cache／battle証明へ流用しないこと。旧entryは新macro未定義のCUDA/MSL生成が旧healing基準と一致し、strict normalizerは不変です。

最終sealed配布 `/tmp/nikke-coordinate-original-final-v2.zip`（68e3a051…）は機能53・制御476（Win1skip）成功、終了後に全1904payload SHA／checkout全byte一致を確認。全reader終了後に原とreplay rawをSHA／inode／size保持で4KiB疎化し、各67,231,744byte回収、削除0。旧世代のGPU再実行はしていません。

model-gap監査の旧unconditional座標guardがprivate opt-in導入後のASTを認識できず、frontier検査が失敗していたため修正。既定False・literal bool guardと公開engine_workerのallowed enemy拒否を独立検査し、負例も追加。現在model-checkのoriginal proof/source match true、public admitted／all-char certified false。inventory245/266・base185/203・未対応21profiles/20分類、全キャラ0／UI CPU／目標未達は維持します。

次はfresh監査238.65秒に余裕を作るCPU observerの対象外locals取得削減（world_coordinate_manual_native等）を行い、元編成multi_hit完全group binding・owner-aware同名damage観測・down/revivalとcallback sessionを進めます。ケース削減・時間短縮・監査timeout拡大で解決しないこと。Windowsは状態を1回確認しrev78 idleのまま、新依頼／GPU0。既存送信APIの同じエラーを繰り返し試さず、実行開始可能な状態になってから必要な短い検証だけに使います。


## 2026-10-25 元の同名DoT4・観測filter・group結合の共通化

最新は `docs/portable-original-periodic.md`／`research/portable-original-periodic-checkpoint.json`。`coordinate-original-periodic`4はハラン／クルミ、3／30秒の完全5人編成、全72／70定義保持。元登録のrow IDとownerで同名DoTを照合し、名前だけで最後の定義へ結び付ける問題を解消。30秒で実DoT発火を確認してM5全一致・別process/GPU禁止fresh監査91.144139秒でsealed登録。非周期の同名はまだ明示拒否、death-spread／同時refresh組合せは残件です。

packet `/tmp/nikke-original-periodic-develop-v1`（60a60b66…）、capture `/tmp/nikke-original-periodic-metal-v1`。共通shader／transport／numeric source変更0、生成とPSO cache必須hit、GPU2.361383秒・PSO0.003104秒・CPU事前82.305819秒。GPU1／同claim retry0、source-only certificateは同じfresh監査から作成。現CUDA計算／warm cache性能へ流用しないこと。Windows新依頼／GPU0。

manual observerは対象codeを判定してからlocalsを取得するようにし、元編成10native指紋保持を200.573231秒で確認。新source-ID観測も含む旧healing340入力／291native全指紋保持は148.908552秒。独立監査との同条件速度比較ではありません。全sampled profileの数値・RNG・観測内容は維持します。

`portable_group_binding` を通常group入力と座標元編成で共有し、既存53＋10入力は全byte保持。ベロータ71／ニヒリスター73全定義をprivate coordinateへ静的結合できました。ただしalive／1HP ADDの4native worldは最大1group1対象、2／4対象のmulti_hit通知と子damageは0。元のnative routing／対象モデル不足として残し、all-enemies routingへ置換したり未発火のpackingからGPU認定しないこと。

最終 `/tmp/nikke-original-periodic-final-v2.zip`（519c3343…）は機能32・制御476（Win1skip）成功、終了後に全1911payload SHA／checkout全byte一致を確認。全reader終了後にrawをsize／SHA／inode保持で4KiB疎化し27,000,832byte回収、削除0。データを失った場合はGPU再実行で復元しないこと。

model-checkでoriginal-periodic proof/source match true、全キャラ0／公開UI CPU／全目標未達。次は同名DoTの実死亡spread／refresh、nonperiodicのsource identityが必要な元定義、down/revivalとcallback sessionの組合せを優先し、multi_hitの正本対象展開を別model-gapとして調べます。既存original10・healing340の認定範囲と240秒fresh上限を維持してください。

## 2026-10-26 元編成DoTの別定義発火・死亡通知・tick位相

最新は `coordinate-original-lifecycle`3、`docs/portable-original-lifecycle.md`、`research/portable-original-lifecycle-checkpoint.json`。完全5人編成のハラン72／クルミ70全定義を保持し、ハラン12秒の敵死亡前／感染後2world、クルミ6秒の実バースト再付与を共通GPUへ通しました。元public body／weapon／操作は置換していません。source-aware受動観測は元の発火元と保持timerを区別し、次tick位相を保つ期限更新を確認。既存original比較をcompare_observedへ分け、再計算せず全battle／packet／RNG・周期最終状態を共用します。

固定GPU packet v1 `/tmp/nikke-original-lifecycle-develop-v1`（9134bac1…）とcapture `/tmp/nikke-original-lifecycle-metal-v1` は全3一致。実GPU1回0.965066秒／PSO cache hit0.002735秒／CPU事前43.059290秒。CUDA/MSL generation cache必須hit・compiler0、元生成物と両方全byte一致。GPU source／数値／wire／容量変更0。ハランの別定義row1は負例0／正例2回、クルミrow1は1回、独立timer0を保存readbackでも確認しました。

発火回数を比較器へ追加したpacket v2 `/tmp/nikke-original-lifecycle-develop-v2`（32f78758…）は全input／native／GPU sourceを保持。GPU禁止replay `/tmp/nikke-original-lifecycle-replay-v2` は全3fresh一致。独立sealは47.556235秒、別child・live parent receiptなし・全3native fresh／GPU0。同じ監査からgoldenとsource-only certificateを作りsealed登録。現CUDA compile/link/cache/battleの証明ではありません。GPU retry／観測修正後の再GPU0。

最終compact `/tmp/nikke-original-lifecycle-final-v1.zip`（6b35f276…）は機能13／制御476（Windows1skip）成功。全1914payloadのSHA・checkout全byteとGPU source／全入力・基準の一致を終了後に再検査。旧元編成14inputも全byte保持。最初の手動_tests起動はcapture directory未作成で検査前停止し、失敗logを保持、専用directory作成後のv2で成功。全reader終了後、原とreplayのrawはSHA／size／inodeを保ち疎化し各15,794,176byte回収、削除0です。

重要な分類: ハランの正例はBODY感染中のADD死亡通知であり、現正本の条件は「現在対象の状態」です。死亡敵自身の感染／生存ADDへのspreadを証明しません。召喚攻撃・自爆は既存共通処理があるという初期仮説を調査で否定し、schedulerとactor registryの2guardが未対応として拒否することを確認。guardを外していません。multi_hitの静的結合を対象ルーティング解決へ読み替えないこと。

model-checkは新suiteのproof/source match true、public/all-char false。全キャラ認定0／UI CPU／全目標未達です。次は元nonperiodic同名damage identity、元武器のgroup対象モデル、down／復活・callback session、召喚攻撃payloadの設計へ進めます。Windowsは新依頼0、送信APIのidle制約へ同じrunを再送しないこと。現CUDA／warm cache実測は未取得のままです。

## 2026-10-26 元マナ編成のdown／復活・状態解除とID分類

最新 `coordinate-original-revival`3、`docs/portable-original-revival.md`／`research/portable-original-revival-checkpoint.json`。元マナ編成の全78定義、3秒のcontrol／1回down／2回downを保持。1回目は元「매터 감마」条件で96%HPへ即時復活、条件解除後の2回目は最終HP0。復活定義発火数・旧共通down/revive trace・ammo補充／再開時刻を、既存全battle／packet／RNG比較と合成しました。元public body・weapons・操作・成長を置換していません。

既存world_revive_nativeをcapture/observeへ分け、旧・新でworld_revival_compareを共用。旧復活35input／26native指紋は全保持（0.991313秒、GPU0）。初期テストの架空ロスター名と、96%HPの再測定値を整数96と同一視する期待値を訂正し、元演算順によるbit単位の検査を保持。native／GPUの計算、許容幅は変えていません。元の失敗logとprobeは/tmpへ保持。

GPU packet `/tmp/nikke-original-revival-develop-v1`（942ef238…）、capture `/tmp/nikke-original-revival-metal-v1` は全3一致。実GPU1回0.363236秒／PSO cache hit0.002823秒／CPU事前12.583214秒。生成cache必須hit・compiler0、旧CUDA/MSLと両方全byte一致。GPU source／numeric／wire／容量変更0、retry0。独立sealは15.100126秒、別child・live parent receiptなし・全3fresh／GPU0。同じ監査からgoldenとsource-only certificateを作成しsealed登録。現CUDA compile/link/cache/battleへ流用しないこと。

最終compact `/tmp/nikke-original-revival-final-v1.zip`（691aaa80…）は機能38／制御476（Win1skip）成功。全1913payload SHAとcheckout全byte／GPU source・全input・native・output一致を終了後に検査。既存original17inputも全byte保持。全reader終了後のrawはSHA／size／inode保持で疎化し、削除0です。

model-checkへ全266プロファイルの完全元編成damage-ID静的監査を追加。非周期同名衝突0、周期はハラン／クルミのみ。非周期受付guardは保ち `unobserved-restriction` と分類し、実データの未対応として優先しないこと。元編成の全定義を検査するが、battle／packing／GPUの証明ではありません。cube・成長を任意追加した場合の保証へ拡張しないこと。

アンは元の敵heal_received_pct/all_enemiesが未対応でpacking拒否、効果を削らないこと。ラプンツェル6秒probeはdownあり／復活未発火で認定なし。次は復活の実burst条件／複数候補・敵回復consumer、元武器group対象モデルと召喚攻撃payloadへ進めます。静的inventoryは245/266・base185/203、全キャラ0／UI CPU／目標未達。Windows新依頼0、現CUDA／warm cache未取得。既存idle送信APIへ重複runを依頼しないこと。

## 2026-10-26 元B1復活・センチの共通skill clockとentry-inventory

最新 `coordinate-original-burst-revival`4、`docs/portable-original-burst-revival.md`／`research/portable-original-burst-revival-checkpoint.json`。ラプンツェルの元編成6秒4world（無down／唯一B3 down／N102 down／センチ＋2候補down）を保持。実revive試行と成功を分け、候補2人から1人の復活、81.67%HP・ammo補充／再開を旧共通比較と合成。B3 downの未発火を連鎖条件だと早合点しないこと。直接native観測は最終ゲージ96.39999999999999%、試行0であり、正本は満タンからB1へ入ります。

初回GPU `/tmp/nikke-original-burst-revival-metal-v1` は3/4一致、元センチのkind22だけsampled受付status64。元効果を抜かず、新入口 `gpu/world_coordinate_original_clock_entry.slang` で既存reduceSkillCooldownを接続しました。元の実発火で次deadlineが前倒しされ、GPU発火数と全periodic due/intervalも照合。数値／wire／Runtime容量は不変。新macro未定義の旧入口はCUDA/MSL原生成物を両方全byte保持、source/transport inverse・負例あり。共有raw sourceは変わるので旧goldenのsource一致falseを隠さず、旧goldenの自動書換えもしません。

修正版packet `/tmp/nikke-original-burst-revival-develop-v2`（2b3247aa…）、capture `/tmp/nikke-original-burst-revival-metal-v2` は全4一致。元全4inputと追加clock観測前nativeの指紋を保持、既存GPU3件全21,238,272byte保持。実GPU計2（source変更後の新packet含む）／同claim retry0、初失敗・raw保存。新GPU0.621067秒／初PSO92.846710秒／CPU事前96.088091秒。generation必須hit/compiler0。独立seal103.516777秒、別child・live parent receiptなし・全4fresh／GPU0。同じ監査からgoldenとsource-only証明書を作成。現CUDA/warm cache証明へ流用しません。

最終compact `/tmp/nikke-original-burst-revival-final-v1.zip`（55d35cc9…）は機能39／制御476（Win1skip）成功。全1923payload SHA／checkout全byteとGPU source／input／native／output一致を終了後に確認。既存復活35input／26native指紋も保持。全reader終了後に初失敗・成功のrawをSHA／size／inode保持で疎化、削除0。

新CLI `entry-inventory --out UNIQUE.json` は開発checkout／full package専用。全266元profile準備をID監査と共用し、入力変換・literal kind一覧・全元定義coverageとhashをCPU battle／GPU禁止で出します。失敗を保存／上書き拒否。結果247/266・3.71秒・禁止呼出し0で、GPU受付／計算／全キャラはfalse。legacy world245/266と座標group結合後247/266を混同しないこと。compactでのコマンド実行は拒否し、比較用の関連モジュールだけを保持します。

次の実在優先候補はkind9/10の固有ゲージcharge/consume（15/12キャラ）。入力変換だけを支持せず、既存共通resource handlerのsampled受付・実増減・cap・後続通知と最終readbackを検証します。新入口を実装するときは可能なら共有capability schemaによるCPU側の受付事前検査も用意し、今回のstatus64をGPU前に検出すること。アンの敵被回復量・他kind・元武器group対象モデル・召喚攻撃も残る。全キャラ0／UI CPU／全目標未達、Windows新依頼0・現CUDA/warm cache未取得のままです。

## 2026-10-26 元ゲージ9/10・共有kind受付schemaと早期停止

最新 `coordinate-original-resources`3、`docs/portable-original-resources.md`／`research/portable-original-resources-checkpoint.json`。E.H.全76／ネオン：ビジョンアイ全83定義を元5人編成・weapon・操作・成長のまま保持。E.H.初期資材10→弾倉1→全消費、敵24体死亡後の弾倉4／資材10と実cap clipping、ネオンのburstで100→0を実証。新resource入口で既存共通kind9/10 handlerを接続し、数値／wire／Runtime容量変更0。最終全resourceのpresence／値／base cap／定義別発火数を全battle／packet／RNG比較へ合成。今回のevery_stack通知はnativeもGPUも0で、正の伝播を認定しません。

共通decl `portable_coordinate_kind_admission` からvital guard fragmentを生成し、SlangとCPUの両方で同じkind条件を使用。fragment不一致・未解釈の条件付きprofile macroは拒否。prepare_entriesは明示subset選択後に正例だけを検査し、native基準作成／GPU実行前に止めます。旧ゲージ9/10／旧センチ22／burst-control無効5をCPUで拒否、native開始0・GPU禁止のテストあり。期待されたdomain=NoneのGPU拒否ケースは維持。kindだけの条件であり、全面GPU受付・計算成功を表しません。

entry-inventoryに--suite選択とkind_admissionを追加。resource入口は全266中247入力変換、kind拒否65、禁止CPU/GPU0。247-65をGPU対応率へ変換しないこと。従来world245と座標247も入口差なので分離します。source／compiler／data hashと各元定義／入力hashを保持、compactでcommandは拒否。profile準備とkind policyの読込みは1 invocation内で共用します。

packet `/tmp/nikke-original-resources-develop-v1`（95b08ccd…）、capture `/tmp/nikke-original-resources-metal-v1` はM5全3一致。実GPU1／retry0、GPU0.570817秒／初PSO90.865717秒／CPU事前17.487625秒、生成必須cache hit/compiler0。resource macro未定義の旧clock入口はCUDA/MSL原生成物を両方全byte保持、厳密inverseと負例も成功。共有raw sourceは変わるので旧source readiness falseを隠さず、旧goldenを自動更新しません。現CUDA cache hitや実計算の証明へ流用しないこと。

独立seal20.138357秒、別child・全3fresh・live parent receiptなし／GPU0。同じ監査からgoldenとsource-only証明書を作成。最終compact `/tmp/nikke-original-resources-final-v1.zip`（44c51fa9…）は機能19／制御476（Win1skip）成功。全1929payload SHA／checkout全byteと実GPU source・input・native・output一致を終了後に確認。全reader終了後のrawはbyte/SHA/size/inode保持で疎化、削除0。

次の候補はammo13/14等の未受付kindと、それに依存する元ゲージevery_stackの正の通知。kind受付は共有declを更新し、生成fragmentも更新してから新source/goldenを独立検証すること。既存parent source inverseも維持すること。敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cache、公開GPU／全キャラ認定も未完。全キャラ0／UI CPU／全目標未達。Windows新依頼0、idle送信APIへ同じrunを繰り返さないこと。

## 2026-10-26 元編成ammo13/14・正のゲージ段階通知

最新 `coordinate-original-ammo`4、`docs/portable-original-ammo.md`／`research/portable-original-ammo-checkpoint.json`。元のギロチン：ウィンタースレイヤー79／ノワール74／アルカナ：フォーチュンメイト80／グレイブ83全定義を5人編成・元weapon／成長／操作のまま保持し、6／6／6／16秒。既存共通割合13／固定14 handlerを新ammo入口の受付へ接続。CPUとSlangのkind条件は同じ宣言から生成、数値／wire／Runtime容量変更0。旧resource入口は新macro未定義でCUDA／MSL原生成物全byte保持、厳密inverseと負例も維持しました。祖先baselineに無い新fragmentはinverse後に除去し、元original7検査も成功。旧goldenのraw source一致falseを隠しません。

受動observerは実handler呼出し・戻りと実capacity照会の戻りだけを観測し、stat再照会0。ギロチンは実経験値10通知→レベル2と10.26%補充、ノワールは全5人の39.88%補充と上限切捨て、アルカナは実2／6発補充、グレイブは元状態終了から−100%で104→0を確認。既存全battle／packet／RNG／最終ammoと、共有resource比較器の全ゲージ／通知・定義別発火数を合成しました。正の通知を未発火のまま認定していません。

packet `/tmp/nikke-original-ammo-develop-v1`（ea73aa56…）、capture `/tmp/nikke-original-ammo-metal-v1` はM5全4一致。GPU1回1.706368秒／初PSO92.190548秒／CPU事前60.414598秒、生成cache必須hit・compiler0、retry0。独立seal64.316086秒、別child・全4fresh・live parent receiptなし／GPU0。同じ監査からgoldenとsource-only証明書を作成。現CUDA compile/link/cache/battleへは流用しません。

最終compact `/tmp/nikke-original-ammo-final-v1.zip`（b8fdecda…）は関連23／制御476（Win1skip）成功。全1938payload SHA／checkout全byteとGPU source・全input／native／output指紋を終了後に検査。全reader終了後にrawをSHA／size／inode保持で疎化し27,058,176byte回収、削除0。全266静的inventoryは247packing／kind拒否46（旧resource65）。残り201をGPU対応数としないこと。

次は実在する現在stack増加19（11profile）、解除26（11profile）、stack追加16等を優先し、元定義の実発火とreadbackを確認します。敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cache、公開GPU・全キャラ認定も未完。全キャラ0／UI CPU／全目標未達、Windows新規実行依頼0。既存idleチャット送信APIはユーザー依頼で再試行しても同じactive-turnエラー。検証の重複runは依頼せず、手動開始または実行開始可能な状態になってから既存短い検証の状態／保存結果を取得します。

## 2026-10-26 元編成stack16/17/19・実消費と再充填

最新 `coordinate-original-stacks`4、`docs/portable-original-stacks.md`／`research/portable-original-stacks-checkpoint.json`。元ペッパー73／ルピー68／マルチャーナ：マリンスタディ80全定義を完全5人編成・元weapon／成長／操作のまま保持、6／10／6／6秒。既存共通16／17／19を新stack入口へ接続し、CPUとSlangのkind条件は同じ宣言から生成。数値／wire／Runtime容量変更0。19は上限増加ではなく現在stack増加です。旧ammo入口のmacro未定義CUDA/MSL原生成物を全byte保持、厳密inverseと祖先7検査も成功。

ルピーの実100hitから3→4と15秒duration更新、マリンスタディ開始時1→5・idleで上限維持、宣言ADD6体存在中の3回消費5→2と退出後2→3再充填を観測。ペッパーは対象carrierなしの実無変更として保持。対象解決／stat再照会をしない受動snapshotを使い、既存全battle／packet／RNG／resourceと、全最終stack carrierのsource・membership・stack・activation・expiration、定義別dispatch数を比較。敵stack20/21・init18・shared partial-skip正例へ認定を広げないこと。

初回packet `/tmp/nikke-original-stacks-develop-v1`（3f448b6e…）／capture `/tmp/nikke-original-stacks-metal-v1` は全status0、計算比較2/4。残2はhost比較器の無期限None対display sentinel1e30の誤り。原失敗・claim・raw保持。比較器は実wireの正の無限大bitsを判定し、有限1e30と区別するテストを追加。GPU source／全input／native指紋を保つpacket v2 `/tmp/nikke-original-stacks-develop-v2`（070d292e…）のGPU禁止saved replay `/tmp/nikke-original-stacks-replay-v2` がfresh全4一致。GPU計1回0.956482秒／初PSO92.513740秒／CPU事前40.028685秒、generation必須hit・compiler0、同claim retry0／訂正後GPU0。

独立seal44.644305秒、別child・全4fresh・live parent receiptなし／GPU0。同じ監査からgoldenとsource-only証明書を作成。現CUDA compile/link/cache/battleへ流用しません。最終compact `/tmp/nikke-original-stacks-final-v1.zip`（4eb6f0ce…）は関連22／制御476（Win1skip）成功。全1945payload SHA／checkout全byteとGPU source・全input／native／outputを終了後に検査。全reader終了後に原／replay rawをSHA／size／inode保持で疎化し各27,148,288byte回収、削除0。

全266静的inventoryは247packing／kind拒否30（旧ammo46）。残り217をGPU対応数としないこと。次の実在候補は解除26（11profile）、15、未受付stack18／20／21など。敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cache、公開GPU／全キャラ認定も未完。全キャラ0／UI CPU／全目標未達。Windowsはrev78 idleのまま、新規実行依頼0。既存APIへ同じrunを再送せず、開始可能になったら既存短い検証の状態／保存結果を取得します。

## 2026-10-26 元編成cleanse26・射撃／味方抽選の共有MT

最新 `coordinate-original-cleanse`4、`docs/portable-original-cleanse.md`／`research/portable-original-cleanse-checkpoint.json`。元ココア71定義6秒の対象なし、ココア＋ベスティ75定義16秒の5人→3人の部分解除、ミカ＋ベスティ／ドレイク77定義26秒の全員解除、ロザンナ76定義3秒の敵world通常buff2つ解除／解除不能1つ保持。元の完全5人編成・全効果・weapon／成長／操作を保持。実在するデメリットを使い、未接続のボス攻撃debuff入力と混同しないこと。既存kind26を共通decl／Slangのsampled受付へ接続しました。

初期native正例で整数抽選のRNG観測不足を検出。sampling observerはglobal Randomの実getrandbitsだけを記録し、point内の二重計数を避けます。契約は全draw前後index・値・word数と最終全624語を再現。既存sampling参照5検査成功、旧元マナ3native指紋保持11.916020秒／GPU0。CPU RNG計算・数値規約・canonical本体は変更していません。

GPU前の調査では味方抽選が独立revival bank、座標射撃がCS bankだったため、新入口だけ `WORLD_ALLIED_RNG` で同じCS MTへ接続。recipient計算／診断traceも同じindexを読み、終了時に既存recipient出力へ全632語を写し、2領域を全語比較します。Runtime／wire容量不変、共通Slang／同じテストをCUDA/Metalで使います。旧stack入口は新macro未定義でCUDA/MSL原生成物が全byte一致。厳密inverseはrecipient／program final／diagnostic差分も戻し、normalizerと旧goldenは不変です。旧raw source一致falseを隠さないこと。

GPU前packet v1は未実行。v2 `/tmp/nikke-original-cleanse-develop-v2`（5ac7c508…）、capture `/tmp/nikke-original-cleanse-metal-v1` は全status0、比較は全4world_nodes fields不足で停止。元失敗・claim・raw保持。共通actor-pool decoderへ解除情報を接続し、`world_overlay_node_readback` を通常overlay／actor-pool／新比較器で共用。期待fieldsを削らず、破損flagの負例を追加。GPU source／全input／native指紋を保持するv3 `/tmp/nikke-original-cleanse-develop-v3`（89538b56…）のsaved replay `/tmp/nikke-original-cleanse-replay-v3` が全4fresh一致。GPU計1回2.614522秒／初PSO92.055633秒／CPU事前62.260447秒、generation必須hit・compiler0、retry0／host訂正後GPU0。

独立seal67.274981秒、別child・全4fresh・live parent receiptなし／GPU0。同じ監査からgoldenとsource-only証明書を作成し、現CUDA compile/link/cache/battleへ流用しません。最終compact `/tmp/nikke-original-cleanse-final-v1.zip`（3f2da212…）は関連28／制御476（Win1skip）成功。全1952payload SHA／checkout全byteとGPU source・全input／native／outputを終了後検査。全reader終了後に原／replay rawをSHA／size／inode保持で疎化し各27,115,520byte回収、削除0。

静的全266／247packing／kind拒否22（旧stack30）。残り225をGPU対応数としないこと。次は実在する未受付15／33／23／27等をstat・target・timingまで調べ、依存をまとめて正の発火を検証します。stack18/20/21、ボス攻撃debuff payload、敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cache、公開GPU／全キャラ認定も未完。全キャラ0／UI CPU／目標未達。Windows新依頼0、idle送信APIへ重複runを依頼しません。

## 2026-10-26 entry-inventoryの演算逆引き・依存分類

最新 `docs/portable-entry-operators.md`／`research/portable-entry-operators-checkpoint.json`。共通CLI `entry-inventory --suite coordinate-original-cleanse --out UNIQUE.json` はcompiled rowを実bindingで元sourceへ戻し、type／stat／target／timing／condition／scaling／参照先／field一覧、owner・name・元effect SHAを記録します。`operator_priorities` はプロファイル／元定義／compiled行の数を別々に計数、`kind_dependencies` は同一profileの必要kind集合、`packing_failures` は未変換を分離。対応するsourceが壊れた場合は普通のpacking gapへ変換せず監査全体を失敗にし、失敗保存／上書き拒否を維持。6検査は行順の逆引き、複数compiled行と元定義の区別、分類漏れ、不正provenanceを検証しました。

全266／247packing／未変換19／kind拒否22を26演算記述へ分類、3.790879秒・監査内CPU battle／GPU0。数値code15はresourceではなく `named_buff_duration_extend`、23は `force_reload`、27は `shield_heal_pct`、31は `decoy_heal_pct`、33は `force_skill_use` です。codeだけで次の実装を判断しないこと。33だけでJulia（율리아）の愛蔵品1/2/3、15だけでクラスト／プリカ、両方でサクラが候補になります。次のGPU入口は15＋33をまとめ、元発火と期限／phaseを検証します。

別のCPU調査では元Julia（율리아）77／79／79全定義、3秒・seed3201、愛蔵品1でスキル1の1定義、2/3で3定義が時刻0に実強制発動。元サクラ74全定義もスキル2の2定義が時刻0に発動。元body・全効果・weapon・成長identityを保持し、GPU禁止で観測。observer sourceと結果は `research/entry-operator-evidence/` に保存。これらはGPU受付／計算成功やregression goldenではありません。時計は時刻0で全て未登録だったため、空の前後一致を非空時計の保持証明へしません。最初のSakura probeは非空時計があるという仮説をassertが否定し、原失敗log `/tmp/nikke-original-force-probe-sakura-v1.log` を保持。実部位破壊によるサクラ2状態の延長・最終期限・tick位相は次の未検証項目です。

今回GPU／数値本体変更0、current cleanse goldenとGPU source一致。Metal再実行0／Windows新実行0。前回のMetal実証の未完了分類（ボスdebuff・敵回復・武器groupモデル・召喚攻撃・現CUDA／warm cache・公開GPU／全キャラ）は維持。全キャラ0／UI CPU／目標未達です。新CLIは開発checkout／full package用で、compactのentry-inventory拒否は維持します。

最新の`coordinate-original-source`5は元Julia愛蔵品1/2/3（77/79/79定義・各3秒）と元サクラ全74定義の対照／実部位破壊（各18秒）をM5 Metalで全一致、独立fresh監査68.982秒でseal済みです。共通kind15/33の入口に加え、resident staged scopeの生成書込み欠落をbuffer scopeで修正し、wide敵DoTの対象tupleを持続延長へ接続。元の10段階DoTと旧期限後の実damageを保持。Julia3件の全21,238,272byteと全5入力/native指紋は不変。実GPU計2（失敗1保存、修正版1成功）、retry0、GPU1.538秒／PSO92.290秒。生成/cacheの共通scope検査、実生成物sliceによる負例、機能31／制御476検査成功（Windows1skip）を追加。通常UI CPU・全キャラ0・現CUDA未検証、Windows新実行0。静的packing247/266、kind拒否16で、受付をキャラ認定へ数えません。次は3プロファイルに影響するkind23 force_reloadを優先。[共通source操作と失敗・修正の証拠](portable-original-source-operations.md)。

最新の`coordinate-original-reload`4はミルクのauto／元tap-hold運用を各18秒（81定義）、アスカWILLE15秒（80）、ジル6秒（78）をM5 Metal全一致・独立fresh監査89.704秒でseal済みです。共通kind23を接続し、判定用の予定チャージのfull昇格と、キャンセル充填がlast-full発射時計を更新する漏れを修正。元の期間・定義・武器・既定操作と全4入力/native指紋を保持。先に通った3ケースの21,238,272byteも不変。既存reload observer／readerを共用し、旧46native指紋をsetup観測再利用の単体検査へ追加。機能38／制御476成功（Win1skip）。実GPU計3（失敗2保存・修正版1成功）、retry0、GPU1.927秒／PSO92.539秒。最終生成cache必須hit・Slang0、Windows新実行0／現CUDA未取得。packing247/266・kind拒否13を全キャラ認定へ数えず、UI CPU・全キャラ0・未達。次はkind27盾回復（3プロファイル）を優先。[強制reloadと制御時計の境界](portable-original-forced-reload.md)。

## 2026-10-26 元編成shield heal27・Python観測経路

最新 `coordinate-original-shield`9、`docs/portable-original-shield-heal.md`／`research/portable-original-shield-heal-checkpoint.json`。元ラプンツェル：ピュアグレイス全73／モリ72／キロ74定義、完全5人編成・武器・成長を保持し各6秒×満タン／実損傷と回復後の再被弾／破壊。既存共通kind27を共有declへ接続、反復instantの実timer位相／無期限・全最終shield保存状態・全battle／packet／RNG等を比較。CPU schedule入力0、数値／wire／Runtime138952byte不変。

初版 `/tmp/nikke-original-shield-metal-v1` は6/9一致、ラプンツェル3件はstatus64。診断stage8000／row1で、回復timerより前の「シールド中」条件付きbuffのactor-field受付不足を特定。新入口だけ引数なし・戦闘中のC_SHIELDを検査して既存hasProtectionへ接続。定義／9入力／native指紋は保持し、旧reload入口のCUDA/MSL原生成物は全byte保持、厳密inverseも追加。失敗claim／raw保持、retry0。

凍結packet v2 `/tmp/nikke-original-shield-develop-v2`（9696f5eb…）、capture `/tmp/nikke-original-shield-metal-v2` はM5全9一致。GPU計2回（失敗1・成功1）、修正版GPU1.289189秒／初PSO93.107942秒／CPU事前56.256191秒。generation必須cache hit・compiler0。独立seal60.446405秒、別child・全9fresh・live parent receiptなし／GPU0。同じ監査からgoldenとsource-only証明書を作成。現CUDA compile/link/cache/battle証明へ流用しません。旧成功6出力の全42,476,544byte保持。

CPU観測のC通知が12段のPython専用profile chainへ伝播することを改善。`native_python_profile`は明示opt-inだけでPython call／return順・全比較を保持し、C通知の伝播を止めます。外部／不明callback・明示C consumer拒否、例外復元あり、旧ケース既定False。凍結packetの損傷3件を非filter版と比較し、全native指紋一致、28.490→3.897／54.184→5.871／71.885→7.069秒。新caseに広げる前に同様の全観測一致確認が必要。正本とCPU数値は変更0。

最終compact `/tmp/nikke-original-shield-final-v1.zip`（96d36c82…）は関連20／制御476（Win1skip）成功、全1971payload SHA／checkout全byteと実GPU source・input／native／output一致を確認。sealed generation必須cache hit・Slang0。全raw reader終了後に失敗／成功rawをSHA／size／inode保持で疎化し計99,745,792byte回収、削除0。全266静的inventoryはpacking247／kind拒否10（旧13）、残り237をGPU対応数としないこと。

次の候補は元ビスケット／リリのcover_revive30。decoy heal31、敵stack20/21、init18、蓄積放出等の元定義も残る。現CUDA／warm cache、公開GPU／全キャラ認定も未完。全キャラ0／UI CPU／目標未達。Windowsは既存idle送信APIをユーザー依頼で再試行したが同じactive-turnエラー、新GPU実行依頼0。同じrun再送・UI制約回避はせず、開始可能になったら既存短い検証の状態／保存結果を取得します。

## 2026-10-26 元編成cover revival30・終端診断の乱数副作用

最新 `coordinate-original-cover`6、`docs/portable-original-cover-revival.md`／`research/portable-original-cover-revival-checkpoint.json`。元ビスケット全70／リリ68定義、完全5人編成・武器・成長・autoを保持。各候補なし6秒／実1人破壊46秒／実3人破壊46秒。元再装填中11.6／14.2秒に非貫通の宣言敵攻撃、43.466秒台の次burstで実復活。ビスケットは3人から2人、リリは3人から1人。定義／期間・元効果順と独立抽選を保持し、CPUスケジュール入力0。既存共通kind30を共有declへ接続、数値／wire／Runtime138952byte不変。

初版 `/tmp/nikke-original-cover-metal-v1` は全status0／ビスケット3件一致、リリ3件はMT比較停止。短いリリはnative選択779／GPU780、MT全624語は同じ・末尾1語余分。先頭128履歴全一致、6.0秒のop40診断snapshotが元CPUに無いget_buffs相当の読取りで味方late caster-ATK対象を固定していた。新入口だけ既存nativeNumericDiagnostic規約をop40へ適用し、診断敵ATKの読取りで結果に寄与しない味方late selectorを解決しない。実戦中／明示op39の元順序は維持。RNG巻戻し・比較除外0。元CPUとGPUのlate random未解決状態も検査。

凍結packet v2 `/tmp/nikke-original-cover-develop-v2`（0be6d765…）、capture `/tmp/nikke-original-cover-metal-v2` はM5全6一致。全6input／native指紋は初版から保持、旧成功3出力の21,238,272byte保持。旧shield入口CUDA/MSL原生成物も全byte保持、厳密inverseを追加。実GPU2／照合失敗1保持／成功1、同claim retry0。修正版GPU6.565994秒／初PSO92.013862秒／CPU事前93.599501秒、generation必須cache hit・compiler0。独立seal104.723796秒、別child・全6fresh・live parent receiptなし／GPU0。同じ監査からgoldenとsource-only証明書を作成。CUDA実計算・compile/cache証明へ流用しないこと。

既存Python観測filterを再利用。凍結46秒poolケースを非filter版と各比較、ビスケット58.954→17.435秒／リリ66.683→22.199秒、全nativeとcreation-index指紋一致。旧ケース既定False。最終compact `/tmp/nikke-original-cover-final-v1.zip`（f50db8a4…）は関連26（旧味方抽選6を含む）／制御476（Win1skip）成功。全1974payload SHA／checkout全byteと実GPU source・input／native／output一致。sealed generation必須cache hit・Slang0。全reader終了後に失敗／成功rawをSHA／size／inode保持で疎化、62,390,272byte回収・削除0。

全266静的inventoryはpacking247／kind拒否8（旧10）、残り239を対応数へ数えない。次は既存handler検証用の固定入口とdata-only追加経路でkind受付だけのsource変更によるcache無効化を減らす設計、元ライのdecoy heal31を優先候補。init18、敵stack20/21、蓄積放出34、feather35、弾消費37と19packing失敗も残る。現CUDA／warm cache・公開GPU／全キャラ認定も未完。全キャラ0／UI CPU／目標未達。Windowsは既存chatをread-only確認しrev78 idle、新規run依頼0。API idleへの同じrun再送やUI制約回避は行わないこと。

## 2026-10-26 固定入口・data-only生成再利用・元分身回復31

最新 `docs/portable-original-shared-entry.md`／`research/portable-original-shared-entry-checkpoint.json`。`coordinate-original-shared`6／`coordinate-original-decoy`3は同じ固定Slang入口を使用。既存handlerのkind18/20/21/31/34/35/37をまとめて受付へ接続し、今後のデータ追加によるsource変更を減らします。inventoryは全266／247packing／失敗19／kind拒否0／旧coverから拡張8profileを分離。受付は実戦認定ではなく全キャラ0です。

共通CLI `source-reuse` は不変package・generation receipt・両CUDA/MSLとreflection・consumerを厳密照合し、データ6→3でsource生成pair保持／追加Slang0を確認。CUDA生成改変負例は拒否。Metalは初回PSO93.271503秒→同key/archive必須hit0.002885秒、Rei実GPU0.703215秒。CUDA実cache/launch未検証、keyとnormalizerの緩和0。

元ライ72全定義・完全編成／weapon／成長・各8秒、満タン／実損傷後回復→再被弾／破壊の3ケース。初GPU全status0だがhost期限readerで2失敗。serialized index0とruntime slot2の混同を修正し、全GPU source/input/native/raw保持のsaved replayで全3一致。修正後GPU0、独立fresh3監査14.403379秒、既存6監査103.122062秒。旧cover6の全42MB／旧shield9のnativeと保存readback／旧cover CUDA/MSL全byteを保持。原失敗・claim保持、GPU計2・retry0。

最終packet shared46240e73…（1981files）、decoy3b83f01d…（1993files）は関連22／27と各制御476成功（Win1skip）、全payload bytesとGPU source/input/native/output一致。reader終了後raw3つをSHA/size/inode保持で疎化し62,521,344byte回収・削除0。次は固定入口のまま元stack初期化18等を正発火で検証。残り18/20/21/34/35/37、packing19、モデル／variants、現CUDA／公開GPU／全キャラは未完、UI CPU。

Windows既存chatはrev78 idle。ユーザー依頼の送信再試行もactive-turnエラーで拒否、新規CUDA実行なし。接続確認を再実行成功と数えず、APIへ同じrunを繰り返し送信しないこと。

## 2026-10-26 元ソーダstack init18・固定入口の再利用

最新 `coordinate-original-init`3、`docs/portable-original-stack-init.md`／`research/portable-original-stack-init-checkpoint.json`。元ソーダ：トゥインクルバニー全77定義、完全5人編成・武器・成長・autoを保持し、スキル1レベル1/4/10、各8秒・seed3701。元値表から40/45/50生成→実burst17消費→実射撃で3加算→最終26/31/36。初期作成でstack_reach通知を合成せず、後続の実再加算は通知。元期限・membership・全battle/packet/RNG/control/health比較を保持、CPU schedule入力0。

同じ固定shared Slang入口を使用、GPU source・Runtime・wire・kind受付・数値変更0。既存stack observer/readerを再利用し発火数の対象operation引数だけ追加、旧既定範囲不変。共通source-reuseでCUDA/MSLと両reflection・identity・consumerの全一致、データ6→3・Slang追加0。M5 Metal全3status0・CPU一致、実GPU1回0.734364秒、pipeline同archive/key必須hit0.002836秒、retry0／失敗0。独立GPU禁止childで全3fresh41.951534秒、live parent receiptなしでseal。

最終packet `/tmp/nikke-original-init-final-v1.zip`（d5274558…、1989files）は関連23／制御476成功（Windows1skip）。全payload SHA/checkout bytesとGPU source/input/native/output一致。reader終了後raw21,238,272byteをSHA/size/inode保持で疎化、15,794,176byte回収・削除0。現CUDAのcompile/cache/launchへ成功を流用しません。Windows新規依頼0。

次は元ミハラ：ボンディングチェーンの敵stack追加20、アンカー：イノセントメイドのharmful stack減少21を、元条件と実対象の正例で検証。34/35/37、packing19、モデル／variant・現CUDA／公開GPU／全キャラも未完。静的247/266・kind拒否0を対応率へ読み替えず、全キャラ0／UI CPU／ゴール未達を維持します。

## 2026-10-26 元ミハラenemy stack20・DoT対象接続

最新 `coordinate-original-enemy-stack`4、`docs/portable-original-enemy-stacks.md`／`research/portable-original-enemy-stacks-checkpoint.json`。元ミハラ：ボンディングチェーンの完全5人編成・全77/78/77/77定義、対照4秒／命中上限11秒／実戦闘不能4秒／元burst引継ぎ8秒、seed3801。命中はDrake先頭のautoで元DoTを保持し、10→…→20と上限での再発火を比較。戦闘不能は10＋20を20へ制限、全入力/native指紋不変。CPU schedule入力0。

初版GPU全status0・引継ぎ1件だけ一致。通常actor-recipientに無い専用periodic snapshotのDoT対象がstack操作から漏れ、加算2件が最終10のまま。`world_actor_stacks.slang` の固定shared macroだけ `worldPeriodicNamedMember` を照合し、周期領域へ論理slot／通常recipientへtag付きrefを渡す。変換・clamp・寿命・通知は同じ共通stack loop。旧cover CUDA/MSL原生成物は全byte保持、厳密inverse追加。host DoT期限readerも表示1e30ではなくwire doubleで比較し、無限大と有限1e30の回帰検査を追加。既存stack/source/resource観測器とreaderを共用し旧既定範囲保持。

修正版packet `/tmp/nikke-original-enemy-stack-develop-v4`、capture `/tmp/nikke-original-enemy-stack-metal-v2` はM5全4一致。実GPU計2回（原比較失敗1保持・成功1）、retry0。修正版GPU1.499809秒／新PSO93.950324秒、変更のない対照／引継ぎの全14,158,848byte保持。別GPU禁止childで全4fresh48.621108秒、live parent receiptなしでseal。最終packet `/tmp/nikke-original-enemy-stack-final-v1.zip`（9dd7761e…、1997files）は関連29／制御476成功（Win1skip）、全payload byteとGPU source/input/native/output一致。

初期data-only生成再利用はSlang0、実装修正はsource/keyが変わるためpaired Slang2回・新PSOが必要。共通source-reuseは変更を拒否し、最終同コードpacketはgeneration必須hit・Slang0。新PSOのファイル検査成功は実warm load／CUDA cache証明ではない。数値／wire／Runtime138952byte不変。全reader終了後、原失敗／成功rawをSHA/size/inode保持で疎化し42,074,112byte回収・削除0。静的inventory全266／247packing／19失敗／kind拒否0／受付拡張8は旧分類と全profile一致、GPU認定ではない。

次はkind21。Anchor＋Mast/Moderniaの64秒CPU調査はFB開始4.316667／44.316667の2回、先頭B2 Mast・B3 Drakeの40秒待機を実notifyで確認、減算発火0。記録 `anchor-frontier.json` はPython observer filter opt-inの探索で、同条件正本とのfilter等価性は未監査・golden禁止。次は宣言burst rulesでB2/B3を交互選択する正例と、既定auto86秒候補を確認する（到達は未検証予測）。元ADD/世代に対する今回のDoT stack変更、21/34/35/37、packing19、モデル/variant・現CUDA/公開GPU/全キャラも未完。全キャラ0／UI CPU／ゴール未達。Windows新規依頼0、idle APIへ重複runを送らないこと。

## 2026-10-26 元アンカーharmful stack21・全座標packet履歴

最新 `coordinate-original-harmful-stack`2、`docs/portable-original-harmful-stacks.md`／`research/portable-original-harmful-stacks-checkpoint.json`。元Dora／Anchor Innocent Maid／Drake／Mast Romantic Maid／N102全82定義・完全成長／武器・auto、6秒対照と86秒、seed3901。78.783333秒の実3回目FBで有害stack3→2、membership／activation56.766667／無期限を保持し最終2、対照発火0・最終1。任意controlをgrowth profileへ入れる探索は入力境界に拒否され、その境界を変更せず既定autoを維持しました。

Python観測filterは不変selected-controlコードsnapshotから両adapterケースを準備し、全native＋外側creation indicesを有効／無効で全一致。元snapshotのmanifestはcontrolのみで、whole-suite/GPU証明ではないことをreceiptへ明記。後の完全2入力packetはそのinput/native指紋と一致、86秒観測142.273／42.564秒（同時同値性検査の実測・制御benchmarkではない）。新caseだけopt-in、正本／旧case既定不変。共通CLI `cases` のm.suite不足を `case_names` APIへ集約して修正し、実列挙・simulate禁止を回帰検査。

初GPU `/tmp/nikke-original-harmful-stack-metal-v1` はcontrol比較名のKeyErrorと、長期case約70秒のstatus64。CP raw trace4096が満杯で、native全5031の先頭4096は全word一致。比較器field引数を既存stack readerへ追加し、固定shared macroだけ全packet SHAを有効化。旧raw容量4096とinput109968/output1769856/Runtime138952は不変。64wordをCP_END1305752からのclear-tailに明示割当（次live1310720より前）、全12word（時計を含む）のSHAと先頭rawを共通sampled-parentで検査。raw tail935件は保持せず全件SHAに含む、digestから復元不可・上限1048576。markerありで欠けたheaderへのfallbackなし、markerなしの旧全raw比較維持。clock/prefix/hash/metadata破損・境界・arena・厳密inverseを検査。

容量不足で `/tmp/nikke-original-harmful-stack-metal-v2` はGPU開始前に停止（reserve1GiBは維持）。今回作った5不変snapshotの同一payloadを共有し全hash再検査、ZIP/manifest/結果/raw/claim保持。論理共有226,592,712byte。歴史全体のcleanupはしていません。

修正版packet `/tmp/nikke-original-harmful-stack-develop-v4`（97a4d4e6…）、capture `/tmp/nikke-original-harmful-stack-metal-v3` はM5全2一致。全315/5031packetのordered SHA一致、実GPU9.068120秒／新PSO91.563034秒。GPU計2（原比較失敗1保持・成功1）、storage拒否1はGPU0、retry0。両input/native指紋を保持、control全旧wordは新64word以外全一致、long先頭4096rowも全一致。旧cover CUDA/MSL原生成物も全byte保持。別GPU禁止childで全2fresh52.867548秒・live parent receiptなしでseal。

最終 `/tmp/nikke-original-harmful-stack-final-v1.zip`（db9ccd15…、2010files）は関連32／制御476成功（Win1skip）、全payload hash/checkout bytesとGPU source/input/native/output一致、generation必須hit・Slang0。reader終了後に原／成功rawをSHA/size/inode保持で疎化し20,840,448byte回収・raw削除0。最初のdata-only世代では実Metal cache hit0.002942秒を確認したが計算は履歴上限で失敗、新コードの実warm PSO／CUDAへ成功を流用しません。

静的全266／247packing／19失敗／kind拒否0／受付拡張8は旧全profileと一致。次は元Dorothy/Trony蓄積放出34、Ein feather35、Cinderella Crystal Wave弾消費37を既存共通handlerで正発火へ。今回のADD/世代・減算floorなどの他variant、packing19、現CUDA／warm cache、公開GPU／全キャラも未完。全キャラ0／UI CPU／ゴール未達、Windows新規依頼0。空き容量は依然小さく、次の検証もstorage gateを維持すること。

## 2026-10-26 元Dorothy／Trony蓄積放出34・共有展開

最新 `coordinate-original-accum`4、`docs/portable-original-accumulation.md`／`research/portable-original-accumulation-checkpoint.json`。元各73／74全定義、5人・武器／成長／auto・seed4001、各対照1秒／18秒。Dorothyは上限5.20秒でも放出せず13.366667秒expiryで1回、Tronyはcap到達5.20／8／10.766667／13.533333秒に4回、元split補正／live消費／archive zero／次carrierまで比較。通常のdamage式を通らない元単発のcreation receipt不足を共通observerで修正、着弾時の推定fallbackは増やしていません。既存accum observer/final reader/timer/全battle比較を再利用しGPU本体／数値／wire／Runtime変更0。

不変dev `/tmp/nikke-original-accum-develop-v3`（bf84a224…）→M5 `/tmp/nikke-original-accum-metal-v1` は全4status0・一致、GPU1.741963秒／必須archive pipeline hit0.002726秒。GPU計1・失敗0・retry0。全4fresh独立監査55.963184秒、live parent receiptなし。全4input/nativeは先行対照限定コードsnapshotの探索値と一致。固定shared sourceのままdata-only2→4、共通source-reuseで両CUDA/MSL全byte保持／Slang0。CUDA実compile/cache/launchへ流用しないこと。

最終packet `/tmp/nikke-original-accum-final-v1.zip`（bccd155a…、1990files）は関連26／制御480成功（Win1skip）、全payload SHA/checkout byteとGPU source/input/native/output一致、generation必須hit・Slang0。新共通CLI `unpack --reuse-payload-from` は既存不変packageの全hashとZIP全memberを検査して同一payloadだけhardlinkで共有（最終1986files／56,655,264byte）。manifestは別、参照コード実行0、異なるbyteは個別に展開、両payloadを絶対に編集しないこと。Macの通常644／Windows通常666を対象、Windowsでの新経路実機確認は未取得。

容量reserve1GiBを維持。最初のCPU-only budget不足後、24元編成snapshotのmanifest外Python bytecodeだけを整理し全payload前後hash検査、184,180,736byte割当回収。raw/ZIP/結果/claim削除0。package CLIはsys.dont_write_bytecode、所有子はPYTHONDONTWRITEBYTECODE=1で再増加を抑制（独立import/故障注入は範囲外、最終検査後2cache・425,167byte）。rawは全reader終了後SHA/size/inode保持の疎化で21,561,344byte回収、削除0。空き容量は依然小さいので予算確認を続けること。

新entry-inventory全266／247packing／19失敗／kind拒否0／拡張8は前の全profileと一致。34のBODY代表を実証、ADD/世代・全variantは未完。次は元Ein羽更新35・Cinderella Crystal Wave弾消費37、19packing失敗・モデル不足。現在CUDA／warm cache・Windows Job smoke・公開GPU／全キャラは未完、全キャラ0／UI CPU／目標未達。Windows新規依頼0、idle APIへ重複runを送らないこと。

## 2026-10-26 元Ein羽35・Cinderella Crystal Wave弾換算37

最新 `coordinate-original-owned`5、`docs/portable-original-owned-sources.md`／`research/portable-original-owned-checkpoint.json`。元74／88全定義・5人・成長／武器・seed4101、Ein1/12/40秒、Cinderella3/30秒（公開weapon_mode_swap=True）。Einは初期4枚→burst4.016667秒で6枚→40秒最終2枚、epoch1/2/2と次時計4.16/12.016667/44.016667。実tick・生存枚数分damageを比較、元推定寿命／間隔のLEGACY_WARNING保持。Cinderella対照0／正例8dispatch、40寄与につき追加39通知、部隊累計1737を元200発triggerのraw counterまで検査。実弾／mode／reload／damage全比較保持。CPU schedule入力0。

既存ammo observerをcapture contextへ共用し旧observeは委譲。Ein40秒・Cinderella30秒でplain/observedの全nativeと外側creation indices一致（同時測定・性能benchmarkではない、全5透過性の主張なし）。別に全5fresh監査138.779740秒・live parent receiptなし。dev `/tmp/nikke-original-owned-develop-v1`（71c67141…）、M5 `/tmp/nikke-original-owned-metal-v1` 全status0／一致、実GPU1回3.254542秒、必須PSO hit.002838秒、失敗/retry0。GPU／数値／wire／Runtime変更0、既存4→5のCUDA/MSL全byte保持・Slang0。

最終 `/tmp/nikke-original-owned-final-v1.zip`（25916dd1…、2004files）は関連29／制御480（Win1skip）成功、全payload SHA/checkout byteと実GPU source/input/native/output一致、generation必須hit・Slang0。owned-state readerは厳密AST同一の関数抽出だけで、元prepare/native/witness AST保持。実readbackの小さな状態fixtureでclock1ULP・population/epoch・counter1件等を壊す負例を実行し、長いnativeの重複を避けました。旧ammo referenceの25literal等・観測透過性テストも保持。1990payload／57,182,951byte共有展開、全raw reader終了後SHA/size/inode保持の疎化で26,542,080byte回収・raw削除0。

静的全266/247packing/19失敗/kind拒否0/拡張8は前の全profileと一致。残り20の観測operator分類（code/message/descriptor/lane保持）はoriginal-owned-evidence/readiness-priorities.json。次はprojectile_dmg_pct／shield_dmg_pct／cover_def_pct等、reference-model-gapのtyped基盤を戦闘producer/consumerへ接続する作業を優先。単一観測分類の件数を完了予測に使わないこと。19packing失敗、移動／selector／damage-sharingモデル、ADD／世代・variant、同一現sourceでの旧suite集約、現CUDA／compile cache・Job smoke・公開GPU／全キャラ認定も未完。全キャラ0／UI CPU／目標未達。Windows新規依頼0、idle APIに同じrunを再送しないこと。

## 2026-10-26 元敵弾・HPシールド補正の共通Frame接続

最新 `original-modifier-probe`19、`docs/portable-original-target-modifiers.md`／`research/portable-original-target-modifiers-checkpoint.json`。元の完全5人編成・全効果／成長／武器を保持し、every:2s・係数100の宣言攻撃を1件だけ追加。敵弾側サクラ7.74／アンカー25.6／エレグ59.66／クレイFB前0→後45.05、HP側アスカ601.01／レイ700.5／マリ100.09／ミサト回復前0→後150。別caster・他axisの非混入負例も比較。CPU射撃schedule入力0。宣言V1型付きtargetの元carrier→factor5を検証した範囲で、自動照準／座標／元武器の自動迎撃や全キャラの認定ではない。

loweringとaxis packingを `portable_target_modifier_input` へ共通化し、既存modifier18／shield88と元Rei/Misato8画像のwire SHA保持。エレグ `target_and_nearby:2` はBODY1体・部位／ADD／座標なしを検査したprivate compiler内だけの特殊化。元定義と一般selector拒否を保持。HP probeは別のliteral boss damage／型／所有者／世代違いを拒否。

元敵弾10は独立監査2.472478秒。HP追加初版はアスカ2件status64、元during_shieldのpredicate受付がtyped入口にないことを確認し失敗結果／claim保持。新5行入口 `destructible_original_modifier_entry.slang` が既存の共通predicate受付とhasProtection consumerを有効化。既存GPU本体・数値・wire・Runtime138952変更0。修正版dev `/tmp/nikke-original-modifier-hp-develop-v2`（1d9b9816…）、capture `/tmp/nikke-original-modifier-hp-metal-v2` は全19status0・一致、実GPU1.744037秒／新PSO65.467683秒。別GPU禁止childの全19fresh3.659128秒、live parent receiptなし。計GPU3（敵弾10成功・19失敗・19修正成功）、retry0。

元10の全input/native・41,943,040byte出力完全一致。失敗19から修正したのはアスカindex10/11のみ、他17全word一致。旧typed sourceの単体監査に厳密な既知receipt inverseを追加した際、全監査合成で二重適用を検出。inverseを単体verify_retained_sourcesへ限定し、既存の全hash/literal検査を維持。失敗CPU control記録も保持。GPUの再実行不要。

最終 `/tmp/nikke-original-modifier-final-v2.zip`（b7178643…、1956files）は関連45／制御480成功（Windows専用1skip）。全payload SHA/checkout byte・元GPU source/input/native/output一致。共通source-reuseで監査修正前後のCUDA/MSLと両reflection・identity・consumer全一致、generation必須hit・Slang0。初版19のPSO必須hit.002517秒は計算失敗だったため成功cache実証へ流用しない。新shaderのwarm PSO／CUDA実compile/cache/launchは未証明。

全reader終了後、3rawをSHA/size/inode保持で疎化し146,669,568byte回収、削除0。manifest外の再生成可能Python bytecodeだけを93旧snapshotで整理し、payload全hash前後検査・453,578,752byte割当回収。ZIP／source／結果／raw／claim保持、reserve1GiB維持。

静的coord entry全266／247packing／19失敗／kind拒否0／拡張8は保持。別のcanonical compilerは245packing、観測20分類のcode／message／descriptor／lane／件数は旧記録と完全一致し、今回の宣言probe実証を添付しただけ。20分類はreference_model_gapのまま、packingをGPU対応率へ読み替えない。次は型付き対象consumerを共通座標resident・自動aimへ合成すること、cover_def_pctのincoming-coverモデル、selector／移動／damage-sharing、ADD世代／variant、同一現sourceへの旧suite集約と現在CUDA。全キャラ0／UI CPU／目標未達。Windows新規GPU依頼0、idle APIに同じrunを繰り返し送らないこと。

## 2026-10-26 共通座標Runtimeへの型付き対象Frame合成

最新 `coordinate-typed`10、`docs/portable-coordinate-typed-targets.md`／`research/portable-coordinate-typed-checkpoint.json`。元マルチャーナ3秒対照と、元Sakura／Anchor／Clay／Asuka／Rei／Mari／Misatoの完全5人編成・全効果／成長／武器を保持。宣言typed targetとevery:2s・係数100の追加攻撃1件を、元の座標射撃と同じRuntime／WorldSchedule／DFSへ接続。Clay3/12秒・Misato3/30秒で条件成立前後を検査。型付きへの自動aim／座標shapeの武器迎撃は未実装、Eleggのnearby座標selectorは閉世界の特殊化を流用せず未対応保持。公開GPU／全キャラの認定ではない。

入力109968＋5712＝115680word、出力1769856＋262144＝2032000word。旧座標領域は保持し、typed state／clock／128receipt／DFS scratchを末尾へ配置。Runtime138952byte不変。既存typed処理をhooks/implへ抽出し、旧入口と新 `world_coordinate_typed_entry.slang` で共有。型付き攻撃も既存sampled skill frameの共通RNGを使用、CPU schedule入力0。binary64／core_probability・正本・strict normalizer不変。旧source監査は全file hashを固定したinverseだけを追加。

初CPU探索でscalarラッパーのbuffs観測不足を修正。座標body着弾を抑止した型付きpacketは、元traceの時刻／owner／source／係数／damage／完了数を型付きreceiptへ明示対応させて別比較。CLI live-parent再利用にも両receipt集合の欠落／重複／改変検査を追加。初capture v1はそのcontext検査でGPU前に停止、v2は容量gateでGPU前に停止。どちらも結果／package保持・GPU0・claim削除0。

dev `/tmp/nikke-coordinate-typed-develop-v2`（f1b700f2…）、M5 `/tmp/nikke-coordinate-typed-metal-v3` は全10status0・CPU一致、実GPU2.299065秒／初PSO92.531390秒、generation必須hit・Slang0。別GPU禁止childで全10fresh111.541363秒、live parent receiptなしでseal。元の座標battle・physical packet・RNG・allied health／gauge・元定義／通知を比較し、typed攻撃数は対照0／3秒各1／Clay12秒5／Misato30秒14。

旧座標入口のCUDA/MSLと両reflectionは既存strict比較で一致。旧typedはアドレス式の抽出等で生成コードが変わったため、保存結果へ成功を流用せず、別のMetal19入力を1回実行。全19一致、GPU1.820227秒／初PSO66.785972秒、独立fresh3.735670秒。旧19の全79,691,776byteが保存結果と完全一致。GPU計2・計算失敗0・retry0、Windows新規GPU依頼0。

最終 `/tmp/nikke-coordinate-typed-final-v1.zip`（a59582ac…、1971files）は関連53／制御480成功（Windows専用1skip）。最終変更は配置ツール・分類とreserved/counter検査。prepare/native/partition AST・native producer filesの一致、比較器がreserved検査2文の追加だけであることを検査し、完了済みfresh native監査を再利用。全payload SHA/checkout bytes、全10input/native/sourceと各出力SHA、最終reserved/counter検査を保存readback全件へ適用。新nativeを再計算したCPU preflightとは主張しない。新GPU実行0で最終検査済み。

`arena-check --profile coordinate-typed-v1` が新しい全領域の所有・重複・consumer sourceを検査。reserved領域／counter context破損の負例も追加。共通source-reuseは修正前後のCUDA/MSL・reflection・identity・consumer全一致、最終generation必須hit・Slang0。新PSOのwarm hit／CUDA実compile/cache/launchは未証明。caseを増やすだけの次の検証は同じ固定入口を使い、生成・pipelineの再構築を避けること。

全reader終了後に両rawをSHA/size/inode保持で疎化し120,651,776byte回収・削除0。130旧snapshotのmanifest外・再生成可能Python bytecodeだけを整理、全payload前後hash検査、451,768,320byte割当回収。source／ZIP／結果／raw／claimは保持。reserve1GiBを維持すること。

静的全266profileの行／packing失敗／kind依存は前記録と完全一致。coord247packing／19失敗／kind拒否0／拡張8、canonical245packing・20分類のcode／message／descriptor／lane／件数も保持。private座標typed証拠だけを分類へ添付し、20はreference_model_gapのまま。次は型付き対象のidentity／livenessと座標shape・selectorの接続、その後の自動aim／武器consumer。cover_def_pct／移動／damage-sharing、ADD世代・variant、現CUDA／公開GPUも未完。全キャラ0／UI CPU／目標未達。Windowsのidle APIへ重複runを送らないこと。


## 2026-10-26 型付き自動照準のCPU契約

共通CLI `reference --suite coordinate-typed-aim-common` を追加。元完全編成・全定義・武器・成長を保持し、明示 `typed-before-body-v1` のframe候補をcanonical調停器へ接続。fallback/期限切れ、散弾破壊後の次frame、手動canonical/typed、ADD優先、元実FB追従の6正例と、元Reiの `enemies_nearest_in_range` を最初のframe前に拒否する1件。ordinary skill geometry/cacheと元定義登録一致検査を保持。詳細 `docs/portable-coordinate-typed-aim.md`。

最終CPU package `/tmp/nikke-typed-aim-cpu-v3`（620ab20e…）。全7契約30.986秒、関連unit6件32.980秒、制御49group成功。既存46/native29のCPU回帰106.740秒・関連74成功、全入力byte/golden保持。v2→v3は新CPU照準の報告・分類・テストのみ4file差分、既存producer/compiler/comparator不変をreceiptへ固定。358 Slang・正本/数値/cache等8保護fileが前Metal最終packageと全byte一致。新GPU0、旧Metal46の成功を自動照準成功とは数えない。

次は共有wire/consumerへ接続。BODY0/canonical1..127/core128を保持してtyped129..256、focusの8bit packingを専用profileで9bit×5へ更新する必要がある。slot容量削減/alias禁止。frame候補固定・元timed skill/調停順・前frame照準queriesを保持。現在compilerは新policyを明示拒否し、current-enemy recipient規則は未対応のまま。classification reference_model_gap／全キャラ0／UI CPU／目標未達。Windows idle送信を再試行したがactive turn不足で拒否、開始未確認・新規検証0。


## 2026-10-26 型付きframe照準の共通GPU consumer

最新sealed `coordinate-typed-aim`59（native36／拒23）。`docs/portable-coordinate-typed-aim.md` と `research/portable-coordinate-typed-aim-gpu-checkpoint.json`。旧46をすべて保持し、CPU正例6と全128slotを使う手動最終slotを追加。型付き候補をframe開始時に固定し、元の手動／camera／実FB追従を共通Slangへ接続。BODY0／canonical1..127／core128／typed129..256／内部ADD257、専用focusは9bit×5owner。手動wireの257／未宣言／範囲外とフラグ不整合を拒否。ordinary skill geometry/cache、元の完全編成・定義／所有者／順序／武器／成長を維持。

初package作成は準備済み入力を再準備する契約のKeyErrorを検出し、raw／prepared両方を扱うよう修正。GPU0。初Metal試行はsandboxでdevice不可視・CPU/GPU前に停止、claim未消費。アクセス可能な環境の実初版 `/tmp/nikke-typed-aim-metal-v2` は58一致／ADD優先1差分。focus有効時に旧論理ADD sentinel0をBODY0として読んでいたため、専用257と物理recipient decoder・比較器を同時に更新。旧GPU結果／claimを保持した。

修正版dev `/tmp/nikke-typed-aim-gpu-develop-v3`（884ef54a…）、capture `/tmp/nikke-typed-aim-metal-v3` は全59一致。GPU3.877019秒／新PSO93.967664秒、生成cache必須hit・追加Slang0。別GPU禁止childの全59 fresh独立監査172.055948秒、live parent receiptなし。実GPU計2（失敗1／成功1）・retry0。修正前後59のnative全指紋保持、入力変更は境界の期限だけindex52、実readbackの変更はADD index50のみで他58全word一致。元の旧46全373888000byteも保存結果と完全一致。実最終focus ID256を確認、candidate世代／ID／stream digest／9bit focus／未使用tail／全照準frame digestの6破損をすべて拒否。

最終 `/tmp/nikke-typed-aim-final-v1.zip`（36acee7f…）は論理BODY／ADD名をtyped labelへ使えない追加拒否guard・seal登録・分類を反映。3guard行を除くと実行版のCPU producer全byte保持、全CLI関数ASTとGPU／数値／transport完全一致。最終CPU-only全59/native36は137.954392秒で成功、関連78／制御488成功（Win専用1skip）。全59 input/source/native・payload byteを実行版へ固定し、新GPU0。最終generation必須hit・Slang0、sealed CUDA/MSL生成物一致。PSO archive作成を現在CUDA compile/cacheや新shaderのwarm load成功へ流用しないこと。

入力115680／出力2032000word、Runtime138952byte不変。typed tail220224から544wordだけをframe候補へ割当、既存物理history／overflow／DFS所有を保持。`arena-check --profile coordinate-typed-aim-v1` で監査。全reader完了後、初失敗／成功rawをSHA/size/inode保持で疎化し、計775028736byte回収、raw／claim削除0。新しいmanifest外bytecodeの大掃除は行わない。

今回の自動照準は明示typed-before-body-v1の私有モデル。分類にはscoped GPU証拠だけを追加し、ゲーム仕様reference_model_gap／全キャラ0／UI CPUを維持。次は元Rei `enemies_nearest_in_range` 等のcurrent-enemy recipientとtyped owner規則を、元定義を落とさず接続。移動形状・他caller／variant、19packing失敗・残るモデル、現CUDA／warm cache・公開GPU／全キャラも未完。Windows新規GPU依頼0。idle送信APIのactive turn不足が既知なので、重複runを送らない。


## 2026-10-26 元Reiの現在対象ダメージ・typed照準合成

最新sealed `coordinate-typed-actor`67（native40／拒27）。`docs/portable-coordinate-typed-actors.md`／`research/portable-coordinate-typed-actor-checkpoint.json`。旧59を全保持し、元Reiの完全5人・73全定義・元武器／成長で1秒対照と12秒BODY／ADD／手動typed＋ADDの4契約を追加。元S1 `선두 제압 2` の `hit_count:100`／`enemies_nearest_in_range` は0／5／5／5回実発動。BODYと手動typedはBODY、ADD autoは先頭の実生存ADDへ着弾し、元traceとpacketの全時刻・量・数・recipientを照合。定義削除／追加probe／CPU射撃scheduleは0。

`typed_actor_policy={"mode":"canonical-current-damage-v1"}` とcompilerの明示opt-inで通常current damageだけを元canonical敵選択へ接続。policy無しの旧gap検査を維持、敵buff／状態変更／typed所有権継承と対象条件は未対応guardを維持。CPU validatorをnative登録／compilerで共用し、GPUにもcurrent enemy fieldの拒否を追加。typed header15=1はweapon13／frame aim14／live aim11を必要とし、旧9bit namespace・arena・input115680/output2032000/Runtime138952を保持。source監査は既知full-hash inverseだけ追加。数値・正本・strict normalizer・CUDA compile cache本体は不変。

最初のCPU契約はBODYの敵選択関数query数で発動を判断して失敗。BODY直接着弾はqueryを呼ばないため、既存の実packet／元traceによる発動・着弾検査へ修正。4件reference42.011秒で成功。観測は元実resolverの受動wrapperだけ、queryの追加呼び出しは0。

実行dev `/tmp/nikke-typed-actor-gpu-develop-v1`（103f948f…）、capture `/tmp/nikke-typed-actor-metal-v1` はM5全67一致。CPU preflight185.208515秒、実GPU4.069825秒／新PSO94.331620秒、生成cache必須hit・実行時Slang0。GPU1回、失敗/retry0。GPU禁止のfresh独立監査223.096155秒は全67／native40一致、live parent receiptなし。旧59の全input/nativeと479552000byte出力を保存結果へ完全一致。実readbackのrecipientを構造上一貫した生存ADDへ差し替える負例、amount/landing-clockの1ULP差、source row改変をすべて拒否。

最終 `/tmp/nikke-typed-actor-final-v1.zip`（959199e6…）はseal登録とscoped分類の2file差分＋goldenだけ。全native producer／tests/data／GPU/transport全byte保持、全CLI関数ASTと全67prepared input/source/nativeを固定して同じfresh監査を再利用。最終版の新CPU preflightを実行したという主張はしない。最終関連84／制御488成功（Windows専用1skip）、最終generation必須hit・Slang0／sealed CUDA/MSL一致。全reader終了後rawのSHA/size/inodeを保持して疎化、439025664byte回収、削除0。

新しい固定入口へdata-onlyケースを追加するときは、既存の生成／pipeline identityを保持して再構築を避ける。今回のarchive作成を現在CUDAのcompile/cache/launchやwarm Metal成功へ流用しない。次はcurrent enemy field／mutationとtyped event所有権・対象条件、他caller／世代・移動形状・skill/weapon同時interception。現CUDAと19packing失敗等の残るモデル／公開GPU／全キャラも未完。scoped証拠だけ分類へ追加し、reference_model_gap／全キャラ0／UI CPU／目標未達を維持。Windows新規依頼0、idle APIへ重複runを送らない。


## 2026-10-26 型付き所有者fieldのCPU基盤

`coordinate-typed-owner-common`5。詳細 `docs/portable-coordinate-typed-owner-reference.md`、`research/portable-coordinate-typed-owner-reference-checkpoint.json`。明示body-owned-current-fields-v1はbinding kind2/3とowner[0,0,1]必須。exact物理世代からlogical BODYへのqueryだけを投影し、event/impact handleを維持。未所有／ADD所有／異なるBODY世代／古いtyped世代を拒否、例外時patch復元。元Prim全71定義・完全5人・武器／成長を保持、1秒対照／8秒BODY／ADD／手動typed。別のcounter監査には原本後に明示2効果だけを追加し、実HPshield命中→counter完了→子buffを実行。camera ADDでも子fieldは所有BODY、実received query BODY17／両ADD0。元current fieldは0/1/1/1/1。

不変CPU package v5 c106fbb2…の全5reference37.628665秒、最終owner unit5／関連84／制御488成功（Win1skip）。旧67/native40回帰はv4 e862a114…で181.761955秒、全prepared inputとgolden保持。最終31724c3b…はreadiness＋owner契約強化のみ、全5保存nativeとinput SHA照合後に強い契約を再監査しnative新生成0。362 Slang／保護正本・数値・cache・backend全byte保持、既存67 generation必須hit・Slang0。owner policyは旧GPU compilerで明示拒否、新GPU／Windows依頼0。共有Slang consumer/wireへ接続する前に、全ケースを保持してbounded fresh auditを分割集約できる共通CLI経路を整備すること。旧67独立監査223秒のためケース削減やguard緩和で済ませない。ゲームgap／全キャラ0／UI CPU／目標未達。


## 2026-10-26 全範囲fresh native監査の分割実行

共通CLI seal/replayに明示comparison-group-sizeを追加、既存比較器を再利用。部分結果はcalculation_verified=False、全index順序・重複／欠落・拒否・全体raw/input/generated／各native指紋・transport・immutable anchorsを集約して初めて全件成功。childはGPU禁止・ライブ親oracle0、各child上限1〜240秒、逐次。既存未指定経路は維持。最終版は各group stdout/stderr/部分JSONと失敗またはaggregateを別temp captureへ保持。

実測development22d968b4…、保存Metal出力の全67/native40/拒27を24/24/19で実行し76.032/72.987/89.328秒、各180秒内。総239.598秒は旧単一child223.096秒より増加し、総短縮の主張なし。旧sealed67の全input/native/output/generated goldens完全一致、GPU新実行0。最終b58926cf…の差分はログ・失敗保存helperと追加unitのみ、native producer/比較器・他CLI関数AST保持。最終新12／seal8／関連84／制御500成功（Win1skip）、generation必須hit・Slang0。新しい全67 native再生成を最終版で行ったとは主張しない。原本/claim保持、全reader終了後の新replay raw疎化で439025664byte割当回収、raw SHA/size/inode保持・削除0。詳細docs/portable-comparison-groups.md、research/portable-comparison-groups-checkpoint.json。

次はbody-owned-current-fields-v1を専用共有entry/headerへ接続し、元Prim全71と実counter完了子fieldをMetal比較。旧67はすべて保持、新ownerケースを含め全範囲group監査を実行すること。GPU本体・数値・正本・strict normalizer・CUDA cache本体は今回不変。現在CUDA、ownerのGPU、ゲームgap／全キャラ0／UI CPU／目標未達。Windowsへの新規依頼0、idle APIへ重複runを送らない。


## 2026-10-26 BODY所有fieldを共通GPUへ接続

最新sealed coordinate-typed-owner80/native45/拒35。docs/portable-coordinate-typed-owner-gpu.md、research/portable-coordinate-typed-owner-gpu-checkpoint.json。元Prim全71・完全5人・武器/成長、対照/BODY/ADD/手動typed/counterの5ケースを追加し旧67保持。body-owned-current-fields-v1はheader12=1/15=2とweapon13/aim14/live11必須、kind2/3・owner[0,0,1]を明示。物理kind/id/genは不変、field/対象条件queryだけ同世代DT→BODY。通常current damageはcaster canonical aimを維持。CPU compilerは明示owner counterの論理validator viewだけを投影、正本guard・実命令不変/例外時復元。strict full-hash inverse追加のみ、normalizer/数値/cache本体不変。Runtime138952、input115680/output2032000word保持。

実GPU dev cf44aa64… capture /tmp/nikke-typed-owner-metal-v2、CPU preflight223.683332秒、Apple M5実GPU4.041898秒、library1.930172/pipeline93.763491秒、generation必須hit/実行時Slang0。初比較は新5だけCPUにnonzero_immunity_used空リストがなく失敗。全field/recipient/子fieldは既に一致。observe_actor_statusを追加し、5native再観測で追加キー以外の全hash一致、全入力/GPU/transport/正本を固定した専用migrationで保存結果を再監査。比較削除やnormalizer緩和0。

修正immutable /tmp/nikke-typed-owner-gpu-replay-v4（4754c201…）の共通replay全80/native45 fresh監査294.003520秒、24/24/24/8 childが78.245/73.308/135.965/4.863秒、各180秒内、live-parent oracle0。元field0/1/1/1/1、別宣言counter監査2効果の実HP3/id10/gen1命中→完了→子fieldはcamera ADDでもBODY17/両ADD0。物理receipt/skill trace/RNGも比較。goldenは同じshared grouped auditの結果を登録、sealコマンド再計算0。旧67全input/nativeと544576000byte raw完全一致。GPU計1/retry0、追加GPU/Windows0。元failure/claim保持、reader終了後のSHA/size/inode保持疎化で525991936byte回収。replayの明示reuse-source-bytesはhardlink共有、全hash再検査、cross-device copy fallback0/失敗保存/通常copy維持。

最終immutable /tmp/nikke-typed-owner-final-v1（93ea25a5…）はseal登録/golden/scoped readinessのみ、全CLI関数ASTと全native producer/tests/GPU、80golden保持。最終関連100/制御507成功（Win1skip）、旧replay6成功、generation必須hit/Slang0。最終版で新fresh native preflightを実行したという主張なし。固定migrationはv4自身のCLIから使うこと、現在の追加変更は厳密source表で拒否。

次は固定同entryへdata-onlyでprojectile所有field、破壊済み同世代/再登場・古い世代counterを追加。これらは今のGPUでは未実証としてreadinessにFalseを明示。入力kind2許可をbattle実証へ数えない。新shader warm load/現CUDA compile-cache-launch、ADD所有/移動/他caller/variant、残るモデル/19packing失敗/旧suite現source集約、公開GPU/全キャラ未完。全キャラ0/UI CPU/目標未達。Windows idle APIへの重複runは送らない。


## 2026-10-26 所有者の寿命・世代88とwarm Metal

最新sealed `coordinate-typed-owner-lifecycle`88/native53/拒35。docs/portable-coordinate-typed-owner-lifecycle.md、research/portable-coordinate-typed-owner-lifecycle-checkpoint.json。旧80保持、元Prim71全定義・完全5人・武器/成長、projectile所有field・破壊済み同世代query・再登場gen2 counter・late stale marker抑止・手動projectileの8入力を同じ共有entryへ追加。物理handle／BODY論理query／実counter子field／生死観測を照合。staleは1.25sにgen1 markerを実arm、後続世代で完了しないことを証明。内部不正contextのerror64直接実証／ADD所有とは区別。GPU source/transport/数値/正本/normalizer/cache consumer不変。

実dev dcd09db2… capture /tmp/nikke-owner-lifecycle-metal-v1、CPU preflight297.821087秒、M5 GPU4.110688秒、library0.005774/pipeline0.002903秒。generation必須hit/Slang0、pipeline必須hit/archive compile0。初86/88差分はcounter markerを通常fieldへ列挙したdecoder2箇所。既存enemy_buff_plan分類へ統一しcounter資源比較は維持、native計算変更0。strict comparator refreshで全88input/native/GPU保持、修正replay8d9c2cf1…から保存rawのfresh全88/native53を4group（79.901/75.157/137.232/90.120秒、各180秒内）、計384.476683秒で成功。同じ監査でgolden登録、seal二重実行0。旧80の650240000byte raw完全一致。GPU1/retry0/追加GPU0。reader完了後raw SHA/size/inode保持疎化で573636608byte回収、失敗/claim/raw削除0。

最終 /tmp/nikke-owner-lifecycle-final-v1（1f1c15b6…）はseal/readiness/goldenと非Mac filesystem unitの4file差分。全CLI関数AST/native producer/comparator/GPUと全golden保持。最終関連106／制御517成功（Win専用1skip）、generation必須hit/Slang0。最終fresh native再生成は未実行。固定comparator migrationはv3自身のCLIで使うこと。

容量不足対策は共通compress-generation-cacheを追加。macOS派生JSON371entryの全key/byte/SHA/4artifactを保ち、割当2651963392→534904832byte、2117058560byte回収。元generation consumer/identity不変、固定packageの必須hit確認、compiler/GPU0。sandboxコピーの不正candidateは公開前拒否し原本保持。Windows操作／driver cache／latency証明ではない。docs/portable-cache-filesystem-compression.md、research/cache-filesystem-compression-evidence/。

次は未対応のADD所有／対象操作をCPU契約から共通実行器へ接続。ゲームgap/移動/他caller/variant/19packing失敗/現source全suite集約/公開GPU/全キャラは未完、全キャラ0/UI CPU/目標未達。Windows新実行0、idle API再試行もactive turn不足で失敗、coordinate-landing依頼は未送信。既存runの再送をしない。


## 2026-10-26 ADD所有者のCPU契約

`coordinate-typed-logical-owner-common`3を共通CLI referenceへ登録。docs/portable-coordinate-typed-logical-owner-reference.md、research/portable-coordinate-typed-logical-owner-reference-checkpoint.json。明示logical-owned-current-fields-v1だけ、型付きworldのproviderを実戦registry_for(manager, world.clock)へ登録し、直接BODY/ADD所有者のexact世代をquery。初v1は独立typed registryのためUnknown actorで失敗、失敗保持。旧BODY policyの意味/拒否は維持。未spawn/未知/古いADD世代は拒否、同世代の生死で所有者を消さず物理event/handle不変。root/label推測/BODY fallbackなし。

元Prim全71・完全5人・武器/成長を保持し、別宣言counter2効果のHP shield/projectile/破壊済みshield3契約。通常元fieldはADD0、counter実完了のtarget_is_add子fieldは宣言ADD1[5,1,1]、receivedはBODY/ADD0/ADD1=0/0/17。v3新3は29.037947秒、旧BODY5は39.236259秒、旧寿命8は72.773368秒成功。旧13のinput/native/trace全SHA保持を前snapshot/既存結果へ照合。

最終 /tmp/nikke-logical-owner-cpu-v4（8183df99…）はv3からunit fixture1fileのみ修正。typed-only初期registryを再現、実helper/producer/comparator不変。最終関連113/制御517成功（Win1skip）、generation必須hit/Slang0。Slang/upstream/正本/数値/transport/CUDA cache本体全byte保持、GPU/Windows0。最終native再生成なし、証拠はv3 producerとの全byte一致に固定。

次は共有SlangのtypedOwnerContextTargetをexact logical actor pool slot/genへ接続し、counterContextAddも同ownerを使う。新wire flagと旧BODYflagを区別、compiler predicate検査viewも宣言ownerへ投影、元実命令/handleは保持。現GPUcompilerは新policyを明示拒否。旧88保持でMetalをfresh全監査。ADD Metal/CUDA/dead ADD実戦field lifetime/ADD再登場battle/ゲーム仕様/公開consumer/全キャラは未完、全キャラ0/UI CPU/目標未達。Windows idle送信を重複しない。

## 2026-10-27 ADD所有者Metal99・一時領域消失と回収

共通Slang logical ownerを接続し、99/native56/拒43のM5通常比較と別child5つのfresh独立監査に成功したことを観測。元Prim71/完全5人/武器/成長を保持、通常field ADD0・宣言owner ADD1、received=0/0/17。header12=3/15=2を新policyに限定、旧BODY12=1と旧拒否12=2保持。physical kind/id/genは保持し、counter条件とfield recipientを同じactor pool exact ownerへ解決。数値/正本/upstream/normalizer/CUDA compile cache本体不変、backendはentry whitelist追加のみ。

初版HP guard失敗を保存rawで診断し、新logical weaponだけ受付を修正。修正版2b99038d…は全99期待値不変、旧88全715264000byte保持、変更rawは88/90/95。CPU preflight327.520719秒、GPU4.182172秒、pipeline94.638508秒、child103.824826秒。世代拒否95は実landing/counter後、owner要求2/実1で64。fresh監査418.076018秒、各180以内、同じ監査からgolden/source certificate生成。最終metadata726ddf4c…は登録等4file差分、関連117/制御517成功（Win1skip）。GPU計2/retry0、CUDA/Windows0。

その後の実行環境更新後、/private/tmpのworktree・capture・ZIP・cache、TMPDIRの監査receiptが見えなくなった。原因未確定。Git indexから17fileを回収し19df7cafへコミット。golden/source certificateは元Git blobと一致。元rawとcaptureは未回収のため、現在のreplay成功やraw保持を主張しない。失われた証跡ファイルを偽って再作成せず、過去のツール観測と新しいCPU検査の出所を分ける。GPU再実行による復元はしない。

現在のworktreeは /Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/runtime-resident。永続proofは同親のproofs/logical-owner-20261027、永続generation cacheはcaches/slang-generation-v1。source/docsの固定pinned upstreamをprimaryからコピーし、GAMEPLAY/timelineの既存source contract SHA一致を確認。現在のCPU検査とCUDA/MSL生成基準一致/必須cache hitは別記録。readinessはhistorical success/raw unavailable/current host GPU未確認を明示。詳細docs/portable-coordinate-typed-logical-owner-gpu.md、research/portable-coordinate-typed-logical-owner-recovery.json。

次はADD実生死・再出現/field lifetimeの新契約へ進む。raw再監査は原本復旧まで停止。今後の新しい成果を一時領域だけに置かない。現CUDA/新sourcewarmMetal/ゲームgap/公開consumer/19packing失敗/全キャラは未完、全キャラ0/UI CPU/目標未達。Windows idleへの重複依頼なし。

## 2026-10-27 ADD所有者のgraph退場・再出現CPU4契約

`coordinate-typed-owner-add-lifetime-common`4を共通referenceへ追加。docs/portable-coordinate-typed-owner-add-lifetime-reference.md、research/portable-coordinate-typed-owner-add-lifetime-reference-checkpoint.json。元Prim71全定義/完全5人/武器/成長と8秒を保持。別宣言counter2効果で、発動前退場・発動後退場・旧field非継承・gen2所有者への発動を検査。再出現はuntil1s/repeat0で最終gen9が生存中、旧gen1/gen2 fieldのreceived=0。physical id10/gen1、子fieldの宣言owner世代を保持。graph終了の退場であり、HPダメージ死亡とは区別。

受動observerは既存OwnerQueries.projectとDestructibleWorld.synchronizeをwrapし、carrier/recipient/current actor/visibleの変化だけを記録。数値buff query/RNG/攻撃/clock追加0、観測なし/ありの完全native・trace一致を検査。初v1は退場前にcounter完了して契約失敗。入力を退場0.5→1.25秒1回armへ修正し、比較器/実行器保持。失敗は永続proofへ残す。v2成功後、再出現を無制限として生存新世代への非継承を強化。

強いv3全4契約40.211833秒成功、最終v4（2f6e0c5f…）はreadiness/CLIテスト登録/packing unitの3file差分。全CLI関数AST/native producer/comparator保持、新4件の最終再生成0。最終関連120/制御517成功（Win1skip）、全4件の共有wire packing/73定義/115680wordとgeneration必須hit/Slang0確認。旧ADD3をfresh CPUで実行しinput/native/trace全SHA保持。reference報告のlogical policy名をBODYが上書きするmetadata bugも修正、古い記録は保持。

GPU/数値/正本/upstream/backend/CUDA compile cache/normalizer全byte・旧99golden保持。新GPU/Windows0、旧capture未取得の制限は維持。全proofは永続 .portable-recovery/proofs/owner-add-lifetime-20261027、要約はresearch/typed-owner-add-lifetime-reference-evidence/。次は同じ固定entryへ新4を追加し、旧99保持の新103入力をGPU検証。新しい寿命契約の検証として行い、失われたrawの再作成や旧capture再ラベルはしない。新4 Metal/CUDA/HP死亡/ゲーム仕様/公開consumer/全キャラ未完、全キャラ0/UI CPU/目標未達。


## 2026-10-27 ADD所有者graph退場・再出現Metal103

共通CLI `coordinate-typed-owner-add-lifetime` をseal済み登録。旧99保持＋4件、103/native60/拒43。元Prim71/完全5人/武器/成長、同じlogical-owner Slang entryで発動前後のgraph退場・旧field非継承・gen2発動を検証。最終gen9生存時に旧field値0。GPUの最終carrier/actor queryと戦闘履歴を照合、frame別visibilityはCPU witnessのみ。HPダメージ死亡は未検証。詳細 `docs/portable-coordinate-typed-owner-add-lifetime-gpu.md` と対応checkpoint。

M5 GPU4.200283秒、CPU preflight375.653591秒、pipeline61.344455秒（miss）、child71.713265秒/180上限。fresh独立監査482.756267秒、20/20/20/20/20/3各180以内、同じ監査でgolden/certificate。新GPU1/retry0/WindowsGPU0。最終0b727fdc…は5file登録差分、全CLI関数AST/native producer/comparator/tests/GPU保持、関連120/制御517成功（Win1skip）、generation必須hit/Slang0。最終版のfresh native再生成なし。

永続proof `.portable-recovery/proofs/owner-add-lifetime-gpu-20261027` に新raw/claim/全groupログ保持、reader終了後SHA/size/inode保持疎化で670760960byte回収。旧99input/native/記録output SHA保持、旧raw自体は未回収。現在の新103実証と旧capture消失を区別する。file-only Metal cache probe hitはwarm実機証明ではない。

Windows既存チャットへの送信APIは今回成功。07e1d178/coordinate-landing40は固定配布・対応cacheの所在を確認できず、CUDA未実行。次の依頼は所在とsource certificateを明示した固定配布でcache triageから開始し、不足時に長いcompile/本体buildをしない。次はHPダメージによるADD死亡など実戦寿命の未対応分類。現CUDA/ゲームgap/公開consumer/全キャラ未完、UI CPU/全キャラ0/目標未達。

## 2026-10-27 HPダメージ死亡CPU3とWindows固定配布

共通reference `coordinate-typed-owner-hp-death-common` を追加。元Prim全71・完全5人/武器/成長・別監査2効果を保持。HP1/1000000 ADDへ実ダメージ、同一攻撃子field先行/遅い子field前死亡/可視field後死亡の3件。hit_add前後の受動観測でdealtがHPへ到達しalive→dead、graphはactive/世代1のままを検査。3件27.509402秒CPU成功。最終742c8a98…は分類/負例unitの2file差分、producer/CLI/GPU保持、22検査・制御517成功（Win1skip）、生成必須hit/Slang0。新3件GPU0、Metal/CUDA未実証。詳細docs/portable-coordinate-typed-owner-hp-death-reference.md、対応checkpoint。次は旧103保持の106へ接続。

Windows c7e4d149探索では現sourceのgenerated/cache未特定、GPU0。package作成は固定upstream未導入で停止。再buildせず、Mac CPU検査済みcompiler-only ZIPを17b52569で共有。research/windows-source-packets/typed-owner-add-lifetime-a2cfc763.zip（11439568byte/SHA82e0322e…、package a2cfc763…）に固定upstream/dataを同梱。新source cache不在時に旧cacheを流用しない。現CUDAのcompile/cache/launch/readback成功は未確認。WindowsでもZIP SHA・全3497payload・pinned source certificateの確認完了。unpack62.820553秒/verify14.818706秒、各BelowNormal/2GiB/180秒以内、終了0。research/windows-source-packets/windows-receipt-a2cfc763.jsonに既存チャットの出所付き結果を保持。追加compile/driver/GPU0、現CUDA計算成功とは区別。

## 2026-10-27 HPダメージ死亡Metal106・依存事前チェック

最新sealed coordinate-typed-owner-hp-death106/native63/拒43。元Prim71/完全5人/武器/成長と旧103保持、同一攻撃子field先行・遅いfield前死亡・可視field後死亡を共通entryへdata-only追加。GPU/backend/数値/正本/normalizer不変。M5 GPU4.185487秒、CPU preflight411.900620秒、pipeline0.003058秒（必須hit/compile0）、child6.520327秒/180上限。fresh6群20/20/20/20/20/6の独立監査534.033338秒、各180以内、同じ監査でgolden/certificate。旧103原raw837184000byteと新prefixをbyte一致、GPU退場理由1・被ダメージ1/1/1000000・gen1/dead/field0。kill時graph activeはCPU witness、最終GPU graphはinactive。追加診断の誤ったfinal-active要求失敗も保持、native/GPU比較器変更0。

最終9a30395d…は分類/登録とPython依存チェック8file差分。変更CLI関数make_package/main/cpu_test_groups、他全関数AST/native producer/comparator/GPU保持。関連123/制御525（Win1skip）、generation必須hit/Slang0。最終native全再生成0。proofは永続 .portable-recovery/proofs/owner-hp-death-gpu-20261027、全groupログもpersistent TMPDIR、reader終了後SHA/size/inode保持疎化で688259072byte回収、raw/claim削除0。小さな証跡はtyped-owner-hp-death-gpu-evidence/と対応checkpoint。

以前の07e1d178の数値40goldenは共通source変更でstale。現在sourceで小さなMetal40/独立監査を行い旧input/native/output完全保持、GPU0.403115秒/child2.503813秒、全GPUコード変更0、旧raw復元ではない。compact sealed v3はWindowsでgmpy2不足によりCPU import時停止、compile/GPU0。v4はpin同梱とvalidation-depsを追加し、専用dependenciesを一時PYTHONPATHで利用。既存envへのinstall/SDK/PATH変更なし。Mac36/525成功、新Windows runは最初のCUDA GPUだけを依頼中。全本体CUDA成功へ拡大しない。

現在inventoryは266profile中245入力変換/21失敗、203base中185変換、20model-gap分類。全profile input/issue/順位保持。過去の19失敗を現状として使わない。HP死亡/field寿命の私有共通契約成立と、canonical/public consumer・ゲーム仕様・全キャラ認定は別。次は本体CUDAの段階別成立と、残20分類・公開consumerへの接続を優先し、固定entryへ小ケースを足すだけで全キャラ達成へ読み替えない。全キャラ0/UI CPU/目標未達。

Windows v4は依存確認・36検査・40/native26比較・NVRTC2.586690秒/ret0・module読込まで成功し、cuLaunchKernelがcode2で失敗しました。成功launch0/readbackなし/計算未認定。保存CUBIN311824byte/SHAe8550ca1…をfile-only cache-probeでhit確認（0.086559秒、compile/driver/GPU追加0）。GPU空き容量やstack/localは保存記録に無く原因未確定。内Job peak2098597888byteは上限近傍ですが因果関係は未証明です。report commit6ed21084…のJSON2blob（3367byte）をMacでhash検査、package/input/generated指紋も一致。CUBIN/Job原本のMac独立監査ではありません。次は同じcacheを必須にしてcompiler DLLを載せない実行profileを明示的に検証する候補。原失敗/claim保持、cold再試行やcap増大をしない。


## 2026-10-27 共通本体の短い実機profileと全byte監査

現在の作業checkoutは `.portable-recovery/runtime-resident`、branch `codex/runtime-resident`。全106のresident arc sourceを保持し、先頭4入力/native4の `coordinate-resident-device` をsealed登録。Marciana controlと元定義modifier3件だけの範囲で、全キャラ4件認定にはしない。M5でGPU0.419713秒、別fresh childのnative4独立監査15.297366秒に成功。全readback33,036,576byteは保存Metal106の先頭rawと全byte一致。元106/native63/rej43の登録・goldenは維持。詳細 `docs/portable-coordinate-resident-device.md`。

共通runnerは現在packetのIDとhistorical compilerの別IDを区別するよう修正。元packageの全byte検査とlineage admissionはそのまま。Windowsの大きいpackage全byte検査を最大4threadへ変更、各gateで全byteを新規SHA計算。Macと128未満は逐次。並列経路は同じ長さの改変・消失・非regular・重複・unsafe pathを拒否。Mac関連49/共通591成功（Windows専用1skip）。`research/benchmark-package-byte-check.py` は逐次→並列各1回のCPU診断で、意味・GPU計算認定とは別。

固定配布v3は `research/windows-source-packets/coordinate-resident-device-v3.json` と同名ZIP。前v2からCLIと回帰testの2fileだけを変更、全GPU/入力/native/goldenは同一。現CUDA実計算の結果は非公開の永続proof `.portable-recovery/proofs/resident-arc-arena-20261027` とWindowsの既存captureを確認する。終了結果・claimを確認してから次へ進み、観測不足を理由に再送しない。Windows結果の公開やraw移動は行わず、同一accountの接続内で最小原本とSHAを取得する。

266profile/245入力変換/21失敗と20model-gap、全キャラ認定0/UI CPUは継続。専用Lock On/移動/範囲/対象数等の不足と、private kernelの実証を区別する。最初の4入力のdevice接続確認後も、現sourceの全106 CUDA、全特殊効果、canonical/public consumer接続は未完了。


## 2026-10-27 resident Frame全106独立seal

`coordinate-resident-frames` はsealed登録。共通Frame32個をケース別Runtime末尾4096byteへ移し、既存247field／入力115680／出力2064786／3binding・CUDA48byteを保持。全106通常Metalは28群176テスト／native63＋拒否43成功、M5 GPU4.103676秒、CPU410.717786秒、比較時はlive parent63を再利用しfresh追加0／file値cache0。旧全875469264byteも全byte一致。別6childの独立監査は513.541770秒・各180秒以内／最長134.245456秒、live parentなし、追加GPU0。同じ監査からgoldenとcompiler certificateを生成した。`research/resident-dispatch-frame-evidence/independent106.json` と `docs/portable-resident-dispatch-frames.md` を参照。

次は `compiler-full--coordinate-resident-frames` の固定compact packetを検査し、Windowsで必要な短いgeneration/PTX/object/link/resource確認へ進む。新Frameの物理CUDA stack削減・起動成功はまだ未実証。未対応分類はprivate Metal基盤の成立だけを追記し、20model-gap／全キャラ0／UI CPUを保持する。古い失敗claimを消したり再送しない。原本と実行状態は永続proof `resident-frame-arena-20261027` の最新continuationと既存Windowsチャットを確認する。

### 2026-10-27: fresh CPU事前検査の段階化と保存compiler owner監査

`docs/portable-staged-native-preflight.md` を参照。begin→fresh native群→一度だけGPU→独立fresh native群集約を共通CLIへ追加。通常runとCPU検査は維持。値cacheや後付けcpu.jsonは作らず、hash-only transaction・全case coverage・host/manifest/claim・Windows各stage Job/180秒を検査する。GPU直後はpending/calculation=falseのまま。

固定device v3のM5実機4入力はfresh preflight2+2→GPU1回→独立fresh2+2で計算一致。GPU子16.93秒、生成cache必須hit/Slang呼出0、readback33,036,576 bytes SHA d1dc8ecdd94b881503bcc588e34103103dce402fc6adbfaa56924484c0545879。初期v1/v2のcompact登録テスト失敗は保持し、検査修正後の別packetを使用。結果要約 `research/shared-native-group-evidence/metal-staged-four-v1.json`。

旧compact compiler ownerは現在のテストregistryを使うと誤拒否されていた。全payloadを検査した後、検証済み旧owner自身のregistry/projectionをfresh CPUで照合するよう修正。実在7b43de12の静的監査成功、追加compile/GPU0、関連49検査成功。固定full106 packet `research/windows-source-packets/staged-native-preflight-v1.zip` (38544c0b)。GPU/保護CPU/goldenと全106入力SHAを保持。Mac選択177検査/108.65秒、共通621検査(Windows専用1skip)成功。Windows新stageはまだ未実証。既存CUBINの追加コンパイルは不要、fresh CPU全群とJob観測が成功するまでGPUへ進めない。

未対応分類266profile/245入力変換/21失敗、20model-gap、全キャラ認定0/UI CPUを維持。Heavyarms空間Lock On/対象数、移動/共有damageなどのゲームgapは未解決。今回の実行器/検証経路の成立を全キャラ対応へ読み替えない。Windows保存結果はprivate readbackで受領し、公的ブランチにraw/PTX/CUBINを送らない。

### 2026-10-27: 選択テストもfresh群へ分割

Windowsの新CLI用smokeは622件成功したが、full106のbeginは選択177件の途中で180秒へ達した。旧packet/claim/失敗原本を保持し、GPU/native前検査は起動していない。選択テストは削らず、新しい `preflight-plan --test-group-size 2`→全 `preflight-test-group`→全native群→GPU→独立native群の経路を追加。通常run/通常beginは不変。全登録群の順序/全ログ/nonce/PID/Job終了・観測をnative前とGPU前に監査し、合成cpu-tests.jsonは作らない。`docs/portable-staged-native-preflight.md` を参照。

固定full packet 7e142c00 (`research/windows-source-packets/staged-unit-tests-v1.zip`) はMacで選択177テストを14fresh群で完走、最長46.30秒/合計129.37秒、共通629テスト成功(Windows専用1skip)。同コードdevice packet e5a04816は元62テスト4群→native4件2群→M5 GPU1回→独立fresh native4件2群で完全一致。必須generation/pipeline cacheを使用しSlang呼出0、共有Swift module cache利用時のGPU子1.86秒。raw SHA d1dc8ecdd94b881503bcc588e34103103dce402fc6adbfaa56924484c0545879を維持。public要約はshared-native-group-evidence/metal-staged-tests-*.json。

全106 GPU/protected CPU/golden/入力SHA7892c2b3を保持し、旧compiler owner7b43de12のownregistry監査も成功。Windowsでは新固定packetでCPU smoke/plan/選択テスト群から開始する。全群とJobが成功するまでnative/GPUへ進めない。保存済みCUBINを使い追加compile不要、GPU子60秒/各stage180秒/2GiB/BelowNormalを維持。今回の成立は新しいゲーム効果や全キャラ対応の証明ではなく、Lock On/対象数/投射物と残20分類、全キャラ0/UI CPUは継続。

### 2026-10-27: Lock Onの対象数とmarker stackを分離

`docs/portable-heavyarms-lock-selection.md`に次のconsumer契約と公開記述の出所を記録。元25定義のcanonical named-marker stack1..5は、異なる5体へのLock Onではない。公開記述の未ロック候補除外・通常5体/+10体・攻撃/遮蔽解除を、第三者資料/実機未検証として固定。対象種別・距離の測り方/参照点・tie・死亡/世代・sequential順は未確定のまま。classifierにmarker stackとdistinct target countの区別、除外未検証を追加し、effect_target_count_addの10体/2射撃consumerを具体化した。

全266profile行、入力、issues、20順位のcode/message/descriptor、laneは前inventoryと全一致。変わったのはreadiness注記だけ。245入力変換/21失敗/全キャラ0/UI CPUを保持。関連61テスト成功。Windowsでは別固定commit48cb1f2fの630テストpacketを検証中で、今回classifier変更を実行中controllerへ混入しない。

### 2026-10-27: 対象数queryの実装とWindows native8 timeout

`effect_target_count_policy.query`を追加。通常reader/namespace/cache/carrierを変えず、指定target_effectの固定整数modifierだけを既存get_buffs/planのローカルviewで読む。元Heavyarms全25定義のindex20(+10/2射撃)を保持した4条件(3/30秒×本体/3ADD)を共通CLI `reference --suite heavyarms-target-count-native` へ登録。固定packet49dc4e97で13単体/透過性検査と4参照契約成功、関連58検査成功。実射撃イベントで2射撃消費・5→15→5を検査し、observer無しの全戦闘/trace/入力を完全保持。通常numeric計算と他targetの値を混ぜないことも検査。詳細はportable-heavyarms-lock-selection.mdとresearch/target-count-query-evidence/。空間選択への接続とGPU実装は未完了、20model-gap/266profile/245変換/21失敗/全キャラ0を保持。

Windows固定9c825fa5の選択177テストは全14群成功。native0..7は計80入力/native45成功したが、native8が180秒timeout(case87途中、case80..86 returned記録)。群8全体は未成立、result/artifacts無し、9/10未実行。全Job post0/missing0/監視cleanup0、GPU/compile0。完了済みnative/テスト、旧失敗、claimsは保持。元packet/transactionを編集せず、group8をそのまま再送しない。まだGPUへ進めない。private-continuation-v10以降の状態を優先して確認する。


### 2026-10-27: 同じ未実行GPU試行のnative tail継続

共通CLIへ`continuation-package`/`preflight-resume`を追加（code7cbc0c58、配布0993b8fe）。元sealed packetの全数値/native/データ/選択テスト/goldenを保持し、制御3fileとhelper/test3fileだけを差し替える。元owner自身のregistryと全payload、入力、host/Python、全選択テスト、成功native連続prefix、clean timeout/Job/観測原本を照合する。未成功の部分returnedは引継がず、値cacheなし。append-only所有claimを作り、同じ未使用GPU保存先へ未完了tailだけ小分けで進む。通常の実行と独立全件fresh監査は維持。詳細docs/portable-staged-native-preflight.md。

M5で実際のCPU-only timeoutを保持したまま成功prefix2入力を引継ぎ、残2入力をfresh実行→Metal1回→独立fresh4入力の全比較が成功。GPU0.413175秒/子2.118125秒、必須generation/pipeline cache、既存raw SHA d1dc8ecdd94b881503bcc588e34103103dce402fc6adbfaa56924484c0545879を維持。元失敗はfalse、元result/artifactsは不在のまま。要約research/shared-native-group-evidence/metal-native-tail-continuation-v1.json。

固定full106継続capsule04515f96（research/windows-source-packets/native-tail-continuation-v1.zip）は元9c825fa5のnumerical byte-lineage監査とMac共通640テスト/66群成功（Windows専用1skip）。Windowsへ新隔離root nikke-native-tail-cont-v1-diagnosticでsmoke→resume(group_size5)→最初tail0/global80..84だけを依頼済み。成功80入力/native45と元177テストは再実行しない。各Job2GiB/BelowNormal/180秒、GPU/compiler0の依頼。現在の実行状態は既存Windowsチャットと永続proof resident-frame-arena-20261027/private-continuation-v11.json以降を優先。旧9c失敗8と全claimsは保持。全106 CUDAと保存CUBIN実行は未成立。

Lock Onの既存typedAim候補順は距離順ではなくz→birth→node→slot順。typedGeometryの形状距離は包含判定用であり、その先頭候補を最近傍Lock Onとして転用できない。独自順位と既ロック集合が未接続であり、対象数queryCPU4契約だけでは全25効果/GPU認定へ昇格しない。266profile/245変換/21失敗/20model-gap/全キャラ認定0/UI CPUを保持。


### 2026-10-27: 名前付き対象数queryの共通GPU実証

code2d0167f4と後続修正で`named-target-count-query`を共通CLIへ登録。専用adapter/model・private stat93で通常compilerの拒否を保持し、共通carrier/event/recipient/stack/expiry/名前付き削除から対象数を読む。固定v4 0b13b4d1で選択17テスト→M5 Metal9入力/native6＋拒否3→独立fresh全9監査が成功、goldenを確定。GPU0.002709秒/pipeline必須hit。full106既存entryのCUDA/MSL生成は以前の厳密な正規化後ハッシュと一致（生成のみ）。詳細portable-heavyarms-lock-selection.mdとtarget-count-query-evidence/metal-shared-query-v1.json。

元の2射撃durationはこの外部イベントadapterで拒否。fixtureは元+10を使う時間契約の派生であり、全25定義やLock On選択を実装済みとしない。次は実物理shot寿命への接続を優先する。通常入場/20model-gap/全キャラ0/UI CPUを保持。

Windowsは既存継続tail1..5の最終結果取得時に接続不能。最後の観測はtail4/global100..104成功、tail5/case105実行中という報告で、terminal/admission未確認。再送しない。userへ接続復旧を依頼済み。復旧後は既存結果のみ取得し、全106/native63のadmission成立前にGPUを起動しない。現在のMac作業コードを実行中の04515capsuleへ混入しない。

新sourceのfull106は正規化後の生成コードが一致する一方、source graph SHAはevent_runtime/program_phases/新helperで変わる。既存golden/certificateを新packetへ自動的に付け替えない。現在のWindowsは元の固定packet/CUBINを使い続け、新source full106の再sealは未実施。

新sourceの共通smokeで、既存の厳密なsource逆投影監査に新しいifdef hookが未登録と判明。sealed-v1の失敗は保持。元9cとM5実証v4の実ファイルから、2変更file/2追加fileだけの完全一致deltaを独立fixtureへ記録し、既存Frame/武器監査の前段へ接続した。旧baseline/生成コードnormalizer/数値比較は変更せず、1byte mutation拒否・元Frame7検査・武器8検査・新query8検査を実行。全smokeの再確認が必要。

最終query配布packet b283876eは共通66群/641検査（Windows専用1skip）と選択18検査/native6＋拒否3のCPU事前検証に成功。GPU追加0。research/windows-source-packets/named-target-count-query-v1.zip/.jsonへsourceだけを保存。Windowsにはまだ新queryの実行を依頼していない。元full106 transactionの保存結果を先に確認する。


### 2026-10-27: 対象数queryを実物理shot寿命へ接続

code30bd0d6eまでで`named-target-count-shots`を共通CLIへ追加。元source20(+10/2射撃)を変更しないauto/charge2ケースと、timing/recipient派生3ケース。既存physical consumerの前後から共通capacity readerを読み、全実射撃の残数/発動時刻/queryをGPUで記録。trace100件は明示的な観測上限であり、overflowを拒否。全戦闘/ダメージ/射撃/skill trace/counter contextの比較を維持し、CPUスケジュール入力なし。

固定v3 6a7b2a2eがM5で全9入力/native5＋拒否4成功、別fresh child監査でseal済み。原定義2→1→0、scatter/muzzleが消費回数を増やさないこと、発動同frameの非bound/bound差、allied独立clockを照合。初版の空buff最適化による観測漏れとv2の静的charge待機0.2/正本0.215差は保持。全射撃比較を削らずprivate entry側観測を直し、待機は起動前に静的正本と照合。元native指紋9件全保持。

quantity reader refactor後、旧query9入力/native6を新M5で再検証し、全input/readback byteを保存v4と完全一致確認。v2 goldenを別名でfresh seal。full106厳密生成ハッシュも元基準を維持。ただしsource mapは変わるため新full106のgolden/certificate付替え不可。現在Windowsの元固定ownerは変更していない。

新しい分類metadataはprivate physical modelの成立だけを追加。fresh inventoryの全266profile行/input/issues/20順位/laneは旧lock-capacity inventoryと一致。全キャラ0/UI CPU/全25・空間selector・公開consumer・CUDA未完了。Windowsの接続復旧要求は未回答で、元tail1..5/admissionはterminal未取得。再依頼しない。

最終物理packet2aafcadfは共通66群/641検査（Windows専用1skip）と自身の8検査/native5＋拒否4 CPU事前検証に成功。query refactor packet56286944は自身の18検査/native6＋拒否3 CPU事前検証成功。両packetの全Python/Slang/Swift code SHAは一致し、共通検査を重複実行しない。配布はwindows-source-packets/named-target-count-shots-v1.zipとnamed-target-count-query-v2.zip（sourceのみ）。Windowsへの新規依頼は送っていない。


### 2026-10-27 Lock On公開情報調査

ユーザーは実機環境の用意を待たず公開情報から判断する方針へ変更した。公式紹介・モーション動画と日英のスキル表/解説を調査したが、中心/外形/奥行き/同距離順の実装を決める根拠は得られていない。距離モデルは保留。順番攻撃の挑発への反応には一般説明とキャラ固有解説の違いがある。出所と判断は `docs/portable-heavyarms-lock-selection.md` 冒頭に保存。

`app/named_generation_locks.py` と専用11テストを追加。既存ActorRegistry/ActorSnapshotと名前付きquota readerを再利用するCPU参照モデルで、外部のhandle列をその順で受け取る。距離の計算/ソートを含めない。死亡/世代更新/上限低下時の扱いは明示的なモデル上の契約に留め、ゲーム仕様へ昇格しない。11テスト成功、diff check成功。GPU接続/全25効果/全キャラ認定は未完了。GPUソース/正本は変更しておらず、今回の追加GPU/Windows実行は0。依頼済みWindows continuationの保存結果取得待ちは継続し、再依頼していない。


### 2026-10-27 実敵poolと名前付きquotaへのLock membership接続

新sealed CLI `named-generation-locks`（16入力/native10/拒否6）はM5 Metal実GPUと別fresh GPU禁止sealが成功。既存WorldSchedule/actor poolの生存・世代を参照し、名前付きquota readerから上限を読む。取得済み除外、死亡/世代更新、15体取得後の上限15→5、明示通常攻撃/ハイド解除、解除前immutable snapshot、BODY/PART/ADD、128体候補表を比較した。候補表128は24取得で検査。明示provider順のみで距離rank・ゲーム仕様は認定していない。

初回v1はmodifierを空statへlowerしたkind4を0へ戻す処理がなく、正例がGPU admission拒否。新入力v2で既存query adapterと同じ変換へ修正、CPU gateを追加。失敗rawは保持、実GPU計2/同claim retry0。v2 GPU0.019384125秒、Metal pipeline必須hit。Windows新依頼0。CUDAは共通Slang生成のみ。保存先はpersistent proofsの`generation-locks-v2-package`/`generation-locks-v2-metal`/`generation-locks-v2-independent.json`。

関連CPU参照/入力/逆投影/分類検査は成功。固定v2packetの共通smoke66groupも成功、GPU0。full106 CUDA/MSLの厳密正規化hashは旧基準と同一（生成のみ、新source full106のCUDA再認定とは別）。全266profile行/issue/20順位が前回inventoryと完全一致、245変換/21失敗/全キャラ認定0/UI CPUを保持。部分実証はmodel-checkの別フィールドへ記録し、公開admissionは閉じたまま。

次：充填中0.2秒event→元index20の2射撃寿命→通常攻撃/ハイドevent→発射前snapshot→sequential deliveryを同じresident battleへ接続する。このentryは元index20を有限時間へ派生したfixtureであり、元全25効果認定ではない。距離式/対象種別/tie breakは保留。Windows既存continuationの保存結果は接続利用不可で未取得のまま、再送/再実行しない。


### 2026-10-27 充填周期から実射撃snapshotへの合成

sealed `physical-generation-locks`7入力（native3/拒否4）はM5 Metalと別fresh GPU禁止sealが成功。元index0の0.2秒/during_chargeをself markerへ投影した既存周期activationでmembershipを駆動し、元index20を変えない2射撃上限と同一battleへ合成した。実on_attackで解除、GPU full_charge callback後・物理着弾前の集合を保存。fixtureには敵状態を変えるfull_charge効果はなく、原全25効果のイベント順は未認定。0.45秒充填で複数取得と再取得/15→15→5、短充填で空集合の射撃、取得後の実HP死亡による発射前除外を検査。候補128/周期63/発射snapshot31、stride不変。GPU .041235208秒/cold PSO8.204335秒。

共通coreの取得/snapshot関数抽出後、従来named-generation-locks16入力も新Metal・独立sealし、全input/readback byteを保持。新v2 goldenへCLIを接続し旧版は保存。実GPU計2/同claim retry0。固定packet共通smoke66group/641（skip1）成功、全266profile/issue/20順位を保持、default106 CUDA/MSL厳密正規化hash保持（生成のみ）。新sourceのCUDA認定ではない。

証跡はpersistent proofsの`physical-locks-v1-package`/`physical-locks-v1-metal`/`physical-locks-v1-independent.json`、および`lock-refactor-v1-package`/`lock-refactor-v1-metal`。Windowsの既存continuation保存結果は接続利用不可で未取得、再送/再実行なし。次は実ハイドevent、full_charge effectが敵状態を変えるときのsnapshot順、sequential delivery・途中死亡・元全25効果への接続。距離モデルは依然未確定で、公開情報を実機認定へ昇格させない。


### 2026-10-27 ロック専用arenaとキュースキルの合成

最新版physical-generation-locksは10入力/native6/拒否4をMetal＋fresh独立監査でseal。出力806912wordへ専用arenaを追加し、旧786432word prefixの位置と全32生存actor set容量を保持。候補/周期receipt/snapshotはactor query/receipt/setを借りない。新3ケースはfull_chargeで全敵を倒すキューダメージ、boss限定ダメージ、死亡後の再召喚。old generation snapshotの保持と新世代取得を比較した。

初版v1は再召喚の最終graph_state[0][6]だけが不一致。finish退場後のuntil_cleared観測をGPUの実poolから導出するopt-in修正でv2成功。close/death通知は不変。旧defaultの同観測の移行・再認定は別途必要。失敗raw保持。旧7入力の全input byte/全旧output wordをprefixまたは明示移設先へ照合（候補解放flag0→独立scratch flag1だけ明示変更）。従来external core16は全byte保持し新v3 golden。

共通smokeでwire幅の厳密source依存登録漏れが見つかり、host wire/Swift/backend/schemaの全文inverse ledgerへ登録して修正。GPU再実行不要。default106のCUDA/MSL厳密正規化hashは保持（生成のみ）。arena GPU計2（失敗1含む）、external core GPU計2、同claim retry0。最後のexternal coreは生成Metal全byte同一を確認してpipeline必須hit。Windows保存結果は接続利用不可、再送/再実行0。全266profile/issue/20順位保持、245変換/21失敗/全キャラ認定0/UI CPU。

証跡はpersistent proofs physical-lock-arena-v2-package/physical-lock-arena-v2-metal/physical-lock-arena-v2-independent.json とlock-core-arena-refactor-v2-package/-metal/-independent.json。次は実ハイドevent、順番攻撃のsnapshot consumer、元全25効果。距離・対象種別・tie順は未確定のまま。


最終固定packet779d20cc（code b9c090ca）は自身の7群54検査と共通66群642検査（Windows専用1skip）がCPU-onlyで成功。GPU追加0。新幅806912を追加しても旧wire修復が変化しないよう、修復元・先の幅列と先SHAを歴史時点へ固定。共通CLIのGPU前必須検査にweapon source・generation separation・historical wire repairを登録し、repo内スキルにも反映。CPU-onlyの先行失敗3件は保持。証跡はresearch/target-count-query-evidence/physical-lock-arena-sealed-preflight-v4.json。全目標は未完了。


### 2026-10-27 実ハイド通知の次接続契約

共通CLI `reference --suite physical-lock-cover-native` を追加。実CharState `_enter_cover` の `event:cover` を使う5ケース（充填中、別caster、禁止、空集合、リロード待ち）が固定packet4acdadd2で成功。通知はcharging取消後。既存observerは同casterの実cover通知でmembershipを解除し、通常攻撃前snapshotと遮蔽後の再取得を検証。通知callbackは透明性比較用の2回目nativeへ漏らさず、全battle/trace/input一致検査を維持する。

自身の8群59検査と共通66群642検査（Win1skip）、model-checkが成功。旧Metal10入力/native6の全指紋保持、全packaged GPU source byte保持。追加GPU0/Windows依頼0。証拠はresearch/target-count-query-evidence/physical-lock-cover-native-v1.json。cover入力は現physical GPU入口で全5ケース拒否を保持し、CPU契約をGPU成功へ昇格させない。次は既存enterManualCover/event31+tagとcaster照合、共通arenaの合成配置監査→接続→Metal。新しい状態機・CPU通知スケジュールは作らない。順番攻撃/元全25/距離とfull106 CUDA再認定は未完。Windows既存continuationのterminal取得待ちは変更せず再送しない。


### 2026-10-27 実ハイドを共通物理実行器へ合成・Metal実証

sealed physical-lock-coverは23入力/native11＋拒否12でM5 Metal＋fresh独立監査が成功。既存手動遮蔽producerと同じweapon/reload/event実行器を使用し、event31+cover tag+lock casterの一致で解除。充填取消後の通知、別caster、禁止、空集合、リロード待ち、遮蔽後の再取得と発射前snapshotを検証。手動80wordはsnapshot後804096の余白へ置き、input104400/output806912・live actor set32個を保持。全posture/padding/戦闘/skill/射撃/quota/candidateを比較。既存manual observerをcaptureとして抽出し、透明性比較用2回目nativeを観測scopeへ混ぜない。

新GPU1（.046597秒）＋共有source変更後のlegacy10/16各1、同claim retry0。3packetともfresh独立seal。legacy2は旧生成CUDA/MSL全byte同一を先に確認し、pipeline必須cache hitで各約.002秒。legacy全input/readback byte保持。物理10はv3、external16はv4、cover23はv1 goldenへ接続し旧golden保持。通常配布3packet作成成功。最終cover db363dc0は専用57・共通642検査（Win1skip）成功、GPU追加0。証拠はtarget-count-query-evidenceのmetal-physical-lock-cover-v1／legacy-retention／sealed-preflight-v1等。

全inventory fieldは旧arena版と一致、266profile/245変換/21失敗/20分類/全キャラ0/UI CPU。default106 CUDA/MSL厳密生成hash不変（生成のみ、現在source CUDA認定ではない）。誤ったmain entryを指定したCPU生成診断は失敗記録を残し、正しいportableEvents指定で保持を確認。Windows既存continuation statusを1回確認したがhost unavailableでterminal未取得、再送/再実行0。次はsnapshotを消費する順番攻撃と元全25効果。距離/tie/対象種別・ゲーム仕様は未確定のまま。


### 2026-10-27 順番攻撃のsnapshot選択部品とCUDA cache専用入口

実通知を追加観測し、on_attack → full_charge_fire → 元index8 named hit通知2回 → weapon hit通知を固定。元index4/8/9を変更せず加えたfixtureではhit予算2→消費後0、発射前snapshotは2対象。キューでlive membershipや消費後gaugeを読み直さず、発射時snapshot番号とhit予算を保持する必要がある。通知観測へ配送policyは注入しない。

共通整数部品cycle-frozen-slot-v1をPython／Slangへ追加し、CLI lock-delivery-policy63入力（共通policy46／raw拒否17）がM5 Metal1回＋fresh独立監査で一致。全6kind/128対象/256hit、空/欠落/死亡/世代違い、整数上限/重複/予約wordを比較。死んだslotを圧縮して別対象へずらさない明示policy。ゲームの途中死亡・挑発・再対象化の実測規則とは別で、実着弾キュー/HP/全25効果へ未接続。

legacy cover23/physical10/external16の全source閉包は151/150/134fileで不変、追加旧GPU/compile0。locked probeの独立sealはpackage14bf0314、Metal source/code e01389f9。最終通常package a2e38df1はpolicy/実順序5検査と共通642（Win1skip）が成功。最終cache専用efba68b8は12検査成功。lock-delivery-cache-onlyは既存compile-cache-only-v1を再利用し、required CUBIN/O1・保存source・事前file-only hitを要求、NVRTC loader禁止。immutable CLIにcache条件を渡さない負例はcapture/claim作成前に停止。実CUDA cache hit/launchは未実証、Windows新依頼0。通常probe63GPUは1回、retry0。

証跡はtarget-count-query-evidence/metal-lock-delivery-policy-v1.json、lock-delivery-native-order-v1.json、lock-delivery-final-preflight-v1.json。model-check成功、public GPU/全キャラ/全目標は未達。次はLandingReceiptに発射時snapshot tokenとhit予算を結び、landWorldSkillReceiptの既存actor set/land/counter/heal経路へ接続。予約word/所有権を監査し、live32setを診断snapshotに使わない。距離/tie/挑発のゲーム規則を勝手に確定しない。Windowsの旧continuation terminal未取得・再送禁止は継続。


### 2026-10-27 実キューのsnapshotリンク・可変hit予算をMetal実証

sealed lock-packet-bindingsは8入力/native4＋拒否4でM5 Metalとfresh独立監査が成功。元index4/8/9/20を保持するpartial fixture（全25ではない）。実receiptのstore/loadにsnapshot番号・既存hit/hitsを結び、空snapshot、待機中のADD死亡→次世代再出現、ハイド後4hit/3targetを比較。選択slot/statusは診断のみで、実着弾の対象は従来named routingのまま。次はslotをactor land/counter/healへ適用するconsumer。

receipt at+7は周期snapshot所有なので流用しない。別bank804176から2048token、31shot時刻、38件×16wordの診断traceを余白に配置。input104400/output806912、live set32、queue2048は保持。38件を超えると拒否、全2048同時queueをstress実証したものではない。終了時2048token全zero、全shot時刻/alignment/trace/tailを比較。native観測器の可変hitを1とする既知観測不足を新flag下で実emission listから観測し、配送後は補助id表も解放。native計算・正本4fileは変更しない。

code9553193f、実GPUpacket20bc39f3、GPU .047511秒、fresh監査4.013988秒。最終normal06d01666は専用39/共通642（Win1skip）成功、cache専用06c63eafは46検査成功。CUBIN必須・NVRTC禁止の既存profileを再利用。実immutable CLIのcache要件なし負例はcapture/claim前停止。追加GPU0。default106 CUDA/MSL厳密生成hashは保持（生成のみ）。全inventory fieldは旧cover版と一致、266/245/21/20分類/全キャラ0/UI CPU。

旧physical10/external16はrequired pipeline hitで新Metal＋独立sealし全shader/input/output byteを保持、新v4/v5 golden。旧cover23は、生成byteは同一だが保存cache未生成のためpipeline_lockでrequired miss。GPU dispatch前の失敗、readbackなし、失敗claimを保持し再送しない。現sourceの再認定は未完了で、現CLIの通常packageはstale golden source guardで実際に拒否を確認。旧配布physical-cover-sealed-v1-0.zipは保持。実GPU成功3/起動前失敗1/retry0/Windows新依頼0。

優先する復旧：テスト付きpre-claim Metal cache確認経路を実装してこの失敗を再発させず、正規の復旧経路を検証してcover23を再認定する。旧claim削除、同packet再送、旧goldenの付替えは不可。次にsnapshot target consumerを接続する。距離/tie/挑発/再対象化のゲーム実測規則と全25/current CUDA認定は未完了。証跡はtarget-count-query-evidence/metal-lock-packet-bindings-v1、lock-packet-final-preflight-v1、lock-packet-legacy23-predevice-failure-v1等。


### 2026-10-27 claim前Metal cache gateとcover23通常入口の復旧

既存metal-cache-probeのbounded archive readerを共通化し、required Metal runのCPU tests/native/worker/claim前へgateを追加。現在device/registry/OS build（SwiftのProcessInfoから取得）、再生成MSL・Swift実行子・resident strideでnativeと同じkeyを計算。source generationはCPUのみ、pipeline compile/dispatch0。miss/破損/OS違いは記録して停止。実行子のcache lock/hash/native failOnBinaryArchiveMiss再検証は維持し、required requestの途中でwarmへfallbackしない。

実修正a4f9ac2eの固定packet a92c3e17で、前回と同じ6fb2d307…のcache missがtests/native/worker/claim前に停止することを実証。旧失敗packet9553193fのsource全closure・input/native指紋一致と旧claim SHA/旧capture全artifact hashを確認。その新packetの未使用claimで明示した初回warm requestを1回だけ実行、Metal23成功＋fresh独立監査でcover v2 goldenへ復旧。旧claimは削除/再送しない。全CUDA/MSL/input/output byteが元cover23と同一。GPU .046675秒、archive作成 .006080秒。作成後はfile-only probeと現在identity gateの実正例もGPU追加0で成功。file hitはnative hit認定とは別。

最終normal cover2811e20e（67検査）、packet378c39f4（49）、CUDA cache profile285cb08d（56）がCPU-only成功、共通67群652（Win1skip）成功。3通常package作成成功、cover23のstale source guard問題は解消。現在のsource model-check成功、public/full character/full goalは未達のまま。今回実GPUは新host修正packetで1回、旧claim retry0、Windows新依頼0。数値/GPUソースは変更せず、その他入口の再GPUは行わない。

証跡はtarget-count-query-evidence/metal-cache-preclaim-cover23-v1.jsonとmetal-cache-preclaim-final-preflight-v1.json。private-continuation-v27.jsonが次の状態。次は発射snapshot slotを既存actor land/counter/heal処理へ適用する共通consumer。距離/tie/挑発・途中死亡再対象化のゲーム規則、元全25とcurrent CUDA実機は未認定。Windows旧continuationのterminal確認待ち・再送禁止は継続。

### 2026-10-27 公開情報による配送policy再評価

ユーザー指定のオンライン調査を追加。Prydwenの取得順循環と挑発例外はキャラ固有説明で、一般順番攻撃説明を無条件適用しない。新たにNIKKE.GGの索引本文（直接open403、動画/再現ログ未確認）で、予定ロック対象が配送前に死亡すると残りロック対象へ振替という記述を確認。現在の`cycle-frozen-slot-v1`の死亡dropをゲーム仕様としてconsumerへ採用しない。既存63/packet8の部分実証はそのまま保持し、ゲーム認定へ昇格しない。距離式・tie・actor種別、具体的な振替順は未確定。

次の実装では既存land/counter/heal経路への接続と死亡policyを分離し、生存対象の配送と未確定死亡policyの境界を明示する。公開情報だけから振替をnext/first/randomへ決め打ちしない。調査記録は`heavyarms-online-delivery-reassessment-v1.json`、判断は`docs/portable-heavyarms-lock-selection.md`冒頭。今回は文書/出所記録のみでGPU/Windows追加0、計算/golden/公開admission変更0。旧Windows continuationを再依頼しない。

### 2026-10-27 生存snapshotを実着弾へ配送

共通Slangの新entry world_lock_delivery_entry、CLI live-lock-deliveryを追加。発射時のfrozen slotをtransient actor setへsingleton captureし、既存land/counter/healをそのまま使う。実queue4正例と5拒否をM5 Metal＋fresh独立監査でseal。充填/ハイド後のBODY→ADD循環、空集合でBODY fallbackしないこと、ADDのskill counter完了・吸血HP回復を全battle/traceと照合。死亡/欠落/世代違いは未確定policyとしてerror64で拒否、振替やdropをゲーム仕様にしない。元index4/8/9/20は保持、index0はself projection、元全25/距離/全キャラは未完了。

実装4c0c114c、実GPU packet15aa4c45、GPU .057052秒、cold archive11.105610秒、独立監査6.390641秒。実パケットの9群57検査と共通67群652（Win1skip）が成功。観測contextを再利用可能に抽出し、従来受動packet4件のnative SHAを保持。新policyの全battle一致はfresh同policy基準との比較で、canonical equivalenceと混同しない。

一度だけ追加した共有hook以外は新entryのみに実装includeを置き、今後の拡張でlegacy source閉包を不要に変えない。今回変わった従来packet8/cover23/physical10/external16はrequired pipeline hitで各1回Metal＋fresh独立seal、全shader厳密hash/input/native/readback byte保持。通常goldenをv2/v3/v5/v6へ更新、旧版を保持。本体106のCUDA/MSL厳密生成hashも不変（生成のみ）。新cache専用CLIは同じ9入力に既存CUBIN/O1/required cache/保存source/NVRTC禁止profileを適用。実CUDA未確認。今回実GPU計5、retry0。診断スクリプトのnormalizer戻り値誤用2件はCPU失敗として保持しnormalizerは未変更。

全inventory fieldが従来と一致、266profile/245packing/21失敗/20分類/全キャラ0/UI CPU。model-check成功、公開admissionは閉じたまま。Windows旧continuation statusを1回確認したがhost unavailable、terminal未取得で再送しない。証跡はtarget-count-query-evidence/metal-live-lock-delivery-v1.jsonとlive-lock-delivery-legacy-retention-v1.json。次は元全25への合成・発射体consumer、距離順位providerと死亡時振替の未確定契約をそれぞれ分離して進める。

最終通常source ea3e27eeから6package作成成功。新live890c43a3は9群58検査、cache専用da3dd160は10群65、共通67群652（Win1skip）がCPU-onlyで成功。実immutable cache CLIで必須flagを省略するとcapture/claim/worker前停止を確認。GPU追加0。通常legacy packet5938c31c/cover2f9036b3/physical eab0b849/external de358814もsource/golden guardを通過して作成済み。最終証跡はlive-lock-final-preflight-v1.json、private継続点はprivate-continuation-v28.json。

### 2026-10-27 ロック＋元発射体攻撃の同一battle合成（開発用、履歴差分あり）

新entry world_lock_projectile_entry / CLI lock-projectile-compositionは、既存typed発射体処理とlive lock配送を同一WorldSchedule/DFS stackへ配線。元index24を変更せずpartial fixtureへ追加したnative5＋拒否4。全25ではなく、index0はself projectionのまま。typed全領域を保持し、lock/manual/link全20480wordを1048576以降へ移し、既存登録stride1310720/input109536で領域衝突を解消した。32 actor sets/128 typed targets/31 snapshots/2048queue/38traceは不変。

初回CPU生成はresident Runtimeの入れ子GenerationLocksを反射検証器が拒否。数値structのleafへサイズ/親子範囲/絶対offset/末尾/名前/深さ・leaf上限を厳密検証するよう拡張し、CUDA/Metalの全plan一致、sizeof/alignof assertion、48byte bindingを維持。実Runtime140008byte/locks1044byteを照合。reflection5検査（入れ子負例8種）、生成cache13検査成功。flat planは不変。現在の検証器SHAを含むpaired生成cacheについて、固定packetのrequired hit/コンパイラ0/GPU0も実証。CUDAコンパイル・実CUDA成功とは別。

code76b931c6、固定packet5e895206のMetal1回は全比較失敗。rawはlock-projectile-composition-v1-metalに保持し、claim再送なし。5正例status0/4拒否64、全5battle状態とtyped全receiptは一致するが、typedが存在する4件でskill traceが異なる。native typed拡張がscalar/通知用のBODY仮HitEventを作り、実typed配送後の次frame _landでskipするのに、world_skill_native.inspectがそのwrapper呼出しをBODY receiptとして記録する。GPUは実typed receiptのみ。空対象1件だけ全比較成功。比較器から行を削除/除外しない。失敗全artifact hashを再監査済み。

**次の優先作業**は実配送／抑止されたnative仮packetのdispositionを明示して両側の履歴契約を揃えること。保存rawで全項目を診断してから、必要な実装修正と新CPU契約を固定する。失敗captureへ新基準を付け替えたり同claimを再実行しない。新合成はdevelopment_onlyのまま、seal/CUDA実行/全25/公開admissionへ進めない。距離・死亡振替も未確定。

共有layout変更を受けた既存live9/packet8/cover23/physical10/external16は生成厳密hash/input/nativeを先に確認、required Metal pipeline hitで各1回＋fresh独立seal、全input/readback byte保持。goldenはlivev2/packetv3/coverv4/physicalv6/externalv7へ更新し旧版を保持。本体106 CUDA/MSL厳密生成hashも保持（生成のみ）。実GPUは新失敗1＋旧成功5、同claim retry0、Windows新依頼0。共通67群652（Win1skip）と専用9群57はCPU-only成功。全inventory fieldは前回と一致、266/245packing/21失敗/20分類/全キャラ0/UI CPU。model-check成功、全目標未達。証跡はtarget-count-query-evidence/lock-projectile-composition-v1-failure-diagnostic.json / lock-projectile-legacy-retention-v1.json / lock-projectile-required-generation-v1.json。private継続点はprivate-continuation-v29.json。

最終source2f2458fcから従来5通常packageを作成しsource/golden guardを確認。新合成を--developなしでpackageするとnative/ファイル作成前に拒否する実CLI負例も成功。追加GPU0。最終通常入口と失敗維持の記録はlock-projectile-final-cli-v1.json。ローカルjobは残っていない。

### 2026-10-27 抑止packetも共通キューへ保持し、合成12入力をseal

配送履歴差分を解消。従来のnative skill trace全行（BODY要求も含む）は保持し、別receipt_fatesでsuppressed_native_bodyとordinary_world_routeを明示する。GPUは凍結数量の監査receiptを既存2048slotキューへ置き、同じdrainの次frameでlogする。抑止receiptはActor land/counter/healへ入らず二重ダメージなし。typed counter子の後・named-hit子の前にenqueueする局所wrapperでnative append順に揃えた。既存完了通知/前提queryをPROJECTILE_CHAIN/FULL_BURST_LANDINGで接続し、新handlerや第二時計を作らない。

144word bank（1069056..1069200、header16＋flag128）の全word/unused/tailを比較してから旧arena projectorへ渡す。旧全word、32actor sets/128typed targets/2048queue/31snapshot/38link trace、input109536/output1310720/resident140008は不変。traceMode1必須。元index24と元4/8/9/20のpartial fixtureで、元index0はself projectionのまま。

新v1 0f5e2a40/code8d3a9b33は旧5条件とcounter-childが全比較成功、named-childが完了flag未接続で64。失敗保持。8e43b374は前提query未接続でCPU生成失敗、GPU/claim0。修正3c21e08eの固定v3 8422e8a3はnative7＋拒否5の全12入力でM5 Metal成功、fresh GPU禁止監査でseal。GPU .113912秒、PSO9.358276秒、独立監査12.005718秒。履歴を除外しないテストも成功。今turn GPU2（失敗1＋成功1）/同claim retry0/legacy GPU0。前回5e895206の失敗とv1失敗は全artifact hash再検査で保持し付替えない。

v3はCPU payload/inputを固定v1と監査してnative期待指紋だけ再利用、package時native0。run内部ではfresh全CPU/nativeを実行し、独立sealもfresh。GPU量や保存GPU結果の引継ぎではない。旧live9/packet8/cover23/physical10/external16と本体106の全GPU source閉包が不変のため、旧生成/GPUを繰り返さない。旧goldenは維持。

通常CLI lock-projectile-compositionはsealed12へ更新。lock-projectile-cache-onlyは同じ計算・goldenに既存CUBIN/O1/保存source/required CUBIN/NVRTC禁止を適用し、さらにrequired paired generationを実行前から要求。監査も生成hit/Slang0を検査する。既存standalone profileは追加要件なし。現在のCUDA実機は未検証。Windows既存continuationのstatusを1回試したがhost unavailable、terminal未取得・再送なし。

追加でtests/test_destructible_battle.pyの21件を実行し17成功、過去fixtureのsource guard4件が失敗。変更前0dc09543の隔離snapshotでも同じ4guardが失敗することを再現して記録した。既存監査課題で、fixture/guardを弱めない。新12の認定と旧履歴の全面再認定は分ける。

証跡はmetal-packet-fates-v3.json、packet-fates-failure-and-default-retention-v1.json、packet-fates-legacy-source-retention-v1.json、preexisting-typed-source-guards-v1.json。次の本体機能は元全25（特に元index0の実敵carrierと順位provider）への合成。距離/死亡振替/終了frameに残る監査receipt/全2048同時queueは未検証。全キャラ0/UI CPU/公開admission falseのまま。private継続点はprivate-continuation-v30.json。

最終通常source a1bef907のnormal/cache2packageを作成し、それぞれ10群62／11群71検査とnative7のfresh CPU-onlyが成功。共通67群654（Win1skip）も成功。normal固定packetのrequired generationはsealed generated baselineまで検証しhit/コンパイラ0/GPU0。実immutable cache CLIでCUBIN側の必須flagを全て与えてもpaired generation指定なしならcapture/worker/claim前に停止する負例が成功。通常CUDA cache hit/launch認定ではない。追加GPU0。packet-fates-final-preflight-v1.jsonに全manifest/receipt hashを保存。ローカルjobは残っていない。

### 2026-10-28 元ヴェルヴェットの敵弾薬を実Metalへ接続

共通CLI enemy-ammoの元76定義/6戦闘条件＋raw拒否14をM5 Metalとfresh GPU禁止全出力監査でseal。固定0d3bce27、packet34cbe45d、GPU0.8562025秒、cold pipeline59.394478秒、独立監査124.232063秒。既存ADD/BODY incomingの前へ世代magazine/残弾/reload gateを接続し、元射撃試行を保持。Lv1/Lv10、空対象、再出現、死亡、BODYを全battle/履歴/通知と比較。resource通知各800/合計4,800を省略せず、従来128prefix＋専用tail4,096容量で保存。味方/敵の割合・flat数値はammo_instant_numeric.slangの同じ関数（standalone713は別独立seal）。Runtime138,952byte不変。

v2はkind11のactor受付漏れstatus64、v5は通知128上限status8で失敗しraw/claimを全保持。resource op3/実行flag付きkind11の専用gateと共通logの容量/offset hookで修正。CPU基準を通常経路で再計算し、現在sourceの正確なinverse ledgerを保持、厳密normalizer/保護CPUは未変更。通常CLIと必須CUBIN/O1/compile cache/paired generationのcache-only入口を登録した。Windows新run依頼0、CUDA実機未確認。

次は共有numeric抽出/resource hook後の旧スイート現source再認定をまとめ、未対応の敵武器/容量変更、flat/forced reload、self-destruct/付随debuff等へ進む。旧成功を現sourceへ付替えない。全キャラ/default受付は未認定。詳細docs/portable-enemy-ammo-gpu.md、証跡target-count-query-evidence/enemy-ammo-metal-v1.json、独立receipt tests/fixtures/enemy-ammo-independent-v1.json。

### 2026-10-28 弾薬4/ゲージ3の現source再認定とcompact監査修正

0321513aのcoordinate-original-ammo4、coordinate-original-resources3を各1回M5 Metal実行＋fresh GPU禁止joint seal（golden/source certificate）で成功。旧全input/native/entry/readback byteを保持し、通常golden/full-compiler aliasをv2へ登録、旧ファイルも保持。GPU1.712281/0.573241秒、cold pipeline58.125915/59.786975秒、独立監査66.204694/22.437469秒。required generation hit/Slang0。実packetテスト35/28成功。

先に監査の逆変換再適用、compactでの台帳Python依存漏れ、routingテストのcompact環境誤用、監査PythonをGPU一覧へ混入したテストを修正。217ファイルの復元include graph全体を旧goldenと照合し、未知/改変source拒否とcompact制限は維持。v1/v2/v3失敗はGPU/claim0、raw/log全保持、v4で各GPU1回/retry0。詳細docs/portable-ammo-resource-recertification.md、証跡original-ammo-resource-recert-v1.json。

次はADD実戦17/敵回復14/logical13等の現source再認定を整理し、敵の武器/容量変更等へ進む。全179履歴を無差別再実行しない。今回Windows新依頼0、現在CUDA実機・全キャラ/default受付は未認定。

### 2026-10-28 ADD17現source再認定と自爆4部品契約

固定a1881e09 / packete9ce00dcの元ADD17入力をM5 Metal各1回＋fresh GPU禁止joint sealで成功。全旧input/native/entry/readback138,176,000byteを保持。元ニヒリスター70定義/6編成、284発/1,120被弾、11拒否。unit35成功、required generation hit/Slang0、Runtime138,952byte不変。GPU0.694337秒、cold pipeline58.155649秒、独立監査104.990122秒。v2 golden/certificateを登録し、旧v1は保持。通常/cache-onlyと分類のreceipt参照もv2へ。現在のCUDA実機未確認、Windows新依頼0。証跡add-attack-battle-current-recert-v2.json。

次の自爆を共通CLI reference --suite add-self-destruct-nativeへ登録。canonical BossScriptを変更せず、単発/間隔3発/同時3発/飛び越し回収の4条件を検査。最後のAttackHitをqueueした同じbegin_frameでalive false・enemy_death・enemy_count1になり、queueは残る。初回CLIのcalculator import path不足失敗を保存し、正規engine_worker初期化後に成功。4unit（改変負例/fresh CLI/出所/未対応分類結合）とreadiness24成功。これはCPU部品のみでfull battle/GPU/default falseを明示。詳細portable-add-self-destruct.md、証跡add-self-destruct-native-contract-v1.json。

次は自爆の元実編成full battle契約を作り、queue済み最終射撃・同frame死亡通知/敵数・until-cleared/再出現へ既存pool/時計/incomingを使って接続する。敵回復/logicalの現source再認定も残る。Lock Onの距離は保留、全キャラ/default受付は未認定。

### 2026-10-28 ADD自爆を共有GPUへ接続

add-self-destructの元実編成8＋不正6をM5実行1回とfresh独立sealで成功。元ニヒリスター70/E.H.76定義不変、18自爆/33射撃/165被弾、0秒/間隔/同時/再出現/BODY混在/HP先行撃破/時間切れ/E.H.死亡resourceを全比較。既存cursor/pool/clock/notices/incoming/resource consumerを使い、最終queue後のreason3/敵数更新と全spawn後・incoming前の死亡通知を接続。未発射世代のrun.opens/_Add.firedも比較。Runtime138,952byte不変。

GPU49a58f13/packetd01a085d。初回38unit/CPU8/必須生成hit/Slang0後に全正例0/不正64、比較器array slice対list不一致で6case失敗。raw/claim保持。3998ad48で純receipt検査とarray/list改変負例を追加し、新packetc52145efが元golden/critical GPU/transport/canonical/input/native一致を検査、immutable hardlinkで保存出力をreplay。GPU再実行0。全14 replay成功後、fresh GPU禁止seal126.237991秒、同時source certificate。GPU0.598816秒/cold pipeline58.053059秒、dispatch1/retry0。

通常/cache-only登録と分類へscoped Metal成功を追加し、CPU部品4の分類は別のまま。UTF-8台帳をCP932模擬でも検査。次は敵magazineとの合成/付随debuffと、今回hookで変わった旧ADD/敵弾薬sourceの必要な再認定。全キャラ/default/UIは未認定、CUDA実機未確認、Windows新依頼0。詳細portable-add-self-destruct.md、証跡add-self-destruct-metal-v1.json。


## 2026-10-29 敵移動を元5戦闘の共通GPU実行器へ接続

通常CLI `enemy-movement`（15入力/native5）を追加。M5実GPU1回で全位置/区間/状態と全戦闘履歴が一致、別GPU禁止8群のfresh sealも成功（348.617秒、各180秒以内、parent再利用0）。元ユニ69/ヤン71/混合69定義、武器・設定・30秒・全履歴を保持し、予定位置/発動時刻を入力しない。既存alive/end/actor field/world clock/LogicalGeometryを読む。専用wire117476word・出力2032000word内の分離bank。GPU2.926秒、PSO初回61.397秒、run前CPU301.701秒。検証root `.portable-recovery/proofs/enemy-movement-battle-20261029`、詳細 `docs/portable-enemy-movement.md`。

初回sandboxのdevice不可視はclaim前失敗として保持、通常承認経路だけで実GPU実行。同claim retry0。正確な小hunk逆投影は7共有ファイルを元byteへ戻す。既存2入口のCUDA/MSL生成byteも保持（生成証明のみ）。保護CPU4/strict normalizerは変更0。通常goldenと小証跡を登録し、readinessは宣言モデルのMetal接続を示すがcanonical/default/ゲーム空間モデルの不足は消さない。全キャラ0/UI CPU/public GPU false、今回CUDA実機未検証/Windows追加依頼0。次はtyped/worldとの合成と、短いCUDA検証単位の選定。


## 2026-10-29 GPU-only反復の小hunk台帳対応

`package --develop --native-baseline-package`が移動実装等のfiles/hunks台帳に対応。現実byteから一意に逆変換し、before全本文/SHA・CPU行・schema/出所/key集合を固定する。元15入力の実CLI梱包2.632969秒/native0/GPU0、全期待hash保持。以前のCPU基準生成291.706845秒の重複を避けるが、run前fresh native/独立sealは維持する。common89検査と固定候補unit13成功。GPU/CLI/保護CPU/normalizer不変、GPU計算の追加認定なし。検査用GPU commentは復元済み、snapshot/候補packetは `.portable-recovery/proofs/movement-expectation-ledgers-20261029` に保持。詳細 `docs/portable-development-expectations.md`、小証跡 `research/portable-native-expectation-files-ledgers-v1.json`。次のtyped/移動合成でGPUのみを反復する前に、この版でCPU基準を固定して使う。


## 2026-10-29 移動演算のCUDA43入力とCUBIN必須hit

固定f20b276b/packet149d1634のenemy-movement-mathだけをWindowsでcompile1回/GPU1回。43入力・688word（status0:32/16:2/64:9）が全一致、CPU11検査成功。CUBIN/O1/2GiB/compile内側60秒・コマンド外側180秒を維持し、runは必須cache hit/NVRTC0、GPU0.003763秒。内側compile12.388/run12.187秒、外側24.811/50.135秒。Job残存/timeout/process欠落0だがservice未識別のため外側終了2・preservation/overall falseは保持する。

保存結果の非個人2JSONだけをWindows report commit557e1840（codex/cuda-enemy-movement-math-v1-report）から取得、Macでfresh native全43/全word/元Metal raw2,752byteをGPU0で再比較した。原CUDA envelopeをMacで独立再監査したという意味ではない。証跡tests/fixtures/enemy-movement-math-cuda-v1.json、専用CPU検査test_enemy_movement_cuda_words.py、詳細docs/portable-enemy-movement.md。mathのscoped CUDAだけTrue、移動実戦5ケースCUDA/default/全キャラはFalse継続。今回のWindows依頼はterminalで、再実行はしない。次はtyped/worldへの位置consumer合成。


## 2026-10-29 移動・typed物理対象を1つの射撃実行器へ合成

`moving-typed`18入力/native6がM5実GPU1回とfresh独立9群sealで一致。元ユニ69/ヤン71/混合69定義、全30秒、2ADDとBODY所有の固定typed対象を保持。停止/force/重複2優先順位/再出現/同frame所有者死亡を含む。CPUはcanonical pelletを1回だけ使うgeometry merge、GPUは既存emState/DT/actor fields/clockから同じ並進/可視性を読む。owner genを再対象化せず、HP/寿命を二重化しない。packet f757ad6a、GPU3.094098秒、run前native162.230秒、fresh seal234.284秒/各群180秒以内/再利用0/GPU0。

入力123188/出力2165136を専用stride登録し、typed bankとlogical skill history/scratch、motion、frame固定aim中心の所有を分離。元2048skill/2048typed-prefix+全streamSHA/4096motion履歴を縮めない。全移動frame/区間と最終中心/padding、全frameのtyped候補hash、既存battle/physical/typed比較を通す。shape query診断や過去全中心をGPU全件serializeした意味ではない。原CPU失敗v1（空groupの誤条件）/v2（frame内死亡の観測差）も保存。旧移動CPU5指紋と旧2entryのCUDA/MSL生成byte保持。保護CPU4/strict normalizer変更0、旧goldenを書換えない。

小証跡tests/fixtures/moving-typed-metal-v1.json、通常goldenresearch/portable-moving-typed-v1-expected.json、詳細docs/portable-moving-typed.md。proof root `.portable-recovery/proofs/moving-typed-20261029`。今回はWindows依頼0、mathの既存CUDA43証拠は維持、合成のCUDAはFalse。次はactor数/group consumerを含む合成の拡張と、162秒のMac native costを踏まえたWindows小group選定。default/ゲームの空間規則/全キャラは未完了。
## 2026-10-30 元support編成で順序観測の不足を特定

開発worktree `.portable-recovery/runtime-resident` の `original-catalogue-support` を続ける。ナガ70/ティア75定義の元30秒編成、全225unit/fresh CPU2成功、M5 Metal1回。ティアの全比較と再突入event7は一致、ナガのnamed_stateだけが順序差で失敗。全体False、seal/goldenなし。同claim再実行禁止。固定packet `dcd89cbbd811915fafef7a36ba5f311ea1d994372b993d028009a40cbdcff831`、proof stem `original-catalogue-support-v5-20261030`。

保存raw/native診断：54 allied carrierの49番目「우정의 서포트」、native recipients `[2,0]`、decoder `[0,2]`。recipient header `[0,0,0]` でordered metadata False、decoderがmaskをスロット順に読む。GPU内部の実順序は未観測。次は既存Runtimeのrecipient orderを独立した明示readback契約で保持する。計算executorを複製せず、比較をsortで緩めず、revival用flagも偽装しない。既存共有GPUファイルを変えずresident entry wrapperで既存executePortableEvents後に観測する案を検討できるが、wire/entryの明示登録と厳密な監査が必要。未実装の案であり実行許可の迂回に使わない。

旧history/logicalの監査テストを厳密な後続inverse＋旧ファイルの完全hashへ修正。IMPL-STATUS.mdを共通CPU依存に追加、梱包漏れをnative前に止める負例を追加。開発suiteはsealedへ昇格していない。Windows host unavailableで既存結果status取得のみ、追加実行0。新規診断exportの審査拒否は未解消、別経路で公開しない。詳細 `docs/portable-original-catalogue.md`、小証跡 `research/target-count-query-evidence/original-catalogue-support-development-v1.json`。
