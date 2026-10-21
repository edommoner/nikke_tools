# 周期スキルの持続的な割合補正

`skill_cooldown_pct`をCUDA／Metal共通Slangの周期時計へ接続しました。canonical stat58／kind0、数値・状態・イベント・テスト入力を共有します。private combat worldだけで受け付け、公開APIの対応認定には使いません。

## 参照との対応

参照CPUの`BuffManager.tick`は、周期スキルのcasterに適用される現residentの値を合計し、`base * max(0, 1 + percent / 100)`を計算して`base * 0.05`を下限とします。-95%の計算結果と、-100%で下限へ達する結果はbinary64で僅かに違うため丸めません。参照Python3.12のfloat sumに合わせて既存の補償加算を再利用し、補償が非有限ならrunning totalを使います。大きな有限値の相殺と合計+infinityを検査しました。

途中付与・失効時は既存時計が残り時間を新旧周期比で調整します。一回だけ残り時間を減らす`skill_cooldown_reduce_pct`とは別の演算で、併用しても次周期の定義を変えません。元のcallback順序と時計更新順序を維持します。

割合補正の参照経路はget_buffs照会とは異なり、永続buffのruntime predicateを再評価しません。まだtarget_charsがNoneなら全casterが対象です。解決済み対象、stack、同名merge、失効・死亡時の削除は既存carrierを参照します。`target_effect`も割合補正のフィルタではありません。flatな`effect_interval`／`skill_cooldown`は別演算で、まだ未対応です。

## 検証

- 個別32入力：native28＋raw拒否4。0／正／負／下限、途中付与・失効、stack・同名merge、複数owner、名前付き・遅延・重複対象、runtime predicate、values、複数period descriptor、死亡後の時計、一回限りの短縮との併用、相殺・overflowを含みます。
- 期待値は参照CPUの実戦結果・全skill traceと、実際の`_next_fire`辞書の次回時刻／前回周期です。GPUの式から再構築しません。
- 実イサベル全効果の3秒・30秒を実編成へ追加。効果・武器・成長値を検証用に差し替えていません。
- regression361（native292＋拒否69）はApple M5 Metalで全一致。GPU8.071477秒、library1.087493秒、pipeline9.769500秒、bounded47.878198秒。旧327ケースのinput・全raw output・native指紋を保持しました。
- 固定development packageを既存CLIでGPU禁止監査・明示sealし、通常regressionを`portable-world-skill-interval-regression-short-expected.json`へ切替。旧goldenは履歴として保持します。

静的packing192/266、基本キャラ133/203、分類112。これは全キャラ実戦認定数ではありません。通常画面CPU、全キャラ実戦認定0、最終目標未完了、新機能のCUDA実機数値一致は未確認です。

## レビュー反映と次の不足

分類へstructured reason／文言fallbackの観測件数を追加しました。inventoryは定義側91／44、program側47／27。同じ不足が両方に出るため未対応機能数として合算しません。境界・event audience・参照scalingの既知経路は明示reasonへ変更しました。

優先候補`projectile_dmg_pct`と`shield_dmg_pct`はpinned参照の計算式・対応表で消費箇所をまだ確認できていません。効果を無視して受付だけ広げず、仕様確認対象に残します。参照処理が確認できる候補はflat周期変更、復活、persona対象選択などです。

CUDAキャッシュは原byte・option・DLL/header SHAの検査を維持し、成功hit／必須miss／破損時にNVRTC DLLを読まない経路へ変更。fake NVRTCによるCPU検査で確認した改善で、Windows実測の速度改善は未主張です。

依頼済みv112の保存結果を取得しました。O1／60秒／Job2GiB、1回のみ、NVRTC30.344秒でallocation failure、artifact0／kernel0／retry0。Job最大2,148,286,464byteと上限との因果は未確定です。missing0・cleanup成功でもservice未識別なので環境保持falseを維持。noinlineの改善は未立証です。原captureはWindowsに保持し、Mac受領の構造化報告は独立raw監査ではありません。同条件再試行・上限拡大をせず次の仮説を先に定めます。
