# 共通GPU移行の全体レビュー：bf05286と敵対象処理の作業差分

利用者の依頼により、ログイン済みClaude Codeで現在の方針をレビューし、Codexが指摘を実ソース・固定packageと照合しました。共通Slangで数値・状態・イベントを実行し、CUDA／Metalは転送・起動を分ける方針は維持します。ただし、機能追加の進捗とCUDAで実行可能な状態への進捗を別々に管理する必要があります。大規模な実行器の書き直しを支持する証拠はありません。

対象HEADは`bf052865bc6dce970cbafbc631ec1528851904c1`、レビュー時の未コミット差分はenemy-selectionです。Metal588の一致は確定版の保存結果です。作業中62入力は56一致・6不一致で未seal。静的packing209/266は変換可能な定義の数で、全キャラ認定ではありません。通常UI CPU・全キャラGPU認定0・最新版CUDA数値一致未確認を維持します。

## 採用する指摘

### 1. noinline属性の移動を修正対象にする

`gpu/world_actor_pools.slang:198`の既存`[noinline]`直後へ`actorSortSpawnOrder`を挿入したため、元の`actorSetCapture`（現在211行）から属性が外れています。HEADとの比較で確認しました。意味を変えない抽出にコンパイル方針の変更が混入しています。

`actorSetCapture`の属性を戻し、sort helperの属性は意図して選びます。生成CUDAの属性・呼出関係を既存compiler-statsで確認し、機能修正後のMetal集約検査で旧588の全rawを確認します。この指摘だけを理由にWindowsで再コンパイルしません。ptxasのメモリへの影響は未測定で、今回のCUDA失敗原因とは断定しません。

### 2. 拒否テストを「status64なら成功」から一段強くする

`scripts/nikke_gpu.py:412`付近の拒否入力はstatus64を必須とし、adapterの`validate_rejection`は任意です。enemy-selection adapterにはこのhookがありません。意図と異なる上流検査で拒否されても、当該入力の拒否は合格し得ます。同じ出力SHA自体は不具合の証明ではありません。

既存診断入口のstageと、単一項目だけを変更した負例・対応する有効入力を組み合わせ、目的の受付経路まで到達したことを確認します。stage404等は複数条件をまとめているため、stage一致だけで正確な拒否理由を証明したとはしません。まず新規8負例を対象にし、旧129を一律にGPU再実行する必須条件は作りません。公開ABIやstrict normalizerは変更しません。

### 3. 受付と実際の消費経路を契約テストで結ぶ

`validEnemyRoute`はroute10をprojectileのcompile flagとRNG metadataで許可しますが、random抽選の実装はActor集合選択側にあります。型・routeの受付だけでは、buff／stack／解除／期間延長／DoTの全消費経路へ接続できたことになりません。既知の6不一致はそのまま保持し、追加発見として数えません。

kind×route×消費経路、対象集合の固定／再解決、timer登録／refresh／失効、budget確認の順序を小さな表と境界fixtureで管理します。`WORLD_FIELDS_ENEMY_SELECT`は一部経路で仮のmaskを返すため、legacy関数へ単純なroute10拒否を追加すると正しい経路まで遮断する可能性があります。Claudeの「一律にlegacyで拒否」はそのまま採用せず、実際の呼出順を確認して接続します。能力無効の不正raw入力を拒否する検査は別途必要です。

### 4. 同一入力のGPU重複を除ける

固定enemy-selection packageの62入力をSHAで数えると、固有入力は52、重複は10でした。省略NとN=1、128と256のcap、code selectorの等価loweringです。1入力の出力は3,145,728byteなので、このsuiteでは約30MiBを減らせます。現在の開発全体の主な遅延原因をこれだけで解消するとは主張しません。

CPUでは各表記のpackingと独立native結果の検査を残します。GPUは代表入力を実行し、別名fixtureにも同じreadbackを各々のnative oracleで比較できる形が候補です。入力SHAだけで期待結果の異なるケースを捨てる方式にはしません。既存sealed goldenを理由なく作り直さず、新suiteの統合時から適用します。

### 5. CUDAコンパイル実現性を別の優先課題にする

v115のcold compiler allocation failureは未解決です。v117のCPU53件成功やcache claimはcoldコンパイル成功でもCUDA計算一致でもありません。Metalで対応件数を増やすだけではこの障害は解消しません。

各機能で生成CUDAの関数規模・noinline属性・Runtime宣言量の差分を既存compiler-statsへ記録し、説明のない変化を検出します。これらの字句指標をcompiler peakの原因や改善量へ換算しません。Windowsの次の試験は、新しい仮説・固定package・成功基準を定めたcompiler-only1回に限定し、既定60秒／2GiB・cleanup条件を維持します。同条件の再試行や上限拡大はしません。

## 採用しなかった仮説

- **body消滅後のadd1体で抽選を省略する疑い**：現在の正本はボスHPを減らして退場させず、`boss_pattern.py:1726`のrandom poolは常にENEMYを含みます。GPUも`initializeActorPools`でbodyを生存にし、`actorPoolsSync`はslot1以降、`actorPoolLand`のkind0は退場処理を通りません。現モデルの不具合とは確認できません。将来body退場を導入する場合の契約として残します。
- **codeをBODYへloweringするのは誤りという疑い**：正本`research/upstream/nikke-calc-master/calculator/boss_pattern.py:1758`は両code selectorを明示的に`[ENEMY],1`へ写し、addのcodeフィルタを行いません。現在のloweringはこの制限に一致します。実ゲームの属性別add選択まで対応したとは扱いません。また元fixtureのnative計算は元のselector文字列で行うため、packed入力が同じでもnative比較が自明になるわけではありません。
- **数値設計に懸念なしという評価**：今回の差分は主に整数RNGで、binary64／pow本体を変更していないことの確認です。全数値実装の再証明ではありません。既存の明示丸め・用途限定pow・不確定時拒否・独立期待値を維持します。

## 次の順序と完了条件

1. 属性移動を修正し、新機能の受付・対象ライフサイクル・拒否意図の契約を整備する。既知6不一致を保存rawと診断で切り分ける。
2. 修正済みの独立fixtureを新immutable packageでMetal検証し、実編成と集約へ接続する。旧588の保持、全native比較、scratch検査、独立sealを維持する。比較項目の削減や許容誤差の拡大で通さない。
3. CUDAのコンパイル障害は仮説に基づいて別管理する。機能追加の優先順位には静的解除件数だけでなく、実編成で確認できる範囲とコンパイルへの変更量も含める。

保存588件のGPU処理は9.011秒、CPU preflight32.985秒、GPU実行と比較を含むbounded子プロセス57.574秒です。工程は包含関係があり単純加算しません。prepare、preflight、比較、独立監査のCPU参照を無差別に削らず、不変な入力準備の再利用と工程別計測から改善します。sealは既に独立監査内の比較1回を再利用しています。この既存改善を重ねて提案しません。

## レビューの実施記録

Claude Codeはツール無効・MCP無効・session保存無効で、関連24ファイルと差分427,843byteをレビューしました。140.301秒、exit0。認証情報・個人session設定・raw GPUバイナリ・PTX・CUBINは含みません。今回のGPU／Windows実行は0。提供範囲のレビューであり、全リポジトリ探索・性能測定ではありません。実装は変更していません。

- prompt SHA256: `f515e59c59fccdd703514fe6e1c51ed36e1f2fd7c0b9e36016d4b083b976d378`
- 回答SHA256: `c12babb308d9239868b8316e5c42fd8712ac06f7066512fc6a17a135ede689f2`
- ローカル原回答: `/tmp/nikke-overall-review-current.response.txt`
- ローカルmanifest／実行記録: `/tmp/nikke-overall-review-current.manifest.json`、`/tmp/nikke-overall-review-current.run.json`
- 使用スキル: `/Users/edo/.codex/skills/claude-code-reviewer/SKILL.md`
