## 2026-10-31 現通常APIの再検証結果

4e861325の固定周期・30秒・標準編成266profileを再実行し、実Metal255件はCPU全製品応答一致、既知11件は理由付きCPU切替。保存raw再投影/入力全byte再生成も独立照合済み。追加profileは0、全設定・全効果の認定ではない。範囲/時間/未対応一覧は`research/target-count-query-evidence/product-current-fixed-api-sweep-v1.json`。現CUDA製品実行0、歴史CUDA1profile・1秒とは区別する。下記11件の契約判断は継続する。

## 2026-10-31 製品残11profileの次の実装判断

現4fa35b70を元catalogueから再prepare/compileした全11の先頭拒否は既存readinessでreference_model_gap。effect_range_pct/effect_target_count_add/移動/lockはcanonical consumerなし、cover_def_pctはSCOPED_INERT、分配はdeferred、敵ammoはchar_states外をskip、敵healは既定world source/recipient経路が未確定。proof product-remaining-profiles-current-20261031.jsonとproduct-current-model-check-20261031.json。GPU/native追加0。これは全効果の網羅的検査ではなく、全11profileの現先頭拒否と既存source監査の照合。

Reiの元定義にはfull_burst_startで同じallies_with_buff:섬멸 태세へ対象数+1・範囲+500%の2効果がある。先頭countだけの受付でprofile完成とはしない。通常cohortはRei/Miranda/Dolla/N102/Maryで対象のAsuka WILLEがいないため、空recipientで数値一致しても実効果を実証できない。必要なのは元Rei＋WILLEの実編成、対象buffが有効になるburst、複数敵/範囲内外の正例、対象なし/期限切れ/世代交代の対照である。

次のprofile実装では、まず既存effect_target_count_policy.query/named_range_battleと共通GPU wireの再利用範囲を決める。CPUの既定consumer追加と製品入力のworld/geometry契約が必要で、別の宣言モデルをcanonical/game verifiedと読み替えない。比較用旧CPU/旧expectations/失敗を保持し、必要な新CPU契約を版分けしてから同じ共通実行器/既存テストへ接続する方針をレビュー対象とする。protected CPU正本を変更するスコープは明示許可が未確認。公開266profile完成を目指す判断であり、残11を目標から除外するものではない。

CUDAは現normal entryのsealed source packetをMacで準備する。前のWindows PTXは旧source4bfd6841で、現normal shader852c1192とは生成codeが違う。旧PTX成功/claims/観測falseを保持し、現sourceの再利用証拠へ付替えない。Windowsへの新compile/runはまだ依頼しない。

# 未対応分類を次の作業へ接続する

共通CLIの`inventory --out <new-file.json>`は、既存の82分類・優先順位を保持したまま、各`priority.reference_readiness`と`work_lanes`を出力する。新しいGPU受付を追加する機能ではない。

| lane | 次の作業 | 現在の分類数 |
| --- | --- | ---: |
| gpu_lowering_candidate | 記録済みCPU契約を前提に共通実行器への接続を設計 | 1 |
| native_contract_extension | 未被覆の対象・scaling等のCPU契約を追加 | 1 |
| native_consumer_research | CPU consumerを特定して意味を確認 | 4 |
| reference_model_gap | 現CPUモデルの制限を整理 | 1 |
| reference_review | まだ準備状況を監査していない | 75 |

回復分配は記録済み28ケースを示すが、全相互作用を検証した意味ではない。all_alliesの分類は接続候補、`['self','allies_weapon_top_atk:RL:2']`は追加契約が必要。projectile／shieldはconsumer未確認で、出力不変を理由に無効果受付しない。cover防御は現在のcanonical分類がSCOPED_INERTであることを実コードで確認する。将来その分類が変われば未監査へ戻る。

新しい情報は独立した`app/portable_readiness_semantics.py`へ置き、元の失敗code・診断文・対象・順位・入力を変更しない。未知の効果、追加フィールドや未被覆targetを接続可能と推定しない。全行のGPU対応・GPU受付検証・全キャラ認定・runtime検証のフラグはfalse。

固定package e33e8ae5でreadiness21件と既存CLI39件が成功。全266 profile/input/issueと旧82順位を直接照合して保持し、静的packing214/base154、CPU battle／GPU0を確認した。記録件数がCLI登録済みliteral factoryの実ケース数と一致することも検査する。詳細は`research/portable-reference-readiness-checkpoint.json`。最初の追加テストがpackageへ含めない研究checkpointに依存した失敗は保存し、実登録factoryを使う契約へ訂正した。

CUDAの分割調査は既存共通assemblerへ暗黙追加しない。NVIDIA 12.4.1の[compiler driver文書](https://docs.nvidia.com/cuda/archive/12.4.1/cuda-compiler-driver-nvcc/index.html)で、ptxasの`--compile-only`がrelocatable objectを生成し、separate compilationにdevice linkが必要なことを確認した。ただし現PTXの分割合法性・tool互換・2GiB内への改善は未証明。元body・外部宣言ABI・global所有・出所と失敗保持のCPU契約を整えてから明示候補を選ぶ。

追加のheal-share-targets6契約をCPU検証し、readinessの記録件数を34へ更新した。旧28は全指紋を保持。複合対象は6literalケースの検証までで、未被覆相互作用が残るためlaneの自動昇格はしない。詳細はportable-heal-share.mdとportable-heal-share-target-reference-checkpoint.json。

さらにheal-share-lifesteal9を検証し、記録件数は43へ更新した。これはCPU側の前提が増えた記録で、GPU laneの昇格や対応率の増加ではない。独立plan演算のMetal10は成功したが、battle接続は別の未完了項目として扱う。

実編成4件の追加後も全266入力と80順位は保持した。hits_partsだけの3分類はpinned timelineとcanonical compilerにconsumerを確認し、native_contract_extensionへ移した。ソース確認でありCPUケース0・runtime検証false・GPU対応falseのまま。複数の未対応fieldsが混ざる行はreference_reviewに残す。段階を混同しない22検査に成功、GPU sourceの変更はない。
