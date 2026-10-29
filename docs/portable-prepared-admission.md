# 監査済み入力の受け渡し：次の実装要件

## 旧snapshotの不足headerを原本不変で閉じる

実Windowsの初版CPU準備は元auditorを全て通ったが、そのauditorはstored compiler identityのheader hashを比較し、実header原文はGPU providerのread_verifiedまで読まなかった。結果、read setからheaderが落ち、厳密readerはfrozen source absentで停止した。元準備の成功を取り消して書換えたり、そのまま実行を許可せず、完全handoff未成立の原失敗を別に保持する。

`materialize-headers --snapshot BASE --binding BINDING.json --expected-sha256 BASE_SHA --certificate-sha256 CERT_SHA --out NEW_DIR`は、元の全sealed source/transaction/入力/CUBINを検査する読取経路を使い、missing headerだけを現在SDKから読んで既存receiptの期待SHAへ一致させる。必要なら`--sources JSON`で元originから同じSHAのlocal fileへの明示mappingを指定する。期待外headerや違う内容は拒否。元native/監査計算の再実行・新compiler・GPU・claimは行わない。

header原文はheader-materials.zipへ、基底snapshot/certificate SHA・binding・正確なheader名/bytes/SHAはmaterials.jsonへ固定する。descriptor.jsonはarchive SHAとmetadata blob SHAを持ち、通常readerが再度全handoffを点検してからresultを作る。元archive/cert/read-set digestは不変。handoff-check/authority-checkに`--header-materials descriptor.json`を追加でき、missing依存だけを追補から読む。authority/claim/childは追補SHAも束縛し、改変を拒否する。SDK資料はローカル証拠だけとしGitHubへ配布しない。今後の新prepareは元read_verifiedをCPU read set内で実行して依存を最初から収録する。

新しい内部childはclaim mirror・run/host/source・live Jobを検査し既存shared execute/file readback/CUDA trace verifierへ接続した。公開runnerと独立post監査はまだ無く、実CUDA計算は未実行。固定49d90bfb…の119関連検査と共通719制御検査はCPU fixtureであり、実GPUや60秒予算の実証ではない。旧失敗のsanitized記録はresearch/portable-prepared-authority-peer-v1.json。SDK path/nonceを含む別診断のGitHub公開拒否は維持し、今回のsource配布に含めない。

## 元準備の認証と一度だけの実行所有

`authority-check --preparation-package ORIGINAL_PREPARATION_PACKET --preparation-stage COMPLETED_STAGE --binding SIX_FIELD_BINDING.json --expected-sha256 EXTERNAL_SNAPSHOT_SHA --certificate-sha256 EXTERNAL_CERT_SHA --out NEW_DIR`は、元Windows hostで成功した制限付きCPU準備を認証し、authority.jsonを新規保存する。CLIはclaimを作らず、GPUを起動しない。Macではauthority作成を拒否し、handoff-checkによるbytes点検だけが可能。JSONにauthority_verified=trueを記すだけでは実行所有を取得できない。

元準備controllerの外部IDと全sourceを検査してから、そのwrapper recipeを再構成する。元command/base Python、子PID/親PID、packet_shared_cliの完了journalを既存job_containedへ渡して2GiB・gate・同一作成identity・終了空・時刻範囲を検査。既存compare_snapshotsで欠落0、終了直後30秒内のafter観測、stage専用claim、terminal result、証明書/外部SHAと完全handoffを照合する。準備とconsumerと元ownerは同じsuite/全goldenを要求し、元transaction/現在host/予約claim/未来capture未作成を照合。観測・証拠metadataは検査前後のhashも一致させ、サービス未知の保全falseを維持する。

ライブラリのclaim APIは、その同じ認証呼出しが返す一回限りのメモリ上handleだけを受け付ける。claim直前に証拠・consumer全source・snapshot SHA・hostを再検査し、元transactionのgpu-execution-claimed.json、consumerのgpu-claimed-cuda.json、authority出力のclaim.jsonを新規作成する。元予約claimは変更しない。新protocol snapshot-prepared-v1と元owner/準備/consumer/nonce/capture/SHAを別々に束縛し、legacyの最小claimへ黙って置換しない。書込み途中で失敗しても既存claimを残し、同じhandleの再利用・削除・自動再試行をしない。現在CLIにclaim実行入口やGPU runnerは公開していない。

固定80c928f3…自身でauthority13を含む関連105検査と既存69群719制御検査（Windows限定1skip）が成功、payload/全golden/455計算record/元CLI main以外の全関数AST保持。テストは一時fixture内で論理Windows分岐をlocal proxyに通し、実JobやGPUとして認定しない。実CLIはMacでのauthority作成をexit1、出力/claim無しで拒否した。小記録research/portable-admission-authority-cli-v1.json。実Windowsでは準備自体が未実行で、本番authority/claim/GPU0。GPU子protocolと完全な独立post監査は未接続であり、60秒子予算の実証ではない。

## 固定snapshotの読み取りと共通実行器用adapter

`handoff-check --snapshot FILE --expected-sha256 EXTERNAL_ARCHIVE_SHA --certificate-sha256 EXTERNAL_CERT_SHA --binding SIX_FIELD_BINDING.json --out NEW.json`を共通CLIへ追加した。sealed consumer自身を完全検査し、全golden/suiteと外部bindingをreaderへ渡す。成功時もhandoff_bytes_verifiedのみでexecution_admitted/calculation_verifiedはfalse、GPU起動はしない。準備controllerと実行consumerのpackage IDは別字段として保持する。SHA/bindingは今後の認証された準備/実行claimから取得すべき値で、任意の自己申告を実行許可へ変換しない。

`portable_admission_handoff.Handoff`はsnapshot全体の外部SHAと証明書blob、完全read-set digest、owner/controllerのpackage IDと全source record、元transaction/nonce/host/input、全golden、実入力framing/全row hash、CUDA原文と全header、既存static CUBIN parserを照合する。元Windows pathはopaque originとして扱い、Macで元ファイルやSDKを開かない。metadata/receipt viewはコピー。使用後のarchive再hashとsingle-use readerを保持する。

saved_providerは既存portable_backend.executeが使うcompile_cuda_source callbackだけへ接続する。実際の生成CUDA全bytesとsnapshot原文が一致する場合にだけ保存CUBINを1回返し、live compilerを拒否する。入力、時計、効果、数値、Slang生成、CUDA/Metal transportは複製しない。callback失敗を捕捉しても成功へ変えず、二度目の要求・無供給・既存の異なるCUBINを拒否し、例外時にも元callbackへ戻す。reader/adapter自身は実行claimもGPU dispatchも作らない。実GPU子protocol・認証claim・完全独立post監査への接続は未完了。

固定dde31e0c…自身でreader16を含む関連92検査、既存69群719制御検査（Windows限定1skip）が成功しpayload保持。元ファイル削除後の読み取り、Windows originのMac消費、改変/omission/nonce/typed scope/異なるCUDA/header/CUBIN、共有execute本体とCPU transport doubleによる入力/CUBIN配送を検査した。doubleの合成evidenceをGPU証明として出力しない。固定CLI実負例は、証明書を持たない既存storage-only archiveをexit1/成功出力無しで拒否。元CLI main以外全関数、全golden、455計算関連record保持。`research/portable-admission-handoff-cli-v1.json`。Windows追加依頼/GPU0。実Windowsの準備snapshotもまだ無く、この検査時間を60秒GPU子の実証にはしない。

## 共通Windows bounded stage

`run-gpu-packet.py --stage prepare-admission --backend cuda --timeout 180 --original-workspace ORIGINAL --capture NEW_STAGE --request REQUEST.json`へ接続した。requestはowner_package/expected_owner_id/transaction/linked_package/linked_capture/producer_package/producer_captureの正確な7キー（ID以外はabsolute path）。既存のfresh Job、BelowNormal、2GiB、開始gate、終了直後の観測、stage専用の新規claimを使い、元のGPU execution claimを作らない。親の準備はmanifest headerのみで、完全な過去証拠の監査とsnapshot作成はgate後のCPU子・180秒以内に入る。

親は小さな証明書のSHAとowner/controller/transaction/nonce/input/artifact、完全native preflight、linked receipt、snapshotの保存先/sizeと整合検査記録を照合する。偽のsuccess flag、GPU/compiler/native/driver呼出し、execution_admitted/calculation trueを準備成功として受け付けない。stageが成功しても環境保全や計算成功とは別。snapshotの全bytesはCPU子が既存freezeで検査し、GPU consumer側にも外部SHAからの全bytes検査が必要で、まだ未接続。

固定cad4086f…自身で関連76検査＋全69群719制御検査（MacではWindows限定1skip）が成功しpayload保持。前版6cc80648…の実bounded負例も、元ownerの認証後に未存在transactionでexit1、0.739秒、timeout/cleanup error無しで止まりclaimとfailureを保持。これはWindows Job成功や元証拠による全準備成功ではない。小記録`research/portable-admission-prepared-stage-v1.json`、配布はsource packetだけでsnapshot/rawは含まない。

固定バイトの保存/検査部分はCPU専用CLIへ実装済み。完全な監査からsnapshotを作るCPU準備CLIを追加。所有claim・GPU実行への接続は未実装であり、現CUDAの計算証明や受付経路ではない。

## 実装したストレージとCLI

```sh
python scripts/nikke_gpu.py admission-snapshot --inventory /new/file-inventory.json --out /new/snapshot.zip
python scripts/nikke_gpu.py admission-snapshot-check --snapshot /new/snapshot.zip --expected-sha256 EXTERNAL_SHA256
```

inventoryはschema=`prepared-admission-file-inventory-v1`、binding、filesの正確な3キー。bindingはowner_package_id/controller_package_id/transaction_nonce/input_sha256/artifact_sha256/future_captureを持つ。filesは絶対rootと安全な相対path、bytes、sha256の一覧。これは宣言の形式とbytesを検査するもので、元の意味監査やownerの認証を代替しない。

全sourceを重複分も含めて読み直し、size/SHAを確認してからcontent address別のblobへ圧縮する。重複した内容の保存だけを共有し、sourceの検査を飛ばさない。manifestは正規JSON、全ZIP memberは完全な許可一覧。元rootは識別情報として保持し、受信側はそこを開かず、Windows由来のrootもMacで扱える。extractallや任意pathへの展開は行わない。

受信側はZIP内の自己申告ではなく外部で固定したarchive SHAを必須とし、全圧縮bytesを検査する。選択したpayloadは展開後もsize/SHAを確認し、readerを閉じる時にarchive全体を再検査する。manifestの閲覧は内部状態を変えないコピーを返す。source/ancestorのsymlink、重複source/ZIP member、不正path、size超過、binding違い、使用中の改変を拒否する。失敗したpartial snapshotは保持し、既存ファイルを上書きしない。

最終固定633dcbb5…自身で専用9検査と既存69群719制御検査が成功。実際の2固定パッケージ、7,391,284byteの準備済み入力、9,907,856byteのMetal pipeline archiveを使うCLI往復も全bytes一致。7,997 sourceを4,000 blob/18,586,316byteへまとめた。M5で作成CLI2.482秒・検査CLI0.209秒・検査＋入力/artifact read0.083秒だが、これはストレージ部分だけの測定であり、WindowsのGPU起動予算や完全なadmissionの時間ではない。実行bindingはこの試験用の合成値で、GPU claimは作らない。

両CLIは常にadmission_verified=false/calculation_verified=false/gpu_calls=0を返す。source/receipt inventory生成は下記prepare-admissionへ接続した。実Windowsの全証拠での準備検証、snapshotの認証と一度だけの実行所有、GPU consumer、独立post監査への接続が次の工程。archive/rawはローカルproofに保持し、小記録だけ`research/portable-admission-snapshot-cli-v1.json`へ保存する。

## 完全な監査からsnapshotを作るCLI

```sh
python scripts/nikke_gpu.py prepare-admission \
  --owner-package /immutable/original-owner --expected-owner-id EXTERNAL_OWNER_ID \
  --transaction /completed/cpu-transaction \
  --linked-package /immutable/link-owner --linked-capture /saved/link-proof \
  --producer-package /immutable/current-producer --producer-capture /saved/compile-proof \
  --out /new/preparation
```

呼出元も同suite/全goldenのsealed packetで実行する。元ownerの外部package ID、自己ID、全sourceを検査してから元CLIを読み込み、既存staged admitとsaved_linked_admissionをそのまま呼ぶ。既にimportされた監査helperが元ownerと違う場合は拒否する。全監査はGPU禁止内で行い、native battleやcompilerを追加実行しない。元の未消費GPU試行に対するCPU準備で、execution claimを作らずfuture captureも作らない。前後に両方の未作成を検査し、旧失敗やclaimを消さない。

input receipt、実CUBIN bytes/size/SHA、全golden、owner/controller、nonce/future capture、元staged/linkの完全なreceiptを証明書へ束縛する。監査で読んだ各packageの全files記録を必須とし、read-setの正規JSON digestを証明書へ保存。`evidence/certificate.json`を加えたinventoryから既存freezeで全sourceを再検査し、`snapshot.zip`と`result.json`を新規作成する。inventoryや証明書は自己参照hashを持たない。失敗はfailure.jsonと途中成果物を保持し、同じoutを再利用できない。

これはCPU準備の接続であり、`preparation_verified=true`でも`execution_admitted=false/calculation_verified=false`。snapshot SHAの認証、append-only実行所有claim、共通GPU consumer、完全な独立post監査は別途必要。合成fixtureの故障注入テストを実Windowsの意味監査成功へ読み替えない。

## 完全な監査で読んだファイルの記録

`portable_admission_readset.ReadSet`を追加した。元の監査を呼ぶ間だけPath.read_bytes/read_textと既存streaming file_digestを記録し、bytes/size/SHAだけを保持する。監査の戻り値・native値・contextはcacheしない。同じsourceの再読は毎回実行し、途中の改変を拒否する。並列digestの記録はlockを使い、重複capture・同じcapture instanceの再利用を拒否し、例外時も元readerへ戻す。read_textは元signature/encoding/errors/newline動作を保持する。

`require_package(root, manifest)`は認証済みmanifestの全filesが記録済みか照合する。これは汎用filesystem tracerではない。任意openやsubprocess内部のreadを観測したとは扱わず、元監査の親側全file検査からpackage closureが揃うことを別途要求する。rowsを既存snapshot inventoryへ渡すと、snapshot作成時にも全source bytesを再検査する。単なるtraceやファイル一致では意味監査の成功を認めない。

専用8件＋既存snapshot9件の17検査が成功。固定owner1e54383d…の実verify_packageとcheck_recordsを呼び、元3,995ファイル全件＋manifestの3,996記録が揃うことを検査した。Macのこのファイル点検は約0.568秒だが、Windowsのstaged/link admission所要時間ではない。小記録は`research/portable-admission-readset-check-v1.json`。完全なstaged/link監査から証明書を発行する処理は上記CLIへ接続した。実Windows検証、認証されたsnapshot、所有claim、GPU consumerへの接続は未完了。

## 接続段階に残る要件

Windows固定1e54383d…で、実戦3/拒否12の全群完了後に既存APIをそのままCPU計測した。staged admit34.451秒、保存link admit67.181秒、入力read/hash0.012秒、合計101.644秒。後者単独でもGPU子の60秒上限を超える。外側の180秒は守れたが、この経路でGPUを起動すると準備だけで子予算を消費する。GPU execution claimを消費せず停止した。

次は監査を省略するcacheではなく、CPU準備・GPU実行・独立監査を明示的に分離する。

1. CPU準備段階は元の全staged/link/PTX/object/compiler/Job/source/golden監査を実行し、渡すartifact・入力・出所・証拠の完全なbytes/SHAを固定する。native計算値/contextを保存・再利用せず、既存の指紋と証拠を使う。
2. GPU段階は準備済み証拠と実行所有claimを束縛した新しい明示protocolだけで受け取り、渡された入力・CUBIN・生成CUDA/source・証拠snapshotの全byte整合性を検査してから既存の共通GPU実行器を呼ぶ。mutableな元pathや単なるsuccess flagだけを信用しない。古いrun/staged-runのガードは保持する。
3. 準備側/実行側のpackage ID、元計算owner、transaction nonce、未来のcapture、完全なgolden/input、旧/現producerとreceipt keyを別々に束縛する。同じ未実行GPU試行のappend-only所有を維持し、claimの消去・再試行をしない。
4. GPU子60秒、各stage180秒、Job2GiB/低優先度/gate/終了後即時観測を維持する。時間短縮は実測で確認し、上限の変更で解決しない。
5. 実行後の完全な出所・artifact・入力/出力・共有native比較を独立CPU段階で行い、完了前はcalculation_verified=falseのままにする。保存監査済みwitnessを使う場合も全input/output/native/source一致と元のscopeが必要で、既存106入力用joinの固定pinを緩めない。

実装前/実装後に、入力/CUBIN/source/proof/claim/nonce/ownerの改変、未完了準備、異なるgolden、同一試行の再実行を拒否する検査を用意する。計算・効果定義・数値演算・strict normalizerを複製/変更せず、transport glueを既存実行器へ接続する。元の失敗/claims/rawを保持する。

今回のsource-host CPU計測は`research/portable-admission-budget-peer-v1.json`。Macは小要約とmanifestの元bytes/SHA、期待input/receipt、bounded sourceを照合した範囲で、Windows原rawや診断script全体のMac独立監査ではない。Windowsはidle、GPU未実行。
