# 元定義まで戻る未受付演算監査

開発checkout／full packageで次を使います。compact packageでは従来どおり拒否します。

```sh
python scripts/nikke_gpu.py entry-inventory --suite coordinate-original-cleanse --out /tmp/new-entry-operators.json
```

従来の入力変換・literal kind検査に、次の出力を追加しました。

- `profiles[].rejected_effects`: compiled rowを実`binding_source_indices`で元source rowへ戻し、owner・name・元effect SHAを保持します。行番号が同じだという仮定は使いません。
- `operator_priorities`: kindだけでまとめず、type／stat／target／timing／condition／scaling／参照先／定義field一覧で分類します。プロファイル数・元定義数・compiled行数を別々に出します。
- `kind_dependencies`: 同じプロファイルに必要なkindの組合せと対象一覧です。複数の受付をまとめて新入口へ接続する候補を調べられます。
- `packing_failures`: 入力変換できない元プロファイルを分離します。kind拒否が無いことを入力変換やGPU実行成功へ読み替えません。

分類中の元binding不整合は、通常のpacking gapへ落とさず監査全体を失敗にします。元effectの参照先はdeep copyし、source/data/compiler/GPU SHAの前後検査・CPU戦闘/GPU禁止・失敗保存・上書き拒否を維持しました。

## 現在の候補

全266プロファイル／247入力変換、未変換19、kind拒否22を26の具体的な演算記述へ分類しました。3.790879秒、監査内のCPU戦闘・GPU呼出し0。実行・GPU受付全体・全キャラ認定の証明ではありません。

| kind | 元のstat | 主な依存・対象 |
|---|---|---|
| 33 | `force_skill_use` | Julia（율리아）の愛蔵品1/2/3は33だけ。サクラはスキル2強制使用と15の両方 |
| 15 | `named_buff_duration_extend` | クラストの全チャージ、プリカの元イベント、サクラの部位破壊。参照先と対象を別分類 |
| 23 | `force_reload` | ミルク：ブルーミングバニー／ジル／アスカ：WILLE。発火条件はそれぞれ異なる |
| 27 | `shield_heal_pct` | ラプンツェル：ピュアグレイス／キロ／モリ。元シールドの実損傷・補充が必要 |

他に18／20／21／30／31／34／35／37が残ります。優先表は静的な影響数であり、実装費用の見積りでもGPU対応率でもありません。現在の共有RNG・解除Metal goldenとGPU sourceは一致したままです。今回GPU source／数値本体は変更していません。

## 次の強制使用のCPU調査

元Julia（율리아）は愛蔵品1が77定義中のスキル1を1件、愛蔵品2/3は各79定義中のスキル1を3件、時刻0に実強制発動しました。元サクラ74定義もスキル2の2件を時刻0に発動。public body／元の全効果・weapon・成長設定を通じて調査し、追加の効果や計算済みスケジュールは入力していません。

これらの時刻0では`_next_fire`が空でした。空の前後一致を非空の周期時計保持の実証には数えません。サクラの実部位破壊による2状態の延長・期限・tick位相は未検証で、次の15＋33実装／Metal検証に含めます。今回の調査はGPU受付・計算成功ではありません。

記録は `research/entry-operator-evidence/` と `research/portable-entry-operators-checkpoint.json`。6検査が成功し、元sourceへの逆引き・複数compiled行の計数・分類漏れ・不正provenanceの監査失敗を検証しました。全キャラ認定0／公開UI CPU／全目標未達、Windows新規実行0です。
