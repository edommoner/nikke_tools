# 親通知の固定割合ダメージ

`dealt_fixed_damage` を共有Slangのprivate world入口へ接続した。CUDA/Metalは同じ実装・入力表・正本比較器を使用する。現在の実行証拠はApple M5 Metalのみ。全キャラ認証、一般worldへの受付、UI GPU切替は未完了。

## 計算と状態

親通知の `dealt` を一時的なFrameの `notifyDealt` に保持し、`dealt * value / 100` を既存software binary64の順序で計算して整数へ切り捨てる。負値とゼロは生成せず、正の1未満は整数0のpacketを生成する。ATK、通常の倍率、named skill倍率、hit生成、gaugeを二重適用しない。既存typed LandingReceiptへ流し、対象選択・着弾・HP・吸血処理を再利用する。

full_charge_hitは丸め済みペレットダメージ×pelletsを各muzzleの通知量に渡す。通知外は0。入れ子の通知は別Frameで0から開始し、復帰後は親Frameの量を保持する。Runtimeの全フィールド配置とstride138952は変更していない。新quantityMask bit24とdamage flag262144は別の名前空間である。

## 証拠

共通CLIの `parent-fixed` は正本23契約と不正入力7件、`parent-fixed-retention` は既存291を加えた321入力。割合0/負/100、端数0packet、散弾/複数muzzle、owner4、boss/target/all-enemies、通知欠如、回数制限、間引き、重複、条件不成立、二重倍率除外、入れ子、吸血、非full charge、大きい整数を含む。全battle/skill traceを正本と比較する。広い武器混在・部位・aimed・実エミリア編成の認証は残件。

固定package c36b3664c9299b3bead1ed6f1a884469017fee2980ac80786b041dd8bde66748 でMetal321（正本241、拒否80）が成功し、保存結果の独立sealも成功。旧291の入力・正本・全915406848出力バイトを保持。CPU29群203検査、67.906秒、正本19.685秒、GPU4.451秒。生成cache必須hit、実run追加Slang0。後続の分類metadata変更は対象21検査で確認した。

詳細は `research/portable-parent-fixed-checkpoint.json` と `research/parent-fixed-evidence/`。短い30入力goldenは独立監査済み321出力の末尾から導出し、adapterの入力バイト・名称と照合した。追加GPU実行なし。raw、claim、不変packageは/tmpの元パスに保持しGitには含めない。

## 失敗と修正

v2はpackageに公開upstream docs/IMPL-STATUS.mdが欠け、CPU事前検査で停止（GPU0）。明示的な `upstream_documents` の公開docs許可リストを導入した。v3はMetalの新23件が不一致。新規fixtureのpost_fire_delays=0が正本の静的SR待機.215と異なった。途中候補.2もCPUの静的正本検査で検出しGPUを起動していない。v5は入力だけを.215へ修正し成功。v3→v5のGPUソース・全321正本期待値は同じで、旧291入力も同じ。失敗raw・報告・claimは保持している。GPU差分を期待値の書換えで隠していない。

## 未対応の整理

`consumer-audit --out <new.json>` はGPU・battleを起動せず、pinned正本AST、明示的未実装表、実呼出し元を確認する。projectile_dmg_pct/shield_dmg_pctとall_projectilesの早期return、multi_hit listenerのbattle producer欠如をreference_model_gapへ分類した。歴史文書の内容は証拠として扱う。

静的packingは240/266、base180/203。残分類35→34だが全キャラ対応の証拠ではない。次のmax_ammo_countによるcharge_dmg_pct scalingは、対象者のlive容量参照と再帰guardを正本sourceで確認しただけで契約0件。native_contract_extensionへ分類し、正本契約の追加から進める。現CUDAは未検証。Windows追加操作0。以前の7プロセス終了原因はunknown、環境保全falseを維持し、ゲーム・動画との因果関係は断定しない。
