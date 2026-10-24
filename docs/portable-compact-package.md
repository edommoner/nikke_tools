# 共通GPU検証パッケージの依存別軽量化

`package --compact` は、検証対象と無関係な研究用Python・テストファイルを同梱しない明示オプションです。既定のフルパッケージは維持します。対応範囲は `destructible-skill-retention`・`destructible-skill-misato-retention`・`destructible-aoe-burst-rosters` の3 suiteで、他suiteへの指定はnative準備・アーカイブ作成前に拒否します。

```sh
python scripts/nikke_gpu.py package --suite destructible-skill-retention --compact --out NEW_PACKAGE.zip
python scripts/nikke_gpu.py unpack --archive NEW_PACKAGE.zip --dest NEW_PACKAGE
cd NEW_PACKAGE
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture NEW_CPU --timeout 180
python scripts/nikke_gpu.py run --backend metal --cpu-only --smoke --capture NEW_CONTROLLER --timeout 180
```

実際のPython/Slangの指定、Windowsの起動方法とJob上限は既存の `gpu-development-cli.md` に従います。このオプションはWindowsのコンパイルやGPU実行を自動で追加しません。`--develop` との併用と、既存の厳密な保存Metal replayも使えます。

## 保持するもの

whitelist内の全app/scriptsコード、全GPUソース、全JSON fixture・公開データ、同梱済みの全pinned upstreamとLICENSEを保持します。元のwhitelist外からファイルを追加しません。選択suiteのadapter・全CPUテスト、全SMOKE_TESTS、bounded runner・phase audit・厳密normalizerを依存解析の起点とし、静的import・動的importのモジュール名literal・Pythonファイル名literalをたどります。同名候補は全て残します。制御テストの `cli.SUITES['compiler-full']` のような明示参照は、そのsuiteのテストファイルも保持します。

汎用Pythonの依存解決器ではありません。未知の式で作る動的依存を完全に証明できるとは扱わず、実行確認した3 suiteだけに制限します。CLI自身の全suite宣言から無関係なadapterを引き込むことを避ける一方、native reference registryは共通テストが実際に参照するため保持します。`inventory`・`reference`・`consumer-audit`・`cases`・`compiler-certificate`・旧監査・再packageは軽量版では拒否し、フルcheckout/packageを使うよう案内します。

manifestの `payload_projection` にprofile・起点・元一覧のSHA・除外一覧・件数・容量を記録し、package IDへ含めます。既存の全同梱ファイルのbyte/SHA検査、GPU source closure、golden、native/input照合、両生成の厳密normalizer、実行claim、Windows Job/優先度/2GiB/180秒上限を維持します。パッケージ作成時は除外前の全レコードも前後照合し、依存解析中・native準備中の変更を拒否します。

## 検証と限界

AoE suite追加の現在の証拠は `portable-destructible-aoe-burst-rosters.md` を参照。以下のv7は軽量化初版の固定測定です。

固定v7の同一ソースから、フル2,795ファイル/8,459,705 byteと軽量1,550ファイル/6,394,966 byteを作成。全同梱byte・レコード・goldenの完全一致、全GPUソース・fixture・data・pinned referenceの保持を直接比較しました。1,245ファイルを除外し、ファイル数は約45%、ZIPは約24%減少しています。Windowsでの準備時間改善は未測定です。

軽量版の共通制御37群372検査は371成功・Windows専用1 skip。生成はrequired cache hit、Slang/GPU追加0、既存sealed CUDA/Metal生成指紋を保持。途中の軽量development版で、元ミサト2入力の保存Metal readbackを既存replayで再監査し全一致。元capture・claim・rawは保持し、再dispatchはしていません。最終固定版もCPU43検査・157入力/native102で成功（CPU群48.520秒、native準備8.255秒）。各SHAは `research/portable-package-projection-checkpoint.json` および `research/package-projection-evidence/` を参照してください。

初回の動的reference factory欠落、別suiteテストファイル欠落は実際のCPU失敗として保存し、検査を減らさず依存へ追加しました。従来の合成パッケージ用テスト3箇所は新しいstorage gateのmockが欠けていたため、当該gateをテスト範囲から分離し、別の実storage budget5検査もSMOKEへ追加しました。保管済みgeneration extraction fixtureは更新していません。後続コミットa68a80fで追加済みの1048576word strideだけを2関数のASTから厳密に逆変換して旧fixtureと比較し、別容量・別transport変更を検出する故障注入を追加しました。生成コードnormalizerや計算本体の変更ではありません。

これは検証準備の改善で、新たなキャラ・効果のGPU対応証明ではありません。packing245/266、base185/203、残20 model gap、全キャラ認定0、通常UI CPUを維持します。現在のfull battle CUDA実機は未確認。Windowsの7プロセス終了原因もunknown/保全falseのままで、ゲーム・動画の利用可能性は因果根拠にしません。次は未実証の正のAoE burst flagと盾混在、貫通・蓄積/吸血混在などを既存共通Frameへ接続します。
