# v135保存PTXの呼出関係と次のコンパイル調査

新しい共通CLI `ptx-stats --callgraph`を使い、Windowsに残るv135のcache entry／compile phaseをCPUだけで解析した。解析ツールは固定`fb234c0`、PTXのproducerは`0e1f71b`であり、最新GPU本文のCUDA成立検査ではない。元PTX・cache・phaseは不変、PTX本体の転送／公開は行っていない。

## 得られた事実

Windows peer summaryによると、定義191はすべてentry `portableEvents`の直接call閉包に属する。強連結成分も191個・各1関数で、自己循環を含むcyclic componentは0。間接call・外部・未宣言symbolも0で、字句的な直接callグラフは閉じている。

最大virtual宣言と最大body行数は引き続き`applyDefinitionFrame_0`の5,865宣言／10,472行で、この関数のlocal宣言は56byte。宣言値は物理register・stack／必要compiler memoryではない。Runtime全体copyがないことも、この値だけでは証明できない。

- PTX SHA: `1e808014ad411bb0675615b4970c7a104ed7d093dd5fcec54233df1c5dc6a6a3`
- cache key: `e0ff1cd685b62c3e4bbc2b449d86989d1a3ad6b51be7f1286d4095b2cb53e824`
- Windows解析: 約1.692秒、BelowNormal、30秒上限内、追加NVRTC／ptxas／link／driver／GPU 0。
- 完全report: 261,148byte、SHA `55a5e93dc1775d67b2219fd0dfdb997d42ed0c61fd2d954767234a5fa7cc4872`。Windowsに保持し、Macへは小さなpeer summaryだけを移送。

Macはpeerのsource bytes/件数を固定6ファイルmanifestへ、PTX SHA/keyを既存v135記録へ照合した。Macによる元PTX・完全reportの独立監査を行ったとは扱わない。根拠は`research/portable-world-v135-callgraph-peer-report.json`。

## 開発順序への影響

- **直接call循環を原因候補とする新しい変形試行は優先しない。** このPTXでは循環が観測されない。ただし関数内部の制御フローやcompiler内部データ構造まで循環がないという意味ではない。
- **到達しない関数を削るだけの対策は、この191定義には適用できない。** 全定義がentryから到達する。実行時に通らない分岐の証明や、機能削除による短縮を意味保持と混同しない。
- **最大関数とmodule全体を区別する診断は依然必要。** DAGであることだけでは、最大関数単独のassemblyや、全moduleのlinkが2GiB以内で成立するとは分からない。

## 次の実装対象

保存PTXを入力とするCPU-onlyの分割計画／抽出検査を共通CLIへ追加する候補とする。最初から実コンパイルを起動しない。

1. 最大関数を一意に選び、元function bodyの全byte／SHAを保持する。呼出先の完全なparameter prototype、module-level global／constant、version／target／address_sizeの所有権と依存を検査する。未知構文・多義的symbol・未対応stateでは停止し、元PTXをその場で訂正しない。
2. 他moduleから使うdefinitionとextern declarationのlinkage／ABIを明示する。global／constantの唯一の定義と、元symbol／bodyを対応付ける。callグラフの切り分けだけで合法なlink単位と認定しない。
3. 診断用relocatable objectは通常のPTX／CUBIN cacheやbattle artifactと区別する。既存assemblerのsource書換え禁止契約を緩めず、新しい明示的な実験manifestへ元PTX／選択／変更箇所／tool／flagsを固定する。
4. CPU検査後、対応ptxasのcompile-only構文と、将来のlinkに使うtoolの版・利用可能性を確認する。準備できた場合だけ、最大関数側のassembly1回を既存BelowNormal Job・60秒／2GiB・cleanupの範囲で検討する。残りmoduleやlinkを自動fallbackとして追加しない。

最大関数側の成功は全体成立ではなく、失敗も必要メモリの定量値にはしない。CUDA数値比較／全キャラ認定は引き続き未完了。

## 失敗保持と再利用

最初のWindows9検査は7成功・2 PermissionErrorで停止し、PTX解析は実行しなかった。元logは保持した。共通`validation_environment(capture)`を子processへ渡すよう起動設定を修正し、別captureで9成功・その後の解析1回成功。parserやPTXは修正せず、親環境は不変。成功で元失敗を置き換えない。

Macの通常immutable packageでは共通smoke163中162成功／Windows専用1skip（約3.183秒）。約142KBの6ファイルCPU受渡しも9検査成功。PTX解析のためにGPU本体を再コンパイル・再実行する工程は不要になったが、全体の開発時間の削減率は測っていない。
