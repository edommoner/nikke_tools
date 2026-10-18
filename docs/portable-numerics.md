# CUDA／Metal共通コアの数値規約

## 2026-10-19のMac実測と採用範囲

MacBook Air / Apple M5（GPU 10コア）/ 24GB / macOS 26.6.2 arm64、Python 3.12.15、Node 24.22.0、Slang 2026.20、Swift 6.3.3で確認しました。CPUカタログは203体、従来のMetal実証は4/4ケース成功です。WindowsやNVIDIA GPUは使用していません。

`gpu/binary64.slang` は、binary64のbit列を `uint64_t` に格納し、整数演算だけで四則演算と比較を実行する候補です。加減乗除は各演算で最近接・偶数丸めを行い、非正規数、符号付きゼロ、無限大を扱います。NaNは共通のquiet NaNへ正規化し、payloadは保存しません。大小比較・等値比較ではNaNはfalse、±0は等値です。

`gpu/numeric_probe.slang` はこの共通実装を呼ぶだけで、CUDA／Metalごとの数式はありません。`scripts/verify-portable-numeric.py` が入力・期待値・梱包・比較を共有します。Swiftは起動・転送・読み戻しだけです。Metalのコンパイルは `mathMode = .safe` とし、数値本体は浮動小数点演算を使いません。

手書き12ケース、境界値の組合せ1,734ケース、固定シードのbit列6,144ケース、近い指数の値6,144ケース、計14,034ケースをApple M5のGPUで実行し、全bitが一致しました。有限の四則演算の期待値は入力binary64を正確な有理数へ変換して計算し、最後に一度binary64へ丸めます。比較は入力binary64の順序を使います。CPUの戦闘トレースや発射時刻を入力へ流用していません。手書きの期待bit列は `tests/fixtures/portable-numeric.json` に一度だけ保持します。

この検証は全入力に対する証明ではありません。記録は `research/portable-numeric-metal.json`。CUDAはソース生成までで、NVRTCコンパイル・NVIDIA実行は未確認です。通常の詳細計算には未接続で、性能採用も未決定です。記録されたGPU時間は小さな独立演算群の一回のコマンド時間であり、本体の速度予測に使いません。

## 現行本体から分ける数量

| 数量 | 現行コードの例 | 共通コアへの方針 |
| --- | --- | --- |
| ID・種類・世代・順序・数・乱数 | `TargetRef`, `Order`, `timer_epoch`, `MTState` | 幅を明示した整数。桁あふれは受付／実行エラー。IDを実数に格納する旧wireは境界で検証して型へ変換する。 |
| 時刻・期限・間隔 | `when`, `timer_at`, `source_next`, `ready`, `fb_end` | 移植の最初はbinary64演算と既存の演算順を維持。単純なフレーム番号・マイクロ秒への切り捨ては採用しない。 |
| ゲージ・確率・HP比率・閾値 | `burst_amount`, `gauges`, `chance_acc`, `hp_edge_prev` | 二進小数の累積と閾値を維持。100の直前／直後、条件発動の順序を個別に確認する。 |
| 攻撃・防御・倍率・回復・容量 | `damage()`, `max_hp()`, `shield_current` | まず共通binary64で各演算の丸めを維持。表示用の丸めを中間状態へ持ち込まない。 |
| 1命中の整数ダメージ | `__double2ll_rn(d)` → `mx(...,1)` | signed int64への最近接・偶数丸めと範囲検査を共通化する。`floor(x+.5)`への置換は不可。今回のコアには整数変換は未実装。 |
| ダメージの合計・補償和 | `total`, `FloatSum`, `add_sum`, `finish_sum` | 演算順とNeumaier補償項も維持する。1命中が整数でもHP・分配等の途中値は整数とは限らず、全配列の一律uint64化はしない。 |
| 桁丸め・離散化 | 充填・装弾の `floor(...+.5)` | 使用箇所ごとの規約を残す。上記の命中丸めと統一しない。floor／切捨て／整数変換の共通実装は後続。 |
| 非整数べき | コア命中期待値の `pow(ratio, 2.55)` | 未実装。倍率の誤差が最終命中丸めを跨ぐケースを独立検証するまで受付を開かない。Metalのfloat32 powを代用しない。 |

現行の時計は `1/60` 秒、攻撃速度／充填速度の除算、反復加算、`1e-9`／`1e-6` の境界補正を混用します。例えば周期ダメージは初回の方針により終了境界を含むかが変わり、終了時には補正参照を `end-1e-4` へ寄せます。これらの比較を固定tickへ移すには、許容値を変えるのでなく仕様の境界を定義し直して独立の期待値を作る必要があります。

現行CUDAのビルドは `--fmad=false` です。共通コアでも積和を勝手に融合せず、式の結合順と各演算の丸めを保ちます。既存CPUとの一致は回帰検査であり、ゲーム仕様の根拠とは分けます。旧CPUの誤りが見つかれば仕様の期待値を先に直します。

## 次の本体接続

1. binary64からの整数変換、floor、有限判定、絶対値を共通実装し、丸め境界を追加する。powは別の未解決ゲートとして残す。
2. 定義は `effect_spec.py` と既存の `*_specs.py` を引き続き唯一の分類・ID源とする。Slang用の型付きwireと状態を定義し、実際のGPU読み戻しで幅・stride・offsetを確認する。現行のdouble配列ABIを推測で使い回さない。
3. 対象世代と時計を本体から共通状態実行器へ移す。登録順スナップショット、子通知前の期限消費、周期維持更新、再登録のepochを保持し、`timer_registry_cases.py` 等の同じ仕様ケースを入力へ変換する。小さな4ケースだけで本体時計の完了としない。
4. 再入は明示スタックと上限エラーへ移す。キャラ別のMetal分岐は作らない。共通ソースのCUDA／MSL生成物は手編集しない。
5. Windowsでは薄い実行アダプターを用意した後に、同じ入力の短いCUDA検証だけを実施する。常時テストやフルビルドは設定しない。
6. 実部隊・装備・一時変更・発動順・最終HP・ダメージを確認し、小バッチから24GBでのピークメモリと処理時間を測る。通常画面のMetal選択はこの接続後に追加する。

全203体・全効果の受付を開くには、未対応の召喚／予約着弾／受領者別時計／同時命中も含めた実行器の完成と検証が必要です。標準条件187体のCUDAコンパイル受付や、今回の数値実証を完成件数に加算しません。

## 再実行

```sh
.venv/bin/python scripts/verify-portable-numeric.py --validate-only
.venv/bin/python scripts/verify-portable-numeric.py
```

後者がMetal実行です。元の4ケースは従来どおり `scripts/verify-portable-probe.py --backend metal` で独立に確認します。両検証は同じSwift転送アダプターを使用します。

## 参考

- [Slang公式対応表](https://github.com/shader-slang/slang/blob/master/docs/target-compatibility.md)：Metalでdoubleは非対応、64bit整数は対応。
- [Apple MTLCompileOptions.mathMode](https://developer.apple.com/documentation/metal/mtlcompileoptions/mathmode)：実行時コンパイルの浮動小数点最適化方針。
