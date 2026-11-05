"""Publish the concrete adoption result only after current validation finishes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '32653b09d597f0443c0df11f2076b249ec33dbd7'
gates = json.loads((ROOT / 'research/portable-element-optimized-global-gates.json').read_text())
assert gates['source_commit'] == SOURCE and gates['passed'] and gates['complete'] and len(gates['gates']) == 31
windows = json.loads((ROOT / 'research/windows-portable-element-v66.json').read_text())
metal = json.loads((ROOT / 'research/portable-combat-metal.json').read_text())
assert windows['passed'] and metal['passed'] and windows['execution']['commit'] == SOURCE
assert windows['input_sha256'] == metal['input_sha256'] and windows['output_sha256'] == metal['output_sha256']

heading = '## 2026-10-20 属性判定の最適化を両GPU検証後に採用'
body = heading + '''

固定ソース `32653b0`、ABI `0x5045566B`。属性優位上書きの存在判定を、alive／対象所属で絞って既存のkind・stat・codeアクセサーを読む方式へ変更しました。実装は共通Slangの1か所です。数値演算・状態配置・入力86016／出力159744 wordsは変更していません。

最適化後も全2182入力の全出力ワードが、基準版 `14c8e2e` とMetal／CUDAの両方で完全一致しました。全ケース別SHA・旧2006入力・全CPU回帰も保持しています。Mac全31ゲート・単体237件・実編成86条件・203武器・203装備・固定8編成・HTTP APIが成功し、旧86条件の実行時間以外の全項目も一致しました。

Windowsの今回v66はBelowNormal・120秒上限の1回、93.48秒で成功しました。元checkoutとサービスを保持し、残存検証0です。結果JSONとreadback照合記録の2ファイルだけをartifactブランチへ保存し、MacでGit blobのbyte数・SHAと内容を照合しました。基準版v65の88.58秒の保存結果も取得済みで、接続復旧に伴う過去検証の再実行はしていません。

全基準検証・転送終了後の測定で選んだ候補と、採用したhelperのソースは同一です。その測定では通常負荷のGPU時間の中央値が約5.6%、末尾一致負荷で約1.3%改善し、標本範囲は重なりませんでした。残る3負荷は範囲が重なります。今回の採用確認は正しさの検証であり、実編成全体・CUDA速度・ピークメモリの新しい測定ではありません。

初回の未保存Metal出力差は原因未特定のまま、`portable-element-initial-core-finding.json` に保持します。現在の検証では再現していません。修正済みとは主張しません。出力不一致時の全readback・差分ケースの入力・ケース別SHAを保存して停止する比較器を維持しています。

最新証拠は `research/portable-element-optimized-validation.json` と `research/portable-combat-checkpoint.json`、基準版証拠はGit `80170c3` の `portable-element-baseline-validation.json` です。定義受付候補43体・未受付効果384件・全変種認証0/203体・通常画面CPUを継続します。次の確率条件は、スキル値・短絡順・所有者共有位相・4096イベントのbinary64状態をCPUで観測し、[接続設計](portable-probability-design.md)へ整理しました。GPU受付はまだ無効です。
'''
updates = {}
for name in ['mac-handoff.md', 'portable-combat-runtime.md']:
    path = ROOT / 'docs' / name
    text = path.read_text()
    if heading not in text:
        first, rest = text.split('\n', 1)
        updates[path] = first + '\n\n' + body + '\n' + rest.lstrip('\n')
path = ROOT / 'docs/mac-migration.md'
text = path.read_text()
old = next(line for line in text.splitlines() if line.startswith('現在の検証済み基準版は固定ソース'))
new = '現在の検証済み基準版は固定ソース `32653b0`、ABI `0x5045566B`。属性優位上書きの直接フィールド読み取りを採用し、全2182入力の全出力が基準版と両GPUで一致しました。Mac全31ゲート・単体237件・86実編成が成功し、Windowsは今回93.48秒・低優先度の1回、結果2ファイルをGit経由で取得・照合済みです。元のWindows作業・サービスを保持し、残存検証0です。初回Mac出力差は原因未特定の記録を維持します。全変種認証0/203体・通常画面CPUです。[最新の引き継ぎ](mac-handoff.md) と [属性優位上書き](portable-element-overrides.md) を参照してください。'
updates[path] = text.replace(old, new, 1)
path = ROOT / 'docs/portable-element-overrides.md'
text = path.read_text()
text = text.replace('候補を選択しましたが、最適化後ソースの両GPU検証は次段です。',
                    'この候補を固定ソース `32653b0` へ採用し、最適化後も全2182入力の出力が両GPUで基準版と完全一致しました。')
note = '最適化後のMac全31ゲート・237単体・86実編成・203武器・203装備・固定8編成・APIも成功しました。Windows v66は93.48秒の1回で、元作業・サービス保持、残存検証0、保存JSONとreadback記録の2ファイルをGit経由で取得しSHA・内容を照合しています。現在の証拠は `research/portable-element-optimized-validation.json`、基準版はGit `80170c3` の証拠です。次段の確率条件は[接続設計](portable-probability-design.md)に整理しましたが、GPU受付は未実装です。'
if note not in text:
    text = text.replace('\n通常画面はCPU、', '\n' + note + '\n\n通常画面はCPU、')
updates[path] = text
for path, text in updates.items():
    path.write_text(text)
print('Updated4 handoff documents after completed optimized-source validation')
