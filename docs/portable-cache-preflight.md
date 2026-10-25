# CPU前処理より前のCUDAキャッシュ確認

Metalのファイル専用事前点検は `metal-cache-probe` を使用します。[使い方と証明範囲](portable-metal-cache-probe.md)を参照してください。保存identityを使うadvisory snapshotであり、現在のdevice／OSやGPU計算の証拠にはしません。実行時のnative cache再検証は必須です。

共通CLIのCUDA battle実行で、`--require-cache` と `--require-generation-cache` の両方を
指定した場合は、単体テスト／正本計算／GPU実行claimより前にキャッシュを確認する。
従来はCPU前処理後、実行子がキャッシュを読むまでmissを検出できなかった。
持続時間の全体検証ではCPU回帰約176秒＋正本事前約93秒だったが、これはMacでの既存測定であり、
今回の変更によるWindows実機の短縮時間を測定したものではない。

先行確認は既存のSlang生成cacheのhitだけを読み、source closureと生成CUDA／Metalの
正規化hashをsealed Metal基準へ照合する。Slang起動・NVRTC／driver DLL読込・GPU呼出は禁止する。
生成cacheがmissなら生成せず停止し、CUDA cacheがmissならclaimも作らずCPU前処理前で停止する。
hitでも従来の単体テストと正本比較を省略しない。実行子も従来どおりcacheを再検査する。
`cache-preflight.json` のhitは時点の診断であり、計算成功や環境保全の証明ではない。

`--require-generation-cache` 単独の場合も、Metal／CUDAの生成cacheをCPU前処理前に確認する。
開発packageには既知の生成goldenがないことがあるため、その場合はsource／paired reflectionを確認し、
生成golden照合済みとは記録しない。sealed packageは従来の生成goldenも一致が必要である。
cache必須指定のない実行、CPU-only、smoke、保存CUBINの経路は変えない。
明示的なcoldコンパイルは、従来の短時間・メモリ制限付き経路を使う。
失敗／古いclaimは自動削除しない。

初期の生成cacheはbackend全体のhashも含み、CUDA側だけの変更でも旧生成cacheがmissした。
この節の初回Metal確認もこの理由でGPU実行前に停止した。現在は生成器を独立させ、転送だけの
変更はkeyから分離している。生成器・ABI/scope監査器のhashは維持する（[現行の境界](portable-generation-boundary.md)）。
その失敗／claimを保持し、Slangコード生成だけを明示的に行って新しいcacheを作成した。
CUDA・Metal・両reflectionの全byteが以前の実証と一致することを確認し、key規則は緩めていない。

## ファイルだけで調べる

`cache-probe` は生成済みCUDA、同じNVRTC／builtins DLL、ヘッダー、コンパイルoptionを使って
cache keyと成果物のhash／長さを検査する。sourceの正規化や旧形式のkey変更は行わない。
壊れた／空の成果物、CUBINとしてELFでない成果物、曖昧なtoolchainは失敗にする。
キャッシュやclaim、toolchainを変更しない。指定した報告ファイルだけを新規作成し、上書きはしない。

```sh
python scripts/nikke_gpu.py cache-probe \
  --generated-cuda /path/to/generated.cu \
  --cuda-root /path/to/CUDA/v11.3 \
  --compile-cache /path/to/cache \
  --artifact-kind cubin --ptxas-level 1 \
  --out /path/to/new-cache-report.json --require-hit
```

`--require-hit` のmissは終了code1、指定なしの正常なmiss診断は終了code0。
破損や不正入力は常に失敗する。reportはcache／toolchainの外へ置く。
相対includeは既存コンパイルと同じcwdで解決し、絶対include先の同じ実ファイルも必要である。
この検査はファイルを読めればMacでも動くが、WindowsのDLL実行やCUDA数値一致を証明しない。

## 開発時の検証

`cache-preflight-regression` は既存の持続時間47入力を再利用し、新しいcache／制御検査も実行する。
GPU計算本体・効果定義・数値primitive・normalizerは変更しない。
CPUテストの合成コンパイラー／成果物は制御の故障注入用であり、実CUDAの性能測定には数えない。
Windowsを追加操作せず、実Metalの短例で非CUDA経路を確認する。
結果・既存出力との比較は `research/portable-cache-preflight-checkpoint.json` に記録する。

最終packageの15群150検査が成功し、MacのCPU-only smokeも30群302検査中301成功・
Windows専用1件skipで完了した。smokeの初回は、古いcompiler-full証明と現行sourceの同一性を
要求する検査で停止した。履歴は保存Metal基準との一致を検査し、現行sourceへは流用できないことを
別の故障注入で検査するよう修正した。旧certificate／goldenは変更していない。

変更したホスト制御でMetal47入力が成功し、入力・native指紋・出力147,849,216 bytesは以前と
完全一致した。テスト追加後のpackageにも共通CLI replayと独立sealで保存結果を適用し、
GPUの追加実行0で再監査した。生成cache先行確認はMacで約0.31秒だった。
Windows実機のcache-probe／新しいJob smoke／CUDA数値・性能は未検証である。
GPU本体の既存1,612入力は従前の証拠を維持し、新ホスト制御で全1,612を再実行したとは扱わない。

旧実装との合成データ比較ではschema1のkey、receipt、cache JSON全byteが一致し、
旧recordを新probeで読めた。これはcache形式の互換性検査で、実NVRTCの計測ではない。
NIKKE共通GPU開発スキルはリポジトリ版とインストール版を同期し、標準validatorで検査した。
