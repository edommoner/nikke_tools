> 追記：名前付き敵の効果解除とアスカWILLE実編成の最新結果は[解除GPU接続](portable-named-enemy-removal.md)。以下は最初の対象選択接続の記録。

# 名前付き効果を持つ敵の共有GPU選択

`enemies_with_buff:<名前>` を既存の敵集合・名前付き状態・世代管理へ接続した。CUDA/Metal共通のSlang実装を使い、今回の実機計算はApple M5のMetalで確認した。公開入口と通常UIの受付は変えず、private / development_onlyを維持する。

23の正本契約は効果付与、bonus damage、名前付き効果の時間延長を対象とする。候補はボス先頭、生存addの誕生順で、同名効果を持つ敵を付与元によらず選ぶ。該当なしとaddなしは正本通りボスへ戻る。コロン・空白・空文字、失効、遅延wave、退場、同じidの再登場、別caster、同名union、明示解除、128敵を含む。正本契約の詳細は[先行契約](portable-named-enemy-reference.md)。

入力は非weaponの未使用MODE24..27へタグ・名前index+1・フラグ・予約0を詰める。名前は実行中の既存所持状態から読み、CPUで対象を選ばない。空文字名は「名前の指定なし」と区別するタグを持つ。route11はprivate actor-pool入口だけで有効とし、combat/world/actor state・タグ・名前容量・フラグ・予約語を検査する。定義番号は付与、変異、直接着弾、周期スナップショットの既存集合取得へ渡す。Runtime構造、stride138952、入出力容量、binary64、整数/pow、normalizer、正本計算器は変更していない。

固定package `0c10abfb3a62068db21bfb3cb68ffb13ac836378e7bf3572d24d0dc3b95143e1` の207入力はMetalと独立sealに成功した。native155、拒否52で、新規はnative23と不正9。以前の175入力のinput/native/output指紋を保持し、出力550,502,400バイト全体のSHAも一致した。

診断package `261750db1e75ac13569f6e8ca850e2dd0254630c206eace5f49e020aaf6dcb94` もMetal23・独立sealに成功した。各3発の全69対象マスクをliteral正本契約と比較した。診断は既存の復活trace領域を専用入力でのみ使用し、味方random/復活との衝突を拒否する。通常実行と診断実行の領域外72,257,444バイトは同一で、入力・Runtimeを増やしていない。

初回207と診断23は追加ダメージ4件がstatus64で失敗した。直接スキル着弾が定義番号を渡さず、名前を引けなかった。全定義依存の集合取得へ番号を渡し、呼び出し箇所の検査を追加した。失敗/raw/claimを保存し、ソース修正版を別の固定packageで検証した。旧失敗を上書き・成功扱いしていない。

CPU事前検査は17群135検査、skip0、28.256秒。native事前比較は12.033秒。Metal計算4.317秒、MSL library1.434秒、pipeline8.333秒で、生成cache必須hit・実行時Slang0。SlangによるCUDA/MSLの事前生成と、実際のCUDA計算の確認は分ける。独立sealと保存結果の照合はGPU0で行った。

実行前は230入力分の非圧縮input/readbackと14GiBの予約を見積もった。過去の完了済み出力のゼロ領域を疎化し、全バイト・SHA・path・inodeを保持した。削除や圧縮率の見込みで容量を満たしていない。実施receiptをevidenceに保存した。

静的受付は238/266、base178/203、残分類39。旧237プロフィールの記録・入力SHAは全保持し、サクラ：ブルームインサマーの入力受付が増えた。これを全プロフィールのGPU実戦確認へ加算しない。名前付き敵へのremove_named_buffは引き続き拒否し、次の正本契約にする。sequential/ref/scaling/budget/passive、interrupt/部位の混在、原実編成、全カタログ、現CUDAは残件。全キャラ認定0、通常UI CPU、全体目標未達。

Windowsの追加操作は0。7プロセス終了の原因は未確定、保全確認はfalseのまま。ユーザーは直前の終了・再起動・再接続操作を否定し、ゲームや動画を利用した可能性を報告したが、原因を示す証拠にはしない。

根拠は`research/portable-named-enemy-gpu-checkpoint.json`、`research/named-enemy-gpu-evidence/`、両suiteのexpected JSON。CLIは `package --suite named-enemy-retention --develop --out <new.zip>` または `named-enemy-diagnostic` で固定し、展開先をcwdにしてCPU事前検査→`generation --develop`→生成cache必須の実行→保存結果sealを行う。
