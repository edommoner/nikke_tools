# 製品CPU参照consumerの接続

2026-10-31、ユーザーは残11profileのCPUモデル拡張を許可した。対象はアンの敵回復、ユニ／ヤンの移動、ソルジャーO.W.の遮蔽DEF、ベルベットの敵弾倉、スノーホワイトHeavy ArmsのLock On、ベイ4段階の配分、レイの対象数。pinned upstreamを変更せず、専用adapterと回帰テストで進める。未確定仕様は宣言モデルとする。この範囲について再確認を待つ必要はない。

最初の接続は `product_reference_models` の敵回復。現在は通常製品Metalまで接続済み（末尾の2026-10-31実証を参照）。以下は最初のCPU接続時点の契約と、その後も維持する境界。通常評価要求に次の任意項目を渡す。

```json
{"reference_models":{"enemy_healing":[{"node":"heal-source","targets":["__enemy__:wave#1"],"amount":1000}]}}
```

sourceは既存idle node、対象は実際の有限HPを持つADDに限る。回復量は元のheal_received_pct、世代別field可視性、現在のdealtを使い、既存のHPへ適用する。hit数と累積damage creditを巻き戻さない。生存・世代・満HPでのclampは既存EnemyHealingを再利用する。receiptは1024件を超えた時点でエラーにし、履歴を切り捨てない。

通常CPU結果の `reference_models` に宣言、実回復receipt、最終ADD状態を返し、未確認の実ゲーム規則と区別する警告も返す。未指定要求は元の計算のまま。失敗時もsimulateの両aliasを復元する。元アンの全69定義を保持した通常評価で、回復倍率の低下と実HP回復を回帰テストした。既存の敵回復12テストも通過した。

**初版のCPU接続だけでは製品Metal対応の完了としなかった。** 当時は宣言がある場合にGPU前で明示拒否した。現在の通常製品Metal接続でもstatic準備には宣言値だけを保持し、CPU receipt・HP・時刻をGPU入力へ渡さない。legacy GPUにも黙ってモデルを省略させない。過去の専用enemy-healing Metal実証を、今回の通常API GPU実証へ付け替えない。

その後、既存enemy_healing wire／共有consumerの製品入口とreadback変換を接続した。残るモデルも同じ境界を守る。移動優先規則、独立したcover基礎DEF、敵弾倉、Lock Onの不明な距離式を暗黙値で補わない。

# バースト周期指定

元の `mast3`／解決済みpatternを既存の共通BurstControlPolicyへ接続した。優先順位を変える規約であり、非該当周期の使用を禁止するフィルタではない。GPUが完了full-burst数を数え、候補選択を行う。CPUの選択結果や予定時刻は入力しない。

既存weapon-stage wordの未使用上位bitへliteralを格納し、input/output strideを増やしていない。every:Nは1〜524287、cycle listは1〜19、nullの存在と空listも区別する。容量を超える指定、未接続のdelay/wait/sequenceは明示拒否する。

M5の通常HTTP6条件は、固定／蓄積、オート対照、B2の配置変更、代替候補なしのすべてで全CPU payloadと一致した。指定ありでは3周期目と6周期目にMastが選ばれ、指定なしの結果とも実際に変わった。代替候補なしでは非該当周期にもMastが発動した。保存raw再投影も一致し、追加GPU／nativeは0。普通のaccumulate基準1入力も実MetalとGPU禁止の独立sealを通し、旧入力・出力・native指紋を保持した新v2へ登録した。旧v1は保存した。他programの基準を未検証のまま更新していない。

添付設定はMac内だけで検証し、周期指定の接続後は実GPUまで到達した。burst履歴はCPU一致だが、1人のdamageとtotalに差があり、GPU結果を拒否してCPUへ戻している。許容差は緩めていない。詳細な個人設定、結果、hash、rawは共有しない。公開の集約証跡は `research/product-burst-pattern-v1.json`。

Windowsの前版はown70成功後にfake SDK検査で停止した。テストの環境コピーに並列化設定が抜け、cache identityが変わったことが原因。fixtureを修正し、Macでthreads=2の模擬45テストを確認した。Windowsの実SDK／driver／GPUへは到達しておらず、今回のCUDA成功とは数えない。以前のtimeoutとclaimも保持する。次の固定sourceで必要な短い検証だけを依頼する。


## 2026-10-31 添付設定の差分解消

前節のprivate-v2の不一致は、同名装備のquantity carrier規約の差と判明した。通常製品のproducerだけをCPU正本の状態更新規約へ接続し、既存共有carrierを使用する。全定義を保持し、数量演算・Slang・CPU正本の変更0。private-v4では通常HTTP→実Metal→製品変換→全CPU payload照合が一致し、保存raw再投影も成功。旧失敗・private traceはMac内に保持し、個人設定・hash・詳細結果は共有しない。

公開のN102／アリス／モダニアの3profile・装備順違い6条件も全一致。既存対応profileの追加条件なので対応総数へ加算しない。CUDAはこの変更版の製品profile成功0を維持し、新しい固定packetの短いコンパイル確認を1回だけ依頼した。詳細は [量補正の製品規約](portable-quantity-runtime.md)、集約は `research/product-equipment-carriers-v1.json`。


## 2026-10-31 アンの敵回復を通常製品Metalへ接続

CPUのみだった初版に、既存のenemy healing共通consumerを接続した。通常要求の元effectに敵heal_received_pctがある場合、または明示reference_models.enemy_healingがある場合に、同じproduct-detail familyのhealing入口を使用する。キャラ名の受付表にはしない。全69定義と元の値・対象を保持し、既存scheduler・actor pool・carrier・ソフトbinary64演算を使う。通常の敵回復イベントなしはbankのsource数0で表現し、敵の受回復field自体は有効なまま保持する。回復量や予定表をCPU戦闘から入力しない。

元アンprofile0の通常APIで固定／蓄積30秒がM5 Metalと全CPU応答一致。明示sourceの技能レベル1／10、満HP、死亡済み、再出現、整数HP撃破の6条件も一致した。元の整数HP条件は小数creditを起こしていなかったためその記録を保持し、HPへ0.25を加えた別の1条件で小数credit／overkillを実際に確認した。計9条件の保存raw再投影も一致、監査の追加native／GPUは0。元の未対応11profileを再準備・静的compileしたところ、Ann1が通過し残り10は元の理由で拒否。これは静的結果からGPU成功数を加算した意味ではなく、Annの実GPU9条件は別の証拠である。旧255/266全体の現在sourceでの再実行数とは区別する。

任意のreference_models結果は、CPU／GPUで同じformatterを使い、実回復receipt・前後HP・hit数・世代・最終ADD・累積creditを返す。過去carrierの完全なリストや可視性診断はprivate observerに保持し、GPUの過去状態をCPUから再構成しない。元の通常結果形式は保持する。有限ADDの宣言モデルであり、BODYの有限HP回復や不明なゲーム規則の認定ではない。共有wireの4,368wordを付加し、input120,048／output2,032,000という既存transport上限内を使用する。

独立した固定product packet af33511d…で、回復sourceなしの通常accumulateもM5／fresh GPU禁止sealを完了した。新しいproduct-programs-v3にはhealing-accumulateだけを追加し、旧16member／v1／v2を保存。healing-fixedは通常APIで実証済みだがCLI goldenは未登録なので、他memberを流用しない。新suiteは追加していない。group／target modifier／ADD攻撃との合成は明示拒否し、CPUへ戻す。次はこの合成と残るconsumerの接続が必要。

共有sourceが変わった旧private enemy-healing certificateは歴史的証拠として保持する。source-baselineは古いsourceを現在扱いせず拒否し、unitでもこの拒否を確認する。privateの期待値・14件の過去出力・証明書の書換えや再ラベルはしない。今回の製品経路の証拠は `research/product-enemy-healing-v1.json`。

Windowsのowner68e212dc…はNVRTC34.511秒で戻り値0、PTX9,866,019byteを生成・cache公開したが、外側60秒上限で内側post／最終receiptが未完了。元のstage=false／image未admit／preservation=falseを保持する。標準file-only cache-probeで元PTXとの全byte一致をWindowsで確認、Macではmanifest・owner・生成pair・options／source SHAを照合した。MacがPTX原byteを読んだ意味ではない。object／link／driver／GPU／APIは0。記録は `research/product-equipment-windows-v1.json`。次は現在の通常product sourceと生成CUDAが完全一致する新ownerで必須cache hitを使用し、NVRTC再実行0のまま標準receiptを完成できるか確認する。旧claimを削除・再試行しない。


## 2026-10-31 Bayの宣言配分を通常製品へ接続

`reference_models.weighted_incoming` に `{"policy":"declared-weighted-incoming-v1","caster_weight":8,"other_weight":3,"cover_weight":262}` を指定すると、既存checked CPU adapterと共有Slang weighted landingを通常製品から使う。これらの値は既存検証fixtureの宣言値であり、ゲームの比率を確認した意味ではない。指定なしでは比率を推測せず理由付きCPU fallbackを維持する。既定266profileの未対応数からBay4件を減算しない。

元のbody／self_cover markerを保持し、既存carrier lifetime・深さ優先event frame・生存者mask・shield／cover／HP処理を再利用する。入力に追加するのは16wordのliteral比率と元定義rowだけで、CPU配分・recipient mask・HP・時刻は入れない。新suite0・新数値演算0・pinned upstream変更0。複数consumer、group／target／ADD攻撃のspecializationとの合成は明示拒否し、黙って効果を省略しない。CPUではExitStackでadapterを復元し、失敗時にもsimulate両alias／namespaceを戻す。

Bay favorite0〜3の30秒、65秒の遮蔽破壊後と2回目burst、3秒の効果発動前、固定周期の計7条件が通常HTTP→実Apple M5 Metal→全CPU製品応答一致。65秒では実際に遮蔽が破壊され、以後のsnapshotはcoverを含まず、元carrierの2回目burst更新も確認。保存input／readback再投影7件が成功し、追加native／GPU0。CLI登録後の再監査も全input byte・GPU source closure・計算応答が一致、VCS evaluator stampだけはcommitの変化として分離した。元の即時監査はevaluatorを含む全応答を照合済み。

既存product-detail familyへweighted-accumulate／weighted-fixedを追加。固定owner087904c1…はown82＋fresh native1＋M5実GPU1を通り、別fresh GPU禁止sealも成功。旧programの期待値を保持したv4へweighted-accumulateのみ追加した。fixedはHTTP実証済みだがCLI golden未登録。最初のpacketは登録数18固定のunitでGPU前停止し、その失敗を保持、登録20への修正後の別ownerで検証した。小証跡は `research/product-weighted-incoming-v1.json`。今回の製品確認は**宣言配分を使うMetal4profile／7条件、CUDA0**。ゲーム比率の認定、既定profileの完成、全効果の合成完成とは区別する。


## 2026-10-31 独立遮蔽DEFと明示手動遮蔽を製品へ接続

`reference_models.cover_defense` は5人の `[{"name":"元の編成名","base_defense":1000}, ...]`。body DEFから推測せず、各ownerの独立した基礎値を既存checked CPU adapterと共有Slang cover consumerへ渡す。通常APIの `manual_cover_sequences` は `{ "元の編成名": [{"action":"cover","t":7.4,"duration":0.25}] }`。既存のliteral validator（1人8操作以内）と共通のmanual controlを使用し、CPUとGPUで同じ操作を実行する。CPUの決定時刻・配分・生存状態はGPU入力にしない。制御区間はGPUの実entry/exit/down境界から既存traceへ出力し、CPU正本のformatterで製品表示へ変換する。時刻を入力から再構成しない。

ソルジャーO.W.の元定義を保持し、通常HTTP7条件が実M5／全CPU応答一致。top ATK3人の倍率・期限切れ、貫通、実遮蔽5件破壊、均等配分＋shield、Noahの確率による実被ダメージ倍率、manual指定なしを含む。操作表示も照合対象。保存input／readback再投影7件はnative／GPU追加0。明示基礎DEFのモデルであり、ゲームの基礎量／レベル曲線を認定していないため、既定profile対応数へ加算しない。固定周期＋manualは結合header未実装で明示拒否。複数consumerやgroup／target／ADD攻撃specializationとの合成も未完了。

初期3版は順に一時snapshotの終了処理不足、操作表示未接続、manual初期化不足を検出してCPUへ戻した。元captureと失敗を保持し、検査・許容差・CPU期待値を緩めていない。同じ不具合を全条件へ展開した重複を受け、最終版は先頭1件の全応答一致後に残6件を検証した。新suite／数値演算／pinned upstream変更0。固定owner3397d554…のown86＋fresh native1＋実Metal1、別fresh GPU禁止sealも成功。v5へcover-accumulateだけを追加し、旧18goldenは保存した。

共通source2ファイルへ観測hookを追加したため、旧通常／Ann／Bay等のgoldenは現在ソースの証拠に読み替えない。完全な旧source inverseとstrict normalizerを保持する。各旧programの現ソース再sealは未完了。今回の製品確認数は**宣言モデルのMetal1profile／7条件、CUDA0**。既定profile残10／全キャラ・全効果の未完了を維持。小証跡は `research/product-cover-defense-v1.json`。

## 2026-10-31 未指定量を使わない既定worldの実行

Bay4段階とソルジャーO.W.の既定30秒・固定周期要求を、モデル宣言なしで通常Metalへ接続した。元effect・値・carrierをすべて保持し、量が存在しないことをproduct専用bankのword3=1で明示する。payloadの0wordは未指定領域の予約paddingで、基礎DEF=0や等分配の仮定ではない。GPU consumerは未指定量を使おうとした時点でstatus64へ停止する。通常producerは全literalのattack／攻撃するsummon nodeを検査し、1個でもあれば明示量を要求する。発動条件やdelayをCPUで実行して「到達しない」と予測することもない。CPU正本／数値演算／strict normalizerを変更していない。

この範囲の既定5profileは、通常HTTP→実M5 Metal→CPU全応答一致。これに加え、元の明示weighted／cover各1条件も一致し、以前の成功captureとinput/readback全byteを保持した。保存監査は7件・追加native/GPU0。ホストの静的判定を迂回して既存の正例wireの量だけを未指定へ変えた2負例も実GPUで確認し、bank初期化後のconsumer実行でstatus64／receipt0へ停止した。未指定値を数値0として消費しないことを確認した。

元の未対応11profileのfresh静的準備・compileはAnn／Bay4／Soldierの6通過、残5拒否となった。残りはユニ・ヤン・ベルベット・Heavy Arms・レイ。静的6通過を実GPU6件と読み替えず、今回の実製品確認は**既定Metal5profile／5条件＋宣言モデル保持2条件、CUDA0**とする。歴史的255件全体の現在sourceでの再実行数ではない。攻撃を含むworldの未知量、複数consumer合成、fixed＋manual cover、他の未実装効果は未完了。小証跡は `research/product-no-incoming-v1.json`。

歴史的source監査は、後続の完全一致preimageを先に復元してから、旧added-sourceの元SHAを確認する順序へ接続した。元SHA／ledger／算術goldenを変更せず、未レビューの追加byteは引き続き拒否する。共通ソースの変化を旧成功の現在認定へ付け替えない。
