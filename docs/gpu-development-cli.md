## 製品プログラムを同じCLIで選択する

`package --suite product-detail --product-program fixed --develop --out NEW.zip` は、固定周期normal入口を既存の製品suiteで固定する。`accumulate`/`fixed`と`-group`/`-target`/`-group-target`の8種類を、共通の`data/portable-product-programs.json`で宣言する。suite追加や効果別の新検証器ではない。`product_program`はmanifest/package IDへ入り、元入力factory・wire・source closure・基準選択と結び付く。未指定の旧packetは従来の設定を維持する。

新programのsealed基準は`research/portable-product-programs-v1-expected.json`のprogram別entryへ登録する。まだ独立Metal sealのないmemberはsealed梱包を拒否し、旧normalの数値へfallbackしない。開発梱包は既存CPU基準生成→run→fresh独立sealを使う。`source-baseline --suite product-detail --product-program fixed --out NEW.json`または固定packet内の同commandは選択programを検査する。新programにも、同program・同CPU/data/input contractが一致する場合だけ既存`--native-baseline-package`の期待hash再利用を適用できる。programを跨ぐ再利用は拒否する。

共有CUBIN設定のprogram keysは同じ共通registryの既知8入口に限る。Nodeのconfiguredはshape/pathのヒント、Pythonの全owner/生成source/header/image/既存phase監査が最終ゲート。Windowsの保存JSONをMacで読む場合、receipt/trace validatorの明示`portable=True`はPOSIX/Windowsの絶対パス表記をデータとして検査する。既定のnative path検査やread_verified、歴史false/missing identitiesの条件は変えない。これは外部artifactをMacで実行する許可ではない。

## 2026-10-31 製品APIの固定周期モード

通常のMetal詳細APIは実蓄積に加え、固定周期の静的入力を共通実行器へ渡す。初回待機と5人のliteral再充填待機最大値だけをcontrol header v4へpackし、共通ソフトbinary64でreadyを判定する。CPU戦闘や発動予定表はGPU入力に使わない。全266profileの通常API確認でMetal255/理由付きCPUfallback11、追加編成1も全CPU製品応答一致。保存全payloadとraw SHAの独立監査成功、cache hit0。固定モードのCUDA実機確認は0で、旧実蓄積1秒のCUDA1profileと区別する。

fixed wrapperはnormal/group/target/group-targetの既存product実行器を共有する。headerはversion4・magic0x46424731、first時刻/最大regenは有限0..180秒、予約wordを厳密検査し、旧入口は新headerを拒否する。実蓄積4入口のCUDA/MSL生成物は既存strict normalizerで従来と同一。これは計算プログラム保持の証拠で、raw source identityが変わった旧sealed CLI ownerを通す例外ではない。現fixed/variant成果物の所有関係を既存product CLIへ統合する作業は未完。旧source/golden guardを維持し、未準備のCUDAは理由付きCPUへ切り替える。

未対応効果のCPU切替ではowner/effect/stat/targetをAPIとcapture resultへ残す。画面の準備・実行時間とGPU実行区間も区別する。実証/未対応一覧は既存 `research/target-count-query-evidence/product-admission-v1.json` の `fixed_product_readiness` に集約する。

## 通常製品APIの明示的な保存CUBIN

### 特定の過去link保全失敗の引き継ぎ

requestへ任意の`historical_link_observation`を追加できる。これは汎用のmissing無視フラグではない。4キー`capture`（同じlink captureの絶対path）、`observation_sha256`（元observation.jsonの全raw byte SHA）、`missing_identities`（消失全件のpid/path/creation_filetime_ticksを昇順・重複なしで保持）、`disposition:"retained-failure"`が必要。pidは整数、pathは元記録のlowercase、FILETIMEは精度を失わない正規化decimal文字列。元ファイル・分類・cause・claimは書き換えない。

監査が元before/afterから再計算した比較全体と一致したうえで、capture/raw SHA/全identityが完全一致する場合だけ、過去のpreservation=false/termination_cause=unknownとサービス識別状態をreceipt identityへ引き継ぐ。falseをtrueへ変更したreceipt、他capture、subset/superset/重複/並び替え/extra key、不一致のrawは拒否する。履歴を除いてkeyを再計算しても、再admissionで得る元receiptとの比較で拒否する。観測を省略したり、新しい実行の欠落を許可する機能ではない。

通常APIは`compute.saved_cubin_admission`を`not_admitted`/`verified`で区別する。履歴がadmitされた場合、成功でもCPU切替でも`historical_link_preservation_verified:false`、missing件数、原因unknownを返し、完全な履歴はcapture/receiptへ保存。admit前の拒否はnot_admittedであり、historical fieldが無いことを過去保全成功と解釈しない。新実行では別のfresh Job/前後観測を行い、現在のmissing件数0とサービス識別未確認を別に報告する。

Windowsの最初の実GPU確認は通常HTTP APIの1秒sceneだけを予定し、実driver/GPU/CPU全応答一致を確認する。30秒profile/全profile認定へ加算しない。Job/timeout/TDR/OS設定は変更せず、1回で停止し、新しいprocess消失があれば後続へ進まない。


`cuda_shared_detail`は既定では従来どおりpaired生成cacheとCUBIN/O1 cacheを必須にする。別の明示設定`NIKKE_SHARED_CUDA_ARTIFACTS`へ絶対JSONファイルパスを渡すと、既存CLIの保存PTX/object/JIT-link監査と同じproviderを使う。NVRTC cacheとして偽装せず、実行時のNVRTCは禁止。現時点の登録対象は通常body入口だけで、group/target入口は理由付きCPU fallbackとなる。

次はパス形状の例であり、現在のWindows保存物を実行許可する設定ではない。

```json
{"schema":1,"programs":{"gpu/product_battle_entry.slang":{"battle_package":"C:/proof/sealed-battle/packet","request":{"package":"C:/proof/sealed-link-controller/packet","capture":"C:/proof/saved-link-capture"}}}}
```

必要な場合だけ、既存CLIと同じ対`producer_package`/`producer_capture`をrequestへ加える。全pathは既存の絶対directory。設定JSONは個人パスを含むためGitへ含めない。`NIKKE_SLANG_GENERATION_CACHE`も必須で、missからの生成/コンパイルfallbackはない。Nodeは設定形状/pathの受付を示し、正確な整数/Unicode identity・観測rawの照合はPythonが最終判定する。画面のavailableは設定の有無であり、実行可否・GPU計算証明は要求ごとに判定する。

実行側の監査コードでowner全payload/goldenと現GPU source closureを照合し、元のPTX→object→link→CUBIN全chain、Job/観測、exact CUDA/header/image SHAを検査する。選択設定のフォルダーからPythonコードを実行しない。既定のmissing-process拒否とPTX/objectの拒否は維持する。過去の特定link失敗だけを保持する下記の明示binding以外では使用できない。

保存CUBIN要求は応答cacheを使わず、毎回admissionと実際のimage readを通す。通常CPU/Metal/native CUDA cacheの挙動は保持。成功時のcomputeへ`artifact_provider`/`artifact_key`を追加し、captureへowner/request/phase/receiptを保持する。共有phase検査は元CLIとAPIで同じ関数を使い、NVRTC/cache混入・source admission/read/receipt順序・receipt不一致を拒否する。GPU読戻し後の全CPU製品応答比較は省略しない。

Windowsでの製品GPU計算とadmission時間は未実証。監査のowner/admission時間をjournalへ記録し、既存deadlineを延長しない。登録された短い実機検証と独立確認が通るまでmockテストをCUDA計算成功に数えない。

`weighted-battle`は元ベイ4段階・独立cover破壊/元ビスケット復活/reburst・破壊条件付き元自己回復をM5/fresh独立監査でsealした21入力（native8/拒否13）。通常package→unpack→run経路を使う。`weighted-battle-cache-only`は同計算のCUBIN/O1・compile cache/paired生成必須。実CUDA/ゲーム比率/公開受付は未達。[範囲と失敗保持](portable-bay-allocation.md)。

`reference --suite weighted-incoming-common --out NEW.json`は元ベイ4段階と破壊/ビスケット復活/再burst/未発動透明対照のCPU7戦闘。既存native着弾・cover更新へ接続し、GPU数値suiteとは証拠を分ける。`weighted-incoming`の通常packetにはこのCPU回帰17検査も同梱する。[範囲と次のGPU接続](portable-bay-allocation.md)。

`weighted-incoming`は明示重み・生存body/独立coverの数値1192入力をM5/fresh独立監査でsealした通常suite。`weighted-incoming-cache-only`は同計算のCUBIN/O1・cache必須版（standalone、paired生成不要）。元ベイcarrier/戦闘接続・実CUDA・実機定数は未達。[規約と次の接続](portable-bay-allocation.md)。

`cover-defense-battle`／`cover-defense-modifiers`は同一の全13入力（元4戦闘＋Noah2戦闘＋拒否7）。共通received補償和をM5/fresh独立監査でsealし、旧11全byteを保持した。通常のpackage→unpack→runを使い、各cache-only版は同じ計算のCUBIN/O1・compile cache/paired生成必須。実CUDA/既定受付は未達。[現sourceの範囲と測定](portable-cover-defense-battle.md)。

`readback-retain --case-words 2048912` は遮蔽物receipt付きの保存出力を全byte照合する。既存typed幅2032000も対応し、CLIの幅一覧を監査器のCASE_SHAPESへ共通化した。GPU/数値再計算0、異なる/欠けたケースは成功にしない。旧11入力90,152,128byteを追加13入力の保存結果へ完全保持した。保持検査は計算証明と分離する。

`cover-defense-battle`は明示基礎DEFを用いた元戦闘4ケース＋拒否7件をM5 Metal/fresh独立監査でsealした。`package --suite cover-defense-battle --out NEW.zip`から通常経路を使う。`cover-defense-battle-cache-only`は同じ計算へCUBIN/O1・compile cacheとpaired生成の必須hitを要求する。実CUDA・既定受付は未達。[範囲と未検証分岐](portable-cover-defense-battle.md)。

`reference --suite cover-defense-common --out NEW.json` は独立した遮蔽物DEFを元戦闘の保護層へ接続するCPU専用4ケース。倍率の発動/失効、貫通、破壊/死亡、分配/シールドを検査する。GPU実証は別段階。[契約と次の接続](portable-cover-defense-battle.md)。

`host-memory`は自分/実parentとJobのWindows CPUメモリ読取、`cuda-resource-summary`は外部SHA付き保存phaseの要約。旧未記録値はunknownのまま、いずれもGPU/driver追加0。将来の未消費prepared-runには`--observe-cuda-resources`で時点観測を付けられる。現在の消費済みGPU試行は再実行しない。[引数と観測の限界](portable-cuda-memory-observation.md)。

`prepared-run`とWindows共通stage `gpu-prepared`は、成功済みCPU準備のsnapshotから元の未消費試行を一度だけ実行する。必須paired生成cache/凍結CUDA・CUBIN/容量/所有認証をclaim前に確認し、既存60秒・2GiBのGPU子へ渡す。成功後も計算はpendingで、既存のbounded `audit-native-group`と`aggregate-native-groups`を完了するまで認定しない。v2はcache/認証成功後の実launchでerror2となり、claim/失敗を保持した。[引数・request schema・失敗時の扱い](portable-prepared-admission.md)。

`saved-battle-audit`と`aggregate-native-groups`の`--case-groups PLAN.json --case-groups-sha256 SHA`は全入力を順序通り一度ずつ比較しつつ、群の幅を変えられる。`--group-size`は最大幅で、既存uniform指定も保持。共通Windows stageにも同じ計画を渡せる。moving-groupのnative3＋拒否12は4群にし、計算や比較を省かず入力準備の重複を減らす。[規約と固定計画](portable-prepared-admission.md)。

`entry-plan --inventory SAVED.json --out NEW.json`は保存した元profile監査から、重複を除いた影響数で未対応を並べる。現在12失敗profile/11系統、最大はベイ4段階。source再準備/compiler/GPU0で、scoped既存証拠とdefault未対応を分離する。[使い方と境界](portable-shared-entry-inventory.md)。

共通移動/groupのWindows準備は59テストとpaired生成が成功したが、CUBIN/O1の1回はptxasメモリ確保失敗で終了した。失敗claimを保持し、GPU0・再試行0。[保存結果と次のメモリ計画](portable-moving-group-cuda.md)。

`moving-many`はBODY＋最大127ADD・30秒を同じ実行器でM5 Metal/fresh独立sealした13入力。全228727frame/228854区間を省略せず比較する。出力10422672wordはframe/segment bankだけを拡張し、既存履歴容量を削らない。`moving-many-cache-only`は同じ計算に既存CUBIN/O1とpaired generation必須を適用する。現CUDA・実ゲーム・同時127体命中は未認定。[容量と全比較](portable-moving-many.md)。

`moving-group`は元ユニ/ニヒリスター全71定義・30秒の3戦闘＋拒否12入力。移動・typed形状・実multi_hit通知と元子攻撃を同じ実行器でM5 Metal/fresh独立seal済み。`moving-group-cache-only`は同じ計算へ既存CUBIN/O1とpaired generation必須を適用する。現CUDA・実ゲーム規則は未認定。[故障注入と範囲](portable-moving-group.md)。

`moving-typed-cache-only`はsealed `moving-typed`と同じ18入力・計算・goldenにCUBIN/O1とpaired generation必須を適用する。packet自身の54テストとcompile-planは成功、現Windows CUDA計算は未確認。[範囲と配布確認](portable-moving-typed.md)。

敵移動は`reference --suite enemy-movement-common`の元5戦闘CPU契約と、`package --suite enemy-movement-math`のMetal43入力数値核を追加。実機規則は未完了。宣言モデルのactor/carrier/frameのMetal接続はsealed `enemy-movement`/`moving-typed`に進んでいる。[範囲・保存結果replay・次の接続](portable-enemy-movement.md)。

現ソースの全106 CUDA接続は `partitioned-current-package` で作った新ownerを使う。旧失敗ownerは保持し、現Metal sealと保存CUBINをpinする。[現ソースownerと3段階](portable-current-source-cuda-owner.md)。

`model-check --summary` は、historical Metal106/CUDA append9/wireと後続joinを別表示する。joinは固定106入力の計算true、stage/環境保全false、Mac原CUDA未読を明示し、canonical model gap・全キャラ・公開受付へ昇格させない。出所は完全reportの `resident_storage_validation`。

保存CUDA sourceとpaired generation／CUBIN cacheを固定して使う経路は、sealed cache-only packetの `run-gpu-packet.py --stage gpu-cached --request REQUEST.json`。既存Job・2GiB・180秒／子60秒・必須hitを保持する。[4キーrequestと境界検査](portable-resident-append-publication.md)。通常gpu段階の失敗claimを消して再送しない。

固定CUDA単発入口は `partitioned-cuda-package` → packet自身の `partitioned-cuda-smoke` → `partitioned-cuda-prepare` → `partitioned-cuda-run --timeout 60`。全106・16件batch・新しい専用claim/ledger・保存CUBINのみ。現在のe2f6470dは全API完了したが出力差分で失敗保存済みであり、同じrunを再送しない。保存結果のCPU比較を優先する。詳細 [分割転送](portable-partitioned-file-transport.md)。

固定packetのWindows保存失敗再監査は `partitioned-origin-smoke` → 成功時だけ `partitioned-origin-audit`。既存run_job/2GiB/180秒以下で元admitと保存CUBINの出所を再評価し、新GPU claimや実行許可は発行しない。引数と境界は [分割転送](portable-partitioned-file-transport.md) 参照。

保存済み分割Metal結果の独立比較は、immutable診断packet自身の `partitioned-native-audit --source-package EXECUTED_PACKET --capture CAPTURE --out NEW_DIR --timeout 240 --group-size 16` を使う。各fresh CPU群と全入力集約を分離し、GPU再実行はしない。詳細は [分割転送](portable-partitioned-file-transport.md)。

`partitioned-file-package --source-package OLD --out NEW.zip` は全入力を保持する共通分割file transportのMetal診断packetを作る。新packetの `partitioned-run` はfresh全CPU比較後、最大16件分のbufferを再利用する。source固定のaddress profileはraw SHAと論理view SHAを分離し、数値/statusを変更しない。`partitioned-address-audit` は保存済み旧flat失敗をread-onlyで検査する。CUDAの新実行許可とは区別する。[分割file契約](portable-partitioned-file-transport.md)。

`gpu-recovery-package --base-package OLD --origin-auditor AUDITOR --out NEW.zip` は、元計算/registry/goldenを保持するcontroller capsuleを作る。新packetの `preflight-recover` が完全証拠とキャッシュを再確認して新owner/ledgerへ結合し、既存staged-gpu-linkedへ接続する。[引き継ぎ契約](portable-gpu-recovery.md)。CPU引き継ぎをGPU計算成功と扱わない。

元の全件事前検査は `staged-origin-check` / CPU-only `audit-staged-origin` で旧packet自身のCLIを呼び再監査し、参照した証拠の全file name/bytes/SHAを固定する。native計算の再実行やGPU recovery admissionとは区別する。[元preflight監査](portable-staged-failure-audit.md)。

保存済みのGPU前失敗は `staged-failure-check` / CPU-only `audit-staged-failure` でpackage/制御フロー/Job/監視/input/claimを結合検査する。診断成功を再実行許可やnative/cache再認定にしない。staged GPU入口には `--slang-root` と `--generation-cache` の明示ペア指定も追加し、recipeと子環境へ固定する。[失敗監査と設定規約](portable-staged-failure-audit.md)。

`enemy-ammo-self-destruct` は元Velvet76定義・正例8＋raw拒否8のsealed共通battle。通常のpackage/unpack/run/独立sealを使う。`enemy-ammo-self-destruct-cache-only` は同じ計算でCUBIN/O1/NVRTC禁止・paired generation必須。M5とfresh独立監査が一致したが、現CUDA/default/全キャラ認定は含まない。[入力・所有権・実証範囲](portable-enemy-ammo-self-destruct.md)。

`staged-gpu-linked` は明示的な既存絶対パスの `NIKKE_SLANG_ROOT` / `NIKKE_SLANG_GENERATION_CACHE` と空でないplatform用slangcをclaim・子起動前に検査し、`environment-preflight.json`へ保存する。設定不足は重いtransaction再検査より先に拒否する。これは存在確認のみであり、compiler identity/cache hit/全stage証拠は従来のbounded実行で再検証する。失敗captureと旧claimを編集したり、自動retryしたりしない。

`reference --suite enemy-ammo-self-destruct-common --out NEW.json` は元Velvet76定義・8条件のCPU合成契約。実自爆のqueue済み射撃だけを同世代/同frameの弾倉へ配送する。既存clock/割合演算/完了通知/被弾を共用し、弾切れで自爆を延期しない。GPU wire/defaultは未接続。詳細は[ADD自爆と敵弾薬](portable-add-self-destruct.md)。full packetの生成は全reference登録rootのtracked payload所属を検査し、未追跡factory等があればnative計算/ZIP作成前に拒否する。compact packetと動的import全closureはこの検査の範囲外。

`source-baseline --all-registered --out NEW.json` はproducer checkoutの全登録source/golden組を棚卸しする。cache aliasを同じ組へまとめ、source entryごとに一度だけclosureをhashする。`current`/`stale`/`unavailable`と全体一致flagを出し、GPU/native/compileは0。固定packet内では全登録の網羅を主張できないため拒否する。21 current/179 stale/2 unavailableという現棚卸しはsourceの状態であり、計算・CUDA・全キャラの認定数ではない。詳細差分は出力file、stdoutはsummaryだけ。

旧logical13/rosters5は共通named/stack admission修正後の現sourceで再認定し、通常登録goldenをv3へ更新した。旧v1/v2と各source証明書を保持し、新v3はfresh独立監査と同時にcurrent source証明書を生成する。入力・全native/entry・readback全byteは従来と同一。`source-baseline` は開発source検査を行うが、この実行/再認定を代替しない。

`source-baseline --suite SUITE --out NEW.json` はsourceだけを検査する。通常は登録goldenのclosureが現sourceと完全一致する必要がある。検証済みdevelopment packet内だけは、そのmanifest closureに要求suiteの全sourceが同じSHAで含まれる場合に限り開発sourceを認め、登録goldenが現sourceかを別fieldへ記録する。過去golden/証明書の整合性、native、GPU、独立sealは省略せず、計算成功を主張しない。無関係suite・改変manifest・sealed stale sourceは拒否する。

`named-range-battle` は元87定義・各54castの4world＋raw拒否12のsealed16入力。`package --suite named-range-battle --out NEW.zip` からown CLIを使う。`named-range-battle-cache-only` は同じ計算/goldenにCUBIN/O1・paired generation必須を適用する。元M5出力を保存replayとfresh独立sealで全比較済み、追加GPU0。現CUDA/実ゲーム半径/空間最近傍/defaultは未認定。[範囲](portable-named-effect-range.md)。

`reference --suite named-range-battle-common --out NEW.json` は元アスカWILLE＋レイ（source名레이 (가칭)、is_preview=False）の全87定義でcast範囲・実敵集合・着弾を検査するCPU4world。前回「マリ」とした出所表記を訂正。今回のbattleのGPU wire/Metalは未接続で、既存sealed21とは別の範囲。[出所と実戦接続](portable-named-effect-range.md)。

`named-effect-range` はsealed21入力（native12/拒否9）。共通event実行後のcarrierから効果名別範囲を読み、既存決定的geometryで実際にcolliderを選ぶ。元レイ（データ上の名称「レイ（仮称）」）5条件を含むが全編成battle/配送の認定ではない。`named-effect-range-cache-only` は同じ計算のCUBIN/O1/paired generation必須入口。M5実GPU1回と保存readback replay・fresh独立監査済み。現CUDAは未確認。[範囲と失敗保持](portable-named-effect-range.md)。

共通direct配送の死亡後overkill修正後、`logical-actor-geometry`13/`logical-actor-rosters`5を現source688de06eのMetal・fresh独立sealで再認定し、v2 goldenを登録した。全旧input/native/readback byteを保持。cache-only版も同じv2計算で、CUBIN/O1・compile cache/paired generation必須を維持する。現CUDA実機成功ではない。旧v1 golden/証明書は保存済み。[再認定出所](../research/target-count-query-evidence/logical-dead-overkill-recertification-v1.json)。

`supplement-test-golden --source-package P --source-capture FAILED_UNITS --donor-package SEALED --baseline-suite NAME --out NEW.zip` は、未claimの開発packetで不足した**別suiteのgolden JSON1個だけ**を、検証済みsealed donorから補う。元producer自身のregistryでpathを解決し、既存全payload・入力/CPU期待指紋は変更しない。元失敗/rootを保持し、新packet自身のunit-check→fresh native preflight→GPU→独立sealを行う。数値変更・golden差替え・実行済みclaimの再試行には使わない。敵回復v3→v4で元3,758ファイルを保持し、32,392byteの検査依存だけを追加、native再計算0で89unitへ復旧した。Slangも必須cache hit/追加compile0。

`reference --suite enemy-healing-common --out NEW.json`は元アン全69定義の敵回復量低下を、既存source node/ADD HPへ接続するCPU契約6件。実倍率・HP変化・再出現・小数撃破creditと最終roundを検査する。別のsealed `enemy-healing`14入力（元native6/拒否8）は共有wire・M5 Metal・fresh独立監査で一致。`enemy-healing-cache-only`は同じ計算に既存CUBIN/O1・paired generation必須を適用する。現CUDAと既定admissionは未認定。[設計・数値境界・次のMetal接続](portable-enemy-healing.md)。

`logical-actor-rosters`は元ニヒリスター全70定義の実2敵通知・範囲外/PART対照・回転矩形・30秒のsealed5入力。前のlogical actor entry/全比較を共有し、CUDA/MSL全byte保持、M5 Metal/独立監査成功。必須Metal pipeline hitでPSO約0.0027秒。`package --suite logical-actor-rosters --out NEW.zip`とown CLIを使う。cache-only版も同じ計算だが現CUDA実機は未確認。[範囲・元スキル・実測](portable-logical-actor-rosters.md)。

`logical-actor-geometry`は実ADD colliderのsealed13入力（元6条件＋raw拒否7条件）。`package --suite logical-actor-geometry --out NEW.zip`から固定packetのown CLIを使う。M5 Metal全比較・GPU禁止の独立監査に成功し、元の全battle・物理packet・group・2,048行スキル履歴を比較する。`logical-actor-geometry-cache-only`は同じ計算に既存CUBIN/O1・compile cache必須・paired generation必須を適用するが、現CUDA実機hitは未確認。全キャラや既定CPUの幾何認定ではない。[範囲と実測](portable-logical-actor-geometry.md)。

`reference --suite logical-actor-geometry-common --out NEW.json`は元ベロータの実RLをBODY＋実ADD形状へ接続するCPU契約6件。元4敵通知/防御低下/子攻撃を検査し、PARTを敵数へ数えない。このCPU referenceコマンド自体はGPU認定を行わず、実Metalの別証拠は上記sealed suiteに保存する。[設計と移植手順](portable-logical-actor-geometry.md)。

`entry-inventory --character NAME --favorite-stage 0 --suite original-shield-weapons --out NEW.json`は指定profileだけを準備する静的監査。元owner/source行/effect hashと既存対応分類を`profile_explanations`へ出し、部分結果と全体を区別する。[使い方・制約・全266保持](portable-shared-entry-inventory.md)。

`original-catalogue-incoming`は元Red Hood B2の挑発/被弾後回復とCinderellaデコイの破壊/実HP被弾/元burst復帰を30秒4条件でMetal独立seal。`original-catalogue-incoming-cache-only`は同じ計算・入力・goldenのCUBIN/O1とpaired generation必須。任意catalogueは1,072名。[範囲と使い方](portable-original-catalogue-incoming.md)。

`original-catalogue-roles`は元RapiのB1編成条件とRed Hoodの明示B1/B2を30秒4条件でMetal独立sealした固定群。`original-catalogue-roles-cache-only`は同じ計算・入力・goldenのCUBIN/O1とpaired generation必須。任意選択catalogueは元1,064＋role4の1,068名。[範囲と使い方](portable-original-catalogue-roles.md)。

`original-catalogue-burst`は元Rapi RH/SBS/Red Hood/Cinderella各30秒のsealed4入力。`package --suite original-catalogue-burst`から既存の固定packet実行を使う。`original-catalogue-burst-cache-only`は同じkernel/入力/goldenにCUBIN/O1・compile cache必須とpaired generation必須を適用。初版の独立観測器の不足はsource/CPU指紋を変えずに修正し、保存GPU結果のstrict replayとfresh独立sealで認定した。独立監査のfailure/timeoutログはcaptureの隣へ保存され、nested causeも比較理由に残る。[実証範囲と未観測条件](portable-original-catalogue-burst.md)。

# 元profileの選択開発

受け手の実順序も含める新規開発は `cases --suite original-catalogue-ordered --match TEXT` と `package --suite original-catalogue-ordered --develop --case NAME --out NEW.zip` を使う。元catalogueから1〜4件だけを準備し、同じ共有実行器と全比較器へ接続する。ナガ/ティア各30秒の固定2件は `original-catalogue-support` で独立Metal認定済み。`original-catalogue-support-cache-only` は同じ2件へCUBIN/O1・compile cacheとpaired generationの必須hitを要求する。実CUDAは未確認で、任意選択はdevelopment-only。[順序readback・元出力保持・範囲](portable-original-catalogue.md)。

`cases --suite original-catalogue --match TEXT` は全profileを準備せずmetadataだけを列挙する。`package --suite original-catalogue --develop --case NAME --out NEW.zip` は明示1〜4件だけを元定義のまま共通compilerへ渡す。固定群`original-catalogue-initial`は共通の2,048行bankを使い、Modernia30秒の全1,618件を含む4入力がM5 Metal・独立監査でsealed。`package --suite original-catalogue-initial --out NEW.zip`から通常の固定packet実行を使う。`original-catalogue-initial-cache-only`は同じ計算/入力/goldenにCUBIN/O1・compile cache必須とpaired generation必須を適用する。実CUDA未確認、全キャラ認定ではない。[選択規約・検査・次の容量拡張](portable-original-catalogue.md)。

`physical-generation-locks`最新版は専用arenaの10入力（native6/raw拒否4）、入力104400/出力806912wordです。全32個の既存スキル対象setを保ち、full_chargeのキューダメージ・死亡・再召喚を追加して独立Metal sealしました。旧幅を受け入れず、Python/Slang/Swiftで一致を検査します。[移設と検証境界](portable-heavyarms-lock-selection.md)。

`physical-generation-locks`は、既存の充填周期と実射撃通知を、元index20の2射撃上限・世代付きmembership・発射snapshotへ合成した明示モデルです。Metal7入力（native3/raw拒否4）を独立seal。`package --suite physical-generation-locks`から通常のrun/seal経路を使います。元index0は周期観測用self marker projectionで、距離選択・実ハイド・順番攻撃・元全25効果は未完了です。[検証境界](portable-heavyarms-lock-selection.md)。

`named-generation-locks`は実敵poolと名前付き上限readerに接続した明示membership契約です。M5 Metalで16入力（native10/raw拒否6）を独立seal。`package --suite named-generation-locks`から通常のrun/seal経路を使います。外部provider順のみで距離選択・充填event・元全25効果は未接続です。[範囲と失敗履歴](portable-heavyarms-lock-selection.md)。

Windows向けコンパイルは固定packetのcwdで `compile-plan --artifact-kind cubin --ptxas-level 1 --memory-limit-mb 2048 --timeout 60 --out UNIQUE.json` を先に実行します。artifact互換性のみを検査し、compilerやGPUは実行しません。[PTX診断／sealed CUBIN経路と手順](portable-compile-plan.md)。

`model-check --summary --out UNIQUE.json` は完全な監査JSONを保持し、stdoutだけを約1KBの状態・保存先・SHAへ絞ります。監査範囲を削る指定ではありません。通常のstdout全文も従来どおり利用できます。

`snapshot-check --original-workspace EXISTING --validation-root ISOLATED --out ISOLATED/NEW.json` はCPU専用のWindows観測診断です。失敗段階と数値codeだけを記録し、compiler／GPUを起動しません。[制約・結果の意味](portable-windows-snapshot-check.md)。

`coordinate-arc-arena`140／`coordinate-landing-arena`40 は共通resource view格納のsealed Metal suiteです。旧logical出力を全保持し、追加scratchも全word照合します。通常のpackage→run→seal経路を使い、standaloneのためresident generation-cacheは指定しません。Windows新sourceのstackと実行は未確認。[容量・alias・証拠](portable-coordinate-arc-arena.md)。

最新sealed `coordinate-typed-owner`80（native45／拒否35）は、明示BODY所有のHPシールドとcurrent enemy field／実counter完了を共通Slangへ接続したsuiteです。元Prim全71定義を保持し、M5保存出力のfresh全範囲監査で一致、旧67全byte保持。`package --suite coordinate-typed-owner` を使います。GPU実行1回・retry0、観測修正後の追加GPU0、最終関連100／制御507成功。CUDA実行・全キャラは未完です。[実装・観測修正・保存結果の厳密な再利用](portable-coordinate-typed-owner-gpu.md)。

`seal --comparison-group-size 24 --timeout 180` は全入力を逐次fresh childへ分割し、全範囲を厳密に集約します。`replay` は `--comparison-group-size 24 --audit-timeout 180` を使えます。未担当rawを含む全ハッシュを検査し、部分結果だけでは成功にしません。旧67全golden保持、GPU再実行0。総高速化ではなく、検証を省かずchild上限を守る経路です。[分割監査の使い方と実測](portable-comparison-groups.md)。

`reference --suite coordinate-typed-owner-common --out UNIQUE.json` はBODY所有を明示した型付き対象と現在対象fieldのCPU契約5件です。元Prim全71定義を保持し、別宣言counter監査で物理handle／所有者／camera照準の分離を検査。このCPU referenceコマンド自体はGPU認定を行いません。専用GPU suiteの実証は本頁冒頭を参照してください。[CPU契約と当時の検証範囲](portable-coordinate-typed-owner-reference.md)。

`coordinate-typed-actor` はsealed67入力（native40／拒否27）。元Reiの現在対象ダメージを、元定義を保ってBODY／ADD／手動typed照準へ接続し、M5実出力とfresh独立監査で一致しました。`package --suite coordinate-typed-actor`、CPU契約だけなら `reference --suite coordinate-typed-actor-common --out UNIQUE.json` を使います。敵fieldの所有権継承・現CUDA／全キャラは未完です。[現在対象ダメージの範囲](portable-coordinate-typed-actors.md)。

`coordinate-typed-aim` はsealed59入力（native36／拒否23）。型付きframe照準・手動・ADD優先・元の実FB追従を同じCUDA／Metal consumerへ接続し、M5実出力とfresh独立監査で全一致。`package --suite coordinate-typed-aim` と `arena-check --profile coordinate-typed-aim-v1` を使います。現在CUDA／論理current-enemy recipient／ゲーム規則／全キャラ認定は未完です。[範囲と証拠](portable-coordinate-typed-aim.md)。

`reference --suite coordinate-typed-aim-common --out UNIQUE.json` は型付き対象のframe照準契約7件（正例6／未対応拒否1）を検査します。CPU専用で、GPU wireはまだ拒否します。[照準契約と次の共有consumer](portable-coordinate-typed-aim.md)。

`coordinate-typed-weapon` はsealed46入力（native29／拒17）。元の通常射撃をtyped対象へ接続し、M5 Metalと独立監査で一致しました。`package --suite coordinate-typed-weapon` を使い、compactはまだ指定しません。CPU観測は全指紋を保持して約2.58倍に短縮。`arena-check --profile coordinate-typed-weapon-v1` で同じbank配置を確認できます。現CUDA／typed auto aim／全キャラは未完です。[範囲と検証記録](portable-coordinate-typed-weapon.md)。

`reference --suite coordinate-typed-weapon-common --out UNIQUE.json` は、元武器の実packetとtyped対象のCPU契約7件を検査します。散弾内のhandle固定・実着弾への遅延・親量・RNG・history超過を確認します。このCPUコマンド単独ではGPU認定を行いません。[通常射撃CPU契約](portable-coordinate-typed-weapon-reference.md)。

開発時のCPU基準重複計算は `package --develop --native-baseline-package PATH` で減らせます。CPU依存と入力が一致する固定基準の期待hashだけを引き継ぎ、fresh run／独立sealは維持します。実35入力の作成3.48秒、22nativeのrun再計算177.03秒・60／488検査成功。[適用条件と使い方](portable-development-expectations.md)。

最新の `coordinate-typed-live-aim`35（native22／拒否13）は、正本の実照準bankを型付きスキルselectorへ渡すsealed suiteです。`package --suite coordinate-typed-live-aim --compact` を使います。M5実GPU・独立監査済み、旧28の全出力保持。操作overlayと元操作保持を区別し、通常武器命中／型付きauto aim／現CUDA／全キャラは未完です。[実照準の範囲と記録](portable-typed-live-aim.md)。

従来の `coordinate-typed-geometry`28（native18／拒否10）は固定pointと実生存世代から実攻撃対象を選ぶsealed suiteです。既存10の全出力と旧型付きCUDA/MSL生成物を保持。[範囲と検証記録](portable-typed-geometry.md)。

従来のprivate合成入口は `coordinate-typed`10（関連53／制御480・Metal独立監査済み）です。元の座標射撃と型付き対象Frameが同じRuntime・時計・RNGで動きます。型付きへの自動aim／公開GPU／全キャラは未完です。[合成範囲と配置検査](portable-coordinate-typed-targets.md)を参照してください。

`coordinate-original-owned`5 は元アインの羽4→6→2枚と、元シンデレラ：クリスタルウェーブの弾換算8回を検証するsealed suiteです。M5全5・独立fresh監査・関連29／制御480検査成功（Win1skip）、元推定モデルの警告を保持。固定shared source・生成CUDA/MSL全byte保持／Slang0・実Metal必須pipeline hit。`package --suite coordinate-original-owned --compact` を使います。[観測透過性・状態負例・残る分類](portable-original-owned-sources.md)。

`coordinate-original-accum`4 は元ドロシーの期限切れ放出と元トロニーの4回の上限放出を、全73／74定義のまま検証するsealed suiteです。M5全4・独立fresh監査・関連26／制御480検査成功（Win1skip）、GPU source変更0・paired generation全byte保持／Slang0・実Metal必須pipeline hit。`package --suite coordinate-original-accum --compact` を使います。[蓄積実証・共有展開・保存](portable-original-accumulation.md)。

`coordinate-original-harmful-stack`2 は元アンカーの3回目フルバーストでの有害stack3→2を、6秒対照／86秒autoで検証するsealed suiteです。M5・独立fresh監査・関連32／制御476検査成功（Win1skip）。固定raw4096件を保ち、全5031packetの時刻・対象・damageを共通SHAで照合します。`cases` のsuite引継ぎ漏れも修正しました。`package --suite coordinate-original-harmful-stack --compact` を使います。[実証・CPU効率・保存](portable-original-harmful-stacks.md)／[全順序packet codec](portable-coordinate-packet-history.md)。

`coordinate-original-enemy-stack`4 は元ミハラの敵DoTスタックを、実命中・上限・戦闘不能・burst引継ぎまで検証するsealed suiteです。通常recipientから漏れていた周期DoT対象を共通stack処理へ接続し、M5全4・独立fresh監査・関連29／制御476検査成功（Windows1skip）。実装修正ではsource/cache identityを変え、data-only再利用は拒否します。`package --suite coordinate-original-enemy-stack --compact` を使います。[修正・証拠・次の減算候補](portable-original-enemy-stacks.md)。

`coordinate-original-init`3 は元ソーダ：トゥインクルバニーのスキルレベル1/4/10で40/45/50スタック生成→burstで17消費→通常攻撃で再加算まで検証するsealed suiteです。固定shared入口・CUDA/MSL生成物を保持、M5 Metal全3と独立fresh監査に成功。`package --suite coordinate-original-init --compact` と既存run経路を使います。kind受付と全キャラ認定を分けます。[範囲と検証記録](portable-original-stack-init.md)。

固定入口 `coordinate-original-shared`6 と元ライの `coordinate-original-decoy`3 を追加しました。両suiteは同一GPU sourceを使い、`source-reuse` が不変package・厳密なCUDA/MSL生成pair・consumer・追加コンパイル0をファイルだけで検査します。`entry-inventory --suite coordinate-original-shared --out UNIQUE.json` は受付拡張8profileを旧入口との差分として保持します。kind受付0拒否を全キャラ認定へ読み替えないこと。[使い方・実Metal cache・残件](portable-original-shared-entry.md)。

# 共通GPU検証CLI

未受付項目の次の調査は `entry-inventory --suite coordinate-original-cleanse --out UNIQUE.json` から始めます。元source行・stat・target・timing・参照先の分類と、同一プロファイルのkind依存を自動出力します。入力変換失敗は別一覧で保持。静的監査だけでGPU対応数へ読み替えないこと。[分類方法と次候補](portable-entry-operators.md)。

`coordinate-original-cleanse`4 は元ココア／ミカ：スノーバディ／ロザンナの部分解除・全員解除・敵バフ解除を実証したsealed suiteです。`package --suite coordinate-original-cleanse --compact` を使います。味方抽選と座標射撃を同じMTへ接続し、実整数draw・全624語と632語の出力同一性を検査。M5保存出力の再照合・独立fresh監査・関連28／制御476が成功（Win1skip）。ボス攻撃のdebuff入力・現CUDAは未完了です。[範囲と最初の比較失敗](portable-original-cleanse.md)。

`coordinate-original-stacks`4 は元ペッパー／ルピー／マルチャーナ：マリンスタディの現在スタック増加・上限・消費・再充填を検証したsealed suiteです。`package --suite coordinate-original-stacks --compact` を使います。既存共通16／17／19を接続し、M5保存出力の再照合と独立fresh監査、関連22／制御476検査が成功（Win1skip）。無期限は実wire bitsで照合し、有限1e30と区別します。静的kind拒否30をGPU対応数へ読み替えないこと。[検証範囲と初回比較失敗](portable-original-stacks.md)。

`coordinate-original-ammo`4 は元のギロチン：ウィンタースレイヤー／ノワール／アルカナ：フォーチュンメイト／グレイブの割合・固定補充と負の割合、正のゲージ段階通知を検証したsealed suiteです。`package --suite coordinate-original-ammo --compact` を使います。共有kind宣言・既存共通handlerを使用し、M5 Metal全一致・独立fresh監査・関連23／制御476成功（Win1skip）。kind受付46拒否をGPU対応数へ読み替えないこと。現CUDA／全キャラ認定は未完了です。[検証範囲](portable-original-ammo.md)。

`coordinate-original-resources`3 は元E.H.／ネオン：ビジョンアイの固有ゲージ加算・消費・上限を共通handlerへ接続したsealed suiteです。M5全3・独立監査・機能19／制御476成功（Win1skip）。sampled-vital kind条件を共通宣言からSlang／CPUへ生成し、正例の未対応kindをnative/GPU前に拒否します。`entry-inventory --suite coordinate-original-resources --out UNIQUE.json` で静的kind拒否を調べられますが、GPU受付全体の認定ではありません。[範囲と残件](portable-original-resources.md)。

`coordinate-original-burst-revival`4 は元ラプンツェルのB1復活とセンチのスキル残り待機短縮を既存共通handlerへ接続したsealed suiteです。M5 Metal全4・独立監査・機能39／制御476成功（Win1skip）。`entry-inventory --out UNIQUE.json` は開発checkout／full packageで全266元profileの座標入力とkind一覧をCPU専用調査し、GPU受付・計算認定とは分けます。[範囲・初回失敗・残件](portable-original-burst-revival.md)。

`coordinate-original-revival`3 は元マナ編成のdown／復活・条件状態解除を既存共通shaderで検証したsealed suiteです。`package --suite coordinate-original-revival --compact` を使います。M5 Metal・独立fresh監査・機能38／制御476成功（Windows1skip）。`model-check` は全266元編成の同名damageも静的分類し、未観測の非周期制限を実データの未対応から分けます。[範囲と残件](portable-original-revival.md)。

`coordinate-original-lifecycle`3 はハランの死亡通知とクルミのバーストによる同名DoT再付与を、完全元編成のままM5 Metal・独立fresh監査で照合したsealed suiteです。`package --suite coordinate-original-lifecycle --compact` を使います。元定義別の実発火数とtick位相を検査し、既存共通shaderを再利用します。死亡敵固有の感染判定・召喚攻撃payload・現CUDAは未完了です。[検証範囲](portable-original-lifecycle.md)。

最新の `coordinate-original-periodic`4はハラン／クルミの元72／70効果と武器を保持し、同名DoTをowner／登録IDで照合してM5全一致・独立fresh監査91.14秒でsealed登録済みです。shader変更0、生成／Metal pipeline cacheを必須再利用。groupのliteral結合も共通化し、元武器でmulti_hit対象数を満たせない部分は正本モデル側の不足として残しています。[同名DoTとgroupの境界](portable-original-periodic.md)。

最新の `coordinate-original`10は元の完全編成68〜81効果・武器・操作設定を保持し、実被弾での名前指定解除までM5 Metal全一致・独立fresh監査238.65秒でsealed登録済みです。保持履歴と省略件数の厳密な検査、比較器だけの固定source-bound再配布、private opt-in／公開拒否の別監査も共通CLIへ接続しました。[元編成と検証境界](portable-coordinate-original.md)。

最新の `coordinate-healing`340（native291／拒否49）は回復貯蔵・分配・放出を座標戦闘へ接続し、保存Metal全件一致・独立fresh監査225.42秒でseal済みです。新16world＋拒否2、旧322全raw保持。新規GPU1回、観測器修正後の再GPU0。厳密な観測基準移行と監査内の静的入力再構築削減も共通CLIへ接続しました。[回復と元編成への接続境界](portable-coordinate-healing.md)。

最新の `coordinate-auto-reload`322（native275／拒否47）は保留自動装填・期限・遮蔽とmode弾倉補充を共通実行器で検証し、M5 Metal全一致・別processのfresh監査済みです。`metal-device-probe`／通常runのCPU前可視性検査、未claim開発packetの `refresh-tests`、同じfresh sealの `--audit-receipt` も追加しました。最終機能33・制御470検査成功（Windows1skip）。[自動装填と検証記録](portable-coordinate-auto-reload.md)／[Metal可視性](portable-metal-device-preflight.md)。

`coordinate-mode-actions`313（native266／拒否47）はmode中の明示hold／coverと射撃後待機を共通実行器で照合し、M5 Metal全件一致・別processのfresh seal済みです。元武器がchargeならcoverで待機時計も解除します。静的base時計とwire登録の矛盾をCPU／GPU計算前に拒否。旧293の入力・nativeは不変、raw287全byte保持／6件は未射撃charge武器のnextShotだけ変更し全差分を保存。[mode操作と待機](portable-coordinate-mode-actions.md)。

`coordinate-burst-control`293の通常比較は、同じ親の実native事前値と生成イベント記録を既存ParentOraclesで再利用します。独立監査はfreshを維持。CPU専用 `coordinate-parent-check --source-package PATH --source-capture PATH --out NEW_PATH` で全件のfresh比較との一致・追加native0回・原capture保持を確認できます。このコマンドはGPU証明を作りません。[仕様と測定](portable-coordinate-parent-oracles.md)。

最新のキャラmode状態入口は`coordinate-squad-mode`251（native213／拒否38）。mode終了から次char tickまでの状態を共通化し、全体遮蔽・調停前の方針要求と装填callback進入へ接続。M5 Metal全件一致・独立seal済み、旧222の全1,571,632,128byteを保持。`seal --compiler-certificate PATH`は同じfresh監査からgoldenとfull-source証明を作成し、別のnative再監査を省く。CUDA実機の成功は別途必要。[mode状態](portable-coordinate-squad-mode.md)／[共同seal](portable-joint-seal-certificate.md)を参照。

最新のスクワッド操作入口は`coordinate-squad`222（native189／拒否33）。focus＋cover_allをカメラ調停前の共通実行器へ接続し、M5 Metal実行1回＋保存結果replay・独立sealで全件一致。旧196入力の全1,387,567,104byteと入力・native指紋を保持。型付き入力拡張は`readback-retain --input-extension coordinate-squad-v1`で監査する。CLIとblock検査器の契約一覧を共有し、二重parserの不一致を回帰検査する。武器変更終了tick、burst操作方針、現CUDA実機は残件。[スクワッド操作](portable-coordinate-squad.md)参照。

最新の条件付きcover／reload入口は`coordinate-policy`196（native171／拒否25）。本人FB coverと4方針・5アンカー・if_dryを共通Slangへ接続し、M5 Metal全件一致・独立seal済み。旧169の全input prefix／native／1,196,163,072byteを保持。入力拡張は`readback-retain --input-extension coordinate-policy-v1`で型付き照合し、汎用の差分無視は行わない。公開受付・全キャラ・現CUDA実行は未完了。[方針の共通実行器](portable-coordinate-cover-policy.md)参照。

武器skill指定と乱数BODY／ADD receipt groupを共通実行器で実証。sealed coordinate-sampled-delivery136（CPU正本126／拒10）がGPU禁止replay・独立sealで全一致。新14契約、CPU95／制御428（Win1skip）、旧120全849346560byte保持。GPU／compiler／transport／数値ソース変更0、旧13 CUDA-MSLペアを保持し生成cache hit・Slang0。Metal実archive hitでPSO91.958→.002588秒、GPU.480秒／子3.491秒。実GPU1／host修正版再GPU0。観測hookのcode identityを修正し、metal-cache-probe、package前の監査データ検査、準備64MiBの容量余裕を追加。現CUDA未取得／Windows新依頼0。手動cover・追加武器／回復混合・全元定義は残る。全キャラ0／20gap／UI CPU／未達。[乱数groupとcache](portable-coordinate-sampled-delivery.md)。

乱数戦闘へ既存の武器変更／HP・遮蔽物回復／現在HP減少を接続。sealed coordinate-sampled-vital120（CPU正本112／拒8）がM5 Metal全一致・独立seal。新29契約、CPU63／制御421（Win1skip）、旧89全629932032byte・旧12 CUDA-MSLペア保持。実総口と初弾係数を受動観測し親量を検査、damageスキルなしの整数総計初期化漏れを修正。新GPU2／retry0、GPU.491秒／初回PSO91.958秒。容量追加0、通常run内のCPUゲートを使い事前CPUの重複を避ける。手動cover packing・追加武器flag／回復混合・sampled group・全元定義は残る。現CUDA未取得／Windows新依頼0、全キャラ0／20gap／UI CPU／未達。[武器変更と回復](portable-coordinate-sampled-vital.md)。

乱数保留バーストの旧B3／opt-inを共通residentへ接続。sealed coordinate-sampled-burst89（CPU正本83／拒6）がM5 Metal全一致・独立seal。新24契約、旧62全373817344byte prefix・追加zero、旧11 CUDA-MSLペア保持。CPU55／制御421（Win1skip）／正本24。512entry×256hit bankを明示し出力+1MiB、Runtime不変。旧B3のbuff除外setterとmarker受付を修正し、修正前失敗保存・新GPU2回／同claim retry0。GPU.486秒／初回PSO92.568秒。異strideのreadback-retainを共通CLIへ追加。現CUDA未取得／Windows新依頼0。武器変更／heal・sampled group・全元定義は残る。全キャラ0／20gap／UI CPU／未達。[保留バースト](portable-coordinate-sampled-burst.md)。

通常damageのhit別critical・cast snapshot・子queueを共通residentへ接続。sealed coordinate-sampled-skill62（共通CPU59／拒3）がM5保存結果replay・独立sealで全一致。実GPU1／比較修正版の再計算0。CPU43／制御419（Win1skip）／正本22、旧38全229113856byteと旧10 CUDA-MSLペアを保持し旧拒否1件を正例へ移行。数値probeは125→4ソースへ独立し14045入力実証、生成コード／全449440byte保持・Metal cache hit。replay容量ゲートと保存版registry監査をCLIへ追加。保留バースト・武器変更／heal・sampled groupと全元定義は残る。現CUDA未取得、全キャラ0／20gap／UI CPU／未達。[乱数スキルとCLI](portable-coordinate-sampled-skill.md)。

乱数物理射撃の親参照量を共通residentへ接続。sealed coordinate-sampled-parent39（共通CPU36／拒3）とpacket-ratio14045がM5 Metal全一致・独立seal。整数128bit÷muzzleを一度だけnearest-even丸めし、dealt_fixed_damageの既存通知／queueへ接続。大整数の旧double総計差も実計上の整数sidecarで解消し、従来double加算の検査を保持。CPU28／制御416（Win1skip）／正本16、旧23全138674176byteと旧9 CUDA-MSLペアを保持。容量追加0、実GPU計4／同claim retry0／raw削除0。戦闘GPU.464秒／初回PSO92.693秒、数値cache hit・GPU.002秒。現CUDA未取得／Windows新依頼0。通常damage RNG・武器変更／heal・sampled group owner・全元定義は残る。全キャラ0／20gap／UI CPU／未達。[親参照量・整数総計](portable-coordinate-sampled-parent.md)。

乱数物理射撃を共通resident executorへ接続。sealed coordinate-sampled-battle23（共通CPU20／拒3）がM5 MetalのGPU禁止replay・独立sealに成功。1256ペレット／1397packet／5498 MT word、127対象・1024ペレットを検査。物理MTとboss MTを分離し、shot snapshot・個別critical・auto／charge通知・muzzle core平均・not_core／prob条件抽選を接続。期待値scratch再利用でRuntime138952byte／入力109528／出力1507328word不変。GPU.448525秒／初回PSO91.909787秒。1024件のteam履歴省略を厳密検査する比較viewへ修正、実GPU計2／修正版再計算0／retry0。旧11raw全66322432byte・旧8 CUDA-MSLペア保持。現受付buffのみ、非buff・親量・sampled group ownerと全元定義は残る。現CUDA未取得／Windows新要求0。全キャラ0／20gap／UI CPU／未達。[乱数射撃の接続](portable-coordinate-sampled-battle.md)。

乱数着弾点の共通producer coordinate-sample-v1を既存MT19937へ接続。sealed coordinate-sample107（共通CPU93／拒14）、1296点がM5 Metal全bit一致・独立seal。MT全624状態／index／消費・拒否数／後続抽選を照合、GPU1回.018514秒／PSO.278665秒／retry0。実CPUのrandom経路11契約で63ペレット／77packet／362wordとcritical再利用を確認。最終CPU12／control416（Win1skip）、旧10閉包193sourceとmixed244 current seal保持、旧GPU再実行0／Windows0。非residentのgeneration cacheは既存reflection guardで開始前停止し、guard不変の通常生成を使用。GPU戦闘callerは未接続。次はphysical専用MT状態→per-pellet core／crit／通知→個別snapshotとgroup delivery。全キャラ0／20gap／UI CPU／未達。[乱数着弾点と正本契約](portable-coordinate-sampling.md)。

座標弾・groupへ有効なsplit_damageとbuff／shield／vanish／move／groggy／直接boss attackを合成。sealed coordinate-mixed244（共通CPU218／拒26）がM5 Metal全一致・独立seal、正例8484 frame、旧225全1356595200byte保持。均等配分・ADD途中消滅・対象順位／seed選択・tie偶数丸め／ゼロ丸めを含む新19契約。旧shareは現parserのnative_reference_exclusionとし、有効splitの移植と区別。距離モード切替と別PART packet診断traceを共通コードで修正し旧7 CUDA-MSLペア全byte保持。CPU149／control416（Win1skip）、修正版GPU3.724秒／初回PSO91.484秒。修正前旧sourceのwarm必須cache hitは.002612秒。CPU上限60停止はdispatch0、v3失敗／v4成功の実GPU計2／同claim retry0、原本保持。現CUDA未取得。次はsampling RNG・召喚攻撃／debuff payload・全元定義認定。全キャラ0／20gap／UI CPU／目標未達。[混在worldと割合配分](portable-coordinate-mixed.md)。

`coordinate-group`225（共通CPU199／拒26）は座標packetのBODY／ADD receiptを共通groupへ接続したsealed profile。M5の保存readbackをGPU禁止replayで再照合し独立seal、GPU dispatch1回。`package --suite coordinate-group --compact` を使う。入力109528／出力1507328word、readback系の `--case-words 1507328` と実consumerを登録。旧6 CUDA-MSLペア保持、現CUDA未取得。[座標GPU group](portable-coordinate-group-gpu.md)を参照。

`reference --suite coordinate-group-common --out /tmp/new.json` は座標弾の実packetとgroup receiptを比較するCPU17契約。full immutable packageから実行し、GPU／packingは0。`coordinate-control`のCPUゲートへ新8＋既存group31検査を追加した。GPU group接続は未完了。[group正本契約](portable-coordinate-group-reference.md)を参照。

`coordinate-control`206（共通CPU182／拒24）は照準と武器変更・reload・散弾・tap／holdを共通executorへ合成したsealed profile。M5 Metalと独立seal、CPU95／control416が成功。`package --suite coordinate-control --compact`を使う。`model-check`はgroup writerの3重複と未実装の移設／caller接続を区別する。[操作合成](portable-coordinate-control.md)を参照。

`coordinate-aim`190（共通CPU166／拒24）は手動照準・camera調停を共通resident実行器へ接続したsealed profile。4window／5anchor／前回skill点と今回physical点／7059frameをMetal実証した。`package --suite coordinate-aim --compact`を使う。[共通GPU照準](portable-coordinate-aim-gpu.md)を参照。

`reference --suite coordinate-aim-common --out /tmp/new.json` は手動照準・camera調停の共通CPU30契約（GPU0／packing0）を検査する。定時skillの前回照準と、調停後physicalの新照準を区別する。静的IR／GPU接続の残件は[照準接続契約](portable-coordinate-aim-contract.md)を参照。

`coordinate-matrix`151（共通CPU136／拒15）は範囲スキルの静的回転係数を共通数値規約へ接続したsealed profile。旧cache133の全input／rawを保持し、18worldを追加。CUDA／Metal共通実行器・生成cacheをそのまま再利用する。[共通area matrix](portable-coordinate-matrix-common.md)を参照。

`coordinate-cache`133（共通CPU118／拒否15）と`coordinate-round`9046（正例9039／拒否7）はM5 Metalで全word照合・独立seal済み。共通CLIの通常手順を使う。Geometryごとの最初のLandingを全射手で共有し、127対象時231件／対象0時4096件を超えると明示拒否する。旧120の入力／元nativeと全semantic領域を保持し、作業scratchと新cacheは別profile指紋。現在のWindows CUDA実行は未取得。[Geometry cache](portable-coordinate-cache.md)を参照。

`coordinate-core`120（共通CPU106／拒否14）はM5 Metalで全word照合・独立seal済み。coreの既存graph寿命・中心・同径優先・既定照準を接続し、旧84の入力prefixとnative／GPU rawを保持。専用entryは入力108792／出力1310720word。`package --suite coordinate-core --compact`から共通手順を使う。Windowsの現CUDA実行は未取得。[live core](portable-coordinate-core.md)を参照。

`coordinate-accum-emission`84（共通CPU78／拒否6）はM5 Metalで照合・独立seal済み。既存蓄積49world＋geometry4worldを追加し、旧31全entryを保持する。immutable package→CPU preflight→bounded GPU→独立sealの共通手順を使う。ADD共有・敵攻撃sceneは未対応、現在のCUDA実行は未取得。[座標蓄積放出](portable-coordinate-accum-emission.md)を参照。

`coordinate-quantity`31（共通CPU25／拒否6）と`packet-integer`305（正例294／拒否11）はM5 Metalで照合・独立seal済み。immutable package→CPU preflight→bounded GPU→保存結果sealの既存手順を使う。`reference --suite coordinate-accumulation-policy --out /tmp/new-policy.json`はCPU正本のtarget蓄積除外3worldだけを検査し、GPU対応を主張しない。現在のCUDA検証は未取得。[整数参照量・cache保持](portable-coordinate-quantity.md)を参照。

共通の可変指数unit pow・GL10定数・形状arcをexpected landingへ接続。sealed `coordinate-power`909（共通CPU898／拒否11）と`coordinate-landing`40（共通CPU26／拒否14）がM5 Metal全word一致・独立seal、MPFR2434入力0 ULP。127対象／5098cut／1024arcを保持し、初版pipeline stack失敗を出力arenaと参照渡しで解消。形状準備をGPU内で一度だけ行い、旧全1715840byte保持・新準備データ照合、GPU17.130→.424秒（単一probe測定対約40.4倍）。最終CPU17／関連・制御462（Win1skip）、full2969→compact1636全byte一致。新kernel3／pipeline失敗1／同claim再試行0、旧主要7suite再GPU0。raw全SHA-byte-inode保持の疎化で1096093696byte回収。Windows新要求0、API active ID不在・CUA Codex安全制約で未送達。物理packet／resident戦闘caller／RNG／aim・cache key／全元定義と公開受付は未接続。全キャラ0／20gap／UI CPU／目標未達。詳細[共通着弾確率](portable-coordinate-landing-v1.md)とresearch/portable-coordinate-landing-v1-checkpoint.json。以下は履歴。


共通数値profileをGPU側の角度→回転係数→形状距離／contains／円・半平面・grow付き回転矩形arc／区切り半径へ接続。sealed `coordinate-geometry`1224（共通CPU1209／拒否15）がM5 Metal全word一致・独立seal。旧正本と方針不変の288入力を距離／breaks照合し、別方式Decimalの円弧内外200点超も成功。最終CPU18／関連・制御445（Win1skip）、full2950→compact1621全残存byte一致。GPU1／retry0／旧6suite再GPU0。GPU .188791秒、Swift module cache利用でexecute全体1.722503秒。Windows新要求0、直前の数値依頼はAPIエラーで未送達。積分／pow・GL定数規約／物理packet／resident戦闘caller／全元定義・公開受付は未完了。全キャラ0／20gap／UI CPU／目標未達。詳細[共通形状・円弧](portable-coordinate-geometry-v1.md)とresearch/portable-coordinate-geometry-v1-checkpoint.json。以下は履歴。


決定的な共通数値profile `coordinate-binary64-v1`のsin/cos・atan2・acos・整数sqrtを共通IRからCPU／Slangへ実装。sealed `coordinate-numeric`2783（共通CPU2771／拒否12）がM5 Metal全word一致・独立seal、独立Decimal10451入力は最大1/1/1/2/0 ULP。共通CLI `numeric-audit`追加、最終CPU9／関連・制御436（Win1skip）、full2944→compact1614全残存byte一致。新GPU1／retry0、旧5suite再実行0。CUDAの新規計算実証は未取得。回転caller・arc生成・積分・物理packet・共通resident戦闘への接続と公開受付は未完了。全キャラ0／20gap／UI CPU／目標未達。詳細[共通数値v1](portable-coordinate-numeric-v1.md)とresearch/portable-coordinate-numeric-v1-checkpoint.json。以下は履歴。


`coordinate-arc-scalar`640入力（native632／拒否8）は、共通の円弧wrap／shift／補償付きmeasureと、生成被覆の差・交差をMetalで実証・独立seal済みです。active区間だけを移動する最適化でも全rawを保持し、今回のGPU測定は2.52秒→0.037秒。数値方針は明示回答により決定的な共通規約へ選定済みで、`model-check`は選択済み／共通三角関数未実装を分けます。[円弧の数値演算](portable-coordinate-arc-scalar.md)を参照してください。

`model-check --out /tmp/new-model.json`で、既存の未対応分類・正本consumer・共通arena監査と、座標物理弾の依存関係をまとめて確認できます。CPU/GPU計算を実行せず、旧GPU証明とcurrent sourceの不一致も明記します。`coordinate-arcs`135入力は遮蔽に必要な共通区間演算をM5 Metalで実証・独立seal済みです。物理着弾全体の接続は未完了。[座標物理の移植境界](portable-coordinate-physical-frontier.md)を参照してください。

座標と実射撃groupの合成入口は`coordinate-composed`97入力（native81／拒否16）。body-only物理射撃と座標skillを同じGPU常駐Runtimeへ接続し、Metal実GPUで全出力を照合・独立sealしました。CUDA／Metalは同じSlang入口・定義・比較器を使います。Windowsの新しい計算実証は未取得です。[合成実行器](portable-arena-composed-executor.md)を参照してください。

```sh
python scripts/nikke_gpu.py package --suite coordinate-composed --compact --out /tmp/new-composed.zip
# 新規フォルダーへ展開し、そのフォルダーをcwdとして実行
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-composed-cpu
python scripts/nikke_gpu.py run --backend metal --cpu-only --smoke --capture /tmp/new-composed-control
```

出力1310720word（5MiB／入力）を確保します。座標物理部位・手動aim・全元定義の公開受付は未接続です。旧`coordinate-generation`88は独立入口として保持します。以降のsuperset表記と件数は各時点の履歴です。

`arena-check --profile coordinate|attack-group|combined-legacy|combined-v1 --out /tmp/new.json`で実consumerに結び付けた入力・出力の合成配置を監査できます。旧配置の結合は終了1。`combined-v1`はprivate合成入口へ接続済みですが、arena-checkは静的監査です。共通CPU smokeにも7検査を追加しました。[arena合成](gpu-arena-composition.md)を参照してください。

座標worldの最新private supersetは`coordinate-generation`88（native75／拒否13）です。世代交代時の対象名解決と期限切れ部位の通知順を接続し、旧76を全byte保持しました。[世代交代の着弾](portable-coordinate-generation.md)と[主実行器とのarena合成課題](gpu-arena-composition.md)を参照してください。

座標worldの最新private supersetは`coordinate-full-burst`76（native63／拒否13）です。opt-in保留弾と子receiptの座標snapshot移動を接続し、旧60と本体81のraw/inputを保持しました。[座標全バースト保留](portable-coordinate-full-burst.md)を参照してください。以前の入口は履歴です。

座標worldの最新private supersetは`coordinate-pending`60（native50／拒否10）です。旧形式B3本体保留を共通executorへ接続し、旧area52を全byte保持しました。opt-in座標保留や全キャラ対応の完了ではありません。[座標B3保留](portable-coordinate-pending.md)を参照してください。

共通wrapperの保存CUBIN戦闘は `gpu-linked` を使用します。2キーrequest・既存出所監査・全stage制限と現full objectの未完了監査は [保存リンク実行](portable-saved-linked-stage.md) を参照してください。

CUDA子が正常終了し親の比較だけが外側timeoutで中断した場合は、[readback回収](portable-readback-recovery.md)の`recover-readback`を使います。元失敗と欠落記録を保持し、別CPU監査で元比較器を実行します。GPUの再実行はありません。

[共通fresh分割監査](portable-shared-native-groups.md)の`saved-battle-audit`／`aggregate-native-groups`はCUDAとMetalの既存保存比較を共有します。Windowsは`audit-native-group` stageで1群ずつ実行し、部分成功と全入力一致、環境保全を区別します。

[起動前fresh検査の段階分割](portable-staged-native-preflight.md)は、sealed packetの全native検査を短いJobへ分け、全群の検証後に一度だけGPUを起動する明示的な経路です。通常runのpreflightや独立保存比較を省略する機能ではありません。

現行suite・入力数・source identityはCLI/package manifestを正とします。最新状態と次の作業は [Mac引き継ぎ](mac-handoff.md)、過去の進捗は [履歴](gpu-development-cli-history.md) に分けています。

座標形状の実戦接続・数値方針gapは [座標area](portable-coordinate-area.md) を参照してください。Metal52入力は一致済みですが、host trig差によりWindows入力検査が停止しており、両GPU完成とは扱いません。

入力gateが失敗した場合はcaptureの `cpu-input-mismatch.json` を確認してください。静的bytesの件数・row名・期待/実SHA・framingを最大64行まで自動記録します。raw値を公開したり、追加native/GPU実行やconsumed claimの削除で復旧したりする機能ではありません。

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

`compiler-full--attack-group-mixed` はcompiler-onlyでも `package --compact` を利用できます。Noneのcase adapterを補わず、指定CPU群とsmokeを保持します。現在のPTXをSlang/NVRTC再実行なしで現ownerへ復元した記録と制約は [compiler compact/cache](portable-compiler-compact-cache.md) を参照してください。他のcompiler aliasへ自動適用はしません。

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

run/cpu-only/smokeは全登録群を1個のfresh CPU workerへ渡します。群別ログ/receiptを保ち、欠落・zero tests・途中失敗・不完全receipt・CPU timeout（suite単体は既定60秒／明示した統合suiteは90秒、共通smokeは180秒）はGPU前に停止。詳細[CPUまとめ実行](portable-cpu-batch.md)。通常run childの出力は明示file modeで固定8MiBずつ保存し、全件監査を維持します。詳細[共通file転送](portable-file-transfer.md)。
# body蓄積と固定量放出の保持49入力

`destructible-body-accum-retention` は旧31の位置を維持して新18を追加した、Metal／native照合・独立seal済みの入口です。`--compact` に対応し、全60 CPU検査と全40 native照合を保持します。単独 `destructible-body-accum` 18入力は開発用なので `--develop` が必要です。実キャラのbody蓄積と、宣言poolの盾放出を区別し、元ドロシーの貫通受付は開放しません。詳細は [body蓄積・固定量放出](portable-destructible-body-accum.md)。

# 共有回復の受益者監査61入力

`destructible-body-heal-share-retention` は旧49の位置を保持して元レム等の全定義12編成を追加した、Metal／native照合・独立seal済みの入口です。`--compact` は全71 CPU検査と全52 native照合を保持します。GPU source／生成CUDA・Metalは前の49と全byte同一で、既存共通共有Frameを使います。単独 `destructible-body-heal-share` は開発用なので `--develop` が必要です。詳細は [共有回復の受益者監査](portable-destructible-body-heal-share.md)。

# 最新typed61の親process再利用

`destructible-body-heal-share-retention` の通常runは既存ParentOraclesを使い、事前照合で算出した52 nativeを同じ親process内だけで通常比較へ渡します。全比較・入力/provider/valueのstampは維持。`audit`／保存結果監査／独立sealは毎回freshです。86 CPU検査のためこのsuiteのCPU枠は120秒、GPU／compiler／Windows枠は以前のままです。新しいcacheファイルやreplay optionはありません。詳細は [共通比較器の親process再利用](portable-destructible-parent-oracles.md)。

## 座標物理の共通規約CPU比較

full packageで `python scripts/nikke_gpu.py reference --suite coordinate-physical-common --out UNIQUE.json`。
共通着弾規約を実戦CPUのpacket・通知へ接続する9worldの参照検査で、GPU実行・packingは禁止する。
旧host正本との同値やGPU受付の証明ではない。compactではreferenceコマンドを従来どおり拒否するが、
coordinate-landingの必須CPU群に同じ比較経路・旧物理・frontierテストを収録する。
詳細は `docs/portable-coordinate-physical-common.md`。

## 座標物理のGPU実戦検査

`package --suite coordinate-physical --compact` はsealed 23入力（共通CPU17／拒否6）を収録する。
既存の `unpack`／`run --cpu-only`／`run --backend metal`／保存結果監査を使う。
Windowsも同じ入力と比較器を使い、既存の低優先度・2GiB・180秒wrapperを維持する。
この入口では射撃groupを無効化し、活core・手動aim・RNGなどは未接続。
範囲と新旧回帰の証拠は `docs/portable-coordinate-physical-gpu.md` を参照。

## 明示cover・holdの共通実行器

`coordinate-manual` はsealed 169入力（native151・拒否18）。`package --suite coordinate-manual --compact` から共通手順を使う。静的な時刻・duration・untilだけをpackingし、cover・reload・charge・camera処理は共通Slang側で実行する。strict adapterとregistryのSOURCE不一致は入力準備前に拒否する。25の新規worldと旧136全byte保持をM5 Metalで確認済み。条件付きpolicy／cover_allと現CUDAは未検証。詳細は [手動操作の共通実行器](portable-coordinate-manual.md)。

## バースト候補policyの単体入口

`burst-control-policy` は347正本＋34拒否の381入力を共有CUDA/Metal sourceで検査し、M5 Metalで実証・独立seal済みです。`package --suite burst-control-policy --compact` で固定packageを作成できます。これは候補・delay・wait・pattern・明示順序・次FB予測の単体契約で、worldのcontrol.burst受付は未接続です。[契約と残り](portable-burst-control-policy.md)を参照してください。

## バースト操作の戦闘入口とCPU観測

`coordinate-burst-control` は293入力（native246／拒否47）を共通候補producer／既存戦闘実行器で実行し、M5 Metal全一致・独立seal済みです。旧251入力の全rawを保持しています。`package --suite coordinate-burst-control --compact` を使います。[実装・配置・残り](portable-coordinate-burst-control.md)を参照してください。

実GPU前のnative照合は `preparation.jsonl` の `cpu_native_oracle` でケース番号・名前・全件数・所要時間と失敗位置を観測できます。値の指紋が一致してから正常終了を記録し、失敗時は入力公開／GPU開始を止めます。processの生存はこの記録から推測しません。GPU禁止の `seal`／`compiler-certificate` のCPU監査だけ `--timeout 240` を明示可能です。293入力の通常比較195秒という実測に基づく分離で、GPU・Windows・compileの180秒上限は維持します。


## CPU前の停止とテストだけの更新

Metalの実行前可視性を `metal-device-probe` で確認し、通常runもCPU準備前に検査します。[可視性と失敗記録](portable-metal-device-preflight.md)。容量不足・device未検出はclaimを消費しません。

`refresh-tests` は、GPU未開始の失敗した開発packetに対する明示テスト更新です。元packet・失敗captureを保持し、新しいZIPを排他的に作ります。既存 `tests/test_*.py` だけを指定でき、shader・正本・入力producer・fixture・goldenは変更しません。workspaceの非test payloadが変わっていれば拒否します。旧CLIの限定launcher差分だけを認識し、出力には元のfrozen CLIをコピーします。GPU開始済み・claim消費済み・filtered/sealed packetは拒否します。元と新ZIPの全byte SHAを検査し、native battle／GPU呼出しは0です。

```sh
python scripts/nikke_gpu.py refresh-tests \
  --source-package /tmp/failed-preflight-package \
  --source-capture /tmp/failed-preflight-capture \
  --test tests/test_example.py --out /tmp/new-test-only-package.zip
```

新packetも通常のCPU tests・全native事前照合・GPU実行・独立fresh監査を通します。基準計算の再作成だけを避ける操作で、計算成功を認定しません。実証では `6594648c…` から `6b24922b…` へcompiler certificateテスト1ファイルだけを更新し、全322入力／native指紋と全非test byteを保持しました。元の容量停止とZIPは残しています。

`seal --audit-receipt NEW_PATH` は同じ1回のGPU禁止fresh子監査から、PID・比較domain数・live parent再利用なし・実測秒数・入出力SHAを保存します。通常比較のParentOracles再利用時間と独立監査時間を区別します。[自動装填](portable-coordinate-auto-reload.md)。

`coordinate-original-source`5は元定義の強制slot・持続延長と後続DoTを実Metal/fresh監査でsealした入口です。生成/cache検査の`portable_scope_snapshot_audit`はresident staged scopeのsnapshot→4word公開→dispatch→4word復元も検査します。全キャラ認定やCUDA成功とは区別します。[source操作とscope検査](portable-original-source-operations.md)参照。

`coordinate-original-reload`4は元編成・元のauto／キャラ既定操作で強制reloadと発射時計を検証するsealed入口です。`test_portable_world_reload`は共通observerとreaderを使い、setupで既に取る46ケースのnative結果から固定指紋も検査します。追加の二重native実行はありません。[強制reloadと比較範囲](portable-original-forced-reload.md)参照。

`coordinate-original-shield`9はラプンツェル：ピュアグレイス／モリ／キロの元全定義で、満タン・実損傷後の回復と再被弾・破壊を比較するsealed入口です。既存共通kind27と「シールド中」条件を接続し、M5 Metal全9一致・独立seal済みです。元計算を保つ明示opt-inのPython観測filterは3ケースで非filter版の全native指紋と一致を確認し、約7～10倍短縮しました。旧ケースの既定値はFalseです。[比較範囲・観測の適用条件](portable-original-shield-heal.md)を参照してください。CUDA／Metalは同じ入力・Slang・比較器を使いますが、現CUDA実行は未取得です。

`coordinate-original-cover`6はビスケット／リリの元全定義で、候補なし・再装填中の実被弾による1人／3人破壊と次burstの復活を比較するsealed入口です。M5 Metal全6一致・独立seal済み、関連26／共通制御476検査成功（Win1skip）。既存の味方抽選境界6検査を再利用します。元CPUに存在しないfinish時の数値queryで、味方late selectorを解決して乱数や対象を変えないことも検査します。[遮蔽物復活と診断の境界](portable-original-cover-revival.md)参照。現CUDA実行は未取得です。

## 不変payloadを共有する展開

同じファイルシステムの既存不変packageを指定すると、展開時点から同じpath・size・SHAのpayloadだけをhardlinkで共有できます。

```sh
python scripts/nikke_gpu.py unpack --archive /tmp/new.zip --dest /tmp/new \
  --reuse-payload-from /tmp/previous
```

通常のZIP全member検査に加え、参照manifestのidentityと全payloadを検査します。異なるファイルはZIPから作成、manifest自体は常に独立です。参照packageのコードは実行しません。symlinkや破損を拒否し、link失敗時の黙ったcopyへの切替はありません。両方のpayloadを不変として扱い、編集は開発checkoutで行って新しいpackageを作ってください。これは転送・領域共有の証明で、GPU計算やCUDA compiler cacheの証明ではありません。

package内CLIは `sys.dont_write_bytecode`、所有する検証子は `PYTHONDONTWRITEBYTECODE=1` で新しいPython bytecodeの生成を抑制します。独立したimportや設定を解除する故障注入はこの範囲に含みません。sourceの実行・ハッシュ検査・既存キャッシュ読取りは保持し、ユーザーのグローバル設定は変更しません。これにより、短い検証packageごとに数MBの `__pycache__` が蓄積するのを防ぎます。


## 型付き所有者の寿命とキャッシュ容量

`coordinate-typed-owner-lifecycle` はsealed88入力（native53／拒否35）。旧80を保持し、同じ共有entryへprojectile所有field・破壊済み同世代query・第2世代counter・古い世代counter抑止を追加しています。M5 Metalと全件fresh grouped監査で成功しました。`package --suite coordinate-typed-owner-lifecycle --compact` で固定packageを作れます。[比較修正・証拠・未対応範囲](portable-coordinate-typed-owner-lifecycle.md)を参照してください。現CUDA成功は未取得です。

`compress-generation-cache --cache ABSOLUTE_CACHE --out NEW_CAPTURE --apply` はmacOSの派生paired生成cacheだけをfilesystem圧縮します。全key／論理byte／SHAと4artifactを検査して同内容をatomic公開し、既存consumerは変更しません。[容量予算・claim・失敗保存・実測](portable-cache-filesystem-compression.md)を参照してください。CUDA driver cache／latencyの実証とは区別します。


`reference --suite coordinate-typed-logical-owner-common --out NEW.json` は元Prim全71定義のCPU3契約です。実counterの子fieldを宣言ADD1へ接続し、通常fieldのADD0経路と分離して照合します。共有戦闘registry・古い世代の拒否・物理命中handle保持を検査します。[ADD所有者CPU契約と次のGPU接続](portable-coordinate-typed-logical-owner-reference.md)参照。新policyはGPU compilerでまだ拒否し、Metal対応数へ加算しません。

## ADD所有者の共有GPUと復旧上の制限

`coordinate-typed-logical-owner` は99入力（native56／拒否43）のsealed基準です。旧88を保持したM5 Metalとfresh独立監査の成功を観測済みですが、一時領域の消失により元raw/captureは現在未取得です。[履歴証拠・復旧状態・未対応範囲](portable-coordinate-typed-logical-owner-gpu.md)を参照してください。新しいsource診断は `compiler-full--coordinate-typed-logical-owner` から固定できます。source certificateをCUDA compile/cache/launch成功へ数えません。

現在の永続worktreeは `.portable-recovery/runtime-resident`、新しい検証保存先は `.portable-recovery/proofs/`、生成cacheは `.portable-recovery/caches/slang-generation-v1` です。今回の消失rawを再作成するためのGPU再実行は行いません。再監査には元のbyteを復旧する必要があります。

`reference --suite coordinate-typed-owner-add-lifetime-common --out NEW.json` はADD所有者のgraph退場・再出現4契約です。完全Prim71定義の実counter子field、同世代の退場、gen2発動、生存gen9への旧field非継承をCPUで確認します。別のpacking検査は既存shared wireを使い、新4件のGPU成功とは数えません。[契約・受動観測・証跡](portable-coordinate-typed-owner-add-lifetime-reference.md)を参照してください。


## 2026-10-27 ADD所有者graph退場・再出現Metal103

共通CLI `coordinate-typed-owner-add-lifetime` をseal済み登録。旧99保持＋4件、103/native60/拒43。元Prim71/完全5人/武器/成長、同じlogical-owner Slang entryで発動前後のgraph退場・旧field非継承・gen2発動を検証。最終gen9生存時に旧field値0。GPUの最終carrier/actor queryと戦闘履歴を照合、frame別visibilityはCPU witnessのみ。HPダメージ死亡は未検証。詳細 `docs/portable-coordinate-typed-owner-add-lifetime-gpu.md` と対応checkpoint。

M5 GPU4.200283秒、CPU preflight375.653591秒、pipeline61.344455秒（miss）、child71.713265秒/180上限。fresh独立監査482.756267秒、20/20/20/20/20/3各180以内、同じ監査でgolden/certificate。新GPU1/retry0/WindowsGPU0。最終0b727fdc…は5file登録差分、全CLI関数AST/native producer/comparator/tests/GPU保持、関連120/制御517成功（Win1skip）、generation必須hit/Slang0。最終版のfresh native再生成なし。

永続proof `.portable-recovery/proofs/owner-add-lifetime-gpu-20261027` に新raw/claim/全groupログ保持、reader終了後SHA/size/inode保持疎化で670760960byte回収。旧99input/native/記録output SHA保持、旧raw自体は未回収。現在の新103実証と旧capture消失を区別する。file-only Metal cache probe hitはwarm実機証明ではない。

Windows既存チャットへの送信APIは今回成功。07e1d178/coordinate-landing40は固定配布・対応cacheの所在を確認できず、CUDA未実行。次の依頼は所在とsource certificateを明示した固定配布でcache triageから開始し、不足時に長いcompile/本体buildをしない。次はHPダメージによるADD死亡など実戦寿命の未対応分類。現CUDA/ゲームgap/公開consumer/全キャラ未完、UI CPU/全キャラ0/目標未達。

`reference --suite coordinate-typed-owner-hp-death-common --out NEW.json` は、graph終了と区別した実HP死亡3契約のCPU入口です。最終owner世代・死亡時のactive graph・子fieldの寿命を検査します。新3件はGPU未実証で、次の106入力接続対象です。[検証範囲](portable-coordinate-typed-owner-hp-death-reference.md)。Windowsにpinned upstreamがない場合は、検査済み `research/windows-source-packets/typed-owner-add-lifetime-a2cfc763.zip` を固定SHAでunpackできます。compiler-only packageであり、CUDA実行証明ではありません。

上記a2cfc763…のWindows配布検証は完了しています（全3497file/source certificate、unpack/verify成功）。出所付きreceiptは `research/windows-source-packets/windows-receipt-a2cfc763.json`。生成/compile/driver/GPU0、現CUDA cache hit/launch/readbackは未実証です。

## 2026-10-27 HP死亡106とPython依存事前検査

`coordinate-typed-owner-hp-death`106/native63/拒43をseal済み登録。元定義・旧103を保持した実HP死亡3件、M5通常比較とGPU禁止fresh6群監査に成功。最終関連123/制御525（Win1skip）、generation必須hit/Slang0、実pipeline必須hit/追加compile0。詳細docs/portable-coordinate-typed-owner-hp-death-gpu.md。

`validation-deps --out NEW.json`（checkoutでは`--suite coordinate-landing`）で、同梱pinに対する独立MPFR oracleのimport可用性を確認できます。通常runもテストworker/GPUより前に不足を検出します。インストールやGPU認定ではありません。詳細docs/portable-python-validation-dependencies.md。現在sourceのstandalone coordinate-landing40も旧input/native/outputを保持してMetal更新済み、Windowsへ専用小packetを共有。全本体CUDA/全キャラ認定は別の未完了事項です。

`coordinate-landing-cache-only` は保存CUBINを必須にする明示profileです。`--require-cache --compile-cache ABS --cached-cuda-source SAVED_generated.cu --artifact-kind cubin --ptxas-level 1` を要求し、CPUより前の保存source/probeと実行子の再検証を両方行います。NVRTC DLL要求を拒否し、通常の計算比較は維持します。[使用条件と未実証範囲](portable-cached-cuda-landing.md)。


`reference --suite heavyarms-lock-marker-native --out NEW.json` は、元25効果を保持するLock Onの単体boss／生存ADD3体それぞれ3秒／30秒、4件のCPU契約です。名前付き状態の生成・stack・解除と診断照会を検査し、観測なしのfresh正本と全結果・射撃履歴を比較します。専用の対象選択／対象数拡張／元25効果のGPU対応は未完で、`reference_model_gap`を維持します。[契約の範囲](portable-coordinate-resident-arc.md)を参照してください。


`run-gpu-packet.py --stage tests` は、compiler-onlyを含む固定packetの登録CPU test群だけを共通workerで実行する段階です。戦闘adapter/native preflightを要求せず、全群receiptの完全性を親でも確認します。`cpu_tests_verified`と正本比較・compiler・GPU計算を区別します。Windowsは`--backend cuda --timeout 180 --original-workspace ORIGINAL`を指定し、既存のfresh Job／2GiB／開始gateを使います。[compiler compact/cache](portable-compiler-compact-cache.md)を参照してください。


`coordinate-resident-device` は全106と同じsource/ABI/全出力比較器の先頭4入力を使うsealed実機確認です。全106や全キャラ認定を置き換えません。[入力と独立Metal実証の範囲](portable-coordinate-resident-device.md)。Windowsのpackage全byte監査は大きいpayloadを最大4readerで毎回検査します。保存checksum・CPU正本結果のcacheは使いません。[CPU比較診断](portable-package-byte-verification.md)。

選択テスト自体がWindowsの180秒を超えるsealed battleでは、[fresh事前検査](portable-staged-native-preflight.md)の`preflight-plan --test-group-size 2`と全`preflight-test-group`を使う。通常の全テストを省略せず、全receiptをnative開始時とGPU直前に監査する。


`reference --suite physical-lock-cover-native --out NEW.json` は、Lock Onモデルの実ハイド通知5ケースをCPUのみで検査する。GPUの物理入口が遮蔽入力を拒否することも専用testで保持する。CUDA/Metal接続の成功ではない。`physical-generation-locks` のGPU前testにこの5検査を追加し、既存54検査と合わせて実行する。詳細は [Lock Onの実ハイド契約](portable-heavyarms-lock-selection.md)。


`physical-lock-cover` はsealed23入力（native11／拒否12）。既存手動遮蔽producerをLock Onの実充填・snapshotへ合成し、入力/出力幅を増やさずM5 Metal＋fresh監査で一致した。通常のpackage→CPU-only→run→保存結果監査を使う。旧physical10/external16も現sourceで再sealし、旧goldenは保持。spatial selector/sequential/full25/CUDA実機の認定ではない。詳細は [実ハイド合成](portable-heavyarms-lock-selection.md)。


`lock-delivery-policy` はsealed63入力（共通CPU policy46／raw拒否17）。発射前snapshotのhit番号→型付き世代付きslot選択部品だけをCUDA/Metal共通で検査し、M5 Metal＋fresh独立監査で一致。標準package/run/seal経路を使う。CPUテストには実 `on_attack`／`full_charge_fire`／gauge消費順の検査も含める。実着弾キュー・HP・ゲームの再対象化規則・全25効果の認定には使わない。詳細は [snapshot選択部品](portable-heavyarms-lock-selection.md)。


`lock-delivery-cache-only` は同じsealed63入力・同じgoldenを使うcompiler-free CUDA入口。既存cache規約をそのまま再利用し、`--require-cache --compile-cache ABS --cached-cuda-source SAVED_generated.cu --artifact-kind cubin --ptxas-level 1` を必須にする。保存sourceのstrict normalized hashとCUBIN hitをCPU/native前に検査し、実行子でもexact-byte cacheを再検証、NVRTCロードを拒否する。非residentなのでgeneration-cache flagは使わない。現在の実CUDA cache hit/launchは未実証。Windowsへ新規依頼は送っていない。


`lock-packet-bindings` はsealed8入力（native4／拒否4）で、実キューのsnapshot tokenとhit予算をMetal＋fresh監査した入口。`lock-packet-cache-only` は同じsource/input/goldenに既存のCUBIN必須・NVRTC禁止profileを付ける。queue slot2048、入出力幅は不変。宛先slotをHPへ適用する段階は未接続。旧physical10/external16の新goldenはv4/v5。旧cover23のcache miss失敗を保持し、claim前cache gateを修正した新packetで再検証・独立sealしたv2 goldenへ復旧済み。旧失敗claimと旧sealed配布packetは保持。詳細は [キューへのsnapshotリンク](portable-heavyarms-lock-selection.md)。

`live-lock-delivery` は発射snapshotの生存同世代slotを、既存HP/counter/healを持つ実着弾経路へ接続するsealed9入力（明示モデル4／拒否5）。`package --suite live-lock-delivery` → 固定packetの `run --cpu-only` → `run --backend metal` を使う。未知の死亡時振替は拒否し、距離/全25/ゲーム仕様を認定しない。`live-lock-delivery-cache-only` は同じ計算とgoldenに既存のCUBIN必須・保存source・required cache・NVRTC禁止規約を適用する。Windows実機未確認。共有hookの変更後、従来packet8/cover23/physical10/external16を全byte保持で再sealし、通常CLIのgoldenはv2/v3/v5/v6へ更新。詳細は [snapshotから実着弾への接続](portable-heavyarms-lock-selection.md)。

`lock-projectile-composition` は元index24の発射体攻撃と実ロック配送を単一battleへ合成する**開発用**9入力（native5／拒否4）。`package --suite lock-projectile-composition --develop` で固定する。typed領域を全保持し、lock/manual/link領域を1048576以降へ移した既存登録幅1310720を使用。常駐Runtimeの入れ子数値structもCUDA/Metalの厳密reflection比較を通す。初回Metalの全battleとtyped receiptは一致したが、抑止されるnative BODY仮packetの履歴が4ケースで異なり、sealしていない。比較器の履歴行を削除・除外しない。保存失敗rawから配送dispositionの契約を調べる。通常CUDA実行・全25認定へ使わない。

更新：`lock-projectile-composition` は配送dispositionと全履歴を保持するsealed12入力（native7／拒否5）へ進んだ。通常の `package --suite lock-projectile-composition` と固定packetの `run` を使う。GPU実行のrun自体がfresh CPU/native gateを実行するため、別のCPU-only実行を習慣的に重ねる必要はない（失敗の切り分けにはCPU-onlyを使う）。前回の失敗raw/goldenなしの9入力は保存。元全25の認定ではない。`lock-projectile-cache-only` は同じ計算をCUBIN/O1必須にし、`--require-cache --compile-cache ABS --cached-cuda-source SAVED.cu --artifact-kind cubin --ptxas-level 1` と `--require-generation-cache --generation-cache ABS` の両方を要求する。欠落はcapture/worker/claim前に停止。paired生成とCUBINの実hitは実行子でも再検証する。CUDA実機未確認。[履歴と副作用の契約](portable-heavyarms-lock-selection.md)を参照。

### 敵ロックcarrierの共通実行

`enemy-lock-carriers` は元Lock On/解除/名前付き敵被ダメージ増加と、既存2射撃上限を共通actor carrier実行器へ接続する部分suite。7入力（native4、raw拒否3）のMetal独立seal済みgoldenを使う。全25定義、照準距離規則、全キャラ/公開GPU認定は含まない。通常の `package --suite enemy-lock-carriers --out NEW.zip` → `unpack` → 固定packetの `run` を使用する。

Windowsの短いCUBIN検証を準備するときは `enemy-lock-carriers-cache-only` を使う。同じSlang/入力/golden/比較器を参照し、既存compile-cache、保存CUDA source、`--require-cache`、CUBIN/O1を要求する。standalone suiteなのでresident専用のgeneration-cache flagは付けない。未検証のCUBINを存在すると仮定せず、必要な場合は既存compile-planを先に通す。今回のMac作業ではCUDA実行・CUBIN hitは未実証である。`enemy-lock-carriers-diagnostic` は既存admission観測器を有効にする開発専用entryで、通常goldenの代わりに使わない。

### 元のHeavyarms全定義を含む実編成の合成

`original-lock-composition` は元25定義を含む実編成91定義・実武器を、3/30秒×本体/3ADDの8入力（native4、raw拒否4）で実行するsealed suite。通常の `package --suite original-lock-composition --out NEW.zip` → `unpack` → 固定packetの `run` を使う。5専用履歴bankと13種類のnative履歴容量チェックを含み、比較のために射撃/通知行を落とさない。対象順位は明示providerであり、実機の距離規則や全条件分岐・全キャラの認定を含まない。

CUDAの短い検証には `original-lock-composition-cache-only` を使用する。同じSlang/入力/比較器/goldenを参照し、CUBIN/O1のcompile-cache必須hitに加えて、residentのpaired generation-cache必須hitを要求する。artifactがない場合は既存compile-planを先に使い、cache fallbackや未承認の長時間compileを行わない。Macの生成cache hitとCUDAのCUBIN hitは区別し、後者は今回未検証。


`original-lock-controls` はsealed17入力（native9/raw拒否8）。`original-lock-composition` の旧8入力を保持し、実編成の明示ハイド4条件と30秒16ADDの15対象burst飽和を同じ共通実行器へ追加する。通常のpackage/unpack/runを使う。元25定義・実編成91定義・実武器/育成/configを保持するが、操作は元identity検査後の明示overlayと区別する。全25entry呼出しと全条件分岐の認定は分ける。新GPU source/wire/runtime追加0、旧8出力40MiB保持。`original-lock-controls-cache-only` は同じ計算とgoldenにCUBIN/O1のcompile-cache必須とresident paired generation-cache必須を適用する。現CUDA実機は未確認。CPU auditの旧比較golden依存はAUDIT_FILESにも登録し、梱包漏れをnative生成前に拒否する。[範囲・証跡・残件](portable-heavyarms-lock-selection.md)を参照。


## 元武器の発射体・敵シールド補正

未対応の選定では`entry-inventory --suite original-projectile-weapons --out NEW.json`または`--suite original-shield-weapons`を使用できる。実際のtyped compiler/元定義/source行対応/KindAdmissionを用い、選択入口のlowering後に失敗する元stat・targetを分類する。現在254/266変換だが、GPU受付・計算認定はFalse。legacy245/元座標247と混同しない。[使用範囲と次の開発経路](portable-shared-entry-inventory.md)。

敵シールド側の`original-shield-weapons`はsealed15入力（native10/raw拒否5）。元4carrierの全定義と実武器、マリ/ミサトのハイド失効・復帰を共通typed owner/自動照準/物理streamへ接続する。catalogのcarrier追加はCPU unit検査、検査用parsed_skills.jsonの梱包漏れはpackage前の依存検査で検出する。通常package/run/sealを使う。`original-shield-weapons-cache-only`は同じ計算のCUBIN/O1必須＋paired generation必須でcold fallback禁止。Metal独立seal済み、実CUDA/CUBIN hit未検証。[詳細](portable-original-shield-weapons.md)。

元武器の`original-projectile-weapons`はsealed13入力（native8/raw拒否5）。サクラ・アンカー・クレイの元全効果と実武器を既存typed owner/照準/着弾へ接続し、追加damage probeなしで補正の受け手・発動・失効を検査する。最大2,186物理receiptは先頭2,048件と全streamSHAを比較する。通常のpackage/run/seal経路を使用。`original-projectile-weapons-cache-only`は同じ計算のCUBIN/O1必須＋paired generation必須経路で、cold fallbackを許さない。Metal独立seal済み、現CUDA実機とCUBIN hitは未検証。[詳細と認定境界](portable-original-projectile-weapons.md)。

## 固定パッケージのunit検査だけを再確認する

```sh
python scripts/nikke_gpu.py unit-check --capture NEW_UNIT_CAPTURE
```

固定packetをcwdにして実行する。既存cpu_test_groupsを同じbounded子プロセス/GPU禁止/依存ファイル検査で実行し、必要な専用CPU参照テストも保持する。一方、追加の全nativeケース事前照合は行わず、resultはunit_tests_verifiedだけを立て、cpu_verified/calculation_verified/gpu_execution_verifiedはFalseのまま保存する。空の検査群・不正packet・未登録composed wire・既存capture上書きを拒否する。失敗はログとartifactを保持する。登録/監査器のみの変更で数値コードと固定input/native期待が不変と確認できた場合の反復に使い、数値変更のrun/native/sealを代替しない。

`original-lock-health-parts`はsealed11入力（native7/raw拒否4）。実PART2個/破壊、負傷/CPR、元burst回復とHP条件、遅延ADDとの同居を全原定義で検証する。新entryは既存回復diagnosticを有効化するだけで、計算/時計は共有。204行の回復呼出し/配分/clamp/heal_received通知を元source付きで照合する。既存projectionが観測専用HP/adjacent_hp通知をserializeしない範囲は残す。`original-lock-health-parts-cache-only`は同じ計算/goldenのCUBIN/O1必須＋paired generation必須。現CUDA実機は未確認。[範囲と残件](portable-heavyarms-lock-selection.md)。

`reference --suite enemy-ammo-common --out NEW.json` は元ヴェルヴェット全76定義の6つのCPU契約。固定容量の宣言モデルで既存敵攻撃・frame・世代・実被ダメージへ接続し、割合演算は元ハンドラのコード本体を再利用する。武器変更/容量バフ/self-destructは未対応。Metal/CUDA/defaultは未接続。[敵弾薬の設計と境界](portable-enemy-ammo.md)。

`package --suite add-attack-schedule --out NEW.zip`はADD射撃生成部品のsealed19入力（元BossScript8/拒否11）を梱包する。`add-attack-schedule-cache-only`は同じ計算にCUBIN/O1必須・NVRTC禁止を適用し、standaloneなのでresident生成cache指定を使わない。M5/独立監査成功、現CUDA・実戦actor pool・敵弾薬は未接続。[部品と残件](portable-add-attack-schedule.md)。

`package --suite add-attack-battle --out NEW.zip`は本体actor poolから既存incoming実行器へ接続したsealed17入力（元70定義の6編成/拒否11）。M5とfresh独立監査で284発・1,120被弾が一致。`add-attack-battle-cache-only`は同じ計算にCUBIN/O1・NVRTC禁止・paired generation必須を適用する。現CUDA・敵弾薬・defaultは未確認。[実戦接続](portable-add-attack-battle.md)。

## 元ヴェルヴェットの敵弾薬実戦

`enemy-ammo`は元76定義の6戦闘条件＋不正14入力を実M5 Metal/独立GPU禁止監査でsealした20入力。`package --suite enemy-ammo`から固定packetを作る。敵BODY/ADDの固定宣言magazine・残弾・reload・世代・完了通知を既存incoming実行器へ接続し、4,800件のresource通知を全保持する。`enemy-ammo-cache-only`は同じ計算/goldenのCUBIN/O1・必須compile cache/NVRTC禁止・必須paired generation入口。現在のCUDA実機は未確認。敵武器変更/容量バフ/flat/forced reload/default受付/全キャラ認定は含まない。[実装・失敗履歴・実測](portable-enemy-ammo-gpu.md)。

## 弾薬・ゲージの現ソース再認定

`coordinate-original-ammo`4条件と`coordinate-original-resources`3条件を共有数値/通知hook追加後のM5 Metalとfresh独立sealで再認定。通常goldenとfull-compiler証明書をv2へ切り替え、旧版は保持する。全旧input/native/entry/readback byte不変。compactの台帳依存を保持する修正と監査合成/CLI fixtureの修正も同梱する。[再認定と事前失敗の記録](portable-ammo-resource-recertification.md)。他の旧source全体やCUDA実機の再認定ではない。

## ADD実戦の現ソースと自爆CPU契約

`add-attack-battle`17入力を共有numeric/resource hook変更後に再認定し、通常/cache-onlyのgoldenをv2へ更新。全旧input/native/entry/readback byte不変、full-source certificateも同じfresh sealで生成した。`reference --suite add-self-destruct-native --out NEW.json`は最終射撃queueと同frame退場/死亡event/敵数の正本4部品契約（packing/GPU0）。自爆のGPU受付は引き続き閉じる。詳細[ADD実戦](portable-add-attack-battle.md)、[自爆の接続点](portable-add-self-destruct.md)。

## ADD自爆の14入力

`add-self-destruct`は元70/76定義の実編成8条件＋不正6をM5保存出力/fresh独立sealで検証した通常入口。`package --suite add-self-destruct`を使う。`add-self-destruct-cache-only`は同じ計算/goldenにCUBIN/O1・必須compile cache/NVRTC禁止・必須paired generationを適用。初回array/list比較器失敗を保持し、計算を変えず既存replayで全14を再照合した。GPU実行は計1回。敵弾薬との合成/現在CUDA/公開GPU受付は未検証。[実装と証拠の境界](portable-add-self-destruct.md)。
# 保存済み同一byte witnessとCUDA原captureの監査

`partitioned-witness-native-audit` / `partitioned-current-envelope-audit`の範囲・コマンド・証拠の分離は[共通native監査](portable-identical-wire-native-audit.md)を参照。追加GPU実行なしで保存済み全106入力を調べる。片側の成功をCUDA計算認定へ読み替えない。


`enemy-movement`は元ユニ/ヤン全効果の30秒実編成5条件とraw拒否10のsealed15入力。元carrier・世代付きADD・既存clockから動的位置を更新し、既存命中/着弾と全battle履歴までM5 Metal/独立sealで照合する。通常package/unpack/runを使う。計算済み位置・発動時刻はGPU入力にしない。CPU全native生成は約5分かかるため、GPUのみの反復は既存`--native-baseline-package`の適用条件を確認し、run前fresh照合と独立sealを維持する。CUDA実機・ゲーム内軌跡/空間範囲/defaultは未検証。[範囲と実測](portable-enemy-movement.md)。


`enemy-movement-math`はWindowsの短い43入力でCUBIN必須hitまで検証済み。元Metalと全688wordが一致し、保存CUDA数値は専用CPU検査で同じnative/全row比較器へ通す。追加GPU不要。source-host計算/Job成功とMacの独立数値照合、未確認service保全、未実証の全battle CUDAを分ける。[結果・cacheと範囲](portable-enemy-movement.md)。


`moving-typed`は元ユニ/ヤンの30秒実編成6条件＋raw拒否12のsealed18入力。停止/強制移動/重複/再出現/同frame所有者死亡とtyped物理対象を1つのclock/actor pool/pelletへ合成する。元全定義と既存履歴容量を保持し、明示した同世代追従モデルでM5 Metal/fresh独立sealに成功。入力123188/出力2165136wordを通常package/unpack/runから使う。CUDA実機・ゲーム規則/defaultは未確認。[wire/比較範囲/実測と残件](portable-moving-typed.md)。

## 監査済み入力の固定受け渡し

`materialize-headers`は、旧snapshotで実際に不足したheader依存だけを、元receiptと同じSHAの資料へ固定するCPU専用CLI。原snapshot/certificateや計算値は書き換えず、native/compiler/GPUは再実行しない。`handoff-check`/`authority-check --header-materials descriptor.json`で明示的に受け取る。[追補の範囲とSHA境界](portable-prepared-admission.md)を参照。SDK資料はGitHubに含めずローカル保持する。

`authority-check`は元Windows hostの完了済みbounded CPU準備、Job/観測/元予約と外部SHAを認証して新しいディレクトリへauthority.jsonを保存するCPU専用点検。claim/GPU起動は行わない。Macではこの権限作成を拒否する。[認証と一回限りの所有API](portable-prepared-admission.md)を参照。

`handoff-check`は外部snapshot/certificate SHAとbindingから固定入力・出所・CUBINを読むCPU専用点検。元pathを開かず全goldenと照合し、準備controllerと実行consumerを別IDで保持する。実行claimやGPU起動を許可せず、成功もhandoff_bytes_verifiedだけ。[読取と共有adapterの契約](portable-prepared-admission.md)を参照。

`prepare-admission`は元ownerの外部package ID、元transactionと保存link/現producer対を受け、既存の完全なCPU監査から証明書・inventory・snapshotを作る。claimやGPU実行は行わず、成功時もexecution_admitted/calculation false。[引数・検査・未接続境界](portable-prepared-admission.md)を参照。既存run/staged-runの受付を置き換えるものではなく、認証されたclaimとGPU consumerへの接続は未完了。
# model-checkの依存分類を読むときの範囲

`model-check --summary --out NEW.json` の `scoped_dependency_gaps` は、公開frontendの残件と既存のprivate実装を分ける。physical-packet-expansionの残件は公開sampling/RNG受付・未検証の合成・全original定義のcoverageであり、既存sampling実装そのものが無いという意味ではない。private sampling／skill／parentは既存suite名とproof_available／sealed_source_matches_currentを別々に返す。古いgoldenの存在を現sourceの再認定に使わない。mixed-worldの残件も、その未sampling suiteの範囲として読む。

この分類だけで5つのcanonical未対応consumer、公開GPU受付、全キャラ認定は解消しない。20分類検査／51 CLI検査と実CLIの約3KB要約を確認した。詳細は`research/portable-coordinate-gap-scope-classification-v1.json`。

## 数量グループ訪問管理の現source検証

共通bitsetの検証はsealed `quantity-visited`（16入力／境界期待9＋raw拒否7）、実数量は`max-ammo-visited`（28／native20）、共通resident Frameとの合成は`moving-visited`（15／native3）を使用する。全て新しいMetal独立sealであり、旧goldenは保持する。`moving-visited-cache-only`は同じsourceへ必須CUBIN/O1とpaired generationを適用するが、実CUDA成功は未確認。旧profileのsource guardを回避せず、現sourceに対応するvisited suiteを選ぶ。[実証・失敗履歴・数値保持](portable-quantity-visited.md)。

保存PTXの統計とcache照合には、共通packetの`--stage ptx-stats`／`--stage cache-check`を使う。既存監査器を2GiB／BelowNormal／gate付きJobへ通し、独自CPU wrapperの上限設定漏れを防ぐ。[要求JSON・scope・未実証境界](portable-packet-file-diagnostics.md)。


### 元supportの条件付き実戦4ケース

`original-support-conditions` は既存ordered catalogue adapter/sourceで負傷・cover・shieldの4ケースを固定するsealed suite。`original-support-conditions-cache-only` は同一入力/goldenでCUBIN/O1とcompile cache/paired generationの必須hitを要求する。M5実GPU＋fresh独立seal済み、現CUDA実機は未確認。任意条件の反復は引き続き `original-catalogue-ordered` を使う。入力、観測、scope、保存結果は [元support条件](portable-original-support-conditions.md) を参照。


### 元防御型のHP閾値・発動上限4ケース

`original-threshold-conditions` は既存ordered catalogue adapter/sourceにビスケットの元72定義を載せ、対照/1人目/2人目/上限消費後を固定するsealed suite。同じ観測器でattemptと実発動を分け、全戦闘比較を保持する。`original-threshold-conditions-cache-only` は同じ入力/goldenでCUDA CUBIN/O1とcompile cache/paired generation必須hitを要求する。M5実GPU＋独立seal済み、現CUDA実機は未確認。[実証範囲と現CPU規約](portable-original-threshold-conditions.md)。


### 元被弾確率・回復4条件

`original-probability-conditions` は既存ordered catalogue/sourceでエマの元70定義・実64連撃を保持するsealed suite。本人の確率成功/不発、初期負傷、別の味方への被弾を区別し、元source発動数と全戦闘/RNGを比較する。`original-probability-conditions-cache-only` は同じ入力/golden/比較器でCUBIN O1・compile cache/paired generation必須hit。M5実GPU＋独立seal済み、現CUDA実機は未確認。[範囲・保存結果・監査再利用](portable-original-probability-conditions.md)。


### 独立したcover DEF数値部品

`cover-defense-numeric` は元cover倍率と独立base DEFを使う562数値＋10wire拒否のstandalone sealed probe。`cover-defense-numeric-cache-only` は同じ入力/goldenでCUDA CUBIN/O1・必須cache hit。standaloneにgeneration-cache/require-generation-cacheやresidentのfull-source certificateを使わない。M5数値＋独立seal済みだが、元戦闘/cover layer/level curve/default admission/CUDA実機は未対応。[数値規約・公開実測の限界・次の接続](portable-cover-defense-numeric.md)。

### 通常製品リクエストのコンパイル所有者

`product-detail` は通常UI/APIの既存fixtureを、同じ `portable_detail.prepare` /
`compile_product` / `decode_payload` で既存package/run/sealへ渡す再利用可能なadapter。
現cohortはMiranda stage0・30秒・plain bodyの通常entry1件で、group/target entryや
全profileを代表するものではない。元効果・入力・数値を変更しない。

`package --suite product-detail --out NEW.zip` で通常のsealed packetを作り、
packet自身の `compile-plan --artifact-kind cubin --ptxas-level 1 --memory-limit-mb 2048
--timeout 60 --out NEW.json` を通してから既存Windows compile stageを使う。
製品用shaderを旧suite packetに差し替えない。公開固定upstreamも通常packageへ同梱される。

永続native fingerprintだけは、unpack先のGit有無で変わる `evaluator` stampを除く。
実際のCPU/GPU比較はこのmetadataも含む全製品payloadの完全一致で、nullable fieldの
欠落も拒否する。数値・警告・履歴を除外しない。実製品APIの確認件数は別に集計する。
