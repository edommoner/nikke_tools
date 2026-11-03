# 参照エンジンのインストールと更新

通常の製品計算は `67835ca3033a95482749ea2db35a8ee2a0856a92` を使います。
開発者・テスト実行者が過去のGPU記録を照合する場合は、旧版
`23164e4a88fe46af609cc99b0de38a98313a5f4d` も明示的にインストールします。

```sh
python3 scripts/setup-engine.py
python3 scripts/setup-engine.py --historical
```

Windowsでは、使用中のPython実行ファイル（例: `python`）で実行してください。

ネットワークを使わない場合は、対応するコミットの取得済みZIPを指定します。
`--historical` は現行版の確認・インストールに加えて旧版も用意します。

```sh
python3 scripts/setup-engine.py --archive /path/to/nikke-calc-67835ca3.zip \
  --historical --historical-archive /path/to/nikke-calc-23164e4.zip
```

現行版は `research/upstream/nikke-calc-master`、旧版は
`research/upstream/nikke-calc-23164e4` に置かれます。
ZIPコメント、パスの安全性、アーカイブから固定した全ファイルのSHA256を確認し、
計算用Python・JSONとライセンスが欠けているZIPは拒否します。
旧版の指紋には `tests/historical_engine_reference.py` の `PINS` も含まれます。
指紋マニフェストはGitの改行変換対象外とし、Windowsでも同じバイト列で検証します。
署名のない版名マーカーや必須ファイルの存在だけでは版を判定しません。

既存のインストールは内容を検証します。検証済みの旧版が現行版の場所にあれば、
新しいZIPの検証を済ませてから `nikke-calc-23164e4` へ移動し、現行版を配置します。
既存ツリーは削除しません。ローカル変更・未知のファイル・リンク・計算用ファイルの
欠落がある場合や、退避先が既に存在する場合は、元のツリーを保ったまま停止します。
退避先の衝突は、両方の内容を確認し、どちらも失わないように解決してから再実行してください。
Pythonの `__pycache__` に加え、通常ファイルの `.DS_Store`・`Thumbs.db`・
`desktop.ini` とAppleDoubleの `._*` だけは、どの階層でも版の判定対象に含めません。
名前が似た別ファイルや未知のPythonファイルは引き続き拒否します。
公開に失敗した場合は、配置先が空であれば元のツリーを元の場所へ戻します。

製品ワーカーも、参照エンジンを読み込む前と各計算の前に、固定した計算用Python・JSONを
検証します。版が違う場合や計算用ファイルが変更されている場合は、明示的なエラーで停止します。
過去の記録を照合するテストだけが、明示した旧版を別プロセスで読み込みます。
通常の製品計算が旧版へ切り替わることはありません。

変更後の検査は `tests/test_engine_setup.py` を使います。この検査は一時ディレクトリと
ローカルで作成したZIPだけを使い、ネットワーク接続やGPU実行を行いません。
