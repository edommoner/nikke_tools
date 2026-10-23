# 生成器と転送コードのキャッシュ境界

Slang生成器を `app/portable_slang_generation.py` へ切り出した。従来 `portable_backend.py` 全体を生成cacheのkeyへ含めていたため、CUDA/Metalの転送・driver起動・出力処理だけの編集でも、生成cacheを必須にした開発がmissで停止し、Slang2回の明示刷新が必要になっていた。

新しいkeyは生成器モジュール全体、生成cache実装、resident ABI監査器、scope監査器を含む。GPU全source・entry・options・Slang distribution全file・host・暗黙依存拒否・必要なsource rootという従来の境界も維持する。転送コードは生成器が依存しない共通モジュールの外に置き、keyから外した。生成結果の正規化を緩めたり、旧cacheを新keyへコピーしたりはしない。

`source_hashes`、`build`、`_build_resident` の3関数はroot引数を追加しただけで、関数ASTを元へ逆変換して完全一致を検査する。backend側は既存APIからの薄い委譲となる。生成以外のbackend関数・imports・定数を含む全module文も変更していない。実GPU計算source・数値・wire・normalizer・正本・NVRTC cache実装は不変である。

## CPU/Auditの禁止経路

共通CLI `forbid_gpu` は新生成器の公開buildとresident生成も禁止する。required-cache先行確認では、cache読み取りのbuild経路だけを戻し、fresh resident生成・subprocess・native libraryを引き続き禁止する。新モジュールはreplayの保護対象であり、新旧packageの生成器が違う場合や一方にしか存在しない場合は拒否する。双方が旧方式の保存replayでは、存在しなかったmoduleを後付けで要求しない。

cache schema1と旧receiptの監査は保持するが、identityの依存集合が変わるため新keyになる。旧keyだけのcacheを新しい必須cache要求へ流用しない。故障注入では旧receiptを元identityで監査でき、新keyのrequired missからcompilerへ進まないことを確認した。古いcache/claimは削除しない。

## 固定packageでの実証

共通CLIの `generation-boundary` は既存175入力（native132/拒否43）を使う。今回追加のGPU dispatchはない。

```sh
python scripts/nikke_gpu.py package --suite generation-boundary --develop --out /tmp/boundary.zip
python scripts/nikke_gpu.py unpack --archive /tmp/boundary.zip --dest /tmp/boundary
# 以下は展開先をcwdとして実行
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/boundary-cpu
python scripts/nikke_gpu.py generation --develop --out /tmp/boundary-generation \
  --generation-cache /absolute/cache --slang-root /absolute/slang
```

基準package `0a9f5ca104cc82b6c070abeac0f5b9d5edef494381f9088ccc67b76beadd66bd` と、読み戻しchunkだけを8MiB→4MiBにした比較package `d4147d9f35c8c49c17347b52f68a104b43b8bfd8f0721361ef31e1e2f5728d47` を固定した。比較用編集は作成後に元byteへ戻し、4MiBの変更は本体へ採用していない。両packageのGPU source・全175入力・native期待値は同一である。

基準のcold生成はphase区間2.765930秒・Slang2回。転送だけを変えたpackageのrequired hitは0.287245秒・Slang0回で、cache keyも一致した。CUDA/MSLと両reflectionの全4fileは、両package間でも、前回の実Metal175の保存生成物とも全byte一致した。旧keyのpayloadも元receipt/生成物と照合して残存を確認した。単発のMac生成測定であり、Windows実測・NVRTC coldコンパイル・GPU戦闘全体の改善率へ外挿しない。

CPU11群116検査（skip0）と175入力のnative事前照合が成功した。cache境界、生成器/ABI/tool変更のmiss、変更された転送のhit、旧receipt、公開の禁止経路、所有claim、失敗phase、fresh reflection、CLI/replayを含む。最初の固定CPU-onlyは子孫終了確認の `ps` をsandboxが拒否して失敗した。元記録を保持し、終了検査をskipせず、同じpackageを別CPU-only captureで権限を付けて検証した。GPU/Slang/NVRTCを再実行したという意味ではない。

## 残件

この変更は生成前段の不要な再コンパイルを減らすもので、本体CUDAのコンパイル/リンク成立・Windowsでの新しいcache hit・環境保全・全キャラ対応の証明ではない。新ホスト経路でのGPU再実行は0で、前回のMetal175はその元captureの範囲の証拠として保持する。新しい効果・静的入力・通常UIを変更していない。

Windowsの既存チャットから保存済みの調査結果を確認した。System/Applicationイベントは権限不足で取得できず、7プロセス終了原因はunknown、環境保全は未認定のまま。新しいWindowsコマンド・compiler・GPUは依頼していない。

次は未対応の名前付き敵対象などの正本契約と共有lowering、および本体CUDAの保存object/リンク証拠から必要な短い検証を選ぶ。生成cacheの改善だけで実CUDA成立と扱わない。記録は `research/portable-generation-boundary-checkpoint.json` と `research/generation-boundary-evidence/`。
