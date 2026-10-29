# 監査済み入力の受け渡し：次の実装要件

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
