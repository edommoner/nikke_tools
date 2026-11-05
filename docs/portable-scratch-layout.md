# 共通GPUのscratch配置監査

割り込み対象の物理着弾を接続する準備中に、旧配置4436fbfの領域重複を発見した。FOCUS/NQR/historyを「すべての既存scratchの後」として追加したが、別ファイルにliteralで置かれていたheal-share診断・部位スキル着弾・割り込み集計を配置表へ含めていなかった。

- 部位スキルは781328..785424に2048件×2wordを保持する。
- 旧NQRの773056..781792と、旧履歴781792..781856はその領域へ重なる。
- 旧数値照会診断781856..785968も部位スキルと割り込み集計785424..785434へ重なる。
- heal-share診断771072..781320は旧FOCUSとNQRへ重なる。

以前の成功ケースはこの組合せを最大容量まで使っておらず、成功を取り消す数値差分はまだ観測されていない。ただし、この配置を混在機能一般へ拡張できるという証拠にはならない。旧証拠と失敗rawは保持し、新配置を別のsourceとして実行する。

## 容量を保つ配置

出力stride786432word、Runtime field、算術本体、入力ABI、キャッシュ数と着弾容量は変更しない。既存領域の最大利用範囲と、初期化時だけpadding全体をゼロ化する順序を監査した上でpaddingを割り当てる。

| 領域 | 新しいword範囲 | 容量 |
|---|---|---|
| NQR cell bank0 | 248600..252952 | 32×136word |
| FOCUS | 258576..260656 | header32＋256×8word |
| NQR cell bank1 | 518336..522688 | 32×136word |
| NQR header | 785440..785472 | 32word |
| 全順序履歴 | 785472..785536 | 64word |
| 数値照会診断 | 770976..775088 | 4112word、専用診断entryのみ |

NQRは64件の完全な64要素binary64辞書を保つ。論理サイズ8736wordは非連続となるため、読書と初期化の両方が共通`nativeNumericCell`を使う。部位スキル、割り込み集計、heal-share診断の旧addressは維持する。

数値照会診断とheal-share診断は別entryの排他的なモードであり、その二つだけは領域を共有する。両macroを同時に有効にするsourceは明示的な`#error`で拒否する。通常計算のFOCUS/NQR/historyは、どちらの診断とも分離している。

## 再利用するチェック

```sh
python scripts/nikke_gpu.py layout-check --out <fresh.json>
python scripts/nikke_gpu.py layout-compare --before <old-capture> --after <new-capture> --out <fresh.json>
python scripts/nikke_gpu.py package --suite scratch-layout --out <fresh.zip>
```

`layout-check`は最大容量のlegacy領域、literalのSlang address、actor-fieldsの末尾query scratch、診断排他guard、既存初期化と新状態初期化の順序を検査する。`compile_program`のschema確認もこの監査を呼ぶ。数値/GPU実行の証明ではない。

`scratch-layout`は通常・数値診断・回復診断の3モード×2seedと2拒否の8入力。共有address helperと実際の部位receipt helperを使い、全64辞書cell、256照準cache、2048部位receipt、履歴、割り込み集計、診断へ異なる32bit patternを書き込む。CPU側の独立したliteral配置から全出力を比較し、未割当wordへの書込も拒否する。単体はMetal全8入力と独立sealに成功し、実goldenで通常CLIへ登録した。battle/full-character認定ではない。

元のリリー30秒入力のwindow診断も新配置でMetal一致。旧1355入力と全CPU正本指紋は不変であり、同じ122sourceのMetal1355入力(native1071/拒否284)が全一致し、独立fresh sealも成功した。CPU92群487検査171.427秒、GPU11.386783秒。新sourceのためSlang2回生成し、CUDA/Metalの本体・normalizerは共通のまま。通常CLIの最終小packetはCPU10検査に成功した。単独25の旧goldenはsource121の履歴として保持し、新sourceの対応25入力は1355の中で検証している。出力は配置が変わるため単純な全raw一致を要求せず、canonicalの全battle比較を維持した上で、移動したcache/header/履歴の対応と、それ以外の全bytesを別途照合する。normalizerは変更しない。

`layout-compare`はレビュー済み4436fbf→新配置のsource差分だけを受け付け、入力ファイルと全rawのSHA、全native指紋、移動したcache/header/履歴、その他の全bytesを検査する。実1355入力では1302入力が全byte一致し、移動対象53入力(focus41/NQR12)の対応も一致した。移動外の4,260,934,400 bytesを保持。入力やゲーム状態を書き換えてraw SHAを更新しても拒否する故障テストを付けた。

新windowの133観測/26missはCPUと一致し、数値照会診断領域以外は同じリリー30秒の通常結果と全byte一致した。両診断macroの同時指定は、実Slangコンパイルでも明示guardのerrorで拒否し、生成出力0/GPU0だった。

割り込み対象のCPU bridgeの試作は `/tmp/nikke-private-interrupt-runtime-draft-v1.py` に保存した。private kind6をcanonical ActorKindへ混ぜず、実際のnative hit_targetの前後を受け渡す方式で、元18ケースが終了まで動くことを観測した。ただし正式な契約・GPU接続はまだ行っておらず、受付を開いていない。配置修正の検証後に再開する。

検証済み旧rawと今回のrawは、全bytes/SHA/path/inodeを保持したまま計4,938,137,600 bytesのゼロ領域割当を回収した。削除0、GPU再実行0。

Windows追加操作0、7プロセス終了原因unknown、環境保全falseを維持。全キャラ認定0、UI CPU、全体ゴール未達。
