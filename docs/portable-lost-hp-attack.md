# 失ったHPに応じるATK倍率を共通実行器へ接続

`buff/atk_pct/scaling:lost_hp_pct/target:self`を、既存の共有Slang `stackedValue`へ接続しました。DEFで既に使っていたflag128と同じ経路です。GPUの変更は`reference_runtime.slang`の受付条件1箇所で、ATKはalliedFlags0、DEFは従来どおりalliedFlags1を必要とします。別stat／別kind／敵buff／非combat／参照倍率の混在／self以外は拒否します。ホスト側の拒否分類にもscaling／recipientの構造化理由を付けました。

正本`BuffManager._get_value`は、照会時の使用者HP%から`基本値 × max(0, 100 − HP%)`を返します。この分岐はstack数を掛けません。値1・HP50%ならATK倍率は50%であり、追加の100除算は通常のATK適用時だけです。新しい数値計算器、状態配列、CPUでの戦闘値の事前計算は追加していません。共有binary64・整数変換・pow、正本CPU・既存CUDA、strict normalizerは不変です。

`reference --suite lost-hp-attack`のCPU21契約は、HP100／75／50／0%・100%超、負の値、端数のties-to-even、100%超のATK倍率、owner4、stack3でも倍率を増やさない規約、期限終了、2つの寄与、被弾と回復、最大HP変更、保護膜で防いだ攻撃、初期条件と照会時条件、親のsnapshotと子の再取得、通常射撃を含みます。親の連続ヒットは1500を2回保持し、回復した後の子は1250／1000。通常射撃は被弾後に1500→1600→1700となります。

観測器は実際のget_buffsと_get_valueの戻りをprofileし、余分な状態照会をしません。既存の全nativeフィールドとtraceを保持し、hookの合成・失敗時の復元、総量／packet／ATK値／HP%／owner／時刻／source名／scalar値／発数／stackへの故障注入を検査しています。初回fixtureではHP条件が成立する前にbuffを発動できると誤認しました。drainを先に行う正しいケースと、初期条件が偽で発動しない対照を分け、初回CPU失敗記録を保持しました。正本は変更していません。

追加の`reference --suite lost-hp-attack-revival`は3契約。死亡のままなら攻撃0、パッシブ再付与と保持buffの50%復活なら1500を2回です。復活後の絶対HPとdown状態も検査します。既存の復活時None bridgeを使い、別モデルは追加していません。

Metalは主suite29（native21／raw拒否8）、復活3、ギロチンの全定義を保持した3秒／30秒2入力が成功・独立seal済みです。3秒は失HP ATK値0の対照、30秒では正のscalar714回、最初は4.016666…秒、最大47.883944738594685、最小HP50.1208908972972%を正本で観測しました。この追加観測でも保存済みnative指紋は完全一致し、GPUの再実行はありません。

旧1016入力を既存の4比較器へ元domainのまま渡す1バッチへ統合し、同じ115 sourceでMetal一致・独立sealしました。旧全input/native/output entriesとraw3,196,059,648バイトが全byte同一です。nested971の元8群も、byte同一の親と全entriesを介して証明書を更新しました。新29＋復活3＋実2を含む合計1050入力（native847／拒否203）です。回帰58群350検査は既存90秒CPU枠内の79.062秒で成功。GPUは10.416秒、追加Slang起動0でした。単発の観測で速度ベンチマークではありません。

full115／commands116のsource certificateを実証から更新し、14検査に成功しました。最終sealed packageをfresh展開し、CPU57検査と29入力／native21の事前照合も成功しました（GPU0、claimなし）。commands専用の生成CUDA／Metalは、前の版と原byteも同一でした。CUDAキャッシュの実hitや新しいCUDA数値一致を証明したものではありません。生成cacheとNVRTC cacheを混同せず、Windowsの新規native／compile／GPUは0を維持します。

ギロチンの物理履歴は3秒112件で省略0、30秒2048件で32件省略。旧キロ32件・レム55件などの制約も残ります。Runtime追加field0、stride138952、CUDA定数48バイト。静的packing223/266・base163/203・72分類はGPU対応率ではありません。UIはCPU、全キャラGPU認定0、最終ゴールは未完了です。

package・seal・全byte保持・実編成の観測・制限は`research/portable-lost-hp-attack-checkpoint.json`へ集約しています。次はプリバティ：アンカインドメイドを阻む`pellet_hit_in_shot:5`の正本consumerを先に契約化します。未確認のprojectile／shield係数はnoopとして受け付けません。
