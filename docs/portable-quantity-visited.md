# 数量グループの共通訪問ビット集合

`quantityTotals`の訪問管理だけを`QuantityVisited`へ置き換えた。定義上限256に対して256個のuintから8個のuintへ移し、ソース上の記憶域は1024→32byteとなる。グループのvalues／flags／初出順orderは従来の配列を使い、フィルター、初出順、binary64の加算・丸め式、通知・時計は変えない。CUDA／Metalが同じSlang型とメソッドを使う。物理stack／PTX localの削減量はまだ測定していない。

initializeは有効グループ数を含むwordだけをゼロにし、insertは初出かどうかを返して対応bitを立てる。呼出側の既存group範囲検査を前提とする。別グループの属性bitを訪問印として流用しない。32bit境界と最大group255も同じ整数演算を使う。従来のcapacity／quantity scan reference分岐もこの訪問管理だけを使い、参考走査の数値式は保持する。

## 実証

| 共通CLI suite | 範囲 | M5 GPU秒 | fresh独立監査秒 |
| --- | --- | ---: | ---: |
| quantity-visited | 9境界ケース＋7 raw拒否、全256group／再初期化／全word | 0.000414 | 0.409858 |
| max-ammo-visited | 従来28入力／native20／拒否8 | 0.051732 | 2.438136 |
| moving-visited | 従来15入力／native3／拒否12 | 2.227792 | 84.360426 |

境界probeも本体と同じ`quantity_visited.slang`を使う。16入力全67584byteを比較し、予約wordや拒否後の残りzeroも省略しない。これは実戦闘9件という意味ではない。最大装弾数はpercent／flat／groupedとseparate rounding／負数／recipient等を既存ケースで比較した。最大装弾数とmovingは旧goldenの全input/output/native指紋を保持し、movingの129908160byte全部のSHAも3765a8c5…と一致した。

全3実証を別fresh GPU禁止プロセスでsealし、それぞれ新goldenを登録した。world2入口には同じfresh監査golden由来のsource-only compiler certificateも登録。`moving-visited-cache-only`は同じ計算・入力・比較器をCUBIN/O1必須／paired generation必須へ接続する。実CUDAのhit／計算認定ではない。

最終コードの関連76検査、最終sealed moving配布fb2c7719…自身の8群42検査が成功。追加の42検査はGPUを起動しない。初版GPU実証後の変更はseal保持検査・suite登録・依存宣言で、GPU sourceを変更せず計算を繰り返していない。

## 履歴と監査境界

最初のpacket dd282090…はSlangのmutating指定不足でGPU起動前に停止。修正版4d98341e…はGPU完了したが、raw拒否7件を通常status0 domainとして登録していたため比較失敗。共通のdomain=None／validate_rejection経路へ修正し、既存status規則を緩めずa6b39ff1…で認定した。拒否domainへの変更はnative指紋が変わるため同一基準replayは使わず、別固定packageとして実行した。失敗4d98の全readbackは認定a6b3と同一であることも確認し、失敗自体は成功に書き換えない。

今回のGPU実行は成功3＋比較失敗1、GPU前Slang失敗1、同claim再送0、Windows依頼0。失敗・raw・claimはすべて保持。max-ammo配布で不足したpinned readiness依存は、宣言済みCPU audit依存の和集合を梱包する修正でCPU/GPU前に解消した。

`quantity-visited-source-change-v1.json`の5hunkを逆変換すると変更前quantity source全体（SHA d04e5689…）へ完全一致する。max-ammoの既存歴史baselineとnormalizerは変更せず、current本文／SHAと新helperの正確なdigestを登録。旧Frameテストは同じ5hunkとhelperの厳密SHAを検査した歴史projectionとして保持し、旧sealを現bitset実装の証明へ昇格しない。現実装は上記の新Metal証跡で認定する。

旧goldenは上書きしない。現sourceでの新規検証には上記visited suiteを使う。他の旧profileが現sourceのguardで停止することを、旧証明書の書換えやnormalizerの除外で回避しない。CPU正本・効果定義・pinned upstreamは不変。CUDA物理資源／旧launch return2の解消／全キャラ／公開GPU受付は未完了。証跡は`research/portable-quantity-visited-metal-v1.json`。次は必要な短いWindows PTX生成・資源比較でquantityTotalsの宣言量を確認する。
