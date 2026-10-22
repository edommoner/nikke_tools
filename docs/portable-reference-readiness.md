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
