# 元武器と発射体ダメージ補正の接続

`original-projectile-weapons`は、既存の`world_coordinate_typed_owner_entry.slang`へ元のサクラ・アンカー・クレイの実編成を渡す共通CUDA/Metal suite。元効果、owner順、武器、育成、configを保持する。追加の模擬damage効果やCPUで作った発火scheduleは入れない。従来の`original-modifier-probe`の追加攻撃実証と、`coordinate-typed-weapon`のサクラ3秒実証を全キャラ対応と混同せず、元武器の長時間条件へ範囲を広げる。

正例8件はサクラ3/30秒、アンカー3/30秒、クレイ3/12/30秒、サクラ3秒の発射体未出現対照。対象は宣言したkind2のtyped発射体2個で、物理handleとlogical BODY ownerを区別する。自動照準は既存の`typed-before-body-v1`、現在敵fieldの所有は明示的な`body-owned-current-fields-v1`を使う。形状/生存/生成/照準/弾丸RNG/物理packet/着弾/補正は既存consumerが実行する。原定義にあるcurrent-enemy fieldを消してpackingを通さない。

CPUの意味契約は、サクラの7.74%が全5人、アンカーの25.6%が本人だけ、クレイの45.05%が元attack-count/full-burst条件で全5人へ発動すること。クレイ3秒は補正0、30秒では20秒以降の失効も検査する。固定seed/実編成における条件であり、全育成・全条件の規則を認定したものではない。30秒クレイの2,186着弾は、既存物理streamの先頭2,048件保持に加えた**全件SHA256**比較を実際に通す。skill用`max_attacks=128`は物理streamの削減上限ではない。

raw拒否5件はowner marker、actor policy、owner generation、無効modifier axis、未使用定義のaxis。入力115680/output2032000wordの既存wireを維持し、全battle/乱数/照準stream/typed state/物理receipt/予約領域を従来比較器で比較する。補正用axisは元statをpacking時に下ろすだけで、原効果dictは不変。1つのlive run内のnative値再利用には既存`ParentOracles`とcreation-index contextを使い、別fresh sealのCPU再計算は省かない。

固定540142c4/package7fa83104…の13入力はApple M5 Metal全比較とfresh GPU禁止の独立sealに成功。58unit、fresh native事前照合81.06秒、実GPU3.04524秒、初回pipeline62.10秒、独立照合97.21秒。live run内だけ8native/creation-index contextを再利用し、比較時の重複CPU battleは0。独立sealは全nativeを新たに計算する。GPU1回/retry0、既存GPU406ファイルは前checkpointから全byte不変。証跡は `research/target-count-query-evidence/metal-original-projectile-weapons-v1.json`。

共通CLIの通常`package --suite original-projectile-weapons`はsealed goldenを使う。`original-projectile-weapons-cache-only`は同じscript/source/golden/input/nativeをCUBIN/O1必須とpaired generation必須へ接続し、cache不在をcold compileへfallbackしない。Windowsへの新規依頼は0、既存status取得はhost unavailableで再送していない。実CUDA/CUBIN hitは未検証。今回の生成のみ事前準備はSlang2回・GPU0、その後の実行は必須generation hitでSlang0。作成済みMetal archiveのfile-only probeも成功したが、これを実warm run成功へ読み替えない。

最終登録e704391dのcache package eff7ddd9…は`unit-check`10群91テスト（3.87秒）に成功し、CUBIN/O1/2GiB/60秒の`compile-plan`も受理された。compile/GPUは0。Metal packageとの全payload差分はreadiness分類・CLI登録・単体テスト・sealed goldenの4ファイルだけで、全CLI関数のASTと全numeric/packing/native/比較ソース、全input/native期待は一致するため、変更のないfull native sweepは重ねない。fresh inventoryは266中245packing/21失敗、全キャラ0/UI CPUを保持し、元武器実証のscopeが分類へ現れることを確認した。最終証跡は `research/target-count-query-evidence/original-projectile-weapons-final-checks-v1.json`。

本scopeは宣言したtyped worldでの元武器接続。Eleggの`target_and_nearby:2`、canonical target-world、ゲーム実機との一致、全キャラ認定、公開GPU受付は未完了。距離規則のネット調査待ちで他の対応を止めない。今回GPU sourceを変更していないことは、過去の全suiteを現在sourceでGPU再認定した証明ではない。
