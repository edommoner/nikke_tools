# 2026-11-01 通常画面で宣言モデルを適用しMetal/CPU一致

「詳細条件 → 部隊の宣言モデル」でreference_modelsと任意のenemy.patternsをJSON指定し、選択した部隊だけで計算できる。画面/結果に実ゲーム未確認の仮定であることを表示する。育成・編成の上書きや他部隊への流用を防ぎ、宣言変更/解除は計算済み表示も無効にする。保存JSONは両scopeを保持する。全データを維持するcompact保存と、利用者が明示する設定のみ保存を追加し、12MiB取り込み上限は変更しない。

実画面のユニ30秒がM5/CPU全応答一致（100,837,867）、前APIとinput/全raw SHA一致。保存raw再投影も追加native/GPU0。別の短い通常API4秒は移動/範囲の2編成がRTX3070TiとCPU全応答、同条件M5のinput/全readback SHAに一致した。標準30秒profileのCUDA認定とは分ける。Windows memory peakは最大2,139,754,496byteで2GiB上限に近いため、大きなrunは追加せず保存compiler情報を読む。サービス未識別/保全falseと観測のunknownを保持する。[検証記録](../research/product-declared-ui-v1.json)。以下は履歴。

# 2026-11-01 宣言モデルの固定移動・範囲を通常製品へ接続

通常HTTP APIで元ユニ/ヤン30秒の固定5条件、アスカWILLE＋レイ仮称15秒の固定4条件、蓄積回帰2条件がM5/CPU全製品応答一致。保存全11のsource/input/rawと全応答再投影も追加native/GPU0。宣言モデルでありゲーム位置/距離/基礎半径の認定ではない。標準profileのGPU数には重複加算しない。

共通の固定readyと座標初期化をversion6で共存させ、同じPROGRAMS/CLIへmovement-fixed/named-range-fixedを追加。両programは自身の109 CPU検査、実M5、fresh GPU禁止sealを通したv15登録済み。旧14memberは全内容保持。手動遮蔽や複数宣言モデルの合成は理由付き拒否。単純な旧header4/5への変換はGPU拒否を保存して撤回した。CUDA/MSLの既存normal/fixed生成物raw一致は確認したが、旧CUBINのsource ownerは書換えず、新座標固定のCUDA実機は未実施。[検証記録](../research/product-coordinate-fixed-v1.json)。以下は履歴。

# 2026-10-31 固定バースト4秒も通常APIでCUDA/Metal一致

現runtime03e166bcのfixed4秒が実CUDAでCPU全製品payload一致し、全読戻しSHAも実M5保存結果と同一。damage16,415,516、burst I3.0/II3.1/III3.2/full3.583秒。通常HTTP14.2125秒、launch/sync/readback0.3737秒、compiler/JIT0、kernel1回。現CUDA確認は同じprofileの蓄積1秒/固定4秒で、標準固定30秒や全編成の確認ではない。Job peak1,989,357,568bytes/missing0/post空、service未確認/保全false。8点のメモリ観測はJob query取得自体は成功したが上限field不足により完全性false。明示buffer要求合計3.73MBに対し、launch前後でprocess private約1.55GB増/GPU free約1.45GB減を観測した。増加の具体的内訳や原因は未認定、Windows処理は終了。[範囲と測定](../research/product-cubin-admission-gate-v1.json)。以下は経過。

# 2026-10-31 現共通runtimeで短い通常APIのCUDA/Metal一致

共通CLIの同一CPU admissionでowner全payloadの重複読取を削減した。初回全byte確認、manifest完全一致、GPU直前の最終全byte確認、別owner/artifact検査、独立監査を維持し、request間cacheは持たない。旧ownerのbaselineはSHA固定sourceのliteralをASTで読む。計算本体/数値/期待値/normalizerは不変。Mac関連145検査とWindows artifact37検査が成功。

新runtime03e166bc…の通常蓄積1秒がRTX3070Ti/Apple M5でCPU全製品payload一致し、入力と全読戻しSHAも両backendで同一。CUDAはこの1profile/元編成/1秒の範囲だけで、標準fixed30秒は0。Windows Job40.930秒・peak1,984,475,136bytes・missing0、service未識別/保全falseと過去link missing7/原因unknownを保持する。別条件fixed4秒はMetal/CPU一致済み。fixed専用PTXは展開前launcher誤りを保持・修正して初回生成成功（NVRTC17.788秒、内外missing0）。service未確認により保全falseのまま、未実施objectと条件付きlinkを依頼済み。その後のfixed4秒成功は冒頭に記録。[検証範囲と原記録](../research/product-cubin-admission-gate-v1.json)。以下は履歴。

# 2026-10-31 全266標準profileを現共通GPU sourceで確認

通常HTTP APIの標準30秒・固定周期・既定育成・cubeなしで、262profileが実Apple M5 MetalとCPU全製品payloadに一致した。4profile（Yuni／Yan／Heavy Arms／Rei仮称）は必要な移動・範囲・Lock Onモデル未指定を理由にCPUへ切替。数値差/API error/cache hit0。全266保存captureの入力再packing・source/raw SHA・全CPU/GPU/API再投影も追加battle/GPU0で一致し、実行中source不変と現共有GPU source完全一致を確認した。以前の255からAnn／Soldier O.W.／Velvet／Bay4段階の7profileが改善した。[検証記録](../research/target-count-query-evidence/product-current-catalogue-v2.json)。全条件・全特殊効果の完成ではない。

現ソースのWindows PTX→object→CUBINと厳密artifact監査は成立した。通常API1秒の試行は出所監査に約45秒を使い、待機helper53秒でCUBIN読込み中に停止、結果/readbackは未完成。今回CUDA製品profile追加0、標準fixed30秒は0。元linkのmissing7/原因unknown/保全falseを履歴付きで保持し、再実行なし。次は同一admission内の重複package検証を既存gateを維持して整理する。[Windows記録](../research/product-cuda-offline-chain-v1.json)。以下は過去sourceの履歴。

# 2026-10-31 通常APIの短い2条件でMetal/CUDA全readback一致

現実装9a6c3aa7のAlice2秒・Rapunzel Pure Grace3秒を通常APIの両backendで実行し、同じ入力・全readback SHAが一致、CPU全製品payloadも各backendで一致。保存raw再投影も成功、追加battle/GPU0。Windowsは同じ保存CUBINを使い、新コンパイル0、2件の実処理合計122.04秒。

CUDA製品確認はMiranda1秒を含め3profile、標準30秒/fixed/group/targetは未確認。範囲・全ハッシュ・保存時間内訳は`research/target-count-query-evidence/product-current-controls-parity-v1.json`。次はCPUに既存consumerがある敵attack.debuffsのGPU入力拒否を、共通incoming/carrierへ接続する。以下は履歴。

# 2026-10-31 現ソースで通常HTTP APIのCUDA実計算を確認

共通の部位packet呼出し境界とCPU監査最適化を含む9a6c3aa7を、M5 Metal/独立seal後に同sourceでPTX→object→CUBIN化した。通常/api/jobsのMiranda・実蓄積1秒がRTX3070Tiで実CUDA実行され、CPU全製品payload一致。保存raw再投影と静的入力全byte再生成もWindows内で照合済み、追加battle/GPU0。コード・効果・入力・結果変換・検査は同じ共通実装を使う。詳細は`research/target-count-query-evidence/product-parts-call-boundary-v1.json`。

現CUDAの製品確認は1profile・1秒に限る（標準30秒/fixed/group/targetは0）。直前sourceの全266 Metal確認は255一致/11理由付きCPU切替で、現sourceでは5主役・7追加条件とCLI蓄積/固定の数値保持を確認した。全キャラ・全効果・全設定の完了とは区別する。Windowsはmissing/cleanup0でもサービス未識別のため環境保全falseを保持し、原本はWindowsにあるpeer報告として記録する。以下は履歴。

# 2026-10-31 対象別補正と部位の製品合成

元projectile/shieldダメージ補正を持つ編成でも、typed対象がないBODY/PART世界を検証して元部位とboss行動を共通実行器へ渡す。対象別補正carrierを部位係数へ転用しない。通常/複数命中×固定/蓄積の4通常API条件がM5実Metal/CPU全payload一致。初回通常2件のGPU拒否は保存し、修正後は同一input全byteで成功。

通常の部位なしGPU source/input/生成物は前回成功と完全同一。保存readbackを既存比較器で現CPUへ再照合して一致、追加GPU/コンパイラ0・期待値更新0。証拠product-modifier-parts-composition-v1.json。これは既存profileの条件拡張で、profile数増加や実typed対象規則の完成を意味しない。

# 2026-10-31 元部位指定を製品結果へ接続

元enemy.partsは既存authored-live-parts factory/pool registryを使用。入力部位名とslot/nodeを事前一致検査し、read_product_partsがGPU直接/extra damage・hit counter・破壊logを検査して既存parts_state形式を返す。部分チャージは本体と同じPARTIAL_IS_FULL、native multi-hitのBODY pelletは既存追加部位packetを呼ぶ。部位を別の論理敵には数えない。

通常API4条件（Miranda固定、Alice固定tap、Belorta蓄積multi-hit、Miranda部位＋boss script）が実M5/CPU全製品payload一致。元失敗2件を保持し、数値期待値/CPU正本/normalizerは変更なし。部位なし通常蓄積/固定も独立CLI/sealで旧数値全一致。集約記録product-parts-composition-v1.json参照。全編成/全効果/現CUDAの完了を意味しない。

# 通常製品APIの共通GPU経路

製品入口は共通の4 helperをnoinlineで呼び、CUDAの大きなフレーム処理の展開を抑える。
計算式・検査・wireは同一。元30秒fixtureのinput/output全バイトとCPU fingerprintを
保持したM5実行・独立監査があるが、現compiler profileの全API回帰は別途確認する。
`product-outline-v1.json` は過去255 profileと現在の確認範囲を分けて記録する。

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
