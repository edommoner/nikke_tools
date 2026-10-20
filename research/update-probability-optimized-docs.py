"""Update the handoff only after fixed-source gates and report transfer pass."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    gates = json.loads((ROOT/'research/portable-probability-optimized-global-gates.json').read_text())
    transfer = json.loads((ROOT/'research/portable-probability-optimized-transfer-completed.json').read_text())
    assert gates['passed'] and gates['complete'] and len(gates['gates']) == 32
    assert gates['source_commit'] == transfer['source_commit'] == '2b89babe0bd6ffa16c9b8b315de3137e7da669c8'
    assert transfer['passed'] and transfer['artifact_transfer_complete']
    section = '''## 2026-10-20 条件helperの効率化を両GPU検証後に採用

固定ソース `2b89bab`、ABI `0x5045566C`。共通Slangの条件helperで必要なowner・duration・flags・conditionCountだけを読みます。測定した候補と採用版のhelperは同一です。数値演算・効果定義・Runtimeの配列、入力86016／出力159744 wordsは変更していません。

全2280入力（1940正例・340拒否）の全出力ワードが基準版 `27a3751` とMetal／CUDAで完全一致し、ケース別SHA・展開結果・CPU回帰・旧2182入力も保持しました。Mac全32ゲート・単体243件・実編成102条件・203武器・203装備・固定8編成・HTTP APIが成功し、従来102条件もCPU参照の実行時間以外は全項目一致しました。

Windows v68はBelowNormal・120秒上限の実GPU1回、99.71秒で成功しました。元checkoutと既存サービスを保持し、残存検証0です。結果2ファイルの共有は利用者の明示許可後にGit `4ab2a94` から取得し、byte数・SHA・全入力と出力・CPU回帰・限定正規化した生成CUDA／MSLをMacで照合しました。転送のためのGPU再実行はありません。

全基準検証・転送終了後の測定では、4096発負荷のGPU時間中央値が約2.7%短縮し、標本範囲は重なりませんでした。他の4負荷の範囲は重なります。今回の採用確認で新しい速度測定は行っておらず、実編成全体・CUDA速度・物理ピークメモリの改善は主張しません。

初回の新しい保存器は入力先頭の件数4バイトを記録し忘れて停止しました。実GPU入力・出力は基準版と一致し、rawを保存したうえで保存器を修正し、固定版の全検証をやり直しました。記録は `portable-probability-optimized-initial-harness-finding.json` です。前段の原因未特定のMetal差分は別の未解決記録として保持し、修正済みとは扱いません。

最新の証拠は `research/portable-probability-optimized-validation.json` と `research/portable-combat-checkpoint.json`、基準版の全体証拠はGit `988858f` です。愛蔵品0～3段階の受付監査は198/812条件・全段階の候補49体で、段階0だけの候補51体と区別します。プリムの対象スタック条件・ジュリアのクリティカル条件などが残ります。全変種認証0/203体・通常画面CPUを維持します。

次のコア／適正距離条件は、実CPUのbuff付き35条件と203体×6武器種の距離境界32,886条件を観測しました。入力余白へ武器ID・距離・元武器と変更後武器の範囲を保持する設計だけで、GPU受付はまだ無効です。残る全キャラ・全特殊効果の接続と認証を続けます。

'''
    for filename in ['docs/mac-handoff.md', 'docs/portable-combat-runtime.md', 'docs/portable-probability-design.md']:
        p = ROOT/filename
        text = p.read_text()
        start = text.index('## 2026-10-20 条件helperの効率化候補を固定して検証中')
        marker = '## CPU参照で確かめた規約' if filename.endswith('portable-probability-design.md') else '## 2026-10-20 確率条件'
        end = text.index(marker, start+1)
        p.write_text(text[:start]+section+text[end:])
    p = ROOT/'docs/mac-migration.md'
    text = p.read_text()
    start = text.index('現在の検証済み基準版は')
    end = text.index('\n', start)
    text = text[:start]+'''現在の検証済み基準版は固定ソース `2b89bab`、ABI `0x5045566C`。確率条件の共通helperで必要なフィールドだけを読む方式を採用しました。全2280入力の全出力が基準版と両GPUで一致し、Mac全32ゲート・単体243件・実編成102条件が成功しました。Windows v68は低優先度の実GPU1回・99.71秒で、元作業とサービスを保持、残存検証0、許可後に結果2ファイルを取得・照合済みです。採用候補の測定では4096発負荷が約2.7%改善し、他4負荷の標本範囲は重なりました。全実編成・CUDA速度・ピークメモリの測定ではありません。段階0の受付候補51体、全愛蔵品段階の候補49体、全変種認証0/203体・通常画面CPUです。初回Mac出力差の原因未特定記録を維持し、残る全キャラ・全特殊効果の接続と認証を進めます。[最新の引き継ぎ](mac-handoff.md) と [確率条件](portable-probability-design.md) を参照してください。'''+text[end:]
    p.write_text(text)
    print('Probability optimized-source handoff updated after completed32 gates')


if __name__ == '__main__':
    main()
