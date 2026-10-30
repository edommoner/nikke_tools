# 通常製品APIの共通GPU経路

対象別倍率とmulti-hitを別のメンバーが持つplain BODY編成も、元carrierとgroup通知を
保持して共通実行器へ渡す。Sakura/Belorta/Miranda/Dora/Drakeの30秒は通常APIから
M5で全CPU応答一致を確認した。axis表は別suffixへ保持し、GPUでもBODY1体の世界を
検査する。modifier自身がmulti-hitをlistenする場合や追加actor/typed対象は未対応。
`product-group-target-v1.json` が小証跡で、Metal255 profileとは別の追加編成確認である。

通常の `/api/jobs` に `compute_backend: metal_detail` またはWindows用の
`compute_backend: cuda_shared_detail` を渡すと、既存の
`engine_worker.evaluate(..., _portable_static_inputs=True)` で入力を準備し、
`app/portable_detail.py` が共通Slang実行器へ接続する。静的準備ではCPU戦闘を
実行しない。元の育成・武器・効果定義を保持し、実際のmulti_hit listenerの有無に
応じて既存の通常／attack-group wireを選ぶ。

GPU読戻しの後にCPU戦闘を実行し、`compute` 以外の全製品レスポンスを完全比較する。
不一致、入力拒否、未接続設定は理由付きでCPUへフォールバックする。
この段階ではGPU単独の速度改善を主張しない。

共通CUDAは既存legacy `cuda_detail` とは別の受付名だが、Metalと同じ入力準備・
計算本体・製品変換・全CPU照合を使う。Windowsで
`NIKKE_SLANG_GENERATION_CACHE` と `NIKKE_CUDA_COMPILE_CACHE` の絶対ディレクトリが
必要。通常要求ではpaired生成とCUBIN/O1のcache hitを必須とし、missならcold compileを
行わずCPUへ切り替える。`/api/hardware` の `shared_cuda.available` は設定の存在であり、
GPU成功の証拠ではない。CUDA時間はlaunch/syncを含む `host_dispatch_seconds` で返す。

`compute.capture_id` は保存ディレクトリに対応し、記録の `request_sha256` と合わせて
元要求とreadbackを結ぶ。共有時にrawバッファや個人設定を含めない。
接続変更後のM5要求は全CPU一致、CUDAのMac要求はOS理由付きCPU fallbackを確認した。
製品Metal255 profileの既存証拠は計算関数とshader不変で保持、実CUDA製品確認は0。
`shared-cuda-product-route-v1.json` が現接続の小証跡。CUDA成功unitのmockを
実GPU確認へ数えない。

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

## 対象別carrierと単一本体の接続

`product-target-modifiers-metal-v1.json` に、対象別補正7profileとEleggの
計8profileの通常API・実Metal・CPU全項目一致を記録した。履歴を通じた成功は
255/266、現ソース全266の回帰は別途必要。静的入力成功255と製品検証件数を混同しない。

元補正は数値を持つkind4 carrierと既存typed axis表へ格納する。本体しかいない
世界ではtypedの係数を本体へ足さず、本体の既存ダメージ・吸血・貫通経路を使う。
空対象の受付は専用製品entryだけの明示フラグで、slot表の予約領域も検査する。
対象がある場合は同じshader内の既存typed消費器を使用する。既存宣言モデルの
飛翔体、HP shield、武器HP shield、散弾hit shieldの4正例と6不正入力を実Metalで
確認した。これを実ゲームのtyped対象規則や製品での敵履歴対応の完成とは扱わない。

nearby selectorは論理敵がBODY1体のときだけ本体へ静的に解決する。
追加actor・parts・座標があれば拒否し、距離や近隣順序を推測しない。probe入力と
製品入力はこの証明を共有する。元effectsは保持し、元selectorもmetadataへ記録する。

Claudeレビューから予約領域検査と対象なし分岐の統一を反映した。既存CPU検査は
24成功、歴史的source固定検査1件は共有runtime変更により失敗中。この旧証明は
現在の数値証明ではない。旧期待hashを変更して成功扱いにしていない。
前回repair-v4のgroup出所誤関連はsource/input/outputの一致で訂正し、元版もGitに残す。

## 現行ソースの全266件確認と既存出力の保持

`product-profile-progress-v5.json` は、c5d9402cの全266件の通常API確認を記録する。
Metal255件は全CPU製品応答一致、11件は理由付きCPU fallback。数値差・API errorは0。
同一コード／入力の8件は既存API cacheを再利用した。保存255件は入力を再packingし、
元APIと同じCPU payloadに結び付くreadbackから完全再生して確認した。archive replay
では元実行のprovenance stampを保持し、数値や期待値を変更しない。

従来の固定source証明が新しい共有runtimeを拒否する点は、旧証明の書換えで解決しない。
既存141ケースの全input/outputを現在の共有kernelで保持検証し、元goldenの全591MBと
全byte一致した。既存の対象テストはこの現source＋全旧vector保持receiptを検査する。
旧goldenと旧source証明は不変。新しい小suiteや逆投影certificateは追加していない。

全profileの標準条件の結果であり、全編成・全設定・全特殊効果の完成ではない。
SakuraとBelortaを同じ実5人編成へ入れると、modifier＋multi_hitのwire合成が未接続で
CPUへ切り替わる。固定ゲージ・boss/parts履歴・手動操作と共通CUDAの製品接続も残る。
共通CUDA実機の製品確認は依然0件。Windowsの今回の作業はcache metadata読取のみ。
