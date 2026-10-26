# 宣言されたADD所有者へのCPU接続

`reference --suite coordinate-typed-logical-owner-common --out NEW.json` はCPU専用の3契約です。明示 `logical-owned-current-fields-v1` に限り、projectile／HP shieldの直接の所有者をBODYまたはADDの完全handleで解決します。旧 `body-owned-current-fields-v1` のBODY必須・旧拒否条件は保持します。ゲーム仕様の認定ではありません。

型付き対象は独自レジストリを使っていたため、最初の実戦契約はUnknown world actor handleで失敗しました。新policyだけ、既存戦闘の `registry_for(manager, world.clock)` へ型付きproviderを登録し、同じregistryを共有します。ADDをlabelから推測したり、別schedulerを作ったり、HP／世代をコピーしません。直接宣言されたownerを `registry.exact` で確認し、物理event／命中handleは保持します。型付き対象・所有ADDが同世代で死んでいても所有関係は保持します。未知・未spawn・再出現による古いADD世代は拒否します。rootをたどる暗黙継承やBODY fallbackはありません。

元Primの完全5人・全71定義・武器・成長を保持し、別宣言のcounter marker／子fieldだけを追加した8秒の3ケースです。HP shield、projectile、破壊直後のHP shieldで実射撃→counter完了→`target_is_add`→子fieldを確認します。所有者はADD1 `[5,1,1]`。通常の元スキルfieldはcanonicalのADD0へ届く一方、子fieldは宣言所有者ADD1へ届きます。BODY／ADD0／ADD1のreceived_dmg_pctは `0／0／17`、physical kind/id/generationは維持します。

不変CPU v3 `/tmp/nikke-logical-owner-cpu-v3` で新3契約29.037947秒、旧BODY5契約39.236259秒、旧寿命・世代8契約72.773368秒で成功しました。旧BODYは前の不変snapshotからfresh取得した5件、旧寿命・世代は既存の全8件と、input/native/traceの全SHAが一致します。GPU／packing呼び出し0。

最終不変 `/tmp/nikke-logical-owner-cpu-v4` のIDは `8183df991f5ca4d1ab569fd11d72dbc7af6d86914cef7ec45757e94306db4f70`。v3との違いはregistry attachment単体テストの初期fixture1ファイルだけです。実構成はtyped-only registryから始まるため、その状態を再現するよう修正しました。失敗v1／v3の記録は保持しています。全native producer・比較器はv3と完全一致、最終版のnative再生成はありません。最終関連19group113検査、制御53group517検査成功（Windows専用1skip）。Slang／upstream／正本／数値／transport／CUDA compile cacheは前のMetal88から全byte保持し、generation必須hit・Slang0も確認しました。このhitはADD所有者のGPU対応を証明しません。

証跡は `research/typed-logical-owner-reference-evidence/`、checkpointは `research/portable-coordinate-typed-logical-owner-reference-checkpoint.json`。共通CLIの `reference` に登録し、readinessにはCPUのみの証拠を追加しました。既存GPU compilerは新policyを入力準備前に明示拒否します。旧GPUへの誤受付を防ぐ負例もあります。

次は共有Slangの所有者resolverをexact actor-pool slot／generationへ接続し、counter条件のADD判定とfield recipientが同じownerを使うようにします。wire policyは旧BODY専用flagと区別し、未宣言／不正ownerを拒否する必要があります。旧88を削減せず、既存validator・source監査を維持して新しいMetal全件fresh監査へ進めます。ADD所有者のMetal／CUDA、dead ADDの実戦field lifetime、再登場ADDの戦闘契約、ゲーム仕様／公開consumer／全キャラは未完です。Windows依頼0、GPU0、全キャラ認定0／UI CPU／目標未達です。
