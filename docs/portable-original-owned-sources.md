# 元アインの羽とシンデレラの弾換算

`coordinate-original-owned` はアインの1／12／40秒と、シンデレラ：クリスタルウェーブの3／30秒を使う5入力です。完全5人編成・元74／88全効果・成長・武器とseed4101を保持。シンデレラは既存の公開 `weapon_mode_swap=True` だけを指定し、任意効果やCPU算出の射撃予定は入力しません。固定shared Slang入口の既存kind35／37を使用し、GPU／数値／wire／Runtimeを変更していません。

アインは戦闘開始時4枚、4.016667秒の元burstで6枚へ更新。1／12／40秒の終端は4／6／2枚、refresh epoch1／2／2、次の時計4.16／12.016667／44.016667秒です。無期限1枚と有限38／32／26秒、burst追加10秒×2の元descriptorを保持し、実通知tickと1枚ごとのダメージ生成を比較します。寿命と間隔は元データが持つ推定モデルです。既存のLEGACY_WARNINGを元managerから観測し、GPU側のlegacy descriptorも検査します。ゲーム実機での寿命確定という主張にはしません。

シンデレラの3秒対照は換算発火0、30秒は実モード切替後に8回の `squad_ammo_consume_as` が発火します。値40の各回は追加39通知で、物理通知を含む部隊カウンタは1,737。実弾・再装填・モード・全ダメージは既存全戦闘比較を保持し、元の200発ごとのtriggerが持つ累計counterもGPU readbackから直接比較します。まとめてカウンタへ足す置換は行いません。

既存 `world_ammo_equivalent_native.observe` の受動観測をcontext manager `capture` として共用し、従来observeはそこへ委譲します。羽は実managerのsource container・refresh・tickを読み、追加のbuff queryは行いません。探索コードsnapshotのmanifestは1秒対照のみで、そこから凍結adapterの全5件をCPU観測しました。探索をwhole-suite認定へ流用せず、後の完全5入力packageで全input/native指紋を照合しています。

結果は `research/portable-original-owned-checkpoint.json` を参照してください。元BODY代表での実証であり、全variant／ADD世代／全敵モデル・全キャラの認定ではありません。現在CUDAの実計算・compile cache、19packing失敗、公開GPU統合も残ります。

M5 Metalは全5status0・CPU一致。実GPU1回3.254542秒、必須archive pipeline hit0.002838秒、Slang追加0。元の4入力と両CUDA/MSL全byte同一。別GPU禁止childで全5fresh138.779740秒・live parent receiptなしでseal。元GPUの失敗／再試行は0で、Windows新規依頼0です。

Ein40秒／Cinderella30秒の実正例では、観測器なしの全nativeと、観測器ありから追加観測fieldだけを外した全native、外側の生成索引がそれぞれ完全一致しました。これは2正例の観測透過性検査で、全5ケースの透過性を別途証明したとは主張しません。実測は同時実行で、性能benchmarkではありません。独立fresh監査は別に全5ケースを比較しています。

GPUで検査済みの状態readerを、文ごとのASTが同一であることを確認して関数へ抽出。prepare／native_reference／witnessのASTも保持しました。実readbackから取り出した小さな状態fixtureで世代・枚数・時計1ULP・dispatch数・カウンタ1件の破損を拒否し、負例のたびに長いnative戦闘を再実行しません。旧ammo観測のnative透過性・25 literal等の既存referenceテストも再利用します。

最終packet `/tmp/nikke-original-owned-final-v1.zip`（25916dd1…、2004files）は関連29／制御480検査成功（Windows専用1skip）。全payload SHA／checkout byteと実GPU source/input/native/outputを照合し、generation必須hit・Slang0。1990同一payload、57,182,951byteを共有展開。全readback reader終了後、SHA/size/inode保持の疎化で26,542,080byteを回収し、raw削除0です。

全266profileの静的分類も再確認し、247packing／19失敗／kind拒否0／拡張8は前の全profileと一致。残る20の観測されたoperator分類を、timing/condition descriptor・診断code・全message・reference readiness laneを保持して保存しました。projectile／shield damage補正、cover defense等は単なるkind受付不足ではなくreference modelの不足を含み、既存のtyped基盤を戦闘producer／consumerへ接続する必要があります。「単一の観測分類」の件数を、完了するprofile数と読み替えません。現在CUDA／公開GPU・全キャラ認定は未完です。
