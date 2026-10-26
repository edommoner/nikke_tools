# 型付き対象の所有者と現在対象fieldのCPU契約

この頁はCPU契約を固定した時点の記録です。現在の専用GPU接続・実証範囲は[共通GPU所有者field](portable-coordinate-typed-owner-gpu.md)を参照してください。

`reference --suite coordinate-typed-owner-common --out UNIQUE.json` は、明示的な `body-owned-current-fields-v1` を検証するCPU専用の5ケースです。不変packageを展開して実行します。現GPU compilerはこのpolicyを明示拒否します。

対象bindingはPROJECTILE／HP_SHIELDかつowner `[0,0,1]` を必須にします。所有者なし、ADD所有、異なるBODY世代をBODYへ推測しません。実worldのregistryから物理handleの完全な世代を照合し、同世代の破壊済み対象は所有者を保持、再登場後の古い世代は拒否します。event／impactの物理handleは書き換えず、敵fieldのrecipientと対象条件を問い合わせるときだけ宣言BODYへ投影します。policy無しの既存経路と通常current damageの照準選択は維持します。例外時にもglobal resolverとmanagerメソッドを復元します。

元Primの完全5人編成、71定義、成長・武器・seed4401を保持しています。元の `…자고 싶다`（`hit_count:4`、target）の実発動を、1秒対照／8秒BODY／ADD／手動typed＋ADDで確認します。原本を登録順・所有者・全定義で照合してから実行します。

5件目には原本を残したまま、明示した監査効果2件だけを追加します。実射撃がHPシールド `[3,10,1]` に命中し、実counter完了から子fieldが発動する経路です。camera照準はADDでも、宣言された所有者BODYへ子fieldが入り、実buff queryはBODYのreceived_dmg_pct=17、両ADD=0でした。counter完了の物理target・attack ID・damageと実攻撃receiptも照合します。この2件は元キャラ効果の実証へ数えません。

## 保存された検証

- CPU reference5件成功、37.628665秒。原本field数0／1／1／1／1。GPU／packing呼び出し0。
- owner単体5件、関連84件、制御488件成功（Windows専用1件skip）。
- 既存sealed67入力／native40のCPU回帰成功、181.761955秒、入力SHAは旧GPU成功時と一致。
- 全362 Slang、数値・正本・CUDA compile cache・backend transportは旧最終packageとbyte一致。既存67の生成cache必須hit、追加Slang0。

検証に用いた不変packageはCPU回帰 `e862a114…`、新reference `c106fbb2…`、最終 `31724c3b…` です。最終差分はreadinessとowner契約の強化のみ。最終契約は保存nativeをJSON往復し、入力・native SHAを照合して全5件再監査しました。最終packageでnativeを再生成したという主張はしません。対応関係は `research/typed-owner-reference-evidence/package-binding.json` と同ディレクトリの検査script、checkpointで固定しています。

## 残件

共通Slangのowner consumer／wire、Metal／CUDA実計算は未接続です。ゲーム仕様・公開GPU・全キャラ認定も未完です。ADD所有・所有者なしの敵弾・他世代／caller／移動形状へ一般化しません。

次のGPU拡張は旧67入力をすべて保持し、所有者と照準が異なるcounter caseも比較します。旧67のfresh独立監査は223秒かかるため、ケースを省かず、各childを制限時間内に収める全範囲集約監査の実行経路を先に整備します。GPU実行やCPU oracleを省略するcacheとして扱いません。
