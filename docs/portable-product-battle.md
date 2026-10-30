# 通常製品APIの共通GPU経路

通常の `/api/jobs` に `compute_backend: metal_detail` を渡すと、既存の
`engine_worker.evaluate(..., _portable_static_inputs=True)` で入力を準備し、
`app/portable_detail.py` が共通Slang実行器へ接続する。静的準備ではCPU戦闘を
実行しない。元の育成・武器・効果定義を保持し、実際のmulti_hit listenerの有無に
応じて既存の通常／attack-group wireを選ぶ。

GPU読戻しの後にCPU戦闘を実行し、`compute` 以外の全製品レスポンスを完全比較する。
不一致、入力拒否、未接続設定は理由付きでCPUへフォールバックする。
この段階ではGPU単独の速度改善を主張しない。

## 最初の全profile確認

`research/target-count-query-evidence/product-profile-progress-v3.json` は、
元266 favorite-stage profileを通常APIで確認した記録。30秒・既定育成・cubeなしの
固定条件で239件がMetal実行・CPU全項目一致、27件がCPUへ切り替わった。
240件の最後のsweepはapp/GPU/依存データの変更なしを確認した。
残り26件は同記録が参照する以前の製品API結果である。

内訳は入力／モデル不足19、GPU入力拒否5、数値と警告の差1、警告のみの差2。
これは当時のソースに対する証拠であり、後続修正の全件回帰を代替しない。
CUDA製品経路の一致確認は0件。全キャラ・全効果・全設定の完成ではない。

## 修正で守る境界

- モデルの注意書きは、元のBuffManager構築時に得る静的メタデータを引き継ぐ。
  GPU後のCPU結果から注意書きをコピーして比較を通さない。
- 段階的DOTのscopeとシールド条件は既存の共通実装を製品入口から有効化する。
  数値式や元効果を変更しない。
- 配置・回復元の条件も既存のbasicConditionsを使用する。受付追加は予約引数0を
  検査し、条件の省略／常時成立への置換はしない。
- 通常入口にも既存のprojectile admission診断を有効にし、失敗の読戻しを保存する。
- 失敗入力／GPU読戻し／CPU結果はpersistent proofsへ保持する。rawはGit共有しない。

固定ゲージ、敵パターン／パーツ、手動操作の製品結果変換は未接続。
これらと19件の入力／モデル不足を、標準profileの通過で対応済みにはしない。

## 8件の修正後の確認

`product-profile-repair-v4.json` に、同一現行ソースでの8修正profileと
Miranda／Belortaの計10profileの実Metal・全CPUレスポンス一致を記録した。
別途Rougeのslot0/1/3も一致。関連CPUテスト75件成功。
共有ソースの変更があるため、旧source certificateや239件の旧成功は当時の証拠を
保持し、現ソース全266件の回帰として読み替えない。履歴を通じた成功247/266と、
現ソースでの確認10件を分ける。Windowsへの追加実行依頼は0件。

次はprojectile_dmg_pctとshield_dmg_pctの既存typed modifier接続を優先する。
通常のbodyだけでは有効対象がなくても、carrier状態や対象別axisを省略しない。
対象が存在する対照も必要であり、標準profileだけの数値一致で効果完成とはしない。
