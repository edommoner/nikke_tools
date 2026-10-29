# 移動中の敵への実グループ効果

## 現在のsourceを独立再認定（2026-10-29）

現在は`moving-group-current`/`moving-group-current-cache-only`と`portable-moving-group-v2-expected.json`を使う。v1の登録pathは元Windows producerの監査のため保持し、古いソースの証拠を現ソースへ読み替えない。後続のwide layout追加を含むclosureは元v1から2ファイル変更/1追加だが、旧15入力のinput/output/全entries/strict normalized CUDA・Metal pairは完全一致した。

固定75fd5e51…のM5 GPU1回が全15入力/native3/拒否12で成功。CPU事前比較69.944秒、GPU2.281339秒、新Swift consumerの冷pipeline60.518秒、generation必須hit/Slang0。旧consumerのcache照合拒否・現在キーの不存在はclaim前の記録として保持し、key/normalizerを緩めない。完了後の新archive file probeはhitだが、実warm GPU loadの計測とは分ける。

同packet自身の別fresh GPU禁止8群監査121.880秒も成功、追加GPU/親native再利用0。raw/旧失敗/claimsを保持。元全定義・実武器/設定・3戦闘のモデルは前述の明示移動モデルのままで、実機規則や全キャラを新たに認定しない。現sealed packet fa991605…自身185検査・前後payload検査・PTX/2GiB/60秒planも成功した。小証跡`research/portable-moving-group-current-metal-v2.json`。

現CUDA計算は未認定。旧76fbe7c3…からのPTX/object/JIT生成成功は旧sourceのまま保存する。次は現packetのexact PTX cache triageと、元producer/native指紋の実行受付。全nativeをWindowsの1つの短いstageへ押し込まず、必要な既存bounded groupを使う。以下は元v1の履歴。

ユニとニヒリスターを元の育成・武器・効果定義で同じ5人編成へ配置する。元ミランダのslotをニヒリスターへ置換した新しい編成として入力identityを記録し、以前の69定義編成と同一とは扱わない。全71定義、seed、30秒を保持する。移動停止は元のburst duration carrier、2敵命中は元`multi_hit:2`→`버닝 샷 3`であり、新しい効果や命中時刻を作らない。

## 元consumerと負例

`reference --suite moving-group-common --out NEW.json`は元のtyped/logical/motion native chainを共有するCPU契約。2ADDの移動、全logical/typed対象を遠方へ置く対照、12秒ごとの再出現の3条件を扱う。typed付属物は前の明示モデル`visible-with-moving-owner-v1`を使い、古い所有者世代を新世代へ読み替えない。

CPU観測では各20group。移動条件は9回の2敵通知・元子攻撃9回・子着弾27回、再出現は17/17/51。範囲外対照は全て0で、typed着弾も0。対象はdistinct logical BODY/ADDのみを数える。各3,602移動frame、現在世代、元の全battle/skill/group/typed比較を保持する。元データ由来のイベント射影を使う故障注入テストでは、通知欠落・対象重複・別名子攻撃・範囲外への架空通知を拒否する。

初回はtyped shapeを照準線から離して正例なのにtyped命中0となり契約が停止した。修正後のpositiveはtyped実命中50/28件を持つ。範囲外には全case非空という誤った監査を適用せず、正例の非空・負例の0をそれぞれ必須とする。元の効果やnative値を削っていない。失敗report、source snapshot、保存nativeは永続 `.portable-recovery/proofs/moving-group-20261029` に保持する。package初版は未追跡test、次は比較用旧goldenの梱包漏れをGPU/claim前に拒否した。必要なsupport fileを宣言した新packetだけを実行し、旧失敗を上書きしない。

## 共通実行と比較

GPU sourceはsealed `moving-typed`の276ファイルと全byte同一。input123188/output2165136wordも同じで、効果handler、clock、sampler、通知、damage、子攻撃の実装を複製していない。比較器は従来の全比較文をAST同一のまま`compare_observed`へ抽出し、両suiteから使う。旧6戦闘の保存native契約は新しい監査でも成立した。これは旧sourceのGPU再認定とは区別する。

固定packet `b6729852…`のM5 Metal実GPU1回で全15入力（native3/拒否12）が一致した。GPU2.281622秒、library0.004941秒、PSO0.003021秒。生成とpipeline cacheを必須にし、両方hit、Slang compiler呼出し0。GPU前のfresh nativeは71.151秒、post-GPU比較はその親の3native/3contextを再利用し、保存nativeを実行時oracleへ注入していない。入力7,391,284byte・出力129,908,160byteを保持する。

別fresh GPU禁止child8群の独立sealは123.327秒で全15入力成功し、親nativeの再利用0・追加GPU0だった。小証跡 `tests/fixtures/moving-group-metal-v1.json` とgolden `research/portable-moving-group-v1-expected.json` を登録した。各保存nativeも新goldenのnative SHAと完全一致する。CPUで元入力を保持したまま移動consumerのfieldsだけを外すと、元通知9→5・子着弾27→15となり、実packetも変わった。故障注入rawも保持する。

通常は `package --suite moving-group --out NEW.zip` を使う。`moving-group-cache-only`は同じ計算・全入力・golden・比較器を、既存CUBIN/O1必須・paired generation必須・NVRTCロード禁止へ接続する。固定76fbe7c3…のCUBIN/O1・2GiB・60秒compile-planは成功したが、コンパイルやCUDA計算証明ではない。キャッシュ不足時にcold fallbackをしない。

固定cache-only packet自身の8群59テスト、開発側CLI51テスト・readiness25テスト・model-checkが成功した。故障注入2テストは新しい独立proofを検査する1テストを加えて3テストになり、保存イベントの改変も拒否する。CLI小証跡は `research/portable-moving-group-cli-v1.json`。この配布確認でnative/GPUを重複実行していない。

この段階で現CUDA、ゲーム上の距離/付属物/recipient規則、3ADD以上の30秒容量、PART/BODY移動、全キャラ、公開admissionを認定しない。Windowsの実行依頼0。
