# 戦闘計算の高速化ノウハウ(GPU検証の結論とCPU版の設計)

2026-11-05 時点のまとめ。GPU(Metal/CUDA/WebGPU)対応は利用者の判断で削除したが、そこで得た計測と教訓をここに残す。
数値はすべて Apple M5(10コア: 高性能6+高効率4)、180秒戦闘(10,800フレーム)で実測したもの。詳細な記録は
`.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/` 配下の各フォルダ(本文中に記載)にある。

## 1. 結論

| 方式 | 1部隊あたり(計算のみ) | 備考 |
|---|---|---|
| 元のPython計算(CPU基準) | 約1.5〜1.8秒 | 正しさの基準として残す |
| Metal GPU、8部隊同時 | 約2.3秒 | 製品の初期構成 |
| Metal GPU、1,008部隊同時(最良) | 218ms | `metal-scaling-v1/` |
| **同じSlangをC++にしてCPU 10並列** | **12ms** | `metal-scaling-v1/cpu-parallel.jsonl`。Metalと126/126バイト一致 |
| 同じC++をWebAssembly、Chrome 10ワーカー | 18ms | `wasm-bench-v1/`。126/126一致 |
| 同、Chrome 1ワーカー | 約100ms | ネイティブ単スレッドとほぼ同等 |

**計算プログラム(Slang)はGPU用に書いたものをそのまま `slangc -target cpp` でC++化して使う。** GPU対応で作った
「1ビット単位で一致する計算プログラムと、その照合の仕組み」がCPU版の土台になっている。

## 2. なぜGPUが合わなかったか

- 1部隊を1スレッドで10,800フレーム順に進める構造。フレーム間に依存があり、部隊内で並列化できない。
- 分岐とメモリ参照が多く、1スレッドあたりの常駐状態は約168KB(`Runtime`)。GPUではレジスタやキャッシュに乗らず、
  デバイスメモリ待ちが支配的(メモリ遅延律速)。
- 浮動小数点はすべて整数で再現したbinary64(f64Add/Mul/Div/Less、ulong演算)。GPUの浮動小数点ユニットの利点がない。
- 同時部隊数を増やすと待ち時間は隠れる(8→31→126→504→1008部隊で2.3s→1.6s→0.83s→0.30s→0.218s)。
  しかし製品の探索は数十〜百数十候補ずつ進むので、1,000件単位のまとめは現実的でない。
- 結果を変えない最適化(`kernel-speed-v1/`)は、Metalで約5%(104.2秒→99.4秒)、CPUで7〜13%しか効かなかった。
- 出力が1部隊3MB(資源履歴の大きい部隊では41MB)あり、読み戻しも重い。

## 3. WebGPU(ブラウザGPU)で分かったこと(`webgpu-bench-v1/`)

- Chrome 152(Dawn/Metal3)では timestamp-query は使えるが、64bit整数(int64)が使えない。
- `slangc -target wgsl` は `u64` を出力し、ブラウザに拒否される。
- 32bit×2でのulong模擬(binary64_pair)は、演算核だけならネイティブ並みの速度で動いた。
- 一方、横に広い起動(T=1024)では「Device was lost」で落ちた。製品カーネル全体をWGSL化するコンパイルは10分以上かかった。
- 結論:ブラウザではWebGPUよりWebAssembly(i64をネイティブで扱える)が適している。

## 4. CPUネイティブ版の作り方(`native_detail`)

- 生成:`slangc <entry>.slang -entry portableEvents -target cpp -fp-mode precise -line-directive-mode none`。
  生成には1種類あたり約1.7秒かかるので、ソース一式のハッシュ、slangcの識別、エントリとフラグをキーにキャッシュする
  (`research/portable-build/cpp/<identity>/`)。
- ビルド:`clang++ -O2 -std=c++17 -ffp-contract=off`。**`-O3` や `-mcpu=native` は逆に遅くなった**(126件で17.9→22.6ms)。
  `-ffp-contract=off` は結果の一致に必須。ホストはキャッシュする(`research/portable-build/native/<identity>/`)。
- 実行:まとめた入力から部隊ごとに単体の入力(`[1, 部隊のワード列]`)を作り直し、ゼロ初期化した `Runtime` と出力領域を
  毎回用意して `portableEvents_Thread` を呼ぶ。部隊同士は独立なのでスレッドプールで並列化する。
  単体の入力にする方式が、Metalのまとめ実行の出力と1バイトも違わないことを確認済み。
- 正しさ:GPU/ネイティブ/WASMの出力は、同じ入力に対してすべてバイト一致(269件+59件の標準回帰、6件の拡張、126件の計測)。

## 5. ブラウザ版の作り方(`browser_detail`、WebAssembly)

- 同じ生成C++を `em++ -O2 -std=c++17 -ffp-contract=off --no-entry -sSTANDALONE_WASM -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=33554432`
  でビルドする。Slang 2026.20 の付属ヘッダーにはwasm向けのプラットフォーム判定がない。そのため、`SLANG_PLATFORM` 一式を
  宣言する小さなヘッダーを `-include` し、wasm32にない `_Float16` を無効化する(`scripts/wasm-platform.h`)。
- **Web Workerごとに独立したWASMインスタンス**を持たせる。SharedArrayBufferを使わないので、COOP/COEPヘッダーが不要。
- 転送量は小さい:入力 約3KB、出力 約52KB(いずれもgzip後、1部隊あたり)。
- サーバーは状態を持たない:準備(入力作成)と仕上げ(入力ハッシュと出力長の再確認→結果の復元→照合)を分ける。
  ブラウザの実行時間は「ブラウザ申告」として記録し、検証済みの値としては扱わない。

## 6. 製品全体での時間の内訳と対策

最初の状態では「計算は12msなのに、1部隊あたり2秒以上」かかった。内訳と対策は次のとおり。

| 要因 | 規模 | 対策 |
|---|---|---|
| Python CPU照合(全部隊) | 1部隊1.5〜1.8秒、180秒戦闘では3〜26秒 | 探索だけ「表示する部隊＋1/8の抜き取り」に変更。不一致が出たら全件照合へ自動で切り替え(利用者の判断、2026-11-05) |
| slangcのC++生成をまとめ実行ごとに実行 | 32件あたり6.1秒 | 生成キャッシュ |
| 計算プログラムの種類ごとに順番に実行 | 32件あたり2.4秒 | 種類ごとに同時実行 |
| Pythonの起動 | まとめ実行ごとに約0.9秒 | 32件ずつにまとめて分散させ、複数を同時に実行 |
| Pythonの入力準備・組み立て | 1部隊60〜80ms(deepcopyが多い) | 複数プロセスで並列化(プロファイルを部隊の5人に絞っても速くならなかった) |
| CPU計算への切り替え(カーネル未対応) | 1件3〜26秒 | 別プロセスで並列化し、カーネル側も対応させて0件に |

まとめ実行の同時数と大きさ(実測、160候補、10コア):3並列×32件→135ms、5並列×16件→108ms、
10並列×16件でホストのスレッドを各10(OSに配分を任せる)→101ms。CPU使用率は約70%で、
カーネル自体が1候補あたり約0.5 CPU秒、Pythonが約0.1 CPU秒。

## 7. カーネルのホットスポット(`kernel-profile-v1/report-v1.md`)

- 時間を食うのは、数量・グループの作業領域の初期化と、順序付きキャリアの繰り返し問い合わせ。
- 結果を変えない改善の例(`kernel-speed-v1/`):
  - `quantityTotals` の毎回のクリアを、初出グループのときだけ行うように変更
  - 変化しない定義の読み出しを走査の外に出す
  - キャリア所属をビットセットで昇順に走査する
  - 受動・周期・間隔の定義一覧を初期化時に作る
  - ダメージ係数の同じ割り算を使い回す
- 守るべき制約:浮動小数点演算の順序と丸めを変えない。逆数による掛け算への置換、計算順の組み替え、ハードウェアの
  浮動小数点の使用は禁止。フレームの飛ばしや、フレームをまたいだ値のキャッシュも禁止。

## 8. 落とし穴

- 長時間の計測を作業中のファイル変更と同時に行わない。Pythonは呼び出しごとに新しいプロセスなので、途中の変更がそのまま
  結果に混ざる。
- 出力は1部隊3MB、資源履歴の大きい部隊(ベルベットなど)は41MB。保存はgzipで約60分の1になる。記録を残す方式では、
  探索1回で約1GBになりうる。
- 照合で見つかった既知の差:リリを含む部隊で、共通カーネルとCPU計算に差がある(Metalでも同じ。既存の差で未修正)。
- Python `http.server` はこの環境ではlistenできなかった。簡単な配信にはNodeを使う。

## 9. S11: 準備・ビルド確認のプロセス内メモ化 (2026-11-06)

`portable_detail.evaluate_many` の既存ネイティブ経路を変更。共有ソースの include グラフ、各ファイルの SHA-256、
Slang の識別、clang の版、生成 C++ / ホスト実行ファイルのハッシュ、生成 C++ の counter-snapshot 検査を
プロセス内で再利用する。キーは `(st_dev, st_ino, st_size, st_mtime_ns)`。include グラフは訪問した全ファイルと
シンボリックリンクの参照先を毎回 stat で確認する。ビルド前後・実行後の共有ソース照合は維持し、永続ハッシュ台帳は作らない。
固定バーストの lowering は prepared 全体の deepcopy をやめ、変更する policies/config の辞書だけをコピーする。
CPU 参照閉包 143 ファイルとカーネルは変更しない。

S9 データの先頭 1,024 ネイティブ成功部隊、S1 条件、32 件ずつ、CPU 照合 deferred。各 damage はデータセットと照合。
Mac は 1 プロセス、ホスト 10 スレッド、同一プロセス内で 2 反復。時間は evaluate_many の呼び出しだけを計る。
gx10 は 5 プロセス × 4 スレッド、重複しない分割を同時実行し、起動・片付けも含めた全体 wall を計る。

| 環境 | 変更前 | 変更後 |
| --- | --- | --- |
| Mac / ms/部隊、反復 1・2 | 149.988 / 158.172 | 115.317 / 138.181 |
| gx10 / 1,024 部隊の全体秒 | 47.437 | 43.472 |

Mac の反復差は大きいため両方を残す。別の変更後計測では 135.473 / 135.662 ms/部隊だった。
単体コストの中央値: include walk 12.53→0.78 ms、Slang 識別 77.82→0.006 ms、
counter 検査 12.88→0.008 ms、固定バースト lowering 0.644→0.001 ms。
これらは並列処理中に重なるため、足し算で全体の短縮量を予測しない。

gx10 の変更後 128 部隊で、ホストプロセス時間の合計 17.87 秒中、カーネル部分は 17.59 秒。
残り 1.6% を削るための常駐ホスト化は今回見送った。次の候補は CPU 参照側の静的準備と、
アダプターの readback / digest / 保存処理。測定スクリプトは `research/team-search/bench_native.py`、
全結果・参照閉包一覧・検証記録は `team-search-v1/s11-report.md` (proofs 内)。

S1 の比較は 2,458 matched と既知の 606/836 mismatched のまま。計算部分は 2,460/2,460 同一。
ただし evaluator の Git provenance は compute 外にあるため、compute の変動キーだけを除く厳密比較では
1,237/2,460 同一、残りは provenance だけが異なる。これを黙って除外して「完全一致」としない。
最終の全検査は Python 2,634 / Node 169 成功。Python は既存の pinned gmpy2 を PYTHONPATH で参照し、インストールなし。

## 10. S12: CPU 最大 HP の一般順序付き索引 (2026-11-06)

`reference_health_runtime.install()` は、互換層を適用した元の `effective_max_hp` の AST から、
stat 分岐に現れる文字列を抽出する。現在は HP の 5 stat と `hp_copy`。その stat に属する carrier だけを
`_active` 順に取り出し、既存の `_indexed_max_hp` に渡す。複数 stat のリストを連結すると加算順が変わるので使わない。
carrier の参照だけを `_stat_index` の private object key に保持し、同じ辞書の clear/reset で同時に破棄する。
値、対象、stack、HP、shield 条件は毎回読む。元の loop/prelude の形が変わると install で明示的に失敗する。

元の互換 AST は、無関係な stat にも query_scope.excludes を呼ぶ。組み込み DamageQueryScope の純粋な判定は
AST で確認し、独自 scope/subclass は元の走査に戻して訪問の副作用を維持する。単純な「元のループに呼び出しはない」
という証明では不十分。最小 manager の unbound 呼び出しも元の経路を保つ。

S1 全件は 2,460 fresh、previous_code_payload_equal 2,460 true / 0 false。coverage reuse/spot check はともに 0。
2,458 matched、既知の 606/836 mismatched、回帰 0。gate wall 980.520 秒、gx10 1,936 行 / local 524 行。

gx10 で gate 終了後、1 プロセスずつ before/after を測定。before は `33ec2908` の変更ファイル 1 個だけを
小さな app overlay から読む。CPU 秒 (before→after、倍率):

| S1 ID | CPU 秒 | 倍率 |
| --- | --- | ---: |
| 280 | 40.962350→7.057472 | 5.804× |
| 18 | 6.137176→5.372096 | 1.142× |
| 1396 | 2.240789→2.231102 | 1.004× |
| 17 (릴리) | 1.774331→1.749430 | 1.014× |
| 0 | 3.363425→2.722508 | 1.235× |

各組は payload 同一。各 1 回の対比較であり、小差の統計的な有意性は主張しない。
同じ 280/18/1396 の cProfile 合計 evaluate は 227.913→62.754 秒。元の full-loop fallback は
5,530,805→0 回、_by_stat は 44,775,898→955,582 回、dict.get は 1,119,769,556→169,827,601 回。
_get_value の 4,059,823 回は変わらない。

次の独立した問い合わせ hotspot は evaluate 比 25% 未満 (base_copy.get_value 24.1%、
survival_scaling.get_value 21.1%、get_buffs 16.1%)。25% を超える残りの health 呼び出しは、
HP clamp、edge callback、再入後の 2 回目の同期を含む。数値をキャッシュするには membership だけでなく
HP/stack/reference/shield/query scope/時刻/復活中の状態を含む全入力と全変更箇所の証明が必要なので、
S12 では追加変更を行わなかった。詳しい AST 証明、全 invalidation 行、profile 上位、gate/test 証拠は
proofs の `team-search-v1/s12-report.md` と `s12/` に保存。

最終の全検査は Python 2,640 / Node 169 成功、失敗・skip 0。Python は既存の pinned gmpy2 と
明示した既存 Slang パスをプロセス環境で参照する。コンパイラパスを欠いた診断実行は保存し、環境を修正して
全件を再実行した。テストの assertion や計算コードを環境のために変更していない。

## 11. S13: native CPU だけ hardware binary64 (2026-11-07)

`gpu/binary64.slang` の既定経路は整数 soft-float のまま維持する。native host のビルド時だけ、共有 C++ の
生成 receipt から `PORTABLE_NATIVE_BINARY64=1` を付けた C++ を別のキャッシュ identity で生成する。
Slang の precise と clang の `-O2 -std=c++17 -ffp-contract=off` は維持する。add / mul / div / signed int64
conversion / ordered less / equal を binary64 の bit-cast とハードウェア命令に置換し、演算結果の全 NaN は
`0x7ff8000000000000` に正規化する。signed zero、infinity、gradual underflow、nearest/even は維持する。
§7 の旧 GPU 向け制約に対し、この単位で許可・検証した例外は **native CPU のみ**。WASM は既定の整数経路を使う。

soft / hardware の両経路を同じ Slang から一つの C++ に生成する差分 harness を追加した。Mac と gx10
(aarch64 Linux / clang 18) の両方で、各二項演算 **41,261,564** 回、int64 conversion **61,261,564** 回を
照合して差は 0。20M の一様乱数ビット対と 20M の極端・近接 exponent 対に加え、special、halfway、各指数境界、
int64 の境界近傍を含む。`tests/native_binary64_diff.py --scratch PATH --pairs 20000000` が完全検証、
`test_native_binary64.py` が短い回帰と生成 flags/cache identity の検証。

既定経路の preprocessed token は HEAD と全一致。37 個の C++ entry variant を再生成して byte 一致を確認した。
`portable_wasm.py`、WASM の生成 C++・host/platform・compiler flags は同一。代表 entry を before/after で独立に
WASM 化して 451,078 bytes 全体の一致も確認した。
S1 は S11 native payload と **2,460/2,460** 一致（許可された compute の timing/capture/device と top-level evaluator
のみ除外）。それ以外の compute 差は 0。状態は 2,458 matched と既知の 606/836 のまま。CPU cache hits 2,460、
CPU evaluation/fallback/host failure は 0。S9 の native 成功 **全 11,956 行**も記録 total_damage と完全一致した。

Mac の 128 部隊、HOST_THREADS=1、2 反復で `os.times()` children CPU は変更前 380.70 / 372.03 ms/部隊、
変更後 224.30 / 222.73 ms/部隊。平均 **40.61% 減**。warm cache の 1,024 部隊 throughput は次表。

| 環境 | 変更前 | 変更後 |
| --- | --- | --- |
| Mac / 1 process × 10 threads / ms/部隊、2反復 | 150.047 / 157.844 | 98.514 / 119.911 |
| gx10 / 5 processes × 4 threads / 全体 wall 秒 | 42.947798 | 29.316063 |

最終 warm 計測の平均 wall は Mac 29.06% 減、gx10 31.74% 減。Mac の反復差は両方残す。
Mac の最初の変更後 pass は未生成 variant のビルドを含んだため、warm 計測から除外した。単なる flags 変更ではなく、
soft-float の整数演算をなくした効果。Python の準備・readback・decode は依然残る。

Mac `sample` はプロセス観測権限で拒否、gx10 `perf` は `perf_event_paranoid=4` で拒否された。sudo や設定変更は行わず、
scratch host の entry 外側だけに worker-PC self-sampler を置いた。26 case の出力全体は production host と byte 一致。
15,891 samples の先頭は effectiveMaxHP 33.3%、basicConditions 19.6%、collectStats 10.6%、quantityTotals 9.5%、
stackedValue 9.2%。これは OS profiler が成功した証拠ではなく、signal sampling の補助的な観測。

次の候補は、orderedRows の純粋な kind/stat prefilter を、markEntry と同時に保つ順序付き structural projection にすること。
既存 loop が dynamic predicate より前に無条件 continue する行だけを除外し、残る行の順序、dead/recycled lifetime、
全条件・scalar 呼び出しと加算順を維持する。HP は無関係な kind-0 stat にも現在 scalarValue を呼ぶため、単に HP stat
だけに絞る変更はその副作用監査なしでは不可。値や eligibility のフレーム間キャッシュは提案していない。ここでは未実装。

全文・コマンド・結果・OS 制約: `team-search-v1/s13-report.md` と `s13/`。Python 2,642 run（2,640 pass、旧 GPU fixture の source hash 比較 2 fail、error/skip 0）、Node 169 pass、fail/skip 0。
