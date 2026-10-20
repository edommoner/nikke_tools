# MacBookへの開発環境の移行

現在の確認範囲と未完了項目は[共通実行器の進捗](portable-combat-runtime.md)と `research/portable-combat-checkpoint.json` を参照してください。以下は移行開始時の手順・経緯を含み、共通Metal本体の全キャラ対応完了を示す文書ではありません。

2026-10-19にMacBook Air・Apple M5（GPU 10コア）・24GB・macOS 26.6.2 arm64を実機確認しました。CPU起動（203体）とMetal実証4ケースは成功し、`research/portable-probe-metal.json` に実GPUの結果を保存しています。移行開始時点では本体のGPU計算はCUDA専用でした。現在は共通Metal本体を部分接続しており、全キャラ対応は未完了です。MacでCPUを使う作業環境と、共通GPUコアの小さな実証を先行して整備しています。

複合instant配送は `60a10b6` でMetal1824入力・Mac全26ゲート・82実編成に成功しました。21回の回復が5回で止まる経路は修正済みです。Windowsの先行実行の結果取得と現ソースの短いCUDA検証が残り、効率化は未実行です。[最新の引き継ぎ](mac-handoff.md) を参照してください。

均等分配と複合バフ対象は `d12b365` でMetal1773入力・Mac全25ゲート・82実編成が成功しました。Windows v59の結果取得と複合instant配送の接続が残り、効率化は未実行です。[継続中の引き継ぎ](mac-handoff.md) を参照してください。

最新の保護膜・デコイ・被弾層は固定版 `c411ddc` でMetal／CUDA1433正例・276拒否、保護層CPU参照57件とMac全24ゲートが成功しました。Windowsは最適化後72.67秒の短い検証で全1709入力を実行し、Metalと一致しています。全変種認証0/203体・通常画面CPUを継続しています。[最新の引き継ぎ](mac-handoff.md) と [共通保護層](portable-protection.md) を参照してください。

## 移行時の問題と対処

| 問題 | 現状と進め方 |
| --- | --- |
| 数値精度 | 本体はダメージ・時刻・ゲージ等に広く`double`を使用しています。Metalは`double`非対応なので、整数化・固定小数点化が妥当な部分と高精度演算が必要な部分を分類します。小さな整数の実証が通っても、本体の数値互換性の根拠にはしません。 |
| CUDA版の検証 | Macでソース生成はできますが、NVIDIA GPUでの実行確認にはWindows PCが必要です。Windowsは必要な差分だけ明示的に検証する補助環境にし、常時の自動ビルド・GPU検査は設定しません。 |
| Windowsの他作業への影響 | CUDAのコンパイルやPTXの初回JITもCPU時間を使います。低いプロセス優先度だけではGPUの他用途への無影響を保証できません。普段の編集・共通テスト・Metal開発はMacへ移し、CUDAは対象を絞った短い検証と、合意した空き時間の測定に分けます。 |
| 起動・コンパイラー | 従来の起動用`.cmd`、PowerShellセットアップ、NVRTCのWindows DLL指定はMacでそのまま使えません。計算エンジンの導入は共通Pythonへ移し、Mac/Linuxの起動時は`python3`を選びます。本体のCUDAビルド手順は依然Windows依存です。 |
| ARM64とバージョン | Apple Silicon用のPython・Node・Slangを使います。Windowsの数値比較環境はPython 3.12.14、Node 24.19.0です。Pythonはまず3.12系でそろえ、OS付属の実行環境やRosetta側と混在させないようにします。 |
| 個人データと過去版 | Gitにはブラウザー内の状態、`local-data/`、過去版の`research/ports/`等がありません。画面の「保存・書き出し」で`nikke-lab-session.json`を保存し、Macで読み込みます。保存したGPU設定はCPUに選び直します。過去版との比較が必要なら、Windows側の保存版を参照するか、必要な保存版だけ別途移します。BlaBlaLinkはMacのブラウザーでログインし直します。 |
| メモリと速度 | 現行CUDA状態は1部隊1,260,136バイトで、1,000候補の状態だけでも約1.26GBです。入力・出力・ホスト側のコピー等は別です。この配置をMetalにそのまま移すと仮定して性能や24GBでの上限を決めず、小さなバッチからMac実機で測定します。 |

## 共通実装の進め方

効果データ・命令仕様・状態管理・イベント実行・数値規約・期待値を共通にします。SlangからCUDA/MSLを生成し、GPU起動・バッファー配置・読み戻しだけをバックエンドへ分離する案を実証します。生成されたCUDA/MSLを手作業で別々に改修しません。現行のCUDA版は比較用の実装として保持します。

SlangのMetal側では型・ポインター等に制約があります。約2,700行のCUDA本体をそのまま変換できると仮定せず、グローバル状態の置き場、構造体の配置、子通知用の明示スタック、整数／高精度数値の操作を順に接続します。型の幅とバッファーの配置も、バックエンドごとの実測・反射情報で確認します。

最初の `gpu/portable_probe.slang` は次の4ケースだけを扱います。

- float32で整数を正確に表せる範囲を超えるダメージの整数演算
- 32bitを超える積と64bitの桁上がり
- 対象が再出現した後に旧世代へ向けた処理を適用しないこと
- 周期時計の再登録・解除・期限と、古い登録の拒否

入力と期待値は `tests/fixtures/portable-probe.json` に一度だけ書きます。`scripts/verify-portable-probe.py` が梱包と結果比較を共有し、Swift側にはMetalの起動・転送だけを置きます。現時点ではCUDA向けの生成確認までで、この実証のCUDA実行アダプター、本体のダメージ数式・float64規約・実編成は未接続です。Windowsで両方のソース生成と入力検査を確認しました。Metalのコンパイル・実GPU4ケースはApple M5で成功しました。本体の速度・メモリは未検証です。追加のbinary64共通コア候補と14,034ケースの実GPU検証は[数値規約](portable-numerics.md)を参照してください。

テストの記述は共通にしますが、機器固有の障害を検出するために各GPUで同じケースを実行することは必要です。CPU由来の途中状態や発射時刻をGPU入力に流用せず、仕様から作った期待値と既存の代表的な部隊検証を使います。

## Macでの最初の起動

以下はM5のMacで実行する手順です。Windows側で実行するコマンドではありません。最初にWindowsの画面の「保存・書き出し」で `nikke-lab-session.json` を保存し、Macへコピーしてください。このファイルは個人の所持・育成データを含むためGitへ追加しません。

### 1. Python・Node・Xcodeを準備

[Homebrew公式サイト](https://brew.sh/)の案内でHomebrewを導入します。すでに導入している場合は再導入不要です。M5ではApple Silicon用の`/opt/homebrew`を使います。ターミナルで次を実行します。

```sh
export PATH="/opt/homebrew/bin:$PATH"
brew install python@3.12 node@24
export PATH="/opt/homebrew/opt/node@24/bin:$PATH"
uname -m
python3.12 --version
node --version
```

`arm64`、`Python 3.12.x`、`v24.x`を確認します。Node 24はHomebrewのkeg-only formulaなのでPATHを明示します。新しいターミナルでも同じPATHが必要です。この手順ではシェルの設定ファイルを自動変更しません。

実機ではCommand Line ToolsのSwift 6.3.3と、`device.makeLibrary(source:)` による実行時コンパイルで両方のMetal実証が成功しました。`xcrun --find metal` は見つかりませんが、今回のソース実行には不要でした。オフラインのMetalコンパイルやXcodeでの解析が必要な段階では、Mac App Store等でXcodeを導入し、一度起動してライセンス確認と初期設定を完了します。通常のXcodeを`/Applications/Xcode.app`へ配置した場合、同じターミナルで次を実行します。

```sh
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodebuild -version
xcodebuild -downloadComponent metalToolchain
xcrun --find metal
swift --version
```

Xcodeを別名・別の場所に置いた場合は`DEVELOPER_DIR`をその場所に合わせます。Metal ToolchainはXcodeのSettings → Componentsからも導入できます。Xcode本体とMetal Toolchainの初期導入には時間・ディスク容量・ネットワークが必要です。

### 2. 移行用ブランチを取得

```sh
cd ~
git clone --branch codex/mac-portability https://github.com/edommoner/nikke_tools.git
cd nikke_tools
git branch --show-current
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python scripts/setup-engine.py
python scripts/check-migration.py --cpu-smoke
```

`codex/mac-portability`ブランチであることを確認します。変更はDraft PR #1にあり、mainへはまだマージしていません。プロジェクトのNode部分とPython部分は標準ライブラリーを使うため、この起動に追加の`npm install`や`pip install`は不要です。Slangのコンパイラーは次の段階で別途取得します。

起動確認のJSONは、`platform: Darwin`、`architecture: arm64`、`engine_present: true`、`cpu_catalog.passed: true`と`characters: 203`を目安にします。ここでの`passed`はCPU起動確認であり、GPU実行の成功ではありません。Metal ToolchainとSwiftの項目も確認します。

すでにMacでクローン済みなら、新たに同じ名前のフォルダーへクローンせず、そのフォルダーで`git fetch origin`、`git switch codex/mac-portability`、`git pull --ff-only`を実行します。未コミットの変更がある場合は先に内容を確認して保存します。

## 小さなMetal実証

```sh
python scripts/setup-slang.py
python scripts/build-portable-probe.py
python scripts/verify-portable-probe.py --validate-only
python scripts/verify-portable-probe.py --backend metal
```

同じターミナル・リポジトリ直下・仮想環境で順番に実行します。Slangは公式の2026.20を`.tools/`へ取得し、配布物のSHA-256を照合します。macOS arm64用とWindows用を分け、既存CUDAのインストールは更新しません。生成物は `research/portable-build/` に置き、各環境で作り直します。最後のコマンドだけがMac GPUを実行します。成功時も実証4ケースの検証であり、通常画面の詳細計算には接続されません。

`research/portable-probe-build.json` はソース生成、`portable-probe-fixtures.json` は入力の検査、`portable-probe-metal.json` はMacでの実行結果です。`gpu_execution_verified` と `production_runtime_connected` を分けて記録し、CPUフォールバックをGPU成功として扱いません。

最後の出力で`passed: true`、`gpu_execution_verified: true`、`backend: metal`、MacのGPU名、4ケースの一覧を確認します。`production_runtime_connected: false`はこの段階では正常です。`--validate-only`だけの成功はMetal実行の確認になりません。Swift／MSLが失敗した場合は診断を表示します。SwiftのキャッシュやGPUデバイスへのアクセスがサンドボックスで拒否される場合は、通常のMacターミナルで実行するか、その実行へのアクセス承認を利用します。入力検査だけへ置き換えて成功扱いにせず、実際の診断から修正します。

## 通常画面の起動と設定の復元

Metal実証を終えてから、同じターミナルで起動します。

```sh
NIKKE_PYTHON=python node server.mjs
```

ブラウザーで `http://127.0.0.1:4317` を開き、Windowsで書き出したJSONを読み込み、詳細計算はCPUを選びます。通常画面にはまだMetal詳細計算は接続されていません。サーバーはターミナルを使い続けるので、追加のコマンドは別のターミナルで実行するか、`Control+C`でサーバーを停止してから実行します。

新しいターミナルでは次の準備を行います。クローン先を変えた場合は`cd`のパスを置き換えます。

```sh
export PATH="/opt/homebrew/opt/node@24/bin:/opt/homebrew/bin:$PATH"
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
cd ~/nikke_tools
source .venv/bin/activate
```

## つまずいた場合

- `brew`・`node`・`python3.12`が見つからない：上記PATHと導入状況を確認します。
- `xcodebuild`がCommand Line Toolsを参照している：Xcodeの配置と`DEVELOPER_DIR`を確認し、Xcodeの初期設定を済ませます。
- Metal Toolchainがない：XcodeのComponentsか`xcodebuild -downloadComponent metalToolchain`で導入します。
- `Rebuild the changed portable probe first`：`python scripts/build-portable-probe.py`を再実行します。Windowsの生成物はコピーせずMacで生成します。
- Swift・MSLのエラー：ターミナルの診断と`research/migration-readiness.json`を確認します。初回実行はApple M5で成功していますが、環境ごとに診断を確認してください。
- ポート4317が使用中：既存サーバーを確認するか、`PORT=4318 NIKKE_PYTHON=python node server.mjs`として、ブラウザーも4318へ合わせます。

Macでの実行により`research/`のレポートJSONがMacの結果へ書き換わるのは正常です。個人のセッションJSON、`.venv/`、`.tools/`、キャッシュはGitへ追加しません。続きを開発する際は[引き継ぎ情報](mac-handoff.md)を先に確認してください。

## 参考

- [Slangの対応表（Metalのdouble制約を含む）](https://github.com/shader-slang/slang/blob/master/docs/target-compatibility.md)
- [Slangのポインター制約](https://docs.shader-slang.org/en/stable/external/slang/docs/language-reference/types-pointer.html)
- [公式Slang配布物](https://github.com/shader-slang/slang/releases/tag/v2026.20)
- [Apple：Xcodeの追加コンポーネント](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components)
- [Homebrew：Python 3.12](https://formulae.brew.sh/formula/python@3.12)
- [Homebrew：Node 24](https://formulae.brew.sh/formula/node@24)

## このMacでの再起動と復元済みデータ

`./Start-NikkeTools.command` でNode 24と`.venv`のPythonを選んで起動します。起動先は `http://127.0.0.1:4317` です。同じポートのサーバーを二重に起動しないでください。今回の元セッションとCPU選択・再計算後のセッションはGit対象外の `local-data/session-original.json` と `local-data/session-mac-cpu.json` に保存しました。後者を画面で読み込むと復元できます。育成データの自動永続保存は既存画面の仕様に含まれないため、再読み込み時はJSONを読み込んでください。

添付の5人・15秒設定で、CPUの現在育成は45,251,089、取り込み時育成は44,888,797でした。デモと記録された5人のセッションであり、全所持キャラのインポート件数ではありません。Pythonは3.12.15、Nodeは24.22.0で、Windowsの記録とパッチ版が異なります。
