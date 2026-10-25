# 元編成の固有ゲージと共通kind事前検査

`coordinate-original-resources`3はE.H.の全76定義・ネオン：ビジョンアイの全83定義を元の5人編成／weapon／成長／操作のまま扱うsealed suiteです。E.H.初期化3秒、敵24体死亡を伴う上限・弾倉生成3秒、ネオンのバースト消費6秒を検証します。元の効果は削らず、CPUの計算済みdamage・射撃・死亡スケジュールを入力へ渡しません。

新入口 `gpu/world_coordinate_original_resource_entry.slang` は既存共通resource handlerのkind9 `gauge_charge` とkind10 `gauge_consume` を受け付けます。計算本体・binary64・wire／Runtime容量は変更しません。元E.H.は初期10の資材→弾倉1→資材全消費を実行し、敵死亡の追加chargeから弾倉4・資材10へ達します。上限10で実chargeが切り捨てられる正本の呼出しも観測します。ネオンはバーストで100→0を実消費します。

受動observerは実 `_dispatch_instant` の元row／owner／nameを照合し、呼出し前後と最終の保存ゲージ辞書をコピーします。GPU比較は全戦闘・packet・RNG・操作に加え、全5人／全resourceのpresence・値・base cap・各定義の実発火数を検査します。今回の元編成には発生するevery_stack通知がなく、GPUにも余分な通知がないことを検査しました。**正のevery_stack伝播を実証したという意味ではありません。** gauge_consume_as_ammoや他の資源操作も今回の受付には含めません。

## Slang／CPUで同じkind条件を使う

`app/portable_coordinate_kind_admission.py` の宣言から `gpu/coordinate_vital_kind_admission.slang` を生成し、sampled-vital初期化の条件としてincludeします。同じ宣言をCPUで読み、元entryの無条件macroと実wireのburst-control有効flagを使って判定します。生成fragmentが宣言と違う場合や、解釈できない条件付きprofile macroは拒否します。

共通CLIの `prepare_entries` では、明示subsetを選んだ後、正例のkindを**native基準作成・GPU実行より前**に検査します。domain=Noneの期待されたGPU拒否ケースは維持します。旧入口でのゲージ9/10拒否、前回の元センチ22拒否、burst-control無効時の5拒否をCPUだけで確認し、native呼出し0・GPU禁止で停止するテストを備えます。この検査は**kind条件だけ**であり、schema全体・他の初期化条件・実行結果の認定ではありません。

開発checkout／full packageでは `python scripts/nikke_gpu.py entry-inventory --suite coordinate-original-resources --out UNIQUE.json` を使います。従来の既定入口、clock入口も選べます。全266profileのうち座標入力変換は247、今回のresource入口でkind条件に残る拒否は65です。残りがGPU対応済みという意味ではなく、`gpu_admission_verified`／`calculation_verified` はfalseのままです。compactではこのコマンドを拒否します。

## 実証と残件

固定packet `/tmp/nikke-original-resources-develop-v1`（95b08ccd…）／capture `/tmp/nikke-original-resources-metal-v1` はM5 Metal全3一致。GPU1回0.570817秒、初PSO90.865717秒、CPU事前17.487625秒、生成cache必須hit／compiler0。同claim retry0です。旧clock入口はresource opt-in未定義時のCUDA／MSL生成物が変更前と全byte一致。strict source／transport inverseと負例も通り、normalizerを緩めていません。旧raw source/goldenの一致は更新せず、生成物保持と新入口の証明を分けます。

独立fresh監査20.138357秒、別child・全3native domain再計算・live parent receiptなし・GPU0で成功。同じ監査からgoldenとsource-only certificateを作成しました。現CUDA compile/link/cache/battleの証明ではありません。生成CUDAのbyte維持もWindows実機のcache hit測定と混同しません。

最終compact `/tmp/nikke-original-resources-final-v1.zip`（44c51fa9…）は機能19／制御476（Windows専用1skip）成功。終了後に全1929payload SHA／checkout全byteとGPU source・input・native・outputを確認。全reader終了後にrawをSHA／size／inode維持で疎化、削除0です。記録は `research/original-resource-evidence/` と `research/portable-original-resources-checkpoint.json`。

次は実在する未受付のammo操作13/14等と、それに依存する元ゲージの正の通知を優先します。敵回復・元武器group対象モデル・召喚攻撃、現CUDA／warm cache性能、公開GPU・全キャラ認定も残ります。全キャラ0／UI CPU／全目標未達、Windows新依頼0です。
