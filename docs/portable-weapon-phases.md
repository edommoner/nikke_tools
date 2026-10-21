# 共通武器フレームの分割

Windows v126の既定JIT、v127の明示レベル1は、同じ保存PTXのcache hit後にmodule loadがCUDA218／ptxas Memory allocation failureで終了しました。上限2GiB・60秒を維持し、同条件の再試行や別レベルへの無根拠な切替は行いません。

次の候補では、保存PTXでvirtual register23,336／38,938行だったweaponFrameBodyを5つの共有Slang helperへ分けます。数値・効果定義・ケースを削らず、状態や対象・時刻をCPUへ移していません。旧PTXはentry_reload追加前のRuntime246なので、次の候補との資源差を分割だけの因果と断定しません。旧観測は失敗原因の証明ではありません。

| helper | 既存処理 |
| --- | --- |
| prepareWeaponFrame | 対象・物理武器の選択、entry待機、再装填、フレーム準備 |
| advanceWeaponCharge | 予約済み自動再装填とchargeの待機・発火準備 |
| captureWeaponShot | 再装填可否・弾の係数・数量・damageのsnapshot |
| landWeaponPellets | 既に計算済みの弾を着弾させ、元のshot数を確定 |
| finishWeaponShot | gauge・通知・弾buff・mode終了・次発時刻 |

Runtime247 fields／138952byte／align8、入力796、wire strideは維持します。外側weaponFrameのphysical context cleanupも維持し、最初の3段階はready=falseで開始して元の早期returnを外へ伝えます。epoch・modeShots・modeは準備の後／chargeの前で一度だけ保存します。着弾後にerrorが立った場合も、元の通り終了段階へ進み、勝手なerror gateを足しません。

portable_weapon_phase_contractは元d97a8dfの2,287 tokenの処理文を再構成して同じ順序で比較します。helper引数の型・順序・inout、caller引数、snapshot位置、早期return伝達も検査します。計算値の改変、snapshot再読取、ready gate欠落、Runtimeのinout欠落を故障注入で拒否します。これは静的契約で、GPU・compiler資源の証明ではありません。

生成CUDAのweaponFrameBody本体は21,965byteから1,260byte、5 helper本体は1,627〜7,182byteです。5関数の__noinline__も確認しました。全関数647→652／noinline215→220、Runtime宣言全fieldは同一です。最大関数admitDefinitionsは変わらず73,200byteです。これらの字句統計からptxasメモリ改善を主張しません。

固定パッケージ8e02b2ebのMetal796（native633／拒否163）はすべて一致し、旧796のinput／全raw／native指紋も保持しました。全2,503,999,488byteのSHAはb9cd45185fb37568494df918a71d4b115b7853e26e8eba0b1af5d307f6d30637、全lazy bankゼロです。全portable CPU788件は787成功・Windows専用1skip・失敗0。静的契約のsignature検査補強後は追加で5検査成功。保存結果・独立seal・構造統計はcheckpointを正本にしてください。

Metal GPU時間の単発観測は分割前13.9128秒、後13.9710秒でした。元はpipeline cacheあり、後はpipeline生成約8秒なので、コンパイル・転送を含む実行器全体時間を速度比較へ流用しません。性能ベンチマークではありません。

次のWindows確認は、この新sourceでCPU事前検査後にPTX-onlyを1回生成し、成功時だけ専用cacheをCPU読取で照合します。さらにmissing0等の境界が揃う場合だけ、その同じPTXを必須cacheから明示JIT1の別fresh Jobでmodule確認します。各Job2GiB／60秒、BelowNormal・start gate・cleanup5秒、保存失敗とclaim保持、NVRTC／driverの分離を維持します。戦闘buffer／転送／同期／kernelは使いません。module成功でも計算一致ではありません。

全キャラGPU認定0、通常UI CPU、entry_reloadのcover4件・新版CUDA計算は未完了、packing214/266は入力受付のみです。全目標は未完了です。

最終sealed packageのfresh展開では、共通smoke91件中90成功・Windows専用1skip・失敗0でした。追加signature guardとそのテスト・suite/smoke登録・独立golden/manifest以外は実行済みパッケージとbyte同一で、GPU sourceと全adapterも保持しています。Windowsでは同じsmoke91が全件成功・新たなmissing0の場合だけ短いcompilerへ進めます。
