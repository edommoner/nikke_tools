# 実射撃groupと子効果の共通GPU接続

`attack-group-battle` は、CPUの [実射撃契約](portable-battle-attack-groups-native.md) を共有Slangの武器frame・Actor receipt・既存DFS・既存着弾queueへ接続する明示的な入口である。通常UIや既定のstatic受付を開かない。`routing='all-logical-enemies'` のBODY／ADDモデルであり、ゲームの射程・爆発半径・散弾分布を認定するものではない。

GPUが実際の発射・pellet×muzzles・Actor着弾からdistinct集合を構成し、全packet終了後に既存DFSへevent62を通知する。登録順の同じ閾値は1通知にまとめ、元のeffect descriptorの重複は既存dispatchが処理する。CPUのhit列や通知列をGPU入力へ渡さない。元ニヒリスター／ベロータの全73／71定義を保持した20入力と、元ノワール／ツバイに宣言listenerを足す2入力を区別する。

groupは32slot／128typed対象／1射1024packetを上限とする。射撃ID・epoch・owner・refcountをGPUが所有し、callback前にsealしてopen groupを切り離す。Frameは対象集合のkeyを保持し、関係しない通知ではそのscopeを隠す。current-target selectorは既存Actor setへ変換するため、敵buffも既存のper-target carrier経路を通る。queued childは専用512key bankに参照を保ち、消費後に解放する。従来のperiodic／interrupt receipt欄を変更しない。

死滅・世代交代した対象へ子効果を付け替えず、正本 `Boss.route(ev.to)` と同様に未着弾の要求量をglobal overkillへ一括乗算で計上する。新世代へのdamage／hit／scoreは増やさない。binary64・整数化・pow・damage formula・strict normalizerは元の共有実装を使う。出力は1,048,576 wordsで、group logは64射までであり、超過は拒否する。履歴を黙って省略しない。

32入力（native22／拒否10）がApple M5上のMetalで一致し、別processの独立sealも成功した。前回CPU22のnative値は全て同一で、32入力のrawは134,217,728byteである。実射撃168group・閾値通知112回、元2プロフィールの3／30秒と破壊／世代交代、元SG2キャラの実10packet射撃を照合した。GPUは1.950231秒、初回library1.546503秒／PSO89.670118秒で、実runのSlang新規起動0（必須generation cache hit）だった。Runtime strideは138,952byteで不変である。登録CPU23検査・共通制御372検査（Windows専用1skip）に成功した。

既存 `destructible-body-heal-share-retention` 61入力も現sourceで一致し、input／native／全255,852,544byte rawを保持した。独立sealの新基準はGPU source closureと生成物identityだけを更新し、全61 entriesとinput／output hashは旧版と同一である。旧rawの破損検査2件のsource gateもexact parent projectionへ接続し、fixtureの内容と期待値は維持した。CPU93件92.349692秒、native52事前照合72.759016秒、GPU10.322387秒だった。親oracle52再利用・追加native0は既存の同一process所有規約であり、独立監査ではfresh52を計算する。

## 失敗と修正

最初のCPU packageは監査用upstream資料の同梱漏れで停止した。次のMetal実行ではCLIの既定786,432 wordsとshaderの1,048,576 wordsが不一致で、22入力でaddress fault、単一入力でstatus64となった。割当値を修正し、adapterの出力宣言とtransportが違えばprepare前に拒否する共通CLI guardと負例を追加した。

修正後の22入力では、長時間DoT4入力がperiodic receiptとの欄衝突、敵buff5入力が対象展開漏れで不一致となった。専用queue key bankと共通Actor set selectorで修正した。敵buff照合に追加した4件の不一致は、正本が戦闘終了時に退場処理するadd objectの `alive` を誤使用した比較器の問題だった。carrierの解決済み対象と現在の世代へ直し、同じ保存readbackをGPU0で再照合した。

さらに全ADDの数量を調べ、dead／stale要求を正本がoverkillへ計上する4入力の差分を発見した。命中を発生させず、共有の超過計上へ接続した。これらの失敗・各claim・raw・保存再照合は維持する。成功したbodyや戦闘総量だけで全対象対応済みとしない。

## 監査と境界

共通比較器はbattle全体、全物理shot snapshot、各groupのID／epoch／時刻／packet数／順序付きtyped集合、通知回数、敵buffの対象・世代、全ADDのdealt／hit／世代、caster別ADD総量、global overkill、queue参照とgroup解放を調べる。入力拒否10件はmagic／policy／owner mask／threshold／counting mode／payload／stageを含む。

歴史source監査は親1192258へのexact逆差分を明示し、変更済み9GPUファイルと追加2ファイルをhash検証する。old include closureだけを再構成して既存監査へ渡し、実行時source hashや生成物のnormalizerは変更しない。これは過去のsource保持検査であり、GPUの結果一致を代用しない。実測と独立seal・旧出力保持の状態は `research/portable-battle-attack-group-gpu-checkpoint.json` に記録する。

64射の観測上限を超える長時間caseと、mixed-owner／callbackの広い境界検証が次の課題である。公開受付、広いgeometry／shield／parts、mixed ownersの広い組合せ、現ソースのCUDA実機計算とcompile cache実測、全キャラ認定は未完了である。Windowsの追加操作は行わず、過去のプロセス終了原因unknown／環境保全falseを維持する。通常UIはCPU、全体目標は未達である。
