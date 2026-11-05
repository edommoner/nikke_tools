# 乱数射撃groupと武器skill指定

`coordinate-sampled-delivery` は、武器変更の `skill_damage` 指定と、乱数射撃からのBODY／ADD receipt groupを同じ共通実行器で検証するprivate profile。固定136入力（共通CPU正本126／拒否10）が保存Metal出力のGPU禁止replay・独立sealで全一致した。GPU／compiler／transport本体と効果IRは変更せず、`coordinate-sampled-vital` と同じSlang入口を使う。全キャラ元定義の認定・公開GPU受付・現在ソースのCUDA実行は未確認。

## 共通経路と正本契約

新14世界は武器skill指定のauto／charge＋親量／初弾倍率／吸血と、groupのBODY／PART混在／前面PARTのみ／散弾・総口／charge＋親量／2射手／ADD生存・途中退場／次shotへのbuff／skill射撃の除外を含む。既存効果定義・mode flag・group eventを使用し、同じ入力・比較器をCUDA／Metalで使用する。

正本の実射撃時のpellet・総口・係数・skill flagを受動観測する。groupは実着弾のBODY／ADD receiptに所有され、PARTは独立した敵として数えない。子の対象handleはgroup終了時の順序・identity・generationを保持し、後から退場したADDを蘇らせたりBODYへ割り直したりしない。skill指定のmode射撃は通常攻撃groupを作らない。ADD退場は3ペレット×2総口の実射撃で、同shot中のADD0→ADD1→BODYを観測する。

新14世界で物理288ペレット／670packet、MT1700word、mode70射撃、group68、receipt207、通知69、子61を検査した。group履歴の既存比較を共通helperへ分離し、全packet・乱数・battle状態は既存sampled比較器で照合する。旧比較器のpacket比較は既定で有効なまま。新経路は同じ強いpacket比較をparentへ委ね、group履歴部分だけを再利用する。ADDの実着弾labelを既存の受動観測器から取得し、全labelが一意なtyped bindingに対応することを必須にした。

Runtime138952byte、入力109528／出力1769472word、既存の全容量は不変。新GPUソース・計算式・効果IR・数値演算・normalizerの変更は0。今回の14世界は全weapon flagや全混合効果の認定ではない。

## キャッシュと実機

生成cache必須でCUDA／MSLの両方がhit、Slang呼出0。生成物は前回vitalと全byte同一で、既存12系統の生成証拠も全source identityを保持した。compiler／transport本体も不変であり、CUDA compile cacheのsource成分を変更しない。現在のCUDA compile/cache hit/実行を確認したという意味ではない。

Metalもnative archive hitを必須にして実行し、実hitを確認した。同じsource・consumer・device／OS・entryのPSO準備は、前回cold91.957517秒→今回0.002588秒。GPU0.480263秒、子プロセス3.491428秒。入力は増えているためGPU性能の比較実験ではない。実GPUは1回、同claim retry0。4sourceの独立整数ratio証拠14045入力も現在のままで、数値GPUは再実行しない。

## 停止・観測器修正と独立監査

準備中の3停止を保持した。CPU既定60秒は79検査成功後に停止したため、このsuiteだけ既存の設定機構でCPU予算120秒とした。GPUの180秒上限・全検査は維持する。次に関連テスト用group基準JSONの同梱漏れを検出し、明示同梱へ修正した。CPU94検査と全入力事前検査が通った後、容量の最終ゲートにも停止した。いずれもGPU claim取得前でGPU0。

空き容量を全byte／SHA／inode保持の疎化で確保した後、同じ固定packageから初回GPUを実行した。GPU処理自体は成功したが、比較器の外側のprofile hookがmodule準備中に `timeline.calc_damage` を参照して例外になった。観測開始時のcode identityを保持する修正を加え、実group scope初期化を通る回帰テストを追加した。元の失敗・GPU raw・claimを保持し、新固定host packageでGPU禁止replayした結果、136/136一致・独立sealに成功した。期待値・計算本体・許容誤差・生成物は変更しない。

旧120入力のinput／native fingerprintと全849346560byteを保持した。compiler source証明書も独立再監査で登録したが、CUDA compiler成功／cache hitの証明とは分ける。保護7source・core probabilityは不変。raw削除0、Windows新依頼0。

## 共通CLIの改善

`package --suite coordinate-sampled-delivery --compact` と `reference --suite coordinate-sampled-delivery-common` を登録した。最終CPU95検査、制御428検査（Windows専用1件skip）、GPU／packing禁止の共通正本14契約が成功した。full3152→compact1811は残存全record／byteが同一。

`metal-cache-probe` はsource／consumer／record／archiveの指紋を読取専用で点検する。5負例・境界検査と実cacheのsnapshotに成功したが、現在のdevice／OS・GPU計算の証拠にはしない。実起動のnative archive再検証は必須。[キャッシュ事前点検](portable-metal-cache-probe.md)を参照する。CUDAは既存の `cache-probe`／厳密なcompile keyを維持した。

CPU監査データはパッケージ作成時にも `AUDIT_FILES` と同梱一覧を照合し、不足は入力準備・archive作成前に拒否する。故障注入で早期停止を確認した。容量の開始前見積もりには準備用64MiBを追加し、CPU後の最終1GiB予備検査も維持した。今回の僅差不足をCPU前に検出する負例が成功し、workloadの削減やreserveの緩和はない。

詳細は `research/portable-coordinate-sampled-delivery-checkpoint.json` と `research/coordinate-sampled-delivery-v1-evidence/inventory.json`。次は手動cover/controlのpacking、追加武器flagとburst／回復保存／instantの混合、actor payload、全キャラ元定義へ進む。全キャラ認定0／20model gap／UI CPU／public GPU closed／full goal falseを維持する。
