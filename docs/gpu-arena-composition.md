# 座標を主実行器へ統合する前のarena確認

現在の座標入口と、実射撃groupを持つ主入口は別profileで実証している。同じRuntimeを使うが、単純に両機能フラグを同時有効化すると出力arenaが重なる。静的な宣言の確認であり、現在の入口で衝突が発生したという実行結果ではない。

| 所有者 | word範囲（終端を含まない） | 根拠 |
| --- | --- | --- |
| 実射撃group | 800000–1048576 | `gpu/attack_group_runtime.slang`のAG_HEADERとcompact終端 |
| 座標packet | 786432–1043608 | Python生成の`coordinate_packet_layout.slang` |
| 同時利用時の重複 | 800000–1043608 | 243608word |

次の優先作業は、共通CLIのlayout合成検査と、両profileの定数を同じ生成schemaへ接続すること。その後、旧profileを保持した合成profileで出力stride・decoder・容量検査を一緒に更新し、主入口へ接続する。必要な領域は増やして確保し、既存の対象数・trace数・検証入力を黙って縮めない。候補として座標arenaを既存1Mword領域の後ろへ置けるが、最終strideは実装時に保存量・GPUメモリとともに検証する。

対象の世代規約も統一対象と混同しない。座標スキルHitEventは対象名を保持し、着弾時に現在世代へ解決する。一方、実射撃groupのActorHandle集合は世代を固定し、`agCapture`は不在・旧世代を除外する。共通のActor poolを使っても、producerの意味に従う明示的な解決方式を保持する。group側を一律に再出現対象へ振り替えてはならない。

この合成は未実装。source hashを含む確認記録は`research/coordinate-generation-evidence/arena-composition-finding.json`。座標物理弾・手動aim・元定義の混合world・公開受付も別途必要であり、private suiteの成功から全キャラ対応を主張しない。
