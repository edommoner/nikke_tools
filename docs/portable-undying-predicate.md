# 不屈の発動条件を共通GPUへ接続

`self_undying` を既存の共有 `liveMarker(s, owner, S_undying, when)` へ接続した。正本 `BuffManager._condition_ok` は `has_live_stat` / `_live` を使い、値やバフ名ではなく、期限・対象・実行時条件を満たすstatを調べる。被ダメージ処理と同じ共有helperを再利用し、新しいRuntime fieldや算術を追加していない。condition ID38は正本compilerの既存IDを使い、schemaを共通定義から生成する。

host/GPUはprivate combat worldの明示的な発動イベントを対象とする。hostはpassiveと不正descriptorを拒否する。GPUの通常/actor-field受付は同じ `validUndyingPredicate` を使い、name=0/arg=0とcombat contextを検査し、passive descriptorを拒否する。5sourceの厳密な逆投影ledgerで旧source境界を維持し、古い監査SHAや許容誤差は変更していない。

CPU契約は22の合成ケース＋原文全定義のマキマ3ケース。ゼロ/負の値でも生きた不屈は成立し、`undying`という名前の別statや無敵では成立しない。期限、途中付与、所有者/味方由来/対象、stack、効果順、実行時HP条件と有限付与時snapshot、短絡順、有限/永続witnessを固定した。合成は66判定/66既存live照会/38成立/66射。追加照会をせず元helperを一度だけ呼び、native全項目・物理trace・照会回数を無観測版と比較する。誤scope/順序/結果/stack/damage/ammoを拒否する故障注入を含む。

実マキマは3秒対照、30秒対照、30秒＋1秒時の本人への致死攻撃1回（atk1e12、slot固定、ignore_taunt）。原文効果は編集せず、攻撃刺激だけを追加した。CPUで不屈条件の結果は `[]` / `[false,false]` / `[true,false]`。正本の致死ヒットで発動し、最初のburstで成立、期限後の2回目では不成立となる。物理履歴は155/1398/1398、省略0。GPUは既存の全native項目・技能trace・物理履歴比較器を使う。CPU観測器の判定ログをGPU入力へ渡していない。

M5 Metal主28（native22/拒否6）、実3、旧1203が同一到達sourceで成功し、それぞれ独立fresh CPU sealも成功した。合計1234入力（native980/拒否254）。旧全entriesとraw3784310784Bが全byte一致。29旧goldenはentries/input/outputを保持し、sourceと生成指紋だけを更新した。3suiteを共通CLIの通常経路へ昇格した。旧来の物理履歴省略は残り、今回の3実入力で省略0という意味である。

主28はCPU111検査20.982秒/GPU0.044492秒、実3は同111検査20.935秒/GPU2.254064秒。旧1203はCPU事前67.249秒＋回帰75群433検査141.520秒、GPU10.966637秒。旧保持/実3は生成cache必須hitでSlang0。親は871正例を再利用、84正例をfresh計算、248入力を拒否。独立sealは再利用しない。full116/commands117 certificate14検査と正式CPU packageの111検査も成功した。CUDAは同じSlangから生成するが、今回のWindows実行/NVRTC cache hitの証拠ではない。

初回主v1はhelper挿入位置が既存命中率source監査の区切りを壊し、GPU前停止。helperを末尾へ移し、監査やnative期待値を変えずv2で成功。旧保持v1は未対応self_undying拒否という古い診断fixtureでGPU前停止。未知のself_future_markerに置き換えて診断検査を保ち、GPU/native/入力は不変のv2で成功。両失敗package/ログ/入力を保持し、claim削除や同一claimの再実行は0。

容量は通常rawの全byte/SHA/path/inodeを維持する `sparsify-raw` で確保した。未圧縮input502372804B＋output3784310784B＋14GiB予備を実際の空きで確認してから実行した。今回の3rawで割当7360544768Bを回収、原文設定/証拠/claimsの削除0。詳細はdocs/portable-sparse-raw.md。

静的packing227/266、base167/203、未対応68分類（consumer研究4/model gap3/review61）はGPU認定ではない。接続済み不屈/命中率条件の古い診断は未実装候補に戻さず、文脈/passive/不正入力の確認へ回す。全キャラ認定0、UI CPU、全目標未達。Windows追加操作0、7終了原因unknown・環境保全falseを維持する。次は共通状態を使う未対応条件をまとめて契約化し、保持検証を集約する。指紋・package・transport・失敗・範囲はresearch/portable-undying-predicate-checkpoint.jsonを参照。
