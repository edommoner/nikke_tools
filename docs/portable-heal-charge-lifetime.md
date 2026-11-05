# 回復蓄積の保持・戦闘不能・復活と条件付き実編成

`heal-charge-lifetime-retention`398入力（native302/拒否96）と、デルタの全79/81定義の実編成4入力をMetalで実証し、それぞれfresh子で独立監査した。既存正本・protected4ファイル・upstream・software binary64・厳密normalizerは変更していない。通常UIはCPU、全キャラ認定0、ゴール未達。最新checkpointは`research/portable-heal-charge-lifetime-checkpoint.json`。

## 一律のowner破棄を避ける

以前のsweepはcasterがdownなら、liveな共有carrierや復活時保持carrierのpoolまで消していた。一方、終了済みpoolは次のbuild/collect/takeまで掃除されず、その前に復活するとdownを見失う可能性があった。

正本`effect_runtime.RuntimeState.retire`は、戦闘不能時もactiveなrecordを一律に消さない。`knockDown`で受益者を取り外した後、通知で復活する前に共通`retireHealChargeDown`を呼ぶ。消えたcarrierとdown本人の終了済みpoolを確定破棄し、activeな共有・persistent carrierを残す。通常sweepから無条件のcaster-down破棄を除いた。これらはCUDA/Metal共通の同じ関数で、別backendの条件分岐はない。

12のliteral正本契約は終了後down/復活、live selfの消失、persistent self、共有carrier、ownerがdown中の他者への回復、別ownerの対象down、別ownerの終了済みpool、未復活、down中の期限切れを区別する。既存battle/skill trace/RNG全体に加え、最終poolの量・基礎容量・done/ended/activeをfieldから読み、GPUとbit単位で比べる。余分なcapacity/ATK/recipient照会はしない。旧29のnative指紋も保持した。

## 発動する実編成と非発動対照

最初の標準79定義の30秒正本で、pool生成・放出が0だった。条件`has_defender_ally`が成立しない編成であり、効果受付の成功だけでは実機能を検証できない。その失敗を保存し、標準編成3/30秒を非発動対照として残した。

N102を防御型のノアに置き換えた81定義の編成3/30秒を追加した。両編成とも元の全効果・timing・auto burst制御を保持する。元のcatalogとnative登録順/owner/name/stat/typeの全同一性を確認する。防御型入り30秒ではpool生成7回、take2回、正の放出2回を実際に観測した。身体回復は発動前から満HPでも蓄積へ入り、最終poolも一致した。全4入力の戦闘結果・物理shot・量観測・最終poolがMetal/native一致し、独立seal済み。これは当該4入力の証拠で、全キャラ・全操作・全worldを認定しない。

## 512件以降の量と順序

実編成30秒は1,272件のbuild/deposit/takeを生じる。先頭512件の20word生recordをそのまま残し、初めて超過した時だけ全件のSHA-256連鎖を作る。H0は32byteの0、Hn=SHA256(Hn-1 || 20wordのlittle-endian record)。時刻も含める。先頭512件を取り込んだ後も、全760件のsuffixを同じ順に更新する。native側はhashlibを使い、時計・量・順序・version/totalの故障を拒否する。短い履歴では従来のheader/生recordと8wordの0末尾を保持する。

追加8wordは781320..781328の既存空隙で、次のparts bankへ重ならない。Runtime全field/stride138952、入力104400word、出力786432wordを維持した。bankを共有する別診断との排他も維持する。traceのhard cap1,048,576件は明示失敗で、超過を成功へ丸めない。

既存ordered-historyのSHA圧縮器を純粋な共通`sha256Block`へ抽出して再利用した。既存13入力（最大8,192記録）のMetal/独立sealも成功し、旧全input/native/raw指紋が同一。旧goldenを保持し、現行registryは`portable-ordered-history-shared-sha-short-expected.json`へ結んだ。非resident probeへgeneration cacheを指定した事前生成はGPU0で拒否された。既存の通常run経路で一度だけ検証し、resident限定やcache keyを緩めていない。

## 保持回帰と時間

398入力のCPU36群248検査85.079秒、native事前28.240秒、GPU4.560913秒。実編成4入力のCPU26検査3.865秒、native事前33.953秒、GPU3.434346秒。したがって現在の主要な時間はCPU検査・正本計算・独立監査である。実runは両方generation cache必須hit/追加Slang0。398のMetal library/pipeline作成は既存cache再利用で約0.002/0.003秒だった。これはMetalの実測で、CUDAのcache速度の証明ではない。

旧386全input/native指紋と入力161193600Bを保持した。385入力はraw1211105280Bが全byte一致。残るdown単独1入力は、旧rawにだけ残っていたpool量1000の高word(109249)とkind10 flag(109270)を0にした2wordだけが変わった。正本は既にrecordを破棄していた。元rawを改変して一致させず、正確な差分を`preservation386.json`へ記録した。

新規rawを含む完了済みrawのゼロ領域だけを回収し、全byte/SHA/path/inodeと原失敗・claimを保持した。削除0。静的inventoryは242/266/base182/203/残30分類、全266profile・旧242input SHAが同じ。

## 通常CLIとCUDA用固定packet

`heal-charge-lifetime`12、`heal-charge-lifetime-retention`398、`heal-charge-rosters`4は明示sealにより通常packageを作れる。単独12のgoldenは独立seal398の末尾12の全input/native/raw一致による射影で、別のGPU再実行はない。

```sh
python scripts/nikke_gpu.py package --suite heal-charge-lifetime --out /tmp/new-lifetime.zip
python scripts/nikke_gpu.py unpack --archive /tmp/new-lifetime.zip --dest /tmp/new-lifetime
# 展開先をcwdにする。CPUのみの確認:
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-lifetime-cpu
```

最終通常packet29ac1ed5...は5群31検査とnative12が成功。共通CLI compiler-certificateで保存Metal398を再監査し、`compiler-full--heal-charge-lifetime-retention`の143sourceを固定した。compiler packet771f4aa1.../2582filesはCPU32群323中322成功・Windows専用1skip。生成cache必須hit/Slang0/GPU0で、CUDA/MSL/両reflection全byteを実証済み保存物と一致確認した。旧compiler証明書やraw CUDA/prelude/toolchain/claim/Job/CUBIN identityは保持し、cache互換を偽装しない。

Windows追加操作0。CUDA compilerの資源・cache速度・実数値一致は未確認で、source-only証明書を実機成功と数えない。7プロセス終了は原因unknown/環境保全falseのまま。

残りは1024 object/1,048,576 historyの容量境界、広いlazy/回復分配/親callback混在、未対応30分類と全カタログ、現在のCUDA実機検証。証拠は`research/heal-charge-lifetime-evidence/`。raw・個人設定・compiler本体はGitHubへ含めない。

次の優先未対応候補はdamage accumulationのdealt/received/rate/accum_split_damage。既存app/damage_accum_runtime.pyの登録とpinned buff_manager/timelineの実consumerがある。まず所有者・名前archive・防御適用後の量・放出の正本契約を作る。今回これらのGPU受付や新規契約は追加しておらず、回復poolの規則をそのまま転用しない。
