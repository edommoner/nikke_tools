# arena配置の共通化と共通実行器への接続

現在は`combined-v1`をprivate合成入口`coordinate-composed`へ接続済み。座標skill／保留／世代交代とbody-only実射撃groupを同じGPU常駐Runtimeで実行し、Metal97入力を独立監査でsealした。入力108648word・出力1310720wordをbackendとdecoderまで接続し、全容量を保持する。`arena-check`自身は静的監査であり、計算の証明は別の実GPU記録による。[合成実行器の設計・範囲](portable-arena-composed-executor.md)を参照。

以下は接続前の問題の記録。旧配置を単純結合すると重複するという検出結果は保持する。

現在の座標入口と、実射撃groupを持つ主入口は別profileで実証している。同じRuntimeを使うが、単純に両機能フラグを同時有効化すると出力arenaが重なる。静的な宣言の確認であり、現在の入口で衝突が発生したという実行結果ではない。

| 所有者 | word範囲（終端を含まない） | 根拠 |
| --- | --- | --- |
| 実射撃group | 800000–1048576 | `gpu/attack_group_runtime.slang`のAG_HEADERとcompact終端 |
| 座標packet | 786432–1043608 | Python生成の`coordinate_packet_layout.slang` |
| 同時利用時の重複 | 800000–1043608 | 243608word |

共通schemaは`app/portable_arena_specs.py`へ実装した。座標packetのPython schemaと実射撃groupのhost定数はここを参照する。既存Slangの宣言はbyte不変で保持し、schemaから生成した宣言との完全一致を検査する。共有resident領域は既存の`portable_scratch_layout.audit_sources`を再利用し、入力位置・出力位置・初期化範囲も実consumerへ照合する。

## 共通CLIでの合成検査

```sh
python scripts/nikke_gpu.py arena-check --profile coordinate --out /tmp/coordinate-arena.json
python scripts/nikke_gpu.py arena-check --profile attack-group --out /tmp/attack-group-arena.json
python scripts/nikke_gpu.py arena-check --profile combined-legacy --out /tmp/unsafe-arena.json
python scripts/nikke_gpu.py arena-check --profile combined-v1 --out /tmp/planned-arena.json
```

出力先は新規ファイルを使う。既存の別profileは終了0、旧配置を結合した`combined-legacy`は終了1で重複一覧を保存する。入力側は`PORTABLE_ATTACK_GROUPS`によって`P_INPUT_WORDS`が104400から104408へ増えるため、scene読取位置が8word移る。一方`CA_BASE_INPUT`は107584のままで、scene終端107592とarea開始107584が8word重なる。単純に入力末尾へpolicyを追加するだけでは解決しない。

出力側は使用bank同士の重複235096wordと、座標initializerの末尾clearがgroup compactへ重なる4968wordを検出する。上表の243608wordは予約範囲の包絡線の交差であり、未使用の隙間8512wordを含む。実際のwriter範囲とclear範囲を区別して監査する。

`combined-v1`はsceneを104408、areaを107592、座標arenaを1048576へ置く合成配置で、入力108648word・出力1310720word（1ケース5MiB）。packet2048、cast32、trace4096、選択65536word、group32・履歴64・compact186528wordはすべて保持する。生成宣言は`gpu/composed_arena_layout.slang`。合成配置のアドレス重複はないが、接続前は`runtime_connected=false`だった。現在は`true`で入口を照合するが、静的検査の終了0だけからGPU計算の完成を主張しない。

7件の制御テストを共通CPU smokeへ接続した。包含した領域が複数の短い領域へ重なる場合、隣接境界、domainの分離、stride超過、不正容量、実宣言／入力位置／clear位置の5改変、CLIの終了状態を検査する。旧88のnative75とCPU37、本体81のnative68とCPU53、共通制御413（Windows専用1skip）が成功。両suiteの入力指紋・native指紋とGPU source閉包は既存baselineに一致し、今回のGPU／Windows実行は0。詳細は`research/portable-arena-composition-checkpoint-v1.json`。

この時点の次作業だった合成入口・出力stride・backend受付・decoder・容量検査の接続は、今回実装した。接続前のbackend最大出力は1048576wordだった。現在は登録された合成入口と正確な入力形状に限り1310720wordを受け付ける。手動で上限だけを緩めない。必要な領域は増やして確保し、既存の対象数・trace数・検証入力を縮めない。

対象の世代規約も統一対象と混同しない。座標スキルHitEventは対象名を保持し、着弾時に現在世代へ解決する。一方、実射撃groupのActorHandle集合は世代を固定し、`agCapture`は不在・旧世代を除外する。共通のActor poolを使っても、producerの意味に従う明示的な解決方式を保持する。group側を一律に再出現対象へ振り替えてはならない。

初回の静的発見は`research/coordinate-generation-evidence/arena-composition-finding.json`、今回のCLI記録は`research/arena-composition-evidence-v1/`。座標物理弾・手動aim・元定義の混合world・公開受付も別途必要であり、private suiteの成功から全キャラ対応を主張しない。
