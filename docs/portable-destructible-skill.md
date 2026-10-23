# 元の弾対象効果から共通ダメージ計算への接続

`destructible-skill` は、元の`all_projectiles`効果定義を既存のスカラーdamage rowへ下げ、既存`damageValue`の7段計算・整数丸めを通してから、生存弾の選択と既存着弾/counter/同期子イベント実行器へ渡す。CUDA/Metalは同じSlang本体を使う。新しいダメージ式や数値層を実装していない。

`app/destructible_skill_specs.py` はplain `damage`だけを扱い、既存`_get_skill_lv`で元のvaluesを選ぶ。名前・source・triggerを保持し、スカラーrowのtargetをbossへ下げる。このrowは弾の攻撃対象を本体へ置換するものではなく、計算済み量はtyped projectile producerにだけ渡す。未定義のscaling/parts/normal_attack等は削除せず拒否する。元のcounter Actor種別・ID・世代も維持し、carrierを既存world-skill用のboss sentinel routeへ置く。初期化は既存world-skill ABI/mode7・時計終了到達コマンドを使用する。

CPU側は既存`calc_damage(expected=True)`と`BuffManager.get_buffs`を使い、GPUは既存のcompiled Definition・`namedDamageCoefficient`・`damageValue`を使う。呼出し側が明示する共有スカラー対象context（DEF等）で量を1回計算し、全着弾へ固定する。最初のcounter子でATKが増えても、同じ攻撃の2本目を再計算しない。係数0は最小1ダメージ計算やhit credit生成に入る前に終了する。

元データのスノーホワイト：ヘビーアームズ`세븐스 드워프 풀 액티브 4`（parsed_skills index24）を変更せず使う。ATK1000の宣言contextでlevel1=24.76%から266、level10=41.9%から450、full burstで660、DEF100では405。これは元の1定義を用いた8入力と、係数0/丸め境界の合成2入力であり、元キャラの全定義・武器・バースト時系列を再現した証拠ではない。その他、ATK/damage/critical buff、失効、空集合、元attack_id、全typed状態・既存時計・全counter trace・epoch・credit・子ATKを照合する。

Apple M5のMetal18（正例10/拒否8）がCPUと全件一致、独立seal成功。GPU0.026898秒、readback56,623,104バイト、Runtime163528バイト、source閉包128。成功package `d780cfaa2f1330d4762afb57db779f9cb33ebeca66a0bcf31cd90538c65d69cd`、capture `/tmp/nikke-ds-metal18-v6`。最終固定packageは`d34d72ec990cf8cfe7dc87424166d6380dbbcba2ed47de7dd3e52dcbd4d2eae4`。最終CPU46検査/native10は成功。保存8blockの故障注入で係数・計算量・Actor世代・選択件数・子ATK・拒否statusの破損を検出する。以前のproducer15入力の全input/native指紋も保持した。

最終CPU v7の旧基準JSON梱包漏れはsupport_filesへ明示追加して修正し、失敗記録を保持した。GPU再実行なし。初期5つの失敗captureは保持した。literal counterのkind3拒否、world時計through未到達、診断有効化、counter carrier route不一致を特定し、host変換を既存契約へ合わせた。通過後の差分は古いfixtureに残ったDEF100と、生成MSLから消えた一時phase代入だった。DEFを宣言入力へ明示し0/100を両方比較。phaseは一時的に差し替えて戻さず、呼出し側フレームが保持し、helperが一致を検査する。既存ソフトbinary64・数値期待値・厳密normalizer・正本を緩めていない。各固定packageの実行claimを保持し、同じclaimの再試行はしていない。

公開の通常戦闘受付は依然拒否する。worldの敵弾生成元、通常burst/skill Frameからの自動dispatch、弾個別のDEF/敵debuff、`projectile_dmg_pct`/shield倍率、盾迎撃・破壊固有效果・attack group完了は残件。今回の宣言contextをゲーム仕様の完全再現と扱わない。classificationは`reference_model_gap`のまま、all_projectilesにこの限定証拠を付記した。通常UI CPU・全キャラ認定0・残20分類・全目標未達。

Windowsは今回、新GPUを実行していない。旧counter PTXの保存cacheを既存CPU-only bounded wrapperで静的分析し、1.401558秒、driver/NVRTC/GPU0。181関数すべてが入口から到達可能、582辺/1510直接call site、循環/間接呼出し/未解決symbol0。広い閉包と大きな仮想レジスタ/local宣言はdriver JIT負荷の候補だが、物理レジスタ・実行stack・コンパイラメモリやtimeout原因の証明ではない。GPU再実行やclaim操作は行わない。詳細は`research/prepared-transport-evidence/windows-ptx-static-reported-summary.json`。

次は通常skill Frameからこのtyped routeへの自動接続と、弾個別の対象context/倍率の明示モデルを整備する。CUDAは保存PTXの共通関数境界を調べ、再コンパイル・module再読込みを始める前に費用削減策を具体化する。
