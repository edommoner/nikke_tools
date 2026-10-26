# HPダメージ死亡と所有fieldを共通GPUで検証する

`coordinate-typed-owner-hp-death` は旧103入力を保持し、実HP死亡の3契約を加えた106入力（native63／拒否43）のseal済み入口です。元Prim全71定義・完全5人・武器/成長・8秒、別宣言counter2効果を保持し、`gpu/world_coordinate_typed_logical_owner_entry.slang` と既存比較器を再利用します。GPU/backend/数値/正本/normalizerは変更しません。

新3件は同一攻撃内で子field発動後に死亡、遅い子field発動前に死亡、fieldが有効になった後に死亡です。HP1または1000000へ既存攻撃がダメージを与え、ADDのgraphノードは有効なまま。CPU observerはhit_add前後のHP/dealt/aliveとgraph状態を読むだけです。GPUは既存readbackの最終ADD HP/生死/世代、field carrierと最終query、全戦闘/物理履歴/RNG/counterを比較対象とします。CPUのhit_add呼出しやframe別visibility記録をGPUの直接履歴証明とは扱いません。

proofは永続 `.portable-recovery/proofs/owner-hp-death-gpu-20261027/` に置きます。GPU実証・fresh独立監査を通し、goldenとsource certificateを登録済みです。旧103の証跡は別の原本として保持します。Windowsでは前ターンに固定sourceの配布検証まで完了しましたが、現sourceのCUDA cache/compile/launch/readback成功は未確認です。

同時に採取した現在のinventoryは266profile中245入力変換成功・21失敗、203base中185変換成功、未対応20分類。過去の19失敗という件数を現在の値として再利用しません。入力変換可能でも全キャラ実戦認定0・UI CPU・目標未達です。残る20分類にはprojectile/shield倍率、移動、cover防御、敵回復受け、弾薬charge、multi-hit、分配、範囲/対象数、lock-on等があり、個別CPU/GPU契約と既存のcanonical inventoryとの接続は別の段階です。

実測package44292161…、M5全106/native63/拒43一致。CPU preflight411.900620秒、GPU4.185487秒、library0.007891秒、pipeline0.003058秒、child6.520327秒/180上限。生成cache必須hit/Slang0、pipeline必須hit/archive compile0。旧103と同じsource/device/OSのpipeline key4c8ab4e0…を実機で利用しました。

fresh GPU禁止child6群（20/20/20/20/20/6、各180秒以内）で独立監査、総534.033338秒、各86.461/37.774/87.910/106.950/138.396/73.565秒。同じ監査からgolden/certificateを生成、二重seal0。全group JSON/stdout/stderr/aggregateは永続audit-tmp配下に保持。

旧103のraw837184000byteは原本と新prefixを直接byte比較し完全一致。新3件のGPU poolはgen1/alive0/退場理由1（damage kill、graph退場2とは別）、被ダメージ1/1/1000000、最終field queryのreceived=0。最終graphはinactiveです。追加診断で最終graphのactiveを誤って要求した失敗を保持し、死亡瞬間のactiveはCPU witness、GPUは保存されたdamage-kill reasonという証明範囲へ訂正しました。既存native/GPU比較器に差分や変更はありません。frame別visibilityとkill時graphのGPU直接traceは未実装です。

全reader終了後、SHA/size/inode保持疎化で688259072byte回収。raw861568000byte/SHA6323e3ba…とclaimは保持。全キャプチャは永続領域です。一時領域で消失した旧99原本の復元とは区別します。

最終package9a30395d…はseal/readiness登録と共通Python依存チェックの8file差分。変更CLI関数はmake_package/main/cpu_test_groupsだけ、その他関数AST・全native producer/comparator/GPUを保持。最終関連123・制御525成功（Windows専用1skip）、generation必須hit/Slang0。最終版でfresh全native preflightを再実行したという主張なし。

小さな証跡はresearch/typed-owner-hp-death-gpu-evidence/と対応checkpoint。追加のstandalone数値Metal40は別証明（GPU1）、本体106はGPU1/retry0。現在sourceの全266profileと20分類も再監査し、全profile input/issue/順位を保持。245変換成功・21失敗、全キャラ認定0/UI CPUのままです。次は既存の共通world契約を公開consumerと残るmodel gapへ接続し、現在本体のCUDA成立を進めます。
