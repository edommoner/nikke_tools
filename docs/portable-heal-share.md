# 回復分配の共通実行器への接続準備

現在の根拠は`research/portable-heal-share-reference-checkpoint.json`。共通CLIで独立CPU契約20件を検証できる段階で、GPU実装・受付はまだ追加していない。全キャラGPU認定0、UI CPUを維持する。固定CPUの`heal_sharing_compat`が宣言するモデルを参照し、実ゲームで未確認のモデル選択まで実証したとは扱わない。

## 再利用する経路

固定packageをfresh展開後、そのpackage内のCLIで実行する。

```sh
python scripts/nikke_gpu.py reference --suite heal-share --out /tmp/heal-share-reference.json
```

既存`portable_reference.run_reference`を再利用し、literal生成中に戦闘を実行せず、参照中はpacking・GPU build/executeを禁止する。出力は排他的に確保し、失敗を保持する。source closure、入力、native全状態、trace、literal契約のSHAを記録し、途中のソース・入力変更を拒否する。詳細nativeはローカル、checkpointにはケース別指紋と契約結果だけを残す。

`world_heal_share_native`は実際のplan・body_heal・共有回復・通知のPython frameを観測する。catalog/handler差し替えや追加state queryは行わない。既存`world_skill_native`のprofileが先行hookを転送しない問題を1行の連鎖追加で修正し、周期観測器との多段連鎖と成功／例外時の復元を確認した。CPU計算式・正本upstreamは変更していない。

## 接続前に確定した契約

- distinct live carrierごとのlive受益者をcarrier順・squad順で評価し、重複した対象名は重みを増やさない。同じownerでも別carrierなら重みを増やす。stack数やstatの値は重みではない。
- 重なるcarrierは連結成分となる。各受益者の重みは所属carrier数。期限切れ・戦闘不能を除き、自己のみ・リンクなしも明示する。
- 元受益者のoutgoing／received倍率を一度だけ評価。正数だけを分配し、複数recipientでは`amount * weight / total`の順。1recipientでは直接amountを渡す。分配先のreceived倍率を再適用しない。
- 満HPへの割当は再分配せず、既存storageへ余剰を渡す。負数／0は共有しないが、元のheal_received通知は維持する。
- 各portionのbody/storage更新後に同期HP通知の子を完了させ、次のportionへ進む。分配自体は再帰的共有や追加heal_received通知を起こさず、元の通知は最後に1回だけ行う。
- 入れ子のHP通知からリンクを解除して別の回復を行っても、外側の分配planはsnapshotを維持する。20番目のケースで外側5人plan、内側slot2のみ、内側完了→外側slot2の再開、元通知slot2→slot0を検査する。

## 失敗からの訂正と検証範囲

初回の隣接満HP通知の期待値2は、特定listenerの発動数と通知全体を混同していた。既存sync_hpは各回復者の隣へ通知するため5人で8件。原失敗を保持し、portionごとの受信先`[1] / [0,2] / [1,3] / [2,4] / [3]`と順序・時刻まで検査する契約へ直した。CPU正本は変更していない。

関連7テストで全20契約、観測器なしとの既存native全field／trace完全一致、hook連鎖・例外復元を確認。plan/portion/通知欠落、HP不一致、辺の受信者・時刻・順序、入れ子plan／数量／復帰境界の改変を拒否する。fresh packageの全846検査は既存ps確認1件がsandbox拒否、Windows専用1skip。他844は成功し、同じpackageの影響群5検査をOS観測可能な環境で再確認して全成功。再実行で元失敗を置換していない。

同packageの共通cpu_preflightで既存796入力・native633も全golden一致、input SHA21080fdf…を保持した。今回GPU実行0、Windowsは既存v132保存fileの読取だけ。

## 次のGPU実装に必要な接続

CPU契約は共通Slang実装の完成ではない。今後はlive/条件評価、共有plan、ordered binary64数量、body/storage、同期HPイベント、元heal通知を既存Frame実行器へ接続する。特にplan・cursor・元recipient/sourceの継続状態を入れ子Frameごとに保持し、子が外側snapshotを上書きしない設計が必要。instant healingとlifesteal双方、maxHP付与／修理／蘇生との区別を確認する。

最新版CUDA assemblyが未成立なので、GPU追加はv132固定基準のcompiler切り分けと混在させない。projectile_dmg_pct／shield_dmg_pctはCPU消費経路未確認で、単純な出力不変だけから意味不在と判定しない。受付だけを増やして無処理で対応済みにしない。
