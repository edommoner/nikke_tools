# 最大127体の移動履歴を共通GPU実行器へ接続

従来の移動履歴4096行では、30秒の3ADD以上を保持できなかった。新しい`moving-many`は同じ128 actor slot（BODY＋ADD127）、同じ静的入力123188word、同じ移動/typed/group executorを使い、frame/segment観測bankだけを各262144行へ拡張する。別の時計、効果handler、damage式、scalar、sampler、recipient規則は作らない。

## 最大slotの完全な入力

元ユニ＋ニヒリスターの全71定義・元武器/育成・5人編成・seed・30秒を保持する。既存宣言waveのcountを127へ変更する。127体全てがlive actor、独立したlogical collider、元移動停止carrierのrecipientを持つ。2体を射線付近、残り125体を遠方へ置き、元グループ通知/子攻撃を残しつつ、最大数を「同時127体命中」と取り違えない。typed shapeは同世代の宣言所有者を追う前回と同じモデル。

CPU確認は全228727frame（127×1801）を記録し、全127世代handle・30秒終端・全127体への元duration carrierを検査した。観測73.590秒、保存/契約検査まで76.577秒、ピークRSS529596416byte。native原本は永続proof rootの`native-v1.json`に保持し、容量に合わせてduration/countや観測行を減らしていない。

## 共通レイアウトと比較

出力10422672word。従来typed/coordinate/skill/packet bankと128slotの最終移動状態は同じ場所に残し、その後へ262144×16wordのframe bank、同量のsegment bank、512wordの最後のtyped aim中心を置く。1入力41690688byte。Python/Slang/Swiftの完全strideを登録し、途中幅、従来の小さい幅、128ADD超過は拒否する。

既存`shader_schema`/`compare_movement`のcapacity引数を使い、旧4096の既定出力は全byte同一。履歴超過時は拒否し、先頭や末尾だけの比較へ変更しない。共通typed比較器は同じ全battle/skill/group/typed観測へ続き、比較済みの拡張bankだけを既存viewでzeroにする。旧entryは小レイアウトのまま残し、新entryは同じ本体includeへ明示flagを渡すだけ。

共有7ファイルはexact hunk inverseで旧sourceへ戻し、厳密normalizerや旧goldenを変更しない。新規2Slang sourceも全SHAを検査する。wire/guard/arena/旧source投影など55テストとmodel-checkが成功。これは計算証明ではなく、Metal実行・独立監査の記録を別に示す。

## M5実行とfresh独立監査

固定packet `b44a5f39…`で全13入力（元127体のnative1＋拒否12）が一致。GPU実行1回・再実行0。GPU42.869923秒、MSL library2.098430秒、初回PSO61.194543秒。paired generationは必須hit・Slang compiler0で、初回のpipeline archiveを新たに保存した。GPU前のfresh CPUは112.842秒、post-GPU比較は同じ親のnative/contextだけを再利用した。

別のGPU禁止child7群の独立sealは160.209秒で全13入力成功、親再利用0・追加GPU0。最大nativeを含む最初の群も123.474秒で180秒以内だった。全228727frame、228854区間、127slotの最終状態、全移動paddingを全word比較し、最後のtyped aim中心と既存の全battle/skill/group/typed比較を保持した。元の実通知9回・子着弾27回・typed着弾50件も残る。入力6405780byte・readback541978944byteは永続保存する。

小証跡 `tests/fixtures/moving-many-metal-v1.json`、golden `research/portable-moving-many-v1-expected.json`。元保存nativeのSHAも固定goldenへ完全一致。旧小entryの生成CUDA/Metalは既存のstrict normalized hashと一致したが、旧source closureやcurrent-source GPUの再認定とは呼ばない。保護CPU4ファイルとstrict normalizerは変更しない。

通常は `package --suite moving-many --out NEW.zip`。`moving-many-cache-only`は同じ計算・入力・golden・比較器に既存CUBIN/O1・paired generation必須・NVRTCロード禁止を適用する。固定e5c5ce5b…の2GiB/60秒compile-planは成功したが、現CUDAの実CUBIN hitや計算成功ではない。初回の新しいcodegen generationは上記実行の前にCPU-onlyで作成・検査し、required missを実行中にcold fallbackさせていない。

固定cache-only packet自身の7群55テスト、開発側CLI/readiness/model-gapの90テストとmodel-checkが成功した。実行packetからの差は分類/CLI/テスト/その証跡のみで、全GPU・入力factory・native observer・wire・比較器の既存payloadは完全一致。小記録は `research/portable-moving-many-cli-v1.json`。この登録確認でGPU/nativeを重複実行していない。

ローカル証跡は `.portable-recovery/proofs/moving-many-20261029`。この拡張からゲーム上の軌跡/距離/付属物、BODY/PART移動、同時127体命中、他キャラの全条件、公開admission、全キャラ認定を主張しない。Windows新依頼0。
